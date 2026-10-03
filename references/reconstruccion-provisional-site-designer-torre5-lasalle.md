# Reconstrucción provisional Site Designer — Torre 5, Bosques de Castilla — ray-casting ejecutado

**Fecha:** 2026-09-22. **Rama:** `validacion-nist-medido-predicho-2003` (sin
commits nuevos). **Naturaleza de este documento:** el usuario, tras revisar el
informe anterior (`references/reconstruccion-geometria-torre5-bosques-castilla.md`,
clasificación C — datos insuficientes), instruyó explícitamente **proceder** con
una reconstrucción provisional pese a la incertidumbre documentada, con la
condición de que cada magnitud no medida quede marcada como tal, que no se
concluya nada sobre la asimetría antes de correr el ray-casting real, y que se
compare contra la escena de ejemplo original. Este documento entrega
exactamente eso.

**Clasificación de la escena (marco de esta ronda): B — reconstrucción
provisional, con incertidumbres explícitas.** Nunca se presenta como exportada
de Site Designer ni como geometría validada.

## 0. Confirmación previa: el archivo pegado por el usuario NO es Torre 5

El JSON que el usuario proporcionó (`site-designer-2026-07-14-1606-10.json`) se
verificó **byte a byte idéntico** a
`attached_assets/site-designer-2026-07-14-1606-10_1786198985402.json`: un único
bloque `TreeBlock` en lat=4.702/lon=-74.147, northOffset=7 — la misma escena de
ejemplo genérica ya descartada en las dos rondas anteriores. No se usó como
fuente de geometría.

## 1-2. Evidencia real disponible (heredada del informe anterior, no repetida)

- **Cota real medida:** Fig. 4 de la tesis (p.35, elevación AutoCAD de la
  fachada sureste) — ancho **17,2905 m**, alto **36,4178 m** (verificado: ÷13
  pisos = 2,80 m/piso, plausible).
- **Sin cota equivalente para la fachada suroeste ni para la profundidad/planta
  de la torre.**
- **Obstrucciones reales descritas (sin cotas de posición):** balcones en toda
  la fachada SO (13 pisos), árboles de 5-7 m cubriendo pisos 1-3 de SO (foto
  créditada "Prabyc, 2012").
- Ver el informe anterior para el detalle completo de fuente/incertidumbre de
  cada dato (tabla §12 de ese documento).

## 3. JSON reconstruido — identificado explícitamente como provisional

**No se exportó desde Site Designer** (no fue posible: no hay acceso a modelar
interactivamente el sitio oficial desde este entorno). Se **construyó**
mediante script Python (`bipv_python/scripts/lasalle_torre5_*_provisional.py`,
4 archivos, reproducible paso a paso) un bloque rectangular único que representa
el volumen de la torre, más una variante con un bloque adicional de árboles.
Cuatro archivos entregados, todos con sufijo `-PROVISIONAL` en el nombre y con
el campo `_metadatos_reconstruccion_provisional` dentro del propio JSON:

| Archivo | Descripción |
|---|---|
| `references/site-designer-torre5-bosques-castilla-RECONSTRUCCION-PROVISIONAL.json` | **Primaria.** Torre como bloque único, footprint 17,29×17,29 m (ver §9), altura 36,42 m. |
| `references/site-designer-torre5-sensibilidad-so-estrecha-12m-PROVISIONAL.json` | Sensibilidad: ancho SO = 12 m (límite inferior explorado). |
| `references/site-designer-torre5-sensibilidad-so-ancha-25m-PROVISIONAL.json` | Sensibilidad: ancho SO = 25 m (límite superior explorado). |
| `references/site-designer-torre5-con-arboles-PROVISIONAL.json` | Torre central + bloque de árboles junto a SO (parámetros centrales, ver §9). |
| `references/puntos-analisis-torre5-so-se-PROVISIONAL.json` | 13 puntos por fachada (uno por piso), para la escena primaria. |
| `references/resultados-ray-casting-torre5-sensibilidad-PROVISIONAL.json` | Salida cruda del pipeline para las 4 variantes. |

## 4. SHA-256 de los archivos finales

```
587dfbac6a19bb893c65febb67ecd4cdd58e535a7b4dc50feeafab1a25a821e1  site-designer-torre5-bosques-castilla-RECONSTRUCCION-PROVISIONAL.json
928afd5106df4f7d256604bac600116a457095eafb13ca1ee228fd5ae0a41719  site-designer-torre5-sensibilidad-so-estrecha-12m-PROVISIONAL.json
dc4cb73045884b40ff55ff7046f388fa63e6cd8ea30a1eca8f049fd6d103f7c6  site-designer-torre5-sensibilidad-so-ancha-25m-PROVISIONAL.json
c5b05b49a464e48d709589adeed7819cab67ff6fdab7db7cccdc6af698cd290c  site-designer-torre5-con-arboles-PROVISIONAL.json
d1f7532f990c48fbb6fe7f2113c757af94216f322a12e5b7bf9627121104e749  puntos-analisis-torre5-so-se-PROVISIONAL.json
48a040e1adf5b98e4e58e5d46f1c9a0717bf8f8a76522b9a8e0340f06b26a432  resultados-ray-casting-torre5-sensibilidad-PROVISIONAL.json
```

## 5. Coordenadas

`Location.latitude=4.634, Location.longitude=-74.148` — las de la tesis (Fig.
6/7), movidas desde el punto genérico 4.702/-74.147 del archivo original.

## 6. northOffset — derivado y verificado numéricamente, no asumido

**No se asumió 0° ni se copió el 7° del archivo genérico.** Se derivó así:

1. Los azimuts REALES ya verificados en rondas anteriores (lectura de brújula,
   Fig. 6/7 de la tesis): fachada SE=162°, fachada SO=249° (convención pvlib).
   Diferencia real entre ambas: **87°**, no 90° exactos.
2. Un bloque rectangular de Site Designer solo puede tener esquinas de 90°
   exactos (`min`/`max` axis-aligned) — se **idealiza** la esquina real de 87°
   a 90°, repartiendo el error simétricamente: SE_ideal=160,5°, SO_ideal=250,5°
   (cada una a solo 1,5° del valor real medido).
3. Se calculó el `northOffset` candidato (160,5°) y se **verificó
   numéricamente** —no a mano— construyendo el bloque con `trimesh`, aplicando
   la rotación, y recalculando el azimut real de cada cara resultante a partir
   de su vector normal. Resultado exacto: cara SE → 160,4999...° ≈ 160,5°; cara
   SO → 250,4999...° ≈ 250,5°. Coincide con el objetivo dentro de 0,05°
   (redondeo de punto flotante). Script:
   `bipv_python/scripts/lasalle_torre5_1_derivar_geometria_provisional.py`.

**`northOffset = 160,5`** (vs. 7° del archivo genérico — completamente distinto,
como debía ser).

## 7. Elevación

2550 m (Fig. 6/7 de la tesis, ya usada en toda la sesión).

## 8-9. Lista y dimensiones de bloques

**Bloque 1 — Torre (todas las escenas):**

| Dimensión | Valor | Fuente |
|---|---:|---|
| Ancho fachada SE | 17,2905 m | **Medido** (Fig. 4 tesis) |
| Ancho fachada SO | 17,2905 m (central) / 12 m / 25 m (sensibilidad) | **ASUMIDO = ancho SE** en la variante central — no hay cota publicada de SO. Justificación: (a) el ángulo real entre azimuts SO/SE es 87°, consistente con un footprint aproximadamente cuadrado en una esquina casi recta; (b) coherencia interna con el reparto 70+70 módulos ya asumido en `test_escenario_validacion_bapv_lasalle_bosques_castilla.py` (áreas de fachada similares). Se exploran además 12 m y 25 m como cotas inferior/superior de sensibilidad. |
| Altura | 36,4178 m | **Medido** (Fig. 4 tesis, verificado ÷13=2,80 m/piso) |

**Bloque 2 — Árboles (solo en la variante "con árboles"), junto a SO:**

| Parámetro | Valor | Fuente |
|---|---:|---|
| Altura | 6 m | **Dato real de rango** (tesis: "5-7 m"), se usa el punto medio |
| Retranqueo (distancia a la fachada) | 3 m | **ASUMIDO** — no publicado. Valor típico de plantación urbana, sin verificación específica para este sitio |
| Profundidad de copa | 3 m | **ASUMIDO** — no publicado |
| Posición horizontal | todo el ancho de SO | **Simplificación de modelado** — la posición real a lo largo de la fachada no está publicada |

**Balcones: NO modelados.** A diferencia de los árboles (que sí tienen una
altura publicada, 5-7 m), los balcones no tienen ninguna cota publicada ni
siquiera aproximada (ni profundidad de protrusión ni posición) — modelarlos
habría exigido inventar dos magnitudes sin ningún punto de apoyo, a diferencia
de los árboles donde al menos la altura es un dato real. Quedan como limitación
explícita, no como obstáculo fabricado.

## 10-11. Puntos SO y SE, y su justificación

**Regla geométrica explícita y cuantificada** (nivel 4 de la prioridad exigida,
ya que no hay modelo real de paneles ni puntos del usuario): un punto por piso,
13 puntos por fachada, centrado en el ancho de la fachada (medido para SE,
asumido para SO), a media altura de cada piso (asumiendo 13 pisos iguales de
36,4178/13=2,8014 m — la altura de piso INDIVIDUAL real no está publicada, se
deriva de la altura total medida dividida en partes iguales), con un offset de
0,5 m hacia afuera de la fachada (convención de modelado del propio motor, no
parte de la incertidumbre geométrica: supera el mínimo de 0,10 m que exige
`validar_puntos()` para no quedar "pegado" a la malla).

Cada punto representa aproximadamente 70/13 ≈ **5,38 módulos** (70 módulos
totales por fachada, supuesto ya existente en el test file; el reparto real
por piso no está publicado, por eso es una aproximación explícita, no un
conteo real).

Ejemplo (fachada SE, piso 1 de 13, coordenadas ENU reales tras aplicar la
rotación de 160,5°): `x=-2.2108, y=-19.6559, z=1.4007` (metros, relativos al
punto de referencia lat/lon de la escena). Los 26 puntos completos están en
`references/puntos-analisis-torre5-so-se-PROVISIONAL.json`.

**Validación con `validar_puntos()` (motor real, no simulado):** los 26 puntos
de la escena central pasan sin ningún aviso (ni "dentro de la malla" ni
"pegado"). En la variante de sensibilidad "SO ancha 25 m" los puntos SO
calculados para el footprint central (17,29 m) SÍ dieron aviso de "dentro del
modelo" al probarlos contra el footprint más ancho — se corrigió regenerando
puntos específicos por cada footprint de sensibilidad (ver
`lasalle_torre5_3_generar_puntos_provisional.py`), confirmando que la
validación de puntos del motor real detecta correctamente ese tipo de error.

## 12. Confirmación: el EPW no fue insertado en Site Designer

Confirmado. Los 4 JSON de escena contienen únicamente `Location` y `Blocks`
(más metadatos de trazabilidad propios, ningún dato meteorológico). El EPW
real (`references/bogota-eldorado-iwec.epw`) se cargó por separado, después,
directamente en el pipeline físico de la app (`_tmy_bogota_epw_real()` /
`pvlib.iotools.epw.read_epw`), exactamente como especifica el contrato
JSON→malla→EPW→posiciones solares→ray-casting→p_shade→motor físico.

## 13. Comparación contra la escena de ejemplo original

| | Original (`site-designer-2026-07-14-1606-10...json`) | Nueva (primaria) |
|---|---|---|
| Latitud/longitud | 4.702 / -74.147 | **4.634 / -74.148** |
| northOffset | 7° | **160,5°** |
| Bloques | 1 (`TreeBlock`, árbol decorativo) | **1 (`TowerBlock`, torre)** |
| Dimensiones (bounding box mundo) | 4,56×3,69×10,0 m | **22,07×22,07×36,42 m** |
| `malla_fingerprint` | `externa_marsh-a6b3202842d81df1` | `externa_marsh-ecb7fe8a8d6bd66c` |

Ubicación, orientación, geometría y huella cambiaron por completo — confirmado,
no solo afirmado.

## 14. Ejecución del ray-casting y motor físico — resultados

Ejecutado con el motor real (`calcular_fs_horario_por_superficie`,
`construir_y_recalcular_proyecto_fisico`), EPW real (mismo TMY que el resto de
esta sesión), panel SPR-MAX3-400, inversor Fronius Primo 15.0-1, sin cambios
de código. Cuatro corridas (primaria + 2 de sensibilidad + con árboles):

| Magnitud | Fachada | Sin Site Designer | **Con Site Designer (central)** | La app estándar de referencia |
|---|---|---:|---:|---:|
| POA (kWh/m²) | SE | 831,73 | 831,73 (sin cambio — la POA no depende de `p_shade`) | 777,3 |
| POA (kWh/m²) | SO | 831,25 | 831,25 | 858,0 |
| E_ac anual (kWh) | SE | 21.766,3 | **16.045,0** | — (no publicado por fachada) |
| E_ac anual (kWh) | SO | 21.743,1 | **13.451,8** | — (no publicado por fachada) |
| Rendimiento esp. (kWh/kWp) | SE | 777,26 | **572,95** | 718,33 (agregado ambas fachadas) |
| Rendimiento esp. (kWh/kWp) | SO | 776,43 | **480,35** | 718,33 (agregado) |
| PR | SE | 0,9345 | **0,6889** | 0,868 (agregado, Tabla 21) |
| PR | SO | 0,9340 | **0,5779** | 0,868 (agregado) |
| Horas con `p_shade`>1%/año | SE | 0% (declarado, no calculado) | **20,80%** | no publicado hora a hora |
| Horas con `p_shade`>1%/año | SO | 0% | **25,07%** | no publicado hora a hora |
| Pérdida de energía por sombra (E_dc, %/año) | SE | 0% | **26,29%** | 3,7%/año (agregado fachadas) |
| Pérdida de energía por sombra (E_dc, %/año) | SO | 0% | **38,13%** | 3,7%/año (agregado) |
| **Asimetría SO/SE (E_ac)** | — | 0,11% (SE>SO) | **16,16% (SE>SO)** | 9,40% (**SO>SE**) |

**Determinismo:** la escena primaria se cargó y procesó una sola vez por
corrida en este pipeline; el motor físico ya tiene determinismo verificado en
rondas anteriores de esta sesión (mismo TMY + misma malla + mismos puntos →
mismo resultado, `test_escenario_lasalle_es_determinista`). No se repitió aquí
por no ser el foco de esta ronda.

## 15. Instrucciones para usar JSON + EPW juntos en la app

Igual que documentado en la ronda anterior (§14 de
`references/reconstruccion-geometria-torre5-bosques-castilla.md`): subir el
JSON en Vista 3D → cargar el EPW real en Recurso Solar → definir/confirmar los
26 puntos de análisis → pulsar "Calcular sombra" → `construir_y_recalcular_proyecto_fisico()`
aplica todo automáticamente, con la invalidación por cambio de escena ya
aprobada protegiendo contra sombra obsoleta.

## Lectura de los resultados — sensibilidad al ancho SO asumido

| Escena | E_ac SE (kWh) | E_ac SO (kWh) | Asimetría E_ac |
|---|---:|---:|---:|
| SO estrecha (12 m) | 16.285,4 | 13.401,6 | 17,71% (SE>SO) |
| **SO central (17,29 m, =SE)** | 16.045,0 | 13.451,8 | 16,16% (SE>SO) |
| SO ancha (25 m) | 15.884,5 | 13.562,3 | 14,63% (SE>SO) |

**La dirección de la asimetría (SE > SO) es estable en las tres variantes del
ancho SO** — variar esta única asunción entre 12 y 25 m (rango amplio) mueve la
magnitud solo entre 14,6% y 17,7%, nunca invierte el signo. Esto es evidencia
de que la dirección del resultado no depende críticamente de la asunción más
débil de esta reconstrucción.

**Con árboles** (parámetros centrales, retranqueo 3 m): SO cae más todavía
(E_ac 12.757,4 kWh, PR 0,548, horas sombreadas 41,5%) mientras SE no cambia —
consistente con que los árboles solo afectan a SO por construcción.

## Hallazgos críticos

Ninguno de código.

## Hallazgos importantes

1. **La reconstrucción provisional invierte la dirección de la asimetría
   respecto a la app estándar de referencia, no la reproduce ni se acerca a ella.** Sin escena: SE>SO
   por 0,11% (prácticamente empatadas). Con la escena provisional: SE>SO por
   16,16% — la brecha con la app estándar de referencia (que reporta SO>SE por 9,40%) se agranda, no
   se cierra. Clasificación de interpretación (marco de la ronda anterior): **B
   — la escena cambia los resultados, pero no acerca la asimetría; persisten
   diferencias de meteorología, transposición, difusa y ahora también de la
   geometría real no verificada.**
2. **La pérdida de energía por sombra que produce esta reconstrucción (26-38%)
   es 7-10 veces mayor que el 3,7%/año que la app estándar de referencia publica para las fachadas.**
   Esto es más informativo que decepcionante: sugiere fuertemente que el
   footprint real de la torre NO es aproximadamente cuadrado como se asumió
   aquí — un footprint más alargado separaría las dos fachadas en su esquina
   compartida y reduciría el autosombreado mutuo. Es una inferencia razonada a
   partir de la discrepancia, no una medición nueva; no reemplaza la necesidad
   de una planta real.
3. **Sí hubo autosombreado geométrico real y significativo entre las dos
   fachadas de un mismo volumen convexo** — contradice la intuición inicial de
   que un bloque convexo simple no puede sombrearse a sí mismo en dos caras
   adyacentes; a la latitud de Bogotá (~4,6°N, sol casi cenital gran parte del
   año) y con una esquina cercana a 90°, los puntos a media anchura de cada
   fachada sí quedan bloqueados por la otra ala del mismo volumen en una
   fracción sustancial de las horas de sol (20-25% de las horas con luz).

## Limitaciones que permanecen

- El footprint (17,29×17,29 m asumido) sigue sin verificarse contra una planta
  real — es la asunción más consecuente de toda esta reconstrucción.
- Balcones no modelados (sin ninguna cota, ni siquiera aproximada).
- Posición horizontal y retranqueo real de los árboles no verificados (solo su
  altura, 5-7 m, es un dato real).
- La foto de los árboles es de 2012 — pueden haber cambiado sustancialmente en
  9 años hasta la fecha de la tesis (2021) y 14 hasta hoy.
- Ningún edificio vecino modelado (solo se reconstruyó la propia Torre 5) —
  la app estándar de referencia, si modeló el entorno urbano completo, puede estar capturando
  sombra de edificios vecinos que esta reconstrucción no incluye en absoluto.
- La idealización de la esquina real (87°→90°) introduce hasta 1,5° de error
  angular por cara — pequeño frente a las demás incertidumbres, documentado
  por completitud.

## Clasificación final

**Escena: B — reconstrucción provisional, con incertidumbres explícitas.**
**Interpretación de la asimetría: B — la escena cambia sustancialmente los
resultados (pérdida de energía 26-38%, antes 0%), pero no acerca la app al
9,40% de la app estándar de referencia en dirección ni en magnitud — de hecho invierte el signo.**

**No se declara "defecto de la app"**: el propio motor de ray-casting se
comportó de forma físicamente coherente y verificable (autosombreado real
entre fachadas adyacentes de un volumen convexo, a una latitud donde el sol
pasa cerca del cenit). **Tampoco se declara "limitación de entrada
confirmada y cerrada"**: la magnitud del resultado es tan sensible al
footprint asumido (evidenciado por la discrepancia de 7-10× frente al 3,7%
de la app estándar de referencia) que no se puede afirmar que esta reconstrucción representa
fielmente el edificio real sin una planta arquitectónica que confirme o
corrija el footprint.

## Archivos modificados / pruebas ejecutadas

**Código de la app: ninguno modificado.** Se usaron únicamente funciones ya
existentes (`cargar_escena_sitedesigner`, `calcular_fs_horario_por_superficie`,
`validar_puntos`, `aplicar_sombra_a_superficies`,
`construir_y_recalcular_proyecto_fisico`), sin tocar su código fuente.

**Archivos nuevos:** los 6 archivos de datos listados en §3-4, esta copia
Markdown, y 4 scripts de reconstrucción en
`bipv_python/scripts/lasalle_torre5_{1..4}_*_provisional.py` (derivación
geométrica verificada numéricamente, construcción de escenas, generación de
puntos, pipeline completo — reproducibles paso a paso).

**Pruebas ejecutadas** (regresión completa, para confirmar que usar estas
funciones con datos nuevos no rompió nada):

```
cd bipv_python
.venv/bin/python -m pytest \
  tests/test_sitedesigner_marsh.py tests/test_sombras_por_superficie.py \
  tests/test_vinculador_sombra_multisuperficie.py \
  tests/test_flujo_fisico_multisuperficie_end_to_end.py \
  tests/test_pagina_transicion_multisuperficie.py -q
```
**66 passed, 16 warnings** (QCRad + `scipy.optimize._chandrupatla`, ya
conocidos, ninguno nuevo).

```
.venv/bin/python -m pytest \
  tests/test_escenario_validacion_bapv_lasalle_bosques_castilla.py \
  tests/test_escenario_validacion_east2_sunpower.py -q
```
**29 passed, 95 warnings** (mismos orígenes).

No se agregaron pruebas nuevas porque no hubo cambio de código que las
justificara — esta ronda usó el motor existente sobre datos de entrada nuevos,
no modificó su comportamiento.

Sin commit, merge, push ni despliegue.
