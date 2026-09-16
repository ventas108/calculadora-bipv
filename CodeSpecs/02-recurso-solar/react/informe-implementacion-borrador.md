# Informe de implementación (borrador) — CodeSpecs/02-recurso-solar/react/

**Fecha:** 2026-09-16 (actualizado el mismo día tras revisión de Copilot)
**Estado:** commit local `7fe68949` creado ("Unificar cálculo POA y reforzar validación solar React"), sin push ni despliegue. Bloqueo de la primera revisión (Perez `NaN`) corregido en la fuente — ver "Corrección aplicada" al final. La revisión técnica de Copilot no encontró bloqueos pendientes tras la corrección; implementación y corrección de Perez quedan aprobadas técnicamente.
**Nota:** este es un borrador de trabajo. `implementacion.md`/`validacion.md` ya fueron completados e incluidos en el commit local `7fe68949`; este borrador es un registro adicional del proceso, no los reemplaza.

## Archivos modificados

**Código:**
- `client/src/lib/poaMonthly.ts` (nuevo) — función pura compartida `calculateMonthlyPOA()`
- `client/src/pages/Home.tsx` — la rama EPW de `poaData` ahora llama a `calculateMonthlyPOA()`; rama `prospectorData` intacta
- `client/src/components/POAAnalyzer.tsx` — su `poaData` ahora llama a la misma función; se eliminaron `dayOfYear`/`MONTHS`/`calculateHourlyPOA` que quedaron sin uso

**Tests:**
- `server/liuJordanModel.test.ts` (nuevo, 15 tests tras la corrección de Perez — ver "Corrección aplicada")
- `server/epwParser.test.ts` (nuevo, 12 tests)
- `server/poaMonthly.test.ts` (nuevo, 10 tests — incluye regresión de no-duplicación)
- `server/pvgisProxy.test.ts` (reescrito, 6 tests) — ahora prueba de verdad `server/pvgisProxy.ts`
- `server/irradianceHeatmapSynthetic.test.ts` (nuevo, contenido = el `pvgisProxy.test.ts` original renombrado, sin cambios)

**No se tocó** `server/pvgisProxy.ts` ni `client/src/components/IrradianceHeatmap.tsx` (solo se usaron como sujetos de test), ni nada en `CodeSpecs/02-recurso-solar/streamlit/`.

## Contrato preservado

Verificado programáticamente (script aparte, no en el repo) con un EPW sintético de **año completo (8760 horas)** y 4 combinaciones de `tilt/azimuth/albedo/usePerez`: la salida de `Home.tsx` es **byte-a-byte idéntica** antes y después del refactor en los 4 casos, incluyendo Perez. Campos, unidades y redondeos sin cambios.

## ⚠️ Cambio numérico observado — requiere decisión

Al hacer la misma comparación para **POAAnalyzer.tsx**, se encontró que su implementación *anterior* (la que se reemplaza) tenía un bug real: al no filtrar horas sin irradiancia antes de llamar a `calculateHourlyPOA`, y al usar el modelo **Perez**, las horas nocturnas (GHI=0) producían `kd = DHI/GHI = 0/0 = NaN` dentro de `liuJordanModel.ts` — y ese `NaN` contaminaba la suma completa del mes. Resultado: **la pestaña "Análisis POA" con modelo Perez mostraba `NaN` en los 12 meses, siempre**, para cualquier EPW cargado (no es un caso límite raro — toda hora nocturna lo dispara, y todo mes tiene horas nocturnas). Con Liu-Jordan (el modelo por defecto) no había diferencia.

Al unificar con la función compartida (que hereda el filtro `GHI>0 || DNI>0` de `Home.tsx`), este bug **se corrige como efecto colateral** — el gráfico de Análisis POA en modo Perez ahora muestra números reales en vez de `NaN`. La causa raíz también se corrigió en `calculatePOARadiationPerez()` con una guarda mínima para `GHI<=0`, y quedó protegida por tests de irradiancia nula y de datos inconsistentes.

No es un cambio de contrato (mismos campos/tipos), pero sí es un cambio de **comportamiento numérico** más allá de "extracción sin cambios" — se señala explícitamente en vez de mezclarlo silenciosamente en el diff.

## Tests ejecutados

```
npx vitest run
```
→ **848 passed**, 2 failed — **los mismos 2 fallos preexistentes y no relacionados** que ya existían antes de esta tarea (confirmado: no están en los archivos modificados):
- `pvwattsProxy.test.ts`: falta `NREL_API_KEY` en este entorno de desarrollo (no relacionado con PVGIS ni recurso solar)
- `sddAgent.test.ts`: gate del propio agente SDD, no relacionado

```
pnpm check
```
→ sin errores.

```
pnpm build
```
→ exitoso (vite build + esbuild), sin nuevos warnings.

## Riesgos / decisiones pendientes

1. ~~La corrección del bug de Perez en POAAnalyzer necesita confirmación explícita~~ → **Resuelto en la fuente**, ver "Corrección aplicada" abajo.
2. ~~Bug latente documentado, no corregido: `calculatePOARadiationPerez` sin guarda contra división por cero~~ → **Corregido** (`kd=0` cuando `GHI<=0`), ver abajo.
3. **`client/src/lib/irradianceHeatmap.ts`** (librería sintética, cero consumidores reales) se conservó sin tocar, solo se renombró su test — decisión de eliminarla sigue pendiente, no se tomó por cuenta propia.

---

## Corrección aplicada (misma fecha, tras la primera revisión técnica)

La revisión técnica de Copilot calificó la implementación como positiva, pero identificó un bloqueo antes de aprobarla: dejaba documentado, sin corregir, un `NaN` en una función pública del modelo físico. Se corrigió la causa raíz con el cambio mínimo pedido. Tras la corrección, la revisión técnica de Copilot no encontró bloqueos pendientes.

### Diff — `client/src/lib/liuJordanModel.ts`

```diff
   // Índice de claridad
   const kt = globalHorizontalIrradiance / (solarAngles.airmass * 1367 * Math.cos(solarAngles.zenithAngle));
-  const kd = diffuseHorizontalIrradiance / globalHorizontalIrradiance;
+  // GHI<=0 (hora sin irradiancia horizontal, o dato con DNI>0 pero GHI=0):
+  // kd=0 evita una división por cero (NaN/Infinity) que contaminaría f1/f2 y,
+  // por tanto, diffusePOA/totalPOA para toda la hora.
+  const kd = globalHorizontalIrradiance > 0
+    ? diffuseHorizontalIrradiance / globalHorizontalIrradiance
+    : 0;
```

Cambio mínimo: solo la línea de `kd`. `kt` (variable ya sin uso en el archivo, no relacionada con el bug) quedó intacta. Fórmulas de componente directa/reflejada sin tocar; con GHI>0 el comportamiento es idéntico al anterior.

### `server/liuJordanModel.test.ts` — se reemplazó el test que aceptaba el `NaN`

- **Hora 100% nula** (DNI=DHI=GHI=0): ahora exige todas las componentes finitas y en `0`.
- **GHI=0 con DNI>0** (dato de calidad dudosa pero permitido por el contrato de tipos): exige `totalPOA` finito, `diffusePOA=0`, `directPOA>0`, `totalPOA ≈ directPOA`.
- **GHI>0 (caso normal)**: nuevo test explícito que confirma que la rama válida no cambió.

### Verificación de que el fix no altera el contrato

Repetí la comparación byte-a-byte antes/después de todo el refactor (EPW sintético de año completo, 4 combinaciones de tilt/azimut/albedo/modelo): **sigue IDÉNTICO** en los 4 casos para `Home.tsx` — el fix solo toca la rama `GHI<=0`, que `calculateMonthlyPOA` ya excluía antes de llamar al modelo. Además, ahora el algoritmo *anterior* de `POAAnalyzer.tsx` (sin filtro de horas nocturnas) **también** deja de producir `NaN` con Perez — la causa raíz quedó corregida en la fuente, no solo evitada por el filtro del agregador.

### Tests ejecutados tras el fix

```
npx vitest run server/liuJordanModel.test.ts server/poaMonthly.test.ts server/pvgisProxy.test.ts server/epwParser.test.ts
```
→ **43/43 passed**

```
pnpm check
```
→ sin errores

```
pnpm build
```
→ exitoso, sin warnings nuevos

**Suite completa**: **850 passed**, 2 failed — los mismos 2 fallos preexistentes y no relacionados (`NREL_API_KEY` ausente en este entorno, gate de `sddAgent`), sin cambios.

Sin push ni despliegue. Alcance sin tocar: IAM/soiling, PR_T, producción, Prospector, Streamlit.

---

## Commit local creado (2026-09-16)

**Hash:** `7fe68949` — *"Unificar cálculo POA y reforzar validación solar React"*

### Archivos incluidos (16, exactamente los pedidos)

**Código:**
- `client/src/lib/poaMonthly.ts`
- `client/src/lib/liuJordanModel.ts`
- `client/src/pages/Home.tsx`
- `client/src/components/POAAnalyzer.tsx`

**Tests:**
- `server/liuJordanModel.test.ts`
- `server/epwParser.test.ts`
- `server/poaMonthly.test.ts`
- `server/pvgisProxy.test.ts`
- `server/irradianceHeatmapSynthetic.test.ts`

**Documentación `react/`:**
- `problema.md`, `propuesta.md`, `diseno.md`, `tareas.md`, `informe-implementacion-borrador.md`, `implementacion.md`, `validacion.md`

16 files changed, 1224 insertions(+), 254 deletions(-).

### Verificaciones previas al commit (todas en verde)

- Diff confirmado: guarda de Perez `kd = GHI>0 ? DHI/GHI : 0` presente en `liuJordanModel.ts`.
- Confirmado: `Home.tsx` y `POAAnalyzer.tsx` llaman a `calculateMonthlyPOA(...)`; contrato `poaData` sin cambios de forma.
- Tests focalizados (5 archivos): **58/58 passed**.
- `pnpm check`: sin errores. `pnpm build`: exitoso.

### Quedó fuera del commit (sin tocar, tal como se pidió)

- `CodeSpecs/00-director/mapa-dependencias.md`, `registro-de-decisiones.md`
- `CodeSpecs/01-datos-proyecto/propuesta.md`
- `CodeSpecs/02-recurso-solar/{diseno,implementacion,problema,propuesta,tareas,validacion}.md` (los del nivel raíz de `02-recurso-solar/`, distintos de los de `react/`)
- `CodeSpecs/02-recurso-solar/streamlit/` y `vision.md`
- `CodeSpecs/02-recurso-solar/react/exploracion-observacional.md` (no estaba en la lista solicitada)
- `client/src/lib/irradianceHeatmap.ts` — confirmado sin cambios, no fue necesario para el rename del test.

Sin push, sin despliegue. `git status --short` post-commit confirma el working tree limpio salvo los archivos deliberadamente excluidos arriba.

---

## Corrección del informe vía amend (2026-09-16) — hash final

Este mismo archivo contenía frases obsoletas ("sin commit", `implementacion.md`/`validacion.md` "pendientes") que contradecían la sección anterior una vez creado el commit. Se corrigieron únicamente esas frases (sin tocar listado de archivos, guarda de Perez, resultados de tests ni la sección de excluidos) y se actualizó el commit local con `git commit --amend --no-edit`.

**Hash final: `5972dad9`** (reemplaza a `7fe68949`, mismo mensaje: *"Unificar cálculo POA y reforzar validación solar React"*, mismos 16 archivos, 1268 insertions(+), 254 deletions(-) — la diferencia de líneas frente al commit anterior es solo el propio informe, que ahora se documenta a sí mismo).

`git status --short` tras el amend: únicamente los archivos deliberadamente excluidos (arriba) — sin rastro de los 16 archivos del commit ni cambios adicionales. Sin push, sin despliegue.

---
*Commit local únicamente (hash `5972dad9`). Sin push, sin despliegue, a la espera de nueva instrucción.*
