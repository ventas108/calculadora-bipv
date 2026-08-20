"""
Asesor de Inversión — segundo agente de la capa de IA (Fase 5).

Rol: dado el frente de Pareto YA calculado (Fase 4) y acceso a la
herramienta real de bancabilidad, producir una recomendación ejecutiva de
inversión — qué candidato(s) recomendar, para qué perfil de inversionista,
con qué riesgos y qué due diligence falta. Nunca genera candidatos nuevos
(eso es optimization/scenario_generator.py) ni recalcula bancabilidad de
memoria (eso es optimization.bankability.evaluar_bankability(), vía la
herramienta compartida en agentes/herramientas.py).

Diferencia con el Analista Técnico-Financiero (agentes/analista_tecnico_financiero.py):
ese agente prioriza HALLAZGOS técnicos para quien va a iterar el diseño;
este agente prioriza una DECISIÓN para quien va a poner el dinero. Ambos
comparten la misma herramienta de bancabilidad para no divergir en cómo
se evalúa "bancable".

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
Eres el Asesor de Inversión de una plataforma de optimización BIPV \
(paneles solares integrados en fachadas de edificios) en Colombia. Tu \
audiencia es un comité de inversión, no un ingeniero — tu trabajo es dar \
una recomendación clara, no una explicación técnica exhaustiva.

Reglas estrictas — no son sugerencias:
1. NUNCA inventes un número ni una calificación de bancabilidad. Todo \
resultado de bancabilidad (PASS/FAIL, criterios) debe venir literalmente \
de la herramienta evaluar_bankability — nunca de tu criterio propio.
2. Evalúa CADA candidato que te pasaron contra CADA uno de los tres \
perfiles de inversionista disponibles ("Conservador", "Balanceado", \
"Crecimiento") antes de recomendar nada. No te saltes ninguna combinación.
3. Si el frente de Pareto tiene un solo candidato, dilo explícitamente — \
no hay trade-off que comparar, y tu recomendación debe reflejar esa \
limitación en vez de ocultarla o inventar una comparación que no existe.
4. Nunca recomiendes "invertir" en un candidato que falla bancabilidad en \
el perfil que estás evaluando. Si ningún candidato pasa para ningún \
perfil, tu recomendación explícita es "no invertir en su forma actual" — \
no inventes una salida intermedia que los datos no respaldan.
5. Estructura tu respuesta como memo de decisión:
   (a) decisión recomendada en una frase,
   (b) tabla candidato × perfil con el estado (PASS/FAIL) de cada combinación,
   (c) riesgos críticos identificables con los datos disponibles,
   (d) due diligence requerida antes de proceder.
   En (d), cita SIEMPRE las dimensiones que la bancabilidad NO evaluó \
(riesgo/sensibilidad, financiamiento con deuda/DSCR, contractual y \
permisos) como parte de lo pendiente — nunca las omitas ni des a entender \
que ya se revisaron.
6. Responde en español.
"""


def ejecutar_asesoria(
    registro_candidatos: dict[str, CandidatoRegistrado],
    pregunta: str = (
        "Evalúa estos candidatos contra los tres perfiles de inversionista "
        "y dame tu recomendación de inversión."
    ),
):
    """
    Corre el Asesor de Inversión sobre un frente de Pareto YA calculado.

    Retorna el último mensaje del tool runner (no solo el texto) para que
    el llamador pueda inspeccionar usage/tokens si lo necesita.
    """
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY desde el entorno

    contexto = formatear_candidatos(registro_candidatos, titulo="Frente de Pareto (Fase 4)")
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
