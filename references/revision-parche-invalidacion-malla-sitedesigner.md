# Revisión senior — parche de invalidación de sombra por cambio de escena Site Designer

**Fecha:** 2026-09-22. **Rama:** `validacion-nist-medido-predicho-2003` (sin commits nuevos).
**Rol:** revisión, no implementación — no se editó código en esta ronda (ningún defecto
concreto lo justificó). **Alcance revisado:**

```
Site Designer JSON → malla_fingerprint → firma_sombra["malla_horizonte"]
  → invalidar_sombra_por_cambio_malla() → construir_y_recalcular_proyecto_fisico()
```

Parche bajo revisión (implementado en una ronda anterior de esta misma sesión):
`bipv_python/calculos/vinculador_sombra_multisuperficie.py`,
`bipv_python/tests/test_vinculador_sombra_multisuperficie.py`,
`bipv_python/tests/test_flujo_fisico_multisuperficie_end_to_end.py`.

## 1. Hallazgos críticos

Ninguno.

## 2. Hallazgos importantes

Ninguno. La invalidación se integra correctamente, no hay regresión numérica y la
compatibilidad legacy se conserva (ver §4-§5).

## 3. Hallazgos menores

1. **Mensaje de `sombra_bloqueo_motivo` puede atribuir la causa incorrecta en un
   cambio simultáneo TMY + escena.** Si TMY y escena cambian a la vez,
   `invalidar_sombra_por_cambio_tmy()` corre primero y ya retira `firma_sombra`
   (incluye `malla_horizonte`); cuando `invalidar_sombra_por_cambio_malla()` corre
   después, `firma_sombra` ya es `None`, así que no encuentra nada que invalidar de
   nuevo. El resultado final es correcto (la superficie queda invalidada de todas
   formas — no hay sombra obsoleta aplicada), pero el mensaje que ve el usuario dice
   "TMY distinto" aunque la escena también haya cambiado. Es un problema puramente
   de diagnóstico/UX, no de seguridad de los datos. No amerita parche sin que el
   usuario decida si vale la pena el mensaje compuesto.
2. **Sin prueba automatizada dedicada a que `northOffset` por sí solo cambie la
   huella.** Verificado manualmente en esta revisión (misma geometría de bloques,
   `northOffset=0` vs. `90` → huellas `externa_marsh-ff23b4eb3431d179` vs.
   `externa_marsh-b8c8aee147fdfd90`, distintas) — el comportamiento es correcto,
   pero `test_escenas_distintas_tienen_huellas_distintas` solo varía el tamaño de
   un bloque, nunca `northOffset` en aislamiento. Gap de cobertura, no defecto.
3. **Sin prueba automatizada dedicada a `firma_sombra=None` explícito ni a
   `malla_horizonte` con tipo no-string.** Verificado manualmente en esta revisión
   (script ad hoc, ver §4) — ambos casos se manejan de forma segura (no se invalida,
   no hay excepción), pero no están codificados como prueba de regresión.

Ninguno de los tres amerita un parche por sí solo (verificados como comportamiento
correcto); se dejan como recomendación de cobertura si el equipo decide añadir esas
pruebas en una ronda futura.

## 4. Revisión de la lógica de invalidación

Verificado leyendo el código y con un script de verificación ad hoc (no se modificó
ningún archivo de test):

| Propiedad exigida | Verificado | Cómo |
|---|---|---|
| No muta la lista original | ✅ | `dict(sup)` crea copia superficial nueva en ambas ramas; `sup` de entrada nunca se modifica in-place. |
| Conserva superficies que no deben invalidarse | ✅ | Rama `else: salida.append(dict(sup))` — copia íntegra, incluye `p_shade`/`firma_sombra`. |
| Elimina todos los campos de `_CAMPOS_SOMBRA` | ✅ | `for campo in _CAMPOS_SOMBRA: nueva.pop(campo, None)` — mismos 6 campos que usa `invalidar_sombra_por_cambio_tmy`. |
| Mantiene `sombra_bloqueo_motivo` | ✅ | Se asigna explícitamente después del `pop` (no está en `_CAMPOS_SOMBRA`, así que el `pop` no lo toca). |
| No elimina campos eléctricos/geométricos | ✅ | `n_serie`, `n_paralelo`, `inversor_id`, `tilt_deg`, `azimuth_deg`, `area_m2`, `uid`, `nombre`, `tipo`, `activa` no están en `_CAMPOS_SOMBRA`; verificado con script: se preservan intactos tras invalidar. |
| No genera energía/resultados físicos obsoletos | ✅ | La función no toca `resultados_dc`/`resultados_ac` (no están en `_CAMPOS_SOMBRA`, no forman parte de `superficies_bipv` crudo); el recálculo físico corre siempre después, sobre superficies reconstruidas desde cero por `superficie_nueva()`. |
| Fingerprint coincidente | ✅ | `test_malla_igual_conserva_sombra` — conserva `p_shade`/`firma_sombra` íntegros. |
| Fingerprint distinto | ✅ | `test_malla_distinta_invalida_p_shade_externa_marsh` — invalida y fija `sombra_bloqueo_motivo`. |
| Fingerprint actual ausente (`None`) con firma Site Designer presente | ✅ | `test_malla_sin_escena_cargada_invalida_sombra_externa` — invalida (no hay con qué confirmar vigencia). |
| Firma ausente (`firma_sombra` no está en el dict) | ✅ | Cubierto en `test_superficie_sin_malla_externa_no_se_toca_por_invalidacion_malla` (`sup_sin_firma`) — no se toca. |
| Firma legacy (`malla_horizonte` sin prefijo `externa_marsh-`) | ✅ | `test_malla_no_prefijada_externa_marsh_no_se_toca` — no se toca. |
| `firma_sombra=None` explícito | ✅ (verificado manualmente, sin test dedicado — hallazgo menor #3) | `isinstance(None, Mapping)` es `False` → `malla_firma=None` → no invalida. Script ad hoc confirma `p_shade` conservado. |
| `malla_horizonte` con tipo no-string (int, list) | ✅ (verificado manualmente, sin test dedicado — hallazgo menor #3) | `isinstance(malla_firma, str)` es `False` para `int`/`list` → no invalida, sin excepción. |

## 5. Revisión de compatibilidad legacy

- **La Salle y East2:** ninguno de los dos escenarios de validación fija
  `malla_horizonte` en su `firma_sombra` ni `multisup_malla_meta` en su
  `session_state` (confirmado con `grep` sin resultados sobre ambos archivos de
  test) → `invalidar_sombra_por_cambio_malla()` es un no-op garantizado en los dos.
- **Tests legacy** (`test_flujo_fisico_multisuperficie_end_to_end.py`,
  `test_cobertura_sombra_por_superficie.py`, `test_pagina_transicion_multisuperficie.py`):
  usan valores como `"malla-e2e-v1"`, `"box-test-v1"`, `"test"` — ninguno empieza
  por `externa_marsh-`, así que no entran en el chequeo nuevo.
- **Flujo SketchUp / otras fuentes:** cualquier `malla_horizonte` que no traiga el
  prefijo literal `externa_marsh-` (que solo produce
  `sitedesigner_marsh.cargar_escena_sitedesigner()`) queda fuera del alcance de esta
  invalidación, por diseño — no se duplica ni se reinterpreta la lógica de huella
  existente para otras fuentes.
- **Superficies sin `malla_horizonte`:** no se tocan (ver tabla §4).

## 6. Pruebas ejecutadas y resultados exactos

**a) Las 4 pruebas obligatorias, por nombre:**
```
cd bipv_python
.venv/bin/python -m pytest \
  tests/test_vinculador_sombra_multisuperficie.py::test_malla_distinta_invalida_p_shade_externa_marsh \
  tests/test_vinculador_sombra_multisuperficie.py::test_malla_igual_conserva_sombra \
  tests/test_vinculador_sombra_multisuperficie.py::test_superficie_sin_malla_externa_no_se_toca_por_invalidacion_malla \
  tests/test_flujo_fisico_multisuperficie_end_to_end.py::test_construir_proyecto_invalida_por_cambio_de_escena_site_designer \
  -v
```
Resultado: **4 passed in 1.12s** — las 4 PASSED individualmente.

**b) Regresión focal (7 archivos):**
```
.venv/bin/python -m pytest \
  tests/test_sitedesigner_marsh.py tests/test_sombras_por_superficie.py \
  tests/test_cobertura_sombra_por_superficie.py tests/test_vinculador_sombra_multisuperficie.py \
  tests/test_adaptador_multisuperficie.py tests/test_flujo_fisico_multisuperficie_end_to_end.py \
  tests/test_pagina_transicion_multisuperficie.py -q
```
Resultado: **92 passed, 16 warnings in 3.34s**. Warnings: únicamente QCRad
(`calculos/solar.py:298`, TMY sintético del test E2E) y
`scipy.optimize._chandrupatla` (`invalid value encountered in divide`, SDM) — los
dos mismos orígenes ya documentados en la ronda de cierre anterior. **Sin warnings
nuevos.**

**c) Regresión de escenarios de validación:**
```
.venv/bin/python -m pytest \
  tests/test_escenario_validacion_bapv_lasalle_bosques_castilla.py \
  tests/test_escenario_validacion_east2_sunpower.py -q
```
Resultado: **29 passed, 95 warnings in 14.42s**. Mismos dos orígenes de warning
(QCRad + chandrupatla), proporcionalmente más porque ambos escenarios corren el
pipeline físico completo hora a hora. **Sin warnings nuevos.**

**Conteo total verificado:** 4 (obligatorias, subconjunto de las 92) + 92 (focal) +
29 (escenarios) — las 4 obligatorias están incluidas dentro de las 92 de la
regresión focal, no se suman aparte. El conteo coincide exactamente con la
ejecución real (pegado arriba, no resumido).

## 7. Comparación numérica La Salle/East2

| Magnitud | Antes del parche | Después del parche (esta revisión) | Lectura |
|---|---:|---:|---|
| La Salle — E_ac Horizontal (kWh) | 79.748,2 | 79.748,2 | Idéntico |
| La Salle — E_ac Óptimo-10-Sur (kWh) | 79.690,6 | 79.690,6 | Idéntico |
| La Salle — E_ac Fachada-Suroeste (kWh) | 39.383,2 | 39.383,2 | Idéntico |
| La Salle — E_ac Fachada-Sureste (kWh) | 28.542,6 | 28.542,6 | Idéntico |
| La Salle — residual normalizado (bloque D) | +4,884377% | +4,884377% | Idéntico, reverificado en esta ronda |
| East2 — suite completa (20 tests) | verde | verde (incluida en las 29 de §6c) | Sin cambio |

Sin variación en ninguna cifra — esperado, dado que ninguno de los dos escenarios
activa el camino nuevo (§5).

## 8. Archivos modificados en esta revisión

Ninguno de código. Esta ronda fue de revisión: no se encontró ningún defecto que
justificara un cambio (los tres puntos de §3 son observaciones de cobertura de
test, no defectos funcionales). Único archivo nuevo: esta copia Markdown
(`references/revision-parche-invalidacion-malla-sitedesigner.md`).

## 9. Diff relevante

Sin diff nuevo — el parche bajo revisión es exactamente el ya entregado y
documentado en el cierre anterior de esta misma sesión
(`bipv_python/calculos/vinculador_sombra_multisuperficie.py` +48 líneas función
`invalidar_sombra_por_cambio_malla` y su integración en
`construir_y_recalcular_proyecto_fisico`; +53 líneas de pruebas en
`test_vinculador_sombra_multisuperficie.py`; +38 líneas de pruebas en
`test_flujo_fisico_multisuperficie_end_to_end.py`). No se tocó nada adicional.

## 10. Veredicto final

**APROBADO.**

Se aprueba porque:
- La invalidación por cambio de escena es correcta en los 10 casos de borde
  auditados en §4 (incluidos 3 verificados manualmente por no tener prueba
  dedicada, sin encontrar ningún comportamiento incorrecto).
- No hay regresiones: 92 + 29 pruebas en verde, sin warnings nuevos.
- Las pruebas nuevas cubren el caso crítico (escena distinta invalida, escena
  igual conserva, sin escena externa no se toca, el flujo físico completo rechaza
  la construcción del proyecto en vez de usar sombra obsoleta en silencio).
- La compatibilidad legacy se conserva (La Salle, East2, tests legacy, SketchUp).
- No se usa `p_shade` obsoleto bajo ningún escenario probado — el caso del §5 del
  encargo (escena A calculada, escena B cargada, sin recalcular) termina en
  `ValueError` explícito antes de construir el proyecto, nunca en un cálculo
  silencioso con datos viejos.
- La física numérica de La Salle/East2 permanece idéntica cifra por cifra.

Los tres hallazgos menores de §3 no bloquean la aprobación — son gaps de
cobertura de test verificados como comportamiento correcto, no defectos.

No se hizo commit, merge, push ni despliegue.
