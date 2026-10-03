# Implementación — Puntos automáticos por módulo

**Estado:** validación

## Cambios realizados

- `calculos/puntos_modulo.py` (nuevo): geometría, strings, texto y
  etiquetado.
- `calculos/sombras_3d.py`: `sombra_por_string`.
- `calculos/mismatch_bypass.py`: `simular_bypass_por_strings`.
- `calculos/adaptador_multisuperficie.py`: `sombra_strings` por grupo.
- `calculos/transicion_multisuperficie.py`: bypass por strings cuando la
  unidad los trae; un cambio de geometría los retira.
- `calculos/vinculador_sombra_multisuperficie.py`,
  `calculos/persistencia_multisuperficie.py`: el campo viaja, caduca y se
  guarda.
- `calculos/guia_vista_3d.py`: pasos y errores nuevos.
- `pages/9_🗺️_Vista_3D.py`: recuadro «🧮 Generar un punto por módulo».

## Archivos modificados

- `bipv_python/calculos/puntos_modulo.py`
- `bipv_python/calculos/sombras_3d.py`
- `bipv_python/calculos/mismatch_bypass.py`
- `bipv_python/calculos/adaptador_multisuperficie.py`
- `bipv_python/calculos/transicion_multisuperficie.py`
- `bipv_python/calculos/vinculador_sombra_multisuperficie.py`
- `bipv_python/calculos/persistencia_multisuperficie.py`
- `bipv_python/calculos/guia_vista_3d.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_puntos_por_modulo.py`
- `bipv_python/tests/test_sombra_por_string_individual.py`
- `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`
- `bipv_python/tests/test_guia_vista_3d.py`
- `bipv_python/datos/base_conocimiento_asistente.md` (secciones 125 y 126)
- `CodeSpecs/00-director/registro-de-decisiones.md`
