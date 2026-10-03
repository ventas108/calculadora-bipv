# Propuesta — Puntos automáticos por módulo

**Estado:** validación

## Objetivo

Generar un punto por módulo con geometría exacta, asignado a su string, y
simular el bypass string por string.

## Alternativa recomendada

Autorizada por el usuario el 3-oct-2026.

- `calculos/puntos_modulo.py`:
  - `vectores_superficie(tilt, az)`: normal `n` (la de `sombras_3d`),
    horizontal `u` = (sen(az − 90°), cos(az − 90°), 0) y `v = n × u`;
  - `generar_puntos_modulos`: centro de cada módulo + `n` × distancia,
    con fila, columna, string y posición;
  - validaciones estrictas: filas × columnas = módulos de los grupos,
    medidas en metros, distancia ≥ 0,10 m, cableado por filas o columnas;
  - `texto_puntos` (al milímetro) y `etiquetar_strings` (solo si el texto
    es exactamente el generado).
- `sombras_3d`: con todos los puntos etiquetados, `sombra_por_string`
  (fracción y profundidad de cada string).
- `mismatch_bypass.simular_bypass_por_strings`: un `simular_bypass_horario`
  por string (N_parallel = 1) y suma de potencias. Con strings idénticos da
  lo mismo que N_parallel strings.
- Adaptador: cada grupo recibe sus strings en orden; si no cuadran con
  `n_paralelo`, error que pide regenerar y recalcular.
- Vinculador y persistencia: el campo viaja, caduca y se guarda.
- Vista 3D: recuadro «🧮 Generar un punto por módulo» por superficie, aviso
  si se editan los puntos generados.
- Guía de la página: los strings se definen antes de generar los puntos.
  Manual del Asistente: sección 125 actualizada y sección 126.

## Alternativas descartadas

- Curva I-V combinada de los strings del MPPT en cada hora: exacta pero
  costosa; ya existe como análisis aparte («🔀 Simular curva IV combinada
  por MPPT»).
- Leer la posición de los módulos desde la escena de Site Designer: la
  escena no trae módulos, solo bloques.
- Cuarta columna «string» en el texto de puntos: más errores de escritura.

## Fuera de alcance

- Varios puntos por módulo (uno por diodo de bypass).
- Campos de módulos no rectangulares.
