# Ficha de Coherencia: Herramientas de Dimensionamiento de Strings (N_strings/tracker)

**Fecha:** 29-ago-2026
**Origen:** continuación de la validación Teusaquillo vs PVsyst — al comparar cómo la app calcula "N_strings por tracker" contra el mecanismo real de PVsyst, se expusieron y corrigieron 3 bugs reales encadenados en las herramientas de dimensionamiento de strings de `pages/4_📐_Dimensionamiento.py`.

## 1. Punto de partida: N_strings/tracker con default duro = 1

El campo **"N_strings por tracker (vía combinadoras)"** era un `number_input` con default fijo en 1, sin importar el inversor seleccionado. Con el proyecto real Teusaquillo (Growatt MID15KTL3-X, que soporta 8 strings/tracker), esto hacía que la app calculara "Paneles/inversor = 8×1×2 = 16" en vez de 128, y de ahí "necesitas 8 inversores" en vez de 1 — un error de dimensionamiento real, no cosmético.

PVsyst no tiene este problema: nunca pide este dato aparte — el usuario declara el **total** de cadenas del generador ("Núm. cadenas") y PVsyst reparte automáticamente entre los MPPT del inversor.

## 2. Fix 1 — Autocálculo desde el catálogo (commit `acd80dd5`)

Nueva función `calculos/dimensionamiento.py::resolver_n_strings_tracker()`: autocalcula `N_str_tr` desde `inversor["n_strings_tracker"]` del catálogo cada vez que cambia el inversor seleccionado, respetando un ajuste manual del usuario mientras siga con el mismo inversor.

**Honestidad pedida por el usuario**: ¿esto ya opera igual que PVsyst? Respuesta: parecido en el resultado (coincide en Teusaquillo porque el diseño real usa la capacidad máxima del inversor), pero no en el mecanismo — PVsyst parte de "cuánto quiero instalar" (el total), esta función partía de "cuánto soporta el equipo" (el máximo del catálogo). Si un proyecto futuro usara menos capacidad que el máximo del inversor, el autocálculo sugeriría un valor incorrecto por defecto.

## 3. Fix 2 — Mecanismo "total" estilo PVsyst (commit `78f940ad`)

`resolver_n_strings_tracker()` ahora soporta **dos mecanismos**, elegibles por el usuario vía un nuevo campo opcional *"N total de cadenas para el proyecto (estilo PVsyst)"*:

- **`N_total_cadenas > 0`** ("total", mecanismo real de PVsyst): reparte `ceil(N_total_cadenas / n_trackers)` entre los trackers del inversor.
- **`N_total_cadenas == 0`** (default, "catálogo"): autocalcula desde la capacidad máxima del inversor — mejor cuando el usuario todavía está explorando cuánto cabe (propósito real de esta página), no verificando un diseño ya decidido.

Ambos respetan un ajuste manual del usuario mientras la fuente activa no cambie (mismo inversor+total, o mismo inversor sin total); cambiar de mecanismo, de inversor, o de total declarado resetea al valor recién calculado. 8 tests cubren ambos mecanismos, incluyendo reparto no exacto (`ceil(17/2)=9`) y que volver el total a 0 regresa al mecanismo de catálogo.

## 4. Fix 3 — `alerta_margen`: dos evaluadores con criterios distintos (commit `c4e0650e`)

Probando el inversor real **TriP 6K-HV** (2 strings/tracker), se encontró que **"Por inversor" (botón "▶️ Optimizar N paneles/string")** y **"Prorrateo preliminar" (🧭 Mapeo de inversores)** recomendaban N distintos (7 vs 8) para el MISMO inversor real:

- `optimizar_n_serie()` usa `semaforo()`, que aplica un **margen de seguridad del 7,5%** (`UMBRAL_ALERTA_PCT`, heredado literalmente de la hoja Excel original `Optimizacion_String` celda L14) — descartaba N=8 porque su Voc en frío (987,6V) queda a solo 1,24% del Vdc_max del inversor (1000V).
- `evaluar_compatibilidad_string()` (usada por el mapeo y por el banner "🟢 Compatibilidad eléctrica" de 📊 Producción) **no aplicaba ningún margen** — N=8 salía "✅ Compatible" sin más.

**Corregido sin romper proyectos ya validados**: nuevo campo informativo `alerta_margen` (mismo `semaforo()`, mismo 7,5%) — `compatible` **no cambia de significado** en ningún caso (retrocompatible con Urabá y cualquier proyecto ya entregado). `mapear_inversores_catalogo()` ahora prioriza, al recomendar, los N sin `alerta_margen` antes que la máxima utilización MPPT. Visible en la UI: columna "⚠️ Margen ajustado" en la tabla del mapeo, marca en el desplegable, y advertencia bajo "Prorrateo preliminar" cuando aplica.

## 5. Fix 4 — Caché obsoleta del prorrateo preliminar (commit `f70928a8`)

Repitiendo el TriP 6K-HV con `N_total_cadenas=16` declarado, "Por inversor" y "Prorrateo preliminar" volvieron a discrepar (112 vs 128 paneles/inversor) — pero **no era la inconsistencia del punto 4** (verificado con los datos reales, ambas herramientas ya coincidían en recomendar N=7). La causa: "Prorrateo preliminar" guardaba el N recomendado en el momento del clic del botón, y **nunca se invalidaba si el usuario cambiaba después el total declarado o ajustaba N_strings/tracker** — solo se invalidaba al cambiar de inversor o panel. El resultado combinaba un N=8 viejo (recomendado ANTES de declarar el total) con el N_str_tr=8 nuevo (derivado del total recién declarado): 8×8×2=128, un número que no correspondía a ninguna recomendación real vigente.

**Corregido**: nueva clave `prorrateo_preliminar_n_str_tr` (separada de `N_str_tr_usado`, que ya escribe también el botón "Optimizar N paneles/string" para su propio fin) que invalida el prorrateo cada vez que cambia N_strings/tracker, igual que ya invalidaba al cambiar de inversor/panel.

## 6. Verificación final — coherencia confirmada (TriP 6K-HV, N_str_tr=2, panel ASP-ST1-T40, 87 m² útiles)

Con los 4 fixes aplicados, "Por inversor" y "Prorrateo preliminar" dan **exactamente los mismos números**, cifra por cifra:

| Variable | Fórmula | Cálculo | Resultado |
|---|---|---|---|
| Paneles/inversor | N_serie × N_str_tr × n_trackers | 7×2×2 | 28 |
| P_DC/inversor | Paneles × Pmax_stc (63W) | 28×0,063 | 1,76 kW |
| Área/inversor | Paneles × área módulo (0,72m²) | 28×0,72 | 20,16 m² |
| Cobertura unitaria | Área/inversor ÷ área útil | 20,16/87 | 23,1% |
| DC/AC | P_DC/inversor ÷ P_ac_nom (8,64kW) | 1,76/8,64 | 0,20 (🔴 muy sobredimensionado) |
| Inversores | ceil(área útil ÷ área/inversor) | ceil(87/20,16) | 5 |
| Paneles totales | Inversores × Paneles/inversor | 5×28 | 140 |
| kWp instalados | Inversores × P_DC/inversor | 5×1,76 | 8,8 kWp |

N=7 coincide exactamente con la última fila 🟢 (0 riesgos) del barrido de compatibilidad antes de que N=8 pase a 🟡 ALERTA — validación eléctrica y aritmética consistentes entre sí.

### Lectura de ingeniería (no solo aritmética)

- **DC/AC=0,20 es una señal real, no un artefacto de cálculo**: el TriP 6K-HV (8,64 kW CA) está muy sobredimensionado para 1,76 kWp DC por unidad — menos del 25% de la capacidad del hardware aprovechada. Vale la pena revisar si conviene un inversor más chico antes de cotizar este diseño.
- **Limitación matemática inherente, no un bug**: `ceil(87/20,16)=5` produce un área total (5×20,16=100,8 m²) que **excede** el área útil real (87 m²) en ~14%. La UI trunca "Cobertura del área útil" a 100% (correcto, para no mostrar >100%), pero en la práctica el 5° inversor no cabría completo en el terreno — el diseño real tendría 4 inversores completos + un remanente parcial. Es una limitación del modelo simple "área ÷ área-por-unidad" (sin layout físico real), no algo que estos fixes debieran resolver.

## Commits relacionados
- `acd80dd5` — autocálculo de N_strings/tracker desde el catálogo del inversor
- `78f940ad` — mecanismo "total" estilo PVsyst (N_total_cadenas declarado)
- `c4e0650e` — `alerta_margen`: armoniza el margen de seguridad del 7,5% entre `optimizar_n_serie()` y `evaluar_compatibilidad_string()`
- `f70928a8` — invalida el prorrateo preliminar cuando cambia N_strings/tracker

Ver también `DIAGNOSTICO_VALIDACION_TEUSAQUILLO_PVSYST.md` para el contexto original (bloqueo de PVsyst, alarma de relación DC/AC, bugs de catálogo de inversores).
