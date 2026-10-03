# Spec — Sombra por string

**Estado:** validación

## Alcance de la fase

Modo físico multi-superficie con sombra de 🗺️ Vista 3D: cómo llega la sombra
de los puntos de análisis al cálculo de bypass de cada string.

## Problema a resolver

1. La sombra de cada superficie (`p_shade`) es el promedio horario de la
   sombra de sus puntos.
2. `simular_bypass_horario` usa ese mismo número para dos cosas: la fracción
   de módulos sombreados y la luz que pierden.
3. Ejemplo: un balcón tapa por completo 1 de 18 módulos. El promedio es
   1/18 ≈ 5,6 %, y el bypass lo lee como «1 módulo con 94 % de luz». El diodo
   casi nunca se activa y la pérdida sale casi nula.
4. Resultado: la sombra parcial de balcones y árboles (módulos enteros a la
   sombra) queda muy subestimada.

## Contexto

Reconstrucción de La Salle (Torre 5, 3-oct-2026): la sombra media por módulo
de la app coincidió con la app estándar de referencia de la tesis (SO 12,4 %
frente a 12,6 %; SE 3,2 % frente a 3,0 %). La pérdida de energía salió en
0,28 %, frente a 3,7 % de la tesis; la cota «el peor módulo limita el string»
daba ≈ 0,7 %.
