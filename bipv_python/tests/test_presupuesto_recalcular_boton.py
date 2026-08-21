# -*- coding: utf-8 -*-
"""Regresión: un usuario cargando cotizaciones reales reportó que la columna
'Total USD' de una fila recién agregada a las tablas de costos no se
actualizaba hasta el siguiente refresco de la página -- comportamiento
conocido de st.data_editor (la columna calculada de una fila nueva no se
re-renderiza hasta el próximo rerun, y a veces ese rerun no se dispara
solo). No es un bug en la fórmula (Cantidad × USD_un se recalcula
correcto en cada rerun, ver el código de _editar_seccion) -- es que el
usuario no siempre tiene una forma obvia de forzar ese rerun.

Fix: un botón "🔄 Recalcular" (solo st.rerun(), no toca la fórmula) en
CADA tabla de costos editable: las 4 que pasan por _editar_seccion()
(Perfilería, Mano de Obra, Sistema FV, Inversor -- y por extensión
Catálogo, que también usa _editar_seccion()) y la de Costos Blandos, que
tiene su propio st.data_editor separado.

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
