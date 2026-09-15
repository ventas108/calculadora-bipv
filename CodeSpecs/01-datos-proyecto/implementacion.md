# Implementación — Datos del proyecto

**Estado:** implementado

## Cambios realizados

- `set_tarifa_from_ciudad()` ya no sobreescribe `tarifa_cop_kwh` cuando la
  `tarifa_fuente` actual en `session_state` es `"Proyecto"` o `"Financiero"`
  (edición manual). Solo actualiza el valor cuando la fuente es `"catálogo"`
  o `"valor por defecto"`.
- Cuando la fuente es manual y la nueva ciudad sí trae tarifa en el catálogo,
  el valor de referencia queda disponible en la nueva clave de
  `session_state` `tarifa_sugerida_ciudad` (sin aplicarlo), y se limpia si
  la ciudad nueva no tiene tarifa en catálogo o si la fuente deja de ser
  manual.
- En `1_🏠_Proyecto.py`, tras el widget de tarifa, se agregó un aviso
  (`st.info`) que se muestra cuando `tarifa_sugerida_ciudad` difiere del
  valor manual actual, con un botón explícito ("Usar tarifa de referencia
  de la nueva ciudad") para aplicarlo — nunca se sobreescribe solo. El aviso
  se limpia automáticamente si el valor manual ya coincide con la
  referencia.
- Se agregaron tests para las dos reglas de precedencia y para el recorte
  defensivo de `factor_ocupacion_pct` (que ya existía en el código pero no
  tenía cobertura de test).

## Archivos modificados

- `bipv_python/calculos/tarifa_utils.py`
- `bipv_python/pages/1_🏠_Proyecto.py`
- `bipv_python/tests/test_tarifa_from_ciudad.py` (nuevo)
- `bipv_python/tests/test_clamp_factor_ocupacion.py` (nuevo)

## Resultado de las pruebas

Ejecutado con `python -m pytest` (venv del sistema; `streamlit`/`pandas`/
`python-docx` no están instalados en este entorno de desarrollo, así que el
resto de la suite no es un baseline limpio aquí):

- Los 11 tests nuevos (`test_tarifa_from_ciudad.py` + `test_clamp_factor_ocupacion.py`)
  pasan.
- Suite completa: `378 passed, 5 failed, 58 errors` — los 58 errores de
  colección y las 5 fallas preexistentes son por dependencias no instaladas
  en este entorno (`streamlit`, `pandas`, `python-docx`), no por este cambio;
  ninguno de los archivos modificados aparece entre ellos.
- `test_invalidacion_ciudad.py` (único test previo que también inspecciona
  `1_🏠_Proyecto.py`) sigue en verde sin cambios.
- `python3 -m py_compile` confirma sintaxis válida en ambos archivos de
  producción modificados.
