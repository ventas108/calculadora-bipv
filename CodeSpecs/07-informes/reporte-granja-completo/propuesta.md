# Propuesta — Reporte PDF de Granja FV completo y ficha del inversor

**Estado:** validación

## Objetivo

Que el reporte de una granja muestre lo mismo que ve el diseñador en 🌾
Granja FV, sin datos contradictorios ni textos de otro tipo de proyecto, y
que una ficha de inversor imposible se vea antes de dimensionar.

## Alternativa recomendada

Aprobada por el usuario el 1-oct-2026 («Prepara la Spec con su PR»).

- `calculos/reporte_granja.py` (sin Streamlit): redibuja en SVG fijo la vista
  3D del campo (oblicua, escala real, módulos con el color de su inversor), el
  plano eléctrico (planta, módulos por inversor y string, inversores, cable AC,
  punto de conexión), la luz en el suelo y el mapa de sombra mensual; trae el
  paso de la maquinaria, la coherencia del campo y la nota de strings que
  cruzan filas.
- `calculos/reporte_produccion.py`: `etiquetas_tipo`, `nota_poa`, `nota_pr`,
  `filas_mismatch`, `altitud_proyecto`, `aviso_soiling`.
- `calculos/ficha_inversor.py`: `alertas_ficha_inversor` y `margen_voc`.
- 📄 Reporte PDF y 📐 Dimensionamiento los usan.
- Manual del Asistente, sección 103.

## Alternativas descartadas

- Exportar las figuras de plotly a imagen: necesita un motor de imágenes en
  el servidor y no se imprime igual en Word.
- Corregir el Excel del catálogo en el repositorio: el catálogo vive en el
  servidor; se corrige desde 🔌 Catálogo Inversores.

## Fuera de alcance

- Cambiar el diseño del proyecto de Urabá (lo hace el usuario: 22 en serie).
- Rango MPPT a plena carga (la ficha no lo da).
