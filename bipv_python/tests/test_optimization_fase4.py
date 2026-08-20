# -*- coding: utf-8 -*-
"""
Validación de Fase 4: sensibilidad, generación de candidatos, evaluación y
frente de Pareto. Reusa los fixtures de Fase 2/3 (TMY sintético offline,
panel/inversor reales validados contra el XLSM).
"""
import dataclasses

import pytest

from datos.catalogo_inversores import INVERSORES
from datos.tecnologias_bipv import ASP_ST1_T40

from simulation.schemas import FinancialConfiguration

from optimization import variables as opt_vars
from optimization.sensitivity import analizar_sensibilidad, ordenar_por_impacto
from optimization.scenario_generator import generar_candidatos, _muestrear_variable
from optimization.numerical_optimizer import evaluar_candidatos, ResultadoCandidato
from optimization.pareto import domina, frente_pareto
from optimization.objectives import estimar_capex_parametrico_usd

from tests.test_simulation_pipeline import _tmy_sintetico_offline, _config_base, LAT, LON, ALT_M

GROWATT = INVERSORES["Growatt-MID15KTL3-X"]


@pytest.fixture(scope="module")
def tmy_bogota():
    return _tmy_sintetico_offline(LAT, LON, ALT_M)


def _cfg_electricamente_valida():
    return dataclasses.replace(
        _config_base(), panel=ASP_ST1_T40, inversor=GROWATT,
        N_serie=8, N_strings_tracker=8,
    )


def _fin_builder(sim):
    capex = estimar_capex_parametrico_usd(sim, "BIPV fachada/pérgola")
    return FinancialConfiguration(capex_usd=capex, tarifa_cop_kWh=750.0, tipo_cambio=4000.0)


# ── sensitivity.py ────────────────────────────────────────────────────────

def test_sensibilidad_solo_evalua_variables_numericas(tmy_bogota):
    variables = opt_vars.variables_geometria("Fachada") + [opt_vars.variable_panel()]
    resultados = analizar_sensibilidad(_config_base(), variables, tmy_bogota)
    assert {r.variable for r in resultados} == {"tilt", "azimuth"}   # panel (categórica) excluida


def test_sensibilidad_impacto_absoluto_correcto(tmy_bogota):
    variables = opt_vars.variables_geometria("Fachada")
    resultados = analizar_sensibilidad(_config_base(), variables, tmy_bogota)
    for r in resultados:
        assert r.impacto_absoluto["energia_anual"] == pytest.approx(
            abs(r.objetivos_alto["energia_anual"] - r.objetivos_bajo["energia_anual"])
        )
        assert "npv" not in r.impacto_absoluto   # sin fin_config_builder, no hay valor numérico


def test_sensibilidad_con_financiero_incluye_npv(tmy_bogota):
    variables = [opt_vars.variable_k_bipv()]
    resultados = analizar_sensibilidad(_config_base(), variables, tmy_bogota, fin_config_builder=_fin_builder)
    assert resultados[0].objetivos_bajo["npv"] is not None
    assert "npv" in resultados[0].impacto_absoluto


def test_ordenar_por_impacto_descendente(tmy_bogota):
    variables = opt_vars.variables_geometria("Fachada") + [opt_vars.variable_k_bipv()]
    resultados = analizar_sensibilidad(_config_base(), variables, tmy_bogota)
    ordenado = ordenar_por_impacto(resultados, "energia_anual")
    impactos = [r.impacto_absoluto["energia_anual"] for r in ordenado]
    assert impactos == sorted(impactos, reverse=True)


# ── scenario_generator.py ────────────────────────────────────────────────

def test_muestrear_variable_categorica_lanza_error():
    with pytest.raises(ValueError, match="categórica"):
        _muestrear_variable(opt_vars.variable_panel(), rng=__import__("random").Random(0))


def test_generar_candidatos_sin_inversor_no_fabrica_candidatos():
    # requerir_evaluables=True (default): compatibilidad_electrica no
    # evaluable sin inversor -> nunca se aprueba por defecto.
    cfg = dataclasses.replace(_config_base(), inversor=None)
    candidatos = generar_candidatos(
        cfg, opt_vars.variables_geometria("Fachada"), n_candidatos=5, seed=1,
    )
    assert candidatos == []


def test_generar_candidatos_relajando_evaluabilidad_si_produce_candidatos():
    cfg = dataclasses.replace(_config_base(), inversor=None)
    candidatos = generar_candidatos(
        cfg, opt_vars.variables_geometria("Fachada"), n_candidatos=5, seed=1,
        requerir_evaluables=False,
    )
    assert len(candidatos) == 5


def test_generar_candidatos_electricamente_validos_respeta_bounds():
    cfg = _cfg_electricamente_valida()
    variables = opt_vars.variables_geometria("Fachada")
    candidatos = generar_candidatos(cfg, variables, n_candidatos=8, seed=7)
    assert len(candidatos) == 8
    tilt_var = next(v for v in variables if v.nombre == "tilt")
    az_var = next(v for v in variables if v.nombre == "azimuth")
    for c in candidatos:
        assert tilt_var.minimo <= c.tilt <= tilt_var.maximo
        assert az_var.minimo <= c.azimuth <= az_var.maximo
        # el resto de la config (panel/inversor/N_serie) no se tocó
        assert c.N_serie == cfg.N_serie


def test_generar_candidatos_es_reproducible_con_seed():
    cfg = _cfg_electricamente_valida()
    variables = opt_vars.variables_geometria("Fachada")
    c1 = generar_candidatos(cfg, variables, n_candidatos=5, seed=42)
    c2 = generar_candidatos(cfg, variables, n_candidatos=5, seed=42)
    assert [(c.tilt, c.azimuth) for c in c1] == [(c.tilt, c.azimuth) for c in c2]


# ── numerical_optimizer.py ───────────────────────────────────────────────

def test_evaluar_candidatos_end_to_end(tmy_bogota):
    cfg = _cfg_electricamente_valida()
    candidatos = generar_candidatos(cfg, opt_vars.variables_geometria("Fachada"), n_candidatos=4, seed=3)
    resultados = evaluar_candidatos(candidatos, tmy_bogota, fin_config_builder=_fin_builder)

    assert len(resultados) == 4
    for r in resultados:
        assert r.objetivos["energia_anual"] > 0
        assert r.objetivos["npv"] is not None


def test_evaluar_candidatos_sin_fin_builder_dejan_financieros_en_none(tmy_bogota):
    cfg = _cfg_electricamente_valida()
    candidatos = generar_candidatos(cfg, opt_vars.variables_geometria("Fachada"), n_candidatos=2, seed=3)
    resultados = evaluar_candidatos(candidatos, tmy_bogota)
    assert all(r.objetivos["npv"] is None for r in resultados)


# ── pareto.py ─────────────────────────────────────────────────────────────

def test_domina_ignora_objetivos_none():
    a = {"npv": 100.0, "payback_simple": None}
    b = {"npv": 50.0, "payback_simple": None}
    assert domina(a, b, ["npv", "payback_simple"]) is True   # solo npv es comparable


def test_domina_requiere_mejor_o_igual_en_todos():
    a = {"npv": 100.0, "payback_simple": 6.0}
    b = {"npv": 50.0, "payback_simple": 4.0}   # b tiene mejor payback
    assert domina(a, b, ["npv", "payback_simple"]) is False
    assert domina(b, a, ["npv", "payback_simple"]) is False


def test_domina_empate_total_no_domina():
    a = {"npv": 100.0}
    b = {"npv": 100.0}
    assert domina(a, b, ["npv"]) is False


def test_frente_pareto_caso_sintetico_conocido():
    r = [
        ResultadoCandidato(config=None, objetivos={"npv": 100.0, "payback_simple": 8.0}),  # A
        ResultadoCandidato(config=None, objetivos={"npv": 80.0,  "payback_simple": 4.0}),  # B
        ResultadoCandidato(config=None, objetivos={"npv": 50.0,  "payback_simple": 9.0}),  # C: dominado por A y B
    ]
    frente = frente_pareto(r, ["npv", "payback_simple"])
    assert len(frente) == 2
    assert r[2] not in frente


def test_frente_pareto_end_to_end_ningun_miembro_dominado(tmy_bogota):
    cfg = _cfg_electricamente_valida()
    candidatos = generar_candidatos(cfg, opt_vars.variables_geometria("Fachada"), n_candidatos=10, seed=11)
    resultados = evaluar_candidatos(candidatos, tmy_bogota, fin_config_builder=_fin_builder)
    frente = frente_pareto(resultados, ["npv", "payback_simple"])

    assert 0 < len(frente) <= len(resultados)
    for candidato in frente:
        assert not any(
            domina(otro.objetivos, candidato.objetivos, ["npv", "payback_simple"])
            for otro in resultados if otro is not candidato
        )
