# Diseño — Difusa en la sombra por string

**Estado:** validación

## Entradas

- Malla 3D, puntos y orientación de cada superficie; `transparencia`.
- POA con componentes `poa_direct`, `poa_sky_diffuse`, `poa_ground_diffuse`.

## Salidas

- Resultado por superficie: `factor_cielo_visible` (float 0–1 o `None`).
- `calcular_poa_superficie(..., reduccion_diffusa_isotropica=1.0)`.
- `simular_bypass_horario(..., fraccion_directa=None)`.
- `attrs["poa_circumsolar"]` en la POA reducida.

## Tipos de datos

Factor escalar por superficie; fracción directa horaria de 8760 valores.

## Errores posibles

- Superficie sin orientación: sin factor, resultado como antes.
- Sombra nueva sin factor: se retira el anterior.
- Bifacial: `calcular_poa` no aplica la reducción (comportamiento existente).

## Dependencias

`calculos/sombras_3d.py`, `calculos/solar.py`, `calculos/multi_superficie.py`,
`calculos/mismatch_bypass.py`, `calculos/transicion_multisuperficie.py`,
`calculos/vinculador_sombra_multisuperficie.py`,
`calculos/adaptador_multisuperficie.py`,
`calculos/persistencia_multisuperficie.py`.

## Criterios de aceptación

1. Escena lejana: factor ≈ 1; edificio enfrente: factor entre 0,3 y 0,9;
   transparencia 0,5: la mitad del cielo tapado.
2. El factor viaja con la superficie, caduca con el TMY, se retira si la
   sombra nueva no lo trae y se guarda con el proyecto.
3. Modo físico: factor 1 → resultado idéntico; factor 0,5 → POA y energía
   más bajas.
4. Bypass: sin `fraccion_directa`, resultado idéntico; con fracción directa
   0,6 y sombra total, el string conserva ≈ 40 % de la luz.
5. Sección 124 del manual sin nombres comerciales de otras apps.
