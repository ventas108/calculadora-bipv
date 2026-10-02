# Implementación — Baja luz de CIGS con factor de forma bajo

**Estado:** validación

## Cambios realizados

- `calculos/modelo_iv.py`: búsqueda del factor de idealidad hasta 2,2, avisos
  numéricos silenciados en los puntos descartados y `_error_ajuste_200` cuando
  el objetivo no se alcanza.
- `pages/3_🔬_Motor_IV.py`: función `_mostrar_origen_modelo`, llamada también
  desde el selector, con el aviso de ajuste no alcanzado.
- `tests/test_sdm_capa_fina_bipv.py`: 4 pruebas nuevas.
- `tests/test_consistencia_sdm_entre_modulos.py`: caso CIGS de factor de forma
  bajo con N_s del catálogo.
- Manual del Asistente, sección 113; registro.

## Datos de la prueba

Ficha reconstruida a partir de lo que mostró Motor IV: Voc 23,3 V, Isc 4,67 A,
Vmp 18,0 V, Imp 3,9 A y N_s 40. Con ella, el modelo reproduce R_s ≈ 0,93 Ω y
R_sh ≈ 115 Ω, como en la pantalla del usuario.
