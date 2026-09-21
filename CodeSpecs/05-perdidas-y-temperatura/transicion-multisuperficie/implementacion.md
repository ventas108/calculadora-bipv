# Implementación — Integración de la transición transaccional multi-superficie con Streamlit

**Estado:** en implementación — adaptadores y modo opt-in completados; integración física completa bloqueada por gates de datos

## Cambios realizados

Se implementaron los adaptadores puros y sus pruebas, sin modificar Streamlit:

- `bipv_python/calculos/adaptador_multisuperficie.py`: convierte el estado
  completo de superficies/inversores al proyecto canónico y publica las cinco
  claves `multisup_*` existentes.
- `bipv_python/tests/test_adaptador_multisuperficie.py`: 8 pruebas focales.
- `bipv_python/pages/9_🗺️_Vista_3D.py`: toggle opt-in, comparación y adopción
  explícita; el modo simplificado sigue siendo el comportamiento por defecto.
- `bipv_python/tests/test_pagina_transicion_multisuperficie.py`: 3 pruebas
  estáticas de página.
- `bipv_python/calculos/sombras_3d.py`: API pura
  `calcular_fs_horario_por_superficie`, que agrupa puntos por superficie,
  alinea la serie a 8760 horas y emite `firma_sombra`.
- `bipv_python/tests/test_sombras_por_superficie.py`: prueba del contrato por
  superficie aislada del backend opcional de `trimesh`.

La integración física completa sigue bloqueada por los gates aprobados de
`p_shade`/`firma_sombra` por superficie, la decisión de Motor Óptico por
superficie y el mockup de inversores. La página ya expone el flujo opt-in,
pero bloquea explícitamente el cálculo si esos datos no existen.

## Archivos modificados

Archivos modificados/creados en esta fase:

- `bipv_python/calculos/adaptador_multisuperficie.py`.
- `bipv_python/tests/test_adaptador_multisuperficie.py`.

Los siguientes archivos son previos a esta fase:

- `bipv_python/calculos/transicion_multisuperficie.py` — el prototipo
  físico, ya implementado y validado ANTES de esta Spec (4 rondas de
  auditoría, 27 pruebas propias), no como parte de esta integración.
- `bipv_python/tests/test_transicion_multisuperficie.py` — sus pruebas,
  también previas a esta Spec.
- Los 6 documentos de esta Spec (`problema.md`, `propuesta.md`,
  `diseno.md`, `tareas.md`, `validacion.md`, este `implementacion.md`).

Cuando exista implementación real, esta sección debe reemplazarse por la
lista efectiva de archivos tocados (esperado, según `diseno.md`: un
adaptador nuevo, cambios en `pages/9_🗺️_Vista_3D.py`, y las pruebas
correspondientes) — nunca antes de que el trabajo se haya hecho.
