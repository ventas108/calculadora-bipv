# Validación — Curva de baja irradiancia de la ficha

**Estado:** validación

## Checklist de validación del módulo

- [x] `tests/test_curva_baja_irradiancia.py`: rojas con el código anterior
  (`parsear_curva_baja_irradiancia` no existía).
- [x] Teja de 32 W con su curva:
  - 500 a 900 W/m² dentro de ±1,5 puntos;
  - a 300 W/m² el modelo da ~90 % frente al 80 % de la ficha, con aviso;
  - STC reproducido.
- [x] Curva fabricada con el modelo: recuperada (≤ 0,3 puntos, 92 % a 200 W/m²).
- [x] Prioridad curva > 200 W/m² > 97 %; sin curva, sin cambios.
- [x] Guardia de física: los 5 motores dan lo mismo con la teja calibrada.
- [x] AppTest de Motor IV (selector + «Generar comparación FF vs G») sin errores.
- [x] Suite completa de `bipv_python`: 2411 pruebas pasan.

## Resultado

Criterios 1 a 6 cumplidos. En espera de la revisión del PR.
