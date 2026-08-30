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

## ⚠️ Hallazgo real, causa NO encontrada — el formulario mostró datos de una carga anterior (dos veces, con archivos distintos)

Dos veces en esta auditoría (con la ficha PV3300 completa y con la ficha aislada PV33-5048/6048), el usuario subió un archivo real a la app y el formulario mostró valores que **no pueden venir de ese archivo** — coinciden exactamente con los de una ficha PV3500 cargada antes en la misma sesión (`Vdc_max=145`, `Vmppt_min=64`, `I_max_tracker=100`, y en la segunda vez además `Modelo *: PV35-8048`).

**Verificado, ambas veces, que el motor de extracción en sí es correcto**: llamando a `extraer_parametros_inversor()` directamente sobre el PDF real (fuera de la app, el mismo código que usa la página) da los valores correctos de PV3300 (`Vdc_max=100`, `I_max_tracker=80`, `modelos_detectados` con los 11 modelos reales). El problema no está en las funciones de `calculos/pdf_inversor_extractor.py`.

**Se revisó a fondo `pages/15_🔌_Catálogo_Inversores_PDF.py` buscando la causa**: no hay ningún `@st.cache_data`/`@st.cache_resource` en el flujo de subida, y las 3 únicas referencias a `st.session_state` de todo el archivo están en la pestaña "Editar/Eliminar" (confirmación de sobrescritura), completamente fuera de la ruta de "Agregar desde PDF". `res = extraer_parametros_inversor(pdf_bytes)` se recalcula desde cero en cada ejecución del script, a partir de `pdf_bytes = uploaded.read()`. No se encontró ningún mecanismo de caché a nivel de código de la página que explique por qué se mostrarían datos de un archivo distinto.

**No se pudo reproducir ni aislar la causa exacta** — es probablemente un comportamiento del lado de la sesión de Streamlit/navegador del usuario (posible caché del navegador, o alguna interacción con el widget `st.file_uploader` sin `key=` fija), no algo verificable desde el código sin acceso a esa sesión en vivo.

**Mitigación aplicada, no una solución de la causa raíz**: `pages/15_🔌_Catálogo_Inversores_PDF.py` ahora muestra siempre, justo después de subir el archivo, el nombre y tamaño exacto del PDF que se está procesando (`st.caption("📄 Procesando: {nombre} ({tamaño} bytes)...")`), con una advertencia explícita de recargar la página si no coincide con lo que el usuario acaba de elegir. Esto no corrige la causa (desconocida), pero hace el síntoma detectable a simple vista antes de reportar un "bug" que en realidad es una carga anterior mostrándose por error.

**Recomendación al usuario para la próxima vez que esto pase**: recargar la página completa (F5) antes de volver a subir el archivo, o probar en una ventana de navegación privada, para descartar caché del navegador.

## 🔴 Hallazgo más grave de toda la auditoría — 8 columnas del catálogo real nunca existieron; datos de híbrido/batería descartados en silencio en cada guardado

El usuario pidió "una estructura lógica para el descargue de fichas técnicas de inversores híbridos... que matemática y electrónicamente se descarguen de forma coherente". Diseñando esa estructura (ver más abajo) se encontró, verificando contra el catálogo real (no solo el código), un bug de persistencia que llevaba tiempo activo:

`guardar_inversor_excel()` solo escribe columnas que **ya existen** en el encabezado real del Excel — nunca crea columnas nuevas. `pages/15_🔌_Catálogo_Inversores_PDF.py` construye desde hace tiempo un `_row` con `"Marca"`, `"Arquitectura"`, `"Inversor Híbrido (Si/No)"`, `"Voltaje Batería Min/Max (V)"`, `"Notas"`, `"Confianza"` — pero **ninguna de esas 6 columnas existía realmente** en `inversores_catalogo.xlsx` (verificado leyendo el encabezado real con pandas, exactamente como lo hace el loader). Cada vez que alguien guardaba un inversor con esos datos, se descartaban en silencio.

**Confirmado con los 17 inversores MUST reales ya guardados en el catálogo de producción**: los 17 son híbridos verdaderos (confirmado por esta misma auditoría, extrayendo directamente de sus fichas), pero los 17 mostraban `es_hibrido=False` y `bat_voltaje_min/max=None` al cargarlos — no porque el extractor fallara, sino porque el dato correcto nunca llegó a persistirse.

**Corregido**:
1. Se agregaron las 6 columnas faltantes al Excel real (`Marca`, `Arquitectura`, `Inversor Híbrido (Si/No)`, `Voltaje Batería Min (V)`, `Voltaje Batería Max (V)`, `Confianza`, `Notas`), más `Corriente Máxima Carga Batería (A)` (columna nueva de esta sesión, ver más abajo) — 8 en total. Cambio puramente aditivo: no se tocó ninguna columna ni valor existente de los 107 inversores ya catalogados.
2. `cargar_catalogo_inversores()` actualizado para leer también `marca`, `arquitectura`, `bat_corriente_carga_max`, `confianza`, `notas` (antes solo leía 2 de las 8).
3. **Backfill de los 17 registros MUST reales**: `Marca="MUST"`, `Arquitectura="Híbrido / Off-grid"`, `Inversor Híbrido="Si"` para los 17; `Corriente Máxima Carga Batería` con el valor real verificado por familia (60/70/80 A para PV35 y PV36, según el submodelo; en blanco para los 11 PV33 — ver el hallazgo de la tabla multinivel más abajo, no es un dato confiable para esa familia). Ningún otro inversor del catálogo (los otros 90) se tocó.

Verificado tras el fix: los 17 MUST ahora cargan `es_hibrido=True` correctamente.

## Mejora real #9 (idea del usuario, implementada) — inversores híbridos: distinguir "submodelo por potencia" de "voltaje que depende de la batería instalada"

El usuario hizo una corrección conceptual importante sobre este tipo de ficha (inversor híbrido): lo que esta auditoría venía llamando "submodelos" (PV35-8048/10048/12048) son 3 **productos físicos distintos por potencia** (distinta electrónica, peso, corriente máxima) — eso está bien modelado. Pero **dentro de cada uno**, el inversor es agnóstico de química de batería: el instalador conecta la batería real (plomo-ácido/AGM/gel/litio) y el equipo se configura en su propio LCD con los puntos de corte según esa batería. El fabricante del **inversor** no puede publicar un voltaje de batería fijo — y la ficha lo dice explícitamente: `"Output voltage Depends on battery type"`, y los puntos de corte se publican como **rangos** ("Low battery voltage cutoff 40-48VDC for 48VDC mode"), no valores únicos.

**Estado antes**: `bat_voltaje_min`/`bat_voltaje_max` ya quedaban en `None` para estas fichas (ningún patrón existente los capturaba) — correcto por casualidad, pero sin ninguna explicación visible: indistinguible de "el extractor falló" para el usuario.

**Implementado**: nueva detección `_HIBRIDO_DEPENDE_BATERIA_RE` (ancla el texto real `"Depends on battery type"` / equivalente español) → nuevo campo `salida_depende_bateria` en el resultado de extracción. Cuando es `True`:
1. **Override defensivo**: `bat_voltaje_min`/`bat_voltaje_max` se fuerzan a `None` sin importar si algún patrón (actual o futuro) capturó un número — el valor correcto depende de la batería real del proyecto, nunca de la ficha del inversor.
2. **Aviso visible propio** en `pages/15_🔌_Catálogo_Inversores_PDF.py` (`st.info`, distinto de la alerta genérica de campos vacíos): explica por qué esos 2 campos quedan en blanco a propósito y qué debe hacer el usuario (completarlos según su batería real).

3 tests nuevos, anclados al texto real. Suite completa: **776/776**.

## Bug real #8 (corregido) — el campo singular `modelo` devolvía el encabezado multi-modelo completo

Confirmado el fix del bug #6 con una recarga limpia (la advertencia de nombre de archivo del hallazgo anterior mostró correctamente `Inversor-Hibrido-PV33-5048-6048-TLV-Must-SUBMODELO.pdf`, 1,8KB — el archivo correcto esta vez), los valores numéricos salieron bien (Vdc_max=145, Vmppt=60-130, I_max=80, P_dc=5000 — todos correctos). Pero el campo **"Modelo \*"** del formulario mostraba `"MODEL PV33-5048 TLV PV33-6048 TLV"` — la fila de encabezado multi-modelo completa, no un nombre de modelo.

**Causa raíz**: `_extract_model()` (el campo singular `modelo`, distinto del detector multi-modelo `modelos_detectados` ya corregido) tiene un "Patrón 1" que acepta cualquier línea que cumpla la forma genérica "todo mayúsculas, 5-35 caracteres" como candidato a nombre de modelo — la fila `"MODEL PV33-5048 TLV PV33-6048 TLV"` cumple esa forma, así que se devolvía completa.

**Corregido**: se excluyen las líneas con 2 o más tokens con forma de código de modelo (usando el mismo patrón `_MODEL_COL_RE` que ya usa el detector multi-modelo) — un nombre de modelo real trae un solo código; 2+ es un encabezado de tabla multi-modelo, no un nombre. Verificado: para las 4 fichas MUST de esta auditoría (PV35, PV36, PV3300 completa, PV33-5048/6048 aislada) `modelo` ahora da `""` consistentemente (correcto — todas son multi-modelo, el usuario elige del selector real) en vez de basura ocasional. Sin impacto en el `modelo` singular de fichas de un solo modelo real (no se tocó esa ruta).

⚠️ **Nota importante**: este campo NUNCA se guarda directamente sin pasar por el selector multi-modelo — `pages/15_🔌_Catálogo_Inversores_PDF.py` bloquea el botón "Guardar" hasta elegir un modelo real del desplegable (`debe_bloquear_guardado()`), así que el bug era de presentación/confusión, no de integridad de datos: no había riesgo de que "MODEL PV33-5048 TLV PV33-6048 TLV" terminara guardado en el catálogo.

1 test nuevo. Suite completa: **773/773**.

## Verificación del submodelo PV33-5048/6048 con ficha aislada

El usuario no podía elegir el submodelo PV33-5048 TLV desde el selector de la app (la ficha de familia completa, 11 modelos, produce un `modelos_detectados` corrupto: entradas basura `PV33-Features`/`PV33-MODEL` y modelos fusionados `PV33-3024 3048`/`PV33-5048 6048` — ver hallazgo aparte más abajo). Pidió generar una ficha PDF aislada para ese par de submodelos y correr la extracción sobre ella.

Se generó `Inversor-Hibrido-PV33-5048-6048-TLV-Must-SUBMODELO.pdf` (entregado en el escritorio del usuario) con **únicamente datos reales**, verificados línea por línea contra el texto completo del PDF original del fabricante (no un fixture inventado) y aislados a solo 2 columnas en vez de 11:

| Campo | PV33-5048 TLV | PV33-6048 TLV |
|---|---|---|
| Rated power (CA) | 5 kW | 6 kW |
| Surge rating | 15.000 VA | 18.000 VA |
| Battery voltage | 48 VDC | 48 VDC |
| Vdc_max (Voc máx.) | 145 V | 145 V |
| Vmppt_min / Vmppt_max | 60 V / 130 V | 60 V / 130 V |
| I_max_tracker (carga PV) | 80 A | 80 A |
| P_dc_max_W | 5.000 W | 5.000 W |

Corriendo el extractor real sobre esta ficha aislada se encontraron **2 bugs más**, ambos corregidos:

### Bug real #4 — el guard AC/DC del bug #3 se podía esquivar por backtracking, truncando el número en vez de rechazarlo

El fix del bug #3 (`(?![Vv]?[Aa][Cc]\b)` tras el número) tenía un defecto propio: cuando el motor de regex de Python no puede satisfacer la aserción con el número completo, **retrocede un dígito y reintenta** — para `"270Vac"`, al fallar con `"270"` (seguido de "Vac"), retrocedía a `"27"` y comprobaba el guard contra el dígito sobrante `"0Vac"`, que **sí pasa** (el `"0"` no es "ac") — capturando **27** en vez de rechazar el match por completo. Encontrado auditando el propio fix de esta misma sesión contra la ficha aislada real.

**Corregido**: grupo atómico `(?>...)` alrededor de la captura de dígitos en ambos patrones del bug #3 — impide que el motor de regex retroceda dentro del número ya matcheado, así el guard se evalúa una sola vez contra el valor completo. 1 test nuevo.

### Bug real #5 — fraseo "Maximum Solar Input Voltage" (con tolerancia "±N") no se leía

La familia PV3300 usa un fraseo de Vdc_max **distinto** al resto de la familia MUST (PV3500/PV3600 usan "Maximum PV array open circuit voltage", ya cubierto): `"Maximum Solar Input Voltage 100±2Vdc / 145±2Vdc..."`. Ningún patrón existente lo cubría — ni por el fraseo ("Solar Input Voltage" en vez de "PV array open circuit voltage"), ni por la tolerancia "±N" pegada al valor, que rompe la adyacencia número→V de los demás patrones.

**Corregido**: nuevo patrón que reconoce el fraseo "Maximum Solar Input Voltage" y tolera el sufijo "±N" (o su variante ASCII "+/-"). 1 test nuevo.

Con ambos fixes, `Vdc_max` de la ficha aislada PV33-5048/6048 pasó de `None` a **145.0** (correcto). Suite completa tras estos 2 fixes: **770/770**.

## 🟢 Bug real #6 (corregido de raíz) — detector multi-modelo producía entradas basura con la ficha de familia completa (11 modelos)

Sobre la ficha ORIGINAL de 11 modelos (no la aislada), `modelos_detectados` daba: `['PV33-Features', 'PV33-MODEL', 'PV33-1012', 'PV33-1512', 'PV33-1524', 'PV33-2012', 'PV33-2024', 'PV33-3024 3048', 'PV33-4024', 'PV33-4048', 'PV33-5048 6048']` — 11 entradas, pero 2 basura (`Features`/`MODEL`, palabras de otra columna/fila que pdfplumber linealizó junto a los nombres reales) y 2 pares fusionados (`3024 3048`, `5048 6048`) en vez de 4 entradas separadas.

**Causa raíz**: la línea de encabezado de esta ficha es 11 veces el mismo token literal `"PV33-"` (sin sufijo, el sufijo numérico vive en la línea SIGUIENTE de continuación). El algoritmo de completado (tanto la rama de "grupos iguales" como el *fallback* por posición horizontal) repartía TODOS los tokens de esa línea de continuación entre las columnas — incluidas las palabras sueltas "Features"/"MODEL" que la preceden (arrastradas de otra columna/fila del PDF original por la linealización de pdfplumber), en vez de reconocerlas como ruido y descartarlas.

**Corregido, en las 2 rutas de reparto**: se filtran los tokens de la línea de continuación para quedarse solo con los que traen al menos un dígito — un sufijo real de variante de modelo (potencia, corriente, código de submodelo) **siempre** trae un dígito; "Features"/"MODEL"/cualquier palabra suelta similar, no. Es la misma condición de forma que la rama de "grupos iguales" ya exigía para *validar* un reparto (línea `~838`), ahora aplicada también para *filtrar* antes de repartir, en ambas rutas (grupos iguales y posición). No afecta el caso Deye/TriP2 documentado en el propio código (`"3P 5K 3P 6K..."` — todos los tokens ya traen dígito, pasan el filtro sin cambios).

Verificado: `modelos_detectados` para la ficha completa PV3300 ahora da los 11 modelos reales, limpios, en el orden correcto:
```
['PV33-1012', 'PV33-1512', 'PV33-1524', 'PV33-2012', 'PV33-2024',
 'PV33-3024', 'PV33-3048', 'PV33-4024', 'PV33-4048', 'PV33-5048', 'PV33-6048']
```
Y las fichas PV35/PV36 (que ya funcionaban bien) siguen funcionando igual — sin regresión.

### Bug hermano encontrado de paso — `P_dc_max_W` por columna no reconocía "Maximum PV Array Power"

Con los 11 modelos ya bien detectados, se verificó que `valores_por_modelo` seguía dando `P_dc_max_W=None` para los 11 — el extractor de la fila de potencia por columna (`_extraer_multimodelo`) no reconocía el fraseo real de MUST ("Maximum PV Array Power 1250W 1250W 2500W..."), solo fraseos de otros fabricantes (SolaX "recommended PV array power", Growatt "for module STC", español "Potencia máxima FV"). **Corregido**: agregado el fraseo "Maximum PV Array Power" a la lista reconocida. Verificado contra la ficha real completa — los 11 valores por columna ahora coinciden exactamente con el texto del fabricante (1250W ×3, 2500W ×4, 5000W ×4, incluidos los 5000W/5000W reales de PV33-5048/6048).

2 tests nuevos, anclados al texto real de la línea de encabezado + continuación de esta ficha. Suite completa: **772/772**.

## 🏗️ Estructura lógica de coherencia (pedida explícitamente por el usuario, 30-ago-2026)

El usuario pidió una "estructura lógica para el descargue de fichas técnicas de inversores híbridos... que matemática y electrónicamente se descarguen de forma coherente, para evitar errores en los datos descargados que afecten los cálculos de producción y diseño". Esto es lo que quedó implementado, en 4 capas — reutilizando y extendiendo `calculos/validador_inversor.py`, no reinventando desde cero:

**Capa 1 — Extracción correcta por campo** (`calculos/pdf_inversor_extractor.py`): cada patrón regex ancla a texto real verificado, con guards defensivos (grupos atómicos contra backtracking, enmascarado de paréntesis con tolerancias, exigir coincidencia 1:1 antes de repartir por posición). Cubre los bugs #1-#8 de este documento.

**Capa 2 — Coherencia física de UN inversor** (`validador_inversor.py::validar_inversor()`, ya existía, extendida esta sesión): invariantes eléctricos universales — Vmppt_min < Vmppt_max ≤ Vdc_max, Isc ≥ I_max, y el techo de potencia FV **P_dc_max_W ≤ Vmppt_min × I_max × n_trackers** (corregido esta sesión: antes usaba Vdc_max, el límite MÁS generoso posible, en vez de Vmppt_min, el peor caso real de mayor corriente — P=V×I, a igual potencia la corriente sube cuando baja el voltaje). Para híbridos sin `n_trackers` publicado (el caso más común en esta familia de productos), se asume 1 tracker en vez de omitir el chequeo por completo.

**Capa 3 — Coherencia entre submodelos de una misma familia** (`validador_inversor.py::validar_coherencia_familia()`, nueva): para fichas multi-modelo, verifica que los campos numéricos por columna (potencia FV, corrientes) sean monótonos no decrecientes en el mismo orden en que el fabricante lista la familia (siempre de menor a mayor potencia, verificado en las 3 familias MUST de esta auditoría). No intenta parsear la potencia del nombre del modelo (varía por fabricante) — es un chequeo genérico, no específico de MUST. Si un campo baja donde otro sube entre el mismo par de modelos, avisa que hay una columna probablemente mal alineada, antes de que el usuario elija ese modelo para guardar.

**Capa 4 — Persistencia íntegra** (`datos/catalogo_inversores_excel.py`): de nada sirven las 3 capas anteriores si el dato ya validado se descarta al guardar — el hallazgo más grave de esta ronda (arriba) fue exactamente eso. Corregido: las 8 columnas que la UI ya intentaba escribir ahora existen realmente en el Excel.

### Nuevo campo: `bat_corriente_carga_max` (idea original del usuario)

Corriente máxima con la que el inversor puede **cargar la batería** (sección "AC CHARGER" de la ficha) — distinta de `I_max_tracker` (corriente máxima del lado FV, sección "SOLAR CHARGER"). Es un dato **fijo del hardware** (no depende de qué batería se instale, a diferencia del voltaje), así que se extrae normalmente. Habilita, a futuro, verificar manualmente si la corriente máxima de carga real de la batería del proyecto es compatible con lo que el inversor puede entregarle — el caso concreto que motivó esta sección (usuario preguntó por una batería de "63A").

⚠️ **Límite real, descubierto verificando contra las 3 familias MUST, no solo una**: para la familia PV3300, esta etiqueta encabeza una tabla de 3 filas (una por nivel de voltaje de batería: 12V/24V/48V), cada una cubriendo solo un subconjunto de los 11 modelos — no una fila 1:1. El extractor detecta este caso (menos valores que modelos) y **deja el campo en blanco en vez de adivinar por posición** — a diferencia de otros campos por columna (P_dc_max_W, I_max_tracker) donde el reparto posicional sí es confiable porque esas filas SÍ son 1:1 con los modelos. Mejor vacío que un dato de seguridad de batería mal asignado a otro submodelo.

### Bug real de paso — `_extract_arch()` clasificaba PV3300 como "trifásico"

La ficha PV3300 se titula literalmente "**Split Phase** Solar Inverter" (monofásico dividido, NO trifásico) — pero el patrón `3P\b` (parte de la detección de "Inversor de red trifásico") matcheaba "3P" en `"Capable of starting electric motor 1P 1P 1.5P 1.5P 2P 3P"` — una lista de potencia de motor en HP abreviada sin la "H", no un indicador de fase. Corregido: `3P\b` → `3P\s*\d+K\b` (exige un código de potencia detrás, patrón real de la familia Deye TriP2 que sí es trifásica genuina — "3P 5K 3P 6K..." — sin romper ese caso). Riesgo genérico: cualquier ficha de cualquier fabricante con una lista de potencia de motor en HP corría el mismo riesgo.

Tests nuevos: `tests/test_validador_inversor.py` (9 tests, primer test directo de este módulo) + 5 tests más en `test_pdf_inversor_extractor.py`. Suite completa: **789/789**.

## Cobertura de tests — hallazgo aparte

Antes de esta auditoría, `calculos/pdf_inversor_extractor.py` (~1.500 líneas, el motor completo de extracción de fichas de inversores) **no tenía ningún test que llamara a `extraer_parametros_inversor()` ni a sus funciones internas directamente** — toda la cobertura de "inversor" existente prueba lógica de catálogo/compatibilidad con diccionarios ya armados a mano, no el motor de regex en sí. Se creó `tests/test_pdf_inversor_extractor.py` (19 tests en total, incluidos los de las secciones anteriores) anclado al texto real de estas fichas MUST, como primer test directo del motor de extracción. También `tests/test_validador_inversor.py` (9 tests) — primer test directo de `validador_inversor.py`.

## Resultado final

Suite completa: **789/789**. Resumen final de esta auditoría: 8 bugs reales de extracción corregidos; el hallazgo más grave (8 columnas del catálogo real que nunca existieron, datos de híbrido/batería descartados en silencio) corregido con backfill de los 17 registros MUST afectados; estructura lógica de coherencia en 4 capas (extracción → un inversor → familia de submodelos → persistencia); 1 campo nuevo (`bat_corriente_carga_max`); 1 bug de clasificación de arquitectura (3P de caballos de fuerza vs trifásico real).
