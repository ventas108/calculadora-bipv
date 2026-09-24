# Tareas — Sombra falsa con el sol detrás del plano del módulo

**Estado:** validación

Orden obligatorio: primero las pruebas (deben fallar con `main` `9398948e`),
luego el código, luego la validación completa.

## Pruebas nuevas (`bipv_python/tests/test_sombra_cara_trasera.py`)

- [x] Invariante: torre convexa de Torre 5 (17,29 × 17,29 × 36,42 m,
      `northOffset` 160,5°) con un punto orientado en cada cara → 0 horas con
      `FS_geometrico > 0`.
- [x] Obstáculo real delante del módulo → `FS_geometrico = 1`,
      `sol_detras_plano = False`, obstáculo y distancia conservados.
- [x] Obstáculo detrás del módulo → `FS_geometrico = 0`,
      `sol_detras_plano = True`, sin obstáculo ni distancia.
- [x] Las horas con sol delante son idénticas con y sin orientación; el
      número de filas no cambia.
- [x] Sin orientación: comportamiento previo, `sol_detras_plano` nulo y
      advertencia `orientacion_desconocida` en `df.attrs`.
- [x] La orientación del punto tiene prioridad sobre la de la función.
- [x] Validación: orientación no numérica, no finita, fuera de rango o
      incompleta → `ValueError`.
- [x] Cubierta inclinada 10° al sur: horas con sol detrás del plano
      filtradas, resto intacto.
- [x] Escena sintética de la prueba de cierre (Fachada Sur): 678 horas-punto
      con y sin el edificio de la fachada.
- [x] Por superficie: la orientación de la geometría llega al ray-casting
      (Torre 5, cara SE → `sombra_cero_calculada`), la firma lleva `v2` y los
      puntos de la firma no se alteran.
- [x] Por superficie sin `tilt_deg`/`azimuth_deg` → `error_geometrico`.
- [x] Persistencia: firma de `sombras_3d` `v1` retirada con motivo; `v2` y
      firmas de otras fuentes conservadas; `construir_y_recalcular_proyecto_fisico`
      aplica la invalidación.
- [x] Contrato web: punto con orientación filtra; orientación incompleta
      rechazada por `validar_solicitud`.

## Implementación

- [x] `calculos/sombras_3d.py`: normal del módulo, filtro por hora, columna
      `sol_detras_plano`, advertencias, orientación por superficie, `v2`.
- [x] `calculos/vinculador_sombra_multisuperficie.py`:
      `invalidar_sombra_por_version_algoritmo` y su llamada en
      `construir_y_recalcular_proyecto_fisico`.
- [x] `calculos/contrato_sombreado.py` y `scripts/run_shading_contract.py`:
      orientación opcional por punto.
- [x] `pages/5a_🌳_Sombras_SketchUp.py`: orientación antes del cálculo de FS,
      en la firma de entradas y por punto si la tabla trae columnas.
- [x] `pages/9_🗺️_Vista_3D.py`: verificado, ya envía `tilt_deg`/`azimuth_deg`
      por superficie; sin cambios.

## Validación

- [x] Las pruebas nuevas fallan con el código previo y pasan con el nuevo.
- [x] 10 suites de la prueba de cierre multisuperficie (línea base
      `110 passed`).
- [x] Suite completa de `bipv_python/tests` en verde.
- [x] Auditoría SDD sin bloqueos.
