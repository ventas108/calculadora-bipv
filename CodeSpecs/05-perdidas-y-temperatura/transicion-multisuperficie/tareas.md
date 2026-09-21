# Tareas — Integración de la transición transaccional multi-superficie con Streamlit

**Estado:** en implementación — backend puro de sombra/inversor por
superficie completado, corregido tras auditoría y probado (2026-09-21,
2 rondas: implementación + corrección); UI de captura de puntos/malla por
superficie y UI de inversor por superficie (mockup) siguen pendientes.

- [x] Aprobación del Director de `problema.md`/`propuesta.md`/`diseno.md` de
  esta Spec (20-sep-2026). La aprobación no autoriza activar el modo físico
  por defecto ni saltar los gates técnicos.
- [x] Decisión del Director sobre Motor Óptico global vs. por superficie
  (ver `diseno.md`, punto 5) — **opción (a), global** (2026-09-21). No
  bloquea más el alcance de la primera versión.
- [x] Mockup de la UI de inversor dedicado/compartido aprobado (ver
  `diseno.md`, punto 6) — aprobado humanamente el 2026-09-21 en
  `mockup-ui.md`; queda desbloqueada la implementación de la UI, sin activar
  el modo físico por defecto.
- [x] Ampliar `calculos.sombras_3d`/horizonte para producir `p_shade` y
  `firma_sombra` por superficie — prerequisito bloqueante para ofrecer sombra
  física por superficie; no se permiten defaults inventados (2026-09-21:
  `calcular_fs_horario_por_superficie` extendido con `cobertura`,
  `advertencias` y `calidad_confianza` explícitas — ver `diseno.md`). Sigue
  faltando la UI de captura de puntos/malla por superficie (no es parte de
  esta línea, ver ítem nuevo abajo).
- [x] Conectar la salida de sombra por superficie con
  `session_state["superficies_bipv"]` mediante una frontera pura testeada
  (`calculos/vinculador_sombra_multisuperficie.py`, 2026-09-21), incluida la
  invalidación automática de `p_shade`/`firma_sombra` cuando tilt/azimuth
  cambian en el editor de geometría de `pages/9_🗺️_Vista_3D.py`.
- [x] Estructura de validación/derivación pura de inversor dedicado/compartido
  por superficie (`calculos/inversores_multisuperficie.py`, 2026-09-21) —
  lista para que la use la UI del ítem de abajo en cuanto exista mockup
  aprobado.
- [x] UI en `pages/9_🗺️_Vista_3D.py` para capturar puntos de análisis y
  malla 3D POR superficie y llamar
  `calcular_fs_horario_por_superficie` + `aplicar_sombra_a_superficies` —
  implementada con carga de JSON Site Designer, verificación de ubicación y
  gate explícito de malla+TMY+puntos (2026-09-21). Sigue pendiente la
  verificación manual con un proyecto real y la prueba de Streamlit real.
- [x] Añadir la API pura base para agrupar puntos por superficie, alinear
  `p_shade` a 8760 horas y emitir `firma_sombra` (`20-sep-2026`). El flujo
  Streamlit y los escritores reales de puntos/malla aún no están conectados.
- [x] Confirmar con Claude y Copilot la clasificación completa de los datos
  faltantes (punto 3) contra los escritores/consumidores reales; la tabla de
  `diseno.md` queda respaldada por lectura directa del código (20-sep-2026).
- [x] Implementar pruebas unitarias de los adaptadores antes de conectarlos a
  Streamlit (`8 passed`, 20-sep-2026).
- [x] Implementar el adaptador de entrada (`session_state → proyecto`) como
  función pura, con rechazo explícito de superficies incompletas.
- [x] Implementar el adaptador de salida (`proyecto["agregados"] →
  session_state`), escribiendo únicamente en las 5 claves `multisup_*`
  existentes con la forma ya vigente.
- [x] Implementar la UI de inversor por superficie (dedicado/compartido)
  según el mockup aprobado en `mockup-ui.md` — widgets de inversor,
  asignación por superficie, campos eléctricos y validación derivada
  implementados en `pages/9_🗺️_Vista_3D.py` (2026-09-21). La captura de
  malla/puntos por superficie sigue siendo un gate independiente.
- [x] Agregar el toggle opt-in `multisup_usar_fisico` (default `False`) a
  `pages/9_🗺️_Vista_3D.py` (`20-sep-2026`).
- [x] Implementar la vista de comparación lado a lado (simplificado vs.
  físico) sin escribir las claves `multisup_*` antes de adoptar
  (`20-sep-2026`).
- [x] Implementar el botón de adopción explícita que invoca el adaptador
  de salida (`20-sep-2026`).
- [x] (parcial) Pruebas estáticas de página para el editor de geometría
  (preserva/invalida campos físicos) y el panel de estado por superficie
  (`tests/test_pagina_transicion_multisuperficie.py`, 2026-09-21). Faltan
  las pruebas de integración completas del punto 8 de `diseno.md` (1-6),
  que dependen de la UI de puntos/malla e inversor todavía no construida.
- [x] Ejecutar la suite de regresión completa (2026-09-21, ronda de
  corrección) y confirmar cero fallos nuevos — ver
  `references/correccion-auditoria-multisuperficie.md` para el resultado
  exacto (comandos + salida).
- [ ] Revisión del diff en modo solo lectura (Claude/Copilot) antes de
  integrar, mismo patrón que `conservacion-optica-inversor`.
- [ ] Verificación manual en al menos un proyecto real: las 7 páginas
  consumidoras y `calculos/invalidacion.py` muestran/gestionan el número
  físico correctamente sin haber sido modificados. (Sigue bloqueado: no hay
  todavía una forma de que un proyecto real capture puntos/malla/inversores
  por superficie sin la UI pendiente.)
- [ ] Actualizar Director (`mapa-dependencias.md`,
  `contratos-entre-modulos.md`, `registro-de-decisiones.md`) — tarea
  reservada al Director, no a esta implementación.

### Ronda de corrección de auditoría (2026-09-21, mismo día)

Una auditoría sobre la ronda anterior encontró 5 hallazgos bloqueantes
reales (no solo mejoras cosméticas), todos corregidos con pruebas nuevas:

- [x] **Hallazgo 1**: `calcular_fs_horario_por_superficie` firmaba el TMY
  con un vector de ceros en vez de `T2m` real — ninguna firma producida por
  el motor podía pasar jamás `_validar_firma_sombra`. Corregido: la función
  ahora exige un `tmy: pd.DataFrame` real y usa
  `huella_horaria(tmy.index, tmy["T2m"])`, MISMA fórmula que
  `transicion_multisuperficie._verificar_geometria_y_tmy`. 5 pruebas nuevas
  en `tests/test_sombras_por_superficie.py`.
- [x] **Hallazgo 2**: un cálculo incompleto/erróneo solo generaba una
  advertencia de texto, nunca bloqueaba — el `p_shade=0` de relleno podía
  adoptarse igual. Corregido: estado explícito
  (`calculado_completo`/`sombra_cero_calculada`/`calculo_incompleto`/
  `error_geometrico`/`resolucion_insuficiente`) con bloqueo real en DOS
  capas independientes (`vinculador_sombra_multisuperficie.
  aplicar_sombra_a_superficies` y `adaptador_multisuperficie.
  construir_proyecto_desde_session_state`). 6 pruebas en
  `test_cobertura_sombra_por_superficie.py`, 9 en
  `test_vinculador_sombra_multisuperficie.py`, 6 en
  `test_adaptador_multisuperficie.py`.
- [x] **Hallazgo 3**: el botón "Adoptar cálculo físico" publicaba
  directamente el candidato guardado de un rerun anterior, sin revalidar.
  Corregido: función única `construir_y_recalcular_proyecto_fisico`, que
  tanto "calcular comparación" como "adoptar" ejecutan de cero contra el
  `session_state` actual; "adoptar" nunca confía en el candidato guardado.
  Pruebas estáticas de orden en `test_pagina_transicion_multisuperficie.py`
  + pruebas reales (no estáticas) en
  `test_flujo_fisico_multisuperficie_end_to_end.py`.
- [x] **Hallazgo 4**: `inversores_multisuperficie.py` existía pero no se
  llamaba desde ningún lado. Corregido: `construir_proyecto_desde_session_state`
  ejecuta `validar_inversores_y_asignaciones` + `aplicar_tipos_derivados`
  antes de construir el proyecto; `n_serie`/`n_paralelo` inválidos también
  se rechazan explícito. 8 pruebas nuevas de integración en
  `test_adaptador_multisuperficie.py`.
- [x] **Hallazgo 5**: la invalidación geométrica solo miraba tilt/azimuth.
  Corregido: se amplió a área, `n_serie`, puntos de análisis, malla y
  transparencia (`CAMPOS_ENTRADA_SOMBRA`), más una invalidación nueva y
  separada por cambio de TMY (`invalidar_sombra_por_cambio_tmy`, el TMY es
  una entrada global, no por superficie). 7 pruebas parametrizadas nuevas.
- [x] **Hallazgo 6 (prueba end-to-end obligatoria)**:
  `tests/test_flujo_fisico_multisuperficie_end_to_end.py`, 7 pruebas reales
  (no mocks de las piezas físicas) que ejercitan la cadena completa con 3
  superficies (2 orientaciones distintas, sombras distintas, un inversor
  dedicado y uno compartido), incluida publicación tras adopción, rechazo de
  TMY alterado y rollback si falla una superficie.

Ver `references/correccion-auditoria-multisuperficie.md` para el informe
completo de esta ronda de corrección, con comandos y resultados de pruebas
reproducibles.
