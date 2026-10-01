# Propuesta — Reporte en Word editable y PDF sin perder gráficas

**Estado:** validación

## Objetivo

Descargar el mismo reporte como Word editable y PDF, con todas sus tablas y
gráficas.

## Alternativa recomendada

Aprobada por el usuario el 1-oct-2026 («entrégame una alternativa…»).

- `calculos/svg_a_png.py`: dibuja con Pillow los SVG del reporte (`rect`,
  `line`, `polyline`, `polygon`, `circle`, `text`, `viewBox`).
- `calculos/reporte_documentos.py`: recorre el HTML una vez (bloques:
  títulos, párrafos, notas, listas, tablas, imágenes) y arma el .docx
  (python-docx, carta) y el PDF (fpdf2, DejaVu, carta).
- 📄 Reporte PDF: botones Word, PDF y HTML; CSS de impresión con colores y sin
  partir tablas ni gráficas.
- Manual del Asistente, sección 106.

## Alternativas descartadas

- Convertir con LibreOffice, WeasyPrint o un navegador en el servidor:
  dependencias de sistema que no están instaladas.
- Rehacer cada gráfica en matplotlib: dos versiones de cada gráfica que
  podrían diferir.

## Fuera de alcance

- Plantillas de Word con la marca de la empresa.
