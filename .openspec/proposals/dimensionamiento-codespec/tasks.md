# Tasks: CodeSpec del módulo Dimensionamiento

## Revisión del contrato

- [x] Localizar la página y la lógica pura del módulo.
- [x] Inventariar entradas de catálogo, clima, proyecto, cadenas, batería y Motor IV.
- [x] Inventariar salidas de compatibilidad, diseño confirmado y totales del proyecto.
- [x] Identificar consumidores downstream y la frontera `diseno_electrico_confirmado()`.

## Validación

- [x] Ejecutar las pruebas focales del módulo en el venv del proyecto: compatibilidad eléctrica, validación VBA, temperaturas por ciudad, compatibilidad con batería y pipeline de simulación; salida del comando: código 0.
- [ ] Añadir pruebas directas de invariantes de diseño confirmado si falta cobertura.
- [ ] Confirmar que cambiar panel/inversor no deja vigentes los totales del diseño anterior.
- [ ] Confirmar que el flujo de prorrateo preliminar se invalida al cambiar N total o strings/tracker.
- [ ] Confirmar que un catálogo incompleto se marca como no evaluable sin producir una recomendación falsa.

## Implementación posterior

- [ ] Convertir la CodeSpec en contrato visible para agentes y documentación del módulo.
- [ ] Extraer funciones puras adicionales solo si reduce duplicación sin cambiar las claves públicas.
- [ ] Mantener el alcance de UI separado de la fuente de verdad eléctrica.
- [ ] Actualizar `status` a `validated` solo con evidencia de pruebas fresca.