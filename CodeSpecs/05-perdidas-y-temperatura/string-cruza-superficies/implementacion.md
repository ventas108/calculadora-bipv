# Implementación — Vista 3D: string que cruza dos superficies

**Estado:** validación

## Cambios realizados

- `calculos/cruce_superficies.py` (nuevo): `tiene_cruce`,
  `cruces_del_proyecto`, `validar_cruces`, `modulos_fisicos_por_superficie`,
  `perdida_cruce` (con `calculos.mismatch.perdida_string_bypass`) y
  `factores_cruce`.
- `calculos/diseno_electrico_multisup.py`:
  - `area_energia_superficie(..., modulos=None)` y `superficies_para_energia`
    con los módulos físicos de cada superficie.
  - `validar_diseno_electrico`: 🔴/🟡 de los cruces en el check del grupo y en
    la lista (misma etiqueta «Superficie · G»).
- `calculos/cadena_perdidas_multisup.py`: `cadena_superficies_estado` aplica
  `f_cruce` al PR (y reporta la falta de POA de la otra superficie como
  error); `tabla_desglose` con la columna «String que cruza»; `firma_cadena`
  con los cruces solo si existen.
- `calculos/adaptador_multisuperficie.py`: el modo físico no se prepara con
  cruces (error explicado).
- `pages/9_🗺️_Vista_3D.py`: casilla «🔀 Este string cruza a otra superficie»,
  destino y módulos por string en el editor de grupos; la sección «🔀 6»
  deja fuera las superficies con cruces, con aviso.
- Manual del Asistente, sección 87; contrato de Energía multi-superficie y
  registro de decisiones.

## Archivos modificados

- `bipv_python/calculos/cruce_superficies.py`
- `bipv_python/calculos/diseno_electrico_multisup.py`
- `bipv_python/calculos/cadena_perdidas_multisup.py`
- `bipv_python/calculos/adaptador_multisuperficie.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_string_cruza_superficies.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
