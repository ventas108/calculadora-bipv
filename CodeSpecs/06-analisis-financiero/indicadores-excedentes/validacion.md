# Validación — Indicadores de Financiero con la tarifa de excedentes

**Estado:** validación

## Checklist de validación del módulo

- [x] `tests/test_indicadores_excedentes.py`: 8 pruebas. La de la página falla
  en `main` y pasa con el cambio; las del módulo no importan en `main`.
- [x] Humo con AppTest de `pages/7_💰_Financiero.py` y tarifa de excedentes
  800 COP/kWh:
  - sin batería: ahorro año 1 = 12.643 × 850 + 826 × 800 = 11,41 M COP y no
    aparece «Impacto de la batería»;
  - con batería (300 kWh descargados): la sección aparece y «Autoconsumo
    extra» = 300 kWh/año.
- [x] Suite completa de `bipv_python`: 1818 pruebas; se actualizó `test_sincronizacion_consumo_y_excedentes.py` (la tarifa de excedentes ahora se pasa a 3 escenarios: P50, P90 y sin batería).

- [x] Complemento: 4 pruebas nuevas (aviso con el caso de 24 kWp, sin aviso
  al 107 %, con balance o sin consumo; tarjetas que suman el total; página).
  Humo con AppTest: consumo 478 kWh/mes sin balance → 2 avisos; 1.200 kWh/mes
  o con balance → ninguno; las 5 tarjetas suman el CAPEX bruto.

## Resultado

Criterios 1 a 6 cumplidos. En espera de la revisión del PR.
