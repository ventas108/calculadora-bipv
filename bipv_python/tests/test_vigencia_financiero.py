# -*- coding: utf-8 -*-
"""💰 Financiero no muestra un TIR calculado con datos viejos (26-sep-2026).

El resultado guardado solo se borraba si cambiaba el CAPEX: al cambiar la
tarifa de excedentes, la energía o las tasas, la tabla seguía mostrando el
TIR anterior sin aviso.
"""
import os

from calculos.vigencia_financiero import datos_cambiados

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BASE = {"capex_total": 26642.0, "e_financiero": 6155.0, "tarifa_cop": 1200.0,
         "tarifa_excedentes_cop": 1200.0, "frac_exportada": 0.134, "tasa_desc": 10.0,
         "ben": {"total_usd": 10088.0}, "config_degradacion": {"modo": "geometrica"}}


def test_sin_cambios_no_hay_nada_que_recalcular():
    assert datos_cambiados(dict(_BASE), dict(_BASE)) == []


def test_cambiar_la_tarifa_de_excedentes_obliga_a_recalcular():
    nuevo = {**_BASE, "tarifa_excedentes_cop": 300.0}
    assert datos_cambiados(_BASE, nuevo) == ["tarifa de excedentes"]


def test_varios_cambios_se_nombran_en_palabras():
    nuevo = {**_BASE, "e_financiero": 6000.0, "ben": {"total_usd": 9000.0}}
    assert datos_cambiados(_BASE, nuevo) == ["energía anual", "beneficios Ley 1715"]


def test_resultado_sin_datos_guardados_se_considera_viejo():
    assert datos_cambiados(None, _BASE) == ["datos del cálculo anterior no disponibles"]


def test_ruido_de_redondeo_no_cuenta_como_cambio():
    assert datos_cambiados(_BASE, {**_BASE, "frac_exportada": 0.134 + 1e-12}) == []


def test_financiero_compara_todos_los_datos_antes_de_mostrar_resultados():
    src = open(os.path.join(_ROOT, "pages", "7_💰_Financiero.py"), encoding="utf-8").read()
    assert "datos_cambiados(" in src and '"_fin_datos_calculo"' in src
