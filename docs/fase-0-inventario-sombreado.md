# Fase 0 — Inventario y línea base del módulo de sombreado

**Fecha del inventario:** 2026-08-08  
**Alcance:** calculadora externa React/TypeScript y su conexión actual con el simulador energético.

## 1. Resultado de la línea base

La línea base técnica se ejecutó sin modificar la lógica de cálculo:

| Validación | Resultado |
|---|---|
| TypeScript (`pnpm check`) | Correcto |
| Pruebas específicas de sombreado/importación | 5 archivos, 169 pruebas correctas |
| Build frontend + servidor (`pnpm build`) | Correcto |

El build genera advertencias no bloqueantes:

- Variables de analítica no definidas en `index.html`.
- Script de analítica sin `type="module"`.
- Regla `@import` de fuentes después de otras reglas CSS.
- Chunks grandes por Three.js y la aplicación principal.

Estas advertencias no se modifican en la Fase 0 porque no forman parte del motor solar.

## 2. Cómo se ejecuta actualmente

El proyecto raíz es una aplicación React/Vite con servidor Express:

```text
pnpm dev
  → tsx watch server/_core/index.ts
  → Express + Vite
  → cliente en client/
```

El servidor usa `PORT` o comienza buscando desde el puerto 3000. El módulo externo no es un workflow separado en la configuración actual. Los workflows registrados de artefactos (`api-server` y `mockup-sandbox`) son servicios diferentes y actualmente fallan por dependencias ausentes en sus respectivos artefactos; no representan la línea de ejecución principal de esta calculadora.

## 3. Mapa funcional actual

### Entrada y normalización

| Responsabilidad | Código principal | Estado |
|---|---|---|
| Carga y parseo de EPW | `client/src/lib/epwParser.ts` | React/TypeScript |
| Importación Andrew Marsh | `client/src/lib/marshSiteDesigner.ts` | React/TypeScript |
| Importación OBJ y modelos 3D | `client/src/lib/objParser.ts`, `buildingModelImporter.ts`, `multiFormatParser.ts` | React/TypeScript |
| Conversión de unidades y ejes | `buildingModelImporter.ts` | React/TypeScript |
| Proyección 3D → máscara angular | `marshSiteDesigner.ts`, `buildingModelImporter.ts` | React/TypeScript |
| Diagrama y edición de obstáculos | `SunPathDiagram.tsx` | React/TypeScript |

### Física solar y sombreado

| Cálculo | Código principal | Observación |
|---|---|---|
| Posición solar | `solarPosition.ts` | SPA simplificado; declara precisión aproximada de ±0,5°. Usa año predeterminado 2024. |
| POA isotrópico | `shadingMaskCrossing.ts` | DNI, DHI, GHI, albedo y superficie inclinada. |
| Cielo claro | `shadingMaskCrossing.ts` | Hottel para DNI y correlación simplificada para DHI. |
| `FS_climatico` | `shadingMaskCrossing.ts` | Compara POA EPW contra POA de cielo claro. |
| `FS_geometrico` por máscara | `shadingMaskCrossing.ts` | Evalúa si el sol cae dentro de polígonos angulares y muestrea ±15 minutos. |
| Cruce máscara + EPW | `shadingMaskCrossing.ts`, `CrossingModal.tsx` | Días críticos o días 21 de cada mes; no es todavía un cálculo anual horario completo. |
| FS mensual por fachada | `facadeShadingAnalysis.ts` | Muestrea días 1, 8, 15 y 22, entre 05:00 y 20:30, en pasos de 30 minutos; escala al mes completo. |
| FS mensual agregado | `Home.tsx` | Promedia puntos por mes y aplica corrección climática adicional. |

### Energía y reportes

| Responsabilidad | Código principal | Estado |
|---|---|---|
| POA Liu-Jordan/Perez | `liuJordanModel.ts` | Segundo conjunto de funciones POA en el mismo cliente. |
| Producción mensual/anual | `energyProduction.ts` | Consume factores mensuales y pérdidas del sistema. |
| IAM, soiling y temperatura BIPV | `iamSoilingEngine.ts` | Cadena física adicional para simulaciones BIPV. |
| Reporte PDF | `reportGenerator.ts`, `shadingCrossingReportSection.ts` | Hay un reporte de cruce técnico y otro reporte solar más amplio. |
| Comparación de datos | `crossValidation.ts` | Métricas RMSE, MAE, R² y exportación CSV. |

## 4. Rutas de cálculo encontradas

### Ruta A — Cruce explícito de máscara y EPW

```text
EPW
  + obstáculos angulares
  + configuración de días/horas/fachadas
  ↓
executeCrossing()
  ↓
FS_geometrico + FS_climatico + FS combinado
  ↓
crossingResultsToAnalysisPoints()
  ↓
tabla de puntos y CSV
```

Características actuales:

- El factor combinado se calcula como `max(FS_geometrico, FS_climatico)`.
- El bypass no debe consumir ese valor combinado; la autoridad física debe ser `FS_geometrico`.
- Los días evaluados pueden ser cuatro fechas críticas, los días 21 de cada mes o una selección personalizada.
- El EPW se busca en la fecha/hora exacta y luego usa fallback a días cercanos o promedio mensual.

### Ruta B — Análisis mensual por fachada y simulador

```text
modelo 3D + fachada + EPW
  ↓
calculateMonthlyShadingFactorsForFacade()
  ↓
POA con y sin sombra + FS mensual
  ↓
FacadeFullAnalysis
  ↓
Home.tsx
  ↓
EnergyProductionSimulator
```

Características actuales:

- Es una aproximación representativa escalada a cada mes, no una simulación anual de 8.760 registros.
- El sombreado geométrico elimina la componente directa y conserva difusa + reflejada.
- Calcula `poaMonthly`, `poaNoShading`, pérdida mensual y pérdida anual estimada.
- Sus resultados no pasan por el mismo contrato de `executeCrossing()`.

### Ruta C — Producción y finanzas

`Home.tsx`, `energyProduction.ts` y `reportGenerator.ts` todavía incluyen:

- Producción AC/DC.
- Pérdidas del sistema.
- Tarifas.
- Costos por Wp.
- Ahorros.
- Payback.
- ROI.
- Parámetros financieros.

Esto confirma que la separación acordada para el módulo de diagnóstico solar todavía no está implementada. Queda como trabajo posterior, después de cerrar la equivalencia física y el contrato de datos.

## 5. Hallazgos técnicos importantes

### 5.1 Hay dos modelos de posición solar

Se encontró:

- `solarPosition.ts`, usado por la máscara solar y el cruce EPW.
- `liuJordanModel.ts`, que calcula sus propios ángulos solares.

Antes de trasladar el motor a Python hay que elegir una convención y comparar ambos resultados para la misma ubicación, fecha, hora y zona horaria.

### 5.2 Hay dos rutas de POA

Se encontró:

- POA isotrópico local en `shadingMaskCrossing.ts`.
- POA Liu-Jordan/Perez en `liuJordanModel.ts`.

No deben sumarse ni mezclarse sin una decisión explícita sobre cuál es contexto diagnóstico y cuál es producción oficial.

### 5.3 El cálculo actual de `FS_geometrico` no es ray-casting 3D directo

La ruta externa proyecta obstáculos 3D a polígonos angulares y evalúa inclusión del punto solar. Esto es útil para el diagnóstico visual, pero es distinto del ray-casting 3D existente en `bipv_python/calculos/sombras_3d.py`.

La migración futura debe comparar ambas rutas con casos geométricos controlados antes de declarar equivalencia.

### 5.4 El año solar está implícito

`calculateSolarPosition()` usa 2024 por defecto. El EPW conserva su año, pero el cruce no transmite explícitamente el año al cálculo de posición solar. Esto debe resolverse en el contrato oficial.

### 5.5 El EPW usa horas de intervalo

El parser conserva la convención EPW `hour = 1..24`. El cruce convierte la hora representativa a `Math.ceil(hourDecimal)`. La alineación debe documentarse y probarse contra el índice horario utilizado por BIPV, especialmente porque el TMY de BIPV se trata como UTC.

### 5.6 Existen fallbacks silenciosos que deben volverse trazables

Entre ellos:

- Ubicación con valores por defecto `0`.
- Unidades desconocidas con escala por defecto milímetros.
- Registro EPW reemplazado por día cercano o promedio mensual.
- Ausencia de EPW exacto que devuelve factores neutros en algunos helpers.

Estos comportamientos pueden ser útiles para la interfaz, pero el motor oficial deberá distinguir entre dato válido, aproximado y faltante.

### 5.7 Los tests actuales prueban rangos y formas, no equivalencia física completa

Las 169 pruebas pasan, pero todavía falta una batería de referencia que compare:

- Posición solar TypeScript contra `pvlib`.
- POA TypeScript contra un caso analítico o `pvlib`.
- Máscara angular contra geometrías conocidas.
- Resultado representativo contra un cálculo horario anual.
- Carga manual y futura integración directa.

Además, el fixture de `shadingMaskCrossing.test.ts` usa `Math.random()` para generar irradiancias; debe convertirse en datos deterministas cuando se cree la batería de regresión física.

## 6. Clasificación inicial para la arquitectura híbrida

### Debe permanecer en React/TypeScript

- Controles y configuración de la simulación.
- Carga de archivos.
- Previsualización 3D.
- Edición visual de obstáculos.
- Diagrama de trayectoria solar.
- Tablas, gráficas y navegación.
- Exportación de resultados ya calculados por el motor oficial, mientras no altere los datos.

### Debe evaluarse para trasladar a Python

- Posición solar oficial.
- Parser y validación semántica de EPW.
- Proyección geométrica y cálculo de `FS_geometrico`.
- POA diagnóstico.
- Cálculo de escenarios.
- Energía recuperable.
- Validación de coordenadas, zona horaria, unidades y norte.

### Debe quedar fuera del módulo de diagnóstico solar

- CAPEX, OPEX y tarifas.
- TIR, VPN, payback y ROI.
- Ahorros COP/USD.
- Producción financiera calculada dentro del módulo externo.

La producción final y las finanzas deben seguir perteneciendo a BIPV, después de recibir `FS_geometrico`.

## 7. Decisión al cierre de Fase 0

No se migra ni se elimina código todavía.

La siguiente fase debe comenzar con una batería de referencia física y un contrato explícito que incluya:

```text
ubicación
zona horaria
EPW
modelo/unidades
norte
escenario
tipo de simulación
fachada
punto o fila
timestamp
FS_geometrico
```

La fuente oficial futura será Python, pero la equivalencia se demostrará comparando primero las rutas TypeScript actuales y la ruta Python existente de BIPV.