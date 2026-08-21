# -*- coding: utf-8 -*-
"""Validación de pages/4d_🧭_Comparador_Orientación.py sin importar streamlit
(no disponible en este entorno de desarrollo) -- mismo patrón que
tests/test_pagina_comparador_paneles.py: audita el código fuente vía AST/regex.
"""
import ast
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAGINA = os.path.join(_ROOT, "pages", "4d_🧭_Comparador_Orientación.py")
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
    propias = {"_df_comparador_orientacion", "ia_orientacion_texto", "ia_orientacion_uso"}

    faltantes = leidas - escritas - propias
    assert not faltantes, (
        f"pages/4d_🧭_Comparador_Orientación.py lee st.session_state[...] que ninguna "
        f"página escribe realmente (posible typo): {sorted(faltantes)}"
    )


def test_gating_de_prerrequisitos_correcto():
    src = _leer(_PAGINA)
    for flag in ("recurso_solar_ok", "produccion_ok"):
        assert f'"{flag}"' in src


def test_no_simula_sin_boton_explicito():
    # comparar_orientacion() puede correr decenas de simulaciones de 8760h --
    # no debe correr automáticamente al cargar la página.
    src = _leer(_PAGINA)
    tree = ast.parse(src)

    llamadas = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "comparar_orientacion"
    ]
    assert llamadas, "no encontré la llamada a comparar_orientacion() en la página"

    def _dentro_de_if(nodo_llamada, arbol):
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.If):
                if any(h is nodo_llamada for h in ast.walk(nodo)):
                    return True
        return False

    for llamada in llamadas:
        assert _dentro_de_if(llamada, tree), (
            "comparar_orientacion() está fuera de un bloque condicional -- se "
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
    assert "formatear_comparacion_orientacion(df_or, tipo_instalacion)" in src


def test_llama_init_trm():
    src = _leer(_PAGINA)
    assert "from calculos.trm_utils import init_trm" in src
    assert "init_trm()" in src


def test_config_base_pasa_n_inversores_al_motor():
    # Mismo criterio que 4c -- si el proyecto tiene varios inversores
    # idénticos (granja), el barrido debe representar el proyecto completo.
    src = _leer(_PAGINA)
    assert 'st.session_state.get("N_inv_total", 1)' in src
    assert "N_inversores=_n_inv_total" in src


def test_malla_incluye_siempre_la_orientacion_actual():
    # Sin esto, el barrido podría nunca comparar contra el punto de partida
    # real del proyecto -- ver malla_tilt_azimuth(tilt_actual=..., azimuth_actual=...).
    src = _leer(_PAGINA)
    assert "tilt_actual=_cfg_actual.tilt" in src
    assert "azimuth_actual=_cfg_actual.azimuth" in src


def test_adopcion_no_escribe_tilt_azimuth_sin_recalcular_la_poa():
    # Bug real que este test evita: escribir tilt_fachada/azimuth_fachada sin
    # recalcular poa_df dejaría la POA desfasada de la geometría nueva --
    # Producción/Financiero seguirían usando la POA de la orientación vieja
    # silenciosamente. calcular_poa() debe llamarse ANTES de actualizar
    # session_state con la nueva geometría.
    src = _leer(_PAGINA)
    assert "from calculos.solar import ORIENTACIONES, calcular_poa" in src
    idx_poa = src.index("poa_nueva = calcular_poa(")
    idx_set = src.index('"tilt_fachada": _tilt_adopt,')
    assert idx_poa < idx_set


def test_adopcion_actualiza_las_guardas_de_drift():
    # Sin actualizar _solar_tilt_guardado/_solar_az_guardado, la próxima
    # visita a 📐 Recurso Solar podría no detectar (o detectar un falso)
    # drift de geometría -- ver el bloque "#64/#172" de esa página.
    src = _leer(_PAGINA)
    for clave in ("_solar_tilt_guardado", "_solar_az_guardado", "_solar_albedo_guardado"):
        assert f'"{clave}": ' in src


def test_adopcion_invalida_derivados_de_poa():
    src = _leer(_PAGINA)
    assert "for k in KEYS_DERIVADOS_POA if k in st.session_state" in src


def test_page_links_apuntan_a_archivos_reales():
    src = _leer(_PAGINA)
    rutas = re.findall(r'st\.page_link\(\s*"(pages/[^"]+\.py)"', src)
    assert rutas, "no encontré ningún st.page_link() en la página"
    for ruta in rutas:
        ruta_absoluta = os.path.join(_ROOT, ruta)
        assert os.path.isfile(ruta_absoluta), f"st.page_link() apunta a un archivo que no existe: {ruta}"


def test_avisa_el_tamano_de_la_malla_antes_de_correrla():
    # Costo real: cada combinación es una simulación de 8760h -- el usuario
    # debe ver cuántas va a correr ANTES de presionar el botón.
    src = _leer(_PAGINA)
    idx_caption = src.index("simulaciones** de 8.760 horas")
    idx_boton = src.index('st.button("▶️ Comparar orientaciones"')
    assert idx_caption < idx_boton
