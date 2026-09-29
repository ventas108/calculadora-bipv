# Implementación — Temperaturas de diseño estables en 📐 Dimensionamiento

**Estado:** validación

## Cambios realizados

- `calculos/temperatura.py`: `CLAVE_FIRMA_TEMPS_TMY`,
  `temperaturas_diseno_desde_tmy`, `firma_temperaturas_tmy`,
  `temperaturas_a_aplicar`.
- `pages/4_📐_Dimensionamiento.py`: recálculo por firma del TMY y del NOCT;
  los tres campos con `campo_persistente`; línea 🌡️ que dice si vienen del
  TMY (y de qué versión de PVGIS) o de la ciudad.
- `pages/1_🏠_Proyecto.py`: «Guardar configuración» no pisa temperaturas del
  TMY; el cambio de ciudad borra la firma.
- Manual del Asistente, sección 82.

## Archivos modificados

- `bipv_python/calculos/temperatura.py`
- `bipv_python/pages/4_📐_Dimensionamiento.py`
- `bipv_python/pages/1_🏠_Proyecto.py`
- `bipv_python/tests/test_temperaturas_diseno_estables.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
