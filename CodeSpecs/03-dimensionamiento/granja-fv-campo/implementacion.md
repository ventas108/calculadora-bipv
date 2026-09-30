# Implementación — 🌾 Granja FV, fase 1: campo de filas coherente con el proyecto

**Estado:** validación

## Cambios realizados

- `calculos/granja_fv.py` (nuevo): `dimensiones_modulo`, `calcular_campo`,
  `sugerir_distribucion`, `modulos_del_proyecto`, `geometria_desde_estado`,
  `coherencia_campo`, `trazas_campo`.
- `pages/9b_🌾_Granja_FV.py` (nuevo): datos del proyecto, terreno y mesas
  (`campo_persistente`, guardado en `granja_fv`), «🪄 Sugerir distribución»,
  resultados, coherencia y 3D.
- `pages/9_🗺️_Vista_3D.py`: la rama de granja usa `calcular_campo` y
  `trazas_campo` con la geometría de `granja_fv` y remite a 🌾 Granja FV; se
  quitan sus campos y su cuenta propia de matrices.
- Manual del Asistente, sección 93; contratos y registro de decisiones.

## Archivos modificados

- `bipv_python/calculos/granja_fv.py`
- `bipv_python/pages/9b_🌾_Granja_FV.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_granja_fv.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
