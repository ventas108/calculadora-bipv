# -*- coding: utf-8 -*-
"""Spec ``05-perdidas-y-temperatura/calidad-y-mismatch`` (29-sep-2026).

PVsyst separa «Module quality loss» y «Mismatch loss, modules and strings».
En el proyecto agrivoltaico de Apartadó: calidad 3.00 % y mismatch 2.10 %,
juntas 1 − 0.97 × 0.979 = 5.04 %. La app tenía un solo control de 0–3 %.
"""
import ast
import os

import numpy as np
import pandas as pd
import pytest

from calculos.mismatch import CLAVE_CALIDAD_MODULO, pct_perdida_modulos
from calculos.produccion import perdidas_desglosadas, simular_produccion_anual
from calculos.produccion_iv import simular_produccion_iv
from calculos.produccion_vigencia import construir_payload_produccion_run_signature_v1
from datos.tecnologias_bipv import ASP_ST1_T40

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_PANELES = 40
_MOTORES = [simular_produccion_anual, simular_produccion_iv]


def _tmy_poa(poa_wm2=600.0):
    index = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    sol = (index.hour >= 6) & (index.hour < 18)
    tmy = pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=index)
    poa = pd.DataFrame({"poa_global": np.where(sol, poa_wm2, 0.0)}, index=index)
    return tmy, poa


def _correr(funcion, **kw):
    tmy, poa = _tmy_poa()
    return funcion(tmy=tmy, poa_base=poa, panel=ASP_ST1_T40, N_paneles=N_PANELES,
                   eta_inversor=0.975, factor_pr_mismatch=1.0, **kw)


def test_perdida_combinada():
    assert pct_perdida_modulos(3.0, 2.1) == pytest.approx(5.037, abs=1e-3)
    assert pct_perdida_modulos(0.0, 1.0) == pytest.approx(1.0)
    assert pct_perdida_modulos(None, None) == 0.0
    assert pct_perdida_modulos(-0.8, 0.0) == pytest.approx(-0.8)
    assert CLAVE_CALIDAD_MODULO == "pct_calidad_modulo"


@pytest.mark.parametrize("funcion", _MOTORES)
def test_calidad_y_mismatch_se_aplican_y_se_reportan_por_separado(funcion):
    base = _correr(funcion)
    r = _correr(funcion, pct_calidad_modulo=3.0, pct_mismatch_fab=2.1)
    e0 = base["E_dc_anual_kWh"]
    assert r["E_dc_anual_kWh"] == pytest.approx(e0 * 0.97 * 0.979, rel=2e-3)
    assert r["pct_calidad_modulo_aplicado"] == 3.0
    assert r["pct_mismatch_fab_aplicado"] == 2.1
    assert r["perdida_calidad_modulo_kWh"] == pytest.approx(e0 * 0.03, rel=5e-3)
    assert r["perdida_mismatch_fab_kWh"] == pytest.approx(e0 * 0.97 * 0.021, rel=5e-3)


@pytest.mark.parametrize("funcion", _MOTORES)
def test_sin_calidad_da_lo_mismo_que_antes(funcion):
    a = _correr(funcion, pct_mismatch_fab=2.0)
    b = _correr(funcion, pct_mismatch_fab=2.0, pct_calidad_modulo=None)
    c = _correr(funcion, pct_mismatch_fab=2.0, pct_calidad_modulo=0.0)
    assert a["E_ac_anual_kWh"] == b["E_ac_anual_kWh"] == c["E_ac_anual_kWh"]
    assert b["pct_calidad_modulo_aplicado"] is None
    assert b["perdida_calidad_modulo_kWh"] == 0


@pytest.mark.parametrize("funcion", _MOTORES)
def test_calidad_negativa_es_ganancia(funcion):
    base = _correr(funcion)
    r = _correr(funcion, pct_calidad_modulo=-0.8)
    assert r["E_dc_anual_kWh"] > base["E_dc_anual_kWh"]
    assert r["perdida_calidad_modulo_kWh"] < 0


def _tabla(res):
    return perdidas_desglosadas(res, poa_bruta_kWh_m2=2190.0).to_dict("records")


def test_loss_diagram_dos_filas_que_reconcilian():
    r = _correr(simular_produccion_anual, pct_calidad_modulo=3.0, pct_mismatch_fab=2.1)
    filas = _tabla(r)
    etapas = [f["Etapa"] for f in filas]
    i_cal = next(i for i, e in enumerate(etapas) if e.startswith("②c0 Calidad del módulo"))
    i_mis = next(i for i, e in enumerate(etapas) if e.startswith("②c Mismatch módulos y strings"))
    assert i_cal + 1 == i_mis
    assert not any("informativo" in e for e in etapas)
    assert filas[i_mis]["kWh"] == round(r["E_dc_anual_kWh"], 0)       # última del bloque
    assert filas[i_cal]["Δ kWh"] + filas[i_mis]["Δ kWh"] == \
        round(r["E_dc_anual_kWh"], 0) - filas[i_cal - 1]["kWh"]
    assert "3.0%" in filas[i_cal]["Nota"]


def test_loss_diagram_solo_calidad_y_ninguna():
    solo = [f["Etapa"] for f in _tabla(
        _correr(simular_produccion_anual, pct_calidad_modulo=3.0))]
    assert any(e.startswith("②c0 Calidad del módulo") for e in solo)
    assert not any("informativo" in e for e in solo)
    ninguna = [f["Etapa"] for f in _tabla(_correr(simular_produccion_anual))]
    assert any("informativo" in e for e in ninguna)


def _payload(**kw):
    idx = pd.date_range("2001-01-01", periods=24, freq="h", tz="UTC")
    return construir_payload_produccion_run_signature_v1(
        panel={"a": 1}, panel_nombre="p", inversor={"b": 2}, inversor_nombre="i",
        N_paneles=1, N_serie=1, N_strings_tracker=1, n_inversores=1, P_dc_stc_kW=1.0,
        eta_inversor=0.97, P_ac_nom_W_total=None, NOCT=45.0, k_bipv=1.0,
        produccion_usar_iv=False, source_mode="sdm_pvsyst", tmy_index=idx, tmy_T2m=np.zeros(24),
        poa_source="poa_df", poa_index=idx, poa_global=np.zeros(24),
        factor_mismatch_aplicado=1.0, **kw)


def test_firma_de_vigencia_incluye_la_calidad():
    a = _payload(pct_calidad_modulo=3.0)
    b = _payload(pct_calidad_modulo=0.0)
    assert a["pct_calidad_modulo"] == 3.0 and a != b


def test_cadena_multisuperficie_usa_la_perdida_combinada():
    from calculos.cadena_perdidas_multisup import parametros_cadena
    p = parametros_cadena({"pct_mismatch_fab": 2.1, "pct_calidad_modulo": 3.0})
    assert p["pct_mismatch_fab"] == pytest.approx(5.037, abs=1e-3)
    assert parametros_cadena({"pct_mismatch_fab": 2.1})["pct_mismatch_fab"] == pytest.approx(2.1)


def _src(nombre):
    with open(os.path.join(_ROOT, "pages", nombre), encoding="utf-8") as f:
        return f.read()


def test_paginas_usan_la_calidad():
    mis = _src("5_🔀_Mismatch.py")
    assert "Calidad del módulo" in mis and "Mismatch módulos y strings" in mis
    assert 'st.session_state[CLAVE_CALIDAD_MODULO] = pct_calidad_modulo' in mis
    prod = _src("6_📊_Produccion.py")
    assert prod.count("pct_calidad_modulo") >= 2          # motor y firma
    for pag in ("4c_🧩_Comparador_Paneles.py", "4d_🧭_Comparador_Orientación.py",
                "18_🤖_Análisis_IA.py"):
        assert "pct_perdida_modulos(" in _src(pag), pag
    ast.parse(mis), ast.parse(prod)


@pytest.mark.parametrize("pregunta, texto", [
    ("que es la calidad del modulo y el mismatch en PVsyst", "Module quality loss"),
    ("por que la app daba mas energia que PVsyst por el mismatch en Apartado", "5.04"),
])
def test_manual_explica_calidad_y_mismatch(pregunta, texto):
    from calculos.asistente import BaseConocimiento
    secciones = BaseConocimiento.cargar().buscar(pregunta, k=6)
    candidatas = [s for s in secciones if "Calidad del módulo y mismatch" in s["titulo"]]
    assert candidatas, [s["titulo"] for s in secciones]
    assert texto in "\n".join(s["texto"] for s in candidatas)
