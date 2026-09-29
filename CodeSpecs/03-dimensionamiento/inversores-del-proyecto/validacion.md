# Validación — Cantidad de inversores del proyecto elegida por el diseñador

**Estado:** validación

## Checklist de validación del módulo

- [x] 20 pruebas nuevas en `tests/test_inversores_del_proyecto.py`: en
  `main` el archivo no se puede cargar (no existen `resolver_inversores`,
  `inversores_para_dcac`, `inversores_fijados_vigentes`); con el cambio
  pasan. Cubren el mínimo, la cantidad fijada, el ajuste, la sugerencia por
  DC/AC, Apartadó (2 inversores, 6 + 5, DC/AC 1,11), el redondeo hacia
  arriba en Producción, el modelo distinto y las páginas 4, 6 y 8.
- [x] Prueba de referencia en `test_consistencia_sdm_entre_modulos.py`:
  Dimensionamiento y Producción dan la misma cantidad en 4 casos de Apartadó.
- [x] Pruebas existentes de `proyecto_completo` y de
  `escalar_p_ac_nom_por_inversores` (840 ÷ 280 = 3; 280 → 1) siguen verdes.
- [x] Prueba con las páginas reales (AppTest, Apartadó, Growatt MAX
  100KTL3 LV con 100 kW AC):
  - 📐 Dimensionamiento con 1 string por MPPT: 0 → «mínimo 2 inversor(es)»,
    6 + 5, DC/AC 1,11 🟢; 3 → «3 fijados por ti», 4 + 4 + 3, DC/AC 0,74 🔴;
    1 → 🟠 «no es posible … se usa 2». `N_inv_total` publica la cantidad
    efectiva.
  - 📊 Producción (TMY sintético, bifacial): antes 1 inversor, recorte
    191.980 kWh (35,7 %); ahora 2 inversores, DC/AC 1,11 🟢, recorte
    3.337 kWh; con 2 fijados, «DC/AC y recorte con 2 inversores fijados».
- [x] Manual del Asistente, sección 90: guía rápida de alarmas (colores de la
  relación DC/AC con sus límites 0,75 / 1,00 / 1,35 / 1,60, 💡, 🟠 de ajuste,
  texto de Producción y campo que vuelve a 0), con qué hacer en cada caso;
  prueba `test_manual_del_asistente_explica_las_alarmas`.
- [x] Suite completa de `bipv_python`: 2133 pruebas pasan.

## Resultado

Criterios 1 a 9 cumplidos. En espera de la revisión del PR.
