# Spec — Guía de Vista 3D

**Estado:** validación

## Alcance de la fase

🗺️ Vista 3D y manual del Asistente: cómo correr la sombra 3D
multi-superficie sin errores tras los PR #115 (sombra por string) y #116
(difusa en la sombra).

## Problema a resolver

1. La página no explicaba al entrar el flujo completo ni los cambios del
   3-oct-2026.
2. Errores comunes sin guía: coordenadas en milímetros, puntos dentro del
   edificio, un solo punto por superficie, no recalcular la sombra tras
   cambiar la escena, escena de otra ubicación.
3. El Asistente no tenía una sección paso a paso de Vista 3D.

## Contexto

Pedido del usuario: «documenta al asistente para que se explique bien al
entrar en el módulo Vista 3D estos nuevos cambios; el usuario necesita
aprender a usar la app sin cometer errores al correr un proyecto».
