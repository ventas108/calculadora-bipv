# Manual de Usuario — Calculadora BIPV
### Innovación Química / SolTech Energy
**Versión:** Julio 2026 | **URL:** calc.innovacionquimica.com.co

---

## Tabla de contenido

1. [Descripción general](#1-descripción-general)
2. [Flujo de trabajo recomendado](#2-flujo-de-trabajo-recomendado)
3. [Página 1 — Proyecto ★★ ACTUALIZADO](#3-página-1--proyecto)
4. [Página 2 — Recurso Solar ★ ACTUALIZADO](#4-página-2--recurso-solar)
5. [Página 3 — Motor IV](#5-página-3--motor-iv)
6. [Página 4 — Dimensionamiento](#6-página-4--dimensionamiento)
7. [Página 5b — Motor Óptico](#7-página-5b--motor-óptico)
8. [Página 5 — Mismatch y Bypass Diodes ★ NUEVO](#8-página-5--mismatch-y-bypass-diodes-)
8b. [Página 9 — Vista 3D y Multi-Superficie ★★ NUEVO](#8b-página-9--vista-3d-y-multi-superficie-)
9. [Página 6 — Producción Anual ★ ACTUALIZADO](#9-página-6--producción-anual-)
10. [Página 7 — Análisis Financiero ★★ ACTUALIZADO](#10-página-7--análisis-financiero-)
11. [Página 8 — Presupuesto Bancable ★★ ACTUALIZADO](#11-página-8--presupuesto-bancable-)
12. [Página 11 — Baterías y Balance ★ ACTUALIZADO](#12-página-11--baterías-y-balance-)
13. [Página 10 — Reporte PDF ★★ ACTUALIZADO](#13-página-10--reporte-pdf-)
14. [Calculadora de Sombreado 3D](#14-calculadora-de-sombreado-3d)
15. [Cadena completa — bypass y multi-superficie](#15-cadena-completa--bypass-y-multi-superficie)
16. [Interpretación de resultados clave](#16-interpretación-de-resultados-clave)
17. [Preguntas frecuentes](#17-preguntas-frecuentes)

---

## 1. Descripción general

La Calculadora BIPV es una herramienta de simulación fotovoltaica especializada en sistemas integrados en edificios (Building-Integrated Photovoltaics). Está diseñada para proyectos en Colombia con paneles SolTech (ASP-ST1-T40) e inversores Growatt.

**Tecnologías simuladas:**
- Paneles monocristalinos BIPV de fachada (ASP-ST1-T40, 200 Wp)
- Inversores Growatt (catálogo desde Excel con motor de emparejamiento automático)
- Baterías de litio (catálogo configurable)
- Modelo óptico completo: IAM, soiling, efecto térmico confinado BIPV
- Modelo eléctrico completo: bypass diodes bajo sombra parcial

**Datos de entrada requeridos:**
- Archivo TMY (EPW) de la ubicación del proyecto
- Área y orientación de la fachada
- Perfil de consumo energético del edificio (para balance con batería)

---

## 2. Flujo de trabajo recomendado

```
1 Proyecto → 2 Recurso Solar → (3 Motor IV) → 4 Dimensionamiento
    → (5b Motor Óptico) → 5 Mismatch/Bypass → 6 Producción
    → [9 Vista 3D Multi-Sup ← opcional]
    → 7 Financiero → 8 Presupuesto → 11 Baterías → 10 Reporte PDF
```

**Páginas obligatorias:** 1, 2, 4, 6, 7, 10
**Páginas opcionales pero recomendadas para BIPV urbano:** 3, 5b, 5, 9 (multi-sup), 11

> **Cuándo usar Página 9 — Vista 3D:** Si el proyecto tiene más de una superficie
> (ej. fachada sur + techo plano + pérgola), ejecuta la Página 9 para combinar las
> producciones y alimentar Financiero con la E_ac total del sistema.

> ⚠️ **Regla de datos:** Cada página guarda sus resultados en memoria de sesión
> (`session_state`). Si recargas el navegador, todos los datos se pierden y
> debes ejecutar el flujo desde el principio.

---

## 3. Página 1 — Proyecto

**Propósito:** Registrar los datos básicos del proyecto y configurar el tipo de instalación que determina los parámetros por defecto del sistema.

### Campos obligatorios
- Nombre del proyecto y empresa cliente
- Ciudad (selección desde lista; define las coordenadas y el TMY por defecto)
- **Tipo de instalación** ← nuevo selector clave (ver tabla más abajo)

### Campos opcionales
- Descripción del sistema BIPV
- Datos del contacto

---

### ★ Selector de Tipo de instalación (nuevo)

El selector **"Tipo de instalación"** reemplaza al anterior campo genérico de área. Su función principal es configurar automáticamente los parámetros físicos correctos para cada tecnología de integración fotovoltaica.

#### Tipos disponibles y parámetros por defecto

| Tipo | Densidad recomendada (W/m²) | PR típico | Tilt por defecto | ¿Por qué ese tilt? |
|---|---|---|---|---|
| 🏢 Fachada BIPV | 80 – 180 W/m² | 0.65 | **90°** | Panel vertical integrado en muro |
| 🏠 Techo inclinado BIPV | 100 – 200 W/m² | 0.75 | **15°** | Inclinación mínima típica en Colombia |
| ⛱️ Pérgola BIPV | 60 – 150 W/m² | 0.70 | **10°** | Estructura casi horizontal para generar sombra |
| 🏗️ Marquesina BIPV | 70 – 160 W/m² | 0.68 | **30°** | Ángulo de voladizo estándar |
| 🏚️ Techo plano | 120 – 220 W/m² | 0.78 | **10°** | Mínimo para garantizar escorrentía |
| 🌿 Granja FV | 130 – 250 W/m² | 0.80 | **15°** | Ángulo óptimo para latitud Colombia (≈5°N) |

#### ¿Qué ocurre al cambiar el tipo?

Cuando seleccionas un tipo de instalación, la app actualiza en cascada tres parámetros:

1. **Densidad de potencia (W/m²):** el slider en esta misma página se mueve al valor central del rango recomendado para ese tipo.
2. **Performance Ratio (PR):** el campo PR se actualiza al valor típico de la tecnología.
3. **Inclinación (tilt):** el slider de tilt en Página 2 — Recurso Solar se inicializa al ángulo físicamente correcto para ese tipo de instalación.

> **Importante:** Si el usuario ajusta manualmente cualquiera de estos valores después de elegir el tipo, sus ajustes se respetan. El reseteo automático ocurre solo cuando cambias el tipo de instalación.

---

### ★ Alertas reactivas de densidad y PR (nuevo)

La app valida en tiempo real que la densidad y el PR ingresados sean coherentes con el tipo de instalación seleccionado. Si algún valor está fuera del rango recomendado, aparece una alerta **inmediatamente al mover el slider**, sin necesidad de hacer clic en Guardar:

```
⚠️ La densidad ingresada (50 W/m²) está fuera del rango recomendado
   para Fachada BIPV (80–180 W/m²).
   Un valor por debajo del mínimo puede subestimar la producción del sistema.
```

```
⚠️ El PR ingresado (0.90) está por encima del valor típico para
   Fachada BIPV (PR típico: 0.65). Verifica que incluya todas las pérdidas
   reales: ópticas, térmicas, cableado y mismatch.
```

**¿Puedo ignorar la alerta?** Sí. Las alertas son informativas y no bloquean el cálculo. Son útiles para detectar errores de entrada (por ejemplo, ingresar la densidad en W en lugar de W/m², o un PR optimista que no incluye pérdidas BIPV).

**¿Cuándo no aparece la alerta?** Si densidad y PR están dentro del rango del tipo seleccionado, la interfaz está limpia sin ningún mensaje.

---

### Panel "Datos del sitio" (actualización en tiempo real)

El panel inferior de la página muestra las coordenadas y altitud del proyecto. Este panel se actualiza **en tiempo real** cada vez que:
- Cambias la ciudad en el selector
- Modificas manualmente las coordenadas en el expander de ajuste fino

Cuando las coordenadas mostradas corresponden al centroide de la ciudad (no al predio exacto), aparece un indicador `⚠️ Coordenadas del centroide de la ciudad` para recordar que se deben ajustar al predio real antes de ejecutar la simulación solar.

**Resultado:** Al guardar, la app persiste el tipo de instalación, el área, la densidad, el PR y el tilt por defecto en memoria de sesión. Estos valores se usan en Página 2, Página 4, Página 6 y el Reporte PDF.

---

## 4. Página 2 — Recurso Solar

**Propósito:** Cargar el archivo climático TMY y calcular la irradiancia sobre el plano de instalación (POA).

### Pasos

1. **Cargar archivo EPW:**
   - Descarga el EPW de [https://energyplus.net/weather](https://energyplus.net/weather)
   - Busca la ciudad más cercana al proyecto
   - Arrastra el archivo `.epw` al uploader

2. **Configurar la geometría de instalación:**
   - **Orientación (azimuth):** 0° = Norte, 90° = Este, 180° = Sur, 270° = Oeste
   - **Inclinación (tilt):** ver sección "Tilt por defecto según tipo" más abajo
   - **Área de instalación (m²):** área total donde van los paneles

3. **Ejecutar cálculo:**
   - Clic en **"Calcular POA"**
   - La app calcula la irradiancia en el plano de instalación hora a hora (8 760 horas)

**Resultados:**
- POA bruta anual (kWh/m²/año)
- Heatmap de irradiancia horaria (meses × horas del día)
- Diagrama solar con la trayectoria del sol sobre el plano

> **Nota timezone:** El diagrama solar usa UTC. Para Colombia (UTC-5), la hora solar
> de mediodía aparece a las 17:00 UTC en el diagrama.

---

### ★ Tilt por defecto según tipo de instalación (nuevo)

Cuando llegas a esta página después de configurar el tipo de instalación en Página 1, el slider de **inclinación (tilt)** ya está pre-cargado con el ángulo físicamente correcto para tu tipo:

| Tipo de instalación | Tilt pre-cargado | Referencia física |
|---|---|---|
| 🏢 Fachada BIPV | **90°** | Panel integrado verticalmente en muro |
| 🏠 Techo inclinado BIPV | **15°** | Inclinación mínima típica en edificios Colombia |
| ⛱️ Pérgola BIPV | **10°** | Estructura de cobertura casi horizontal |
| 🏗️ Marquesina BIPV | **30°** | Voladizo en ángulo estándar de marquesina |
| 🏚️ Techo plano | **10°** | Mínimo para escorrentía en techos planos |
| 🌿 Granja FV | **15°** | Óptimo para latitud Colombia (~5° N) |

Un **banner informativo** en la parte superior de la página muestra el tipo activo y el ángulo sugerido, por ejemplo:

```
ℹ️ Tipo de instalación: Fachada BIPV
   Tilt sugerido: 90° (panel vertical integrado en muro).
   Puedes ajustar el slider si el diseño específico requiere otro ángulo.
```

**¿Puedo cambiar el tilt manualmente?** Sí. El valor pre-cargado es una sugerencia. Si tu diseño requiere un ángulo diferente (por ejemplo, una fachada inclinada a 75°), mueve el slider libremente. La app guardará tu selección manual para esa sesión.

**¿Qué pasa si vuelvo a cambiar el tipo en Página 1?** El tilt se resetea al valor correspondiente al nuevo tipo. Esto evita que el ángulo de una fachada quede accidentalmente en un proyecto de granja FV.

> **Impacto en el cálculo:** El tilt es el parámetro geométrico más sensible en el cálculo de POA. Una fachada vertical (90°) capta principalmente irradiancia difusa y directa de bajo ángulo solar; un techo plano (10°) capta mucho más irradiancia directa anual. Usar el tilt incorrecto puede llevar a errores de ±20–30% en la POA anual.

---

## 5. Página 3 — Motor IV

**Propósito:** Modelar la curva corriente-voltaje (I-V) del panel usando el modelo de 5 parámetros (SDM).

**¿Cuándo usar?**
- Cuando tienes la ficha técnica completa del panel (Voc, Isc, Vmpp, Impp, α, β, γ)
- Para verificar que los parámetros del catálogo son coherentes

**¿Cuándo no es necesario?**
- Si usas los paneles ASP-ST1-T40 del catálogo estándar (ya tienen SDM calibrado)
- Para una estimación rápida sin análisis eléctrico detallado

**El Motor IV se activa automáticamente** cuando el panel tiene ficha técnica completa
en el catálogo. No requiere intervención manual.

---

## 6. Página 4 — Dimensionamiento

**Propósito:** Calcular cuántos paneles caben en la fachada y seleccionar el inversor óptimo.

### Pasos

1. **Revisar los datos de la fachada:**
   - Área disponible (viene de Página 2)
   - Dimensiones del panel (0.98 m × 1.76 m para ASP-ST1-T40)

2. **Configurar el layout:**
   - Orientación de los módulos (portrait / landscape)
   - Espaciado entre paneles (si aplica)

3. **Selección de inversor:**
   - La app propone el inversor más adecuado del catálogo Growatt
   - Verifica que Vdc_máx del string ≤ Vdc_máx del inversor
   - Verifica que P_pico_array ≤ 1.3 × P_nominal_inversor

**Resultados:**
- N° de paneles instalables
- Potencia instalada (kWp)
- Inversor recomendado con alertas de compatibilidad

---

## 7. Página 5b — Motor Óptico

**Propósito:** Aplicar las correcciones ópticas específicas de BIPV sobre la POA bruta.

**Cascada de correcciones:**
```
POA bruta
  × IAM (Incidence Angle Modifier)    → pérdida por reflexión a ángulos oblicuos
  × Soiling                           → pérdida por suciedad acumulada en vidrio
  × Factor térmico BIPV (k_BIPV)      → penalización por cámara trasera confinada
  = POA efectiva
```

**¿Cuándo usar?**
- Siempre en proyectos BIPV de fachada para un cálculo más preciso
- El k_BIPV para fachada ventilada es ~0.93–0.97; para fachada sellada es ~0.88–0.92

**¿Cuándo omitir?**
- En estudios de prefactibilidad donde una estimación ±10% es suficiente

**Resultado:** `POA efectiva` (kWh/m²/año) que la Página 6 usa en lugar de la POA bruta.

---

## 8. Página 5 — Mismatch y Bypass Diodes ★

> **Esta página es nueva y clave para proyectos BIPV en entornos urbanos con obstáculos.**

**Propósito:** Calcular las pérdidas eléctricas reales por sombra parcial en strings,
modelando la activación de los bypass diodes integrados en cada panel.

### ¿Por qué importa?

Cuando un obstáculo (edificio vecino, voladizo, antena) sombrea *parte* de un string,
los módulos sombreados reducen su Isc. Los bypass diodes se activan para proteger el
circuito, pero al hacerlo **eliminan toda la tensión** de esos módulos. La pérdida real
es mucho mayor que la reducción proporcional de irradiancia.

Ejemplo: sombra en 2 de 8 módulos en serie → pérdida NO es 25%, sino puede ser 40-60%
de la producción de ese string en esas horas.

---

### Sección 1 — Cargar el CSV de Factor de Sombreado

El CSV debe provenir de la **Calculadora de Sombreado 3D** (bipv.innovacionquimica.com.co).

**Formato del CSV esperado:**
```
Hora,Mes,Dia,FS_geometrico,FS_climatico,FS_combinado,Fachada,...
8,3,21,0.00,0.05,0.04,Fachada_Sur,...
9,3,21,0.12,0.15,0.24,Fachada_Sur,...
```

- **FS_geometrico:** factor de sombreado solo por obstáculos físicos (recomendado)
- **FS_climatico:** incluye nubes → sobreestima el bypass
- **FS_combinado:** combinación de ambos
- **Convención:** 0 = sin sombra, 1 = sombra total (p_shade directo)
- **Fachada:** nombre de la fachada del análisis

**Pasos:**
1. Arrastra el CSV al uploader
2. La app detecta automáticamente qué columna de FS usar (prioridad: FS_geometrico)
3. Revisa el banner de color:
   - 🟩 **Verde:** FS_geometrico detectado — resultados más precisos
   - 🟨 **Amarillo:** solo FS combinado disponible — puede sobreestimar bypass

---

### ★ Detección automática de CSV con FS invertido

> **Importante para CSVs generados por herramientas externas**

Algunas herramientas exportan el Factor de Sombreado con la **convención invertida**:
- Convención estándar (calculadora BIPV): **0 = sin sombra, 1 = sombra total**
- Convención invertida (puntos manuales): **1 = sin sombra, 0 = sombra total** (transmitancia)

La app detecta automáticamente si el CSV parece estar invertido (>55% de valores > 0.90
y sin columna FS_geometrico explícita) y muestra:

```
🔴 POSIBLE CSV INVERTIDO: el 87% de los valores FS están entre 0.90 y 1.00,
lo que sugiere transmitancia (1=sin sombra), no Factor de Sombreado (1=sombra total).
```

**Acción:** Abre "Opciones avanzadas" y activa **"Invertir FS (1 − FS)"**.

---

### ★ Selector de Fachada

Si el CSV contiene datos de múltiples fachadas o fachadas con múltiples orientaciones,
aparece un selector **"🏗️ Seleccionar fachada del array"** con las fachadas detectadas.

Selecciona solo la fachada donde está instalado el array antes de simular.
Esto evita que obstáculos de otras fachadas contaminen el cálculo de bypass.

---

### Sección 5 — Configuración de strings y cobertura temporal

#### Configuración de strings

| Parámetro | Descripción | Ejemplo Ruta N |
|---|---|---|
| Panel fotovoltaico | Debe coincidir con el de Producción | ASP-ST1-T40 |
| Módulos en serie (N_series) | Módulos en un string | 8 |
| Strings en paralelo (N_parallel) | Número de strings | 55 |

La app infiere N_series automáticamente buscando que Voc_array ≈ 400 V DC.

#### ★ Cobertura temporal del CSV

El CSV de días críticos típicamente cubre solo 4–6 días del año (~60 horas).
La app muestra:

| Métrica | Descripción |
|---|---|
| Días críticos | Cuántos días con datos hay en el CSV |
| Cobertura modo exacto | Horas TMY con coincidencia exacta (mes/día/hora) |
| Cobertura modo mensual | Horas cubiertas al replicar el patrón a todo el mes |

**Modos de cobertura:**

- **📅 Modo mensual (recomendado):** El patrón horario de cada día crítico
  (ej. 21 de marzo) se replica a todos los días de ese mes. La geometría solar
  varía <3° dentro de un mes, así que el día crítico es representativo del mes.
  **Cobertura típica: 25–40% del año.**

- **📌 Modo exacto:** Solo usa los días del CSV. El 98%+ del año tiene FS=0.
  Útil para verificación pero subestima enormemente las pérdidas anuales.

> **Recomendación:** Usa el modo mensual siempre para el diseño. Usa el modo exacto
> para comparar con mediciones puntuales o para auditorías.

---

### Sección 5 — Ejecutar la simulación

Clic en **"⚡ Calcular pérdida real por bypass diodes"**.

La simulación:
1. Alinea el CSV con el TMY según el modo seleccionado
2. Para cada hora del año (8 760 iteraciones): si FS > 5%, resuelve el circuito IV
   con los módulos sombreados activos y calcula la potencia real del array
3. Compara con la producción sin sombra (baseline) → calcula pérdida horaria

**Resultados mostrados:**
- **Pérdida bypass (kWh DC/año):** energía DC perdida por la activación de bypass
- **% sobre E_dc:** fracción de la producción DC base
- **Horas con bypass activo / año:** magnitud del problema
- **E_dc_base vs E_dc_bypass:** curva mensual comparativa
- **Tabla mensual:** desglose de pérdidas mes a mes

**Interpretación del % de pérdida bypass:**
- < 2%: Bajo — sombras leves, bypass no es un problema crítico
- 2–5%: Moderado — considerar redibujo de layout o modificar strings
- 5–10%: Alto — evaluar cambio de orientación o supresores de sombra
- > 10%: Muy alto — el sistema BIPV tiene un problema de sombreado serio

---

## 8b. Página 9 — Vista 3D y Multi-Superficie ★★ NUEVO

**Propósito:** Modelar proyectos BIPV con **más de una superficie** (fachada + techo + pérgola + marquesina), combinando sus POA y producciones en un único valor de E_ac total que alimenta Financiero, Baterías y CO₂.

> **Cuándo usarla:** Solo si el proyecto tiene múltiples superficies con distintas orientaciones. Para una sola superficie (techo plano, fachada única), Página 9 no es necesaria.

### Sub-tabs de la Página 9

| Sub-tab | Función |
|---|---|
| ⚙️ Superficies BIPV | Crear y configurar cada superficie (tilt, azimuth, área, tipo) |
| 🗺️ Vista 3D | Visualización 3D del edificio con mapa de POA o FS por mes |
| 📊 Producción por Superficie | Barras apiladas, recurso solar, tabla resumen, bypass por superficie |
| ☀️ Diagrama Solar | Trayectoria solar con perfil de obstáculos (sin cambios) |

### ⚙️ Sub-tab 1 — Superficies BIPV

**Tipos de superficie disponibles:**

| Tipo | Tilt por defecto | Azimuth sugerido | Corrección T° |
|---|---|---|---|
| Fachada BIPV | 90° | 0° / 90° / 180° / 270° | Confinada (k=1.3) |
| Techo plano | 10° | 0° | Ventilada (k=1.0) |
| Techo inclinado | 30° | 180° (sur) | Ventilada (k=1.0) |
| Pérgola BIPV | 15° | 180° (sur) | Semi-ventilada (k=1.1) |
| Marquesina | 20° | 180° (sur) | Semi-ventilada (k=1.1) |

**Pasos:**
1. Pulsar **"➕ Agregar superficie"** para cada plano activo del edificio
2. Configurar nombre, tipo, área, tilt y azimuth para cada superficie
3. Pulsar **"☀️ Calcular POA para todas las superficies"**
4. La app calcula el perfil TMY para cada orientación

### 📊 Sub-tab 3 — Producción y Bypass Multi-Superficie

#### Secciones 1–4 (producción base)
- **1.** Barras apiladas de E_ac mensual por superficie
- **2.** POA anual por orientación (gráfica horizontal)
- **3.** Tabla resumen con área, POA, E_ac y % del total
- **4.** FS mensual por superficie desde el CSV (requiere columna `Fachada`)

#### ★ Sección 5 — Bypass diodes por superficie (#46)

Ejecuta el modelo de bypass **individualmente** para cada superficie usando su propio perfil POA y su propio perfil FS del CSV:

1. Seleccionar el panel fotovoltaico y N_series (compartido para todas las superficies)
2. El N_parallel de cada superficie se calcula automáticamente: `N_parallel = área_m² / área_panel / N_series`
3. Pulsar **"⚡ Calcular bypass por superficie"**

**Resultado — tabla por superficie:**

| Columna | Significado |
|---|---|
| Fachada CSV | Qué filas del CSV se usaron para esta superficie |
| E_ac base (kWh/año) | E_ac sin corrección bypass |
| Pérdida bypass (%) | % de la E_ac perdida por activación de bypass diodes |
| Horas bypass/año | Horas al año con bypass activo en esa superficie |
| E_ac bypass (kWh/año) | E_ac real corregida por bypass |

> **Clave:** `E_ac_anual_kWh_multisup` se actualiza con la suma de E_ac_bypass de todas las superficies. Esta clave tiene **prioridad máxima** en Financiero, Baterías y CO₂.

### 🔗 Botón "Integrar al Financiero"

Después de calcular la POA (o el bypass), el botón **"🔗 Integrar al Financiero"** escribe las claves exclusivas del sistema multi-superficie en la sesión:

| Clave | Contenido | Nunca sobreescribe |
|---|---|---|
| `E_ac_anual_kWh_multisup` | E_ac total del sistema | `E_ac_anual_kWh` (superficie única) |
| `poa_df_multisup` | POA combinada ponderada por área | `poa_df` (POA bruta original) |
| `area_total_multisup` | Suma de áreas activas | `area_fachada_m2` |
| `multisup_desglose` | Lista con detalle por superficie | — |
| `multisup_activo` | Flag booleano | — |

### Prioridad en las páginas aguas abajo

Cuando `multisup_activo = True`, Financiero, Baterías y CO₂ usan la E_ac multi-superficie:

```
💰 Financiero / 🔋 Baterías / 🌿 CO₂ leen en este orden:
  1. E_ac_anual_kWh_multisup  ← si multi-superficie activo  ★ prioridad máxima
  2. E_ac_anual_kWh_bypass    ← si bypass (superficie única) ejecutado
  3. E_ac_anual_kWh           ← simulación estándar base
```

Un banner en cada página indica qué modo está activo.

---

## 9. Página 6 — Producción Anual ★ ACTUALIZADO

**Propósito:** Calcular la producción AC anual del sistema completo.

### Pasos

1. Revisa los datos de entrada (tomados automáticamente de páginas anteriores)
2. Verifica que el inversor esté correctamente seleccionado
3. Si ejecutaste el Motor Óptico (5b), la POA efectiva se usa automáticamente
4. Clic en **"Calcular producción"**

**Balance energético mostrado:**

```
POA bruta → Motor Óptico (IAM + Soiling + Térmico) → POA efectiva
  → Pérdida mismatch → E_dc → Pérdida bypass ← (si Página 5 fue ejecutada)
  → Pérdida inversor → E_ac anual
```

Si ejecutaste el modelo de bypass en Página 5, el balance incluye automáticamente
una barra **"Bypass diodes"** mostrando los kWh DC perdidos.

**La E_ac guardada en memoria:**
- `E_ac_anual_kWh` — producción base (sin corrección bypass)
- `E_ac_anual_kWh_bypass` — producción real (con corrección bypass) ← usada por Páginas 7, 11

### ★ Tasa de degradación anual desde historial PR (#28)

Al final de la Página 6 hay una nueva sección **"📉 Tasa de degradación anual del sistema"**. Permite calcular la degradación real de los módulos a partir del PR corregido por temperatura de varios años operativos.

**Pasos:**
1. Ingresar el número de años con datos (mínimo 2)
2. Para cada año: el año calendario y el PR_corr_T promedio anual (tomado de la tabla de diagnóstico)
3. La app ajusta una **regresión lineal** sobre los puntos e informa:

| Métrica | Descripción |
|---|---|
| Pendiente PR (pp/año) | Cambio absoluto en puntos porcentuales por año |
| Tasa de degradación | % de pérdida relativa al PR inicial por año |
| Vida útil (PR > 70%) | Años estimados hasta degradación severa |

El resultado se guarda como `tasa_degradacion_calculada` y queda disponible en Página 7 como alternativa al slider paramétrico.

> **Ejemplo:** Si PR_corr_T fue 82% en 2022, 81.3% en 2023 y 80.6% en 2024, la regresión da −0.7 pp/año → tasa = 0.70%/año (ligeramente superior al 0.5% de catálogo CdTe).

---

## 10. Página 7 — Análisis Financiero ★★ ACTUALIZADO

**Propósito:** Calcular TIR, VPN, Payback y LCOE del proyecto bajo la Ley 1715/2014.

### ★ Prioridad de E_ac: multi-superficie > bypass > base

La Página 7 selecciona automáticamente la estimación de producción más precisa disponible:

```
Prioridad alta    → E_ac_anual_kWh_multisup   (Página 9 integrada)
Prioridad media   → E_ac_anual_kWh_bypass     (Página 5 bypass ejecutado)
Prioridad baja    → E_ac_anual_kWh            (simulación estándar)
```

Un banner muestra qué fuente está activa y permite desactivar el modo multi-superficie con un botón "Desactivar".

### ★ Toggle de degradación desde historial real (#28)

Si ejecutaste la sección **"📉 Degradación anual"** de Página 6 con al menos 2 años de PR histórico, aparece un interruptor junto al slider de degradación:

```
🔘 Usar degradación del historial real — 0.62%/año
   (calculada en 📊 Producción › Degradación anual)
```

Al activarlo, el slider paramétrico se reemplaza por la tasa calculada por regresión lineal. La TIR y el VPN quedan calculados con la degradación **real medida** del sistema, no el valor genérico de catálogo.

### Pasos

1. **Sección 1 — CAPEX:** Ingresa costos de módulos, inversor, estructura, instalación
2. **Sección 2 — Parámetros financieros:**
   - Tarifa energía (COP/kWh)
   - TRM (COP/USD)
   - Tasa de descuento (%)
   - Horizonte de análisis (años)
   - Degradación anual del sistema (% — o usar historial real con toggle)
3. **Sección 3 — Beneficios Ley 1715:** Revisa los ahorros tributarios calculados
4. **Clic "📊 Calcular TIR, VPN, Payback y LCOE"**

### Beneficios Ley 1715/2014

| Artículo | Beneficio | Cálculo |
|---|---|---|
| Art. 11 | Deducción renta | 50% × CAPEX × tasa_renta (35%) |
| Art. 12 | Exclusión IVA equipos | 19% × CAPEX_equipos |
| Art. 14 | Depreciación acelerada | VPN del diferencial 5yr vs 10yr |

> Requiere certificación UPME previa al inicio del proyecto.

### Indicadores de viabilidad

| Indicador | Proyecto viable | Proyecto marginal | Proyecto no viable |
|---|---|---|---|
| TIR | > 12% | 8–12% | < 8% |
| VPN | > 0 USD | Cercano a 0 | < 0 USD |
| Payback simple | < 10 años | 10–15 años | > 15 años |
| LCOE | < tarifa red | ≈ tarifa red | > tarifa red |

---

## 11. Página 8 — Presupuesto Bancable ★★

**Propósito:** Construir el presupuesto completo del proyecto con estructura
financiera exigida para bancabilidad: CAPEX directo, costos blandos, contingencias
diferenciadas y OPEX anual proyectado a 25 años.

> **¿Por qué "bancable"?** Un banco o fondo de inversión no financia proyectos
> con un estimado de obra simple. Exige un presupuesto que demuestre que todos
> los costos están identificados, cuantificados y respaldados por fuentes.
> Esta estructura cumple ese estándar.

---

### Encabezado del presupuesto

Antes de comenzar, completa el bloque superior (expandible):

| Campo | Qué es | Por qué importa |
|---|---|---|
| **Nombre del proyecto** | Identificador único | Traza el presupuesto a un proyecto específico |
| **Vigencia** | Fecha hasta la que los precios son válidos | Los bancos exigen presupuestos vigentes; precios de hace >90 días se consideran desactualizados |
| **Elaboró** | Nombre de la empresa o profesional | Da trazabilidad y responsabilidad técnica al documento |

---

### Estructura de 7 pestañas

| Pestaña | Contenido | Categoría financiera |
|---|---|---|
| 🔩 Perfilería y Estructura | Rieles, soportes, fijaciones BIPV | CAPEX Directo |
| 👷 Mano de Obra | Instalación, certificación RETIE, transporte | CAPEX Directo |
| ⚡ Sistema FV | Cables, protecciones, cajas, puesta a tierra, monitoreo | CAPEX Directo |
| 🔌 Inversor y Equipos Eléctricos | Tableros, breakers, comunicaciones | CAPEX Directo |
| 📦 Equipos del Catálogo | Módulos + inversor + baterías (auto desde Dimensionamiento) | CAPEX Directo |
| 🧾 **Costos Blandos** | Ingeniería, trámites, legal, PM, ITA, póliza CAR | CAPEX Blando (soft costs) |
| 📅 **OPEX Anual** | O&M, limpieza, seguro operativo, monitoreo, fondos reposición | Gasto operativo anual |

---

### Columna "✔ Activo" — incluir o excluir ítems

Cada fila tiene un **checkbox** al inicio:

- ✅ **Marcado:** el ítem suma al subtotal y al CAPEX total.
- ☐ **Desmarcado:** queda visible como referencia pero **no suma**. Útil
  para ítems opcionales o que cubre otra partida del contrato.

**Agregar una fila nueva:** botón **➕** al pie de la tabla → fila en blanco → escribe directamente.
**Eliminar una fila:** selecciona la fila → tecla **Supr / Delete**.
**Resetear:** botón **↺** en la parte superior de cada pestaña vuelve a la plantilla base del Excel.

> **¿Por qué "Suprimir eliminar" aparece en gris?**
> El botón se activa **solo cuando hay al menos una fila desmarcada** (desactivada).
> Su función es eliminar permanentemente todas las filas que estén sin marcar.
> Si todas las filas están activas (0 desactivados), no hay nada que suprimir y Streamlit
> lo muestra deshabilitado automáticamente. Para activarlo: desactiva cualquier fila
> quitando su ✅, y el botón quedará disponible.

---

### Fuente de precios — campo de trazabilidad

Cada pestaña tiene un campo de texto **"Fuente / cotización"**. Escribe aquí el
origen de los precios ingresados (ej.: *"Cotización Acesco julio 2026"*,
*"Lista de precios Schneider distribuidora Medellín"*).

> **Impacto bancario:** El auditor técnico independiente (ITA) y el banco
> verifican que los precios sean de mercado y tengan respaldo documental.
> Sin fuente, los precios se consideran estimados, no cotizaciones.

---

### 🧾 Pestaña Costos Blandos — soft costs

Los **costos blandos** son todos los gastos del proyecto que no son materiales
ni mano de obra de instalación física. Representan entre el **8–18% del CAPEX
directo** en proyectos BIPV en Colombia.

| Ítem | Qué incluye | Referencia Colombia |
|---|---|---|
| **Ingeniería, diseño y memorias** | Planos eléctricos y mecánicos, cálculos estructurales, estudio de producción | 1.5–3% CAPEX directo |
| **Estudio de sombreado y simulación BIPV** | Modelo 3D, análisis horario, curvas IV, informe técnico | USD 800–2.500 (proyecto pequeño) |
| **Registro UPME y trámites Ley 1715** | Solicitud calificación UPME, resolución de calificación | USD 500–1.200 (incluye honorarios gestor) |
| **Concepto de conexión — operador de red** | Solicitud al operador local (EPM, ENEL, etc.) para conexión en paralelo | USD 200–800 |
| **Certificación RETIE / RITEL** | Inspección por organismo certificador acreditado. Obligatorio en Colombia | USD 300–900 según potencia |
| **Gestión del proyecto (PM)** | Director de proyecto, coordinación, informes de avance, actas de entrega | 3–5% CAPEX directo |
| **Asesoría legal y estructuración financiera** | Contratos EPC, contrato O&M, asesoría financiera, estructuración crédito | USD 1.500–5.000 |
| **Auditoría técnica independiente (ITA)** | Revisión por firma especializada externa. **Obligatorio para financiamiento > USD 200k** | USD 2.000–8.000 |
| **Póliza CAR — construcción todo riesgo** | Seguro durante la ejecución del proyecto (daños, robo, responsabilidad civil) | 0.4–0.6% CAPEX directo |
| **Gastos notariales, registros y licencias** | Escrituras de servidumbre, permisos municipales, otros | USD 300–1.000 |

> **Impacto:** Si omites los costos blandos, el CAPEX está subvalorado en
> un 8–18%. Esto hace que la TIR calculada sea artificialmente alta y el
> VPN sobreestimado — el proyecto parecerá más rentable de lo que es.
> Un banco detecta esto inmediatamente y lo considera una señal de riesgo.

---

### 📅 Pestaña OPEX Anual — costos de operación

El **OPEX** (Operating Expenditure) es el costo anual de mantener el sistema
funcionando durante su vida útil (25–30 años). Es la diferencia entre los
ingresos brutos por energía y el flujo de caja neto que recibe el inversionista.

> **Los valores en esta pestaña representan USD por año** (no por unidad física).
> El total anual se envía automáticamente a 💰 **Financiero** para construir el
> flujo de caja a 25 años.

| Ítem | Qué incluye | Referencia Colombia |
|---|---|---|
| **O&M preventivo — visitas técnicas** | Revisión anual de módulos, strings, inversor, cableado, torqueo de conexiones | USD 5–10/kWp·año |
| **Limpieza de módulos** | Lavado manual o con agua a presión. En Urabá: alta frecuencia por humedad y vegetación | USD 1–3/kWp·año (4 veces/año aprox.) |
| **Seguro operativo — todo riesgo** | Cubre daños por granizo, viento, cortocircuito, robo de módulos o inversor | 0.3–0.5% CAPEX/año |
| **Monitoreo remoto (Growatt/SCADA)** | Plataforma de telemetría en tiempo real, alertas de falla, informes de producción | USD 200–600/año |
| **Revisión anual inversor** | Actualización firmware, limpieza ventiladores, verificación protecciones | USD 150–400/año |
| **Fondo de reposición inversor** | Provisión anual para reemplazar el inversor al año 12–15 de vida | Costo inversor ÷ 12 años |
| **Fondo de reposición módulos** | Provisión para módulos dañados fuera de garantía, degradación acelerada | 0.1–0.2% CAPEX/año |
| **Administración y costos fijos** | Contabilidad, reportes a UPME, administración de contratos O&M | USD 300–800/año |

**Referencia consolidada Colombia BIPV:**

| KPI OPEX | Valor de referencia |
|---|---|
| OPEX total / kWp · año | USD 8–15 |
| OPEX / CAPEX anual | 1.0–2.5% |
| Fondo reposición inversor | ~0.8–1.2% CAPEX/año |

> **Impacto financiero:** Si el OPEX es USD 0 en el modelo, la TIR y el VPN
> están sobreestimados. Un modelo sin OPEX no es financieramente evaluable.
> El banco proyecta el OPEX incluso si el solicitante no lo incluye, y usa
> sus propios estimados (conservadores) si no hay datos del proyecto.

---

### Cálculo del CAPEX Total — tres niveles de contingencia

El CAPEX total se construye en cascada:

```
CAPEX Directo     = Perfilería + Mano de Obra + Sistema FV + Inversor + Catálogo
CAPEX Base        = CAPEX Directo + Costos Blandos
─────────────────────────────────────────────────────────
+ Costos indirectos (%)   → AUI: Administración, Imprevistos, Utilidad del contratista
+ Contingencia técnica (%) → Reserva por riesgo específico de instalación BIPV en fachada
+ Contingencia de precios (%) → Reserva por volatilidad de TRM y materiales importados
═════════════════════════════════════════════════════════
= CAPEX TOTAL     → va a Financiero, Ley 1715 y Reporte PDF
```

#### Significado de cada contingencia

**Costos indirectos — AUI (Administración, Imprevistos, Utilidad)**

El AUI es el porcentaje que aplica el **contratista EPC** sobre el costo
directo para cubrir sus propios gastos de administración, los imprevistos
de ejecución y su utilidad neta.

- Referencia Colombia: **10–18%** del CAPEX directo.
- En proyectos BIPV con acceso difícil o trabajo en altura: extremo alto del rango.
- *No confundir con la utilidad del inversionista (dueño del proyecto).*

**Contingencia técnica**

Reserva específica para riesgos de ejecución que son más altos en BIPV
que en una instalación convencional en suelo:

- Integración con la fachada existente (interferencias no previstas en planos)
- Trabajos en altura con andamios o grúas
- Adaptaciones estructurales del edificio
- Pruebas de compatibilidad electromagnética con la fachada

- Referencia: **8–15%** para BIPV de fachada. Instalación en suelo: 4–8%.

**Contingencia de precios**

Reserva para absorber el impacto de variaciones en el tipo de cambio
(TRM) y en los precios de materiales importados (módulos, inversor,
cables de cobre) entre la fecha del presupuesto y la ejecución.

- Referencia: **3–7%** según horizonte de ejecución.
- Para proyectos con ejecución > 6 meses desde la cotización: usar extremo alto.

---

### KPIs de bancabilidad — semáforo automático

La calculadora evalúa cuatro indicadores y muestra alertas si están
fuera del rango de referencia para proyectos BIPV en Colombia:

| KPI | Cálculo | Rango sano | Alerta si... |
|---|---|---|---|
| **USD / Wp** | CAPEX total ÷ potencia instalada (W) | USD 1.8–4.0/Wp | > 5.0/Wp (precio en COP?) · > 3.5/Wp (rango alto) |
| **USD / m²** | CAPEX total ÷ área de fachada (m²) | USD 180–350/m² | > 400/m² |
| **OPEX / CAPEX** | OPEX anual ÷ CAPEX total | 1.0–2.5%/año | > 3.0% |
| **OPEX / kWp·año** | OPEX anual ÷ potencia instalada | USD 8–15/kWp | indicativo |

> **USD/Wp** es el indicador más universal. Un banco lo compara contra
> proyectos financiados en la región. Si está fuera de rango, el banco
> pide justificación técnica o rechaza el presupuesto.

> **USD/m²** es clave para BIPV porque relaciona el costo con el área
> de fachada aprovechada, no solo con la potencia. Un edificio en zona
> de alto costo de construcción puede tener un USD/m² alto pero un
> USD/Wp razonable — es importante mostrar ambos.

---

### Fracción de equipos — base para Ley 1715

La calculadora determina automáticamente qué proporción del CAPEX total
corresponde a **equipos calificables** (módulos, inversor, sistema FV):

```
Fracción equipos = (Sistema FV + Inversor + Catálogo) ÷ CAPEX total
```

Esta fracción es la base del **Art. 12 — Exclusión IVA** y del
**Art. 11 — Deducción renta** de la Ley 1715. Si es incorrecta, los
beneficios tributarios en Financiero quedan mal calculados.

---

### Conexión automática con otras páginas

| Dato exportado | Lo usa | Para qué |
|---|---|---|
| **CAPEX TOTAL** | 💰 Financiero | TIR, VPN, Payback, LCOE, Ley 1715 |
| **OPEX Anual** | 💰 Financiero | Flujo de caja anual a 25 años (reemplaza el slider paramétrico) |
| **Fracción equipos** | 💰 Financiero | Art. 11 y Art. 12 Ley 1715 |
| **CAPEX TOTAL** | 📄 Reporte PDF | Sección de costos y resumen ejecutivo |

En 💰 Financiero aparece un **toggle** que permite elegir entre:
- OPEX del presupuesto detallado (recomendado, valores reales ingresados aquí)
- OPEX paramétrico (slider % del CAPEX, para estimaciones rápidas)

---

### TRM y precios en USD

Todos los precios se ingresan en **USD**. La conversión a pesos colombianos
(millones de COP) se muestra automáticamente usando la TRM del campo superior.

> ⚠️ Error frecuente: ingresar precios en COP en lugar de USD. La alerta
> de USD/Wp > 5.0 es el primer síntoma. Si ocurre, divide todos los
> precios de esa sección por la TRM vigente.

---

## 12. Página 11 — Baterías y Balance ★

**Propósito:** Dimensionar el sistema de almacenamiento y calcular el balance energético
(autogeneración, autosuficiencia, excedentes a red).

### ★ E_ac corregida por bypass (nuevo)

Si bypass fue ejecutado en Página 5, la E_ac usada para el balance es la corregida.
Verás el banner:

```
⚡ Corrección bypass activa:
E_ac base = 91.000 kWh/año → pérdida bypass = 2.850 kWh/año → E_ac usada en el balance = 88.150 kWh/año (3.1% menos)
La autogeneración y el dimensionamiento de la batería se calculan con la producción real.
```

Esto evita **sobredimensionar la batería** basándose en una producción solar inexistente.

### Pasos

1. **Seleccionar la batería** del catálogo (o ingresar manualmente)
2. **Ingresar el perfil de consumo** del edificio (kWh/día o perfil horario)
3. **Ejecutar el balance energético**

**Resultados:**
- Tasa de autogeneración (%) — fracción del consumo cubierta por solar
- Tasa de autosuficiencia (%) — fracción de la producción solar autoconsumida
- Excedentes a red (kWh/año)
- Dimensionamiento recomendado de la batería (kWh y ciclos/año)

---

## 13. Página 10 — Reporte PDF ★

**Propósito:** Generar el reporte técnico descargable del proyecto.

### Secciones del reporte

| Sección | Contenido | Disponible si | Checkbox |
|---|---|---|---|
| 1. Proyecto | Datos generales, ubicación, sistema | Siempre | — |
| 2. Recurso Solar | POA anual, GHI, temperatura | Página 2 ejecutada | — |
| 3. Motor Óptico | Cascada IAM + Soiling + Térmico | Página 5b ejecutada | ✅ Motor Óptico |
| 4. Producción | E_ac, PR, Factor de Planta | Página 6 ejecutada | ✅ Producción |
| 4b. Diagnóstico | PR real vs esperado mes a mes | Datos reales ingresados | — |
| ★ 4c. Bypass Diodes | Pérdidas bypass, tabla mensual | Página 5 ejecutada | ✅ Bypass Diodes |
| ★★ 4d. Multi-Superficie | Desglose E_ac + bypass por superficie | Página 9 integrada | ✅ Multi-Superficie |
| ★ 5. Financiero | TIR, VPN, Payback + fuente E_ac | Página 7 ejecutada | ✅ Financiero |
| ★★ 5b. Costos Presupuesto | CAPEX, OPEX, KPIs de bancabilidad | Página 8 completada | ✅ Costos Presupuesto |
| 6. Balance | Autogeneración, batería | Página 11 ejecutada | ✅ Balance |
| 7. CO₂ | Emisiones evitadas, equivalencias | Página 12 ejecutada | ✅ CO₂ |

### ★ Sección 4c — Bypass Diodes (superficie única)

Cuando el modelo de bypass fue ejecutado en Página 5, el reporte incluye:
- Tabla con pérdida anual, % E_dc, horas bypass, E_ac corregida
- Fuente del FS (geométrico o combinado) y modo de cobertura temporal
- Semáforo de impacto: 🟢 < 2% · 🟡 2–5% · 🔴 > 5%
- Tabla mensual con pérdidas coloreadas (rojo si > 20 kWh ese mes)
- Referencia técnica: Deline et al. 2013

### ★★ Sección 4d — Multi-Superficie (nueva, #45)

Cuando Página 9 fue integrada, el reporte incluye una tabla por superficie con:
- E_ac base, pérdida bypass (%), horas bypass/año, E_ac con bypass
- Fila TOTAL SISTEMA con área total y E_ac total
- Nota con densidad del sistema (kWh/m²·año)

> Activar con checkbox **"🏗️ Incluir desglose Multi-Superficie"** en opciones del reporte.

### ★★ Sección 5b — Costos del Presupuesto (nueva, #8)

Cuando Página 8 fue completada, el reporte incluye:
- CAPEX directo (equipos + obra) y costos blandos en USD y M COP
- CAPEX total y KPIs: USD/m², USD/kWp, OPEX/CAPEX
- Fracción de equipos (base para beneficios Ley 1715)

> Activar con checkbox **"💼 Incluir Resumen de Costos del Presupuesto"**.

### ★ Sección 5 — Trazabilidad de E_ac (actualizado, #38)

La sección Financiero del reporte muestra qué fuente de E_ac se usó (en orden de prioridad):

```
# Caso 1: Sistema multi-superficie con bypass
E_ac usada: 33.929 kWh/año (multi-superficie — 2 superficies + bypass)

# Caso 2: Superficie única con bypass
E_ac usada: 88.150 kWh/año (corregida por bypass diodes)
Pérdida bypass descontada: 2.850 kWh/año (3.1% de E_ac base)

# Caso 3: Simulación estándar
E_ac usada: 91.000 kWh/año (simulación estándar superficie única)
```

Esto permite al cliente o a la UPME verificar que los números de TIR y Payback son **conservadores y realistas** (no optimistas).

### Cómo generar el PDF

1. Completa los campos "Nombre de la empresa" y "Nombre del proyecto"
2. Selecciona qué secciones incluir (checkboxes)
3. Clic en **"⬇️ Descargar reporte (.html → imprimir como PDF)"**
4. El archivo `.html` se abre en el navegador
5. Usa **Ctrl+P → Guardar como PDF** (escala recomendada: 85%, márgenes: mínimos)

---

## 14. Calculadora de Sombreado 3D

**URL:** bipv.innovacionquimica.com.co

**Propósito:** Generar el CSV de Factor de Sombreado para usar en Página 5 de la calculadora BIPV.

### Pasos en la Calculadora de Sombreado 3D

1. **Cargar el archivo EPW** del proyecto (el mismo que en Página 2)
2. **Dibujar los obstáculos** en el mapa 3D:
   - Edificios vecinos (altura, distancia, ancho)
   - Voladizos, antenas, tanques
3. **Configurar los puntos de análisis:**
   - Ubicar puntos sobre la fachada fotovoltaica
   - Asignar nombre de fachada (campo "Fachada")
4. **Seleccionar días críticos:**
   - Mínimo recomendado: solsticios (21 jun, 21 dic) + equinoccios (21 mar, 21 sep)
   - Para mayor precisión: un día representativo por mes (12 días)
5. **Cruzar máscara de sombras con el EPW:**
   - Botón "Cruzar Máscara + EPW"
   - Genera: FS_geometrico (obstáculos), FS_climatico (nubes), FS_combinado
6. **Exportar CSV:**
   - Botón "Exportar CSV"
   - El CSV incluye columnas: Hora, Mes, Dia, FS_geometrico, FS_climatico, FS_combinado, **Fachada** ← columna nueva

### Convención del CSV exportado

| Valor FS | Significado |
|---|---|
| 0.00 | Sin sombra en esa hora |
| 0.50 | 50% de la fachada sombreada |
| 1.00 | Sombra total (100%) |

> Esta es la convención **p_shade**: 0 = libre, 1 = sombreado.
> Es la convención correcta para cargar en Página 5.

---

## 15. Cadena completa — bypass y multi-superficie

### Flujo A — Superficie única con bypass diodes

```
bipv.innovacionquimica.com.co (Calculadora Sombreado 3D)
  └── Exportar CSV (con columna Fachada)
           │
           ↓
Página 5 — Mismatch
  ├── Cargar CSV · Detectar FS_geometrico / invertido / multi-fachada
  ├── [Si multi-fachada] → Seleccionar fachada del array
  ├── Cobertura temporal: Modo mensual (recomendado) o exacto
  ├── Configurar strings (N_series, N_parallel)
  └── ⚡ Calcular → kWh_bypass_anual, pct_bypass, horas_bypass
           │
           ↓
Página 6 — Producción
  └── Guarda: E_ac_anual_kWh_bypass ← usada aguas abajo
           │
    ┌──────┼──────┬──────────┐
    ↓      ↓      ↓          ↓
Pág.7   Pág.11  Pág.12     Pág.10
Financ. Baterías CO₂        PDF
TIR/VPN  Balance  Emisiones  §4c bypass
                             §5 E_ac label
```

### Flujo B — Multi-superficie (Página 9)

```
Página 9 — Vista 3D
  ├── ⚙️ Superficies BIPV: crear fachada, techo, pérgola, marquesina
  ├── ☀️ Calcular POA para cada superficie
  ├── [Opcional] Cargar CSV → FS por fachada en sub-tab FS
  ├── [Opcional] ⚡ Bypass por superficie (Sección 5)
  │      Para cada superficie:
  │        · POA propia × FS propio del CSV (filtrado por Fachada)
  │        · N_parallel = área / área_panel / N_series
  │        · simular_bypass_horario() → pérdida% por superficie
  │        · E_ac_bypass_i = E_ac_base_i × (1 - pérdida%)
  └── 🔗 Integrar al Financiero
       Escribe claves exclusivas (nunca sobreescriben las de Pág. 1):
         E_ac_anual_kWh_multisup ← suma E_ac por superficie
         poa_df_multisup         ← POA combinada ponderada
         area_total_multisup     ← suma de áreas
         multisup_desglose       ← lista por superficie
         multisup_activo = True
           │
    ┌──────┼──────┬──────────┐
    ↓      ↓      ↓          ↓
Pág.7   Pág.11  Pág.12     Pág.10
Financ. Baterías CO₂        PDF §4d
★ prioridad máxima en todas     multi-sup
```

### Prioridad global de E_ac

```
Página 7 / 11 / 12 / 10 leen:
  1. E_ac_anual_kWh_multisup  ← Página 9 integrada  ★ MÁX
  2. E_ac_anual_kWh_bypass    ← Página 5 ejecutada
  3. E_ac_anual_kWh           ← Página 6 base
```

---

## 16. Interpretación de resultados clave

### Performance Ratio (PR)

```
PR = Y_f / Y_r = (E_ac / P_STC) / (H_POA / G_STC)
```

- **PR > 100%:** Posible en Bogotá/Medellín (altitud, temperatura baja) — físicamente correcto
- **PR 80–100%:** Rango normal para fachadas BIPV bien diseñadas
- **PR 60–80%:** Revisar pérdidas ópticas, mismatch o sombreado
- **PR < 60%:** Problema real — inspección de campo recomendada

### E_ac según escenario del proyecto

| Escenario | E_ac usada | Para qué |
|---|---|---|
| Superficie única, sin sombras significativas | E_ac base | Proyectos con obstrucción < 5% |
| Superficie única, con sombras urbanas | E_ac_bypass | Fachadas en centros urbanos |
| Multi-superficie (techo + fachada + pérgola) | E_ac_multisup | Proyectos con orientaciones mixtas |
| Multi-superficie + bypass por superficie | E_ac_multisup (corregida) | Máxima precisión — BIPV urbano complejo |
| Certificación UPME / bancos | E_ac más conservadora disponible | Exigencia de estimación realista |

### Horas con bypass activo

- **< 200 h/año:** Sombra estacional leve (ej. solo invierno solar)
- **200–500 h/año:** Sombra moderada — bypass tiene impacto real
- **> 500 h/año:** Sombra severa — reconsiderar el layout del array

---

## 17. Preguntas frecuentes

**P: ¿El CSV de la Calculadora de Sombreado cubre las 8 760 horas del año?**
R: No. El CSV cubre solo los días críticos (~60–150 horas). El modo "mensual" replica
el patrón de cada día a todo el mes (cobertura ~25–40%). Para máxima precisión,
incluye un día representativo por cada mes (12 días en total), de modo que cada mes
tenga su propio perfil de sombra real.

**P: ¿Por qué mi TIR es diferente antes y después de ejecutar bypass?**
R: Con bypass activo, la Página 7 usa E_ac_bypass (menor que E_ac base). Menos
energía generada = menos ahorro = TIR levemente menor. La diferencia es proporcional
al % de pérdida bypass. Para proyectos con < 2% de pérdida, el impacto en TIR
es < 0.3 puntos porcentuales.

**P: El banner de "FS invertido" apareció. ¿Qué hago?**
R: Si el CSV viene de la Calculadora de Sombreado 3D de esta suite, NO está invertido
— el banner puede ser un falso positivo si el FS promedio real es muy alto (fachada
muy poco sombreada). Si el CSV viene de otra herramienta, activa el checkbox
"Invertir FS (1 − FS)" y verifica que la gráfica mensual tenga sentido.

**P: ¿Por qué hay meses sin dato de bypass?**
R: Si el CSV no tiene ningún día crítico de ese mes, la app asume FS=0 en todo el mes.
Solución: en la Calculadora de Sombreado, agrega al menos un día representativo
de los meses faltantes antes de exportar el CSV.

**P: ¿El PR puede ser mayor de 100%?**
R: Sí. En ciudades de alta altitud como Bogotá (2 600 m) o Medellín (1 500 m), la
temperatura ambiente baja hace que los módulos operen por debajo de 25°C muchas horas,
ganando eficiencia. Esto es físicamente correcto según IEC 61724.

**P: ¿Qué es el modo "Motor Óptico vs sin Motor Óptico"?**
R: El Motor Óptico aplica correcciones de IAM (reflexión angular), soiling (suciedad)
y temperatura confinada BIPV. Sin él, la app usa la POA bruta × factor de mismatch
global. El Motor Óptico da resultados más precisos para fachadas BIPV (diferencia
típica: 5–12% en la producción final).

**P: Cambié el tipo de instalación a "Granja FV" pero el tilt sigue en 90°. ¿Por qué?**
R: El tilt se resetea al valor del nuevo tipo solo si aún no has ajustado manualmente
el slider en Página 2 en esta sesión. Si ya lo moviste antes del cambio de tipo, la
app respeta tu selección manual para no sobreescribir trabajo hecho. Solución: ve a
Página 2 y ajusta el slider manualmente al valor deseado (15° para Granja FV).

**P: Aparece la alerta de densidad fuera de rango pero estoy seguro de que mi valor es correcto. ¿Puedo continuar?**
R: Sí, la alerta es informativa y no bloquea ningún cálculo. En instalaciones especiales
(fachadas con módulos de alta densidad > 200 W/m² o pérgolas de baja densidad < 60 W/m²)
los rangos pueden diferir de los típicos. La alerta te pide verificar — si el valor
es intencional, simplemente ignórala y continúa.

**P: ¿Qué pasa si selecciono "Fachada BIPV" pero mi edificio tiene la fachada inclinada a 75°?**
R: El tilt pre-cargado es 90° (fachada vertical estándar), pero puedes moverlo a 75°
libremente en Página 2. El slider acepta cualquier valor entre 0° y 90°. La app
calculará la POA correctamente para el ángulo que ingreses, independientemente del
tipo de instalación seleccionado.

**P: ¿La alerta de PR considera las pérdidas del Motor Óptico?**
R: No. La alerta de PR en Página 1 compara tu entrada con el rango típico global del
tipo de instalación, que ya incorpora las pérdidas ópticas promedio (IAM, soiling,
temperatura confinada). El PR que ingresas en Página 1 es el PR total del sistema
(incluyendo todas las pérdidas). Si ejecutas el Motor Óptico en Página 5b, las
correcciones ópticas se aplican sobre la POA y el PR resultante se recalcula en
Página 6 con mayor precisión.

**P: ¿Cómo funciona la Página 9 (Vista 3D) con un proyecto de una sola superficie?**
R: Para proyectos de una sola superficie (ej. solo fachada sur), la Página 9 no es
necesaria. El flujo normal (Páginas 1→2→4→5→6→7) es suficiente. La Página 9 agrega
valor cuando hay 2 o más superficies con distintas orientaciones que deben combinarse
en un solo sistema.

**P: Si activo multi-superficie en Página 9, ¿se pierden los resultados de la Página 6?**
R: No. Las claves de multi-superficie (`E_ac_anual_kWh_multisup`, `poa_df_multisup`)
son **exclusivas** y nunca sobreescriben `E_ac_anual_kWh` ni `poa_df`. Al desactivar
el modo multi-superficie con el botón "Desactivar", Financiero vuelve a usar la E_ac
de Página 6 automáticamente.

**P: ¿Cómo calcula el N_parallel para cada superficie en el bypass por superficie?**
R: La app divide el número estimado de módulos de cada superficie
(`N_panels = área_m² / área_panel`) por el N_series configurado:
`N_parallel = max(1, round(N_panels / N_series))`. El N_series es el mismo
para todas las superficies (se asume un único tipo de string); el N_parallel
varía proporcionalmente al área de cada superficie.

**P: Tengo datos de PR de 3 años. ¿Por qué la degradación calculada es negativa (mejora)?**
R: Una pendiente positiva (PR creciente) puede reflejar mejora real en limpieza o
mantenimiento entre años, no que los módulos "mejoren". Si ves PR_corr_T subiendo,
revisa si cambió el protocolo de limpieza. La app indica "PR estable o en mejora" y
no actualiza la tasa de degradación en Financiero si la pendiente es positiva.

**P: ¿Puedo usar el bypass por superficie si el CSV no tiene columna "Fachada"?**
R: Sí. Si el CSV no tiene columna `Fachada`, la app usa el promedio de todos los
puntos del CSV como FS para cada superficie. Esto es menos preciso que tener una
columna `Fachada`, pero es funcional. Para mayor precisión, asigna un nombre de
fachada a cada punto de análisis en la Calculadora de Sombreado 3D antes de exportar.

---

*Manual actualizado el 31 de julio de 2026*
*Novedades de esta versión: Vista 3D Multi-Superficie (Pág. 9) completa · Bypass por superficie (#46) · Degradación desde historial PR (#28) · Reporte PDF con desglose multi-sup (#45), costos presupuesto (#8) y E_ac multi-sup (#38)*
*Calculadora BIPV — Innovación Química / SolTech Energy*
*Repositorio: github.com/ventas108/calculadora-bipv*
