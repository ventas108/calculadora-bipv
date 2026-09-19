# Implementación — Dimensionamiento eléctrico

**Estado:** completado

## Cambios realizados

- `diseno_electrico_confirmado()` concentra el estado confirmado y detecta cambios
	posteriores de panel o inversor.
- El prorrateo preliminar conserva su firma de entrada y se descarta si cambia el
	modelo, panel o `N_str_tr` efectivo.
- `mapear_inversores_catalogo()` devuelve `No evaluable` para fichas incompletas o
	valores no finitos, sin ofrecerlas como compatibles.

## Archivos modificados

- `bipv_python/calculos/dimensionamiento.py`
- `bipv_python/pages/4_📐_Dimensionamiento.py`
- `bipv_python/tests/test_compatibilidad_string.py`
