# -*- coding: utf-8 -*-
"""Spec ``05-perdidas-y-temperatura/mismatch-orientacion-horario`` (29-sep-2026).

Módulos de distinta orientación en el mismo string: la app usaba los totales
anuales (σ²/2μ²) y daba 0.00 % para fachadas Este/Oeste, que hora a hora con
diodos de bypass pierden ≈ 14.9 %. Cada prueba termina en lo que recibe el
motor de 📊 Producción.
"""
import os

import numpy as np
import pandas as pd
import pytest

from calculos.mismatch import (
    aplicar_factor_horario,
    calcular_mismatch_orientacion,
    calcular_sombreado_horizonte,
    factores_mismatch_produccion,
    firma_orientacion,
    perdida_string_bypass,
    publicar_cascada_mismatch,
)
from calculos.solar import calcular_poa
from tests.test_simulation_pipeline import _tmy_sintetico_offline

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG5 = os.path.join(_ROOT, "pages", "5_🔀_Mismatch.py")
LAT, LON, ALT = 7.883, -76.6259, 44
E_O = [{"azimuth": 90, "tilt": 90, "fraccion": 0.5, "label": "Este"},
       {"azimuth": 270, "tilt": 90, "fraccion": 0.5, "label": "Oeste"}]


@pytest.fixture(scope="module")
def tmy():
    return _tmy_sintetico_offline(LAT, LON, ALT)


@pytest.fixture(scope="module")
def res_eo(tmy):
    return calcular_mismatch_orientacion(tmy, LAT, LON, ALT, E_O)


# ── Criterio 1: cuentas a mano ───────────────────────────────────────────────
def test_string_con_bypass_casos_a_mano():
    ideal, string = perdida_string_bypass([[800.0, 1000.0, 500.0, 0.0],
                                           [100.0, 900.0, 500.0, 0.0]], [0.5, 0.5])
    np.testing.assert_allclose(ideal, [450.0, 950.0, 500.0, 0.0])
    # 800/100: mejor a la corriente del fuerte (el débil puenteado): 800 × 0.5
    # 1000/900: mejor a la corriente del débil, todos aportan: 900 × 1.0
    np.testing.assert_allclose(string, [400.0, 900.0, 500.0, 0.0])


def test_string_tres_grupos():
    ideal, string = perdida_string_bypass([[1000.0], [600.0], [200.0]], [0.2, 0.5, 0.3])
    # candidatos: 1000×0.2=200, 600×0.7=420, 200×1.0=200 → 420; ideal 200+300+60
    assert string[0] == pytest.approx(420.0) and ideal[0] == pytest.approx(560.0)


# ── Criterio 2 y 3: Apartadó ─────────────────────────────────────────────────
def test_este_oeste_ya_no_da_cero(res_eo):
    assert res_eo["modelo"] == "bypass_horario"
    assert 13.0 < res_eo["factor_mismatch_pct"] < 17.0          # ≈ 14.9 %
    assert res_eo["factor_mismatch_pct_anual_aprox"] < 0.1       # lo que daba antes
    f = res_eo["factor_horario"]
    assert isinstance(f, pd.Series) and len(f) == 8760
    assert f.min() >= 0.0 and f.max() <= 1.0 + 1e-12


def test_perdida_ponderada_por_energia(tmy, res_eo):
    g = [calcular_poa(tmy, LAT, LON, ALT, c["tilt"], c["azimuth"])["poa_global"].to_numpy() for c in E_O]
    ideal, string = perdida_string_bypass(g, [0.5, 0.5])
    esperado = (1 - string.sum() / ideal.sum()) * 100
    assert res_eo["factor_mismatch_pct"] == pytest.approx(esperado, abs=0.01)
    assert res_eo["energia_perdida_kWh_m2"] == pytest.approx(ideal.sum() / 1000 * esperado / 100, abs=0.2)


def test_una_orientacion_no_pierde(tmy):
    r = calcular_mismatch_orientacion(tmy, LAT, LON, ALT, [dict(E_O[0], fraccion=1.0)])
    assert r["factor_mismatch_pct"] == 0.0
    assert np.all(r["factor_horario"].to_numpy() == 1.0)


# ── Criterio 4: albedo y bifacial del proyecto ───────────────────────────────
def test_usa_albedo_y_bifacial_del_proyecto(tmy):
    base = calcular_mismatch_orientacion(tmy, LAT, LON, ALT, E_O)
    otro = calcular_mismatch_orientacion(tmy, LAT, LON, ALT, E_O, albedo=0.40)
    bif = calcular_mismatch_orientacion(
        tmy, LAT, LON, ALT, E_O, albedo=0.20,
        bifacial={"bifacialidad": 0.8, "altura_m": 1.0, "gcr": 0.4, "ancho_colector_m": 2.4})
    assert otro["poas"][0]["poa_anual"] > base["poas"][0]["poa_anual"]
    assert bif["poas"][0]["poa_anual"] > base["poas"][0]["poa_anual"]


def test_firma_orientacion(tmy):
    a = firma_orientacion(E_O, tmy, 0.20, None)
    assert a == firma_orientacion([dict(c) for c in E_O], tmy, 0.20, None)
    assert a != firma_orientacion(E_O, tmy, 0.30, None)
    assert a != firma_orientacion(E_O, tmy, 0.20, {"bifacialidad": 0.8})
    assert a != firma_orientacion([E_O[0], dict(E_O[1], fraccion=0.4)], tmy, 0.20, None)
    otro = tmy.copy()
    otro["G_h"] = otro["G_h"] * 1.01
    assert a != firma_orientacion(E_O, otro, 0.20, None)


# ── Criterio 5: lo que recibe Producción ─────────────────────────────────────
def _estado(res_or, sombra=None, soil=0.0, motor_ok=False):
    e = {"res_mismatch_or": res_or}
    if sombra is not None:
        e.update(res_sombra=sombra, sombra_ok=True)
    publicar_cascada_mismatch(e, poa_anual=2000.0, pct_soiling=soil, motor_ok=motor_ok)
    return e


def test_publicacion_escalar_sin_orientacion_si_es_horaria(res_eo):
    e = _estado(res_eo, soil=2.0)
    assert e["mismatch_or_horario"] is True
    assert e["factor_global_mismatch"] == pytest.approx(0.98, abs=1e-4)   # solo suciedad
    assert e["factor_mismatch_sin_soiling"] == 1.0
    fila = next(r for r in e["cascada_mismatch"] if r["etapa"].startswith("Mismatch orientación"))
    assert fila["pct_total"] == pytest.approx(res_eo["factor_mismatch_pct"], abs=0.05)


def test_resultado_anterior_sin_horario_como_antes():
    e = _estado({"factor_mismatch_pct": 3.0}, soil=0.0)
    assert e["mismatch_or_horario"] is False
    assert e["factor_global_mismatch"] == pytest.approx(0.97, abs=1e-4)


@pytest.mark.parametrize("motor_ok", [False, True])
def test_produccion_recibe_orientacion_hora_a_hora(tmy, res_eo, motor_ok):
    poa = calcular_poa(tmy, LAT, LON, ALT, 90, 90)
    sombra = calcular_sombreado_horizonte(LAT, LON, ALT, tmy, poa, [(90, 15), (270, 15)])
    e = _estado(res_eo, sombra=sombra, soil=2.0, motor_ok=motor_ok)
    r = factores_mismatch_produccion(e, poa, motor_ok)
    esperado = sombra["factor_horario"].to_numpy() * res_eo["factor_horario"].to_numpy()
    np.testing.assert_allclose(r["factor_horario"], esperado)
    assert r["factor_escalar"] == (1.0 if motor_ok else pytest.approx(0.98, abs=1e-4))


def test_factor_orientacion_desalineado_no_aplica_y_avisa(tmy, res_eo):
    poa = calcular_poa(tmy, LAT, LON, ALT, 90, 90)
    corto = dict(res_eo, factor_horario=res_eo["factor_horario"].iloc[:100])
    e = _estado(res_eo)
    e["res_mismatch_or"] = corto
    r = factores_mismatch_produccion(e, poa, False)
    assert r["factor_horario"] is None and r["avisos"]


def test_punta_a_punta_motor_de_produccion(tmy, res_eo):
    from calculos.produccion import simular_produccion_anual
    from datos.catalogo_paneles_excel import cargar_catalogo_paneles
    cat = cargar_catalogo_paneles()
    panel = dict(cat[next(k for k in cat if "JAM66D46-720" in k)])
    poa = calcular_poa(tmy, LAT, LON, ALT, 90, 90)
    e = _estado(res_eo, soil=0.0)
    r = factores_mismatch_produccion(e, poa, False)
    res = simular_produccion_anual(tmy, aplicar_factor_horario(poa, r["factor_horario"]),
                                   panel, 20, 0.98, r["factor_escalar"])
    ref = poa.copy()
    ref["poa_global"] = poa["poa_global"].to_numpy() * res_eo["factor_horario"].to_numpy()
    res_ref = simular_produccion_anual(tmy, ref, panel, 20, 0.98, 1.0)
    assert res["E_ac_anual_kWh"] == pytest.approx(res_ref["E_ac_anual_kWh"], rel=1e-9)
    sin = simular_produccion_anual(tmy, poa, panel, 20, 0.98, 1.0)
    assert res["E_ac_anual_kWh"] < 0.9 * sin["E_ac_anual_kWh"]      # antes: 0 % de pérdida


# ── Criterio 6: página ───────────────────────────────────────────────────────
def test_pagina_usa_albedo_bifacial_y_firma():
    with open(_PAG5, encoding="utf-8") as f:
        src = f.read()
    assert 'albedo=float(st.session_state.get("albedo_suelo", 0.20))' in src
    assert "firma_orientacion(configs, tmy, _albedo_or, _bifacial_or)" in src
    assert '_res_or_prev.get("firma") != _firma_or' in src
    assert "factor_mismatch_pct_anual_aprox" in src


# ── Criterio 8: manual ───────────────────────────────────────────────────────
@pytest.mark.parametrize("pregunta, texto", [
    ("por que fachadas este y oeste en el mismo string pierden energia", "14,9 %"),
    ("como calcula la app el mismatch de orientacion hora a hora", "diodos de bypass"),
])
def test_manual_explica_orientacion(pregunta, texto):
    from calculos.asistente import BaseConocimiento
    secciones = BaseConocimiento.cargar().buscar(pregunta, k=6)
    candidatas = [s for s in secciones if "orientaciones en el mismo string" in s["titulo"].lower()]
    assert candidatas, [s["titulo"] for s in secciones]
    assert texto in "\n".join(s["texto"] for s in candidatas)
