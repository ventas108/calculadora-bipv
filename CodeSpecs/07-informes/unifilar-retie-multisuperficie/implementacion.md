# Implementación — Diagrama Unifilar y Ficha RETIE con el sistema multi-superficie real

**Estado:** validación

## Cambios realizados

- `calculos/topologia_electrica.py` (nuevo): `construir_topologia`,
  `bateria_desde_estado`, `topologia_desde_estado`, `CLAVE_OPTIMIZADORES`,
  `CLAVE_BATERIA_INVERSOR`.
- `calculos/ficha_validacion_retie.py`: `calcular_retie_multisuperficie`,
  `validar_retie_multisuperficie`, `generar_ficha_svg(..., topologia=)`;
  tarjetas con el «dónde» en su propia línea y detalle partido en líneas;
  alto de la ficha según la tabla y las tarjetas.
- `calculos/diagrama_unifilar.py`: parámetro `topologia`, breakers por
  inversor y general (`_topologia_config`) y `_dibujar_topologia`; `_rect`
  con las dos esquinas ancladas al origen (antes `Rect(w, h)` se ignoraba y
  las cajas salían corridas, también en el modo de una superficie).
- `utils/sistema_electrico_ui.py` (nuevo): opciones del sistema
  (optimizadores, batería e inversor) y resumen del sistema.
- `pages/20_⚡_Diagrama_Unifilar.py`: selector «Sistema a dibujar»; en
  multi-superficie el diagrama sale de la topología y no se piden módulos a
  mano; `st.image(png_bytes)` (Streamlit 1.36 no acepta
  `use_container_width` en `st.image`: la página se caía siempre).
- `pages/21_📋_Ficha_Validacion_RETIE.py`: selector «Sistema a validar»,
  validación multi-superficie y detalle completo de cada validación.

## Archivos modificados

- `bipv_python/calculos/topologia_electrica.py`
- `bipv_python/calculos/ficha_validacion_retie.py`
- `bipv_python/calculos/diagrama_unifilar.py`
- `bipv_python/utils/sistema_electrico_ui.py`
- `bipv_python/pages/20_⚡_Diagrama_Unifilar.py`
- `bipv_python/pages/21_📋_Ficha_Validacion_RETIE.py`
- `bipv_python/tests/test_topologia_electrica.py`
- `bipv_python/tests/test_retie_unifilar_multisuperficie.py`
- `bipv_python/tests/test_pagina_diagrama_unifilar.py`
- `bipv_python/tests/test_asistente_retrieval.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/mapa-dependencias.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
