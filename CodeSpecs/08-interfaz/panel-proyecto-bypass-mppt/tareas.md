# Tareas — Panel y strings del proyecto en bypass y MPPT por superficie

**Estado:** completado

Orden obligatorio: primero las pruebas (deben fallar con el commit previo
`3b53a1a0`), luego el código, luego la validación completa.

## Pruebas nuevas (`bipv_python/tests/test_panel_proyecto_bypass_mppt.py`)

- [x] Panel del proyecto en catálogo: primera opción, sin aviso.
- [x] Panel del proyecto fuera de catálogo: se puede usar.
- [x] Sin panel o sin SDM completo: aviso y solo el catálogo.
- [x] `es_panel_del_proyecto`: etiqueta del proyecto, mismo modelo desde el
      catálogo, panel distinto, selección vacía.
- [x] Strings: configurados en la superficie, desde Dimensionamiento con
      paralelo por área, serie de la superficie con paralelo estimado.
- [x] Valores no numéricos, cero o no enteros: respaldo con aviso.
- [x] Sin ningún N serie: `ValueError` (no se inventa); paralelo por área sin
      área del panel: `ValueError`.
- [x] Orígenes de strings cerrados.
- [x] Página (AST): ningún selector fija `ASP-ST1-T40`; ambos usan
      `opciones_panel_superficie` y `strings_superficie`; sin los N en serie
      comunes.

## Implementación

- [x] `calculos/strings_superficie.py` (nuevo).
- [x] `pages/9_🗺️_Vista_3D.py`: bypass y MPPT con panel y strings del
      proyecto, marca de panel distinto y origen de strings.
- [x] Manual (`docs/`, `entregables/`) y Asistente actualizados.

## Validación

- [x] Pruebas nuevas en rojo con el código previo y en verde con el nuevo.
- [x] Prueba de humo de la página con `AppTest` (bypass y MPPT).
- [x] Suite completa de `bipv_python/tests` en verde.
- [x] Auditoría SDD sin bloqueos.
