---
name: BIPV - modelo bifacial en POA
description: Decisiones del modo bifacial (pvlib infinite_sheds) en calcular_poa y su caché
---

Regla: en modo bifacial, `poa_global` sale ÍNTEGRO de `pvlib.bifacial.infinite_sheds`
(frente con sombreado fila-fila + trasera × bifacialidad). Nunca mezclar el frente
haydavies clásico con la trasera de infinite_sheds.
**Why:** la revisión architect marcó FAIL el híbrido — modelos con supuestos
geométricos distintos sobreestiman con GCR alto; todo aguas abajo (Motor Óptico,
Producción, Financiero) consume `poa_global`.
**How to apply:** cualquier cambio en `calculos/solar.py::calcular_poa` con
`bifacial` activo debe conservar esa base única; guardia: `scripts/test_bifacial.py`.

Caché de Recurso Solar: el pickle de disco guarda SIEMPRE la POA monofacial; la
ganancia bifacial se recalcula localmente. La clave lleva sufijo `_albXX` solo si
albedo ≠ 0.20 (para no invalidar cachés viejos del servidor) y "Limpiar caché"
debe borrar por glob todas las variantes.

Catálogo: `BifacialidadPct` en el Excel → `bifacialidad_pct` en panel_dict; la
ruta del Excel de paneles ahora es relativa al módulo con fallback a /var/www.
