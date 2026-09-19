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
    #
    # Regresión real (2026-08-21): esta aserción antes verificaba
    # "formatear_comparacion_paneles(df_cmp, tipo_instalacion)" -- pero
    # `tipo_instalacion` es la variable del selectbox LOCAL "Perfil de costos
    # CAPEX" (una de las 3 claves de BENCH, sin relación con el proyecto
    # real), no el tipo real del proyecto. El test pasaba igual porque solo
    # verificaba el NOMBRE de la variable, no su origen -- dándole falsa
    # confianza a un bug real: el selectbox arrancaba en "Granja FV campo"
    # (primera clave de BENCH) para CUALQUIER proyecto, y ese valor se le
    # narraba al agente como si fuera el tipo real, incluso sobre una
    # fachada. Ahora se verifica que el agente reciba una variable derivada
    # de session_state["tipo_instalacion"] (el dato real), no del selectbox.
    src = _leer(_PAGINA)
    assert "formatear_comparacion_paneles(df_cmp, _tipo_para_agente)" in src
    assert '_tipo_real_proyecto = st.session_state.get("tipo_instalacion"' in src
    idx_tipo_real = src.index('_tipo_real_proyecto = st.session_state.get("tipo_instalacion"')
    idx_uso_agente = src.index("formatear_comparacion_paneles(df_cmp, _tipo_para_agente)")
    assert idx_tipo_real < idx_uso_agente


def test_perfil_capex_no_es_el_tipo_real_del_proyecto():
    # El selectbox de perfil de costos CAPEX y el tipo real del proyecto son
    # conceptos distintos -- confirma que la página los distingue por
    # nombre de variable, no que comparta una sola "tipo_instalacion" para
    # ambos usos (la raíz del bug original).
    src = _leer(_PAGINA)
    assert "_MAPA_TIPO_A_CAPEX" in src
    assert 'tipo_instalacion = st.selectbox(\n        "Perfil de costos CAPEX' in src


def test_llama_init_trm_antes_de_leer_tipo_cambio():
    # Reportado por el usuario: la TRM mostraba el default hardcodeado
    # (4000.0) en vez de la TRM real, porque session_state["tipo_cambio"]
    # solo existe si el usuario ya visitó 💰 Financiero/💼 Presupuesto en
    # esta sesión (esas páginas son las que llaman init_trm()). Esta
    # página debe llamarlo también, no asumir que ya corrió en otro lado.
    src = _leer(_PAGINA)
    assert "from calculos.trm_utils import init_trm" in src
    assert "init_trm()" in src
    # Debe llamarse ANTES del primer session_state.get("tipo_cambio"...).
    idx_init = src.index("init_trm()")
    idx_uso = src.index('st.session_state.get("tipo_cambio"')
    assert idx_init < idx_uso


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


# ── Coherencia de adopción (19-sep-2026) ─────────────────────────────────────
# Hallazgo (auditoría de coherencia de comparadores): la adopción resolvía el
# panel elegido SOLO contra MODULOS_BIPV (7 fichas) aunque comparar_paneles()
# ya compara el catálogo unido real (miles de fichas Excel/NREL) -- KeyError
# o, peor, adoptar una ficha DISTINTA de la comparada si el nombre coincidía
# por casualidad. Además, "Compatible" != "❌" dejaba adoptar filas "—" (no
# evaluable) como si fueran compatibles. Ver tests/test_comparador_paneles.py
# para la cobertura de que _panel_dict trae la MISMA ficha usada al simular.

def test_adopcion_exige_compatible_exactamente_ok():
    src = _leer(_PAGINA)
    assert '_elegibles = df_cmp[df_cmp["Compatible"] == "✅"]["Panel"].tolist()' in src
    # Nunca el criterio laxo original (cualquier cosa que no sea "❌").
    assert '!= "❌"' not in src


def test_adopcion_nunca_resuelve_el_panel_contra_modulos_bipv():
    src = _leer(_PAGINA)
    # El módulo docstring de cabecera todavía MENCIONA MODULOS_BIPV en
    # prosa (contexto histórico del catálogo) -- lo que no debe existir es
    # un import ni un uso real en el flujo de adopción.
    assert "from datos.tecnologias_bipv import MODULOS_BIPV" not in src
    assert "MODULOS_BIPV[" not in src
    assert 'st.session_state["panel_dict"] = fila["_panel_dict"]' in src


def test_filas_no_evaluables_muestran_su_motivo():
    src = _leer(_PAGINA)
    assert '_no_evaluables = df_cmp[df_cmp["Compatible"] == "—"]' in src
    idx_no_eval = src.index("_no_evaluables = df_cmp")
    idx_elegibles = src.index("_elegibles = df_cmp")
    bloque = src[idx_no_eval:idx_elegibles]
    assert "_motivo_electrico" in bloque
    assert "st.info(" in bloque or "st.warning(" in bloque


def test_columnas_internas_nunca_llegan_a_la_tabla_ni_al_csv():
    # _panel_dict (dict de Python) rompería el render/format de st.dataframe
    # y ensuciaría el CSV exportado -- debe quedar fuera de ambos, igual que
    # _motivo_electrico ya quedaba fuera.
    src = _leer(_PAGINA)
    assert '_cols_internas = ["_motivo_electrico", "_panel_dict"]' in src
    assert "df_cmp.drop(columns=_cols_internas)" in src
    assert src.count("df_cmp.drop(columns=_cols_internas)") >= 2


# ── Guard de resultado legacy (19-sep-2026) ──────────────────────────────────
# Hallazgo (arreglo urgente post-coherencia): un df_cmp que ya estaba en
# session_state["_df_comparador_paneles"] ANTES de que comparar_paneles()
# empezara a publicar "_panel_dict"/"_motivo_electrico" no trae esas
# columnas -- df_cmp.drop(columns=[...]) lanza KeyError y rompe la página.
# El guard debe descartar ese resultado (nunca reconstruirlo desde ningún
# catálogo) ANTES de que el bloque de render/adopción lo toque.

def test_guard_legacy_verifica_ambas_columnas_internas_antes_de_renderizar():
    src = _leer(_PAGINA)
    assert '_COLS_INTERNAS_REQUERIDAS = ("_panel_dict", "_motivo_electrico")' in src
    idx_declara = src.index("_COLS_INTERNAS_REQUERIDAS = ")
    idx_guard = src.index("if df_cmp is not None and not df_cmp.empty and not all(")
    idx_render = src.index('if df_cmp is not None and not df_cmp.empty:\n    _cols_internas')
    assert idx_declara < idx_guard < idx_render, (
        "el guard de legacy debe declararse y ejecutarse ANTES del bloque "
        "que renderiza/adopta df_cmp"
    )


def test_guard_legacy_descarta_sin_reconstruir_desde_ningun_catalogo():
    src = _leer(_PAGINA)
    idx_guard = src.index("if df_cmp is not None and not df_cmp.empty and not all(")
    idx_render = src.index('if df_cmp is not None and not df_cmp.empty:\n    _cols_internas')
    bloque = src[idx_guard:idx_render]

    # Descarta el resultado guardado y detiene ESE flujo (df_cmp = None),
    # nunca lo repara.
    assert 'st.session_state.pop("_df_comparador_paneles", None)' in bloque
    assert "st.warning(" in bloque
    assert "df_cmp = None" in bloque
    assert "se generó con una versión" in bloque

    # Nunca intenta resolver/reconstruir la ficha o el motivo desde ningún
    # catálogo dentro de este bloque -- ese es exactamente el bug original.
    assert "MODULOS_BIPV" not in bloque
    assert "catalogo" not in bloque.lower()
    assert "_catalogo_paneles_real" not in bloque


def test_guard_legacy_no_dispara_con_dataframe_vacio():
    # Un df_cmp vacío (ningún panel simulable) es un caso YA manejado por el
    # "elif df_cmp is not None: st.error(...)" de más abajo -- no es un
    # problema de esquema legacy, y el guard no debe confundir los dos.
    src = _leer(_PAGINA)
    idx_guard = src.index("if df_cmp is not None and not df_cmp.empty and not all(")
    linea_guard = src[idx_guard: src.index(")", idx_guard) + 1]
    assert "not df_cmp.empty" in linea_guard or "not df_cmp.empty" in src[idx_guard:idx_guard + 80]


def test_guard_predicate_detecta_legacy_sin_columnas_internas():
    # Mismo predicado que usa la página, ejercido directamente contra
    # pandas real (sin depender de Streamlit) -- confirma el comportamiento,
    # no solo el texto fuente.
    import pandas as pd
    cols_requeridas = ("_panel_dict", "_motivo_electrico")

    df_legacy_total = pd.DataFrame([{"Panel": "ASP-ST1-T40", "Compatible": "✅"}])
    es_legacy = not df_legacy_total.empty and not all(
        c in df_legacy_total.columns for c in cols_requeridas
    )
    assert es_legacy is True

    # Solo falta _motivo_electrico (versión intermedia) -- también legacy,
    # nunca se reconstruye aunque _panel_dict SÍ esté presente.
    df_legacy_parcial = pd.DataFrame([
        {"Panel": "ASP-ST1-T40", "Compatible": "✅", "_panel_dict": {"Pmax_stc": 63.0}}
    ])
    es_legacy_parcial = not df_legacy_parcial.empty and not all(
        c in df_legacy_parcial.columns for c in cols_requeridas
    )
    assert es_legacy_parcial is True


def test_guard_predicate_caso_normal_no_es_legacy_y_tabla_csv_excluyen_internas():
    # Resultado NORMAL (con ambas columnas internas): el guard no lo
    # descarta, y drop(columns=[...]) sigue funcionando sin KeyError --
    # exactamente lo que rompería si el guard fuera demasiado agresivo.
    import pandas as pd
    cols_requeridas = ("_panel_dict", "_motivo_electrico")
    df_ok = pd.DataFrame([{
        "Panel": "ASP-ST1-T40", "Compatible": "✅",
        "E_ac (kWh/año)": 12345.0,
        "_panel_dict": {"Pmax_stc": 63.0}, "_motivo_electrico": "",
    }])

    es_legacy = not df_ok.empty and not all(c in df_ok.columns for c in cols_requeridas)
    assert es_legacy is False

    _cols_internas = ["_motivo_electrico", "_panel_dict"]
    tabla = df_ok.drop(columns=_cols_internas)
    csv = tabla.to_csv(index=False)
    assert "_panel_dict" not in tabla.columns
    assert "_motivo_electrico" not in tabla.columns
    assert "_panel_dict" not in csv
    assert "_motivo_electrico" not in csv
    assert "ASP-ST1-T40" in csv  # el resto de los datos SÍ debe seguir ahí


def test_page_link_a_analisis_ia_apunta_a_un_archivo_real():
    # El usuario reportó que no encontraba el Analista de Producción -- se
    # agregó un st.page_link() de vuelta hacia 🤖 Análisis IA (donde viven
    # los otros dos agentes). Un typo en la ruta dejaría el enlace roto sin
    # que nada lo avise -- mismo test simétrico que en test_pagina_analisis_ia.py.
    src = _leer(_PAGINA)
    rutas = re.findall(r'st\.page_link\(\s*"(pages/[^"]+\.py)"', src)
    assert rutas, "no encontré ningún st.page_link() en la página"
    for ruta in rutas:
        ruta_absoluta = os.path.join(_ROOT, ruta)
        assert os.path.isfile(ruta_absoluta), f"st.page_link() apunta a un archivo que no existe: {ruta}"
