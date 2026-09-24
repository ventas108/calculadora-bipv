# Tareas — Validación visible de los puntos 3D por superficie

**Estado:** validación

Orden obligatorio: primero las pruebas (deben fallar con el commit previo
`3b53a1a0`), luego el código, luego la validación completa.

## Pruebas nuevas (`bipv_python/tests/test_puntos_3d_validacion.py`)

- [x] Parser, líneas válidas: `8,0,2`, `8.5,0,2`, `8;0;2`, `8,5;0;2`,
      espacios y signos.
- [x] Parser, errores con número de línea y motivo: `8,5,0,2`, `8,0`,
      `8,a,2`, `8;0`, campo con dos comas decimales, `nan`, `inf`, espacios
      como separador; las líneas válidas vecinas se conservan.
- [x] Líneas vacías ignoradas sin error; sugerencia de `;` para coma decimal.
- [x] Vista previa con la `validar_puntos` del motor: punto dentro, a 5 cm y
      a 30 cm; sin malla o sin puntos no hay avisos.
- [x] Migración por nombre, por `uid` en texto (JSON recargado), superficie
      borrada con aviso, idempotencia y sin mutar la entrada.
- [x] Renombrar conserva los puntos; el motor recibe los nombres actuales de
      las superficies activas.
- [x] Página (AST): usa parser, vista previa y migración; `_sombra_lista`
      depende de `_errores_puntos`; sin `except ValueError: pass`.

## Implementación

- [x] `calculos/puntos_3d.py` (nuevo).
- [x] `pages/9_🗺️_Vista_3D.py`: captura por `uid`, errores por línea,
      vista previa, botón bloqueado con el motivo.
- [x] Manual (`docs/`, `entregables/`) y Asistente actualizados.

## Validación

- [x] Pruebas nuevas en rojo con el código previo y en verde con el nuevo.
- [x] Prueba de humo de la página con `AppTest`.
- [x] Suite completa de `bipv_python/tests` en verde.
- [x] Auditoría SDD sin bloqueos.
