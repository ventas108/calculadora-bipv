# Diseño — Baja luz de CIGS con factor de forma bajo

**Estado:** validación

- `calculos/modelo_iv.py`, función `estimar_sdm_desde_ficha`:
  - la malla de búsqueda del factor de idealidad pasa de [0,75, γ de partida]
    a [0,75, máx(γ, 2,2)], con 49 puntos;
  - R_s sigue re-anclado a la Pmax de la ficha, así que el STC se reproduce;
  - los avisos numéricos de los puntos no físicos se silencian dentro de
    `_rel_seguro`, porque esos puntos ya se descartan;
  - si el resultado queda a más de 1 punto del objetivo,
    `_error_ajuste_200` explica el valor alcanzado.
- `pages/3_🔬_Motor_IV.py`:
  - `_mostrar_origen_modelo(sdm)` se llama en los dos caminos: el panel de
    Dimensionamiento y el del selector;
  - muestra el aviso de `_error_ajuste_200`.
