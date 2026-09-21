# Diseño — Integración de la transición transaccional multi-superficie con Streamlit

**Estado:** aprobado para implementación opt-in; sombras por superficie, Motor Óptico por superficie y UI de inversores permanecen como gates previos

## Entradas

### Contrato de entrada desde `session_state` (punto 1)

El adaptador de entrada (`construir_proyecto_desde_session_state`, nombre
propuesto) lee, por cada superficie de `session_state["superficies_bipv"]`
con `activa=True`:

- Ya existentes hoy: `nombre`, `tipo`, `tilt_deg`, `azimuth_deg`, `area_m2`.
- Globales del proyecto reutilizados tal cual: `panel_dict` (mismo panel
  para todas las superficies, sin cambios respecto a hoy).
- **Nuevos, por superficie** (ver punto 3 — no existen hoy):
  `n_serie`, `n_paralelo`, `inversor_id`, `p_shade` (array 8760),
  `firma_sombra` (dict), y opcionalmente `motor_optico_vigente`,
  `poa_sin_termico_df`, `firma_poa_optica`, `iam_config`, `soiling_config`.
- **Nueva estructura de proyecto** (no existe hoy):
  `session_state["multisup_inversores"]`, lista de
  `{inversor_id, tipo: "dedicado"|"compartido", eta_inversor, P_ac_nom_W,
  ficha}` — ver punto 6.

Regla de consumo: si una superficie activa no trae `n_serie`, `n_paralelo`
o `inversor_id`, el adaptador **no infiere ni completa con un default** —
retorna un error nombrando la superficie y el campo faltante. Mismo
criterio que ya usa `transicion_multisuperficie.py` (rechazo explícito, sin
defaults silenciosos).

## Salidas

### Contrato de salida hacia las claves existentes (punto 2)

El adaptador de salida (`aplicar_proyecto_a_session_state`, nombre
propuesto) traduce `proyecto["agregados"]` y `proyecto["superficies"]` a
las 5 claves que los 8 consumidores YA leen, sin cambiar su forma:

| Clave `session_state` | Origen en `proyecto` | Forma (sin cambios respecto a hoy) |
| --- | --- | --- |
| `E_ac_anual_kWh_multisup` | `agregados["E_ac_total_kWh"]` | `float` |
| `area_total_multisup` | `agregados["area_total_m2"]` | `float` |
| `multisup_desglose` | por superficie: `nombre`, `tipo`, `area_m2`, `resultados_ac["E_ac_anual_kWh"]`, `resultados_dc["poa_anual_kWh_m2"]` | `list[dict]` con claves `nombre, tipo, area_m2, e_ac_kWh, poa_kWh_m2` — IDÉNTICAS a las que ya arma `calculos.multi_superficie.e_ac_total_multisup()` |
| `multisup_activo` | `True` si el adaptador corrió sin error | `bool` |
| `poa_df_multisup` | ponderación por área de `poa_df` por superficie, o `None` si ningún consumidor la necesita hora a hora | `pd.DataFrame` \| `None` |

Regla de consumo: ningún consumidor existente debe requerir cambios de
código para leer estas 5 claves cuando las escribe el adaptador físico en
vez del modelo simplificado — la forma es un contrato ya vigente, este
adaptador solo cambia quién lo llena.

## Falta actual de datos (punto 3)

Confirmado por lectura directa de `pages/9_🗺️_Vista_3D.py` y
`calculos/multi_superficie.py`, no por suposición:

| Dato | Existe hoy | Nota |
| --- | --- | --- |
| Inversor por superficie | No | Un solo inversor/`N_serie` global del proyecto |
| `p_shade` por superficie | No | Multi-superficie no tiene sombreado en absoluto hoy |
| `firma_sombra` | No | El concepto de firma no existe en ninguna página |
| POA del Motor Óptico por superficie | No | `poa_sin_termico_df` es una sola serie global (página 5b) |
| `firma_poa_optica` | No | No existe el concepto |

## Ampliación necesaria de `sombras_3d`/horizonte por superficie (punto 4)

`calculos.sombras_3d` calcula sombra sobre un único conjunto de puntos de
análisis del proyecto (ray-casting contra una malla 3D o una máscara de
horizonte), no por superficie independiente. Para poblar `p_shade`/
`firma_sombra` por superficie se necesita, como mínimo:

- Que el motor acepte un conjunto de puntos de análisis POR superficie
  (hoy asume un único punto base representativo por fachada, ver también
  el caso East2 documentado en `references/`).
- Que emita, junto al array `p_shade`, los metadatos que
  `_validar_firma_sombra` exige: geometría con la que se calculó, puntos
  de análisis, malla/horizonte usados y huella del TMY.

Esta ampliación **no es parte de esta Spec** — es un prerequisito de datos
que debe resolverse en `02-recurso-solar`/`05-perdidas-y-temperatura` (el
módulo de sombreado) antes de que la integración pueda ofrecer sombra real
por superficie. Mientras no exista, las superficies sin `p_shade` real
quedan fuera del modo físico (bloqueadas explícitamente, no con sombra
inventada en 0).

## Decisión: Motor Óptico global vs. por superficie (punto 5) — DECIDIDO 2026-09-21

**Decisión del Director (registrada en `registro-de-decisiones.md`,
2026-09-21): opción (a), Motor Óptico sigue global.** Dos caminos se
evaluaron:

- **(a) Motor Óptico sigue global — ELEGIDA.** Ninguna superficie
  multi-superficie declara `motor_optico_vigente=True` con datos reales en
  la primera versión; el modo físico opera con POA cruda de pvlib
  (`calcular_poa_superficie`) para todas las superficies, salvo que una
  superficie concreta declare explícitamente `motor_optico_vigente=True` con
  su propia `poa_sin_termico_df` real (ya bloqueado sin default silencioso
  por `recalcular_fisica_superficie` — ver siguiente sección). Costo: no hay
  corrección IAM/soiling por superficie en la primera versión.
- **(b) Motor Óptico corre una vez por superficie.** Requeriría modificar
  `pages/5b_🔆_Motor_Optico.py` para producir N corridas en vez de una, con
  sus N firmas — cambio de alcance mayor, propio de una Spec futura separada
  de esta, NO abierta todavía.

Justificación física (no solo de conveniencia): `calculos/invalidacion.py`
ya trata el estado multi-superficie (`KEYS_MULTISUP_ESTADO`) como un ciclo
de vida INDEPENDIENTE del Motor Óptico —
`KEYS_DOWNSTREAM_MOTOR_OPTICO` lo excluye explícitamente desde el
17-sep-2026 porque multi-superficie calcula su propia POA sin depender de
`poa_sin_termico_df`/`poa_efectiva_df` globales—. Elegir (b) exigiría
rediseñar esa invalidación (una POA por superficie, N firmas ópticas), un
cambio de alcance mayor no justificado todavía por ningún caso de uso real
pendiente. Elegir (a) es coherente con la arquitectura YA vigente, no una
elección por conveniencia.

### Separación explícita de las cuatro magnitudes (POA geométrica / POA
óptica / pérdida térmica / sombra), con opción (a) sin IAM/soiling

Ya implementada en `transicion_multisuperficie.recalcular_fisica_superficie`
(líneas 378-403), sin cambios de esta ronda, documentada aquí explícitamente
porque el punto 5 lo exige:

| Magnitud | Fuente | Cuándo se aplica |
| --- | --- | --- |
| POA geométrica | `calculos.multi_superficie.calcular_poa_superficie` (envuelve `calculos.solar.calcular_poa`, pvlib real) | Por defecto, toda superficie sin Motor Óptico vigente |
| POA óptica (IAM+soiling, SIN térmico) | `poa_sin_termico_df` del Motor Óptico global (página 5b) | Solo si esa superficie declara `motor_optico_vigente=True` — bloquea explícito si falta, nunca sustituye en silencio por POA cruda |
| Pérdida térmica | `k_bipv`/NOCT, aplicada UNA sola vez dentro de `mismatch_bypass.simular_bypass_horario` | Siempre, sin importar el origen de la POA — evita doble conteo térmico |
| Sombra | `p_shade`/`firma_sombra`, por superficie (ver `calculos.sombras_3d.calcular_fs_horario_por_superficie`) | Eje totalmente independiente de la POA |

## UI de inversor dedicado/compartido (punto 6)

**Mockup aprobado:** `mockup-ui.md`, aprobación humana del 2026-09-21.
La implementación queda autorizada con los gates descritos allí; el modo
físico sigue siendo opt-in y el modelo simplificado continúa como default.

Propuesta de interacción en `pages/9_🗺️_Vista_3D.py`, pestaña nueva o
sección dentro de "⚙️ Superficies BIPV":

- Una lista de "inversores del proyecto" (nueva, hoy no existe ninguna):
  agregar/eliminar inversor, elegir ficha del catálogo, `eta_inversor`,
  `P_ac_nom_W`.
- Por cada superficie: un selector para asignarla a uno de los inversores
  de la lista.
- Un inversor con exactamente 1 superficie asignada se marca `dedicado`
  automáticamente; con 2+ se marca `compartido` — sin que el usuario tenga
  que declarar el tipo a mano (se deriva, igual que
  `recalcular_etapa_inversor_bus` ya exige esa correspondencia).
- Validación en la UI: un inversor sin ninguna superficie asignada, o una
  superficie sin inversor asignado, bloquea el cálculo físico con un
  mensaje explícito (no un `KeyError`).

## Estrategia opt-in (punto 7)

1. **Default simplificado.** Toggle `multisup_usar_fisico` en
   `session_state`, default `False`. Sin tocarlo, el boton "Integrar" se
   comporta exactamente igual que hoy.
2. **Cálculo físico experimental.** Con el toggle activo, correr el
   adaptador de entrada + `recalcular_fisica_superficie` +
   `recalcular_etapa_inversor_bus` + agregados, SIN escribir todavía en
   las claves `multisup_*` reales.
3. **Comparación lado a lado.** Mostrar simplificado vs. físico:
   `E_ac` total, diferencia %, y por superficie (reusando
   `multisup_desglose` como forma de tabla para ambos). Advertencia
   explícita si la diferencia excede un umbral (mismo criterio ±10% que ya
   usa Producción para el Motor IV).
4. **Adopción explícita.** Un botón separado ("Adoptar cálculo físico")
   ejecuta el adaptador de salida real sobre las 5 claves `multisup_*` —
   nunca ocurre solo por activar el toggle o ver la comparación.
5. **Rollback.** Si `transicion_cambiar_geometria`/`transicion_cambiar_inversor`
   devuelve `ok=False` en cualquier punto, la página muestra el error y
   NO llama al adaptador de salida — `session_state` queda exactamente
   como estaba (mismo comportamiento de rollback que ya garantiza el
   módulo Python).

## Pruebas de página e integración (punto 8)

1. Adaptador de entrada rechaza una superficie incompleta con mensaje
   específico (superficie + campo faltante), no una excepción cruda.
2. Adaptador de salida produce `multisup_desglose` con las mismas 5
   sub-claves que `e_ac_total_multisup()` ya produce.
3. Un intento fallido (`ok=False`) deja `session_state` bit a bit
   idéntico al estado previo.
4. El toggle por defecto está apagado en una sesión nueva.
5. La comparación lado a lado no escribe ninguna clave `multisup_*` hasta
   la adopción explícita.
6. Integración completa: `session_state` realista → adaptador de entrada →
   motor físico → adaptador de salida → Financiero lee el número físico
   nuevo con su lógica de prioridad existente, sin modificarla.

## Criterios de aceptación y bloqueo (punto 9)

**Aceptación** (todas deben cumplirse antes de considerar esta Spec lista
para pasar a `tareas.md` de verdad):

- Las 7 páginas consumidoras de `multisup_*` y `calculos/invalidacion.py` no
  requieren ningún cambio de código.
- El modo físico nunca se activa sin que el usuario encienda el toggle
  explícitamente.
- Ninguna superficie con datos incompletos produce un resultado — bloquea
  con mensaje explícito.
- Las pruebas de página de la sección anterior pasan.

**Bloqueo** (estado a 2026-09-21, actualizado tras la ronda de corrección de
auditoría del mismo día):

- ~~`sombras_3d` no ofrece sombra por superficie (punto 4)~~ — **backend
  resuelto y corregido**: `calcular_fs_horario_por_superficie` acepta
  puntos/geometría por superficie y devuelve un **estado explícito** por
  superficie (`calculado_completo`, `sombra_cero_calculada`,
  `calculo_incompleto`, `error_geometrico`, `resolucion_insuficiente` — ver
  `ESTADOS_SOMBRA_ACEPTABLES`). La ronda de corrección del 2026-09-21 cerró
  dos hallazgos de la auditoría sobre el backend de la ronda anterior:
  - **`tmy_fingerprint` ahora usa el TMY real** (`huella_horaria(tmy.index,
    tmy["T2m"])`), la MISMA fórmula que `transicion_multisuperficie.
    _verificar_geometria_y_tmy` recalcula — antes firmaba un vector de
    ceros, por lo que NINGUNA firma producida por el motor podía pasar
    jamás esa validación (bug reproducido y corregido).
  - **Bloqueo real, no solo advertencia**: `calculos/
    vinculador_sombra_multisuperficie.aplicar_sombra_a_superficies` (primera
    línea de defensa) y `calculos/adaptador_multisuperficie.
    construir_proyecto_desde_session_state` (segunda línea, independiente)
    rechazan explícitamente cualquier superficie cuyo estado no sea
    aceptable — antes, un `calculo_incompleto` solo generaba una advertencia
    de texto y el `p_shade=0` de relleno podía adoptarse igual.
  - La invalidación geométrica se amplió de tilt/azimuth a TODAS las
    entradas de la sombra (área, N_serie, puntos de análisis, malla,
    transparencia) y se agregó invalidación por cambio de TMY
    (`invalidar_sombra_por_cambio_tmy`).

  **Sigue bloqueado**: no existe todavía en `pages/9_🗺️_Vista_3D.py` una UI
  para que el usuario capture puntos de análisis y malla por superficie —
  sin eso, ninguna superficie real puede llegar a tener `p_shade` calculado
  por el motor 3D, solo uno provisto manualmente (vía script o carga
  directa en `session_state`). Ese es el trabajo pendiente concreto, ya no
  una ampliación de arquitectura ni un bug de contrato.
- ~~No existe una decisión del Director sobre Motor Óptico global vs. por
  superficie (punto 5)~~ — **decidido**: opción (a), Motor Óptico global
  (ver sección de decisión arriba, `registro-de-decisiones.md` 2026-09-21).
- La UI de inversor por superficie no está diseñada a nivel de mockup
  aprobado (punto 6) — **sigue bloqueado**. `calculos/inversores_multisuperficie.py`
  provee la validación/derivación pura (dedicado/compartido, asignaciones
  sin defaults silenciosos) y ahora está **conectada** al flujo real:
  `construir_proyecto_desde_session_state` la ejecuta siempre antes de
  construir el proyecto, y sobrescribe cualquier `tipo` declarado a mano por
  el derivado real. Los widgets de asignación en sí no existen todavía —
  evita improvisar la UI sin mockup aprobado.
- **Nuevo, cerrado en esta ronda**: la adopción física en
  `pages/9_🗺️_Vista_3D.py` ya NO confía en que el candidato guardado en
  `session_state["multisup_proyecto_fisico_candidato"]` siga siendo válido
  — el botón "Adoptar cálculo físico" vuelve a ejecutar
  `calculos.vinculador_sombra_multisuperficie.construir_y_recalcular_proyecto_fisico`
  (la misma función única que usa "calcular comparación") con el
  `session_state` ACTUAL antes de publicar, y aborta sin tocar `multisup_*`
  si esa revalidación falla.

## Migración posterior de Vista 3D sin tocar las 7 páginas consumidoras ni `calculos/invalidacion.py` (punto 10)

Orden de trabajo recomendado para una futura fase de implementación (no
parte de esta Spec de diseño):

1. Adaptador de entrada + salida como funciones puras en un módulo nuevo
   `calculos/adaptador_multisuperficie.py` (o dentro de
   `transicion_multisuperficie.py`), con pruebas unitarias propias, SIN
   tocar `pages/9_🗺️_Vista_3D.py` todavía.
2. UI de inversor por superficie + toggle opt-in en
   `pages/9_🗺️_Vista_3D.py`, con el modo físico en modo "solo
   comparación" (paso 2/3 de la estrategia opt-in) — todavía sin poder
   adoptar.
3. Botón de adopción explícita que llama al adaptador de salida.
4. Verificación manual en al menos un proyecto real de que las 8
   consumidoras muestran el número físico igual de bien que mostraban el
   simplificado, sin modificar ninguna de ellas.
5. Solo entonces, evaluar (Spec aparte, decisión del Director) si el modo
   físico pasa a ser el default.

## Dependencias

- Módulo ya validado: `calculos/transicion_multisuperficie.py` (27 pruebas
  propias, 4 rondas de auditoría, 2026-09-20).
- Módulos que esta Spec NO modifica: `calculos/multi_superficie.py`
  (modelo simplificado, coexiste), las 7 páginas consumidoras y
  `calculos/invalidacion.py` que consumen
  `multisup_*`, `calculos/sombras_3d.py`, `pages/5b_🔆_Motor_Optico.py`.
- Specs futuras de las que esta depende antes de una integración completa:
  sombra por superficie (`02-recurso-solar`/`05-perdidas-y-temperatura`) y
  Motor Óptico por superficie (`05-perdidas-y-temperatura`).
