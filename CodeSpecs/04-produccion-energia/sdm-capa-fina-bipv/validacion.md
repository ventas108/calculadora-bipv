# Validación — Modelo IV de paneles BIPV de capa fina (CIGS) sin parámetros de laboratorio

**Estado:** validación

## Checklist de validación del módulo

- [x] Pruebas en `tests/test_sdm_capa_fina_bipv.py` con la ficha real del
  MiaSolé FLEX-03 90N (rojas con el código anterior: `normalizar_tecnologia`
  no existía).
- [x] MiaSolé: CIGS, N_s estimado 40 y ficha reproducida en STC.
  - Sin el dato de baja luz: 97,0 % a 200 W/m² (antes, tratado como
    silicio, 95,85 %; con CIGS sin ajuste, 91,6 %).
  - Con el dato de la ficha (94, 97 y 99 %): reproducido ± 0,3 puntos.
- [x] Silicio sin cambios (mismo factor de idealidad, sin ajuste).
- [x] Guardia de física.
- [x] Suite completa de `bipv_python`: 2380 pruebas pasan.

## Resultado

Criterios 1 a 6 cumplidos. En espera de la revisión del PR.
