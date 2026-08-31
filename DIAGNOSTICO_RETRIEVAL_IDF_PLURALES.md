# El buscador del asistente 🧭: de conteo simple a IDF + plurales

**Fecha**: 31 de agosto de 2026
**Disparador**: tras publicar el manual consolidado (sección `25g.` de `base_conocimiento_asistente.md`),
el usuario probó en el chat REAL de la app la pregunta *"enumérame las alertas nuevas que se instalaron
aguas abajo entre los módulos para evitar errores del usuario"*. El asistente citó 2 alertas **viejas**
(densidad/PR del 5-ago, alarma SDM vs ficha técnica del 21-ago) como si fueran "lo nuevo de esta semana",
ignorando la alerta real (vigencia del diseño confirmado, `25f.`). Un primer intento de arreglo agregó la
respuesta correcta directamente al contenido de `25g.` — funcionó, pero el usuario notó correctamente que
el problema de fondo seguía sin tocarse: *"verifica, creo que aun persiste... verifica y solucionalo de
raiz"*.

## Causa raíz real (no era un problema de contenido)

`BaseConocimiento.buscar()` (`calculos/asistente.py`) puntuaba cada sección por **conteo simple** de
palabras en común con la pregunta, más un bono fijo (×2) si la palabra también aparecía en el título. Dos
defectos de ese diseño causaron el bug, verificados directamente contra el mecanismo real:

1. **Sin ponderar por especificidad.** La etiqueta "NUEVO"/"nueva" marca decenas de funciones agregadas
   en todo el manual (cada actualización documentada la usa) — para la pregunta real, con "nuevas" entre
   sus palabras, esas secciones sin relación ganaban por volumen de coincidencias. La sección real
   (`25f.`) sacaba score=3, empatada y perdiendo contra 6 secciones irrelevantes que también sacaban 3 o
   más.
2. **Sin normalización de plural/singular.** La pregunta decía "alertas" (plural), el título real decía
   "alerta de vigencia" (singular) — nunca calzaban como el mismo token, así que la sección específica ni
   se beneficiaba del bono de título.

Verificado con un script exploratorio contra el `buscar()` real, ANTES de tocar nada: para la pregunta
literal del usuario, ni `25f.` ni la subsección de detalle de Dimensionamiento aparecían en el top-8.

## Corrección: 2 cambios en el mecanismo, no en el contenido

1. **IDF (frecuencia inversa de documento)**, calculado una vez al cargar el manual
   (`_calcular_idf(secciones)`): una palabra que aparece en pocas secciones (específica, ej. "vigencia")
   pesa más en el score que una que aparece en decenas (genérica, ej. "nuevo"). `BaseConocimiento` ahora
   guarda un campo `idf: dict[str, float]`; si una instancia se arma a mano sin pasar por `cargar()` (como
   en un test unitario con secciones sintéticas), `buscar()` cae a peso uniforme (`idf.get(tok, 1.0)`) —
   mismo comportamiento que antes de este cambio, sin romper nada que dependiera de la conducta vieja.
2. **`_singularizar()`**: heurística simple de plural→singular en español (`alertas`→`alerta`,
   `errores`→`error`, `paneles`→`panel`), aplicada dentro de `_normalizar()` — afecta solo el *matching*
   interno, nunca el texto que se muestra al usuario. No pretende ser un stemmer completo (palabras cortas
   de 4 letras o menos no se tocan, para evitar falsos positivos como "mes"/"gas"), pero cubre el patrón
   real que causó el bug y el resto de sustantivos/adjetivos comunes del manual.

## Verificación

Contra el corpus **real** (`BaseConocimiento.cargar()`, no un caso sintético), con la pregunta textual
exacta del usuario: ahora `25f.` y el detalle de Dimensionamiento aparecen dentro del top-4/top-6 en vez
de estar ausentes del top-8. Repetido con 2 variantes de la pregunta ("cuales alertas son nuevas de esta
semana", "que cambio en materia de alertas el 31 de agosto") con el mismo resultado correcto. Verificado
también que preguntas de control sin relación ("como calculo la produccion anual", "que es el performance
ratio") siguen devolviendo las secciones correctas de siempre — el cambio no distorsiona el resto del
buscador.

**7 tests nuevos** en `tests/test_asistente_retrieval.py` — primera cobertura de tests que existe para
`buscar()` en la vida de este archivo (no tenía ninguna, ni siquiera cuando se corrigió el truncamiento a
4.000 caracteres el mismo día, `DIAGNOSTICO_RETRIEVAL_ASISTENTE_TRUNCAMIENTO.md`): normalización de
plurales, ponderación IDF con secciones sintéticas controladas, comportamiento sin romper cuando no hay
`idf` precalculado, y 2 tests anclados al corpus real con la pregunta textual del usuario. Suite completa:
**821/821**.

## Lección para el futuro

Este es el segundo bug real de este mismo mecanismo de búsqueda encontrado en un solo día (el primero fue
el truncamiento a 4.000 caracteres por sección). Ambos comparten la misma causa raíz de fondo: el
mecanismo nunca tuvo tests de calidad de búsqueda, solo se verificaba manualmente con preguntas sueltas.
Con `tests/test_asistente_retrieval.py` ahora existiendo, un cambio futuro al contenido del manual que
rompa la recuperación de una sección específica debería fallar un test antes de llegar a producción, en
vez de descubrirse por un usuario probando el chat en vivo.
