# Diseño — Resumen coherente de Financiero

**Estado:** validación

## Entradas

- `st.session_state` (`tarifa_excedentes_cop_kWh`), `tarifa_cop_kwh`,
  `e_financiero`, `frac_exportada`.
- Paybacks de `m_con`, `m_p90`, `m_sin` (años o `None`).

## Salidas

- `tarifa_excedentes_vigente` → `float` COP/kWh.
- `etiquetas_payback` → lista de `{texto, x, y, color}` (`y` en fracción de la
  gráfica, 0,98 y bajando 0,08 por etiqueta).

## Tipos de datos

Números `float`; textos `str`.

## Errores posibles

- Tarifa guardada no numérica, NaN o negativa: se usa la de compra.
- Payback `None` o 0: la etiqueta se omite.

## Dependencias

`calculos/indicadores_excedentes.ahorro_anual_cop` (sin cambios).

## Criterios de aceptación

1. «Ahorro estimado» × 12 = «Ahorro energía año 1» (6,85 M en el caso cliente).
2. Sin exportación, la tarjeta usa solo la tarifa de compra.
3. Todos los rótulos P90 muestran el factor con un decimal (−9,5 %).
4. Las etiquetas de payback nunca comparten altura y quedan ordenadas por año.
