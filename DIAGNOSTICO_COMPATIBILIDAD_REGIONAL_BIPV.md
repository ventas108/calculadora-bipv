# Auditoría de compatibilidad regional BIPV: panel/tecnología vs. región de Colombia

**Fecha**: 31 de agosto de 2026
**Disparador**: tras la verificación cruzada JRC/Huld (CdTe/CIS/Crystalline), el usuario preguntó si
esa auditoría podría ayudarle a elegir el panel ideal por región — *"estoy seguro que el panel que
evalúe para Bogotá no servirá para el Chocó"*. Compartió luego 2 carpetas de documentos propios sin
terminar de estructurar (`HOJA DINAMICA DE SELECCION PANELES BIPV EINNOVA PARA COLOMBIA` y
`HOJA DINAMICA DE SELECCION BIPV HITIIO PARA COLOMBIA`) con matrices reales de compatibilidad
región×producto. Al preguntar dónde vivía ya esa función, el usuario reveló que **ya existe, en
producción**, en la otra aplicación del mismo repositorio (`client/`, React/TypeScript, deployada en
`bipv.innovacionquimica.com.co`) — pidió explícitamente extraerla de ahí y "optimizarla" combinándola
con el trabajo de JRC/Huld ya hecho, no reinventarla.

## Qué se descubrió en el repositorio (no se adivinó nada)

El mismo repositorio git `calculadora-bipv` contiene **dos aplicaciones separadas**: el Streamlit
Python (`bipv_python/`, en el que se trabajó toda la sesión) y una app TypeScript/React/Node
(`client/`, `server/`, `shared/`) — probablemente el prototipo original antes de la reescritura en
Python, todavía viva en producción bajo otro subdominio.

En `client/src/lib/`:
- **`colombianRegions.ts`**: detección de región climática colombiana por coordenadas, con
  **polígonos geográficos reales** (base IGAC) y algoritmo ray-casting — no solo una tabla de
  ciudades, funciona para cualquier lat/lon.
- **`panelTechnologies.ts`**: catálogo de **63 productos reales** de 3 marcas (17 HIITIO, 18
  EINNOVA, 25 SOLTECH + 3 genéricos) — **SOLTECH es la misma marca del panel ASP-ST1-T40** ya usado
  en el proyecto real Teusaquillo de la app Python (confirmado: la familia `soltech_transparente`
  incluye módulos "ASP-ST1-Txx" con Voc=116,0 V, idéntico al panel real). Cada producto trae
  `regionalCompatibility`: score 1-2-3 (no recomendado/aceptable/óptimo) por cada una de las 6
  regiones climáticas de Colombia (Caribe, Andina, Pacífica, Orinoquía, Amazonía, Insular) + una
  nota técnica real (estructural, estética, salinidad, logística, transmitancia — no solo energía).
- **`PanelTechSelector.tsx`**: ya muestra esto como tarjeta informativa (★★★/★★☆/★☆☆ por región), no
  bloqueante — mismo espíritu que el usuario pidió para la versión Python.

## Extracción programática, no transcripción manual

Para no introducir errores de transcripción con 63 productos reales, se usó Node.js (ya disponible
en el entorno) para **evaluar el array TypeScript real** y volcarlo a JSON, en vez de copiar a mano.
Verificado: dentro de cada una de las 21 familias de producto, todas las variantes (distintas
potencias/transparencias) comparten la misma `regionalCompatibility` — así que las 63 entradas
reales se reducen, sin pérdida de información, a **21 familias únicas**.

## Qué se portó a Python

1. **`datos/compatibilidad_regional_bipv.py`**: las 21 familias reales, generadas directamente desde
   el JSON extraído (`COMPATIBILIDAD_REGIONAL_BIPV`) — mismo score, misma nota técnica, misma marca.
2. **`calculos/regiones_colombia.py`**: `detectar_region_colombia(lat, lon)` — traducción 1:1 del
   algoritmo ray-casting y los polígonos reales de `colombianRegions.ts`, verificada contra el
   **TypeScript original ejecutado con Node** (no solo "se ve razonable") para varias ciudades reales.
   Un caso, Villavicencio, cae en "andina" en vez de "orinoquía" (piedemonte llanero, límite de
   polígono) — **verificado que el TS original también lo clasifica así**: es un límite conocido del
   polígono simplificado real, no un error introducido al portar. No se "corrigió" — se documentó.
3. **`calculos/compatibilidad_regional.py`**: la pieza nueva que combina ambos —
   `clasificar_familia_regional()` mapea el texto libre de tecnología del catálogo real (ej. "CdTe
   pelicula delgada", "Mono PERC Bifacial BIPV", "CIGS") a una de las 21 familias, y
   `evaluar_compatibilidad_regional()`/`evaluar_compatibilidad_regional_desde_ciudad()` arman el
   resultado completo (score, nivel, nota, región detectada, confianza).

### Diseño anti-falso-positivo (mismo principio de toda la sesión)

CdTe y CIS siempre resuelven a una familia representativa razonable (pocas familias, puntajes
similares entre sí — verificado: `cdte_semit`/`cdte_bipv`/`einnova_vidrio` comparten exactamente el
mismo score regional). **Crystalline es distinto**: sus familias reales tienen puntajes MUY
divergentes entre sí para la misma región (ej. Bifacial=1 en Andina vs. Teja BC=3 en Andina, ambas
"Crystalline") — así que `clasificar_familia_regional()` solo asigna una familia Crystalline
específica si hay una palabra clave positiva en el texto (bifacial, flex, curtain/cortina, teja/tile,
antirreflejo, agri, pavimento, fachada). Si no hay ninguna pista, devuelve `None` explícitamente —
nunca un representante inventado con falsa precisión.

## Verificado contra los ejemplos reales ya documentados

Antes de integrar a la app, se corrió contra los 2 ejemplos concretos que el propio usuario había
documentado en el RTF de EINNOVA:

- **"Bifacial 580W en Andina = 1 (rojo, no recomendado)"** → `evaluar_compatibilidad_regional("Mono
  PERC Bifacial BIPV", 4.711, -74.072)` da exactamente `score=1, nivel="no_recomendado"`. ✅
- **"Flexible 250W en Pacífica = 3 (verde, óptimo)"** → `evaluar_compatibilidad_regional("N-Type
  TopCon Flex", 5.69, -76.66)` da exactamente `score=3, nivel="optimo"`. ✅

## Integrado en la app, combinado con JRC/Huld (la "optimización" pedida)

- **📐 Dimensionamiento**: alarma temprana no bloqueante (🔴/🟡/🟢ᵒ vía `st.error`/`st.warning`/
  `st.caption` según severidad) apenas se conoce panel + ciudad — antes incluso de correr Producción.
  Guarda el resultado en `session_state["compatibilidad_regional_bipv"]`.
- **📊 Producción**: el expander "🔬 Segunda opinión — modelo JRC/Huld" (ya existente) ahora también
  muestra, en la misma tarjeta, la auditoría regional — combinando **"¿el PR de este proyecto tiene
  sentido frente a un modelo independiente?"** (JRC/Huld, energía) con **"¿este panel encaja
  físicamente con esta región?"** (matriz portada, criterios más allá de energía) — dos preguntas
  complementarias, no la misma pregunta respondida dos veces.
- **🧭 El asistente**: `contexto_sesion()` ahora incluye la compatibilidad regional cuando está
  disponible, con el mismo principio que la verificación JRC — nunca inventa una auditoría que no se
  calculó de verdad para esa sesión.

## Verificación técnica

21 tests nuevos (`tests/test_regiones_colombia.py`, `tests/test_compatibilidad_regional.py`) + 3 en
`tests/test_contexto_sesion_jrc.py`, incluyendo los 2 casos reales del RTF, la verificación cruzada
del algoritmo de región contra el TypeScript original ejecutado con Node, y el caso de rechazo
anti-falso-positivo. Sintaxis de las 2 páginas modificadas verificada con `ast.parse()`. Suite
completa: **892/892**.
