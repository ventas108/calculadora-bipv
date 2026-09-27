# Implementación — Parámetros de Financiero persistentes

**Estado:** validación

## Cambios realizados

- `calculos/campos_persistentes.py` (nuevo): `campo_persistente`,
  `valor_inicial`, `clave_widget`.
- `pages/7_💰_Financiero.py`: tarifa de excedentes
  (`tarifa_excedentes_cop_kWh`), estructura (`fin_costo_estructura_usd_kw`),
  instalación (`fin_costo_instalacion_pct`), imprevistos (`fin_imprevistos_pct`),
  escalación de tarifa (`fin_esc_tarifa_pct`) y de O&M (`fin_esc_opex_pct`),
  O&M %CAPEX (`fin_opex_pct_capex`), WACC (`fin_tasa_desc_pct`), horizonte
  (`fin_n_anos`) y tasa de renta (`fin_tasa_renta_pct`) con `campo_persistente`.
- `tests/test_sincronizacion_consumo_y_excedentes.py`: la prueba del campo de
  excedentes comprueba la forma nueva con el mismo valor por defecto.

## Archivos modificados

- `bipv_python/calculos/campos_persistentes.py`
- `bipv_python/pages/7_💰_Financiero.py`
- `bipv_python/tests/test_campos_persistentes_financiero.py`
- `bipv_python/tests/test_sincronizacion_consumo_y_excedentes.py`
- `bipv_python/tests/test_asistente_retrieval.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
