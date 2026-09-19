# Validación — Producción de energía

**Estado:** completado

## Checklist de validación del módulo

- [x] Pruebas de integración `03 → 04`: `49 passed` al ejecutar
	`test_pagina_produccion_diseno_vencido.py` y
	`test_compatibilidad_string.py`.
- [x] Diseño vencido bloquea la simulación y limpia resultados persistidos.
- [x] Firmas deterministas de Producción y bypass verificadas: `191 passed`
	  en pruebas focales, más `21/21` del script de persistencia.
- [x] Con Motor Óptico activo, Producción consume mismatch sin soiling para
	  evitar aplicarlo dos veces.
- [x] Restauración persistida rechaza resultados legacy o cuya firma no coincide.
- [x] Suite física adicional ejecutada en entorno reproducible: `38 passed`
	  (pérdida óhmica, balance de pérdidas PVsyst, coherencia térmica bypass).
- [x] Finanzas/Presupuesto: restauración protegida mediante verificación de
	  payload canónico (ver `06-analisis-financiero`), validada funcionalmente
	  en producción (pestaña nueva restaura con datos reales).

## Resultado

Módulo completado: vigencia de diseño eléctrico, firmas de Producción/bypass,
prevención de doble soiling y persistencia segura, todo verificado con pruebas
focales y físicas frescas, y validado funcionalmente en producción vía
`06-analisis-financiero`.
