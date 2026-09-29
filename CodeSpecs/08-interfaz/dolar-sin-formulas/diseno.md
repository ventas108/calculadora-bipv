# Diseño — El signo «$» no debe convertirse en fórmula

**Estado:** validación

## Entradas

Textos de `st.markdown`, `success`, `info`, `warning`, `error`, `caption`,
`write` y `toast` en `pages/`; mensaje final de Financiero.

## Salidas

Los mismos textos con «\$».

## Tipos de datos

`str`.

## Errores posibles

Un «$» nuevo sin escapar en un texto con otro «$»: la prueba lo detecta.

## Dependencias

Ninguna.

## Criterios de aceptación

1. El mensaje final no tiene «$» sin escapar.
2. Ninguna página tiene un texto markdown con dos o más «$» sin escapar.
3. Ningún archivo produce avisos de secuencia de escape inválida.
