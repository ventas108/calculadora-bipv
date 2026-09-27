# Diseño — Parámetros de Financiero persistentes

**Estado:** validación

## Entradas

- `session_state`, el widget (`st.slider` o `st.number_input`), etiqueta,
  clave de datos, valor por defecto y rango.

## Salidas

- El valor del campo, que también queda en `session_state[clave]`.

## Tipos de datos

Números (`float`, o `int` para el horizonte): el dato se convierte al tipo del
valor por defecto.

## Errores posibles

- Dato guardado fuera de rango o no numérico: se recorta o se usa el valor por
  defecto (el campo nunca falla al dibujarse).

## Dependencias

`calculos/campos_editor.sincronizar_campo`; `proyectos_manager` (sin cambios:
las claves `fin_*` y `tarifa_excedentes_cop_kWh` ya se guardan; `_w_*` no).

## Criterios de aceptación

1. Tarifa de excedentes en 800 → otra página → vuelve a Financiero: 800.
2. Un proyecto guardado con 800 y WACC 12 % los muestra al cargarlo.
3. Los 10 parámetros usan `campo_persistente`; ninguno queda con `value=` fijo.
4. Sin dato guardado, cada campo muestra el mismo valor por defecto de antes
   (excedentes = tarifa de compra, sin descuento inventado).
