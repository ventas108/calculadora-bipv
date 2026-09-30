# -*- coding: utf-8 -*-
"""☀️ Seguidor de un eje frente a la estructura fija (🌾 Granja FV, fase 4).

Spec ``05-perdidas-y-temperatura/seguidor-un-eje`` (30-sep-2026).

- Ángulos: ``pvlib.tracking.singleaxis`` (eje Norte–Sur horizontal), con y
  sin backtracking.
- Luz en la cara frontal: ``pvlib.bifacial.infinite_sheds`` para las tres
  variantes (fija del campo, seguidor con y sin backtracking), así la
  comparación usa el mismo modelo de cielo y la misma sombra entre filas.
- Sin backtracking la fila vecina tapa una franja del seguidor en las horas
  de sol bajo. En luz la pérdida es pequeña (la fila recibe casi la misma
  luz directa que con backtracking), pero la franja de sombra desactiva
  bloques de celdas por los diodos de bypass: se aplica
  ``pvlib.shading.direct_martinez`` con la fracción sombreada y los bloques
  del ancho del seguidor. Con backtracking la fila nunca se sombrea.

Módulo puro: sin Streamlit.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

EJE_AZIMUT_DEG = 180.0          # eje Norte–Sur
SEP_MODULOS_M = 0.02
FRACCION_MINIMA = 1e-6        # redondeo numérico del backtracking
SEGUIDOR_DEFECTO: dict[str, Any] = {
    "modulos_ancho": 1,          # 1P / 2P (módulos en vertical a lo ancho)
    "gcr": 0.35,
    "altura_eje_m": 2.0,
    "angulo_max_deg": 60.0,
    "celdas_partidas": True,
}


def ancho_seguidor(largo_modulo_m: float, modulos_ancho: int) -> float:
    """Ancho del seguidor (m): módulos en vertical a lo ancho del eje."""
    n = int(modulos_ancho)
    return n * float(largo_modulo_m) + (n - 1) * SEP_MODULOS_M


def bloques_bypass(modulos_ancho: int, celdas_partidas: bool) -> int:
    """Bloques de celdas a lo ancho que la sombra de la fila vecina puede apagar.

    En vertical, la franja de sombra entra por el borde paralelo al eje y
    toca las tres columnas del módulo: con celdas enteras se apaga todo el
    módulo (1 bloque); con celdas partidas las dos mitades trabajan en
    paralelo (2 bloques).
    """
    return int(modulos_ancho) * (2 if celdas_partidas else 1)


def fraccion_sombreada(rotacion_deg, psi_deg, gcr: float) -> np.ndarray:
    """Fracción del ancho sombreada por la fila vecina (misma rotación, eje horizontal).

    ``f = 1 − cos ψ ÷ (GCR · cos(θ − ψ))``, limitada a 0…1; ψ es el ángulo
    cenital proyectado del sol en el plano perpendicular al eje.
    """
    th = np.radians(np.asarray(rotacion_deg, dtype=float))
    ps = np.radians(np.asarray(psi_deg, dtype=float))
    den = float(gcr) * np.cos(th - ps)
    with np.errstate(divide="ignore", invalid="ignore"):
        f = 1.0 - np.cos(ps) / den
    f = np.where((den > 1e-9) & (np.abs(ps) < np.pi / 2), f, 0.0)
    return np.clip(np.nan_to_num(f, nan=0.0), 0.0, 1.0)


def _luz(tmy, sp, dni_extra, albedo, tilt, azim, gcr, altura, ancho):
    from pvlib.bifacial import infinite_sheds

    return infinite_sheds.get_irradiance(
        surface_tilt=tilt, surface_azimuth=azim, solar_zenith=sp["apparent_zenith"],
        solar_azimuth=sp["azimuth"], gcr=gcr, height=altura, pitch=ancho / gcr,
        ghi=tmy["G_h"], dhi=tmy["Gd_h"], dni=tmy["Gb_n"], albedo=albedo, model="haydavies",
        dni_extra=dni_extra, bifaciality=0.0,
    ).fillna(0.0)


def _mensual(serie: pd.Series) -> list[float]:
    s = serie.groupby(serie.index.month).sum() / 1000.0
    return [round(float(s.get(m, 0.0)), 2) for m in range(1, 13)]


def comparar_seguidor_fijo(tmy: pd.DataFrame, lat: float, lon: float, alt_m: float, albedo: float,
                           fijo: Mapping[str, Any], seguidor: Mapping[str, Any],
                           largo_modulo_m: float) -> dict:
    """POA frontal anual y mensual: estructura fija del campo, seguidor con y sin backtracking.

    ``fijo``: ``tilt_deg``, ``azimut_deg``, ``gcr``, ``altura_m`` (centro),
    ``ancho_m``. ``seguidor``: claves de ``SEGUIDOR_DEFECTO``.
    """
    import pvlib

    sp = pvlib.location.Location(lat, lon, altitude=alt_m).get_solarposition(tmy.index)
    dni_extra = pvlib.irradiance.get_extra_radiation(tmy.index)
    s = {**SEGUIDOR_DEFECTO, **dict(seguidor)}
    gcr = min(max(float(s["gcr"]), 0.05), 0.95)
    ancho = ancho_seguidor(largo_modulo_m, s["modulos_ancho"])
    alt_eje = float(s["altura_eje_m"])
    ang_max = float(s["angulo_max_deg"])

    f = _luz(tmy, sp, dni_extra, albedo, float(fijo["tilt_deg"]), float(fijo["azimut_deg"]),
             float(fijo["gcr"]), float(fijo["altura_m"]), float(fijo["ancho_m"]))

    psi = pvlib.shading.projected_solar_zenith_angle(sp["apparent_zenith"], sp["azimuth"], 0.0,
                                                     EJE_AZIMUT_DEG)
    dia = (sp["apparent_zenith"] < 90.0).to_numpy()
    res_seg = {}
    for clave, bt in (("backtracking", True), ("sin_backtracking", False)):
        tr = pvlib.tracking.singleaxis(sp["apparent_zenith"], sp["azimuth"], axis_tilt=0.0,
                                       axis_azimuth=EJE_AZIMUT_DEG, max_angle=ang_max,
                                       backtrack=bt, gcr=gcr)
        theta = tr["tracker_theta"].fillna(0.0)
        tilt = tr["surface_tilt"].fillna(0.0)
        azim = tr["surface_azimuth"].fillna(90.0)
        luz = _luz(tmy, sp, dni_extra, albedo, tilt, azim, gcr, alt_eje, ancho)
        fs = np.where(dia, fraccion_sombreada(theta, psi.fillna(0.0), gcr), 0.0)
        fs = np.where(fs > FRACCION_MINIMA, fs, 0.0)
        # Luz sin la sombra óptica de la fila vecina, para el modelo eléctrico.
        aoi = pvlib.irradiance.aoi(tilt, azim, sp["apparent_zenith"], sp["azimuth"]).to_numpy()
        directa = np.where(dia & (aoi < 90.0), tmy["Gb_n"].to_numpy() * np.cos(np.radians(aoi)), 0.0)
        directa = np.clip(directa, 0.0, None)
        glob_sin = luz["poa_front"].to_numpy() + (directa - luz["poa_front_direct"].to_numpy())
        nb = bloques_bypass(s["modulos_ancho"], s["celdas_partidas"])
        perdida = pvlib.shading.direct_martinez(glob_sin, directa, fs, np.ceil(fs * nb), nb)
        perdida = np.clip(np.nan_to_num(np.asarray(perdida, dtype=float), nan=0.0), 0.0, 1.0)
        efectiva = pd.Series(np.where(fs > 0, glob_sin * (1.0 - perdida), luz["poa_front"].to_numpy()),
                             index=tmy.index).clip(lower=0.0)
        res_seg[clave] = {
            "poa_optica_kwh_m2": round(float(luz["poa_front"].sum()) / 1000.0, 2),
            "poa_kwh_m2": round(float(efectiva.sum()) / 1000.0, 2),
            "mensual_kwh_m2": _mensual(efectiva),
            "horas_sombra": int((fs > 0).sum()),
            "theta": theta,
        }

    fijo_anual = float(f["poa_front"].sum()) / 1000.0

    def _gan(v):
        return round((v / fijo_anual - 1.0) * 100.0, 2) if fijo_anual > 0 else 0.0

    # Día de ejemplo: 21 de marzo, hora local aproximada por la longitud.
    desfase = int(round(float(lon) / 15.0))
    local = tmy.index + pd.Timedelta(hours=desfase)
    sel = (local.month == 3) & (local.day == 21)
    dia_ej = {"hora": [int(h) for h in local[sel].hour]}
    for clave in res_seg:
        th = res_seg[clave].pop("theta")
        dia_ej[clave] = [round(float(v), 1) for v in th[sel]]

    return {
        "fijo": {"poa_kwh_m2": round(fijo_anual, 2), "mensual_kwh_m2": _mensual(f["poa_front"])},
        **res_seg,
        "ganancia_backtracking_pct": _gan(res_seg["backtracking"]["poa_kwh_m2"]),
        "ganancia_sin_backtracking_pct": _gan(res_seg["sin_backtracking"]["poa_kwh_m2"]),
        "perdida_sombra_electrica_pct": round(
            (1.0 - res_seg["sin_backtracking"]["poa_kwh_m2"] / res_seg["sin_backtracking"]["poa_optica_kwh_m2"])
            * 100.0, 2) if res_seg["sin_backtracking"]["poa_optica_kwh_m2"] > 0 else 0.0,
        "dia_ejemplo": dia_ej,
        "geometria": {"ancho_m": round(ancho, 3), "pitch_m": round(ancho / gcr, 3), "gcr": gcr,
                      "altura_eje_m": alt_eje, "angulo_max_deg": ang_max,
                      "bloques": bloques_bypass(s["modulos_ancho"], s["celdas_partidas"]),
                      "borde_bajo_m": round(alt_eje - ancho / 2.0 * math.sin(math.radians(ang_max)), 2)},
    }


def energia_estimada(e_ac_fijo_kwh: float, comparacion: Mapping[str, Any], clave: str = "backtracking") -> float:
    """Energía con seguidor, de primer orden: E fija × POA seguidor ÷ POA fija."""
    pf = float(comparacion["fijo"]["poa_kwh_m2"])
    return float(e_ac_fijo_kwh) * float(comparacion[clave]["poa_kwh_m2"]) / pf if pf > 0 else 0.0
