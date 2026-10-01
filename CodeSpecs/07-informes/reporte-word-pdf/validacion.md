# Validación — Reporte en Word editable y PDF sin perder gráficas

**Estado:** validación

## Checklist de validación del módulo

- [x] 8 pruebas en `tests/test_reporte_word_pdf.py`:
  - SVG a PNG con su tamaño (viewBox en mayúsculas o minúsculas) y colores;
  - bloques del reporte de granja (una imagen por SVG, títulos, tablas);
  - Word editable: una imagen por SVG, tablas y textos clave, carta 1,8 cm;
  - PDF: una imagen por SVG y el texto clave;
  - la página genera Word y PDF; el manual lo explica (sección 106).
- [x] Con el código anterior no carga el archivo de pruebas (módulos nuevos).
- [x] Conversión del reporte real de la Granja Apartadó: 13 tablas y 6
  gráficas en Word y en PDF (7 páginas), revisado visualmente.
- [x] Guardia de física: sin cambios en fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2325 pruebas pasan.

## Resultado

Criterios 1 a 5 cumplidos. En espera de la revisión del PR.
