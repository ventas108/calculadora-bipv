# Propuesta — Análisis financiero

**Estado:** aprobado

## Objetivo

Que `pages/7_💰_Financiero.py` y `pages/8_💼_Presupuesto.py` solo restauren
resultados persistidos de Producción cuando puedan verificar, de forma
determinista, que esos resultados corresponden a la firma
`produccion_run_signature_v1` con la que se guardaron — sin inventar un
fallback inseguro ni asumir que la firma persistida es correcta solo por
estar presente.

## Hallazgo de exploración (18/19-sep-2026)

Ambas páginas llaman `restaurar_resultados_produccion()` al inicio del
render, antes de cargar panel, inversor, TMY o POA — en una pestaña nueva
(el único caso real donde `restaurar_resultados_produccion()` hace algo,
ver docstring del módulo) esas páginas **no tienen ningún dato en vivo**
con qué reconstruir `calcular_produccion_run_signature_v1()`. Además,
`CLAVES_RESULTADOS` (`calculos/persistencia_resultados.py`) solo persiste
escalares (`E_ac_anual_kWh`, `panel_nombre_final`, etc.) y la firma final —
nunca el payload canónico que la produjo. El plan original ("reconstruir la
firma desde `session_state` de Finanzas/Presupuesto") es estructuralmente
inviable con el estado actual de persistencia.

## Alternativas consideradas

1. **Reconstruir la firma desde `session_state` de Finanzas/Presupuesto.**
   Inviable: esas páginas no cargan panel/inversor/TMY/POA: no hay insumos
   en vivo para recalcularla.
2. **Persistir también los arrays completos de TMY/POA** para poder
   recalcular la firma igual que Producción. Descartada: payload pesado en
   disco por usuario, y innecesaria — ya existen los fingerprints.
3. **Persistir el payload canónico (pre-hash) que ya usa
   `calcular_produccion_run_signature_v1()`** — fingerprints y escalares,
   sin arrays — junto a la firma. Al restaurar, se recalcula el SHA-256 de
   ese payload persistido y debe coincidir con la firma persistida
   (verificación de integridad de la propia foto persistida, sin depender
   de ningún estado en vivo).

## Alternativa recomendada

La 3: persistir el payload canónico junto a `produccion_run_signature_v1` y
verificar su consistencia interna al restaurar, reutilizando las funciones
puras existentes en `calculos/produccion_vigencia.py` (sin duplicar la
normalización ni la serialización). No se restaura nada si el payload falta,
no coincide con la firma, o la huella de ciudad/coordenadas ya no aplica.

