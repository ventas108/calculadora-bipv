# -*- coding: utf-8 -*-
"""Regresión, en tres rondas, de un mismo síntoma reportado por un usuario
cargando cotizaciones reales: la columna calculada 'Total USD' de una
tabla de costos se quedaba mostrando un valor viejo tras editar una fila
-- aunque el Subtotal (calculado en Python aparte) SIEMPRE dio el número
correcto, confirmando que nunca fue un bug de fórmula, solo de qué
mostraba la grilla en pantalla.

Ronda 1: se agregó un botón "🔄 Recalcular" que solo hacía st.rerun() --
insuficiente, el usuario reportó que seguía sin funcionar.

Ronda 2: se versionó el `key` del data_editor (f"ed_{key}_v{N}") para
forzar un remount completo del componente al presionar 'Recalcular' --
tampoco resultó suficiente en todos los casos; el usuario lo confirmó de
nuevo en producción.

Ronda 3 (fix definitivo): dejar de mostrar "Total USD" DENTRO de la
grilla editable. st.data_editor puede cachear en el navegador el valor
de una columna disabled/calculada de forma que ni un rerun ni un `key`
nuevo garantizan romper -- es un comportamiento del componente, no algo
que el backend de Streamlit controle del todo. La única forma
verdaderamente confiable es no depender de esa columna dentro de un
widget con estado de edición: se excluye del data_editor vía
`column_order` (sigue existiendo en los datos, solo no se renderiza ahí)
y se muestra aparte en un st.dataframe de solo lectura, que no tiene
estado de edición que cachear y por lo tanto se reconstruye completo y
correcto en cada rerun sin excepción.

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


def test_total_usd_no_esta_dentro_de_la_grilla_editable_de_editar_seccion():
    # Fix definitivo (ronda 3): "Total USD" se excluye del data_editor via
    # column_order -- ya no puede quedarse con un valor cacheado del
    # navegador porque ya no vive ahí.
    src = _leer()
    assert 'column_order=["Activo", "Descripcion", "Ref", "Cantidad", "Unidad", "USD_un"]' in src
    # La única aparición de "Total USD" en column_config del editor debía
    # desaparecer -- ahora solo debe quedar en el st.dataframe de solo lectura.
    assert '"Total USD":   st.column_config.NumberColumn("Total USD", disabled=True' not in src


def test_total_usd_no_esta_dentro_de_la_grilla_editable_de_costos_blandos():
    src = _leer()
    assert 'column_order=["Activo", "Descripcion", "Ref", "Cantidad", "Unidad", "USD_un"]' in src


def test_existe_tabla_de_solo_lectura_con_total_usd_en_ambos_lugares():
    src = _leer()
    assert src.count('st.dataframe(') >= 2  # una en _editar_seccion(), otra en Costos Blandos
    assert src.count('edited[["Descripcion", "Cantidad", "USD_un", "Total USD"]]') == 1
    assert src.count('ed_soft[["Descripcion", "Cantidad", "USD_un", "Total USD"]]') == 1
