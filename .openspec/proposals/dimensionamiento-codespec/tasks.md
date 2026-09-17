# Tasks: CodeSpec del módulo Dimensionamiento

## Revisión del contrato

- [x] Localizar la página y la lógica pura del módulo.
- [x] Inventariar entradas de catálogo, clima, proyecto, cadenas, batería y Motor IV.
- [x] Inventariar salidas de compatibilidad, diseño confirmado y totales del proyecto.
- [x] Identificar consumidores downstream y la frontera `diseno_electrico_confirmado()`.

## Validación

- [x] Ejecutar las pruebas focales del módulo en el venv del proyecto: compatibilidad eléctrica, validación VBA, temperaturas por ciudad, compatibilidad con batería y pipeline de simulación; salida del comando: código 0.
- [x] Confirmar cobertura directa de invariantes de diseño confirmado: `test_compatibilidad_string.py` cubre `N_str_tr_usado`, ausencia de diseño, referencias históricas y cambios de panel/inversor.
- [x] Confirmar que cambiar panel/inversor invalida la vigencia del diseño confirmado: `test_diseno_confirmado_avisa_si_panel_cambio_sin_reconfirmar` y `test_diseno_confirmado_avisa_si_inversor_cambio_sin_reconfirmar`.
- [ ] Confirmar que el flujo de prorrateo preliminar se invalida al cambiar N total o strings/tracker.
- [ ] Confirmar que un catálogo incompleto se marca como no evaluable sin producir una recomendación falsa.

## Implementación posterior

- [ ] Convertir la CodeSpec en contrato visible para agentes y documentación del módulo.
- [ ] Extraer funciones puras adicionales solo si reduce duplicación sin cambiar las claves públicas.
- [ ] Mantener el alcance de UI separado de la fuente de verdad eléctrica.
- [ ] Actualizar `status` a `validated` solo con evidencia de pruebas fresca.