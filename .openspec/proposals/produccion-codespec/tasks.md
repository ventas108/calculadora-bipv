# Tasks: CodeSpec del Módulo Producción

## Revisión del contrato

- [x] Identificar página, motores y modelos térmicos/eléctricos propietarios.
- [x] Identificar entradas desde Recurso Solar, Dimensionamiento, Motor Óptico y Mismatch.
- [x] Identificar consumidores: Financiero, Balance, Reporte, CO₂ y Asistente.
- [x] Identificar persistencia e invalidación asociadas.
- [ ] Inventariar todas las claves publicadas y su fuente física.

## Reproducción prioritaria

- [x] Probar que cambiar panel, inversor, módulos, eficiencia o modo IV invalida `res_produccion` antes de republicarlo.
- [x] Probar que Motor Óptico + Mismatch no aplica soiling dos veces.
- [x] Probar que bypass se rechaza si panel, strings, módulos o POA no coinciden con la corrida vigente.
- [x] Probar que recalcular bypass con pérdida cero elimina cualquier energía bypass anterior.
- [x] Probar que la persistencia rechaza resultados de otra configuración en las mismas coordenadas.

## Fase 1: criterios ejecutables

- [x] Given una corrida vigente, when cambia panel/inversor/módulos/eficiencia/modo IV, then `produccion_ok` queda falso antes de leer `res_produccion`.
- [x] Given Motor Óptico con soiling, when Producción usa Mismatch, then la entrada eléctrica contiene un solo factor de soiling.
- [x] Given bypass de otra configuración, when Producción intenta consumirlo, then se invalida sin modificar la energía base.
- [x] Given bypass positivo seguido de bypass cero, when Producción actualiza el resultado, then no sobrevive la energía corregida anterior.
- [x] Given persistencia de una firma A, when la configuración activa tiene firma B, then no se restaura ningún agregado.
- [x] Given los mismos datos canónicos, when la firma se calcula en procesos distintos, then produce el mismo digest.
- [x] Given un cambio en cada campo o serie firmada, when se recalcula la firma, then el digest cambia.
- [x] Given `NaN`, infinito, índice ambiguo o persistencia legacy sin firma, when se valida, then se rechaza sin restaurar resultados.

## Coherencia del resultado oficial

- [ ] Verificar igualdad anual, mensual y horaria para el resultado base.
- [ ] Verificar el mismo contrato cuando bypass es oficial.
- [ ] Verificar o reclasificar multi-superficie como estimación preliminar si no reproduce el motor horario.
- [ ] Verificar que Balance y Reporte no mezclen anual corregido con mensual base.
- [ ] Verificar que toda invalidación de Producción caduque Balance y demás consumidores derivados.

## Física y trazabilidad

- [x] Confirmar el método efectivo por tecnología: JRC/Huld, SDM PVsyst, Motor IV o lineal (`calculos.produccion.determinar_source_mode()`, campo `source_mode` de la firma).
- [ ] Verificar alineación por índice de la corrección espectral, no solo por longitud.
- [ ] Verificar cierre del diagrama de pérdidas contra `E_ac_anual_kWh`.
- [ ] Documentar incertidumbre cuando Motor Óptico no se ha ejecutado.

## Implementación

- [x] Aplicar primero el cambio mínimo de vigencia, doble soiling y bypass respaldado por pruebas rojas.
- [x] Actualizar `mismatch-sombreado-codespec` con `factor_mismatch_sin_soiling` y `bypass_run_signature_v1` sin cambiar sus claves históricas.
- [x] Mantener las API públicas y consumidores actuales durante la primera fase.
- [x] Registrar evidencia fresca de cada suite ejecutada (ver "Evidencia Fase 1" abajo).
- [ ] Cambiar `status` a `validated` solo cuando se cierre el contrato oficial completo (Fase 1 cierra vigencia/soiling único/bypass/persistencia; coherencia horaria=mensual=anual, multi-superficie y trazabilidad espectral por índice quedan para fases posteriores).

## Evidencia Fase 1 (2026-09-17, commit base `7cc47b49`)

- [x] `bipv_python/tests/test_produccion_vigencia.py`: 65 aprobadas (normalización canónica, huellas horarias, `produccion_run_signature_v1`, `bypass_run_signature_v1`, `calcular_factor_mismatch_sin_soiling`, `determinar_source_mode`, persistencia con firma).
- [x] `bipv_python/tests/test_produccion_pagina_vigencia.py`: 14 aprobadas (integración estructural en Página 5 y Página 6).
- [x] `bipv_python/tests/test_seleccion_poa_bypass_pagina5.py`: 47 aprobadas.
- [x] `bipv_python/tests/test_mismatch_bypass_termico.py`: 5 aprobadas.
- [x] `bipv_python/tests/test_ejecutor_escenarios.py`: 14 aprobadas.
- [x] `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`, `test_produccion_perdida_ohmica.py`, `test_perdidas_desglosadas_pvsyst.py`, `test_correccion_espectral_cdte.py`, `test_agregador_anual.py`: 77 aprobadas en conjunto.
- [x] `bipv_python/scripts/test_persistencia_89_94_114.py`: aprobado (actualizado para exigir `produccion_run_signature_v1` coincidente al restaurar).
- [x] `bipv_python/scripts/test_invalidacion_cadena.py`: aprobado, sin cambios.
- [x] Red de seguridad adicional (no exigida por el CodeSpec, ejecutada por auditoría): `test_geometria_solar_unificada.py`, `test_optimization_fase4.py`, `test_yr_bruta_real.py`, `test_jrc_huld_primario_cdte.py`, `test_rsh_gating_tecnologia.py`, `scripts/test_kbipv_thermal_single_source.py`, `scripts/test_tau_una_vez.py`: todos aprobados. `scripts/test_produccion_iv.py` mantiene el mismo fallo preexistente (`panel_apto_para_iv()` sin `I_L_ref`) ya presente en el commit base `7cc47b49`, sin relación con este cambio.