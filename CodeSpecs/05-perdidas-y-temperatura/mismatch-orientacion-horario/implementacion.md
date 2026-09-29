# Implementación — Mismatch por orientación hora a hora

**Estado:** validación

## Cambios realizados

- `calculos/mismatch.py`:
  - `perdida_string_bypass(poas, fracciones)`: potencia ideal y del string,
    hora a hora, con diodos de bypass.
  - `firma_orientacion(configuraciones, tmy, albedo, bifacial)`.
  - `calcular_mismatch_orientacion(..., albedo=0.20, bifacial=None)`: POA de
    cada orientación con el albedo y el panel bifacial; `factor_horario`,
    `factor_mismatch_pct` ponderado por energía,
    `factor_mismatch_pct_anual_aprox` (cálculo anterior, referencia),
    `modelo` y `firma`.
  - `publicar_cascada_mismatch`: con resultado horario el escalar no lleva la
    orientación y marca `mismatch_or_horario`.
  - `factores_mismatch_produccion`: multiplica el factor horario por el de la
    orientación (si las horas no coinciden, no lo aplica y avisa).
- `pages/5_🔀_Mismatch.py`: albedo y bifacial del proyecto, vigencia por firma,
  tarjeta «Factor mismatch (hora a hora)» y nota con el cálculo anterior.
- `pages/6_📊_Produccion.py`: la nota «🔀 Aplicado hora a hora» dice qué entra
  (horizonte, orientación, suciedad frontal).
- `tests/test_mismatch_horizonte_coherente.py`: la vigencia de orientaciones
  ahora se busca por la firma completa.
- Manual del Asistente, sección 86; contrato de 05 y registro de decisiones.

## Archivos modificados

- `bipv_python/calculos/mismatch.py`
- `bipv_python/pages/5_🔀_Mismatch.py`
- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/tests/test_mismatch_orientacion_horario.py`
- `bipv_python/tests/test_mismatch_horizonte_coherente.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
