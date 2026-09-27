# Propuesta — Parámetros de Financiero persistentes

**Estado:** validación

## Objetivo

Que lo que el usuario escribe en Financiero se conserve al cambiar de página,
se guarde con el proyecto y vuelva al cargarlo.

## Alternativas consideradas

1. **Copiar el valor a otra clave al final de la página.** Descartada: el
   campo sigue perdiendo su valor al volver y se desincroniza.
2. **Clave de datos + clave temporal del campo sincronizada** (patrón de la
   tarifa de compra y de Vista 3D). Recomendada.

## Alternativa recomendada

`calculos/campos_persistentes.campo_persistente(estado, widget, etiqueta,
clave, defecto, min_value, max_value, ...)`: el valor vive en `clave` (se
guarda con el proyecto); el campo usa `_w_<clave>` (temporal, no se guarda) y
se vuelve a llenar desde el dato cuando falta o cuando el dato cambió fuera
del campo (al cargar un proyecto). El dato se recorta al rango del campo.

La tarifa de excedentes conserva su clave de datos `tarifa_excedentes_cop_kWh`,
así un proyecto que ya la tenía la recupera. Los demás usan claves `fin_*`.

## Fuera de alcance

- Casillas y selectores de Financiero (modelo de degradación, modo O&M, P90
  manual) y los campos que ya se conservaban (degradación, O&M USD/kWp).
