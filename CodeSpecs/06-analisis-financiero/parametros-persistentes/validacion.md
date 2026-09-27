# Validación — Parámetros de Financiero persistentes

**Estado:** validación

## Checklist de validación del módulo

- [x] Reproducción del error con AppTest: 800 → otra página → 1.200.
- [x] `tests/test_campos_persistentes_financiero.py`: 5 pruebas (cambio de
  página, carga de proyecto y edición posterior, rango, página, guardado). La
  de la página falla en `main` y pasa con el cambio.
- [x] Humo con AppTest de la página: valores por defecto iguales a antes;
  excedentes 800 y WACC 12 % quedan en los datos; una sesión nueva solo con
  esos datos los muestra y calcula sin errores.
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 4 cumplidos. En espera de la revisión del PR.
