# -*- coding: utf-8 -*-
"""📊 Producción debe pasar el resumen real del Motor Óptico a
perdidas_desglosadas() para que la tabla de balance use los nombres estilo
PVsyst con IAM/soiling desglosados (1-sep-2026). Mismo patrón AST/substring
que el resto de tests de páginas de este repo."""
import ast
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG_PRODUCCION = os.path.join(_ROOT, "pages", "6_📊_Produccion.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_pagina_produccion_tiene_sintaxis_valida():
    ast.parse(_leer(_PAG_PRODUCCION))


def test_pagina_produccion_pasa_el_resumen_del_motor_optico_a_la_tabla():
    src = _leer(_PAG_PRODUCCION)
    assert "perdidas_desglosadas(res, poa_bruta_anual, _mo_summary)" in src


def test_pagina_produccion_declara_las_categorias_pvsyst_no_modeladas():
    # Nunca debe dar a entender que la tabla cubre el Loss Diagram completo
    # de PVsyst -- debe declarar explícitamente lo que falta (calidad de
    # módulo, óhmico), mismo principio de honestidad del resto de la app.
    src = _leer(_PAG_PRODUCCION)
    assert "Module quality loss" in src
    assert "Ohmic wiring loss" in src


def test_pagina_produccion_explica_el_desglose_irradiancia_vs_temperatura():
    src = _leer(_PAG_PRODUCCION)
    assert "②a/②b" in src
