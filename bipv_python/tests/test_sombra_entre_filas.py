# -*- coding: utf-8 -*-
"""Spec ``05-perdidas-y-temperatura/sombra-entre-filas`` (granja FV fase 2, 30-sep-2026).

La energía usa la geometría del campo de 🌾 Granja FV: sombra mutua entre
filas en la cara frontal (paneles monofaciales), ancho real de la mesa en el
modelo bifacial (antes fijo en 2,0 m sin mostrarse) y dos factores de la
cara trasera (sombra de la estructura y mismatch trasero). Referencia:
Apartadó en la referencia estándar internacional — GCR 39,8 %, inclinación
10°, mesa 2,626 m, sombra cercana −0,20 %, sombra trasera 5 %, mismatch
trasero 10 %.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
import pytest

from calculos.granja_fv import (
    GEOMETRIA_DEFECTO,
    aplicar_geometria_a_energia,
    calcular_campo,
    coherencia_campo,
    dimensiones_modulo,
    estado_poa_filas,
    geometria_filas,
    geometria_poa,
    mismas_filas,
    sombra_filas_estimada,
)
from calculos.solar import aplicar_sombra_filas, calcular_poa

LAT, LON, ALT_M = 7.884, -76.635, 30.0     # Apartadó / Urabá
TILT, AZ = 10.0, 180.0
PAGINAS = Path(__file__).resolve().parents[1] / "pages"
JAM = {"nombre": "JA Solar JAM66D46-720/LB", "dimensiones_mm": "2384x1303x33 mm",
       "area_m2": 3.1064, "Pmax_stc": 720.0}
FILAS_APARTADO = {"gcr": 0.398, "altura_m": 2.628, "ancho_colector_m": 2.626}


@pytest.fixture(scope="module")
def tmy():
    """TMY offline con nubes: difusa = 45 % del GHI de cielo claro (determinista)."""
    idx = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    loc = pvlib.location.Location(latitude=LAT, longitude=LON, altitude=ALT_M, tz="UTC")
    cs = loc.get_clearsky(idx, model="ineichen")
    zen = loc.get_solarposition(idx)["apparent_zenith"].to_numpy()
    cosz = np.clip(np.cos(np.radians(zen)), 0.0, None)
    ghi = cs["ghi"].to_numpy() * 0.8
    dhi = np.minimum(ghi, 0.45 * cs["ghi"].to_numpy())
    dni = np.where(cosz > 0.05, (ghi - dhi) / np.maximum(cosz, 0.05), 0.0)
    return pd.DataFrame({"G_h": ghi, "Gb_n": dni, "Gd_h": dhi,
                         "T2m": 27.0, "WS10m": 1.5, "SP": 101_325.0}, index=idx)


def _geo(**kw):
    g = dict(GEOMETRIA_DEFECTO)
    g.update(dict(tilt_deg=10.0, azimut_deg=180.0, ancho_terreno_m=80.0, largo_terreno_m=30.0,
                  modulos_pendiente=2, orientacion="horizontal", modulos_por_mesa=31,
                  mesas_por_fila=1, pasillo_m=3.0, pitch_m=6.60, altura_libre_m=2.4))
    g.update(kw)
    return g


def _campo(**kw):
    return calcular_campo(_geo(**kw), dimensiones_modulo(JAM), 308, pmax_w=720.0)


def _anual(poa, col="poa_global"):
    return float(poa[col].sum()) / 1000.0


# ── Cara frontal: sombra entre filas (monofacial) ────────────────────────────
def test_sin_filas_es_identico_a_antes(tmy):
    a = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ)
    b = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ, filas=None)
    pd.testing.assert_frame_equal(a, b)


def test_filas_nunca_suben_la_irradiancia_hora_a_hora(tmy):
    a = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ)
    b = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ, filas=FILAS_APARTADO)
    for col in ("poa_direct", "poa_sky_diffuse", "poa_ground_diffuse", "poa_global"):
        assert (b[col].to_numpy() <= a[col].to_numpy() + 1e-9).all(), col


def test_componentes_suman_el_global(tmy):
    b = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ, filas=FILAS_APARTADO)
    np.testing.assert_allclose(b["poa_diffuse"], b["poa_sky_diffuse"] + b["poa_ground_diffuse"], atol=1e-9)
    np.testing.assert_allclose(b["poa_global"], (b["poa_direct"] + b["poa_diffuse"]).clip(lower=0), atol=1e-9)


def test_apartado_pierde_como_la_referencia(tmy):
    # Referencia estándar internacional: sombra cercana −0,20 % (GCR 39,8 %, 10°)
    a = _anual(calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ))
    b = _anual(calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ, filas=FILAS_APARTADO))
    perdida = (1 - b / a) * 100
    assert 0.05 <= perdida <= 0.5


def test_filas_mas_juntas_pierden_mas(tmy):
    base = _anual(calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ))
    perdidas = []
    for gcr in (0.3, 0.5, 0.8):
        b = _anual(calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ,
                                filas=dict(FILAS_APARTADO, gcr=gcr)))
        perdidas.append(1 - b / base)
    assert perdidas[0] < perdidas[1] < perdidas[2]


def test_mas_inclinacion_con_filas_juntas_pierde_mas(tmy):
    def perdida(tilt):
        a = _anual(calcular_poa(tmy, LAT, LON, ALT_M, tilt, AZ))
        b = _anual(calcular_poa(tmy, LAT, LON, ALT_M, tilt, AZ, filas=dict(FILAS_APARTADO, gcr=0.6)))
        return 1 - b / a
    assert perdida(10.0) < perdida(30.0)


def test_aplicar_sombra_filas_conserva_los_atributos(tmy):
    a = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ)
    a.attrs["marca"] = "x"
    loc = pvlib.location.Location(LAT, LON, altitude=ALT_M)
    sp = loc.get_solarposition(tmy.index)
    dni_extra = pvlib.irradiance.get_extra_radiation(tmy.index)
    b = aplicar_sombra_filas(a, tmy, sp, dni_extra, TILT, AZ, 0.20, FILAS_APARTADO)
    assert b.attrs.get("marca") == "x"


# ── Cara trasera: sombra de la estructura y mismatch trasero ─────────────────
_BIF = {"bifacialidad": 0.80, "altura_m": 2.628, "albedo_trasero": 0.20, "gcr": 0.398,
        "factor_vista_trasera": 1.0, "ancho_colector_m": 2.626}


def test_factores_traseros_en_cero_no_cambian_nada(tmy):
    a = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ, bifacial=_BIF)
    b = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ,
                     bifacial=dict(_BIF, sombra_trasera_pct=0.0, mismatch_trasero_pct=0.0))
    pd.testing.assert_frame_equal(a, b)


def test_factores_traseros_de_la_referencia_bajan_la_trasera_exacto(tmy):
    a = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ, bifacial=_BIF)
    b = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ,
                     bifacial=dict(_BIF, sombra_trasera_pct=5.0, mismatch_trasero_pct=10.0))
    f = 0.95 * 0.90
    np.testing.assert_allclose(b["poa_rear"], a["poa_rear"] * f, rtol=1e-9, atol=1e-9)
    np.testing.assert_allclose(b["poa_front"], a["poa_front"], atol=1e-9)
    np.testing.assert_allclose(b["poa_global"], b["poa_front"] + 0.80 * b["poa_rear"], atol=1e-6)


def test_ancho_de_mesa_cambia_el_modelo_bifacial(tmy):
    a = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ, bifacial=dict(_BIF, ancho_colector_m=2.0))
    b = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZ, bifacial=_BIF)
    assert _anual(a, "poa_rear") != pytest.approx(_anual(b, "poa_rear"), rel=1e-6)


# ── Geometría del campo → energía ────────────────────────────────────────────
def test_geometria_filas_de_apartado():
    g = geometria_filas(_campo())
    assert g["gcr"] == pytest.approx(0.3979, abs=1e-4)
    assert g["ancho_colector_m"] == pytest.approx(2.626)
    assert g["altura_m"] == pytest.approx(2.4 + 2.626 * np.sin(np.radians(10)) / 2, abs=1e-3)


def test_geometria_poa_prefiere_el_modelo_bifacial():
    assert geometria_poa({"gcr": 0.4, "altura_m": 2.6}, FILAS_APARTADO) == \
        {"gcr": 0.4, "altura_m": 2.6, "ancho_colector_m": 2.0}
    assert geometria_poa(None, FILAS_APARTADO) == FILAS_APARTADO
    assert geometria_poa({}, None) is None


def test_mismas_filas_con_tolerancia():
    assert mismas_filas(FILAS_APARTADO, dict(FILAS_APARTADO, gcr=0.41))
    assert not mismas_filas(FILAS_APARTADO, dict(FILAS_APARTADO, gcr=0.45))
    assert not mismas_filas(FILAS_APARTADO, dict(FILAS_APARTADO, ancho_colector_m=2.0))
    assert not mismas_filas(None, FILAS_APARTADO)


def test_usar_geometria_monofacial_solo_escribe_filas_energia():
    estado = {"bifacial_activo": False, "bifacial_cfg": {}}
    geo = aplicar_geometria_a_energia(estado, _campo())
    assert estado["filas_energia"] == geo
    assert estado["bifacial_cfg"] == {}


def test_usar_geometria_bifacial_actualiza_el_modelo_y_conserva_lo_demas():
    estado = {"bifacial_activo": True,
              "bifacial_cfg": {"bifacialidad": 0.8, "gcr": 0.25, "altura_m": 1.0, "sombra_trasera_pct": 5.0}}
    original = estado["bifacial_cfg"]
    geo = aplicar_geometria_a_energia(estado, _campo())
    cfg = estado["bifacial_cfg"]
    assert (cfg["gcr"], cfg["altura_m"], cfg["ancho_colector_m"]) == \
        (geo["gcr"], geo["altura_m"], geo["ancho_colector_m"])
    assert cfg["bifacialidad"] == 0.8 and cfg["sombra_trasera_pct"] == 5.0
    assert original["gcr"] == 0.25          # no muta el dict anterior


def test_estado_poa_filas_verde_naranja():
    c = _campo()
    assert estado_poa_filas(c, {"poa_geometria_filas": geometria_filas(c)})["nivel"] == "🟢"
    sin = estado_poa_filas(c, {})
    assert sin["nivel"] == "🟠" and "Usar la geometría del campo" in sin["texto"]
    otra = estado_poa_filas(c, {"poa_geometria_filas": {"gcr": 0.25, "altura_m": 1.0,
                                                        "ancho_colector_m": 2.0}})
    assert otra["nivel"] == "🟠" and "0.25" in otra["texto"] and "Recurso Solar" in otra["texto"]


def test_coherencia_incluye_el_chequeo_de_la_poa():
    c = _campo()
    ids = [x["id"] for x in coherencia_campo(c, {"N_paneles_final": 308})]
    assert "poa_filas" in ids


def test_sombra_estimada_de_apartado(tmy):
    r = sombra_filas_estimada(tmy, LAT, LON, ALT_M, TILT, AZ, 0.20, _campo())
    assert r["poa_con_kwh_m2"] < r["poa_sin_kwh_m2"]
    assert 0.05 <= r["perdida_frontal_pct"] <= 0.5


# ── Páginas y manual ─────────────────────────────────────────────────────────
def _fuente(patron):
    return next(PAGINAS.glob(patron)).read_text(encoding="utf-8")


def test_recurso_solar_usa_la_geometria_del_campo():
    src = _fuente("2_*Recurso_Solar.py")
    for t in ("ancho_colector_m", "sombra_trasera_pct", "mismatch_trasero_pct",
              "filas=_filas_energia", "poa_geometria_filas", "geometria_poa("):
        assert t in src, t


def test_granja_ofrece_el_boton_y_la_estimacion():
    src = _fuente("9b_*Granja_FV.py")
    for t in ("aplicar_geometria_a_energia", "sombra_filas_estimada(", "lat_proyecto", "lon_proyecto"):
        assert t in src, t
    assert 'ss.get("lat")' not in src


def test_manual_del_asistente_lo_explica():
    kb = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 94."):]
    for texto in ("sombra entre filas", "Usar la geometría del campo en la energía", "0,20",
                  "5 %", "10 %", "Ancho de la mesa"):
        assert texto in seccion, texto
    assert "PVsyst" not in seccion
