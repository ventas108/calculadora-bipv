# Validación — Coeficiente de temperatura de Isc (α) en el catálogo de paneles

**Estado:** validación

## Checklist de validación del módulo

- [x] 4 pruebas en `tests/test_coef_isc_catalogo.py` (rojas con el código
  anterior: la función no existía).
- [x] Motor IV sigue usando el SDM estimado para paneles del Excel: α no
  completa por sí solo los parámetros calibrados.
- [x] Suite completa de `bipv_python`: 2360 pruebas pasan.

## Resultado

Criterios 1 a 4 cumplidos. En espera de la revisión del PR.
