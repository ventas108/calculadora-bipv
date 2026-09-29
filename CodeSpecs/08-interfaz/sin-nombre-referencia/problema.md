# Spec — La app no nombra el software de simulación de referencia

**Estado:** validación

## Alcance de la fase

Textos que ve el usuario: páginas, notas que arman los cálculos (por ejemplo
el Loss Diagram de 📊 Producción), el manual del 🧭 Asistente
(`datos/base_conocimiento_asistente.md`), las respuestas del Asistente y los
textos de los catálogos de paneles e inversores que se muestran (notas,
confianza, fuentes).

## Problema a resolver

El 30-ago-2026 el usuario decidió, «por cuestiones legales», no nombrar el
software de simulación de referencia en la app ni en el manual del Asistente
(que puede citarlo a un cliente). El 29-sep-2026 la auditoría encontró el
nombre 150 veces en el manual, en 28 líneas de texto de páginas y cálculos
(selector de PVGIS, controles de 🔀 Mismatch, notas del Loss Diagram,
Financiero) y en más de 3.000 celdas de notas y fuentes del catálogo de
paneles. El usuario reafirmó la regla ese día.

## Contexto

El catálogo Excel del servidor puede tener cambios propios del usuario: no se
reescribe; se filtra al leerlo. Los comentarios, docstrings y nombres internos
del código (por ejemplo `sdm_pvsyst`) no se muestran y quedan igual.
