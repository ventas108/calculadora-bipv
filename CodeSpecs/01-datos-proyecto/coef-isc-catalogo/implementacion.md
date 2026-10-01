# Implementación — Coeficiente de temperatura de Isc (α) en el catálogo de paneles

**Estado:** validación

## Cambios realizados

- `datos/catalogo_paneles_excel.py`: `alfa_isc_desde_fila`; el panel trae
  `CoefIsc_C` y `Tk_alfa`.
- `pages/14_📋_Catálogo_Paneles.py`: columna «α Isc (%/°C)» en la edición.
- Manual del Asistente, sección 111; registro.

## Archivos modificados

- `bipv_python/datos/catalogo_paneles_excel.py`
- `bipv_python/pages/14_📋_Catálogo_Paneles.py`
- `bipv_python/tests/test_coef_isc_catalogo.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
