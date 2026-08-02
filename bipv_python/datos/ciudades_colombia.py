"""
Base de datos de ciudades colombianas con datos solares validados.
Fuente: IDEAM / UPME / PVGIS.

Tarifas comerciales/industriales (sin subsidio) validadas 2025
por el equipo Innovación Química. Actualizar cuando cambien las
resoluciones CREG o se disponga de facturas más recientes.
"""

# Fecha de la última validación de tarifas — avisa en Proyecto si llevan >6 meses
FECHA_VALIDACION_TARIFAS = "2025-01-01"

CIUDADES = {
    "Bogotá": {
        "lat": 4.711, "lon": -74.072, "alt_m": 2600,
        "GHI_kWh_m2_dia": 4.5, "HSP": 4.5,
        "T_amb_media": 14.0, "T_min_diseno": 5.0,
        "T_cel_realista": 36.35, "T_cel_extremo": 41.94,
        "region": "Andina", "CREG_zona": "Centro",
        "operador": "Codensa",
        "tarifa_comercial_cop_kwh": 1200,
    },
    "Medellín": {
        "lat": 6.244, "lon": -75.574, "alt_m": 1495,
        "GHI_kWh_m2_dia": 4.8, "HSP": 4.8,
        "T_amb_media": 22.0, "T_min_diseno": 10.0,
        "T_cel_realista": 45.0, "T_cel_extremo": 52.0,
        "region": "Andina", "CREG_zona": "Antioquia",
        "operador": "EPM",
        "tarifa_comercial_cop_kwh": 900,
    },
    "Cali": {
        "lat": 3.437, "lon": -76.522, "alt_m": 1000,
        "GHI_kWh_m2_dia": 4.6, "HSP": 4.6,
        "T_amb_media": 24.0, "T_min_diseno": 12.0,
        "T_cel_realista": 47.0, "T_cel_extremo": 55.0,
        "region": "Andina", "CREG_zona": "Valle",
        "operador": "EMCALI",
        "tarifa_comercial_cop_kwh": 850,
    },
    "Barranquilla": {
        "lat": 10.964, "lon": -74.796, "alt_m": 18,
        "GHI_kWh_m2_dia": 5.5, "HSP": 5.5,
        "T_amb_media": 28.0, "T_min_diseno": 20.0,
        "T_cel_realista": 55.0, "T_cel_extremo": 65.0,
        "region": "Caribe", "CREG_zona": "Costa",
        "operador": "Air-e",
        "tarifa_comercial_cop_kwh": 900,
    },
    "Cartagena": {
        "lat": 10.391, "lon": -75.479, "alt_m": 2,
        "GHI_kWh_m2_dia": 5.4, "HSP": 5.4,
        "T_amb_media": 28.5, "T_min_diseno": 20.0,
        "T_cel_realista": 56.0, "T_cel_extremo": 66.0,
        "region": "Caribe", "CREG_zona": "Costa",
        "operador": "Afinia",
        "tarifa_comercial_cop_kwh": 900,
    },
    "Bucaramanga": {
        "lat": 7.119, "lon": -73.123, "alt_m": 959,
        "GHI_kWh_m2_dia": 4.9, "HSP": 4.9,
        "T_amb_media": 26.0, "T_min_diseno": 15.0,
        "T_cel_realista": 50.0, "T_cel_extremo": 58.0,
        "region": "Andina", "CREG_zona": "Santander",
        "operador": "ESSA",
        "tarifa_comercial_cop_kwh": 950,
    },
    "Pereira": {
        "lat": 4.814, "lon": -75.696, "alt_m": 1411,
        "GHI_kWh_m2_dia": 4.4, "HSP": 4.4,
        "T_amb_media": 21.0, "T_min_diseno": 8.0,
        "T_cel_realista": 43.0, "T_cel_extremo": 50.0,
        "region": "Andina", "CREG_zona": "Eje Cafetero",
        "operador": "CHEC",
        "tarifa_comercial_cop_kwh": 850,
    },
    "Manizales": {
        "lat": 5.070, "lon": -75.513, "alt_m": 2153,
        "GHI_kWh_m2_dia": 4.2, "HSP": 4.2,
        "T_amb_media": 17.0, "T_min_diseno": 2.0,
        "T_cel_realista": 38.0, "T_cel_extremo": 45.0,
        "region": "Andina", "CREG_zona": "Eje Cafetero",
        "operador": "CHEC",
        "tarifa_comercial_cop_kwh": 850,
    },
    "Santa Marta": {
        "lat": 11.240, "lon": -74.199, "alt_m": 15,
        "GHI_kWh_m2_dia": 5.6, "HSP": 5.6,
        "T_amb_media": 29.0, "T_min_diseno": 22.0,
        "T_cel_realista": 57.0, "T_cel_extremo": 67.0,
        "region": "Caribe", "CREG_zona": "Costa",
        "operador": "Air-e",
        "tarifa_comercial_cop_kwh": 900,
    },
    "Ibagué": {
        "lat": 4.438, "lon": -75.232, "alt_m": 1285,
        "GHI_kWh_m2_dia": 4.7, "HSP": 4.7,
        "T_amb_media": 23.0, "T_min_diseno": 10.0,
        "T_cel_realista": 46.0, "T_cel_extremo": 53.0,
        "region": "Andina", "CREG_zona": "Tolima",
        "operador": "ENERTOLIMA",
        "tarifa_comercial_cop_kwh": 900,
    },
    "Villavicencio": {
        "lat": 4.142, "lon": -73.626, "alt_m": 467,
        "GHI_kWh_m2_dia": 5.1, "HSP": 5.1,
        "T_amb_media": 27.0, "T_min_diseno": 18.0,
        "T_cel_realista": 52.0, "T_cel_extremo": 61.0,
        "region": "Llanos", "CREG_zona": "Meta",
        "operador": "ENERCA",
        "tarifa_comercial_cop_kwh": 950,
    },
    "Pasto": {
        "lat": 1.215, "lon": -77.281, "alt_m": 2527,
        "GHI_kWh_m2_dia": 4.0, "HSP": 4.0,
        "T_amb_media": 13.0, "T_min_diseno": -2.0,
        "T_cel_realista": 34.0, "T_cel_extremo": 40.0,
        "region": "Andina", "CREG_zona": "Sur",
        "operador": "CEDENAR",
        "tarifa_comercial_cop_kwh": 900,
    },
    "Quibdó": {
        "lat": 5.694, "lon": -76.658, "alt_m": 54,
        "GHI_kWh_m2_dia": 4.3, "HSP": 4.3,
        "T_amb_media": 28.0, "T_min_diseno": 20.0,
        "T_cel_realista": 53.0, "T_cel_extremo": 62.0,
        "region": "Pacífico", "CREG_zona": "Chocó",
        "operador": "DISPAC",
        "tarifa_comercial_cop_kwh": 1000,
    },
    "Apartadó (Urabá)": {
        "lat": 7.884, "lon": -76.635, "alt_m": 30,
        "GHI_kWh_m2_dia": 5.3, "HSP": 5.3,
        "T_amb_media": 28.0, "T_min_diseno": 20.0,
        "T_cel_realista": 55.0, "T_cel_extremo": 64.0,
        "region": "Caribe/Tropical", "CREG_zona": "Antioquia",
        "operador": "EPM",
        # Tarifa EPM zona Urabá (comercial/industrial, sin subsidio). Fuente: EPM 2025.
        "tarifa_comercial_cop_kwh": 950,
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
