"""
Herramientas compartidas entre agentes de la Fase 5.

Un solo lugar donde se envuelve optimization.bankability.evaluar_bankability()
como herramienta de Anthropic — evita que cada agente reimplemente su propio
wrapper y terminen divergiendo con el tiempo. Es el mismo principio aplicado
en todo este proyecto: una sola fuente de verdad por cálculo, la IA solo
la invoca.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from anthropic import beta_tool

from simulation.schemas import FinancialResult
from optimization.numerical_optimizer import ResultadoCandidato
from optimization.bankability import evaluar_bankability as _evaluar_bankability_real
from optimization.investor_profile import PERFILES_PRESET


@dataclass
class CandidatoRegistrado:
    """Un candidato ya evaluado (Fase 4) que un agente puede consultar."""
    resultado: ResultadoCandidato
    fin: FinancialResult
    capex_usd: float


def crear_herramienta_bankability(registro: dict[str, CandidatoRegistrado]):
    """
    Cierra sobre el registro de ESTA llamada — sin estado global compartido
    entre agentes o entre ejecuciones concurrentes.
    """

    @beta_tool
    def evaluar_bankability(candidato_id: str, perfil: str) -> str:
        """Evalúa la bancabilidad de un candidato ya simulado contra un perfil de inversionista.

        Args:
            candidato_id: ID del candidato tal como aparece en el resumen (p.ej. "C3").
            perfil: uno de "Conservador", "Balanceado", "Crecimiento".
        """
        if candidato_id not in registro:
            return json.dumps({
                "error": f"candidato_id '{candidato_id}' no existe.",
                "disponibles": list(registro.keys()),
            }, ensure_ascii=False)
        if perfil not in PERFILES_PRESET:
            return json.dumps({
                "error": f"perfil '{perfil}' no existe.",
                "disponibles": list(PERFILES_PRESET.keys()),
            }, ensure_ascii=False)

        c = registro[candidato_id]
        evaluacion = _evaluar_bankability_real(
            c.fin, PERFILES_PRESET[perfil], capex_usd=c.capex_usd,
        )

        return json.dumps({
            "candidato_id": candidato_id,
            "perfil": perfil,
            "estado": evaluacion.estado,
            "criterios": [
                {
                    "nombre": crit.nombre, "cumple": crit.cumple,
                    "valor": crit.valor, "umbral": crit.umbral,
                    "mensaje": crit.mensaje,
                }
                for crit in evaluacion.criterios
            ],
            "dimensiones_no_evaluadas": list(evaluacion.dimensiones_no_evaluadas),
        }, ensure_ascii=False)

    return evaluar_bankability


def formatear_candidatos(registro: dict[str, CandidatoRegistrado], titulo: str = "Candidatos evaluados") -> str:
    lineas = [f"## {titulo}", ""]
    for cid, c in registro.items():
        obj = c.resultado.objetivos
        cfg = c.resultado.config
        irr = f"{obj['irr']:.1f}%" if obj.get("irr") is not None else "None (sin solución real)"
        payback = f"{obj['payback_simple']:.1f} años" if obj.get("payback_simple") is not None else "None"
        lineas.append(
            f"- **{cid}**: tilt={cfg.tilt:.1f}° azimuth={cfg.azimuth:.1f}° | "
            f"energía={obj['energia_anual']:,.0f} kWh, PR={obj['pr']:.3f} | "
            f"CAPEX=USD {c.capex_usd:,.0f}, NPV=USD {obj['npv']:,.0f}, "
            f"IRR={irr}, payback={payback}"
        )
    return "\n".join(lineas)
