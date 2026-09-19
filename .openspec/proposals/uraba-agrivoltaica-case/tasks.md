# Tasks: caso concreto de granja agrivoltaica en Urabá

## Goal

Protect and validate the existing agrivoltaic Urabá real-world scenario through a disciplined OpenSpec workflow.

## Checklist

### Analysis
- [ ] Confirm the current project state and branch status.
- [ ] Review the agrivoltaic logic in the relevant project pages and docs.
- [ ] Identify the real calculation path crossing shared, server, and UI layers.

### Contract and model checks
- [ ] Verify the shading contract and regional assumptions remain intact.
- [ ] Validate the land occupation model and usable area logic.
- [ ] Confirm that production and financial outputs still align with the documented Urabá case.

### Implementation if needed
- [ ] Apply a minimal fix only if the issue is real and supported by evidence.
- [ ] Avoid broad refactors or UI-only changes when logic is affected.
- [ ] Maintain architecture compatibility and existing data contracts.

### Validation
- [ ] Run the small relevant validation command(s).
- [ ] Check the affected shared/server calculation path.
- [ ] Confirm any display/UI changes reflect the validated model.

### Documentation
- [ ] Keep the proposal, design, and task notes synced with the actual implementation.
- [ ] Record final validation notes and any remaining risk.

## Reference evidence

- `informe_granja_fv_uraba_2026.md`
- `.agents/memory/bipv-agrivoltaica.md`
- `DIAGNOSTICO_NSERIE_URABA_TEMPERATURA_REAL.md`
- `DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md`
