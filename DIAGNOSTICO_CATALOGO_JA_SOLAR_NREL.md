# Ampliación real del catálogo de paneles: 278 módulos JA Solar (NREL/SAM + Sandia JPV 2025)

**Fecha**: 2-3 de septiembre de 2026
**Disparador**: el usuario preguntó si podía ampliar el catálogo de paneles/inversores por marca y
modelo, "como PVsyst". Se investigó con rigor antes de implementar (dos rondas: primero una idea de
"3 capas de confianza" con estimadores propios, descartada tras encontrar que la estimación de
dimensiones físicas por familia constructiva no es confiable con los datos disponibles; luego la
ruta finalmente usada, dos fuentes públicas reales cruzadas).

## Fuentes reales (2, cruzadas por nombre exacto de módulo)

1. **`PVS_params_translated.csv`** — dataset público de Deville, Hansen, Anderson, Chambers &
   Theristis, *"Parameter Translation for Photovoltaic Single-Diode Models"*, IEEE J. Photovoltaics
   15(3), mayo 2025 (Sandia National Labs). Zenodo DOI 10.5281/zenodo.14173605. 16.857 módulos
   reales (solo silicio mono/policristalino — el paper excluye CdTe/a-Si explícitamente por el
   término de recombinación), con parámetros SDM ya traducidos al modelo **PVsyst v6** (el mismo
   que usa `calcparams_pvsyst` en `calculos/modelo_iv.py` desde el 2-sep-2026). Calidad verificada
   directamente (no solo citada del paper): mediana de error de Pmax 0.083%, solo 0.66% de módulos
   con error >5% — coincide exacto con lo reportado por los autores.
2. **`CEC Modules.csv`** — NREL/SAM (`github.com/NREL/SAM/blob/patch/deploy/libraries/CEC%20Modules.csv`),
   base de datos pública de la California Energy Commission, la misma fuente que usó el paper
   anterior. Trae **NOCT, dimensiones (Length/Width/A_c) y coeficientes de temperatura reportados
   directamente** (no estimados con ninguna fórmula propia) — resolvió de raíz un intento previo y
   descartado de estimar NOCT con una fórmula de Excel cuyo documento de origen (autoría "Manus AI")
   resultó tener datos de validación que no coincidían con datasheets reales verificados.

## Decisión de diseño: no se inyectan los parámetros SDM crudos

Verificado leyendo `datos/catalogo_paneles_excel.py::cargar_catalogo_paneles()`: el catálogo Excel
**nunca** guarda `I_L_ref/I_o_ref/R_s/R_sh_ref` para ningún panel, ni siquiera los 76 preexistentes
— siempre quedan en `None`, y el Motor IV los recalcula on-demand con `estimar_sdm_desde_ficha()` a
partir de la ficha (Voc/Isc/Vmp/Imp/Ns/CoefT). Por consistencia, este import **no** rompe ese
patrón: los parámetros PVsyst-v6 del paper cumplieron su función real como chequeo de plausibilidad
física de la ficha que sí se importa (ver auditoría abajo), pero no se persisten. El único dato del
paper que sí pasa al catálogo es `gamma_ref` (factor de idealidad real, mejor que una estimación),
como columna `n (Factor Idealidad)`.

## Auditoría real (reutilizando `calculos.modelo_iv.validar_sdm_vs_ficha()`, tolerancia 6%)

| Resultado | Cantidad |
|---|---|
| 🔴 Fuera de tolerancia real de producción (>6% en Voc/Isc/Vmp/Imp/Pmax) | 0 de 278 |
| ⚠️ Dentro de tolerancia, con desviación a revisar (>2%) | 64 de 278 |
| Sin dimensiones físicas en la fuente (solo área total, `A_c`) | 115 de 278 |

Los 64 con desviación se revisaron con 2 casos reales contra ficha oficial de JA Solar 2012
(familia JAP6 72-celdas): buena parte de la desviación (Isc 2-2.6%) ya existía entre la propia
ficha del fabricante y CEC/NREL, explicada por la tolerancia de potencia real que declara JA Solar
("Positive Power Tolerance: 0~+5W", nunca negativa) — no es necesariamente error de traducción, es
tolerancia de fabricación real ya presente en el dato de origen. Cada fila del catálogo documenta
esto explícitamente en su columna `Notas`, incluyendo el % de error de traducción real de ese
módulo específico.

## 2 bugs reales encontrados y corregidos al correr la suite tras el import

El catálogo pasó de ~76 a 354 paneles reales — la primera vez que el catálogo Excel tiene entradas
sin dimensiones físicas completas (`area_m2=None`). Esto expuso un hueco real, ya anticipado en
comentarios previos del código pero nunca activado hasta ahora:

1. **`optimization/variables.py::variable_panel()`** — filtraba solo por `Pmax_stc is not None`,
   no por `area_m2`. `calculos.dimensionamiento.dimensionar_sistema()` revienta con
   `TypeError: unsupported operand type(s) for *: 'int' and 'NoneType'` (`N_paneles * area_m2`) si
   se le pasa un panel sin área. Corregido: el filtro ahora exige ambos.
2. **`calculos/comparador_paneles.py::paneles_excluidos_por_ficha_incompleta()`** — mismo hueco: el
   propio docstring de la función ya decía *"aunque hoy no cambia el resultado... subreportaría en
   silencio el día que el catálogo Excel gane una ficha incompleta"* — ese día llegó. Corregido para
   reportar también los excluidos por `area_m2=None`, así el usuario ve por qué 115 paneles no
   aparecen en 🧩 Comparador de Paneles en vez de que simplemente falten sin explicación.

## Verificación

- `tests/test_comparador_paneles.py::test_paneles_excluidos_por_ficha_incompleta_refleja_el_catalogo_real`
  actualizado: ahora exige 115 excluidos (antes 0), todos por `area_m2` (ninguno por `Pmax_stc`,
  que el import siempre trae real de CEC), y confirma que los 7 ASP-ST1 nunca quedan excluidos.
- `tests/test_optimization_fase4.py::test_generar_candidatos_con_panel_e_inversor_varia_ambos`:
  `max_intentos_por_candidato` subido de 60 a 120 — con el catálogo 4.6x más grande y heterogéneo,
  la tasa de aciertos eléctricos por intento baja (verificado empíricamente con el mismo seed).
- `tests/test_optimization_contract.py::test_variable_panel_opciones_coincide_con_catalogo_real_simulable`:
  el conjunto "esperado" ahora exige también `area_m2 is not None`, igual que el filtro real.
- Suite completa: 942/942 (aislado por archivo, confirmado; la corrida completa en un solo proceso
  es notablemente más lenta ahora — cada test que llama `comparar_paneles()` tarda ~20s real con 285
  paneles JA Solar en el barrido, medido directamente — sin que eso sea un bug, solo el costo real
  de un catálogo 4.6x más grande).

## Script de import

`datos/agregar_paneles_ja_solar_nrel.py` — de uso único, documentado, protegido contra duplicados
(si se re-ejecuta, omite los `TipoPanel` que ya existan en vez de duplicarlos). Las rutas a las 2
fuentes CSV no se distribuyen con el repo por tamaño — quedan documentadas en el script para
volver a descargarlas si hace falta reproducir el import.
