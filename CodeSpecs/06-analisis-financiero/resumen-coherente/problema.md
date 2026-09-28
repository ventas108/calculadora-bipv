# Spec — Resumen coherente de Financiero: ahorro, rótulo P90 y etiquetas de payback

**Estado:** validación

## Alcance de la fase

App Streamlit (`bipv_python/`): tarjeta «Ahorro estimado» del panel «Consumo vs
Producción estimada», rótulos del escenario P90 y etiquetas de payback de la
gráfica de flujo acumulado en `pages/7_💰_Financiero.py`. Sin cambios en
`calculos/financiero.py`. Evidencia: proyecto del cliente en Bogotá,
27-sep-2026 (5.943 kWh/año, consumo 5.738 kWh/año, 693 kWh exportados,
tarifa 1.200 COP/kWh, excedentes 800 COP/kWh).

## Problema a resolver

1. **Dos ahorros distintos en la misma página.** «Ahorro estimado» decía
   6,89 M COP/año (todo el consumo × 1.200) y «Ahorro energía año 1»
   6,85 M COP/año (autoconsumo × 1.200 + excedentes × 800). El segundo es el
   que usan TIR y VPN; el primero ignoraba la tarifa de excedentes.
2. **Rótulo P90 redondeado.** La columna decía «P90 (−10%)» y el texto de
   arriba «−9,5 %» para el mismo factor.
3. **Etiquetas encimadas.** «Payback P50: 6,7 a» y «Payback sin 1715: 10,0 a»
   se escribían a la misma altura y se tapaban.

## Contexto

- Spec `06-analisis-financiero/indicadores-excedentes`: `ahorro_anual_cop`.
- Spec `06-analisis-financiero/parametros-persistentes`: la tarifa de
  excedentes vive en `tarifa_excedentes_cop_kWh`.
