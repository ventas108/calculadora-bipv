# -*- coding: utf-8 -*-
"""Bug real encontrado y corregido (4-sep-2026, ver
FANTASMA NEGATIVO Y POSITIVO EN TEMPERATURA BMODULO PRODUCCION.docx): los 3
defaults de session_state para las temperaturas de diseño en 📐 Dimensionamiento
eran valores mágicos fijos (-5.0/36.35/41.94, universales para cualquier
ciudad) en vez de derivarse de la ciudad activa del proyecto (mismo dato real
que ya usa 🏠 Proyecto, datos/ciudades_colombia.py::CIUDADES).

Consecuencia real observada por el usuario: al abrir la página ANTES de que
☀️ Recurso Solar cacheara el TMY completo (tmy_df en session_state), T_mín
diseño mostraba -5,00°C para un proyecto en Bogotá real (donde el valor
correcto es 5.0°C) -- y para cualquier otra ciudad (ej. Cali: real 12.0/47.0/
55.0) los 3 valores hubieran sido directamente incorrectos, no solo el
primero. El bloque de auto-población desde el TMY real (líneas ~197-220)
corregía el valor una vez visitada esa página, pero mientras tanto el
placeholder mostrado -- y usado en cálculos reales de compatibilidad
eléctrica (Voc_max, Vdc_max) -- era el número inventado, no el real de la
ciudad.

Mismo patrón AST/substring que test_pagina_dimensionamiento_compat_bateria.py
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


def test_pagina_dimensionamiento_importa_ciudades():
    src = _leer(_PAG_DIM)
    assert "from datos.ciudades_colombia import CIUDADES" in src


def test_pagina_dimensionamiento_ya_no_usa_los_3_defaults_magicos_fijos():
    # Regresión directa del bug: -5.0/36.35/41.94 hardcodeados como default
    # universal, sin depender de la ciudad activa del proyecto.
    src = _leer(_PAG_DIM)
    assert 'st.session_state.setdefault("T_min_diseno", -5.0)' not in src
    assert 'st.session_state.setdefault("T_cel_realista", 36.35)' not in src
    assert 'st.session_state.setdefault("T_cel_extremo", 41.94)' not in src


def test_pagina_dimensionamiento_deriva_los_3_defaults_de_la_ciudad_activa():
    src = _leer(_PAG_DIM)
    assert '_ciudad_activa_dim = st.session_state.get("ciudad", "Bogotá")' in src
    assert '_ciudad_defaults = CIUDADES.get(_ciudad_activa_dim, CIUDADES.get("Bogotá", {}))' in src
    assert 'st.session_state.setdefault("T_min_diseno", _ciudad_defaults.get("T_min_diseno", 5.0))' in src
    assert 'st.session_state.setdefault("T_cel_realista", _ciudad_defaults.get("T_cel_realista", 36.35))' in src
    assert 'st.session_state.setdefault("T_cel_extremo", _ciudad_defaults.get("T_cel_extremo", 41.94))' in src


def test_ciudades_colombia_tiene_valores_reales_distintos_por_ciudad():
    # Ancla real: si esto alguna vez colapsa a un solo valor universal para
    # todas las ciudades, el fix de esta página deja de tener sentido.
    from datos.ciudades_colombia import CIUDADES

    bogota = CIUDADES["Bogotá"]
    cali = CIUDADES["Cali"]
    assert bogota["T_min_diseno"] == 5.0
    assert bogota["T_cel_realista"] == 36.35
    assert bogota["T_cel_extremo"] == 41.94
    assert cali["T_min_diseno"] == 12.0
    assert cali["T_cel_realista"] == 47.0
    assert cali["T_cel_extremo"] == 55.0
    assert bogota["T_min_diseno"] != cali["T_min_diseno"]
