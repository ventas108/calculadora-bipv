# Implementación — Difusa en la sombra por string

**Estado:** validación

## Cambios realizados

- `calculos/sombras_3d.py`: `factor_cielo_visible` por superficie.
- `calculos/solar.py`: la reducción de difusa isotrópica deja la circunsolar
  en `attrs["poa_circumsolar"]`.
- `calculos/multi_superficie.py`: `reduccion_diffusa_isotropica` en
  `calcular_poa_superficie`.
- `calculos/mismatch_bypass.py`: `fraccion_directa` opcional.
- `calculos/transicion_multisuperficie.py`: POA reducida y fracción directa
  cuando la superficie trae el factor.
- `calculos/vinculador_sombra_multisuperficie.py`,
  `calculos/adaptador_multisuperficie.py`,
  `calculos/persistencia_multisuperficie.py`: el campo viaja, caduca y se
  guarda.

## Archivos modificados

- `bipv_python/calculos/sombras_3d.py`
- `bipv_python/calculos/solar.py`
- `bipv_python/calculos/multi_superficie.py`
- `bipv_python/calculos/mismatch_bypass.py`
- `bipv_python/calculos/transicion_multisuperficie.py`
- `bipv_python/calculos/vinculador_sombra_multisuperficie.py`
- `bipv_python/calculos/adaptador_multisuperficie.py`
- `bipv_python/calculos/persistencia_multisuperficie.py`
- `bipv_python/tests/test_difusa_sombra_por_string.py`
- `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`
- `bipv_python/datos/base_conocimiento_asistente.md` (sección 124)
- `CodeSpecs/00-director/registro-de-decisiones.md`
