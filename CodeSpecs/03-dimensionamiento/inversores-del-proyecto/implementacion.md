# Implementación — Cantidad de inversores del proyecto elegida por el diseñador

**Estado:** validación

## Cambios realizados

- `calculos/dimensionamiento.py`: `DCAC_OBJETIVO`, `resolver_inversores`,
  `inversores_para_dcac`, `inversores_fijados_vigentes`;
  `proyecto_completo(..., N_inversores_fijado)` y
  `escalar_p_ac_nom_por_inversores(..., n_inversores_fijado)` (mínimo hacia
  arriba).
- `pages/4_📐_Dimensionamiento.py`: campo «Cantidad de inversores del
  proyecto» (`campo_persistente`, vuelve a 0 al cambiar de modelo), pasado a
  los dos «Proyecto completo»; textos «mínimo»/«fijados por ti», aviso 🟠 de
  ajuste y 💡 para DC/AC ≤ 1,3.
- `pages/6_📊_Produccion.py`: cantidad fijada vía
  `inversores_fijados_vigentes`; texto «DC/AC y recorte con N inversores
  fijados».
- `pages/8_💼_Presupuesto.py`: cotiza `N_inv_total` inversores.
- Manual del Asistente, sección 90, con la guía rápida de alarmas (pedido del
  usuario: que oriente de forma simple qué significa cada color y qué hacer);
  contratos y registro de decisiones.

## Archivos modificados

- `bipv_python/calculos/dimensionamiento.py`
- `bipv_python/pages/4_📐_Dimensionamiento.py`
- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/pages/8_💼_Presupuesto.py`
- `bipv_python/tests/test_inversores_del_proyecto.py`
- `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
