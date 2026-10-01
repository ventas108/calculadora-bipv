# Spec — Reporte PDF de proyectos multi-superficie (🗺️ Vista 3D)

**Estado:** validación

## Alcance de la fase

📄 Reporte PDF con energía multi-superficie publicada y la publicación de la
cadena de pérdidas de 🗺️ Vista 3D.

## Problema a resolver

Revisión pedida por el usuario (1-oct-2026): «revisar también si las
actualizaciones realizadas en el módulo Vista 3D se reportan en el Reporte
PDF; ponte en el lugar del cliente».

- «Producción Anual» mostraba la energía de 📊 Producción (superficie única)
  aunque la energía del proyecto fuera la multi-superficie: **dos cifras**
  distintas en el mismo reporte.
- La sección multi-superficie solo traía área, POA y energía por superficie:
  faltaban orientación, panel, módulos, kWp, **PR** y **kWh/kWp**, los
  **inversores** (potencia, strings, DC/AC), la **cadena de pérdidas** por
  superficie, los **strings que cruzan**, el método de cálculo, el estado
  eléctrico y la producción mensual.
- La publicación solo guardaba el PR de cada superficie, no su tabla de
  pérdidas.

## Contexto

Continúa la Spec `07/reporte-produccion-completo` (#96), que completó el
reporte de superficie única y de granjas.
