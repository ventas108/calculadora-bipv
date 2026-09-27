# Implementación — Cadena de pérdidas multi-superficie

**Estado:** validación

## Cambios realizados

- `calculos/cadena_perdidas_multisup.py` (nuevo):
  - `parametros_cadena`: óptica de 🔆 Motor Óptico (o valores por defecto) y
    pérdidas de 🔀 Mismatch (o sus valores por defecto: 1 % y 1,5 %), sombra
    de horizonte `factor_sombra_anual`.
  - `cadena_superficie`: `cascada_optica` con la POA de la superficie (b0 del
    vidrio según Motor Óptico con el mismo panel o por tecnología; suciedad
    vertical solo con inclinación ≥ 75°; sin transparencia) y luego
    `produccion.simular_produccion_anual` (SDM) con esa POA óptica. Sin SDM
    completo: temperatura lineal con γ y aviso.
  - `cadena_superficies_estado` con memoria por huella; `k_bipv_superficie`
    (Fachada 1,3; Techo 1,0; Pérgola y Marquesina 1,15; o el montaje elegido);
    `tabla_desglose`; `registro_publicacion` y `aviso_cadena_vencida`
    (versión `cadena_perdidas_v1` y huella de parámetros).
  - `cadena_optica_fisico` y `poa_optica_fisico` para el físico.
- `calculos/multi_superficie.e_ac_total_multisup`: acepta un PR por superficie.
- `calculos/transicion_multisuperficie.recalcular_fisica_superficie`: con
  `cadena_optica`, el SDM recibe la POA con IAM + suciedad (`f_optico` en los
  resultados); la POA anual informada sigue siendo la bruta.
- `calculos/adaptador_multisuperficie`: `k_bipv` según el montaje de la
  superficie y `cadena_optica` en cada unidad física.
- `pages/9_🗺️_Vista_3D.py`: campo «🌡️ Montaje térmico»; resumen POA con
  columna PR y tabla «De dónde sale el PR»; publicación simplificada, bypass y
  físico con la cadena y su registro; producción mensual y vista del mes con el
  PR de cada superficie; aviso de energía de la versión anterior.
- `pages/7_💰_Financiero.py`, `11_🔋_Baterias_y_Balance.py`,
  `12_🌿_Impacto_CO2.py`: aviso si la energía se publicó con el 0,78 o con
  parámetros que cambiaron.

## Archivos modificados

- `bipv_python/calculos/cadena_perdidas_multisup.py`
- `bipv_python/calculos/multi_superficie.py`
- `bipv_python/calculos/transicion_multisuperficie.py`
- `bipv_python/calculos/adaptador_multisuperficie.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/pages/7_💰_Financiero.py`
- `bipv_python/pages/11_🔋_Baterias_y_Balance.py`
- `bipv_python/pages/12_🌿_Impacto_CO2.py`
- `bipv_python/tests/test_cadena_perdidas_multisup.py`
- `bipv_python/tests/test_asistente_retrieval.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/mapa-dependencias.md`
