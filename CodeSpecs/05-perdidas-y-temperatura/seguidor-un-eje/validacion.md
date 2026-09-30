# Validación — 🌾 Granja FV, fase 4: seguidor de un eje con backtracking frente a la estructura fija

**Estado:** validación

## Checklist de validación del módulo

- [x] 17 pruebas nuevas en `tests/test_granja_seguidor.py`: en `main` el
  archivo no se puede cargar (no existe `calculos.seguidor`); con el motor y
  sin el manual falla 1; con el cambio completo pasan.
- [x] Contra pvlib: fracción sombreada igual a `shaded_fraction1d` (±1e-6)
  en 6 posiciones del sol; con backtracking siempre 0.
- [x] Prueba con la página real (AppTest, Apartadó, JAM66D46-720/LB del
  catálogo, TMY sintético de cielo claro sin red):
  - Estructura fija 2,420 kWh/m²; seguidor con backtracking 3,017 kWh/m²
    (+24,7 %); sin backtracking 2,930 kWh/m² (+21,1 %), sombra eléctrica
    2,7 %.
  - Seguidor de 2,38 m, separación 6,81 m, 2 bloques, borde bajo 0,97 m.
  - Estimación: 340.381 kWh/año fija → ≈ 424.346 kWh/año con seguidor.
  - Ángulo máximo 75°: el resultado viejo se oculta; eje 1,2 m y 75°: aviso
    🟠 del borde a 0,05 m del suelo.
- [x] Guardia de física: sin cambios en fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2238 pruebas pasan.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR.
