# -*- coding: utf-8 -*-
"""Spec ``03-dimensionamiento/granja-agrivoltaica`` (granja FV fase 3, 30-sep-2026).

Luz que llega al cultivo bajo y entre las filas, mapa de sombra en el suelo
y paso de la maquinaria. Validado contra las funciones 2D de
``pvlib.bifacial.utils`` (factor de vista suelo-cielo y fracción del suelo
con sol directo). Caso Apartadó: mesas de 2 × JAM66D46-720/LB horizontales,
inclinación 10°, separación 6,60 m, altura libre 2,4 m.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
import pytest
from pvlib.bifacial import utils as pvu

from calculos.agrivoltaica import (
    ALTURA_CATEGORIA_I_M,
    geometria_corte,
    luz_en_el_suelo,
    paso_maquinaria,
    puntos_suelo,
    sol_en_el_suelo,
    vista_cielo_suelo,
)
from calculos.granja_fv import GEOMETRIA_DEFECTO, calcular_campo, dimensiones_modulo

LAT, LON, ALT_M = 7.884, -76.635, 30.0
PAGINAS = Path(__file__).resolve().parents[1] / "pages"
JAM = {"nombre": "JA Solar JAM66D46-720/LB", "dimensiones_mm": "2384x1303x33 mm",
       "area_m2": 3.1064, "Pmax_stc": 720.0}
P, W, T, H0 = 6.60, 2.626, 10.0, 2.4
HU, DZ = W * np.cos(np.radians(T)), W * np.sin(np.radians(T))


@pytest.fixture(scope="module")
def tmy():
    """TMY offline con nubes: difusa = 45 % del GHI de cielo claro (determinista)."""
    idx = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    loc = pvlib.location.Location(latitude=LAT, longitude=LON, altitude=ALT_M, tz="UTC")
    cs = loc.get_clearsky(idx, model="ineichen")
    ghi = cs["ghi"].to_numpy() * 0.8
    dhi = np.minimum(ghi, 0.45 * cs["ghi"].to_numpy())
    return pd.DataFrame({"G_h": ghi, "Gb_n": 0.0, "Gd_h": dhi, "T2m": 27.0}, index=idx)


def _campo(**kw):
    g = dict(GEOMETRIA_DEFECTO)
    g.update(dict(tilt_deg=10.0, azimut_deg=180.0, ancho_terreno_m=80.0, largo_terreno_m=30.0,
                  modulos_pendiente=2, orientacion="horizontal", modulos_por_mesa=31,
                  mesas_por_fila=1, pasillo_m=3.0, pitch_m=6.60, altura_libre_m=2.4))
    g.update(kw)
    return calcular_campo(g, dimensiones_modulo(JAM), 308, pmax_w=720.0)


# ── Geometría del corte ──────────────────────────────────────────────────────
def test_geometria_corte_de_apartado():
    g = geometria_corte(_campo())
    assert g["pitch"] == pytest.approx(P)
    assert g["huella"] == pytest.approx(HU)
    assert g["h0"] == pytest.approx(H0)
    assert g["dz"] == pytest.approx(DZ)


# ── Contra pvlib ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("tilt,h0", [(10.0, 2.4), (0.0, 1.0), (30.0, 3.0)])
def test_vista_del_cielo_igual_a_pvlib(tilt, h0):
    hu, dz = W * np.cos(np.radians(tilt)), W * np.sin(np.radians(tilt))
    y = puntos_suelo(P, 24)
    mia = vista_cielo_suelo(y, P, hu, h0, dz, max_filas=10)
    ref = pvu.vf_ground_sky_2d(tilt, W / P, (y - hu / 2) / P, P, h0 + dz / 2, max_rows=10)[:, 0]
    np.testing.assert_allclose(mia, ref, atol=2e-3)


def test_sol_directo_igual_a_pvlib():
    cenit = np.array([20.0, 30.0, 50.0, 70.0, 60.0])
    az_sol = np.array([0.0, 180.0, 120.0, 250.0, 90.0])
    tan_phi = np.cos(np.radians(az_sol - 180.0)) * np.tan(np.radians(cenit))
    mia = sol_en_el_suelo(puntos_suelo(P, 3000), P, HU, H0, DZ, tan_phi).mean(axis=1)
    ref = pvu._unshaded_ground_fraction(T, 180.0, cenit, az_sol, W / P)
    np.testing.assert_allclose(mia, ref, atol=1e-3)


def test_sol_al_mediodia_la_sombra_esta_bajo_la_mesa():
    y = puntos_suelo(P, 60)
    sol = sol_en_el_suelo(y, P, HU, H0, DZ, [0.0])[0]      # sol en el cenit
    assert (sol[y < HU - 0.1] == 0).all()
    assert (sol[y > HU + 0.1] == 1).all()


# ── Luz en el suelo ──────────────────────────────────────────────────────────
def test_apartado_luz_media_cercana_a_uno_menos_gcr(tmy):
    r = luz_en_el_suelo(tmy, LAT, LON, ALT_M, _campo())
    assert r["media_pct"] == pytest.approx(100 * (1 - W / P), abs=3.0)       # ≈ 60 %
    assert r["bajo_mesa_pct"] < r["media_pct"] < r["entre_filas_pct"]
    assert r["media_kwh_m2"] == pytest.approx(r["referencia_kwh_m2"] * r["media_pct"] / 100, rel=1e-3)
    assert r["referencia_kwh_m2"] == pytest.approx(tmy["G_h"].sum() / 1000, rel=1e-6)
    assert 0 < r["min_pct"] <= r["max_pct"] < 100
    assert r["homogeneidad"] == pytest.approx(r["min_pct"] / r["max_pct"], abs=1e-3)


def test_mapa_mensual_tiene_12_meses_por_punto(tmy):
    r = luz_en_el_suelo(tmy, LAT, LON, ALT_M, _campo(), n=30)
    assert len(r["y_m"]) == len(r["pct"]) == 30
    assert len(r["mensual_pct"]) == 12 and all(len(f) == 30 for f in r["mensual_pct"])
    assert all(0 <= v <= 100 for f in r["mensual_pct"] for v in f)


def test_mas_altura_reparte_mejor_la_luz(tmy):
    baja = luz_en_el_suelo(tmy, LAT, LON, ALT_M, _campo(altura_libre_m=2.4))
    alta = luz_en_el_suelo(tmy, LAT, LON, ALT_M, _campo(altura_libre_m=4.0))
    assert alta["homogeneidad"] > baja["homogeneidad"]
    assert alta["media_pct"] == pytest.approx(baja["media_pct"], abs=1.5)


def test_filas_separadas_dejan_pasar_casi_toda_la_luz(tmy):
    juntas = luz_en_el_suelo(tmy, LAT, LON, ALT_M, _campo())
    separadas = luz_en_el_suelo(tmy, LAT, LON, ALT_M, _campo(pitch_m=20.0, largo_terreno_m=100.0))
    assert separadas["media_pct"] > juntas["media_pct"]
    assert separadas["max_pct"] > 97


# ── Maquinaria ───────────────────────────────────────────────────────────────
def _niveles(checks):
    return {c["id"]: c["nivel"] for c in checks}


def test_apartado_categoria_i_y_maquinaria_por_el_corredor():
    checks = paso_maquinaria(_campo(), altura_maquina_m=2.5, ancho_maquina_m=2.2)
    niv = _niveles(checks)
    assert niv == {"categoria": "🟢", "maquinaria_bajo": "🟠", "maquinaria_entre": "🟢"}
    texto = " ".join(c["texto"] for c in checks)
    assert "2.80 m" in texto and "4.01 m" in texto


def test_maquina_baja_pasa_por_debajo():
    niv = _niveles(paso_maquinaria(_campo(), altura_maquina_m=2.0, ancho_maquina_m=5.0))
    assert niv["maquinaria_bajo"] == "🟢"
    assert niv["maquinaria_entre"] == "🟢"          # el corredor angosto no importa


def test_categoria_ii_y_ninguna_via():
    c = _campo(altura_libre_m=1.0, pitch_m=4.0)
    assert geometria_corte(c)["h0"] < ALTURA_CATEGORIA_I_M
    niv = _niveles(paso_maquinaria(c, altura_maquina_m=2.5, ancho_maquina_m=2.2))
    assert niv == {"categoria": "🟡", "maquinaria_bajo": "🟠", "maquinaria_entre": "🟠"}


# ── Página y manual ──────────────────────────────────────────────────────────
def _fuente(patron):
    return next(PAGINAS.glob(patron)).read_text(encoding="utf-8")


def test_pagina_granja_muestra_la_agrivoltaica():
    src = _fuente("9b_*Granja_FV.py")
    for t in ("luz_en_el_suelo(", "paso_maquinaria(", "granja_altura_maquinaria_m",
              "granja_ancho_maquinaria_m", "go.Heatmap", "granja_luz_suelo"):
        assert t in src, t
    assert "no cambia la energía" not in src


def test_manual_del_asistente_lo_explica():
    kb = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 95."):]
    for texto in ("luz que llega al cultivo", "categoría I", "2,10 m", "homogeneidad", "60 %",
                  "Calcular la luz en el suelo", "mapa de sombra"):
        assert texto in seccion, texto
    assert "PVsyst" not in seccion
