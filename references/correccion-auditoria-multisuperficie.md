# Corrección de auditoría: cierre de brechas multi-superficie BIPV

**Fecha:** 2026-09-21. **Rama:** `fix-cierre-brechas-multisuperficie` (aislada de `main`,
sin commits). **Copia web:** https://claude.ai/artifact/FbzNMMNu65y6ysvsdKYtQ4 (documento
vivo). Esta es la copia local identificable exigida por el encargo. Sin commit ni
despliegue.

## Resumen ejecutivo

Los 5 hallazgos bloqueantes que señaló la auditoría sobre la ronda anterior eran reales
— no observaciones cosméticas — y los cinco quedan corregidos con código y pruebas
ejecutadas:

1. **Firma TMY**: `calcular_fs_horario_por_superficie` firmaba un vector de ceros en vez
   del TMY real; ninguna firma podía pasar jamás la validación de la transición.
   **Corregido**: exige el TMY real, misma fórmula de huella que la transición.
2. **Bloqueo de sombra incompleta**: un cálculo incompleto/erróneo solo advertía, nunca
   bloqueaba. **Corregido**: estado explícito por superficie con bloqueo real en dos
   capas independientes.
3. **Adopción en Vista 3D**: el botón "Adoptar" publicaba el candidato guardado sin
   revalidar. **Corregido**: una función única revalida contra el `session_state`
   actual tanto al calcular como al adoptar.
4. **Inversores desconectados**: `inversores_multisuperficie.py` existía pero nada lo
   llamaba. **Corregido**: el adaptador de entrada lo ejecuta siempre.
5. **Invalidación geométrica incompleta**: solo tilt/azimuth invalidaban la sombra.
   **Corregido**: ampliada a área, N_serie, puntos, malla, transparencia, más
   invalidación separada por cambio de TMY.

**Resultado medible:** la batería focal reportada como `38 passed` pasa a **`116 passed`**
(mismos archivos + la prueba end-to-end nueva exigida). **Lo que NO cambió**: la UI de
captura de puntos/malla por superficie y la UI de inversor (bloqueada por falta de
mockup) siguen sin existir — esta ronda es backend + wiring de página.

## Regla previa cumplida

1. `git status` inicial: 4 archivos modificados sin commitear + 22 nuevos sin trackear
   (heredados de rondas anteriores de esta conversación).
2. Rama aislada creada ANTES de editar: `fix-cierre-brechas-multisuperficie`.
3. No se revirtió ni sobrescribió nada ajeno — todo se extendió.
4. Identificación de mío vs. ajeno hecha antes de tocar código (ver detalle abajo).
5. CodeSpecs leídas (`diseno.md`/`tareas.md`) antes de modificar código.
6. Sin commit ni despliegue.

## Hallazgo 1 — Firma TMY real, no ceros

Bug reproducido antes de corregir:

```
>>> huella_horaria(idx, np.zeros(8760))   # lo que firmaba sombras_3d.py
89d2780c92e9ec8bb3c08f122e791c54ea7abaa5ceb2b7cf96c1c431b5055ac6
>>> huella_horaria(idx, t2m_real)         # lo que valida la transición
4ba8bf357d9fe970e062c5404edde5be605ecf30569eb3dc1edc9a0f5824e2b1
>>> COINCIDEN? False
```

`huella_horaria` firma índice Y valores; firmar ceros garantizaba que NINGUNA firma
producida por el motor pasara nunca `_validar_firma_sombra`. Corrección: el parámetro
`indice_tmy` se reemplazó por `tmy: pd.DataFrame` (exige columna `T2m`), y
`tmy_fp = huella_horaria(idx, tmy["T2m"].to_numpy(dtype=float))` — misma llamada que
`_verificar_geometria_y_tmy`.

5 pruebas nuevas en `tests/test_sombras_por_superficie.py`: firma real pasa
`_validar_firma_sombra`; cambiar T2m cambia la firma; cambiar índice/tz cambia la firma;
TMY distinto provoca rechazo; nunca coincide con un vector de ceros. Más
`test_tmy_debe_ser_dataframe_con_t2m_no_indice_suelto`.

## Hallazgo 2 — Bloqueo real de sombra incompleta

Cinco estados explícitos (`calculos/sombras_3d.py`), precedencia:
`error_geometrico > calculo_incompleto > resolucion_insuficiente >
(sombra_cero_calculada | calculado_completo)`. Solo los dos últimos
(`ESTADOS_SOMBRA_ACEPTABLES`) son válidos sin aprobación adicional.

Bloqueo real en dos capas independientes:
1. `vinculador_sombra_multisuperficie.aplicar_sombra_a_superficies` — nunca escribe
   `p_shade`/`firma_sombra` para un estado no aceptable; retira cualquier resultado
   previo.
2. `adaptador_multisuperficie.construir_proyecto_desde_session_state` — revisa
   `estado_sombra` antes de mirar `p_shade`, rechaza aunque los datos "se vean válidos".

Excepción documentada: `resolucion_insuficiente` solo se acepta con
`aprobacion_resolucion_insuficiente=True` explícito. Mensaje uniforme
(`describir_bloqueo_sombra`) nombra superficie, estado, horas afectadas y acción
requerida.

6 casos exigidos, todos con prueba real: horas no calculadas bloquean; error geométrico
bloquea; resolución insuficiente bloquea o exige aprobación; sombra cero calculada es
válida; p_shade con ceros parciales no publica; superficie inválida impide publicar el
proyecto completo (end-to-end).

## Hallazgo 3 — Adopción en Vista 3D revalida

Gap real: el botón "Adoptar" publicaba `session_state["multisup_proyecto_fisico_candidato"]`
de un rerun anterior sin revalidar. Corrección: función única
`vinculador_sombra_multisuperficie.construir_y_recalcular_proyecto_fisico(session_state,
tmy, lat, lon, alt_m)` — invalidación TMY + construcción + recálculo físico + etapa de
inversor + agregados, todo en una llamada. Tanto "calcular comparación" como "adoptar"
llaman la MISMA función, cada uno con el `session_state` de su momento.

```
comparación -> construir_y_recalcular_proyecto_fisico() [1ª llamada] -> candidato temporal
adopción    -> construir_y_recalcular_proyecto_fisico() [2ª llamada, REVALIDA] ->
               si falla: no publica, no toca multisup_*, motivo exacto
               si pasa: aplicar_proyecto_a_session_state()
```

Verificado con pruebas estáticas de orden (`test_pagina_transicion_multisuperficie.py`) y
ejecución real en `test_flujo_fisico_multisuperficie_end_to_end.py`.

## Hallazgo 4 — Inversores conectados al flujo real

Gap real: `inversores_multisuperficie.py` existía pero nada lo llamaba. Corrección: en
`construir_proyecto_desde_session_state`, antes de construir nada:

```python
validacion_inv = validar_inversores_y_asignaciones(activas, inversores_ss)
if not validacion_inv["ok"]:
    raise ValueError("..." + "; ".join(validacion_inv["errores"]))
inversores_ss = aplicar_tipos_derivados(inversores_ss, validacion_inv["tipos_derivados"])
```

También se agregó validación de `eta_inversor` (0,1] y `n_serie`/`n_paralelo` como
enteros positivos explícitos (antes un valor inválido lanzaba un error crudo de Python).

5 casos exigidos, con pruebas de integración reales: estado válido entra (tipo manual
incorrecto se corrige a partir de la asignación real); asignación inválida bloquea; tipo
manual incorrecto se corrige; inversor huérfano bloquea; una superficie válida y otra
inválida no publica nada.

## Hallazgo 5 — Invalidación geométrica completa

| Entrada | ¿Invalida? |
| --- | --- |
| tilt_deg / azimuth_deg | Sí (ya existía) |
| area_m2 | Sí (nuevo) — condiciona distribución modular |
| n_serie | Sí (nuevo) — el chequeo de resolución modular depende de N_serie |
| puntos_analisis | Sí (nuevo) — comparación de lista completa |
| malla_horizonte | Sí (nuevo) |
| transparencia | Sí (nuevo) |
| resolución espacial/temporal, proveedor | No — son salidas derivadas |
| TMY | Sí (nuevo, capa separada — entrada global, no por superficie) |

`n_serie` se conserva como dato eléctrico pero su cambio invalida la sombra igual que
tilt/azimuth. TMY en función separada `invalidar_sombra_por_cambio_tmy` (compara
`firma_sombra["tmy_fingerprint"]` de cada superficie contra la huella vigente, en lote).

7 pruebas parametrizadas (una por entrada) + 3 pruebas de invalidación por TMY.

## Hallazgo 6 — Prueba end-to-end obligatoria

`tests/test_flujo_fisico_multisuperficie_end_to_end.py`, 7 pruebas, sin mocks de las
piezas físicas (SDM/bypass/POA reales, panel mono-Si con SDM completo). Escenario: 3
superficies — Este (dedicado, sombra 0%), Sur y Oeste (mismo inversor compartido, sombra
10% y 25%).

Pruebas: flujo completo con resultados físicos válidos + publicación exacta de las 5
claves `multisup_*`; modelo simplificado no se toca con el toggle apagado (garantía
estructural); rechazo de TMY alterado; session_state original intacto tras un fallo;
rollback si falla una superficie (inversor inexistente); falta de TMY bloquea explícito;
sombra bloqueada impide publicar el proyecto completo.

## Pruebas ejecutadas

`git diff --check`: exit code 0, sin problemas.

Batería focal exacta pedida + prueba end-to-end:

```
$ pytest tests/test_cobertura_sombra_por_superficie.py \
         tests/test_vinculador_sombra_multisuperficie.py \
         tests/test_inversores_multisuperficie.py \
         tests/test_adaptador_multisuperficie.py \
         tests/test_pagina_transicion_multisuperficie.py \
         tests/test_transicion_multisuperficie.py \
         tests/test_sombras_por_superficie.py \
         tests/test_flujo_fisico_multisuperficie_end_to_end.py -q

116 passed in 9.67s
```

Suite de regresión completa del proyecto (`pytest tests/ -q`, mismos 5 archivos
excluidos por fallos de entorno preexistentes y ajenos: `test_agentes_herramientas.py`/
`test_agentes_system_prompt.py` por falta del paquete `anthropic`;
`test_diagrama_unifilar.py`/`test_perdida_ohmica_cableado.py`/
`test_semaforo_ampacidad.py` por `schemdraw` sin backend Matplotlib utilizable aquí):

```text
1 failed, 1358 passed, 133 warnings in 916.99s (0:15:16)
```

El único fallo (`test_solar_svf.py::test_reduccion_svf_baja_isotropica_en_la_proporcion_exacta`)
es el MISMO artefacto de versión de `pvlib` ya documentado en la ronda anterior (sandbox
con `pvlib==0.15.2` instalado; el test está pineado contra `pvlib==0.11.1`, que nombraba
distinto las columnas de `haydavies()`). Confirmado ajeno a esta ronda: `git status
--porcelain` vacío para `calculos/solar.py` y `tests/test_solar_svf.py` — ninguno de los
dos fue tocado ni en esta ronda ni en la anterior.

**Conclusión: 0 regresiones nuevas introducidas por esta ronda de corrección, en 1359
pruebas ejecutadas.**

## Rama, git status y archivos tocados

**Modificados en esta ronda:** `bipv_python/calculos/sombras_3d.py`,
`bipv_python/calculos/vinculador_sombra_multisuperficie.py`,
`bipv_python/calculos/adaptador_multisuperficie.py`,
`bipv_python/pages/9_🗺️_Vista_3D.py`, `bipv_python/tests/test_sombras_por_superficie.py`,
`bipv_python/tests/test_cobertura_sombra_por_superficie.py`,
`bipv_python/tests/test_vinculador_sombra_multisuperficie.py`,
`bipv_python/tests/test_adaptador_multisuperficie.py`,
`bipv_python/tests/test_pagina_transicion_multisuperficie.py`,
`CodeSpecs/00-director/registro-de-decisiones.md`,
`CodeSpecs/00-director/contratos-entre-modulos.md`,
`CodeSpecs/05-perdidas-y-temperatura/transicion-multisuperficie/diseno.md`,
`CodeSpecs/05-perdidas-y-temperatura/transicion-multisuperficie/tareas.md`.

**Nuevo en esta ronda:**
`bipv_python/tests/test_flujo_fisico_multisuperficie_end_to_end.py`,
`references/correccion-auditoria-multisuperficie.md`.

**No tocados en esta ronda** (de rondas anteriores de la misma conversación):
`transicion_multisuperficie.py`, `inversores_multisuperficie.py` (su contenido no
cambió, solo se conectó desde afuera), archivos de la verificación de `pybdshadow` y
referencias East2.

## Brechas que permanecen abiertas

1. UI de captura de puntos de análisis + malla 3D por superficie — no existe.
2. UI de asignación de inversor dedicado/compartido por superficie — bloqueada por falta
   de mockup aprobado (`diseno.md`, punto 6).
3. Pruebas de integración con Streamlit real — no hay arnés de ejecución real de
   Streamlit en este proyecto; las pruebas de página son estáticas (orden del código
   fuente) más las end-to-end de las funciones puras.
4. Verificación manual en un proyecto real — imposible sin los puntos 1 y 2.
5. Revisión del diff en modo solo lectura (Claude/Copilot) — no ejecutada en esta ronda.
6. Actualizar `mapa-dependencias.md` — reservado al Director.

Ninguno de estos 6 puntos queda oculto: están como checkboxes `[ ]` explícitos en
`tareas.md` de la Spec.
