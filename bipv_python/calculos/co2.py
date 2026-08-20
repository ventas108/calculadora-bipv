"""
Módulo de huella de carbono evitada — BIPV Colombia.

Extraído de pages/12_🌿_Impacto_CO2.py (auditoría Fase 1, cuello de
botella #4: la página no tenía módulo propio en calculos/, todo el
cálculo vivía inline mezclado con Streamlit). Funciones puras — no tocan
Streamlit ni session_state.

Estándares aplicados (ver también la página, que conserva las citas
completas para el usuario):
  GHG Protocol Scope 2 · ISO 14064-1 · UNFCCC CDM AMS-I.D ·
  IPCC AR6 WG III · Ley 1931/2018 · NDC Colombia 2030 · XM/UPME · IDEAM.
"""
import numpy as np

# ── Factor marginal combinado (CDM) — el promedio SIN Colombia vive en
# datos/ciudades_colombia.py::FACTOR_CO2_COLOMBIA_KG_KWH y es override-able
# por el usuario en la página, así que se pasa como parámetro aquí. ────────
FACTOR_MARGINAL_KG_KWH = 0.300   # kg/kWh — OM≈0.25, BM≈0.35 → CM=(OM+BM)/2
                                  # Fuente: UNFCCC CDM Tool 07 — Combined margin

# ── Equivalencias de impacto — Colombia ──────────────────────────────────
KG_CO2_ARBOL_ANUAL     = 22.0     # kg CO₂/árbol/año — IDEAM 2010 (Bosque Húmedo)
KWH_HOGAR_ANUAL         = 1_560.0  # kWh/año — UPME 2022 (130 kWh/mes residencial)
KG_CO2_KM_VEHICULO      = 0.162    # kgCO₂/km — IDEAM FECOC 2022 (auto gasolina)
KG_CO2_VUELO_BOG_MDE    = 89.0     # kg CO₂/pasajero/vuelo ida — ICAO 2023
KG_CO2_BARRIL_PETROLEO  = 431.7    # kgCO₂/barril — EPA AP-42 (API 31°)
KG_CO2_CILINDRO_GLP     = 55.6     # kgCO₂/cilindro 40 lb — IPCC 2006 Vol.2 cap.1

# ── Intensidades carbono por tecnología — IPCC AR6 WG III Tabla A.III.2 ──
INTENSIDAD_IPCC = {
    "Carbón (subcrítico)":     820,
    "Carbón (ultrasupercrítico)": 670,
    "Gas natural ciclo abierto":  490,
    "Gas natural ciclo combinado": 410,
    "Fuel oil / Diesel":       650,
    "Solar PV suelo (c-Si)":    24,
    "Solar BIPV fachada":       30,     # +25% vs PV suelo por vidrio laminado y soporte
    "Eólica terrestre":         7,
    "Hidroeléctrica":           24,
    "Nuclear":                  12,
    "Geotérmica":               38,
    "Biomasa":                  230,    # promedio, varía mucho
}

# ── NDC Colombia 2030 ─────────────────────────────────────────────────────
META_NDC_TOTAL_MT  = 169.0   # Mt CO₂eq total Colombia 2030
META_SECTOR_MT     = 59.0    # Mt CO₂eq sector energía (≈35% del total)
EMIS_NAL_MT_ANIO   = 258.0   # Mt CO₂eq/año Colombia (IDEAM BUR4 2023)


def produccion_anual_con_degradacion(e_ac: float, tasa_deg_pct: float, n_anos: int = 25):
    """Producción año a año con degradación geométrica anual.

    Retorna (anos_array, e_ac_anual) — kWh/año para cada año 1..n_anos.
    """
    anos_array = np.arange(1, n_anos + 1)
    e_ac_anual = e_ac * (1 - tasa_deg_pct / 100) ** (anos_array - 1)
    return anos_array, e_ac_anual


def emisiones_evitadas(e_ac, e_ac_anual, factor_activo, factor_promedio, factor_marginal):
    """CO₂ evitado año 1 y acumulado en vida útil, con los tres factores."""
    co2_anual_kg = e_ac * factor_activo
    co2_anual_t = co2_anual_kg / 1000
    co2_total_t = (e_ac_anual * factor_activo / 1000).sum()
    co2_total_prom_t = (e_ac_anual * factor_promedio / 1000).sum()
    co2_total_marg_t = (e_ac_anual * factor_marginal / 1000).sum()
    intensidad_sistema = factor_activo * 1000   # gCO₂/kWh
    return {
        "co2_anual_kg": co2_anual_kg,
        "co2_anual_t": co2_anual_t,
        "co2_total_t": co2_total_t,
        "co2_total_prom_t": co2_total_prom_t,
        "co2_total_marg_t": co2_total_marg_t,
        "intensidad_sistema": intensidad_sistema,
    }


def valor_bonos_carbono(co2_total_t: float, precio_bono_usd: float, tipo_cambio: float):
    """Retorna (valor_usd, valor_cop)."""
    valor_usd = co2_total_t * precio_bono_usd
    valor_cop = valor_usd * tipo_cambio
    return valor_usd, valor_cop


def equivalencias_impacto(co2_total_t: float, e_ac_total: float, n_anos: int):
    """Equivalencias de impacto para la vida útil del proyecto."""
    return {
        "arboles":       co2_total_t * 1000 / KG_CO2_ARBOL_ANUAL / n_anos,
        "hogares":       e_ac_total / KWH_HOGAR_ANUAL,
        "km_vehiculo":   co2_total_t * 1000 / KG_CO2_KM_VEHICULO / 1000,
        "vuelos_bogmde": co2_total_t * 1000 / KG_CO2_VUELO_BOG_MDE,
        "barriles":      co2_total_t * 1000 / KG_CO2_BARRIL_PETROLEO,
        "cilindros_glp": co2_total_t * 1000 / KG_CO2_CILINDRO_GLP,
    }


def contribucion_ndc(co2_total_t: float, co2_anual_t: float):
    """Retorna (pct_ndc_total, pct_ndc_sector, pct_emis_nac)."""
    pct_ndc_total = co2_total_t / (META_NDC_TOTAL_MT * 1e6) * 100
    pct_ndc_sector = co2_total_t / (META_SECTOR_MT * 1e6) * 100
    pct_emis_nac = co2_anual_t / (EMIS_NAL_MT_ANIO * 1e6) * 100
    return pct_ndc_total, pct_ndc_sector, pct_emis_nac


def cumplimiento_real_vs_proyectado(kwh_real_list, proy_mes, factor_activo: float, e_ac: float):
    """Sección 9 — CO₂ real (inversor) vs proyectado, mes a mes.

    kwh_real_list, proy_mes : listas de 12 valores kWh (Ene..Dic).
    Retorna None si no hay ningún mes con dato real > 0 (nada que comparar).
    """
    meses_con_dato = sum(1 for v in kwh_real_list if v > 0)
    if meses_con_dato == 0:
        return None

    co2_real_mes = [v * factor_activo / 1000 for v in kwh_real_list]
    co2_proy_mes = [v * factor_activo / 1000 for v in proy_mes]
    co2_real_acum = sum(co2_real_mes[:meses_con_dato])
    co2_proy_acum = sum(co2_proy_mes[:meses_con_dato])
    cumpl_pct = (co2_real_acum / co2_proy_acum * 100) if co2_proy_acum > 0 else 0
    delta_co2 = co2_real_acum - co2_proy_acum
    kwh_real_total = sum(kwh_real_list)
    kwh_real_anual_proy = kwh_real_total / meses_con_dato * 12 if meses_con_dato > 0 else 0
    pr_real_pct = (kwh_real_total / (e_ac * meses_con_dato / 12) * 100) if e_ac > 0 else 0

    return {
        "meses_con_dato": meses_con_dato,
        "co2_real_mes": co2_real_mes,
        "co2_proy_mes": co2_proy_mes,
        "co2_real_acum": co2_real_acum,
        "co2_proy_acum": co2_proy_acum,
        "cumpl_pct": cumpl_pct,
        "delta_co2": delta_co2,
        "kwh_real_total": kwh_real_total,
        "kwh_real_anual_proy": kwh_real_anual_proy,
        "pr_real_pct": pr_real_pct,
    }
