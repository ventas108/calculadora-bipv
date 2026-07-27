"""
Base de datos de ciudades colombianas con datos solares validados.
Fuente: IDEAM / UPME / PVGIS.
"""

CIUDADES = {
    "Bogotá": {
        "lat": 4.711, "lon": -74.072, "alt_m": 2600,
        "GHI_kWh_m2_dia": 4.5, "HSP": 4.5,
        "T_amb_media": 14.0, "T_min_diseno": -5.0,
        "T_cel_realista": 36.35, "T_cel_extremo": 41.94,
        "region": "Andina", "CREG_zona": "Centro",
    },
    "Medellín": {
        "lat": 6.244, "lon": -75.574, "alt_m": 1495,
        "GHI_kWh_m2_dia": 4.8, "HSP": 4.8,
        "T_amb_media": 22.0, "T_min_diseno": 10.0,
        "T_cel_realista": 45.0, "T_cel_extremo": 52.0,
        "region": "Andina", "CREG_zona": "Antioquia",
    },
    "Cali": {
        "lat": 3.437, "lon": -76.522, "alt_m": 1000,
        "GHI_kWh_m2_dia": 4.6, "HSP": 4.6,
        "T_amb_media": 24.0, "T_min_diseno": 12.0,
        "T_cel_realista": 47.0, "T_cel_extremo": 55.0,
        "region": "Andina", "CREG_zona": "Valle",
    },
    "Barranquilla": {
        "lat": 10.964, "lon": -74.796, "alt_m": 18,
        "GHI_kWh_m2_dia": 5.5, "HSP": 5.5,
        "T_amb_media": 28.0, "T_min_diseno": 20.0,
        "T_cel_realista": 55.0, "T_cel_extremo": 65.0,
        "region": "Caribe", "CREG_zona": "Costa",
    },
    "Cartagena": {
        "lat": 10.391, "lon": -75.479, "alt_m": 2,
        "GHI_kWh_m2_dia": 5.4, "HSP": 5.4,
        "T_amb_media": 28.5, "T_min_diseno": 20.0,
        "T_cel_realista": 56.0, "T_cel_extremo": 66.0,
        "region": "Caribe", "CREG_zona": "Costa",
    },
    "Bucaramanga": {
        "lat": 7.119, "lon": -73.123, "alt_m": 959,
        "GHI_kWh_m2_dia": 4.9, "HSP": 4.9,
        "T_amb_media": 26.0, "T_min_diseno": 15.0,
        "T_cel_realista": 50.0, "T_cel_extremo": 58.0,
        "region": "Andina", "CREG_zona": "Santander",
    },
    "Pereira": {
        "lat": 4.814, "lon": -75.696, "alt_m": 1411,
        "GHI_kWh_m2_dia": 4.4, "HSP": 4.4,
        "T_amb_media": 21.0, "T_min_diseno": 8.0,
        "T_cel_realista": 43.0, "T_cel_extremo": 50.0,
        "region": "Andina", "CREG_zona": "Eje Cafetero",
    },
    "Manizales": {
        "lat": 5.070, "lon": -75.513, "alt_m": 2153,
        "GHI_kWh_m2_dia": 4.2, "HSP": 4.2,
        "T_amb_media": 17.0, "T_min_diseno": 2.0,
        "T_cel_realista": 38.0, "T_cel_extremo": 45.0,
        "region": "Andina", "CREG_zona": "Eje Cafetero",
    },
    "Santa Marta": {
        "lat": 11.240, "lon": -74.199, "alt_m": 15,
        "GHI_kWh_m2_dia": 5.6, "HSP": 5.6,
        "T_amb_media": 29.0, "T_min_diseno": 22.0,
        "T_cel_realista": 57.0, "T_cel_extremo": 67.0,
        "region": "Caribe", "CREG_zona": "Costa",
    },
    "Ibagué": {
        "lat": 4.438, "lon": -75.232, "alt_m": 1285,
        "GHI_kWh_m2_dia": 4.7, "HSP": 4.7,
        "T_amb_media": 23.0, "T_min_diseno": 10.0,
        "T_cel_realista": 46.0, "T_cel_extremo": 53.0,
        "region": "Andina", "CREG_zona": "Tolima",
    },
    "Villavicencio": {
        "lat": 4.142, "lon": -73.626, "alt_m": 467,
        "GHI_kWh_m2_dia": 5.1, "HSP": 5.1,
        "T_amb_media": 27.0, "T_min_diseno": 18.0,
        "T_cel_realista": 52.0, "T_cel_extremo": 61.0,
        "region": "Llanos", "CREG_zona": "Meta",
    },
    "Pasto": {
        "lat": 1.215, "lon": -77.281, "alt_m": 2527,
        "GHI_kWh_m2_dia": 4.0, "HSP": 4.0,
        "T_amb_media": 13.0, "T_min_diseno": -2.0,
        "T_cel_realista": 34.0, "T_cel_extremo": 40.0,
        "region": "Andina", "CREG_zona": "Sur",
    },
}

# Ley 1715 de 2014 — beneficios Colombia
LEY_1715 = {
    "deduccion_renta_pct":        50,     # % — deducción renta sobre inversión
    "depreciacion_acelerada_anos": 5,     # años
    "exencion_iva":               True,
    "exencion_arancel":           True,
    "potencia_maxima_autoconsumo_kW": 1000,
}

# Factor CO₂ — Sistema Interconectado Nacional (SIN) Colombia
FACTOR_CO2_COLOMBIA_KG_KWH = 0.126

# Tasa de descuento recomendada Colombia
TASA_DESCUENTO_COLOMBIA = 0.12  # 12% anual

LISTA_CIUDADES = sorted(CIUDADES.keys())
