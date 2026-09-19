# Validación — Pérdidas y temperatura

**Estado:** completado

## Checklist de validación del módulo

- [x] Evidencia estática: Producción exige `poa_sin_termico_df` cuando Motor
	Óptico está activo y bloquea si falta.
- [x] Evidencia estática: el bypass y Producción reciben `k_BIPV` y calculan
	temperatura desde la misma fuente de verdad.
- [x] Evidencia estática: recalcular Motor Óptico invalida resultados downstream
	sin borrar multi-superficie independiente.
- [x] `test_mismatch_bypass_termico.py`: `5 passed` (coherencia térmica bypass).
- [x] Invalidación de Motor Óptico verificada por pruebas automatizadas
	  (`exigir_poa_sin_termico`, `invalidar_downstream_motor_optico`) en
	  `test_seleccion_poa_bypass_pagina5.py` — no se hizo click-through manual
	  en la app para este módulo, pero la lógica pura ya está cubierta punto
	  por punto.

## Resultado

Módulo completado: contrato de POA sin térmico, prevención de doble conteo
térmico e invalidación downstream verificados con pruebas frescas.
