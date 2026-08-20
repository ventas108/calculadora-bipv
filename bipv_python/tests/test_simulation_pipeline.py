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
