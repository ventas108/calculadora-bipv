# Spec — Proveedor de sombra opcional `pybdshadow` (cubiertas horizontales)

**Estado:** propuesta — NO aprobada. Borrador generado por una verificación técnica
(`references/informe-verificacion-pybdshadow-p-shade.md`, 2026-09-21) que NO modificó código
productivo. Pendiente de decisión del Director.

## Problema a resolver

El motor de sombra propio (`calculos/sombras_3d.py`) exige una malla 3D exportada de SketchUp
(`cargar_malla`). Cuando un proyecto no tiene esa malla — por ejemplo, un techo horizontal en
zona urbana densa donde solo existe información catastral/OSM de altura de edificios vecinos —
hoy no hay ninguna alternativa: el usuario debe modelar en SketchUp o quedarse sin sombra
horaria real, y el proyecto queda bloqueado por la regla existente de "sin defaults silenciosos
`p_shade=0`" (`CodeSpecs/05-perdidas-y-temperatura/transicion-multisuperficie/diseno.md`).

Se evaluó si la librería externa `pybdshadow` (BSD-3-Clause,
https://github.com/ni1o1/pybdshadow) podría cubrir ese hueco. La verificación técnica
(`references/informe-verificacion-pybdshadow-p-shade.md`) concluyó:

- Su motor geométrico (`bdshadow_sunlight`) es correcto para **planos horizontales** (validado
  contra ray-casting propio, error ≤0.008 en los casos de aceptación ejecutados).
- Es **estructuralmente incapaz** de representar superficies inclinadas o verticales — no tiene
  parámetro de tilt/azimuth en su API pública; forzar su uso en esos casos produce errores de
  hasta 51 puntos porcentuales frente al ray-casting real.
- No calcula nada eléctrico — sigue siendo obligatorio pasar por `mismatch_bypass.simular_bypass_horario`
  para cualquier `p_shade` que produzca, igual que con el motor propio.
- Tiene riesgos concretos de adopción: incompatible con Python 3.14 tal como se distribuye
  (dependencia obligatoria de `keplergl`, que falla al compilar), mantenimiento estancado desde
  enero de 2024, y una función declarada en su API pública (`cal_sunshine_facade`) que no existe.

## Alcance de esta Spec (si se aprueba)

Únicamente: un proveedor de sombra **opcional, secundario, nunca por defecto**, limitado a
superficies BIPV horizontales (`tipo="Techo"`, `tilt_deg≈0`) de proyectos multi-superficie, para
el caso en que no exista malla 3D propia y sí exista información catastral de altura de
edificios vecinos. No sustituye `sombras_3d.py`, no toca fachadas/cubiertas inclinadas, no
cambia el contrato `p_shade`/`FS_geometrico` vigente.

## Fuera de alcance (explícito)

- Cualquier superficie con `tilt_deg` distinto de horizontal.
- Reemplazo del motor `sombras_3d.py` o de `mismatch_bypass.py`.
- Cambios al contrato `docs/contratos/shading-engine-contract.v1.json`.
- Convertir `pybdshadow` en dependencia obligatoria del proyecto (`requirements.txt` base).
- Resolver el bloqueo de `transicion-multisuperficie` (punto 4 de su `diseno.md`: sombra por
  superficie con múltiples puntos de análisis) — ese bloqueo es sobre fachadas/inclinadas,
  terreno donde `pybdshadow` no aplica; sigue dependiendo de ampliar `sombras_3d.py`.
