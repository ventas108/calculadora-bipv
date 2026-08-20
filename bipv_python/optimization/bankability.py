"""
Optimization Contract — Fase 3, Paso 5: evaluación de bancabilidad.

Deliberadamente NO es un score único ("bancabilidad = 87/100"). El plan
original ya advertía contra eso: un número solo esconde en qué falló un
candidato. evaluar_bankability() devuelve PASS/FAIL por criterio, más un
estado agregado, y — esto es lo importante — declara explícitamente qué
dimensiones NO evalúa todavía, para que nadie lea "PASS" como "bancable de
verdad" cuando solo se chequearon IRR/Payback/NPV/CAPEX.
"""
from dataclasses import dataclass
from typing import Literal

from optimization.investor_profile import InvestorProfile
from simulation.schemas import FinancialResult

Estado = Literal["PASS", "FAIL", "SIN_CRITERIOS"]

# Dimensiones del framework de bancabilidad original que este módulo NO
# evalúa — no porque se hayan olvidado, sino porque el motor todavía no
# calcula lo que haría falta para juzgarlas honestamente:
#   riesgo               → no hay stress testing / sensibilidad (Fase posterior)
#   financiamiento_deuda  → calculos/financiero.py no modela deuda ni DSCR
#   contractual           → permisos, garantías, EPC — fuera del alcance del motor
DIMENSIONES_NO_EVALUADAS: tuple[str, ...] = (
    "riesgo_y_sensibilidad", "financiamiento_deuda_DSCR", "contractual_y_permisos",
)


@dataclass(frozen=True)
class CriterioBankability:
    nombre: str
    cumple: bool
    valor: float | None
    umbral: float | None
    mensaje: str


@dataclass(frozen=True)
class BankabilityEvaluation:
    perfil: str
    estado: Estado
    criterios: list[CriterioBankability]
    dimensiones_no_evaluadas: tuple[str, ...] = DIMENSIONES_NO_EVALUADAS


def evaluar_bankability(
    fin: FinancialResult,
    perfil: InvestorProfile,
    capex_usd: float | None = None,
) -> BankabilityEvaluation:
    """
    Evalúa un FinancialResult contra los umbrales definidos en `perfil`.
    Un criterio que el perfil no define (queda en None) simplemente no se
    incluye — no se inventa un umbral por defecto.
    """
    criterios: list[CriterioBankability] = []

    if perfil.minimum_irr_pct is not None:
        valor = fin.irr_pct
        cumple = valor is not None and valor >= perfil.minimum_irr_pct
        mensaje = (
            f"IRR {valor:.1f}% {'≥' if cumple else '<'} mínimo requerido {perfil.minimum_irr_pct:.1f}%"
            if valor is not None else
            f"IRR no calculable (el flujo de caja no tiene una solución real) — no cumple {perfil.nombre}"
        )
        criterios.append(CriterioBankability("IRR", cumple, valor, perfil.minimum_irr_pct, mensaje))

    if perfil.maximum_payback_anos is not None:
        valor = fin.payback_simple_anos
        cumple = valor is not None and valor <= perfil.maximum_payback_anos
        mensaje = (
            f"Payback {valor:.1f} años {'≤' if cumple else '>'} máximo aceptado {perfil.maximum_payback_anos:.1f}"
            if valor is not None else
            f"El proyecto no recupera la inversión dentro del horizonte simulado — no cumple {perfil.nombre}"
        )
        criterios.append(CriterioBankability(
            "Payback simple", cumple, valor, perfil.maximum_payback_anos, mensaje
        ))

    if perfil.minimum_npv_usd is not None:
        valor = fin.npv_usd
        cumple = valor >= perfil.minimum_npv_usd
        mensaje = f"VPN USD {valor:,.0f} {'≥' if cumple else '<'} mínimo USD {perfil.minimum_npv_usd:,.0f}"
        criterios.append(CriterioBankability("NPV", cumple, valor, perfil.minimum_npv_usd, mensaje))

    if perfil.maximum_capex_usd is not None:
        cumple = capex_usd is not None and capex_usd <= perfil.maximum_capex_usd
        mensaje = (
            "CAPEX no fue provisto a evaluar_bankability() — no se puede verificar el tope"
            if capex_usd is None else
            f"CAPEX USD {capex_usd:,.0f} {'≤' if cumple else '>'} máximo USD {perfil.maximum_capex_usd:,.0f}"
        )
        criterios.append(CriterioBankability("CAPEX máximo", cumple, capex_usd, perfil.maximum_capex_usd, mensaje))

    if not criterios:
        estado: Estado = "SIN_CRITERIOS"
    elif all(c.cumple for c in criterios):
        estado = "PASS"
    else:
        estado = "FAIL"

    return BankabilityEvaluation(perfil=perfil.nombre, estado=estado, criterios=criterios)
