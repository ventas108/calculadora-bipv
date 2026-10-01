# Propuesta — Comparador y Dimensionamiento con el mismo margen de Voc

**Estado:** validación

## Objetivo

Que el comparador, el reporte y el optimizador de Dimensionamiento usen el
mismo margen de seguridad y recomienden el mismo N.

## Alternativa recomendada

Aprobada por el usuario el 1-oct-2026 («Sí, prepara como un PR corto»).

- `comparador_inversores.MARGEN_VOC_MIN_PCT` = `dimensionamiento.UMBRAL_ALERTA_PCT` (7,5 %).
- Orden en `mejor_n_por_inversor`: margen ≥ 7,5 %, luego reparto exacto,
  luego string más largo.
- `ficha_inversor.margen_voc`: 🟠 por debajo del 7,5 %.
- Manual del Asistente: secciones 103 y 104 al día y sección 105.

## Alternativas descartadas

- Bajar el margen del optimizador al 3 %: es el criterio de la hoja Excel
  original validada; 11 V de margen es poco para el día más frío.

## Fuera de alcance

- Cambiar el optimizador de Dimensionamiento.
