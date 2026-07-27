"""
Módulo de pérdidas por mismatch y sombreado para sistemas BIPV.

Cubre:
  1. Sombreado de horizonte — obstáculos cercanos (edificios, árboles)
  2. Mismatch por orientación múltiple — fachadas distintas en el mismo string
  3. Pérdidas simples en cascada — fabricación, suciedad, cableado DC
  4. Cascada total de pérdidas → POA efectiva

Referencia mismatch orientación: PVsyst Technical Reference v7,
  "Electrical Mismatch Losses", σ²/(2μ²) — primera orden.
"""

import numpy as np
import pandas as pd
import pvlib

from calculos.solar import calcular_poa


# ─── 1. Sombreado de horizonte ───────────────────────────────────────────────

def _interpolar_horizonte(puntos: list[tuple], az_query: np.ndarray) -> np.ndarray:
    """
    Interpola linealmente el perfil de horizonte definido por el usuario.

    puntos   : [(azimuth_deg, elevacion_deg), ...] — 0=Norte, 90=Este, 180=Sur, 270=Oeste
    az_query : array de azimuths a consultar (grados)
    Retorna  : array de elevaciones de horizonte para cada az_query
    """
    if not puntos:
        return np.zeros(len(az_query))

    pts  = sorted(puntos, key=lambda p: p[0])
    azs  = np.array([p[0] for p in pts], dtype=float)
    els  = np.array([p[1] for p in pts], dtype=float)

    # Extiende a -360 … +720 para interpolación circular
    az_ext = np.concatenate([azs - 360, azs, azs + 360])
    el_ext = np.tile(els, 3)

    return np.interp(az_query % 360, az_ext, el_ext)


def calcular_sombreado_horizonte(
    lat: float,
    lon: float,
    alt_m: float,
    tmy: pd.DataFrame,
    poa: pd.DataFrame,
    puntos_horizonte: list[tuple],
) -> dict:
    """
    Calcula pérdidas anuales de POA por sombreado de horizonte.

    Parámetros
    ----------
    lat, lon, alt_m   : coordenadas del sitio
    tmy               : DataFrame TMY (índice DatetimeIndex UTC)
    poa               : DataFrame POA con columna 'poa_global'
    puntos_horizonte  : [(azimuth_Norte_deg, elev_obs_deg), ...]
                        Cada punto define la elevación del obstáculo
                        visible desde el array en ese azimuth.

    Retorna dict
    ────────────
    factor_sombra_anual    : fracción de energía POA perdida (0–1)
    energia_perdida_kWh_m2 : kWh/m² perdidos al año
    horas_sombreadas       : nº horas afectadas
    mascara_sombra         : pd.Series bool (True = hora sombreada)
    solar_pos              : DataFrame posiciones solares (para diagrama)
    """
    loc       = pvlib.location.Location(latitude=lat, longitude=lon, altitude=alt_m, tz="UTC")
    solar_pos = loc.get_solarposition(poa.index)

    if not puntos_horizonte:
        return dict(
            factor_sombra_anual    = 0.0,
            energia_perdida_kWh_m2 = 0.0,
            horas_sombreadas       = 0,
            mascara_sombra         = pd.Series(False, index=poa.index),
            solar_pos              = solar_pos,
        )

    horizon_elev = _interpolar_horizonte(puntos_horizonte, solar_pos["azimuth"].values)

    sol_visible = solar_pos["apparent_elevation"].values > 0.0
    sombreado   = sol_visible & (solar_pos["apparent_elevation"].values < horizon_elev)
    mask        = pd.Series(sombreado, index=poa.index)

    poa_g            = poa["poa_global"].clip(lower=0)
    energia_total    = poa_g.sum() / 1000.0
    energia_perdida  = poa_g[mask].sum() / 1000.0
    factor           = energia_perdida / energia_total if energia_total > 0 else 0.0

    return dict(
        factor_sombra_anual    = round(factor, 4),
        energia_perdida_kWh_m2 = round(energia_perdida, 1),
        horas_sombreadas       = int(mask.sum()),
        mascara_sombra         = mask,
        solar_pos              = solar_pos,
    )


# ─── 2. Mismatch por orientación múltiple ───────────────────────────────────

def calcular_mismatch_orientacion(
    tmy: pd.DataFrame,
    lat: float,
    lon: float,
    alt_m: float,
    configuraciones: list[dict],
) -> dict:
    """
    Pérdidas de mismatch cuando módulos de distintas orientaciones están
    conectados en el mismo string (BIPV esquinas, fachadas múltiples).

    configuraciones : [
        {"azimuth": 0,  "tilt": 90, "fraccion": 0.60, "label": "Norte"},
        {"azimuth": 90, "tilt": 90, "fraccion": 0.40, "label": "Este"},
    ]

    Modelo (PVsyst aprox. 1er orden):
        LM = σ²_poa / (2 · μ²_poa)
    donde σ² es la varianza ponderada de POA anual entre orientaciones.

    Retorna dict con POA por orientación y factor de mismatch.
    """
    poa_res = []
    for cfg in configuraciones:
        poa      = calcular_poa(tmy, lat, lon, alt_m, cfg["tilt"], cfg["azimuth"])
        poa_anual = poa["poa_global"].sum() / 1000.0
        poa_res.append({
            "label":   cfg.get("label", f"Az{cfg['azimuth']}°/{cfg['tilt']}°"),
            "azimuth": cfg["azimuth"],
            "tilt":    cfg["tilt"],
            "fraccion": cfg["fraccion"],
            "poa_anual": round(poa_anual, 1),
        })

    fracs    = np.array([p["fraccion"]  for p in poa_res])
    poa_vals = np.array([p["poa_anual"] for p in poa_res])

    poa_medio = float(np.sum(fracs * poa_vals))

    if len(poa_res) < 2 or poa_medio == 0:
        return dict(
            poas                   = poa_res,
            factor_mismatch_pct    = 0.0,
            energia_ideal_kWh_m2   = round(poa_medio, 1),
            energia_perdida_kWh_m2 = 0.0,
        )

    variance        = float(np.sum(fracs * (poa_vals - poa_medio) ** 2))
    mismatch_pct    = (variance / (2 * poa_medio ** 2)) * 100
    energia_perdida = poa_medio * mismatch_pct / 100.0

    return dict(
        poas                   = poa_res,
        factor_mismatch_pct    = round(mismatch_pct, 2),
        energia_ideal_kWh_m2   = round(poa_medio, 1),
        energia_perdida_kWh_m2 = round(energia_perdida, 1),
    )


# ─── 3. Cascada de pérdidas ──────────────────────────────────────────────────

def cascada_perdidas(
    poa_bruta_kWh_m2:       float,
    factor_sombra:          float,   # fracción (0–1)
    factor_mismatch_orient: float,   # porcentaje (0–100)
    pct_mismatch_fab:       float,   # porcentaje (0–100)
    pct_soiling:            float,   # porcentaje (0–100)
    pct_cableado:           float,   # porcentaje (0–100)
) -> list[dict]:
    """
    Cascada de pérdidas POA → POA efectiva.
    Retorna lista de dicts lista para gráfico waterfall.

    Columnas: etapa, energia (kWh/m²), perdida (kWh/m²), pct_perdida
    """
    etapas = []

    def _paso(nombre, energia_in, factor_perdida_frac):
        perdida   = energia_in * factor_perdida_frac
        energia   = energia_in - perdida
        pct_total = perdida / poa_bruta_kWh_m2 * 100 if poa_bruta_kWh_m2 > 0 else 0
        etapas.append({
            "etapa":     nombre,
            "energia":   round(energia, 2),
            "perdida":   round(perdida, 2),
            "pct_total": round(pct_total, 2),
        })
        return energia

    etapas.append({
        "etapa":     "POA bruta",
        "energia":   round(poa_bruta_kWh_m2, 2),
        "perdida":   0.0,
        "pct_total": 0.0,
    })

    e = poa_bruta_kWh_m2
    e = _paso("Sombreado horizonte",    e, factor_sombra)
    e = _paso("Mismatch orientación",   e, factor_mismatch_orient / 100)
    e = _paso("Mismatch fabricación",   e, pct_mismatch_fab / 100)
    e = _paso("Suciedad (Soiling)",     e, pct_soiling / 100)
    e = _paso("Cableado DC",            e, pct_cableado / 100)

    etapas.append({
        "etapa":     "POA efectiva final",
        "energia":   round(e, 2),
        "perdida":   0.0,
        "pct_total": 0.0,
    })

    return etapas


def factor_global_perdidas(cascada: list[dict]) -> float:
    """Factor de rendimiento global = POA_efectiva / POA_bruta."""
    bruta   = next(r["energia"] for r in cascada if r["etapa"] == "POA bruta")
    efectiva = next(r["energia"] for r in cascada if r["etapa"] == "POA efectiva final")
    return round(efectiva / bruta, 4) if bruta > 0 else 0.0
