# Propuesta — El signo «$» no debe convertirse en fórmula

**Estado:** validación

## Objetivo

Que todo valor en pesos se lea como «$ 48,76 M COP», nunca como fórmula.

## Alternativa recomendada

Aprobada por el usuario el 28-sep-2026.

- Escapar el «$» («\$») en los cinco textos afectados; en 💼 Presupuesto los
  precios en dólares pasan a «USD».
- Prueba que recorre todas las páginas y falla si un texto markdown tiene dos
  «$» sin escapar.

## Fuera de alcance

- `st.metric` y tablas de datos (no interpretan markdown).
