# Propuesta — Motor Óptico: NOCT y γ coherentes con la ficha del panel

**Estado:** validación

## Objetivo

Que un NOCT o γ del Motor Óptico distinto de la ficha del panel nunca pase
en silencio a la energía, y que volver a la ficha sea un clic.

## Alternativa recomendada

Aprobada por el usuario el 30-sep-2026 («si prepara la Spec con su PR»).

- `calculos/motor_optico_ficha.py` (nuevo): `ficha_termica(panel)` (NOCT y γ
  con la misma prioridad que el modelo del panel: `Tk_gamma`, `gamma_mp`,
  `beta_mp`), `diferencias_ficha(noct, γ, panel)` (tolerancia 0,5 °C y
  0,005 %/°C; marca que el NOCT afecta la energía y el γ no) y
  `texto_aviso_ficha(...)` con el efecto en grados: (NOCT motor − NOCT
  ficha) ÷ 800 × 1000 × k.
- 🔆 Motor Óptico: aviso 🟠 y botón **«↩️ Usar los de la ficha»** (pone NOCT
  y γ de la ficha dentro del rango de los campos); el auto-llenado usa
  `ficha_termica`.
- 📊 Producción: el mismo aviso 🟠 antes de simular cuando el NOCT o el γ del
  Motor Óptico no son los de la ficha.
- Manual del Asistente, sección 92, con el caso Apartadó y el recordatorio
  del montaje (k).

## Alternativas descartadas

- Pisar siempre con la ficha al abrir el proyecto: borraría un NOCT medido a
  propósito.
- Que Producción use siempre el NOCT de la ficha: rompería la coherencia con
  la cascada óptica, que usa el del Motor Óptico.

## Fuera de alcance

- El montaje (k) sigue siendo una elección del usuario; el manual explica la
  equivalencia con Uc.
