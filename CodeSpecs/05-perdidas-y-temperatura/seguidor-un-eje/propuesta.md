# Propuesta — 🌾 Granja FV, fase 4: seguidor de un eje con backtracking frente a la estructura fija

**Estado:** validación

## Objetivo

Comparar con el mismo modelo la luz frontal del campo fijo y de un seguidor
de un eje, con y sin backtracking, incluida la pérdida eléctrica de la
sombra parcial.

## Alternativa recomendada

Aprobada por el usuario el 30-sep-2026 (fases de 🌾 Granja FV en su orden).

- `calculos/seguidor.py`:
  - Giro con `pvlib.tracking.singleaxis` (eje Norte–Sur horizontal).
  - Luz frontal con `infinite_sheds` para la fija del campo y para el
    seguidor con y sin backtracking (mismo cielo y misma sombra entre filas).
  - Sin backtracking: fracción sombreada 2D (igual a
    `pvlib.shading.shaded_fraction1d`) y pérdida eléctrica con
    `pvlib.shading.direct_martinez`; bloques a lo ancho = módulos × 2 con
    celdas partidas, × 1 con celdas enteras.
  - Mensual, día de ejemplo (21 de marzo), geometría y borde bajo con el
    giro máximo; `energia_estimada` proporcional a la luz frontal.
- 🌾 Granja FV, sección 7: datos del seguidor (se guardan con el
  proyecto), botón «🔄 Comparar seguidor y estructura fija», tarjetas,
  gráficas, aviso del borde bajo y estimación de energía; el resultado se
  oculta si cambian los datos.
- Manual del Asistente, sección 96.

## Alternativas descartadas

- Cambiar la cadena de energía (Motor Óptico, Mismatch, Producción) a
  seguidor: toca IAM, temperatura, bifacialidad y recorte con ángulos que
  cambian cada hora; se deja para una fase propia, con la comparación
  como paso previo para decidir.
- Solo pérdida óptica sin backtracking: en luz directa el seguidor sin
  backtracking recibe casi lo mismo que con backtracking; la diferencia que
  importa es la eléctrica.

## Fuera de alcance

- Seguidores de dos ejes, eje inclinado o terreno inclinado.
- Costo del seguidor y cara trasera del seguidor bifacial.
