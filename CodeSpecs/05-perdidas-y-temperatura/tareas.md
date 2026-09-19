# Tareas — Pérdidas y temperatura

**Estado:** completado

- [x] Inventariar POA completa, POA sin térmico y consumidores SDM.
- [x] Documentar la regla de una sola aplicación térmica.
- [x] Documentar invalidación downstream al recalcular Motor Óptico.
- [x] Ejecutar pruebas focales térmicas e invalidación en un entorno compatible:
	  `test_mismatch_bypass_termico.py` (`5 passed`, dentro del batch de `38 passed`).
- [x] Confirmar integración con Producción y sus resultados persistidos: cubierto
	  por evidencia automática (`exigir_poa_sin_termico`,
	  `invalidar_downstream_motor_optico`) en `test_seleccion_poa_bypass_pagina5.py`.
