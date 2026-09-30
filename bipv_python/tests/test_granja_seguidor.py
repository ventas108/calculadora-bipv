# -*- coding: utf-8 -*-
"""Spec ``05-perdidas-y-temperatura/seguidor-un-eje`` (granja FV fase 4, 30-sep-2026).

Seguidor de un eje Norte–Sur con y sin backtracking frente a la estructura
fija del campo, con el mismo modelo de filas (``infinite_sheds``). Sin
backtracking, la franja de sombra de la fila vecina se lleva a pérdida
eléctrica con ``pvlib.shading.direct_martinez``. Caso Apartadó.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
import pytest

from calculos.seguidor import (
    SEGUIDOR_DEFECTO,
    ancho_seguidor,
    bloques_bypass,
    comparar_seguidor_fijo,
    energia_estimada,
    fraccion_sombreada,
)

LAT, LON, ALT_M = 7.884, -76.635, 30.0
LARGO = 2.384
FIJO = {"tilt_deg": 10.0, "azimut_deg": 180.0, "gcr": 0.398, "altura_m": 2.628, "ancho_m": 2.626}
PAGINAS = Path(__file__).resolve().parents[1] / "pages"


@pytest.fixture(scope="module")
def tmy():
    idx = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    loc = pvlib.location.Location(latitude=LAT, longitude=LON, altitude=ALT_M, tz="UTC")
    cs = loc.get_clearsky(idx, model="ineichen")
    zen = loc.get_solarposition(idx)["apparent_zenith"].to_numpy()
    cosz = np.clip(np.cos(np.radians(zen)), 0.0, None)
    ghi = cs["ghi"].to_numpy() * 0.8
    dhi = np.minimum(ghi, 0.45 * cs["ghi"].to_numpy())
    dni = np.where(cosz > 0.05, (ghi - dhi) / np.maximum(cosz, 0.05), 0.0)
    return pd.DataFrame({"G_h": ghi, "Gb_n": dni, "Gd_h": dhi, "T2m": 27.0}, index=idx)


@pytest.fixture(scope="module")
def comp(tmy):
    return comparar_seguidor_fijo(tmy, LAT, LON, ALT_M, 0.20, FIJO, SEGUIDOR_DEFECTO, LARGO)


# ── Geometría ────────────────────────────────────────────────────────────────
def test_ancho_y_bloques():
    assert ancho_seguidor(LARGO, 1) == pytest.approx(2.384)
    assert ancho_seguidor(LARGO, 2) == pytest.approx(2 * 2.384 + 0.02)
    assert bloques_bypass(1, True) == 2 and bloques_bypass(1, False) == 1
    assert bloques_bypass(2, True) == 4


@pytest.mark.parametrize("zen,az", [(75, 90), (80, 95), (70, 270), (78, 260), (30, 90), (85, 100)])
def test_fraccion_sombreada_igual_a_pvlib(zen, az):
    gcr = 0.35
    psi = float(pvlib.shading.projected_solar_zenith_angle(zen, az, 0.0, 180.0))
    theta = float(np.clip(psi, -60, 60))          # seguimiento real, sin backtracking
    mia = float(fraccion_sombreada(theta, psi, gcr))
    ref = float(pvlib.shading.shaded_fraction1d(zen, az, 180.0, theta, collector_width=LARGO,
                                                pitch=LARGO / gcr))
    assert mia == pytest.approx(ref, abs=1e-6)


def test_backtracking_nunca_se_sombrea():
    zen = np.array([60.0, 70.0, 80.0, 85.0, 75.0])
    az = np.array([90.0, 95.0, 100.0, 265.0, 270.0])
    tr = pvlib.tracking.singleaxis(zen, az, axis_azimuth=180.0, max_angle=60.0, backtrack=True, gcr=0.35)
    psi = pvlib.shading.projected_solar_zenith_angle(zen, az, 0.0, 180.0)
    assert np.all(fraccion_sombreada(np.asarray(tr["tracker_theta"], dtype=float), psi, 0.35) < 1e-6)


# ── Comparación en Apartadó ──────────────────────────────────────────────────
def test_seguidor_gana_frente_a_la_fija(comp):
    assert comp["backtracking"]["poa_kwh_m2"] > comp["fijo"]["poa_kwh_m2"]
    assert 10.0 < comp["ganancia_backtracking_pct"] < 40.0
    assert comp["ganancia_backtracking_pct"] == pytest.approx(
        (comp["backtracking"]["poa_kwh_m2"] / comp["fijo"]["poa_kwh_m2"] - 1) * 100, abs=0.01)


def test_backtracking_sin_horas_de_sombra_y_sin_perdida_electrica(comp):
    bt = comp["backtracking"]
    assert bt["horas_sombra"] == 0
    assert bt["poa_kwh_m2"] == pytest.approx(bt["poa_optica_kwh_m2"], abs=0.01)


def test_sin_backtracking_pierde_por_sombra_electrica(comp):
    sb = comp["sin_backtracking"]
    assert sb["horas_sombra"] > 0
    assert sb["poa_kwh_m2"] < sb["poa_optica_kwh_m2"]
    assert comp["perdida_sombra_electrica_pct"] > 0.5
    assert comp["backtracking"]["poa_kwh_m2"] > sb["poa_kwh_m2"]


def test_celdas_enteras_pierden_mas_que_partidas(tmy):
    partidas = comparar_seguidor_fijo(tmy, LAT, LON, ALT_M, 0.20, FIJO, dict(SEGUIDOR_DEFECTO), LARGO)
    enteras = comparar_seguidor_fijo(tmy, LAT, LON, ALT_M, 0.20, FIJO,
                                     dict(SEGUIDOR_DEFECTO, celdas_partidas=False), LARGO)
    assert enteras["perdida_sombra_electrica_pct"] > partidas["perdida_sombra_electrica_pct"]
    assert enteras["backtracking"]["poa_kwh_m2"] == pytest.approx(partidas["backtracking"]["poa_kwh_m2"])


def test_mensual_suma_el_anual_y_dia_de_ejemplo(comp):
    for k in ("fijo", "backtracking", "sin_backtracking"):
        assert len(comp[k]["mensual_kwh_m2"]) == 12
        assert sum(comp[k]["mensual_kwh_m2"]) == pytest.approx(comp[k]["poa_kwh_m2"], abs=0.2)
    de = comp["dia_ejemplo"]
    assert len(de["hora"]) == 24
    assert max(abs(v) for v in de["sin_backtracking"]) <= 60.0 + 1e-6
    # Con backtracking el giro nunca supera al del seguimiento real
    assert all(abs(b) <= abs(s) + 1e-6 for b, s in zip(de["backtracking"], de["sin_backtracking"]))
    assert min(de["backtracking"]) < 0 < max(de["backtracking"])       # mañana al Este, tarde al Oeste


def test_geometria_y_borde_bajo(comp):
    g = comp["geometria"]
    assert g["pitch_m"] == pytest.approx(LARGO / 0.35, abs=1e-3)
    assert g["borde_bajo_m"] == pytest.approx(2.0 - LARGO / 2 * np.sin(np.radians(60)), abs=0.01)


def test_energia_estimada_proporcional(comp):
    e = energia_estimada(340_381.0, comp)
    assert e == pytest.approx(340_381.0 * comp["backtracking"]["poa_kwh_m2"] / comp["fijo"]["poa_kwh_m2"])


# ── Página y manual ──────────────────────────────────────────────────────────
def test_pagina_granja_compara_el_seguidor():
    src = next(PAGINAS.glob("9b_*Granja_FV.py")).read_text(encoding="utf-8")
    for t in ("comparar_seguidor_fijo(", "energia_estimada(", "granja_seg_gcr", "granja_seguidor",
              "Comparar seguidor y estructura fija", "sección 7"):
        assert t in src, t


def test_manual_del_asistente_lo_explica():
    kb = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 96."):]
    for texto in ("backtracking", "diodos de bypass", "celdas partidas", "Comparar seguidor y estructura fija",
                  "24 %", "misma luz directa"):
        assert texto in seccion, texto
    assert "PVsyst" not in seccion
