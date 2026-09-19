# Módulo 07 — Informes

**Estado:** completado

## Alcance de la fase

Gráficas, tablas, exportación y presentación de resultados al usuario.

## Problema a resolver

Este módulo (`10_📄_Reporte_PDF.py`, `11_🔋_Baterias_y_Balance.py`,
`12_🌿_Impacto_CO2.py`) nunca tuvo su contrato SDD formalizado. A diferencia de
`06-analisis-financiero`, la exploración no encontró un gap de coherencia
nuevo: estas páginas no restauran resultados persistidos por su cuenta — solo
leen `session_state` con la misma prioridad de energía
(multi-superficie > bypass > base) que ya usa Financiero, y confiían en que
`04-produccion-energia` ya validó vigencia antes de escribir esas claves. El
Ledger de Auditoría además sella un hash de insumos+resultados en el momento
exacto de generar el reporte.

## Contexto

Regularización documental, no correctiva: fijar el contrato real de entrada
(banderas `_ok`, prioridad de energía, resultados financieros) y confirmar por
escrito que ninguna página de este módulo introduce una vía de restauración
propia que deba protegerse como se hizo en `06`.

