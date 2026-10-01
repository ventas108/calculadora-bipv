# Diseño — Reporte PDF de proyectos multi-superficie (🗺️ Vista 3D)

**Estado:** validación

## Entradas

- Publicación: `multisup_activo`, `E_ac_anual_kWh_multisup`, `multisup_desglose`,
  `area_total_multisup`, `multisup_origen`, `multisup_estado_electrico`,
  `multisup_sistema`, `multisup_cadena_perdidas` (`pr`, `desglose`),
  `multisup_perdida_bus_kWh`.
- Diseño: `superficies_bipv` (inclinación, azimut, grupos, cruces),
  `multisup_inversores`, panel de cada superficie.

## Salidas

- Filas de resumen; tabla por superficie (orientación, panel, módulos
  físicos, kWp, área, POA, energía, kWh/kWp, PR); filas por panel; tabla de
  inversores (P AC, superficies, strings, módulos, kWp, DC/AC); tabla de
  pérdidas por superficie; cruces; 12 valores mensuales.

## Tipos de datos

`list[tuple]`, `list[dict]`, `list[float]`, `bool`.

## Errores posibles

- Publicación anterior sin `desglose`: el reporte pide volver a publicar.
- Datos que faltan: «—», nunca se inventan.

## Dependencias

`calculos/cadena_perdidas_multisup.py`, `calculos/publicacion_multisuperficie.py`,
`calculos/diseno_electrico_multisup.py`, `calculos/cruce_superficies.py`,
`calculos/topologia_electrica.py`, `pages/10_📄_Reporte_PDF.py`.

## Criterios de aceptación

1. La publicación guarda la tabla de pérdidas por superficie.
2. Resumen: energía, kWp y módulos, kWh/kWp, método y estado eléctrico.
3. Por superficie: módulos donde están (con cruce), kWp, kWh/kWp y PR.
4. Inversores: P AC, strings, módulos, kWp y DC/AC.
5. El reporte multi-superficie no muestra la energía de superficie única
   (una sola cifra) y sí todas las tablas nuevas; sin multi-superficie el
   reporte no cambia.
6. El manual del Asistente lo explica (sección 102).
