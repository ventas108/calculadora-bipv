# Validación — Resumen coherente de Financiero

**Estado:** validación

## Checklist de validación del módulo

- [x] `tests/test_lectura_resumen_financiero.py`: 5 pruebas, rojas en `main`
  (no existían las funciones) y verdes con el cambio; caso cliente 6,854 M COP
  (antes 6,886 M).
- [x] Humo con AppTest de la página: «Ahorro estimado» = «Ahorro energía año 1»
  (15,71 M en el caso de prueba); rótulos «P90 (−9.5%)» en tabla y métricas;
  etiquetas de payback a alturas 0,98 / 0,90 / 0,82.
- [x] Prueba de recuperación del Asistente.
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 4 cumplidos. En espera de la revisión del PR.
