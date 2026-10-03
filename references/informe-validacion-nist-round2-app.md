# Informe de validación — Candidato NIST Round 2 (BIPV vertical, Gaithersburg)

**Fecha:** 2026-09-22. **Rama:** `validacion-nist-round2` (nueva rama aislada, creada desde
`validacion-east2-sunpower-e20327`, sin commit, sin tocar `main`). **Commit/push/deploy:**
ninguno. **Cambios de código:** ninguno — ver veredicto (§4) sobre por qué no procede
implementación.

## 0. Fuente y verificación bibliográfica

- **Artículo:** *Measured Performance of Building Integrated Photovoltaic Panels—Round 2*.
  Dougherty, B. P.; Fanney, A. H.; Davis, M. W. *Journal of Solar Energy Engineering*
  (Trans. ASME), Vol. 127, pp. 314–323, agosto 2005.
- **DOI:** [10.1115/1.1883237](https://doi.org/10.1115/1.1883237) — confirmado impreso en el
  propio PDF ("DOI: 10.1115/1.1883237", pág. 314, final del abstract).
- **PDF descargado:** directamente del repositorio de publicaciones del NIST
  (`https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=860956`), fuente oficial del
  propio instituto autor, no un espejo ni una versión pirata. Guardado en
  `references/buildings-nist-round2.pdf`.
- **SHA-256 del PDF:** `35dcb3710e9db55cb29b7c29c6f78f37ad098d8dbb057971b4f9caf3995fed33`.
- **Extensión:** 10 páginas, leídas **íntegras** (no solo el abstract) — Introducción, Test
  Facility and BIPV Panel Descriptions, Data Measurements, Annual/Monthly/Daily Performance,
  Discussion and Conclusions, Acknowledgments, Appendix (Tabla 3 de incertidumbres), 14
  referencias.

## 1. Clasificación arquitectónica (verificación explícita pedida por el encargo)

**Confirmado: es un caso multi-panel en una única fachada vertical común, no un caso
multi-fachada.**

El propio artículo lo dice explícitamente: los ocho paneles están *"installed vertically,
face true south, and are an integral part of the building's shell"* (abstract, pág. 314) y la
Fig. 1 (pág. 315) los muestra dispuestos **lado a lado en una sola pared, una sola orientación,
un solo tilt** ("As Viewed from Outdoors" — estaciones A a J en fila). No hay ninguna mención
de tilt o azimut distintos entre paneles: la única variable geométrica que cambia entre
estaciones es la tecnología de celda, el material del frente (vidrio/ETFE/PVDF) y si el panel
está aislado por detrás — nunca la orientación.

**Consecuencia para la APP:** este caso NO debe forzarse dentro del contrato multi-superficie
(`transicion_multisuperficie.py`, que existe para superficies con **distinto** tilt/azimuth,
cada una con su propia sombra 3D). Si alguna vez se implementara, correspondería a **una sola
superficie física con 8 variantes de panel/configuración eléctrica**, no a un proyecto
multi-superficie. Esta conclusión se mantiene con independencia del hallazgo de §2 (bloqueo por
datos): incluso si los datos existieran, el contrato correcto sería de una sola superficie.

Esto separa correctamente esta conclusión de la validación geométrica multi-fachada de East2
(`references/informe-validacion-east2-sunpower-e20327-app.md`), que sigue siendo el caso que
valida tilt/azimuth por superficie y sombra 3D independiente — NIST Round 2 serviría, si los
datos lo permitieran, como benchmark eléctrico/térmico de una fachada, nunca como sustituto de
esa validación geométrica.

## 2. Fase 1 — Extracción bibliográfica (tabla completa)

| Campo | Valor | Unidad | Página/Tabla/Figura | Estado | ¿Representable en la APP? |
|---|---|---|---|---|---|
| Ubicación | NIST, 100 Bureau Drive, Gaithersburg, Maryland | — | Encabezado de autores, pág. 314 | Publicado (dirección) | Sí, como ciudad; sin coordenadas exactas del artículo |
| Coordenadas (lat/lon) | No se publican en el artículo | — | — | **Ausente** | No — cualquier lat/lon usado sería una fuente externa al artículo, debe marcarse como tal |
| Altitud | No se publica | m | — | **Ausente** | No |
| Orientación | Vertical, cara verdadero sur, para los 8 paneles | ° | Abstract pág. 314; Intro pág. 315; Fig. 1 pág. 315 | Publicado | Sí — tilt=90°, azimuth=180° (convención brújula) |
| Geometría de panel (dimensiones, bordes, recesos, % vidriado) | Ver Tabla 1 completa | mm / % | **Tabla 1**, pág. 316 | Publicado | Sí, para el cálculo geométrico de área activa; no para sombra 3D (ver §3) |
| Marca/modelo — panel 2-a-Si (E,F) | Módulos BP Solar, largo personalizado (donados a NIST) | — | Acknowledgments, pág. 323 | Publicado (marca), modelo específico no | Parcial |
| Marca/modelo — paneles A-D (mono-Si/poly-Si) | Celdas "del mismo lote y proveedor" del fabricante, sin nombrarlo | — | pág. 316 | **Ausente** (fabricante no identificado) | No |
| Marca/modelo — paneles CIS (G,H) | "Cuatro módulos disponibles comercialmente", fabricante no identificado | — | pág. 316 | **Ausente** | No |
| Pmax nominal — A (mono-Si) | 133 | W | Tabla 1, pág. 316 | Publicado | Parcial (sin Voc/Isc/Vmp/Imp, ver abajo) |
| Pmax nominal — B/C/D (poly-Si) | 143–155 (NIST) / 147–154 (fuente alternativa, flash test) | W | Tabla 1, pág. 316 | Publicado como **rango**, no valor único por panel | Parcial |
| Pmax nominal — E/F (2-a-Si, panel completo de 2 módulos) | 246.7 | W | Tabla 1, pág. 316, nota (c) | Publicado, **explícitamente no estabilizado** ("~100 h de exposición, no refleja desempeño estabilizado") | Parcial, con caveat fuerte |
| Pmax nominal — G/H (CIS, panel completo de 4 módulos) | 438.8 (NIST) / 440 (fabricante) | W | Tabla 1, pág. 316, nota (e) | Publicado | Parcial |
| Voc, Isc, Vmp, Imp (los 4 valores STC) — cualquier panel | **No se publican para ningún panel** | V/A | — | **Ausente** | **No** — bloqueo total para construir cualquier SDM |
| Coeficientes térmicos — 2-a-Si (únicos publicados) | Imp +0.0021 A/°C; Isc +0.0012 A/°C; Vmp −0.20 V/°C; Voc −0.30 V/°C | A/°C, V/°C | pág. 321–322 | Publicado, pero el propio artículo dice: *"cannot be directly compared to values typically reported in the literature... not normalized to standard rating conditions. No attempt at normalization is made here."* | **No** usable en un SDM sin normalizar a STC |
| Coeficientes térmicos — mono-Si, poly-Si, CIS | No se publican | — | — | **Ausente** | No |
| Área de celda / cobertura / apertura (por tecnología) | 1.020/1.160/1.682 (mono-Si); 1.134/1.168/1.682 (poly-Si); 1.487/1.487/1.682 (2-a-Si); 1.451/1.451/1.935 (CIS) | m² | Tabla 1, pág. 316 | Publicado | Sí |
| Número de módulos / config. eléctrica | A-D: 1 módulo, 72 celdas en serie c/u. E-F: 2 módulos en **paralelo**, 68 celdas en serie por módulo. G-H: 4 módulos en **paralelo**, 42 celdas en serie por módulo | — | Tabla 1 + texto, pág. 315–316 | Publicado a nivel de celdas/módulos, **no** como n_serie×n_paralelo de módulos en el sentido que usa la APP | Parcial — mapeo no directo, ver §3 |
| Inversor | **No existe.** Cada panel se conecta a un Raydec RD-2400S "multi-tracer" fotovoltaico que lo opera en su propio punto de máxima potencia; no hay etapa de inversión ni salida AC | — | pág. 316 | **No aplica** (no es un dato ausente — el sistema medido es puramente DC) | **No** — el escenario no tiene equivalente de `etapa_inversor_bus` |
| Aislamiento posterior / configuración constructiva | 6 de 8 paneles aislados con 100 mm de poliestireno extruido (A,B,C,D,F,H); 2 sin aislar, expuestos al aire interior (E,G) | mm | pág. 316–317, Fig. 1 | Publicado | Sí, como variable de comparación cualitativa (no como parámetro térmico numérico del SDM de la APP) |
| Fuente meteorológica, periodo, resolución | Pyranómetro espectral de precisión (PSP) propio en el plano vertical del panel + sensor ultrasónico de viento + termopares; periodo = año calendario 2002 completo; muestreo cada 15 s, promedios guardados cada 5 min | — | pág. 316 | Publicado (metodología) | **No** — la serie numérica NUNCA se publica como tabla/archivo |
| Irradiancia, temperatura, viento (series horarias/5-min) | Medidas pero **no publicadas como datos numéricos** — solo se muestran en gráficas ilustrativas de 2–3 días puntuales (Figs. 4–8) y como % agregados anuales/mensuales (Figs. 3, 9) | W/m², °C, m/s | Figs. 2–9 | **Ausente como serie utilizable** | **No** — no hay TMY ni serie horaria que alimentar a `calcular_poa` |
| Energía DC mensual/anual medida (kWh) | **No se publica en kWh** — se publica como **eficiencia de conversión** anual (%): A=10.1%, B=11.2%, C=12.2%, D=12.2%, E=4.6%, F=4.6%, G=10.2%, H=9.7% (base área de cobertura) | % | Fig. 3 (valores impresos en las barras) + texto pág. 317–318 | Publicado como %, no como energía absoluta | Parcial — no convertible a kWh sin una irradiancia total que el artículo no da |
| Energía AC | No aplica — no hay inversor | — | — | **No aplica** | No |
| Eficiencia mensual (serie de 12 meses) | Fig. 9: curvas mensuales de eficiencia (%) para las 8 configuraciones, ene–dic | % | Fig. 9, pág. 322 | Publicado (gráfica con ejes rotulados, valores extremos citados en texto) | Parcial — legible aproximadamente, no como tabla numérica exacta mes a mes |
| Diferencias porcentuales entre pares de paneles | Tabla 2: ETFE vs vidrio +8.4%(todo el día)/+7.8%(mediodía); PVDF vs vidrio +8.6%/+8.7%; PVDF vs ETFE +0.1%/+0.9%; efecto aislamiento 2-a-Si +0.1%/−0.3%; efecto aislamiento CIS −4.2%/−5.1% | % | **Tabla 2**, pág. 318 | Publicado | Sí, como métrica de comparación relativa (no absoluta) |
| PR (Performance Ratio) | No se reporta | — | — | **Ausente** | No |
| Pérdidas térmicas cuantificadas (kWh o %) | No se reporta como pérdida térmica aislada; solo temperaturas pico ilustrativas de días puntuales (ej. CIS aislado 51.5 °C vs no aislado 40.4 °C, 5-mayo-2002, T_amb 23.5 °C; ETFE pico 72.3 °C en enero vs 56.0 °C en junio) | °C | pág. 320, 322 | Publicado (ejemplos puntuales) | Parcial — solo como referencia cualitativa de días concretos |
| Métricas de error modelo-vs-medición (RMSE, MBE, nRMSE) | **No se reportan en este artículo** — el propio texto dice que la comparación modelo-vs-medición "está por venir" en trabajo futuro/round-robin con Sandia (pág. 323, "Discussion and Conclusions") | — | pág. 323 | **Ausente en este artículo** | No |
| Incertidumbres experimentales | Tabla 3 completa: potencia panel primaria 0.73%, secundaria 1.0%, voltaje 0.46%, corriente 0.81%, irradiancia solar 2.3%, eficiencia de conversión 2.5%, área de panel 0.31%, temperatura de panel 0.22 °C (k=2) | % / °C | **Tabla 3** (Apéndice), pág. 323 | Publicado | Sí, como nivel de confianza declarado del propio artículo |
| Tablas/figuras/datos suplementarios | Tabla 1 (especificaciones), Tabla 2 (diferencias %), Tabla 3 (incertidumbres), Figs. 1–9 (layout, intervalos, eficiencias, I-V, temperaturas). **Sin archivo de datos crudos ni apéndice numérico horario** | — | Todo el artículo | Publicado (solo agregados/gráficas) | No hay datos crudos descargables de ningún tipo |

## 3. Fase 2 — Decisión de reproducibilidad

**Clasificación: NO REPRODUCIBLE en el pipeline físico de la APP, tal como existe hoy en este
repositorio.**

Justificación, contrastada explícitamente contra el mínimo que exige
`references/candidato-validacion-bipv-nist-round2.md` ("Criterio de selección"):

| Mínimo requerido | ¿Se cumple? |
|---|---|
| 1. Geometría y ubicación | Parcial — orientación sí (vertical, sur), coordenadas/altitud no |
| 2. Ficha eléctrica del panel | **No** — sin Voc/Isc/Vmp/Imp para ninguno de los 8 paneles |
| 3. Configuración eléctrica | Parcial — celdas/módulos descritos, pero no como n_serie×n_paralelo directamente equivalente al contrato de la APP |
| 4. Fuente o serie meteorológica utilizable | **No** — nunca se publica una serie numérica, solo gráficas de 2–3 días y agregados % |
| 5. Energía mensual o anual medida | Parcial — solo como % de eficiencia, nunca en kWh; no hay energía AC porque no hay inversor |
| 6. Definición de la métrica de comparación | Parcial — hay diferencias % entre pares de paneles (Tabla 2), no un error absoluto modelo-vs-medición (el propio artículo dice que esa comparación es trabajo futuro) |

Solo 0 de 6 mínimos se cumple por completo; los demás son parciales o ausentes, y el más crítico
para poder ejecutar la APP —la ficha eléctrica del panel (2)— está completamente ausente para
las 8 unidades. Sin Voc/Isc/Vmp/Imp no puede construirse el SDM de **ningún** panel sin inventar
esos cuatro valores por unidad, algo que el encargo prohíbe explícitamente ("No inventes
defaults para sustituir datos ausentes"). Sin una serie meteorológica numérica, tampoco hay un
POA horario real que calcular — cualquier TMY usado sería enteramente inventado para un sitio
del que ni siquiera se conocen coordenadas exactas en el propio artículo (a diferencia de
East2, donde sí existía un supuesto de TMY sintético ya documentado y aceptado explícitamente
como tal en una ronda anterior). Y no existe inversor en el sistema medido, por lo que la
etapa `recalcular_etapa_inversor_bus()` de la APP no tiene ningún equivalente físico que
representar.

**Qué SÍ puede compararse, aunque no se ejecute la APP:**

- La ficha de área/geometría (Tabla 1) es un dato de placa verificable, sin necesidad de
  simulación.
- Las diferencias porcentuales relativas entre pares de paneles (Tabla 2, Fig. 3, Fig. 9) son
  comparaciones **medida-contra-medida**, internas al artículo — no involucran a la APP en
  absoluto y no deben presentarse como si lo hicieran.
- Los coeficientes térmicos del 2-a-Si (aunque no normalizados) y los ejemplos puntuales de
  temperatura (CIS, ETFE) son útiles como referencia cualitativa de "aislar sube la
  temperatura, y eso baja la tensión" — un efecto que el propio modelo NOCT+SDM de la APP ya
  captura de forma genérica (ver `simular_bypass_horario`), pero comparar eso NO es lo mismo
  que reproducir el panel de NIST: sería solo una coincidencia de dirección física, no una
  validación numérica.

**Qué NO puede compararse:** ninguna magnitud de energía DC/AC, POA, PR, pérdida térmica en
kWh, ni error de modelo (RMSE/MBE), porque ninguna de esas series existe en el artículo en
forma numérica utilizable.

## 4. Fase 3 — Mapeo al pipeline (documentado, no implementado)

Se documenta dónde bloquearía cada paso si se intentara el mapeo, usando el nombre real
`calculos.vinculador_sombra_multisuperficie.construir_y_recalcular_proyecto_fisico()` (el
prompt cita `calculos.vinculador_multisuperficie`, que no existe en este repositorio; el módulo
real es `vinculador_sombra_multisuperficie`, verificado leyendo el archivo).

| Paso del mapeo | Estado | Bloqueo específico |
|---|---|---|
| Datos del artículo → `session_state` | Bloqueado | `panel_dict` requeriría Voc/Isc/Vmp/Imp inexistentes; no hay `tmy_df` |
| Superficie → geometría/POA/sombra | Parcial | Geometría (tilt=90, azimuth=180) sí mapea; "sombra" del artículo es en realidad recorte de área activa por marco (coverage vs. aperture area, Tabla 1) y efecto estacional de ángulo de incidencia (Fig. 2) — **no** es sombra por obstáculo externo; forzarlo en `p_shade`/`sombras_3d.py` mezclaría conceptos físicos distintos |
| Panel → SDM | **Bloqueado por completo** | Sin Voc/Isc/Vmp/Imp no existe `estimar_sdm_desde_ficha()` posible para ninguno de los 8 paneles |
| TMY → POA | **Bloqueado por completo** | No hay serie de GHI/DNI/DHI ni siquiera de POA medida (aunque el PSP mide POA directo en el plano del panel, ese dato no se publica como serie) |
| Temperatura → modelo térmico | Bloqueado | Coeficientes crudos (solo 2-a-Si) explícitamente no normalizados a STC; sin NOCT publicado para ningún panel |
| Inversor → etapa AC | **No aplica** | El sistema medido no tiene inversor; no hay `eta_inversor` ni `P_ac_nom_W` que definir |
| Medición → métrica de comparación | Parcial | Existen diferencias % entre pares (Tabla 2) y eficiencia % anual/mensual (Figs. 3, 9), pero no una energía absoluta con la que calcular un error contra un resultado de la APP |

## 5. Fase 4 — Implementación

**No se implementó nada.** Regla del encargo: *"No modifiques código productivo si el bloqueo
es la falta de datos científicos."* Ese es exactamente este caso: el bloqueo es de datos, no de
arquitectura ni de cobertura de pruebas. Por eso:

- No se creó ningún archivo de prueba (`test_escenario_validacion_nist_round2.py` u
  equivalente) — no hay ninguna entrada mínima válida que probar sin inventar al menos cuatro
  parámetros eléctricos por panel y una serie meteorológica completa.
- No se tocó ningún archivo de `calculos/`, `pages/` ni `datos/`.
- No se activó multi-superficie ni se modificó ningún consumidor downstream.
- Todo el trabajo de esta ronda es de investigación y documentación.

## 6. Comparación obligatoria

"Valor simulado en el artículo" está vacío en todas las filas porque el artículo **no reporta
ninguna simulación ni comparación modelo-vs-medición** — es puramente un reporte de datos
medidos; el propio texto dice que la comparación con modelos vendrá en trabajo futuro
(pág. 323).

| Magnitud | Valor medido del artículo | Valor simulado en el artículo | Valor de la APP | Dif. absoluta | Dif. % | Fuente | Incertidumbre/confianza | Explicación |
|---|---|---|---|---|---|---|---|---|
| Potencia instalada (Pmax nominal) | 133 W (A) · 143–155 W (B/C/D) · 246.7 W (E/F, no estabilizado) · 438.8 W (G/H) | No reportado | No calculado (bloqueado) | N/D | N/D | Tabla 1 | Sin incertidumbre declarada para este dato de placa | Bloqueo total: sin Voc/Isc/Vmp/Imp no hay SDM que instanciar en la APP |
| POA anual | No publicado como serie ni total | No reportado | No calculado (bloqueado) | N/D | N/D | — | — | Sin serie meteorológica publicada |
| Energía DC anual | No publicada en kWh (solo % de eficiencia) | No reportado | No calculado (bloqueado) | N/D | N/D | Fig. 3, texto pág. 317–318 | Eficiencia de conversión: incertidumbre 2.5% (Tabla 3) | Sin irradiancia total no se puede convertir % a kWh; sin SDM no se puede simular |
| Energía AC anual | **No aplica** — no hay inversor | No aplica | No aplica | N/D | N/D | pág. 316 | — | El sistema medido es puramente DC |
| PR (Performance Ratio) | No reportado | No reportado | No calculado | N/D | N/D | — | — | Ausente |
| Temperatura de módulo (ejemplo puntual) | CIS aislado 51.5 °C vs no aislado 40.4 °C (5-may-2002, T_amb 23.5 °C, un solo día) | No reportado | No calculado (bloqueado) | N/D | N/D | pág. 320, Fig. 5 | Temperatura de panel: incertidumbre 0.22 °C (Tabla 3) | Un solo día ilustrativo, no una serie anual; sin NOCT/k_bipv publicado para replicar con el modelo térmico de la APP |
| Pérdidas térmicas por aislamiento (% anual) | CIS: aislado produce 4.2% (sunrise-sunset) / 5.1% (mediodía) menos energía que no aislado. 2-a-Si: diferencia de 0.1%/−0.3%, prácticamente nula | No reportado | No calculado | N/D | N/D | Tabla 2 | — | Comparación medida-contra-medida, interna al artículo; no involucra la APP |
| Pérdidas por orientación/ángulo de incidencia | Efecto estacional documentado (Fig. 9): eficiencia varía p.ej. 11.1%→13.0% (PVDF, jul→dic) atribuido a AOI, no a sombra externa | No reportado | No calculado (bloqueado) | N/D | N/D | Fig. 9, pág. 322 | — | Es un efecto de AOI acumulado estacional, no una máscara `p_shade` puntual; requeriría el mismo TMY inexistente |
| Clipping AC | No aplica | No aplica | No aplica | N/D | N/D | — | — | No hay inversor |
| Error mensual RMSE (modelo vs. medición) | No reportado en este artículo | No reportado | No calculado | N/D | N/D | pág. 323 (texto: comparación futura) | — | El propio artículo aplaza esta comparación a trabajo posterior |
| Bias anual (modelo vs. medición) | No reportado en este artículo | No reportado | No calculado | N/D | N/D | — | — | Ídem |
| Diferencia poly-Si polímero vs. vidrio (frente) | +8.4% (ETFE) / +8.6% (PVDF) anual, sunrise-sunset; +7.8%/+8.7% mediodía | No aplica | No aplica | — | — | Tabla 2 | — | Comparación interna del artículo; no requiere ni involucra la APP |
| Eficiencia de conversión anual (base cobertura) | A=10.1% · B=11.2% · C=12.2% · D=12.2% · E=4.6% · F=4.6% · G=10.2% · H=9.7% | No reportado | No calculado (bloqueado) | N/D | N/D | Fig. 3 | Eficiencia: 2.5% (Tabla 3) | Es eficiencia de campo medida (energía real / irradiancia real), no la eficiencia de placa STC que sí podría calcular la APP desde un catálogo — comparar ambas sería inválido sin la irradiancia real |

## 7. Validación obligatoria — estado

No aplica ejecutar estas verificaciones porque **no se construyó ningún escenario ni prueba**
(no hay una entrada mínima válida sin inventar datos). Se documenta explícitamente por qué cada
punto queda fuera de alcance en esta ronda, en vez de omitirlo en silencio:

| Verificación pedida | Estado |
|---|---|
| Determinismo | No aplica — no hay escenario que ejecutar |
| Ficha del módulo | Verificada como **ausente** (Voc/Isc/Vmp/Imp) para los 8 paneles — ver §2 |
| Configuración eléctrica | Verificada como **parcial** — celdas/módulos descritos, no mapeables 1:1 a n_serie×n_paralelo sin una decisión editorial no respaldada por el artículo |
| Coherencia QCRad si se construye TMY | No aplica — no se construyó ningún TMY, sintético o real, para este caso (habría exigido inventar una serie completa sin respaldo del artículo) |
| Sensibilidad a TMY, geometría y sombra | No aplica — no hay pipeline ejecutado |
| No mezcla entre superficies | No aplica — el caso es de una sola superficie (§1), no de multi-superficie |
| Comparación mensual y anual | Se realizó como comparación **medida-contra-medida** dentro del propio artículo (Tabla 2, Fig. 9), no como comparación contra la APP — ver §6 |
| Un resultado inválido no se consume downstream | No aplica — no se generó ningún resultado que pudiera consumirse |

## 8. Limitaciones

1. Ninguno de los 8 paneles tiene ficha eléctrica STC (Voc/Isc/Vmp/Imp) en este artículo —
   probablemente se encuentre en las referencias que el propio artículo cita para la
   caracterización de cada panel (Ref. [5]: Fanney, Dougherty, Davis, 2003, *"Short-Term
   Characterization of Building Integrated Photovoltaic Panels,"* ASME J. Sol. Energy Eng.,
   125, pp. 13–20; y Ref. [6]/[7]/[8]) — **no leídas en esta ronda**, fuera del alcance de los
   archivos de contexto obligatorios de este encargo. Es la pista más concreta para una
   eventual Ronda 3 si se autoriza explorar esas referencias.
2. No se publica ninguna serie meteorológica numérica ni un TMY equivalente — solo gráficas de
   ejemplo de 2–3 días puntuales y agregados porcentuales anuales/mensuales.
3. El sistema medido no tiene inversor — cualquier intento de mapear una "etapa AC" sería una
   invención sin respaldo.
4. Las coordenadas y la altitud del sitio no están en el artículo — cualquier lat/lon usado
   provendría de una fuente externa (conocimiento público sobre la sede de NIST en
   Gaithersburg), que este informe **no adopta** como supuesto por no ser data del artículo
   citado ni estar ya documentado en una ronda previa de este repositorio.
5. El artículo mismo declara que la comparación modelo-vs-medición para estos paneles está
   pendiente de trabajo futuro — es decir, ni siquiera los propios autores tenían, al momento
   de publicar, una comparación numérica que emular.
6. La clasificación de "una sola fachada, multi-panel" (§1) es sólida y no depende de estos
   bloqueos de datos — se mantendría igual aunque aparecieran las fichas eléctricas de la
   Ref. [5].

## 9. Veredicto final

**No reproducible** (en el pipeline físico de la APP, con los datos que este artículo
publica).

- No es "parcialmente reproducible": ese veredicto exigiría al menos un dato utilizable en
  cada una de las categorías críticas del mínimo del candidato (§3) — aquí la ficha eléctrica
  del panel, el elemento más crítico para instanciar cualquier superficie física en la APP,
  está completamente ausente para los 8 paneles, y no existe ninguna serie meteorológica
  numérica que sustituya al TMY.
- No es "reproducido con supuestos": ese veredicto exige que los supuestos sean razonables y
  acotados (como el TMY sintético clear-sky de East2, ya documentado y aceptado); aquí haría
  falta inventar simultáneamente Voc/Isc/Vmp/Imp para 8 paneles y una serie meteorológica
  horaria completa para un sitio sin coordenadas publicadas — eso excede lo que el encargo
  permite como "supuesto documentado" y entra en "sustituir datos ausentes con inventos",
  expresamente prohibido.
- No se cambia el veredicto sin evidencia nueva del PDF: si en una ronda futura se autoriza
  leer la Ref. [5] (caracterización eléctrica de estos mismos paneles) y esa referencia sí
  contiene Voc/Isc/Vmp/Imp, el veredicto podría revisarse a "reproducible con supuestos" — pero
  eso no se hizo aquí porque no estaba en los archivos de contexto obligatorios de este
  encargo.

Este veredicto no resta valor a NIST Round 2 como estudio experimental — es una fuente sólida,
con incertidumbres declaradas (Tabla 3) y metodología rigurosa. El bloqueo es específicamente
sobre si **este artículo, tal como está escrito**, entrega lo necesario para ejecutar el
pipeline físico de esta APP en particular. No lo hace.

## 10. Comandos ejecutados

```bash
curl -sL -A "Mozilla/5.0" -o references/buildings-nist-round2.pdf \
  "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=860956"
sha256sum references/buildings-nist-round2.pdf
```

No se ejecutaron pruebas de pytest en esta ronda porque no se modificó ni añadió código
Python — el único artefacto nuevo es este informe y el PDF fuente.
