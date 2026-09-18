# Informe de exploración observacional — CodeSpecs/02-recurso-solar/react/

**Fecha:** 2026-09-16
**Alcance:** solo exploración de lectura. No se modificó código, no se redactó ninguna Spec, no se hizo commit ni push.

## Archivos revisados

**Código:**
- `client/src/pages/Home.tsx` (878 líneas, completo)
- `client/src/components/POAAnalyzer.tsx` (350 líneas, completo)
- `client/src/components/IrradianceHeatmap.tsx` (552 líneas)
- `client/src/lib/liuJordanModel.ts` (285 líneas, completo)
- `client/src/lib/epwParser.ts` (286 líneas, completo)
- `client/src/lib/pvgisApi.ts` (402 líneas, completo)
- `server/pvgisProxy.ts` (115 líneas, completo)
- `client/src/lib/solarRigor.ts` (256 líneas, completo — no estaba en la lista pedida pero es el gate de entrada que consume `Home.tsx`, imprescindible para entender el contrato)

**Tests:**
- `server/pvgisProxy.test.ts`, `server/solarRigor.test.ts`, `server/prTHourly.test.ts` (leídos/ejecutados)
- Búsqueda exhaustiva de tests para `liuJordanModel`, `epwParser`, `POAAnalyzer`, `IrradianceHeatmap`, `pvgisApi` (ninguno encontrado)

**Diagnósticos:**
- `DIAGNOSTICO_POA_SIMULADOR.md`
- `DIAGNOSTICO_GRAFICA_COMPATIBILIDAD_ELECTRICA.md`
- `DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md`
- Búsqueda de otros diagnósticos con patrón `poa|epw|pvgis|zona|tz|irradia|solar|radiac` en el nombre (solo estos tres son relevantes; los demás `DIAGNOSTICO_*NREL*`/`CI_PVLIB*` son de catálogo de paneles, no de recurso solar)

## Flujo actual (React/Node)

1. **Entrada climática — dos fuentes independientes, sin fusionar:**
   - **EPW real**: `WeatherDataManager` → `epwParser.ts::parseEPW()` → `EPWData` (ubicación, 8.760 registros horarios DNI/DHI/GHI/temp/viento/nubosidad) → estado `weatherData` en `Home.tsx`.
   - **PVGIS vía heatmap/prospector**: `IrradianceHeatmap.tsx` llama a `/api/pvgis/MRcalc` (proxy `server/pvgisProxy.ts`) por punto de grilla → un único valor de GHI anual por punto → al seleccionar un punto, `SolarProspector` (`source="heatmap_pvgis"`) lo transforma y llama `onUseInSimulator` → `Home.tsx::handleProspectorToSimulator` → estado `prospectorData`.
2. **Gate de calidad**: `Home.tsx` arma `solarRigorReport = validateSolarRigor({ epwData, tilt, azimuth, ... })` (`solarRigor.ts`). Si hay errores (`errorCount > 0`), `canCalculate = false` y no se calcula POA. Valida: 8.760 registros, TMY, coordenadas, zona horaria (rango −12..14, **sin verificar consistencia interna UTC/local**, solo rango), elevación, unidades, alineación horaria, tilt/azimut/fachadas/puntos de análisis.
3. **Cálculo POA — dos implementaciones independientes:**
   - **`Home.tsx` (línea 384-484)**: la que realmente alimenta Producción/Reporte. Si hay `prospectorData`, usa una aproximación gruesa (fracciones mensuales fijas + reparto 70/25/5% direct/diffuse/reflected). Si no, itera cada hora del EPW y llama `calculateHourlyPOA()` (Liu-Jordan o Perez, según `poaUsePerez`) con `tilt`/`azimuth`/`albedo` compartidos (`poaTilt`, `poaAzimuth`, `poaAlbedo`, `poaUsePerez`), agregando también `avgWindSpeed` real.
   - **`POAAnalyzer.tsx` (línea 63-126)**: recalcula el **mismo** promedio mensual de forma independiente (su propio `useMemo`), solo para los gráficos de la pestaña "Análisis POA" — no es la fuente que consume Producción/Reporte.
4. **Salidas del módulo** (contrato real consumido aguas abajo): `poaData: {month, directPOA, diffusePOA, reflectedPOA, totalPOA, avgTemp, avgWindSpeed}[]` (12 meses) + `solarRigorReport` (scope, recordCount, canCalculate) + `weatherData.location` (lat/lon/alt/timezone) + parámetros compartidos `tilt/azimuth/albedo/usePerez`. Consumido por `EnergyProductionSimulator` (confirmado: usa `avgWindSpeed` real, comentario explícito "ya viene calculado en poaData desde Home.tsx"), `ReportGenerator`, y `02-recurso-solar` invalida en cascada `densidad_Wm2`/`PR`/`tilt_default`/resultados de producción al cambiar de ciudad (mismo patrón que ya se documentó en `01-datos-proyecto`, aquí sin módulo `invalidacion.ts` nombrado — se hace inline en `Home.tsx`).
5. **PVGIS proxy**: `server/pvgisProxy.ts` valida `endpoint`/`params` contra allowlist, reenvía a `re.jrc.ec.europa.eu/api/v5_3/`, con reintento+backoff en fallos de red (agregado el 2026-09-15) y timeout de 60s.

## Problemas confirmados

1. **Duplicación de cálculo POA entre `Home.tsx` y `POAAnalyzer.tsx`.** Son dos implementaciones independientes de "promedio mensual de POA horario desde EPW vía Liu-Jordan/Perez". Hoy coinciden en la práctica (ambas usan `calculateHourlyPOA`, mismos parámetros compartidos), pero son código duplicado que puede divergir silenciosamente si se edita uno sin el otro — el gráfico de "Análisis POA" podría dejar de representar lo que realmente usa Producción/Reporte sin que nada lo detecte (no hay test que compare ambos).
2. **Cero cobertura de test para la física y el parsing del módulo.** `liuJordanModel.ts` (motor Liu-Jordan/Perez), `epwParser.ts` (parsing EPW), `pvgisApi.ts` (normalización de respuestas PVGIS) y el propio `server/pvgisProxy.ts` no tienen ningún test dedicado.
3. **`server/pvgisProxy.test.ts` está mal nombrado / no prueba lo que dice probar.** Importa y prueba `client/src/lib/irradianceHeatmap.ts` (una librería de **estimación sintética** de irradiancia por latitud), no `server/pvgisProxy.ts`. Ese archivo (`irradianceHeatmap.ts`) es código muerto: su único consumidor en todo el repo es ese mismo test; `IrradianceHeatmap.tsx` (el componente real, con PVGIS real) no lo importa.

## Riesgos pendientes (no confirmados como bug, sí como huecos)

- La divergencia entre las dos implementaciones de POA (#1 arriba) no tiene ningún test de regresión que la detecte si aparece.
- `validateSolarRigor` valida que la zona horaria esté en rango IANA (−12..14) pero no valida consistencia interna EPW (p. ej. que `timezone` declarado coincida con lat/lon) — es solo un chequeo de rango.
- `getPVGISHourlyData` (seriescalc, usado para `PR_T` en `PVGISAnalyzer.tsx`) recibe timestamps en UTC de PVGIS sin conversión explícita a zona local — verifiqué que `calculatePR_T_Hourly` es autocontenido (no cruza esos timestamps contra el índice horario local del EPW), por lo que **no reproduce** el bug de timezone documentado en el lado Python, pero es un patrón a vigilar si `PR_T` alguna vez se cruza con datos EPW indexados en hora local.
- `PVGISAnalyzer.tsx`/PR_T pertenece más a producción/rendimiento (04) que a recurso solar — su presencia aquí es solo tangencial (consume `getPVGISHourlyData` de `pvgisApi.ts`).

## Problemas descartados (verificados, no reabrir)

- **Incidente PVGIS por ráfagas (`ECONNRESET`)**: confirmado resuelto. Commits `808182d5` (logging de `error.cause`) y `2367dbb8` (retry+backoff en `pvgisProxy.ts` + pausa entre lotes en `IrradianceHeatmap.tsx`), desplegados en producción (`bipv-colombia`) y verificados en vivo el 2026-09-15 (16/16 puntos consultados sin pérdidas). `fetchWithRetry` sigue presente en el código actual.
- **`DIAGNOSTICO_POA_SIMULADOR.md`** describe 7 brechas entre el "Análisis POA" y el Simulador (POA simplificado, tilt/azimut/albedo/modelo/viento ignorados). Verificado en el código actual: la mayoría de las correcciones **ya están implementadas** — `poaData` en `Home.tsx` usa `calculateHourlyPOA` real (no la fórmula simplificada descrita), los parámetros `tilt/azimuth/albedo/usePerez` están unificados en estado compartido, y `avgWindSpeed` real se calcula y se consume en `EnergyProductionSimulator` (confirmado por grep + comentario explícito en el código). Es un diagnóstico histórico ya resuelto — no reabrir como problema, aunque sigue vigente la duplicación de cálculo (#1 en confirmados) como remanente relacionado.
- **`DIAGNOSTICO_GRAFICA_COMPATIBILIDAD_ELECTRICA.md`**: no aplica a este módulo. Es 100% `bipv_python` (Streamlit), sobre compatibilidad eléctrica string-inversor (`calculos/dimensionamiento.py`, `pages/6_📊_Produccion.py`, `pages/10_📄_Reporte_PDF.py`) — cero relación con POA/EPW/PVGIS/recurso solar. Pertenece, si acaso, a `03-dimensionamiento` o `04-produccion-energia` del lado Streamlit.
- **`DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md`**: el bug de timezone (re-etiquetar UTC como hora local) es 100% Python (`bipv_python/scripts/*.py`), ya corregido y commiteado. El propio diagnóstico confirma explícitamente que el motor real de producción (`calculos/solar.py`) nunca tuvo el bug. No aplica al React ni a esta Spec.

## Límites recomendados para react/problema.md

- **Dentro de alcance**: fuente climática (EPW + PVGIS), parsing EPW, gate de calidad (`solarRigor.ts`), modelo de transposición POA (Liu-Jordan/Perez, `liuJordanModel.ts`), componentes directa/difusa/reflejada, tilt/azimut/albedo compartidos, contrato de salida `poaData`/`weatherData.location` hacia Producción/Dimensionamiento/Reporte, y la duplicación de cálculo POA (#1) como defecto a corregir.
- **Fuera de alcance** (aunque toquen los mismos archivos): el motor óptico IAM/soiling (ya excluido por decisión previa → 04/05); `PR_T`/`PVGISAnalyzer` como métrica de rendimiento (→ 04-produccion-energia, aunque consuma `pvgisApi.ts`); el modelo "Prospector/Mulcué-Llanos" de estimación rápida desde un solo punto GHI (→ probablemente 03-dimensionamiento o 04, es un atajo de estimación, no adquisición climática); la librería muerta `irradianceHeatmap.ts` y su test mal-nombrado (limpieza de código, no comportamiento de recurso solar — mencionar como nota, no como criterio de aceptación).
- **Aceptación sugerida**: "Análisis POA" y el `poaData` consumido por Producción deben provenir de una única fuente de cálculo (eliminar duplicación), y debe existir cobertura de test mínima para `liuJordanModel.ts` y `epwParser.ts`.

## Comandos y resultados de verificación (solo lectura)

```
wc -l <7 archivos objetivo>                          → 2.868 líneas totales, tamaño manejable
grep -rln "lib/irradianceHeatmap" client/src server   → solo server/pvgisProxy.test.ts lo importa (código muerto confirmado)
grep -n "^import" client/src/components/IrradianceHeatmap.tsx → no importa irradianceHeatmap.ts
grep -n "avgWindSpeed" client/src/components/EnergyProductionSimulator.tsx → confirma consumo real del viento EPW
cat vitest.config.ts                                  → include: ["server/**/*.test.ts"] únicamente
npx vitest run server/solarRigor.test.ts server/pvgisProxy.test.ts → 2 files passed, 18 tests passed
npx vitest run (suite completa)                       → 807 passed, 2 failed (pvwattsProxy: falta NREL_API_KEY en este entorno; sddAgent: no relacionado) — ninguno de los 2 fallos toca recurso solar
git log --oneline --grep="ECONNRESET|PVGIS" -- server/pvgisProxy.ts client/src/components/IrradianceHeatmap.tsx → 2367dbb8, 808182d5
grep -n "fetchWithRetry" server/pvgisProxy.ts          → confirma que el retry sigue presente en el código actual
```

---
*Exploración detenida aquí, sin modificar archivos ni redactar `problema.md`. Pendiente de aprobación humana para avanzar.*
