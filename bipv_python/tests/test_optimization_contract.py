# -*- coding: utf-8 -*-
"""
Validación del Optimization Contract (Fase 3): variables, constraints,
objectives, investor profiles y bankability.

Reusa el TMY sintético offline y BIPVConfiguration base de
test_simulation_pipeline.py. Los casos de compatibilidad eléctrica usan el
panel/inversor de referencia ya validados contra el XLSM en
test_validacion_vba.py (N=8 → OK, N=9 → FALLA) para no inventar umbrales.
"""
import dataclasses
import json

import numpy as np
import pytest

from datos.catalogo_inversores import INVERSORES
from datos.tecnologias_bipv import ASP_ST1_T40

from simulation.bipv_simulator import run_bipv_simulation
from simulation.financial_simulator import run_financial_simulation
from simulation.schemas import FinancialConfiguration, FinancialResult

from optimization import variables as opt_vars
from optimization import constraints as opt_constraints
from optimization import objectives as opt_obj
from optimization.investor_profile import InvestorProfile, PERFIL_CONSERVADOR
from optimization.bankability import evaluar_bankability

from tests.test_simulation_pipeline import _tmy_sintetico_offline, _config_base, LAT, LON, ALT_M

GROWATT = INVERSORES["Growatt-MID15KTL3-X"]


@pytest.fixture(scope="module")
def tmy_bogota():
    return _tmy_sintetico_offline(LAT, LON, ALT_M)


# ── variables.py ──────────────────────────────────────────────────────────

def test_variables_geometria_usa_bounds_reales_de_tipos_superficie():
    from calculos.multi_superficie import TIPOS_SUPERFICIE

    vars_fachada = opt_vars.variables_geometria("Fachada")
    tilt = next(v for v in vars_fachada if v.nombre == "tilt")
    assert tilt.minimo == TIPOS_SUPERFICIE["Fachada"]["tilt_min"]
    assert tilt.maximo == TIPOS_SUPERFICIE["Fachada"]["tilt_max"]

    vars_generico = opt_vars.variables_geometria(None)
    tilt_generico = next(v for v in vars_generico if v.nombre == "tilt")
    assert (tilt_generico.minimo, tilt_generico.maximo) == (0.0, 90.0)


def test_variable_panel_opciones_coincide_con_catalogo_real_simulable():
    # No es TODO MODULOS_BIPV -- variable_panel() excluye por defecto los
    # paneles con Pmax_stc=None o area_m2=None (fichas incompletas que hacen
    # reventar dimensionar_sistema()). Ver docstring de variable_panel() y
    # tests/test_optimization_fase4.py::test_variable_panel_excluye_fichas_incompletas_del_catalogo_real
    # para el hallazgo completo.
    #
    # Desde que variable_panel() se conectó al catálogo Excel (27-ago-2026),
    # el catálogo real ya no es solo MODULOS_BIPV -- es la unión con los
    # paneles del Excel (ver optimization.variables._catalogo_paneles_real()).
    # "esperado" debe construirse contra esa misma unión, no contra
    # MODULOS_BIPV a secas, o este test volvería a fallar por diseño cada
    # vez que el catálogo Excel aporte una clave nueva.
    #
    # area_m2 agregado al filtro esperado (3-sep-2026): tras importar 278
    # paneles reales de JA Solar (datos/agregar_paneles_ja_solar_nrel.py),
    # 115 no traen dimensiones físicas en la fuente (solo área total) --
    # variable_panel() ya los excluye (ver el fix real en optimization/
    # variables.py), pero "esperado" aquí seguía construido solo con
    # Pmax_stc, así que sobre-incluía esos 115 y el test fallaba comparando
    # contra el propio filtro real que ya está corregido.
    from optimization.variables import _catalogo_paneles_real
    var = opt_vars.variable_panel()
    esperado = {
        k for k, v in _catalogo_paneles_real().items()
        if v.get("Pmax_stc") is not None and v.get("area_m2") is not None
    }
    assert set(var.opciones) == esperado


def test_variable_k_bipv_rango_documentado():
    var = opt_vars.variable_k_bipv()
    assert (var.minimo, var.maximo) == (1.0, 1.5)


def test_capex_usd_esta_documentado_como_no_exogeno():
    assert "capex_usd" in opt_vars.FIJOS_NO_OPTIMIZABLES
    assert "no es un dato exógeno" in opt_vars.FIJOS_NO_OPTIMIZABLES["capex_usd"].lower()


# ── constraints.py ────────────────────────────────────────────────────────

def test_cobertura_area_cumple_y_falla():
    assert opt_constraints.evaluar_cobertura_area({"cobertura_pct": 80.0}).cumple is True
    assert opt_constraints.evaluar_cobertura_area({"cobertura_pct": 120.0}).cumple is False


def test_compatibilidad_electrica_sin_inversor_no_es_evaluable():
    cfg = dataclasses.replace(_config_base(), panel=ASP_ST1_T40, N_serie=8, inversor=None)
    r = opt_constraints.evaluar_compatibilidad_electrica(cfg)
    assert r.evaluable is False
    assert r.cumple is False


def test_compatibilidad_electrica_n8_ok_n9_falla():
    # Docstring de calculos.dimensionamiento.optimizar_n_serie: N=8 → OK
    # (0 riesgos), N=9 → FALLA (Voc frío > 1100V) — validado contra el XLSM.
    cfg_n8 = dataclasses.replace(
        _config_base(), panel=ASP_ST1_T40, inversor=GROWATT,
        N_serie=8, N_strings_tracker=8,
    )
    cfg_n9 = dataclasses.replace(cfg_n8, N_serie=9)

    r8 = opt_constraints.evaluar_compatibilidad_electrica(cfg_n8)
    r9 = opt_constraints.evaluar_compatibilidad_electrica(cfg_n9)

    assert r8.evaluable and r8.cumple is True
    assert r9.evaluable and r9.cumple is False


def test_todas_cumplidas_exige_evaluabilidad_por_defecto():
    resultados = [opt_constraints.ConstraintResult("x", cumple=True, evaluable=False, mensaje="")]
    assert opt_constraints.todas_cumplidas(resultados) is False
    assert opt_constraints.todas_cumplidas(resultados, requerir_evaluables=False) is True


def test_evaluar_constraints_end_to_end(tmy_bogota):
    cfg = dataclasses.replace(
        _config_base(), panel=ASP_ST1_T40, inversor=GROWATT,
        N_serie=8, N_strings_tracker=8,
    )
    resultado = run_bipv_simulation(cfg, tmy=tmy_bogota)
    constraints = opt_constraints.evaluar_constraints(cfg, resultado.dim)
    assert {c.nombre for c in constraints} == {"cobertura_area", "compatibilidad_electrica"}
    assert opt_constraints.todas_cumplidas(constraints) is True

    # evaluar_factibilidad_previa() debe dar el mismo resultado sin correr
    # la simulación física (solo dimensionamiento, aritmética pura).
    previa = opt_constraints.evaluar_factibilidad_previa(cfg)
    assert [(c.nombre, c.cumple) for c in previa] == [(c.nombre, c.cumple) for c in constraints]


# ── objectives.py ─────────────────────────────────────────────────────────

def test_extraer_objetivos_sin_financiero_deja_esos_en_none(tmy_bogota):
    cfg = _config_base()
    sim = run_bipv_simulation(cfg, tmy=tmy_bogota)
    objetivos = opt_obj.extraer_objetivos(sim, fin=None)
    assert objetivos["energia_anual"] == sim.E_ac_anual_kWh
    assert objetivos["pr"] == sim.PR
    assert objetivos["npv"] is None
    assert objetivos["irr"] is None


def test_extraer_objetivos_con_financiero(tmy_bogota):
    cfg = _config_base()
    sim = run_bipv_simulation(cfg, tmy=tmy_bogota)
    fin = run_financial_simulation(sim, FinancialConfiguration(
        capex_usd=sim.P_dc_stc_kW * 1000 * 1.5, tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    ))
    objetivos = opt_obj.extraer_objetivos(sim, fin)
    assert objetivos["npv"] == fin.npv_usd
    assert objetivos["irr"] == fin.irr_pct
    assert objetivos["lcoe"] == fin.metricas["lcoe_usd_kWh"]


def test_estimar_capex_parametrico_coincide_con_presupuesto_directo(tmy_bogota):
    from calculos import presupuesto as presupuesto_calc

    cfg = _config_base()
    sim = run_bipv_simulation(cfg, tmy=tmy_bogota)

    esperado = presupuesto_calc.calcular_parametrico(
        sim.P_dc_stc_kW, "BIPV fachada/pérgola", "Base", "Bogotá / Sabana",
    )["capex_total"]

    obtenido = opt_obj.estimar_capex_parametrico_usd(sim, "BIPV fachada/pérgola")
    assert obtenido == pytest.approx(esperado)


# ── investor_profile.py + bankability.py ────────────────────────────────

def test_bankability_pass_con_proyecto_barato_y_buena_tarifa(tmy_bogota):
    cfg = _config_base()
    sim = run_bipv_simulation(cfg, tmy=tmy_bogota)
    fin = run_financial_simulation(sim, FinancialConfiguration(
        capex_usd=sim.P_dc_stc_kW * 1000 * 0.5,   # barato a propósito
        tarifa_cop_kWh=900.0, tipo_cambio=4000.0,
    ))
    ev = evaluar_bankability(fin, PERFIL_CONSERVADOR, capex_usd=None)
    assert ev.estado == "PASS"
    assert all(c.cumple for c in ev.criterios)
    assert ev.dimensiones_no_evaluadas   # declara honestamente lo que falta


def test_bankability_fail_con_proyecto_caro(tmy_bogota):
    cfg = _config_base()
    sim = run_bipv_simulation(cfg, tmy=tmy_bogota)
    fin = run_financial_simulation(sim, FinancialConfiguration(
        capex_usd=sim.P_dc_stc_kW * 1000 * 20.0,   # deliberadamente caro
        tarifa_cop_kWh=300.0, tipo_cambio=4000.0,
    ))
    ev = evaluar_bankability(fin, PERFIL_CONSERVADOR)
    assert ev.estado == "FAIL"
    assert any(not c.cumple for c in ev.criterios)


def test_bankability_sin_criterios_si_el_perfil_no_define_umbrales():
    fin = FinancialResult(beneficios_1715=None, flujos=[], metricas={
        "vpn_usd": 0.0, "tir_pct": None, "payback_simple": None, "lcoe_usd_kWh": 0.0,
    })
    ev = evaluar_bankability(fin, InvestorProfile(nombre="Vacío"))
    assert ev.estado == "SIN_CRITERIOS"
    assert ev.criterios == []


def test_bankability_maximo_capex_sin_proveer_capex_no_cumple():
    perfil = InvestorProfile(nombre="ConTope", maximum_capex_usd=100_000.0)
    fin = FinancialResult(beneficios_1715=None, flujos=[], metricas={
        "vpn_usd": 1.0, "tir_pct": 99.0, "payback_simple": 1.0, "lcoe_usd_kWh": 0.01,
    })
    ev = evaluar_bankability(fin, perfil, capex_usd=None)
    criterio = ev.criterios[0]
    assert criterio.nombre == "CAPEX máximo"
    assert criterio.cumple is False


def test_bankability_cumple_es_bool_nativo_no_numpy_bool():
    # Regresión: encontrado corriendo el Analista Técnico-Financiero (agente)
    # contra datos reales -- fin.irr_pct/npv_usd/payback_simple_anos venían
    # de metricas calculadas con numpy, así que `valor >= umbral` daba
    # numpy.bool_. numpy.bool_ imprime como "bool" (__class__.__name__) pero
    # NO hereda de bool (a diferencia de numpy.float64, que sí hereda de
    # float) -- json.dumps() lo rechaza con
    # "TypeError: Object of type bool is not JSON serializable", un error
    # confuso porque el nombre de la clase engaña. Cualquier consumidor que
    # serialice CriterioBankability (como la herramienta del agente) se
    # rompía en todos los perfiles.
    fin = FinancialResult(beneficios_1715=None, flujos=[], metricas={
        "vpn_usd": np.float64(1234.0),
        "tir_pct": np.float64(18.0),
        "payback_simple": np.float64(5.0),
        "lcoe_usd_kWh": np.float64(0.05),
    })
    perfil = InvestorProfile(
        nombre="Test", minimum_irr_pct=12.0, maximum_payback_anos=8.0,
        minimum_npv_usd=0.0, maximum_capex_usd=100_000.0,
    )
    ev = evaluar_bankability(fin, perfil, capex_usd=np.float64(50_000.0))

    assert len(ev.criterios) == 4
    for criterio in ev.criterios:
        assert type(criterio.cumple) is bool, (
            f"{criterio.nombre}: cumple es {type(criterio.cumple)}, no bool nativo"
        )

    # La razón real de este test: esto no debe volver a lanzar TypeError.
    json.dumps({"criterios": [{"cumple": c.cumple} for c in ev.criterios]})
