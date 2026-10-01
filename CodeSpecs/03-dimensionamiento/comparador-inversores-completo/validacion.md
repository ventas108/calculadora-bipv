# Validación — Comparador de Inversores completo

**Estado:** validación

## Checklist de validación del módulo

- [x] 9 pruebas en `tests/test_comparador_inversores_completo.py` con el panel
  JAM66D46-720/LB y el Growatt MAX 100KTL3 LV de la ficha oficial:
  - Vmp a la temperatura extrema (descarta un MPPT mínimo de 830 V);
  - ficha 🔴 descarta, ficha 🟠 se muestra, margen de Voc 1,0 %;
  - mejor N: Growatt → 22, 14 strings, 7 + 7, 1 string por MPPT, 🟠;
    1.500 V → 28, 11 strings, 2 unidades por DC/AC; sin N compatible, motivo;
  - sin precio no hay TIR ni LCOE; con 310 módulos gana 21 en serie (294
    módulos) y la energía se escala por los módulos usados;
  - adoptar: Dimensionamiento resuelve 1 string por MPPT con 14 cadenas;
  - página real (sección nueva y T. extrema) y manual.
- [x] Con el código anterior no carga el archivo de pruebas; con la página
  anterior fallan 3 (adopción, página y manual).
- [x] Pruebas existentes del comparador siguen verdes.
- [x] Guardia de física: sin cambios en fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2313 pruebas pasan.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR.
