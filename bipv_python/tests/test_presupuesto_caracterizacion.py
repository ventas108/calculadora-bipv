# -*- coding: utf-8 -*-
"""
Caracterización — extracción de calculos/presupuesto.py (auditoría Fase 1,
cuello de botella #3: 8_💼_Presupuesto.py tenía lógica financiera real
escrita directamente en la página, sin cobertura de tests).

`FIXTURE_CALC_PARAMETRICO` se generó ANTES del refactor, ejecutando la
función `_calc_parametrico` tal como vivía en la página (extraída con
`ast` desde el código fuente real, sin reescribir nada a mano) sobre 135
combinaciones de tipo × escenario × zona × kWp. Este test compara esa
salida congelada contra `calculos.presupuesto.calcular_parametrico` — si
alguna cifra cambia por un futuro edit, este test debe fallar.
"""
import json
import os

import pandas as pd
import pytest

from calculos.presupuesto import (
    BENCH,
    ZONA_FACTOR,
    calcular_parametrico,
    recolectar_items_cotizacion,
)

_FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "presupuesto_parametrico_pre_refactor.json"
)


def _casos_congelados():
    with open(_FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("clave", _casos_congelados().keys())
def test_calcular_parametrico_identico_al_pre_refactor(clave):
    esperado = _casos_congelados()[clave]
    tipo, escenario, zona, kwp = clave.split("|")
    obtenido = calcular_parametrico(float(kwp), tipo, escenario, zona)
    assert obtenido.keys() == esperado.keys()
    for k, v_esperado in esperado.items():
        assert obtenido[k] == pytest.approx(v_esperado, rel=1e-12, abs=1e-9), (
            f"{clave} → campo '{k}': {obtenido[k]!r} != {v_esperado!r}"
        )


def test_bench_y_zona_factor_cubren_los_mismos_tipos_y_zonas_congelados():
    claves = _casos_congelados().keys()
    tipos_usados = {c.split("|")[0] for c in claves}
    zonas_usadas = {c.split("|")[2] for c in claves}
    assert tipos_usados <= set(BENCH.keys())
    assert zonas_usadas <= set(ZONA_FACTOR.keys())


def _df(rows):
    return pd.DataFrame(rows, columns=["Activo", "Descripcion", "Ref", "Cantidad", "Unidad", "USD_un"])


def test_recolectar_items_cotizacion_ignora_inactivos_y_vacios():
    secciones = {
        "perfileria": _df([
            [True,  "Perfil aluminio", "P-1", 10, "m", 5.0],
            [False, "Perfil descartado", "P-2", 3, "m", 2.0],   # inactivo → excluido
            [True,  "Sin costo",  "P-3", 1, "un", 0.0],          # total 0 → excluido
            [True,  "",           "P-4", 1, "un", 10.0],         # sin descripción → excluido
        ]),
        "mano_obra": _df([
            [True, "Instalación", "M-1", 8, "h", 25.0],
        ]),
    }
    etiquetas = {"perfileria": "Perfilería", "mano_obra": "Mano de obra"}

    filas = recolectar_items_cotizacion(secciones, trm_cop=4000.0, etiquetas=etiquetas)

    assert len(filas) == 2
    assert filas[0]["categoria"] == "Perfilería"
    assert filas[0]["total_usd"] == pytest.approx(50.0)
    assert filas[0]["total_cop"] == pytest.approx(200000.0)
    assert filas[1]["categoria"] == "Mano de obra"
    assert filas[1]["total_usd"] == pytest.approx(200.0)


def test_recolectar_items_cotizacion_orden_sigue_al_dict_secciones():
    secciones = {
        "inversor":   _df([[True, "Inversor", "I-1", 1, "un", 3000.0]]),
        "perfileria": _df([[True, "Perfil", "P-1", 1, "un", 100.0]]),
    }
    filas = recolectar_items_cotizacion(
        secciones, trm_cop=1.0, etiquetas={"inversor": "Inversor", "perfileria": "Perfilería"}
    )
    assert [f["categoria"] for f in filas] == ["Inversor", "Perfilería"]


def test_recolectar_items_cotizacion_seccion_ausente_no_rompe():
    filas = recolectar_items_cotizacion(
        {"perfileria": None}, trm_cop=4000.0, etiquetas={"perfileria": "Perfilería"}
    )
    assert filas == []
