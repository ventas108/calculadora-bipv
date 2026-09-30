# Diseño — 🌾 Granja FV, fase 3: agrivoltaica — luz para el cultivo, mapa de sombra y maquinaria

**Estado:** validación

## Entradas

- Resultado de `granja_fv.calcular_campo` (GCR, huella, elevación, altura
  superior, inclinación, azimut, corredor).
- TMY (`G_h`, `Gd_h`), latitud, longitud, altitud.
- `granja_altura_maquinaria_m` (2,5 m) y `granja_ancho_maquinaria_m` (2,2 m).

## Salidas

- `luz_en_el_suelo(...) -> dict`: `y_m`, `pct`, `anual_kwh_m2`,
  `vista_cielo`, `referencia_kwh_m2`, `media_pct`, `media_kwh_m2`,
  `bajo_mesa_pct`, `entre_filas_pct`, `min_pct`, `max_pct`,
  `homogeneidad`, `mensual_pct` (12 × franjas), `geometria`.
- `paso_maquinaria(...) -> [{id, nivel, texto}]` con `categoria`,
  `maquinaria_bajo`, `maquinaria_entre`.
- Estado: `granja_luz_suelo` (con su firma de geometría).

## Tipos de datos

`dict`, `list[float]`, `numpy.ndarray`.

## Errores posibles

- Campo con errores o sin recurso solar: no se ofrece el cálculo.
- Sol a menos de 2° del horizonte: sin luz directa (cenit > 88°).

## Dependencias

`pvlib` (posición solar), `calculos/granja_fv.py`, `pages/9b_🌾_Granja_FV.py`.

## Criterios de aceptación

1. Fracción de cielo igual a `pvlib.bifacial.utils.vf_ground_sky_2d` (±0,002)
   y fracción de suelo con sol igual a `_unshaded_ground_fraction` (±0,001).
2. Con el sol en el cenit la sombra queda justo bajo la mesa.
3. Apartadó: luz media ≈ 1 − GCR (≈ 60 %); bajo la mesa < media < entre filas.
4. Más altura → luz más pareja con la misma media; filas separadas → más luz.
5. Maquinaria: Apartadó categoría I, tractor de 2,5 m no pasa por debajo
   (necesita 2,80 m) y sí por el corredor de 4,01 m; una máquina que pasa por
   debajo no depende del corredor.
6. La página muestra avisos, métricas, perfil y mapa; oculta el resultado
   si cambia la geometría; el texto ya no dice que no cambia la energía.
7. El manual del Asistente lo explica (sección 95).
