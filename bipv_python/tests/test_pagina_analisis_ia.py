# -*- coding: utf-8 -*-
"""Validación de pages/18_🤖_Análisis_IA.py sin importar streamlit (no
disponible en este entorno de desarrollo — mismo patrón que
test_carga_proyecto_127.py e invalidacion.py): se audita el código fuente
vía AST/regex.

El riesgo real de esta página no es de sintaxis (py_compile ya lo cubre) —
es que _candidato_actual() lea una clave de session_state que NINGUNA
página realmente escribe (typo o clave renombrada en otro refactor), lo
que produciría un candidato con campos en None/0.0 silenciosamente en vez
de fallar. Este test cruza cada `st.session_state.get("clave"` de la
página nueva contra `st.session_state["clave"] =` en las páginas que
DEBERÍAN escribirla, para que un typo rompa el test en vez de en producción.
"""
import ast
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAGINA_IA = os.path.join(_ROOT, "pages", "18_🤖_Análisis_IA.py")
_PAGES_DIR = os.path.join(_ROOT, "pages")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_pagina_ia_es_python_valido():
    ast.parse(_leer(_PAGINA_IA))


def _claves_leidas_en(src: str) -> set[str]:
    """Claves de st.session_state.get("clave"...) o st.session_state["clave"] (lectura)."""
    return set(re.findall(r'st\.session_state(?:\.get)?\[?"([a-zA-Z_][\w]*)"', src))


def _claves_escritas_en_repo() -> set[str]:
    """Unión de toda clave `st.session_state["clave"] = ...` en pages/."""
    escritas = set()
    for nombre in os.listdir(_PAGES_DIR):
        if not nombre.endswith(".py"):
            continue
        src = _leer(os.path.join(_PAGES_DIR, nombre))
        escritas |= set(re.findall(r'st\.session_state\["([a-zA-Z_][\w]*)"\]\s*=', src))
    return escritas


def test_todas_las_claves_leidas_por_ia_tienen_escritor_real():
    src = _leer(_PAGINA_IA)
    leidas = _claves_leidas_en(src)
    escritas = _claves_escritas_en_repo()

    # Flags de sesión que la propia página escribe (resultados de los agentes,
    # cacheados en session_state) -- no son claves que otra página deba producir.
    propias = {
        "ia_analista_texto", "ia_analista_uso", "ia_asesor_texto", "ia_asesor_uso",
    }

    faltantes = leidas - escritas - propias
    assert not faltantes, (
        f"pages/18_🤖_Análisis_IA.py lee st.session_state[...] que ninguna página "
        f"escribe realmente (posible typo): {sorted(faltantes)}"
    )


def test_gating_de_prerrequisitos_usa_los_tres_flags_correctos():
    src = _leer(_PAGINA_IA)
    for flag in ("recurso_solar_ok", "produccion_ok", "financiero_ok"):
        assert f'"{flag}"' in src, f"falta el gate de prerrequisito '{flag}'"


def test_no_ejecuta_agentes_sin_boton_explicito():
    # Regla de costo: ejecutar_analisis/ejecutar_asesoria SOLO deben aparecer
    # dentro de un bloque `if st.button(...)`, nunca al nivel del módulo.
    src = _leer(_PAGINA_IA)
    tree = ast.parse(src)

    llamadas_top_level = set()
    for nodo in ast.walk(tree):
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
            llamadas_top_level.add(nodo.func.id)

    # No debe haber una llamada a ejecutar_analisis/ejecutar_asesoria que NO
    # esté anidada dentro de un ast.If (aproximación: contarlas y verificar
    # que el número de apariciones coincide con las que están dentro de un If).
    def _dentro_de_if(nodo_llamada, arbol):
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.If):
                for hijo in ast.walk(nodo):
                    if hijo is nodo_llamada:
                        return True
        return False

    llamadas_agentes = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id in ("ejecutar_analisis", "ejecutar_asesoria")
    ]
    assert llamadas_agentes, "no encontré llamadas a los agentes en la página"
    for llamada in llamadas_agentes:
        assert _dentro_de_if(llamada, tree), (
            "una llamada a un agente (con costo real de API) está fuera de un "
            "bloque condicional -- se ejecutaría automáticamente al cargar la página"
        )


def test_pregunta_de_ambos_agentes_declara_el_tipo_de_instalacion_real():
    # Regresión: un usuario corrió un ejercicio de "Granja fotovoltaica" y el
    # Analista narró en clave de "fachada de edificio" -- el SYSTEM_PROMPT de
    # los agentes asumía BIPV-en-fachada por defecto. El fix tiene dos partes:
    # el SYSTEM_PROMPT ya no asume fachada (ver tests de agentes/), Y esta
    # página declara el tipo real como dato explícito en cada pregunta para
    # que el agente nunca tenga que adivinarlo. Este test cubre la segunda
    # parte -- que _contexto_tipo (derivado de session_state["tipo_instalacion"])
    # efectivamente viaje a las DOS llamadas, no solo a una.
    src = _leer(_PAGINA_IA)
    assert 'st.session_state.get("tipo_instalacion"' in src

    tree = ast.parse(src)
    llamadas = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id in ("ejecutar_analisis", "ejecutar_asesoria")
    ]
    assert len(llamadas) == 2

    def _usa_contexto_tipo(nodo_llamada, arbol):
        # La pregunta se arma en una asignación previa (`pregunta = ...` /
        # `pregunta_asesor = ...`) dentro del mismo bloque `if`. Verificamos
        # que ese `if` contenga una f-string que referencie _contexto_tipo.
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.If):
                contiene_llamada = any(h is nodo_llamada for h in ast.walk(nodo))
                if not contiene_llamada:
                    continue
                for hijo in ast.walk(nodo):
                    if isinstance(hijo, ast.Name) and hijo.id == "_contexto_tipo":
                        return True
        return False

    for llamada in llamadas:
        assert _usa_contexto_tipo(llamada, tree), (
            f"la llamada a {llamada.func.id} no parece incluir _contexto_tipo "
            "en su bloque -- el agente podría volver a adivinar el tipo de instalación"
        )
