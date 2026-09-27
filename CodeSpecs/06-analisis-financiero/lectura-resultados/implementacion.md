# Implementación — Lectura de resultados de Financiero

**Estado:** validación

## Cambios realizados

- `calculos/lectura_financiera.py` (nuevo): `umbral_vpn_cero` y
  `valor_nivelado_energia`.
- `pages/7_💰_Financiero.py`:
  - la sensibilidad usa `umbral_vpn_cero`; fila del umbral ordenada por precio,
    o leyenda «sin umbral»; leyenda de colores corregida;
  - tabla de flujo: Autoconsumo y Exportación con formato `{:,.0f}`;
  - nota «Cómo leer el LCOE» bajo el comparativo; la métrica LCOE y el
    resumen lo comparan con el valor nivelado de la energía.

## Archivos modificados

- `bipv_python/calculos/lectura_financiera.py`
- `bipv_python/pages/7_💰_Financiero.py`
- `bipv_python/tests/test_lectura_financiera.py`
- `bipv_python/tests/test_asistente_retrieval.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
