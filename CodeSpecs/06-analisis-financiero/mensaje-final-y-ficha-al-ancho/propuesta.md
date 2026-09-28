# Propuesta — Mensaje final de Financiero y Ficha RETIE al ancho

**Estado:** validación

## Objetivo

Que el resumen nombre los paneles reales y muestre todos sus indicadores, y
que la ficha se lea sin desplazarse de lado.

## Alternativa recomendada

Aprobada por el usuario el 28-sep-2026.

- `lectura_financiera.rotulo_modulos`: «112 ASP-ST1-T40 + 4 SPR-…» con el
  sistema publicado; si no, «N módulos panel».
- `lectura_financiera.mensaje_resumen_financiero`: cada parte por separado.
- Ficha: `st.image(svg, use_column_width=True)`; el SVG escala con su viewBox.
  Las descargas conservan el tamaño original.

## Fuera de alcance

- Cambiar el contenido de la ficha o los cálculos.
