# Implementación — Escena de Site Designer vigente

**Estado:** validación

## Cambios realizados

- `calculos/sitedesigner_marsh.py`: `malla_fingerprint` en el meta.
- `calculos/vinculador_sombra_multisuperficie.py`:
  `invalidar_sombra_por_cambio_malla` y su llamada en
  `construir_y_recalcular_proyecto_fisico`.
- `pages/9_🗺️_Vista_3D.py`: escena de otra ubicación rechazada; firma con la
  huella.
- `calculos/mismatch_bypass.py`: alcance radiativo documentado.

## Archivos modificados

- `bipv_python/calculos/sitedesigner_marsh.py`
- `bipv_python/calculos/vinculador_sombra_multisuperficie.py`
- `bipv_python/calculos/mismatch_bypass.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_escena_site_designer_vigente.py`
- `bipv_python/datos/base_conocimiento_asistente.md` (sección 122)
- `CodeSpecs/00-director/registro-de-decisiones.md`
