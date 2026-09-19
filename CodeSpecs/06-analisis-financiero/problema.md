# Módulo 06 — Análisis financiero

**Estado:** completado

## Alcance de la fase

Ahorro, tarifa, flujo de caja, retorno, TIR y periodo de recuperación.

## Problema a resolver

Finanzas puede restaurar resultados persistidos de Producción en una pestaña
nueva. Tras introducir una firma de vigencia para evitar reutilizar energía de
otra configuración, Finanzas y Presupuesto aún no reconstruyen la firma esperada
antes de solicitar la restauración; por seguridad, esta queda rechazada.

## Contexto

`calculos/persistencia_resultados.py` exige coincidencia de
`produccion_run_signature_v1`. Las páginas `7_💰_Financiero.py` y
`8_💼_Presupuesto.py` son consumidores downstream de Producción y deben
reconstruir la firma usando la configuración vigente antes de restaurar. Hasta
entonces, el usuario debe volver a ejecutar Producción; es seguro, pero menos
cómodo.
