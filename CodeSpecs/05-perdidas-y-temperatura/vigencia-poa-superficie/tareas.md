# Tareas — Vigencia de la POA por superficie

**Estado:** completado

Orden obligatorio: primero las pruebas (deben fallar con `main` `38a56c81`),
luego el código, luego la validación completa.

## Pruebas nuevas (`bipv_python/tests/test_vigencia_poa_superficie.py`)

- [x] Firma estable ante renombrado; cambia con tilt, azimuth, área, tipo y
      montaje.
- [x] Firma cambia con albedo, bifacial activo, latitud, altitud y TMY; el
      bifacial desactivado no entra en la firma.
- [x] Configuración bifacial por montaje (techo, adosada, ventilada, heredar)
      sin mutar la configuración global.
- [x] Cálculo firmado indexado por `uid`, solo superficies activas.
- [x] Un fallo de cálculo queda en `errores[uid]` con su causa; el resto se
      calcula.
- [x] Vigencia: POA vigente tras calcular y tras renombrar.
- [x] Cambio de geometría invalida solo esa superficie (`geometria_cambiada`).
- [x] Cambio de albedo o bifacial ⇒ `geometria_cambiada`.
- [x] Cambio de TMY o coordenadas, o TMY ausente ⇒ todas en `tmy_cambiado`.
- [x] `sin_calcular`, `error_calculo` e inactivas excluidas.
- [x] Sesión antigua indexada por nombre ⇒ `sin_calcular`.
- [x] `poas_vigentes_estado` usa los mismos parámetros que el cálculo
      (incluida la casilla bifacial de Vista 3D).
- [x] `preservar_o_invalidar_campos_fisicos` conserva `firma_poa` sin cambio
      de geometría y la retira si cambia tilt, azimuth, área, tipo o montaje.
- [x] Página (AST): ninguna lectura directa de `poa_superficies`.
- [x] Página: usa `calcular_poa_superficies_firmadas`, consulta la vigencia en
      los cuatro consumidores y guarda errores y `firma_poa`.
- [x] Persistencia: una `firma_poa` distinta rechaza la restauración
      (`tests/test_persistencia_multisuperficie.py`).
- [x] Asistente: recuperación de la sección «POA vigente por superficie».

## Implementación

- [x] `calculos/multi_superficie.py`: motivos, firma, cálculo firmado,
      vigencia y lectura desde la sesión.
- [x] `calculos/vinculador_sombra_multisuperficie.py`: `firma_poa` en
      `preservar_o_invalidar_campos_fisicos`.
- [x] `calculos/proyectos_manager.py`: `poa_superficies*` fuera del guardado
      y reiniciadas al cargar otro proyecto.
- [x] `pages/9_🗺️_Vista_3D.py`: cálculo firmado, `firma_poa`, avisos y
      consumidores por vigencia.
- [x] Manual (`docs/`, `entregables/`) y Asistente actualizados.

## Validación

- [x] Pruebas nuevas en rojo con el código previo y en verde con el nuevo.
- [x] Prueba de humo de la página con `streamlit.testing.v1.AppTest`.
- [x] Suite completa de `bipv_python/tests` en verde.
- [x] Auditoría SDD sin bloqueos.
