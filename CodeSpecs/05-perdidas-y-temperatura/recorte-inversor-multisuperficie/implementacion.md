# Implementación — Vista 3D: recorte de cada inversor en los modos simplificado y bypass

**Estado:** validación

## Cambios realizados

- `calculos/recorte_inversores_multisup.py` (nuevo): `potencia_ac_inversor`,
  `factores_recorte`, `tabla_recorte`.
- `calculos/cadena_perdidas_multisup.py`: `perfil_ac` en `cadena_superficie`;
  recorte en `cadena_superficies_estado` después del cruce;
  `recorte_por_inversor`; columna «Recorte inversor» en `tabla_desglose`;
  `firma_cadena(..., inversores)` y sus dos usos con `multisup_inversores`;
  aviso de cadena vencida menciona la potencia AC.
- `calculos/diseno_electrico_multisup.py`: el aviso DC/AC dice que Vista 3D
  resta el recorte hora a hora.
- `calculos/dimensionamiento.py`: el mensaje de `evaluar_relacion_dc_ac` dice
  «1.00–1.35» (antes 0.95–1.35); límites sin cambio.
- `pages/9_🗺️_Vista_3D.py`: tabla «✂️ Recorte por inversor (hora a hora)».
- Manual del Asistente, sección 91; contratos y registro de decisiones.

## Archivos modificados

- `bipv_python/calculos/recorte_inversores_multisup.py`
- `bipv_python/calculos/cadena_perdidas_multisup.py`
- `bipv_python/calculos/diseno_electrico_multisup.py`
- `bipv_python/calculos/dimensionamiento.py`
- `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`
- `bipv_python/tests/test_compatibilidad_string.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_recorte_inversor_multisup.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
