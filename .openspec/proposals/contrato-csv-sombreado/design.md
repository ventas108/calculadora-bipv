# Design: Contrato del CSV de Factor de Sombreado entre apps hermanas

## Ownership

- **Fuente de verdad de la física:** Motor Solar Python (`bipv_python/calculos/sombras_3d.py`, `contrato_sombreado.py`, `scripts/run_shading_contract.py`).
- **Fuente de verdad del contrato de transporte JSON:** `bipv.shading.v1`, validado en paralelo por `contrato_sombreado.py` (Python) y `shared/shading-engine-contract.ts` (TypeScript).
- **Fuente de verdad del contrato de transporte CSV (derivado del JSON):** hasta ahora, implícita en `mismatch_bypass.py::cargar_csv_fs()` — este proceso la hace explícita en `CONTRATO_CSV_SOMBREADO_ENTRE_APPS.md`.

## Approach

1. No se toca la lógica de cálculo existente — este es un trabajo de **documentación y blindaje de contrato**, no de refactor.
2. El documento `CONTRATO_CSV_SOMBREADO_ENTRE_APPS.md` en la raíz del repo es el artefacto central, referenciado desde esta propuesta OpenSpec.
3. Pendiente abierto explícito: localizar en `client/` la transformación exacta que convierte el JSON oficial (`hour_utc`) al CSV descargable (hora local + promedio de 5 puntos). Esto no bloquea el uso del contrato ya documentado, pero sí queda como riesgo residual mientras no se aísle.
4. Si se decide agregar una columna/cabecera de versión explícita al CSV, debe implementarse primero en el lado productor (`client/` + Motor Python) y luego relajarse gradualmente la aceptación en el consumidor (`cargar_csv_fs`) para no romper CSVs ya exportados por usuarios existentes.

## Non-goals

- No se busca canalizar el CSV como reemplazo del contrato JSON `bipv.shading.v1` — el CSV sigue siendo una materialización derivada, no la fuente primaria.
- No se refactoriza `cargar_csv_fs()` en este proceso; solo se documenta su contrato real tal como existe hoy.
