# Bug real: defaults de temperatura de diseño fijos e inventados en 📐 Dimensionamiento

**Fecha**: 4 de septiembre de 2026
**Disparador**: el usuario adjuntó 3 capturas reales del proyecto Teusaquillo mostrando que
`T_mín diseño` cambiaba entre `-5,00°C` y `6,30°C` en la misma página, sin que él tocara nada, y
pidió verificar si era otro caso de bug silencioso.

## Las 3 capturas (evidencia real)

1. **8:09 a.m.** — 📐 Dimensionamiento: `T_mín diseño = -5,00°C`, `T_celda realista = 36,35°C`,
   `T_celda extremo = 41,94°C`. Sin ninguna leyenda de origen debajo.
2. **8:10 a.m.** (1 min después) — misma página: `T_mín diseño = 6,30°C`, `T_celda realista =
   42,60°C`, `T_celda extremo = 52,20°C`, con una leyenda nueva: *"🌡️ Temperaturas desde TMY
   Bogotá — T_mín: 6.3°C · T_cel realista: 42.6°C · T_cel extremo: 52.2°C (NOCT 45°C · editable
   manualmente)"*.
3. **8:12 a.m.** — 🏠 Proyecto: `T_mín diseño: 5.0°C` (un tercer valor, distinto de los dos
   anteriores).

## Causa raíz confirmada en el código

`pages/4_📐_Dimensionamiento.py` tenía **dos mecanismos compitiendo** por el mismo campo:

1. Un bloque real que recalcula las 3 temperaturas desde el TMY horario real de la ciudad
   (líneas ~197-220), pero **solo se ejecuta si `tmy_df` ya está en `session_state`** — es decir,
   solo después de que el usuario visitó ☀️ Recurso Solar en esa sesión.
2. Un `st.session_state.setdefault(...)` que sembraba un **valor mágico fijo, universal para
   cualquier ciudad**, cuando el TMY todavía no estaba disponible:
   ```python
   st.session_state.setdefault("T_min_diseno", -5.0)
   st.session_state.setdefault("T_cel_realista", 36.35)
   st.session_state.setdefault("T_cel_extremo", 41.94)
   ```

Se verificó contra `datos/ciudades_colombia.py::CIUDADES` (la tabla real por ciudad que también usa
🏠 Proyecto): Bogotá tiene `T_min_diseno=5.0, T_cel_realista=36.35, T_cel_extremo=41.94`. Los
últimos 2 números coinciden por casualidad con el default fijo — **pero el primero no**: el -5.0
es el valor viejo, de antes de un fix ya documentado (`ciudades_colombia.py`, "Bogotá
T_min_diseno=-5.0 -> 5.0") que corrigió ese mismo dato en la tabla de ciudades, pero nunca se
sincronizó con este default independiente de Dimensionamiento.py.

**Para cualquier otra ciudad, los 3 números eran directamente incorrectos** — no solo el primero.
Ejemplo real verificado: Cali tiene `T_min_diseno=12.0, T_cel_realista=47.0, T_cel_extremo=55.0`;
el usuario habría visto `-5.0/36.35/41.94` (los de Bogotá) hasta visitar Recurso Solar.

## Por qué es un bug real, no solo cosmético

El valor sembrado por `setdefault` **no es solo una etiqueta visual** — se lee directamente vía
`key="T_min_diseno"` en el `number_input`, y ese valor (`T_frio`) se pasa a
`evaluar_compatibilidad_string()`, `dimensionar_sistema()` y el cálculo de Voc_max/Vdc_max real
(línea 691 y siguientes). Si un usuario corre el dimensionamiento **antes** de visitar ☀️ Recurso
Solar en esa sesión, el cálculo de compatibilidad eléctrica se hace contra un `T_mín` inventado
(y para ciudades distintas a Bogotá, contra las 3 temperaturas de Bogotá) — un resultado real,
pero basado en un dato falso, exactamente el patrón de bug silencioso que este proyecto ha
corregido repetidamente en otros módulos (catálogo de paneles/inversores).

## Fix aplicado

Se reemplazó el valor mágico universal por el dato real de la ciudad activa del proyecto (mismo
`CIUDADES[ciudad]` que ya usa 🏠 Proyecto), con el valor de Bogotá solo como último recurso si la
ciudad no está en la tabla:

```python
_ciudad_activa_dim = st.session_state.get("ciudad", "Bogotá")
_ciudad_defaults = CIUDADES.get(_ciudad_activa_dim, CIUDADES.get("Bogotá", {}))
st.session_state.setdefault("T_min_diseno", _ciudad_defaults.get("T_min_diseno", 5.0))
st.session_state.setdefault("T_cel_realista", _ciudad_defaults.get("T_cel_realista", 36.35))
st.session_state.setdefault("T_cel_extremo", _ciudad_defaults.get("T_cel_extremo", 41.94))
```

El bloque de auto-población desde el TMY real sigue intacto y sin cambios — sigue siendo la fuente
más precisa una vez disponible (usa el mínimo/percentil real del año meteorológico típico, no solo
el promedio anual de la tabla de ciudades). El fix solo mejora el **placeholder previo**, para que
nunca muestre ni use un número inventado que no corresponde a ninguna ciudad real del proyecto.

## Nota sobre la 3ª fuente (Proyecto: 5.0°C vs Dimensionamiento TMY: 6.3°C)

Estos dos valores **no son un bug** — son dos metodologías reales distintas y legítimas:
`ciudades_colombia.py` da un valor de referencia fijo por ciudad (5.0°C para Bogotá, una
estimación general), mientras que el bloque TMY de Dimensionamiento calcula el mínimo real
histórico del año meteorológico típico específico de esa ubicación (6.3°C). Es normal que difieran
ligeramente; ambos son datos reales, solo con distinta resolución. No se tocó este comportamiento.

## Verificación

- 5 tests nuevos (`tests/test_pagina_dimensionamiento_temperaturas_ciudad.py`), patrón AST/substring
  (no requiere sesión Streamlit autenticada) — ancla el fix y confirma que `CIUDADES` tiene valores
  reales distintos por ciudad (Bogotá ≠ Cali).
- Suite completa ejecutada tras el cambio, sin regresiones en los 4 archivos de test relacionados
  (`test_pagina_dimensionamiento_compat_bateria.py`, `test_temps_diseno_229.py`,
  `test_compatibilidad_string.py`, `test_validacion_vba.py` — estos usan `T_frio=-5.0` como
  parámetro de función directo en pruebas de física, no relacionado con el default de la página).
