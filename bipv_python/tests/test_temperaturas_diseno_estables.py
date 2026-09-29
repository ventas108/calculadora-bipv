# -*- coding: utf-8 -*-
"""Spec ``03-dimensionamiento/temperaturas-diseno`` (29-sep-2026).

En la comparación con PVsyst de Apartadó las temperaturas de diseño salieron
en 0 y luego en 20.0 / 55.0 / 64.0 (valores fijos de la ciudad) en vez de las
del TMY de PVGIS 5.3 (20.9 / 54.2 / 63.6); con 20.0 °C N = 28 cae en ALERTA.
"""
import os

import numpy as np
import pandas as pd
import pytest

from calculos.temperatura import (
    CLAVE_FIRMA_TEMPS_TMY,
    firma_temperaturas_tmy,
    temperaturas_a_aplicar,
    temperaturas_diseno_desde_tmy,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOCT_JA = 45.0


def _t2m(t_min=20.9, t_max=34.0):
    rng = np.random.default_rng(0)
    v = rng.uniform(t_min + 1.0, t_max - 1.0, 8760)
    v[0], v[1] = t_min, t_max
    return pd.Series(v)


def test_formula_de_siempre():
    t = _t2m()
    r = temperaturas_diseno_desde_tmy(t, NOCT_JA)
    assert r["T_min_diseno"] == 20.9
    assert r["T_cel_realista"] == round(round(float(t.quantile(0.95)), 1) + 25.0, 1)
    assert r["T_cel_extremo"] == round(34.0 + 25.0 / 800.0 * 1000.0, 1)


def test_firma_cambia_con_el_tmy_y_el_noct():
    a = firma_temperaturas_tmy(_t2m(), NOCT_JA)
    assert a == firma_temperaturas_tmy(_t2m(), NOCT_JA)
    assert a != firma_temperaturas_tmy(_t2m(t_min=22.0), NOCT_JA)
    assert a != firma_temperaturas_tmy(_t2m(), 43.0)


def test_mismo_tmy_respeta_lo_escrito():
    t = _t2m()
    estado = {"T_min_diseno": 18.0, "T_cel_realista": 50.0, "T_cel_extremo": 60.0,
              CLAVE_FIRMA_TEMPS_TMY: firma_temperaturas_tmy(t, NOCT_JA)}
    assert temperaturas_a_aplicar(estado, t, NOCT_JA) is None


@pytest.mark.parametrize("estado", [
    {},                                                                  # proyecto sin firma
    {"T_min_diseno": 20.0, "T_cel_realista": 55.0, "T_cel_extremo": 64.0,
     CLAVE_FIRMA_TEMPS_TMY: "otra"},                                     # otro TMY / PVGIS
    {"T_min_diseno": 0.0, "T_cel_realista": 0.0, "T_cel_extremo": 0.0},  # en cero
])
def test_recalcula_cuando_hace_falta(estado):
    t = _t2m()
    r = temperaturas_a_aplicar(estado, t, NOCT_JA)
    assert r["T_min_diseno"] == 20.9
    assert r[CLAVE_FIRMA_TEMPS_TMY] == firma_temperaturas_tmy(t, NOCT_JA)


def test_en_cero_con_la_firma_vigente_tambien_recalcula():
    t = _t2m()
    estado = {"T_min_diseno": 0.0, "T_cel_realista": 0.0, "T_cel_extremo": 0.0,
              CLAVE_FIRMA_TEMPS_TMY: firma_temperaturas_tmy(t, NOCT_JA)}
    assert temperaturas_a_aplicar(estado, t, NOCT_JA)["T_min_diseno"] == 20.9


def test_sin_tmy_no_aplica():
    assert temperaturas_a_aplicar({}, None, NOCT_JA) is None


def _src(nombre):
    with open(os.path.join(_ROOT, "pages", nombre), encoding="utf-8") as f:
        return f.read()


def test_dimensionamiento_usa_campos_persistentes_y_firma():
    src = _src("4_📐_Dimensionamiento.py")
    assert 'key="T_min_diseno"' not in src and 'key="T_cel_realista"' not in src
    assert src.count("campo_persistente(") >= 3
    assert "temperaturas_a_aplicar(" in src
    assert "_dim_tmy_ciudad_ref" not in src


def test_proyecto_no_pisa_temperaturas_del_tmy():
    src = _src("1_🏠_Proyecto.py")
    ini = src.index('if st.button("💾 Guardar configuración"')
    bloque = src[ini:src.index('st.session_state["GHI_kWh_m2_dia"]', ini)]
    assert "CLAVE_FIRMA_TEMPS_TMY" in bloque
    assert '"dim_temps_tmy_firma"' in src[src.index("_KEYS_LIMPIAR_CIUDAD"):]


@pytest.mark.parametrize("pregunta, texto", [
    ("de donde salen las temperaturas de diseño de dimensionamiento", "20.9"),
    ("por que las temperaturas de diseño salieron 20 55 64 o en cero", "Guardar configuración"),
])
def test_manual_explica_temperaturas(pregunta, texto):
    from calculos.asistente import BaseConocimiento
    secciones = BaseConocimiento.cargar().buscar(pregunta, k=6)
    candidatas = [s for s in secciones if "Temperaturas de diseño" in s["titulo"]]
    assert candidatas, [s["titulo"] for s in secciones]
    assert texto in "\n".join(s["texto"] for s in candidatas)
