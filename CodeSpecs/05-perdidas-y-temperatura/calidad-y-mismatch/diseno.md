# Diseño — «Calidad del módulo» y «Mismatch» por separado

**Estado:** validación

## Entradas

- `st.session_state["pct_calidad_modulo"]` (−2.0 a 5.0 %, por defecto 0.0).
- `st.session_state["pct_mismatch_fab"]` (0 a 4 %, igual que antes).

## Salidas

- `calculos/mismatch.py`:
  - `pct_perdida_modulos(calidad, mismatch) -> float`: pérdida combinada
    `(1 − (1 − c/100)(1 − m/100)) × 100`.
  - `CLAVE_CALIDAD_MODULO = "pct_calidad_modulo"`.
- `simular_produccion_anual` y `simular_produccion_iv`: parámetro
  `pct_calidad_modulo=None`; resultado con `pct_calidad_modulo_aplicado` y
  `perdida_calidad_modulo_kWh`; `perdida_mismatch_fab_kWh` queda solo con el
  mismatch.
- `perdidas_desglosadas`: fila «②c0 Calidad del módulo (aplicado)» y fila
  «②c Mismatch módulos y strings (aplicado)»; la última fila del bloque se
  ajusta a `E_dc_anual_kWh` (sin residuo de redondeo).
- Firma de vigencia de Producción: campo `pct_calidad_modulo`.
- `parametros_cadena`: `pct_mismatch_fab` pasa a ser la pérdida combinada.
- Comparadores de paneles y de orientación, 🤖 Análisis IA: pérdida combinada
  en `BIPVConfiguration.pct_mismatch_fab`.

## Tipos de datos

`float` (porcentajes) y `dict` de resultados.

## Errores posibles

- Sin calidad en la sesión (proyecto anterior): 0.0 %, mismo resultado que
  antes.
- Calidad negativa: Pmax sube (ganancia), la fila del Loss Diagram muestra
  Δ positivo.

## Dependencias

Ninguna nueva.

## Criterios de aceptación

1. Con calidad 3.0 y mismatch 2.1, los dos motores aplican
   0.97 × 0.979 = 0.94963 sobre la energía DC antes de cables, y reportan la
   pérdida de cada una por separado (sumas exactas).
2. Sin calidad (None o 0) los dos motores dan exactamente lo mismo que antes.
3. El Loss Diagram muestra dos filas y reconcilia hasta E_dc sin residuo.
4. Cambiar la calidad cambia la firma de vigencia de Producción.
5. La cadena multi-superficie y los comparadores usan la pérdida combinada.
6. 🔀 Mismatch muestra los dos controles y guarda `pct_calidad_modulo`.
7. El manual del Asistente explica las dos pérdidas con el caso Apartadó.
