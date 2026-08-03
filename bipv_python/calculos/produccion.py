"""
Módulo de producción anual BIPV — IEC 61724.

Simula la energía hora a hora aplicando:
  1. SDM De Soto 2006 vectorizado  (pvlib + Rsh CdTe Mermoud 2005)
  2. Factor de pérdidas ópticas/eléctricas de la cascada Mismatch
  3. Temperatura de celda NOCT hora a hora
  4. Curva de eficiencia del inversor

Métricas de salida (IEC 61724):
  Y_f  — Final yield    (kWh/kWp)
  Y_r  — Reference yield (kWh/m² / kW/m² = h)
  Y_a  — Array yield    (kWh/kWp)
  PR   — Performance Ratio = Y_f / Y_r
  CF   — Capacity Factor (%)
"""

import numpy as np
import pandas as pd
import pvlib

from calculos.modelo_iv import obtener_constantes_tecnologia
from calculos.temperatura import temperatura_celda_noct

# ── Constantes físicas (mismas que modelo_iv.py) ──────────────────────────────
K_BOLTZMANN = 1.380649e-23
Q_ELECTRON  = 1.602176634e-19
T_REF_K     = 298.15
G_REF       = 1000.0


# ── Parámetros SDM mínimos requeridos para el modelo De Soto completo ─────────
_SDM_PARAMS_REQUERIDOS = ("I_L_ref", "I_o_ref", "R_s", "R_sh_ref", "a_ref")


def panel_tiene_sdm_completo(panel: dict) -> bool:
    """Retorna True si el panel tiene todos los parámetros SDM para De Soto 2006."""
    return all(
        panel.get(p) is not None and float(panel.get(p)) != 0.0
        for p in _SDM_PARAMS_REQUERIDOS
    )


def _calcular_pmax_vectorizado(
    G: np.ndarray,
    T_cel: np.ndarray,
    panel: dict,
) -> np.ndarray:
    """
    Calcula Pmax (W) por módulo hora a hora usando SDM De Soto 2006 vectorizado.
    Utiliza el modelo Rsh exponencial CdTe (Mermoud 2005) en lugar del lineal de pvlib.

    G     : irradiancia efectiva en el plano (W/m²) — array 1D
    T_cel : temperatura de celda (°C) — array 1D
    panel : dict con parámetros SDM del catálogo

    Retorna: array 1D de Pmax (W) por módulo
    """
    # ── Fallback para paneles sin parámetros SDM completos ───────────────────
    # (paneles del catálogo Excel que no tienen a_ref, I_L_ref, etc.)
    if not panel_tiene_sdm_completo(panel):
        gamma = float(panel.get("Tk_gamma", -0.45)) / 100.0   # %/°C → 1/°C
        pmax_stc = float(panel.get("Pmax_stc", 0))
        pmax = pmax_stc * np.where(G > 5.0, G / 1000.0, 0.0) * (1.0 + gamma * (T_cel - 25.0))
        pmax = np.maximum(pmax, 0.0)
        return pmax

    constantes = obtener_constantes_tecnologia(panel["tecnologia"])

    # nNsVth_ref en Voltios (pvlib convention)
    Vt_ref     = K_BOLTZMANN * T_REF_K / Q_ELECTRON   # 0.025693 V
    nNsVth_ref = panel["a_ref"] * Vt_ref               # 154 × Vt_ref

    # R_sh CdTe exponencial vectorizado
    G_safe = np.where(G > 0, G, 1.0)
    R_sh   = (panel["R_sh_ref"] * np.exp(-constantes["c_Rsh"] * (G_safe / G_REF - 1.0))
              + panel.get("R_sh_base", 0.0))

    I_L, I_o, R_s, _rsh_pvlib, nNsVth = pvlib.pvsystem.calcparams_desoto(
        effective_irradiance = G,
        temp_cell            = T_cel,
        alpha_sc             = panel["Tk_alfa"] / 100.0 * float(panel.get("Isc_stc") or panel.get("Isc") or 1.0),
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

    pmax = np.array(resultado["p_mp"], dtype=float)
    pmax[G < 5.0] = 0.0     # sin producción nocturna / irradiancia mínima
    pmax[pmax < 0] = 0.0    # seguridad numérica
    return pmax


def simular_produccion_anual(
    tmy: pd.DataFrame,
    poa_base: pd.DataFrame,
    panel: dict,
    N_paneles: int,
    eta_inversor: float,
    factor_pr_mismatch: float,
    P_dc_stc_kW: float | None = None,
) -> dict:
    """
    Simulación de producción anual hora a hora — IEC 61724.

    Parámetros
    ----------
    tmy                 : DataFrame TMY con columna 'T2m' (°C)
    poa_base            : DataFrame POA bruta con columna 'poa_global' (W/m²)
    panel               : dict del catálogo MODULOS_BIPV
    N_paneles           : número de módulos del sistema
    eta_inversor        : eficiencia del inversor (0.90–0.99)
    factor_pr_mismatch  : factor de pérdidas cascada (0–1)
                          = poa_efectiva / poa_bruta  (de página Mismatch)
    P_dc_stc_kW         : potencia pico instalada kWp; si None → N_paneles × Pmax_stc

    Retorna dict
    ────────────
    E_dc_anual_kWh    : energía DC anual (kWh)
    E_ac_anual_kWh    : energía AC anual (kWh)
    P_stc_kW          : potencia instalada (kWp)
    Y_f               : Final yield (kWh/kWp)
    Y_r               : Reference yield (h = kWh/m²)
    Y_a               : Array yield (kWh/kWp)
    PR                : Performance Ratio IEC 61724
    CF_pct            : Capacity Factor (%)
    perdida_temp_kWh  : energía perdida por temperatura
    perdida_inv_kWh   : energía perdida en inversor
    df_horario        : DataFrame horario (G_eff, T_cel, Pmax, P_dc, P_ac)
    df_mensual        : DataFrame mensual con E_dc, E_ac, kWh/kWp
    """
    if P_dc_stc_kW is None:
        P_dc_stc_kW = round(panel.get("Pmax_stc", 60) * N_paneles / 1000, 3)

    # ── Alinear índices ────────────────────────────────────────────────────────
    idx   = poa_base.index.intersection(tmy.index)
    G_raw = poa_base.loc[idx, "poa_global"].values.astype(float)
    T_amb = tmy.loc[idx, "T2m"].values.astype(float)

    # ── Irradiancia efectiva (cascada mismatch aplicada) ──────────────────────
    G_eff = np.clip(G_raw * factor_pr_mismatch, 0, None)

    # ── Temperatura de celda hora a hora (modelo NOCT) ────────────────────────
    try:
        NOCT = float(panel.get("NOCT") or 45.0)
        if not (20.0 < NOCT < 100.0):
            NOCT = 45.0
    except (TypeError, ValueError):
        NOCT = 45.0
    T_cel = T_amb + (NOCT - 20.0) / 800.0 * G_eff

    # ── SDM vectorizado — Pmax por módulo ─────────────────────────────────────
    pmax_mod = _calcular_pmax_vectorizado(G_eff, T_cel, panel)

    # ── Pérdida por temperatura (referencia: Pmax a T=25°C con mismo G_eff) ───
    T_ref_arr = np.full_like(T_cel, 25.0)
    pmax_stc_g = _calcular_pmax_vectorizado(G_eff, T_ref_arr, panel)
    perdida_temp_por_modulo = np.maximum(pmax_stc_g - pmax_mod, 0.0)

    # ── Escalar al sistema ─────────────────────────────────────────────────────
    P_dc_W  = pmax_mod * N_paneles
    P_ac_W  = P_dc_W * eta_inversor

    # ── Energías anuales (Wh → kWh) ───────────────────────────────────────────
    E_dc_anual  = float(P_dc_W.sum()) / 1000.0
    E_ac_anual  = float(P_ac_W.sum()) / 1000.0
    perdida_temp_kWh = float(perdida_temp_por_modulo.sum()) * N_paneles / 1000.0
    perdida_inv_kWh  = E_dc_anual - E_ac_anual

    # ── Métricas IEC 61724 ────────────────────────────────────────────────────
    H_i  = float(G_raw.sum()) / 1000.0          # POA bruta kWh/m²
    H_ef = float(G_eff.sum()) / 1000.0          # POA efectiva kWh/m² (post-mismatch)
    Y_r  = H_i                                   # Reference yield [h] = H_t / G_STC (IEC 61724)
    # NOTA: Y_r usa POA bruta (H_i), no H_ef, para que el PR incluya las pérdidas
    # de mismatch como una pérdida real (PR más conservador y correcto según IEC 61724).
    Y_a  = E_dc_anual  / P_dc_stc_kW if P_dc_stc_kW > 0 else 0.0   # Array yield
    Y_f  = E_ac_anual  / P_dc_stc_kW if P_dc_stc_kW > 0 else 0.0   # Final yield
    PR   = Y_f / Y_r   if Y_r > 0    else 0.0   # Performance Ratio
    CF   = E_ac_anual  / (P_dc_stc_kW * 8760) if P_dc_stc_kW > 0 else 0.0

    # ── DataFrame horario ─────────────────────────────────────────────────────
    df_h = pd.DataFrame({
        "G_eff_Wm2":    G_eff,
        "T_cel_C":      T_cel,
        "Pmax_mod_W":   pmax_mod,
        "P_dc_kW":      P_dc_W  / 1000.0,
        "P_ac_kW":      P_ac_W  / 1000.0,
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
        "E_dc_anual_kWh":         round(E_dc_anual, 0),
        "E_ac_anual_kWh":         round(E_ac_anual, 0),
        "P_stc_kW":               round(P_dc_stc_kW, 3),
        "Y_f":                    round(Y_f, 0),
        "Y_r":                    round(Y_r, 0),
        "Y_a":                    round(Y_a, 0),
        "PR":                     round(PR, 3),
        "CF_pct":                 round(CF * 100, 1),
        "perdida_temp_kWh":       round(perdida_temp_kWh, 0),
        "perdida_inv_kWh":        round(perdida_inv_kWh, 0),
        "H_i_kWh_m2":             round(H_i, 1),
        "H_ef_kWh_m2":            round(H_ef, 1),
        "df_horario":             df_h,
        "df_mensual":             df_m,
        "uso_modelo_simplificado": not panel_tiene_sdm_completo(panel),
    }


def perdidas_desglosadas(res: dict, poa_bruta_kWh_m2: float) -> pd.DataFrame:
    """
    Tabla de balance energético IEC 61724.

    Para climas fríos de alta altitud (Bogotá, Medellín) el SDM puede producir
    MÁS que la referencia STC porque los módulos operan por debajo de 25°C.
    En ese caso el 'delta SDM' es positivo (ganancia, no pérdida).
    """
    P_stc  = res["P_stc_kW"]
    ref_dc = P_stc * poa_bruta_kWh_m2   # kWh teóricos a STC (Pmax_nom × POA)
    if ref_dc == 0:
        return pd.DataFrame()

    delta_sdm = res["E_dc_anual_kWh"] - ref_dc          # positivo = ganancia temperatura
    delta_t   = -res["perdida_temp_kWh"]                 # horas T > 25 °C (siempre ≤ 0)
    delta_inv = -res["perdida_inv_kWh"]                  # pérdida inversor (siempre ≤ 0)

    def _signo(v):
        return f"+{v:,.0f}" if v >= 0 else f"{v:,.0f}"

    filas = [
        {
            "Etapa":     "① E ref  (P_STC × POA bruta)",
            "kWh":       round(ref_dc, 0),
            "Δ kWh":     0,
            "Nota":      "Baseline a condiciones STC",
        },
        {
            "Etapa":     "② Efecto SDM  (T° + baja irradiancia)",
            "kWh":       round(res["E_dc_anual_kWh"], 0),
            "Δ kWh":     round(delta_sdm, 0),
            "Nota":      ("🟢 Ganancia por T_cel < 25°C (clima frío / alta altitud)"
                          if delta_sdm >= 0
                          else "🔴 Pérdida óptica + temperatura"),
        },
        {
            # Fila informativa: desglosa la componente térmica pura del efecto SDM de fila ②
            # NO es un paso acumulado — la kWh muestra E_dc (mismo que fila ②)
            "Etapa":     "   ↳ Componente T° horas calientes  (T_cel > 25°C)",
            "kWh":       round(res["E_dc_anual_kWh"], 0),
            "Δ kWh":     round(delta_t, 0),
            "Nota":      f"Sub-componente de ②  ·  Tk_gamma={res.get('Tk_gamma_pct','—')}%/°C",
        },
        {
            "Etapa":     "③ E_dc  (salida del array)",
            "kWh":       round(res["E_dc_anual_kWh"], 0),
            "Δ kWh":     0,
            "Nota":      "",
        },
        {
            "Etapa":     "④ Pérdida inversor",
            "kWh":       round(res["E_ac_anual_kWh"], 0),
            "Δ kWh":     round(delta_inv, 0),
            "Nota":      f"η_inv = {round(res['E_ac_anual_kWh'] / res['E_dc_anual_kWh'] * 100, 1) if res['E_dc_anual_kWh'] > 0 else '—'}%",
        },
        {
            "Etapa":     "⑤ E_ac  (energía a la red / edificio)",
            "kWh":       round(res["E_ac_anual_kWh"], 0),
            "Δ kWh":     0,
            "Nota":      "",
        },
    ]
    df = pd.DataFrame(filas)
    df["% de E_ref"] = (df["Δ kWh"].abs() / ref_dc * 100).round(2)
    return df
