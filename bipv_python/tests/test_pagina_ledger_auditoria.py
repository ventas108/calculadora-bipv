# -*- coding: utf-8 -*-
"""Ledger de Auditoría — integración en las páginas (2026-08-25).

Streamlit no está instalado en este entorno de desarrollo -- se audita el
código fuente vía regex/AST, mismo patrón que los demás tests de páginas.
"""
import ast
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG_LEDGER = os.path.join(_ROOT, "pages", "19_🔒_Ledger_Auditoria.py")
_PAG_REPORTE = os.path.join(_ROOT, "pages", "10_📄_Reporte_PDF.py")
_PAG_DIAGNOSTICO = os.path.join(_ROOT, "pages", "13_🔍_Diagnostico.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# ═══════════════════════════ Página del Ledger ══════════════════════════════

def test_pagina_ledger_tiene_sintaxis_valida():
    ast.parse(_leer(_PAG_LEDGER))


def test_pagina_ledger_requiere_login():
    src = _leer(_PAG_LEDGER)
    assert "requerir_login()" in src


def test_pagina_ledger_bloquea_sin_usuario_de_sesion():
    src = _leer(_PAG_LEDGER)
    assert "if not _usuario:" in src
    assert "st.stop()" in src


def test_pagina_ledger_tiene_boton_de_verificar_integridad():
    src = _leer(_PAG_LEDGER)
    assert "verificar_cadena" in src
    assert "Verificar integridad de la cadena" in src


def test_pagina_ledger_tiene_exportacion_json_y_markdown():
    src = _leer(_PAG_LEDGER)
    assert 'formato="json"' in src
    assert 'formato="markdown"' in src


def test_pagina_ledger_permite_sellar_los_3_tipos():
    src = _leer(_PAG_LEDGER)
    assert "options=list(ledger.TIPOS_VALIDOS)" in src


# ═══════════════════════════ Reporte PDF ════════════════════════════════════

def test_reporte_pdf_importa_el_ledger():
    src = _leer(_PAG_REPORTE)
    assert "from calculos import ledger_auditoria" in src


def test_reporte_pdf_el_sellado_es_opcional_no_forzado():
    src = _leer(_PAG_REPORTE)
    assert 'st.checkbox(\n    "🔒 Sellar este resultado en el Ledger de Auditoría"' in src \
        or "🔒 Sellar este resultado en el Ledger de Auditoría" in src
    assert "value=True" in src  # default marcado, pero el usuario puede desmarcarlo


def test_reporte_pdf_solo_ofrece_bancable_e_informativo_no_diagnostico():
    # El diagnóstico de sistema instalado se sella desde su propia página, no
    # desde el Reporte PDF de un proyecto nuevo.
    src = _leer(_PAG_REPORTE)
    idx = src.index("sel_tipo_sello_reporte")
    bloque = src[max(0, idx - 400):idx]
    assert '"presupuesto_bancable", "presupuesto_informativo"' in bloque
    assert "diagnostico_operacion" not in bloque


def test_reporte_pdf_imprime_id_de_verificacion_en_el_html():
    src = _leer(_PAG_REPORTE)
    assert "ID de verificación del Ledger de " in src
    assert "Auditoría: <code>" in src
    assert '_eslabon_rep["hash_propio"][:16]' in src


def test_reporte_pdf_avisa_si_falla_el_sellado_en_vez_de_fallar_en_silencio():
    src = _leer(_PAG_REPORTE)
    assert "No se pudo sellar en el Ledger de Auditoría" in src


def test_reporte_pdf_no_bloquea_la_generacion_si_no_se_sella():
    # El reporte debe poder generarse igual con el checkbox desmarcado.
    src = _leer(_PAG_REPORTE)
    assert "html_bytes = html_str.encode" in src


# ═══════════════════════════ Diagnóstico ════════════════════════════════════

def test_diagnostico_importa_el_ledger():
    src = _leer(_PAG_DIAGNOSTICO)
    assert "from calculos import ledger_auditoria" in src


def test_diagnostico_sella_con_tipo_diagnostico_operacion():
    src = _leer(_PAG_DIAGNOSTICO)
    assert '"diagnostico_operacion"' in src


def test_diagnostico_el_sellado_es_independiente_del_historico():
    # Deben ser 2 botones distintos -- uno para el histórico de tendencia,
    # otro para el ledger de integridad -- no la misma acción.
    src = _leer(_PAG_DIAGNOSTICO)
    assert "Guardar este diagnóstico en el histórico" in src
    assert "Sellar en el Ledger de Auditoría" in src
