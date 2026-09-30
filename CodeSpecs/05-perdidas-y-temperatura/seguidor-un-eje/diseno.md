# Diseño — 🌾 Granja FV, fase 4: seguidor de un eje con backtracking frente a la estructura fija

**Estado:** validación

## Entradas

- TMY (`G_h`, `Gd_h`, `Gb_n`), latitud, longitud, altitud, albedo.
- Fija: `tilt_deg`, `azimut_deg`, `gcr`, `altura_m`, `ancho_m` del campo.
- Seguidor (`SEGUIDOR_DEFECTO`): `modulos_ancho` 1, `gcr` 0,35,
  `altura_eje_m` 2,0, `angulo_max_deg` 60, `celdas_partidas` sí.
- Largo del módulo (ficha).

## Salidas

- `comparar_seguidor_fijo(...) -> dict`: `fijo`, `backtracking`,
  `sin_backtracking` (luz anual efectiva y óptica, mensual, horas con
  sombra), ganancias %, pérdida eléctrica %, `dia_ejemplo`, `geometria`.
- `energia_estimada(E_fija, comparación)`.
- Estado: `granja_seg_*` y `granja_seguidor` (con firma).

## Tipos de datos

`dict`, `list[float]`, `pandas.Series`, `numpy.ndarray`.

## Errores posibles

- Sin recurso solar o campo con errores: no se ofrece la comparación.
- Horas de noche: giro 0 y sin luz.

## Dependencias

`pvlib` 0.11.1 (`tracking`, `bifacial.infinite_sheds`, `shading`),
`pages/9b_🌾_Granja_FV.py`.

## Criterios de aceptación

1. Fracción sombreada igual a `shaded_fraction1d` (±1e-6); con
   backtracking siempre 0.
2. Apartadó: el seguidor con backtracking gana entre 10 y 40 % frente a la
   fija; su luz efectiva es igual a la óptica.
3. Sin backtracking: horas con sombra, pérdida eléctrica > 0 y menos luz que
   con backtracking; celdas enteras pierden más que partidas.
4. Mensual suma el anual; el giro con backtracking nunca supera al del
   seguimiento puro; mañana al Este y tarde al Oeste.
5. Borde bajo = altura del eje − ancho ÷ 2 × sen(giro máximo), con aviso si
   queda a menos de 0,5 m.
6. La página compara, oculta el resultado viejo y estima la energía.
7. El manual del Asistente lo explica (sección 96).
