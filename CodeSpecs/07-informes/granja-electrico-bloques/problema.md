# Spec — 🌾 Granja FV, fase 5: eléctrico por bloques — strings, inversores y cables que alimentan Unifilar y RETIE

**Estado:** validación

## Alcance de la fase

🌾 Granja FV (sección nueva), ⚡ Diagrama Unifilar (tramos de cable en
superficie única) y 📋 Ficha RETIE (validaciones de la granja), con un
motor puro `calculos/granja_electrico.py`.

## Problema a resolver

- Los strings, los inversores y el reparto de 📐 Dimensionamiento (Apartadó:
  11 strings de 28, reparto 6 + 5) no estaban ubicados en el campo: no se
  sabía qué filas van a cada inversor ni si un string queda partido entre
  filas.
- ⚡ Diagrama Unifilar pedía **a mano** un solo largo de cable DC; si se
  dejaba en 0, 📊 Producción usaba un % fijo de pérdida en cables.
- 📋 Ficha RETIE no revisaba la caída de tensión de los cables.

## Contexto

Pedido del usuario el 30-sep-2026 («Eléctrico por bloques. Strings por fila,
inversores por bloque y largo de cables estimado desde la geometría, que
alimenta Unifilar y RETIE»); diseño aprobado («si, empieza la fase 5»).
