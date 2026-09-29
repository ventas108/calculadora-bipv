# Validación — «Calidad del módulo» y «Mismatch» por separado

**Estado:** validación

## Checklist de validación del módulo

- [x] 16 pruebas nuevas en `tests/test_calidad_y_mismatch.py`: en `main` el
  archivo no se puede cargar (no existe `pct_perdida_modulos`); con el
  cambio pasan.
- [x] Prueba de referencia en `tests/test_consistencia_sdm_entre_modulos.py`:
  los dos motores quitan 0.97 × 0.979 de la energía DC con calidad 3.00 % y
  mismatch 2.10 % (caso Apartadó).
- [x] Pruebas existentes de pérdidas, Loss Diagram, pérdida óhmica, vigencia
  y cadena multi-superficie: 136 pasan sin cambios.
- [x] Prueba de humo de 🔀 Mismatch (AppTest): cinco controles; calidad 3.0 y
  mismatch 2.1 quedan guardados en la sesión.
- [x] Compilación con `-W error::SyntaxWarning`.
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR.
