# Implementación — «Proyecto completo» cabe en el área y respeta el total de cadenas

**Estado:** validación

## Cambios realizados

- `calculos/dimensionamiento.py`: `proyecto_completo()` cuenta strings
  completos (declarados o los que caben), inversores necesarios, reparto
  parejo, módulos, potencia, área, cobertura sin tope, m² que faltan y DC/AC
  del proyecto y del inversor más cargado.
- `pages/4_📐_Dimensionamiento.py`: `_mostrar_proyecto_completo()` muestra y
  publica el resultado en las dos secciones (prorrateo preliminar y
  resultado de «▶️ Optimizar N paneles/string»); la sección por inversor
  pasa a llamarse «📊 Un inversor lleno (todos sus MPPT)» y la relación DC/AC
  se evalúa con el sistema real. Nueva clave publicada:
  `reparto_strings_inversores`.
- Manual del Asistente, sección 80.

## Archivos modificados

- `bipv_python/calculos/dimensionamiento.py`
- `bipv_python/pages/4_📐_Dimensionamiento.py`
- `bipv_python/tests/test_proyecto_completo.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
