# Implementación — Unifilar y RETIE coherentes con Motor Óptico, Mismatch y Vista 3D

**Estado:** validación

## Cambios realizados

- `calculos/corriente_bifacial.py` (nuevo): `BNPI_TRASERA_W_M2`,
  `factor_isc_bifacial`, `phi_proyecto`, `phi_superficie`,
  `panel_para_corriente`, `texto_origen`.
- `calculos/diseno_electrico_multisup.py`: `validar_diseno_electrico(...,
  bifacial=None)` usa el panel con Isc BNPI para la corriente del grupo
  (`isc_total`, caja combinadora, límite de corriente del string); grupos
  con `factor_bifacial` y `origen_bifacial`; aviso «lado seguro» si la
  bifacialidad sale de la ficha; `_bifacial_estado` y
  `diagnostico_electrico_estado` con la configuración de la sesión.
- `calculos/topologia_electrica.py`: grupos con `isc_stc_A` en BNPI,
  `isc_frontal_A`, `factor_bifacial` y `cruce_texto`; superficies con
  `modulos_fisicos`.
- `calculos/diagrama_unifilar.py`: `calcular_perdida_ohmica(...,
  factor_bifacial=1.0)` (corriente DC de diseño y ampacidad); rótulo
  «↔ cruza: …» en las ramas.
- `calculos/ficha_validacion_retie.py`: `construir_config_retie(...,
  factor_bifacial=1.0)`; `calcular_retie` con `isc_bnpi_a` e Isc de diseño en
  BNPI; fusible gPV de las cajas con «Isc BNPI (bifacial)»; superficies con
  módulos físicos; línea «Isc diseño … (Isc BNPI …)» en la ficha.
- `utils/sistema_electrico_ui.py`: tabla del sistema con «Isc diseño módulo»
  y «Cruza a otra superficie».
- Páginas: 20 (factor BNPI, % de cableado real en multi-superficie), 21
  (factor BNPI con su explicación), 5 (aviso de cableado del Unifilar) y 9
  (diagnóstico con la configuración bifacial).
- Manual del Asistente, sección 88; contrato de Energía multi-superficie y
  registro de decisiones.

## Archivos modificados

- `bipv_python/calculos/corriente_bifacial.py`
- `bipv_python/calculos/diseno_electrico_multisup.py`
- `bipv_python/calculos/topologia_electrica.py`
- `bipv_python/calculos/diagrama_unifilar.py`
- `bipv_python/calculos/ficha_validacion_retie.py`
- `bipv_python/utils/sistema_electrico_ui.py`
- `bipv_python/pages/20_⚡_Diagrama_Unifilar.py`
- `bipv_python/pages/21_📋_Ficha_Validacion_RETIE.py`
- `bipv_python/pages/5_🔀_Mismatch.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_unifilar_retie_bifacial_cruce.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
