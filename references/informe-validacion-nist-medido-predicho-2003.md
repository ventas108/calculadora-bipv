# Informe de validación — NIST 2003, medido versus predicho (SNL/IV Curve Tracer)

**Fecha:** 2026-09-22. **Rama:** `validacion-nist-medido-predicho-2003` (nueva rama aislada,
creada desde `validacion-nist-round2`; ese caso queda descartado y no se usó como base de este
análisis, evaluado desde cero como pide el encargo). **Commit/push/deploy:** ninguno.
**Cambios de código:** ninguno — ver §5 (Fase 2, gate) sobre por qué no procede Fase 4.

## 0. Fuente y verificación bibliográfica

- **Artículo:** *Measured Versus Predicted Performance of Building Integrated Photovoltaics*.
  Davis, M. W.; Fanney, A. H.; Dougherty, B. P. *Journal of Solar Energy Engineering*
  (Trans. ASME), Vol. 125, pp. 21–27, febrero 2003.
- **DOI:** [10.1115/1.1532006](https://doi.org/10.1115/1.1532006) — confirmado impreso en el
  propio PDF ("[DOI: 10.1115/1.1532006]", pág. 21, final del abstract).
- **PDF descargado:** fuente oficial del NIST (`https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=860906`),
  el mismo repositorio institucional usado para el PDF de Round 2, no un espejo ni copia
  informal. Guardado en `references/nist-medido-vs-predicho-2003.pdf`.
- **SHA-256 del PDF:** `249dffe68b2381bf391849749b77a7b5e432628e435bd73a2acf4defd91f7d78`.
- **Extensión:** 7 páginas, leídas **íntegras** — Introducción, Sandia Electrical Performance
  Model (ecuaciones 1–9), Panel Temperature Prediction Models, Modeling Parameters, Model
  Implementation, Results (Tablas 2–4, Figs. 1–3), Conclusion, Nomenclatura, 12 referencias.

## 1. Relación con NIST Round 2 (descartado explícitamente)

Este NO es el mismo conjunto de paneles que `references/informe-validacion-nist-round2-app.md`
(Round 2, datos de 2002). Verificado con evidencia interna del propio artículo:

- Las **tecnologías de celda** difieren: este artículo usa *"crystalline, polycrystalline,
  silicon film, and triple-junction amorphous"* (pág. 21) — Round 2 usaba mono-Si, poly-Si (3
  variantes de vidriado), 2-a-Si y CIS. "Silicon film" y "CIS" no son la misma tecnología.
- El **año de datos** difiere: este artículo analiza el **año calendario 2000** ("During the
  calendar year 2000... Twelve months of performance data was recorded", pág. 21; fechas de
  ejemplo en Figs. 1–3: 02/05/00, 05/04/00, 10/04–06/00, 11/24/00) — Round 2 analiza 2002.
- El número de celdas en serie (Tabla 2, pág. 23) difiere del de Round 2 para las tecnologías de
  película delgada: `Ns`=56 (silicon film) y 11 (triple-junction amorphous) aquí, versus 68
  (2-a-Si) y 42 (CIS) en Round 2 — confirma que son paneles distintos, no un error de lectura.
- Coincidencia parcial notable: el panel monocristalino de este artículo (Ns=72, Vmp₀×Imp₀ =
  33.680 V × 3.961 A ≈ 133.4 W) coincide casi exactamente con el panel "A" de Round 2 (Ns=72,
  133 W nominal, "instalado desde septiembre de 1999") — es razonable, aunque no confirmado
  explícitamente en este artículo, que sea la MISMA unidad física reutilizada entre la Ronda 1
  (este artículo, año 2000) y la Ronda 2 (año 2002). No se afirma con certeza porque este
  artículo no lo declara.
- Este artículo cita como referencia [4] *"Fanney, Dougherty, Davis, 2001, Measured Performance
  of Building Integrated Photovoltaic Panels, ASME J. Sol. Energy Eng., 123(1), pp. 187–193"* —
  es decir, la **Ronda 1** del mismo programa NIST, publicada un año antes que este artículo de
  predicción. Este artículo de 2003 es, con alta probabilidad, el análisis de predicción
  aplicado a los paneles de la **Ronda 1**, no de la Ronda 2.

Esta distinción se mantiene sin ambigüedad en el resto del informe: **medición** = este
artículo (2003, año de datos 2000); **predicción publicada** = el modelo SNL (King, Sandia
National Laboratories) y la variante SNL/NIST (con el modelo térmico propio de NIST), ambas
evaluadas por los mismos autores en este mismo artículo; **APP** = calculadora-bipv, no
ejecutada en esta ronda (ver §5).

## 2. Fase 1 — Extracción exacta (con página/tabla/figura)

| Campo | Valor | Página/Tabla/Fig. | Estado |
|---|---|---|---|
| Ubicación | NIST, Gaithersburg, MD 20899-8632 | Encabezado de autores, pág. 21 | Publicado (dirección); sin coordenadas/altitud en este artículo |
| Coordenadas / altitud | No se publican en este artículo | — | Ausente |
| Orientación / tilt | No reafirmado explícitamente en este artículo; el texto remite al mismo banco de pruebas BIPV descrito en Ref. [2] ("Building Integrated Photovoltaic Test Facility") y Ref. [4] (Ronda 1), ambas ya conocidas como vertical/sur | pág. 21, Refs. [2],[4] | **Inferido por referencia directa**, no publicado en este artículo |
| Geometría / dimensiones de panel | No se repite Tabla 1-tipo de Round 2 en este artículo (solo Ns por tecnología, ver abajo) | — | Ausente en este artículo específico |
| Marca/modelo de cada panel | No se identifica fabricante ni modelo para ninguna de las 4 tecnologías | — | Ausente |
| **Isc₀, Imp₀, Voc₀, Vmp₀** (por tecnología, a condiciones de referencia) | Mono: Isc=4.375 A, Imp=3.961 A, Voc=42.926 V, Vmp=33.680 V · Poly: 4.250/3.818/41.498/32.944 · Silicon Film: 5.114/4.488/29.614/23.165 · Triple-Junction Amorphous: 4.440/3.613/23.156/16.037 | **Tabla 2**, pág. 23 | **Publicado — las 4 tecnologías** |
| Coeficientes térmicos (α-Isc, α-Imp, β-Voc, β-Vmp) | Valores completos para las 4 tecnologías, en A/°C y V/°C (y su forma normalizada 1/°C) | Tabla 2, pág. 23 | **Publicado — las 4 tecnologías** |
| Ns (celdas en serie) | Mono=72, Poly=72, Silicon Film=56, Triple-Junction Amorphous=11 | Tabla 2, pág. 23 | Publicado |
| Coeficientes empíricos del modelo SNL (A0–A4, B0–B5, C0–C3, n — funciones de masa de aire, ángulo de incidencia y factor diodo) | Publicados en su totalidad para las 4 tecnologías | Tabla 2, pág. 23 | Publicado, pero es parte del **modelo SNL/King**, no del SDM de un diodo que usa la APP — ver §4 |
| Pmax nominal | No se publica como "Pmax" directo; calculable como Vmp₀×Imp₀ (ej. mono ≈133.4 W) | Derivado de Tabla 2 | Publicado indirectamente (derivable) |
| Número de módulos / configuración eléctrica | Un panel por tecnología por condición (aislado/no aislado) — 4 tecnologías × 2 = 8 paneles, consistente con Round 2 pero paneles distintos | pág. 21 | Publicado a nivel de conteo; sin strings/paralelo explícitos más allá de Ns por panel |
| Aislamiento posterior / construcción | 4 pares, uno sin aislamiento posterior y otro con aislamiento de 102 mm (4 in) de poliestireno extruido, R=3.5 m²·K/W nominal | pág. 21 | Publicado |
| Modelo térmico de montaje (SNL) | Tabla 1: parámetros a, b, ΔT para "Open Rack Glass/Cell/Glass", "Close Roof Mount Glass/Cell/Glass", "Open Rack Glass/Cell/Tedlar" — el propio artículo aclara que ninguno aplica con precisión al montaje real del *test bed*, se usó el más apropiado disponible | **Tabla 1**, pág. 22 | Publicado, con **aproximación ya reconocida por los propios autores** |
| Modelo térmico NIST (capas del panel) | Tabla 3: espesor/densidad/calor específico/conductividad térmica de vidriado, celda, respaldo y aislamiento, por tecnología | **Tabla 3**, pág. 23 | Publicado en detalle, pero excede el modelo térmico NOCT simplificado de la APP — ver §4 |
| Fuente meteorológica, periodo, resolución | Estación meteorológica de techo (GHI, DHI, DNI, T_amb, viento) + estación de pared en el plano de los paneles (POA, viento, T_amb); año calendario 2000 completo; muestreo cada 5 min | pág. 21 | Publicado (metodología) |
| Irradiancia, temperatura, viento (serie numérica) | **No se publica como archivo/tabla anual.** Solo aparecen valores numéricos puntuales: energía solar diaria en 3 días concretos (4462, 512 y 1461 Wh/m² — tabla de la Fig. 2) e irradiancia promedio en 2 días concretos (580 y 210 W/m² — texto de Fig. 3) | Figs. 1–3 y su tabla incorporada, pág. 25–26 | **Ausente como serie anual utilizable**; presente solo como 5 puntos de datos ilustrativos |
| Energía DC medida mensual/anual | Implícita en las cifras de diferencia % de la Tabla 4 (la medición es el 100% de referencia), pero no se publica el valor absoluto de energía medida en kWh | Tabla 4, pág. 24 | Publicado como base de la comparación %, no como cifra absoluta en kWh |
| Energía DC predicha mensual/anual | Ídem — publicada como % de diferencia respecto a la medición, para SNL y SNL/NIST, 8 paneles × 12 meses + total anual | **Tabla 4**, pág. 24 | **Publicado — 96 valores mensuales + 8 totales anuales, ambos modelos** |
| Energía AC | No aplica — no se menciona inversor en ningún punto del artículo; el sistema es de caracterización DC en su punto de máxima potencia | — | No aplica |
| PR, RMSE, MBE | No se reportan estas métricas con esos nombres; la métrica usada es **diferencia porcentual de energía acumulada** y **R² de correlación punto a punto** | Tabla 4, pág. 24 | Publicado, con nombres de métrica distintos a RMSE/MBE/PR |
| Bias anual | La "Diff (%)" anual de la Tabla 4 es, en efecto, un sesgo (bias) relativo anual por panel y modelo | Tabla 4, pág. 24 | Publicado (equivalente funcional a bias anual) |
| Incertidumbre experimental | "A 95% de confianza, la incertidumbre expandida de la energía eléctrica medida es ±1.2%"; temperatura de celda y ambiente ±0.3 °C (95%) | pág. 24 | Publicado |
| Parámetros y modelo IV Curve Tracer/SNL | Modelo eléctrico de Sandia (King, Ref. [10], "Sandia's PV Module Electrical Performance Model, Version 2000"), implementado en el software comercial **IV Curve Tracer** (Maui Solar Software) y verificado de forma independiente contra una subrutina FORTRAN/TRNSYS propia de NIST (acuerdo del 0.25% entre ambas implementaciones) | pág. 21–23 | Publicado en detalle — ecuaciones (1)–(9), Tablas 1–3 |
| Modelo térmico NIST vs. SNL | Dos modelos de temperatura de celda comparados explícitamente: el de SNL (superficie trasera, Ec. 10–11) y el transitorio multicapa de NIST (Ref. [5]) | pág. 22–23 | Publicado en detalle |
| Tablas/figuras suplementarias | Tabla 1 (montajes SNL), Tabla 2 (ficha eléctrica completa), Tabla 3 (capas térmicas), Tabla 4 (comparación mensual/anual medición-vs-2 modelos), Figs. 1–3 (ejemplos de días concretos) | Todo el artículo | Publicado, sin archivo de datos crudos descargable |

## 3. Fase 2 — Gate de reproducibilidad

Las cuatro condiciones exigidas por el encargo, evaluadas explícitamente antes de considerar
cualquier código:

| # | Condición | ¿Se cumple? | Evidencia |
|---|---|---|---|
| 1 | Ficha eléctrica suficiente para construir el SDM | **Sí** | Tabla 2 da Isc₀/Imp₀/Voc₀/Vmp₀, coeficientes térmicos α/β y Ns para las 4 tecnologías — exactamente el mismo tipo de insumo (Voc/Isc/Vmp/Imp + coeficientes) que ya usa `datos.tecnologias_bipv.SUNPOWER_E20_327` para estimar su SDM en la ronda de East2 |
| 2 | Meteorología numérica o serie reconstruible sin inventar | **No** | Solo existen 5 valores numéricos puntuales (3 energías diarias, 2 irradiancias promedio de días concretos) — no hay una serie horaria ni siquiera diaria para el año completo. Reconstruir un año a partir de 5 puntos sería inventar, no reconstruir |
| 3 | Al menos una magnitud final absoluta comparable | **Parcial** | La Tabla 4 da diferencia % y R² mensual/anual entre medición y 2 modelos — es una comparación real medición-vs-predicción ya publicada, pero expresada como % relativo, no como energía absoluta en kWh |
| 4 | Geometría y configuración suficientemente definidas | **Parcial** | Ns, tecnología y condición de aislamiento están definidos; tilt/azimuth se infieren por referencia directa a la instalación (no se reafirman en este artículo); no hay strings/paralelo eléctrico más allá de un panel por tecnología |

**Resultado del gate: no se cumplen las cuatro condiciones — falla la condición 2 (meteorología)
sin ambigüedad.** Por regla explícita del encargo, esto detiene cualquier implementación.

## 4. Fase 3 — Separación arquitectónica (documentada, no implementada)

Confirmado: es la misma clase de banco de pruebas que Round 2 — **una fachada/superficie
vertical común con paneles lado a lado**, no un caso multi-fachada. Aunque este artículo no
repite la descripción física de la instalación (remite a las Refs. [2] y [4]), la estructura de
Tabla 2/3/4 (4 tecnologías × 2 condiciones = 8 paneles, un solo conjunto de resultados sin
distinguir orientaciones) es consistente con esa misma configuración. **No debe representarse
como varias superficies con orientaciones distintas** en `transicion_multisuperficie.py`; si
alguna vez se implementara (condicionado a resolver el bloqueo de §3), sería una sola superficie
física con 8 variantes de panel, igual que se concluyó para Round 2.

Además, y esto es específico de este artículo: el objeto de estudio real es la **comparación
entre dos modelos de predicción** (SNL puro vs. SNL con modelo térmico NIST), no solo la
medición en sí. Cualquier intento de "reproducir" este artículo en la APP tendría que decidir
contra cuál de los dos modelos comparar — el modelo eléctrico de la APP (SDM de un diodo,
`calculos.modelo_iv`) no es ni el modelo SNL/King ni el modelo térmico transitorio de NIST; sería
un **tercer modelo independiente**, lo cual es exactamente el tipo de comparación de tres vías
que pide el encargo (medición / predicción publicada / APP) — pero solo tiene sentido ejecutarla
si además hay una serie meteorológica real que alimentar, que es justamente lo que falta.

East2 (`references/east2-validacion-informe.md`) sigue siendo el caso de geometría, sombra y
multi-superficie; este artículo, si el bloqueo meteorológico se resolviera algún día, serviría
solo como benchmark eléctrico/térmico de una fachada, nunca como sustituto de esa validación
geométrica — igual que se concluyó para Round 2.

## 5. Fase 4 — Simulación

**No se ejecuta.** El gate de §3 no se cumple (falla la condición 2). Regla explícita del
encargo: *"Si no pasa el gate, no crees un escenario artificial. Produce únicamente el informe
de factibilidad."* Por eso:

- No se creó ningún archivo de prueba ni escenario (`test_escenario_validacion_nist_2003.py` o
  equivalente).
- No se construyó ningún TMY sintético para este caso — a diferencia de East2, donde el
  supuesto de TMY sintético está documentado y aceptado explícitamente en una ronda anterior,
  aquí el propio encargo prohíbe expresamente un "TMY sintético silencioso", y construir uno
  para Gaithersburg-2000 sin ese respaldo previo sería exactamente eso.
- No se tocó ningún archivo de `calculos/`, `pages/` ni `datos/`.
- Regresión física relacionada ejecutada de todas formas, como verificación de higiene (ver §8) —
  sin relación con este artículo, ya que no se generó código nuevo que probar.

## 6. Comparación obligatoria (medición vs. predicción publicada vs. APP)

"Valor de la APP" es "No calculado" en toda la tabla — no se ejecutó el pipeline físico (§5).
Los valores de "predicción publicada" son los que el propio artículo ya reporta (Tabla 4), como
diferencia porcentual respecto a la medición (que actúa como referencia 100%).

| Magnitud | Medición NIST (referencia) | Predicción SNL (publicada) | Predicción SNL/NIST (publicada) | APP | Fuente | Confianza |
|---|---|---:|---:|---|---|---|
| Energía anual — Monocristalino, no aislado | 100% (base) | −1.1% (R²=0.947) | −4.6% (R²=0.951) | No calculado | Tabla 4 | Energía: ±1.2% (95%) |
| Energía anual — Monocristalino, aislado | 100% (base) | −2.5% (R²=0.956) | −4.2% (R²=0.953) | No calculado | Tabla 4 | Ídem |
| Energía anual — Policristalino, no aislado | 100% (base) | −1.4% (R²=0.948) | −4.5% (R²=0.951) | No calculado | Tabla 4 | Ídem |
| Energía anual — Policristalino, aislado | 100% (base) | −5.4% (R²=0.958) | −6.8% (R²=0.953) | No calculado | Tabla 4 | Ídem |
| Energía anual — Silicon Film, no aislado | 100% (base) | +6.2% (R²=0.945) | +1.8% (R²=0.954) | No calculado | Tabla 4 | Ídem |
| Energía anual — Silicon Film, aislado | 100% (base) | +3.0% (R²=0.960) | +0.3% (R²=0.957) | No calculado | Tabla 4 | Ídem |
| Energía anual — Triple-Junction Amorphous, no aislado | 100% (base) | −1.0% (R²=0.967) | −1.7% (R²=0.967) | No calculado | Tabla 4 | Ídem |
| Energía anual — Triple-Junction Amorphous, aislado | 100% (base) | −1.5% (R²=0.966) | −1.9% (R²=0.966) | No calculado | Tabla 4 | Ídem |
| Diferencia global (las 8 unidades, anual) | 100% (base) | Máximo 6.2% (Silicon Film no aislado) | Dentro de ~7% en todos los casos (conclusión del artículo) | No calculado | Texto de Conclusión, pág. 27 | — |
| Temperatura de celda (ejemplo puntual, mono no aislado, día despejado) | Medida, Figs. 1a/1b | SNL subestima en clima frío (Fig. 1a, 05-feb-00) | NIST más cercana a la medición en clima frío | No calculado | Fig. 1, pág. 25 | Temp.: ±0.3 °C (95%) |
| Energía diaria (3 días concretos, mono no aislado) | 4462 / 512 / 1461 Wh/m² (04, 05, 06-oct-00) | Diff −1.0% / −12.3% / −4.2%; R²=0.998/0.958/0.890 | Diff −2.5% / −14.1% / −5.1%; R²=0.997/0.952/0.885 | No calculado | Fig. 2 (tabla incorporada), pág. 25 | — |
| POA anual | No publicado como total | No aplica | No aplica | No calculado | — | — |
| PR | No reportado con ese nombre | No aplica | No aplica | No calculado | — | — |
| Clipping AC | No aplica (sin inversor) | No aplica | No aplica | No aplica | pág. 21 | — |
| RMSE mensual explícito | No reportado con ese nombre — la métrica publicada es Diff(%) y R², no RMSE | — | — | No calculado | Tabla 4 | — |

## 7. Datos ausentes (lista explícita)

- Coordenadas geográficas y altitud del sitio, en este artículo específico.
- Marca/modelo comercial de cualquiera de los 4 paneles.
- Serie horaria o diaria de irradiancia (GHI/DHI/DNI/POA), temperatura ambiente y viento para
  el año 2000 completo — solo existen 5 valores puntuales (§2).
- Energía medida y predicha en unidades absolutas (kWh o Wh) a nivel mensual/anual — solo se
  publica como % de diferencia respecto a la medición.
- Confirmación explícita de tilt/azimuth dentro de este artículo (se infiere por referencia).
- Configuración de strings/paralelo más allá de un panel por tecnología.
- RMSE y MBE con esos nombres exactos (la métrica publicada — Diff% y R² — es funcionalmente
  relacionada pero no idéntica).

## 8. Supuestos explícitos

**Ninguno fue necesario ni se introdujo**, porque no se llegó a construir ningún escenario
(§5). Esta es una diferencia deliberada frente a East2, donde sí se documentaron y reutilizaron
supuestos (TMY sintético clear-sky, `eta_inversor`) precisamente porque ese caso sí superaba su
propio gate de reproducibilidad mínima. Aquí, introducir un supuesto de serie meteorológica
para poder ejecutar algo habría violado la restricción explícita del encargo ("no TMY sintético
silencioso").

## 9. Limitaciones

1. Sin una serie meteorológica real, cualquier ejecución de la APP para este caso dependería de
   inventar un año climático completo — exactamente lo que este encargo prohíbe.
2. La ficha eléctrica (Tabla 2) es rica, pero pertenece al modelo SNL/King, no al modelo de un
   diodo (SDM) que usa la APP — construir el SDM de la APP desde Isc₀/Voc₀/Imp₀/Vmp₀ + α/β es
   posible en principio (mismo tipo de insumo que ya usa `tecnologias_bipv.py`), pero no sería
   una "réplica" del modelo SNL, sino un tercer modelo independiente comparado contra los otros
   dos — coherente con lo que pide el encargo, pero condicionado a resolver primero el bloqueo
   meteorológico.
3. El modelo térmico multicapa de NIST (Tabla 3) excede lo que el modelo térmico NOCT
   simplificado de la app puede consumir directamente.
4. Los propios autores ya reconocen una aproximación en el modelo de montaje SNL (Tabla 1: "no
   aplican con precisión... se usó el más apropiado de las tres opciones") — una limitación
   del artículo original, no introducida por este informe.
5. No se leyeron las referencias [2], [4] y [5] citadas por este artículo (podrían contener
   coordenadas, geometría exacta o series meteorológicas más completas) — quedan señaladas como
   pista concreta para una posible ronda futura, no leídas por estar fuera de los archivos de
   contexto obligatorios de este encargo.
6. La clasificación arquitectónica de "una sola fachada, multi-panel" (§4) no depende de este
   bloqueo de datos y se mantendría igual si se resolviera.

## 10. Clasificación arquitectónica (resumen)

Confirmado: conjunto multi-panel (4 tecnologías × 2 condiciones = 8 paneles) en una única
fachada/superficie vertical común, heredada del mismo programa de pruebas BIPV del NIST que
Round 2 pero con datos y paneles distintos (§1). No debe representarse ni presentarse como
validación multi-fachada.

## 11. Veredicto final

**Parcialmente reproducible.**

- Mejor posicionado que NIST Round 2: aquí SÍ existe una ficha eléctrica completa (Isc₀, Voc₀,
  Imp₀, Vmp₀, coeficientes térmicos, Ns) para las 4 tecnologías — la condición que bloqueaba
  Round 2 por completo. También existe una comparación medición-vs-predicción ya publicada
  (Tabla 4, 96 valores mensuales + 8 anuales, dos modelos), algo que Round 2 no tenía en
  absoluto.
- Sigue bloqueado para una ejecución real de la APP: no hay una serie meteorológica horaria o
  diaria publicada para el año completo — solo 5 valores puntuales ilustrativos — y el encargo
  prohíbe explícitamente sustituir esa ausencia con un TMY sintético no autorizado para este
  caso.
- No se cambia el veredicto sin evidencia nueva: si una ronda futura autoriza leer las
  referencias [2], [4] o [5] y alguna contiene la serie meteorológica completa del año 2000,
  el veredicto podría revisarse a "reproducible con supuestos" o mejor — pero eso no se hizo
  aquí por estar fuera de los archivos de contexto obligatorios de este encargo.

Este veredicto reconoce el valor real de este artículo (ficha eléctrica completa, comparación
de dos modelos ya publicada, metodología con incertidumbres declaradas) sin forzar una
implementación que requeriría inventar la única pieza que falta: los datos meteorológicos del
año completo.

## 12. Validación — advertencias y regresión

No se generó ningún escenario nuevo (§5), por lo que no hay pruebas nuevas que ejecutar. Como
verificación de higiene se re-ejecutó la batería física existente (sin relación con este
artículo, para confirmar que la rama sigue en un estado correcto tras la investigación):

```bash
cd bipv_python
.venv/bin/python -m pytest \
  tests/test_transicion_multisuperficie.py \
  tests/test_sombras_por_superficie.py \
  tests/test_adaptador_multisuperficie.py \
  tests/test_persistencia_multisuperficie.py \
  tests/test_flujo_fisico_multisuperficie_end_to_end.py \
  tests/test_pagina_transicion_multisuperficie.py \
  tests/test_escenario_validacion_east2_sunpower.py -q
```

```
101 passed, 107 warnings in 16.65s
```

Advertencias observadas (ninguna oculta ni convertida en éxito silencioso): 28+4 `UserWarning`
de inconsistencia QCRad, atribuidas —como ya se documentó en la auditoría de East2— a los
*fixtures* sinusoidales preexistentes de `test_transicion_multisuperficie.py` y
`test_flujo_fisico_multisuperficie_end_to_end.py`, no relacionadas con este artículo; y
`RuntimeWarning` benigna de `scipy.optimize._chandrupatla` en el solver del SDM. Ninguna
advertencia nueva se introdujo en esta ronda porque no se añadió código.

## 13. Comandos ejecutados

```bash
curl -sL -A "Mozilla/5.0" -o references/nist-medido-vs-predicho-2003.pdf \
  "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=860906"
sha256sum references/nist-medido-vs-predicho-2003.pdf
```
