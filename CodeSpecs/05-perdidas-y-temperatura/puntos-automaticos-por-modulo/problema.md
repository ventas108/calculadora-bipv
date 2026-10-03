# Spec — Puntos automáticos por módulo

**Estado:** validación

## Alcance de la fase

🗺️ Vista 3D, sombra 3D multi-superficie: puntos de análisis y sombra de cada
string hasta el modo físico.

## Problema a resolver

1. Los puntos 3D se escribían a mano. Errores frecuentes: milímetros en vez
   de metros, puntos dentro del edificio, un solo punto por superficie.
2. Aunque hubiera un punto por módulo, todos los strings de una superficie
   recibían la misma fracción de sombra. Si la sombra cae siempre en el
   mismo string, el bypass se repartía mal: un string entero a media luz se
   trataba como medio módulo apagado en cada string, cerca del doble de
   pérdida.

## Contexto

Revisión de brechas tras La Salle (3-oct-2026): la escritura manual de
puntos es la brecha de mayor impacto; la asignación punto ↔ string, la
segunda. Pedido del usuario: «prepara la Spec de puntos automáticos por
módulo… bajo el más estricto cálculo y precisión».
