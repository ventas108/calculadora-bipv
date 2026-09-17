# Tasks: CodeSpec de Mismatch y Pérdidas de Sombreado

## Revisión del contrato

- [x] Identificar parser CSV y rechazo de FS climático/combinado.
- [x] Identificar alineación mensual/exacta y agregación ponderada.
- [x] Identificar simulación SDM de bypass y condición `Isc_sombreado < Imp_claro`.
- [x] Identificar combinación horizonte + FS 3D por máximo.
- [x] Identificar cascada visual y separación de pérdidas eléctricas downstream.
- [x] Identificar consumidores: Producción, Financiero, Reporte, Escenarios y Vista 3D.

## Validación

- [ ] Ejecutar suite focal completa de Mismatch/Sombreado.
- [ ] Verificar que `FS_geometrico` sea la única capa usada por bypass en todos los caminos.
- [ ] Verificar que el modo mensual y exacto produzcan cobertura y trazabilidad correctas.
- [ ] Verificar que los pesos por módulos/área/potencia coincidan con el contrato seleccionado.
- [x] Verificar coherencia térmica del motor y escenarios entre POA sin térmico, NOCT y `k_BIPV` mediante `test_mismatch_bypass_termico.py` (regresión aprobada el 2026-09-17).
- [x] Cubrir la selección de POA en Página 5 y bloquear el fallback a `poa_efectiva_df` cuando falta `poa_sin_termico_df`.
- [x] Bloquear el mismo fallback térmico al entrar directamente a Producción.
- [x] Invalidar Producción, bypass, Financiero, CO₂ y persistencia en disco al recalcular Motor Óptico.
- [x] Verificar que Producción no duplique la corrección térmica del Motor Óptico.
- [ ] Verificar que Producción/Financiero no dupliquen otras pérdidas de la cascada visual.

## Implementación posterior

- [x] Corregir la incoherencia térmica reproducida en el camino normal: Página 5 selecciona POA sin térmico y bypass/escenarios Fase 4 propagan `k_BIPV` (commit `95388cd4`).
- [x] Añadir invalidación del bypass y resultados downstream cuando cambia la POA del Motor Óptico (commit `f7402f70`; desplegado en `main` como `e6b76069b`).
- [ ] Añadir registro reproducible del CSV, modo, agregación, fachada, strings y panel usados.
- [ ] Cambiar `status` a `validated` solo con evidencia fresca.

## Evidencia térmica validada (2026-09-17)

- [x] `tests/test_seleccion_poa_bypass_pagina5.py`: 42 aprobadas.
- [x] `tests/test_mismatch_bypass_termico.py`: 5 aprobadas.
- [x] `tests/test_ejecutor_escenarios.py`: 14 aprobadas; 1 advertencia preexistente.
- [x] Suite focal SDM/métricas/horizonte: 46 aprobadas.
- [x] Suite de invalidación y consumidores: 42 aprobadas.
- [x] Pruebas de Producción y Motor Óptico: 10 aprobadas.
- [x] Scripts de fuente térmica única, invalidación y persistencia: aprobados.
- [x] Despliegue verificado: PM2 `online` y `/_stcore/health` respondió `ok`.