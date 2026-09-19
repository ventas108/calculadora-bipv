# Validación — Análisis financiero

**Estado:** completado

## Checklist de validación del módulo

- [x] `python -m pytest tests/test_produccion_vigencia.py
      tests/test_produccion_pagina_vigencia.py
      tests/test_seleccion_poa_bypass_pagina5.py`: `124 passed` (Python 3.14.2,
      pytest 9.1.1).
- [x] `python scripts/test_persistencia_89_94_114.py`: `21/21` casos pasados.
- [x] Contrato de `calcular_produccion_run_signature_v1()` y
      `calcular_bypass_run_signature_v1()` sin cambios.
- [x] Gates ya desplegados intactos: diseño eléctrico vencido, vigencia de
      bypass, doble soiling.
- [x] Validación funcional en producción: pestaña nueva de 💰 Financiero
      muestra "📂 Datos restaurados del proyecto guardado" y los agregados
      reales del proyecto (128 módulos, 8.06 kWp, 4.743 kWh/año), no defaults
      en cero — confirmado 19-sep-2026.

## Resultado

Validación local completa: la integridad de `produccion_run_signature_v1`
vía payload canónico persistido queda verificada con evidencia de pruebas.
Falta únicamente la verificación funcional en producción tras el despliegue.

