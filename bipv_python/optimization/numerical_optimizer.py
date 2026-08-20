"""
Fase 4, Paso 3: evaluar candidatos por el pipeline completo.

Corre cada candidato (ya filtrado por scenario_generator.py) a través de
run_bipv_simulation() + run_financial_simulation() (Fase 2) y extrae sus
objetivos (Fase 3). No decide todavía CUÁLES candidatos generar de forma
inteligente — eso es optimization/pareto.py y, más adelante, una
metaheurística real. Esta pieza es deliberadamente la más simple posible:
"correr N configuraciones y guardar los resultados", separada de cómo se
eligieron esas N configuraciones.
"""
from dataclasses import dataclass
from typing import Callable

import pandas as pd

from simulation.schemas import BIPVConfiguration, FinancialConfiguration, SimulationResult
from simulation.bipv_simulator import run_bipv_simulation
from simulation.financial_simulator import run_financial_simulation
from optimization.objectives import extraer_objetivos

FinConfigBuilder = Callable[[SimulationResult], "FinancialConfiguration | None"]


@dataclass
class ResultadoCandidato:
    config: BIPVConfiguration
    objetivos: dict[str, float | None]


def evaluar_candidatos(
    candidatos: list[BIPVConfiguration],
    tmy: pd.DataFrame,
    fin_config_builder: FinConfigBuilder | None = None,
) -> list[ResultadoCandidato]:
    """
    fin_config_builder : callable(SimulationResult) -> FinancialConfiguration
                          (o None para omitir ese candidato del lado
                          financiero). Se llama una vez por candidato — así
                          puede resolver el CAPEX específico de cada uno
                          (p.ej. con optimization.objectives.
                          estimar_capex_parametrico_usd(), que depende del
                          P_dc_stc_kW de ESE candidato, no uno fijo).
    """
    resultados = []
    for config in candidatos:
        sim = run_bipv_simulation(config, tmy=tmy)
        fin = None
        if fin_config_builder is not None:
            fin_cfg = fin_config_builder(sim)
            if fin_cfg is not None:
                fin = run_financial_simulation(sim, fin_cfg)
        resultados.append(ResultadoCandidato(config=config, objetivos=extraer_objetivos(sim, fin)))
    return resultados
