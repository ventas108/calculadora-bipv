# Tareas — Dimensionamiento eléctrico

**Estado:** completado

- [x] Inventariar entradas, salidas y consumidores del módulo.
- [x] Centralizar el diseño consumible en `diseno_electrico_confirmado()`.
- [x] Invalidar prorrateo preliminar ante cambios de selección o de strings por
	tracker efectivo.
- [x] Marcar fichas incompletas o no finitas como `No evaluable`.
- [x] Ejecutar de nuevo la prueba focal del módulo en el entorno actual:
	`46 passed` con Python 3.14.2 y pytest 9.1.1.
- [x] Validar la integración con Producción: la simulación consume el diseño
	confirmado y bloquea resultados cuando su vigencia es falsa.
