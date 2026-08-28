# -*- coding: utf-8 -*-
"""
Tests de calculos/financiero.py -- cruce contra el entregable real ya
publicado del proyecto Agrivoltaico Urabá (auditoría 27-ago-2026).

`entregables/generar_informe_final_evaluador_uraba.py` reporta cifras
oficiales (TIR, VPN, Payback, LCOE) para 2 escenarios. Estos tests
reproducen esas cifras INDEPENDIENTEMENTE, ejecutando el módulo financiero
real con los insumos declarados en el propio informe (CAPEX ≈USD 177.200,
tarifa 950 COP/kWh EPM, TRM 3.118,24, degradación 0,4%/año, 25 años,
OPEX 10 USD/kWp/año, sin beneficios Ley 1715) -- si algún día
calcular_flujo_caja()/calcular_metricas() cambian de forma que dejen de
reproducir el informe ya entregado a un evaluador externo, este test debe
fallar para que se note.

E_ac de cada escenario derivado de "Producción año 25 (con degradación)"
del propio informe (304.100 kWh bifacial / 281.600 kWh monofacial),
revertiendo la degradación geométrica -- no son valores inventados.
"""
import pytest

from calculos.financiero import calcular_flujo_caja, calcular_metricas

CAPEX_USD = 177_200.0
TARIFA_COP_KWH = 950.0
TRM = 3_118.24
DEG_PCT = 0.4
N_ANOS = 25
P_DC_KW = 220.32
OPEX_PCT_CAPEX = 10.0 * P_DC_KW / CAPEX_USD * 100  # 10 USD/kWp/año, mismo supuesto de la ficha


def _metricas_uraba(e_ac_anual: float) -> dict:
    flujos = calcular_flujo_caja(
        capex_usd=CAPEX_USD, beneficios_1715_usd=0.0, e_ac_kWh_anual=e_ac_anual,
        tarifa_cop_kWh=TARIFA_COP_KWH, tipo_cambio=TRM, tasa_escalacion_tarifa=0.0,
        tasa_degradacion_pct=DEG_PCT, opex_pct_capex=OPEX_PCT_CAPEX, n_anos=N_ANOS,
    )
    return calcular_metricas(flujos, tasa_descuento=0.10, capex_usd=CAPEX_USD,
                              e_ac_kWh_anual=e_ac_anual, tipo_cambio=TRM)


def test_caso_base_bifacial_reproduce_el_informe_entregado():
    # E_ac año 1 = 304.100 / (1-0.004)^24 -- revierte la degradación del
    # "Producción año 25" reportado en el informe.
    e_ac_1 = 304_100 / (1 - DEG_PCT / 100) ** 24
    met = _metricas_uraba(e_ac_1)

    # Reportado en el informe: TIR 55,9%, VPN USD 701.820, Payback 1,8,
    # LCOE 0,0668 USD/kWh (208 COP/kWh).
    assert met["tir_pct"] == pytest.approx(55.9, abs=0.1)
    assert met["vpn_usd"] == pytest.approx(701_820, rel=0.001)
    assert met["payback_simple"] == pytest.approx(1.8, abs=0.05)
    assert met["lcoe_cop_kWh"] == pytest.approx(208.0, abs=1.0)


def test_piso_conservador_monofacial_reproduce_el_informe_entregado():
    e_ac_1 = 281_600 / (1 - DEG_PCT / 100) ** 24
    met = _metricas_uraba(e_ac_1)

    # Reportado en el informe: TIR 51,7%, VPN USD 635.213, Payback 1,9,
    # LCOE 0,0722 USD/kWh (225 COP/kWh).
    assert met["tir_pct"] == pytest.approx(51.7, abs=0.1)
    assert met["vpn_usd"] == pytest.approx(635_213, rel=0.001)
    assert met["payback_simple"] == pytest.approx(1.9, abs=0.05)
    assert met["lcoe_cop_kWh"] == pytest.approx(225.0, abs=1.0)


def test_caso_base_usa_e_ac_previo_al_ajuste_fino_de_motor_optico():
    # Cabo suelto documentado (no corregido en esta auditoría, decisión
    # pendiente del usuario): el informe usa E_ac=334.805 kWh/año (el
    # supuesto "+8% bifacial fijo" sin Motor Óptico/IAM), no los 336.662
    # kWh/año ya validados como más precisos tras aplicar IAM con el
    # motor real de la app (ver DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md). La
    # diferencia es pequeña (~0,5%, TIR 55,9%→56,2%) pero es real y sigue
    # sin decidirse si se regeneran los entregables oficiales.
    e_ac_informe = 304_100 / (1 - DEG_PCT / 100) ** 24
    assert e_ac_informe == pytest.approx(334_805, abs=50)

    e_ac_preciso = 336_662.0
    met_informe  = _metricas_uraba(e_ac_informe)
    met_preciso  = _metricas_uraba(e_ac_preciso)
    assert met_preciso["tir_pct"] > met_informe["tir_pct"]
    assert met_preciso["tir_pct"] - met_informe["tir_pct"] < 1.0  # diferencia real, pero no material
