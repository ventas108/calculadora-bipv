# Diseño — Comparador y Dimensionamiento con el mismo margen de Voc

**Estado:** validación

## Entradas

Las mismas de `mejor_n_por_inversor` y `margen_voc`.

## Salidas

N recomendado por inversor y nivel 🟢/🟠 del margen de Voc.

## Tipos de datos

`pd.DataFrame`, `dict`.

## Errores posibles

Ninguno nuevo: si ningún N tiene margen, se elige entre los que solo
cumplen la ficha (🟠), como antes.

## Dependencias

`calculos/dimensionamiento.py` (`UMBRAL_ALERTA_PCT`, `optimizar_n_serie`),
`calculos/comparador_inversores.py`, `calculos/ficha_inversor.py`.

## Criterios de aceptación

1. Urabá (308, Growatt 1.100 V): el comparador da 20 en serie, 15 strings,
   8 + 7, 🟢; igual al «N óptimo» de `optimizar_n_serie`.
2. Con margen y reparto exacto (300 módulos) gana el exacto; un inversor de
   1.500 V sigue en 28.
3. El margen del reporte usa el mismo 7,5 %.
4. El manual del Asistente lo explica (sección 105).
