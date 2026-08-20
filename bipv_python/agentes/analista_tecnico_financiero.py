"""
Analista Técnico-Financiero — primer agente de la capa de IA (Fase 5).

Rol, deliberadamente acotado: leer resultados YA CALCULADOS por el motor
determinista (sensibilidad de Fase 4, candidatos evaluados, frente de
Pareto) y producir hallazgos priorizados en lenguaje natural. Nunca calcula
un número — solo los que ya existen en simulation/ y optimization/, o los
que obtiene llamando a la herramienta evaluar_bankability compartida
(agentes/herramientas.py), que a su vez llama a
optimization.bankability.evaluar_bankability() real.

Por qué un solo agente y no los seis del plan original: optimization/
sensitivity.py ya calcula determinísticamente qué variable mueve qué
objetivo. Pedirle a un LLM que "diagnostique" lo que el motor ya
diagnosticó con números exactos sería un narrador redundante — o peor,
una fuente de alucinación sobre datos que ya son ciertos.

Diferencia con el Asesor de Inversión (agentes/asesor_inversion.py): este
agente prioriza HALLAZGOS técnicos para quien va a iterar el diseño; el
Asesor prioriza una DECISIÓN para quien va a poner el dinero. Comparten
la misma herramienta de bancabilidad para no divergir en cómo se evalúa
"bancable".

Modelo: claude-opus-5 (default de Anthropic — no se baja de tier por
costo salvo que el usuario lo pida explícitamente).
"""
from __future__ import annotations

import anthropic

from agentes.herramientas import (
    CandidatoRegistrado,
    crear_herramienta_bankability,
    formatear_candidatos,
)

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """\
Eres el Analista Técnico-Financiero de una plataforma colombiana de \
optimización de sistemas fotovoltaicos. La plataforma cubre BIPV integrado \
en edificios (fachada, techo inclinado, techo plano, pérgola, marquesina) \
Y TAMBIÉN granjas fotovoltaicas de suelo -- no asumas fachada por defecto.

Reglas estrictas — no son sugerencias:
0. El tipo de instalación REAL del proyecto viene declarado explícitamente \
en el contexto que te pasaron (p.ej. "Granja fotovoltaica", "Fachada \
BIPV"). Usa ESE tipo en tu lenguaje y tus supuestos -- nunca asumas \
"fachada" ni "edificio" si el contexto dice otra cosa. Si el contexto no \
declara el tipo, dilo explícitamente en vez de asumir uno.
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
        + formatear_candidatos(registro_candidatos, titulo="Candidatos evaluados (frente de Pareto, Fase 4)")
    )

    herramienta = crear_herramienta_bankability(registro_candidatos)

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
