# Implementación — Tensión máxima de sistema del módulo en el límite del Voc

**Estado:** validación

## Cambios realizados

- `calculos/tension_modulo.py` (nuevo).
- Límite del Voc en `dimensionamiento.py`, `comparador_inversores.py`,
  `diseno_electrico_multisup.py`, `ficha_inversor.py` y
  `ficha_validacion_retie.py`.
- Catálogo: `datos/catalogo_paneles_excel.py`, `datos/tecnologias_bipv.py`,
  extractor de fichas PDF y 📋 Catálogo de Paneles.
- Páginas 📐 Dimensionamiento, 📋 Ficha RETIE y 📄 Reporte PDF.
- Manual del Asistente; registro.

## Archivos modificados

- `bipv_python/calculos/tension_modulo.py`
- `bipv_python/calculos/dimensionamiento.py`
- `bipv_python/calculos/comparador_inversores.py`
- `bipv_python/calculos/diseno_electrico_multisup.py`
- `bipv_python/calculos/ficha_inversor.py`
- `bipv_python/calculos/ficha_validacion_retie.py`
- `bipv_python/calculos/pdf_panel_extractor.py`
- `bipv_python/datos/catalogo_paneles_excel.py`
- `bipv_python/datos/tecnologias_bipv.py`
- `bipv_python/pages/4_📐_Dimensionamiento.py`
- `bipv_python/pages/14_📋_Catálogo_Paneles.py`
- `bipv_python/pages/21_📋_Ficha_Validacion_RETIE.py`
- `bipv_python/pages/10_📄_Reporte_PDF.py`
- `bipv_python/tests/test_tension_maxima_modulo.py`
- `bipv_python/tests/test_manual_corrida_teusaquillo.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
