# Spec — Sombra entre filas y cara trasera según la geometría del campo (🌾 Granja FV, fase 2)

**Estado:** validación

## Alcance de la fase

☀️ Recurso Solar (POA de superficie única), modelo bifacial de
`calculos/solar.calcular_poa` y 🌾 Granja FV. Granjas solares y
agrivoltaicas con filas de mesas.

## Problema a resolver

Informe de Apartadó de la referencia estándar internacional (308 ×
JAM66D46-720/LB, mesas de 2 módulos horizontales, inclinación 10°,
separación 6,60 m, GCR 39,8 %): sombra cercana entre filas **−0,20 %**,
sombra de la estructura en la cara trasera **5 %** y mismatch trasero
**10 %**.

- Con paneles **monofaciales** la app calculaba la granja como una fila
  aislada: no había sombra entre filas.
- Con paneles **bifaciales** `infinite_sheds` sí incluye la sombra, pero con
  un ancho de mesa **fijo de 2,0 m** que no se mostraba (Apartadó: 2,626 m).
- La cara trasera no tenía sombra de estructura ni mismatch trasero.
- La fase 1 de 🌾 Granja FV calculaba GCR, altura y ancho de la mesa, pero no
  los llevaba a la energía.

## Contexto

La fase 1 (Spec `03-dimensionamiento/granja-fv-campo`) dejó explícito que la
geometría → energía era la fase 2. El usuario la pidió el 30-sep-2026
(«me arriesgo .. sigamos con la fase 2»).
