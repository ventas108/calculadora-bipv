# Validación — Dimensionamiento eléctrico

**Estado:** completado

## Checklist de validación del módulo

- [x] Evidencia estática: el diseño downstream se resuelve mediante
	`diseno_electrico_confirmado()` y usa `N_str_tr_usado` confirmado.
- [x] Evidencia estática: el prorrateo descarta resultados al cambiar panel,
	inversor o `N_str_tr` efectivo.
- [x] Evidencia estática: las fichas incompletas se devuelven como `No evaluable`.
- [x] `python -m pytest tests/test_compatibilidad_string.py`: `46 passed` en
	0.60 s (Python 3.14.2, pytest 9.1.1).
- [x] Integración con Producción: la simulación usa
	`diseno_electrico_confirmado()` y bloquea, limpia resultados y detiene la
	ejecución si el diseño confirmado no está vigente.

## Resultado

Validación completada: el contrato interno y la integración `03 → 04` están
cubiertos por `49 passed` en 0.70 s (Python 3.14.2, pytest 9.1.1), al ejecutar
`test_compatibilidad_string.py` y `test_pagina_produccion_diseno_vencido.py`.
