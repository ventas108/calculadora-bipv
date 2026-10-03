# Implementación — Sombra por string

**Estado:** validación

## Cambios realizados

- `calculos/sombras_3d.py`: `fraccion_modulos_sombra` y `profundidad_sombra`
  por superficie (umbral 0,05; `None` con un solo punto).
- `calculos/mismatch_bypass.py`: `profundidad_sombra` opcional; con valor,
  el string toma el máximo entre el punto con bypass y sin bypass.
- `calculos/vinculador_sombra_multisuperficie.py`: los dos campos en
  `_CAMPOS_SOMBRA` y `_CAMPOS_SOMBRA_HORARIA`; `aplicar_sombra_a_superficies`
  los copia o los retira.
- `calculos/adaptador_multisuperficie.py`: los pasa a cada unidad física.
- `calculos/transicion_multisuperficie.py`: el bypass los usa cuando existen;
  un cambio de geometría los retira.
- `calculos/persistencia_multisuperficie.py`: se guardan y se restauran.

## Archivos modificados

- `bipv_python/calculos/sombras_3d.py`
- `bipv_python/calculos/mismatch_bypass.py`
- `bipv_python/calculos/vinculador_sombra_multisuperficie.py`
- `bipv_python/calculos/adaptador_multisuperficie.py`
- `bipv_python/calculos/transicion_multisuperficie.py`
- `bipv_python/calculos/persistencia_multisuperficie.py`
- `bipv_python/tests/test_sombra_por_string.py`
- `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`
- `bipv_python/datos/base_conocimiento_asistente.md` (sección 123)
- `CodeSpecs/00-director/registro-de-decisiones.md`
- `CodeSpecs/05-perdidas-y-temperatura/sombra-cara-trasera/` (nombre
  comercial reemplazado por «app estándar de referencia»)
