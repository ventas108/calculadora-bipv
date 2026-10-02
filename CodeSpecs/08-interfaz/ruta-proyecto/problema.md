# Spec — 🧭 Ruta del proyecto en 🏠 Proyecto

**Estado:** validación

## Alcance de la fase

🏠 Proyecto: ruta pictográfica de las páginas según el tipo de instalación,
con el estado de cada paso leído de la sesión. Sin cambios de cálculo.

## Problema a resolver

El usuario (2-oct-2026) pidió «una idea práctica para que, cuando se marque
el tipo de instalación y haya dudas, se visualice pictográficamente (los
módulos aguas abajo) el paso a paso a seguir». Tras desplegar el PR #111 (solo
la sección 119 del manual): «no funcionó, no aparece».

El orden existía solo en el manual del Asistente. El checklist del 🧭
Asistente (`calculos/asistente.FLUJO`) no distingue tipos de instalación ni
incluye Granja FV, Unifilar ni la segunda pasada de Recurso Solar.

## Contexto

- La revisión de coherencia del Reporte (`revisar_coherencia_reporte`) ya
  sabe qué quedó viejo.
- `granja_fv.mismas_filas` sabe si la POA usa la geometría del campo.
