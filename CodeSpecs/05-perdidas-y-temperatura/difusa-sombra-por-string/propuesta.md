# Propuesta — Difusa en la sombra por string

**Estado:** validación

## Objetivo

Que el modo físico reste la difusa que tapa el entorno 3D y que el bypass
deje la difusa a los módulos a la sombra.

## Alternativa recomendada

Pedida por el usuario el 3-oct-2026 («prepara esa spec y repite luego La
Salle»).

- `calcular_fs_horario_por_superficie`: `factor_cielo_visible` = promedio de
  `f_svf` de los puntos (grilla de 10°). Con transparencia, el cielo tapado
  se multiplica por (1 − transparencia). Sin orientación completa: `None`.
- `calcular_poa_superficie` acepta `reduccion_diffusa_isotropica` y la pasa a
  `calcular_poa`. La reducción existente solo toca la difusa isotrópica de
  Hay-Davies y ahora deja la difusa circunsolar en `attrs`.
- `recalcular_fisica_superficie`, solo si la superficie trae
  `factor_cielo_visible`:
  - POA con la difusa reducida;
  - el bypass recibe `fraccion_directa` = (directa + circunsolar) / global.
- `simular_bypass_horario`: `fraccion_directa` opcional. La profundidad
  efectiva es profundidad × fracción directa; con `None`, el resultado es
  idéntico.
- Vinculador, adaptador y persistencia: el campo viaja, caduca y se guarda
  como la sombra.
- Manual del Asistente, sección 124, y registro.

## Alternativas descartadas

- SVF por módulo en el bypass: la difusa es pareja entre módulos vecinos y
  constante en el día; su efecto de mismatch es menor que el de la directa.
- Restar toda la difusa del cielo con el SVF (también la circunsolar): la
  circunsolar se tapa con el haz, hora a hora, no con el cielo visible.

## Fuera de alcance

- Modo simplificado y bypass con CSV: no tienen escena 3D.
- Sombra parcial dentro del módulo (celdas y diodos).
