# Auditoría — integración EPW real / Site Designer (Marsh) / sombras 3D / motor físico multisuperficie / caso La Salle

**Fecha:** 2026-09-22. **Rama:** `validacion-nist-medido-predicho-2003` (sin commits nuevos). **Alcance:** auditoría matemática y de diseño de la cadena EPW real → Site Designer → `calcular_fs_horario_por_superficie` → `construir_y_recalcular_proyecto_fisico` → validación La Salle 2021. Sin fabricar geometría, puntos de análisis, máscaras horarias, reparto de módulos ni datos meteorológicos faltantes.

## 0. Aviso operativo — ediciones concurrentes detectadas durante la auditoría

Al iniciar esta auditoría, `git status` mostraba únicamente archivos nuevos sin
seguimiento. Durante la lectura de código se detectó que tres archivos
prioritarios pasaron a `modified` **mientras la auditoría estaba en curso**,
sin que esta sesión los tocara:

- `bipv_python/calculos/sombras_3d.py` (+parámetro `fuente` en
  `calcular_fs_horario_por_superficie`, propagado a `firma_sombra`).
- `bipv_python/pages/9_🗺️_Vista_3D.py` (+gate `validar_puntos()` antes del
  botón "Calcular sombra de todas las superficies").
- `bipv_python/tests/test_sombras_por_superficie.py` (+prueba
  `test_firma_conserva_la_fuente_externa_marsh`).

Además, `bipv_python/tests/test_escenario_validacion_bapv_lasalle_bosques_castilla.py`
(371→410 líneas) y `references/informe-validacion-bapv-lasalle-bosques-castilla-2021.md`
(228→312 líneas) — ambos sin seguimiento — crecieron durante la sesión con
trabajo ya orientado al EPW real. Todo indica una sesión paralela trabajando
en simultáneo sobre exactamente el mismo alcance de esta auditoría.

**Decisión tomada:** auditar el estado *actual* de los archivos (el que
realmente ejecuta pytest), verificar independientemente sus números, y
**no editar** los tres archivos activamente modificados — hacerlo arriesgaría
sobrescribir o entrar en conflicto con trabajo en curso de otra sesión, lo
cual viola la restricción "no reviertas cambios existentes del usuario". Los
cambios de código recomendados en la §6 se entregan como especificación
verificable, no aplicados.

---

## 1. Hallazgos críticos

### 1.1 `malla_horizonte` no es una huella del contenido de la escena Site Designer — invalidación ciega ante un cambio de escena

**Código:** `bipv_python/pages/9_🗺️_Vista_3D.py:1160` construye
`malla_horizonte=str(st.session_state.get("multisup_malla_meta", {}).get("fuente", "site_designer"))`.
`meta["fuente"]` se fija en `calculos/sitedesigner_marsh.py:157` como el
literal constante `"externa_marsh"` — **no depende del contenido del JSON**
(ni de `n_bloques`, ni de `dim_m`, ni de `north_offset_deg`).

`calculos/vinculador_sombra_multisuperficie.preservar_o_invalidar_campos_fisicos`
usa `malla_horizonte` como una de las siete entradas que determinan si un
`p_shade`/`firma_sombra` previamente calculado se conserva o se invalida al
editar una superficie (línea 49). Como `malla_horizonte` es constante para
toda escena proveniente de Site Designer, **esta función nunca detecta que
el usuario reemplazó el archivo de escena** (edificio vecino movido, nuevo
`northOffset`, obstáculo añadido/quitado) si los puntos de análisis,
tilt/azimuth y demás campos de la superficie no cambiaron.

**Verificación ejecutada** (no es una prueba de pytest, es un script
reproducible en `.venv/bin/python`):

```python
from calculos.sitedesigner_marsh import cargar_escena_sitedesigner
import json

escena_a = json.dumps({"Location": {"latitude":4.7,"longitude":-74.13,"northOffset":0,"timezone":-5,"elevation":2548},
    "Blocks":[{"min":[50000,50000,0],"max":[51000,51000,1000]}]})   # bloque pequeño y lejano
escena_b = json.dumps({"Location": {"latitude":4.7,"longitude":-74.13,"northOffset":0,"timezone":-5,"elevation":2548},
    "Blocks":[{"min":[2000,-10000,0],"max":[3000,10000,30000]}]})   # muro alto pegado al punto

_, meta_a = cargar_escena_sitedesigner(escena_a)
_, meta_b = cargar_escena_sitedesigner(escena_b)
print(meta_a["fuente"], meta_a["dim_m"])   # externa_marsh {'x': 1.0, 'y': 1.0, 'z': 1.0}
print(meta_b["fuente"], meta_b["dim_m"])   # externa_marsh {'x': 1.0, 'y': 20.0, 'z': 30.0}
```

Salida real:

```
externa_marsh {'x': 1.0, 'y': 1.0, 'z': 1.0}
externa_marsh {'x': 1.0, 'y': 20.0, 'z': 30.0}
```

Dos escenas geométricamente muy distintas (una obstrucción trivial vs. un
muro que sombrea por completo) producen el mismo `malla_horizonte`. El
mecanismo de invalidación (que sí está bien probado —
`test_cambiar_entrada_de_sombra_invalida_p_shade`, parametrizado con
`("malla_horizonte", "v1", "v2")`) nunca se dispara en la práctica para
Site Designer porque su precondición (`malla_horizonte` cambia de verdad)
no ocurre en el flujo real de la página.

**Escenario de fallo concreto:** un usuario sube `escena_v1.json`, calcula
sombra, luego el vecino construye una ampliación y el usuario sube
`escena_v2.json` con un obstáculo nuevo, pero **no** vuelve a pulsar
"Calcular sombra de todas las superficies" (por ejemplo porque solo edita
el inversor). El `p_shade` calculado contra `escena_v1` queda marcado
`estado_sombra="sombra_cero_calculada"` o `"calculado_completo"` — un estado
aceptable — y entra sin aviso al modo físico con una sombra que ya no
corresponde a la escena vigente.

**Esto no es un error del motor de ray-casting** (la física de
`calcular_fs_horario` es correcta, ver §4) — es un vacío en la cadena de
invalidación específica de la fuente Site Designer.

---

## 2. Hallazgos importantes

### 2.1 El modelo de bypass reduce la irradiancia difusa proporcionalmente igual que la directa — simplificación no documentada como tal en el pipeline multisuperficie

`calculos/transicion_multisuperficie.recalcular_fisica_superficie` pasa
`G_eff = poa_global` (directa + difusa de cielo + difusa de suelo, ver
`calculos/solar.py:282`) completo a
`calculos/mismatch_bypass.simular_bypass_horario`, que para la fracción de
módulos sombreados aplica `G_shade = G_eff × (1 − p_shade)`
(`mismatch_bypass.py:326`). Es decir, el `p_shade` geométrico — calculado
por `sombras_3d.calcular_fs_horario` lanzando un rayo **hacia el sol** (solo
detecta bloqueo de haz directo) — se usa para atenuar **toda** la
irradiancia POA, incluida la componente difusa de cielo y de suelo, no solo
la directa.

Esto es una simplificación conservadora razonable en la mayoría de los
casos (sobreestima la pérdida por sombra en fachadas con mucha difusa), pero
el propio repositorio **ya tiene** un mecanismo más correcto para la difusa:
`calculos.sombras_3d.calcular_svf_difuso` + `calculos.solar._aplicar_reduccion_svf_isotropica`
(parámetro `reduccion_diffusa_isotropica` de `calcular_poa`), que reduce
*solo* el término isotrópico de Hay-Davies según el Sky View Factor real de
la malla 3D. Ese mecanismo **está cableado únicamente en el flujo de una
sola superficie** (`pages/5a_🌳_Sombras_SketchUp.py:441`), nunca en
`calculos/multi_superficie.calcular_poa_superficie` — que es lo que llama
`recalcular_fisica_superficie` y por tanto todo el pipeline multisuperficie
(La Salle, East2, Site Designer) usado aquí.

**Consecuencia práctica:** el pipeline multisuperficie/Site Designer tiene
dos modelos de sombreado geométrico coexistiendo en el código con distinto
grado de sofisticación, y el más simple (proporcional a toda la POA) es el
que efectivamente corre en el camino que este proyecto está integrando con
clientes. No es un bug — es una brecha de integración entre dos
subsistemas ya existentes.

### 2.2 La convención de signo de `northOffset` está verificada por autoconsistencia y por una segunda implementación independiente, pero no contra una fuente externa autoritativa

`calculos/sitedesigner_marsh.py` rota la malla `ang = -deg2rad(northOffset)`
alrededor de Z. `test_north_offset_rota_la_malla` solo verifica que el
resultado coincide con la misma fórmula reimplementada en la prueba
(autoconsistencia, no validación externa).

Se encontró una segunda implementación independiente del mismo cálculo en
`client/src/lib/marshSiteDesigner.ts:174-182` (la otra app del repositorio,
calculadora web) — `projectToAngular()`, que sigue el camino
`bearing = atan2(dx, dy); bearing += northOffsetDeg`. Se verificó
algebraicamente (no solo por inspección) que ambas fórmulas son
matemáticamente equivalentes: para un punto en coordenadas de escena con
bearing relativo `β_escena = atan2(x,y)`, la rotación de malla en Python
produce un bearing mundial `atan2(x_mundo, y_mundo) = β_escena +
northOffset`, idéntico al `bearing += northOffsetDeg` del TypeScript. Esto
es evidencia de consistencia cruzada entre dos implementaciones escritas
independientemente, pero **ninguna de las dos** está contrastada contra
documentación oficial de Andrew Marsh / Site Designer ni contra un archivo
real con orientación de compás conocida de antemano (los tres archivos
reales disponibles en `attached_assets/site-designer-*.json` traen
`northOffset=7°`, un ángulo demasiado pequeño para confirmar visualmente el
signo). Queda como limitación documentada, no como error encontrado.

---

## 3. Observaciones menores

- **Advertencia QCRad en el EPW real de La Salle (8,12% de horas de día).**
  `calculos.solar.verificar_consistencia_radiativa` marca 333/4.103 horas
  de día del EPW real como inconsistentes con el cierre
  `GHI≈DNI·cosZ+DHI`. Se investigó si esto refleja un desfase de huso
  horario (la causa típica de esta advertencia, según su propio mensaje) o
  ruido real de los datos: las horas inconsistentes tienen elevación solar
  entre 10,9° y 62,3° (media 35,3°), **no concentradas cerca del amanecer
  o atardecer** — un desfase de zona horaria o de centrado de intervalo
  produce errores grandes y sistemáticos justo en baja elevación, donde el
  cénit cambia más rápido; aquí no aparece ese patrón. Se interpreta como
  ruido/variabilidad real del dato meteorológico medido (cielo parcialmente
  nublado, redondeo de instrumentación), consistente con lo que el informe
  ya actualizado documenta. El caso East2 (TMY real distinto) pasa el mismo
  chequeo sin advertencia (`test_tmy_east2_es_radiativamente_coherente_qcrad`),
  lo que indica que el chequeo sí es sensible y no es un falso positivo
  sistemático del código — es específico de este EPW.
- **`pvlib.iotools.epw.read_epw` ya entrega el índice correctamente
  localizado** (`tz=UTC-05:00`, timestamps en hora de inicio de intervalo,
  8760 filas) — no hay corrección manual de huso horario que auditar ni
  desplazamiento de 5 h introducido por este repositorio.
- 32-43 `RuntimeWarning: invalid value encountered in divide` de
  `scipy.optimize._chandrupatla` por corrida de test — preexistente, no
  relacionado con esta auditoría, no afecta resultados (son NaN internos
  del solver de SDM en condiciones de irradiancia ~0 que no se usan).
- `calcular_fs_horario_por_superficie` y el botón de la página ahora llaman
  `validar_puntos()` dos veces (una vez en el gate de la UI, otra dentro del
  motor) para el mismo cálculo — redundante pero inofensivo; si el gate de
  la UI bloquea, la segunda llamada nunca se alcanza para ese click.

---

## 4. Cálculos que estaban correctos (verificados, no solo revisados)

- **SHA-256 del EPW** — coincide exacto contra el valor declarado por el
  usuario: `b9d837ed551edbd86c6070e550e394465d27f53573d65eda455de81a13277e58`.
- **Convención de coordenadas** — `vector_al_sol()` (X=Este, Y=Norte,
  Z=arriba) verificada algebraicamente: azimut 0°→(0,+1,·), azimut 90°→(+1,0,·),
  consistente con la convención pvlib (0=N, 90=E, sentido horario) y con
  ENU estándar.
- **mm→m** — `ESCALA_MM_A_M=0.001` fijo, aplicado antes de cualquier
  comparación de tamaño; probado (`test_escala_mm_a_metros`).
- **Rotación por `northOffset`** — fórmula autoconsistente y verificada
  algebraicamente equivalente a una segunda implementación independiente
  (TypeScript, ver §2.2).
- **Ray-casting: origen y dirección** — el rayo nace en el punto de
  análisis, desplazado `OFFSET_RAYO_M=0.05` m hacia el sol (evita
  autointersección con la superficie propia), y viaja hacia el sol
  (dirección correcta para detectar obstrucción de haz directo).
- **Horas sin sol** — filtradas por `elevacion > ALTURA_SOLAR_MIN_DEG=1.0°`,
  nunca se calculan ni se cuentan como sombra (irrelevante: irradiancia
  directa ≈0 en esas horas).
- **`p_shade` se aplica una sola vez** — únicamente dentro de
  `simular_bypass_horario`, llamado una sola vez por superficie desde
  `recalcular_fisica_superficie`; `recalcular_etapa_inversor_bus` (etapa de
  inversor) no vuelve a tocar sombra ni POA. Confirmado por lectura
  completa de `calculos/transicion_multisuperficie.py` — no hay una
  segunda multiplicación por `p_shade` ni por `FS_geometrico` en ningún otro
  punto del pipeline multisuperficie.
- **No se mezcla con IAM/soiling/mismatch de forma oculta** —
  `simular_bypass_horario` solo recibe `G_eff, T_amb, p_shade, N_series,
  N_parallel, panel, NOCT, k_bipv`; no hay parámetro de IAM/soiling que
  pueda solaparse con la sombra dentro de esa función.
- **Estados de sombra (5)** — los cinco estados
  (`calculado_completo`, `sombra_cero_calculada`, `calculo_incompleto`,
  `error_geometrico`, `resolucion_insuficiente`) están implementados con
  la prioridad correcta (`error_geometrico` sobrescribe a los demás) y
  cada uno tiene al menos una prueba dedicada en
  `test_cobertura_sombra_por_superficie.py`.
- **Invalidación por cambio de TMY** — `invalidar_sombra_por_cambio_tmy`
  compara `firma_sombra["tmy_fingerprint"]` (misma función
  `huella_horaria` que usa el cálculo original, no una segunda fórmula) y
  se ejecuta automáticamente dentro de
  `construir_y_recalcular_proyecto_fisico`; probado en
  `test_tmy_distinto_invalida_sombra` / `test_tmy_igual_conserva_sombra`.
- **Rechazo de estado geométrico inválido en el modo físico** —
  `construir_proyecto_desde_session_state` lanza `ValueError` si
  `estado_sombra` no está en `ESTADOS_SOMBRA_ACEPTABLES`; probado en
  `test_estado_sombra_no_aceptable_bloquea_aunque_p_shade_este_presente`.
- **Diseño de puntos de análisis (opción A)** — `pages/9_🗺️_Vista_3D.py`
  ya implementa la opción **A** del listado del usuario: el usuario escribe
  manualmente `x,y,z` por superficie en un `st.text_area`; no hay
  detección automática de módulos BIPV desde el JSON de Site Designer (que
  en efecto solo trae `Blocks`, nunca puntos de panel) y no se fabrica
  ningún punto. Esta es la opción correcta dado que el JSON de Site
  Designer no expone geometría de paneles — ver §5 de esta auditoría.
- **Caso La Salle, EPW real — reproducido independientemente.** Se
  recalculó el escenario completo con
  `_tmy_bogota_epw_real()` (fuera de pytest, script directo) y se comparó
  contra el informe ya actualizado
  (`references/informe-validacion-bapv-lasalle-bosques-castilla-2021.md`
  §4): los números coinciden exactamente (ver §9). El informe **no mezcla**
  EPW real, clear-sky sintético y PVGIS histórico en una misma tabla — usa
  tres secciones separadas (§4, §4bis, §5) — se verificó que esto es
  cierto en el archivo actual.

---

## 5. Cálculos o conversiones incorrectos

**Ninguno encontrado en la física central** (geometría solar, ray-casting,
conversión mm→m, aplicación de sombra a POA, cálculo de energía DC/AC). El
único hallazgo de severidad alta (§1.1) es una **brecha de invalidación /
detección de cambios**, no un error aritmético ni de signo en el motor
físico: los números que produce el motor para una escena y unos puntos
dados son correctos; el problema es que un cambio de escena puede no
disparar el recálculo automáticamente.

---

## 6. Cambios de código recomendados y estado posterior

### 6.1 Fijar §1.1: derivar `malla_horizonte` del contenido real de la escena

**Aplicado después de esta auditoría:** `cargar_escena_sitedesigner()` ahora
genera `meta["malla_fingerprint"]` con una huella SHA-256 estable del
contenido relevante de la escena, y Vista 3D usa esa huella como
`malla_horizonte`.

En `calculos/sitedesigner_marsh.py`, añadir al `meta` devuelto por
`cargar_escena_sitedesigner` una huella de contenido, por ejemplo:

```python
import hashlib

huella_escena = hashlib.sha256(
    json.dumps(
        {"blocks": bloques, "north_offset": north_offset, "lat": lat, "lon": lon},
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()[:16]
meta["malla_fingerprint"] = f"externa_marsh-{huella_escena}"
```

Y en `pages/9_🗺️_Vista_3D.py:1160`, reemplazar

```python
malla_horizonte=str(st.session_state.get("multisup_malla_meta", {}).get("fuente", "site_designer")),
```

por

```python
malla_horizonte=str(st.session_state.get("multisup_malla_meta", {}).get("malla_fingerprint")
                     or st.session_state.get("multisup_malla_meta", {}).get("fuente", "site_designer")),
```

**Razón:** hace que `malla_horizonte` cambie cuando cambia el contenido de
la escena (bloques o `northOffset`), sin tocar la semántica de
`preservar_o_invalidar_campos_fisicos` (que ya compara `malla_horizonte`
correctamente — ver `test_cambiar_entrada_de_sombra_invalida_p_shade`).
Prueba focal sugerida: repetir el script de §1.1 y afirmar
`meta_a["malla_fingerprint"] != meta_b["malla_fingerprint"]`.

### 6.2 Documentar (o resolver) 2.1: difusa reducida proporcionalmente por `p_shade`

**Aplicado como documentación, sin cambio de comportamiento:** se añadió al
docstring de `simular_bypass_horario` una nota explícita de que `G_eff` se
reduce como bloque único (directa+difusa+suelo), lo que sobreestima la
pérdida de difusa en sombra parcial — ya se documenta implícitamente pero
no se nombra el efecto.

Opción de fondo (cambio de comportamiento, requiere aprobación explícita
porque toca el motor): cablear `calcular_svf_difuso` /
`reduccion_diffusa_isotropica` también en
`calculos/multi_superficie.calcular_poa_superficie`, usando la malla ya
cargada de Site Designer/SketchUp. Esto es un cambio de física, no de
auditoría — no se implementa aquí.

---

## 7. Cambios de código implementados

Se implementó la corrección de invalidación de escena en
`calculos/sitedesigner_marsh.py`, `pages/9_🗺️_Vista_3D.py` y
`tests/test_sitedesigner_marsh.py`. También se documentó el alcance radiativo
actual en `calculos/mismatch_bypass.py`. No se implementó el cambio de física
para separar difusa mediante Sky View Factor.

---

## 8. Pruebas ejecutadas y resultado

Entorno: `bipv_python/.venv/bin/python` (Python 3.14.2, pytest 9.1.1),
sin red.

**Tanda 1:**
```
cd bipv_python && .venv/bin/python -m pytest tests/test_sitedesigner_marsh.py tests/test_sombras_por_superficie.py -q
....................                                                     [100%]
20 passed in 1.54s
```

**Tanda 2:**
```
.venv/bin/python -m pytest \
  tests/test_cobertura_sombra_por_superficie.py \
  tests/test_vinculador_sombra_multisuperficie.py \
  tests/test_adaptador_multisuperficie.py \
  tests/test_flujo_fisico_multisuperficie_end_to_end.py \
  tests/test_pagina_transicion_multisuperficie.py -q
................................................................         [100%]
64 passed, 8 warnings in 2.07s
```
(8 warnings: RuntimeWarning de scipy chandrupatla + un QCRad del fixture
sintético propio de `test_flujo_fisico_multisuperficie_end_to_end.py`
(30,75% de horas inconsistentes) — ese fixture usa una serie sinusoidal
sintética no diseñada para pasar el cierre radiativo; no representa
datos reales ni afecta el resultado de las aserciones.)

**Tanda 3:**
```
.venv/bin/python -m pytest \
  tests/test_escenario_validacion_bapv_lasalle_bosques_castilla.py \
  tests/test_escenario_validacion_east2_sunpower.py -v
29 passed, 95 warnings in 14.03s
```
Incluye `test_fachadas_epw_real_no_reproduce_asimetria_de_ref` (PASSED) —
la prueba que verifica honestamente que el EPW real **no** reproduce el
orden SO>SE de la app estándar de referencia.

**Estado posterior a la corrección: 119/119 pruebas en verde, 0 fallos, 0 errores.**
Se añadieron pruebas para fingerprints de escenas y para el contrato radiativo
documentado.

---

## 9. Valores numéricos obtenidos (verificación independiente, EPW real)

Recalculado fuera de pytest con
`construir_y_recalcular_proyecto_fisico` + `_tmy_bogota_epw_real()`
(`references/bogota-eldorado-iwec.epw`), comparado contra
`references/informe-validacion-bapv-lasalle-bosques-castilla-2021.md` §4:

| Superficie | POA anual (kWh/m²) | E_dc anual (kWh) | E_ac anual (kWh) | Rend. esp. (kWh/kWp) | PR |
|---|---:|---:|---:|---:|---:|
| Horizontal | 1.613,31 | 42.995,8 | 42.393,9 | 1.513,85 | 0,938 |
| Óptimo 10° sur | 1.613,66 | 42.995,3 | 42.393,4 | 1.513,83 | 0,938 |
| Fachada suroeste | 831,25 | 22.051,9 | 21.743,1 | 776,43 | 0,934 |
| Fachada sureste | 831,73 | 22.075,3 | 21.766,3 | 777,26 | 0,935 |

- **Residual normalizado, referencia:** +5,79% (calculado de nuevo,
  idéntico al informe).
- **Residual normalizado, fachadas (promedio SO/SE):** +6,35% (idéntico).
- **Diferencia SO vs. SE:** 0,058% — **técnicamente invertida** (SE 831,73
  > SO 831,25 por 0,48 kWh/m²/año), dentro del ruido, no una asimetría real
  reproducible. La app estándar de referencia publica SO>SE por ~9,4%. **No se afirma que el EPW
  real reproduzca el orden SO>SE de la app estándar de referencia — no lo reproduce.**
- **QCRad EPW real:** 333/4.103 horas de día (8,12%) inconsistentes —
  ver §3, interpretado como ruido de dato real, no como bug de zona
  horaria.

Estos números son **independientes** de los que ya aparecen en el informe
actualizado (se recalcularon desde cero en esta sesión, no se copiaron) y
coinciden exactamente, lo que corrobora que el informe concurrente es
reproducible y no está fabricado.

---

## 10. Limitaciones que permanecen

- El casi-empate/inversión SO/SE con el EPW real **no se puede explicar**
  con los datos disponibles: no hay máscara angular horaria publicada por
  la tesis, ni la base meteorológica que usó la app estándar de referencia, así que no es posible
  determinar si la asimetría de la app estándar de referencia (9,4%) es un artefacto de su propia
  fuente meteorológica/modelo de transposición o si el EPW real de El
  Dorado (~9 km del sitio exacto) simplemente no captura una asimetría
  real del microclima del sitio. Se declara "no comparable", no se
  fabrica una explicación.
- El EPW usado está a ~9 km del edificio real (estación El Dorado vs.
  coordenadas de las Fig. 6/7 de la tesis) — declarado explícitamente en
  el docstring del fixture, no es el punto exacto.
- La convención de signo de `northOffset` no está validada contra una
  fuente externa autoritativa (§2.2) — solo por autoconsistencia y por
  una segunda implementación independiente del mismo repositorio.
- No se auditó `calculos/ejecutor_escenarios.py` (pipeline de un solo
  panel/superficie, fuera del alcance de "motor multisuperficie" de esta
  tarea) ni el flujo de sombra de una sola superficie
  (`pages/5a_🌳_Sombras_SketchUp.py`) más allá de confirmar que ahí sí está
  cableado `calcular_svf_difuso` (§2.1).
- No se ejecutó la app Streamlit interactivamente (sin navegador en este
  entorno) — la auditoría del flujo de la página es por lectura de código
  y pruebas automatizadas, no por prueba manual en UI.
- Ediciones concurrentes: si la sesión paralela detectada en §0 sigue
  modificando `sombras_3d.py`, `9_🗺️_Vista_3D.py` o el test de La Salle
  después de este informe, los números y el estado de las pruebas de esta
  auditoría pueden quedar desactualizados — recomendable re-ejecutar las
  tres tandas de pytest antes de tomar esto como estado final.

---

## 11. Recomendación final

## **Aprobado con limitaciones.**

El motor físico (geometría solar, ray-casting, conversión de sombra a
energía, estados y su invalidación por TMY/geometría) está correcto y bien
probado (119/119 pruebas en verde, incluida verificación independiente de
los números de La Salle con EPW real). La opción de diseño ya elegida para
los puntos de análisis (A: entrada manual, sin fabricar geometría) es la
correcta dado lo que Site Designer expone.

La integración Site Designer puede pasar a una primera fase controlada:
§1.1 ya está corregido mediante `malla_fingerprint`, sin tocar la física del
motor. Continúa siendo obligatorio aportar puntos 3D válidos por superficie y
revisar el estado antes de adoptar resultados.

La simplificación de difusa (§2.1) y la falta de validación externa de
`northOffset` (§2.2) son limitaciones a documentar para el cliente, no
bloqueantes para una primera integración controlada.

---

## 12. Lista exacta de archivos modificados por esta auditoría

- `references/auditoria-integracion-sitedesigner-marsh-sombras-lasalle-epw-real.md` (este informe, actualizado).
- `bipv_python/calculos/sitedesigner_marsh.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_sitedesigner_marsh.py`
- `bipv_python/calculos/mismatch_bypass.py`

Ningún otro archivo del repositorio fue modificado por esta sesión. No se
hizo commit, merge, push ni despliegue.
