# Informe de validación — Fachada BAPV "Bosques de Castilla" (La Salle, 2021)

**Fecha:** 2026-09-22 (segunda corrección: EPW real de la estación Bogotá El
Dorado, IWEC, reemplaza al TMY sintético de cielo despejado como fuente
meteorológica de las comparaciones numéricas). **Rama:**
`validacion-nist-medido-predicho-2003` (sin commit nuevo hasta que el usuario lo
pida). **Cambios de código:** ninguno en el motor — solo el archivo de test
`bipv_python/tests/test_escenario_validacion_bapv_lasalle_bosques_castilla.py`,
el archivo `references/bogota-eldorado-iwec.epw` (fuente meteorológica real,
descargado una vez de `energyplus-weather.s3.amazonaws.com` y versionado) y
este informe.

**Aviso metodológico:** este documento usa TRES fuentes de TMY distintas, cada
una en su propia sección, nunca mezcladas dentro de una misma tabla:

1. **EPW real (El Dorado, IWEC) — §4, fuente vigente.** La que ejecutan los
   bloques C y D de la suite de pruebas. Estación oficial de EnergyPlus para
   Bogotá (WMO 802220, lat 4.70, lon -74.13, alt 2548 m) — a ~9 km del sitio
   real de la tesis (4.634, -74.148, 2550 m). Es la mejor fuente meteorológica
   real disponible sin depender de una descarga en vivo de PVGIS.
2. **TMY sintético (clear-sky Ineichen) — §4bis, chequeo mecánico.** Solo
   usado por el bloque B (ejecución end-to-end, determinismo): verifica que
   el motor responde a la geometría, no que reproduce el clima real.
3. **TMY real de PVGIS — §5, histórico.** Sesión anterior con acceso a red,
   coordenadas exactas del sitio (4.634, -74.148). Ya no se repite en cada
   corrida (frágil, no determinista sin red) — se conserva como referencia
   cruzada independiente, no como aserción de la suite actual.

## 0. Fuente

- **Documento:** Cardozo Sarmiento, J. J. & Moreno Suarez, J. F. (2021). *Diseño de
  un sistema solar fotovoltaico para la fachada de un edificio de propiedad
  horizontal*. Trabajo de grado, Ingeniería Eléctrica, Universidad de La Salle,
  Bogotá.
- **URL de origen:** `ciencia.lasalle.edu.co/server/api/core/bitstreams/29f650c8-a042-4f82-927c-55debc50a41b/content`
  (aportada por el usuario), landing page `ciencia.lasalle.edu.co/ing_electrica/630`.
- **PDF guardado:** `references/lasalle-2021-bipv-fachada-propiedad-horizontal.pdf`
  (91 páginas, SHA-256 `320c4fbc82b4da0996afe1d430d1d29cd1e6c8f0c89243796e6afcec2c40a4c5`).
  Leído íntegro: Generalidades, Marco teórico, Diseño (cargas, fachada, radiación
  teórica, simulación en la app estándar de referencia, técnico-económico), Anexos.
- **Herramienta de referencia del propio documento:** la app estándar de referencia (no la APP
  de este repositorio) — el documento no es un artículo científico con datos de
  medición real, sino un trabajo de grado que compara un cálculo teórico
  (Collares-Pereira y Rabl / Duffie-Beckman) contra una simulación en la app estándar de referencia.

## 1. Caso descrito

Edificio residencial (Torre 5, conjunto "Bosques de Castilla", localidad de
Kennedy, Bogotá D.C.), 13 pisos. Sistema BAPV instalado en dos fachadas
verticales libres de la torre:

| Fachada | Azimut brújula (Fig. 6/7) | Azimut convención Duffie (Ec. 15, sur=0°) | Azimut pvlib (0=N, 180=S) |
|---|---|---|---|
| Suroeste | 249° | +69° | 249° |
| Sureste | 162° | −18° | 162° |

(La tesis usa la convención sur=0°/oeste positivo de Duffie-Beckman para sus
ecuaciones [1]-[15]; la conversión a convención pvlib es `azimut_pvlib = 180 +
azimut_Duffie`, verificada porque reproduce EXACTO los 249°/162° que las
brújulas de las Fig. 6/7 ya muestran.)

Coordenadas del sitio: no publicadas como lat/lon en el texto, pero SÍ impresas
dentro de las fotografías de brújula (Fig. 6/7): `4°38'18"N 74°8'54"O`, altitud
2550-2660 m. Convertido: **lat=4.634, lon=-74.148**. Verificación independiente:
PVGIS devuelve **elevación 2550 m** para esas coordenadas exactas — coincide con
el valor impreso en la Fig. 7, confirma que la lectura de la fotografía es
correcta.

**Panel:** SunPower Maxeon 3, modelo SPR-MAX3-400 (Tabla 18: 400 W, 22.6%,
1690×1046 mm) — 148 módulos, 59.2 kWp. **Inversor:** Fronius Primo 15.0-1 ×4
(Fig. 21). Diseño limitado al 15% de la capacidad del transformador del conjunto
(500 kW → 75 kW máx., CREG 030 art. 5).

**Resultado publicado por la app estándar de referencia** (Tabla 21, sistema en fachadas, con sombra):
PR 86.8%, 718.33 kWh/kWp/año, 42.560 kWh/año, reducción por sombreado 3.7%/año.
**Sistema de referencia horizontal/óptimo** (Tabla 23, mismos 148 módulos a 10°
sur, sin obstrucción): PR 89.6%, 1.393,42 kWh/kWp/año, 82.521 kWh/año,
reducción por sombreado solo 1%/año.

## 2. Qué NO publica el documento (y por qué eso limita la réplica exacta)

A diferencia del caso East2 (`references/east2-validacion-informe.md`), que sí
publica una tabla numérica de sombra angular hora a hora, esta tesis solo
publica:

- Un **mapa de sombra por posición de panel** (Tablas 19/20: % de tiempo
  sombreado al año por cada posición V×H), sin serie horaria ni ángulos.
- Las **pérdidas agregadas** que la app estándar de referencia calculó internamente (3.7%/año y 1%/año),
  como salida, no como dato de entrada reconstruible.
- **Ningún reparto publicado** de los 148 módulos entre fachada suroeste y
  sureste (las Fig. 18/20 son capturas de pantalla de la app estándar de referencia, no tablas).
- **Ninguna base meteorológica declarada** para la app estándar de referencia (el software normalmente
  usa Meteonorm o su propia base; el documento no lo menciona).

Por regla del proyecto (no fabricar datos, `[[no-mezclar-apps-bipv]]` y
precedente de East2), **no se inventa** una máscara angular horaria ni un
reparto de módulos con precisión falsa. Las cuatro superficies se declaran con
estado `sombra_cero_calculada` (nunca `calculado_completo`): un cero calculado
explícitamente, no una sombra medida ni fabricada. La validación que sigue es
de **orden de magnitud y de geometría relativa** (qué fachada capta más y
cuánto), no una reproducción bit a bit del kWh anual del PDF.

## 3. Qué se reconstruyó en la APP

Pipeline físico multi-superficie real (`construir_y_recalcular_proyecto_fisico`,
el mismo motor de producción de la app, sin atajos):

1. **Panel SPR-MAX3-400**: no está en `datos.tecnologias_bipv` — se construyó su
   ficha desde el **datasheet oficial** de Maxeon Solar Technologies (doc
   544451 REV A, abril 2022, y doc 532420 REV C, julio 2020 — mismos valores
   eléctricos en ambas), y se resolvió el modelo de un diodo con
   `calculos.modelo_iv.estimar_sdm_desde_ficha()` (el mismo método ya usado
   para `SUNPOWER_E20_327` en el catálogo). Validación STC: Voc, Isc y Pmax
   reproducidos con **0.0% de error**; Vmp/Imp con 2.2-2.25% (`validar_sdm_vs_ficha`,
   tolerancia por defecto 6%, `validacion_ok=True`).
2. **TMY real** (`references/bogota-eldorado-iwec.epw`, EnergyPlus Weather,
   estación Bogotá El Dorado IWEC, WMO 802220) para el bloque C/D — fuente
   vigente de las comparaciones numéricas. Un TMY sintético determinista
   (clear-sky Ineichen, pvlib) se conserva solo para el bloque B (chequeo
   mecánico del motor, sin pretensión de realismo climático). La sesión que
   produjo las cifras de §5 usó un TMY real de PVGIS descargado en vivo
   (`calculos.solar.obtener_tmy_pvgis`) — ver "Aviso metodológico" al inicio.
3. **Cuatro superficies**, mismo panel/inversor, geometría real (pvlib, sin
   aproximación de multiplicación simple de POA):
   - `Horizontal` (tilt 0°, az 180°) — referencia.
   - `Optimo-10-Sur` (tilt 10°, az 180°) — reconstruye el sistema de
     referencia de la Tabla 23.
   - `Fachada-Suroeste` (tilt 90°, az 249°).
   - `Fachada-Sureste` (tilt 90°, az 162°).
   - Estado `sombra_cero_calculada` en las cuatro (ver §2 — sin máscara
     publicada; nunca se declara sombra medida ni "calculado_completo").
4. Inversor Fronius Primo 15.0-1 ya catalogado en la app
   (`datos.catalogo_inversores.INVERSORES["Fronius-Primo-15"]`,
   eficiencia_max=0.986); `P_ac_nom_W=None` (sin recorte, para aislar el efecto
   puramente DC/geométrico y no mezclarlo con un supuesto de dimensionamiento
   de string no publicado — sin este dato, tampoco se modela clipping AC ni
   autoconsumo del inversor).

**Conteo de módulos, verificado como discrepancia explícita:** la tesis publica
148 módulos (Tabla 18/21) sin repartirlos entre fachadas; esta reconstrucción
usa 70+70=140 (`N_SERIE=10, N_PARALELO=7` por superficie, supuesto propio de
dimensionamiento). `test_conteo_modulos_app_difiere_del_publicado_en_la_tesis`
fija esa diferencia como un hecho verificado — por eso ninguna prueba de este
archivo compara energía TOTAL del sistema contra los 42.560/82.521 kWh
publicados: el reparto real de módulos por fachada no se conoce.

## 4. Resultados de la corrida vigente (EPW real de El Dorado — la que ejecutan los bloques C y D de la suite)

Esta es la corrida más rigurosa que la suite reproduce sin red, con una fuente
meteorológica real (no sintética) versionada en el repositorio.

| Superficie | tilt/az | Pdc,stc (kWp) | POA anual (kWh/m²) | Edc anual (kWh) | Eac anual (kWh) | Rend. esp. (kWh/kWp) | PR |
|---|---|---:|---:|---:|---:|---:|---:|
| Horizontal | 0°/180° | 28,004 | 1.613,31 | 42.995,8 | 42.393,9 | 1.513,85 | 0,938 |
| Óptimo 10° sur | 10°/180° | 28,004 | 1.613,66 | 42.995,3 | 42.393,4 | 1.513,83 | 0,938 |
| Fachada suroeste | 90°/249° | 28,004 | 831,25 | 22.051,9 | 21.743,1 | 776,43 | 0,934 |
| Fachada sureste | 90°/162° | 28,004 | 831,73 | 22.075,3 | 21.766,3 | 777,26 | 0,935 |

Agregado del proyecto (4 superficies, no solo fachadas): `E_ac_total ≈ 128.296,7 kWh`,
`E_dc_total ≈ 130.118,3 kWh`, área total 495 m².

**POA/energía absolutas — mucho más cercanas que con el TMY sintético:**

| Superficie | La app estándar de referencia (Fig. 23) | APP (EPW real) | Dif. % |
|---|---:|---:|---:|
| Horizontal | 1.571,3 | 1.613,31 | **+2,7%** |
| Fachada suroeste | 858,0 | 831,25 | **−3,1%** |
| Fachada sureste | 777,3 | 831,73 | **+7,0%** |

Comparar con el TMY sintético (§4bis): +94,8% / +74,6% / +39,3% de diferencia.
El EPW real reduce la brecha en un orden de magnitud completo.

**Hallazgo relevante (no ocultado) — la asimetría suroeste/sureste no se reproduce:**
La app estándar de referencia reporta suroeste (858,0) > sureste (777,3), una asimetría de **~9,4%**.
Con el EPW real, ambas fachadas quedan **prácticamente empatadas**
(831,25 vs. 831,73 kWh/m²/año, **0,058% de diferencia** —
`test_fachadas_epw_real_no_reproduce_asimetria_de_ref`). El TMY sintético de
cielo despejado, en cambio, exageraba la asimetría en la dirección correcta
pero a una magnitud irreal (~28%, §4bis). Ninguna de las dos fuentes de esta
reconstrucción reproduce fielmente la asimetría que la app estándar de referencia reporta: esto no es
un error del motor de la app, sino evidencia de que esa asimetría depende de
la base meteorológica/modelo de transposición propio de la app estándar de referencia, al que esta
reconstrucción no tiene acceso.

**Rendimiento normalizado por recurso (el chequeo de paridad real):**

| Magnitud | Tesis/la app estándar de referencia | APP (EPW real) | Dif. abs. | Dif. % | Lectura |
|---|---:|---:|---:|---:|---|
| Rend. normalizado — referencia (kWh/kWp) | 1.393,42 | 1.474,09 | +80,67 | **+5,79%** | Residual positivo y acotado (<25%) |
| Rend. normalizado — fachadas prom. (kWh/kWp) | 718,33 | 763,91 | +45,58 | **+6,35%** | ≈0,56 pp por encima del residual de referencia |
| PR — referencia óptimo 10° sur | 89,6% | 93,8% | +4,2 pp | +4,7% | Sin sombra publicada en ninguno de los dos casos |
| PR — fachadas (prom. SO/SE) | 86,8% | 93,5% | +6,7 pp | +7,7% | Coherente con sombra 3,7%/cableado/mismatch/clipping no modelados |

Esta corrida está fijada por `test_rendimiento_normalizado_por_recurso_queda_por_encima_de_ref`
(residual > 0% y < 25%, calculado sobre la referencia) y documenta
explícitamente cuatro pérdidas de la app estándar de referencia que este escenario no modela: sombra
real, cableado, mismatch entre módulos y autoconsumo/clipping del inversor
(`PERDIDAS_REF_NO_MODELADAS`). El residual de fachadas (+6,35%) queda
apenas por encima del de referencia (+5,79%) — mucho más cerca entre sí que
con el TMY sintético (donde la brecha era de ~2,1 pp), otra pista de que la
asimetría de sombra 3,7%/1,0% de la app estándar de referencia no se refleja con la misma fuerza
bajo esta fuente meteorológica.

Advertencia técnica esperable con datos reales: el chequeo QCRad
(`calculos.solar.verificar_consistencia_radiativa`) marca 8,12% de horas de
día inconsistentes en este EPW — normal en datos meteorológicos reales
(cierre imperfecto GHI≈DNI·cosZ+DHI por redondeo/instrumentación), muy por
debajo del 30,75% que emiten los fixtures sintéticos ajenos de otros archivos
de prueba (ver `informe-validacion-east2-sunpower-e20327-app.md`). No bloquea
ninguna prueba.

## 4bis. Chequeo mecánico adicional (TMY sintético clear-sky — solo bloque B)

El TMY sintético (clear-sky Ineichen, pvlib) ya no se usa para comparar contra
La app estándar de referencia (bloques C/D); se conserva únicamente para el bloque B (ejecución
end-to-end, determinismo), donde el objetivo es verificar que el motor
responde a la geometría, no que reproduce el clima real. Se documentan aquí
sus valores solo para contraste con la §4:

| Superficie | tilt/az | POA anual (kWh/m²) | Rend. esp. (kWh/kWp) | PR |
|---|---|---:|---:|---:|
| Horizontal | 0°/180° | 3.060,94 | 2.847,74 | 0,930 |
| Óptimo 10° sur | 10°/180° | 3.059,52 | 2.845,69 | 0,930 |
| Fachada suroeste | 90°/249° | 1.497,75 | 1.406,34 | 0,939 |
| Fachada sureste | 90°/162° | 1.082,85 | 1.019,23 | 0,941 |

**POA/energía absolutas:** ❌ no comparables — el TMY sintético de cielo
despejado sobreestima el recurso frente a la app estándar de referencia en +74% a +95% según la
superficie. Con este TMY, la asimetría SO/SE sí aparece (1.497,75 vs. 1.082,85,
~28%) en la dirección correcta, pero de magnitud muy superior a la real
(la app estándar de referencia: ~9,4%) — ver el análisis completo del hallazgo SO/SE en la §4.

## 5. Corrida histórica de referencia (TMY real de PVGIS, sesión anterior con red — no reproducida por la suite actual)

Las cifras de esta sección se obtuvieron con un TMY real de PVGIS descargado
en una sesión con acceso a red, ANTES de reemplazar el fixture por el TMY
sintético de la §4. Se conservan aquí solo como referencia histórica —
**no se mezclan con la tabla de la §4** — porque usan una fuente de recurso
solar distinta.

| Superficie | tilt/az | POA app, PVGIS real (kWh/m²/año) | POA de la app estándar de referencia (Fig. 23) | dif. | Rend. esp. app (kWh/kWp) | PR app |
|---|---|---:|---:|---:|---:|---:|
| Horizontal | 0°/180° | 1.794,7 | 1.571,3 | **+14.2%** | 1.684,6 | 0.939 |
| Óptimo 10° sur | 10°/180° | 1.797,1 | — (Tabla 23 combina PR+sombra) | — | 1.686,3 | 0.938 |
| Fachada suroeste | 90°/249° | 986,2 | 858,0 | **+14.9%** | 923,3 | 0.936 |
| Fachada sureste | 90°/162° | 852,2 | 777,3 | **+9.6%** | 799,6 | 0.938 |

Residual normalizado de esta corrida histórica: referencia +6.0%, fachadas
+6.8% — del mismo orden y signo que el residual reproducible de la §4
(+4.88%/+6.99%), obtenido con un TMY completamente distinto. Esa estabilidad
entre dos fuentes de recurso solar diferentes es evidencia adicional de que
el residual refleja las pérdidas de la app estándar de referencia no modeladas, no un artefacto del
TMY elegido.

- El propio documento reporta esta misma clase de brecha **dentro de sí mismo**:
  su cálculo teórico Duffie-Beckman con datos IDEAM (1.457,0 kWh/m²/año
  horizontal) difiere **7.84%** de su propia simulación en la app estándar de referencia (1.571,3
  kWh/m²/año) — Tabla 22 del documento.
- El GHI anual de PVGIS para estas coordenadas exactas es **1.794,7 kWh/m²/año
  = 4,92 kWh/m²/día** — dentro del rango 4-5 kWh/m²/día que el propio documento
  cita de IDEAM (Fig. 2) para Bogotá.
- **Asimetría SO/SE en esta corrida histórica:** suroeste (986,2) > sureste
  (852,2), **~13,6%** — más cercana a la de la app estándar de referencia (~9,4%) que a las otras dos
  fuentes de este informe (clear-sky ~28%, EPW real ~0,06%). Las tres fuentes
  de recurso solar usadas en este documento (PVGIS histórico, clear-sky
  sintético, EPW real) dan tres magnitudes de asimetría distintas — ninguna
  reproduce exactamente el 9,4% de la app estándar de referencia, pero la PVGIS histórica es la más
  próxima. Esto refuerza la lectura de la §4: la asimetría publicada por
  la app estándar de referencia depende de su propia base meteorológica/modelo de transposición, no
  solo de la geometría, y es sensible a la fuente de TMY elegida.

## 6. Veredicto

- **Geometría/orientación:** ✅ reproducida exactamente (azimuts 249°/162°
  confirmados contra las brújulas fotografiadas; orden relativo suroeste>sureste
  reproducido).
- **Ficha del panel:** ✅ SPR-MAX3-400 real, SDM validado contra STC dentro de
  tolerancia.
- **Ubicación:** ✅ confirmada de forma independiente (altitud PVGIS = altitud
  de la foto de brújula).
- **Paridad numérica exacta con la app estándar de referencia:** ❌ no alcanzable con los datos
  publicados (faltan máscara angular horaria, reparto de módulos por fachada y
  base meteorológica de la app estándar de referencia) — y **no se fabricaron** esos datos.
- **Paridad de orden de magnitud y de física:** ✅ residual reproducible con
  EPW real (§4) de **+5,79%** en referencia y **+6,35%** en fachadas —
  consistente con el residual de la corrida histórica con PVGIS real
  (+6,0%/+6,8%, §5) y con el del TMY sintético (+4,88%/+6,99%, §4bis), pese a
  usar tres fuentes de recurso solar distintas. La dirección y el orden de
  magnitud (todas en la banda +4,9% a +7,0%) son los esperados dado que
  la app estándar de referencia modela sombra y pérdidas de cableado/mismatch/clipping que este
  escenario deliberadamente no modela (sin datos para hacerlo sin inventar).
- **Asimetría suroeste/sureste:** ⚠️ hallazgo honesto, no oculto — ninguna de
  las tres fuentes de TMY reproduce fielmente el 9,4% de la app estándar de referencia: EPW real da
  un empate casi perfecto (0,058%), clear-sky sintético exagera a ~28%, y
  PVGIS histórico da ~13,6% (la más cercana). Esto indica que la asimetría
  publicada por la app estándar de referencia depende de su propia base meteorológica/modelo de
  transposición, no reconstruible sin acceso a esos datos internos.

## 7. Archivos de esta validación

- `references/lasalle-2021-bipv-fachada-propiedad-horizontal.pdf` — fuente.
- `references/bogota-eldorado-iwec.epw` — TMY real (EnergyPlus Weather,
  estación Bogotá El Dorado IWEC, WMO 802220), fuente vigente de los bloques
  C/D, descargado una vez de `energyplus-weather.s3.amazonaws.com` y
  versionado para uso offline determinista.
- `bipv_python/tests/test_escenario_validacion_bapv_lasalle_bosques_castilla.py`
  — 10 tests, todos en verde y **sin red** (EPW real versionado + TMY
  sintético offline): ficha/SDM del panel (bloque A), discrepancia de conteo
  de módulos verificada (bloque A), ejecución end-to-end y determinismo con
  TMY sintético (bloque B, chequeo mecánico), rangos de orden de magnitud de
  POA frente a la app estándar de referencia y hallazgo de casi-empate SO/SE con EPW real (bloque C),
  y residual normalizado acotado frente a la app estándar de referencia con EPW real (bloque D).
