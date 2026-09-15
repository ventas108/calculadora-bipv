# Validación — Datos del proyecto

**Estado:** validado

## Checklist de validación del módulo

- [x] Tests nuevos (`test_tarifa_from_ciudad.py`, `test_clamp_factor_ocupacion.py`)
      pasan: 11/11.
- [x] `python3 -m py_compile` confirma sintaxis válida en `tarifa_utils.py` y
      `1_🏠_Proyecto.py`.
- [x] `test_invalidacion_ciudad.py` (test previo que también inspecciona
      `1_🏠_Proyecto.py`) sigue en verde sin cambios.
- [x] Validación funcional en producción: valor manual (850) conservado al
      cambiar a Medellín, aviso mostrado con la tarifa de catálogo correcta
      (900 COP/kWh), y el botón aplicó el cambio correctamente (valor → 900,
      ícono ✏️ → 📍, fuente → "catálogo").

## Resultado

Cambio validado localmente y en producción: la regla de precedencia de
tarifa por ciudad funciona según lo diseñado (fuente manual se conserva,
fuente catálogo/defecto se actualiza, sugerencia obsoleta se limpia). La
suite completa de `bipv_python` no se pudo usar como baseline limpio en este
entorno de desarrollo por dependencias no instaladas (`streamlit`, `pandas`,
`python-docx`) — ninguno de los archivos modificados aparece entre los
errores/fallas preexistentes. La verificación manual en producción confirmó
el comportamiento diseñado en los tres escenarios del checklist.
