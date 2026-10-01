# Validación — Reporte PDF de Granja FV completo y ficha del inversor

**Estado:** validación

## Checklist de validación del módulo

- [x] 12 pruebas en `tests/test_reporte_granja_completo.py` con el campo real
  de Urabá (30 × 100 m, 13 filas de 2 × 12, 308 × JAM66D46-720/LB):
  - ficha del inversor (LV con 1.500 V → 🟠, ficha oficial sin alertas, MPPT
    sobre Vdc → 🔴) y margen de Voc (1.386 V 🔴, 1.089 V 🟠, 990 V 🟢);
  - módulos por inversor (154 + 154 con 22 en serie; 168 + 140 con 28);
  - SVG de vista 3D, plano eléctrico, luz en el suelo y mapa mensual;
    maquinaria, coherencia y strings que cruzan filas;
  - textos por tipo, mismatch aplicado, altitud y aviso de suciedad;
  - la página real del reporte de granja (todas las secciones nuevas, sin
    «Factor Mismatch aplicado», «CdTe», «Bogotá» ni textos de fachada) y de
    fachada (conserva sus textos); alerta en Dimensionamiento; manual.
- [x] Con las páginas anteriores fallan 3 (reporte, Dimensionamiento y
  manual); sin los módulos nuevos no carga el archivo de pruebas.
- [x] `test_mismatch_horizonte_coherente::test_reporte_muestra_el_factor_aplicado`
  ahora comprueba el comportamiento: el reporte usa `filas_mismatch`, que lee
  el factor aplicado antes que el de respaldo.
- [x] Revisión visual del reporte generado (capturas en Chromium).
- [x] Guardia de física: sin cambios en fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2304 pruebas pasan.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR.
