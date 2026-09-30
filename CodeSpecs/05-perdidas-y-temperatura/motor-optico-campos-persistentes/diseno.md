# Diseño — Motor Óptico: los campos no vuelven a su mínimo al cambiar de página

**Estado:** validación

## Entradas

- Datos `mo_noct`, `mo_coef_temp`, `mo_vidrio_sel`, `mo_b0_custom`,
  `mo_transparencia`, `mo_montaje`, `mo_soiling_custom`,
  `mo_k_soiling_vert`, `mo_f_iam_dif`.
- Respaldo: `motor_optico_noct`, `motor_optico_coef_temp`, ficha del panel.

## Salidas

- Widgets `_w_mo_*` sincronizados; los datos `mo_*` se actualizan con lo
  que escribe el usuario en cada ejecución.

## Tipos de datos

`float`, `int`, `str`, `bool`.

## Errores posibles

- Dato fuera del rango del campo: se recorta al rango.
- Opción de lista que ya no existe: se usa la de por defecto.

## Dependencias

`calculos/campos_editor.sincronizar_campo`, `calculos/motor_optico_ficha`.

## Criterios de aceptación

1. NOCT y γ escritos sobreviven al cambio de página (antes volvían a 35 y
   −0,70).
2. Un proyecto abierto muestra los valores guardados.
3. Sin dato, NOCT y γ toman el último cálculo (no el mínimo).
4. «Usar los de la ficha» actualiza campo y dato, y sobrevive al cambio de
   página.
5. Ningún campo de la página usa la clave del dato como widget.
6. El manual del Asistente lo explica (sección 99).
