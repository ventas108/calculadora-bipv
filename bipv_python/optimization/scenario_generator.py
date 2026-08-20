"""
Fase 4, Paso 2: generación de candidatos.

Muestrea configuraciones dentro de los límites de optimization/variables.py
(Fase 3) y descarta las que no pasan evaluar_factibilidad_previa() —
constraints.py, que corre SIN física completa — antes de que le cueste una
sola simulación a nadie.

Solo variables continua/entera (mismo alcance que sensitivity.py — ver su
docstring sobre por qué "panel" categórico queda fuera del muestreo
genérico).
"""
import random
from dataclasses import replace

from simulation.schemas import BIPVConfiguration
from optimization.variables import OptimizationVariable
from optimization.constraints import evaluar_factibilidad_previa, todas_cumplidas


def _muestrear_variable(var: OptimizationVariable, rng: random.Random):
    if var.tipo == "categorica":
        raise ValueError(
            f"'{var.nombre}' es categórica — generar_candidatos() no la muestrea; "
            "resuélvela explícitamente antes de armar la configuración base."
        )
    if var.tipo == "entera":
        return rng.randint(int(var.minimo), int(var.maximo))
    return rng.uniform(var.minimo, var.maximo)


def generar_candidatos(
    config_base: BIPVConfiguration,
    variables: list[OptimizationVariable],
    n_candidatos: int,
    seed: int | None = None,
    requerir_evaluables: bool = True,
    max_intentos_por_candidato: int = 20,
) -> list[BIPVConfiguration]:
    """
    Muestreo aleatorio uniforme (no Latin Hypercube todavía — ver nota al
    final del módulo) dentro de los límites de `variables`, filtrando por
    evaluar_factibilidad_previa().

    requerir_evaluables : se pasa tal cual a todas_cumplidas(). En True
        (default), un candidato sin config_base.inversor definido nunca pasa
        el filtro (la restricción eléctrica queda "no evaluable" y eso NO
        se trata como aprobado) — pásalo en False si de verdad solo te
        interesa la cobertura de área para esta exploración.

    Devuelve HASTA n_candidatos configuraciones factibles — puede devolver
    menos si el espacio de búsqueda es muy restrictivo; nunca inventa
    candidatos para completar la cuota.
    """
    rng = random.Random(seed)
    solo_numericas = [v for v in variables if v.tipo != "categorica"]

    candidatos: list[BIPVConfiguration] = []
    max_intentos = n_candidatos * max_intentos_por_candidato
    intentos = 0
    while len(candidatos) < n_candidatos and intentos < max_intentos:
        intentos += 1
        cambios = {v.nombre: _muestrear_variable(v, rng) for v in solo_numericas}
        candidato = replace(config_base, **cambios)
        constraints = evaluar_factibilidad_previa(candidato)
        if todas_cumplidas(constraints, requerir_evaluables=requerir_evaluables):
            candidatos.append(candidato)
    return candidatos

# Nota: muestreo aleatorio uniforme, no Latin Hypercube Sampling (LHS). Para
# pocas variables (~5) y unas pocas decenas de candidatos la diferencia
# práctica es pequeña; LHS mejora la cobertura del espacio a medida que
# crece la dimensionalidad o se reduce el presupuesto de simulaciones.
# Migrar a LHS es un cambio aislado a _muestrear_variable() — no toca el
# resto del pipeline (constraints, evaluación, Pareto).
