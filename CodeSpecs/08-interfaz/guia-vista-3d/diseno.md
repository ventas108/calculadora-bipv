# Diseño — Guía de Vista 3D

**Estado:** validación

## Entradas

Ninguna: texto fijo.

## Salidas

- `GUIA_TITULO`, `RESUMEN`, `AYUDA_PUNTOS`, `PASOS`, `ERRORES_FRECUENTES`.
- `guia_markdown() -> str`.

## Tipos de datos

Cadenas y tuplas de cadenas.

## Errores posibles

Ninguno en tiempo de ejecución; las pruebas verifican orden y contenido.

## Dependencias

`pages/9_🗺️_Vista_3D.py`, `datos/base_conocimiento_asistente.md`.

## Criterios de aceptación

1. Los pasos siguen el orden del flujo: Recurso Solar, Superficies BIPV,
   Site Designer, un punto por módulo, Calcular sombra, estado, Inversores,
   comparación física, Adoptar.
2. La guía explica string, bypass, difusa, metros frente a milímetros,
   0,3 m y `northOffset`; trae al menos 6 errores frecuentes.
3. La página muestra el resumen y el recuadro entre el título y las
   pestañas, y el recordatorio junto a los puntos 3D.
4. Sección 125 del manual con el mismo contenido y sin nombres comerciales
   de otras apps.
