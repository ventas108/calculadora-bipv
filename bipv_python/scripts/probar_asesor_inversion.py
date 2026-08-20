"""
Prueba manual del Asesor de Inversión — CON COSTO REAL DE API.

Este script llama a la API de Anthropic (claude-opus-5) de verdad. NO se
ejecuta en ningún test automático ni en CI — correrlo es una decisión
explícita de quien lo invoca. Requiere ANTHROPIC_API_KEY en el entorno.

Uso:
    python scripts/probar_asesor_inversion.py

Qué hace:
1. Corre generación de candidatos + Pareto (Fase 4) sobre un TMY sintético
   offline (Bogotá) — cero costo, ya validado en tests/test_optimization_fase4.py.
2. Re-simula el frente de Pareto para tener el FinancialResult completo
   de cada candidato.
3. Llama al Asesor de Inversión UNA vez sobre esos resultados reales —
   aquí es donde se gasta dinero.
"""
import dataclasses
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datos.catalogo_inversores import INVERSORES
from datos.tecnologias_bipv import ASP_ST1_T40

from simulation.bipv_simulator import run_bipv_simulation
from simulation.financial_simulator import run_financial_simulation
from simulation.schemas import FinancialConfiguration

from optimization import variables as opt_vars
from optimization.scenario_generator import generar_candidatos
from optimization.numerical_optimizer import evaluar_candidatos
from optimization.pareto import frente_pareto
from optimization.objectives import estimar_capex_parametrico_usd

from agentes.herramientas import CandidatoRegistrado
from agentes.asesor_inversion import ejecutar_asesoria, texto_final

from tests.test_simulation_pipeline import _tmy_sintetico_offline, _config_base, LAT, LON, ALT_M

GROWATT = INVERSORES["Growatt-MID15KTL3-X"]


def _fin_builder(sim):
    capex = estimar_capex_parametrico_usd(sim, "BIPV fachada/pérgola")
    return FinancialConfiguration(capex_usd=capex, tarifa_cop_kWh=750.0, tipo_cambio=4000.0)


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY no está en el entorno. Exporta la key antes de correr esto.")
        sys.exit(1)

    print("1/4 — Construyendo TMY sintético offline (Bogotá)...")
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)

    cfg_base = dataclasses.replace(
        _config_base(), panel=ASP_ST1_T40, inversor=GROWATT,
        N_serie=8, N_strings_tracker=8,
    )

    print("2/4 — Generando candidatos + Pareto (sin costo, motor determinista)...")
    variables_geo = opt_vars.variables_geometria("Fachada")
    candidatos = generar_candidatos(cfg_base, variables_geo, n_candidatos=15, seed=7)
    resultados = evaluar_candidatos(candidatos, tmy, fin_config_builder=_fin_builder)
    frente = frente_pareto(resultados, ["npv", "payback_simple"])
    print(f"    {len(candidatos)} candidatos generados, {len(frente)} en el frente de Pareto")

    print("3/4 — Re-simulando el frente de Pareto para el FinancialResult completo...")
    registro: dict[str, CandidatoRegistrado] = {}
    for i, r in enumerate(frente):
        sim = run_bipv_simulation(r.config, tmy=tmy)
        fin_cfg = _fin_builder(sim)
        fin = run_financial_simulation(sim, fin_cfg)
        cid = f"C{i + 1}"
        registro[cid] = CandidatoRegistrado(resultado=r, fin=fin, capex_usd=fin_cfg.capex_usd)

    print("4/4 — Llamando al Asesor de Inversión (claude-opus-5 — ESTO GASTA DINERO)...\n")
    mensaje = ejecutar_asesoria(registro)

    print("=" * 70)
    print(texto_final(mensaje))
    print("=" * 70)
    print(
        f"\n[uso] input_tokens={mensaje.usage.input_tokens} "
        f"output_tokens={mensaje.usage.output_tokens}"
    )


if __name__ == "__main__":
    main()
