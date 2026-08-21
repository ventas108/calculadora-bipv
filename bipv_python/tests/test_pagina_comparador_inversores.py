# -*- coding: utf-8 -*-
"""Regresión puntual en pages/4b_⚖️_Comparador_Inversores.py -- no había
cobertura previa de esta página (predata la capa de agentes de Fase 5),
así que este archivo cubre SOLO el hallazgo de hoy, no un audit completo.

Hallazgo (reportado por el usuario probando la página hermana 4c 🧩
Comparador de Paneles, que copió este mismo patrón): la TRM mostraba el
default hardcodeado (4000.0) en vez de la TRM real, porque
session_state["tipo_cambio"] solo existe si el usuario ya visitó
💰 Financiero/💼 Presupuesto en la misma sesión (esas páginas son las que
llaman calculos.trm_utils.init_trm()). 4b nunca lo llamaba -- mismo bug,
independiente de mi trabajo de hoy, encontrado por auditar el patrón que
había copiado de aquí.

Sin streamlit disponible en este entorno de desarrollo, se audita el
código fuente vía regex -- mismo patrón que los demás tests de páginas.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAGINA = os.path.join(_ROOT, "pages", "4b_⚖️_Comparador_Inversores.py")


def _leer():
    with open(_PAGINA, encoding="utf-8") as f:
        return f.read()


def test_llama_init_trm_antes_de_leer_tipo_cambio():
    src = _leer()
    assert "from calculos.trm_utils import init_trm" in src
    assert "init_trm()" in src
    idx_init = src.index("init_trm()")
    idx_uso = src.index('st.session_state.get("tipo_cambio"')
    assert idx_init < idx_uso
