# -*- coding: utf-8 -*-
"""Spec ``05-perdidas-y-temperatura/motor-optico-bifacial`` (29-sep-2026).

Con panel bifacial la POA global es cara frontal + bifacialidad × trasera,
pero la cascada óptica armaba la POA después del IAM solo con las
componentes de la cara frontal: el aporte trasero desaparecía sin figurar
como pérdida. Proyecto de Apartadó: POA bruta 1,861, pérdidas 55 + 62 + 90,
POA efectiva 1,497 en vez de 1,654 (faltaban ≈ 157 kWh/m², 8.4 %).
"""
import os

import numpy as np
import pytest

from calculos.motor_optico import (
    cascada_optica,
    iam_ashrae,
    mensaje_impacto_optico,
    poa_publicable,
)
from calculos.solar import calcular_poa
from tests.test_simulation_pipeline import _tmy_sintetico_offline

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG5B = os.path.join(_ROOT, "pages", "5b_🔆_Motor_Optico.py")
_SIN_SUCIEDAD = {m: 0.0 for m in range(1, 13)}
_SUCIEDAD_10 = {m: 0.10 for m in range(1, 13)}
_BIFACIAL = {"bifacialidad": 0.80, "altura_m": 1.0, "gcr": 0.4, "ancho_colector_m": 2.4}


@pytest.fixture(scope="module")
def tmy():
    return _tmy_sintetico_offline(7.883, -76.6259, 44)


@pytest.fixture(scope="module")
def poa_bif(tmy):
    return calcular_poa(tmy, 7.883, -76.6259, 44, 10, 180, albedo=0.20, bifacial=_BIFACIAL)


@pytest.fixture(scope="module")
def poa_mono(tmy):
    return calcular_poa(tmy, 7.883, -76.6259, 44, 10, 180, albedo=0.20)


def _cierre(s):
    """POA bruta − IAM − suciedad − POA que va al SDM (sin térmico).

    El término térmico no entra: las horas frías con ganancia (f_term > 1) se
    recortan a pérdida 0 desde antes de esta Spec y no son parte del defecto.
    """
    return (s["poa_bruta_anual_kWh_m2"] - s["perdida_iam_kWh_m2"]
            - s["perdida_soil_kWh_m2"] - s["poa_post_soil_anual_kWh_m2"])


# ── Criterio 1: conservación en bifacial ─────────────────────────────────────
@pytest.mark.parametrize("suciedad", [_SIN_SUCIEDAD, _SUCIEDAD_10, None])
def test_bifacial_conserva_la_energia(tmy, poa_bif, suciedad):
    _, s = cascada_optica(tmy, poa_bif, soiling_config=suciedad, k_bipv=1.15)
    assert abs(_cierre(s)) < 0.3, _cierre(s)


def test_bifacial_el_aporte_trasero_llega_a_la_poa_optica(tmy, poa_bif):
    r, s = cascada_optica(tmy, poa_bif, soiling_config=_SIN_SUCIEDAD, k_bipv=1.15)
    trasero = float((poa_bif["poa_global"] - poa_bif["poa_front"]).clip(lower=0).sum()) / 1000
    assert s["bifacial"] is True
    assert s["aporte_trasero_kWh_m2"] == pytest.approx(trasero, abs=0.1)
    assert trasero > 150  # el caso sí tiene aporte trasero apreciable
    # la trasera solo pierde la IAM difusa (0.95)
    assert s["aporte_trasero_optico_kWh_m2"] == pytest.approx(0.95 * trasero, abs=0.2)
    np.testing.assert_allclose(
        r["poa_optica"].to_numpy(),
        (r["poa_frontal_optica"] + r["poa_trasera_optica"]).to_numpy(), atol=1e-9)
    # la POA óptica (antes de suciedad) queda cerca de la bruta: solo IAM
    assert s["poa_optica_anual_kWh_m2"] > 0.95 * s["poa_bruta_anual_kWh_m2"]


def test_bifacial_la_cara_frontal_usa_poa_front(tmy, poa_bif):
    r, _ = cascada_optica(tmy, poa_bif, soiling_config=_SIN_SUCIEDAD)
    frontal = float(poa_bif["poa_front"].sum())
    assert float(r["poa_frontal_optica"].sum()) <= frontal
    assert float(r["poa_frontal_optica"].sum()) > 0.95 * frontal


# ── Criterio 2: monofacial sin cambios ───────────────────────────────────────
def test_monofacial_igual_que_antes(tmy, poa_mono):
    r, s = cascada_optica(tmy, poa_mono, b0=0.05, soiling_config=_SIN_SUCIEDAD, f_iam_dif=0.95)
    dir_ = poa_mono["poa_direct"].to_numpy()
    dif = (poa_mono["poa_sky_diffuse"] + poa_mono["poa_ground_diffuse"]).to_numpy()
    dni = tmy["Gb_n"].to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        cos_aoi = np.clip(np.where(dni > 2.0, dir_ / np.maximum(dni, 1.0), 0.0), 0.0, 1.0)
    aoi = np.where(dni <= 2.0, 90.0, np.degrees(np.arccos(cos_aoi)))
    esperado = dir_ * iam_ashrae(aoi, 0.05) + dif * 0.95
    np.testing.assert_allclose(r["poa_optica"].to_numpy(), esperado, rtol=0, atol=1e-9)
    assert s["bifacial"] is False and s["aporte_trasero_kWh_m2"] == 0.0
    assert float(r["poa_trasera_optica"].abs().sum()) == 0.0
    assert abs(_cierre(s)) < 0.3


# ── Criterio 3: suciedad solo en la cara frontal ─────────────────────────────
def test_suciedad_no_se_aplica_a_la_trasera(tmy, poa_bif):
    r, s = cascada_optica(tmy, poa_bif, soiling_config=_SUCIEDAD_10)
    esperado = 0.10 * float(r["poa_frontal_optica"].sum()) / 1000
    assert s["perdida_soil_kWh_m2"] == pytest.approx(esperado, abs=0.2)


# ── Criterio 4: factores promedio ponderados por energía ─────────────────────
@pytest.mark.parametrize("cual", ["mono", "bif"])
def test_factores_promedio_ponderados(tmy, poa_mono, poa_bif, cual):
    poa = poa_mono if cual == "mono" else poa_bif
    _, s = cascada_optica(tmy, poa, soiling_config=_SUCIEDAD_10, k_bipv=1.15)
    bruta = s["poa_bruta_anual_kWh_m2"]
    assert s["f_iam_prom"] == pytest.approx(1 - s["perdida_iam_kWh_m2"] / bruta, abs=2e-4)
    if cual == "mono":
        assert s["f_soil_prom"] == pytest.approx(0.90, abs=2e-3)
    else:  # la suciedad solo pesa sobre la cara frontal
        assert 0.90 < s["f_soil_prom"] < 0.92
    producto = s["f_iam_prom"] * s["f_soil_prom"] * s["f_term_prom"]
    assert producto == pytest.approx(s["factor_global"], abs=5e-4)


# ── Criterio 5: POA que se publica para Producción ───────────────────────────
def test_poa_publicable_bifacial(tmy, poa_bif):
    r, s = cascada_optica(tmy, poa_bif, soiling_config=_SUCIEDAD_10)
    st_df = poa_publicable(poa_bif, r, "poa_post_soil")
    np.testing.assert_allclose(st_df["poa_global"].to_numpy(), r["poa_post_soil"].to_numpy())
    trasero = float((st_df["poa_global"] - st_df["poa_front"]).sum()) / 1000
    assert trasero == pytest.approx(s["aporte_trasero_optico_kWh_m2"], abs=0.2)
    assert poa_bif["poa_global"].sum() > st_df["poa_global"].sum()  # no se toca el original


def test_poa_publicable_monofacial(tmy, poa_mono):
    r, _ = cascada_optica(tmy, poa_mono, soiling_config=_SUCIEDAD_10)
    st_df = poa_publicable(poa_mono, r, "poa_efectiva")
    np.testing.assert_allclose(st_df["poa_global"].to_numpy(), r["poa_efectiva"].to_numpy())
    assert "poa_front" not in st_df.columns


def test_la_pagina_publica_con_poa_publicable():
    with open(_PAG5B, encoding="utf-8") as f:
        src = f.read()
    assert 'poa_publicable(poa_df, result_df, "poa_post_soil")' in src
    assert 'poa_publicable(poa_df, result_df, "poa_efectiva")' in src
    assert "aporte_trasero_optico_kWh_m2" in src


# ── Criterio 6: aviso según la inclinación ───────────────────────────────────
def test_aviso_no_dice_fachada_fijo():
    with open(_PAG5B, encoding="utf-8") as f:
        src = f.read()
    assert "significativa para una fachada vertical" not in src
    assert "mensaje_impacto_optico(" in src


@pytest.mark.parametrize("tilt, texto", [
    (90, "fachada"), (80, "fachada"), (30, "superficie inclinada"), (10, "casi horizontal"),
])
def test_mensaje_impacto_segun_inclinacion(tilt, texto):
    nivel, msg = mensaje_impacto_optico(19.6, tilt)
    assert nivel == "warning" and texto in msg and "19.6" in msg


def test_mensaje_impacto_niveles():
    assert mensaje_impacto_optico(10.0, 10)[0] == "info"
    assert mensaje_impacto_optico(5.0, 10)[0] == "success"
    assert "IAM" not in mensaje_impacto_optico(19.6, 10)[1]  # en granja el IAM no domina


# ── Criterio 7: cadena multi-superficie ──────────────────────────────────────
def test_cadena_multisuperficie_no_cuenta_la_trasera_como_iam(tmy, poa_bif):
    r, _ = cascada_optica(tmy, poa_bif, soiling_config=_SIN_SUCIEDAD)
    f_iam = float(r["poa_optica"].sum()) / float(r["poa_bruta"].sum())
    assert f_iam > 0.95  # antes ≈ 0.89: el aporte trasero se contaba como IAM


# ── Criterio 8: manual del Asistente ─────────────────────────────────────────
@pytest.mark.parametrize("pregunta, texto", [
    ("por que la POA efectiva del motor optico es menor con panel bifacial", "1,654"),
    ("el motor optico pierde la ganancia bifacial de la cara trasera", "casi no acumula polvo"),
    ("que significa factor IAM promedio en el motor optico", "ponderado por energía"),
])
def test_manual_explica_bifacial(pregunta, texto):
    from calculos.asistente import BaseConocimiento
    secciones = BaseConocimiento.cargar().buscar(pregunta, k=6)
    candidatas = [s for s in secciones if "cara trasera en el motor óptico" in s["titulo"].lower()]
    assert candidatas, [s["titulo"] for s in secciones]
    assert texto in "\n".join(s["texto"] for s in candidatas)
