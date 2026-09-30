# Propuesta — Sombra entre filas y cara trasera según la geometría del campo (🌾 Granja FV, fase 2)

**Estado:** validación

## Objetivo

Que la energía de una granja use la geometría del campo diseñado en 🌾
Granja FV, con paneles monofaciales y bifaciales, sin contar dos veces la
sombra.

## Alternativa recomendada

Aprobada por el usuario el 30-sep-2026 («sigamos con la fase 2 (sombra entre
filas y cara trasera según la geometría del campo)»).

- `solar.aplicar_sombra_filas`: corre `pvlib.bifacial.infinite_sheds` con
  el GCR del campo y con una fila aislada (GCR 0,01); la razón de cada
  componente frontal (directa, difusa del cielo, reflejada del suelo)
  multiplica la POA clásica. `calcular_poa(..., filas=...)` la usa solo con
  paneles monofaciales: con bifacial la cara frontal de `infinite_sheds` ya
  trae la sombra.
- Modelo bifacial: `ancho_colector_m` visible en ☀️ Recurso Solar; nuevos
  `sombra_trasera_pct` y `mismatch_trasero_pct` (0 por defecto) que
  multiplican el aporte trasero por (1 − s)(1 − m).
- 🌾 Granja FV: botón «⚡ Usar la geometría del campo en la energía»
  (`filas_energia` y, con bifacial, `bifacial_cfg`), botón «📏 Estimar la
  sombra entre filas de este campo» y comprobación 🟢/🟠 de la POA vigente
  (`poa_geometria_filas`).
- Manual del Asistente, sección 94.

## Alternativas descartadas

- Usar `poa_front` de `infinite_sheds` como POA monofacial: cambia el
  modelo de cielo y el reparto de componentes que usan Motor Óptico y
  Mismatch; la razón aísla solo el efecto de las filas.
- Un factor anual fijo de sombra: no ve las horas de sol bajo ni el clima.
- Aplicar los factores traseros por defecto (5 % y 10 %): cambiaría la
  energía de los proyectos guardados sin que el usuario lo pida.

## Fuera de alcance

- Sombra eléctrica por celdas o por strings (la pérdida es de irradiancia).
- El horizonte lejano sigue quitando la luz directa sin distinguir la parte
  ya sombreada por la fila vecina (efecto muy pequeño a 10°).
