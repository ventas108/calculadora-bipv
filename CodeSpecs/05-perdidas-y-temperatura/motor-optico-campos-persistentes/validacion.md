# Validación — Motor Óptico: los campos no vuelven a su mínimo al cambiar de página

**Estado:** validación

## Checklist de validación del módulo

- [x] 6 pruebas en `tests/test_motor_optico_campos_persistentes.py` con la
  página real (AppTest; el cambio de página se simula abriendo la página de
  nuevo solo con los datos, sin las claves de los widgets). Con la página
  anterior fallan las 5 de comportamiento y la guarda (NOCT y γ vuelven a 35
  y −0,70); con el cambio pasan.
- [x] Pruebas de la Spec `05/motor-optico-ficha-termica` siguen verdes (aviso
  y botón «Usar los de la ficha»).
- [x] Guardia de física: sin cambios en fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2269 pruebas pasan.

## Resultado

Criterios 1 a 6 cumplidos. En espera de la revisión del PR.
