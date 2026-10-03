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
