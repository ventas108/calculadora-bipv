# Tareas — Estado de sombra visible por superficie

**Estado:** completado

Orden obligatorio: primero las pruebas (deben fallar con el commit previo
`3b53a1a0`), luego el código, luego la validación completa.

## Pruebas nuevas (`bipv_python/tests/test_estado_sombra_superficie.py`)

- [x] Diagnóstico para cada uno de los ocho estados, con motivo y acción sin
      jerga interna.
- [x] Detalles: horas con sol calculadas, calidad, número de puntos, punto
      concreto del error geométrico y campo de la geometría cambiada.
- [x] Sin TMY: sombras calculadas en `invalidada_tmy` con acción «Recurso
      Solar».
- [x] Estado del motor no listado (`resolucion_insuficiente`) mostrado tal
      cual como no utilizable; sombra horaria inválida no utilizable.
- [x] Solo superficies activas; la función no muta su entrada.
- [x] Coherencia: `utilizable` coincide con lo que acepta
      `construir_proyecto_desde_session_state` tras las mismas
      invalidaciones, en los ocho estados y con sombra horaria corta o fuera
      de rango.
- [x] `aplicar_sombra_a_superficies` conserva advertencias y calidad en
      estados no aceptables y limpia el motivo de invalidación al recalcular.
- [x] `preservar_o_invalidar_campos_fisicos` deja
      `sombra_invalidada_motivo` con el campo (tilt, azimuth, área), lo
      conserva en reruns sin cambios y no lo crea si no había sombra.
- [x] Página: la tabla se construye con `diagnostico_sombra_superficies`
      después del botón de sombra.

## Implementación

- [x] `calculos/vinculador_sombra_multisuperficie.py`: diagnóstico, motivos
      conservados.
- [x] `pages/9_🗺️_Vista_3D.py`: tabla de estado y corrección de la pérdida
      del resultado de sombra.
- [x] Manual (`docs/`, `entregables/`) y Asistente actualizados.

## Validación

- [x] Pruebas nuevas en rojo con el código previo y en verde con el nuevo.
- [x] Prueba de humo de la página con `AppTest`.
- [x] Suite completa de `bipv_python/tests` en verde.
- [x] Auditoría SDD sin bloqueos.
