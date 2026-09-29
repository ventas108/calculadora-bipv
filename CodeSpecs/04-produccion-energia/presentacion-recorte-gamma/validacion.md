# Validación — 📊 Producción: recorte del inversor y γ bien presentados

**Estado:** validación

## Checklist de validación del módulo

- [x] 10 pruebas nuevas en `tests/test_produccion_presentacion.py`: en `main`
  el archivo no se puede cargar (no existe `calculos.formato_produccion`);
  con el cambio pasan. Cubren el formato de todas las columnas de
  `df_mensual` en los dos motores, `4927.475563` → `4,927`, `Tk_gamma_pct`
  en los dos motores, la nota con γ, la ficha sin γ («—») y la página con el
  formato compartido.
- [x] Pruebas existentes de la tabla de balance y de la página de Producción
  (`test_perdidas_desglosadas_pvsyst.py`, `test_produccion_pagina_vigencia.py`)
  siguen verdes.
- [x] Prueba de referencia en `test_consistencia_sdm_entre_modulos.py`: los dos
  motores devuelven el mismo γ de la ficha.
- [x] Suite completa de `bipv_python`: 2109 pruebas pasan.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR.
