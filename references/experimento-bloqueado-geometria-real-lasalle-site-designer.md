# Experimento bloqueado — geometría real Site Designer para La Salle 2021 (Bosques de Castilla)

**Fecha:** 2026-09-22. **Rama:** `validacion-nist-medido-predicho-2003` (sin commits
nuevos). **Rol:** cierre experimental de la duda "limitación de entrada vs. defecto
interno" para la asimetría SO/SE. **Cambios de código:** ninguno — el experimento
se detiene antes de necesitar ninguno (ver §1).

## Pregunta que se intentó cerrar

> ¿La APP no reproduce la asimetría SO/SE de la app estándar de referencia porque le faltaban la geometría
> 3D y las sombras reales, o existe un defecto interno en nuestros cálculos?

**No se puede cerrar experimentalmente con datos reales.** El motivo exacto: no
existe en el repositorio ninguna escena Site Designer del edificio real (Torre 5,
Bosques de Castilla). Este documento entrega todo lo que SÍ se pudo verificar de
forma reproducible sin fabricar esa escena, y deja explícito qué falta para cerrar
la pregunta.

## 1. Estado de disponibilidad del JSON Site Designer real

Búsqueda exhaustiva en el repositorio (`find` sobre `attached_assets/`,
`references/`, `bipv_python/datos/`, y el resto del árbol excluyendo
`node_modules`/`.git`/`.venv`). Resultado: **3 archivos** con nombre
`site-designer-*.json`, todos en `attached_assets/`:

| Archivo | `Location.latitude` | `Location.longitude` | `northOffset` | `elevation` | Bloques |
|---|---:|---:|---:|---:|---|
| `site-designer-2026-07-14-1606-10_1786198985402.json` | 4.702 | -74.147 | 7 | 2548.4 | 1 (`TreeBlock`, 4.2×3.2×10 m) |
| `site-designer-2026-08-08-1832-43_1786247034057.json` | 4.702 | -74.147 | 7 | 2548.4 | 1 (caja genérica, 4.5×28×25 m) |
| `site-designer-2026-08-08-2251-20_1786247506266.json` | 4.702 | -74.147 | 7 | 2600 | 1 (caja genérica, 4.5×28×25 m) |

Ninguno trae nombre de proyecto, capa o metadato que lo identifique como Bosques
de Castilla. Los tres son, por su propia estructura (un único bloque sin
subdivisión, uno explícitamente un árbol), los archivos de ejemplo que ya usa
`test_sitedesigner_marsh.py::test_archivo_real_de_ejemplo` para probar que el
lector no falla con datos reales — no una modelación de un edificio.

## 2. Validación de correspondencia con Bosques de Castilla

**No corresponde.** Verificación cuantitativa:

- **Ubicación:** los 3 archivos usan lat=4.702, lon=-74.147. Bosques de Castilla
  (leído de las Fig. 6/7 de la tesis, confirmado contra la altitud PVGIS en la
  ronda de validación anterior) está en lat=4.634, lon=-74.148 — una diferencia de
  0.068° en latitud, **≈7.6 km** de distancia. No es tolerancia de redondeo, es
  otro punto de la ciudad.
- **Geometría:** un solo bloque por archivo. Bosques de Castilla es una torre de
  13 pisos con dos fachadas verticales libres (suroeste y sureste) — un único
  paralelepípedo sin subdivisión ni identificación de fachada no permite distinguir
  "fachada suroeste" de "fachada sureste" dentro de la escena, que es precisamente
  lo que este experimento necesita comparar.
- Uno de los tres archivos es explícitamente un `TreeBlock` (árbol decorativo de
  Site Designer), no una edificación.

**Conclusión:** ninguno de los tres archivos es una escena válida de Bosques de
Castilla, ni con tolerancia relajada.

## 3. Validación de puntos de análisis

No aplica: al no existir una escena real del edificio, tampoco existen puntos de
análisis (posiciones de paneles) que referencien sus fachadas. Se revisó
`bipv_python/pages/9_🗺️_Vista_3D.py` y no hay ningún archivo complementario de
puntos para este caso en `references/` ni `attached_assets/` (a diferencia de
East2, que sí publica su Tabla 4 con máscara angular — ver
`references/east2-mascara-angular.json`). Siguiendo el orden de prioridad exigido
(puntos reales del archivo → puntos del usuario → puntos de otra herramienta
demostrablemente correspondientes → bloqueo), se llega directo a la opción 4:
**el ray-casting de fachada no puede ejecutarse con validez física para este caso.**

## 4. Método matemático usado (documentado, sin cambios)

El flujo físico multi-superficie (`calculos/transicion_multisuperficie.py`,
`calculos/vinculador_sombra_multisuperficie.py`) aplica el sombreado geométrico
como:

```
G_eff = G_poa × (1 − p_shade)
```

donde `p_shade` es la fracción de bloqueo geométrico del haz directo calculada por
`calculos.sombras_3d.calcular_fs_horario_por_superficie()` mediante ray-casting
contra una malla `trimesh`. **La componente difusa NO se separa mediante Sky View
Factor (SVF) en este flujo** — el mismo factor `(1 − p_shade)` calculado desde el
haz directo se aplica a la irradiancia total en el plano (POA), que incluye directa
y difusa. Esto es una simplificación documentada, no un error: separar la difusa
requeriría un modelo de SVF por punto (p.ej. integración del hemisferio visible),
que no está implementado. **No se corrige en esta tarea** — no se encontró un
error concreto que lo justifique, solo una simplificación conocida y ya
documentada en la auditoría previa
(`references/auditoria-integracion-sitedesigner-marsh-sombras-lasalle-epw-real.md`).

En esta ejecución específica, `p_shade = 0` en las 4 superficies
(`estado_sombra = sombra_cero_calculada`, nunca `calculado_completo`) porque no
hay máscara angular publicada por la tesis ni escena real disponible — no porque
el edificio no tenga sombra real. Esto está declarado explícitamente, no oculto.

## 5. Resultados APP sin Site Designer (EPW real, reproducidos en esta ronda)

Ejecución directa de `construir_y_recalcular_proyecto_fisico()` con el EPW real
(`references/bogota-eldorado-iwec.epw`, SHA-256 verificado exacto contra el
declarado: `b9d837ed...` — ver §Verificación de fuente). Metadato leído del EPW:
lat=4.70, lon=-74.13, altitud=2548 m, TZ=-5.0 fijo, 8760 registros, índice
1993-01-01 a 1996-12-31 (TMYx típico, meses representativos de años distintos).
Sin desplazamiento de huso horario detectado.

| Superficie | tilt/az | P_dc,stc (kWp) | POA anual (kWh/m²) | E_dc anual (kWh) | E_ac anual (kWh) | Rend. esp. (kWh/kWp) | PR |
|---|---|---:|---:|---:|---:|---:|---:|
| Horizontal | 0°/180° | 28,004 | 1.613,31 | 42.995,8 | 42.393,9 | 1.513,85 | 0,9384 |
| Óptimo 10° sur | 10°/180° | 28,004 | 1.613,66 | 42.995,3 | 42.393,4 | 1.513,83 | 0,9381 |
| Fachada suroeste | 90°/249° | 28,004 | 831,25 | 22.051,9 | 21.743,1 | 776,43 | 0,9340 |
| Fachada sureste | 90°/162° | 28,004 | 831,73 | 22.075,3 | 21.766,3 | 777,26 | 0,9345 |

**Diferencia relativa SO/SE: 0,0577%** — prácticamente empatadas, con **sureste
ligeramente por encima de suroeste** (dirección opuesta a la app estándar de referencia). Reproducido dos
veces con el mismo fixture: `E_ac` idéntico cifra por cifra en ambas corridas
(determinismo, ver §10).

## 6. Resultados APP con Site Designer real

**No disponibles — experimento bloqueado (§1-§3).** No se ejecutó ray-casting con
geometría del edificio real porque no existe una escena válida.

## 7. Resultados de la app estándar de referencia (publicados por la tesis, Fig. 23 y Tabla 23)

| Superficie | POA de la app estándar de referencia (kWh/m²/año) | Rend. esp. de la app estándar de referencia (kWh/kWp/año) |
|---|---:|---:|
| Horizontal / referencia 10° sur | 1.571,3 | 1.393,42 |
| Fachada suroeste | 858,0 | 718,33* |
| Fachada sureste | 777,3 | 718,33* |

*la app estándar de referencia solo publica un rendimiento específico agregado del sistema de fachadas
(Tabla 21, no desglosado por fachada individual) — se usa como referencia conjunta
para el residual de fachadas en §9, no como valor por-fachada.

**Asimetría SO/SE de la app estándar de referencia:** (858,0 − 777,3) / 858,0 = **9,40%**, con suroeste >
sureste.

## 8. Diferencias porcentuales (APP sin Site Designer vs. la app estándar de referencia)

| Magnitud | APP sin escena | La app estándar de referencia | Diferencia absoluta | Diferencia % |
|---|---:|---:|---:|---:|
| POA Horizontal (kWh/m²) | 1.613,31 | 1.571,3 | +42,01 | **+2,67%** |
| POA Fachada-Suroeste (kWh/m²) | 831,25 | 858,0 | −26,75 | **−3,12%** |
| POA Fachada-Sureste (kWh/m²) | 831,73 | 777,3 | +54,43 | **+7,00%** |
| Asimetría SO/SE | 0,058% (SE>SO) | 9,40% (SO>SE) | — | signo invertido |
| Rendimiento normalizado, referencia | 1.474,1** | 1.393,42 | +80,68 | **+5,79%** |
| Rendimiento normalizado, fachadas (prom.) | 763,98** | 718,33 | +45,65 | **+6,35%** |

**Rendimiento normalizado por recurso: rendimiento específico de la app dividido
por su exceso de POA frente a la app estándar de referencia (misma metodología del bloque D del test),
usando el EPW real en vez del TMY sintético.

## 9. Cambio de asimetría SO/SE al incorporar geometría real

**No se puede evaluar** — es exactamente la pregunta bloqueada. Lo que SÍ se puede
documentar, con datos ya generados en rondas anteriores de esta sesión (mismo
motor, mismas coordenadas, solo cambia la fuente de recurso solar), es la
sensibilidad de esa asimetría a la fuente meteorológica/modelo de transposición,
sin tocar geometría en ninguno de los cuatro casos (las 4 superficies usan el
mismo `p_shade=0`, mismo panel, mismo inversor):

| Fuente meteorológica | Asimetría SO/SE | Signo |
|---|---:|---|
| Clear-sky sintético (Ineichen, pvlib, sin nubosidad) | ≈28% | SO > SE |
| PVGIS histórico (TMY real descargado en sesión previa con red) | ≈13,6% | SO > SE |
| **EPW real El Dorado (esta ronda, reproducido)** | **0,058%** | SE > SO (empate) |
| La app estándar de referencia (publicado por la tesis) | 9,40% | SO > SE |

La asimetría cambia en **más de dos órdenes de magnitud** (28% → 0,058%) solo por
cambiar la base meteorológica, sin tocar geometría, panel, inversor ni ningún otro
parámetro del motor. Esto ya demuestra que el modelo de transposición y la
correlación GHI/DNI/DHI de la fuente meteorológica dominan la magnitud (y en el
caso EPW real, incluso el signo) de la asimetría SO/SE — pero **no descarta** que
la geometría/sombra real del edificio también contribuya; solo confirma que no es
la única variable en juego, y que su peso relativo frente a la meteorología no se
puede aislar sin la escena real.

## 10. Evidencia de determinismo

Reproducido en esta ronda con el EPW real (no un test nuevo, verificación directa
del pipeline): dos corridas independientes de
`construir_y_recalcular_proyecto_fisico()` con el mismo `session_state`/TMY EPW
real producen `E_ac_anual_kWh` idéntico cifra por cifra:

```
Horizontal        determinista: True  42393.9
Fachada-Suroeste  determinista: True  21743.1
Fachada-Sureste   determinista: True  21766.3
```

(El test automatizado `test_escenario_lasalle_es_determinista` ya cubre esto con
el TMY sintético; esta ronda extiende la verificación al EPW real directamente,
sin agregar un test nuevo por no requerir cambio de código.)

## 11. Evidencia de invalidación por cambio de escena

Ya demostrada y **APROBADA** en la revisión inmediatamente anterior de esta misma
sesión (`references/revision-parche-invalidacion-malla-sitedesigner.md`,
web: la publicada en esa ronda). Resumen de lo ya verificado, no repetido aquí:
`cargar_escena_sitedesigner()` produce `malla_fingerprint` dependiente de bloques
y `northOffset`; en esta ronda se verificó además que lat/lon distintos también
cambian la huella (no estaba explícitamente probado antes):

```
lat distinta -> huella distinta: True
lon distinta -> huella distinta: True
```

`invalidar_sombra_por_cambio_malla()` invalida `p_shade` cuando la escena cambia,
conserva la sombra cuando la escena es idéntica, y no toca La Salle/East2 (que no
usan Site Designer). `construir_y_recalcular_proyecto_fisico()` rechaza con
`ValueError` explícito la construcción del proyecto si una superficie activa queda
sin `p_shade`/`firma_sombra` tras la invalidación — nunca usa sombra obsoleta en
silencio.

## 12. Hallazgos críticos

Ninguno nuevo en esta ronda.

## 13. Hallazgos importantes

1. **No existe una escena Site Designer real de Bosques de Castilla en el
   repositorio.** Es el hallazgo central de esta ronda — bloquea la pregunta
   original. No es un defecto de código, es una brecha de datos de entrada.
2. **La asimetría SO/SE es extremadamente sensible a la fuente meteorológica**
   (28% → 13,6% → 0,058%, incluso cambio de signo con el EPW real), lo que hace
   que comparar el 9,40% de la app estándar de referencia contra cualquiera de estas corridas sea una
   comparación entre bases de recurso solar distintas, no solo entre geometrías
   distintas. Esto ya estaba documentado antes de esta ronda; se reconfirma aquí.

## 14. Limitaciones que permanecen

- Sin escena Site Designer real de Bosques de Castilla → sin ray-casting de
  fachada con validez física → la contribución de la sombra real del entorno
  (edificios vecinos, autosombreado de la propia torre) a la asimetría SO/SE
  **sigue sin poder medirse**.
- Sin máscara angular horaria publicada por la tesis (a diferencia de East2) → no
  hay ningún dato de sombra real contra el cual comparar, publicado o no.
- Reparto real de los 148 módulos entre fachadas no publicado (la reconstrucción
  usa 70+70=140 como supuesto propio, ya documentado y verificado como
  discrepancia explícita en `test_conteo_modulos_app_difiere_del_publicado_en_la_tesis`).
- Base meteorológica de la app estándar de referencia no declarada por el documento (Meteonorm u otra) —
  ninguna de las 4 fuentes de esta tabla (clear-sky, PVGIS, EPW real, la app estándar de referencia) es
  necesariamente la misma que usó la app estándar de referencia.
- La difusa no se separa mediante SVF en el flujo multisuperficie (§4) — esto
  afecta por igual a ambas fachadas (mismo tratamiento), así que no explica por sí
  solo una asimetría, pero es una simplificación real del motor que no se ha
  cuantificado su efecto en fachadas verticales con mucha componente difusa.

## 15. Clasificación

**D — La escena no puede validarse: faltan geometría o puntos legítimos.** El
resultado queda como experimento bloqueado, no como conclusión física, para la
pregunta específica de si la geometría real cierra la brecha SO/SE.

(No se puede clasificar en A/B/C porque esas tres categorías presuponen que sí se
ejecutó el experimento con una escena real — ninguna corrió en esta ronda.)

## 16. Veredicto

**"Experimento bloqueado por falta de datos."**

No se puede declarar "limitación de entrada confirmada" ni "posible defecto de la
APP" para la pregunta específica de la asimetría SO/SE, porque falta el único dato
que permitiría distinguir entre ambas: una escena real de Bosques de Castilla con
sus obstrucciones y, sobre ella, puntos de análisis por fachada demostrablemente
correspondientes al reparto real de módulos. Lo que SÍ queda establecido con
evidencia reproducible (§9) es que la meteorología/transposición por sí sola ya
produce una dispersión de más de dos órdenes de magnitud en la asimetría — así que
cualquier futura comparación de asimetría con una escena real deberá normalizar
primero por fuente meteorológica antes de atribuir la diferencia restante a
geometría, o el resultado seguirá siendo ambiguo.

## 17. Archivos modificados

Ninguno de código. Nuevo: esta copia Markdown.

## 18. Pruebas ejecutadas

```
cd bipv_python
.venv/bin/python -m pytest \
  tests/test_sitedesigner_marsh.py \
  tests/test_sombras_por_superficie.py \
  tests/test_vinculador_sombra_multisuperficie.py \
  tests/test_flujo_fisico_multisuperficie_end_to_end.py \
  tests/test_pagina_transicion_multisuperficie.py -q
```
Resultado: **66 passed, 16 warnings in 3.09s** (warnings: QCRad + `scipy.optimize._chandrupatla`, ya conocidos, ninguno nuevo).

```
.venv/bin/python -m pytest \
  tests/test_escenario_validacion_bapv_lasalle_bosques_castilla.py \
  tests/test_escenario_validacion_east2_sunpower.py -q
```
Resultado: **29 passed, 95 warnings in 14.35s** (mismos dos orígenes de warning).

## 19. Diff completo

Ninguno — no se modificó código en esta ronda. No hubo ningún defecto concreto que
lo justificara (§12-§13); el hallazgo central es una brecha de datos de entrada,
no un error corregible en `calculos/`.

## 20. Instrucciones concretas para desbloquear el experimento

Para poder responder la pregunta original con evidencia física real, se necesita:

1. Abrir Site Designer (`drajmarsh.bitbucket.io/site-designer/`).
2. Ubicar el proyecto en **lat=4.634, lon=-74.148** (coordenadas leídas de las
   Fig. 6/7 de la tesis, confirmadas contra la altitud PVGIS en la validación
   anterior).
3. Modelar la Torre 5 del conjunto Bosques de Castilla y las obstrucciones
   relevantes del entorno (edificios vecinos, la propia geometría de la torre que
   pueda autosombrear sus fachadas suroeste/sureste).
4. Verificar la orientación norte (`northOffset`) contra las brújulas fotografiadas
   en las Fig. 6/7 del documento de la tesis — no asumir 0°.
5. Exportar con **File → Save Model File**.
6. Entregar el JSON original sin editar, junto con los puntos de análisis por
   fachada (posición real o al menos representativa de cada fila/columna de
   módulos en cada una de las dos fachadas) — sin esos puntos, aun con la escena
   correcta, el ray-casting seguiría sin poder ejecutarse con validez física
   (§3).

## 21. Publicación

Informe Markdown local: este archivo
(`references/experimento-bloqueado-geometria-real-lasalle-site-designer.md`).
Informe publicado en web temporal: ver enlace entregado en la respuesta de chat
que acompaña esta ronda.

---

### Verificación de fuente (EPW)

```
$ sha256sum references/bogota-eldorado-iwec.epw
b9d837ed551edbd86c6070e550e394465d27f53573d65eda455de81a13277e58  references/bogota-eldorado-iwec.epw
```

Coincide exacto con el SHA-256 declarado. Lectura vía
`pvlib.iotools.epw.read_epw()`, sin desplazamiento de zona horaria (índice
UTC-05:00 fijo, coherente con el metadato TZ=-5.0 del propio archivo).
