# Validación — Reporte PDF de proyectos multi-superficie (🗺️ Vista 3D)

**Estado:** validación

## Checklist de validación del módulo

- [x] 9 pruebas en `tests/test_reporte_multisuperficie.py` con fachadas Este
  y Oeste y un string que cruza: publicación de la tabla de pérdidas,
  resumen (14.920 kWh, 13,08 kWp, 1.141 kWh/kWp, método, 🟢), tabla por
  superficie (módulos físicos 10 y 30, kWp, PR, kWh/kWp), inversores (INV-1,
  15 kW, 4 strings, 40 módulos, DC/AC 0,87), cadena, cruces y mensual; la
  página real genera el reporte con una sola energía y todas las tablas; sin
  multi-superficie el reporte no cambia.
- [x] Con el código anterior fallan 3 (publicación, cadena y doble energía);
  con el cambio pasan.
- [x] Pruebas de la cadena de pérdidas multi-superficie y del reporte de
  producción siguen verdes.
- [x] Guardia de física: sin cambios en fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2292 pruebas pasan.

## Resultado

Criterios 1 a 6 cumplidos. En espera de la revisión del PR.
