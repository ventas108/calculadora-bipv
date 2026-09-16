# Contrato: CSV de Factor de Sombreado entre apps hermanas (BORRADOR)

## Apps y arquitectura reales (corregido)

| Componente | Rol | Directorio (servidor) | Rama |
|---|---|---|---|
| `bipv.innovacionquimica.com.co` (interfaz React/Node) | UI de carga de geometría y exportación del CSV | `/var/www/bipv/calculadora` | `branch-agent` |
| **Motor Solar Python** (`bipv_python/scripts/run_shading_contract.py`) | **Productor real** del cálculo — ray-casting oficial, invocado por Node vía `child_process.spawn` | mismo checkout, subproceso Python | — |
| `calc.innovacionquimica.com.co` (Streamlit) | **Consumidor** del CSV exportado | `/var/www/bipv/calculadora-bipv` | `main` |

**Importante:** `bipv.innovacionquimica.com.co` NO calcula la física del sombreado en Node/TypeScript. El servidor Express expone `POST /api/shading-engine/run` ([server/shadingEngineProxy.ts](server/shadingEngineProxy.ts)), que lanza el proceso Python oficial y le pasa la solicitud por stdin/stdout, validada por [bipv_python/calculos/contrato_sombreado.py](bipv_python/calculos/contrato_sombreado.py) (`CONTRACT_VERSION = "bipv.shading.v1"`). El CSV que termina exportando la interfaz React es la salida de ESE motor Python, reformateada para descarga.

### Las 3 capas exactas (mismo repositorio, un solo checkout de código fuente)

1. **`client/`** (React/TS): UI de geometría 3D, botón "Cruzar Máscara de Sombreado + EPW" ([client/src/components/CrossingModal.tsx](client/src/components/CrossingModal.tsx)); calcula los 5 puntos de muestreo por fachada en [client/src/lib/buildingModelImporter.ts](client/src/lib/buildingModelImporter.ts) (`buildFacadeSamplePoints`).
2. **`server/`**: [server/shadingEngineProxy.ts](server/shadingEngineProxy.ts) — proxy puro, `spawn()` del proceso Python, reenvía stdin/stdout sin tocar el resultado.
3. **`bipv_python/`** (única fuente de física real):
   - [bipv_python/scripts/run_shading_contract.py](bipv_python/scripts/run_shading_contract.py) — CLI que invoca `calcular_fs_horario()` (ray-casting con `trimesh`).
   - [bipv_python/calculos/contrato_sombreado.py](bipv_python/calculos/contrato_sombreado.py) — valida entrada y salida (`validar_solicitud`, `validar_resultado`, `resultado_a_contrato`).
   - [shared/shading-engine-contract.ts](shared/shading-engine-contract.ts) — réplica **exacta** en TypeScript de las mismas reglas (`isOfficialShadingEngineResult()`), para que React no confíe ciegamente en el payload aunque venga de su propio backend.

### Garantía estructural del contrato JSON (doble candado Python + TS)

Ambas validaciones (`contrato_sombreado.py` y `shading-engine-contract.ts`) exigen simultáneamente:
- `fs_climatico === null` y `fs_combinado === null` — el payload oficial nunca puede transportar esos valores.
- `fs === fs_geometrico` (tolerancia `1e-9`).

Esto hace **estructuralmente imposible** que el JSON oficial cuele un FS climático o combinado disfrazado de geométrico. La transformación posterior a CSV está localizada en [client/src/components/ShadingCalculator.tsx](client/src/components/ShadingCalculator.tsx): `toLocalCalendarParts()` convierte `timestamp_utc` a `Mes/Dia/Hora` usando el offset del EPW; `exportOfficialCSV()` exporta el detalle crudo; y `computeAggregatedFacadeResults()` / `exportAggregatedOfficialCSV()` agrupan y promedian los puntos por fachada y `timestamp_utc`.

### Implementación exacta del exportador localizada

La búsqueda en la rama desplegada encontró el flujo descrito en los anexos 56-57:

- `runOfficialEngine()` llama a `runOfficialShadingEngine()` y recibe el resultado validado `bipv.shading.v1`.
- `toLocalCalendarParts(timestampUtcIso, tzOffsetHours)` suma el offset horario del EPW a `timestamp_utc` y obtiene calendario UTC para evitar depender de la zona horaria del navegador.
- `exportOfficialCSV()` genera `FS_geometrico_motor_python.csv`, con detalle por punto muestreado.
- `computeAggregatedFacadeResults()` agrupa por `(facade, timestamp_utc)` y calcula el promedio aritmético de `fs_geometrico`.
- `exportAggregatedOfficialCSV()` genera `FS_geometrico_promediado_motor_python.csv`, el archivo destinado a Mismatch.

El componente `CrossingModal` sigue siendo un flujo local separado para días críticos; no debe confundirse con el botón `Motor solar Python` ni con los dos exportadores oficiales ubicados en `ShadingCalculator.tsx`.

## Módulo consumidor real (identificado en el repo)

- Parser: [bipv_python/calculos/mismatch_bypass.py](bipv_python/calculos/mismatch_bypass.py) — función `cargar_csv_fs()`
- Página que lo carga: [bipv_python/pages/5_🔀_Mismatch.py](bipv_python/pages/5_🔀_Mismatch.py) — Sección 5 "Bypass Diodes — Pérdida eléctrica por sombra parcial"
- Alternativa de generación local (misma sesión, mismo formato de salida): [bipv_python/pages/5a_🌳_Sombras_SketchUp.py](bipv_python/pages/5a_🌳_Sombras_SketchUp.py)

## Módulos que consumen el resultado derivado (`factor_sombra_anual`, vía `st.session_state`)

- [bipv_python/pages/6_📊_Produccion.py](bipv_python/pages/6_📊_Produccion.py) — cascada de pérdidas de producción
- [bipv_python/pages/7_💰_Financiero.py](bipv_python/pages/7_💰_Financiero.py) — E_ac corregida por sombra parcial
- [bipv_python/pages/5b_🔆_Motor_Optico.py](bipv_python/pages/5b_🔆_Motor_Optico.py) — usa `factor_sombra_anual` de session_state
- [bipv_python/pages/9_🗺️_Vista_3D.py](bipv_python/pages/9_🗺️_Vista_3D.py) — solo visualización del FS por superficie (no recalcula)
- [bipv_python/pages/10_📄_Reporte_PDF.py](bipv_python/pages/10_📄_Reporte_PDF.py) — reporta horas de sombra y fuente del FS

## Formato del CSV (extraído de la validación real del parser)

### Formato estándar mínimo
```
Mes, Dia, Hora, FS
```

### Formato extendido (post-cruce EPW) — el que realmente se usa
```
Evento, Mes, Dia, Hora, Altura Solar (deg), Acimut Solar (deg),
Obstaculo, FS_geometrico, FS_climatico, FS, Situacion
```

### Formato exacto de los CSV oficiales del Motor Solar Python

El exportador vigente en `ShadingCalculator.tsx` genera estas cabeceras:

CSV crudo (`FS_geometrico_motor_python.csv`):
```text
Mes, Dia, Hora, Altura Solar (deg), Acimut Solar (deg), FS_geometrico, Fachada, Punto, timestamp_utc
```

CSV promediado (`FS_geometrico_promediado_motor_python.csv`):
```text
Mes, Dia, Hora, Altura Solar (deg), Acimut Solar (deg), FS_geometrico_promedio, N_puntos_muestreados, Fachada, timestamp_utc
```

`cargar_csv_fs()` acepta `FS_geometrico_promedio` porque su detección busca `fs_geometrico` como subcadena. Para Mismatch se debe usar el CSV promediado; el crudo se conserva para auditoría punto por punto.

### Columnas obligatorias
| Columna | Aliases aceptados | Notas |
|---|---|---|
| Mes | `mes`, `month` | |
| Dia | `dia`, `day` | |
| Hora | `hora`, `hour`, `hora_utc` | |
| **FS_geometrico** | contiene `fs_geometrico` o `fs_geometrica` | **única columna que puede activar bypass diodes**; 0 = sin sombra, 1 = sombra total |

### Columnas opcionales relevantes
| Columna | Uso |
|---|---|
| `Fachada` / `Obstaculo` | identifica fachada/array cuando hay múltiples superficies |
| `Punto` / `Punto de análisis` | identifica fila de módulos |
| `FS_climatico` | reducción por nubes — **nunca** se usa para bypass, solo diagnóstico |
| `FS` (combinado) | alias legado / diagnóstico, nunca fuente independiente |
| `n_modulos`, `area_activa_m2`, `potencia_instalada_kw` | metadatos de tamaño por punto |
| `obstacle_id`, `obstacle_name`, `first_hit_distance_m` | trazabilidad del ray-casting |

## Reglas de rechazo (ya implementadas, no negociables)

1. Si falta `FS_geometrico`, el CSV se **rechaza por completo** (`ValueError`) — nunca se usa `FS_climatico` ni `FS` combinado como sustituto, para no inflar/deflactar el bypass silenciosamente.
2. Si faltan `Mes`/`Dia`/`Hora`, se rechaza.
3. El parser detecta y repara comas embebidas en la columna `Obstaculo` (nombres con comas).
4. Existe detección de "convención invertida" (FS como transmitancia vs. p_shade) con advertencia explícita en la UI — no es automática silenciosa.

## Dos variantes de CSV exportadas por el Motor Solar Python (crítico, ya documentado en `base_conocimiento_asistente.md`)

Desde el 5-sep-2026, cada fachada se muestrea con **5 puntos** (no 1 solo), repartidos a lo largo del lado más largo. Esto generó dos botones de exportación distintos:

| CSV | Filas por fachada-hora | Uso correcto |
|---|---|---|
| **Crudo** (`FS_geometrico_motor_python.csv`) | 5 (una por punto muestreado) | Auditoría punto por punto únicamente |
| **Promediado** («CSV FS geométrico promediado») | 1 (promedio de los 5 puntos, valor continuo 0–1) | **El que se debe subir a 🔀 Mismatch** |

Subir el CSV crudo a Mismatch sin saberlo infla el dataset ~5× y puede confundir el análisis punto a punto con el agregado por fachada.

## Advertencia de zona horaria (ya corregida, pero crítica para cualquier cambio futuro)

El Motor Solar Python calcula todo internamente en **UTC** (pvlib). Ambos CSV recalculan `Mes/Dia/Hora` a **hora LOCAL** a partir de `timestamp_utc` usando el timezone del EPW cargado — `timestamp_utc` se conserva intacto como referencia. Si esta conversión se rompe en un cambio futuro, cualquier hora de sombra queda desfasada (se detectó un desfase de 5h con Bogotá antes del fix) sin ningún aviso al comparar contra el TMY local que usa Producción/Mismatch.

## Advertencia sobre la casilla "Invertir FS" en Mismatch

Esa opción es para un formato de CSV **distinto y más antiguo** ("Puntos manuales", convención de transmitancia). El CSV oficial del Motor Solar Python (`FS_geometrico` / `FS_geometrico_promedio`) **ya usa la convención correcta** de esta app (0=sin sombra, 1=sombra total) — **no debe marcarse** con este CSV. Se confirmó en producción que marcarla por error invierte el FS (ej. 0.080 → 0.920) e infla artificialmente la pérdida por bypass (falso 62.74%).

## Dependencia silenciosa con Motor Óptico (POA)

`simular_bypass_horario` solo cuenta una hora como "con sombra activa" si `p_shade > umbral` **Y** `G_eff > 5 W/m²` esa misma hora. Si el POA de 🌞 Motor Óptico quedó invalidado (p. ej. tras cambiar orientación en ☀️ Recurso Solar sin recalcular), el resultado puede salir en "0 horas con sombra" de forma silenciosa aunque el FS real no sea cero. Verificar que Motor Óptico esté recalculado antes de confiar en ese número.

## Riesgo de romper el contrato

Si la app productora (`bipv.innovacionquimica.com.co`) cambia:
- el nombre de la columna `FS_geometrico`,
- la convención de rango (0=sin sombra vs. 1=sin sombra),
- o elimina las columnas de tiempo `Mes/Dia/Hora`,

el parser de `calc.innovacionquimica.com.co` lo rechazará con error, o peor, lo aceptará con la convención invertida sin que el usuario lo note si la detección de inversión falla.

## Pendiente para completar el contrato formal

- [ ] Decidir si se agrega un número de versión explícito al CSV (ej. columna `contract_version` o cabecera) para detectar incompatibilidades futuras de forma explícita en vez de heurística de columnas.
- [ ] Evaluar si este contrato debe vivir junto a `shared/shading-engine-contract.ts` como referencia cruzada, dado que ambos gobiernan la misma frontera de dominio (sombreado) y el CSV es, en esencia, la materialización en disco del mismo `CONTRACT_VERSION = "bipv.shading.v1"`.
- [x] Localizar en `client/` la transformación del JSON oficial (`hour_utc`) al CSV descargable: `client/src/components/ShadingCalculator.tsx`, mediante `toLocalCalendarParts()`, `exportOfficialCSV()`, `computeAggregatedFacadeResults()` y `exportAggregatedOfficialCSV()`.
- [x] ~~Confirmar versión/changelog del formato CSV en el lado de la app Node~~ — confirmado: el cálculo NO vive en Node, vive en el Motor Solar Python (`bipv_python/calculos/contrato_sombreado.py` + `scripts/run_shading_contract.py`), Node solo hace de proxy HTTP↔proceso.

## Fuentes usadas para este borrador

- [bipv_python/calculos/mismatch_bypass.py](bipv_python/calculos/mismatch_bypass.py) (`cargar_csv_fs`, líneas ~260-450)
- [bipv_python/calculos/contrato_sombreado.py](bipv_python/calculos/contrato_sombreado.py)
- [server/shadingEngineProxy.ts](server/shadingEngineProxy.ts)
- [shared/shading-engine-contract.ts](shared/shading-engine-contract.ts)
- [client/src/components/ShadingCalculator.tsx](client/src/components/ShadingCalculator.tsx) — conversión UTC→local y exportadores oficiales
- [bipv_python/datos/base_conocimiento_asistente.md](bipv_python/datos/base_conocimiento_asistente.md) — Anexos 56 y 57 (5-sep-2026)
