# -*- coding: utf-8 -*-
"""Regresión, en dos rondas, de un mismo síntoma reportado por un usuario
cargando cotizaciones reales: la columna calculada 'Total USD' de una
tabla de costos se quedaba mostrando un valor viejo tras editar una fila.

Ronda 1: se agregó un botón "🔄 Recalcular" que solo hacía st.rerun() --
insuficiente, el usuario reportó que seguía sin funcionar.

Ronda 2 (el bug real): st.data_editor de Streamlit cachea en el navegador
el valor de columnas calculadas/disabled y no siempre las refresca aunque
el `data` que le pasa Python cambie -- un st.rerun() por sí solo no rompe
ese caché del lado del componente. Fix: versionar el `key` del widget
(f"ed_{key}_v{N}") e incrementar N cuando el usuario pide 'Recalcular' o
'Resetear' -- un `key` nuevo fuerza a Streamlit a tratar el widget como un
componente distinto, sin caché previo. No se versiona en cada edición
individual (eso reconstruiría la tabla en cada tecla).

Cubre las 4 tablas que pasan por _editar_seccion() (Perfilería, Mano de
Obra, Sistema FV, Inversor -- y por extensión Catálogo, que también usa
_editar_seccion()) y la de Costos Blandos, que tiene su propio
st.data_editor separado.

Sin streamlit disponible en este entorno de desarrollo, se audita el
código fuente vía regex -- mismo patrón que tests/test_pagina_analisis_ia.py.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAGINA = os.path.join(_ROOT, "pages", "8_💼_Presupuesto.py")


def _leer():
    with open(_PAGINA, encoding="utf-8") as f:
        return f.read()


def test_boton_recalcular_existe_en_editar_seccion_compartida():
    # Cubre Perfilería, Mano de Obra, Sistema FV, Inversor y Catálogo --
    # las 5 pestañas que llaman a _editar_seccion().
    src = _leer()
    assert 'col_rc.button("🔄 Recalcular", key=f"recalc_{key}"' in src


def test_boton_recalcular_existe_en_costos_blandos():
    # Costos Blandos tiene su propio st.data_editor, no pasa por
    # _editar_seccion() -- necesita su propio botón.
    src = _leer()
    assert 'col_rc.button("🔄 Recalcular", key="recalc_soft"' in src


def test_data_editor_de_editar_seccion_usa_key_versionada():
    # El key estático f"ed_{key}" no rompe el caché del navegador al
    # cambiar de versión -- debe incluir el contador _ver_key.
    src = _leer()
    assert 'key=f"ed_{key}_v{st.session_state[_ver_key]}"' in src
    assert '_ver_key = f"_ver_{key}"' in src
    # Recalcular y Resetear DEBEN incrementar la versión antes del rerun.
    assert "st.session_state[_ver_key] += 1" in src


def test_data_editor_de_costos_blandos_usa_key_versionada():
    src = _leer()
    assert 'key=f"ed_soft_v{st.session_state[\'_ver_soft\']}"' in src
    assert '"_ver_soft" not in st.session_state' in src
    assert 'st.session_state["_ver_soft"] += 1' in src
