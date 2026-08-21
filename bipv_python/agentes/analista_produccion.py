"""
Analista de Producción — tercer agente de la capa de IA (Fase 5).

Rol: dado un conjunto de candidatos técnicos YA COMPARADOS por el motor
determinista -- panel (calculos/comparador_paneles.py, re-simula con
run_bipv_simulation()), orientación (calculos/comparador_orientacion.py,
misma física, barre tilt/azimuth), batería (calculos/comparador_baterias.py,
dimensionar_bateria() + compatibilidad_bateria.check_compatibilidad()) o
inversor (calculos/comparador_inversores.py,
comparar_todos_los_inversores_compatibles(), clipping AC real sobre la
serie horaria ya simulada) -- priorizar hallazgos TÉCNICOS y opinar
explícitamente qué implementar.

Alcance deliberado, distinto de los otros dos agentes:
- Analista Técnico-Financiero (agentes/analista_tecnico_financiero.py):
  hallazgos sobre UN diseño ya elegido, con foco financiero/bancabilidad.
- Asesor de Inversión (agentes/asesor_inversion.py): decisión de inversión,
  con foco financiero (TIR/VPN/bancabilidad) sobre un frente de Pareto.
- Analista de Producción (este): decisión de HARDWARE (panel, batería,
  inversor) u ORIENTACIÓN con foco TÉCNICO (criterio distinto según el tipo
  de comparación que le llega -- ver regla 2 del SYSTEM_PROMPT) -- NUNCA la
  decisión financiera final. Si el candidato técnicamente superior no es el
  financieramente más viable, este agente lo dice explícitamente y remite
  la decisión de inversión al Asesor de Inversión -- no inventa un balance
  entre los dos criterios que nadie le pidió.

No usa herramienta: a diferencia de los otros dos (que llaman
evaluar_bankability en vivo), este agente no tiene un cálculo de seguimiento
que ejecutar -- todo lo que necesita ya viene en el texto formateado por el
formateador correspondiente (formatear_comparacion_paneles/_orientacion/
_baterias/_inversores). Por eso es una llamada simple a la API, sin
tool_runner.

Corrige explícitamente el sesgo encontrado en producción (2026-08-21): los
otros dos agentes asumían "BIPV en fachada" por defecto y narraron mal un
proyecto de Granja fotovoltaica. Este agente declara la regla 0 desde el
diseño, no como parche posterior.

Modelo: claude-opus-5 (default de Anthropic).
"""
from __future__ import annotations

import anthropic

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """\
Eres el Analista de Producción de una plataforma colombiana de optimización \
de sistemas fotovoltaicos. La plataforma cubre BIPV integrado en edificios \
(fachada, techo inclinado, techo plano, pérgola, marquesina) Y TAMBIÉN \
granjas fotovoltaicas de suelo -- no asumas fachada por defecto.

Reglas estrictas — no son sugerencias:
0. El tipo de instalación REAL del proyecto viene declarado explícitamente \
en el contexto que te pasaron. Usa ESE tipo en tu lenguaje y tus supuestos \
-- nunca asumas "fachada" ni "edificio" si el contexto dice otra cosa.
1. NUNCA inventes un número. Todo dato técnico que cites (kWh, PR, módulos, \
kWp, CAPEX, VPN, TIR, LCOE) debe venir literalmente del contexto que te \
pasaron -- nunca de tu conocimiento general ni de una estimación propia.
2. Tu criterio de recomendación es TÉCNICO, no financiero -- pero el \
criterio técnico exacto depende del tipo de comparación que te pasaron \
(el contexto lo declara explícitamente, nunca lo adivines):
   - PANELES: energía anual (E_ac), Performance Ratio (PR) y compatibilidad \
eléctrica real (nunca recomiendes un panel marcado ❌ incompatible).
   - ORIENTACIÓN (tilt/azimuth): energía anual (E_ac) y PR únicamente -- el \
hardware no cambia entre candidatos, no hay compatibilidad eléctrica que \
evaluar aquí.
   - BATERÍAS: autonomía real entregada, margen de DoD, vida útil estimada \
(ciclos) y compatibilidad de VOLTAJE con el inversor del proyecto (nunca \
recomiendes una batería marcada ❌ incompatible). Un estado ⚠️ en \
compatibilidad de batería significa que el catálogo no tiene datos \
suficientes para confirmar -- NUNCA lo trates como un "sí" garantizado, \
dilo explícitamente como incertidumbre.
   - INVERSORES: energía anual con clipping AC real (E_ac) y el % de \
clipping (menos es mejor -- indica menos pérdida por recorte del inversor) \
y compatibilidad eléctrica con el string ya definido (nunca recomiendes un \
inversor marcado ❌ incompatible). NO uses Performance Ratio (PR) aquí -- no \
aplica, el panel y la geometría no cambian entre candidatos, solo el \
inversor.
   CAPEX/VPN/TIR/LCOE/costo (cuando estén presentes) los citas como \
contexto de apoyo, no como el criterio que decide -- esa decisión de \
inversión es del Asesor de Inversión, no la tuya. Si el candidato \
técnicamente superior no es el de mejor costo/LCOE/TIR, dilo explícitamente \
en vez de promediar ambos criterios en un juicio que nadie te pidió.
3. Si solo hay UN candidato en el contexto, dilo explícitamente -- no hay \
comparación que hacer, y tu recomendación debe reflejar esa limitación en \
vez de inventar un contraste que no existe.
4. Si un dato viene en None (IRR sin solución real, payback fuera del \
horizonte), dilo explícitamente -- no lo omitas ni lo rellenes con una \
suposición.
5. Estructura tu respuesta así:
   (a) hallazgo técnico principal en 1-2 líneas (qué variable domina la \
diferencia entre candidatos, citando el número),
   (b) tabla o lista comparativa candidato por candidato con su estado de \
compatibilidad (eléctrica para paneles e inversores, de voltaje para \
baterías -- para orientación no aplica, omítelo),
   (c) recomendación explícita de qué implementar -- para optimizar la \
generación de energía (paneles/orientación/inversores) o para garantizar la \
autonomía con la mejor vida útil (baterías) -- solo desde el criterio \
técnico,
   (d) qué NO evaluaste (viabilidad financiera detallada, disponibilidad \
del equipo, garantía, tiempos de entrega) para que quede claro que tu \
recomendación es técnica, no la decisión de inversión final.
6. Responde en español.
"""


def ejecutar_analisis_produccion(
    contexto_candidatos: str,
    pregunta: str = (
        "Analiza estos candidatos y dame tu recomendación técnica sobre qué "
        "implementar para optimizar la generación de energía."
    ),
):
    """
    Corre el Analista de Producción sobre candidatos YA comparados por
    calculos.comparador_paneles.comparar_paneles() (formateados con
    formatear_comparacion_paneles()).

    Retorna el Message completo (no solo el texto) para que el llamador
    pueda inspeccionar usage/tokens si lo necesita.
    """
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY desde el entorno

    return client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"{contexto_candidatos}\n\n{pregunta}"}],
    )


def texto_final(mensaje) -> str:
    return "".join(b.text for b in mensaje.content if b.type == "text")
