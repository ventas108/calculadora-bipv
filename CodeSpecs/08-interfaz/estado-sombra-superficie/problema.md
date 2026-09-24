# Spec — Estado de sombra visible por superficie

**Estado:** validación

## Alcance de la fase

App hermana Streamlit (`bipv_python/`): sección «🌳 Sombra 3D por superficie»
de `pages/9_🗺️_Vista_3D.py` y funciones de estado de
`calculos/vinculador_sombra_multisuperficie.py`. No cambia el cálculo de
sombra ni sus reglas de aceptación.

## Problema a resolver

El motor ya clasifica la sombra de cada superficie, pero el usuario no lo ve:

1. Tras «🌳 Calcular sombra» la página dice «revisa el estado antes de
   adoptar resultados» (línea 1151), pero **no muestra ningún estado**:
   `estado_sombra`, `cobertura_sombra`, `advertencias_sombra` y
   `calidad_confianza_sombra` no se leen en ninguna parte de la página.
2. Para estados no aceptables (`calculo_incompleto`, `error_geometrico`),
   `aplicar_sombra_a_superficies` (vinculador, línea 28) borra también
   `advertencias_sombra`: se pierde el motivo (por ejemplo, qué punto quedó
   dentro de la malla).
3. `invalidar_sombra_por_cambio_tmy` e `invalidar_sombra_por_version_algoritmo`
   escriben `sombra_bloqueo_motivo` solo en la copia interna de
   `construir_y_recalcular_proyecto_fisico`; el motivo nunca llega a la UI.
4. `preservar_o_invalidar_campos_fisicos` (línea 42) retira la sombra al
   cambiar la geometría sin dejar motivo.

Hoy el usuario solo lo descubre en el modo físico, como
«falta 'p_shade'», sin saber por qué.

## Contexto

- El manual (`docs/MANUAL_VISTA_3D.md`) documenta esta limitación como
  provisional.
- Relacionada: la Spec `puntos-3d-validacion` evita parte de los errores
  geométricos antes del cálculo; ambas tocan la misma sección de la página,
  por lo que se implementan en secuencia: primero `puntos-3d-validacion`,
  después esta.
