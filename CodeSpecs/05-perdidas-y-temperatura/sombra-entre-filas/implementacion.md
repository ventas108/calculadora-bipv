# Implementación — Sombra entre filas y cara trasera según la geometría del campo (🌾 Granja FV, fase 2)

**Estado:** validación

## Cambios realizados

- `calculos/solar.py`: `GCR_FILA_AISLADA`, `aplicar_sombra_filas`,
  parámetro `filas` de `calcular_poa` y factores traseros del modelo
  bifacial.
- `calculos/granja_fv.py`: `geometria_filas`, `geometria_poa`,
  `mismas_filas`, `aplicar_geometria_a_energia`, `estado_poa_filas` (en
  `coherencia_campo`), `sombra_filas_estimada`.
- `pages/2_☀️_Recurso_Solar.py`: GCR de 0,01 en 0,01; ancho de la mesa,
  sombra trasera y mismatch trasero; POA con `filas_energia` en monofacial;
  publica `poa_geometria_filas`.
- `pages/9b_🌾_Granja_FV.py`: sección «5. Sombra entre filas y cara trasera
  en la energía» con los dos botones; coordenadas del predio.
- Manual del Asistente, sección 94 (y nota en la 93); contratos y registro.

## Archivos modificados

- `bipv_python/calculos/solar.py`
- `bipv_python/calculos/granja_fv.py`
- `bipv_python/pages/2_☀️_Recurso_Solar.py`
- `bipv_python/pages/9b_🌾_Granja_FV.py`
- `bipv_python/tests/test_sombra_entre_filas.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
