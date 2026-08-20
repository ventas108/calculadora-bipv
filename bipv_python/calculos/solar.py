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
    albedo: float = 0.20,
    bifacial: dict | None = None,
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
    albedo   : reflectividad del suelo frente al array (0.05–0.50)
    bifacial : None → panel monofacial (comportamiento clásico).
               dict → activa el modelo bifacial pvlib infinite_sheds:
                 {
                   "bifacialidad":   0.80,  # fracción (Isc trasero / frontal)
                   "altura_m":       1.0,   # altura del centro del panel sobre el suelo
                   "albedo_trasero": 0.20,  # reflectividad detrás del array
                   "gcr":            0.25,  # ground coverage ratio (fila aislada ≈ 0.2–0.3)
                   "ancho_colector_m": 2.0, # ancho inclinado de la fila (m)
                   "factor_vista_trasera": 1.0, # 0–1: fracción del aporte trasero que
                                                # llega al panel. 0 = fachada adosada al
                                                # muro (trasera sellada, sin ganancia).
                 }

    Retorna DataFrame con columnas:
        poa_global, poa_direct, poa_diffuse, poa_sky_diffuse, poa_ground_diffuse
    y, si bifacial está activo, además:
        poa_front, poa_rear  (poa_global = poa_front + bifacialidad × poa_rear)
    """
    loc = pvlib.location.Location(
        latitude=lat, longitude=lon, altitude=alt_m, tz="UTC"
    )
    solar_pos = loc.get_solarposition(tmy.index)
    dni_extra = pvlib.irradiance.get_extra_radiation(tmy.index)

    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        solar_zenith=solar_pos["apparent_zenith"],
        solar_azimuth=solar_pos["azimuth"],
        dni=tmy["Gb_n"],
        ghi=tmy["G_h"],
        dhi=tmy["Gd_h"],
        albedo=albedo,
        model="haydavies",
        dni_extra=dni_extra,
    ).fillna(0.0)

    if not bifacial:
        return poa

    # ── Modelo bifacial: pvlib infinite_sheds (estándar de la industria) ──────
    # poa_global bifacial = poa frontal + bifacialidad × poa trasera, con
    # sombreado fila-a-fila y vista del suelo resueltos geométricamente.
    from pvlib.bifacial import infinite_sheds

    bifacialidad = float(bifacial.get("bifacialidad", 0.80))
    altura_m     = float(bifacial.get("altura_m", 1.0))
    alb_rear     = float(bifacial.get("albedo_trasero", albedo))
    gcr          = min(max(float(bifacial.get("gcr", 0.25)), 0.05), 0.95)
    ancho        = float(bifacial.get("ancho_colector_m", 2.0))
    pitch        = ancho / gcr
    # Factor de vista trasera (0–1): atenúa el aporte de la cara trasera antes
    # de componer poa_global. 0 = fachada adosada al muro (trasera sellada, sin
    # ganancia bifacial); 1 = trasera plenamente expuesta. Retro-compatible:
    # sin la clave, el factor es 1.0 y el comportamiento es idéntico.
    factor_vista = min(max(float(bifacial.get("factor_vista_trasera", 1.0)), 0.0), 1.0)

    poa_bif = infinite_sheds.get_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        solar_zenith=solar_pos["apparent_zenith"],
        solar_azimuth=solar_pos["azimuth"],
        gcr=gcr,
        height=altura_m,
        pitch=pitch,
        ghi=tmy["G_h"],
        dhi=tmy["Gd_h"],
        dni=tmy["Gb_n"],
        albedo=alb_rear,
        model="haydavies",
        dni_extra=dni_extra,
        bifaciality=bifacialidad,
    ).fillna(0.0)

    # En modo bifacial, poa_global proviene ÍNTEGRAMENTE de infinite_sheds
    # (frente con sombreado fila-a-fila + trasera × bifacialidad), para no
    # mezclar dos modelos con supuestos geométricos distintos. Las columnas
    # clásicas (poa_direct, poa_diffuse, ...) se conservan solo como
    # descomposición informativa del frente sin sombreado fila-fila.
    out = poa.copy()
    _front = poa_bif["poa_front"].clip(lower=0.0)
    _rear  = poa_bif["poa_back"].clip(lower=0.0)
    # Atenuar el aporte trasero por el factor de vista antes de componer.
    # poa_global = poa_front + bifacialidad × factor × poa_back
    # poa_rear se reporta YA multiplicada por el factor de vista.
    out["poa_front"] = _front
    out["poa_rear"] = (_rear * factor_vista).clip(lower=0.0)
    out["poa_global"] = (_front + bifacialidad * factor_vista * _rear).clip(lower=0.0)
    return out.fillna(0.0)


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


def posiciones_solares_representativas(
    lat: float, lon: float, alt_m: float, elevacion_min: float = 0.0
) -> pd.DataFrame:
    """
    Posiciones solares horarias para 12 días representativos del año
    (día 15 de cada mes, año estándar 2001, UTC).

    Uso: diagramas de trayectoria solar (sun-path chart). NO interviene en
    el cálculo de energía ni de sombreado horizonte, que usa la resolución
    horaria real del TMY — ver calcular_poa() y calculos.mismatch.

    elevacion_min : conserva solo posiciones con apparent_elevation
                    estrictamente mayor a este umbral (grados).
    """
    loc = pvlib.location.Location(latitude=lat, longitude=lon, altitude=alt_m, tz="UTC")
    dias_rep = pd.date_range("2001-01-15", periods=12, freq="MS") + pd.Timedelta(days=14)
    frames = []
    for dia in dias_rep:
        times = pd.date_range(dia, dia + pd.Timedelta(hours=23), freq="h", tz="UTC")
        sp = loc.get_solarposition(times)
        sp["mes"] = dia.month
        frames.append(sp[sp["apparent_elevation"] > elevacion_min])
    return pd.concat(frames) if frames else pd.DataFrame()


def posiciones_solares_anio_estandar(lat: float, lon: float, alt_m: float) -> pd.DataFrame:
    """
    Posiciones solares para un año estándar de 8760 h UTC (sin datos TMY).

    Uso: render geométrico 3D del recorrido solar — independiente del
    cálculo energético, que sigue el calendario real del TMY.
    """
    loc = pvlib.location.Location(latitude=lat, longitude=lon, altitude=alt_m, tz="UTC")
    times = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    return loc.get_solarposition(times)


def heatmap_poa_horario(poa: pd.DataFrame, utc_offset: int = 0) -> pd.DataFrame:
    """
    Matriz 24h × 12 meses para heatmap — promedio POA por hora y mes.

    utc_offset : offset UTC en horas enteras para mostrar hora local.
                 Por ejemplo, -5 para Colombia (UTC-5).
                 Los datos de irradiancia no se modifican; solo cambia
                 la agrupación horaria para que el eje Y refleje hora local.
    """
    df = poa[["poa_global"]].copy()
    df["hora"] = (df.index.hour + utc_offset) % 24   # hora local 0-23
    df["mes"]  = df.index.month
    pivot = df.groupby(["hora", "mes"])["poa_global"].mean().unstack()
    meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    pivot.columns = meses
    pivot = pivot.sort_index()          # asegura orden 00-23 h
    return pivot
