# Implementación — Baja luz de CIGS con factor de forma bajo

**Estado:** validación

## Cambios realizados

- Búsqueda del factor de idealidad hasta 2,2, con 49 puntos.
- Avisos numéricos silenciados en `_rel_seguro`.
- `_error_ajuste_200` cuando el objetivo no se alcanza.
- `_mostrar_origen_modelo` en 🔬 Motor IV, llamada desde Dimensionamiento y
  desde el selector.
- Panel del selector guardado en la sesión (`motor_iv_panel_usado`).
- El SDM estimado trae el NOCT de la ficha (solo si existe) y el control NOCT de
  Motor IV usa una clave por panel.
- Ficha real del MiaSolé FLEX-03N 1,7 m (la envió el usuario): 70N con Voc
  23,2 V, Isc 4,67 A, Vmp 18,1 V, Imp 3,88 A, NOCT 48 °C y N_s 40 del catálogo.
  Con el código anterior y el Voc del catálogo del servidor (23,3 V), el modelo
  da R_s 0,930 Ω y R_sh 114,56 Ω, igual que la pantalla del usuario.

## Archivos modificados

- `bipv_python/calculos/modelo_iv.py`
- `bipv_python/pages/3_🔬_Motor_IV.py`
- `bipv_python/tests/test_sdm_capa_fina_bipv.py`
- `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`
- `bipv_python/datos/base_conocimiento_asistente.md` (sección 113)
- `CodeSpecs/00-director/registro-de-decisiones.md`
