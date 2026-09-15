# Validación — Datos del proyecto

**Estado:** validado

## Checklist de validación del módulo

- [x] Tests nuevos (`test_tarifa_from_ciudad.py`, `test_clamp_factor_ocupacion.py`)
      pasan: 11/11.
- [x] `python3 -m py_compile` confirma sintaxis válida en `tarifa_utils.py` y
      `1_🏠_Proyecto.py`.
- [x] `test_invalidacion_ciudad.py` (test previo que también inspecciona
      `1_🏠_Proyecto.py`) sigue en verde sin cambios.
- [ ] Validación funcional en producción tras el despliegue (cambiar de
      ciudad con una tarifa editada manualmente y confirmar que aparece el
      aviso, no la sobreescritura).

## Resultado

Cambio validado localmente: la regla de precedencia de tarifa por ciudad
funciona según lo diseñado (fuente manual se conserva, fuente
catálogo/defecto se actualiza, sugerencia obsoleta se limpia). La suite
completa de `bipv_python` no se pudo usar como baseline limpio en este
entorno de desarrollo por dependencias no instaladas (`streamlit`, `pandas`,
`python-docx`) — ninguno de los archivos modificados aparece entre los
errores/fallas preexistentes. Queda pendiente la verificación funcional en
producción tras el despliegue, marcada como último ítem del checklist.
