# Propuesta — Estado de sombra visible por superficie

**Estado:** validación

## Objetivo

Que el usuario vea, para cada superficie activa, si su sombra es utilizable
y, si no, el motivo concreto y qué hacer.

## Alternativas consideradas

1. **Mostrar solo `estado_sombra` crudo.** Insuficiente: no explica la causa
   ni cubre sombras invalidadas por TMY, versión o geometría.
2. **Función pura de diagnóstico + tabla en la UI.** Recomendada.

## Alternativa recomendada

1. `diagnostico_sombra_superficies(superficies, tmy)` en el vinculador: de
   solo lectura, reutiliza las mismas reglas de
   `invalidar_sombra_por_cambio_tmy` e `invalidar_sombra_por_version_algoritmo`
   y devuelve, por superficie activa: estado, motivo, horas cubiertas,
   calidad, número de puntos y acción sugerida.
2. `aplicar_sombra_a_superficies` conserva `advertencias_sombra` en los
   estados no aceptables (retira solo `p_shade`, `firma_sombra` y
   `cobertura_sombra`).
3. `preservar_o_invalidar_campos_fisicos` deja `sombra_invalidada_motivo`
   con el campo que cambió.
4. La página muestra una tabla de estado bajo el botón de sombra, siempre
   visible, con semáforo por superficie.

Fuera de alcance: cambiar qué estados son aceptables o la física de sombra.
