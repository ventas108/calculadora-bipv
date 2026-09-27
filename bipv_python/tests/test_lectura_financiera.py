"""Umbral de tarifa, decimales del flujo y lectura del LCOE (27-sep-2026)."""
from pathlib import Path

import pytest

from calculos.financiero import calcular_beneficios_ley_1715, comparativo_ley_1715
from calculos.lectura_financiera import umbral_vpn_cero, valor_nivelado_energia

PAGINA = Path(__file__).resolve().parents[1] / "pages" / "7_💰_Financiero.py"


def test_umbral_mayor_que_600_no_se_queda_en_600():
    # Caso real: 650 COP/kWh → VPN −662; el umbral real era ~677, no 600.
    umbral = umbral_vpn_cero(lambda t: 24.6 * (t - 677.0))
    assert umbral == pytest.approx(677.0, abs=0.5)


def test_umbral_menor_que_600_y_casos_limite():
    assert umbral_vpn_cero(lambda t: t - 300.0) == pytest.approx(300.0, abs=0.5)
    assert umbral_vpn_cero(lambda t: t - 10.0) == 50.0          # ya positivo en el mínimo
    assert umbral_vpn_cero(lambda t: -1.0) is None              # nunca llega a VPN 0
    assert umbral_vpn_cero(lambda t: None) is None


def _caso_cliente():
    ben = calcular_beneficios_ley_1715(capex_usd=23730, fraccion_equipo=0.8,
                                       tasa_renta=0.35, tipo_cambio=3307, tasa_descuento=0.10)
    return comparativo_ley_1715(capex_usd=23730, e_ac_kWh_anual=6155, tarifa_cop_kWh=1200,
                                tipo_cambio=3307, tasa_descuento=0.10, tasa_escalacion=5.0,
                                tasa_degradacion=0.4, opex_pct=0.7, n_anos=25,
                                beneficios_1715=ben, frac_exportada=826 / 6155,
                                tarifa_excedentes_cop_kWh=800)


def test_lcoe_menor_que_valor_nivelado_si_y_solo_si_vpn_sin_ley_positivo():
    comp = _caso_cliente()
    m = comp["sin"]["metricas"]
    vne = valor_nivelado_energia(comp["sin"]["flujos"], 0.10, 3307)
    # El LCOE supera la tarifa del año 1 y aun así el proyecto se paga.
    assert m["lcoe_cop_kWh"] > 1200
    assert (vne["cop_kWh"] > m["lcoe_cop_kWh"]) == (m["vpn_usd"] > 0)
    assert vne["cop_kWh"] > 1200


def test_valor_nivelado_sin_produccion():
    assert valor_nivelado_energia([], 0.1, 3307) is None


def test_pagina_usa_umbral_valor_nivelado_y_formato_sin_decimales():
    src = PAGINA.read_text(encoding="utf-8")
    assert "_tlo, _thi = 50.0, 600.0" not in src
    assert "umbral_vpn_cero(" in src
    assert "valor_nivelado_energia(" in src
    assert '"Autoconsumo (kWh)":     "{:,.0f}"' in src
    assert '"Exportación (kWh)":     "{:,.0f}"' in src
    # El resumen ya no compara el LCOE con la tarifa del año 1.
    assert "'<' if m_con['lcoe_cop_kWh'] < tarifa_cop else '>'" not in src
