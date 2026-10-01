# Validación — Reporte PDF de producción completo para el cliente

**Estado:** validación

## Checklist de validación del módulo

- [x] 8 pruebas en `tests/test_reporte_produccion_completo.py`: funciones
  del módulo con los datos de Urabá (sistema eléctrico 308 módulos, 221,76
  kWp, 2 × Growatt, 200 kW, 6 + 5, DC/AC 1,11, recorte; pérdidas de ① a ⑤;
  bifacial 39,8 %, 2,63 m, 5 %, 10 %; granja completa) y la página real del
  reporte (AppTest: genera el HTML con las secciones nuevas y sin nombrar el
  software de referencia).
- [x] Con las páginas anteriores fallan la prueba del reporte y la de
  Producción; con el cambio pasan.
- [x] Guardia de física: sin cambios en fórmulas del SDM.
- [x] Suite completa de `bipv_python`: 2283 pruebas pasan.

## Resultado

Criterios 1 a 7 cumplidos. En espera de la revisión del PR.
