# Implementación — Producción de energía

**Estado:** implementado retrospectivamente

## Cambios realizados

- La simulación anual exige compatibilidad eléctrica y vigencia del diseño
	confirmado. Si falla cualquiera, limpia resultados persistidos, marca
	`produccion_ok=False` y detiene la ejecución.
- Se añadió una prueba de regresión para impedir que este gate vuelva a ser
	solo informativo.

## Archivos modificados

- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/tests/test_pagina_produccion_diseno_vencido.py`
