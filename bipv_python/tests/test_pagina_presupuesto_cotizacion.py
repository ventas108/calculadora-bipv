# -*- coding: utf-8 -*-
"""Carga de cotización de proveedor en 💼 Presupuesto (2026-08-22).

Pedido de seguimiento del usuario: no duplicar el uploader en cada pestaña
de costo -- un solo punto de carga, con un clasificador liviano por
palabras clave que SUGIERE a cuál de las 6 secciones (todas menos
Estimación Rápida, que es paramétrica) pertenece la cotización. El usuario
confirma o corrige el destino antes de aplicar.

Streamlit no está instalado en este entorno de desarrollo -- se audita el
código fuente vía regex/AST, mismo patrón que los demás tests de páginas de
esta suite.
"""
import ast
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAGINA = os.path.join(_ROOT, "pages", "8_💼_Presupuesto.py")


def _leer():
    with open(_PAGINA, encoding="utf-8") as f:
        return f.read()


def test_la_pagina_tiene_sintaxis_valida():
    ast.parse(_leer())


def test_importa_el_extractor_y_el_clasificador_genericos():
    src = _leer()
    assert "from calculos.extractor_cotizaciones import" in src
    assert "extraer_cotizacion" in src
    assert "clasificar_categoria_costo" in src
    assert "CATEGORIA_LABELS" in src
    assert "CAMPOS_COTIZACION" in src


def test_hay_un_solo_uploader_no_uno_por_pestana():
    src = _leer()
    assert src.count('st.file_uploader(') == 1
    assert "upl_cotizacion_global_v" in src


def test_uploader_acepta_pdf_y_word():
    src = _leer()
    assert 'type=["pdf", "docx"]' in src


def test_no_se_reextrae_el_mismo_archivo_en_cada_rerun():
    src = _leer()
    assert "hashlib.sha256" in src
    assert "_cotiz_hash_global" in src


def test_el_uploader_vive_fuera_de_las_pestanas_por_costo():
    # El bloque de carga debe estar ANTES de que se abran las tabs (para que
    # aplique a cualquiera de las 6 secciones, no solo a la que esté activa).
    src = _leer()
    idx_upload = src.index("upl_cotizacion_global_v")
    idx_tabs = src.index("tabs = st.tabs([")
    assert idx_upload < idx_tabs


def test_las_6_secciones_de_costo_estan_disponibles_como_destino():
    src = _leer()
    assert '_SECCIONES_CON_CARGA = ("perfileria", "mano_obra", "sistema_fv", "inversor", "catalogo", "soft")' in src


def test_el_selectbox_de_destino_usa_la_categoria_sugerida_como_default():
    src = _leer()
    assert 'st.selectbox(' in src
    assert "_cotiz_categoria_sugerida_global" in src
    assert "index=_opciones_dest.index(_sugerida)" in src


def test_muestra_evidencia_citada_antes_de_aplicar():
    src = _leer()
    assert "Evidencia citada" in src
    assert "evidencia" in src


def test_muestra_las_coincidencias_por_categoria_para_transparencia():
    src = _leer()
    assert "_cotiz_puntajes_categoria_global" in src
    assert "Coincidencias por sección" in src


def test_fila_principal_admite_dos_modos_por_watt_o_monto_total():
    # Estructura/paneles se cotizan por Watt; mano de obra/ingeniería casi
    # siempre como un monto global -- ambos deben poder aplicarse.
    src = _leer()
    assert "if _cap and _precio_w:" in src
    assert 'elif _tot_fob:' in src
    assert '1.0, "glb", float(_tot_fob)' in src


def test_no_aplica_sin_fila_principal_utilizable():
    src = _leer()
    assert "_puede_aplicar = _fila_principal is not None" in src
    assert "disabled=not _puede_aplicar" in src


def test_boton_aplicar_escribe_en_la_seccion_elegida_dinamicamente():
    src = _leer()
    assert 'ss_key = f"df_sec_{_dest_key}"' in src
    assert 'st.session_state[f"fuente_inp_{_dest_key}"] = _fuente_txt' in src


def test_solo_persiste_a_disco_las_secciones_realmente_persistibles():
    # catalogo/soft no están en pstore.SECCIONES_PERSISTIBLES -- no deben
    # intentar guardarse a disco (evita una falla silenciosa o engañosa).
    src = _leer()
    assert "if _dest_key in pstore.SECCIONES_PERSISTIBLES:" in src


def test_recargar_la_misma_cotizacion_reemplaza_en_vez_de_duplicar():
    src = _leer()
    assert '_df_actual = _df_actual[_df_actual["Ref"] != _ref]' in src


def test_hay_boton_para_descartar_sin_aplicar():
    src = _leer()
    assert 'btn_descartar_cotizacion_global' in src


def test_advierte_si_capacidad_por_precio_no_coincide_con_el_total_del_documento():
    src = _leer()
    assert "Capacidad × Precio/W da USD" in src


def test_inicializa_costos_blandos_con_su_propia_plantilla_por_defecto():
    # "soft" (Costos Blandos) no usa _plantilla_con_activo (no viene del
    # Excel) -- debe caer a _SOFT_DEFAULT como el resto de la página.
    src = _leer()
    assert 'if key == "soft":' in src
    assert "_df_con_activo(_SOFT_DEFAULT)" in src


# ═══════ Auditoría 2026-08-23: el uploader debe soltar el archivo ═══════════
# Hallazgo: st.file_uploader retiene el archivo cargado entre reruns mientras
# su `key` no cambie. Aplicar/Descartar borraban el estado de sesión pero NO
# el archivo del widget -- en el siguiente rerun la app lo volvía a extraer
# sola, como si el botón no hubiera hecho nada. La corrección versiona el
# `key` del uploader (y del selector, para resincronizar la sugerencia con
# cada documento nuevo), mismo patrón que _ver_key en _editar_seccion().

def test_el_uploader_esta_versionado_para_poder_soltar_el_archivo():
    src = _leer()
    assert '"_cotiz_ver_uploader"' in src
    assert 'key=f"upl_cotizacion_global_v{st.session_state[\'_cotiz_ver_uploader\']}"' in src


def test_aplicar_y_descartar_incrementan_la_version_del_uploader():
    src = _leer()
    assert src.count('st.session_state["_cotiz_ver_uploader"] += 1') == 2


def test_el_selector_de_destino_esta_versionado_y_se_resincroniza_por_documento():
    src = _leer()
    assert '"_cotiz_ver_selector"' in src
    assert 'key=f"sel_destino_cotizacion_global_v{st.session_state[\'_cotiz_ver_selector\']}"' in src
    # Se incrementa SOLO al detectar un hash nuevo (documento distinto), no en
    # cada rerun mientras se revisa el mismo documento.
    assert 'st.session_state["_cotiz_ver_selector"] += 1' in src


def test_avisa_si_falla_el_guardado_en_disco_de_una_seccion_persistible():
    src = _leer()
    assert "No se pudo guardar la tabla en disco" in src


def test_avisa_si_no_hay_usuario_de_sesion_para_persistir():
    src = _leer()
    assert "No se detectó usuario de sesión" in src
