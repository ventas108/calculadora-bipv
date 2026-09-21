# Validación — Persistencia multi-superficie

**Estado:** pendiente

## Pruebas unitarias obligatorias

- [x] Payload válido produce JSON determinista y firma estable.
- [x] Restauración válida recupera superficies, asignaciones, resultados `multisup_*` permitidos y el snapshot físico adoptado con resultados DC/AC.
- [x] DataFrame/Series/arrays se serializan en formato canónico etiquetado y se reconstruyen.
- [x] Payload alterado es rechazado.
- [x] Firma global alterada es rechazada.
- [x] Firma de sombra alterada es rechazada durante la validación contextual.
- [x] Firma de POA alterada es rechazada durante la validación contextual.
- [x] TMY cambiado es rechazado.
- [x] Geometría, tilt o azimuth cambiados son rechazados.
- [x] Inversor, asignación, `N_serie` o `N_paralelo` cambiados son rechazados cuando el contexto actual los proporciona.
- [x] Superficie eliminada o inversor inexistente es rechazado.
- [ ] Payload incompleto y schema no soportado son rechazados.
- [x] Firma global alterada deja `session_state` idéntico al snapshot previo.
- [x] Restauración rechazada no escribe ninguna clave `multisup_*`.
- [ ] Resultados rechazados no llegan a Finanzas, CO₂, Presupuesto, Baterías ni Reporte.
- [x] Modelo simplificado permanece intacto sin multi-superficie, según la regresión de los consumidores existentes.

## Validación de integración

- [x] Guardar proyecto produce payload canónico y escritura atómica por usuario.
- [x] Cargar proyecto valida antes de publicar cualquier estado y difiere la restauración física hasta disponer de TMY.
- [ ] Dos superficies con sombra, POA e inversores válidos restauran completas en prueba manual real.
- [x] Se conserva el comportamiento opt-in del modo físico.
- [x] Comparación global sigue siendo exploratoria y su adopción continúa bloqueada en `multisup_activo=True`.

## Validación operativa manual

1. Crear dos superficies.
2. Configurar inversores y asignaciones.
3. Calcular sombra y POA.
4. Calcular y adoptar el resultado físico.
5. Guardar el proyecto.
6. Cerrar sesión o reiniciar la pestaña.
7. Cargar el proyecto y confirmar restauración completa.
8. Alterar una firma.
9. Confirmar rechazo completo sin alimentar módulos downstream.

## Gate de publicación

No se considera completada la Spec hasta que pasen las pruebas focales, la regresión, la revisión humana, el commit en GitHub `main` y la verificación del mismo commit en DigitalOcean.
