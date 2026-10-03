# Verificación bibliográfica de la referencia [5] — NIST

**Fecha:** 2026-09-22
**Caso relacionado:** NIST Round 2 — `10.1115/1.1883237`
**Estado:** referencia localizada; contenido completo no accesible en esta ronda

## Identificación

La referencia [5] citada por el informe de NIST Round 2 corresponde a:

**A. Hunter Fanney, Brian P. Dougherty y Mark W. Davis.**

**Título:** *Short-Term Characterization of Building Integrated Photovoltaic Panels*

**DOI de la versión de revista:** `10.1115/1.1531642`

**Versión de conferencia relacionada:** `10.1115/SED2002-1055`

La consulta bibliográfica de Crossref confirma ambos títulos, autores y DOI.

## Qué confirma el abstract

El abstract de la versión de revista declara que:

- NIST ejecutó un proyecto plurianual para comparar rendimiento BIPV medido con predicciones de herramientas de simulación;
- los modelos requieren parámetros que caractericen el rendimiento eléctrico bajo distintas condiciones meteorológicas;
- el artículo describe el aparato experimental y los procedimientos para capturar esos parámetros;
- se estudiaron paneles BIPV customizados monocristalinos, policristalinos y de película de silicio, además de un panel comercial de silicio amorfo de triple unión.

Esto confirma que la referencia es potencialmente relevante para recuperar fichas eléctricas y procedimientos de caracterización que no aparecen en Round 2.

## Qué no puede afirmarse todavía

El abstract no confirma que la referencia publique, para cada panel de Round 2:

- `Voc`;
- `Isc`;
- `Vmp`;
- `Imp`;
- coeficientes térmicos completos;
- curvas I-V numéricas;
- series meteorológicas horarias;
- coordenadas y altitud;
- datos suficientes para calcular POA y energía anual.

No se debe asumir que el artículo contiene todos esos valores solo porque describe el procedimiento para medirlos.

## Acceso comprobado

- DOI de revista: localizado mediante Crossref.
- DOI de conferencia: localizado mediante Crossref.
- Enlaces PDF oficiales ASME recuperados desde los metadatos Crossref:
  - `http://asmedigitalcollection.asme.org/solarenergyengineering/article-pdf/125/1/13/5713034/13_1.pdf`
  - `http://asmedigitalcollection.asme.org/ISEC/proceedings-pdf/doi/10.1115/SED2002-1055/2570785/211_1.pdf`
- Ambos enlaces devolvieron `HTTP 403` desde este entorno.
- OpenAlex no localizó una copia PDF abierta o un repositorio institucional utilizable para esta referencia.
- No se utilizó ninguna copia no autorizada ni se inventaron datos a partir de snippets.

## Consecuencia para NIST Round 2

La referencia [5] es una pista bibliográfica válida y prioritaria, pero no desbloquea todavía la simulación. Con la evidencia accesible:

- el caso sigue siendo multi-panel en una fachada vertical común;
- no es un caso multi-fachada;
- la APP sigue sin poder construir un SDM verificable para los ocho paneles de Round 2;
- no existe aún una serie meteorológica numérica utilizable;
- no se puede comparar energía de la APP contra kWh publicados;
- el veredicto permanece **no reproducible con los datos accesibles**.

## Acción bibliográfica pendiente

Para cerrar definitivamente esta línea hay que obtener la versión completa por una vía legítima:

1. acceso institucional ASME;
2. biblioteca universitaria o préstamo interbibliotecario;
3. repositorio NIST o solicitud directa a los autores;
4. comprobar si NIST conserva anexos, informes técnicos o datasets del proyecto.

Solo después de leer el texto completo y sus tablas se puede decidir si la referencia aporta los parámetros eléctricos faltantes. Hasta entonces, no debe modificarse el código ni construirse un caso sintético atribuido a NIST.
