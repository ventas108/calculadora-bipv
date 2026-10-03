# Diseño — Columnas a medida

**Estado:** validación

## Entradas

Lista opcional de distancias en metros (texto en la página).

## Salidas

Puntos con centro = esquina + u·(posición + w/2) + v·(fila) + n·d.

## Tipos de datos

`list[float] | None`.

## Errores posibles

- Número de posiciones distinto de las columnas: «Hay N posiciones de
  columna y el campo tiene M columnas».
- Fuera de orden, primera negativa, columnas que se solapan, texto no
  numérico: `ValueError` con mensaje claro y sin tocar los puntos.

## Dependencias

`calculos/puntos_modulo.py`, `calculos/guia_vista_3d.py`,
`pages/9_🗺️_Vista_3D.py`.

## Criterios de aceptación

1. Fachada sur con posiciones 0; 1,1; 3,43: centros 0,523 / 1,623 / 3,953 m.
2. Cada columna coincide (1e-12 m) con la misma columna generada sola con
   su esquina desplazada, en fachada y techo.
3. Strings por columna con posiciones a medida.
4. Cuatro validaciones con mensajes claros; parser con coma decimal.
5. La página genera columnas a 4,5 m y rechaza 3 posiciones para 2
   columnas.
6. Guía y manual (sección 127) sin nombres comerciales de otras apps.
