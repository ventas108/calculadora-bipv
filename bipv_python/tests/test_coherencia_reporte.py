# -*- coding: utf-8 -*-
"""Spec 07-informes/coherencia-reporte (2-oct-2026).

Caso real: Granja Solar Apartadó 3 (403,2 kWp). El informe decía
«3 × Growatt MAX 100KTL3 LV · DC/AC 1,34» y, en la línea siguiente, «Reparto
7 + 7 + 7 + 7» (4 inversores); no traía Producción; y el CO₂ era 6,3 t/año
(los 50.000 kWh de ejemplo de 🌿 Impacto CO₂ sin Producción) cuando la granja
da ~604 MWh (~76 t). Además, la verificación PVGIS–PVWatts comparaba la POA
bifacial total con la frontal de PVWatts (−7,1 % en vez de ~+0,4 %).
"""
from pathlib import Path

import pytest

from calculos.coherencia_reporte import energia_vigente, revisar_coherencia_reporte

_RAIZ = Path(__file__).resolve().parents[1]

APARTADO_OK = {
    "E_ac_anual_kWh": 604_195.0,
    "produccion_n_inversores": 4,
    "reparto_strings_inversores": [7, 7, 7, 7],
    "N_inversores_proyecto": 4,
    "co2_anual_t": 604_195.0 * 0.126 / 1000.0,
    "co2_factor_kg_kwh": 0.126,
}


def _titulos(problemas, nivel="error"):
    return [p["titulo"] for p in problemas if p["nivel"] == nivel]


def test_estado_coherente_sin_errores():
    assert _titulos(revisar_coherencia_reporte(APARTADO_OK)) == []


def test_inversores_de_produccion_distintos_del_reparto():
    estado = {**APARTADO_OK, "produccion_n_inversores": 3}
    probs = revisar_coherencia_reporte(estado)
    err = [p for p in probs if p["nivel"] == "error" and "inversores" in p["titulo"].lower()]
    assert err and "3" in err[0]["detalle"] and "4" in err[0]["detalle"]
    assert "Producción" in err[0]["accion"]


def test_inversores_fijados_y_no_simulados():
    estado = {**APARTADO_OK, "produccion_n_inversores": 3, "reparto_strings_inversores": [10, 9, 9]}
    assert any("inversores" in t.lower() for t in _titulos(revisar_coherencia_reporte(estado)))


def test_co2_con_la_energia_de_ejemplo():
    estado = {**APARTADO_OK, "co2_anual_t": 6.3}                     # 50.000 kWh × 0,126
    err = [p for p in revisar_coherencia_reporte(estado) if p["nivel"] == "error" and "CO₂" in p["titulo"]]
    assert err and "50,000" in err[0]["detalle"] and "604,195" in err[0]["detalle"]
    assert "Impacto CO₂" in err[0]["accion"]


def test_co2_manual_marcado_es_error_aunque_coincida():
    estado = {**APARTADO_OK, "co2_e_ac_manual": True}
    assert any("CO₂" in t for t in _titulos(revisar_coherencia_reporte(estado)))


def test_financiero_con_otra_energia():
    estado = {**APARTADO_OK, "fin_e_ac_kWh": 50_000.0}
    assert any("Financiero" in t for t in _titulos(revisar_coherencia_reporte(estado)))
    assert not any("Financiero" in t for t in _titulos(
        revisar_coherencia_reporte({**APARTADO_OK, "fin_e_ac_kWh": 604_195.0})))


def test_sin_produccion():
    estado = {k: v for k, v in APARTADO_OK.items() if k != "E_ac_anual_kWh"}
    assert any("Producción" in t for t in _titulos(revisar_coherencia_reporte(estado)))


def test_energia_vigente_misma_prioridad_que_co2_y_financiero():
    assert energia_vigente({"E_ac_anual_kWh": 10.0}) == 10.0
    assert energia_vigente({"E_ac_anual_kWh": 10.0, "bypass_ok": True, "E_ac_anual_kWh_bypass": 9.0}) == 9.0
    assert energia_vigente({"E_ac_anual_kWh": 10.0, "multisup_activo": True,
                            "E_ac_anual_kWh_multisup": 8.0}) == 8.0


def test_paginas_conectadas():
    rep = (_RAIZ / "pages" / "10_📄_Reporte_PDF.py").read_text(encoding="utf-8")
    assert "revisar_coherencia_reporte(" in rep and 'key="rep_generar_incoherente"' in rep
    assert "fachada BIPV desplaza" not in rep
    co2 = (_RAIZ / "pages" / "12_🌿_Impacto_CO2.py").read_text(encoding="utf-8")
    assert 'st.session_state["co2_e_ac_kWh"]' in co2 and 'st.session_state["co2_e_ac_manual"]' in co2
    fin = (_RAIZ / "pages" / "7_💰_Financiero.py").read_text(encoding="utf-8")
    assert 'st.session_state["fin_e_ac_kWh"]' in fin
    rs = (_RAIZ / "pages" / "2_☀️_Recurso_Solar.py").read_text(encoding="utf-8")
    assert "poa_pvgis_frontal_mensual" in rs


def test_pvwatts_compara_la_cara_frontal():
    from calculos.pvwatts_crosscheck import comparar_poa_pvgis_vs_pvwatts
    frontal = [141.7] * 12                                            # 1.700 kWh/m² frontal
    pvwatts = [142.25] * 12                                           # 1.707
    cmp = comparar_poa_pvgis_vs_pvwatts(frontal, pvwatts)
    assert cmp["diferencia_pct_anual"] == pytest.approx(0.4, abs=0.1)


def test_manual_del_asistente_seccion_118():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 118.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("Apartadó", "inversores", "Impacto CO₂", "PVWatts", "Generar de todas formas", "50.000"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    assert "PVsyst" not in s and "pendiente" not in s
