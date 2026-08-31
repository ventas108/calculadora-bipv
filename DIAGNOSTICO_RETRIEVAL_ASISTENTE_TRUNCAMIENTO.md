# Bug real: el asistente 🧭 nunca leía la mayoría del changelog reciente (truncamiento silencioso)

**Fecha**: 31 de agosto de 2026
**Disparador**: el usuario pidió confirmar que el asistente citaba bien las 4 secciones nuevas
agregadas hoy (gráfica de compatibilidad eléctrica, Motor IV). Se confirmó que sí — pero al pedir
"revisa qué otras páginas citan mal secciones viejas", la auditoría encontró un bug estructural
mucho más grande en el propio mecanismo de búsqueda del asistente.

## Cómo funciona el asistente (recordatorio)

`calculos/asistente.py::BaseConocimiento.cargar()` parte `datos/base_conocimiento_asistente.md`
en "secciones" cada vez que encuentra una línea que empieza con `##` o `###` (regex
`\n(?=#{2,3} )`). `responder()` busca las 4 secciones más relevantes para la pregunta del usuario
(`buscar(pregunta, k=4)`, por intersección de palabras clave) y les corta el texto a **4000
caracteres cada una** (`s["texto"][:4000]`) antes de mandarlas al modelo.

**Esto significa que cualquier bloque de texto entre dos encabezados `##`/`###`, si supera 4000
caracteres, pierde todo lo que exceda ese límite — en silencio, sin ningún error ni aviso.**

## El bug real encontrado

El patrón de changelog más reciente de este archivo (`Manual actualizado el [fecha]` /
`Novedades de esta versión: ...` / `Versión anterior (...): ...`, usado desde el 27-ago-2026 en
adelante) **nunca usa encabezados `##`/`###` entre entradas** — son párrafos de texto plano
separados solo por líneas en blanco. Como el último encabezado real (`## 24. Anexo —
Actualizaciones del 26 de agosto de 2026`) no se repetía para cada día nuevo, **toda la cadena de
changelog desde el 27-ago hasta hoy (31-ago) — 30 entradas distintas, prácticamente todo el
trabajo real de las últimas 3 sesiones — quedó atrapada dentro de esa única sección**, que llegó a
medir **49.419 caracteres**.

Consecuencia medida: solo los primeros 4.000 caracteres (≈8% del contenido) de esa sección
llegaban alguna vez al modelo — y esos 4.000 caracteres eran literalmente el contenido *original*
del 26 de agosto. Todo lo del 27, 28, 29, 30 y 31 de agosto (los 3 bugs reales de Motor IV, la
gráfica de compatibilidad eléctrica, el N_s de Solar First, la corrección de N_strings/tracker, la
alarma de relación DC/AC, la auditoría de fichas MUST, etc.) **nunca llegaba al modelo cuando esa
sección era la seleccionada** — y peor, cuando SÍ se recuperaba (porque alguna palabra clave
coincidía), la fuente citada al usuario decía *"Actualizaciones del 26 de agosto de 2026"*,
atribuyendo mal la fecha de contenido mucho más reciente.

Auditando el archivo completo se encontraron **15 secciones en total** por encima de 4.000
caracteres (no solo la de 26-ago) — incluyendo secciones antiguas y de alto tráfico esperado como
"11. Página 8 — Presupuesto Bancable" (10.086 caracteres, perdía 6.086) y "17. Preguntas
frecuentes" (7.808 caracteres, perdía 3.808) — es decir, este bug llevaba probablemente **desde el
origen del archivo**, no solo desde el 27-ago.

## Corrección aplicada

Se insertaron encabezados `##`/`###` nuevos en los puntos de quiebre temático/temporal naturales
de cada sección sobredimensionada, sin reescribir ni resumir ningún contenido — solo se dividió.
Continuando la numeración existente de "Anexo" (hasta `## 24.`), se crearon 14 nuevas secciones
`## 25.` a `## 38.` para la cadena de changelog reciente, más subdivisiones `24b`/`24c` para el
propio anexo 26-ago que también excedía el límite. Además se dividieron 7 secciones más antiguas
(Dimensionamiento, Producción, Catálogo de Inversores PDF, Presupuesto Bancable, Preguntas
frecuentes, Anexo 6-7 de agosto) en sus puntos de quiebre temáticos existentes.

**Resultado medido**: de 15 secciones por encima de 4.000 caracteres, quedan **7**, todas con una
pérdida marginal (6 a 1.430 caracteres, ninguna arriba de los ~1.400) frente a las pérdidas
originales de hasta 45.419 caracteres. Las 2 más grandes que aún exceden levemente ("Auditoría del
pipeline de cálculo" y "Bug real corregido: clipping", ambas con menos de 120 caracteres perdidos)
se dejaron así a propósito — lo que se pierde es una lista de 2-3 líneas sin información nueva, no
vale el riesgo de una edición más para un beneficio marginal.

**Verificación real, no solo teórica**: se probaron 15 preguntas realistas contra
`BaseConocimiento.buscar()` (el mecanismo real que usa `responder()`, no una simulación aparte) —
incluyendo preguntas dirigidas específicamente a contenido que antes estaba enterrado (fit_desoto,
bug de unidades a_ref, alerta_margen, inversores duplicados, clipping, confusión AC/DC en Vdc_max,
Estimación Rápida paso a paso, preguntas frecuentes de Vista 3D). Las 15 recuperan correctamente
la sección relevante, con el título correcto y sin ningún texto truncado a mitad de una idea.

No se tocó ningún contenido — solo se agregaron encabezados. Suite completa: **806/806** (sin
tests nuevos: es un archivo de datos, no código; la verificación fue directamente contra el
mecanismo real de búsqueda, documentada arriba).
