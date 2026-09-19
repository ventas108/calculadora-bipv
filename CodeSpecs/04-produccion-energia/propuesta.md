# Propuesta — Producción de energía

**Estado:** en validación

## Objetivo

Formalizar el contrato de la simulación anual BIPV y sus resultados
persistidos, preservando la trazabilidad entre recurso solar, diseño eléctrico,
Motor Óptico, Producción, Finanzas e Informes.

## Alternativas consideradas

1. Recalcular energía sin validar el estado confirmado de Dimensionamiento.
2. Separar simulaciones o contratos para cada consumidor downstream.
3. Conservar `simular_produccion_anual()` como motor puro y centralizar los
	gates, selección de modo y persistencia en la página de Producción.

## Alternativa recomendada

Mantener la alternativa 3. La simulación solo se ejecuta con recurso solar
válido, compatibilidad eléctrica y diseño vigente. Sus resultados conservan las
claves históricas que consumen Finanzas, Baterías e Informes.
