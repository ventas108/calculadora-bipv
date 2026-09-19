# Implementación — Pérdidas y temperatura

**Estado:** completado

## Cambios realizados

- Motor Óptico publica por separado `poa_efectiva_df` y
	`poa_sin_termico_df`; esta última alimenta el SDM.
- `exigir_poa_sin_termico()` bloquea estados ópticos inconsistentes sin
	fallback a POA efectiva o bruta.
- La invalidación central elimina resultados dependientes de la POA reemplazada
	y conserva el estado multi-superficie independiente.

## Archivos modificados

- `bipv_python/pages/5b_🔆_Motor_Optico.py`
- `bipv_python/calculos/mismatch_bypass.py`
- `bipv_python/calculos/invalidacion.py`
- `bipv_python/tests/test_mismatch_bypass_termico.py`
- `bipv_python/tests/test_seleccion_poa_bypass_pagina5.py`
