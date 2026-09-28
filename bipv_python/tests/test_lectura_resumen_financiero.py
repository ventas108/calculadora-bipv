"""Tarjeta «Ahorro estimado», rótulo P90 y etiquetas de payback de 💰 Financiero.

Prueba del proyecto cliente (27-sep-2026, 5.943 kWh/año, 693 kWh exportados a
800 COP/kWh, consumo 5.738 kWh/año, tarifa 1.200 COP/kWh):

- «Ahorro estimado» decía 6,89 M COP/año (todo el consumo a 1.200) y «Ahorro
  energía año 1» 6,85 M (el reparto del flujo de caja, que usan TIR y VPN).
- La columna P90 decía «(−10%)» y el texto «−9,5 %» para el mismo factor.
- Las etiquetas «Payback P50» y «Payback sin 1715» se encimaban en la gráfica.
"""
from pathlib import Path

import pytest

from calculos.indicadores_excedentes import ahorro_anual_cop, tarifa_excedentes_vigente
from calculos.lectura_financiera import etiquetas_payback

FINANCIERO = Path(__file__).resolve().parents[1] / "pages" / "7_💰_Financiero.py"


def test_tarifa_excedentes_vigente_usa_la_guardada_solo_si_hay_exportacion():
    estado = {"tarifa_excedentes_cop_kWh": 800.0}
    assert tarifa_excedentes_vigente(estado, 1200.0, 0.117) == 800.0
    assert tarifa_excedentes_vigente(estado, 1200.0, 0.0) == 1200.0
    assert tarifa_excedentes_vigente({}, 1200.0, 0.117) == 1200.0          # sin guardar: la de compra
    assert tarifa_excedentes_vigente({"tarifa_excedentes_cop_kWh": "x"}, 1200.0, 0.1) == 1200.0


def test_ahorro_del_resumen_es_el_del_anio_1_caso_cliente():
    tarifa_exc = tarifa_excedentes_vigente({"tarifa_excedentes_cop_kWh": 800.0}, 1200.0, 693 / 5943)
    total = ahorro_anual_cop(5943, 693 / 5943, 1200.0, tarifa_exc)["total_cop"]
    assert total == pytest.approx(6.854e6, rel=1e-3)     # no 5.738 × 1.200 = 6,886 M


def test_pagina_resumen_usa_el_mismo_ahorro_y_p90_con_un_decimal():
    src = FINANCIERO.read_text(encoding="utf-8")
    assert "min(_prod_mes_fin, _consumo_mes_fin) * _tarifa_prev_fin" not in src
    assert "tarifa_excedentes_vigente(" in src
    assert "factor_p90:.0f" not in src
    assert "etiquetas_payback(" in src


def test_etiquetas_payback_no_se_enciman():
    etq = etiquetas_payback([("Payback sin 1715: 10.0 a", 10.0, "#EF5350"),
                             ("Payback P50: 6.7 a", 6.7, "#2E7D32"),
                             ("Payback P90: 7.4 a", 7.4, "#F57F17")])
    assert [e["x"] for e in etq] == [6.7, 7.4, 10.0]          # ordenadas por año
    ys = [e["y"] for e in etq]
    assert len(set(ys)) == 3 and ys == sorted(ys, reverse=True)
    assert min(a - b for a, b in zip(ys, ys[1:])) >= 0.07     # una fila de texto de separación
    assert all(e["color"] and e["texto"] for e in etq)


def test_etiquetas_payback_omite_los_sin_payback():
    assert etiquetas_payback([("P50", None, "#000"), ("P90", 0, "#111")]) == []
