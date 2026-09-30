# Diseño — Motor Óptico: NOCT y γ coherentes con la ficha del panel

**Estado:** validación

## Entradas

- `mo_noct` (°C), `mo_coef_temp` (%/°C), `mo_montaje` (k) del Motor Óptico.
- `motor_optico_noct`, `motor_optico_coef_temp` (decimal) en Producción.
- Ficha del panel: `NOCT`, `Tk_gamma` / `gamma_mp` / `beta_mp`.

## Salidas

- `ficha_termica(panel) -> {"noct", "gamma_pct"}` (None si falta o es 0).
- `diferencias_ficha(noct, gamma_pct, panel) -> list[{campo, motor, ficha,
  afecta_energia}]`.
- `texto_aviso_ficha(diferencias, panel_nombre, k_bipv) -> str` ("" sin
  diferencias).

## Tipos de datos

`dict`, `list`, `float | None`, `str`.

## Errores posibles

- Ficha sin NOCT o sin γ: no se compara ese campo (sin aviso).
- Valor de la ficha fuera del rango del campo: el botón lo lleva al límite.

## Dependencias

`pages/5b_🔆_Motor_Optico.py`, `pages/6_📊_Produccion.py`.

## Criterios de aceptación

1. Apartadó (35 °C, −0,70 frente a 45 °C, −0,29): se detectan los dos; el
   NOCT marcado como que afecta la energía.
2. Iguales o dentro de la tolerancia: sin aviso.
3. El aviso dice cuántos grados cambia la celda (12,5 °C más fría con k 1,0).
4. Motor Óptico: aviso 🟠 y botón; el botón deja 45 °C y −0,29 y el aviso
   desaparece.
5. Producción: el aviso aparece antes de simular con 35 °C y no con 45 °C.
6. El auto-llenado usa la misma lectura de la ficha.
7. El manual del Asistente lo explica con el caso Apartadó.
