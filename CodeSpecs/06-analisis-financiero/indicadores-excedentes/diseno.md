# Diseño — Indicadores de Financiero con la tarifa de excedentes

**Estado:** validación

## Entradas

- `e_financiero`, `frac_exportada`, `tarifa_cop`, `tarifa_excedentes_cop` de
  la página.
- `balance_metricas` de 🔋 Baterías y Balance: `E_solar_anual_kWh`,
  `E_autoconsumo_anual_kWh`, `E_bateria_total_kWh`.
- `_capex_bat_usd` (precio vigente del catálogo de baterías).

## Salidas

- `ahorro_anual_cop` → `{autoconsumo_kWh, exportada_kWh, ahorro_autoconsumo_cop, ingreso_excedentes_cop, total_cop}`.
- `hay_bateria` → `bool`.
- `escenario_sin_bateria` → `{energia_kWh, autoconsumo_kWh, exportada_kWh, frac_exportada}` o `None`.

## Tipos de datos

Números `float` en kWh/año y COP; `frac_exportada` entre 0 y 1.

## Errores posibles

- Datos vacíos, `None` o NaN: se tratan como 0 y el ahorro queda en 0.
- `frac_exportada` fuera de 0–1: se recorta.
- Balance sin `E_solar_anual_kWh`: `escenario_sin_bateria` devuelve `None` y
  la sección de batería no se muestra.

## Dependencias

`calculos/financiero.py` (`comparativo_ley_1715` con `frac_exportada` y
`tarifa_excedentes_cop_kWh`).

## Criterios de aceptación

1. «Ahorro energía año 1» = autoconsumo × tarifa + excedentes × tarifa de
   excedentes (7,05 M COP en el caso del cliente, no 7,39 M).
2. Sin batería no aparece «Impacto de la batería».
3. Con batería, el escenario sin batería usa el mismo sistema solar con su
   excedente a la tarifa de excedentes; sin batería su TIR sería igual a la
   del análisis.
4. «Autoconsumo extra» muestra la energía descargada por la batería (≥ 0),
   no la diferencia con la producción.
