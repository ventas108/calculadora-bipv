# Implementación — Caché del catálogo de paneles

**Estado:** validación

## Cambios realizados

- `cargar_catalogo_paneles` usa `_CACHE_CATALOGO` con `_clave_excel()` y
  devuelve `{k: dict(v)}`. La lectura pasa a `_leer_catalogo_paneles`.
- `cargar_catalogo_paneles.clear` limpia la caché.
- Filas con `df.to_dict("records")`: primera lectura de 2,3 s a 1,5 s.
- `_texto_celda` ya no tiene decorador.

## Archivos modificados

- `bipv_python/datos/catalogo_paneles_excel.py`
- `bipv_python/tests/test_cache_catalogo_paneles.py`
- `bipv_python/datos/base_conocimiento_asistente.md` (sección 116)
- `CodeSpecs/00-director/registro-de-decisiones.md`
