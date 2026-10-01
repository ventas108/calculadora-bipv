# Validación — Tensión máxima de sistema del módulo en el límite del Voc

**Estado:** validación

## Checklist de validación del módulo

- [x] Pruebas en `tests/test_tension_maxima_modulo.py` (rojas con el código
  anterior).
- [x] Teusaquillo: ASP-ST1-T40 + SG8.0RT con 7 en serie × 16 🟢 en Vista 3D;
  8 en serie a 0 °C 🔴 por el módulo.
- [x] Guardia de física: sin cambios en el SDM.
- [x] 11 pruebas que usaban el ASP con 8 en serie a −5 °C (1.017 V): las que
  reproducen el XLSM y la mecánica del optimizador usan el ASP sin el dato;
  las de RETIE, SG5.0RT y comparador de paneles pasan a la regla nueva.
- [x] Suite completa de `bipv_python`: 2351 pruebas pasan.

## Resultado

Criterios 1 a 5 cumplidos. En espera de la revisión del PR.
