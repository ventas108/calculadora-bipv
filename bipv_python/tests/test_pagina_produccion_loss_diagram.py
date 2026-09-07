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


def test_pagina_produccion_declara_la_categoria_pvsyst_ohmica():
    # 7-sep-2026: "Ohmic wiring loss" DEJÓ de ser una categoría no modelada
    # en absoluto -- ahora se aplica de verdad (filas ②d/④c) si hay un %
    # manual en 🔀 Mismatch o un cálculo real en ⚡ Diagrama Unifilar. La
    # página debe seguir nombrando la categoría explícitamente en AMBOS
    # estados (activa/inactiva) -- nunca ocultar cuál es el estado actual.
    src = _leer(_PAG_PRODUCCION)
    assert "Ohmic wiring loss" in src
    assert "perdida_ohmica_dc_modo" in src  # rama condicional real, no solo texto fijo


def test_pagina_produccion_aclara_que_la_fila_de_modulo_es_informativa():
    # Fila ②c "Módulo" (+0,75%, visto idéntico en 2 papers PVsyst reales) --
    # 7-sep-2026: sigue siendo solo informativa CUANDO no hay un % de
    # mismatch de fabricación configurado (pct_mismatch_fab_aplicado es
    # None) -- pero ya no es SIEMPRE informativa, así que la página debe
    # distinguir ambos estados, no dar a entender que nunca se aplica.
    src = _leer(_PAG_PRODUCCION)
    assert "②c" in src
    assert "esta app no lo aplica" in src
    assert "pct_mismatch_fab_aplicado" in src  # rama condicional real


def test_pagina_produccion_explica_el_desglose_irradiancia_vs_temperatura():
    src = _leer(_PAG_PRODUCCION)
    assert "②a/②b" in src
