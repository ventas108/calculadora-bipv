"""
Analista Técnico-Financiero — primer agente de la capa de IA (Fase 5).

Rol, deliberadamente acotado: leer resultados YA CALCULADOS por el motor
determinista (sensibilidad de Fase 4, candidatos evaluados, frente de
Pareto) y producir hallazgos priorizados en lenguaje natural. Nunca calcula
un número — solo los que ya existen en simulation/ y optimization/, o los
que obtiene llamando a la herramienta evaluar_bankability, que a su vez
llama a optimization.bankability.evaluar_bankability() real.

Por qué un solo agente y no los seis del plan original: optimization/
sensitivity.py ya calculó determinísticamente qué variable mueve qué
objetivo. Pedirle a un LLM que "diagnostique" lo que el motor ya
diagnosticó con números exactos sería un narrador redundante — o peor,
una fuente de alucinación sobre datos que ya son ciertos. Ver la
conversación de arquitectura donde se decidió esto.

Modelo: claude-opus-5 (default de Anthropic — no se baja de tier por
costo salvo que el usuario lo pida explícitamente).
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import anthropic
from anthropic import beta_tool

from simulation.schemas import FinancialResult
from optimization.numerical_optimizer import ResultadoCandidato
from optimization.bankability import evaluar_bankability as _evaluar_bankability_real
from optimization.investor_profile import PERFILES_PRESET

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """\
Eres el Analista Técnico-Financiero de una plataforma de optimización BIPV \
(paneles solares integrados en fachadas de edificios) en Colombia.

Reglas estrictas — no son sugerencias:
1. NUNCA inventes un número. Todo dato numérico que cites (kWh, PR, NPV, \
IRR, payback, LCOE, CAPEX) debe venir literalmente del contexto que te \
pasaron o de una herramienta que llamaste — nunca de tu conocimiento \
general ni de una estimación propia.
2. Para evaluar bancabilidad de un candidato contra un perfil de \
inversionista, usa SIEMPRE la herramienta evaluar_bankability — nunca \
la califiques de memoria. Perfiles disponibles: "Conservador", \
"Balanceado", "Crecimiento".
3. Tu trabajo es interpretar y priorizar, no calcular. El motor \
determinista ya hizo todos los cálculos; tu valor es explicar qué \
importa y por qué, en el orden correcto.
4. Si un dato no está disponible (por ejemplo IRR=None porque el flujo \
de caja no tiene solución real, o payback=None porque el proyecto no \
recupera la inversión en el horizonte simulado), dilo explícitamente — \
no lo omitas ni lo rellenes con una suposición.
5. Estructura tu respuesta así: (a) resumen ejecutivo de 2-3 líneas, \
(b) hallazgos técnicos priorizados (qué variable importa más y por qué, \
citando el número), (c) recomendación de candidato(s) con su \
evaluación de bancabilidad.
6. Responde en español.
"""


@dataclass
class CandidatoRegistrado:
    """Un candidato ya evaluado (Fase 4) que el agente puede consultar."""
    resultado: ResultadoCandidato
    fin: FinancialResult
    capex_usd: float


def _crear_herramienta_bankability(registro: dict[str, CandidatoRegistrado]):
    """
    Cierra sobre el registro de ESTA llamada a ejecutar_analisis() — sin
    estado global entre llamadas concurrentes.
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


def _formatear_sensibilidad(resultados_sensibilidad) -> str:
    lineas = ["## Sensibilidad (barrido uno-a-la-vez, Fase 4)", ""]
    for r in resultados_sensibilidad:
        impacto_e = r.impacto_absoluto.get("energia_anual")
        impacto_npv = r.impacto_absoluto.get("npv")
        partes = [f"- **{r.variable}**: {r.valor_bajo} → {r.valor_alto}"]
        if impacto_e is not None:
            partes.append(f"impacto energía={impacto_e:,.0f} kWh")
        if impacto_npv is not None:
            partes.append(f"impacto NPV=USD {impacto_npv:,.0f}")
        lineas.append(" | ".join(partes))
    return "\n".join(lineas)


def _formatear_candidatos(registro: dict[str, CandidatoRegistrado]) -> str:
    lineas = ["## Candidatos evaluados (frente de Pareto, Fase 4)", ""]
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


def ejecutar_analisis(
    resultados_sensibilidad,
    registro_candidatos: dict[str, CandidatoRegistrado],
    pregunta: str = "Analiza estos resultados y dame tus hallazgos priorizados.",
):
    """
    Corre el Analista Técnico-Financiero sobre resultados YA calculados.

    Retorna el último mensaje del tool runner (no solo el texto) para que
    el llamador pueda inspeccionar usage/tokens si lo necesita.
    """
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY desde el entorno

    contexto = (
        _formatear_sensibilidad(resultados_sensibilidad)
        + "\n\n"
        + _formatear_candidatos(registro_candidatos)
    )

    herramienta = _crear_herramienta_bankability(registro_candidatos)

    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[herramienta],
        messages=[{"role": "user", "content": f"{contexto}\n\n{pregunta}"}],
    )

    ultimo = None
    for mensaje in runner:
        ultimo = mensaje
    return ultimo


def texto_final(mensaje) -> str:
    return "".join(b.text for b in mensaje.content if b.type == "text")
