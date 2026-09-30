# Propuesta — Reporte PDF de producción completo para el cliente

**Estado:** validación

## Objetivo

Que el reporte muestre todo lo que la app calcula para la producción, con
los mismos números de las páginas, y que la parte financiera se pueda quitar.

## Alternativa recomendada

Aprobada por el usuario el 30-sep-2026 («prepara ya esa Spec con su PR»).

- `calculos/reporte_produccion.py` (sin Streamlit): `filas_sistema_electrico`,
  `filas_perdidas` (la misma `produccion.perdidas_desglosadas` de la página),
  `filas_bifacial` y `secciones_granja` (campo, energía, agrivoltaica,
  seguidor, eléctrico con `granja_electrico.diseno_desde_estado`). Solo leen
  lo calculado; no recalculan energía.
- 📊 Producción guarda `produccion_n_inversores` y `produccion_p_ac_total_w`
  (los inversores con que simuló).
- 📄 Reporte PDF: sección «🔌 Sistema Eléctrico e Inversores» (la casilla
  Dimensionamiento ahora sí genera), «📉 Diagrama de Pérdidas», datos
  bifaciales completos y «🌾 Granja FV», con sus casillas; el HTML generado
  queda en `_reporte_html` (temporal, no se guarda con el proyecto).
- Manual del Asistente, sección 101 (cómo sacarlo sin la parte financiera).

## Alternativas descartadas

- Calcular de nuevo las pérdidas en el reporte: dos cálculos de la misma
  magnitud; se usa la función de Producción.
- Quitar la parte financiera del código: el usuario la quiere después; se
  desmarca con su casilla.

## Fuera de alcance

- Gráficas nuevas (perfil de luz, plano eléctrico) dentro del PDF.
- Exigir la TRM solo cuando hay parte financiera (comportamiento actual).
