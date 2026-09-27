# Spec — Lectura de resultados de Financiero: umbral de tarifa, flujo y LCOE

**Estado:** validación

## Alcance de la fase

App Streamlit (`bipv_python/`): tabla de sensibilidad de tarifa, tabla de
flujo de caja anual, métrica y resumen del LCOE de `pages/7_💰_Financiero.py`.
Sin cambios en `calculos/financiero.py`. Evidencia: prueba del proyecto de un
cliente en Bogotá (8,36 kWp, 6.155 kWh/año, tarifa 1.200 COP/kWh), 27-sep-2026.

## Problema a resolver

1. **Umbral de tarifa falso.** La tabla decía «Umbral mínimo (VPN ≈ 0):
   600 COP/kWh», pero la fila de 650 COP/kWh tenía VPN −662 USD. La búsqueda
   solo probaba precios de 50 a 600 COP/kWh; si el umbral real era mayor, se
   quedaba en 600. El real era unos 677 COP/kWh. La leyenda además decía
   «Amarillo = rentable con menor margen» cuando las filas amarillas tenían
   VPN negativo.
2. **Decimales en el flujo de caja.** Autoconsumo y Exportación salían como
   «5018.000000».
3. **LCOE comparado con la tarifa del año 1.** El resumen decía «LCOE 1.564
   COP/kWh > tarifa 1.200» y parecía que el proyecto no se pagaba, aunque el
   VPN era positivo: la tarifa sube cada año y los excedentes tienen su propia
   tarifa. Tampoco se explicaba por qué el LCOE es igual con y sin Ley 1715.

## Contexto

- El flujo de caja y el LCOE salen de `calculos/financiero.py`
  (`calcular_flujo_caja`, `calcular_metricas`, `comparativo_ley_1715`).
- Spec `06-analisis-financiero/indicadores-excedentes`: reparto autoconsumo /
  excedentes con `frac_exportada` y la tarifa de excedentes.
