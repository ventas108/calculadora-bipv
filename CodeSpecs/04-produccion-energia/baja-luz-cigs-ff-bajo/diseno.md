# Diseño — Baja luz de CIGS con factor de forma bajo

**Estado:** validación

## Entradas

Ficha del catálogo: Voc, Isc, Vmp, Imp, N_s (opcional), tecnología y
`eficiencia_rel_200` (opcional).

## Salidas

- `estimar_sdm_desde_ficha` devuelve `gamma_ref` en [0,75, 2,2],
  `_rel_200_modelo` y `_error_ajuste_200`: `None` o un texto con el valor
  alcanzado.
- 🔬 Motor IV muestra «Origen del modelo» en los dos caminos (Dimensionamiento y
  selector), con la línea ⚠️ si el ajuste no llegó al objetivo.

## Tipos de datos

`_error_ajuste_200: str | None`; `gamma_ref: float`.

## Errores posibles

- Puntos de la malla donde el modelo no es físico (R_s ≤ 0, desbordes): se
  descartan y sus avisos numéricos se silencian dentro de `_rel_seguro`.
- Objetivo inalcanzable: se usa el valor físico más cercano y queda avisado.

## Dependencias

`_resolver_Rs_pvsyst_por_pmax`, `_resolver_IL_Io_stc` y `_pmax_pvsyst_a_G` de
`calculos/modelo_iv.py`.

## Criterios de aceptación

1. Ficha de factor de forma bajo, con N_s 40 y sin N_s: 97 ± 0,3 % a
   200 W/m², factor de idealidad > 1 y STC reproducido.
2. FLEX-03 90N sin cambios: 97 % y factor de idealidad 1,053.
3. Objetivo de 60 %: `_error_ajuste_200` lo explica.
4. Los 5 motores dan lo mismo con el caso nuevo (guardia de física).
5. «Origen del modelo» llamado desde los dos caminos de 🔬 Motor IV.
