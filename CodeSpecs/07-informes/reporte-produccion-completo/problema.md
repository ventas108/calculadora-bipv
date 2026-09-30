# Spec — Reporte PDF de producción completo para el cliente

**Estado:** validación

## Alcance de la fase

📄 Reporte PDF (secciones de producción, sin la parte financiera) y un dato
que 📊 Producción no guardaba (inversores de la simulación).

## Problema a resolver

El usuario quiere entregar al cliente de Urabá un reporte de producción muy
completo. Revisión del 30-sep-2026:

- La casilla «Incluir sección Dimensionamiento» **no generaba ninguna
  sección**; el reporte no decía cuántos inversores hay (2 × 100 kW), el
  reparto (6 + 5), la relación DC/AC (1,11) ni el recorte.
- Solo mostraba el factor de mismatch: faltaba el **diagrama de pérdidas**
  que 📊 Producción ya calcula (IAM, suciedad, temperatura, calidad,
  mismatch, cables, inversor, recorte).
- Faltaban los datos bifaciales nuevos (GCR, ancho de la mesa, sombra y
  mismatch traseros) y **todo 🌾 Granja FV** (campo, sombra entre filas,
  agrivoltaica, seguidor y eléctrico por bloques).

## Contexto

Pedido del usuario: «quiero que este reporte esté muy completo para el
cliente, por ahora sin la parte financiera, solo la de producción».
