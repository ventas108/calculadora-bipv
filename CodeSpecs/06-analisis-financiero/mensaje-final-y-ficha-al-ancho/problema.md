# Spec — Mensaje final de Financiero y Ficha RETIE al ancho de la pantalla

**Estado:** validación

## Alcance de la fase

`pages/7_💰_Financiero.py` (mensaje final) y `pages/21_📋_Ficha_Validacion_RETIE.py`
(presentación de la ficha). Evidencia: proyecto del cliente desplegado el
28-sep-2026 (112 ASP-ST1-T40 + 4 SPR-E20-327).

## Problema a resolver

1. El mensaje final decía «116 módulos ASP-ST1-T40»: tomaba el panel de
   📐 Dimensionamiento aunque el sistema multi-superficie tiene dos paneles.
2. El mismo mensaje terminaba en «TIR: 16.8% |»: el `if/else` de la f-string
   abarcaba todo el texto, así que con TIR se perdían VPN, Payback y LCOE.
3. La ficha RETIE (SVG de 1800 px en un iframe) se veía con barra horizontal.

## Contexto

`multisup_sistema["por_panel"]` ya trae cada panel con sus módulos
(Spec `06/sistema-multisuperficie`).
