# Diseño — Coeficiente de temperatura de Isc (α) en el catálogo de paneles

**Estado:** validación

## Entradas

Fila del Excel (`CoefIsc_C`, %/°C) y nombre del modelo.

## Salidas

Panel del catálogo con `CoefIsc_C` y `Tk_alfa` (%/°C) o `None`.

## Tipos de datos

`float | None`.

## Errores posibles

Celda vacía o 0 → respaldo de `tecnologias_bipv` o `None` (Motor IV usa el
valor por tecnología, como antes).

## Dependencias

Ninguna nueva.

## Criterios de aceptación

1. Se lee `CoefIsc_C`; vacío o NaN → respaldo o `None`.
2. ASP-ST1-T40 entrega `Tk_alfa` 0,06 y Motor IV deja de avisar.
3. La tabla de edición muestra y guarda la columna.
4. El manual del Asistente lo explica (sección 111).
