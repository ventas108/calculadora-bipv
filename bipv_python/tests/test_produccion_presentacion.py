# -*- coding: utf-8 -*-
"""📊 Producción: detalles de presentación (29-sep-2026).

Revisando el proyecto Apartadó en el servidor se vieron dos detalles que no
cambian ningún kWh pero confunden al leer la pantalla:

1. La tabla mensual mostraba «Recorte inversor (kWh)» sin formato
   (``4927.475563``) porque la página solo formateaba las otras columnas.
2. La fila «↳ Solo horas calientes» del balance decía ``Tk_gamma=—%/°C``: la
   tabla lee ``res["Tk_gamma_pct"]`` y ningún motor lo devolvía.
"""
import pytest

from calculos.produccion import perdidas_desglosadas, simular_produccion_anual
from calculos.produccion_iv import simular_produccion_iv
from datos.tecnologias_bipv import ASP_ST1_T40
from tests.test_produccion_perdida_ohmica import N_PANELES, _tmy_poa_sintetico
from calculos.formato_produccion import FORMATO_TABLA_MENSUAL, texto_gamma

_MOTORES = [simular_produccion_anual, simular_produccion_iv]


def _simular(funcion, panel=ASP_ST1_T40):
    tmy, poa_df = _tmy_poa_sintetico(600.0)
    return funcion(
        tmy=tmy, poa_base=poa_df, panel=panel, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
    )


@pytest.mark.parametrize("funcion", _MOTORES)
def test_cada_columna_de_la_tabla_mensual_tiene_formato(funcion):
    res = _simular(funcion)
    columnas = list(res["df_mensual"].columns)
    assert "Recorte inversor (kWh)" in columnas
    faltan = [c for c in columnas if c not in FORMATO_TABLA_MENSUAL]
    assert faltan == []


def test_recorte_se_muestra_como_kwh_enteros_con_miles():
    assert FORMATO_TABLA_MENSUAL["Recorte inversor (kWh)"].format(4927.475563) == "4,927"


@pytest.mark.parametrize("funcion", _MOTORES)
def test_los_motores_devuelven_el_gamma_de_la_ficha(funcion):
    res = _simular(funcion)
    assert res["Tk_gamma_pct"] == pytest.approx(ASP_ST1_T40["Tk_gamma"])


@pytest.mark.parametrize("funcion", _MOTORES)
def test_la_nota_de_horas_calientes_muestra_el_gamma(funcion):
    res = _simular(funcion)
    df = perdidas_desglosadas(res, poa_bruta_kWh_m2=600.0 * 12 * 365 / 1000)
    nota = df[df["Etapa"].str.contains("Solo horas calientes")]["Nota"].iloc[0]
    assert "Tk_gamma=-0.214%/°C" in nota
    assert "—" not in nota


def test_gamma_sin_dato_en_la_ficha_queda_como_raya():
    panel = dict(ASP_ST1_T40, Tk_gamma=None)
    res = _simular(simular_produccion_anual, panel)
    assert res["Tk_gamma_pct"] is None
    assert texto_gamma(None) == "—"


def test_texto_gamma_sin_decimales_de_sobra():
    assert texto_gamma(-0.29000000000000004) == "-0.29"
    assert texto_gamma(-0.214) == "-0.214"


def test_la_pagina_usa_el_formato_compartido():
    from pathlib import Path
    fuente = (Path(__file__).resolve().parents[1] / "pages" / "6_📊_Produccion.py").read_text(encoding="utf-8")
    assert "FORMATO_TABLA_MENSUAL" in fuente
