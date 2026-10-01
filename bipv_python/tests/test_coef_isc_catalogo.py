# -*- coding: utf-8 -*-
"""Spec 01-datos-proyecto/coef-isc-catalogo (1-oct-2026).

El coeficiente de temperatura de Isc (α, %/°C) se guardaba desde «Agregar
desde PDF» (columna CoefIsc_C) pero el catálogo nunca lo leía: el panel
quedaba sin α y 🔬 Motor IV avisaba «Coef. Temp. Isc (α) no definido». La
tabla de edición tampoco tenía la columna.
"""
from pathlib import Path

import pandas as pd

from calculos.panel_iv_check import analizar_panel_motiv
from datos.catalogo_paneles_excel import alfa_isc_desde_fila

_RAIZ = Path(__file__).resolve().parents[1]


def test_lee_la_columna_y_usa_el_respaldo_de_la_ficha():
    assert alfa_isc_desde_fila({"CoefIsc_C": 0.045}, "Otro") == 0.045
    assert alfa_isc_desde_fila(pd.Series({"CoefIsc_C": float("nan")}), "Otro") is None
    assert alfa_isc_desde_fila({}, "ASP-ST1-T40") == 0.06          # ficha SolTech: TKα +0,06 %/°C
    assert alfa_isc_desde_fila({"CoefIsc_C": 0.05}, "ASP-ST1-T40") == 0.05   # el Excel manda


def test_el_catalogo_entrega_tk_alfa_a_motor_iv():
    from datos.catalogo_paneles_excel import cargar_catalogo_paneles
    p = dict(cargar_catalogo_paneles()["ASP-ST1-T40"])
    assert p["Tk_alfa"] == 0.06 and p["CoefIsc_C"] == 0.06
    _, avisos = analizar_panel_motiv(p)
    assert not any("Isc (α)" in a[0] for a in avisos)


def test_la_tabla_de_edicion_tiene_la_columna():
    src = (_RAIZ / "pages" / "14_📋_Catálogo_Paneles.py").read_text(encoding="utf-8")
    assert '"α Isc (%/°C)":' in src and '"CoefIsc_C":         row_ed["α Isc (%/°C)"]' in src


def test_manual_del_asistente_lo_explica():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 111.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("α Isc (%/°C)", "Motor IV", "Validar y usar SDM real", "menos de 0,1 %"):
        assert t in s
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    assert "PVsyst" not in s and "pendiente" not in s
