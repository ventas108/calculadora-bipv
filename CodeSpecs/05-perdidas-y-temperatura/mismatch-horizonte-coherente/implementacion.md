# Implementación — 🔀 Mismatch: horizonte hora a hora y cascada coherente

**Estado:** validación

## Cambios realizados

- `calculos/mismatch.py`:
  - `DEFAULTS_MISMATCH`, `VERSION_MISMATCH = 2`, `CLAVE_VERSION_MISMATCH`.
  - `calcular_sombreado_horizonte`: pérdida = luz directa frontal de las horas
    bloqueadas; agrega `factor_horario`, `solo_directa` y `firma`.
  - `factor_horizonte_horario`, `firma_horizonte`, `aplicar_factor_horario`.
  - `publicar_cascada_mismatch`: cascada visible (sin filas eléctricas en 0,
    suciedad «la aplica 🔆 Motor Óptico» si corresponde) y factores para
    Producción sin horizonte.
  - `factores_mismatch_produccion`: factor escalar + factor horario
    (horizonte; en bifacial sin Motor Óptico, suciedad sobre la cara frontal
    que queda tras el horizonte); estado anterior sin marca de versión: el
    escalar de antes y aviso.
- `calculos/mismatch_bypass.excluir_horas_horizonte`: FS 3D = 0 en las horas
  de horizonte.
- `calculos/invalidacion.py`: `factor_mismatch_aplicado` caduca con Producción.
- `pages/5_🔀_Mismatch.py`:
  - Horizonte y orientaciones se recalculan solos si cambian sus datos o la
    POA.
  - Nota «solo luz directa, hora a hora».
  - Control de suciedad deshabilitado con Motor Óptico (muestra su valor).
  - Valores por defecto desde `DEFAULTS_MISMATCH`.
  - Cascada con `publicar_cascada_mismatch`, «Factor sobre la irradiancia» y
    tabla «Pérdidas que 📊 Producción aplica sobre la potencia».
  - Bypass: se retira la casilla del horizonte; `excluir_horas_horizonte`.
- `pages/6_📊_Produccion.py`: `factores_mismatch_produccion` y
  `aplicar_factor_horario` antes de la firma y de la simulación; nota del
  horizonte, avisos, aviso si 🔀 Mismatch no se abrió y
  `factor_mismatch_aplicado`.
- `pages/10_📄_Reporte_PDF.py`: muestra `factor_mismatch_aplicado`.
- Pruebas de páginas que buscaban el código anterior
  (`test_produccion_pagina_vigencia.py`, `test_pagina_perdida_ohmica.py`)
  ahora verifican la función que publica, con números donde se puede.
- Manual del Asistente, sección 85; contrato de 05 y registro de decisiones.

## Archivos modificados

- `bipv_python/calculos/mismatch.py`
- `bipv_python/calculos/mismatch_bypass.py`
- `bipv_python/calculos/invalidacion.py`
- `bipv_python/pages/5_🔀_Mismatch.py`
- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/pages/10_📄_Reporte_PDF.py`
- `bipv_python/tests/test_mismatch_horizonte_coherente.py`
- `bipv_python/tests/test_produccion_pagina_vigencia.py`
- `bipv_python/tests/test_pagina_perdida_ohmica.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
