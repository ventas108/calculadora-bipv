# Diseño — Ficha RETIE en Word editable, PDF y PNG

**Estado:** validación

## Entradas

`svg`, `config`, `calc` y `checks` de la página (los mismos que dibujan la
ficha).

## Salidas

`documentos_ficha_retie(svg, cfg, calc, checks)` → `{"png", "docx", "pdf"}`.

- PNG: 2.400 px de ancho, proporción de la ficha.
- Word: sección 1 carta horizontal con la ficha; sección 2 carta vertical con
  «Datos del proyecto» y «Validaciones» (Estado, Validación, Detalle).
- PDF: hoja 1 horizontal con la ficha; hoja 2 vertical con los mismos datos.

## Tipos de datos

`bytes`, `dict`.

## Errores posibles

Si falla la conversión, la página avisa y deja el SVG.

## Dependencias

Pillow, lxml, python-docx, fpdf2, matplotlib (DejaVu), fontTools: las mismas
del Reporte.

## Criterios de aceptación

1. PNG sin CairoSVG, con el tamaño y los colores de la ficha.
2. `path` dibujado y `<defs>` omitido.
3. Word con la ficha en horizontal y todas las validaciones en una tabla.
4. PDF con la ficha en horizontal y las validaciones en texto.
5. La página ofrece Word editable, PDF, PNG y SVG.
6. El manual del Asistente lo explica (sección 110).
