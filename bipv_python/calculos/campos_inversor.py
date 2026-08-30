"""
campos_inversor.py — Definición compartida de los campos del extractor de inversores.

Fuente única de verdad para las páginas de producción (15, 16), el extractor
(calculos/pdf_inversor_extractor.py) y el harness de pruebas
(scripts/casos_test_inversores.py). Antes vivían en el harness, lo que hacía que
las páginas de producción dependieran de un módulo de pruebas (#155).
"""

# Campos que el harness verifica en cada caso (incluye opcionales como batería)
CAMPOS_CRITICOS = [
    "Vdc_max", "Vmppt_min", "Vmppt_max", "V_mppt_activo",
    "V_arranque", "n_trackers", "n_strings_tracker",
    "I_max_tracker", "Isc_max_tracker", "P_dc_max_W",
    "bat_voltaje_min", "bat_voltaje_max", "bat_corriente_carga_max",
]

# Subconjunto imprescindible para dimensionar: si varios de estos quedan en None,
# la extracción probablemente falló en silencio (alerta #139 en la UI).
CAMPOS_CRITICOS_INVERSOR = [
    "Vdc_max", "Vmppt_min", "Vmppt_max", "V_arranque",
    "n_trackers", "n_strings_tracker",
    "I_max_tracker", "Isc_max_tracker", "P_dc_max_W",
]

# Etiquetas legibles para la UI
CAMPO_LABELS = {
    "Vdc_max":           "Vdc máx (V)",
    "Vmppt_min":         "MPPT mín (V)",
    "Vmppt_max":         "MPPT máx (V)",
    "V_mppt_activo":     "MPPT activo (V)",
    "V_arranque":        "V arranque (V)",
    "n_trackers":        "N trackers",
    "n_strings_tracker": "Strings/tracker",
    "I_max_tracker":     "I máx (A)",
    "Isc_max_tracker":   "Isc máx (A)",
    "P_dc_max_W":        "P FV máx (W)",
    "bat_voltaje_min":   "Bat mín (V)",
    "bat_voltaje_max":   "Bat máx (V)",
    "bat_corriente_carga_max": "I carga batería máx (A)",
}
