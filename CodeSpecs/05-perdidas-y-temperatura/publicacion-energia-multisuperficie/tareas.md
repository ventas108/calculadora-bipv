# Tareas — Publicación única de la energía multi-superficie

**Estado:** completado

Orden obligatorio: primero las pruebas (deben fallar con `main` `38a56c81`),
luego el código, luego la validación completa.

## Pruebas nuevas (`bipv_python/tests/test_publicacion_energia_multisuperficie.py`)

- [x] `simplificado` y `bypass_csv`: claves completas, suma del desglose =
      total, suma de áreas = área total, POA de 8760 h, sin proyecto físico.
- [x] `fisico`: `multisup_perdida_bus_kWh` = suma del desglose − total de
      buses y proyecto físico publicado; POA ponderada por área.
- [x] `fisico` sin proyecto ⇒ `ValueError`; proyecto físico con otro origen
      ⇒ `ValueError`.
- [x] Publicación atómica ante total, área, desglose, POA o número no finito
      incoherentes: nada escrito.
- [x] Origen fuera del conjunto cerrado ⇒ `ValueError`.
- [x] Proyecto físico incompleto no toca una publicación anterior.
- [x] Reemplazar otro origen sin confirmación no escribe; con confirmación
      retira el proyecto físico y la pérdida de bus.
- [x] Mismo origen reemplaza sin confirmar; adoptar físico sobre
      simplificado puede pedir confirmación.
- [x] Sesión antigua sin origen ⇒ `desconocido` y pide confirmación.
- [x] Retirar borra todas las claves de la publicación y es idempotente.
- [x] Invalidación: las claves nuevas están en `KEYS_DERIVADOS_POA` y
      `KEYS_MULTISUP_ESTADO`.
- [x] `proyectos_manager`: claves nuevas excluidas y reiniciadas.
- [x] Guardado tras reemplazar físico por simplificado: sin `proyecto_fisico`.
- [x] Página (AST): ningún botón escribe, borra ni recorre las claves de
      energía directamente; los tres orígenes, retirar, confirmación y
      etiqueta de origen presentes.
- [x] Persistencia: origen restaurado, origen físico inferido en proyectos
      antiguos con proyecto físico, origen físico sin proyecto rechazado.
- [x] Asistente: recuperación de «un solo origen, con confirmación».

## Implementación

- [x] `calculos/publicacion_multisuperficie.py` (nuevo).
- [x] `calculos/adaptador_multisuperficie.py`: `aplicar_proyecto_a_session_state`
      delega en la publicación única.
- [x] `calculos/invalidacion.py`, `calculos/proyectos_manager.py`,
      `calculos/persistencia_multisuperficie.py`: claves nuevas.
- [x] `pages/9_🗺️_Vista_3D.py`: tres botones por la publicación única,
      confirmación de reemplazo, banner con origen, «Desactivar» con
      `retirar_energia_multisuperficie`.
- [x] Manual (`docs/`, `entregables/`) y Asistente actualizados.

## Validación

- [x] Pruebas nuevas en rojo con el código previo y en verde con el nuevo.
- [x] Prueba de humo de la página con `streamlit.testing.v1.AppTest`
      (integrar, confirmar reemplazo, desactivar).
- [x] Suite completa de `bipv_python/tests` en verde.
- [x] Auditoría SDD sin bloqueos.
