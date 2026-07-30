# Manual de Usuario — Calculadora BIPV
### Innovación Química / SolTech Energy
**Versión:** Julio 2026 | **URL:** calc.innovacionquimica.com.co

---

## Tabla de contenido

1. [Descripción general](#1-descripción-general)
2. [Flujo de trabajo recomendado](#2-flujo-de-trabajo-recomendado)
3. [Página 1 — Proyecto](#3-página-1--proyecto)
4. [Página 2 — Recurso Solar](#4-página-2--recurso-solar)
5. [Página 3 — Motor IV](#5-página-3--motor-iv)
6. [Página 4 — Dimensionamiento](#6-página-4--dimensionamiento)
7. [Página 5b — Motor Óptico](#7-página-5b--motor-óptico)
8. [Página 5 — Mismatch y Bypass Diodes ★ NUEVO](#8-página-5--mismatch-y-bypass-diodes-)
9. [Página 6 — Producción Anual](#9-página-6--producción-anual)
10. [Página 7 — Análisis Financiero ★ ACTUALIZADO](#10-página-7--análisis-financiero-)
11. [Página 8 — Presupuesto](#11-página-8--presupuesto)
12. [Página 11 — Baterías y Balance ★ ACTUALIZADO](#12-página-11--baterías-y-balance-)
13. [Página 10 — Reporte PDF ★ ACTUALIZADO](#13-página-10--reporte-pdf-)
14. [Calculadora de Sombreado 3D](#14-calculadora-de-sombreado-3d)
15. [Cadena completa de bypass diodes](#15-cadena-completa-de-bypass-diodes)
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
    → 7 Financiero → 8 Presupuesto → 11 Baterías → 10 Reporte PDF
```

**Páginas obligatorias:** 1, 2, 4, 6, 7, 10
**Páginas opcionales pero recomendadas para BIPV urbano:** 3, 5b, 5, 11

> ⚠️ **Regla de datos:** Cada página guarda sus resultados en memoria de sesión
> (`session_state`). Si recargas el navegador, todos los datos se pierden y
> debes ejecutar el flujo desde el principio.

---

## 3. Página 1 — Proyecto

**Propósito:** Registrar los datos básicos del proyecto.

**Campos obligatorios:**
- Nombre del proyecto y empresa cliente
- Ciudad (selección desde lista; define el TMY por defecto)
- Tipo de edificación y uso

**Campos opcionales:**
- Descripción del sistema BIPV
- Datos del contacto

**Resultado:** Los datos del proyecto aparecen en el encabezado del Reporte PDF.

---

## 4. Página 2 — Recurso Solar

**Propósito:** Cargar el archivo climático TMY y calcular la irradiancia sobre la fachada (POA).

### Pasos

1. **Cargar archivo EPW:**
   - Descarga el EPW de [https://energyplus.net/weather](https://energyplus.net/weather)
   - Busca la ciudad más cercana al proyecto
   - Arrastra el archivo `.epw` al uploader

2. **Configurar la fachada:**
   - **Orientación (azimuth):** 0° = Norte, 90° = Este, 180° = Sur, 270° = Oeste
   - **Inclinación (tilt):** 90° = fachada vertical (caso típico BIPV), 0° = horizontal
   - **Área de la fachada (m²):** área total de la fachada donde van los paneles

3. **Ejecutar cálculo:**
   - Clic en **"Calcular POA"**
   - La app calcula la irradiancia en el plano de la fachada hora a hora (8 760 horas)

**Resultados:**
- POA bruta anual (kWh/m²/año)
- Heatmap de irradiancia horaria (meses × horas del día)
- Diagrama solar con la trayectoria del sol sobre la fachada

> **Nota timezone:** El diagrama solar usa UTC. Para Colombia (UTC-5), la hora solar
> de mediodía aparece a las 17:00 UTC en el diagrama.

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

## 9. Página 6 — Producción Anual

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

---

## 10. Página 7 — Análisis Financiero ★

**Propósito:** Calcular TIR, VPN, Payback y LCOE del proyecto bajo la Ley 1715/2014.

### ★ E_ac corregida por bypass (nuevo)

Si ejecutaste el modelo de bypass en Página 5, la app usa **automáticamente**
la E_ac corregida como base del análisis. Verás el banner:

```
⚡ Corrección bypass diodes aplicada:
E_ac base = 91.000 kWh/año → pérdida bypass = 2.850 kWh/año → E_ac neta = 88.150 kWh/año (3.1% menos)
TIR y Payback calculados con la producción real corregida.
```

Si bypass NO fue ejecutado, aparece una nota sugiriendo ejecutar Página 5 para
un análisis más realista.

### Pasos

1. **Sección 1 — CAPEX:** Ingresa costos de módulos, inversor, estructura, instalación
2. **Sección 2 — Parámetros financieros:**
   - Tarifa energía (COP/kWh)
   - TRM (COP/USD)
   - Tasa de descuento (%)
   - Horizonte de análisis (años)
   - Degradación anual del sistema (%)
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

## 11. Página 8 — Presupuesto

**Propósito:** Generar una cotización detallada del sistema con costos de equipos y mano de obra.

Los precios se leen automáticamente desde el archivo Excel del servidor
(`inversores_catalogo.xlsx`). Si ves `$0` en alguna línea, verifica que la
hoja `Presupuesto` del Excel tenga los datos correctos.

El presupuesto se puede exportar como PDF imprimible desde Página 10.

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

| Sección | Contenido | Disponible si |
|---|---|---|
| 1. Proyecto | Datos generales, ubicación, sistema | Siempre |
| 2. Recurso Solar | POA anual, heatmap | Página 2 ejecutada |
| 3. Motor Óptico | Cascada IAM + Soiling + Térmico | Página 5b ejecutada |
| 4. Producción | E_ac, PR, Factor de Planta | Página 6 ejecutada |
| 4b. Diagnóstico | PR real vs esperado mes a mes | Datos reales ingresados |
| ★ 4c. Bypass Diodes | Pérdidas bypass, tabla mensual | Página 5 ejecutada |
| ★ 5. Financiero | TIR, VPN, Payback + fuente E_ac | Página 7 ejecutada |
| 6. Balance | Autogeneración, batería | Página 11 ejecutada |

### ★ Sección 4c — Bypass Diodes (nueva)

Cuando el modelo de bypass fue ejecutado, el reporte incluye:
- Tabla con pérdida anual, % E_dc, horas bypass, E_ac corregida
- Fuente del FS (geométrico o combinado) y modo de cobertura temporal
- Semáforo de impacto: 🟢 < 2% · 🟡 2–5% · 🔴 > 5%
- Tabla mensual con pérdidas coloreadas (rojo si > 20 kWh ese mes)
- Referencia técnica: Deline et al. 2013

### ★ Sección 5 — Trazabilidad de E_ac (nuevo)

La sección Financiero del reporte ahora muestra explícitamente qué E_ac se usó:

```
E_ac usada en el análisis:  88.150 kWh/año (corregida por bypass)
Pérdida bypass descontada:  2.850 kWh/año (3.1% de E_ac base)
```

Esto permite al cliente o a la UPME verificar que los números de TIR y Payback
son **conservadores y realistas** (no optimistas).

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

## 15. Cadena completa de bypass diodes

Este es el flujo completo cuando se usa el modelo de bypass:

```
bipv.innovacionquimica.com.co (Calculadora Sombreado 3D)
  │
  ├── Dibujar obstáculos 3D
  ├── Cruzar con EPW (días críticos)
  └── Exportar CSV (con columna Fachada)
           │
           ↓
Calculadora BIPV — Página 5 (Mismatch)
  │
  ├── Cargar CSV
  ├── Detectar: FS_geometrico ✓ | FS invertido ✓ | Multi-fachada ✓
  ├── [Si multi-fachada] → Seleccionar fachada del array
  ├── Cobertura temporal: Modo mensual (recomendado) o exacto
  ├── Configurar strings (N_series, N_parallel)
  └── Ejecutar simulación → kWh_bypass_anual, pct_bypass, horas_bypass
           │
           ↓
Página 6 — Producción
  └── Balance energético con barra "Bypass diodes"
      Guarda: E_ac_anual_kWh_bypass en memoria
           │
    ┌──────┴──────┐
    ↓             ↓
Página 7        Página 11
Financiero      Baterías
TIR/VPN con     Dimensionamiento con
E_ac_bypass     E_ac_bypass
           │
           ↓
Página 10 — Reporte PDF
  ├── Sección 4c: Pérdidas bypass (tabla mensual)
  └── Sección 5: "E_ac usada: X kWh/año (corregida por bypass)"
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

### E_ac vs E_ac_bypass

| Escenario | E_ac usada | Para qué |
|---|---|---|
| Sin sombras significativas | E_ac base | Proyectos con obstrucción < 5% |
| Con sombras urbanas | E_ac_bypass | Fachadas en centros urbanos |
| Certificación UPME | E_ac_bypass | Estimación conservadora requerida |

### Horas con bypass activo

- **< 200 h/año:** Sombra estacional leve (ej. solo invierno solar)
- **200–500 h/año:** Sombra moderada — bypass tiene impacto real
- **> 500 h/año:** Sombra severa — reconsiderar el layout del array

---

## 17. Preguntas frecuentes

**P: ¿El CSV de la Calculadora de Sombreado cubre las 8 760 horas del año?**
R: No. El CSV cubre solo los días críticos seleccionados (~60–150 horas). El modo
"mensual" replica el patrón de cada día crítico a todos los días del mismo mes,
elevando la cobertura al 25–40% del año. Los meses sin día crítico asumen FS=0.
Para máxima precisión, incluye un día representativo por cada mes del año.

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

---

*Manual generado el 30 de julio de 2026*
*Calculadora BIPV — Innovación Química / SolTech Energy*
*Repositorio: github.com/ventas108/calculadora-bipv*
