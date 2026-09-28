# Implementación — Resumen coherente de Financiero

**Estado:** validación

## Cambios realizados

- `calculos/indicadores_excedentes.py`: `tarifa_excedentes_vigente`.
- `calculos/lectura_financiera.py`: `etiquetas_payback`.
- `pages/7_💰_Financiero.py`: «Ahorro estimado» con `ahorro_anual_cop` y ayuda
  que explica la cuenta; rótulos P90 con `{factor_p90:.1f}`; líneas de payback
  con etiquetas escalonadas (`add_annotation`).

## Archivos modificados

- `bipv_python/calculos/indicadores_excedentes.py`
- `bipv_python/calculos/lectura_financiera.py`
- `bipv_python/pages/7_💰_Financiero.py`
- `bipv_python/tests/test_lectura_resumen_financiero.py`
- `bipv_python/tests/test_asistente_retrieval.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
