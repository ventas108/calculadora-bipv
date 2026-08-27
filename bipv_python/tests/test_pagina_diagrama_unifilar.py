# -*- coding: utf-8 -*-
"""Diagrama Unifilar — integración en la página (Fase 4, 27-ago-2026).

Mismo patrón que test_pagina_ledger_auditoria.py: se audita el código
fuente vía AST/substring en vez de ejecutar Streamlit (más rápido, y no
depende de una sesión autenticada para llegar al código que nos interesa).
"""
import ast
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG_UNIFILAR = os.path.join(_ROOT, "pages", "20_⚡_Diagrama_Unifilar.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_pagina_unifilar_tiene_sintaxis_valida():
    ast.parse(_leer(_PAG_UNIFILAR))


def test_pagina_unifilar_requiere_login():
    src = _leer(_PAG_UNIFILAR)
    assert "requerir_login()" in src


def test_pagina_unifilar_importa_el_ledger():
    src = _leer(_PAG_UNIFILAR)
    assert "from calculos import ledger_auditoria" in src


def test_pagina_unifilar_sella_con_tipo_diagrama_unifilar():
    src = _leer(_PAG_UNIFILAR)
    assert '"diagrama_unifilar"' in src
    assert "Sellar en el Ledger de Auditoría" in src


def test_pagina_unifilar_advierte_que_no_es_documento_certificado():
    # Limite declarado del modulo (ver calculos/diagrama_unifilar.py) debe
    # seguir visible en la UI, no solo en el docstring del modulo.
    src = _leer(_PAG_UNIFILAR)
    assert "No es un documento certificado" in src


def test_pagina_unifilar_auto_llena_bateria_y_multisuperficie():
    src = _leer(_PAG_UNIFILAR)
    assert "bateria_ok" in src
    assert "multisup_activo" in src
    assert "multisup_desglose" in src
