"""
Fase 4, Paso 1: análisis de sensibilidad.

Antes de generar decenas de candidatos (scenario_generator.py) o correr una
búsqueda, esto responde una pregunta más barata: ¿qué variables mueven de
verdad los objetivos? Barrido uno-a-la-vez (OAT) desde una configuración
base: mueve UNA variable entre sus extremos, deja las demás fijas, mide el
impacto en cada objetivo. No es un análisis de varianza global (Sobol/
Morris) — es la versión barata y explicable que el plan original pedía
antes de comprometer presupuesto de cómputo a una búsqueda más cara
("no desperdicies simulaciones optimizando una variable que casi no
cambia el NPV").

Alcance v1: solo variables continua/entera (tilt, azimuth, N_serie,
N_strings_tracker, k_bipv). Las categóricas (panel) quedan fuera a
propósito — "mover" una elección de catálogo no es un barrido continuo
entre dos extremos, es una comparación explícita de opciones discretas con
su propia semántica; mezclarla aquí oscurecería el resultado en vez de
aclararlo.

Variables circulares (OptimizationVariable.circular=True, p.ej. azimuth):
minimo y maximo son el MISMO punto físico (0°=360°=Norte), así que el
barrido no compara minimo vs maximo sino minimo vs el punto medio del
dominio (el verdadero opuesto en el ciclo, p.ej. Norte vs Sur) — ver
_valores_extremos() más abajo. Sin esto, "valor_alto" en ResultadoSensibilidad
sería una repetición de "valor_bajo" y el impacto daría cero por
construcción, no porque la variable no importe.
"""
from dataclasses import dataclass, replace

import pandas as pd

from simulation.schemas import BIPVConfiguration
from simulation.bipv_simulator import run_bipv_simulation
from simulation.financial_simulator import run_financial_simulation
from optimization.variables import OptimizationVariable
from optimization.objectives import extraer_objetivos


@dataclass(frozen=True)
class ResultadoSensibilidad:
    variable: str
    valor_bajo: float
    valor_alto: float
    objetivos_bajo: dict
    objetivos_alto: dict
    # {objetivo: |objetivo_alto - objetivo_bajo|} — solo objetivos con valor
    # numérico en AMBOS extremos (p.ej. si irr_pct es None en alguno, no
    # entra aquí en vez de romper con un TypeError).
    impacto_absoluto: dict


def _evaluar(config: BIPVConfiguration, tmy: pd.DataFrame, fin_config_builder) -> dict:
    sim = run_bipv_simulation(config, tmy=tmy)
    fin_cfg = fin_config_builder(sim) if fin_config_builder else None
    fin = run_financial_simulation(sim, fin_cfg) if fin_cfg else None
    return extraer_objetivos(sim, fin)


def _valores_extremos(var: OptimizationVariable) -> tuple[float, float]:
    """
    Los dos puntos a evaluar en el barrido OAT para `var`.

    Para variables normales: (minimo, maximo).
    Para variables circulares (var.circular=True): minimo y maximo son el
    MISMO punto físico (p.ej. azimuth 0°=360°=Norte), así que se usa el
    punto medio del dominio como el verdadero opuesto en el ciclo
    (Norte vs Sur, no Norte vs Norte).
    """
    if var.circular:
        return var.minimo, var.minimo + (var.maximo - var.minimo) / 2
    return var.minimo, var.maximo


def analizar_sensibilidad(
    config_base: BIPVConfiguration,
    variables: list[OptimizationVariable],
    tmy: pd.DataFrame,
    fin_config_builder=None,
) -> list[ResultadoSensibilidad]:
    """
    fin_config_builder : callable(SimulationResult) -> FinancialConfiguration,
                          o None para evaluar solo objetivos técnicos (más
                          rápido — no requiere haber resuelto el CAPEX).
    """
    resultados = []
    for var in variables:
        if var.tipo == "categorica":
            continue   # ver docstring del módulo

        bajo, alto = _valores_extremos(var)
        if var.tipo == "entera":
            bajo, alto = int(bajo), int(alto)

        obj_bajo = _evaluar(replace(config_base, **{var.nombre: bajo}), tmy, fin_config_builder)
        obj_alto = _evaluar(replace(config_base, **{var.nombre: alto}), tmy, fin_config_builder)

        impacto = {
            k: abs(obj_alto[k] - obj_bajo[k])
            for k in obj_bajo
            if obj_bajo[k] is not None and obj_alto.get(k) is not None
        }

        resultados.append(ResultadoSensibilidad(
            variable=var.nombre, valor_bajo=bajo, valor_alto=alto,
            objetivos_bajo=obj_bajo, objetivos_alto=obj_alto,
            impacto_absoluto=impacto,
        ))
    return resultados


def ordenar_por_impacto(
    resultados: list[ResultadoSensibilidad], objetivo: str,
) -> list[ResultadoSensibilidad]:
    """
    De mayor a menor impacto sobre `objetivo`. Variables sin impacto
    medible para ese objetivo (p.ej. un objetivo financiero cuando no se
    pasó fin_config_builder) quedan al final, no generan error.
    """
    return sorted(
        resultados,
        key=lambda r: r.impacto_absoluto.get(objetivo, -1.0),
        reverse=True,
    )
