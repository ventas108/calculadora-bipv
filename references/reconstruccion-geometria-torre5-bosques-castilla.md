# Reconstrucción de geometría 3D — Torre 5, Bosques de Castilla

**Fecha:** 2026-09-22. **Rama:** `validacion-nist-medido-predicho-2003` (sin
commits nuevos). **Resultado:** no se construyó ninguna escena Site Designer ni
JSON de geometría en esta ronda. Se encontró evidencia real nueva y valiosa (una
elevación acotada publicada por la propia tesis), pero **insuficiente** para un
modelo 3D de obstrucción con validez física sin fabricar dimensiones que no están
publicadas. Clasificación: **C — datos insuficientes para validar la geometría**
(mejora sobre la ronda anterior, que cerró en D sin ninguna evidencia real nueva).

## 0. Qué se intentó y qué no

- **No se usó Google Earth interactivo.** Este entorno de ejecución no tiene
  acceso a un navegador controlable en esta corrida — no se intentó ni se simuló.
  En su lugar se usaron dos fuentes con el mismo propósito (evidencia geométrica
  del sitio), documentadas explícitamente como sustitutos, no como Google Earth:
  1. La captura aérea de Google Maps que la propia tesis ya publica (Figura 5, p.34,
     "Fuente propia" de los autores, sin fecha ni escala visible).
  2. Consultas programáticas a OpenStreetMap (Nominatim + Overpass API) para
     buscar un polígono de edificio real nombrado "Bosques de Castilla" o
     "Torre 5" cerca de 4.634, -74.148.
- **Sí se releyó el PDF de la tesis en las páginas relevantes** (33-38, sección
  3.3 "Análisis de fachada del edificio") — ahí apareció el hallazgo principal de
  esta ronda: una elevación 2D acotada en AutoCAD de la fachada sureste (Figura 4),
  no reportada como dato explotable en las rondas anteriores de esta sesión.

## 1. Evidencia de Google Earth utilizada

Ninguna directa. Sustitutos usados (ver §0), ambos de menor calidad evidencial que
una inspección real de Google Earth con medición de distancias:

- **Figura 5 de la tesis** (p.34): captura de pantalla de Google Maps, vista
  aérea, con rótulos N/S/E/O y compás superpuestos por los propios autores.
  Confirma cualitativamente que el edificio no tiene ninguna fachada orientada
  exactamente al sur y que hay construcciones vecinas alrededor — no permite
  medir distancias porque no trae escala ni fecha de la imagen.
- **OpenStreetMap, Nominatim** (`nominatim.openstreetmap.org/search`, consultado
  en esta ronda): "Bosques de Castilla" existe como polígono de uso de suelo
  (`landuse=residential`), centroide lat=4.6369789, lon=-74.1484100, bounding box
  aproximado 4.6360897-4.6376653 / -74.1492790–(-74.1475395) (≈175 × 130 m). Esto
  es el COMPLEJO completo, no la Torre 5 individual — está a ≈330 m del punto
  leído de las Fig. 6/7 de la tesis (4.634,-74.148), consistente a la escala de
  "mismo conjunto residencial", no una confirmación de la torre exacta.
- **OpenStreetMap, Overpass API** (consultado en esta ronda, dos búsquedas): (a)
  búsqueda de edificios/relaciones con nombre que contenga "Castilla" o "Torre"
  en 600 m — apareció "León de Castilla apartments" (conjunto DISTINTO, más al
  norte) y varias relaciones de escala barrio/UPZ, ninguna es Torre 5. (b)
  búsqueda de todos los edificios en 150 m de 4.634,-74.148 — 7 resultados, todos
  sin nombre o con nombres comerciales ("Eximarket", "Panadería"), ninguno con
  `building:levels=13` ni identificable como Torre 5. **Resultado: intento
  fallido, documentado, no se fuerza una correspondencia.**

## 2. KML/KMZ/GeoJSON/OBJ original

No existe ninguno correspondiente a Bosques de Castilla en el repositorio (ya
verificado en la ronda anterior: `find` sobre todo el árbol solo encontró
`attached_assets/SUBUD_TESAUQUILLO_teja_fv_ULT_1786029427006.obj`, un proyecto
SketchUp de un sitio distinto — descartado).

## 3. JSON original exportado desde Site Designer

No fue posible obtenerlo. El archivo que el usuario pegó/referenció
(`site-designer-2026-07-14-1606-10.json`) es, verificado byte a byte, idéntico a
`attached_assets/site-designer-2026-07-14-1606-10_1786198985402.json`: un único
bloque `TreeBlock` (árbol decorativo) en lat=4.702/lon=-74.147 — no es una
modelación de Torre 5. No se generó ningún JSON alternativo en esta ronda: dado
que no hay footprint (profundidad de la torre), ni protrusión real de los
balcones, ni posición real de los árboles, construir un JSON ahora exigiría
inventar esas tres magnitudes, lo que viola la regla de no fabricar geometría.

## 4. SHA-256 del JSON

No aplica — no se generó ningún archivo de escena en esta ronda.

## 5. Coordenadas

Sitio: **lat=4.634, lon=-74.148** (Fig. 6/7 de la tesis, brújula fotografiada,
ya usado en todas las rondas anteriores de esta sesión). Confirmado a escala de
conjunto residencial por Nominatim (§1) — no a nivel de torre individual.

## 6. northOffset

No aplica — no se construyó escena. Nota metodológica para cuando sí se
construya: si la escena se modela directamente en coordenadas ENU verdaderas
(X=Este, Y=Norte ya alineado con el norte real, usando los azimuts pvlib ya
verificados 249°/162°), `northOffset=0` sería una elección de construcción, no
una medición — debe declararse así explícitamente, nunca como "northOffset
verificado = 0" sin esa aclaración.

## 7. Elevación

2550-2660 m, impresa en las propias Fig. 6/7 de la tesis (dos lecturas de GPS de
teléfono en dos fotos distintas, mismo lugar, valores ligeramente distintos —
consistente con imprecisión típica de GPS de teléfono en altitud, ±50-100 m).
Confirmado contra PVGIS=2550 m en rondas anteriores de esta sesión.

## 8-9. Lista y dimensiones de bloques

No se construyó ningún bloque. **Hallazgo nuevo de esta ronda, no bloque pero sí
dimensión real medida:** la Figura 4 de la tesis (p.35, "Boceto 2D diseñado en
AutoCAD, cara sureste del edificio — Fuente propia") es una elevación acotada
con tres cifras impresas en la imagen:

| Cota impresa | Valor | Interpretación | Confianza |
|---|---:|---|---|
| Margen izquierdo | 1,6800 | Probable retranqueo/margen antes de la primera columna de ventanas — no se puede confirmar si se suma al ancho total | Media — unidad no rotulada explícitamente |
| Ancho superior | 17,2905 | Ancho de la franja de ventanas/balcones dibujada (fachada sureste) | Media-alta — coherente con el resto |
| Alto lateral | 36,4178 | Altura total de la fachada dibujada | **Alta** — verificado por chequeo de sanidad: 36,4178 ÷ 13 pisos = 2,80 m/piso, un valor de altura de entrepiso completamente plausible para un edificio residencial real. Esto confirma que las cifras están en **metros** (nunca declarado explícitamente en la figura, se infiere por este chequeo) |

Esta es la evidencia geométrica más fuerte encontrada en las tres rondas de esta
sesión sobre este caso — una cota real, publicada por los propios autores, sobre
la fachada sureste. **Limitación crítica: es una elevación 2D (vista frontal),
no una planta.** No da la profundidad de la torre, y por eso **no alcanza por sí
sola** para construir un bloque 3D — un bloque necesita 3 dimensiones (ancho,
alto, profundidad) y aquí solo hay 2 medidas independientes y confiables (ancho,
alto), ambas de una sola fachada (la sureste). La fachada suroeste no tiene una
elevación acotada equivalente publicada — solo la fotografía de la Fig. 6, sin
cotas.

## 10-11. Puntos SO y SE, y su justificación

**No se generó ningún punto.** Se revisó explícitamente el orden de prioridad
exigido:

1. Modelo real de paneles → no existe.
2. Modelo 3D verificable → no existe (§2-3).
3. Puntos del usuario → no se proporcionaron.
4. Regla geométrica explícita y cuantificada → **evaluado y descartado**: aunque
   ahora se tiene el ancho/alto real de la fachada sureste (§8-9), una regla
   cuantificada para derivar puntos de análisis (p.ej. un punto por piso a media
   altura de cada piso, centrado en el ancho) requeriría además: (a) la
   profundidad/posición 3D de la fachada dentro de la escena (no solo su
   elevación 2D), y (b) el mismo dato para la fachada suroeste, que no está
   publicado con cotas. Aplicar la regla solo a la fachada sureste, y para la
   suroeste asumir las mismas dimensiones "por simetría", sería una inferencia
   no verificada, no una regla cuantificada — se descarta explícitamente.
5. **Se llega al nivel 5: bloquear.** No existe evidencia suficiente para
   generar puntos de análisis con validez física en ninguna de las dos fachadas.

## 12. Incertidumbre geométrica (resumen)

| Dato | Fuente | Observado/Medido/Inferido | Incertidumbre |
|---|---|---|---|
| Lat/lon del sitio | Fig. 6/7 tesis (brújula) | Observado (lectura de foto) | Baja — confirmado contra PVGIS en rondas previas |
| Azimuts SO=249°/SE=162° | Fig. 6/7 tesis (brújula) | Observado (lectura de foto) | Baja — ya verificado, convención Duffie-Beckman coincide |
| 13 pisos | Texto tesis, §3.2-3.3 (múltiples menciones) | Observado (declarado por los autores) | Muy baja |
| Ancho fachada SE ≈17,29 m | Fig. 4 tesis (cota AutoCAD) | Medido (por los autores, cota impresa) | Media — unidad inferida, no rotulada |
| Alto fachada SE ≈36,42 m | Fig. 4 tesis (cota AutoCAD) | Medido (por los autores, cota impresa) | Media-alta — coherente con 13 pisos |
| Ancho fachada SO | — | **No existe** | — |
| Profundidad/footprint de la torre | — | **No existe** | — |
| Balcones como fuente de sombra en SO, 13 pisos | Texto tesis, p.37 | Observado (declarado, sin cota) | Alta — sin profundidad de protrusión |
| Árboles 5-7 m, cubren pisos 1-3 de SO | Texto + Fig. 8 tesis (foto créditada "Prabyc, 2012") | Observado (foto + texto) | Alta — sin posición/distancia a la fachada, y la foto está fechada 2012 (9 años antes de la tesis, 14 antes de hoy) — los árboles pueden haber crecido o sido podados/talados desde entonces |
| Footprint OSM cerca del sitio | Overpass API, esta ronda | Consultado, **sin match confiable** | No usable |

## 13. Confirmación: el EPW no fue insertado en Site Designer

Confirmado. No se generó ningún JSON de escena en esta ronda, así que no hubo
oportunidad de mezclar columnas meteorológicas del EPW dentro de un archivo Site
Designer. El EPW real (`references/bogota-eldorado-iwec.epw`, SHA-256 ya
verificado exacto en la ronda anterior) permanece intacto y sin modificar.

## 14. Instrucciones para usar JSON + EPW juntos en la APP (cuando exista la escena)

Una vez se exporte una escena real (o se complete una reconstrucción provisional
con las dimensiones que faltan, ver §15), el flujo correcto ya implementado en
la app es:

1. Subir el `.json` de Site Designer en la página **Vista 3D** (🗺️) — esto llama
   a `cargar_escena_sitedesigner()`, que calcula `malla_fingerprint` a partir del
   contenido geométrico (bloques, `northOffset`, lat/lon) — **nunca** a partir
   del EPW.
2. Cargar el EPW real en la sección de Recurso Solar de la app (ya está
   versionado en `references/bogota-eldorado-iwec.epw`).
3. Definir los puntos de análisis por fachada (cuando existan, con la
   trazabilidad exigida en §10-11) en la misma página.
4. Pulsar "🌳 Calcular sombra de todas las superficies" — esto ejecuta
   `calcular_fs_horario_por_superficie()` con la malla y el EPW cargados,
   produciendo `p_shade` horario por superficie.
5. `construir_y_recalcular_proyecto_fisico()` aplica `p_shade` sobre el POA
   calculado con el EPW real (`G_eff = G_poa × (1 − p_shade)`, sin separar la
   difusa por SVF, ver informes anteriores de esta sesión).
6. Si se vuelve a subir una escena distinta sin recalcular, `firma_sombra["malla_horizonte"]`
   quedará desactualizada frente a `multisup_malla_meta["malla_fingerprint"]`, y
   `invalidar_sombra_por_cambio_malla()` retira automáticamente la sombra
   obsoleta antes de construir el proyecto (parche ya implementado y aprobado en
   la ronda anterior de esta sesión).

## 15. Qué falta exactamente para subir de clasificación

Para pasar de **C** a **B (reconstrucción provisional, con incertidumbres
explícitas)**, se necesita como mínimo uno de:

- Una **planta** (vista en planta, no elevación) de la torre con cotas, o
- La **profundidad de la torre** medida de cualquier fuente confiable (plano
  arquitectónico, ficha catastral, medición en sitio), o
- Una **elevación acotada de la fachada suroeste** equivalente a la Fig. 4 (para
  no tener que asumir simetría sin verificar).

Para pasar a **A (JSON exportado y geometría real validada)**, se necesita
exportar la escena desde Site Designer siguiendo exactamente las instrucciones
ya entregadas en la ronda anterior de esta sesión (`references/experimento-bloqueado-geometria-real-lasalle-site-designer.md`,
§20): ubicar el proyecto en 4.634,-74.148, modelar Torre 5 con sus obstrucciones
reales, verificar `northOffset` contra las brújulas de las Fig. 6/7, exportar con
**File → Save Model File**, y entregar el JSON sin editar — más los puntos de
análisis reales por fachada.

## Clasificación final

**C — datos insuficientes para validar la geometría.**

No D puro (como la ronda anterior) porque esta ronda sí aportó evidencia real
nueva y citable (la elevación acotada de la fachada sureste, Fig. 4 de la
tesis) — es un avance real en la base de datos disponible. Pero sigue sin ser
suficiente para construir una escena 3D con validez física: falta la
profundidad de la torre, la dimensión equivalente para la fachada suroeste, y
la posición cuantificada de los dos obstáculos reales documentados (balcones,
árboles). Fabricar cualquiera de esas tres magnitudes para completar un bloque
3D violaría la regla de no fabricar geometría — por eso no se construyó ningún
JSON, provisional o no, en esta ronda.

## Archivos modificados / pruebas ejecutadas

Ninguno de código. No se generó ningún JSON de escena. No se modificó el EPW.
Por no haber cambios de código, no se ejecutó regresión de pytest en esta ronda
(no aplica la condición "después de cada modificación"). Único archivo nuevo:
esta copia Markdown.

Sin commit, merge, push ni despliegue.
