"""
Fase 4, Paso 2: generación de candidatos.

Muestrea configuraciones dentro de los límites de optimization/variables.py
(Fase 3) y descarta las que no pasan evaluar_factibilidad_previa() —
constraints.py, que corre SIN física completa — antes de que le cueste una
sola simulación a nadie.

Variables continua/entera Y categóricas de catálogo (panel, inversor) —
sensitivity.py (Fase 4, Paso 1) SÍ sigue excluyendo categóricas del barrido
OAT (ver su docstring: "mover" una elección de catálogo no es un barrido
continuo entre dos extremos), pero un generador de candidatos por muestreo
aleatorio no tiene ese problema — cada candidato ya es una elección
discreta completa, así que sortear panel/inversor junto con tilt/azimuth/
N_serie es exactamente lo que hace falta para comparar configuraciones de
hardware real, no solo geometría.
"""
import random
from dataclasses import replace

from simulation.schemas import BIPVConfiguration
from optimization.variables import OptimizationVariable
from optimization.constraints import evaluar_factibilidad_previa, todas_cumplidas

# Variables categóricas cuyo OptimizationVariable.opciones guarda la CLAVE
# de un catálogo real (str), no el dict completo -- ver el docstring de
# variable_panel()/variable_inversor() en optimization/variables.py. Antes
# de armar el candidato hay que resolver esa clave al dict real, y en el
# caso de "inversor" además sincronizar eta_inversor (antes fijo en
# FIJOS_NO_OPTIMIZABLES) con la eficiencia del inversor sorteado -- un
# candidato con inversor Growatt pero eta_inversor de otro fabricante sería
# una config internamente inconsistente que nadie pidió.
def _resolver_categoricas_de_catalogo(cambios: dict) -> dict:
    resuelto = dict(cambios)
    if "panel" in resuelto:
        from datos.tecnologias_bipv import MODULOS_BIPV
        resuelto["panel"] = MODULOS_BIPV[resuelto["panel"]]
    if "inversor" in resuelto:
        from datos.catalogo_inversores import INVERSORES
        inversor_dict = INVERSORES[resuelto["inversor"]]
        resuelto["inversor"] = inversor_dict
        resuelto["eta_inversor"] = inversor_dict["eficiencia_max"]
    return resuelto


def _muestrear_variable(var: OptimizationVariable, rng: random.Random):
    if var.tipo == "categorica":
        return rng.choice(var.opciones)
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
    evaluar_factibilidad_previa(). Incluye variables categóricas de
    catálogo (panel, inversor) además de continua/entera -- ver
    _resolver_categoricas_de_catalogo().

    requerir_evaluables : se pasa tal cual a todas_cumplidas(). En True
        (default), un candidato sin config_base.inversor definido nunca pasa
        el filtro (la restricción eléctrica queda "no evaluable" y eso NO
        se trata como aprobado) — pásalo en False si de verdad solo te
        interesa la cobertura de área para esta exploración.

    Devuelve HASTA n_candidatos configuraciones factibles — puede devolver
    menos si el espacio de búsqueda es muy restrictivo; nunca inventa
    candidatos para completar la cuota.

    Nota de escala: sortear panel + inversor + N_serie + N_strings_tracker
    a la vez multiplica el espacio de búsqueda -- la ventana eléctrica
    Voc/Vmp válida para un panel+inversor concreto suele ser angosta (ver
    calculos.dimensionamiento.optimizar_n_serie(), rango típico N=6-12 de
    un límite general de 1-40), así que la tasa de rechazo puede ser alta.
    Si con el max_intentos_por_candidato por defecto no alcanzas
    n_candidatos, súbelo explícitamente -- esta función nunca lo hace sola
    ni inventa candidatos para completar la cuota.
    """
    rng = random.Random(seed)

    candidatos: list[BIPVConfiguration] = []
    max_intentos = n_candidatos * max_intentos_por_candidato
    intentos = 0
    while len(candidatos) < n_candidatos and intentos < max_intentos:
        intentos += 1
        cambios = {v.nombre: _muestrear_variable(v, rng) for v in variables}
        cambios = _resolver_categoricas_de_catalogo(cambios)
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
