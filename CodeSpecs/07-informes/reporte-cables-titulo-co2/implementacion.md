# Implementación — Reporte: cables reales, título y autos equivalentes

**Estado:** validación

## Cambios realizados

- `calculos/coherencia_reporte.py`: error «📊 Producción no usó los cables
  calculados».
- `calculos/reporte_produccion.py`: `titulo` y `sujeto` en `etiquetas_tipo`.
- `calculos/co2.py`: `KM_ANUALES_AUTO`, `vehiculos_equivalentes` y
  `texto_vehiculos`.
- 📄 Reporte: encabezado con `_tx['titulo']`, texto de CO₂ con
  `etiquetas_tipo(...)["sujeto"]` y fila del año 1 con `texto_vehiculos`.
- 🌿 Impacto CO₂: años de un auto promedio con `KM_ANUALES_AUTO`.

## Archivos modificados

- `bipv_python/calculos/coherencia_reporte.py`
- `bipv_python/calculos/reporte_produccion.py`
- `bipv_python/calculos/co2.py`
- `bipv_python/pages/10_📄_Reporte_PDF.py`
- `bipv_python/pages/12_🌿_Impacto_CO2.py`
- `bipv_python/tests/test_reporte_cables_titulo_co2.py`
- `bipv_python/datos/base_conocimiento_asistente.md` (sección 120)
- `CodeSpecs/00-director/registro-de-decisiones.md`
