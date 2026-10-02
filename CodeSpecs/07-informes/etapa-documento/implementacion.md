# Implementación — Etapa del documento en el Reporte

**Estado:** validación

## Cambios realizados

- `calculos/etapa_documento.py`: `ETAPAS`, `ETAPA_DEFECTO` y
  `encabezado_etapa`.
- 📄 Reporte PDF:
  - selector «Etapa del documento», guardado en `reporte_etapa` para que no se
    pierda al cambiar de página;
  - encabezado con `encabezado_etapa`;
  - la clase CSS `aviso-borrador` pasa a llamarse `aviso-etapa`.

## Archivos modificados

- `bipv_python/calculos/etapa_documento.py`
- `bipv_python/pages/10_📄_Reporte_PDF.py`
- `bipv_python/tests/test_etapa_documento.py`
- `bipv_python/datos/base_conocimiento_asistente.md` (sección 117)
- `CodeSpecs/00-director/registro-de-decisiones.md`
