# Spec — Difusa en la sombra por string

**Estado:** validación

## Alcance de la fase

Modo físico multi-superficie con sombra de 🗺️ Vista 3D: la luz difusa que
tapa el entorno (balcones, aleros, árboles, edificios vecinos).

## Problema a resolver

1. La sombra 3D de cada superficie solo restaba el rayo directo. El cielo que
   tapa el entorno (difusa) no llegaba al cálculo de energía, aunque la app ya
   sabe calcularlo (`calcular_svf_difuso`).
2. El bypass aplicaba la profundidad de la sombra a toda la luz: un módulo a
   la sombra perdía también la difusa del resto del cielo.

## Contexto

La Salle, fachada SO con balcones, módulos elegidos por la tesis: 4,98 % de
sombra en irradiación (directa + difusa) frente a 2,83 % de pérdida de
energía. Con la difusa, la estimación proporcional total era ≈ 3,3 %,
frente a 3,7 % de la app estándar de referencia. Spec anterior:
`05/sombra-por-string`.
