# Propuesta — Reporte: cables reales, título y autos equivalentes

**Estado:** validación

## Objetivo

Que el informe no muestre dos cifras de cables y que los textos correspondan
al proyecto.

## Alternativa recomendada

Autorizada por el usuario el 2-oct-2026 («autorizado»).

- Revisión de coherencia: error «📊 Producción no usó los cables calculados»
  cuando el Unifilar o Granja FV calcularon los cables y Producción aplicó el
  % manual. No aplica con el sistema multi-superficie, que tiene sus propios
  cables.
- `etiquetas_tipo` agrega `titulo` y `sujeto` según el tipo de instalación;
  el encabezado y el texto de CO₂ los usan.
- `co2.vehiculos_equivalentes` y `co2.texto_vehiculos`:
  CO₂ ÷ (0,162 kg/km × 20.000 km/año). La constante `KM_ANUALES_AUTO` es la
  misma que ya usaba 🌿 Impacto CO₂.

## Alternativas descartadas

- Aplicar en Producción, sin avisar, los cables de Granja FV: cambiaría la
  energía sin que el diseñador lo vea, y el Unifilar es el que verifica la
  vigencia (panel, inversor, serie y módulos).
- Quitar la frase de los vehículos: la equivalencia es útil para el cliente.

## Fuera de alcance

- La eficiencia del inversor y la calidad del módulo: son datos del catálogo
  y de 🔀 Mismatch que el diseñador revisa.
