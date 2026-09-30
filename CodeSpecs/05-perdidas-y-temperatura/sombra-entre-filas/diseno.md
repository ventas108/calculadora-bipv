# Diseño — Sombra entre filas y cara trasera según la geometría del campo (🌾 Granja FV, fase 2)

**Estado:** validación

## Entradas

- `filas = {gcr, altura_m, ancho_colector_m}` (de `granja_fv.geometria_filas`).
- `bifacial_cfg`: `gcr`, `altura_m`, `ancho_colector_m`,
  `sombra_trasera_pct`, `mismatch_trasero_pct`.
- TMY (`G_h`, `Gd_h`, `Gb_n`), inclinación, azimut, albedo.

## Salidas

- `calcular_poa(..., filas=None)`: POA con la sombra entre filas en
  `poa_direct`, `poa_sky_diffuse`, `poa_ground_diffuse`, `poa_diffuse` y
  `poa_global` (monofacial).
- Bifacial: `poa_rear` y `poa_global` con el factor (1 − s)(1 − m).
- Estado: `filas_energia`, `poa_geometria_filas`, `granja_sombra_estimada`.
- `granja_fv`: `geometria_filas`, `geometria_poa`, `mismas_filas`,
  `aplicar_geometria_a_energia`, `estado_poa_filas`, `sombra_filas_estimada`.

## Tipos de datos

`pandas.DataFrame`, `dict`, `float`.

## Errores posibles

- GCR fuera de rango: se limita a 0,02–0,95.
- Hora sin luz de fila aislada: razón 1 (sin cambio).
- Campo con errores (filas que se tocan): no se ofrece la estimación.

## Dependencias

`pvlib.bifacial.infinite_sheds` (0.11.1), `pages/2_☀️_Recurso_Solar.py`,
`pages/9b_🌾_Granja_FV.py`.

## Criterios de aceptación

1. `filas=None` y factores traseros en 0: resultado idéntico al anterior.
2. Con filas ninguna hora sube; las componentes suman el global.
3. Apartadó: pérdida frontal entre 0,05 % y 0,5 % (referencia 0,20 %); más
   GCR o más inclinación → más pérdida.
4. Cara trasera con 5 % y 10 %: aporte trasero × 0,855 exacto; frontal igual.
5. El botón escribe la geometría (y la del modelo bifacial si está activo)
   sin tocar lo demás.
6. Coherencia 🟢 con la geometría vigente y 🟠 sin ella o con otra.
7. 🌾 Granja FV usa las coordenadas del predio de ☀️ Recurso Solar.
8. El manual del Asistente lo explica (sección 94).
