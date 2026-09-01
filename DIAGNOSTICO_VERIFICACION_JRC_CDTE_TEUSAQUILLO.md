# Verificación cruzada CdTe: power-rating model JRC/Huld vs. SDM De Soto (Teusaquillo)

**Fecha**: 31 de agosto de 2026
**Disparador**: el usuario pidió analizar, "como un científico", un paper académico real
(`S2214157X18303940.htm` y la familia de papers relacionados de Kumar/Sudhakar/Samykano sobre
CdTe BIPV bajo clima tropical) para sacarle provecho práctico a la app. La corrida real del
proyecto Teusaquillo (fachada CdTe vertical, ver `FICHA_PVSYST_TEUSAQUILLO.md`) había dado
PR=100,6%/101,2% con el motor principal — inusualmente alto para un sistema real, y una duda
abierta desde el 27-ago-2026.

## Fuente académica real (no un resumen — texto completo verificado)

De los 3 papers relacionados encontrados, se logró descargar y leer el **texto completo** de:

> Kumar, N.M. (2019). "Performance of single-sloped pitched roof cadmium telluride (CdTe)
> building-integrated photovoltaic system in tropical weather conditions." *Beni-Suef University
> Journal of Basic and Applied Sciences*, 8:2. DOI: 10.1186/s43088-019-0003-2 (Open Access, CC BY).

**Corrección importante a la premisa inicial del usuario**: este paper (y con alta probabilidad
los otros 2 de la misma familia de autores, dado que comparten metodología) usa **PVGIS**
(European Commission JRC), no PVsyst, para simular el sistema.

Metodología real (Tabla 2 del paper): power-rating model de Huld et al. (2011), un ajuste
empírico polinómico calibrado contra mediciones reales de módulos CdTe en el ESTI europeo —
NO un circuito equivalente físico como el SDM De Soto que usa esta app.

```
P(I',T') = I'·P_STC·[1 + t1·ln(I') + t2·ln(I')² + t3·T' + t4·T'·ln(I') + t5·T'·ln(I')² + t6·T'²]
Coeficientes CdTe: t1=-0,046689  t2=-0,072844  t3=-0,002262  t4=0,000276  t5=0,000159  t6=-0,000006
T_módulo: Faiman con n=23,37, n*=5,44 (coeficientes de temperatura específicos de CdTe)
```

Resultados reales del paper (CdTe, techo, 7 kWp, Malasia tropical, 7 ángulos 15°-45°):
**PR entre 74,92% y 77,36%**, pérdidas totales entre -23,63% y -25,08%. Un segundo paper de la
misma familia (fachadas CdTe, resumen consultado) reporta **PR entre 66,42% y 76,26%**. Ningún
estudio de la literatura revisada reporta PR por encima de 78% para CdTe BIPV bajo clima tropical.

## La verificación: implementar el modelo y correrlo contra datos REALES de Teusaquillo

Nuevo módulo `calculos/modelo_jrc_cdte.py`: reimplementa el power-rating model con los
coeficientes CdTe exactos del paper, usando `pvlib.temperature.faiman()` (ya en el repo) con
`u0=23,37, u1=5,44` en vez de los genéricos de pvlib (calibrados para c-Si). 6 tests nuevos,
incluyendo el ancla física más simple: a condiciones STC exactas (I'=1, T'=0), el modelo debe
reproducir exactamente P_STC (el corchete se reduce a 1).

`scripts/verificar_jrc_cdte.py <slug>` (generalizado el mismo día, ver sección "Actualización" al
final de este archivo): descarga el TMY REAL de PVGIS para Bogotá (mismas
coordenadas que usa la app: 4,711°N, -74,072°O, 2.600 m), calcula la POA con
`calculos.solar.calcular_poa()` (el mismo pipeline Hay-Davies que usa la app en producción, no
uno paralelo) para una fachada vertical (tilt=90°, azimut=180°), y corre el modelo JRC/Huld sobre
esa serie horaria real con los 128 módulos ASP-ST1-T40 (8,064 kWp).

## Resultado

| | POA anual | E_dc anual | **PR** |
|---|---|---|---|
| App (SDM De Soto, sin Motor Óptico) | 807,8 kWh/m²/año | 6.554 kWh/año | **100,6%** |
| **JRC/Huld (este script, mismos datos reales)** | 807,8 kWh/m²/año | 5.825 kWh/año | **89,4%** |
| Literatura (Kumar, CdTe techo, Malasia tropical) | — | — | 74,9%-77,4% |
| Literatura (Kumar, CdTe fachada, Malasia tropical) | — | — | 66,4%-76,3% |

La POA anual coincide EXACTAMENTE (807,8 kWh/m²/año) entre el script y la app — confirma que
ambos parten de los mismos datos reales de recurso solar, así que la diferencia de PR es
atribuible al modelo de módulo, no a una discrepancia de entrada.

## Conclusión científica

El modelo JRC/Huld, corriendo con los mismos datos reales de Teusaquillo, da un PR **11,2 puntos
porcentuales más bajo** que el motor SDM principal de la app (89,4% vs 100,6%) — un modelo de
CdTe completamente independiente, calibrado contra mediciones reales de otro laboratorio, no
reproduce el >100%.

Al mismo tiempo, el 89,4% de JRC sigue estando **12 a 23 puntos por encima** del rango que reporta
la literatura real para CdTe BIPV en clima tropical (66-77%) — pero esto SÍ tiene una explicación
física razonable: Bogotá (14°C media, 2.600 m) es mucho más fría que Malasia tropical (donde CdTe
opera con más pérdida térmica), y el coeficiente de temperatura de CdTe favorece climas fríos. Un
PR más alto que Malasia es esperable; el modelo JRC ya incorpora esa diferencia climática real
(usa T_ambiente y viento reales de Bogotá) y aun así queda muy por debajo del resultado de la app.

**Con esto, la hipótesis (b) queda más respaldada que la (a)**: el >100% de PR del motor principal
de la app parece ser, con evidencia cuantitativa (no solo sospecha), un artefacto de la curva
FF-vs-irradiancia calibrada específicamente para el ASP-ST1-T40 en el SDM De Soto — no un
comportamiento físico genuino de CdTe a baja irradiancia/clima frío, que el modelo JRC (calibrado
también para CdTe, pero contra mediciones de otro panel/laboratorio) no reproduce en la misma
magnitud.

## Qué NO se concluye (límites honestos de esta verificación)

- No es una prueba definitiva de bug — es evidencia convergente de 2 fuentes independientes
  (literatura + modelo alterno) apuntando en la misma dirección. El resultado real de PVsyst
  (pendiente, ver `FICHA_PVSYST_TEUSAQUILLO.md`) sigue siendo el tercer punto de comparación más
  directo y aún no está disponible.
- El modelo JRC/Huld está calibrado contra módulos CdTe genéricos de laboratorio, no contra el
  ASP-ST1-T40 específico (que sí tiene su propia curva FF-vs-irradiancia calibrada, validada
  contra Batzner et al. 2001) — es razonable esperar CIERTA diferencia entre ambos modelos incluso
  si el SDM de la app fuera correcto; la pregunta es si 11 puntos es "cierta diferencia esperada" o
  señal de una calibración específicamente inflada. No se decide aquí cuál es.
- Este módulo es una verificación cruzada puntual, no reemplaza al motor principal ni se integró a
  la UI de la app — queda como herramienta de diagnóstico en `scripts/`, disponible para volver a
  correrla si se ajusta la calibración del panel o cuando llegue el resultado real de PVsyst.

## Verificación técnica

6 tests nuevos en `tests/test_modelo_jrc_cdte.py` (ancla STC exacta, comportamiento nocturno,
orden de magnitud a baja irradiancia, diferenciación de los coeficientes de temperatura CdTe vs.
los genéricos de pvlib, caso sintético día completo, caso sin irradiancia). Suite completa:
**827/827**. El script de verificación reutiliza `calculos.solar.obtener_tmy_pvgis()` y
`calculos.solar.calcular_poa()` reales (no una reimplementación paralela) — la coincidencia exacta
de la POA anual (807,8 kWh/m²/año) confirma que la comparación es de manzanas contra manzanas.

## Actualización 31-ago-2026 — generalizado para cualquier proyecto guardado

Pedido explícito del usuario tras confirmar que el script solo servía para Teusaquillo (los datos
del sitio/panel estaban fijos como constantes al inicio del archivo): "generalízalo para leer
cualquier proyecto guardado". Renombrado `scripts/verificar_jrc_teusaquillo.py` →
`scripts/verificar_jrc_cdte.py <slug>`, que ahora:

- Lee el JSON del proyecto directamente de `datos/proyectos/*.json` (bypasea
  `calculos.proyectos_manager`, que exige una sesión de Streamlit activa para el aislamiento por
  usuario — este es un script de terminal, no una vista multi-usuario de la app).
- Nueva función pura `calculos/modelo_jrc_cdte.py::extraer_parametros_proyecto(estado)`: deriva
  sitio (vía `datos/ciudades_colombia.py`), geometría (tilt/azimuth/albedo) y potencia STC total
  del proyecto guardado. Rechaza con un mensaje claro (nunca un valor inventado) si el panel no es
  CdTe, si la ciudad no está en el catálogo, o si Dimensionamiento nunca se corrió en ese proyecto.
- `--listar` enumera los proyectos disponibles en disco.

**Verificado que la generalización no cambió el resultado conocido**: se armó un JSON de proyecto
sintético con los valores reales exactos de Teusaquillo (128 módulos ASP-ST1-T40, Bogotá, fachada
90°/180°) y se corrió el script generalizado contra él — reproduce EXACTAMENTE el mismo resultado
que la versión original fija: POA 807,8 kWh/m²/año, E_dc 5.825 kWh/año, PR 89,41%.

7 tests nuevos en `tests/test_extraer_parametros_proyecto_jrc.py` (extracción real anclada a
Teusaquillo, prioridad `N_paneles_granja` > `N_paneles_dim`, rechazo de panel no-CdTe, rechazo sin
panel/ciudad/Dimensionamiento, defaults razonables si faltan tilt/azimuth/albedo). Suite completa:
**834/834**.

## Actualización 31-ago-2026 — generalizado también a CIS, módulo renombrado

Pedido explícito del usuario: *"puedo tambien tener esta auditoría puntual proyecto por proyecto
con paneles CIS... recuerda que los sistemas BIPV necesitan tambien este tipo de tecnologia"*.

**Verificación real antes de implementar** (mismo rigor que con CdTe, nunca coeficientes
inventados): se descargó y leyó el texto completo (no el resumen) del segundo paper de la familia
Kumar/Sudhakar/Samykano — "Performance comparison of BAPV and BIPV systems with c-Si, CIS and CdTe
photovoltaic technologies under tropical weather conditions", *Case Studies in Thermal Engineering*
13:100374, DOI 10.1016/j.csite.2018.100374 (repositorio institucional CityU HK, mismo mecanismo que
dio acceso al primer paper). Su Tabla 4 trae los coeficientes de Faiman + power-rating model para
las 3 tecnologías (Crystalline, CIS, CdTe) — **la fila de CdTe coincide EXACTA con la ya
implementada** (23,37/5,44/-0,046689/-0,072844/-0,002262/0,000276/0,000159/-0,000006), confirmando
que ambas fuentes son consistentes entre sí, no solo internamente.

⚠️ **Nota honesta**: un resumen automático de búsqueda web había sugerido coeficientes CIS
distintos (u0=22,64, u1=3,60) antes de conseguir el texto completo — NO se usaron. Los coeficientes
reales de la Tabla 4 son u0=22,19, u1=4,09 (temperatura) y t1=-0,005554, t2=-0,038724,
t3=-0,003723, t4=-0,000905, t5=-0,001256, t6=0,000001 (potencia). Este episodio confirma la regla
ya establecida en esta sesión: nunca confiar en un número específico de un resumen de búsqueda sin
verificarlo contra la fuente primaria real.

**Módulo renombrado** `calculos/modelo_jrc_cdte.py` → `calculos/modelo_jrc_huld.py` (ya no es
específico de CdTe): `COEFICIENTES_JRC` es ahora un dict por tecnología (`CdTe`, `CIS`), y las
funciones (`potencia_jrc()`, `calcular_pr_jrc()`, `temperatura_modulo_faiman_jrc()`) reciben un
parámetro `tecnologia`. `extraer_parametros_proyecto()` acepta CdTe o CIS, rechazando con mensaje
claro cualquier otra tecnología (ej. c-Si, mayoría real del catálogo, todavía sin coeficientes
verificados aquí). Script renombrado igual: `scripts/verificar_jrc_huld.py <slug>`, que ahora
detecta la tecnología del proyecto sola y muestra el rango de referencia de la literatura correcto
para cada una (CdTe: 66,4%-77,4%; CIS: 72,2%-75,5%).

**Verificado end-to-end con datos reales para ambas tecnologías**: corrido contra un proyecto
sintético CdTe (mismos valores de Teusaquillo) → reproduce el resultado ya conocido exacto
(PR=89,41%); corrido contra un proyecto sintético CIS (100 Wp × 50 módulos, mismo sitio Bogotá) →
PR=91,50% (dentro de un rango físicamente razonable, más alto que el 72-75% de la literatura
tropical por la misma razón climática ya discutida para CdTe: Bogotá es mucho más fría que Malasia).

11 tests en `tests/test_modelo_jrc_huld.py` (4 nuevos: coeficientes CdTe y CIS anclados a las 2
tablas citadas, CIS y CdTe dan potencias distintas para el mismo input, tecnología no soportada
lanza error claro) + 2 tests actualizados en `tests/test_extraer_parametros_proyecto_jrc.py`
(acepta CIS, rechaza tecnología sin coeficientes). Suite completa: **840/840**.

## Actualización 31-ago-2026 — integrado visualmente en 📊 Producción + Crystalline (c-Si) + asistente

Pedido explícito del usuario, en 2 mensajes seguidos: primero preguntó *"si internamente se corre
esta auditoria pero el valor se ubica fisico dentro del modulo respectivo solo para comparacion
visual y verificacion de coherencia... y que el asistente si se le pregunta ayude a explicar de
forma asertiva dicha comparacion... ahi si estariamos hablando de una auditoria"* — confirmado que
sí era posible — y luego: *"implementalo, pero tambien integra en el calculo interno technologies
namely crystalline (c-Si) y asi cumplimos con el ciclo"* (las 3 tecnologías que compara el paper
fuente de los coeficientes de CIS).

### 1. Tercera tecnología: Crystalline (c-Si)

Mismo paper y misma Tabla 4 que dio los coeficientes de CIS — verificados sin research adicional
(ya estaban en el texto extraído): `u0=30,02`, `u1=6,28`, `t1=-0,017237` a `t6=0,000005`. Rango de
referencia propio (mismo paper, mismo sistema 32,7 kWp, así que es directamente comparable con CIS
y CdTe del mismo estudio, sin mezclar configuraciones de estudios distintos): BIPV 71,11%-73,92%,
BAPV 74,18%-76,34%.

### 2. El catálogo real no usa etiquetas limpias — nuevo clasificador

Auditando el catálogo real (`datos/catalogo_paneles_excel.py`) se encontró que NINGÚN panel de
silicio cristalino usa literalmente "Crystalline" ni "c-Si" — el texto real es de fabricante:
"MonoSi", "Mono PERC Bifacial BIPV", "N-Type TopCon Bifacial Agri", etc. (13 valores distintos
reales encontrados). Comparar por igualdad exacta (como hacía la función hasta este punto) habría
rechazado casi todo el catálogo real, no solo los paneles genuinamente sin coeficientes.

Nuevo `clasificar_tecnologia_jrc()`: reglas por palabra clave (nunca adivina — si nada calza,
sigue rechazando con mensaje claro). CdTe se revisa primero. **Aproximación declarada, no
ocultada**: "CIGS" (la variante real presente en el catálogo, no hay panel etiquetado "CIS" a
secas) se mapea a los coeficientes de CIS — son familias de calcogenuro de cobre relacionadas pero
no idénticas; es la mejor aproximación disponible con literatura verificada, documentada como tal
en el docstring de la función.

### 3. Visible dentro de 📊 Producción, no bloqueante

`calculos/modelo_jrc_huld.py::resultado_jrc_desde_sesion(session_state)`: versión "en vivo" que
reutiliza `session_state["poa_df"]`/`["tmy_df"]` (ya calculados por ☀️ Recurso Solar para esa
sesión) — **sin ninguna llamada de red nueva**, a diferencia del script de terminal. Devuelve
`None` (nunca revienta) si la tecnología no aplica o Recurso Solar no ha corrido.

En `pages/6_📊_Produccion.py`, justo después de la nota existente de "PR > 100%" (que afirmaba
"resultado correcto... no es un error de cálculo" sin ningún contraste — exactamente la afirmación
que esta sesión llevaba horas cuestionando con evidencia real): un `st.expander` colapsado con la
comparación (motor principal vs. JRC/Huld, diferencia en puntos porcentuales, rango de literatura),
dejando explícito que **ninguno de los 2 modelos es automáticamente "el correcto"** — nunca
reemplaza al motor principal, solo lo contrasta.

### 4. El asistente 🧭 explicándolo con los números reales de la sesión

El resultado se guarda en `session_state["verificacion_jrc"]` (incluido `None` cuando no aplica,
para que quede explícito que se evaluó y no hubo dato, no que se olvidó revisar). `contexto_sesion()`
(Nivel 1, sin IA — la misma función que ya le dice al asistente qué páginas están listas/pendientes)
ahora incluye una línea con el PR de ambos modelos y la diferencia real, cuando está disponible —
así, si el usuario pregunta "¿por qué difiere el PR?", el asistente responde con los números
REALES de esa sesión, no una explicación genérica del manual.

### Verificación

25 tests nuevos: 15 en `tests/test_modelo_jrc_huld.py` (coeficientes Crystalline, clasificador
contra los 13 valores reales del catálogo + casos de rechazo, `resultado_jrc_desde_sesion()` con
un caso sintético completo verificando que NO llama a red), 3 en
`tests/test_extraer_parametros_proyecto_jrc.py` (acepta Crystalline, acepta 4 textos reales del
catálogo, rechazo con mensaje claro), 3 en `tests/test_contexto_sesion_jrc.py` (primera cobertura
de tests que existe para `contexto_sesion()` en este repo). Sintaxis de `pages/6_📊_Produccion.py`
y `calculos/asistente.py` verificada con `ast.parse()` (fix de página, no unit-testeable
directamente sin un harness de Streamlit — mismo criterio que el resto de fixes de página de esta
sesión). Suite completa: **868/868**.
