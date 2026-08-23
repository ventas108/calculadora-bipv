# -*- coding: utf-8 -*-
"""Carga de cotización de proveedor en 💼 Presupuesto → Perfilería y
Estructura (2026-08-22).

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


def test_importa_el_extractor_generico_de_cotizaciones():
    src = _leer()
    assert "from calculos.extractor_cotizaciones import" in src
    assert "extraer_cotizacion" in src
    assert "CAMPOS_COTIZACION" in src


def test_uploader_acepta_pdf_y_word():
    src = _leer()
    assert 'type=["pdf", "docx"]' in src
    assert 'key="upl_cotizacion_perfileria"' in src


def test_no_se_reextrae_el_mismo_archivo_en_cada_rerun():
    # Debe usar un hash del contenido para no volver a llamar al extractor
    # (y potencialmente a la IA) en cada rerun de Streamlit con el mismo PDF.
    src = _leer()
    assert "hashlib.sha256" in src
    assert '_cotiz_hash_perfileria' in src


def test_muestra_evidencia_citada_antes_de_aplicar():
    src = _leer()
    assert "Evidencia citada" in src
    assert "evidencia" in src


def test_no_aplica_sin_capacidad_y_precio_extraidos():
    src = _leer()
    assert "_puede_aplicar = bool(_cap and _precio_w)" in src
    assert "disabled=not _puede_aplicar" in src


def test_boton_aplicar_escribe_en_la_seccion_perfileria_y_persiste_la_fuente():
    src = _leer()
    assert 'ss_key = "df_sec_perfileria"' in src
    assert 'st.session_state["fuente_inp_perfileria"] = _fuente_txt' in src
    assert "pstore.guardar_seccion(" in src


def test_recargar_la_misma_cotizacion_reemplaza_en_vez_de_duplicar():
    src = _leer()
    assert '_df_actual = _df_actual[_df_actual["Ref"] != _ref]' in src


def test_hay_boton_para_descartar_sin_aplicar():
    src = _leer()
    assert 'btn_descartar_cotizacion_perfileria' in src


def test_advierte_si_capacidad_por_precio_no_coincide_con_el_total_del_documento():
    src = _leer()
    assert "Capacidad × Precio/W da USD" in src
