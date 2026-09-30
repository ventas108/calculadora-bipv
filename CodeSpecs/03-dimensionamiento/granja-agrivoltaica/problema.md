# Spec — 🌾 Granja FV, fase 3: agrivoltaica — luz para el cultivo, mapa de sombra y maquinaria

**Estado:** validación

## Alcance de la fase

🌾 Granja FV (sección nueva) y un motor puro `calculos/agrivoltaica.py`. No
cambia la energía.

## Problema a resolver

La página 🌾 Granja FV diseña el campo y lleva la sombra entre filas a la
energía, pero no dice nada del **cultivo**, que es lo que diferencia un
proyecto agrivoltaico de una granja solar:

- No se sabía cuánta luz llega al suelo bajo las mesas y entre las filas
  (en % y en kWh/m²), ni cómo cambia mes a mes.
- No había mapa de sombra en el suelo.
- No se revisaba si la maquinaria agrícola pasa por debajo de las mesas o
  por el corredor, ni la categoría agrivoltaica según la altura libre.

Además, el texto de la página seguía diciendo que el campo «no cambia la
energía», lo que dejó de ser cierto con la fase 2.

## Contexto

Pedido del usuario el 30-sep-2026 («continua con lo pendiente … Agrivoltaica.
Luz que llega al cultivo bajo y entre filas (% y kWh/m²), mapa de sombra en
el suelo y altura libre para maquinaria»). Fases siguientes: seguidor de un
eje y eléctrico por bloques.
