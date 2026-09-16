# Tasks: Contrato del CSV de Factor de Sombreado entre apps hermanas

## Análisis (completado)

- [x] Identificar módulo consumidor real del CSV (`mismatch_bypass.py::cargar_csv_fs()`).
- [x] Identificar módulos que propagan el resultado derivado (`factor_sombra_anual`): Producción, Financiero, Motor Óptico, Vista 3D, Reporte PDF.
- [x] Confirmar arquitectura de 3 capas (client React → server proxy → Motor Solar Python) y descartar que Node calcule física.
- [x] Extraer formato de columnas obligatorias/opcionales directamente del parser (`cargar_csv_fs`).
- [x] Extraer reglas de rechazo y advertencias ya documentadas (`base_conocimiento_asistente.md`, Anexos 56-57).
- [x] Redactar borrador centralizado (`CONTRATO_CSV_SOMBREADO_ENTRE_APPS.md`).

## Validación (pendiente)

- [x] Auditar `client/` y localizar el exportador real: `client/src/components/ShadingCalculator.tsx` contiene los dos botones oficiales del Motor Solar Python.
- [x] Identificar `FS_geometrico_motor_python.csv` y `FS_geometrico_promediado_motor_python.csv` en `ShadingCalculator.tsx`.
- [x] Localizar la conversión UTC→hora local (`toLocalCalendarParts`) y el promedio de 5 puntos por `(facade, timestamp_utc)` (`computeAggregatedFacadeResults`).
- [ ] Confirmar con una prueba (existente o nueva) que `cargar_csv_fs()` sigue rechazando un CSV sin `FS_geometrico`.
- [ ] Revisar si hay algún test o script que valide el CSV crudo vs. promediado automáticamente (o si depende solo de instrucción al usuario).

## Cierre (pendiente)

- [ ] Decidir si se agrega versión explícita al formato CSV.
- [ ] Decidir si se referencia este contrato desde `shared/shading-engine-contract.ts` con un comentario cruzado.
- [ ] Mover `CONTRATO_CSV_SOMBREADO_ENTRE_APPS.md` a un estado "aprobado" una vez resueltos los pendientes anteriores, o archivar la propuesta si se decide que el borrador actual es suficiente.
