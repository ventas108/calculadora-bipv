# Implementación — Estado de sombra visible por superficie

**Estado:** validación

## Cambios realizados

- `calculos/vinculador_sombra_multisuperficie.py`:
  - `diagnostico_sombra_superficies(superficies, tmy)`: de solo lectura
    (trabaja sobre copias). Aplica las mismas invalidaciones que
    `construir_y_recalcular_proyecto_fisico` (TMY y versión del algoritmo) y
    las mismas validaciones de sombra que `construir_proyecto_desde_session_state`
    (estado aceptable, sombra horaria y firma presentes, 8760 valores
    finitos en [0, 1]). Devuelve por superficie activa: nombre, estado,
    utilizable, motivo, horas con sol calculadas, calidad, número de puntos
    y acción. Estados nuevos definidos una sola vez
    (`ESTADOS_DIAGNOSTICO_SOMBRA`).
  - `aplicar_sombra_a_superficies`: en estados no aceptables solo retira
    `p_shade`, `firma_sombra` y `cobertura_sombra`; guarda las advertencias y
    la calidad del nuevo cálculo; limpia los motivos de invalidación.
  - `preservar_o_invalidar_campos_fisicos`: al cambiar una entrada de sombra
    deja `sombra_invalidada_motivo` («cambió tilt», «cambió área»…) si había
    sombra, y lo conserva mientras no cambie nada.
- `pages/9_🗺️_Vista_3D.py`: tabla «Estado de la sombra por superficie»,
  siempre visible, con 🟢 utilizable, 🔴 no utilizable y ⚪ sin calcular,
  estado, horas, calidad, puntos, motivo y qué hacer. Se retiró el mensaje
  «revisa el estado antes de adoptar resultados», que remitía a un estado
  que la página no mostraba.

Hallazgo corregido en esta Spec: tras «🌳 Calcular sombra», la sección de
inversores volvía a guardar en `superficies_bipv` la lista previa al
cálculo, en el mismo rerun, y el resultado de sombra se perdía (reproducido
con `AppTest`: ambas superficies sin sombra justo después de calcular). Por
eso el modo físico decía «falta p_shade» aunque la sombra se hubiera
calculado. Ahora la lista con la sombra reemplaza a `_sups_actualizado` antes
de esa sección.

Desviaciones del diseño, con motivo:

- `aplicar_sombra_a_superficies` también conserva la calidad (además de las
  advertencias) en estados no aceptables: la tabla la muestra.
- La columna «Puntos» usa el número de puntos del cálculo y, si la sombra no
  es utilizable, el de puntos escritos actualmente.

## Archivos modificados

- `bipv_python/calculos/vinculador_sombra_multisuperficie.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_estado_sombra_superficie.py` (nuevo)
- `bipv_python/datos/base_conocimiento_asistente.md`
- `docs/MANUAL_VISTA_3D.md`, `entregables/MANUAL_VISTA_3D_BIPV.docx`
- `CodeSpecs/08-interfaz/estado-sombra-superficie/`
- `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue

- Solo la app Streamlit (reinicio de `streamlit-bipv`). No cambian los
  estados aceptables ni la física de sombra.
- Tras desplegar, las sombras que antes se perdían al calcular quedan
  guardadas: hay que volver a pulsar «🌳 Calcular sombra».
