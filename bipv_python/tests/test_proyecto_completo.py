# -*- coding: utf-8 -*-
"""Spec ``03-dimensionamiento/proyecto-completo`` (29-sep-2026).

Caso real: comparación con PVsyst del proyecto agrivoltaico de Apartadó.
Área útil 2,393 m² × 40 % = 957.2 m²; JA Solar JAM66D46-720/LB (3.106 m²,
720 W), 28 en serie; Growatt MAX 100KTL3 LV (10 MPPT, 100 kW AC), 1 string por
MPPT. PVsyst: 11 strings, 308 módulos, 222 kWp, 2 inversores, DC/AC 1.11.
La app decía 2 inversores llenos: 560 módulos, 403.2 kWp en 1,740 m².
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos.dimensionamiento import proyecto_completo  # noqa: E402

PANEL = {"area_m2": 3.106, "Pmax_stc": 720.0}
AREA_UTIL = 2393 * 0.40
P_AC = 100_000.0
_PAG4 = os.path.join(os.path.dirname(__file__), "..", "pages", "4_📐_Dimensionamiento.py")


def _apartado(**kw):
    base = dict(panel=PANEL, area_util_m2=AREA_UTIL, N_serie=28,
                N_strings_tracker=1, N_mppt=10, P_ac_nom_W=P_AC)
    base.update(kw)
    return proyecto_completo(**base)


def test_sin_cadenas_declaradas_cabe_lo_de_pvsyst():
    r = _apartado()
    assert r["fuente"] == "area"
    assert r["strings_que_caben"] == 11
    assert (r["N_strings_total"], r["N_inversores"], r["reparto"]) == (11, 2, [6, 5])
    assert r["N_paneles"] == 308
    assert r["P_dc_kWp"] == pytest.approx(221.76)
    assert r["area_m2"] == pytest.approx(956.6, abs=0.1)
    assert r["cabe"] and r["faltan_m2"] == 0
    assert r["dcac"]["ratio"] == pytest.approx(1.109, abs=0.001)
    assert r["dcac"]["nivel"] == "🟢"
    assert r["dcac_max_inversor"] == pytest.approx(1.21, abs=0.001)   # 6 × 28 × 720 W


def test_con_11_cadenas_declaradas_da_lo_mismo():
    r = _apartado(N_total_cadenas=11)
    assert r["fuente"] == "declarado"
    assert (r["N_paneles"], r["N_inversores"], r["reparto"]) == (308, 2, [6, 5])


def test_declarado_que_no_cabe_avisa_los_m2_que_faltan():
    r = _apartado(N_total_cadenas=20)
    assert (r["N_paneles"], r["N_inversores"], r["reparto"]) == (560, 2, [10, 10])
    assert not r["cabe"]
    assert r["cobertura_pct"] == pytest.approx(181.7, abs=0.1)   # sin tope en 100
    assert r["faltan_m2"] == pytest.approx(560 * 3.106 - AREA_UTIL, abs=0.1)


@pytest.mark.parametrize("area", [50.0, 100.0, 500.0, 957.2, 1739.0, 5000.0])
def test_sin_declarar_nunca_pasa_del_area(area):
    r = _apartado(area_util_m2=area)
    assert r["area_m2"] <= area + 1e-9
    assert r["cabe"] == (r["N_strings_total"] > 0)
    assert sum(r["reparto"]) == r["N_strings_total"]
    assert all(s <= r["capacidad_strings_inversor"] for s in r["reparto"])


def test_area_menor_que_un_string():
    r = _apartado(area_util_m2=50.0)
    assert (r["N_strings_total"], r["N_inversores"], r["N_paneles"]) == (0, 0, 0)
    assert not r["cabe"]
    assert r["faltan_m2"] == pytest.approx(28 * 3.106 - 50.0, abs=0.01)
    assert r["dcac"]["evaluable"] is False


def test_sin_potencia_ac_no_evalua_dcac():
    r = _apartado(P_ac_nom_W=None)
    assert r["dcac"]["evaluable"] is False and r["dcac_max_inversor"] is None
    assert r["N_paneles"] == 308


def test_datos_invalidos():
    with pytest.raises(ValueError):
        _apartado(N_mppt=0)
    with pytest.raises(ValueError):
        _apartado(panel={"Pmax_stc": 720.0})


def test_pagina_usa_la_funcion_en_las_dos_secciones():
    with open(_PAG4, encoding="utf-8") as f:
        src = f.read()
    assert src.count("proyecto_completo(") >= 2
    assert "math.ceil(area / dim" not in src
    assert "math.ceil(_prelim_area / _prelim_dim" not in src
    assert 'st.session_state["reparto_strings_inversores"]' in src


@pytest.mark.parametrize("pregunta, texto", [
    ("por que proyecto completo de dimensionamiento daba 560 modulos y 403 kWp", "560"),
    ("como calcula dimensionamiento cuantos inversores y modulos caben en el area util", "6 + 5"),
])
def test_manual_explica_proyecto_completo(pregunta, texto):
    from calculos.asistente import BaseConocimiento
    secciones = BaseConocimiento.cargar().buscar(pregunta, k=6)
    candidatas = [s for s in secciones if "Proyecto completo" in s["titulo"]]
    assert candidatas, [s["titulo"] for s in secciones]
    assert texto in "\n".join(s["texto"] for s in candidatas)
