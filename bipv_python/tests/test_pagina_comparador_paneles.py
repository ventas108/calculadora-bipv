# -*- coding: utf-8 -*-
"""Validación de pages/4c_🧩_Comparador_Paneles.py sin importar streamlit
(no disponible en este entorno de desarrollo) -- mismo patrón que
tests/test_pagina_analisis_ia.py: audita el código fuente vía AST/regex.

Riesgo real que este test cubre: _config_base() lee varias claves de
session_state a mano (mismo patrón que la página de Análisis IA) -- un
typo ahí produciría una BIPVConfiguration con campos en 0/None sin que
nadie lo note hasta que alguien compare paneles con un sitio equivocado.
"""
import ast
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAGINA = os.path.join(_ROOT, "pages", "4c_🧩_Comparador_Paneles.py")
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

    # La propia página escribe estas al comparar/adoptar/consultar al agente
    # -- no son claves que otra página deba producir.
    propias = {"_df_comparador_paneles", "ia_produccion_texto", "ia_produccion_uso"}

    faltantes = leidas - escritas - propias
    assert not faltantes, (
        f"pages/4c_🧩_Comparador_Paneles.py lee st.session_state[...] que ninguna "
        f"página escribe realmente (posible typo): {sorted(faltantes)}"
    )


def test_gating_de_prerrequisitos_correcto():
    src = _leer(_PAGINA)
    for flag in ("recurso_solar_ok", "produccion_ok"):
        assert f'"{flag}"' in src


def test_no_simula_sin_boton_explicito():
    # comparar_paneles() re-simula 8760h por candidato -- no debe correr
    # automáticamente al cargar la página.
    src = _leer(_PAGINA)
    tree = ast.parse(src)

    llamadas = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "comparar_paneles"
    ]
    assert llamadas, "no encontré la llamada a comparar_paneles() en la página"

    def _dentro_de_if(nodo_llamada, arbol):
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.If):
                if any(h is nodo_llamada for h in ast.walk(nodo)):
                    return True
        return False

    for llamada in llamadas:
        assert _dentro_de_if(llamada, tree), (
            "comparar_paneles() está fuera de un bloque condicional -- se "
            "ejecutaría automáticamente al cargar la página"
        )


def test_analista_produccion_no_se_ejecuta_sin_boton_explicito():
    # ejecutar_analisis_produccion() tiene costo real de API -- mismo
    # requisito que comparar_paneles(), verificado por separado porque es
    # un llamado distinto con su propio botón.
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
    # Mismo principio que corrigió el sesgo de fachada en los otros agentes
    # -- el contexto que arma esta página debe declarar el tipo real.
    src = _leer(_PAGINA)
    assert "formatear_comparacion_paneles(df_cmp, tipo_instalacion)" in src


def test_config_base_pasa_n_inversores_al_motor():
    # Corregido 2026-08-22 (ver simulation/schemas.py -- nota "Multi-inversor"):
    # run_bipv_simulation() ahora escala N_paneles/P_dc_stc_kW por
    # config.N_inversores, así que _config_base() DEBE pasar N_inv_total del
    # proyecto real -- si no, el comparador vuelve a subestimar la energía de
    # un proyecto multi-inversor como el de la granja de 9 inversores.
    src = _leer(_PAGINA)
    assert 'st.session_state.get("N_inv_total", 1)' in src
    assert "N_inversores=_n_inv_total" in src


def test_avisa_que_la_comparacion_es_del_proyecto_completo_cuando_aplica():
    src = _leer(_PAGINA)
    assert "_n_inv_total > 1" in src
    assert "proyecto completo" in src


def test_adopcion_invalida_poa_efectiva_a_diferencia_del_comparador_de_inversores():
    # A diferencia de 4b (que excluye poa_efectiva_df de la invalidación
    # porque el inversor no afecta la POA), adoptar un panel SÍ debe
    # invalidar la POA completa -- el panel determina NOCT/transparencia
    # que usa el Motor Óptico. La página NO debe filtrar KEYS_DERIVADOS_POA
    # como hace 4b (`if k != "poa_efectiva_df"`).
    src = _leer(_PAGINA)
    assert "for k in KEYS_DERIVADOS_POA if k in st.session_state" in src
    assert 'if k != "poa_efectiva_df"' not in src
