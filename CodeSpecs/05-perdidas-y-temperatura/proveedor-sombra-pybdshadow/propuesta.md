# Propuesta — Proveedor de sombra opcional `pybdshadow`

**Estado:** propuesta — NO aprobada.

## Propuesta

1. Definir el contrato `ShadowProvider`/`ShadowResult` (esquema completo en
   `references/informe-verificacion-pybdshadow-p-shade.md`, sección "Contrato universal") como
   una interfaz Python interna, sin publicarla todavía como contrato aprobado del Director.
2. Implementar UN solo proveedor concreto tras ese contrato:
   `calculos/proveedores_sombra/pybdshadow_horizontal.py`, que:
   - Solo acepta superficies con `tilt_deg` dentro de una tolerancia de horizontalidad
     (propuesta: `abs(tilt_deg) <= 5.0`) — cualquier otra superficie se rechaza explícitamente
     con un mensaje, nunca con un resultado silenciosamente incorrecto.
   - Requiere que el llamador aporte los edificios vecinos como `GeoDataFrame` con `height`
     (catastro/OSM) — no genera esa geometría por sí mismo.
   - Llama `pybdshadow.bdshadow_sunlight` una vez por hora con sol (mismo filtro
     `ALTURA_SOLAR_MIN_DEG` que ya usa `sombras_3d.py`), interseca el polígono de sombra con el
     footprint de la superficie, y publica `p_shade` = fracción de área en sombra — mismo
     contrato numérico que `FS_geometrico`.
   - Declara `capacidades_declaradas={"soporta_vertical": False, "soporta_inclinada": False,
     "soporta_parcial_por_modulo": False}` explícitamente en su `ShadowResult`.
3. `pybdshadow` entra como dependencia **opcional** (import perezoso, `try/except ImportError`
   con mensaje explícito si falta) — nunca en `requirements.txt` base de `bipv_python`.
4. La UI (si se implementa) ofrece este proveedor solo cuando el usuario marca una superficie
   como horizontal y no ha cargado malla 3D — nunca como default.

## Alternativas consideradas y descartadas

- **Adaptar `pybdshadow` para superficies inclinadas/verticales mediante una capa de proyección
  propia** (proyectar el volumen de sombra sobre un plano oblicuo): descartada — equivale a
  reimplementar el ray-casting que `sombras_3d.py` ya hace, sin ninguna ventaja sobre usarlo
  directamente; la verificación técnica no encontró una forma de hacerlo con la API pública de
  `pybdshadow` sin llegar a esa reimplementación.
- **Usar `cal_sunshine`/`cal_shadowcoverage` como fuente de `p_shade`**: descartada — son un
  conteo diario de horas de sol/sombra, no una serie horaria por timestamp; no cumplen el
  contrato `p_shade[t]` que exige `transicion_multisuperficie.py`.
- **Declarar `pybdshadow` como dependencia obligatoria del proyecto**: descartada por el riesgo
  de incompatibilidad con Python 3.14 y el mantenimiento estancado documentados en el informe de
  verificación.

## Criterio de éxito propuesto

- El proveedor nuevo produce `p_shade` para una superficie horizontal con error ≤2% frente al
  ray-casting propio (`sombras_3d.py`) en un caso de validación con malla 3D real disponible
  (comparación directa, no solo el prototipo sintético).
- Ninguna superficie no horizontal puede obtener un resultado de este proveedor sin un rechazo
  explícito.
- `bipv_python` sigue instalando y arrancando sin `pybdshadow` presente.
