# -*- coding: utf-8 -*-
"""
Validación de la Fase 2 — run_bipv_simulation() / run_financial_simulation()
como función maestra invocable (blueprint de extracción, Paso 1 → Fase 2).

No golpea PVGIS: se construye un TMY sintético offline con el modelo
clear-sky Ineichen de pvlib (mismas columnas y contrato de índice que
calculos.solar.obtener_tmy_pvgis — 8760 h, año 2001 no bisiesto, UTC) para
que el test sea determinista y no dependa de un servicio externo. Esto NO
reemplaza una validación manual contra la app real con datos PVGIS —
sirve para probar que el pipeline encadena correctamente los módulos de
calculos/ con los mismos contratos que ya usan las páginas Streamlit.
"""
import dataclasses

import numpy as np
import pandas as pd
import pvlib
import pytest

from datos.tecnologias_bipv import ASP_ST1_T40

from simulation.schemas import BIPVConfiguration, FinancialConfiguration
from simulation.bipv_simulator import run_bipv_simulation
from simulation.financial_simulator import run_financial_simulation

# Bogotá — mismas coordenadas que test_geometria_solar_unificada.py
LAT, LON, ALT_M = 4.7110, -74.0721, 2620.0


def _tmy_sintetico_offline(lat, lon, alt_m):
    """TMY offline determinista (clear-sky Ineichen) — mismo contrato de
    columnas/índice que calculos.solar.obtener_tmy_pvgis."""
    idx = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    loc = pvlib.location.Location(latitude=lat, longitude=lon, altitude=alt_m, tz="UTC")
    cs = loc.get_clearsky(idx, model="ineichen")

    dia_del_anio = idx.dayofyear.values
    hora_del_dia = idx.hour.values
    # Variación diurna/anual simple y físicamente razonable — no pretende
    # ser un TMY real, solo dar T2m no degenerada para el modelo térmico.
    t2m = (
        18.0
        + 4.0 * np.sin(2 * np.pi * (hora_del_dia - 9) / 24.0)
        + 2.0 * np.sin(2 * np.pi * dia_del_anio / 365.0)
    )

    return pd.DataFrame({
        "G_h":   cs["ghi"].values,
        "Gb_n":  cs["dni"].values,
        "Gd_h":  cs["dhi"].values,
        "T2m":   t2m,
        "WS10m": 2.0,
        "SP":    101_325.0 * (1 - 2.25577e-5 * alt_m) ** 5.25588,   # ISA aprox.
    }, index=idx)


@pytest.fixture(scope="module")
def tmy_bogota():
    return _tmy_sintetico_offline(LAT, LON, ALT_M)


def _config_base(puntos_horizonte=()):
    return BIPVConfiguration(
        lat=LAT, lon=LON, alt_m=ALT_M,
        tilt=90.0, azimuth=180.0,   # fachada vertical orientada al sur
        area_m2=50.0,
        puntos_horizonte=list(puntos_horizonte),
        panel=ASP_ST1_T40,
        N_serie=8, N_strings_tracker=4, N_mppt=1,
        eta_inversor=0.97,
        k_bipv=1.3,
    )


def test_run_bipv_simulation_estructura_y_coherencia(tmy_bogota):
    config = _config_base()
    r = run_bipv_simulation(config, tmy=tmy_bogota)

    # ── Dimensionamiento coherente con la config ──────────────────────
    assert r.dim["N_paneles"] == config.N_serie * config.N_strings_tracker * config.N_mppt
    assert r.dim["area_ocupada_m2"] == pytest.approx(
        r.dim["N_paneles"] * config.panel["area_m2"], rel=1e-6
    )

    # ── Cascada de pérdidas: cada etapa reduce o iguala, nunca aumenta ──
    energias = [e["energia"] for e in r.cascada]
    assert all(a >= b - 1e-9 for a, b in zip(energias, energias[1:]))
    assert r.factor_pr_mismatch == pytest.approx(
        energias[-1] / energias[0], rel=1e-3
    )

    # ── Producción físicamente plausible (clear-sky, sin nubosidad real) ─
    assert r.E_ac_anual_kWh > 0
    assert 0.0 < r.PR <= 1.15   # clear-sky sube el PR vs un TMY real nublado
    assert r.produccion["E_dc_anual_kWh"] >= r.produccion["E_ac_anual_kWh"]

    # ── El resultado expone lo que promete el contrato (SimulationResult) ─
    assert r.P_dc_stc_kW == pytest.approx(r.dim["P_dc_stc_kW"])


def test_multi_inversor_escala_paneles_y_potencia_sin_cambiar_razones(tmy_bogota):
    # Hallazgo real (2026-08-21): un proyecto de Granja FV con 9 inversores
    # -- 80 paneles/inversor, 511.2 kWp totales (9 x 56.80 kWp/inversor) --
    # mostraba solo 1/9 de la energía real porque BIPVConfiguration no tenía
    # forma de expresar "N inversores idénticos". N_inversores=1 (default)
    # debe reproducir EXACTAMENTE el comportamiento de antes de este fix.
    config_1 = dataclasses.replace(
        _config_base(), tilt=20.0, area_m2=2100.0,
        N_serie=8, N_strings_tracker=10,   # 80 paneles/inversor
    )
    assert config_1.N_inversores == 1   # default explícito del contrato

    r1 = run_bipv_simulation(config_1, tmy=tmy_bogota)
    assert r1.dim["N_paneles"] == 80

    config_9 = dataclasses.replace(config_1, N_inversores=9)
    r9 = run_bipv_simulation(config_9, tmy=tmy_bogota)

    assert r9.dim["N_paneles"] == 720                       # 80 * 9, como el caso real
    assert r9.dim["P_dc_stc_kW"] == pytest.approx(r1.dim["P_dc_stc_kW"] * 9)
    assert r9.dim["area_ocupada_m2"] == pytest.approx(r1.dim["area_ocupada_m2"] * 9)
    # cobertura_pct de r1 ya viene redondeada a 1 decimal (dimensionar_sistema) --
    # multiplicarla x9 amplifica ese redondeo (~2% relativo en un valor chico como
    # 2.7). r9.dim["cobertura_pct"] se calcula del área EXACTA x9, no de la
    # versión ya redondeada -- es el valor más preciso, no un bug. Tolerancia
    # laxa a propósito, coherente con ese redondeo de 1 decimal previo.
    assert r9.dim["cobertura_pct"] == pytest.approx(r1.dim["cobertura_pct"] * 9, rel=0.02)

    # Energía absoluta escala x9 (tolerancia laxa: E_ac_anual_kWh se
    # redondea a 0 decimales en calculos/produccion.py -- comparar los
    # totales redondeados, no el redondeado-de-1-unidad x9).
    assert r9.E_ac_anual_kWh == pytest.approx(r1.E_ac_anual_kWh * 9, rel=1e-3)

    # Las razones (PR, Y_f, Y_a, CF) NO cambian -- normalizadas por P_dc_stc_kW,
    # el factor de escala se cancela en numerador y denominador.
    assert r9.PR == pytest.approx(r1.PR, abs=1e-9)
    assert r9.produccion["Y_f"] == pytest.approx(r1.produccion["Y_f"], rel=1e-6)
    assert r9.produccion["CF_pct"] == pytest.approx(r1.produccion["CF_pct"], rel=1e-6)


def test_multi_inversor_con_n_inversores_1_es_identico_al_comportamiento_previo():
    # N_inversores=1 (default) no debe alterar dim en absoluto -- ni el
    # dict debe ganar la clave "N_inversores" que solo se agrega cuando
    # != 1 (para no romper nada que ya lea dim.keys() literalmente).
    from calculos import dimensionamiento
    config = _config_base()
    dim_directo = dimensionamiento.dimensionar_sistema(
        config.panel, config.area_m2, config.N_serie,
        config.N_strings_tracker, config.N_mppt,
    )
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    r = run_bipv_simulation(config, tmy=tmy)
    assert r.dim == dim_directo
    assert "N_inversores" not in dim_directo


def test_sombreado_horizonte_reduce_produccion_nunca_la_aumenta(tmy_bogota):
    sin_sombra = run_bipv_simulation(_config_base(puntos_horizonte=[]), tmy=tmy_bogota)
    assert sin_sombra.sombreado["factor_sombra_anual"] == 0.0

    # Obstáculo alto de 0 a 360° → sombra real todo el año.
    con_sombra = run_bipv_simulation(
        _config_base(puntos_horizonte=[(0, 60), (90, 60), (180, 60), (270, 60)]),
        tmy=tmy_bogota,
    )
    assert con_sombra.sombreado["factor_sombra_anual"] > 0.0
    assert con_sombra.E_ac_anual_kWh < sin_sombra.E_ac_anual_kWh
    assert con_sombra.factor_pr_mismatch < sin_sombra.factor_pr_mismatch


def test_run_financial_simulation_estructura(tmy_bogota):
    energy = run_bipv_simulation(_config_base(), tmy=tmy_bogota)
    fin_config = FinancialConfiguration(
        capex_usd=energy.P_dc_stc_kW * 1000 * 0.30,   # ~0.30 USD/Wp, orden de magnitud BIPV
        tarifa_cop_kWh=750.0,
        tipo_cambio=4000.0,
        n_anos=25,
    )
    r = run_financial_simulation(energy, fin_config)

    assert len(r.flujos) == fin_config.n_anos + 1   # año 0..25
    assert r.flujos[0]["año"] == 0
    assert r.flujos[0]["flujo_usd"] < 0   # desembolso inicial neto de beneficios 1715
    assert r.beneficios_1715 is not None
    assert r.beneficios_1715["total_usd"] > 0

    assert isinstance(r.npv_usd, float)
    assert {"vpn_usd", "tir_pct", "payback_simple", "lcoe_usd_kWh"} <= r.metricas.keys()


def test_run_financial_simulation_sin_ley_1715(tmy_bogota):
    energy = run_bipv_simulation(_config_base(), tmy=tmy_bogota)
    fin_config = FinancialConfiguration(
        capex_usd=50_000.0, tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
        aplicar_ley_1715=False,
    )
    r = run_financial_simulation(energy, fin_config)
    assert r.beneficios_1715 is None
    # Sin beneficios, el desembolso neto del año 0 es el CAPEX completo.
    assert r.flujos[0]["flujo_usd"] == pytest.approx(-50_000.0)


def test_mayor_capex_empeora_payback_pero_no_cambia_produccion(tmy_bogota):
    energy = run_bipv_simulation(_config_base(), tmy=tmy_bogota)
    barato = run_financial_simulation(energy, FinancialConfiguration(
        capex_usd=30_000.0, tarifa_cop_kWh=750.0, tipo_cambio=4000.0, aplicar_ley_1715=False,
    ))
    caro = run_financial_simulation(energy, FinancialConfiguration(
        capex_usd=90_000.0, tarifa_cop_kWh=750.0, tipo_cambio=4000.0, aplicar_ley_1715=False,
    ))
    assert caro.metricas["vpn_usd"] < barato.metricas["vpn_usd"]
    if barato.metricas["payback_simple"] and caro.metricas["payback_simple"]:
        assert caro.metricas["payback_simple"] > barato.metricas["payback_simple"]
