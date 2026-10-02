# Propuesta — Caché del catálogo de paneles

**Estado:** validación

## Objetivo

Que leer el catálogo cueste una sola vez por versión del Excel.

## Alternativa recomendada

- Caché en memoria con la clave (ruta, mtime, tamaño) del Excel:
  - se invalida sola al guardar, borrar o actualizar el servidor;
  - `.clear()` sigue existiendo para guardar y eliminar.
- Cada llamada recibe una copia ligera (un dict nuevo por panel), así
  modificar un panel en una página no altera la caché.
- Recorrer las filas con `to_dict("records")` en lugar de `iterrows`.
- Guardia: todo `cargar_catalogo*` de `datos/` debe tener caché.

## Alternativas descartadas

- Volver solo a `st.cache_data`: ~2 s por llamada por la copia serializada.
- `st.cache_resource` sin copia: una página que modifique un panel
  cambiaría el catálogo de todas.

## Fuera de alcance

El catálogo de inversores, que ya tiene caché con mtime.
