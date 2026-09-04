"""
Verificación cruzada de irradiancia — PVGIS (fuente oficial) vs PVWatts (NREL/NLR).
Fuente datos: PVWatts v8 API (developer.nlr.gov, antes developer.nrel.gov —
migración de dominio NREL→NLR completada 29-may-2026) — requiere API key
gratuita (developer.nlr.gov/signup/).

Diseño (4-sep-2026, sesión de evaluación de huecos de la app): PVGIS sigue
siendo la ÚNICA fuente que alimenta el motor de producción real (SDM/JRC-Huld)
-- esto es un chequeo de sanidad NO bloqueante, no un reemplazo. Confirmado
revisando Mod_Importar_PVWatts.bas (optimizador Excel original, previo al
puerto a Python) que PVWatts no expone irradiancia cruda (GHI/DNI/DHI): entrega
POA ya transpuesto a la inclinación/azimut dados -- por eso la comparación es
POA final contra POA final (post-transposición), no componente a componente
como hace calculos.solar.verificar_consistencia_radiativa() con PVGIS solo.

La key se comparte con la app hermana ("solar_shading_calculator", que ya
usa PVWatts en client/src/lib/crossValidation.ts + server/pvwattsProxy.ts) —
se lee del MISMO archivo .env de esa app en el servidor
(/var/www/bipv/calculadora/.env), no se duplica ni se pide una key aparte.
"""
from __future__ import annotations

import math
import os

import pandas as pd
import requests

PVWATTS_URL = "https://developer.nlr.gov/api/pvwatts/v8.json"

# Ruta real del .env de la app hermana en el servidor de producción (confirmada
# 4-sep-2026 vía `pm2 show calculadora-bipv` -- NO es /var/www/bipv/calculadora-bipv/,
# ese es el clon git de ESTA app; la hermana vive en un directorio de deploy
# separado). En desarrollo local, o si el archivo no existe, cae a la variable
# de entorno NREL_API_KEY.
_ENV_PATH_SERVIDOR_HERMANA = "/var/www/bipv/calculadora/.env"

PVWATTS_ALERTA_PCT_DEFAULT = 15.0  # % de diferencia anual que dispara la alerta


def _leer_nrel_api_key(env_path: str = _ENV_PATH_SERVIDOR_HERMANA) -> str | None:
    """
    Lee NREL_API_KEY compartida con la app hermana. Nunca lanza excepción:
    retorna None si no la encuentra en ningún lado, para que el chequeo se
    desactive limpiamente (el resto de Recurso Solar sigue funcionando igual
    que hoy, sin PVWatts).
    """
    key = os.environ.get("NREL_API_KEY")
    if key:
        return key.strip() or None
    try:
        with open(env_path, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea.startswith("NREL_API_KEY="):
                    return linea.split("=", 1)[1].strip() or None
    except OSError:
        pass
    return None


def obtener_produccion_pvwatts(
    lat: float,
    lon: float,
    tilt: float,
    azimuth: float,
    system_capacity_kw: float = 1.0,
    losses_pct: float = 14.08,
    timeout: int = 30,
) -> dict | None:
    """
    Consulta PVWatts v8 (mensual) para la misma ubicación/inclinación/azimut
    del proyecto activo. system_capacity_kw=1.0 por defecto porque solo se usa
    poa_monthly (kWh/m², independiente de la capacidad) -- ac_monthly/dc_monthly
    se devuelven igual por si se quieren usar más adelante, pero no se usan en
    comparar_poa_pvgis_vs_pvwatts().

    Retorna dict con poa_monthly_kwh_m2 (12 valores), ac_monthly_kwh,
    dc_monthly_kwh y weather_data_source (para trazabilidad), o None si falta
    la key, la key es inválida, o la llamada falla por cualquier motivo --
    este chequeo es opcional/no bloqueante por diseño, igual que el resto de
    verificaciones de calculos/solar.py.
    """
    api_key = _leer_nrel_api_key()
    if not api_key:
        return None

    params = {
        "api_key": api_key,
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "system_capacity": system_capacity_kw,
        "azimuth": azimuth,
        "tilt": tilt,
        "array_type": 1,  # Fixed Roof Mount -- mismo default que server/pvwattsProxy.ts de la app hermana
        "module_type": 0,
        "losses": losses_pct,
        "timeframe": "monthly",
    }
    try:
        resp = requests.get(PVWATTS_URL, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None

    if data.get("errors"):
        return None

    out = data.get("outputs")
    if not out or "poa_monthly" not in out or len(out["poa_monthly"]) != 12:
        return None

    return {
        "poa_monthly_kwh_m2": out["poa_monthly"],
        "ac_monthly_kwh": out.get("ac_monthly"),
        "dc_monthly_kwh": out.get("dc_monthly"),
        "weather_data_source": data.get("station_info", {}).get("weather_data_source"),
    }


def poa_horaria_a_mensual_kwh_m2(poa_horaria_wm2: pd.Series) -> list[float]:
    """
    Agrega una serie horaria de POA (W/m², índice DatetimeIndex -- el mismo
    formato que devuelve calculos.solar.calcular_poa()) a 12 totales mensuales
    en kWh/m², mismas unidades que poa_monthly de PVWatts, para poder
    comparar directo.
    """
    if len(poa_horaria_wm2) == 0:
        raise ValueError("poa_horaria_wm2 no puede estar vacía.")
    mensual_wh_m2 = poa_horaria_wm2.groupby(poa_horaria_wm2.index.month).sum()
    return [float(mensual_wh_m2.get(mes, 0.0)) / 1000.0 for mes in range(1, 13)]


def comparar_poa_pvgis_vs_pvwatts(
    poa_pvgis_mensual_kwh_m2: list[float],
    poa_pvwatts_mensual_kwh_m2: list[float],
    umbral_alerta_pct: float = PVWATTS_ALERTA_PCT_DEFAULT,
) -> dict:
    """
    Compara el POA mensual (kWh/m²) ya transpuesto de PVGIS contra el de
    PVWatts para la misma inclinación/azimut. Ambas series deben venir en las
    MISMAS unidades y con la MISMA transposición aplicada (tilt/azimut) -- la
    comparación es post-transposición, no de irradiancia cruda (ver docstring
    del módulo).

    Retorna dict con diferencia_pct_mensual (12 valores, None si el mes de
    PVGIS es 0), diferencia_pct_anual, los totales anuales de cada fuente, y
    alerta (True si |diferencia_pct_anual| > umbral_alerta_pct).
    """
    if len(poa_pvgis_mensual_kwh_m2) != 12 or len(poa_pvwatts_mensual_kwh_m2) != 12:
        raise ValueError("Ambas series deben tener exactamente 12 valores mensuales.")

    diferencia_pct_mensual = [
        ((pvw - pvg) / pvg * 100.0) if pvg > 0 else None
        for pvg, pvw in zip(poa_pvgis_mensual_kwh_m2, poa_pvwatts_mensual_kwh_m2)
    ]

    total_pvgis = float(sum(poa_pvgis_mensual_kwh_m2))
    total_pvwatts = float(sum(poa_pvwatts_mensual_kwh_m2))
    diferencia_pct_anual = (
        (total_pvwatts - total_pvgis) / total_pvgis * 100.0
        if total_pvgis > 0 else None
    )

    return {
        "diferencia_pct_mensual": diferencia_pct_mensual,
        "diferencia_pct_anual": diferencia_pct_anual,
        "poa_pvgis_anual_kwh_m2": total_pvgis,
        "poa_pvwatts_anual_kwh_m2": total_pvwatts,
        "alerta": (
            diferencia_pct_anual is not None
            and math.isfinite(diferencia_pct_anual)
            and abs(diferencia_pct_anual) > umbral_alerta_pct
        ),
        "umbral_alerta_pct": umbral_alerta_pct,
    }
