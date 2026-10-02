# Propuesta — Baja luz de CIGS con factor de forma bajo

**Estado:** validación

## Objetivo

Que cualquier ficha CIGS, o cualquier ficha con el dato de 200 W/m², quede en
el objetivo: 97 % por defecto o el valor de la ficha. Si no se puede, debe quedar
avisado. Y «Origen del modelo» debe salir siempre que el modelo sea estimado.

## Alternativa recomendada

- Buscar el factor de idealidad entre 0,75 y 2,2. R_s se re-ancla a la Pmax de
  la ficha, así que el STC se sigue reproduciendo.
- `_error_ajuste_200` cuando el resultado queda a más de 1 punto del objetivo.
- Llamar `_mostrar_origen_modelo` también desde el selector de 🔬 Motor IV.
- Guardar el panel del selector en la sesión (`motor_iv_panel_usado`) para que
  todas las acciones de la página lo sigan usando. Se descarta si cambia el
  panel de 📐 Dimensionamiento.

## Alternativas descartadas

- Cambiar cómo se interpreta N_s / NsA del catálogo para todas las tecnologías:
  mueve los resultados del silicio, que hoy están validados.
- Ajustar la resistencia en paralelo: en la Spec anterior solo movía el
  resultado entre 91 y 92 %.

## Fuera de alcance

- Paneles de silicio sin el dato de 200 W/m².
- SDM calibrados (ASP-ST1) y SDM manuales.
