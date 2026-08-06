---
name: BIPV - Sombras desde SketchUp
description: Ruta alternativa de FS horario por ray-casting (trimesh) — convenciones críticas de alineación y formato
---

## Regla
La página de Sombras SketchUp genera el mismo CSV de FS que la calculadora web
(Mes, Dia, Hora, FS_geometrico, FS, Fachada) y entra a la Página 5 sin tocar la cadena.

**Why:** el parser de la Página 5 prioriza `FS_geometrico` (sombra física; las nubes no
deben activar bypass) y alinea por (mes,dia,hora) contra el TMY — el TMY de PVGIS viene
en UTC, así que el ray-casting DEBE usar el mismo índice del TMY de la sesión o la sombra
queda corrida ~5 h. Por eso la página bloquea si no hay `tmy_df`.

**How to apply:**
- Convención geométrica SketchUp: X=Este, Y=Norte, Z=arriba, metros; corrección de norte
  = giro −θ alrededor de Z (θ horario visto desde arriba). Acimut pvlib desde norte, horario.
- FS: 0=sin sombra, 1=sombra total (nativo del bypass; sin riesgo de FS invertido).
- La Página 5 PROMEDIA los puntos por timestamp con igual peso → un punto por fila de
  módulos con conteos similares.
- trimesh puro-Python: límite 300k triángulos / 6M rayos; validar puntos dentro del sólido
  (darían sombra total falsa).
- Servidor: instalar trimesh en el venv (`venv/bin/pip install trimesh`) — está en
  requirements.txt pero el deploy habitual no reinstala dependencias.
