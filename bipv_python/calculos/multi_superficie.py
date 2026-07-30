"""
multi_superficie.py — Soporte BIPV para instalaciones con múltiples superficies.

Tipos soportados: Fachada | Techo | Pérgola | Marquesina
Cada superficie tiene su propia tilt, azimuth, área y POA calculada con pvlib.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from calculos.solar import calcular_poa

# ── Constantes de tipos ────────────────────────────────────────────────────────

TIPOS_SUPERFICIE: dict[str, dict] = {
    "Fachada": {
        "icon":        "🏢",
        "tilt_deg":    90,
        "azimuth_deg": 180,
        "color_hex":   "#2196F3",
        "descripcion": "Panel vertical integrado en cerramiento",
        "tilt_min":    70,
        "tilt_max":    90,
        "posicion_3d": "cara_vertical",
    },
    "Techo": {
        "icon":        "🏠",
        "tilt_deg":    10,
        "azimuth_deg": 180,
        "color_hex":   "#FF9800",
        "descripcion": "Panel sobre cubierta plana o inclinada",
        "tilt_min":    0,
        "tilt_max":    45,
        "posicion_3d": "cubierta",
    },
    "Pérgola": {
        "icon":        "🌿",
        "tilt_deg":    5,
        "azimuth_deg": 180,
        "color_hex":   "#4CAF50",
        "descripcion": "Estructura semi-horizontal con soporte propio",
        "tilt_min":    0,
        "tilt_max":    20,
        "posicion_3d": "exterior_horizontal",
    },
    "Marquesina": {
        "icon":        "🏪",
        "tilt_deg":    20,
        "azimuth_deg": 180,
        "color_hex":   "#9C27B0",
        "descripcion": "Voladizo inclinado adosado a fachada",
        "tilt_min":    5,
        "tilt_max":    45,
        "posicion_3d": "voladizo",
    },
}

MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# ── Constructores ──────────────────────────────────────────────────────────────

def superficie_nueva(
    nombre: str,
    tipo: str,
    tilt_deg: float | None = None,
    azimuth_deg: float | None = None,
    area_m2: float = 20.0,
    activa: bool = True,
) -> dict:
    """Crea un dict de superficie con defaults del tipo dado."""
    meta = TIPOS_SUPERFICIE.get(tipo, TIPOS_SUPERFICIE["Fachada"])
    return {
        "nombre":      nombre,
        "tipo":        tipo,
        "tilt_deg":    tilt_deg    if tilt_deg    is not None else meta["tilt_deg"],
        "azimuth_deg": azimuth_deg if azimuth_deg is not None else meta["azimuth_deg"],
        "area_m2":     area_m2,
        "activa":      activa,
    }


def superficies_por_defecto(
    azimuth_principal: float = 180.0,
    area_fachada: float = 50.0,
) -> list[dict]:
    """Retorna una lista inicial con la fachada principal del proyecto."""
    return [
        superficie_nueva(
            "Fachada principal",
            "Fachada",
            tilt_deg=90,
            azimuth_deg=azimuth_principal,
            area_m2=area_fachada,
        )
    ]


# ── Cálculo POA por superficie ─────────────────────────────────────────────────

def calcular_poa_superficie(
    tmy_df: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
    superficie: dict,
) -> pd.DataFrame:
    """
    Calcula POA horaria para UNA superficie.
    Retorna DataFrame con columnas pvlib estándar (poa_global, ...).
    """
    return calcular_poa(
        tmy_df,
        lat,
        lon,
        alt_m,
        tilt=float(superficie["tilt_deg"]),
        azimuth=float(superficie["azimuth_deg"]),
    )


def calcular_poa_todas(
    superficies: list[dict],
    tmy_df: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
) -> dict[str, pd.DataFrame]:
    """
    Calcula POA para todas las superficies activas.
    Retorna dict {nombre_superficie: poa_df}.
    """
    resultado: dict[str, pd.DataFrame] = {}
    for sup in superficies:
        if not sup.get("activa", True):
            continue
        try:
            resultado[sup["nombre"]] = calcular_poa_superficie(
                tmy_df, lat, lon, alt_m, sup
            )
        except Exception:
            resultado[sup["nombre"]] = pd.DataFrame()
    return resultado


def poa_mensual_superficie(poa_df: pd.DataFrame) -> list[float]:
    """
    Convierte POA horaria en lista de 12 valores mensuales [kWh/m²/mes].
    """
    if poa_df is None or poa_df.empty:
        return [0.0] * 12
    m_kwh = poa_df.groupby(poa_df.index.month)["poa_global"].sum() / 1000.0
    return [float(m_kwh.get(m, 0.0)) for m in range(1, 13)]


def poa_anual_superficie(poa_df: pd.DataFrame) -> float:
    """POA anual total en kWh/m²/año."""
    if poa_df is None or poa_df.empty:
        return 0.0
    return float(poa_df["poa_global"].sum() / 1000.0)


# ── Cálculo producción ─────────────────────────────────────────────────────────

def produccion_superficie(
    poa_df: pd.DataFrame,
    area_m2: float,
    eta_panel: float = 0.16,
    pr: float = 0.78,
) -> dict:
    """
    Calcula producción AC para una superficie.

    Parámetros
    ----------
    poa_df    : DataFrame POA horario (poa_global en W/m²)
    area_m2   : área activa de paneles
    eta_panel : eficiencia de panel [0-1] (default 0.16 = 16%)
    pr        : Performance Ratio [0-1] (default 0.78)

    Retorna dict con:
        e_ac_anual_kWh, e_ac_mensual (lista 12), poa_anual_kWh_m2
    """
    if poa_df is None or poa_df.empty:
        return {"e_ac_anual_kWh": 0.0, "e_ac_mensual": [0.0]*12, "poa_anual_kWh_m2": 0.0}

    poa_anual = poa_anual_superficie(poa_df)
    e_ac_anual = poa_anual * area_m2 * eta_panel * pr

    poa_mes = poa_mensual_superficie(poa_df)
    e_ac_mensual = [p * area_m2 * eta_panel * pr for p in poa_mes]

    return {
        "e_ac_anual_kWh":   round(e_ac_anual, 1),
        "e_ac_mensual":     [round(v, 1) for v in e_ac_mensual],
        "poa_anual_kWh_m2": round(poa_anual, 1),
    }


# ── Integración con CSV de Sombreado ──────────────────────────────────────────

def mapear_fachadas_csv(
    df_fs_raw: pd.DataFrame,
    superficies: list[dict],
) -> dict[str, str | None]:
    """
    Intenta mapear la columna 'fachada' del CSV a las superficies definidas.

    Retorna dict {nombre_superficie: nombre_fachada_csv | None}
    """
    if df_fs_raw is None or "fachada" not in df_fs_raw.columns:
        return {s["nombre"]: None for s in superficies}

    fachadas_csv = sorted(df_fs_raw["fachada"].dropna().unique().tolist())
    nombres_sup  = [s["nombre"] for s in superficies]

    mapeo: dict[str, str | None] = {}
    for nombre in nombres_sup:
        # Coincidencia exacta
        if nombre in fachadas_csv:
            mapeo[nombre] = nombre
            continue
        # Coincidencia parcial (ignora mayúsculas/espacios)
        norm = nombre.lower().replace(" ", "")
        match = next(
            (f for f in fachadas_csv if f.lower().replace(" ", "") == norm),
            None,
        )
        mapeo[nombre] = match
    return mapeo


def fs_mensual_por_superficie(
    df_fs_raw: pd.DataFrame,
    nombre_fachada_csv: str | None,
) -> list[float]:
    """
    Calcula FS promedio mensual para una superficie/fachada del CSV.
    Retorna lista de 12 valores FS ∈ [0,1]. 0=sin sombra.
    """
    if df_fs_raw is None or df_fs_raw.empty:
        return [0.0] * 12

    df = df_fs_raw.copy()
    if nombre_fachada_csv and "fachada" in df.columns:
        df = df[df["fachada"] == nombre_fachada_csv]

    if df.empty:
        return [0.0] * 12

    fs_mes = df.groupby("mes")["FS"].mean()
    return [float(fs_mes.get(m, 0.0)) for m in range(1, 13)]


# ── Paleta de colores ──────────────────────────────────────────────────────────

PALETA_TIPOS: dict[str, str] = {
    "Fachada":    "#2196F3",
    "Techo":      "#FF9800",
    "Pérgola":    "#4CAF50",
    "Marquesina": "#9C27B0",
}

def color_tipo(tipo: str) -> str:
    return PALETA_TIPOS.get(tipo, "#607D8B")


def color_poa_normalizado(val: float, vmin: float, vmax: float) -> str:
    """Mapea POA [vmin, vmax] a color rgb azul → amarillo → rojo."""
    rng = max(1.0, vmax - vmin)
    t   = max(0.0, min(1.0, (val - vmin) / rng))
    if t < 0.5:
        s = t * 2
        r = int(40  + 215 * s)
        g = int(100 + 155 * s)
        b = int(220 - 170 * s)
    else:
        s = (t - 0.5) * 2
        r = 255
        g = int(255 - 230 * s)
        b = int(50  -  50 * s)
    return f"rgb({r},{g},{b})"


def color_fs(fs: float) -> str:
    """FS 0-1 → color: verde (libre) → naranja (parcial) → rojo (bypass)."""
    if fs < 0.10:
        return "rgb(56, 161, 105)"    # verde
    if fs < 0.35:
        return "rgb(237, 137, 54)"    # naranja
    return "rgb(229, 62, 62)"         # rojo
