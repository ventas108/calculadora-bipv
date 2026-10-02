# Spec — Reporte: cables reales, título según la instalación y autos equivalentes

**Estado:** validación

## Alcance de la fase

📄 Reporte, revisión de coherencia y 🌿 Impacto CO₂. No cambia el cálculo de
energía.

## Problema a resolver

Informe real «Granja Solar Apartadó» (2-oct-2026, 606.522 kWh/año), ya con la
revisión de coherencia del PR #110:
1. El diagrama de pérdidas decía «②d Pérdida óhmica DC −0,85 % · Fuente: %
   manual configurado en Mismatch» y no tenía fila de cables AC. En el mismo
   informe, 🌾 Granja FV daba 0,50 % DC y caídas AC de hasta 1,69 %:
   📊 Producción no usó los cables reales y la revisión no lo detectó.
2. El encabezado decía «REPORTE TÉCNICO — SISTEMA BIPV» en una granja en
   suelo.
3. «CO₂ evitado — año 1: 76,42 t» con el texto fijo «Equivale a sacar un
   vehículo de circulación durante 1 año completo». Son ~24 autos.

## Contexto

Producción guarda en `res_produccion` la fuente de la pérdida en cables
(`perdida_ohmica_dc_modo`: «calculado» o «manual»). El Unifilar guarda
`perdida_ohmica_unifilar` y Granja FV guarda `granja_electrico_cfg`.
