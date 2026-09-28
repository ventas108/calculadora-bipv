# Diseño — Mensaje final de Financiero y Ficha RETIE al ancho

**Estado:** validación

## Entradas

`multisup_sistema` (o nada), número de módulos, panel de Dimensionamiento,
métricas con Ley 1715 y valor nivelado de la energía.

## Salidas

Textos del rótulo y del mensaje final.

## Tipos de datos

`str`, `float`, `dict`.

## Errores posibles

Sin TIR: «TIR: N/A»; sin payback: «> horizonte»; sin valor nivelado: el LCOE
sin comparación; sin panel: «—».

## Dependencias

Ninguna nueva.

## Criterios de aceptación

1. Con dos paneles el mensaje dice «112 ASP-ST1-T40 + 4 SPR-E20-327 (…)».
2. Con TIR el mensaje incluye VPN, Payback y LCOE.
3. La ficha se muestra al ancho de la columna, sin iframe con desplazamiento.
