# Tareas — Datos del proyecto

**Estado:** completado

- [ ] Añadir en `tarifa_utils.py` la verificación de `tarifa_fuente` antes de
      sobreescribir en `set_tarifa_from_ciudad()`: solo actualizar el valor si la
      fuente actual es `"catálogo"` o `"valor por defecto"`.
- [ ] Cuando la fuente sea manual (`"Proyecto"` o `"Financiero"`) y el usuario cambie
      de ciudad, mostrar un aviso en `1_🏠_Proyecto.py` indicando el valor de
      referencia de la nueva ciudad sin sobreescribir automáticamente, con opción
      explícita de actualizarlo.
- [ ] Escribir tests (`bipv_python/tests/`) que cubran: fuente manual se conserva al
      cambiar de ciudad; fuente catálogo sí se actualiza; recorte defensivo de
      `factor_ocupacion_pct` fuera de [5, 100].
- [ ] Ejecutar `pnpm check` y `pnpm build` (o el equivalente de tests Python del
      proyecto) como validación previa a `validacion.md`.
- [ ] Documentar en `implementacion.md` los archivos modificados y el resultado de
      las pruebas.
