"""
Módulo de recurso solar — TMY desde PVGIS + POA para fachadas BIPV.
Fuente datos: PVGIS v5.2 (JRC European Commission) — sin API key.
"""
import warnings

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


# ── Auditoría 27-ago-2026 ────────────────────────────────────────────────────
# El usuario aportó un motor BIPV Python puro (sin pvlib) que trae integrado
# un chequeo de cierre físico GHI≈DNI·cosZ+DHI en cada corrida -- al
# auditarlo, ese mismo chequeo detectó (891 avisos de 8760 horas) que el
# script tenía un bug real de 30 minutos en el centrado del timestamp para
# TMY de PVGIS (misma familia que el bug de 5 horas de
# DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md, 26-ago-2026). Investigado: pvlib NO
# trae este chequeo (`irradiance.py` no lo tiene). Sí existe en el paquete
# hermano oficial `pvanalytics` (mismo equipo de pvlib/NREL) como
# `quality.irradiance.check_irradiance_consistency_qcrad()` -- implementa el
# algoritmo QCRad publicado (Long & Shi, 2008, estándar BSRN de control de
# calidad de radiación solar), verificado leyendo su código fuente real. Se
# decidió NO agregar `pvanalytics` como dependencia (arrastra `statsmodels` +
# `scikit-image`, pesados y no usados para nada más) -- se porta aquí solo el
# chequeo central del algoritmo (cierre físico), con numpy/pandas que ya son
# dependencias existentes.
QCRAD_TOLERANCIA_WM2_DEFAULT = 50.0
QCRAD_ELEVACION_MINIMA_DEG = 3.0   # excluye horas rasantes (ruido relativo grande, irradiancia ~0)
QCRAD_PCT_ALERTA = 2.0             # % de horas de día inconsistentes que dispara el warning


def verificar_consistencia_radiativa(
    tmy: pd.DataFrame,
    solar_zenith_deg,
    tolerancia_wm2: float = QCRAD_TOLERANCIA_WM2_DEFAULT,
    elevacion_minima_deg: float = QCRAD_ELEVACION_MINIMA_DEG,
    pct_alerta: float = QCRAD_PCT_ALERTA,
) -> dict:
    """
    Chequeo de cierre físico GHI ≈ DNI·cos(zenit) + DHI (algoritmo QCRad,
    Long & Shi 2008 -- ver nota de módulo arriba). Detecta el mismo tipo de
    bug que causó DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md: un desfase de huso
    horario o de centrado de intervalo empareja la irradiancia con la
    posición solar de una hora equivocada, y este chequeo lo revela como una
    inconsistencia física medible aunque los datos "se vean razonables" a
    simple vista.

    Parámetros
    ----------
    tmy              : DataFrame con columnas G_h (GHI), Gb_n (DNI), Gd_h (DHI)
                        -- mismo formato que devuelve obtener_tmy_pvgis().
    solar_zenith_deg : ángulo cenital solar (°), mismo índice que tmy.
    tolerancia_wm2    : diferencia absoluta máxima tolerada por hora, W/m².
                        Calibrado empíricamente: el TMY real de Urabá, ya
                        validado contra PVsyst, da 0% de horas inconsistentes
                        con este umbral; un desfase de solo 30 min en el
                        centrado del timestamp ya produce >10%.
    elevacion_minima_deg : excluye horas con el sol muy bajo (elevación
                        menor a este valor) -- ahí la irradiancia es casi
                        nula y el ruido relativo es enorme sin ser un
                        problema real.
    pct_alerta        : % de horas de día inconsistentes que dispara el
                        `UserWarning`.

    Retorna
    -------
    dict con horas_evaluadas, horas_inconsistentes, pct_inconsistente,
    diferencia_media_wm2, diferencia_maxima_wm2.
    """
    zenith = np.asarray(solar_zenith_deg, dtype=float)
    elevacion = 90.0 - zenith
    mask_dia = elevacion > elevacion_minima_deg

    ghi = tmy["G_h"].to_numpy(dtype=float)
    dni = tmy["Gb_n"].to_numpy(dtype=float)
    dhi = tmy["Gd_h"].to_numpy(dtype=float)

    cos_z = np.clip(np.cos(np.radians(zenith)), 0.0, None)
    suma_componentes = dni * cos_z + dhi
    diferencia = np.abs(ghi - suma_componentes)

    horas_dia = int(mask_dia.sum())
    if horas_dia == 0:
        return {
            "horas_evaluadas": 0, "horas_inconsistentes": 0,
            "pct_inconsistente": 0.0, "diferencia_media_wm2": 0.0,
            "diferencia_maxima_wm2": 0.0,
        }

    dif_dia = diferencia[mask_dia]
    inconsistentes = int((dif_dia > tolerancia_wm2).sum())
    pct = round(100 * inconsistentes / horas_dia, 2)
    resultado = {
        "horas_evaluadas": horas_dia,
        "horas_inconsistentes": inconsistentes,
        "pct_inconsistente": pct,
        "diferencia_media_wm2": round(float(dif_dia.mean()), 1),
        "diferencia_maxima_wm2": round(float(dif_dia.max()), 1),
    }
    if pct > pct_alerta:
        warnings.warn(
            f"Inconsistencia radiativa: {inconsistentes}/{horas_dia} horas de "
            f"día ({pct}%) no cumplen GHI≈DNI·cosZ+DHI dentro de "
            f"{tolerancia_wm2:.0f} W/m² (chequeo QCRad, Long & Shi 2008). "
            "Puede indicar un desfase de huso horario o de centrado de "
            "intervalo entre el TMY y la posición solar -- ver "
            "DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md para un caso real "
            "encontrado con este mismo síntoma.",
            UserWarning,
            stacklevel=2,
        )
    return resultado


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

    # Chequeo QCRad de cierre físico (ver verificar_consistencia_radiativa()
    # arriba) -- corre una sola vez por llamada, independiente de
    # tilt/azimuth/bifacial (solo depende del TMY y la posición solar, ya
    # calculados). No cambia el DataFrame devuelto (mismo contrato que
    # antes) -- el resultado queda en .attrs["qcrad"] para quien quiera
    # inspeccionarlo, y emite un UserWarning automático si hay inconsistencia.
    qcrad = verificar_consistencia_radiativa(tmy, solar_pos["apparent_zenith"])

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
    poa.attrs["qcrad"] = qcrad

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
