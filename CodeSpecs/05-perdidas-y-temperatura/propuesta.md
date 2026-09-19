# Propuesta — Pérdidas y temperatura

**Estado:** en validación

## Objetivo

Formalizar la fuente única de POA y temperatura para Motor Óptico, bypass y
Producción, evitando doble conteo térmico y resultados persistidos obsoletos.

## Alternativas consideradas

1. Entregar a Producción la POA efectiva completa, incluido el término térmico.
2. Entregar la POA sin térmico y aplicar el efecto térmico una sola vez en el
	SDM mediante `T_cell(k_BIPV)`.
3. Mantener resultados downstream cuando se recalcula la cascada óptica.

## Alternativa recomendada

Adoptar la alternativa 2 e invalidar la alternativa 3: con Motor Óptico activo,
solo `poa_sin_termico_df` es una entrada válida para el SDM; al recalcular la
cascada se eliminan los resultados downstream que dependían de la POA anterior.
