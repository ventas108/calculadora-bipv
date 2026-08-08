"""
Claves de session_state que caducan en cadena (#64 / #172).

Única fuente de verdad para invalidar resultados derivados cuando cambian las
entradas aguas arriba:

- Cambian las COORDENADAS del predio  → caduca TODO (TMY + POA + derivados).
- Cambia la GEOMETRÍA (tilt/azimuth/albedo) → el TMY del sitio sigue válido,
  pero caducan la POA y todos los derivados.
- Cambia el ÁREA o el TIPO de instalación → caducan producción, bypass,
  financiero y CO₂ (el recurso solar sigue válido; el nº de paneles no).

Sin esta limpieza, Financiero/Reporte leen E_ac_anual_kWh directamente y
entregarían TIR/payback calculados con el sol o la geometría de otro escenario.
"""

# ── Derivados de la POA: producción y todo lo que cuelga de ella ─────────────
KEYS_DERIVADOS_POA = (
    # Motor Óptico (Página 5b) — estado, parámetros y POA corregidas
    # poa_efectiva_df    : POA tras IAM + soiling + térmico (visualización / Financiero)
    # poa_sin_termico_df : POA tras IAM + soiling SIN térmico (G_eff del SDM)
    # Ambas deben invalidarse juntas para evitar que Producción use la POA
    # antigua cuando cambian coordenadas o geometría.
    "motor_optico_ok",
    "motor_optico_result_df",
    "motor_optico_summary",
    "poa_efectiva_df",
    "poa_sin_termico_df",
    "poa_efectiva_anual_kWh_m2",
    "motor_optico_b0",
    "motor_optico_tau",
    "motor_optico_k_bipv",
    "motor_optico_noct",
    "motor_optico_coef_temp",
    "motor_optico_f_iam_dif",
    "motor_optico_k_soil_vert",
    # Producción (Página 6)
    "produccion_ok", "produccion_modo_iv", "E_ac_anual_kWh", "PR_sistema",
    "res_produccion", "res_produccion_base", "res_produccion_iv",
    # Bypass — resultados y flags (Página 5); si quedan vivos, Producción
    # re-aplica sombras viejas a la producción nueva
    "E_ac_anual_kWh_bypass",
    "bypass_ok", "bypass_result", "bypass_p_shade",
    "bypass_n_series_usado", "bypass_n_parallel_usado", "bypass_panel_usado",
    "kwh_bypass_anual",
    "bypass_modo_usado", "bypass_multisup_ok", "bypass_multisup_resultados",
    # Multi-superficie (Página 9)
    "E_ac_anual_kWh_multisup", "poa_df_multisup",
    "area_total_multisup", "multisup_desglose", "multisup_activo",
    # Financiero cacheado (Página 7)
    "financiero_ok", "comp_financiero", "comp_financiero_p90",
    "metricas_financiero", "metricas_financiero_p90",
    # Impacto CO₂ (Página 12)
    "impacto_co2_ok", "co2_anual_t", "co2_total_t", "co2_total_prom_t",
    "co2_total_marg_t", "co2_arboles_equiv", "co2_hogares_equiv",
    "co2_km_vehiculo_equiv", "co2_valor_bonos_usd",
)

# ── Recurso solar (Página 2) — POA y agregados; SIN tmy_df ───────────────────
KEYS_RECURSO_SOLAR_POA = (
    "recurso_solar_ok", "poa_df", "poa_anual_kWh_m2",
    "ganancia_bifacial_pct",
)

# ── Recurso solar completo — incluye el TMY del sitio ────────────────────────
KEYS_RECURSO_SOLAR = KEYS_RECURSO_SOLAR_POA + (
    "tmy_df", "tmy_ciudad", "ghi_anual_kWh_m2", "t_media_anual",
    "zona_geo_coords",
)
