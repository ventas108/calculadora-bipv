# Propuesta — Guía de Vista 3D

**Estado:** validación

## Objetivo

Que el usuario vea, al entrar a Vista 3D, cómo correr la sombra 3D paso a
paso y qué errores evitar, y que el Asistente responda con el mismo texto.

## Alternativa recomendada

Pedida por el usuario el 3-oct-2026.

- `calculos/guia_vista_3d.py`: título, resumen, 8 pasos, 7 errores
  frecuentes, valores esperados y recordatorio de los puntos 3D, en un solo
  lugar.
- Vista 3D:
  - resumen visible y recuadro «📘 Cómo usar Vista 3D sin errores» bajo el
    título;
  - recordatorio justo antes de los puntos 3D.
- Manual del Asistente, sección 125, con el mismo texto y un ejemplo de
  puntos.

## Alternativas descartadas

- Abrir la guía siempre expandida: ocupa la pantalla en cada visita; el
  resumen visible ya invita a abrirla.
- Textos distintos en página y manual: se desalinean con el tiempo.

## Fuera de alcance

Convertir automáticamente coordenadas de Site Designer a puntos 3D.
