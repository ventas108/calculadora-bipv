# Spec — Columnas a medida

**Estado:** validación

## Alcance de la fase

«🧮 Generar un punto por módulo» de 🗺️ Vista 3D: campos con columnas de
módulos a distinta separación.

## Problema a resolver

El generador solo armaba campos regulares (misma separación entre todas las
columnas). En fachadas con columnas entre ventanas o junto a balcones, las
columnas quedaban fuera de su sitio. En La Salle (Torre 5, fachada SO), con
13 columnas y huecos de 1,1 m a 9,15 m, un campo regular las desplazaba
hasta 7,5 m; la única salida era escribir los puntos a mano o crear una
superficie por tramo.

## Contexto

Prueba del generador con La Salle (3-oct-2026), informe de la rama
`borrador/lasalle-sobre-main`, sección 10.
