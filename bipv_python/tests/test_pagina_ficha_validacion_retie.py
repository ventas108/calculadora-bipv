# -*- coding: utf-8 -*-
"""Ficha de Validación RETIE — integración en la página (27-ago-2026).

Mismo patrón que test_pagina_diagrama_unifilar.py: se audita el código
fuente vía AST/substring en vez de ejecutar Streamlit.
"""
import ast
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG = os.path.join(_ROOT, "pages", "21_📋_Ficha_Validacion_RETIE.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_pagina_ficha_retie_tiene_sintaxis_valida():
    ast.parse(_leer(_PAG))


def test_pagina_ficha_retie_requiere_login():
    src = _leer(_PAG)
    assert "requerir_login()" in src


def test_pagina_ficha_retie_advierte_que_no_es_constructivo():
    src = _leer(_PAG)
    assert "No es un documento constructivo" in src


def test_pagina_ficha_retie_sella_con_tipo_propio():
    src = _leer(_PAG)
    assert '"ficha_validacion_retie"' in src
    assert "Sellar en el Ledger de Auditoría" in src


def test_pagina_ficha_retie_auto_llena_desde_dimensionamiento():
    src = _leer(_PAG)
    assert "panel_dict" in src
    assert "inversor_dict_dim" in src
    assert "N_serie" in src


def test_pagina_ficha_retie_no_hardcodea_cantidad_de_inversores():
    # Regresion explicita pedida por el usuario: el motor original venia
    # con 2 inversores fijos -- la pagina debe pedir la cantidad como
    # input, no traerla fija en el codigo.
    src = _leer(_PAG)
    assert "n_inversores=int(n_inversores)" in src
    assert "strings_inversor_1" not in src
    assert "strings_inversor_2" not in src


def test_pagina_ficha_retie_degrada_sin_cairosvg():
    src = _leer(_PAG)
    assert "exportar_ficha_png_bytes" in src
    assert "no disponible en este servidor" in src
