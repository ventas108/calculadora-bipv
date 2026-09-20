# Implementación — Conservación óptica al adoptar inversor

**Estado:** completado

## Cambios realizados

- Se agregó `ESTADO_MOTOR_OPTICO` como fuente única de las 15 claves ópticas
	independientes del inversor, incluidas ambas POA y el soiling personalizado.
- Se derivó `KEYS_DERIVADOS_INVERSOR` como la diferencia entre todos los
	derivados de POA y el estado óptico conservable.
- Se implementó `invalidar_por_cambio_inversor()`, idempotente y compatible con
	`st.session_state` o un diccionario de prueba.
- El comparador delega la transición a esa función y dejó de mantener la
	exclusión local limitada a `poa_efectiva_df`.
- El mensaje de adopción informa que Motor Óptico se conserva y exige recalcular
	Producción y Financiero.
- Se añadió una prueba integrada que confirma que Producción vuelve a seleccionar
	exactamente `poa_sin_termico_df` después de la transición.

## Archivos modificados

- `bipv_python/calculos/invalidacion.py`
- `bipv_python/pages/4b_⚖️_Comparador_Inversores.py`
- `bipv_python/tests/test_pagina_comparador_inversores.py`
- `bipv_python/tests/test_invalidacion_cambio_inversor.py`

No se modificaron fórmulas físicas, React, comparador de orientación,
Multi-Superficie ni firmas de tablas/IA.
