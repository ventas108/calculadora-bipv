# Validación — Producción de energía

**Estado:** en validación

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
- [ ] Implementar reconstrucción de firma esperada en Finanzas y Presupuesto
	  antes de reactivar restauración automática en una pestaña nueva.
- [ ] Ejecutar una suite física amplia en entorno reproducible con `pvlib`.

## Resultado

La vigencia de Producción, bypass y persistencia está validada localmente. La
restauración automática en Finanzas y Presupuesto queda bloqueada de forma
segura hasta que esos consumidores reconstruyan la firma esperada de la corrida;
el módulo permanece en validación por esa integración y por pruebas físicas
pendientes en un entorno reproducible.
