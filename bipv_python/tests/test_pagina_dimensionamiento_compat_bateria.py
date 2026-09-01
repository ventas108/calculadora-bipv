# -*- coding: utf-8 -*-
"""Hueco #1 de la auditoría de emparentamiento inversor híbrido ↔ batería
(1-sep-2026): 📐 Dimensionamiento no tenía ninguna referencia a "batería" ni
"híbrido" -- se podía cambiar libremente de inversor sin ninguna alerta,
aunque el proyecto ya tuviera una batería configurada en 🔋 Baterías y
Balance. Mismo patrón AST/substring que test_pagina_diagrama_unifilar.py
(más rápido que ejecutar Streamlit, no depende de sesión autenticada)."""
import ast
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG_DIM = os.path.join(_ROOT, "pages", "4_📐_Dimensionamiento.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_pagina_dimensionamiento_tiene_sintaxis_valida():
    ast.parse(_leer(_PAG_DIM))


def test_pagina_dimensionamiento_importa_check_compatibilidad_bateria():
    src = _leer(_PAG_DIM)
    assert "from calculos.compatibilidad_bateria import check_compatibilidad" in src


def test_pagina_dimensionamiento_solo_alerta_si_ya_hay_bateria_configurada():
    # Nunca debe inventar la alerta si el proyecto no usa batería -- gateado
    # por la presencia real de session_state["bateria_dict"].
    src = _leer(_PAG_DIM)
    assert '_bateria_dict_dim = st.session_state.get("bateria_dict")' in src
    assert "if _bateria_dict_dim:" in src


def test_pagina_dimensionamiento_reverifica_contra_el_inversor_recien_seleccionado():
    src = _leer(_PAG_DIM)
    assert "_check_compat_bateria_dim(\n        _bateria_dict_dim, inversor, inversor_nombre\n    )" in src


def test_pagina_dimensionamiento_distingue_severidad_error_warning_caption():
    src = _leer(_PAG_DIM)
    assert '_bat_estado_dim == "error"' in src
    assert '_bat_estado_dim == "warning"' in src
