# Propuesta — Campos ligados a su dato en Dimensionamiento, Mismatch y Producción

**Estado:** validación

## Objetivo

Que ningún campo de la app que otros módulos leen pierda su valor al cambiar
de página, y que el patrón no pueda volver sin que falle una prueba.

## Alternativa recomendada

Aprobada por el usuario el 30-sep-2026.

- `campos_editor.campo_ligado(estado, widget, etiqueta, clave, defecto,
  **kwargs)`: widget en `_w_<clave>`, dato en `clave`, unidos con
  `sincronizar_campo`; recorta al rango y vuelve a `defecto` si la opción
  ya no existe. Mismo patrón que 💰 Financiero y 🔆 Motor Óptico.
- Se usa en los 5 campos de la auditoría; el resto del código sigue leyendo
  las mismas claves de dato (`resolver_n_strings_tracker`,
  `escenarios_fase4`, `produccion_vigencia`).
- Guarda general: una prueba recorre todas las páginas y falla si un widget
  usa como clave un dato que lee otra página o un cálculo.
- Manual del Asistente, sección 100.

## Alternativas descartadas

- Arreglar solo los tres campos sin guarda: el patrón ya había vuelto una
  vez (Financiero → Motor Óptico → estas páginas).

## Fuera de alcance

- Campos que solo lee su propia página y no se guardan con el proyecto.
