# Implementación — «Calidad del módulo» y «Mismatch» por separado

**Estado:** validación

## Cambios realizados

- `calculos/mismatch.py`: `CLAVE_CALIDAD_MODULO` y `pct_perdida_modulos()`.
- `calculos/produccion.py` y `calculos/produccion_iv.py`: parámetro
  `pct_calidad_modulo` aplicado antes del mismatch; resultado con
  `pct_calidad_modulo_aplicado` y `perdida_calidad_modulo_kWh`.
- `perdidas_desglosadas`: filas «②c0 Calidad del módulo» y «②c Mismatch
  módulos y strings»; la informativa solo sin ninguna de las dos.
- `calculos/produccion_vigencia.py`: la calidad entra en la firma solo si se
  aplica (las firmas guardadas no cambian).
- `calculos/cadena_perdidas_multisup.py`: pérdida combinada.
- Páginas: 🔀 Mismatch (dos controles), 📊 Producción (motor, firma y
  notas), comparadores de paneles y de orientación, 🤖 Análisis IA.
- Manual del Asistente, sección 81.

## Archivos modificados

- `bipv_python/calculos/mismatch.py`
- `bipv_python/calculos/produccion.py`
- `bipv_python/calculos/produccion_iv.py`
- `bipv_python/calculos/produccion_vigencia.py`
- `bipv_python/calculos/cadena_perdidas_multisup.py`
- `bipv_python/pages/5_🔀_Mismatch.py`
- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/pages/4c_🧩_Comparador_Paneles.py`
- `bipv_python/pages/4d_🧭_Comparador_Orientación.py`
- `bipv_python/pages/18_🤖_Análisis_IA.py`
- `bipv_python/tests/test_calidad_y_mismatch.py`
- `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
