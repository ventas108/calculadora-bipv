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
3. Evaluar la Spec «sombra por string» del punto 4.3.
