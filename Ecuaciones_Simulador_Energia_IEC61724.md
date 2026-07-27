# Ecuaciones del Simulador de Energía con Datos PVWatts Satelital y Optimización según IEC 61724

**Autor:** Manus AI  
**Fecha:** 16 de mayo de 2026  
**Proyecto:** Solar Shading Calculator — Módulo Simulador de Energía  

---

## 1. Introducción

El presente documento describe de forma exhaustiva las ecuaciones que ejecuta el botón **"Simulador Energía"** cuando recibe datos provenientes del **Heatmap PVWatts Satelital (NREL)**. Se excluyen deliberadamente los cálculos financieros y de costos. El análisis se estructura en tres bloques: (a) el flujo de datos desde PVWatts hasta el Simulador, (b) las ecuaciones internas del motor de producción, y (c) las métricas IEC 61724 que el sistema calcula. Finalmente, se proponen optimizaciones concretas alineadas con la norma **IEC 61724-1:2021** [1].

---

## 2. Flujo de Datos: PVWatts Satelital → Prospector Solar → Simulador

Cuando el usuario genera un heatmap con PVWatts y selecciona un punto, el sistema ejecuta dos etapas intermedias antes de que los datos lleguen al Simulador de Energía.

### 2.1 Etapa 1: Consulta a la API PVWatts v8 (NREL)

El proxy backend consulta la API PVWatts v8 de NREL [2] con los parámetros del punto seleccionado. La respuesta incluye datos mensuales de producción AC, DC, irradiación POA, temperatura ambiente, temperatura de celda y velocidad del viento. Adicionalmente, se realiza una segunda consulta con **tilt = 0°** para obtener la **irradiación horizontal global (GHI)** real, ya que `solrad_annual` con tilt > 0 devuelve irradiación en el plano inclinado (POA), no GHI.

| Variable PVWatts | Descripción | Unidad |
|---|---|---|
| `solrad_monthly[i]` (tilt=0) | Irradiación solar diaria promedio en plano horizontal | kWh/m²/día |
| `solrad_annual` (tilt=0) × 365 | GHI anual real | kWh/m²/año |
| `tamb[i]` | Temperatura ambiente promedio mensual | °C |
| `ac_monthly[i]` | Producción AC mensual | kWh |
| `dc_monthly[i]` | Producción DC mensual | kWh |
| `poa_monthly[i]` | Irradiación POA mensual | kWh/m² |

### 2.2 Etapa 2: Prospector Solar — Modelo Mulcue-Llanos

Con el GHI anual obtenido de PVWatts (tilt=0), el SolarProspector ejecuta el modelo **Mulcue-Llanos** [3] para calcular el Performance Ratio estimado y la producción esperada. Este modelo utiliza las siguientes ecuaciones:

**Performance Ratio máximo (PR_max):**

> PR_max = K_sist × (1 + γ × (1.12 × T_a − 10))

Donde **K_sist = 0.82** es el factor de sistema para equipos óptimos, **γ** es el coeficiente de temperatura del módulo en forma decimal (por ejemplo, −0.0036 para −0.36 %/°C), y **T_a** es la temperatura ambiente promedio en °C.

**Performance Ratio corregido (PR_C):**

> PR_C = PR_max + 0.0006 × T_a − 0.017

**Temperatura de celda (modelo NOCT — IEC 61215):**

> T_cell = T_amb + (NOCT − 20) × (G / 800)

Donde **NOCT** es la temperatura nominal de operación de la celda (típicamente 43–47 °C) y **G** es la irradiancia promedio durante horas de sol (por defecto 800 W/m²).

**Potencia esperada del módulo (P_exp):**

> P_exp = P_nom × [1 + γ × (T_cell − 21)] × (G / 1000)

Nótese que el modelo Mulcue-Llanos usa **T_ref = 21 °C** como temperatura de referencia, a diferencia del estándar STC que usa 25 °C. El factor **(G / 1000)** ajusta la potencia por irradiancia respecto a las condiciones estándar de prueba (STC = 1000 W/m²).

**Producción energética anual estimada:**

> G_a(α,β) = GHI_diario × FI × FS  
> HSP_total = G_a(α,β) × 365  
> E_PV = HSP_total × P_pico(kW) × PR_C

Donde **FI** es el factor de irradiación regional (0.88–1.00 según la región colombiana), **FS** es el factor de sombreado (0–1), y **P_pico** es la potencia pico instalada en kW. Estos datos se empaquetan como `ProspectorToSimulatorData` con el campo `source = 'heatmap_pvwatts'` y se envían al Simulador.

### 2.3 Etapa 3: Datos que recibe el Simulador

El Simulador recibe del Prospector los siguientes parámetros pre-llenados:

| Parámetro | Origen | Uso en el Simulador |
|---|---|---|
| GHI anual (kWh/m²/año) | PVWatts tilt=0 | Referencia informativa en el banner |
| PR Mulcue-Llanos (0–1) | Modelo Mulcue-Llanos | Comparación con PR IEC 61724 |
| Región colombiana | Detección geográfica | Selección de FI regional |
| T. ambiente promedio (°C) | PVWatts `tamb` promedio | Referencia en banner |
| T. celda estimada (°C) | Modelo NOCT | Referencia en banner |
| Pérdida por T° (%) | Factor de pérdida térmica | Referencia en banner |
| Estimación Prospector (kWh/año) | Modelo Mulcue-Llanos | Comparación con simulación |
| Panel seleccionado (ID) | Catálogo de paneles | Pre-llena especificaciones |
| Cantidad de módulos | Configuración del Prospector | Pre-llena cantidad |
| Inclinación recomendada (°) | Tabla regional FI | Pre-llena tilt |

Adicionalmente, el Simulador recibe **weatherData** (datos climáticos horarios del archivo EPW de la ciudad seleccionada) y **poaData** (irradiación POA mensual calculada con el modelo Liu-Jordan o Perez a partir del EPW). Cuando no hay EPW disponible, se genera weatherData sintético a partir de los datos mensuales de PVWatts.

---

## 3. Ecuaciones del Motor de Producción del Simulador

El motor de producción (`calculateAnnualProduction`) procesa los datos mes a mes y acumula los resultados anuales. A continuación se describen todas las ecuaciones en el orden exacto de ejecución.

### 3.1 Temperatura de Celda (modelo NOCT extendido con viento)

El Simulador utiliza un modelo NOCT más completo que el del Prospector, incorporando el efecto del viento y la eficiencia del panel:

> T_cell = T_amb + (NOCT − 20) × (G_POA / 800) × (1 − η_real) × f_viento

Donde:

| Símbolo | Descripción | Unidad |
|---|---|---|
| T_amb | Temperatura ambiente promedio mensual | °C |
| NOCT | Temperatura nominal de operación de la celda | °C |
| G_POA | Irradiancia POA después de sombreado | W/m² |
| η_real | Eficiencia real del panel (decimal, ej: 0.15) | — |
| f_viento | Factor de enfriamiento por viento = 1 / (1 + 0.05 × v) | — |
| v | Velocidad del viento promedio mensual | m/s |

Este modelo es más preciso que el NOCT simple del Prospector porque considera que: (a) parte de la radiación se convierte en electricidad y no en calor (factor `1 − η_real`), y (b) el viento enfría el panel (factor `f_viento`). La referencia es el modelo térmico de Sandia [4].

### 3.2 Eficiencia del Panel Ajustada por Temperatura

La eficiencia del panel se degrada linealmente con la temperatura respecto a las condiciones STC (25 °C):

> η(T) = η_STC × (1 + γ × (T_cell − 25))

Donde **η_STC** es la eficiencia nominal del panel en condiciones estándar de prueba (%) y **γ** es el coeficiente de temperatura de potencia máxima (%/°C, valor negativo). Por ejemplo, para un panel con η_STC = 22.5% y γ = −0.0026/°C, a T_cell = 55 °C la eficiencia baja a 22.5 × (1 + (−0.0026) × (55 − 25)) = 22.5 × 0.922 = **20.7%**.

### 3.3 Potencia DC Generada

La potencia DC instantánea promedio del arreglo se calcula como:

> P_DC = G_POA × A_total × η(T) / 100

Donde **A_total = A_panel × N_paneles** es el área total del arreglo en m² y **η(T)** es la eficiencia ajustada por temperatura en %. La irradiancia **G_POA** ya incluye el efecto del sombreado (G_POA = G_POA_raw × FS_mensual).

### 3.4 Cadena de Pérdidas del Sistema (DC → AC)

La potencia AC se obtiene aplicando secuencialmente las pérdidas del sistema sobre la potencia DC:

> P_AC = P_DC × (1 − L_DC) × η_inv × (1 − L_AC) × (1 − L_trafo) × (1 − L_mismatch) × (1 − L_suciedad) × (1 − L_sombra) × (1 − L_disp)

| Pérdida | Símbolo | Valor típico | Descripción |
|---|---|---|---|
| Cableado DC | L_DC | 2.0% | Pérdidas óhmicas en cables DC |
| Eficiencia inversor | η_inv | 96.5% | Conversión DC→AC |
| Cableado AC | L_AC | 1.0% | Pérdidas óhmicas en cables AC |
| Transformador | L_trafo | 0.5% | Pérdidas en transformador (si aplica) |
| Desajuste (mismatch) | L_mismatch | 2.0% | Diferencias entre módulos |
| Suciedad (soiling) | L_suciedad | 3.0% | Polvo, hojas, excrementos |
| Sombreado | L_sombra | Variable | Factor de sombreado mensual |
| Disponibilidad | L_disp | 1.5% | Tiempo fuera de servicio |

Estos valores por defecto provienen de la configuración de instalación seleccionada (techo inclinado, techo plano, pérgola, etc.) y pueden ser ajustados manualmente por el usuario.

### 3.5 Energía Mensual (kWh)

La energía mensual se calcula asumiendo que la potencia promedio es constante durante todas las horas del mes:

> E_DC_mes = P_DC × horas_mes / 1000   [kWh]  
> E_AC_mes = P_AC × horas_mes / 1000   [kWh]

Donde **horas_mes = días_mes × 24**. Esta es una simplificación significativa: se usa la irradiancia POA promedio mensual como si fuera constante las 24 horas, lo cual sobreestima la producción porque en realidad solo hay irradiancia durante las horas de sol (~5–6 horas pico equivalentes por día). Sin embargo, dado que los datos POA de entrada ya representan promedios mensuales en W/m² calculados a partir de datos horarios del EPW (o de PVWatts), el resultado es correcto porque el promedio mensual ya incorpora las horas nocturnas (irradiancia = 0).

### 3.6 Energía de Referencia STC

Para el cálculo de las métricas IEC 61724, se necesita la energía que produciría el sistema si operara siempre a eficiencia nominal STC:

> E_ref_mes = (G_POA_raw / G_ref) × P_nom_total(kW) × horas_mes   [kWh]

Donde **G_POA_raw** es la irradiancia POA antes de sombreado (W/m²), **G_ref = 1000 W/m²** es la irradiancia de referencia STC, y **P_nom_total** es la potencia nominal total del arreglo en kW.

---

## 4. Métricas IEC 61724 Calculadas por el Simulador

El Simulador implementa las métricas definidas en la norma IEC 61724-1:2021 [1]. A continuación se describe cada una con su ecuación exacta.

### 4.1 Reference Yield (Y_r)

El Reference Yield representa las horas equivalentes de sol a irradiancia STC:

> Y_r = H_POA / (G_ref / 1000)

Donde **H_POA = Σ(G_POA_raw_i × días_i × 24) / 1000** es la irradiación POA total anual en kWh/m², y **G_ref = 1000 W/m² = 1 kW/m²**. El resultado se expresa en **horas equivalentes** (h).

### 4.2 Final Yield (Y_f)

El Final Yield es la producción AC específica del sistema:

> Y_f = E_AC_total / P_nom_total(kW)   [kWh/kWp]

Este valor es equivalente al **Specific Yield** y se expresa en kWh/kWp/año.

### 4.3 Array Yield (Y_a)

El Array Yield es la producción DC específica del arreglo:

> Y_a = E_DC_total / P_nom_total(kW)   [kWh/kWp]

### 4.4 Capture Losses (L_c)

Las pérdidas de captura representan las pérdidas en el arreglo (temperatura, sombreado, suciedad, mismatch):

> L_c = Y_r − Y_a   [h]

### 4.5 System Losses (L_s)

Las pérdidas del sistema representan las pérdidas en la conversión DC→AC (inversor, cableado, transformador):

> L_s = Y_a − Y_f   [h]

### 4.6 Performance Ratio (PR)

El PR estándar IEC 61724 se calcula como:

> PR = Y_f / Y_r = E_AC_total / (H_POA × P_nom_total / G_ref)

Un PR de 0.80 significa que el sistema entrega el 80% de la energía que produciría si operara siempre a eficiencia STC. Valores típicos para sistemas bien diseñados están entre 0.75 y 0.85 [1] [5].

### 4.7 PR Corregido por Temperatura (PR_T) — IEC 61724-1:2021

El PR estándar es sensible a la temperatura ambiente: en climas cálidos el PR baja porque los módulos operan a mayor temperatura. La norma IEC 61724-1:2021 define el PR corregido por temperatura para eliminar esta dependencia climática [1] [6]:

> PR_T = PR / (1 + γ × (T_cell_avg_ponderada − 25))

Donde **T_cell_avg_ponderada** es la temperatura de celda promedio ponderada por irradiancia:

> T_cell_avg_ponderada = Σ(T_cell_i × G_POA_raw_i × horas_i) / Σ(G_POA_raw_i × horas_i)

Y **γ** es el coeficiente de temperatura en forma decimal (%/°C). El PR_T normaliza el rendimiento a 25 °C, permitiendo comparar sistemas en diferentes climas.

**Nota importante:** La implementación actual del Simulador usa una fórmula simplificada para PR_T. La norma IEC 61724-1:2021 define una versión más rigurosa que opera paso a paso temporal (ver Sección 5.2).

### 4.8 BOS Efficiency (η_BOS)

La eficiencia del Balance of System mide las pérdidas entre DC y AC:

> η_BOS = E_AC_total / E_DC_total

### 4.9 Capacity Factor (CF)

El factor de capacidad indica qué fracción del tiempo teórico máximo opera el sistema:

> CF = E_AC_total / (P_nom_total(kW) × 8760) × 100   [%]

### 4.10 Pérdidas Ponderadas por Energía

Las pérdidas individuales (temperatura, cableado DC, inversor, etc.) se ponderan por la energía de referencia mensual para obtener promedios anuales representativos:

> L_tipo_anual = Σ(L_tipo_i × E_ref_i) / Σ(E_ref_i)

Esto asegura que los meses con mayor producción tengan mayor peso en el promedio de pérdidas.

---

## 5. Optimizaciones Propuestas según IEC 61724-1:2021

A continuación se presentan las optimizaciones recomendadas para alinear completamente el Simulador con la norma IEC 61724-1:2021, organizadas por prioridad de impacto.

### 5.1 Implementar PR_T Paso a Paso (Alta Prioridad)

**Problema actual:** El Simulador calcula PR_T dividiendo el PR anual por un factor de corrección global basado en la temperatura promedio ponderada. Esto es una aproximación.

**Solución IEC 61724-1:2021:** La norma define PR_T como una suma paso a paso [1] [6]:

> PR_T = Σ(E_j) / Σ(P_nom × G_j / G_ref × [1 + γ × (T_mod_j − 25)])

Donde cada **j** es un paso temporal (idealmente horario, mínimo mensual). La diferencia es que el denominador se corrige por temperatura en cada paso, no como promedio global. Esto es más preciso porque la relación entre temperatura y producción no es lineal cuando se promedia.

**Implementación sugerida:** Modificar `calculateAnnualProduction` para acumular el denominador corregido mes a mes:

```
denominador_PR_T = Σ_i [ P_nom(kW) × (G_POA_raw_i / G_ref) × horas_i × (1 + γ × (T_cell_i − 25)) ]
PR_T = E_AC_total / denominador_PR_T
```

### 5.2 Incorporar el Energy Performance Index — EPI (Alta Prioridad)

**Problema actual:** El Simulador no calcula el EPI, que es la métrica más avanzada de IEC 61724-1:2021.

**Definición IEC 61724-1:2021:**

> EPI = Y_medido / Y_esperado

Donde **Y_esperado** proviene de un modelo de simulación PV detallado. En el contexto de este Simulador, **Y_esperado** podría ser la producción calculada por PVWatts (que ya está disponible en `pvwattsData.annualAC_kWh`) y **Y_medido** sería la producción calculada por el motor interno del Simulador.

**Ventajas del EPI sobre el PR** [1]:

| Característica | PR | EPI |
|---|---|---|
| Independencia climática | No (sensible a T°) | Sí (normalizado por modelo) |
| Resolución temporal | Mensual/anual | Hasta 15 minutos |
| Identificación de pérdidas | Agregada | Por categoría |
| Comparación entre sitios | Limitada | Directa |

**Implementación sugerida:** Agregar al objeto `IEC61724Metrics`:

```typescript
epi: pvwattsData 
  ? production.totalACEnergy / pvwattsData.annualAC_kWh 
  : null
```

### 5.3 Usar Datos Horarios en Lugar de Promedios Mensuales (Media Prioridad)

**Problema actual:** El motor de producción opera con promedios mensuales de POA, temperatura y viento. Esto introduce errores porque:

- La relación T_cell = f(G_POA) no es lineal.
- Las pérdidas por temperatura son mayores en las horas de máxima irradiancia.
- El promedio mensual suaviza picos de producción y pérdidas.

**Solución IEC 61724:** La norma recomienda resolución horaria o sub-horaria para Class A monitoring [1]. Dado que los datos EPW ya contienen 8760 registros horarios, el Simulador podría ejecutar el cálculo hora a hora y sumar los resultados mensuales.

**Impacto estimado:** La diferencia entre cálculo horario y mensual puede ser del 2–5% en la producción anual, dependiendo de la variabilidad climática del sitio [5].

### 5.4 Separar Pérdidas de Captura por Categoría (Media Prioridad)

**Problema actual:** Las Capture Losses (L_c = Y_r − Y_a) se reportan como un valor agregado. La norma IEC 61724 recomienda descomponer L_c en sus componentes:

> L_c = L_c_temp + L_c_sombra + L_c_suciedad + L_c_mismatch + L_c_cableadoDC

**Implementación sugerida:** El Simulador ya calcula cada pérdida individualmente. Solo falta expresarlas en las mismas unidades que L_c (horas equivalentes) en lugar de porcentajes:

```
L_c_temp = Y_r × (pérdida_temp% / 100)
L_c_sombra = Y_r × (pérdida_sombra% / 100)
...
```

### 5.5 Implementar Degradación Anual del Módulo (Baja Prioridad)

**Problema actual:** El Simulador calcula la producción del año 1 sin considerar la degradación anual del módulo (típicamente 0.4–0.7%/año para cristalino).

**Solución:** Agregar un parámetro `yearsFromInstall` (que ya existe en el estado del componente) y aplicar:

> η_degradada = η_STC × (1 − δ)^n

Donde **δ** es la tasa de degradación anual (%) y **n** es el número de años desde la instalación.

### 5.6 Validar con Datos PVWatts como Benchmark (Baja Prioridad)

**Propuesta:** Dado que el Simulador ya recibe datos PVWatts completos (AC mensual, DC mensual, POA mensual), se podría agregar una tabla comparativa automática:

| Mes | Simulador AC (kWh) | PVWatts AC (kWh) | Δ (%) | PVGIS AC (kWh) | Δ (%) |
|---|---|---|---|---|---|
| Ene | ... | ... | ... | ... | ... |
| ... | ... | ... | ... | ... | ... |
| **Total** | ... | ... | ... | ... | ... |

Esto permitiría al usuario validar la coherencia entre las tres fuentes y detectar discrepancias significativas.

---

## 6. Resumen de Ecuaciones Clave

La siguiente tabla resume todas las ecuaciones del motor de producción en orden de ejecución:

| # | Ecuación | Referencia |
|---|---|---|
| 1 | T_cell = T_amb + (NOCT − 20) × (G_POA / 800) × (1 − η) × f_viento | IEC 61215 / Sandia |
| 2 | η(T) = η_STC × (1 + γ × (T_cell − 25)) | IEC 61215 |
| 3 | P_DC = G_POA × A_total × η(T) / 100 | Modelo de área |
| 4 | P_AC = P_DC × Π(1 − L_i) × η_inv | Cadena de pérdidas |
| 5 | E_mes = P × horas_mes / 1000 | Integración temporal |
| 6 | Y_r = H_POA / G_ref | IEC 61724 |
| 7 | Y_f = E_AC / P_nom | IEC 61724 |
| 8 | Y_a = E_DC / P_nom | IEC 61724 |
| 9 | PR = Y_f / Y_r | IEC 61724 |
| 10 | PR_T = PR / (1 + γ × (T_avg − 25)) | IEC 61724-1:2021 |
| 11 | CF = E_AC / (P_nom × 8760) | Estándar industria |
| 12 | η_BOS = E_AC / E_DC | IEC 61724 |

---

## 7. Referencias

[1]: https://kb.solargis.com/docs/pv-performance-indicators "IEC 61724-1:2021 — PV Performance Indicators (Solargis Knowledge Base)"

[2]: https://developer.nrel.gov/docs/solar/pvwatts/v8/ "PVWatts v8 API Documentation (NREL)"

[3]: Mulcue-Nieto, L.F. — Modelo de estimación de Performance Ratio para sistemas fotovoltaicos en Colombia. Universidad Nacional de Colombia.

[4]: https://pvpmc.sandia.gov/modeling-guide/5-ac-system-output/pv-performance-metrics/performance-ratio/ "Performance Ratio — Sandia PV Performance Modeling Collaborative (PVPMC)"

[5]: https://www.pvsyst.com/help-pvsyst7/performance_ratio.htm "Performance Ratio — PVsyst Documentation"

[6]: https://docs.nrel.gov/docs/fy13osti/57991.pdf "Weather-Corrected Performance Ratio — NREL Technical Report (Dierauf et al., 2013)"
