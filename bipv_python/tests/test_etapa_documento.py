# -*- coding: utf-8 -*-
"""Spec 07-informes/etapa-documento (2-oct-2026).

El 📄 Reporte llevaba «BORRADOR» fijo en el encabezado y un aviso dirigido al
diseñador («Verifique los datos de entrada antes de presentarlo al cliente»)
que llegaba al cliente. El usuario lo borraba a mano en Word y volvía a salir.
Ahora un selector «Etapa del documento» elige la etiqueta y el aviso.
"""
import io
from pathlib import Path

import pytest

from calculos.etapa_documento import ETAPA_DEFECTO, ETAPAS, encabezado_etapa

_RAIZ = Path(__file__).resolve().parents[1]


def test_etapas_y_defecto():
    assert ETAPA_DEFECTO == "prefactibilidad"
    assert list(ETAPAS) == ["prefactibilidad", "propuesta", "conceptual", "revision_cliente", "borrador"]
    assert ETAPAS["prefactibilidad"]["etiqueta"] == "ESTUDIO DE PREFACTIBILIDAD"
    assert ETAPAS["borrador"]["etiqueta"] == "BORRADOR INTERNO"


@pytest.mark.parametrize("clave", ["prefactibilidad", "propuesta", "conceptual", "revision_cliente"])
def test_las_etapas_para_el_cliente_no_dicen_borrador(clave):
    badge, aviso = encabezado_etapa(clave)
    texto = (badge + aviso).upper()
    assert "BORRADOR" not in texto and "PRESENTARLO AL CLIENTE" not in texto
    assert ETAPAS[clave]["etiqueta"] in badge


def test_el_borrador_interno_conserva_el_aviso_al_disenador():
    badge, aviso = encabezado_etapa("borrador")
    assert "BORRADOR INTERNO" in badge and "presentarlo al cliente" in aviso


def test_clave_desconocida_usa_la_de_defecto():
    assert encabezado_etapa("xyz") == encabezado_etapa(ETAPA_DEFECTO)
    assert encabezado_etapa(None) == encabezado_etapa(ETAPA_DEFECTO)


def test_word_y_pdf_llevan_la_etapa_elegida():
    from calculos.reporte_documentos import documentos_reporte
    badge, aviso = encabezado_etapa("propuesta")
    html = (f"<html><body><div><h1>Empresa</h1><div>REPORTE TÉCNICO — SISTEMA BIPV {badge}</div></div>"
            f"{aviso}<h2>Sección</h2><p>Texto</p></body></html>")
    docs = documentos_reporte(html)
    from docx import Document
    texto = " ".join(p.text for p in Document(io.BytesIO(docs["docx"])).paragraphs)
    assert "PROPUESTA TÉCNICA" in texto and "BORRADOR" not in texto
    import pdfplumber
    with pdfplumber.open(io.BytesIO(docs["pdf"])) as d:
        assert "PROPUESTA TÉCNICA" in " ".join(p.extract_text() or "" for p in d.pages)


def test_la_pagina_tiene_el_selector_y_no_tiene_borrador_fijo():
    src = (_RAIZ / "pages" / "10_📄_Reporte_PDF.py").read_text(encoding="utf-8")
    assert '"Etapa del documento"' in src and 'key="rep_etapa"' in src
    assert "encabezado_etapa(" in src
    assert ">BORRADOR<" not in src and "<strong>BORRADOR:</strong>" not in src


def test_manual_del_asistente_seccion_117():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 117.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("Etapa del documento", "Estudio de prefactibilidad", "Propuesta técnica", "Diseño conceptual",
              "Borrador interno", "Word"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    assert "PVsyst" not in s and "pendiente" not in s
