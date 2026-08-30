# Auditoría del extractor de fichas de inversores — MUST PV3500/PV3600 TLV Series

**Fecha:** 30-ago-2026
**Origen:** el usuario reportó inversores sobredimensionados al correr el catálogo contra la fachada Teusaquillo, y pidió probar el extractor real con 3 fichas de inversores híbridos MUST (distribuidos por Solis Colombia): PV35-8048 TLV, PV35-10048 TLV, PV35-12048 TLV, con el estándar "no deseo más errores e incoherencias en los datos extraídos".

**Archivos auditados** (`C:\Users\Mauricio\Desktop\TODO FICHAS TECNICAS BIPV\TODO INVERSORES\INVERORES SOLIS COLOMBIA\HIBRIDOS  MARCA MUST DE SOLIS`):
- `Inversor-Hibrido-8000W-48V-PV35-Fase-Dividida-TLV-Must.pdf`
- `Inversor-Hibrido-10000W-48V-PV35-Fase-Dividida-TLV-Must.pdf`
- `Inversor-Hibrido-12000W-48V-PV35-Fase-Dividida-TLV-Must.pdf`

## 🔴 Hallazgo crítico — no es un bug de código, es un archivo mal nombrado

El archivo `Inversor-Hibrido-12000W-48V-PV35-Fase-Dividida-TLV-Must.pdf` **NO contiene la ficha de PV35-12048 TLV**. Su contenido real es la ficha de la **serie PV3600 TLV** (modelos PV36-8048/10048/12048 TLV) — verificado extrayendo el texto completo del PDF, no por inferencia:

```
Low Frequency Solar Inverter
PV3600 TLV Series (8KW-12KW)
Specification
Features MODEL PV36-8048 TLV PV36-10048 TLV PV36-12048 TLV
...
MPPT range @ operating voltage(VDC) 64~235VDC
Maximum PV array open circuit voltage 250VDC
```

Comparado con los otros 2 archivos (que sí son PV3500 TLV Series real, con MPPT range 64~145V y Vdc_max=145V), la serie PV36 tiene un rango de tensión MUY distinto (64~235V, Vdc_max=250V) — **no es una variante menor, es una familia de producto diferente**. Además, el diagrama de conexión de la PV36 menciona explícitamente "PV1 input" y "PV2 input" (dos entradas FV separadas), mientras que la PV35 solo menciona "PV input" (una sola) — sugiere que PV36 podría tener 2 MPPT/trackers donde PV35 tiene 1, aunque ninguna de las dos fichas lo declara en su tabla de especificaciones (ver hallazgo de campos ausentes más abajo).

**Los 2 archivos correctos SÍ traen los 3 modelos PV35 reales** (8048/10048/12048 TLV) en una sola ficha combinada de familia — de hecho `Inversor-Hibrido-8000W-...pdf` e `Inversor-Hibrido-10000W-...pdf` son la MISMA ficha de 3 modelos, solo descargada/guardada dos veces con nombres distintos (contenido de texto extraído idéntico, 6.049 caracteres en ambos). Así que el PV35-12048 TLV real **sí está disponible** — solo que en el archivo "8000W" o "10000W", no en el "12000W".

**Corregido (30-ago-2026)**: el archivo se renombró en el escritorio del usuario, de
`Inversor-Hibrido-12000W-48V-PV35-Fase-Dividida-TLV-Must.pdf` a
`Inversor-Hibrido-12000W-48V-PV36-Fase-Dividida-TLV-Must.pdf` — mismo contenido (verificado tras el rename: `modelos_detectados` sigue dando `['PV36-8048', 'PV36-10048', 'PV36-12048']`, Vdc_max=250V), solo el nombre ahora coincide con lo que realmente hay adentro. El PV35-12048 TLV real sigue disponible en cualquiera de los otros dos archivos ("8000W"/"10000W", ficha combinada de familia).

## Valores reales extraídos (tras los 2 fixes de esta auditoría)

| Campo | PV35-8048 TLV | PV35-10048 TLV | PV35-12048 TLV | Fuente |
|---|---|---|---|---|
| Nominal Battery Voltage | 48 VDC | 48 VDC | 48 VDC | tabla, compartido |
| Rated power (CA) | 8.0 kW | 10.0 kW | 12.0 kW | tabla, por modelo |
| Vdc_max (Voc máx. array) | 145 V | 145 V | 145 V | compartido en la ficha |
| Vmppt_min / Vmppt_max | 64 V / 145 V | 64 V / 145 V | 64 V / 145 V | compartido en la ficha |
| I_max_tracker (carga PV) | 100 A | 100 A | 100 A | compartido en la ficha |
| P_dc_max_W | 5.000 W (10.000 W con upgrade opcional a 200 A) | igual | igual | compartido en la ficha |

Los valores de Vdc_max/Vmppt/I_max/P_dc_max son **compartidos por los 3 modelos de la familia PV3500** — el fabricante no los diferencia por modelo en esta ficha (solo Rated power/Surge rating/Maximum charge current/pesos varían por modelo). Esto es coherente con el propio texto de la ficha, no un fallo del extractor.

## Campos que quedan vacíos — y por qué (ninguno es un bug)

| Campo | Estado | Motivo real |
|---|---|---|
| `marca` | vacío | "MUST" no aparece como texto extraíble en las páginas leídas (solo como logo/imagen) — no está en el PDF como texto |
| `modelo` (singular) | vacío | La ficha es multi-modelo (3 columnas); el modelo real se resuelve vía `modelos_detectados` (ver abajo), no vía el campo singular |
| `V_arranque` | vacío | El fabricante no publica una tensión de arranque separada — solo da el rango MPPT (64~145V) y el Voc máximo (145V) |
| `n_trackers` / `n_strings_tracker` | vacío | El fabricante no declara un número de trackers en la tabla de especificaciones (ficha de un solo "MPPT solar charge controller 100A", sin desglose plural) |
| `Isc_max_tracker` | vacío | El fabricante no publica una corriente de cortocircuito separada — solo la corriente máxima de carga (100A) |

**Ninguno de estos 5 es un bug del extractor** — son datos que el fabricante genuinamente no publica en esta ficha. El extractor hace lo correcto al dejarlos en blanco en vez de inventar un valor.

## Bugs reales de código encontrados y corregidos

### 1. `P_dc_max_W` no se extraía por un typo real del fabricante ("Maximim" en vez de "Maximum")

La ficha imprime literalmente **"Maximim PV array power 5000W(10000W for 200A optional)"** — nótese "Maxim**i**m", no "Maxim**u**m". Ningún patrón `Max(?:imum)?` de los ~15 que ya existían para este campo lo cubre, porque "Maximim" no es "Max" + el sufijo opcional "imum": es una palabra distinta letra por letra. El valor (5.000 W, dato real y explícito) se perdía por completo.

**Corregido**: nuevo patrón en `calculos/pdf_inversor_extractor.py::_PAT_PDCMAX` — `Maxim(?:um|im)\.?\s+PV\s+(?:array\s+)?[Pp]ower...` — cubre ambas grafías (correcta y con el typo real), sin afectar ningún patrón existente. 2 tests nuevos (grafía correcta + typo).

### 2. `modelo` confundía el encabezado de sección "INVERTER" con un código de modelo real

Para la ficha PV3600 (el archivo mal nombrado), el campo singular `modelo` devolvía **"INVERTER"** — un encabezado de fila de tabla ("INVERTER\nOUTPUT\n...") que quedó aislado en su propia línea tras la extracción de pdfplumber, y que cumplía por coincidencia la forma genérica que `_extract_model()` busca (todo mayúsculas, 5-35 caracteres, sin espacios raros).

Este patrón de encabezado de sección en mayúsculas ("INVERTER", "OUTPUT", "BATTERY", "SPECIFICATIONS", "MECHANICAL", "PROTECTION", etc.) es común a **muchas** fichas de inversores, no solo esta — así que el fix es general, no específico de MUST.

**Corregido**: nueva lista `_SECCION_HEADERS_GENERICAS` en `calculos/pdf_inversor_extractor.py`, excluida de `_extract_model()`. 2 tests nuevos.

⚠️ **Impacto real en el flujo de la app antes de este fix**: bajo — `pages/15_🔌_Catálogo_Inversores_PDF.py` ya obliga a elegir explícitamente el modelo real desde `modelos_detectados` cuando una ficha cubre varios modelos (no usa el campo `modelo` singular en ese caso), y muestra una alerta 🚨 cuando ninguna columna por modelo se pudo leer. El campo `modelo="INVERTER"` nunca se habría guardado en el catálogo real sin que el usuario lo notara y corrigiera manualmente en el selector — pero seguía siendo un dato incorrecto en la salida cruda del extractor, y valía la pena corregirlo en la fuente.

## 🔴 Bug real #3 (más serio) — confusión AC/DC, encontrado con las fichas PV3300

El usuario corrió el extractor sobre las 2 fichas PV3300 TLV Series (3000W/24V) y pegó el resultado del formulario real de la app. Comparado contra una extracción fresca del PDF real, **los valores no coincidían**: el formulario mostraba `Vdc_max=145`, `Vmppt_min=64`, `I_max_tracker=100` — pero la ficha PV3300 real, verificada línea por línea, dice `I_max_tracker=80A±4A` (nunca 100A) y no tiene ningún voltaje MPPT que empiece en 64V. Esos números (145/64/100) son exactamente los de la ficha PV3500 auditada antes en esta misma sesión — indicio fuerte de que el formulario mostraba el resultado de una carga anterior, no de la ficha PV3300 recién subida (no se pudo confirmar la causa exacta del lado de la sesión de Streamlit del usuario; se recomienda repetir la carga verificando que aparezca el banner "✅ PDF digital procesado correctamente" para la ficha correcta antes de guardar).

Investigando esa discrepancia se encontró un **bug real y potencialmente amplio** en la extracción de `Vdc_max`, no exclusivo de MUST: la ficha PV3300 trae, en su sección de **entrada AC** (red/generador), la línea:

```
Max input voltage 270Vac MAX
```

El patrón genérico de `Vdc_max` (`(?:Input|Array|DC)\s+...[Vv]oltage`) acepta la palabra "Input" sin exigir que venga calificada como "PV" o "DC" — así que capturaba **270 como si fuera el voltaje DC máximo del array FV**, cuando en realidad es el voltaje AC máximo de la red eléctrica. El guard de plausibilidad (50-1500V) no lo detecta porque 270V es un voltaje DC perfectamente creíble — el error es de **origen** (AC confundido con DC), no de rango. El Vdc_max/Voc real de esta ficha es 100V o 145V según el submodelo (`"Maximum Solar Input Voltage 100±2Vdc / 145±2Vdc..."`), nunca 270.

**Por qué esto es más serio que los otros 2 bugs**: `Vdc_max` alimenta directamente el gate de seguridad eléctrica de la app (`Voc_frío ≤ Vdc_max`) — un valor AC confundido con DC podría marcar como "compatible" un diseño de string que en realidad excede el límite físico real del inversor, o viceversa. Y el patrón que falló es genérico (`Max ... input voltage` sin calificador DC), presente en la mayoría de fabricantes — cualquier ficha con una sección de entrada AC fraseada así puede tener el mismo riesgo, no solo MUST.

**Corregido**: ambos patrones vulnerables (`_PAT_VDCMAX`, el primario y su fallback multilínea) ahora excluyen explícitamente cualquier coincidencia donde el número venga seguido de "ac"/"AC" (voltaje de corriente alterna). Verificado tras el fix: `Vdc_max` para PV3300 ahora da `None` (correcto: el dato real varía por submodelo — 100V o 145V — y no hay un único valor global que reportar con certeza, así que dejarlo en blanco es más honesto que adivinar) en vez del 270 fabricado; `I_max_tracker` ahora da 80.0 (el valor real). 1 test nuevo anclado al texto real de la sección AC de esta ficha.

⚠️ **Limitación real que queda, no corregida esta sesión**: PV3300 TLV Series no es una familia "columna por modelo" simple como PV3500 — agrupa 11 submodelos (1012 a 6048) por **voltaje de batería** (12V/24V/48V), cada tier con su propia ventana MPPT (16~95V @12V · 30~130V @24V · 60~130V @48V) y su propia potencia FV máxima (1250W a 5000W). El extractor actual reporta el primer valor de la lista (el del submodelo más pequeño, 12V/1250W) como si fuera el valor "global" de la ficha — no es un dato fabricado (es un valor real, textual, de la ficha), pero sí puede ser el submodelo equivocado si lo que se necesita es un PV33-5048/6048 (24V/48V). Para esos submodelos, verificar manualmente contra la tabla de la sección "Solar MPPT Range @ Operating Voltage" antes de guardar.

## Cobertura de tests — hallazgo aparte

Antes de esta auditoría, `calculos/pdf_inversor_extractor.py` (~1.500 líneas, el motor completo de extracción de fichas de inversores) **no tenía ningún test que llamara a `extraer_parametros_inversor()` ni a sus funciones internas directamente** — toda la cobertura de "inversor" existente prueba lógica de catálogo/compatibilidad con diccionarios ya armados a mano, no el motor de regex en sí. Se creó `tests/test_pdf_inversor_extractor.py` (7 tests, incluido el de la sección anterior) anclado al texto real de esta ficha MUST, como primer test directo del motor de extracción.

## Resultado final

Suite completa: **768/768**. Los 3 bugs de código corregidos y verificados contra las 5 fichas reales (PV35 ×3, PV36, PV3300 ×2); el archivo mal nombrado ya se corrigió en el escritorio (renombrado a PV36) para que no se vuelva a cargar por error como PV35-12048 TLV.
