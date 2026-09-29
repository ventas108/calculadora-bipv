# Propuesta — «Calidad del módulo» y «Mismatch» por separado

**Estado:** validación

## Objetivo

Poder escribir en la app las dos pérdidas de módulo de un informe de PVsyst y
verlas como dos filas en el Loss Diagram.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («si prepara la Spec para separar
calidad y mismatch»).

- Control nuevo «🏷️ Calidad del módulo (%)» en 🔀 Mismatch, de −2.0 a 5.0
  (negativo = ganancia), por defecto **0.0**: los proyectos existentes no
  cambian.
- El control actual pasa a llamarse «🔩 Mismatch módulos y strings (%)», con
  la misma clave (`pct_mismatch_fab`) y rango 0–4 %.
- Los dos motores reciben `pct_calidad_modulo` y lo aplican antes del
  mismatch: Pmax × (1 − calidad) × (1 − mismatch). Devuelven la pérdida de
  cada una por separado.
- Loss Diagram: fila «②c0 Calidad del módulo» y fila «②c Mismatch módulos y
  strings»; la fila informativa de PVsyst solo aparece si no se aplica
  ninguna de las dos.
- La calidad entra en la firma de vigencia de Producción (cambiarla invalida
  el resultado guardado), en la cadena multi-superficie y en los
  comparadores y 🤖 Análisis IA (pérdida combinada).
- Manual del Asistente con el caso Apartadó.

## Alternativas descartadas

- Subir el tope del control único a 6 %: sigue sin una fila por pérdida y no
  admite la calidad negativa de PVsyst.

## Fuera de alcance

- La cascada de 🔀 Mismatch (sección 4) sigue sin aplicar estas pérdidas
  (Producción las aplica directo, como hasta ahora).
