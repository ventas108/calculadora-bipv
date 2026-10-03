# Diseño — Sombra por string

**Estado:** validación

## Entradas

- `FS_geometrico` por punto y hora (`calcular_fs_horario`).
- Número de puntos de la superficie.

## Salidas

- Resultado por superficie: `fraccion_modulos_sombra` y `profundidad_sombra`
  (8760 valores entre 0 y 1, o `None` con un solo punto).
- `simular_bypass_horario(..., profundidad_sombra=None)`.
- Superficie del proyecto físico con los dos campos cuando existen.

## Tipos de datos

`np.ndarray` de 8760 `float`. Umbral de punto sombreado: 0,05, el mismo que
`umbral_shade` del bypass.

## Errores posibles

- Serie con otra longitud o con NaN: `_validar_serie_horaria` lanza
  `ValueError`.
- Sombra nueva sin los dos campos: se retiran los anteriores.
- Cambio de geometría con `p_shade_nuevo`: se retiran los dos campos.

## Dependencias

`calculos/sombras_3d.py`, `calculos/mismatch_bypass.py`,
`calculos/vinculador_sombra_multisuperficie.py`,
`calculos/adaptador_multisuperficie.py`,
`calculos/transicion_multisuperficie.py`,
`calculos/persistencia_multisuperficie.py`.

## Criterios de aceptación

1. 4 puntos, 1 con sombra total: promedio 0,25; fracción 0,25; profundidad 1.
2. Sin `profundidad_sombra`, el bypass da exactamente lo mismo que antes.
3. 1 de 18 módulos sin luz: pérdida ≈ 1/18 con bypass activo.
4. String entero a media luz: pierde ≈ la mitad, no todo.
5. Los dos campos viajan con la superficie, caducan con la sombra y se
   guardan con el proyecto.
6. Modo físico: con un módulo entero a la sombra, la energía AC baja más de
   3 % frente al promedio.
7. Con un solo punto se mantiene el promedio.
8. Sección 123 del manual sin nombres comerciales de otras apps.
