# Spec — «Calidad del módulo» y «Mismatch» por separado, como en PVsyst

**Estado:** validación

## Alcance de la fase

🔀 Mismatch (sección «⚙️ 3. Otras pérdidas del sistema»), los dos motores de
📊 Producción (`calculos/produccion.py`, `calculos/produccion_iv.py`), el
Loss Diagram de Producción, la firma de vigencia de Producción, la cadena de
pérdidas multi-superficie y los comparadores que usan la misma pérdida.

## Problema a resolver

La app tiene un solo control, «🔩 Mismatch de fabricación» (0–3 %), que el
motor aplica como pérdida del módulo. PVsyst separa dos pérdidas:

- «Module quality loss»: diferencia entre la potencia real y la de la ficha
  (puede ser negativa: ganancia por tolerancia positiva).
- «Mismatch loss, modules and strings»: módulos y strings que no trabajan
  exactamente en el mismo punto.

En la comparación con PVsyst del proyecto agrivoltaico de Apartadó
(29-sep-2026) PVsyst usa calidad 3.00 % y mismatch 2.10 %: juntas
1 − 0.97 × 0.979 = 5.04 %. El control de la app llega a 3.0 %, así que la
app sale ≈ 2 % por encima de PVsyst solo por esto, y el Loss Diagram muestra
una sola fila donde PVsyst muestra dos.

## Contexto

`pct_mismatch_fab` también lo usan la cadena multi-superficie, los
comparadores de paneles y de orientación, 🤖 Análisis IA y la firma de
vigencia de Producción.
