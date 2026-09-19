# Propuesta — Dimensionamiento eléctrico

**Estado:** completado

## Objetivo

Formalizar el contrato funcional de Dimensionamiento, preservando compatibilidad
eléctrica, vigencia del diseño confirmado y propagación coherente hacia Producción,
Unifilar, RETIE, análisis financiero y reportes.

## Alternativas consideradas

El módulo combina catálogo de equipos, temperaturas de diseño por ciudad, área y
ocupación del proyecto, cadenas/trackers y estado de Motor IV y batería. La lógica
pura principal incluye `evaluar_compatibilidad_string`, `optimizar_n_serie`,
`dimensionar_sistema`, `mapear_inversores_catalogo`,
`resolver_n_strings_tracker` y `diseno_electrico_confirmado`.

## Alternativa recomendada

Mantener las claves públicas de `session_state` y usar
`diseno_electrico_confirmado(session_state)` como frontera única para los
consumidores aguas abajo. La UI puede recalcular sugerencias, pero solo una acción
de confirmación actualiza el diseño consumible.
