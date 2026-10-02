# Spec — Manual del Asistente: orden de las páginas según el tipo de instalación

**Estado:** validación

## Alcance de la fase

Manual del Asistente (🧭), sección nueva 119 y aviso en la sección 2. Sin
cambios de cálculo ni de páginas.

## Problema a resolver

El usuario (2-oct-2026): «dime cuál es el orden ideal tanto para un sistema
BIPV y un agrivoltaico como el de Urabá… agrega esta guía de orden como una
sección del Manual del Asistente para que la app la responda».

- El orden estaba repartido entre las secciones 2, 107 y 108.
- La sección 2 (6-sep-2026) ponía 📊 Producción antes de 🗺️ Vista 3D y
  💰 Financiero antes de 💼 Presupuesto.
- La sección 2 no nombraba ⚡ Diagrama Unifilar, que va antes de Producción
  porque da la pérdida real en los cables.
- Nada decía qué volver a ejecutar al cambiar un dato. El informe de
  Apartadó 3 salió con datos de momentos distintos por eso (sección 118).

## Contexto

`calculos/invalidacion.py` ya define qué caduca en cadena. Producción toma la
pérdida óhmica del Unifilar (`perdida_ohmica_unifilar`) y la granja usa dos
pasadas de Recurso Solar (sección 107).
