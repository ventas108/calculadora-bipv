# Diseño — Reporte en Word editable y PDF sin perder gráficas

**Estado:** validación

## Entradas

El HTML del reporte (`generar_html_reporte`).

## Salidas

- `.docx` (bytes): carta, márgenes 1,8 cm, Calibri 10, títulos, párrafos,
  notas sombreadas, listas, tablas «Table Grid» con fondos, imágenes a todo
  el ancho.
- `.pdf` (bytes): carta, márgenes 15 mm, DejaVu, títulos de sección con
  fondo, tablas con anchos según la palabra más larga, imágenes enteras.

## Tipos de datos

`bytes`, `list[dict]` (bloques).

## Errores posibles

- Una gráfica que no se pueda dibujar queda fuera (el resto sigue).
- Si falla la conversión, la página avisa y deja el HTML.
- Emojis que la fuente del PDF no tiene se quitan; los de estado se dibujan
  como ● de color.

## Dependencias

python-docx, fpdf2, Pillow, lxml, matplotlib (fuente DejaVu), fontTools.

## Criterios de aceptación

1. Las figuras SVG del reporte pasan a PNG con su tamaño (`viewBox` en
   mayúsculas o minúsculas) y colores.
2. El Word tiene una imagen por cada SVG y las tablas y textos clave.
3. El PDF tiene una imagen por cada SVG y el texto clave.
4. La página genera Word y PDF al generar el reporte.
5. El manual del Asistente lo explica (sección 106).
