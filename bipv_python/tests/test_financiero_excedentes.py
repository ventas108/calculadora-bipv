# -*- coding: utf-8 -*-
"""Validación de la tarifa diferenciada de excedentes exportados (2026-08-21).

Hallazgo del usuario: el motor financiero (calculos/financiero.py) valoraba
TODA la energía a una sola tarifa, sin distinguir energía autoconsumida
(ahorro a tarifa de compra) de excedente exportado/vendido a la red
(Res. CREG 174/2021, típicamente a una tarifa menor). Peor aún: cuando había
un balance de baterías activo, el excedente exportado quedaba EXCLUIDO por
completo del cálculo (e_financiero = solo autoconsumo), sin generar ningún
ingreso -- ver pages/7_💰_Financiero.py.

calcular_flujo_caja()/comparativo_ley_1715() ahora aceptan frac_exportada y
tarifa_excedentes_cop_kWh, con defaults (0.0 / None→misma tarifa) que
reproducen EXACTAMENTE el comportamiento anterior -- estos tests verifican
tanto la compatibilidad hacia atrás como la corrección real.
"""
import pytest

from calculos.financiero import calcular_flujo_caja, calcular_metricas, comparativo_ley_1715


def _flujo_base(**overrides):
    params = dict(
        capex_usd=100_000.0, beneficios_1715_usd=0.0, e_ac_kWh_anual=150_000.0,
        tarifa_cop_kWh=800.0, tipo_cambio=4000.0, tasa_escalacion_tarifa=5.0,
        tasa_degradacion_pct=0.5, opex_pct_capex=1.5, n_anos=5,
    )
    params.update(overrides)
    return calcular_flujo_caja(**params)


def test_default_reproduce_exactamente_el_comportamiento_anterior():
    # frac_exportada=0.0 (default) -- toda la energía a tarifa_cop_kWh, igual
    # que antes de este cambio.
    f = _flujo_base()
    assert f[1]["autoconsumo_kWh"] == f[1]["produccion_kWh"]
    assert f[1]["exportacion_kWh"] == 0.0
    esperado_usd = 150_000.0 * 800.0 / 4000.0
    assert f[1]["ingreso_energia_usd"] == pytest.approx(esperado_usd, abs=1.0)


def test_tarifa_excedentes_none_usa_la_misma_tarifa_de_compra():
    # Aunque se declare frac_exportada > 0, si no se pasa una tarifa de
    # excedentes explícita, el ingreso debe ser IDÉNTICO al caso sin split
    # (misma tarifa para todo) -- backward compatible por diseño.
    f_sin_split = _flujo_base()
    f_con_frac_sin_tarifa = _flujo_base(frac_exportada=0.4)
    assert f_con_frac_sin_tarifa[1]["ingreso_energia_usd"] == pytest.approx(
        f_sin_split[1]["ingreso_energia_usd"], abs=1.0
    )


def test_split_autoconsumo_exportacion_correcto():
    f = _flujo_base(frac_exportada=0.3, tarifa_excedentes_cop_kWh=400.0)
    fila = f[1]
    assert fila["autoconsumo_kWh"] == pytest.approx(150_000.0 * 0.7, abs=1.0)
    assert fila["exportacion_kWh"] == pytest.approx(150_000.0 * 0.3, abs=1.0)
    ingreso_esperado = (150_000.0 * 0.7 * 800.0 + 150_000.0 * 0.3 * 400.0) / 4000.0
    assert fila["ingreso_energia_usd"] == pytest.approx(ingreso_esperado, abs=1.0)


def test_tarifa_excedentes_menor_reduce_el_ingreso_frente_a_tarifa_unica():
    f_una_tarifa = _flujo_base()
    f_excedentes = _flujo_base(frac_exportada=0.3, tarifa_excedentes_cop_kWh=400.0)
    assert f_excedentes[1]["ingreso_energia_usd"] < f_una_tarifa[1]["ingreso_energia_usd"]


def test_frac_exportada_se_acota_a_0_1():
    f_neg = _flujo_base(frac_exportada=-0.5)
    assert f_neg[1]["exportacion_kWh"] == 0.0
    f_exceso = _flujo_base(frac_exportada=1.5)
    assert f_exceso[1]["autoconsumo_kWh"] == 0.0
    assert f_exceso[1]["exportacion_kWh"] == f_exceso[1]["produccion_kWh"]


def test_produccion_total_no_cambia_por_el_split():
    # El split reparte el ingreso, pero la producción física total (para
    # LCOE/degradación) debe seguir siendo la misma independientemente del
    # split de autoconsumo/exportación.
    f_sin = _flujo_base()
    f_con = _flujo_base(frac_exportada=0.6, tarifa_excedentes_cop_kWh=300.0)
    assert f_con[1]["produccion_kWh"] == f_sin[1]["produccion_kWh"]
    assert f_con[1]["autoconsumo_kWh"] + f_con[1]["exportacion_kWh"] == pytest.approx(
        f_con[1]["produccion_kWh"], abs=1.0
    )


def test_metricas_siguen_funcionando_con_las_columnas_nuevas():
    # calcular_metricas() solo lee flujo_usd/flujo_acum_usd -- las columnas
    # nuevas (autoconsumo_kWh/exportacion_kWh) no deben romper nada.
    f = _flujo_base(frac_exportada=0.3, tarifa_excedentes_cop_kWh=400.0)
    met = calcular_metricas(f, 0.10, 100_000.0, 150_000.0, 4000.0)
    assert met["vpn_usd"] is not None
    assert "lcoe_usd_kWh" in met


# ── comparativo_ley_1715() -- thread-through de los parámetros nuevos ───────

def _ben_cero():
    return {"total_usd": 0.0, "ahorro_renta_usd": 0.0, "ahorro_iva_usd": 0.0,
            "ahorro_dep_vpn_usd": 0.0, "capex_neto_usd": 100_000.0, "pct_capex": 0.0}


def test_comparativo_ley_1715_aplica_el_split_en_ambos_escenarios():
    comp = comparativo_ley_1715(
        capex_usd=100_000.0, e_ac_kWh_anual=150_000.0, tarifa_cop_kWh=800.0,
        tipo_cambio=4000.0, tasa_descuento=0.10, tasa_escalacion=5.0,
        tasa_degradacion=0.5, opex_pct=1.5, n_anos=5, beneficios_1715=_ben_cero(),
        frac_exportada=0.3, tarifa_excedentes_cop_kWh=400.0,
    )
    for escenario in ("sin", "con"):
        fila = comp[escenario]["flujos"][1]
        assert fila["exportacion_kWh"] == pytest.approx(150_000.0 * 0.3, abs=1.0)


def test_comparativo_ley_1715_default_sin_cambios():
    comp_default = comparativo_ley_1715(
        capex_usd=100_000.0, e_ac_kWh_anual=150_000.0, tarifa_cop_kWh=800.0,
        tipo_cambio=4000.0, tasa_descuento=0.10, tasa_escalacion=5.0,
        tasa_degradacion=0.5, opex_pct=1.5, n_anos=5, beneficios_1715=_ben_cero(),
    )
    assert comp_default["con"]["flujos"][1]["exportacion_kWh"] == 0.0
