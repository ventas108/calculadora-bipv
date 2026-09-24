# Propuesta — Validación visible de los puntos 3D por superficie

**Estado:** validación

## Objetivo

Que ningún punto escrito por el usuario se pierda sin aviso y que los puntos
geométricamente inválidos se detecten antes de calcular la sombra.

## Alternativas consideradas

1. **Editor gráfico de puntos sobre la malla.** Útil a futuro, pero es una
   Spec mayor de interfaz.
2. **Parser puro con errores por línea + vista previa geométrica.**
   Recomendada.

## Alternativa recomendada

1. `parsear_puntos_3d(texto, nombre_superficie)` en `calculos/` (pura):
   devuelve puntos válidos y errores por número de línea con su motivo.
   Formatos aceptados: `x,y,z` con punto decimal, y `x;y;z` con coma o punto
   decimal. Una línea ambigua o incompleta es error, nunca se descarta.
2. La página muestra los errores bajo cada recuadro y deshabilita
   «🌳 Calcular sombra» mientras haya líneas con error.
3. Con la malla cargada, vista previa con `validar_puntos` (misma función del
   motor): marca los puntos dentro del volumen o a menos de 10 cm antes de
   calcular.
4. Los puntos se asocian por `uid` de superficie.

Fuera de alcance: editor gráfico y cambios del motor de sombra.
