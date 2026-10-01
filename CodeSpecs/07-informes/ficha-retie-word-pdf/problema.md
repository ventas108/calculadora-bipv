# Spec — Ficha RETIE en Word editable, PDF y PNG

**Estado:** validación

## Alcance de la fase

Descargas de la 📋 Ficha de Validación RETIE.

## Problema a resolver

El usuario (1-oct-2026): «tengo el mismo problema de descarga pero con el
módulo validación RETIE… aplica la misma solución que en Reporte PDF». La
ficha solo se descargaba en SVG: el botón PNG pedía CairoSVG, que no está en
el servidor («Descarga en PNG no disponible»), y Word no muestra SVG.

## Contexto

La ficha es un SVG propio (`generar_ficha_svg`, 1.800 × 1.420) con
rectángulos, texto, líneas con flecha (`marker-end`) y un `path` de tramos
rectos (barra de tierra). El conversor del Reporte (`calculos.svg_a_png`,
Spec `07/reporte-word-pdf`) no dibujaba `path` ni flechas y dibujaba lo que
había dentro de `<defs>`.
