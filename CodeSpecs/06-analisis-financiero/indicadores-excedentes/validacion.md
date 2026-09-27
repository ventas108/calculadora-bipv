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
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 4 cumplidos. En espera de la revisión del PR.
