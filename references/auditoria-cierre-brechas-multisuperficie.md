# Auditoría: cierre de brechas multi-superficie BIPV

**Fecha:** 2026-09-21. **Copia web:** https://claude.ai/artifact/FovpatwzfPKBbpRcWHEYYY
(documento vivo). Esta es la copia local identificable exigida por el encargo.

## Resumen ejecutivo

La arquitectura multi-superficie tenía mucho más construido de lo que las Specs
documentaban como pendiente — el motor de transición físico
(`transicion_multisuperficie.py`), los dos adaptadores (`adaptador_multisuperficie.py`)
y el toggle opt-in en `pages/9_🗺️_Vista_3D.py` ya existían como cambios sin confirmar
en el repositorio (`git diff`, 152 líneas). Lo que NO existía era la conexión entre
ellos y visibilidad explícita sobre qué significa un `p_shade=0`.

Cerrado en esta ronda, con código y pruebas unitarias:

1. **Gap 1 (sombra por superficie):** `calcular_fs_horario_por_superficie` distingue
   sombra-cero-calculada de cálculo-incompleto y de error-geométrico, y advierte
   resolución espacial insuficiente frente a `N_serie`.
2. **Gap 2 (firma/vigencia):** `firma_sombra` ampliada con tilt/azimuth explícitos,
   transparencia, versión de algoritmo, proveedor, resolución espacial/temporal y zona
   horaria.
3. **Gap 3 (Motor Óptico):** decisión tomada — **opción (a), global** — justificada y
   registrada.
4. **Gap 4 (inversores):** módulo nuevo `calculos/inversores_multisuperficie.py`.
5. **Gap 5 (adaptadores):** auditados (ya correctos); se agregó la pieza faltante
   (`calculos/vinculador_sombra_multisuperficie.py`).

**Sigue abierto, explícitamente:** ninguna superficie real del modo físico puede
todavía tener un resultado, porque `pages/9_🗺️_Vista_3D.py` no tiene widgets para
capturar puntos de análisis/malla por superficie ni para asignar inversor por
superficie (esto último bloqueado por la Spec misma: mockup no aprobado).

## Estado real encontrado al auditar

`tareas.md` de la Spec marcaba como `[x]` varios ítems que en `git status` aparecían
como cambios sin commitear. Contraste:

| Pieza | ¿Existía? |
| --- | --- |
| `transicion_multisuperficie.py` (27 pruebas propias) | Sí, completo |
| `adaptador_multisuperficie.py` | Sí, completo (8 pruebas propias) |
| `sombras_3d.calcular_fs_horario_por_superficie` | Sí, sin commitear (77 líneas) |
| Toggle opt-in + comparación + adopción en Vista_3D.py | Sí, sin commitear (75 líneas) |
| Conexión sombra por superficie ↔ `superficies_bipv` | **No** (cero referencias a `cargar_malla`/`calcular_fs_horario` en Vista_3D.py) |
| `n_serie`/`n_paralelo`/`inversor_id`/`p_shade`/`firma_sombra` en `superficies_bipv` | **No** (el editor reconstruye cada superficie con solo 8 claves) |

Consecuencia verificada: pulsar "🧪 Calcular comparación física" en cualquier proyecto
real fallaría siempre con el error explícito del adaptador — el botón existía pero era
no funcional. El encargo no era diseñar la transacción física (ya existía, ya
validada); era construir la tubería de datos que la alimenta.

## Gap 1 — Sombra real por superficie

`calculos/sombras_3d.py:calcular_fs_horario_por_superficie` extendida (compatible hacia
atrás — `_validar_firma_sombra` exige solo un subconjunto de claves, no igualdad).

| Estado | Cómo se detecta | Dónde aparece |
| --- | --- | --- |
| Sombra cero calculada | Fila real de ray-casting con FS≈0 | `p_shade[t]=0`, sin advertencia |
| Cálculo incompleto | Hay sol pero ninguna fila lo cubre | `cobertura["horas_con_sol_no_calculadas"]>0` + advertencia |
| Horario no calculable | Elevación solar ≤ `ALTURA_SOLAR_MIN_DEG` | `cobertura["horas_sin_sol"]` |
| Error geométrico | `validar_puntos()` detecta punto dentro del obstáculo/pegado | Advertencia `error_geometrico:` + `calidad_confianza="baja"` |

**Regla de área vs. módulos:** documentada y verificada con `n_modulos_serie_por_superficie`
opcional. `p_shade` es un promedio espacial — coincide con "fracción de módulos
sombreados" solo con ≥1 punto por módulo/fila. Con menos puntos, no bloquea (mejor
aproximación disponible) pero marca `calidad_confianza="baja"` y advierte
explícitamente. 6 pruebas en `tests/test_cobertura_sombra_por_superficie.py`.

## Gap 2 — Firma y vigencia de sombras

`firma_sombra` ampliada con `tilt_deg`, `azimuth_deg`, `transparencia`,
`version_algoritmo`, `proveedor`, `resolucion_espacial`, `resolucion_temporal`,
`zona_horaria` — sin romper `_validar_firma_sombra`.

Invalidación downstream verificada: `transicion_cambiar_geometria` sigue haciendo
rollback completo si la firma no coincide con la geometría/TMY nuevos (27 pruebas
previas ya lo cubrían). Esta ronda agregó la capa ANTERIOR:
`vinculador_sombra_multisuperficie.preservar_o_invalidar_campos_fisicos` invalida
`p_shade`/`firma_sombra` en `session_state["superficies_bipv"]` en el momento en que
el usuario cambia tilt/azimuth en el editor, antes de llegar al adaptador.

## Gap 3 — Motor Óptico: decisión tomada

**Decisión: opción (a), Motor Óptico sigue global** (registrada en
`registro-de-decisiones.md` y `diseno.md`, 2026-09-21).

- Por qué NO (b): `calculos/invalidacion.py` ya trata `KEYS_MULTISUP_ESTADO` como un
  ciclo de vida independiente del Motor Óptico (`KEYS_DOWNSTREAM_MOTOR_OPTICO` lo
  excluye explícitamente desde el 17-sep-2026). Elegir (b) exigiría rediseñar esa
  invalidación — cambio de alcance mayor no abierto por ninguna Spec.
- Por qué SÍ (a): es la arquitectura ya vigente, no una elección nueva.

Separación de las 4 magnitudes (ya existía en `recalcular_fisica_superficie:378-403`,
documentada ahora explícitamente):

| Magnitud | Fuente |
| --- | --- |
| POA geométrica | `calcular_poa_superficie` (pvlib, sin IAM/soiling) — default |
| POA óptica | `poa_sin_termico_df` del Motor Óptico global, solo si `motor_optico_vigente=True` |
| Pérdida térmica | `k_bipv`/NOCT, una sola vez dentro de `simular_bypass_horario` |
| Sombra | `p_shade`/`firma_sombra`, eje independiente |

## Gap 4 — Inversores y configuración eléctrica por superficie

`calculos/inversores_multisuperficie.py`: `derivar_tipo_inversor` (1→dedicado,
2+→compartido, 0→error), `validar_inversores_y_asignaciones` (audita superficie sin
inversor, inversor inexistente, inversor sin superficies, ids duplicados — cada error
nombra la superficie/inversor exacto), `aplicar_tipos_derivados` (sobrescribe un tipo
declarado a mano). 11 pruebas en `tests/test_inversores_multisuperficie.py`.

## Gap 5 — Adaptadores y transiciones

Frontera auditada, ya era correcta:
`adaptador_multisuperficie.construir_proyecto_desde_session_state`/
`aplicar_proyecto_a_session_state` sin cambios (ya rechazaban/escribían correctamente);
`transicion_multisuperficie.py` sin cambios. Pieza agregada:
`calculos/vinculador_sombra_multisuperficie.py` (el tramo entre el motor de sombra y el
adaptador de entrada que faltaba). 8 pruebas propias. Ninguna de las 7 páginas
consumidoras de `multisup_*` ni `calculos/invalidacion.py` fueron tocadas.

## Pruebas ejecutadas

```text
$ pytest tests/test_sombras_por_superficie.py -q                                    → 1 passed
$ pytest tests/test_cobertura_sombra_por_superficie.py -q                           → 6 passed
$ pytest tests/test_vinculador_sombra_multisuperficie.py -q                         → 8 passed
$ pytest tests/test_inversores_multisuperficie.py -q                                → 11 passed
$ pytest tests/test_pagina_transicion_multisuperficie.py tests/test_adaptador_multisuperficie.py -q → 11 passed
```

Total de esta ronda: **37 pruebas nuevas o actualizadas, 0 fallos.**

Suite de regresión completa (`pytest tests/ -q`, excluyendo 5 archivos con fallos de
entorno preexistentes y ajenos a esta ronda: `test_agentes_herramientas.py`/
`test_agentes_system_prompt.py` — falta el paquete `anthropic`; `test_diagrama_unifilar.py`/
`test_perdida_ohmica_cableado.py`/`test_semaforo_ampacidad.py` — `schemdraw` sin backend
Matplotlib utilizable aquí):

```text
1 failed, 1308 passed, 127 warnings in 931.85s (0:15:31)
```

El único fallo (`test_solar_svf.py::test_reduccion_svf_baja_isotropica_en_la_proporcion_exacta`)
es un artefacto de versión de este sandbox, no una regresión de esta ronda: el test espera
que `pvlib.irradiance.haydavies()` devuelva la columna `isotropic` (convención de
`pvlib==0.11.1`, la versión que fija `requirements.txt`), pero este entorno tiene instalado
`pvlib==0.15.2`, que renombró esas columnas a `poa_isotropic`/`poa_sky_diffuse`/etc. El
propio comentario del test lo anticipa ("Si esto falla, pvlib cambió el nombre de columna
en la versión instalada"). Confirmado ajeno a esta ronda: `git status --porcelain` vacío
para `calculos/solar.py` y `tests/test_solar_svf.py` — ninguno de los dos fue tocado, y el
mismatch de versión ya existía antes de empezar.

**Conclusión: 0 regresiones nuevas introducidas por esta ronda, en 1309 pruebas ejecutadas.**

## Qué sigue pendiente y bloqueado

1. UI de captura de puntos de análisis + malla 3D por superficie en Vista_3D.py.
2. UI de asignación de inversor dedicado/compartido por superficie (bloqueada por
   falta de mockup aprobado, `diseno.md` punto 6).
3. Pruebas de integración end-to-end (`diseno.md` punto 8, ítems 1-6).
4. Verificación manual en un proyecto real (imposible sin 1 y 2).
5. Actualizar `mapa-dependencias.md` con los módulos nuevos (reservado al Director).

## Archivos creados y modificados

**Nuevos:** `calculos/vinculador_sombra_multisuperficie.py`,
`calculos/inversores_multisuperficie.py`,
`tests/test_cobertura_sombra_por_superficie.py`,
`tests/test_vinculador_sombra_multisuperficie.py`,
`tests/test_inversores_multisuperficie.py`,
`references/auditoria-cierre-brechas-multisuperficie.md`.

**Modificados:** `calculos/sombras_3d.py`, `pages/9_🗺️_Vista_3D.py`,
`tests/test_sombras_por_superficie.py`, `tests/test_pagina_transicion_multisuperficie.py`,
`CodeSpecs/00-director/registro-de-decisiones.md`,
`CodeSpecs/00-director/contratos-entre-modulos.md`,
`CodeSpecs/05-perdidas-y-temperatura/transicion-multisuperficie/diseno.md`,
`CodeSpecs/05-perdidas-y-temperatura/transicion-multisuperficie/tareas.md`.

Nada de esto toca `calculos/invalidacion.py`, `calculos/adaptador_multisuperficie.py`,
`calculos/transicion_multisuperficie.py`, el Director (`vision.md`/`arquitectura-global.md`),
ni ninguna de las 7 páginas consumidoras de `multisup_*`.
