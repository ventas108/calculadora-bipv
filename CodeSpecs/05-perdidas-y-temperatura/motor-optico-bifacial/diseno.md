# Diseño — Motor Óptico en modo bifacial

**Estado:** validación

## Entradas

- `poa_df` de `calculos/solar.calcular_poa`; en bifacial trae `poa_front`,
  `poa_rear` y `poa_global = poa_front + bifacialidad × factor × poa_back`.
- Los mismos parámetros de siempre de `cascada_optica`.

## Salidas

- `cascada_optica`:
  - Columnas nuevas de `result_df`: `poa_frontal_optica`,
    `poa_trasera_optica` (0 en monofacial).
  - Resumen: `bifacial` (bool), `aporte_trasero_kWh_m2`
    (antes del IAM) y `aporte_trasero_optico_kWh_m2` (después).
  - `f_iam_prom = 1 − pérdida IAM ÷ POA bruta`,
    `f_soil_prom = 1 − pérdida suciedad ÷ POA óptica`,
    `f_term_prom = POA post-térmica ÷ POA post-suciedad`
    (ponderados por energía; su producto es `factor_global`).
- `motor_optico.poa_publicable(poa_df, result_df, columna)`: copia de la POA
  con `poa_global` = la etapa pedida y, en bifacial, `poa_front` = global −
  aporte trasero óptico; la página la usa para `poa_sin_termico_df` y
  `poa_efectiva_df`.
- `motor_optico.mensaje_impacto_optico(pct, tilt_deg) -> (nivel, texto)`.

## Tipos de datos

`numpy.ndarray` horarios, `dict` de resumen, `pandas.DataFrame`.

## Errores posibles

- `poa_front` > `poa_global` por redondeo: el aporte trasero se recorta a 0.
- Hora con componentes clásicas en 0 y `poa_front` > 0: factor IAM de la
  cara frontal = IAM difusa.

## Dependencias

Ninguna nueva.

## Criterios de aceptación

1. Bifacial: POA bruta − IAM − suciedad − térmica = POA efectiva (±0.2
   kWh/m²); el aporte trasero queda dentro de la POA efectiva.
2. Monofacial: la cascada da exactamente lo mismo que antes.
3. La suciedad no se aplica al aporte trasero; la IAM difusa sí.
4. Factores promedio ponderados por energía; su producto es el factor global.
5. `poa_sin_termico_df` en bifacial: `poa_global − poa_front` = aporte trasero
   óptico.
6. El aviso de la sección 5 nombra el tipo de superficie según la inclinación.
7. La cadena multi-superficie ya no cuenta el aporte trasero como pérdida IAM.
8. El manual del Asistente explica el caso con los números de Apartadó.
