# Propuesta — Informes

**Estado:** completado

## Objetivo

Formalizar el contrato de Informes como consumidor de `04-produccion-energia`,
`05-perdidas-y-temperatura` y `06-analisis-financiero`, dejando explícito que
la vigencia de los datos se garantiza aguas arriba (gates de Producción y la
verificación de payload de Financiero), no dentro de este módulo.

## Alternativas consideradas

1. **No documentar nada** — descartada: sin contrato publicado, un cambio
   futuro en las claves de energía (`E_ac_anual_kWh*`) podría romper Informes
   sin que nadie lo note en el director.
2. **Duplicar la verificación de firma/payload dentro de Reporte PDF** —
   descartada: no se encontró evidencia de que Reporte PDF, Baterías o CO₂
   restauren nada por su cuenta; agregar una verificación redundante ahí
   duplicaría lógica sin cerrar ningún riesgo real.
3. **Documentar el contrato tal como existe hoy**, dejando constancia explícita
   de que la garantía de vigencia vive en `04` y `06`, no aquí.

## Alternativa recomendada

La 3: regularización documental sin cambios de código. Si en el futuro alguna
página de Informes empieza a restaurar resultados por su cuenta, esa Spec
deberá reabrirse con el mismo rigor que `06`.

