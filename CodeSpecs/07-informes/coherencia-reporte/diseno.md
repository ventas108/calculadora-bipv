# Diseño — Coherencia del Reporte

**Estado:** validación

## Entradas

Estado de la sesión: `E_ac_anual_kWh` (o bypass / multi-superficie),
`produccion_n_inversores`, `reparto_strings_inversores`,
`N_inversores_proyecto`, `co2_anual_t`, `co2_factor_kg_kwh`,
`co2_e_ac_kWh`, `co2_e_ac_manual`, `fin_e_ac_kWh` y `fin_e_ac_manual`.

## Salidas

`revisar_coherencia_reporte(estado) -> list[{nivel, titulo, detalle, accion}]`
y `energia_vigente(estado)`, con la misma prioridad que CO₂ y Financiero.

## Tipos de datos

`nivel ∈ {"error", "aviso"}`; textos en español para el diseñador.

## Errores posibles

- Claves ausentes o no numéricas: cuentan como 0 y no generan falsos errores.
- CO₂ sin `co2_e_ac_kWh` (páginas anteriores): la energía se deduce como
  `co2_anual_t × 1000 / factor`.

## Dependencias

Ninguna fuera de la biblioteca estándar.

## Criterios de aceptación

1. Estado coherente de Apartadó (4 inversores, 604.195 kWh, CO₂ de esa
   energía): sin errores.
2. Producción con 3 inversores y reparto en 4: error que nombra 3 y 4 y pide
   volver a ejecutar Producción.
3. CO₂ de 6,3 t: error con «50,000» y «604,195».
4. CO₂ o Financiero escritos a mano, o Financiero con otra energía: error.
5. Sin Producción: error.
6. PVWatts frente a la cara frontal: diferencia ~0,4 %.
7. Páginas conectadas y sin «fachada BIPV desplaza» fijo.
