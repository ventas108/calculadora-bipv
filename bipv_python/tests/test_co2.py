# -*- coding: utf-8 -*-
"""
Regresión — extracción de calculos/co2.py (auditoría Fase 1, cuello de
botella #4: 12_🌿_Impacto_CO2.py no tenía módulo propio, todo el cálculo
(factor marginal/promedio, equivalencias, bonos, NDC, cumplimiento real vs
proyectado) vivía inline en la página).

Cada test recalcula la fórmula de forma independiente (no copiando el
código del módulo) y la compara contra calculos.co2 — igual que en
test_geometria_solar_unificada.py. Los valores de referencia (factor
promedio 0.126, marginal 0.300, etc.) están tomados literalmente del
código fuente de la página antes del refactor.
"""
import os

import numpy as np
import pytest

from calculos import co2

_PAGINA_CO2 = os.path.join(os.path.dirname(__file__), "..", "pages", "12_🌿_Impacto_CO2.py")

FACTOR_PROMEDIO = 0.126   # UPME Resolución 520/2019 — mismo valor que
                            # datos.ciudades_colombia.FACTOR_CO2_COLOMBIA_KG_KWH


def test_produccion_anual_con_degradacion():
    e_ac, deg, n = 50_000.0, 0.5, 25
    anos, e_ac_anual = co2.produccion_anual_con_degradacion(e_ac, deg, n)
    assert len(anos) == n
    assert e_ac_anual[0] == pytest.approx(e_ac)   # año 1 sin degradar
    esperado_ano_25 = e_ac * (1 - deg / 100) ** 24
    assert e_ac_anual[-1] == pytest.approx(esperado_ano_25)


@pytest.mark.parametrize("e_ac,factor_activo", [
    (50_000.0, FACTOR_PROMEDIO),
    (50_000.0, co2.FACTOR_MARGINAL_KG_KWH),
    (183_250.0, FACTOR_PROMEDIO),
])
def test_emisiones_evitadas_coincide_con_calculo_independiente(e_ac, factor_activo):
    deg, n = 0.5, 25
    anos, e_ac_anual = co2.produccion_anual_con_degradacion(e_ac, deg, n)

    esperado_anual_kg = e_ac * factor_activo
    esperado_total_t = sum(e_ac_anual * factor_activo / 1000)
    esperado_total_prom_t = sum(e_ac_anual * FACTOR_PROMEDIO / 1000)
    esperado_total_marg_t = sum(e_ac_anual * co2.FACTOR_MARGINAL_KG_KWH / 1000)

    r = co2.emisiones_evitadas(e_ac, e_ac_anual, factor_activo, FACTOR_PROMEDIO, co2.FACTOR_MARGINAL_KG_KWH)

    assert r["co2_anual_kg"] == pytest.approx(esperado_anual_kg)
    assert r["co2_anual_t"] == pytest.approx(esperado_anual_kg / 1000)
    assert r["co2_total_t"] == pytest.approx(esperado_total_t)
    assert r["co2_total_prom_t"] == pytest.approx(esperado_total_prom_t)
    assert r["co2_total_marg_t"] == pytest.approx(esperado_total_marg_t)
    assert r["intensidad_sistema"] == pytest.approx(factor_activo * 1000)


def test_valor_bonos_carbono():
    usd, cop = co2.valor_bonos_carbono(co2_total_t=1234.5, precio_bono_usd=12.0, tipo_cambio=4000.0)
    assert usd == pytest.approx(1234.5 * 12.0)
    assert cop == pytest.approx(1234.5 * 12.0 * 4000.0)


def test_equivalencias_impacto_coincide_con_calculo_independiente():
    co2_total_t, e_ac_total, n_anos = 1234.5, 4_500_000.0, 25
    r = co2.equivalencias_impacto(co2_total_t, e_ac_total, n_anos)
    assert r["arboles"] == pytest.approx(co2_total_t * 1000 / 22.0 / n_anos)
    assert r["hogares"] == pytest.approx(e_ac_total / 1_560.0)
    assert r["km_vehiculo"] == pytest.approx(co2_total_t * 1000 / 0.162 / 1000)
    assert r["vuelos_bogmde"] == pytest.approx(co2_total_t * 1000 / 89.0)
    assert r["barriles"] == pytest.approx(co2_total_t * 1000 / 431.7)
    assert r["cilindros_glp"] == pytest.approx(co2_total_t * 1000 / 55.6)


def test_contribucion_ndc_coincide_con_calculo_independiente():
    co2_total_t, co2_anual_t = 1234.5, 61.2
    pct_total, pct_sector, pct_nac = co2.contribucion_ndc(co2_total_t, co2_anual_t)
    assert pct_total == pytest.approx(co2_total_t / (169.0 * 1e6) * 100)
    assert pct_sector == pytest.approx(co2_total_t / (59.0 * 1e6) * 100)
    assert pct_nac == pytest.approx(co2_anual_t / (258.0 * 1e6) * 100)


def test_cumplimiento_sin_datos_reales_retorna_none():
    proy = [1000.0] * 12
    assert co2.cumplimiento_real_vs_proyectado([0.0] * 12, proy, FACTOR_PROMEDIO, 12_000.0) is None


def test_cumplimiento_real_vs_proyectado_tres_meses():
    factor = FACTOR_PROMEDIO
    e_ac = 12_000.0
    proy_mes = [1000.0] * 12
    kwh_real = [900.0, 950.0, 1100.0] + [0.0] * 9

    r = co2.cumplimiento_real_vs_proyectado(kwh_real, proy_mes, factor, e_ac)

    assert r["meses_con_dato"] == 3
    co2_real_esperado = sum(v * factor / 1000 for v in kwh_real[:3])
    co2_proy_esperado = sum(v * factor / 1000 for v in proy_mes[:3])
    assert r["co2_real_acum"] == pytest.approx(co2_real_esperado)
    assert r["co2_proy_acum"] == pytest.approx(co2_proy_esperado)
    assert r["cumpl_pct"] == pytest.approx(co2_real_esperado / co2_proy_esperado * 100)
    assert r["delta_co2"] == pytest.approx(co2_real_esperado - co2_proy_esperado)
    assert r["kwh_real_total"] == pytest.approx(sum(kwh_real))
    pr_esperado = sum(kwh_real) / (e_ac * 3 / 12) * 100
    assert r["pr_real_pct"] == pytest.approx(pr_esperado)


def test_cumplimiento_e_ac_cero_no_divide_por_cero():
    proy_mes = [1000.0] * 12
    kwh_real = [900.0] + [0.0] * 11
    r = co2.cumplimiento_real_vs_proyectado(kwh_real, proy_mes, FACTOR_PROMEDIO, 0.0)
    assert r["pr_real_pct"] == 0


def test_intensidad_ipcc_bipv_fachada_treinta():
    # Valor citado explícitamente en la UI (banner de la Sección 2) — si
    # alguien cambia el diccionario sin querer, este test debe fallar.
    assert co2.INTENSIDAD_IPCC["Solar BIPV fachada"] == 30


def test_pagina_no_reimplementa_constantes_co2():
    with open(_PAGINA_CO2, encoding="utf-8") as f:
        src = f.read()
    assert "from calculos import co2 as co2_calc" in src
    # Los valores duros ya no deben vivir como literales en la página —
    # solo como referencia a co2_calc.*
    assert "FACTOR_MARGINAL_KG_KWH  = 0.300" not in src
    assert "KG_CO2_ARBOL_ANUAL       = 22.0" not in src
    assert 'INTENSIDAD_IPCC = {\n    "Carbón' not in src
