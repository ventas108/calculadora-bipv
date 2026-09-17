# Tasks: CodeSpec del Módulo Producción

## Revisión del contrato

- [x] Identificar página, motores y modelos térmicos/eléctricos propietarios.
- [x] Identificar entradas desde Recurso Solar, Dimensionamiento, Motor Óptico y Mismatch.
- [x] Identificar consumidores: Financiero, Balance, Reporte, CO₂ y Asistente.
- [x] Identificar persistencia e invalidación asociadas.
- [ ] Inventariar todas las claves publicadas y su fuente física.

## Reproducción prioritaria

- [ ] Probar que cambiar panel, inversor, módulos, eficiencia o modo IV invalida `res_produccion` antes de republicarlo.
- [ ] Probar que Motor Óptico + Mismatch no aplica soiling dos veces.
- [ ] Probar que bypass se rechaza si panel, strings, módulos o POA no coinciden con la corrida vigente.
- [ ] Probar que recalcular bypass con pérdida cero elimina cualquier energía bypass anterior.
- [ ] Probar que la persistencia rechaza resultados de otra configuración en las mismas coordenadas.

## Fase 1: criterios ejecutables

- [ ] Given una corrida vigente, when cambia panel/inversor/módulos/eficiencia/modo IV, then `produccion_ok` queda falso antes de leer `res_produccion`.
- [ ] Given Motor Óptico con soiling, when Producción usa Mismatch, then la entrada eléctrica contiene un solo factor de soiling.
- [ ] Given bypass de otra configuración, when Producción intenta consumirlo, then se invalida sin modificar la energía base.
- [ ] Given bypass positivo seguido de bypass cero, when Producción actualiza el resultado, then no sobrevive la energía corregida anterior.
- [ ] Given persistencia de una firma A, when la configuración activa tiene firma B, then no se restaura ningún agregado.
- [ ] Given los mismos datos canónicos, when la firma se calcula en procesos distintos, then produce el mismo digest.
- [ ] Given un cambio en cada campo o serie firmada, when se recalcula la firma, then el digest cambia.
- [ ] Given `NaN`, infinito, índice ambiguo o persistencia legacy sin firma, when se valida, then se rechaza sin restaurar resultados.

## Coherencia del resultado oficial

- [ ] Verificar igualdad anual, mensual y horaria para el resultado base.
- [ ] Verificar el mismo contrato cuando bypass es oficial.
- [ ] Verificar o reclasificar multi-superficie como estimación preliminar si no reproduce el motor horario.
- [ ] Verificar que Balance y Reporte no mezclen anual corregido con mensual base.
- [ ] Verificar que toda invalidación de Producción caduque Balance y demás consumidores derivados.

## Física y trazabilidad

- [ ] Confirmar el método efectivo por tecnología: JRC/Huld, SDM PVsyst, Motor IV o lineal.
- [ ] Verificar alineación por índice de la corrección espectral, no solo por longitud.
- [ ] Verificar cierre del diagrama de pérdidas contra `E_ac_anual_kWh`.
- [ ] Documentar incertidumbre cuando Motor Óptico no se ha ejecutado.

## Implementación

- [ ] Aplicar primero el cambio mínimo de vigencia, doble soiling y bypass respaldado por pruebas rojas.
- [ ] Actualizar `mismatch-sombreado-codespec` con `factor_mismatch_sin_soiling` y `bypass_run_signature_v1` sin cambiar sus claves históricas.
- [ ] Mantener las API públicas y consumidores actuales durante la primera fase.
- [ ] Registrar evidencia fresca de cada suite ejecutada.
- [ ] Cambiar `status` a `validated` solo cuando se cierre el contrato oficial completo.