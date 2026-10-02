# Diseño — Curva de baja irradiancia de la ficha

**Estado:** validación

## Entradas

- `panel["curva_baja_irradiancia"]`: texto `"300:80; 400:88"`, lista de pares
  o dict.
- Valores válidos: G entre 50 y 999 W/m²; η entre 30 y 115 % (fracciones ≤ 1,5
  se pasan a %).

## Salidas

- `parsear_curva_baja_irradiancia(valor) -> list[(G, η)]`, ordenada.
- `estimar_sdm_desde_ficha` con curva devuelve:
  - `_ajuste_200 = "curva"` y `_metodo = "pvsyst_v6_calibrado_curva"`;
  - `_ajuste_curva = [{G, ficha, modelo, diferencia}]`;
  - `_desv_max_curva`;
  - `_rel_200_modelo`, el valor del modelo a 200 W/m².
- 🔬 Motor IV:
  - línea de origen;
  - gráfica «Eficiencia relativa vs G» (modelo de 100 a 1.000 W/m² y puntos de
    la ficha).
- 📋 Catálogo: columna editable que se guarda en `CurvaBajaIrradiancia`.

## Tipos de datos

`list[tuple[float, float]]`; `_ajuste_curva: list[dict] | None`;
`_desv_max_curva: float | None`.

## Errores posibles

- Texto ilegible o puntos fuera de rango: se ignoran. Si no queda ninguno, no
  hay curva y se usan los métodos anteriores.
- Curva que el modelo de un diodo no puede seguir: se usa el mejor ajuste
  físico y queda avisado en `_error_ajuste_200` con la irradiancia del peor
  punto.
- Puntos de la malla no físicos (R_s ≤ 0): se descartan y se busca el borde.

## Dependencias

`_resolver_Rs_pvsyst_por_pmax`, `_resolver_IL_Io_stc` y `_pmax_pvsyst_a_G`
(`calculos/modelo_iv.py`); `calcular_pmax_vectorizado` para la gráfica.

## Criterios de aceptación

1. Teja de 32 W con su curva:
   - ±1,5 puntos entre 500 y 900 W/m²;
   - al menos 4 puntos más cerca de la ficha que el 97 % por defecto a 300, 400
     y 500 W/m²;
   - STC reproducido.
2. Aviso de 300 W/m² cuando la ficha no se puede seguir.
3. Curva fabricada con el modelo: se recupera con desviación ≤ 0,3.
4. La curva manda sobre el dato de 200 W/m²; sin curva no cambia nada (90N:
   factor 1,053; 70N: 1,557).
5. Los 5 motores dan lo mismo con la teja calibrada (guardia de física).
6. Catálogo, página de edición y Motor IV con la columna, la línea y la gráfica.
