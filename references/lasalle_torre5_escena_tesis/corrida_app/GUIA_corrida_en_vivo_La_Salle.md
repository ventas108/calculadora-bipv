# Corrida en vivo: proyecto «Edificio La Salle — Torre 5» en la calculadora BIPV

**Fecha:** 3-oct-2026 · **Versión de la app:** `main` con el PR #118 (columnas a medida).
**Verificado antes de entregarlo:** todos los datos de esta guía se corrieron con el mismo
código de la app. Resultado: 156 puntos con 0,0 mm de error, ningún punto dentro del
edificio, sin bloqueos eléctricos y con los valores esperados de la sección 10.

> **Qué es este proyecto.** Las fachadas SO y SE de la Torre 5 de Bosques de Castilla
> (tesis de la Universidad de La Salle, 2021), con la escena **recalibrada por columnas**
> (informe, secciones 9 y 10). Es una **reconstrucción provisional**, no una validación.
> El documento del 22-sep todavía usaba el escalón de 7,7 m entre alas, que se descartó;
> **usa la escena de esta carpeta**, no la anterior.

---

## 0. Qué necesitas a mano

| Archivo (carpeta `references/lasalle_torre5_escena_tesis/corrida_app/`) | Para qué |
|---|---|
| `escena_lasalle_para_app.json` | La escena de Site Designer: 88 bloques (torre, núcleo, 3 pilas de balcones SO, balcones NE y edificio vecino frente a la SE). |
| `puntos_fachada_SO.txt` | Los 117 puntos de la fachada SO, para comprobar lo que genera la app. |
| `puntos_fachada_SE.txt` | Los 39 puntos de la fachada SE. |
| `resultados_esperados.json` | Los valores esperados de la sección 10. |

**El sistema que vamos a correr (parecido al de la tesis):**

| | Tesis | Esta corrida |
|---|---|---|
| Panel | SunPower SPR-MAX3-400 | **SPR-MAX3-400-COM** (catálogo de la app) |
| Módulos | 148 instalados (156 con sombra < 2 %) | **156** (117 SO + 39 SE) |
| Potencia | 59,2 kWp | **62,4 kWp** |
| Inversores | 4 × 15 kW | **4 × Growatt MID15KTL3-X** (15 kW; no hay otro de 15 kW con datos completos en el catálogo) |
| Strings | — | **12 strings de 13 módulos**: uno por columna, filas 1 a 13 de la tesis (las de arriba) |

¿Por qué solo las 13 filas de arriba? Las filas 14 a 21 (abajo) reciben la sombra de los
árboles y de los balcones bajos. Además, 13 módulos en serie es el máximo que cabe en el
inversor (Voc en frío 1.047 V frente a 1.100 V).

¿Por qué esas columnas? Son las de menos sombra según la tabla de la tesis:
- **SO:** columnas 1, 2, 4, 5, 6, 8, 9, 10 y 11. Se dejan fuera la 3, la 7, la 12 y la 13, que quedan detrás o al lado de las pilas de balcones.
- **SE:** columnas 1, 2 y 3.

---

## 1. 🏠 Proyecto

1. «¿Cuál es tu punto de partida?» → **📐 Tengo un área disponible**.
2. **Nombre del proyecto:** `Edificio La Salle - Torre 5`.
3. **Ciudad de referencia climática:** `Bogotá`.
4. **Tipo de instalación:** `🏢 Fachada BIPV`.
5. Abre **«📍 Coordenadas exactas del predio»** y escribe:
   - **Latitud (°N):** `4.63833`
   - **Longitud (°E):** `-74.14833` (siempre negativa)
   - **Altitud (m.s.n.m.):** `2555`

   ⚠️ **Indispensable:** sin estas coordenadas, la escena de Site Designer se **rechaza**
   porque la del centro de Bogotá queda a más de 0,1°.
6. Pulsa **💾 Guardar configuración**.

---

## 2. ☀️ Recurso Solar

1. Pulsa **🌐 Descargar TMY de PVGIS y calcular POA**.
2. ✅ Debe decir «Recurso solar calculado…» con las coordenadas del paso 1.

Sin este año típico no se puede calcular la sombra ni la energía.

---

## 3. 📋 Catálogo Paneles: completar el SPR-MAX3-400-COM (se hace una sola vez)

En el catálogo, este panel **no trae dimensiones ni α Isc**. Sin esos dos datos, el modo
físico no puede calcular área, eficiencia ni la curva del panel.

1. Pestaña **✏️ Editar / Eliminar** → busca **SPR-MAX3-400-COM**.
2. **Dimensiones (mm):** `1690x1046x40`
3. **α Isc (%/°C):** `0.058` (dato de la ficha usada en la tesis).
4. Guarda los cambios.

ℹ️ Este cambio queda en el catálogo del servidor. Si algún día `git pull` falla y
menciona `paneles_catalogo.xlsx`, detente y avísame, como siempre.

---

## 4. 📐 Dimensionamiento

1. **Panel:** `SPR-MAX3-400-COM`.
2. **Inversor:** `Growatt MID15KTL3-X`.
3. Revisa las **temperaturas de diseño** (T mín, T celda) que trae Bogotá. Si los campos
   salen vacíos, la app usa −5 °C / 36,35 °C / 41,94 °C, y eso también sirve.

---

## 5. 🔬 Motor IV: guardar el modelo eléctrico del panel (se hace una sola vez)

El modo físico necesita los 6 parámetros del modelo de un diodo. El catálogo no los trae
para este panel; estos son los de su ajuste a la ficha técnica, y la app los valida.

1. Abre **«🧪 Introducir parámetros SDM reales (opcional)»** y escribe:

| Campo | Valor |
|---|---|
| Iph / I_L_ref (A) | `6.57321` |
| I0 / I_o_ref (A) | `1.02098e-11` |
| Rs (ohm) | `0.322225` |
| Rsh (ohm) | `660` |
| a_ref (n x Ns) | `108` |
| N_s (celdas) | `104` |

2. **Fuente:** `Ajuste de 6 parámetros a la ficha SunPower SPR-MAX3-400-COM (Voc 75,4 V; Isc 6,57 A; Vmp 66,0 V; Imp 6,07 A)`.
3. Pulsa **✅ Validar y usar SDM real**.
   - ✅ Esperado: Pmax 400,6 W (error 0,15 %); Voc e Isc exactos; Vmp e Imp con ≈ 2 %.
4. Marca la casilla de confirmación y pulsa **💾 Guardar SDM real en el catálogo Excel**.
   Honestidad: son parámetros **ajustados a la ficha real del fabricante**, no medidos en
   laboratorio con una curva I-V. La decisión de guardarlos es tuya.
5. Vuelve a abrir **📐 Dimensionamiento** para que el proyecto tome el panel con su modelo
   completo.

---

## 6. 🗺️ Vista 3D → pestaña 🌞 Diagrama Solar → ⚙️ Superficies BIPV

Antes de empezar, lee el recuadro **📘 Cómo usar Vista 3D sin errores**.

### 6.1 Superficies

Pulsa **🏢 Fachada** dos veces y completa cada una:

| Campo | Fachada 1 | Fachada 2 |
|---|---|---|
| Nombre | `Fachada SO` | `Fachada SE` |
| Tipo | Fachada | Fachada |
| Tilt (°) | `90` | `90` |
| Azimuth (°) | `250.5` | `160.5` |
| Área (m²) | `207` | `69` |
| Panel de esta superficie | panel del proyecto | panel del proyecto |
| Activa | ✅ | ✅ |

⚠️ **Por qué 250,5° y 160,5°, y no los 249° y 162° de la tesis.** Son las direcciones
**exactas** de las caras del edificio en la escena (norte de la escena 160,5°). Los puntos se
generan sobre la cara de la escena: si la superficie tiene otro azimut, los módulos del
extremo quedan hasta 0,9 m fuera de su sitio. En energía, 1,5° de diferencia pesa menos de
0,1 %.

⚠️ **Por qué esas áreas.** Deben ser **un poco mayores** que el área de los módulos:
117 × 1,768 = 206,8 m² y 39 × 1,768 = 68,94 m². Con 68,94 m² exactos, la app bloquea
(«39 módulos ocupan 68,9 m² y la superficie tiene 68,9 m²»).

### 6.2 🔌 Inversores por superficie (antes de generar los puntos)

1. Pulsa **➕ Agregar inversor** 4 veces. En cada uno:
   - **ID:** `INV-1`, `INV-2`, `INV-3`, `INV-4`
   - **Ficha del inversor:** `Growatt MID15KTL3-X`
   - **Eficiencia (0-1):** `0.983`
   - **Potencia AC (W):** `15000`
2. **Grupos de strings.** En la Fachada SO pulsa **➕ Agregar grupo de strings** hasta tener 3:

| Superficie | Grupo | Inversor | MPPT | N serie | N paralelo |
|---|---|---|---|---|---|
| Fachada SO | G1 | INV-1 | 1 | `13` | `3` |
| Fachada SO | G2 | INV-2 | 1 | `13` | `3` |
| Fachada SO | G3 | INV-3 | 1 | `13` | `3` |
| Fachada SE | G1 | INV-4 | 1 | `13` | `3` |

✅ **Semáforos esperados.** 🟡 amarillo es normal en este diseño, no es un error:
- «pasa con poco margen (< 7,5 %)»: el Voc en frío (1.047 V) queda a 4,8 % del máximo del
  inversor (1.100 V). Es aceptable.
- «Se usan temperaturas de diseño por defecto» (solo si no las definiste en el paso 4).

No debe aparecer ningún 🔴.

### 6.3 ⚡ POA

Pulsa **⚡ Calcular POA para todas las superficies**.

### 6.4 🌳 Sombra 3D por superficie: escena

1. En **Escena Site Designer (.json)** sube `escena_lasalle_para_app.json`.
2. ✅ Debe decir «Malla Site Designer cargada: **88 bloque(s)**».
   - Si dice «No se aplicó la escena…», revisa las coordenadas del paso 1.

### 6.5 🧮 Generar un punto por módulo: Fachada SO

Abre **«🧮 Generar un punto por módulo — Fachada SO»** y escribe:

| Campo | Valor |
|---|---|
| Esquina x (m) | `-29.101` |
| Esquina y (m) | `30.381` |
| Esquina z (m) | `13.896` |
| Filas | `13` |
| Columnas | `9` |
| Módulo | `vertical` |
| Largo del módulo (m) | `1.690` |
| Ancho del módulo (m) | `1.046` |
| Strings por | `columnas` |
| Separación horizontal (m) | `0.020` (no se usa: hay posiciones a medida) |
| Separación vertical (m) | `0.044` |
| Distancia a la superficie (m) | `0.30` |
| **Posición de cada columna (m)** | `0,000; 1,100; 11,350; 12,450; 16,230; 26,480; 27,580; 28,730; 30,460` |

Pulsa **🧮 Generar puntos**.
- ✅ «117 puntos generados, asignados a 9 strings.»
- ✅ Debajo del cuadro: «🔗 117 puntos asignados a 9 strings: la sombra se calcula por string.»
- ✅ Primera línea del cuadro: `-29.209,29.788,14.741` · última: `-19.041,1.075,35.551`
  (el archivo `puntos_fachada_SO.txt` tiene las 117 líneas).

Qué significa cada columna generada (C01 a C09 = columnas de la tesis):

| Generador | C01 | C02 | C03 | C04 | C05 | C06 | C07 | C08 | C09 |
|---|---|---|---|---|---|---|---|---|---|
| Columna de la tesis | 1 | 2 | 4 | 5 | 6 | 8 | 9 | 10 | 11 |
| String | G1-S1 | G1-S2 | G1-S3 | G2-S1 | G2-S2 | G2-S3 | G3-S1 | G3-S2 | G3-S3 |

El generador cuenta las filas **desde abajo**: su F01 es la fila 13 de la tesis y su F13 es la fila 1.

### 6.6 🧮 Generar un punto por módulo: Fachada SE

| Campo | Valor |
|---|---|
| Esquina x (m) | `-15.104` |
| Esquina y (m) | `-5.349` |
| Esquina z (m) | `13.896` |
| Filas | `13` |
| Columnas | `3` |
| Módulo | `vertical` |
| Largo / Ancho (m) | `1.690` / `1.046` |
| Strings por | `columnas` |
| Separación vertical (m) | `0.044` |
| Distancia a la superficie (m) | `0.30` |
| **Posición de cada columna (m)** | `0,000; 3,500; 6,900` |

Pulsa **🧮 Generar puntos**.
- ✅ «39 puntos generados, asignados a 3 strings.»
- ✅ Primera línea: `-14.511,-5.457,14.741` · última: `-8.007,-3.154,35.551`.

⚠️ **No edites a mano los puntos generados.** Si cambias una sola línea, la app ya no sabe
a qué string pertenece cada punto y calcula la sombra por superficie, con un aviso.
Ningún punto debe mostrar el aviso amarillo «está DENTRO del modelo» o «muy pegado».

### 6.7 🌳 Calcular sombra

Pulsa **🌳 Calcular sombra de todas las superficies**. En «Estado de la sombra por superficie»:

| Superficie | Esperado |
|---|---|
| Fachada SO | 🟢 calculado completo · Puntos 117 |
| Fachada SE | 🟢 sombra cero calculada · Puntos 39 (en las 13 filas de arriba la SE no recibe sombra) |

### 6.8 Comparar y adoptar

1. Pulsa **🧪 Calcular comparación física (sin adoptar)**.
2. Revisa los valores de la sección 10.
3. Si cuadran, pulsa **✅ Adoptar cálculo físico** y continúa con 💰 Financiero, 🌿 CO₂ y 📄 Reporte.

---

## 7. Qué es indispensable y qué no

| Indispensable (si falta, no corre o da otro resultado) | Opcional |
|---|---|
| Coordenadas exactas del paso 1 | Correr 🔀 Mismatch y 🔆 Motor Óptico (si los corres, la energía cambia un poco por la suciedad y el ángulo de incidencia) |
| Dimensiones y α Isc del panel (paso 3) | Temperaturas de diseño propias |
| SDM del panel guardado (paso 5) | |
| Azimut 250,5° / 160,5° y áreas 207 / 69 m² | |
| Strings definidos **antes** de generar los puntos | |
| Posición de cada columna | |
| Escena de esta carpeta (88 bloques) | |

---

## 8. Errores frecuentes en esta corrida

1. **«No se aplicó la escena Site Designer»** → faltan las coordenadas exactas del paso 1.
2. **«El campo tiene N módulos y los grupos de strings suman M»** → revisa filas y columnas
   (13 × 9 = 117 en la SO, 13 × 3 = 39 en la SE) o N serie × N paralelo.
3. **«Hay N posiciones de columna y el campo tiene M columnas»** → cuenta los números
   separados por «;» (SO: 9; SE: 3).
4. **«los módulos ocupan … m² y la superficie tiene … m²»** → usa áreas 207 y 69 m².
5. **Panel sin modelo SDM completo** → repite el paso 5 y vuelve a abrir 📐 Dimensionamiento.
6. **Los puntos no coinciden con la primera y la última línea esperadas** → revisa la
   esquina (con signo menos) y que el azimut de la superficie sea 250,5° / 160,5°.

---

## 9. Por qué la app y la tesis no van a coincidir en la pérdida

La tesis reporta 3,7 % de «reducción por sombreado». Con esta escena, la app da ≈ 1 %. Ya
se revisaron, con números:
- la geometría módulo a módulo (correlación 0,90);
- la luz difusa;
- la sombra dentro del módulo;
- el horizonte real de PVGIS.

Ninguna explica la diferencia. A un panel horizontal sin obstáculos, la propia tesis le
asigna 1 % de pérdida; eso indica que su «sombreado» incluye otras pérdidas. Detalle en el
informe, secciones 8 a 10.

---

## 10. Valores esperados ✅

Calculados con el código de la app, el TMYx 2009-2023 de El Dorado y sin 🔆 Motor Óptico.
En el servidor la app usa **PVGIS**: los kWh pueden cambiar unos puntos porcentuales; la
cantidad de módulos y de strings, los kWp, los estados de sombra y la pérdida por sombra
(≈ 1 %) deben coincidir.

| Unidad | kWp | POA (kWh/m²·año) | Energía AC (kWh/año) | Sin sombra | Pérdida por sombra |
|---|---|---|---|---|---|
| Fachada SO · G1 (INV-1) | 15,6 | 819,8 | 10.752 | 10.884 | 1,22 % |
| Fachada SO · G2 (INV-2) | 15,6 | 819,8 | 10.762 | 10.884 | 1,12 % |
| Fachada SO · G3 (INV-3) | 15,6 | 819,8 | 10.710 | 10.884 | 1,60 % |
| Fachada SE (INV-4) | 15,6 | 718,3 | 9.221 | 9.221 | 0,00 % |
| **Total** | **62,4** | — | **41.445** | — | **1,02 %** |

- Rendimiento ≈ **664 kWh/kWp** con TMYx; con PVGIS probablemente más alto. La tesis dice 718 kWh/kWp, con otra base climática.
- Cielo visible: SO **0,973** · SE **1,000**.
- Sombra directa media en horas de sol: SO 0,9 % · SE 0 %.
