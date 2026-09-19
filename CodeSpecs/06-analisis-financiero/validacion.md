# Validación — Análisis financiero

**Estado:** validado

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
- [ ] Validación funcional en producción: simular Producción, abrir
      Finanzas/Presupuesto en pestaña nueva y confirmar restauración; alterar
      el JSON persistido a mano y confirmar el rechazo.

## Resultado

Validación local completa: la integridad de `produccion_run_signature_v1`
vía payload canónico persistido queda verificada con evidencia de pruebas.
Falta únicamente la verificación funcional en producción tras el despliegue.

