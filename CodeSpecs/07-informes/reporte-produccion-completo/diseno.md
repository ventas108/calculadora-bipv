# Diseño — Reporte PDF de producción completo para el cliente

**Estado:** validación

## Entradas

- `res_produccion`, `poa_anual_kWh_m2`, `motor_optico_summary`.
- `panel_dict`, `N_paneles_final`, `N_serie`, `reparto_strings_inversores`,
  `inversor_dict_dim`, `produccion_n_inversores`, `produccion_p_ac_total_w`.
- `bifacial_cfg`; `granja_fv`, `granja_fv_resultado`, `poa_geometria_filas`,
  `granja_sombra_estimada`, `granja_luz_suelo`, `granja_seguidor`,
  `granja_electrico_cfg`.

## Salidas

- Filas `(etiqueta, valor, unidad, nota)` por sección; pérdidas como lista
  de `{etapa, kwh, delta_kwh, pct, nota}`; bloques por inversor.
- HTML del reporte con las secciones nuevas.

## Tipos de datos

`list[tuple]`, `list[dict]`, `dict`, `str`.

## Errores posibles

- Sin Producción o sin POA: no hay diagrama de pérdidas.
- Proyecto que no es granja o sin campo: no hay sección Granja FV.
- Datos que faltan: se muestran como «—» (nunca se inventan).

## Dependencias

`calculos/produccion.perdidas_desglosadas`, `calculos/granja_electrico`,
`pages/10_📄_Reporte_PDF.py`, `pages/6_📊_Produccion.py`.

## Criterios de aceptación

1. Urabá: 308 módulos, 221,76 kWp, 28 en serie (11 strings), 2 × Growatt,
   200 kW AC, reparto 6 + 5, DC/AC 1,11 y recorte.
2. Pérdidas iguales a la tabla de Producción (de ① E ref a ⑤ E_ac, con el
   recorte).
3. Bifacial: GCR 39,8 %, mesa 2,63 m, sombra trasera 5 %, mismatch 10 %.
4. Granja: campo, energía, agrivoltaica, seguidor, eléctrico y tabla de
   bloques; nada si no es granja.
5. La página genera el reporte con esas secciones y sin nombrar el software
   de referencia.
6. Producción guarda los inversores de la simulación.
7. El manual del Asistente lo explica (sección 101).
