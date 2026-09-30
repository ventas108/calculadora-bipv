# Spec — 🌾 Granja FV, fase 4: seguidor de un eje con backtracking frente a la estructura fija

**Estado:** validación

## Alcance de la fase

🌾 Granja FV (sección nueva) y un motor puro `calculos/seguidor.py`. La
energía de 📊 Producción sigue calculada con la estructura fija.

## Problema a resolver

En una granja la primera pregunta de diseño es si conviene un seguidor de
un eje. La app solo modelaba estructura fija: no había forma de comparar
cuánta luz gana un seguidor Norte–Sur, ni qué pasa con y sin backtracking
(la sombra de la fila vecina al amanecer y al atardecer), ni si el borde
del seguidor queda demasiado cerca del suelo con el giro máximo.

## Contexto

Pedido del usuario el 30-sep-2026 («Seguidor de un eje. Con backtracking y
comparación contra la estructura fija»), después de la fase 3
(agrivoltaica). Sigue la fase 5 (eléctrico por bloques).
