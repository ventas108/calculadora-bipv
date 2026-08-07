"""
Producción hora a hora usando la curva IV real del panel (Motor IV / SDM De Soto 2006).

A diferencia del modelo simplificado lineal `Pmax = Pmax_stc × G/1000 × (1 + γ·ΔT)`,
este módulo deriva la potencia Pmp(G, Tcell) de la curva I-V single-diode calibrada
a partir de la ficha completa del panel (Voc, Isc, Vmp, Imp, Ns + parámetros SDM:
I_L_ref, I_o_ref, R_s, R_sh_ref, a_ref y coeficientes térmicos).

Está VECTORIZADO: las 8760 h se resuelven en una sola llamada a
pvlib.pvsystem.singlediode (método Lambert-W), NO en un bucle Python hora a hora.

Uso previsto (opt-in): la página de Producción ofrece este modo SOLO cuando el panel
tiene ficha completa para el Motor IV (calculos.modelo_iv.tiene_sdm_completo).
"""

import numpy as np
import pandas as pd
import pvlib

from calculos.modelo_iv import (
    obtener_constantes_tecnologia,
    tiene_sdm_completo,
    preparar_panel_iv,
    K_BOLTZMANN,
    Q_ELECTRON,
    T_REF_K,
    G_REF,
)
from calculos.temperatura import temperatura_celda_noct


def preparar_para_iv(panel: dict) -> tuple:
    """
    Resuelve el panel utilizable por la curva IV y su procedencia (#105).

    Cascada (misma que el Motor IV, calculos.modelo_iv.preparar_panel_iv):
      1. SDM calibrado en catálogo         → (panel, "calibrado")
      2. Ficha completa (Voc/Isc/Vmp/Imp + Ns) → fit_desoto on-demand
                                           → (panel_estimado, "estimado_ficha")
      3. Datos insuficientes o fit fallido → (None, None)

    Antes, Producción solo aceptaba el caso 1: los paneles con ficha completa
    pero sin SDM precalibrado caían al modelo lineal simplificado aunque el
    Motor IV sí sabía estimar sus parámetros.
    """
    # Un panel ya preparado por esta función conserva su procedencia (el dict
    # estimado pasa tiene_sdm_completo y sin esta marca se re-clasificaría
    # como "calibrado" al re-entrar, perdiendo la trazabilidad).
    if panel.get("_sdm_estimado"):
        return panel, "estimado_ficha"
    if tiene_sdm_completo(panel):
        return panel, "calibrado"
    try:
        _prep = preparar_panel_iv(panel)
    except Exception:
        _prep = None
    if _prep is not None and tiene_sdm_completo(_prep):
        # Merge sobre el panel original: estimar_sdm_desde_ficha devuelve un
        # dict nuevo SIN metadatos del catálogo (NOCT, área, N_s...). Sin el
        # merge, la simulación caería al NOCT default 45°C aunque la ficha
        # tenga otro valor.
        return {**panel, **_prep, "_sdm_estimado": True}, "estimado_ficha"
    return None, None


def panel_apto_para_iv(panel: dict) -> bool:
    """
    True si el panel puede simularse con la curva IV real: SDM calibrado
    o ficha completa de la que estimar el SDM (fit_desoto on-demand).
    """
    return preparar_para_iv(panel)[0] is not None


def _pmp_iv_vectorizado(
    G: np.ndarray,
    T_cel: np.ndarray,
    panel: dict,
) -> np.ndarray:
    """
    Pmp (W) por módulo hora a hora derivado de la curva IV single-diode.

    Idéntico modelo físico que calculos.modelo_iv (De Soto 2006 + Rsh exponencial
    CdTe Mermoud 2005) pero aplicado de forma vectorizada sobre arrays de 8760 h.

    G      : irradiancia efectiva en el plano (W/m²) — array 1D
    T_cel  : temperatura de celda (°C) — array 1D
    panel  : dict con parámetros SDM completos del catálogo

    Retorna: array 1D de Pmp (W) por módulo.
    """
    G     = np.asarray(G, dtype=float)
    T_cel = np.asarray(T_cel, dtype=float)

    constantes = obtener_constantes_tecnologia(panel["tecnologia"])

    # nNsVth_ref en Voltios (convención pvlib)
    Vt_ref     = K_BOLTZMANN * T_REF_K / Q_ELECTRON      # 0.025693 V @ 25°C
    nNsVth_ref = panel["a_ref"] * Vt_ref

    # R_sh exponencial CdTe (Mermoud 2005) — reemplaza el lineal de pvlib
    G_safe = np.where(G > 0, G, 1.0)
    R_sh   = (panel["R_sh_ref"] * np.exp(-constantes["c_Rsh"] * (G_safe / G_REF - 1.0))
              + panel.get("R_sh_base", 0.0))

    # alpha_sc: pvlib espera A/°C → Tk_alfa[%/°C] / 100 × Isc_stc[A]
    _Isc_stc = float(panel.get("Isc_stc") or panel.get("Isc") or 1.0)
    alpha_sc = panel["Tk_alfa"] / 100.0 * _Isc_stc

    I_L, I_o, R_s, _rsh_pvlib, nNsVth = pvlib.pvsystem.calcparams_desoto(
        effective_irradiance = G,
        temp_cell            = T_cel,
        alpha_sc             = alpha_sc,
        a_ref                = nNsVth_ref,
        I_L_ref              = panel["I_L_ref"],
        I_o_ref              = panel["I_o_ref"],
        R_sh_ref             = panel["R_sh_ref"],
        R_s                  = panel["R_s"],
        EgRef                = constantes["Eg_ref"],
        dEgdT                = constantes["dEgdT"],
        irrad_ref            = G_REF,
        temp_ref             = 25.0,
    )

    resultado = pvlib.pvsystem.singlediode(
        photocurrent       = I_L,
        saturation_current = I_o,
        resistance_series  = R_s,
        resistance_shunt   = R_sh,   # modelo CdTe Mermoud 2005
        nNsVth             = nNsVth,
        method             = 'lambertw',
    )

    pmp = np.asarray(resultado["p_mp"], dtype=float)
    pmp = np.where(G < 5.0, 0.0, pmp)   # sin producción nocturna / irradiancia mínima
    pmp = np.maximum(pmp, 0.0)          # seguridad numérica
    return pmp


def simular_produccion_iv(
    tmy: pd.DataFrame,
    poa_base: pd.DataFrame,
    panel: dict,
    N_paneles: int,
    eta_inversor: float,
    factor_pr_mismatch: float,
    P_dc_stc_kW: float | None = None,
    k_bipv: float = 1.0,
) -> dict:
    """
    Simulación de producción anual hora a hora usando la curva IV real (Motor IV).

    Misma firma y misma cadena de correcciones (mismatch + temperatura NOCT) que
    calculos.produccion.simular_produccion_anual, pero la potencia por módulo se
    obtiene de la curva I-V single-diode en lugar del modelo lineal genérico.

    Parámetros
    ----------
    tmy                 : DataFrame TMY con columna 'T2m' (°C)
    poa_base            : DataFrame POA bruta con columna 'poa_global' (W/m²)
    panel               : dict del catálogo con ficha SDM completa
    N_paneles           : número de módulos del sistema
    eta_inversor        : eficiencia del inversor (0.90–0.99)
    factor_pr_mismatch  : factor de pérdidas cascada (poa_efectiva / poa_bruta)
    P_dc_stc_kW         : potencia pico instalada kWp; si None → N_paneles × Pmax_stc

    Retorna dict con las mismas claves que simular_produccion_anual más:
      metodo : "curva_iv" (para trazabilidad)

    Lanza ValueError si el panel no tiene ficha completa para el Motor IV.
    """
    # #105: acepta SDM calibrado o estimado on-demand desde la ficha completa.
    panel, _sdm_origen = preparar_para_iv(panel)
    if panel is None:
        raise ValueError(
            "El panel no tiene ficha completa para el Motor IV (SDM De Soto). "
            "Se requieren parámetros SDM calibrados, o al menos "
            "Voc/Isc/Vmp/Imp + Ns para estimarlos con fit_desoto."
        )

    if P_dc_stc_kW is None:
        P_dc_stc_kW = round(panel.get("Pmax_stc", 60) * N_paneles / 1000, 3)

    # ── Alinear índices ────────────────────────────────────────────────────────
    idx   = poa_base.index.intersection(tmy.index)
    G_raw = poa_base.loc[idx, "poa_global"].values.astype(float)
    T_amb = tmy.loc[idx, "T2m"].values.astype(float)

    # ── Irradiancia efectiva (cascada mismatch aplicada) ──────────────────────
    G_eff = np.clip(G_raw * factor_pr_mismatch, 0, None)

    # ── Temperatura de celda hora a hora (modelo NOCT + k_BIPV confinamiento) ──
    try:
        NOCT = float(panel.get("NOCT") or 45.0)
        if not (20.0 < NOCT < 100.0):
            NOCT = 45.0
    except (TypeError, ValueError):
        NOCT = 45.0
    # k_bipv eleva la temperatura de celda en fachadas con ventilación restringida
    T_cel = temperatura_celda_noct(G_eff, T_amb, NOCT=NOCT, k_bipv=k_bipv)

    # ── Pmp por módulo desde la curva IV real (vectorizado) ───────────────────
    pmp_mod = _pmp_iv_vectorizado(G_eff, T_cel, panel)

    # ── Pérdida por temperatura (referencia: mismo G_eff a T=25°C) ────────────
    T_ref_arr  = np.full_like(T_cel, 25.0)
    pmp_stc_g  = _pmp_iv_vectorizado(G_eff, T_ref_arr, panel)
    perdida_temp_por_modulo = np.maximum(pmp_stc_g - pmp_mod, 0.0)

    # ── Escalar al sistema ─────────────────────────────────────────────────────
    P_dc_W = pmp_mod * N_paneles
    P_ac_W = P_dc_W * eta_inversor

    # ── Energías anuales (Wh → kWh) ───────────────────────────────────────────
    E_dc_anual       = float(P_dc_W.sum()) / 1000.0
    E_ac_anual       = float(P_ac_W.sum()) / 1000.0
    perdida_temp_kWh = float(perdida_temp_por_modulo.sum()) * N_paneles / 1000.0
    perdida_inv_kWh  = E_dc_anual - E_ac_anual

    # ── Métricas IEC 61724 (idénticas al modelo simple) ───────────────────────
    H_i  = float(G_raw.sum()) / 1000.0
    H_ef = float(G_eff.sum()) / 1000.0
    Y_r  = H_i
    Y_a  = E_dc_anual / P_dc_stc_kW if P_dc_stc_kW > 0 else 0.0
    Y_f  = E_ac_anual / P_dc_stc_kW if P_dc_stc_kW > 0 else 0.0
    PR   = Y_f / Y_r if Y_r > 0 else 0.0
    CF   = E_ac_anual / (P_dc_stc_kW * 8760) if P_dc_stc_kW > 0 else 0.0

    # ── DataFrame horario ─────────────────────────────────────────────────────
    df_h = pd.DataFrame({
        "G_eff_Wm2":    G_eff,
        "T_cel_C":      T_cel,
        "Pmax_mod_W":   pmp_mod,
        "P_dc_kW":      P_dc_W / 1000.0,
        "P_ac_kW":      P_ac_W / 1000.0,
        "perdida_T_kW": perdida_temp_por_modulo * N_paneles / 1000.0,
    }, index=idx)

    # ── DataFrame mensual ─────────────────────────────────────────────────────
    meses_es = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
    df_m = (df_h[["P_dc_kW","P_ac_kW","perdida_T_kW"]]
            .resample("ME").sum()
            .rename(columns={
                "P_dc_kW":      "E_dc (kWh)",
                "P_ac_kW":      "E_ac (kWh)",
                "perdida_T_kW": "Pérdida T° (kWh)",
            }))
    df_m["Producción (kWh/kWp)"] = df_m["E_ac (kWh)"] / P_dc_stc_kW if P_dc_stc_kW > 0 else 0
    df_m.index = [meses_es[m] for m in df_m.index.month]

    return {
        "E_dc_anual_kWh":          round(E_dc_anual, 0),
        "E_ac_anual_kWh":          round(E_ac_anual, 0),
        "P_stc_kW":                round(P_dc_stc_kW, 3),
        "Y_f":                     round(Y_f, 0),
        "Y_r":                     round(Y_r, 0),
        "Y_a":                     round(Y_a, 0),
        "PR":                      round(PR, 3),
        "CF_pct":                  round(CF * 100, 1),
        "perdida_temp_kWh":        round(perdida_temp_kWh, 0),
        "perdida_inv_kWh":         round(perdida_inv_kWh, 0),
        "H_i_kWh_m2":              round(H_i, 1),
        "H_ef_kWh_m2":             round(H_ef, 1),
        "df_horario":              df_h,
        "df_mensual":              df_m,
        "uso_modelo_simplificado": False,
        "metodo":                  "curva_iv",
        "sdm_origen":              _sdm_origen,   # "calibrado" | "estimado_ficha" (#105)
    }
