# Implementación — Modelo IV de paneles BIPV de capa fina (CIGS) sin parámetros de laboratorio

**Estado:** validación

## Cambios realizados

- `calculos/modelo_iv.py`:
  - `normalizar_tecnologia`;
  - factor de idealidad y coeficientes típicos por tecnología, incluido CIGS;
  - N_s estimado cuando la ficha no lo trae;
  - ajuste a 200 W/m² con el factor de idealidad;
  - marcas de origen.
- `datos/catalogo_paneles_excel.py`: `eficiencia_rel_200` desde
  `EficRel200Pct`.
- `pages/14_📋_Catálogo_Paneles.py`: columna «η rel. 200 W/m² (%)».
- `pages/3_🔬_Motor_IV.py`: bloque «Origen del modelo».
- Manual del Asistente, sección 112; registro.

## Archivos modificados

- `bipv_python/calculos/modelo_iv.py`
- `bipv_python/datos/catalogo_paneles_excel.py`
- `bipv_python/pages/14_📋_Catálogo_Paneles.py`
- `bipv_python/pages/3_🔬_Motor_IV.py`
- `bipv_python/tests/test_sdm_capa_fina_bipv.py`
- `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
