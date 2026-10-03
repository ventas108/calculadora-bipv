# La Salle, Torre 5 — escena reconstruida desde la tesis (3-oct-2026)

**Clasificación:** escena estimada y calibrada, no medida. Todas las medidas
son coherentes con los datos y las figuras de la tesis
(`lasalle-torre5-datos-escena-real.md`). Los 3 datos sin cota se calibraron
contra la sombra por módulo de la app estándar de referencia (Tablas 19 y 20). Autorizado por el
usuario: «elabora unas mediciones coherentes con la información explícita y
fotográfica de la tesis».

Script: `bipv_python/scripts/lasalle_torre5_5_escena_tesis.py`
(`--calibrar`, `--energia`, `--submodulo`). Salidas en
`references/lasalle_torre5_escena_tesis/`.

## 1. Escena

| Elemento | Valor | Origen |
|---|---|---|
| Ubicación | 4,63833 N, −74,14833; 2.555 m; norte 160,5° | ✅ Brújula de las Figs. 6 y 7; norte derivado de los azimuts 162°/249° |
| Ala sur | 17,29 × 17,29 × 36,42 m | ✅ Fig. 4 |
| Núcleo | 3,8 m entre alas, 3 m más alto | 🟠 Figs. 6, 8 y 20 |
| Ala norte | 17,29 × 17,29 × 36,42 m, **retranqueada 7,7 m** respecto a la cara SO del ala sur | 🟠 Fig. 5 (aérea) + calibrada: el mejor ajuste entre −7,7, 0 y +7,7 m |
| Balcones SO | 3 pilas de 3,5 m de ancho, 13 pisos, vuelo 1,68 m, baranda maciza de 1 m | ✅ Pág. 35-36 · 🟠 Fig. 4 (vuelo), Figs. 6 y 8 (posición) |
| Balcones NE | 1 pila en la esquina este de la fachada SE | 🟠 Fig. 31 |
| Árboles SO | Volumen continuo a **3 m** de la fachada, 4 m de profundidad, **7 m** de alto, transparencia 0,3 | ✅ Altura 5-7 m y pisos 1-3 (pág. 36) · calibrados distancia y altura |
| Vecino frente a la SE | Bloque de **15 m** de alto a **22 m** de la fachada SE, 35 × 15 m | 🟠 Fig. 17 · calibrados distancia y altura |
| Clima | TMYx 2009-2023 El Dorado (PVGIS no es accesible desde este entorno) | Repositorio |

JSON para cargar en 🗺️ Vista 3D: `escena_torre5_completa_para_vista3d.json`
(89 bloques). Los árboles también van aparte (`escena_torre5_arboles.json`),
porque Site Designer no tiene transparencia: en la app quedarían sólidos.

## 2. Sombra por módulo frente a la app estándar de referencia (378 módulos)

| | App | La app estándar de referencia |
|---|---|---|
| **SO**: sombra media (273 módulos) | **12,4 %** | **12,6 %** |
| SO: error del perfil por altura | ±2,1 puntos | — |
| SO: error de la distribución por columnas | ±6,3 puntos | — |
| SO: módulos con < 2 % | 63 | 99 |
| **SE**: sombra media (105 módulos) | **3,2 %** | **3,0 %** |
| SE: error por altura / por columnas | ±2,4 / ±1,3 puntos | — |
| SE: módulos con < 2 % | 67 | 57 |

Sombra = pérdida de irradiación anual: haz directo bloqueado más difusa del
cielo bloqueada (Sky View Factor).

- Con la planta cuadrada (sin retranqueo), el error por altura en la SO sube
  a ±7-11 puntos: **la planta escalonada es real**, como sugería la Fig. 5.
- La distribución por columnas en la SO sigue con ±6 puntos: la posición
  exacta de cada pila de balcones y de las columnas de módulos no se puede
  fijar con las fotos.

## 3. Energía: pérdida por sombra frente al 3,7 % de la app estándar de referencia

Módulos elegidos como en la tesis (sombra < 2 %): 130 (63 SO + 67 SE), frente
a 148 instalados. Física de la app: bypass, temperatura e inversor.

| Cálculo | SO | SE | Total |
|---|---|---|---|
| App, un punto por módulo (método actual) | 0,52 % | 0,01 % | **0,28 %** |
| Sombra en irradiación de los elegidos (con difusa) | 0,91 % | 0,06 % | ≈ 0,5 % |
| Cota «peor borde del módulo» (5 puntos por módulo) | 0,67 % | 0,02 % | ≈ 0,35 % |
| Cota «string sin bypass» (el peor módulo limita la columna) | 1,42 % | 0,09 % | ≈ 0,7 % |
| **La app estándar de referencia (Tabla 21)** | — | — | **3,7 %** |

## 4. Veredicto

1. **Geometría: reproducida.** Con medidas coherentes con la tesis, la sombra
   media coincide con la app estándar de referencia dentro de 0,2-0,3 puntos en las dos fachadas.
   Los balcones, la planta escalonada, los árboles y un edificio bajo frente
   a la SE explican la sombra; las torres vecinas altas no son necesarias.
2. **Energía: no llega al 3,7 %.** Ni las cotas altas (≈ 0,7 % con el peor
   módulo limitando cada string) alcanzan el 3,7 %. Los módulos elegidos
   tienen solo 0,4-0,9 % de sombra en irradiación, también según la app estándar de referencia. Que
   la app estándar de referencia convierta eso en 3,7 % de energía apunta a su modelo eléctrico de
   sombra parcial (celda a celda, curva I-V del string) o a pérdidas que
   agrupa bajo «sombreado». Eso solo se aclara con el informe detallado de
   la app estándar de referencia: su diagrama de flujo de energía.
3. **Hallazgo para la app:** la sombra de cada superficie es el **promedio**
   de los puntos. En fachadas con sombra parcial de balcones, el módulo más
   sombreado limita la corriente del string, y el promedio subestima la
   pérdida (aquí 0,28 % frente a una cota de 0,7 %). Una Spec futura podría
   usar el peor módulo de cada string, o varios puntos por módulo, en el
   bypass.

## 5. Informe del 22-sep: qué se conserva y qué se descarta

- ✅ Se conserva: «la planta real no es cuadrada». Confirmado: el
  retranqueo de 7,7 m mejora el ajuste de ±7-11 a ±2 puntos.
- ❌ Se descarta: «un volumen convexo puede sombrearse a sí mismo entre caras
  adyacentes». Era el artefacto del algoritmo v1, que contaba el sol detrás
  de la fachada. También se descartan sus pérdidas de 26-38 % y su asimetría
  de 16 % SE>SO.

## 6. Siguientes pasos sugeridos

1. Pedir a los autores, o buscar en el anexo de la tesis, el informe completo
   de la app estándar de referencia con el diagrama de pérdidas, para separar la sombra en
   irradiación del efecto eléctrico.
2. Repetir con PVGIS cuando el entorno lo permita (`re.jrc.ec.europa.eu`)
   para la asimetría SO/SE.
3. ~~Evaluar la Spec «sombra por string» del punto 4.3.~~ Hecha (PR #115);
   resultados en la sección 7.

## 7. Nueva corrida con la Spec «sombra por string» (3-oct-2026)

Script: `lasalle_torre5_5_escena_tesis.py --energia` y
`--energia --seleccion-referencia`. Strings de 18 módulos. Salidas:
`energia.json` y `energia_seleccion_referencia.json`.

| Selección de módulos | Módulos | Sombra en irradiación SO | Pérdida, promedio | Pérdida, por string |
|---|---|---|---|---|
| Los que elige la app (< 2 % según la app) | 130 | 0,91 % | 0,28 % | **0,29 %** |
| Los que eligió la tesis (< 2 % según su tabla) | 156 | 4,98 % | 1,76 % | **1,88 %** |
| App estándar de referencia (tesis) | 148-158 | — | — | **3,7 %** |

Hallazgos:
1. **El método por string funciona**: los datos nuevos llegan al bypass y
   la pérdida sube donde hay módulos enteros a la sombra (SO: 2,64 % → 2,83 %).
   En este caso cambia poco porque la sombra de la escena es total en cada
   punto (balcones y edificios sólidos): el promedio ya activaba el bypass.
2. **Lo que más pesa es qué módulos se eligen.** Con los módulos de la tesis,
   la pérdida pasa de 0,29 % a 1,88 %: la brecha con el 3,7 % se cierra a
   la mitad. Varios módulos que la tesis ve con < 2 % de sombra tienen,
   en la escena reconstruida, ≈ 5 % en la SO: la posición exacta de las
   pilas de balcones no se puede fijar con las fotos (error por columnas
   ±6 puntos, sección 2).
3. **La brecha restante (≈ 1,8 puntos)** sigue sin explicación con los
   datos publicados. Hipótesis por revisar con el informe detallado de la
   tesis: sombra parcial dentro del módulo (celdas y diodos), sombra de la
   difusa en el bypass (la app solo usa el haz directo) y pérdidas que la
   app estándar de referencia agrupa bajo «sombreado».

## 8. Nueva corrida con la Spec «difusa en la sombra por string» (3-oct-2026)

La app ahora resta la difusa del cielo que tapan balcones, árboles y
vecinos (factor de cielo visible), y el bypass deja la difusa a los módulos
a la sombra. Pérdida de energía por sombra:

| Selección de módulos | Promedio | Por string | **Por string + difusa** | Cielo visible SO |
|---|---|---|---|---|
| Los que elige la app (130) | 0,28 % | 0,29 % | **0,56 %** | 0,98 |
| Los que eligió la tesis (156) | 1,76 % | 1,88 % | **3,66 %** | 0,90 |
| App estándar de referencia (tesis) | — | — | **3,7 %** | — |

Por fachada, con los módulos de la tesis: SO 2,64 % → 2,83 % → **5,50 %**;
SE 0,00 % → 0,01 % → 0,03 %.

Lectura honesta:
1. **La difusa era la pieza que faltaba en el cálculo de energía**: aporta
   1,8 puntos de los 1,9 que separaban 1,88 % del 3,7 %.
2. **La coincidencia (3,66 % frente a 3,7 %) es en el total, no módulo a
   módulo.** Según la tabla de la tesis, sus módulos elegidos pierden solo
   0,4 % de irradiación; en la escena reconstruida pierden ≈ 5 % en la SO.
   La escena (posición de cada balcón) sigue siendo estimada; parte del
   acuerdo puede venir de diferencias que se compensan.
3. La Salle sigue siendo una **reconstrucción provisional**, no una
   validación. Para validarla hacen falta la escena real y el diagrama de
   pérdidas de la tesis.

## 9. Recalibración por columnas (3-oct-2026)

Script: `bipv_python/scripts/lasalle_torre5_6_calibrar_columnas.py`
(`--biblioteca`, `--alas`, `--ajustar`, `--verificar`, `--energia-columnas`).
Salidas en `references/lasalle_torre5_escena_tesis/calibracion_columnas/`.

**Método.** La tabla de referencia de la fachada SO muestra franjas
verticales constantes de la fila 2 a la 16, que es la huella de pilas de
balcones que actúan como aletas. Con una biblioteca de sombra en función de
la distancia a una pila (detrás de la pila 20-38 %; a 0,5 m ≈ 10-13 %; a 1 m
≈ 5-8 %; a más de 2,5 m < 1,5 %), se ubicaron 3 pilas (las que describe la
tesis) y las 13 columnas de módulos. Después se verificó con trazado de rayos
completo.

**El escalón entre alas se descarta.** Con el retranqueo de 7,7 m de la
calibración anterior, toda el ala norte tendría sombra creciente hacia el
núcleo (hasta 37 %). La tabla de referencia tiene 0 % en las columnas 1 y 4:
la referencia modeló una fachada plana.

| Fachada SO | Escena anterior | Escena por columnas | Referencia |
|---|---|---|---|
| Correlación módulo a módulo | 0,57 | **0,90** | — |
| Sombra media (273 módulos) | 12,4 % | 14,3 % | 12,6 % |
| Sombra de los 99 módulos elegidos por la tesis | 4,98 % | **1,08 %** | 0,46 % |
| Elegidos con ≥ 2 % | 58 | 11 | 0 |

**Energía con los módulos de la tesis (escena por columnas):**

| | Promedio | Por string | Por string + difusa |
|---|---|---|---|
| SO | 0,67 % | 0,72 % | 1,36 % |
| SE | 0,00 % | 0,00 % | 0,03 % |
| **Total** | 0,45 % | 0,48 % | **0,91 %** |
| Referencia | — | — | **3,7 %** |

**Lectura física.**
1. El 3,66 % de la sección 8 venía de una geometría equivocada: los
   balcones sombreaban módulos que en la referencia están libres. Con la
   sombra en su sitio, la app da 0,91 %. La app convierte la sombra en
   pérdida de energía casi 1 a 1 (1,08 % de irradiación → 1,36 % de energía
   en la SO).
2. La referencia convierte 0,46 % de irradiación de sus módulos en 3,7 % de
   energía: un factor ≈ 8. Las sombras cercanas no pueden explicarlo.
3. La sombra dentro del módulo (bordes, celdas y diodos) tampoco basta: la
   cota de «peor borde» de la sección 3 solo sumaba ≈ 0,07 puntos.
4. **Candidato físico principal: el horizonte lejano.** La propia
   referencia da 1 %/año de «reducción por sombreado» a un arreglo
   horizontal de referencia en la cubierta, sin obstáculos cercanos. Eso
   apunta a un perfil de horizonte (los Cerros Orientales tapan el sol bajo
   de la mañana), que afecta a todos los módulos por igual y no aparece en
   la tabla por módulo. Una fachada vertical depende más del sol bajo que
   un arreglo horizontal, sobre todo la SE en la mañana. La corrida de la
   app no tenía horizonte: PVGIS no es accesible desde este entorno.
5. Prueba siguiente: repetir con el perfil de horizonte de PVGIS
   (☀️ Recurso Solar en el servidor, o habilitando `re.jrc.ec.europa.eu` en
   la red del entorno).

### 9.1 Comprobación del horizonte lejano (estimación)

Horizonte supuesto: Cerros Orientales entre los azimuts 30° y 150°, con
elevación de 4°, 6° u 8°, y 1° en el resto. Base: TMYx El Dorado, Perez.
Pérdida = haz directo tapado / irradiación total.

| Elevación de los cerros | SO | SE | Horizontal 10° S |
|---|---|---|---|
| 4° | 0,00 % | 0,79 % | 0,05 % |
| 6° | 0,00 % | 1,42 % | 0,12 % |
| 8° | 0,00 % | 1,90 % | 0,20 % |

Con el peso de cada fachada (SO ≈ 2/3 de la energía), el horizonte suma
como mucho ≈ 0,3-0,6 puntos al total. Tampoco explica el 1 % de la
referencia horizontal. **La hipótesis del horizonte queda descartada como
causa principal**; la brecha restante (≈ 2 puntos) sigue sin causa física
identificada con los datos publicados. Hace falta el diagrama de pérdidas
detallado de la tesis.

El JSON de Site Designer recibido el 3-oct (lat 4,702, lon −74,147, sin
bloques) no sirve para esta escena: está a ≈ 7 km al norte de la Torre 5 y
no trae edificios ni terreno.

### 9.2 Horizonte real de PVGIS (3-oct-2026)

Perfil descargado por el usuario de PVGIS 5.3 («Horizonte calculado», lat
4,638, lon −74,148): `references/lasalle-horizonte-pvgis-4.638_-74.148.csv`.
El horizonte más alto está al este-sureste, con **4,2°** (Cerros Orientales);
el resto está entre 0,4° y 3,4°.

| | SO | SE | Horizontal 10° S |
|---|---|---|---|
| Pérdida por horizonte (haz tapado / irradiación total) | < 0,01 % | < 0,01 % | < 0,01 % |

Solo 35 horas al año tienen el sol por debajo de ese horizonte, todas al
amanecer o al atardecer, con irradiación casi nula. **El horizonte queda
descartado**: no explica la brecha de las fachadas ni el 1 % de la
referencia horizontal.

## 10. Prueba de «🧮 Generar un punto por módulo» con la fachada SO (3-oct-2026)

Script: `bipv_python/scripts/lasalle_torre5_7_puntos_automaticos.py`
(salida `calibracion_columnas/prueba_puntos_automaticos.json`). Escena
recalibrada por columnas (sección 9), módulo SPR-MAX3-400 de 1,690 × 1,046 m
vertical, 21 filas con un paso de 1,7342 m (separación vertical 0,044 m).

**1. Precisión.** La columna 12 generada (1 × 21) coincide con los puntos
que arma el script de la escena por su cuenta: **error máximo 0,0 mm** ✅.
El generador cuenta las filas desde abajo (F01 = fila 21 de la tesis).

**2. Cuentas (13 columnas × 21 filas = 273 módulos, cableado por columnas):**

| Strings | Resultado |
|---|---|
| 21 S × 13 P | ✅ 273 puntos, 13 strings, un string por columna |
| 7 S × 39 P | ✅ 273 puntos, 39 strings (3 por columna) |
| 2 grupos: 21 S × 7 P + 21 S × 6 P | ✅ 273 puntos, 13 strings |
| 10 S × 7 P (70 módulos) | ❌ «El campo tiene 273 módulos y los grupos de strings suman 70…» |

**3. Limitación encontrada: columnas con separación irregular.** Las 13
columnas reales van entre ventanas y balcones con huecos de 1,1 m a 9,15 m.
Un campo regular entre la primera y la última columna las desplaza hasta
**7,5 m**: para esta fachada no sirve un solo campo regular. Con el
generador actual hay que generar cada tramo regular como una superficie
aparte o escribir los puntos a mano. Mejora propuesta: posiciones de columna
a medida en el generador.

**4. Sombra por string (puntos reales, un string de 21 módulos por columna):**

| | Pérdida por bypass (directa) |
|---|---|
| **Por string** (método nuevo) | **3,9 %** |
| Promedio de la superficie | 4,6 % |

Pérdida por columna: c12 29,2 %, c13 12,3 %, c3 4,6 %, c7 3,9 %, c11 0,4 %
y el resto < 0,2 %. Es el mismo patrón de franjas de la tabla de referencia
(c12 47 %, c13 17 %, c3 11 %, c7 6,5 % de irradiación). Con la sombra
concentrada en pocos strings enteros, el promedio de superficie la reparte
entre todos y **sobrestima la pérdida en 0,7 puntos (18 %)**. Cielo visible
de la fachada: 0,908. Sin árboles, porque esta prueba aísla los balcones.
