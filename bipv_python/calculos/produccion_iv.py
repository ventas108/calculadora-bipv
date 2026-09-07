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

from calculos.modelo_iv import (
    tiene_sdm_completo,
    preparar_panel_iv,
    calcular_pmax_vectorizado,
    calcular_iv_vectorizado,
)
from calculos.modelo_jrc_huld import clasificar_tecnologia_jrc
from calculos.temperatura import temperatura_celda_noct
from calculos.agregador_anual import (
    agregar_anual_8760_poa,
    validar_entradas_horarias_8760,
)


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
    try:
        _prep = preparar_panel_iv(panel)
    except Exception:
        _prep = None
    if _prep is not None and tiene_sdm_completo(_prep):
        if _prep.get("_estimado") or panel.get("_sdm_estimado"):
            return {**panel, **_prep, "_sdm_estimado": True}, "estimado_ficha"
        return _prep, "calibrado"
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

    # Motor SDM centralizado en calculos.modelo_iv.calcular_pmax_vectorizado()
    # (modelo PVsyst v6, migrado desde De Soto 2006 el 2-sep-2026, ver
    # DIAGNOSTICO_MOTOR_PVSYST.md; incluye recombinación PVsyst/Merten 1998
    # para CdTe con d2mutau calibrado, ver DIAGNOSTICO_RECOMBINACION_CDTE.md)
    # -- misma llamada que produccion.py.
    pmp = calcular_pmax_vectorizado(G, T_cel, panel)
    pmp = np.where(G < 5.0, 0.0, pmp)   # sin producción nocturna / irradiancia mínima
    pmp = np.maximum(pmp, 0.0)          # seguridad numérica
    return pmp


def _iv_completo_vectorizado(G: np.ndarray, T_cel: np.ndarray, panel: dict) -> dict:
    """
    Igual que _pmp_iv_vectorizado(), pero también expone i_mp (A) por módulo
    -- usa calcular_iv_vectorizado() (modelo_iv.py, 7-sep-2026) en vez de
    calcular_pmax_vectorizado(), así que resuelve el single-diode UNA sola
    vez para obtener p_mp E i_mp juntos (no llama dos veces al solver).
    Solo se usa cuando hace falta la corriente real (pérdida óhmica DC en
    modo calculado) -- el resto de llamadas sigue usando el camino barato
    _pmp_iv_vectorizado(), que no necesita i_mp.
    """
    G     = np.asarray(G, dtype=float)
    T_cel = np.asarray(T_cel, dtype=float)
    iv = calcular_iv_vectorizado(G, T_cel, panel)
    mask = G < 5.0
    p_mp = np.maximum(np.where(mask, 0.0, iv["p_mp"]), 0.0)
    i_mp = np.maximum(np.where(mask, 0.0, iv["i_mp"]), 0.0)
    return {"p_mp": p_mp, "i_mp": i_mp}


def simular_produccion_iv(
    tmy: pd.DataFrame,
    poa_base: pd.DataFrame,
    panel: dict,
    N_paneles: int,
    eta_inversor: float,
    factor_pr_mismatch: float,
    P_dc_stc_kW: float | None = None,
    k_bipv: float = 1.0,
    P_ac_nom_W: float | None = None,
    poa_bruta_kWh_m2: float | None = None,
    factor_espectral: pd.Series | np.ndarray | None = None,
    pct_mismatch_fab: float | None = None,
    resistencia_dc_ohm: float | None = None,
    pct_cableado_dc: float | None = None,
    resistencia_ac_ohm: float | None = None,
    pct_cableado_ac: float | None = None,
    N_serie: int | None = None,
    tension_red_V: float | None = None,
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
    P_ac_nom_W          : potencia AC nominal del inversor (W) -- tope físico real de
                          salida (recorte/clipping, PVsyst: "Pnom"). None (default)
                          = sin recorte, retrocompatible. Ver el mismo parámetro en
                          calculos.produccion.simular_produccion_anual() para el
                          hallazgo real que lo motivó (29-ago-2026) -- este módulo
                          tenía el mismo hueco.
    poa_bruta_kWh_m2    : POA bruta REAL (antes de Motor Óptico) para el Reference
                          Yield (Y_r)/PR -- ver el mismo parámetro y el hallazgo real
                          (6-sep-2026) en calculos.produccion.simular_produccion_anual().
                          Este módulo tenía el mismo hueco (Y_r usaba poa_base, que con
                          Motor Óptico activo ya viene post-IAM+soiling). None (default)
                          = comportamiento histórico, retrocompatible.
    factor_espectral    : corrección espectral CdTe (First Solar) -- ver el mismo
                          parámetro y docstring completo en
                          calculos.produccion.simular_produccion_anual() (6-sep-2026).
                          Igual que ahí: solo se aplica si el panel es CdTe, y solo
                          al cálculo eléctrico (nunca a G_eff/H_ef/T_cel). Este
                          módulo usa el SDM completo para CdTe (no JRC/Huld como
                          produccion.py), así que necesita la MISMA corrección para
                          no divergir del motor base en paneles CdTe.
    pct_mismatch_fab, resistencia_dc_ohm, pct_cableado_dc, resistencia_ac_ohm,
    pct_cableado_ac, N_serie, tension_red_V : mismo significado y mismo
                          criterio (retrocompatible, None = sin pérdida) que en
                          calculos.produccion.simular_produccion_anual() -- ver
                          el docstring completo ahí (7-sep-2026). Única
                          diferencia real entre motores: este módulo SÍ resuelve
                          la curva I-V completa, así que la corriente I(t) del
                          modo calculado DC es la i_mp REAL que devuelve
                          pvlib.singlediode/bishop88_mpp (calculos.modelo_iv.
                          calcular_iv_vectorizado()), no una aproximación vía
                          Vmp nominal como en produccion.py (que usa JRC/Huld,
                          un modelo power-only sin curva I-V) -- más preciso.

    Retorna dict con las mismas claves que simular_produccion_anual (incluye
    perdida_clipping_kWh, horas_con_clipping, E_ac_sin_recorte_kWh, Y_r_es_bruta_real,
    factor_espectral_aplicado, factor_espectral_promedio) más:
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

    # ── Validar año TMY completo antes de simular ─────────────────────────────
    # Nunca usar intersection(): descartaría horas silenciosamente y después
    # las métricas anuales aparentarían cubrir 8760 h aunque no lo hagan.
    validar_entradas_horarias_8760(tmy, poa_base)
    idx   = tmy.index
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

    # ── Corrección espectral CdTe -- ver docstring "factor_espectral" arriba y
    # el comentario completo en calculos.produccion.simular_produccion_anual().
    factor_espectral_aplicado = False
    factor_espectral_promedio = None
    G_para_potencia = G_eff
    if factor_espectral is not None and clasificar_tecnologia_jrc(panel.get("tecnologia")) == "CdTe":
        fe = np.asarray(factor_espectral, dtype=float)
        if fe.shape == G_eff.shape:
            G_para_potencia = G_eff * fe
            factor_espectral_aplicado = True
            _mask_dia = G_eff > 5.0
            factor_espectral_promedio = (
                round(float(fe[_mask_dia].mean()), 4) if _mask_dia.any() else 1.0
            )

    # ── Pmp por módulo desde la curva IV real (vectorizado) ───────────────────
    # Solo se pide también i_mp (más caro -- ver _iv_completo_vectorizado())
    # cuando el modo calculado de pérdida óhmica DC lo necesita.
    i_mp_mod = None
    if resistencia_dc_ohm is not None and resistencia_dc_ohm > 0 and N_serie:
        _iv_pot = _iv_completo_vectorizado(G_para_potencia, T_cel, panel)
        pmp_mod, i_mp_mod = _iv_pot["p_mp"], _iv_pot["i_mp"]
    else:
        pmp_mod = _pmp_iv_vectorizado(G_para_potencia, T_cel, panel)

    # ── Pérdida por temperatura (referencia: mismo G_eff a T=25°C) ────────────
    T_ref_arr  = np.full_like(T_cel, 25.0)
    pmp_stc_g  = _pmp_iv_vectorizado(G_para_potencia, T_ref_arr, panel)
    perdida_temp_por_modulo = np.maximum(pmp_stc_g - pmp_mod, 0.0)

    # ── Mismatch fabricación + pérdida óhmica DC (7-sep-2026) ─────────────────
    # Mismo criterio y mismo orden que calculos.produccion.simular_produccion_anual()
    # -- ver ese docstring/comentarios para el detalle completo. pmp_stc_g NO
    # se toca (sigue siendo la referencia T=25°C pura para ②a/②b).
    E_dc_antes_binning_ohmico_kWh = float(pmp_mod.sum()) * N_paneles / 1000.0

    pct_mismatch_fab_aplicado = None
    if pct_mismatch_fab:
        factor_fab = 1.0 - pct_mismatch_fab / 100.0
        pmp_mod = pmp_mod * factor_fab
        if i_mp_mod is not None:
            i_mp_mod = i_mp_mod * factor_fab  # misma reducción proporcional de corriente
        pct_mismatch_fab_aplicado = pct_mismatch_fab
    E_dc_despues_mismatch_kWh = float(pmp_mod.sum()) * N_paneles / 1000.0

    perdida_ohmica_dc_modo = None
    perdida_ohmica_dc_por_hora_W = np.zeros_like(pmp_mod)
    if i_mp_mod is not None:
        # Corriente REAL resuelta por el modelo (i_mp por módulo = i_mp por
        # string, ya que los módulos en serie comparten corriente) escalada
        # al número total de strings en paralelo del proyecto.
        N_strings_total = N_paneles / N_serie
        I_total_A = i_mp_mod * N_strings_total
        perdida_ohmica_dc_por_hora_W = (I_total_A ** 2) * resistencia_dc_ohm
        pmp_mod = np.maximum(
            pmp_mod - perdida_ohmica_dc_por_hora_W / N_paneles, 0.0
        )
        perdida_ohmica_dc_modo = "calculado"
    elif pct_cableado_dc:
        pmp_mod = pmp_mod * (1.0 - pct_cableado_dc / 100.0)
        perdida_ohmica_dc_modo = "manual"
    E_dc_despues_ohmico_dc_kWh = float(pmp_mod.sum()) * N_paneles / 1000.0

    perdida_mismatch_fab_kWh = round(E_dc_antes_binning_ohmico_kWh - E_dc_despues_mismatch_kWh, 0)
    perdida_ohmica_dc_kWh    = round(E_dc_despues_mismatch_kWh - E_dc_despues_ohmico_dc_kWh, 0)

    # ── Escalar al sistema ─────────────────────────────────────────────────────
    P_dc_W = pmp_mod * N_paneles
    P_ac_sin_recorte_W = P_dc_W * eta_inversor
    if P_ac_nom_W is not None and P_ac_nom_W > 0:
        P_ac_W = np.minimum(P_ac_sin_recorte_W, P_ac_nom_W)
    else:
        P_ac_W = P_ac_sin_recorte_W
    clipping_W = P_ac_sin_recorte_W - P_ac_W

    # ── Pérdida óhmica AC (7-sep-2026) ─────────────────────────────────────────
    E_ac_antes_ohmico_ac_kWh = float(P_ac_W.sum()) / 1000.0
    perdida_ohmica_ac_modo = None
    perdida_ohmica_ac_por_hora_W = np.zeros_like(P_ac_W)
    if resistencia_ac_ohm is not None and resistencia_ac_ohm > 0 and tension_red_V:
        I_ac_A = P_ac_W / (np.sqrt(3.0) * tension_red_V)
        perdida_ohmica_ac_por_hora_W = (I_ac_A ** 2) * resistencia_ac_ohm
        P_ac_W = np.maximum(P_ac_W - perdida_ohmica_ac_por_hora_W, 0.0)
        perdida_ohmica_ac_modo = "calculado"
    elif pct_cableado_ac:
        _perdida_pct_ac_W = P_ac_W * (pct_cableado_ac / 100.0)
        perdida_ohmica_ac_por_hora_W = _perdida_pct_ac_W
        P_ac_W = P_ac_W - _perdida_pct_ac_W
        perdida_ohmica_ac_modo = "manual"
    perdida_ohmica_ac_kWh = round(E_ac_antes_ohmico_ac_kWh - float(P_ac_W.sum()) / 1000.0, 0)

    # ── Energías anuales (Wh → kWh) ───────────────────────────────────────────
    E_dc_anual       = float(P_dc_W.sum()) / 1000.0
    E_ac_anual       = float(P_ac_W.sum()) / 1000.0
    E_ac_sin_recorte_anual = float(P_ac_sin_recorte_W.sum()) / 1000.0
    perdida_temp_kWh = float(perdida_temp_por_modulo.sum()) * N_paneles / 1000.0
    perdida_inv_kWh      = E_dc_anual - E_ac_sin_recorte_anual
    perdida_clipping_kWh = E_ac_sin_recorte_anual - E_ac_antes_ohmico_ac_kWh
    horas_con_clipping   = int(np.sum(clipping_W > 1e-6))

    # ── Métricas IEC 61724 (idénticas al modelo simple) ───────────────────────
    # Y_r debe referenciarse a la POA bruta REAL -- ver docstring de
    # "poa_bruta_kWh_m2" arriba (mismo bug/fix que produccion.py, 6-sep-2026).
    Y_r_es_bruta_real = poa_bruta_kWh_m2 is not None
    H_i  = float(poa_bruta_kWh_m2) if Y_r_es_bruta_real else float(G_raw.sum()) / 1000.0
    H_ef = float(G_eff.sum()) / 1000.0
    Y_r  = H_i
    Y_a  = E_dc_anual / P_dc_stc_kW if P_dc_stc_kW > 0 else 0.0
    Y_f  = E_ac_anual / P_dc_stc_kW if P_dc_stc_kW > 0 else 0.0
    PR   = Y_f / Y_r if Y_r > 0 else 0.0
    CF   = E_ac_anual / (P_dc_stc_kW * 8760) if P_dc_stc_kW > 0 else 0.0

    # ── DataFrame horario ─────────────────────────────────────────────────────
    df_h = pd.DataFrame({
        "G_eff_Wm2":    G_eff,
        "factor_espectral": (
            G_para_potencia / np.where(G_eff > 0, G_eff, 1.0)
            if factor_espectral_aplicado else np.ones_like(G_eff)
        ),
        "T_cel_C":      T_cel,
        "Pmax_mod_W":   pmp_mod,
        "P_dc_kW":      P_dc_W / 1000.0,
        "P_ac_kW":      P_ac_W / 1000.0,
        "perdida_T_kW": perdida_temp_por_modulo * N_paneles / 1000.0,
        "clipping_kW":  clipping_W / 1000.0,
        "perdida_ohmica_dc_W": perdida_ohmica_dc_por_hora_W,
        "perdida_ohmica_ac_W": perdida_ohmica_ac_por_hora_W,
    }, index=idx)

    # ── Contrato anual oficial: suma directa de las 8760 horas ───────────────
    # Se conserva además el formato histórico de las claves E_* para
    # compatibilidad con Baterías, Financiero y Reporte.
    anual_8760 = agregar_anual_8760_poa(
        resultado_horario=df_h,
        poa_horaria=poa_base,
        columnas_energia=("P_dc_kW", "P_ac_kW", "perdida_T_kW", "clipping_kW"),
    )["annual_8760"]

    # ── DataFrame mensual ─────────────────────────────────────────────────────
    meses_es = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
    df_m = (df_h[["P_dc_kW","P_ac_kW","perdida_T_kW","clipping_kW"]]
            .resample("ME").sum()
            .rename(columns={
                "P_dc_kW":      "E_dc (kWh)",
                "P_ac_kW":      "E_ac (kWh)",
                "perdida_T_kW": "Pérdida T° (kWh)",
                "clipping_kW":  "Recorte inversor (kWh)",
            }))
    df_m["Producción (kWh/kWp)"] = df_m["E_ac (kWh)"] / P_dc_stc_kW if P_dc_stc_kW > 0 else 0
    df_m.index = [meses_es[m] for m in df_m.index.month]

    return {
        "E_dc_anual_kWh":          round(E_dc_anual, 0),
        "E_ac_anual_kWh":          round(E_ac_anual, 0),
        "P_stc_kW":                round(P_dc_stc_kW, 3),
        "Y_f":                     round(Y_f, 0),
        "Y_r":                     round(Y_r, 0),
        "Y_r_es_bruta_real":       Y_r_es_bruta_real,
        "Y_a":                     round(Y_a, 0),
        "PR":                      round(PR, 3),
        "CF_pct":                  round(CF * 100, 1),
        "perdida_temp_kWh":        round(perdida_temp_kWh, 0),
        "perdida_inv_kWh":         round(perdida_inv_kWh, 0),
        "perdida_clipping_kWh":    round(perdida_clipping_kWh, 0),
        "horas_con_clipping":      horas_con_clipping,
        "factor_espectral_aplicado":  factor_espectral_aplicado,
        "factor_espectral_promedio":  factor_espectral_promedio,
        "E_ac_sin_recorte_kWh":    round(E_ac_sin_recorte_anual, 0),
        "E_dc_antes_binning_ohmico_kWh": round(E_dc_antes_binning_ohmico_kWh, 0),
        "pct_mismatch_fab_aplicado":     pct_mismatch_fab_aplicado,
        "perdida_mismatch_fab_kWh":      perdida_mismatch_fab_kWh,
        "perdida_ohmica_dc_kWh":         perdida_ohmica_dc_kWh,
        "perdida_ohmica_dc_modo":        perdida_ohmica_dc_modo,
        "E_ac_antes_ohmico_ac_kWh":      round(E_ac_antes_ohmico_ac_kWh, 0),
        "perdida_ohmica_ac_kWh":         perdida_ohmica_ac_kWh,
        "perdida_ohmica_ac_modo":        perdida_ohmica_ac_modo,
        # Mismo campo que calculos.produccion.simular_produccion_anual() --
        # ver ahí el comentario completo. E_dc con G_eff real, T_cel=25°C fija.
        "E_dc_a_T25_kWh":          round(float(pmp_stc_g.sum()) * N_paneles / 1000.0, 0),
        "H_i_kWh_m2":              round(H_i, 1),
        "H_ef_kWh_m2":             round(H_ef, 1),
        "df_horario":              df_h,
        "df_mensual":              df_m,
        "annual_8760":             anual_8760,
        "critical_dates":          None,
        "uso_modelo_simplificado": False,
        "metodo":                  "curva_iv",
        "sdm_origen":              _sdm_origen,   # "calibrado" | "estimado_ficha" (#105)
    }
