# Candidato de validación científica BIPV — NIST Round 2

**Estado:** candidato recomendado para investigación, pendiente de extracción completa del PDF
**Fecha:** 2026-09-22
**No implica:** aprobación de implementación, commit, despliegue ni validación científica de la APP

## Referencia principal

**Artículo:** *Measured Performance of Building Integrated Photovoltaic Panels—Round 2*

**DOI:** [10.1115/1.1883237](https://doi.org/10.1115/1.1883237)

**Institución/caso:** programa experimental del National Institute of Standards and Technology (NIST).

## Por qué es el mejor candidato actual

El artículo fue diseñado para generar datos de rendimiento BIPV medidos que puedan compararse con modelos predictivos. El caso contiene paneles BIPV verticales, orientados al sur verdadero, integrados en la envolvente del edificio y monitorizados durante 12 meses.

Esto lo hace más adecuado que East2 para comparar resultados finales de la APP:

- East2 no publica energía anual agregada del arreglo.
- NIST Round 2 sí está orientado a la comparación entre medición y modelo.
- La geometría vertical de fachada se acerca directamente al flujo multi-superficie.
- El periodo anual permite comparar energía mensual, anual, PR y sesgo.
- La configuración aislada/no aislada permite investigar pérdidas térmicas.

## Clasificación arquitectónica

Este no es un caso multi-fachada en el sentido del contrato físico de la APP.
Es un caso **multi-panel en una fachada vertical común**, con orientación sur
compartida y variantes constructivas de aislamiento posterior.

Por tanto, sirve principalmente para validar:

- SDM y rendimiento eléctrico;
- temperatura y pérdidas térmicas;
- energía mensual/anual y PR;
- diferencia entre panel aislado y no aislado.

No debe presentarse como validación de:

- varias superficies con tilt/azimuth distintos;
- sombra independiente por superficie;
- inversores dedicados/compartidos entre fachadas;
- agregación física multi-superficie completa.

East2 conserva la función complementaria de validar geometría y sombreado por
superficie. NIST Round 2 sería un benchmark eléctrico/térmico de una fachada
vertical, no un sustituto del caso multi-fachada.

## Información confirmada por metadatos y abstract

- Ocho paneles BIPV monitorizados durante 12 meses.
- Paneles instalados verticalmente y orientados al sur verdadero.
- Integración como parte de la envolvente del edificio.
- Tecnologías: silicio monocristalino, silicio policristalino, a-Si de unión tándem y CIS.
- Para cada pareja se compara un panel con aislamiento posterior y otro sin aislamiento.
- Objetivo: producir datos para evaluar modelos computacionales de rendimiento BIPV.

## Datos que deben extraerse del PDF antes de simular

No deben inventarse ni completarse con defaults:

- marca, modelo y ficha eléctrica de cada panel;
- potencia nominal, Voc, Isc, Vmp, Imp y área;
- número de módulos, strings y paralelos;
- orientación y geometría exacta;
- coordenadas y altitud del sitio;
- periodo, resolución y fuente meteorológica;
- irradiancia y temperatura usadas;
- temperatura de módulo o variables para reconstruirla;
- aislamiento posterior, ventilación y configuración constructiva;
- inversor, eficiencia y potencia AC nominal, si existe;
- energía DC/AC mensual y anual medida;
- PR, pérdidas o métricas de error publicadas;
- tablas, figuras o datos suplementarios necesarios para la comparación.

## Compatibilidad esperada con la APP

### Puede reproducirse razonablemente

- fachada vertical y orientación sur;
- POA por superficie;
- modelo eléctrico SDM;
- temperatura NOCT o modelo térmico disponible;
- energía DC/AC;
- pérdidas y PR;
- comparación mensual/anual;
- sensibilidad a tilt, azimuth, TMY y configuración eléctrica.

### Puede quedar fuera de equivalencia

- temperatura de fachada ventilada o aislada si requiere CFD;
- transferencia térmica detallada del cerramiento;
- condiciones de viento no modeladas;
- curva I-V medida del módulo;
- inversor no identificado o sin ficha completa;
- datos meteorológicos horarios no publicados;
- resultados disponibles solo como gráficos sin datos numéricos.

## Criterio de selección

El caso solo debe avanzar a implementación si el PDF permite extraer suficientes entradas y al menos una métrica final comparable. El mínimo recomendado es:

1. geometría y ubicación;
2. ficha eléctrica del panel;
3. configuración eléctrica;
4. fuente o serie meteorológica utilizable;
5. energía mensual o anual medida;
6. definición de la métrica de comparación.

Si faltan esos datos, el resultado debe clasificarse como **parcialmente reproducible**, no como validación.

## Ranking de candidatos

1. **NIST Round 2** — mejor equilibrio entre fachada vertical, medición anual y objetivo de validación.
2. **Li et al., 2015, PV double-skin facade**, DOI `10.1002/pip.2727` — mejor validación estadística publicada, con RMSE mensual AC de 2.47%, pero exige modelar una doble piel semitransparente.
3. **NIST Round 1**, DOI `10.1115/1.1385824` — primer conjunto de mediciones BIPV, útil para térmica e integración en fachada.
4. **Facade-BIPV optimizer**, DOI `10.3390/buildings14123850` — útil para sombreado eléctrico y optimizadores, menos adecuado como validación anual principal.
5. **BIPV 70.6 kWp PVSol**, DOI `10.17485/ijst/v18i7.3972` — resultados finales disponibles, pero menos cercano al problema de fachada y sombra por superficie.

## Regla de interpretación

La APP no debe afirmar que reproduce NIST hasta comparar entradas equivalentes. La salida debe separar:

- valor medido del artículo;
- valor simulado por el artículo, si existe;
- valor calculado por la APP;
- diferencia absoluta y porcentual;
- fuente y confianza;
- supuestos añadidos.

El veredicto inicial esperado, salvo que el PDF aporte todos los datos, es **reproducido con supuestos** o **parcialmente reproducido**.

## Referencia asociada verificada

La referencia [5] del artículo Round 2 fue localizada como *Short-Term
Characterization of Building Integrated Photovoltaic Panels*, Fanney, Dougherty
y Davis:

- versión de revista: `10.1115/1.1531642`;
- versión de conferencia relacionada: `10.1115/SED2002-1055`.

Su abstract confirma que describe el aparato y los procedimientos para capturar
los parámetros eléctricos necesarios para modelar paneles BIPV. El texto
completo y sus tablas no fueron accesibles desde este entorno: los enlaces PDF
oficiales ASME devolvieron `HTTP 403` y no se localizó una copia abierta legítima.
Por tanto, la referencia es una pista prioritaria, no evidencia suficiente para
desbloquear todavía la simulación NIST Round 2. Ver
`references/verificacion-referencia-5-nist-short-term-characterization.md`.
