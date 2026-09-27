# Implementación — Indicadores de Financiero con la tarifa de excedentes

**Estado:** validación

## Cambios realizados

- `calculos/indicadores_excedentes.py` (nuevo): `ahorro_anual_cop`,
  `hay_bateria`, `escenario_sin_bateria`.
- `pages/7_💰_Financiero.py`:
  - «Ahorro energía año 1» usa `ahorro_anual_cop` y explica el cálculo en la
    ayuda de la métrica.
  - «Impacto de la batería» solo aparece con batería. Su escenario sin
    batería pasa a `comparativo_ley_1715` la energía y la `frac_exportada`
    de `escenario_sin_bateria`, con `tarifa_excedentes_cop_kWh`.
  - El texto y la métrica «Autoconsumo extra» usan la energía que la batería
    desplaza de excedente a autoconsumo.

- Complemento (26-sep-2026): `aviso_sobredimension` y `desglose_capex` en
  `calculos/indicadores_excedentes.py`; la página muestra el aviso en «Consumo
  vs Producción» y antes del botón Calcular, y la tarjeta «Imprevistos (x %)»
  (u «Otros (Presupuesto)»).

## Archivos modificados

- `bipv_python/calculos/indicadores_excedentes.py`
- `bipv_python/pages/7_💰_Financiero.py`
- `bipv_python/tests/test_indicadores_excedentes.py`
- `bipv_python/tests/test_sincronizacion_consumo_y_excedentes.py`
- `bipv_python/tests/test_asistente_retrieval.py`
- `bipv_python/datos/conocimiento_bipv.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
