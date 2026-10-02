# -*- coding: utf-8 -*-
"""Spec 07-informes/reporte-cables-titulo-co2 (2-oct-2026).

Informe real «Granja Solar Apartadó» (606.522 kWh/año) ya con la revisión de
coherencia:
- el diagrama de pérdidas decía «Pérdida óhmica DC −0,85 % · Fuente: % manual
  configurado en Mismatch», sin fila de cables AC, mientras 🌾 Granja FV daba
  0,50 % DC y caídas AC de hasta 1,69 %: Producción no usó los cables reales;
- el encabezado decía «SISTEMA BIPV» en una granja en suelo;
- «CO₂ evitado — año 1: 76,42 t» con el texto fijo «Equivale a sacar un
  vehículo de circulación durante 1 año completo» (son ~24 autos).
"""
from pathlib import Path

import pytest

from calculos.co2 import KM_ANUALES_AUTO, texto_vehiculos, vehiculos_equivalentes
from calculos.coherencia_reporte import revisar_coherencia_reporte
from calculos.reporte_produccion import etiquetas_tipo

_RAIZ = Path(__file__).resolve().parents[1]

GRANJA = {
    "tipo_instalacion": "Granja fotovoltaica",
    "E_ac_anual_kWh": 606_522.0,
    "produccion_n_inversores": 4,
    "reparto_strings_inversores": [7, 7, 7, 7],
    "granja_electrico_cfg": {"calibre_dc_mm2": 6, "calibre_ac_mm2": 70},
    "pct_cableado_dc": 1.0, "pct_cableado_ac": 0.0,
    "res_produccion": {"perdida_ohmica_dc_modo": "manual", "perdida_ohmica_ac_modo": None},
}


def _cables(estado):
    return [p for p in revisar_coherencia_reporte(estado)
            if p["nivel"] == "error" and "cables" in p["titulo"]]


def test_granja_con_cables_calculados_y_produccion_manual():
    err = _cables(GRANJA)
    assert err, "debe avisar que Producción no usó los cables de Granja FV"
    assert "1.0 %" in err[0]["detalle"] and "🌾 Granja FV" in err[0]["detalle"]
    assert "⚡ Diagrama Unifilar" in err[0]["accion"] and "📊 Producción" in err[0]["accion"]


def test_unifilar_calculado_y_produccion_manual():
    estado = {**GRANJA, "tipo_instalacion": "Fachada BIPV", "granja_electrico_cfg": None,
              "perdida_ohmica_unifilar": {"resistencia_dc_ohm": 0.0084}}
    assert _cables(estado)


@pytest.mark.parametrize("cambio", [
    {"res_produccion": {"perdida_ohmica_dc_modo": "calculado", "perdida_ohmica_ac_modo": "calculado"}},
    {"granja_electrico_cfg": None},                                   # sin cables calculados
    {"multisup_activo": True, "E_ac_anual_kWh_multisup": 600_000.0},  # la cadena multi-superficie tiene los suyos
])
def test_sin_error_de_cables(cambio):
    assert not _cables({**GRANJA, **cambio})


def test_titulo_segun_tipo_de_instalacion():
    assert etiquetas_tipo("Granja fotovoltaica")["titulo"] == "SISTEMA FOTOVOLTAICO — GRANJA SOLAR"
    assert etiquetas_tipo("Techo plano (con soporte)")["titulo"] == "SISTEMA FOTOVOLTAICO"
    for t in ("Fachada BIPV", "Techo inclinado (BIPV)", "Pérgola / sombreadero", "Marquesina / voladizo", None):
        assert etiquetas_tipo(t)["titulo"] == "SISTEMA BIPV", t
    assert etiquetas_tipo("Granja fotovoltaica")["sujeto"] == "la granja solar"
    assert etiquetas_tipo("Fachada BIPV")["sujeto"] == "la fachada BIPV"
    assert etiquetas_tipo("Techo plano (con soporte)")["sujeto"] == "el sistema fotovoltaico"


def test_vehiculos_equivalentes():
    assert KM_ANUALES_AUTO == 20_000
    assert vehiculos_equivalentes(76.42) == pytest.approx(23.6, abs=0.1)     # 76,42 t ÷ (0,162 × 20.000)
    assert "24 autos" in texto_vehiculos(76.42)
    assert "1 auto " in texto_vehiculos(3.0)
    assert "un auto" not in texto_vehiculos(76.42)


def test_paginas_usan_los_textos_calculados():
    rep = (_RAIZ / "pages" / "10_📄_Reporte_PDF.py").read_text(encoding="utf-8")
    assert "REPORTE TÉCNICO — SISTEMA BIPV" not in rep and "_tx['titulo']" in rep
    assert "Equivale a sacar un vehículo" not in rep and "texto_vehiculos(" in rep
    co2 = (_RAIZ / "pages" / "12_🌿_Impacto_CO2.py").read_text(encoding="utf-8")
    assert "/20_000" not in co2 and "KM_ANUALES_AUTO" in co2


def test_manual_del_asistente_seccion_120():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 120.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("Diagrama Unifilar", "Granja FV", "% manual", "GRANJA SOLAR", "autos", "20.000 km"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    assert "PVsyst" not in s and "pendiente" not in s
