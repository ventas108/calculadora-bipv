# Implementación — 🌾 Granja FV, fase 3: agrivoltaica — luz para el cultivo, mapa de sombra y maquinaria

**Estado:** validación

## Cambios realizados

- `calculos/agrivoltaica.py` (nuevo): `geometria_corte`, `puntos_suelo`,
  `vista_cielo_suelo`, `sol_en_el_suelo`, `luz_en_el_suelo`,
  `paso_maquinaria`.
- `pages/9b_🌾_Granja_FV.py`: sección «6. 🌱 Agrivoltaica» (maquinaria,
  avisos, botón, métricas, perfil, mapa de sombra mensual); la vista 3D pasa
  a ser la sección 7; texto de la página al día.
- Manual del Asistente, sección 95; contratos y registro.

## Archivos modificados

- `bipv_python/calculos/agrivoltaica.py`
- `bipv_python/pages/9b_🌾_Granja_FV.py`
- `bipv_python/tests/test_granja_agrivoltaica.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
