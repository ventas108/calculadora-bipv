# -*- coding: utf-8 -*-
"""Validación de la sección "Comparar todas las baterías del catálogo" +
Analista de Producción agregada a pages/11_🔋_Baterias_y_Balance.py -- mismo
patrón AST/regex que tests/test_pagina_comparador_paneles.py (streamlit no
está instalado en este entorno de desarrollo). Solo audita la sección NUEVA,
no la página completa preexistente.
"""
import ast
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAGINA = os.path.join(_ROOT, "pages", "11_🔋_Baterias_y_Balance.py")
_PAGES_DIR = os.path.join(_ROOT, "pages")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_pagina_es_python_valido():
    ast.parse(_leer(_PAGINA))


def _claves_leidas_en(src: str) -> set[str]:
    return set(re.findall(r'st\.session_state(?:\.get)?\[?"([a-zA-Z_][\w]*)"', src))


def _claves_escritas_en_repo() -> set[str]:
    escritas = set()
    for nombre in os.listdir(_PAGES_DIR):
        if not nombre.endswith(".py"):
            continue
        src = _leer(os.path.join(_PAGES_DIR, nombre))
        escritas |= set(re.findall(r'st\.session_state\["([a-zA-Z_][\w]*)"\]\s*=', src))
    return escritas


def test_todas_las_claves_leidas_tienen_escritor_real():
    src = _leer(_PAGINA)
    leidas = _claves_leidas_en(src)
    escritas = _claves_escritas_en_repo()
    # Propias del comparador de baterías (caché del DataFrame y del agente).
    propias = {"_df_comparador_baterias", "ia_bateria_texto", "ia_bateria_uso"}
    faltantes = leidas - escritas - propias
    assert not faltantes, (
        f"pages/11_🔋_Baterias_y_Balance.py lee st.session_state[...] que ninguna "
        f"página escribe realmente (posible typo): {sorted(faltantes)}"
    )


def test_comparar_baterias_no_se_ejecuta_sin_boton_explicito():
    src = _leer(_PAGINA)
    tree = ast.parse(src)

    llamadas = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "comparar_baterias"
    ]
    assert llamadas, "no encontré la llamada a comparar_baterias() en la página"

    def _dentro_de_if(nodo_llamada, arbol):
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.If):
                if any(h is nodo_llamada for h in ast.walk(nodo)):
                    return True
        return False

    for llamada in llamadas:
        assert _dentro_de_if(llamada, tree), (
            "comparar_baterias() está fuera de un bloque condicional -- se "
            "ejecutaría automáticamente al cargar la página"
        )


def test_analista_produccion_no_se_ejecuta_sin_boton_explicito():
    src = _leer(_PAGINA)
    tree = ast.parse(src)

    llamadas = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id == "ejecutar_analisis_produccion"
    ]
    assert llamadas, "no encontré la llamada a ejecutar_analisis_produccion() en la página"

    def _dentro_de_if(nodo_llamada, arbol):
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.If):
                if any(h is nodo_llamada for h in ast.walk(nodo)):
                    return True
        return False

    for llamada in llamadas:
        assert _dentro_de_if(llamada, tree), (
            "ejecutar_analisis_produccion() está fuera de un bloque condicional -- se "
            "ejecutaría automáticamente al cargar la página"
        )


def test_analista_produccion_recibe_el_tipo_de_instalacion_real():
    src = _leer(_PAGINA)
    assert "formatear_comparacion_baterias(df_bat_cmp, _tipo_inst_bat)" in src


def test_comparador_usa_el_inversor_y_los_parametros_de_diseno_ya_configurados():
    # No debe duplicar widgets de consumo/autonomía -- debe reusar los que ya
    # existen en el flujo B-6 de esta misma página.
    src = _leer(_PAGINA)
    assert "comparar_baterias(\n        cat_bat, _inv_dim, _inv_nombre, E_consumo_diario, autonomia_h,\n    )" in src \
        or "comparar_baterias(" in src and "_inv_dim, _inv_nombre, E_consumo_diario, autonomia_h" in src


def test_page_links_apuntan_a_archivos_reales():
    src = _leer(_PAGINA)
    rutas = re.findall(r'st\.page_link\(\s*"(pages/[^"]+\.py)"', src)
    assert rutas, "no encontré ningún st.page_link() en la página"
    for ruta in rutas:
        ruta_absoluta = os.path.join(_ROOT, ruta)
        assert os.path.isfile(ruta_absoluta), f"st.page_link() apunta a un archivo que no existe: {ruta}"


def test_analisis_ia_enlaza_de_vuelta_a_baterias():
    _pagina_ia = os.path.join(_ROOT, "pages", "18_🤖_Análisis_IA.py")
    src = _leer(_pagina_ia)
    assert "pages/11_🔋_Baterias_y_Balance.py" in src
