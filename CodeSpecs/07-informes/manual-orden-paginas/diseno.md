# Diseño — Manual del Asistente: orden de las páginas

**Estado:** validación

## Entradas

Las páginas vigentes de la app (2-oct-2026) y sus dependencias:
- Producción lee la pérdida óhmica del Unifilar.
- 🌳 Sombras SketchUp con Sky View Factor invalida Recurso Solar.
- Financiero necesita el CAPEX de Presupuesto.
- 🌾 Granja FV envía la geometría a Recurso Solar.

## Salidas

Sección 119 del manual y aviso en la sección 2.

## Tipos de datos

Texto Markdown. Los bloques usan encabezados `###`, así el buscador del
Asistente los encuentra uno por uno.

## Errores posibles

Un nombre de página que cambie en el futuro: las pruebas fijan el orden.

## Dependencias

`datos/base_conocimiento_asistente.md` y `calculos/asistente.py`
(`BaseConocimiento.buscar`).

## Criterios de aceptación

1. La ruta BIPV de una superficie lista las páginas en orden, con Unifilar
   antes de Producción y Presupuesto antes de Financiero.
2. La ruta de granja tiene dos pasadas de Recurso Solar, con 🌾 Granja FV
   entre ellas, y nombra «Cantidad de inversores del proyecto».
3. Varias superficies remite a la 108 y a 🗺️ Vista 3D.
4. La tabla de cambios cubre ciudad, inclinación, Granja FV, inversor y
   Motor Óptico, y nombra el aviso del Reporte.
5. La sección 2 remite a la 119.
6. El Asistente encuentra la sección para preguntas de orden de granja y de
   fachada.
