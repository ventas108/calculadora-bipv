# Propuesta — Resumen coherente de Financiero

**Estado:** validación

## Objetivo

Que cada número de la página diga lo mismo que el flujo de caja.

## Alternativas consideradas

1. **Quitar la tarjeta «Ahorro estimado».** Descartada: el usuario la usa
   para ver el ahorro mensual antes de calcular.
2. **Calcular la tarjeta con `ahorro_anual_cop`**, con la tarifa de excedentes
   guardada (el campo se dibuja más abajo). Recomendada.
3. **Etiquetas en la leyenda en vez de la gráfica.** Descartada: se pierde la
   lectura directa del año de recuperación.

## Alternativa recomendada

- `indicadores_excedentes.tarifa_excedentes_vigente(estado, tarifa, frac)`:
  la tarifa guardada si hay exportación; si no, la de compra (misma regla que
  el campo).
- La tarjeta usa `ahorro_anual_cop(e_financiero, frac_exportada, …)`.
- Todos los rótulos P90 con un decimal.
- `lectura_financiera.etiquetas_payback`: ordena por año y baja cada etiqueta
  una fila; la página dibuja la línea y la etiqueta a la derecha.

## Fuera de alcance

- Cambiar las fórmulas de ahorro, P90 o payback.
