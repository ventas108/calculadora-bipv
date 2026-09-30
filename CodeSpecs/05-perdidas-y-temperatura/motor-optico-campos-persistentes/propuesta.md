# Propuesta — Motor Óptico: los campos no vuelven a su mínimo al cambiar de página

**Estado:** validación

## Objetivo

Que ningún campo del Motor Óptico pierda su valor al cambiar de página,
recargar, guardar o abrir un proyecto.

## Alternativa recomendada

Aprobada por el usuario el 30-sep-2026 («solucionalo para que no vuelva a
suceder»).

- El dato vive en `mo_*` (no es clave de widget, se guarda con el
  proyecto) y el widget en `_w_mo_*`, sincronizados con
  `campos_editor.sincronizar_campo` (helper `_campo_mo` de la página).
- Sin dato (proyecto viejo o sesión nueva): NOCT y γ toman el último valor
  con que se calculó la cascada (`motor_optico_noct`,
  `motor_optico_coef_temp`) y si no, la ficha del panel; nunca el mínimo.
- El auto-llenado y «Usar los de la ficha» escriben el dato; el campo se
  actualiza solo.
- Prueba que impide volver a usar la clave del dato como widget en esta
  página; manual del Asistente, sección 99.

## Alternativas descartadas

- Poner `value=` en los widgets: Streamlit ignora `value` cuando la clave
  existe y avisa si ambos se usan; no resuelve el borrado.
- Rellenar desde la ficha al abrir el proyecto: borraría un valor medido que
  el usuario guardó a propósito.

## Fuera de alcance

- Otros campos con el mismo patrón en otras páginas (`N_str_tr` en
  Dimensionamiento, `bypass_n_series` en Mismatch, `produccion_usar_iv` en
  Producción): encontrados en la auditoría; van en una Spec propia.
