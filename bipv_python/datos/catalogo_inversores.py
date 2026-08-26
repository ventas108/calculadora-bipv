"""
Catálogo de inversores — extraído del XLSM auditado.
Parámetros verificados contra fichas técnicas oficiales.
"""

INVERSORES = {
    # ── PROYECTO ACTUAL (Teusaquillo, Bogotá) ──────────────────────────────
    "Growatt-MID15KTL3-X": {
        "fabricante":          "Growatt",
        "modelo":              "MID15KTL3-X",
        "fuente":              "Ficha_Tecnica_Inversores_GROWATT_MID15_25KTL3X.docx",
        "Vdc_max":             1100,    # V — tensión DC máxima absoluta
        "Voc_arranque":         250,    # V — tensión de arranque
        "Vmppt_min":            200,    # V — rango MPPT mínimo
        "Vmppt_max":           1000,    # V — rango MPPT máximo
        "Vmppt_activo_min":     580,    # V — tensión mínima MPPT activo ← CRÍTICO
        "N_mppt":                 2,    # — trackers MPPT
        "N_strings_nativo":       2,    # — strings por tracker
        "I_max_tracker":         27,    # A — corriente máxima por tracker
        "Isc_max_tracker":       33.8,  # A — Isc máxima por tracker
        "P_dc_max_W":          22500,   # W — potencia FV máxima recomendada
        "P_ac_nom_W":          15000,   # W — potencia AC nominal
        "eficiencia_max":       0.985,
    },
    "Huawei-SUN2000-15KTL": {
        "fabricante": "Huawei", "modelo": "SUN2000-15KTL-M0",
        "Vdc_max": 1100, "Vmppt_min": 200, "Vmppt_max": 1000,
        "Vmppt_activo_min": 600, "N_mppt": 2, "N_strings_nativo": 2,
        "I_max_tracker": 26, "Isc_max_tracker": 32.5,
        "P_dc_max_W": 20000, "P_ac_nom_W": 15000, "eficiencia_max": 0.987,
    },
    "Fronius-Primo-15": {
        "fabricante": "Fronius", "modelo": "Primo 15.0-1",
        "Vdc_max": 1000, "Vmppt_min": 200, "Vmppt_max": 800,
        "Vmppt_activo_min": 200, "N_mppt": 2, "N_strings_nativo": 2,
        "I_max_tracker": 27, "Isc_max_tracker": 33.0,
        "P_dc_max_W": 20000, "P_ac_nom_W": 15000, "eficiencia_max": 0.986,
    },
    "SMA-STP15000TL": {
        "fabricante": "SMA", "modelo": "STP 15000TL-30",
        "Vdc_max": 1000, "Vmppt_min": 175, "Vmppt_max": 800,
        "Vmppt_activo_min": 175, "N_mppt": 2, "N_strings_nativo": 3,
        "I_max_tracker": 30, "Isc_max_tracker": 36.0,
        "P_dc_max_W": 20000, "P_ac_nom_W": 15000, "eficiencia_max": 0.987,
    },
    # ── INVERSORES PARA GRANJA FOTOVOLTAICA (sistema 1500 V) ──────────────────
    "Growatt-MAX-100KTL3-LV": {
        "fabricante":         "Growatt",
        "modelo":             "MAX 100KTL3 LV",
        "fuente":             "Ficha técnica Growatt MAX 100KTL3 LV",
        "Vdc_max":            1500,   # V — tensión DC máxima
        "Voc_arranque":        200,   # V — tensión de arranque
        "Vmppt_min":           200,   # V — rango MPPT mínimo
        "Vmppt_max":          1300,   # V — rango MPPT máximo
        "Vmppt_activo_min":    850,   # V — punto MPPT activo mínimo típico
        "N_mppt":               10,   # — trackers MPPT
        "N_strings_nativo":      2,   # — strings por tracker (nativo)
        "I_max_tracker":        26,   # A — corriente máxima por tracker
        "Isc_max_tracker":      32.5, # A — Isc máxima por tracker
        "P_dc_max_W":       130000,   # W — potencia FV máxima
        "P_ac_nom_W":       100000,   # W — potencia AC nominal
        "P_ac_max_VA":      110000,   # VA — potencia AC máxima (sobrecarga)
        # Lado AC (26-ago-2026) -- verificado contra growatt.tech y
        # pretapower.com para "MAX 100KTL3-X LV": no había datos AC en el
        # catálogo hasta ahora. Aún no lo usa ningún validador (el motor de
        # producción/dimensionamiento no tiene capa de verificación AC).
        "Vac_nom":             400,   # V — tensión AC nominal trifásica (también opera a 380 V)
        "Vac_min":             340,   # V — rango de tensión AC mínimo
        "Vac_max":             440,   # V — rango de tensión AC máximo
        "I_ac_max_A":        158.8,   # A — corriente AC máxima @400V (167.1 A @380V)
        "frecuencia_hz":  (50, 60),   # Hz — frecuencias de red soportadas
        # eficiencia_max corregida 0.990→0.988 (26-ago-2026): el valor previo
        # no coincidía con la ficha oficial verificada (98.8%, no 99.0%).
        # eta_inversor (optimization/scenario_generator.py) se sincroniza
        # directo con este campo, así que la corrección SÍ cambia los kWh AC
        # estimados para este inversor (~0.2% menos que antes).
        "eficiencia_max":    0.988,
    },
    "Huawei-SUN2000-100KTL-M1": {
        "fabricante":         "Huawei",
        "modelo":             "SUN2000-100KTL-M1",
        "fuente":             "Ficha técnica Huawei SUN2000-100KTL-M1",
        "Vdc_max":            1500,
        "Voc_arranque":        200,
        "Vmppt_min":           200,
        "Vmppt_max":          1500,
        "Vmppt_activo_min":    780,   # V — MPPT activo mínimo
        "N_mppt":               12,
        "N_strings_nativo":      2,
        "I_max_tracker":        26,
        "Isc_max_tracker":      32.5,
        "P_dc_max_W":       135000,
        "P_ac_nom_W":       100000,
        "eficiencia_max":    0.990,
    },
    "Sungrow-SG110CX": {
        "fabricante":         "Sungrow",
        "modelo":             "SG110CX",
        "fuente":             "Ficha técnica Sungrow SG110CX",
        "Vdc_max":            1500,
        "Voc_arranque":        200,
        "Vmppt_min":           200,
        "Vmppt_max":          1500,
        "Vmppt_activo_min":    850,
        "N_mppt":               12,
        "N_strings_nativo":      2,
        "I_max_tracker":        26,
        "Isc_max_tracker":      32.5,
        "P_dc_max_W":       148500,
        "P_ac_nom_W":       110000,
        "eficiencia_max":    0.990,
    },
}


def seleccionar_inversor(nombre: str) -> dict:
    if nombre not in INVERSORES:
        raise KeyError(
            f"Inversor '{nombre}' no encontrado. "
            f"Disponibles: {list(INVERSORES.keys())}"
        )
    return INVERSORES[nombre]
