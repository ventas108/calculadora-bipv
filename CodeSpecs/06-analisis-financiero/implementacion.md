# Implementación — Análisis financiero

**Estado:** completado

## Cambios realizados

- `construir_payload_produccion_run_signature_v1()` y `firma_desde_payload()`
  separan el payload canónico (pre-hash) del cálculo de la firma;
  `calcular_produccion_run_signature_v1()` queda como envoltorio de ambas —
  mismo contrato, mismo resultado.
- Producción guarda el payload en `session_state[CLAVE_PAYLOAD_FIRMA]` en
  sincronía con la firma, en la rama de simulación nueva y en la de
  reutilización validada; lo limpia cuando la vigencia se invalida.
- `guardar_resultados_produccion()` persiste ese payload junto a la firma;
  `restaurar_resultados_produccion()` ya no compara contra una firma
  "esperada" en sesión (que Finanzas/Presupuesto no tienen) sino que
  recalcula el SHA-256 del payload persistido y exige coincidencia exacta.
- La huella de ciudad/coordenadas se sigue evaluando antes que el payload.

## Archivos modificados

- `bipv_python/calculos/produccion_vigencia.py`
- `bipv_python/calculos/persistencia_resultados.py`
- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/tests/test_produccion_vigencia.py`
- `bipv_python/tests/test_produccion_pagina_vigencia.py`
- `bipv_python/tests/test_seleccion_poa_bypass_pagina5.py`
- `bipv_python/scripts/test_persistencia_89_94_114.py`

