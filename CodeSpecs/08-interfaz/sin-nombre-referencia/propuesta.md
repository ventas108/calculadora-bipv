# Propuesta — La app no nombra el software de simulación de referencia

**Estado:** validación

## Objetivo

Que ninguna pantalla, texto del Asistente ni dato de catálogo mostrado nombre
el software de referencia, y que una prueba lo impida en el futuro.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («si mantén la regla, no nombrar …»).

- `calculos/texto_referencia.anonimizar_referencia`: cambia el nombre (con o
  sin versión) por «la referencia estándar internacional», con reglas de
  gramática («de …», «estilo de …», «base de datos de …») y mayúscula al
  comienzo de oración; nombres de archivos y funciones que lo contienen pasan
  a «un documento interno», «un módulo interno» o «una función interna».
  «pvlib.pvsystem» (librería) no se toca.
- Manual del Asistente y textos de páginas y cálculos reescritos.
- Catálogos: el filtro se aplica al leer notas, confianza y fuentes.
- Asistente: regla 6 del prompt y filtro de la respuesta. La regla 2 permite
  explicar paso a paso los ejemplos del manual y cuentas de un paso.
- Prueba que recorre todo texto entre comillas de páginas, cálculos y
  utilidades, el manual, los catálogos y la respuesta del Asistente.

## Fuera de alcance

- Comentarios, docstrings, nombres internos, documentos del director y
  scripts de importación de catálogos (no se muestran).
