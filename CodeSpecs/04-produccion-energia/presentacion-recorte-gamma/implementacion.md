# Implementación — 📊 Producción: recorte del inversor y γ bien presentados

**Estado:** validación

## Cambios realizados

- `calculos/formato_produccion.py` (nuevo): `FORMATO_TABLA_MENSUAL`,
  `gamma_ficha`, `texto_gamma`.
- `calculos/produccion.py` y `calculos/produccion_iv.py`: el resultado
  incluye `Tk_gamma_pct` (γ de la ficha); la nota de «↳ Solo horas
  calientes» usa `texto_gamma`. Ninguna fórmula cambia.
- `pages/6_📊_Produccion.py`: la tabla mensual usa `FORMATO_TABLA_MENSUAL`
  con las columnas presentes.
- Manual del Asistente, sección 89; registro de decisiones.

## Archivos modificados

- `bipv_python/calculos/formato_produccion.py`
- `bipv_python/calculos/produccion.py`
- `bipv_python/calculos/produccion_iv.py`
- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/tests/test_produccion_presentacion.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
