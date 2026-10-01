# Spec — Reporte en Word editable y PDF sin perder gráficas

**Estado:** validación

## Alcance de la fase

Descarga del 📄 Reporte PDF en Word (.docx) y PDF desde la app.

## Problema a resolver

El usuario (1-oct-2026): «al descargarlo en Word se pierden muchos datos
gráficos… entrégame una alternativa para descargarlo como Word modificable
compatible y en PDF sin que se pierda información importante para el
cliente». Su .docx del reporte de la Granja Apartadó tenía 13 tablas y 0
imágenes: Word no lee los 6 SVG del HTML. El PDF dependía de imprimir desde
el navegador, y la impresión no conservaba los colores de fondo.

## Contexto

El reporte es un HTML con SVG propios (Specs `07/reporte-produccion-completo`
y `07/reporte-granja-completo`). En el servidor no hay navegador ni librerías
de sistema para SVG; sí python-docx, fpdf2, Pillow, lxml y matplotlib (con
la fuente DejaVu).
