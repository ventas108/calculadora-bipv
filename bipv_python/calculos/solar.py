"""
Módulo de recurso solar — TMY desde PVGIS + POA para fachadas BIPV.
Fuente datos: PVGIS v5.2 (JRC European Commission) — sin API key.
"""
import requests
import pandas as pd
import numpy as np
import pvlib

PVGIS_TMY_URL = "https://re.jrc.ec.europa.eu/api/v5_2/tmy"

# Mapa azimuth etiqueta → grados pvlib (0=Norte, 90=Este, 180=Sur, 270=Oeste)
ORIENTACIONES = {
    "Norte (0°)":         0,
    "Noreste (45°)":     45,
    "Este (90°)":        90,
    "Sureste (135°)":   135,
    "Sur (180°)":       180,
    "Suroeste (225°)":  225,
    "Oeste (270°)":     270,
    "Noroeste (315°)":  315,
}


def obtener_tmy_pvgis(lat: float, lon: float, timeout: int = 30) -> pd.DataFrame:
    """
    Descarga datos TMY horarios desde PVGIS para lat/lon dados.
    Retorna DataFrame con índice DatetimeIndex (año 2001, horario) y columnas:
        G_h    — GHI  W/m²
        Gb_n   — DNI  W/m²
        Gd_h   — DHI  W/m²
        T2m    — Temperatura ambiente °C
        WS10m  — Velocidad viento m/s
        SP     — Presión superficial Pa
    """
    params = {
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "outputformat": "json",
    }
    resp = requests.get(PVGIS_TMY_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    hourly = data["outputs"]["tmy_hourly"]
    df = pd.DataFrame(hourly)

    # Parsear tiempo — PVGIS devuelve "20070101:0010" (YYYYMMDD:HHmm)
    df["dt"] = pd.to_datetime(df["time(UTC)"], format="%Y%m%d:%H%M", utc=True)
    # Normalizar al año 2001 para tener un año completo consistente
    df["dt"] = df["dt"].apply(
        lambda t: t.replace(year=2001)
    )
    df = df.set_index("dt").sort_index()

    # Renombrar columnas
    df = df.rename(columns={
        "G(h)":  "G_h",
        "Gb(n)": "Gb_n",
        "Gd(h)": "Gd_h",
        "T2m":   "T2m",
        "WS10m": "WS10m",
        "SP":    "SP",
    })

    cols = ["G_h", "Gb_n", "Gd_h", "T2m", "WS10m", "SP"]
    return df[[c for c in cols if c in df.columns]].astype(float)


def calcular_poa(
    tmy: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
    tilt: float,
    azimuth: float,
) -> pd.DataFrame:
    """
    Calcula irradiancia POA (Plane of Array) para la orientación dada.

    Parámetros
    ----------
    tmy      : DataFrame de obtener_tmy_pvgis()
    lat, lon : coordenadas del sitio
    alt_m    : altitud en metros
    tilt     : inclinación del plano (0=horizontal, 90=vertical fachada)
    azimuth  : azimuth del plano — pvlib convention (0=N, 90=E, 180=S, 270=O)

    Retorna DataFrame con columnas:
        poa_global, poa_direct, poa_diffuse, poa_sky_diffuse, poa_ground_diffuse
    """
    loc = pvlib.location.Location(
        latitude=lat, longitude=lon, altitude=alt_m, tz="UTC"
    )
    solar_pos = loc.get_solarposition(tmy.index)

    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        solar_zenith=solar_pos["apparent_zenith"],
        solar_azimuth=solar_pos["azimuth"],
        dni=tmy["Gb_n"],
        ghi=tmy["G_h"],
        dhi=tmy["Gd_h"],
        model="haydavies",
        dni_extra=pvlib.irradiance.get_extra_radiation(tmy.index),
    )
    return poa.fillna(0.0)


def resumen_mensual(tmy: pd.DataFrame, poa: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa GHI y POA por mes — retorna kWh/m²/mes.
    """
    meses = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
    }
    df = pd.DataFrame({
        "GHI_Wh": tmy["G_h"],
        "POA_Wh": poa["poa_global"],
    })
    monthly = df.resample("ME").sum() / 1000.0  # → kWh/m²
    monthly.columns = ["GHI (kWh/m²)", "POA (kWh/m²)"]
    monthly.index = [meses[m] for m in monthly.index.month]
    return monthly


def heatmap_poa_horario(poa: pd.DataFrame) -> pd.DataFrame:
    """
    Matriz 24h × 12 meses para heatmap — promedio POA por hora y mes.
    """
    df = poa[["poa_global"]].copy()
    df["hora"] = df.index.hour
    df["mes"]  = df.index.month
    pivot = df.groupby(["hora", "mes"])["poa_global"].mean().unstack()
    meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    pivot.columns = meses
    return pivot
