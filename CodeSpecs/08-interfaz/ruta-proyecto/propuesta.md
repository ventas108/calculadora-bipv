# Propuesta — 🧭 Ruta del proyecto

**Estado:** validación

## Objetivo

Que el diseñador vea, al elegir el tipo de instalación, qué páginas siguen,
en qué orden, cuáles ya están y cuál toca ahora.

## Alternativa recomendada

Pedida por el usuario el 2-oct-2026.

- `calculos/ruta_proyecto.py` (puro) con dos rutas:
  - BIPV: 16 pasos;
  - granja: 15 pasos, con dos pasadas de Recurso Solar.
- Estado de cada paso:
  - ✅ listo · 🟠 desactualizado · ▶️ siguiente · ⬜ por hacer · ⚪ opcional · 🔎 verificación;
  - 🟠 sale de la revisión del Reporte o de la geometría del campo sin POA
    nueva, y se propaga aguas abajo.
- 🏠 Proyecto, debajo del tipo de instalación:
  - desplegable con la línea de estaciones (HTML con flex-wrap);
  - consejo al pasar el mouse;
  - «Siguiente» con botón «Ir a … →» y la lista «¿Qué hago en cada paso?».

## Alternativas descartadas

- Reescribir el checklist del 🧭 Asistente: lo usan otras pruebas y el chat.
- Barra lateral en todas las páginas: toca las 28 páginas. Queda como
  segunda fase si el usuario la pide.

## Fuera de alcance

- Ejecutar páginas automáticamente.
