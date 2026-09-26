# Propuesta — Financiero, Baterías y CO₂ con el sistema multi-superficie publicado

**Estado:** implementación

## Objetivo

Cuando hay energía multi-superficie publicada, todo lo que Financiero,
Baterías y CO₂ usan sale del **mismo** diseño de 🗺️ Vista 3D (energía,
potencia, módulos, reparto mensual), con la fuente visible, y nunca se mezcla
con el sistema de superficie única ni depende de 📊 Producción.

## Alternativas consideradas

1. **Solo un aviso** en Financiero cuando falta Producción. Descartada: el
   CAPEX seguiría saliendo de otro sistema.
2. **Recalcular potencia y módulos en cada página** desde las superficies.
   Descartada: podría no coincidir con la energía publicada si el diseño
   cambió después.
3. **Publicar el sistema junto con la energía** (potencia, módulos por panel,
   reparto mensual) en la misma publicación todo o nada. Recomendada.

## Alternativa recomendada

La publicación multi-superficie agrega `multisup_sistema`, calculado del mismo
diseño en el mismo momento:

- potencia DC STC = Σ módulos de los grupos × Pmax de su panel;
- módulos y potencia por referencia de panel;
- reparto mensual: la energía anual de cada superficie repartida según la POA
  mensual de esa superficie (exacto para el simplificado; para bypass y
  físico reparte la energía anual con la forma de la POA);
- `completo = False` y la lista de superficies sin grupos de strings, cuya
  potencia no se puede conocer.

Consumidores:

- **Financiero**: con modo multi-superficie activo no exige 📊 Producción.
  Usa energía, kWp y módulos publicados. Con varios paneles, un costo por
  módulo por cada referencia (prellenado con `costo_usd` del catálogo). Si el
  sistema está incompleto o la publicación es anterior a esta versión: 🔴 y
  no calcula, con la acción exacta.
  Si el Presupuesto está vinculado, 🟡 que dice con cuántos módulos y kWp se
  armó frente a los del sistema multi-superficie.
- **Baterías**: balance mensual con el reparto mensual publicado; el balance
  horario sigue usando 📊 Producción y lo dice.
- **CO₂**: kWp y módulos del sistema publicado.
- **Presupuesto**: aviso 🟡 de que usa el sistema de superficie única (H3).

## Fuera de alcance

- Presupuesto por superficie (H3), Reporte PDF, Unifilar y Análisis IA con el
  sistema multi-superficie: se registran para sus propias Specs.
- Balance horario multi-superficie.
