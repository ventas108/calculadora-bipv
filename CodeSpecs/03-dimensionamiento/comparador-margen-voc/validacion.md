# Validación — Comparador y Dimensionamiento con el mismo margen de Voc

**Estado:** validación

## Checklist de validación del módulo

- [x] `tests/test_comparador_inversores_completo.py` (13 pruebas):
  - el comparador da para Urabá el mismo N que `optimizar_n_serie` (20);
  - 20 × 15 = 300 módulos, reparto 8 + 7, 🟢, DC/AC 1,08;
  - con 300 módulos gana el reparto exacto; un inversor de 1.500 V sigue en 28;
  - el margen del reporte usa el mismo 7,5 %;
  - el manual lo explica (sección 105).
- [x] Con el criterio anterior fallan 6 de ellas.
- [x] Pruebas del reporte de granja y del comparador anteriores siguen verdes.
- [x] Guardia de física: sin cambios en fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2317 pruebas pasan.

## Resultado

Criterios 1 a 4 cumplidos. En espera de la revisión del PR.
