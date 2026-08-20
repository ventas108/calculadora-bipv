# -*- coding: utf-8 -*-
"""Validación de agentes/herramientas.py -- en particular formatear_candidatos(),
que ahora recibe candidatos armados a mano desde session_state (página 18
Análisis IA) además de los que arma optimization/numerical_optimizer.py.
Ese segundo origen no garantiza objetivos siempre numéricos -- ver el
docstring de _fmt() en agentes/herramientas.py.
"""
from simulation.schemas import BIPVConfiguration, FinancialResult
from optimization.numerical_optimizer import ResultadoCandidato
from agentes.herramientas import CandidatoRegistrado, formatear_candidatos

_CFG = BIPVConfiguration(
    lat=4.711, lon=-74.072, alt_m=2600.0,
    tilt=90.0, azimuth=180.0, area_m2=100.0,
)


def _fin(vpn_usd=1000.0, tir_pct=15.0, payback_simple=6.0):
    return FinancialResult(
        beneficios_1715=None, flujos=[],
        metricas={"vpn_usd": vpn_usd, "tir_pct": tir_pct,
                  "payback_simple": payback_simple, "lcoe_usd_kWh": 0.05},
    )


def test_formatear_candidatos_caso_normal_todo_numerico():
    objetivos = {
        "energia_anual": 12345.678, "pr": 0.834, "capacidad_instalada": 9.5,
        "npv": 1000.0, "irr": 15.0, "payback_simple": 6.0, "lcoe": 0.05,
    }
    registro = {
        "C1": CandidatoRegistrado(
            resultado=ResultadoCandidato(config=_CFG, objetivos=objetivos),
            fin=_fin(), capex_usd=36000.0,
        ),
    }
    texto = formatear_candidatos(registro)
    assert "energía=12,346 kWh" in texto
    assert "PR=0.834" in texto
    assert "potencia DC=9.5 kWp" in texto
    assert "NPV=USD 1,000" in texto
    assert "IRR=15.0%" in texto
    assert "payback=6.0 años" in texto


def test_formatear_candidatos_no_crashea_con_objetivos_faltantes():
    # Regresión: un candidato armado a mano desde session_state (página 18
    # Análisis IA) puede tener un objetivo ausente sin que sea un bug del
    # motor -- formatear_candidatos() antes hacía f"{None:,.0f}" y rompía
    # con TypeError en vez de degradar a "N/D".
    objetivos = {
        "energia_anual": None, "pr": None, "capacidad_instalada": None,
        "npv": 1000.0, "irr": None, "payback_simple": None, "lcoe": None,
    }
    registro = {
        "Actual": CandidatoRegistrado(
            resultado=ResultadoCandidato(config=_CFG, objetivos=objetivos),
            fin=_fin(), capex_usd=36000.0,
        ),
    }
    texto = formatear_candidatos(registro)   # no debe lanzar TypeError
    assert "energía=N/D kWh" in texto
    assert "PR=N/D" in texto
    assert "potencia DC=N/D kWp" in texto
    assert "IRR=None (sin solución real)" in texto
    assert "payback=None" in texto


def test_formatear_candidatos_capex_cero_por_defecto_no_es_none():
    # capex_usd nunca debería ser None (CandidatoRegistrado lo tipa float),
    # pero confirmamos que 0.0 se formatea como número, no como "N/D".
    objetivos = {"energia_anual": 100.0, "pr": 0.8, "capacidad_instalada": 1.0,
                 "npv": 0.0, "irr": None, "payback_simple": None, "lcoe": None}
    registro = {
        "C1": CandidatoRegistrado(
            resultado=ResultadoCandidato(config=_CFG, objetivos=objetivos),
            fin=_fin(vpn_usd=0.0), capex_usd=0.0,
        ),
    }
    texto = formatear_candidatos(registro)
    assert "CAPEX=USD 0" in texto
    assert "NPV=USD 0" in texto
