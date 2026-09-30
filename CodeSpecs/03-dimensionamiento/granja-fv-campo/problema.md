# Spec — 🌾 Granja FV, fase 1: campo de filas coherente con el proyecto

**Estado:** validación

## Alcance de la fase

Página nueva 🌾 Granja FV (terreno, mesas, filas, separación, altura, GCR,
ángulo límite de sombra, 3D) y el dibujo de granja de 🗺️ Vista 3D. Sin cambios
en la energía.

## Problema a resolver

Las granjas solares y agrivoltaicas se diseñaban dentro de 🗺️ Vista 3D, que
está hecho para BIPV (superficies del edificio). En Apartadó (30-sep-2026) el
usuario encontró:

- El modelo 3D decía **288 módulos · 207,36 kWp** cuando el proyecto tiene
  **308 · 221,76 kWp**: Vista 3D tenía su propia cuenta de «matrices» y su
  propio origen de módulos.
- El GCR del dibujo salía del factor de ocupación, el del modelo bifacial de
  ☀️ Recurso Solar se escribe aparte y la altura del dibujo tampoco se
  comparaba con la del modelo bifacial: tres geometrías sin relación.
- No había dónde ver el GCR, el ángulo límite de sombra ni el corredor libre
  entre filas, que el informe de la referencia estándar internacional sí
  reporta (separación 6,60 m, ancho 2,65 m, GCR 39,8–40,1 %, 6,5°, altura
  3,00 m).

## Contexto

Plan de 5 fases acordado con el usuario: 1) campo y 3D coherentes; 2) sombra
entre filas y bifacial por geometría; 3) agrivoltaica (luz al cultivo);
4) seguidor de un eje; 5) eléctrico por bloques. Regla: motores comunes, sin
copiar Vista 3D.
