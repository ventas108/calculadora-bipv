# Auditoría — commit local `c9858c2e`

**Fecha:** 2026-09-16
**Alcance:** auditoría de solo lectura del commit local ("Unificar cálculo POA y reforzar validación solar React"), antes de cualquier push. No se hizo push, no se desplegó.
**Historial de hash:** `7fe68949` (commit original) → `5972dad9` (primer `amend`, corrigió frases obsoletas del informe) → **`c9858c2e`** (segundo `amend`, conservó la sección que documentaba el cambio de hash anterior). Los tres son el mismo commit lógico, reescrito dos veces vía `git commit --amend --no-edit` — nunca hubo push de ninguna versión intermedia.

## Comandos ejecutados (segunda pasada, sobre `c9858c2e`)

```
git add CodeSpecs/02-recurso-solar/react/informe-implementacion-borrador.md
git commit --amend --no-edit
git show --stat --oneline HEAD
git diff-tree --no-commit-id --name-status -r HEAD
git status --short --branch
```

## Resultado

| # | Comprobación | Resultado | Evidencia | Observación / riesgo |
|---|---|---|---|---|
| 1 | Hash existe y mensaje correcto | ✅ Coincide | `git show --stat --oneline HEAD` → `c9858c2e Unificar cálculo POA y reforzar validación solar React` | Hash cambió respecto a la auditoría anterior (`5972dad9`), por el `amend` — esperado y solicitado. |
| 2 | Exactamente los 16 archivos autorizados | ✅ Coincide | `git diff-tree --name-status -r HEAD` → 16 líneas, misma lista exacta que en `5972dad9` (4 código + 5 tests + 7 docs) | Sin cambios de alcance respecto a la auditoría anterior. |
| 3 | No contiene `01-datos-proyecto/`, `00-director/`, `streamlit/`, `vision.md`, config/secretos | ✅ Coincide | Mismo listado de 16 archivos que en `5972dad9`, sin adiciones | — |
| 4 | Guarda de Perez para `GHI<=0` presente | ✅ Coincide | Sin cambios respecto a `5972dad9`: `const kd = globalHorizontalIrradiance > 0 ? ... : 0;` en `liuJordanModel.ts` | Este `amend` solo tocó `informe-implementacion-borrador.md`; el resto del contenido del commit es idéntico. |
| 5 | `Home.tsx` y `POAAnalyzer.tsx` llaman a `calculateMonthlyPOA()` | ✅ Coincide | Sin cambios respecto a `5972dad9` | — |
| 6 | Contrato `poaData` conservado | ✅ Coincide | Sin cambios respecto a `5972dad9` | — |
| 7 | `implementacion.md`/`validacion.md` corresponden al estado final | ✅ Coincide | `git show HEAD:.../implementacion.md` y `validacion.md` — contenido idéntico al verificado en la auditoría de `5972dad9` (no se tocaron en este `amend`) | Verificación funcional en producción sigue correctamente declarada como pendiente (`[ ]`) en `validacion.md`. |
| 8 | Working tree solo con archivos deliberadamente excluidos, sin residuos de los 16 | ✅ **Coincide (corregido)** | `git status --short --branch` → solo `CodeSpecs/00-director/*`, `CodeSpecs/01-datos-proyecto/propuesta.md`, `CodeSpecs/02-recurso-solar/{diseno,implementacion,problema,propuesta,tareas,validacion}.md` (nivel raíz, no `react/`), `CodeSpecs/02-recurso-solar/{streamlit/,vision.md}`, y dos archivos `??` propios de este proceso de auditoría (`auditoria-commit-5972dad9.md`, `exploracion-observacional.md`) — ninguno de los 16 archivos del commit aparece modificado | El bloqueo de la auditoría anterior quedó resuelto: la modificación de `+11/-1` sobre `informe-implementacion-borrador.md` ya está dentro del commit (`amend`), no como diff suelto. |

## Veredicto

**COMMIT c9858c2e APROBADO PARA PUSH, SIN DESPLIEGUE**

Las 8 comprobaciones coinciden. El commit conserva exactamente los 16 archivos autorizados, el alcance no incluye `01-datos-proyecto/`, `00-director/`, `streamlit/`, `vision.md` ni configuración/secretos, la guarda de Perez y el consumo de `calculateMonthlyPOA()` están presentes, el contrato `poaData` se conserva, `implementacion.md`/`validacion.md` reflejan el estado final, y el working tree ya no tiene residuos de los archivos comiteados. Sigue sin hacerse push ni despliegue — ambos quedan pendientes de tu instrucción explícita.
