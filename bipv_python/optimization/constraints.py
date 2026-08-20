"""
Optimization Contract — Fase 3, Paso 2: restricciones de factibilidad.

Un candidato puede tener un NPV excelente y ser físicamente irrealizable
(más panel del que cabe en la fachada) o eléctricamente inválido (string
fuera de la ventana MPPT del inversor). Estas funciones separan "¿es
factible?" de "¿qué tan bueno es?" (eso es optimization/objectives.py) —
un optimizador (Fase 4) debe poder descartar un candidato barato de evaluar
ANTES de correr la simulación física completa.

Ninguna restricción se reimplementa aquí: evaluar_compatibilidad_electrica()
delega en calculos.dimensionamiento.evaluar_compatibilidad_string(), la
misma función que ya usan Dimensionamiento y sus tests de validación contra
el XLSM de referencia.
"""
from dataclasses import dataclass

from calculos import dimensionamiento
from simulation.schemas import BIPVConfiguration


@dataclass(frozen=True)
class ConstraintResult:
    nombre: str
    cumple: bool
    evaluable: bool   # False = no se pudo evaluar (p.ej. falta el inversor)
    mensaje: str


def evaluar_cobertura_area(dim: dict) -> ConstraintResult:
    """dim : el dict que devuelve calculos.dimensionamiento.dimensionar_sistema()."""
    cobertura = float(dim.get("cobertura_pct", 0.0))
    cumple = cobertura <= 100.0
    mensaje = (
        f"Cobertura {cobertura:.1f}% del área disponible"
        if cumple else
        f"Cobertura {cobertura:.1f}% excede el área disponible (>100%) — "
        f"reduce N_paneles o aumenta area_m2"
    )
    return ConstraintResult("cobertura_area", cumple, True, mensaje)


def evaluar_compatibilidad_electrica(
    config: BIPVConfiguration,
    T_frio: float = -5.0,
    T_real: float = 36.35,
    T_extremo: float = 41.94,
    FS_isc: float = 1.25,
) -> ConstraintResult:
    """
    Ventana eléctrica Voc/Vmp/Isc del string contra el inversor elegido.

    T_frio/T_real/T_extremo mantienen los mismos valores por defecto que
    calculos.dimensionamiento.evaluar_compatibilidad_string() (validados
    contra el XLSM de referencia) — no se inventan nuevos aquí.
    """
    if config.inversor is None:
        return ConstraintResult(
            "compatibilidad_electrica", False, False,
            "No evaluable: BIPVConfiguration.inversor no está definido.",
        )

    r = dimensionamiento.evaluar_compatibilidad_string(
        config.panel, config.inversor, config.N_serie,
        T_frio=T_frio, T_real=T_real, T_extremo=T_extremo,
        N_strings_tracker=config.N_strings_tracker, FS_isc=FS_isc,
    )
    if not r["evaluable"]:
        return ConstraintResult(
            "compatibilidad_electrica", False, False, "; ".join(r["mensajes"]),
        )
    mensaje = (
        "Compatible con la ventana eléctrica del inversor" if r["compatible"]
        else "; ".join(r["mensajes"])
    )
    return ConstraintResult("compatibilidad_electrica", r["compatible"], True, mensaje)


def evaluar_constraints(
    config: BIPVConfiguration,
    dim: dict,
    **kwargs_electrico,
) -> list[ConstraintResult]:
    """
    Corre todos los constraints conocidos.

    dim : el dict de calculos.dimensionamiento.dimensionar_sistema() — puede
          venir de un SimulationResult ya calculado (resultado.dim) o
          calcularse directo sin correr la física completa (ver
          evaluar_factibilidad_previa(), más barato para un optimizador).
    """
    return [
        evaluar_cobertura_area(dim),
        evaluar_compatibilidad_electrica(config, **kwargs_electrico),
    ]


def evaluar_factibilidad_previa(
    config: BIPVConfiguration,
    **kwargs_electrico,
) -> list[ConstraintResult]:
    """
    Los mismos constraints de evaluar_constraints(), pero SIN correr la
    física completa (TMY/POA/sombreado/producción) — dimensionar_sistema()
    es aritmética pura. Pensada para que un generador de candidatos (Fase 4)
    descarte configuraciones inválidas ANTES de gastar una simulación en
    ellas, tal como pide el docstring de este módulo.
    """
    dim = dimensionamiento.dimensionar_sistema(
        config.panel, config.area_m2, config.N_serie,
        config.N_strings_tracker, config.N_mppt,
    )
    return evaluar_constraints(config, dim, **kwargs_electrico)


def todas_cumplidas(resultados: list[ConstraintResult], *, requerir_evaluables: bool = True) -> bool:
    """
    True si ningún constraint evaluable falla.

    requerir_evaluables=True (default): un constraint que NO se pudo evaluar
    (p.ej. falta el inversor) cuenta como no-factible — nunca se aprueba por
    default lo que no se pudo verificar. Pásalo en False solo si de verdad no
    te importa esa restricción para el caso de uso.
    """
    if requerir_evaluables and any(not r.evaluable for r in resultados):
        return False
    return all(r.cumple for r in resultados if r.evaluable)
