# Propuesta — Sombra por string

**Estado:** validación

## Objetivo

Que el bypass reciba, hora a hora, cuántos módulos del string tienen sombra y
cuánta luz pierden esos módulos, en lugar del promedio de la superficie.

## Alternativa recomendada

Pedida por el usuario el 3-oct-2026 («prepara la Spec sombra por string»).

- `sombras_3d.calcular_fs_horario_por_superficie`: además de `p_shade`
  (promedio, sin cambios), devuelve:
  - `fraccion_modulos_sombra`: parte de los puntos con más de 5 % de sombra;
  - `profundidad_sombra`: sombra media de esos puntos (0 si no hay).
  Con un solo punto se devuelven vacíos (`None`): no se sabe cuántos módulos
  tienen sombra y se mantiene el promedio.
- `mismatch_bypass.simular_bypass_horario`: parámetro opcional
  `profundidad_sombra`.
  - `None`: comportamiento anterior, idéntico.
  - Con valor: módulos sombreados = `p_shade × N`; su irradiancia =
    `G × (1 − profundidad)`; el string toma el máximo entre el punto con
    bypass y el punto sin bypass (el MPPT busca el máximo global).
- Vinculador, adaptador y transición: los dos datos viajan con la superficie,
  caducan con la sombra y se descartan si llega una sombra nueva sin ellos.
- Persistencia: se guardan con el proyecto.
- Manual del Asistente, sección 123, y registro.

## Alternativas descartadas

- Usar el peor módulo de cada string: cota alta, sin bypass, exagera la
  pérdida.
- Curva I-V del string celda a celda: más exacta, pero necesita la posición
  de cada celda y la geometría del diodo de bypass; fuera de alcance.
- Cambiar `p_shade` al nuevo método: rompería la huella de los proyectos
  guardados y las demás páginas que lo leen.

## Fuera de alcance

- Asignar cada punto a un string concreto (hoy todos los strings de una
  superficie reciben la misma fracción).
- Separar la difusa en el bypass.
