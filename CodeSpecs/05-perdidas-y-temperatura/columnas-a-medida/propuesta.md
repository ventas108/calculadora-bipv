# Propuesta — Columnas a medida

**Estado:** validación

## Objetivo

Que el generador ubique cada columna en su posición real, con la misma
precisión que una columna generada sola.

## Alternativa recomendada

Pedida por el usuario el 3-oct-2026 («prepara la Spec columnas a medida en
el generador»).

- `generar_puntos_modulos(..., posiciones_columnas_m=None)`: distancia, a lo
  largo de la horizontal del plano, desde la esquina hasta el borde
  izquierdo de cada columna (vista desde afuera). Vacío = separación
  regular, sin cambios.
- Validaciones: una posición por columna, en orden, primera ≥ 0, sin
  solaparse (separadas al menos el ancho del módulo).
- `parsear_posiciones(texto)`: «0; 1,1; 3,43» o «0 1.1 3.43»; coma decimal.
- Vista 3D: campo «Posición de cada columna (m, opcional)» antes del botón.
- Guía (paso de puntos 3D) y manual del Asistente, sección 127, con el
  ejemplo de La Salle.

## Alternativas descartadas

- Una superficie por tramo regular: multiplica superficies, inversores y
  strings que en la realidad son uno solo.
- Posiciones de los centros en lugar de los bordes: la esquina ya es un
  borde; medir bordes evita mezclar referencias.

## Fuera de alcance

Filas a medida (las filas siguen siendo regulares).
