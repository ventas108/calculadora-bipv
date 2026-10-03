# La Salle, Torre 5 de Bosques de Castilla — datos para la escena real (3-oct-2026)

**Fuente:** tesis «Diseño de un sistema solar fotovoltaico para la fachada de un
edificio de propiedad horizontal» (Universidad de La Salle, 2021), 91 páginas.
También la tabla comparativa anterior de la app (`tabla-comparativa-lasalle-app.docx`).

**Marcas:**
- ✅ **Medido**: dato publicado en la tesis.
- 🟠 **Estimado**: leído de una figura, sin cota.
- ❓ **Falta**: hay que medirlo, por ejemplo en Google Earth.

## 1. Ubicación

| Dato | Valor | Fuente |
|---|---|---|
| Dirección del conjunto | Cra. 80 Bis n.º 7A-15, Bogotá (Kennedy) — «Bosques de Castilla» | ✅ Factura Enel, Fig. 29 |
| Coordenadas de la Torre 5 | **4°38'18" N, 74°8'54" O → lat 4,63833, lon −74,14833** | ✅ Brújula de las Figs. 6 y 7 (la SE marca 74°8'53") |
| Altitud | 2.550–2.560 m | ✅ Figs. 6 y 7 |
| Latitud usada en los cálculos de la tesis | 4,634° | ✅ Pág. 39 |

⚠️ La app usaba lat 4,634 y lon −74,148. La diferencia es de unos 500 m. Para la escena usa **4,63833, −74,14833**: la app rechaza la escena si se aleja más de 0,1° (PR #114).

## 2. Torre 5 (el edificio con los paneles)

| Dato | Valor | Fuente |
|---|---|---|
| Ancho de la fachada SE | **17,29 m** | ✅ Fig. 4 (cota AutoCAD 17,2905) |
| Altura | **36,42 m** (13 pisos × 2,80 m) | ✅ Fig. 4 (cota 36,4178) |
| Pisos | 13 | ✅ Pág. 36 |
| Fachada SO | Azimut **249°** | ✅ Fig. 6 (brújula) |
| Fachada SE | Azimut **162°** | ✅ Fig. 7 (brújula) |
| Ancho de la fachada SO | ❓ No está acotado | Medir en Google Earth |
| Planta | 🟠 Dos bloques desplazados (planta escalonada), con un núcleo de escaleras más alto y oscuro en el centro de la fachada SO | Figs. 5, 6, 8 y 20 |
| Área útil de fachada | ≈ 1.754 m² | ✅ Pág. 34 |

## 3. Obstáculos que dan sombra (lo que la tesis modeló en la app estándar de referencia)

| Obstáculo | Datos | Fuente |
|---|---|---|
| **Balcones de la fachada SO** (la fuente principal de sombra) | En los 13 pisos. Vuelo 🟠 **≈ 1,68 m**: la cota «1,6800» de la Fig. 4 es lo que sobresale a la izquierda de la fachada SE. Barandas metálicas abiertas | ✅ Pág. 35-36 (los balcones) · 🟠 Fig. 4 (el vuelo) |
| **Árboles junto a la fachada SO** | Altura **5–7 m**; cubren los **pisos 1 a 3** | ✅ Pág. 36, Fig. 8 |
| **Edificios vecinos** | En el modelo 3D de la app estándar de referencia (Fig. 17) hay **3 volúmenes vecinos**: un bloque bajo delante de la torre y dos bloques largos de ≈ 5-6 pisos | 🟠 Fig. 17 · ❓ posiciones y alturas exactas |
| Fachadas SE y otras | Sin obstáculos cercanos relevantes; la sombra en la SE es baja | ✅ Tabla 20 |

La tesis dice expresamente (pág. 48): «la mayor parte de las sombras que inciden en el sistema provienen de **los balcones con los que cuenta el edificio**». Para llegar al 3,7 % hay que modelar **los balcones y los árboles**; las torres vecinas pesan menos.

## 4. Sistema fotovoltaico de la tesis

| Dato | Valor |
|---|---|
| Panel | SunPower Maxeon 3 SPR-MAX3-400 (400 W, 22,6 %, 1.690 × 1.046 mm) |
| Disposición | Columnas verticales de 21 módulos entre ventanas: **SO 13 columnas × 21 filas** (273 posiciones) y **SE 5 columnas × 21 filas** (105 posiciones) |
| Criterio de selección | Solo módulos con sombra < 2 %: 156 según la Tabla 19 + 20 (la tesis dice 158) |
| Instalado | **148 módulos = 59,2 kWp** (límite: 15 % del transformador de 500 kVA) |
| Inversores | 4 × Fronius Primo 15.0-1 |
| Cable | DC 2,5 mm²; AC 120 mm² |

## 5. Resultados de la app estándar de referencia para comparar

| Magnitud | Fachadas | Referencia horizontal 10° sur |
|---|---|---|
| Potencia | 59,2 kWp | 59,2 kWp |
| Rendimiento específico | **718,33 kWh/kWp** | 1.393,42 kWh/kWp |
| PR | **86,8 %** | 89,6 % |
| **Reducción por sombreado** | **3,7 %/año** | 1 %/año |
| Energía AC | 42.560 kWh/año | 82.521 kWh/año |
| Irradiación horizontal | 1.571,3 kWh/m² | — |
| POA fachada SO / SE | 858,0 / 777,3 kWh/m² | — |

**Sombra por módulo (Tablas 19 y 20):** digitalizadas en
`references/lasalle-sombra-por-modulo-referencia-tablas-19-20.csv` (378 posiciones).
- Fachada SO: media 12,6 %. Las filas 17 a 21 (abajo, árboles) y las columnas 12 y 13 (junto al núcleo y los balcones) llegan a 40-60 %.
- Fachada SE: media 3,0 %; crece hacia abajo y hacia la columna 5.
- Los módulos elegidos (< 2 %) promedian ≈ 0,4 % de sombra en irradiación. El 3,7 % de la app estándar de referencia es **pérdida de energía**, más alta por el efecto eléctrico de la sombra parcial en los strings (bypass).

## 6. Base climática: lo que explica la asimetría SO > SE

| Fuente | POA SO | POA SE | SO/SE |
|---|---|---|---|
| La app estándar de referencia (tesis) | 858,0 | 777,3 | **+10,4 %** |
| App con PVGIS (tabla anterior) | 986,2 | 852,2 | **+15,7 %** |
| App con EPW IWEC El Dorado (3-oct) | 831,4 | 831,6 | 0 % |

Con **PVGIS**, la fuente normal de la app, la asimetría SO > SE **sí aparece**. Con el EPW IWEC desaparece. Para la corrida de comparación usa el **año típico de PVGIS** de ☀️ Recurso Solar.

## 7. Cómo armar la escena en Site Designer (cuando lo indiques)

1. **Ubicación:** lat 4,63833, lon −74,14833, elevación 2.555 m. El norte se ajusta para que las fachadas queden a 249° (SO) y 162° (SE).
2. **Torre 5:** bloque de 17,29 m (SE) × ancho SO (medido) × 36,42 m.
3. **Balcones SO:** 13 losas de ≈ 1,68 m de vuelo, una por piso, en los tramos con balcones de la Fig. 6. Las barandas son abiertas: se pueden modelar como losa más baranda, o solo la losa.
4. **Árboles SO:** un volumen de 6 m de alto a lo largo de la fachada SO (pisos 1-3), con la separación medida en Google Earth.
5. **Vecinos (Fig. 17):** los 3 bloques, con planta y altura medidas en Google Earth.
6. **Puntos de análisis:** uno por columna de módulos (SO 13 y SE 5) y a varias alturas de las 21 filas, para comparar con las Tablas 19 y 20 módulo por módulo.

## 8. Lo que falta medir antes de cargar la escena

- [x] Ubicación, altura, ancho SE, azimuts, panel, sistema y resultados (en la tesis).
- ❓ Ancho de la fachada SO y forma de la planta (dos bloques desplazados).
- ❓ Posición y ancho exactos de los balcones en la fachada SO.
- ❓ Separación de los árboles a la fachada SO.
- ❓ Planta, altura y distancia de los 3 edificios vecinos.

Las mediciones se hacen con la regla de Google Earth sobre la vista aérea (Fig. 5) y contando pisos en Street View.
