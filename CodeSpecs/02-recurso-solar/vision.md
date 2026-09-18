# Visión — Módulo 02: Recurso Solar

**Estado:** borrador de exploración (no es uno de los 6 documentos del ciclo SDD;
sirve para acotar el alcance antes de escribir `problema.md`)

## 1. Hallazgo previo: existen DOS implementaciones de "Recurso Solar"

La calculadora BIPV tiene dos aplicaciones hermanas en este mismo repositorio, cada
una con su propio flujo de recurso solar:

| | App React/Node (`client/src`) | App Streamlit (`bipv_python`) |
|---|---|---|
| Despliegue en producción | `calculadora-bipv` (pm2, la que verificamos hoy con OAuth/PVGIS) | `streamlit-bipv` (pm2, app "hermana") |
| Entrada climática | Archivo `.epw` subido por el usuario (`epwParser.ts`) | TMY descargado de PVGIS por coordenadas (`calculos/solar.py::obtener_tmy_pvgis()`) |
| Cálculo POA | `calculateHourlyPOA()` (Liu-Jordan/Perez) en `lib/liuJordanModel.ts`, orquestado desde `pages/Home.tsx` | `calculos/solar.py::calcular_poa()` (pvlib, incl. modelo bifacial `infinite_sheds`) |
| UI | `POAAnalyzer.tsx`, `IrradianceHeatmap.tsx` (usa proxy `server/pvgisProxy.ts`), `SolarProspector.tsx` | `pages/2_☀️_Recurso_Solar.py` |
| Motor óptico (IAM/soiling) | `lib/iamSoilingEngine.ts` | Página "5b Motor Óptico" (opcional, no siempre se usa) |

El módulo `01-datos-proyecto` que ya cerramos documentó y corrigió la app
**Streamlit** (`bipv_python/pages/1_🏠_Proyecto.py`). Para `02-recurso-solar` hay que
decidir explícitamente cuál app (o ambas) cubre esta Spec, porque los flujos no
comparten código y los problemas encontrados son distintos en cada una.

## 2. Estado real encontrado (evidencia, no suposición)

### App React — `client/src/pages/Home.tsx` + `POAAnalyzer.tsx`
- Existe un diagnóstico previo, [DIAGNOSTICO_POA_SIMULADOR.md](../../DIAGNOSTICO_POA_SIMULADOR.md),
  que documentó 7 brechas críticas entre el "Análisis POA" y el "Simulador de
  Energía" (POA simplificado, tilt/azimut/albedo ignorados, viento fijo en 1 m/s,
  eficiencia genérica en T_cell).
- **Verificado por código (15-sep-2026): las 7 brechas ya están cerradas.**
  Evidencia concreta:
  1. `Home.tsx` calcula `poaData` con `calculateHourlyPOA()` — la misma función y
     firma exacta que usa `POAAnalyzer.tsx` (no hay una versión simplificada
     paralela).
  2/3/4. `effectiveTilt`, `poaAzimuth`, `poaAlbedo`, `poaUsePerez` viven en estado
     compartido de `Home.tsx` y se sincronizan con `POAAnalyzer` vía
     `onConfigChange` — un cambio en el Análisis POA se refleja en el Simulador.
  5. `avgWindSpeed` se calcula del EPW real (`sumWind / monthData.length`) y se
     pasa a `calculateCellTemperature()`; ya no hay `windSpeed = 1` hardcodeado en
     la ruta activa (solo aparece como valor por defecto de parámetro, no usado).
  6. `calculateCellTemperature()` recibe `panelSpecs.efficiency` real (no
     `eta=0.15` fijo) — ver `energyProduction.ts::calculateMonthlyProduction()`.
  7. `directPOA`/`diffusePOA`/`reflectedPOA` se calculan y devuelven por separado
     en cada mes, no solo el total.

  Esto es una lectura de código, no una prueba numérica end-to-end con un EPW
  real comparando contra un caso de referencia — pero la evidencia estructural es
  sólida: **no hay dos rutas de cálculo distintas, es la misma función con el
  mismo estado compartido.** Recomendación: marcar
  `DIAGNOSTICO_POA_SIMULADOR.md` como resuelto/archivado en vez de tratarlo como
  problema abierto para la Spec `02-recurso-solar` (app React).

### App Streamlit — `calculos/solar.py`
- El motor real (`calcular_poa()`) **no tiene** el bug de timezone de
  [DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md](../../DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md) —
  ese bug estaba confinado a 4 scripts sueltos de análisis (`barrido_dcac_uraba.py`,
  etc.), ya corregidos, y confirmado que **nunca afectó la app que ven los
  clientes**.
- Sí hay una recomendación abierta: el flujo agrivoltaico recomendado en el manual
  del asistente **salta la página "Motor Óptico" (IAM)**, lo que sobreestima
  producción ~3% para ese tipo de proyecto. Esto es más bien un tema de
  `04-produccion-energia` (o del manual de uso) que de captura del recurso solar en
  sí, pero afecta directamente cómo se usan las salidas de este módulo.

## 3. Propuesta de acotación de alcance

Para no repetir el error de abrir una Spec demasiado amplia, propongo que
`02-recurso-solar` cubra **solo**:

**Dentro del alcance:**
- Captura de la fuente climática (EPW subido, o TMY descargado por coordenadas).
- Cálculo de irradiancia en el plano de la fachada (POA): componentes directa,
  difusa, reflejada; parámetros tilt, azimut, albedo, modelo (Liu-Jordan/Perez).
- Zona horaria / alineación temporal entre irradiancia y posición solar.
- Las claves de estado que este módulo expone para los módulos siguientes.

**Fuera del alcance (pertenece a otros módulos):**
- Simulación de producción anual (E_ac, PR) → `04-produccion-energia`.
- Motor óptico (IAM, soiling) como derate de producción → `04-produccion-energia`
  o `05-perdidas-y-temperatura` (a confirmar con el director).
- Dimensionamiento de strings/inversor → `03-dimensionamiento`.

## 4. Preguntas para decidir antes de `problema.md`

1. ¿Esta Spec cubre la app React (`client/src`), la app Streamlit (`bipv_python`),
   o ambas por separado (dos Specs verticales dentro del mismo módulo `02`)?
2. Sobre la app React: ¿confirmamos primero con una prueba numérica si las 7
   brechas del diagnóstico previo siguen abiertas o ya se cerraron, antes de asumir
   que no hay problema?
3. ¿El Motor Óptico (IAM/soiling) se documenta como parte de este módulo (porque
   modifica la irradiancia efectiva) o del módulo de producción/pérdidas?

## 5. Decisiones (2026-09-15)

1. **Ambas apps, por separado.** El módulo `02-recurso-solar` se divide en dos
   Specs verticales independientes, cada una con su propio ciclo de 6 documentos:
   - [`react/`](react/problema.md) — app en producción `client/src` + `server/pvgisProxy.ts`.
   - [`streamlit/`](streamlit/problema.md) — app hermana `bipv_python`.
2. **Verificación numérica de las 7 brechas: hecha por lectura de código** (sección
   3 arriba) — no queda pendiente una prueba end-to-end adicional para abrir esta
   Spec; el hallazgo de "ya resuelto" pasa a `react/problema.md` como contexto, no
   como problema a resolver.
3. **Motor óptico (IAM/soiling) NO entra en `02-recurso-solar`** — el usuario
   confirma que pertenece a producción/pérdidas (`04-produccion-energia` /
   `05-perdidas-y-temperatura`). Se anota en `00-director/mapa-dependencias.md`
   para que ese módulo lo reciba explícitamente en su alcance.
