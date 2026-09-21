# Tareas — Persistencia multi-superficie

**Estado:** pendiente de implementación

- [ ] Revisar y aprobar el contrato de `diseno.md`.
- [x] Inventariar las claves reales de Guardar/Cargar proyecto y definir el adaptador de entrada/salida.
- [x] Implementar serialización canónica de DataFrames/series y rechazo de objetos no serializables.
- [x] Implementar `construir_payload_multisuperficie`.
- [x] Implementar `firmar_payload_multisuperficie`.
- [x] Implementar validación de schema, campos obligatorios y firma global.
- [x] Implementar validación de TMY, geometría, tilt, azimuth, sombra, POA y configuración eléctrica cuando el contexto actual está disponible.
- [x] Implementar restauración todo-o-nada sin mutación parcial, incluyendo el snapshot físico adoptado y sus resultados DC/AC etiquetados.
- [x] Conectar Guardar proyecto con escritura atómica por usuario y sección `multisuperficie` firmada.
- [x] Conectar Cargar proyecto con validación estructural y restauración diferida hasta disponer de TMY.
- [ ] Rechazar explícitamente payload incompleto, alterado, legacy o de versión no soportada.
- [x] Añadir pruebas unitarias de payload, firmas, serialización y rollback; la batería focal actual es de 26 pruebas.
- [ ] Añadir pruebas de consumidores: Finanzas, CO₂, Presupuesto, Baterías y Reporte no consumen estado invalidado.
- [ ] Verificar que el modelo simplificado no cambia cuando `multisup_activo` es falso.
- [ ] Actualizar contratos, mapa de dependencias, registro de decisiones y base del Asistente.
- [ ] Ejecutar revisión solo lectura de Copilot y revisión de Claude según su Spec.
- [ ] Crear rama, validar, publicar, fusionar a `main` y desplegar con hashes alineados.
