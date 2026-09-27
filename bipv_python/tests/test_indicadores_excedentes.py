"""Indicadores de 💰 Financiero con la tarifa de excedentes (27-sep-2026).

Caso real (cliente Bogotá): 6.155 kWh/año, 5.329 de autoconsumo, 826 de
excedentes, tarifa 1.200 COP/kWh y excedentes a 800 COP/kWh, sin batería.
"""
from pathlib import Path

import pytest

from calculos.financiero import calcular_beneficios_ley_1715, comparativo_ley_1715
from calculos.indicadores_excedentes import (
    ahorro_anual_cop,
    escenario_sin_bateria,
    hay_bateria,
)

PAGINA = Path(__file__).resolve().parents[1] / "pages" / "7_💰_Financiero.py"

METRICAS_SIN_BATERIA = {
    "E_solar_anual_kWh": 6155.0,
    "E_autoconsumo_anual_kWh": 5329.0,
    "E_exportacion_anual_kWh": 826.0,
    "E_bateria_total_kWh": 0.0,
}


def test_ahorro_anio_1_valora_excedentes_a_su_tarifa():
    r = ahorro_anual_cop(6155.0, 826.0 / 6155.0, 1200.0, 800.0)
    assert r["autoconsumo_kWh"] == pytest.approx(5329.0)
    assert r["exportada_kWh"] == pytest.approx(826.0)
    assert r["total_cop"] == pytest.approx(5329 * 1200 + 826 * 800)      # 7,05 M, no 7,39 M
    assert r["total_cop"] < 6155 * 1200


def test_ahorro_sin_excedentes_es_el_de_antes():
    r = ahorro_anual_cop(6155.0, 0.0, 1200.0, 800.0)
    assert r["total_cop"] == pytest.approx(6155 * 1200)
    assert r["ingreso_excedentes_cop"] == 0


def test_ahorro_tolera_datos_raros():
    assert ahorro_anual_cop(None, float("nan"), 1200, 800)["total_cop"] == 0
    assert ahorro_anual_cop(100, 2.0, 1200, 800)["total_cop"] == pytest.approx(80000)


def test_sin_bateria_no_hay_comparacion():
    assert not hay_bateria(0.0, METRICAS_SIN_BATERIA)
    assert hay_bateria(3000.0, METRICAS_SIN_BATERIA)
    assert hay_bateria(0.0, {**METRICAS_SIN_BATERIA, "E_bateria_total_kWh": 300.0})
    assert not hay_bateria(0.0, None)


def test_escenario_sin_bateria_sin_bateria_es_el_mismo_sistema():
    esc = escenario_sin_bateria(METRICAS_SIN_BATERIA)
    assert esc["energia_kWh"] == pytest.approx(6155.0)
    assert esc["exportada_kWh"] == pytest.approx(826.0)
    assert esc["frac_exportada"] == pytest.approx(826.0 / 6155.0)


def test_escenario_sin_bateria_devuelve_la_descarga_a_excedentes():
    # Con batería: 300 kWh descargados salen del excedente (más pérdidas).
    con_bateria = {
        "E_solar_anual_kWh": 6155.0,
        "E_autoconsumo_anual_kWh": 5629.0,
        "E_exportacion_anual_kWh": 500.0,
        "E_bateria_total_kWh": 300.0,
    }
    esc = escenario_sin_bateria(con_bateria)
    assert esc["autoconsumo_kWh"] == pytest.approx(5329.0)
    assert esc["exportada_kWh"] == pytest.approx(826.0)
    assert escenario_sin_bateria({}) is None


def test_sin_bateria_la_tir_de_referencia_es_la_misma_que_la_del_analisis():
    # Antes: «sin batería» 18,0 % contra «con batería» 17,2 % sin batería alguna.
    esc = escenario_sin_bateria(METRICAS_SIN_BATERIA)
    ben = calcular_beneficios_ley_1715(capex_usd=23730, fraccion_equipo=0.7,
                                       tasa_renta=0.35, tipo_cambio=3307, tasa_descuento=0.10)
    comun = dict(capex_usd=23730, tarifa_cop_kWh=1200, tipo_cambio=3307,
                 tasa_descuento=0.10, tasa_escalacion=0.03, tasa_degradacion=0.005,
                 opex_pct=0.01, n_anos=25, beneficios_1715=ben,
                 tarifa_excedentes_cop_kWh=800)
    analisis = comparativo_ley_1715(e_ac_kWh_anual=5329 + 826,
                                    frac_exportada=826 / 6155, **comun)
    referencia = comparativo_ley_1715(e_ac_kWh_anual=esc["energia_kWh"],
                                      frac_exportada=esc["frac_exportada"], **comun)
    assert referencia["con"]["metricas"]["tir_pct"] == pytest.approx(
        analisis["con"]["metricas"]["tir_pct"])


def test_pagina_usa_los_indicadores_con_excedentes():
    src = PAGINA.read_text(encoding="utf-8")
    assert "ahorro_anual_cop(" in src
    assert 'f"${e_ac * (tarifa_cop/1e6):.2f} M COP/año"' not in src
    assert "escenario_sin_bateria(" in src
    assert "hay_bateria(" in src
    # El escenario sin batería valora sus excedentes a la tarifa de excedentes.
    bloque = src[src.index("_comp_sinbat = _comp1715("):]
    bloque = bloque[:bloque.index(")\n")]
    assert "frac_exportada" in bloque and "tarifa_excedentes_cop_kWh" in bloque
    assert "_e_autoconsumo - e_ac" not in src
