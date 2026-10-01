# Diseño — Reporte PDF de Granja FV completo y ficha del inversor

**Estado:** validación

## Entradas

- Granja: `tipo_instalacion`, `granja_fv`, `panel_dict`, `N_paneles_final`,
  `N_serie`, `reparto_strings_inversores`, `granja_electrico_cfg`,
  `granja_luz_suelo`, `granja_altura_maquinaria_m`, `granja_ancho_maquinaria_m`.
- Reporte: `res_produccion` (`pct_calidad_modulo_aplicado`,
  `pct_mismatch_fab_aplicado`), `factor_mismatch_aplicado`, `alt_proyecto`,
  `ciudad`, `motor_optico_summary`, `ghi_anual_kWh_m2`, `poa_anual_kWh_m2`.
- Inversor: `inversor_dict_dim` (`Vdc_max`, `Vmppt_min`, `Vmppt_max`,
  `Vmppt_activo_min`, `I_max_tracker`, `Isc_max_tracker`, `nombre`).

## Salidas

- SVG de vista 3D, plano eléctrico, luz en el suelo y mapa mensual; listas
  🟢/🟡/🟠/🔴 de maquinaria y coherencia; nota de strings que cruzan.
- Textos por tipo de instalación, filas de mismatch aplicado, altitud, aviso
  de suciedad, margen de Voc y alertas de la ficha.

## Tipos de datos

`str` (SVG/HTML), `dict`, `list[dict]`, `list[tuple]`, `float | None`.

## Errores posibles

- Campo con errores o sin módulos: no se dibuja (las tablas siguen).
- Sin diseño eléctrico (`N_serie` 0): la vista 3D va sin colores de inversor
  y no hay plano.
- Datos que faltan: «—» o nada; nunca se inventan.

## Dependencias

`calculos/granja_fv.py`, `calculos/granja_electrico.py`,
`calculos/agrivoltaica.py`, `datos/ciudades_colombia.py`,
`pages/10_📄_Reporte_PDF.py`, `pages/4_📐_Dimensionamiento.py`.

## Criterios de aceptación

1. Vista 3D: terreno y los 308 módulos de Urabá, coloreados por inversor
   (154 + 154 con 22 en serie y 7 + 7; 168 + 140 con 28 y 6 + 5).
2. Plano eléctrico con strings, inversores, filas y punto de conexión.
3. Luz en el suelo, mapa mensual, maquinaria y coherencia en el reporte.
4. Producción muestra la calidad del módulo y el mismatch aplicados y no
   «Factor Mismatch 100 %»; altitud con valor; textos de granja; aviso de
   suciedad en 0 %; nota de PR > 100 % solo si aplica.
5. Ficha LV con 1.500 V → 🟠; ficha oficial → sin alertas; margen de Voc
   1.386 V → 🔴, 1.089 V → 🟠, 990 V → 🟢 (límite 1.100 V).
6. Un reporte de fachada conserva sus textos.
7. El manual del Asistente lo explica (sección 103).
