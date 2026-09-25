# Implementación — Error del mapa de calor POA con POA por superficie calculado

**Estado:** completado

## Cambios realizados

- `_poa_hm_df` se obtiene de `poa_superficies` y, solo si es `None`, se usa
  `_poa_s`. Se eliminó el `or` que evaluaba la verdad del DataFrame.
- Prueba nueva con análisis AST de la página y verificación del patrón.

## Archivos modificados

- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_vista3d_heatmap_poa_superficie.py` (nuevo)
- `CodeSpecs/08-interfaz/heatmap-poa-superficie/` (esta Spec)
- `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue

Solo Streamlit: `git pull --ff-only origin main` en
`/var/www/bipv/calculadora-bipv` y `pm2 restart streamlit-bipv`. La app web
no usa esta página.
