# Propuesta — Coeficiente de temperatura de Isc (α) en el catálogo de paneles

**Estado:** validación

## Objetivo

Que α Isc se pueda ver, editar y guardar en el catálogo y que llegue a Motor IV.

## Alternativa recomendada

Aprobada por el usuario el 1-oct-2026 (reporte del bug con capturas).

- `alfa_isc_desde_fila(fila, nombre)`: columna `CoefIsc_C`; sin ella, el
  `Tk_alfa` de `datos/tecnologias_bipv.py` del mismo modelo (ASP-ST1: +0,06
  %/°C de su ficha).
- El catálogo entrega `CoefIsc_C` y `Tk_alfa`.
- Tabla de edición: columna «α Isc (%/°C)» que guarda en `CoefIsc_C` (la
  columna se crea en el Excel del servidor con el primer guardado).
- Manual del Asistente, sección 111.

## Alternativas descartadas

- Escribir la columna en el Excel del repositorio: el `git pull` del
  servidor fallaría porque ese Excel se edita allá.

## Fuera de alcance

- Cargar α de los 3.128 paneles: se escribe al editar cada panel o al
  agregarlo desde su ficha PDF.
