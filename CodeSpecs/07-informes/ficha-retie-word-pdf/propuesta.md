# Propuesta — Ficha RETIE en Word editable, PDF y PNG

**Estado:** validación

## Objetivo

Descargar la ficha como Word editable, PDF y PNG en el servidor, sin
programas externos.

## Alternativa recomendada

Aprobada por el usuario el 1-oct-2026 («aplica la misma solución que en
Reporte PDF»).

- `svg_a_png`: `path` de tramos rectos (M, L, H, V, Z), flechas
  `marker-end` y omitir `<defs>`.
- `exportar_ficha_png_bytes`: CairoSVG si existe; si no, `svg_a_png`.
- `calculos/ficha_retie_documentos.py`: Word (ficha en carta horizontal +
  hoja vertical con datos y tabla de validaciones editable) y PDF (igual).
- Página: botones Word editable, PDF, PNG y SVG.
- Leyenda «Verde/Naranja/Rojo» de la ficha 75 unidades más a la derecha (con
  DejaVu el título la tapaba).
- Manual del Asistente, sección 110.

## Alternativas descartadas

- Instalar CairoSVG en el servidor: depende de librerías de sistema (cairo)
  que hay que instalar a mano en cada despliegue.

## Fuera de alcance

- Incluir la ficha dentro del 📄 Reporte.
