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
import ast
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAGINA = os.path.join(_ROOT, "pages", "4b_⚖️_Comparador_Inversores.py")
_PAGES_DIR = os.path.join(_ROOT, "pages")


def _leer(ruta=_PAGINA):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_llama_init_trm_antes_de_leer_tipo_cambio():
    src = _leer()
    assert "from calculos.trm_utils import init_trm" in src
    assert "init_trm()" in src
    idx_init = src.index("init_trm()")
    idx_uso = src.index('st.session_state.get("tipo_cambio"')
    assert idx_init < idx_uso


# ── Extensión 2026-08-21: "Comparar TODOS los inversores compatibles" +
# Analista de Producción (4º candidato de hardware, junto a paneles/
# orientación/baterías) -- mismo patrón AST/regex que los demás comparadores.

def test_pagina_sigue_siendo_python_valido():
    ast.parse(_leer())


def test_comparar_todos_no_se_ejecuta_sin_boton_explicito():
    src = _leer()
    tree = ast.parse(src)
    llamadas = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id == "comparar_todos_los_inversores_compatibles"
    ]
    assert llamadas, "no encontré la llamada a comparar_todos_los_inversores_compatibles()"

    def _dentro_de_if(nodo_llamada, arbol):
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.If):
                if any(h is nodo_llamada for h in ast.walk(nodo)):
                    return True
        return False

    for llamada in llamadas:
        assert _dentro_de_if(llamada, tree), (
            "comparar_todos_los_inversores_compatibles() está fuera de un bloque "
            "condicional -- se ejecutaría automáticamente al cargar la página"
        )


def test_analista_produccion_no_se_ejecuta_sin_boton_explicito():
    src = _leer()
    tree = ast.parse(src)
    llamadas = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id == "ejecutar_analisis_produccion"
    ]
    assert llamadas, "no encontré la llamada a ejecutar_analisis_produccion()"

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
    src = _leer()
    assert "formatear_comparacion_inversores(df_inv_cmp, _tipo_inst_inv)" in src


def test_reusa_el_mismo_n_strings_total_y_p_ac_ya_calculados():
    # No debe recalcular ni duplicar la serie horaria -- debe reusar
    # n_strings_total/p_ac_W/p_dc_stc_kW ya presentes en la página.
    src = _leer()
    assert "comparar_todos_los_inversores_compatibles(\n        df_comp, n_strings_total, p_ac_W, p_dc_stc_kW," in src


def test_no_reemplaza_el_flujo_manual_de_multiselect():
    # El multiselect de 2-4 modelos debe seguir existiendo -- esta función es
    # una adición, no un reemplazo.
    src = _leer()
    assert 'st.multiselect(' in src
    assert "Elige 2–4 modelos a comparar" in src


def test_page_links_apuntan_a_archivos_reales():
    src = _leer()
    rutas = re.findall(r'st\.page_link\(\s*"(pages/[^"]+\.py)"', src)
    assert rutas, "no encontré ningún st.page_link() en la página"
    for ruta in rutas:
        ruta_absoluta = os.path.join(_ROOT, ruta)
        assert os.path.isfile(ruta_absoluta), f"st.page_link() apunta a un archivo que no existe: {ruta}"


def test_analisis_ia_enlaza_de_vuelta_a_comparador_de_inversores():
    src_ia = _leer(os.path.join(_PAGES_DIR, "18_🤖_Análisis_IA.py"))
    assert "pages/4b_⚖️_Comparador_Inversores.py" in src_ia


def test_claves_de_session_state_propias_no_chocan_con_otras_paginas():
    # _df_comparador_inversores / ia_inversor_texto / ia_inversor_uso son
    # propias de esta sección -- confirmar que no las escribe ninguna otra
    # página (evita una colisión de caché entre features).
    src = _leer()
    propias = {"_df_comparador_inversores", "ia_inversor_texto", "ia_inversor_uso"}
    for nombre in os.listdir(_PAGES_DIR):
        if not nombre.endswith(".py") or nombre == "4b_⚖️_Comparador_Inversores.py":
            continue
        otro_src = _leer(os.path.join(_PAGES_DIR, nombre))
        for clave in propias:
            assert f'st.session_state["{clave}"] =' not in otro_src, (
                f"{nombre} también escribe st.session_state['{clave}'] -- colisión de caché"
            )
    assert 'st.session_state["_df_comparador_inversores"] = df_inv_cmp' in src
