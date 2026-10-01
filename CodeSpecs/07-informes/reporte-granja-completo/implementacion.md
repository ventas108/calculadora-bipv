# Implementación — Reporte PDF de Granja FV completo y ficha del inversor

**Estado:** validación

## Cambios realizados

- `calculos/reporte_granja.py` (nuevo): campo, módulos por string e inversor,
  SVG de vista 3D, plano eléctrico, luz en el suelo y mapa mensual,
  maquinaria, coherencia y nota de strings que cruzan.
- `calculos/ficha_inversor.py` (nuevo): alertas de la ficha y margen de Voc.
- `calculos/reporte_produccion.py`: textos por tipo, nota de POA y de PR,
  mismatch aplicado, altitud y aviso de suciedad.
- `pages/10_📄_Reporte_PDF.py`: lo usa en Información General, Recurso Solar,
  Compatibilidad, Motor Óptico, Producción y Granja FV.
- `pages/4_📐_Dimensionamiento.py`: alerta de la ficha del inversor.
- Manual del Asistente, sección 103; contratos y registro.

## Archivos modificados

- `bipv_python/calculos/reporte_granja.py`
- `bipv_python/calculos/ficha_inversor.py`
- `bipv_python/calculos/reporte_produccion.py`
- `bipv_python/pages/10_📄_Reporte_PDF.py`
- `bipv_python/pages/4_📐_Dimensionamiento.py`
- `bipv_python/tests/test_reporte_granja_completo.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
