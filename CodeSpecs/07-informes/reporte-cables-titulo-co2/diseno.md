# Diseño — Reporte: cables reales, título y autos equivalentes

**Estado:** validación

## Entradas

- `res_produccion.perdida_ohmica_dc_modo`
- `perdida_ohmica_unifilar`
- `granja_electrico_cfg` con `tipo_instalacion` = Granja fotovoltaica
- `multisup_activo`
- `pct_cableado_dc` y `pct_cableado_ac`
- `co2_anual_t`

## Salidas

- Problema de coherencia `{nivel: "error", titulo, detalle, accion}`.
- `etiquetas_tipo(tipo)["titulo"]` y `["sujeto"]`.
- `vehiculos_equivalentes(co2_anual_t) -> float` y
  `texto_vehiculos(co2_anual_t) -> str`.

## Tipos de datos

Títulos: «SISTEMA FOTOVOLTAICO — GRANJA SOLAR» (granja), «SISTEMA
FOTOVOLTAICO» (techo plano con soporte), «SISTEMA BIPV» (los demás o sin
tipo).

## Errores posibles

- Sin Producción o sin `res_produccion`: la revisión de cables no aplica (ya
  hay el error «Falta ⚡ Producción»).
- CO₂ ≤ 0: el texto dice «≈ 1 auto» como mínimo.

## Dependencias

`calculos/coherencia_reporte.py`, `calculos/reporte_produccion.py`,
`calculos/co2.py`.

## Criterios de aceptación

1. Granja con cables de Granja FV y Producción manual: error que nombra
   «🌾 Granja FV», el % manual y la acción con ⚡ Diagrama Unifilar y
   📊 Producción.
2. Unifilar calculado y Producción manual (no granja): error.
3. Producción con cables calculados, sin cables calculados o con el sistema
   multi-superficie: sin error.
4. Títulos y sujeto según el tipo de instalación.
5. 76,42 t → ≈ 23,6 autos («24 autos»); 3 t → «1 auto».
6. El Reporte no tiene «SISTEMA BIPV» ni «un vehículo» fijos; 🌿 Impacto CO₂
   usa `KM_ANUALES_AUTO`.
