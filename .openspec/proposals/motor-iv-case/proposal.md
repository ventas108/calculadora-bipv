# Proposal: Módulo 3 — Motor IV

## Objective

Define and validate the real operating contract for the IV curve engine used by the BIPV calculator, preserving the single-diode model logic, the panel data validation path, and the automatic activation flow from Dimensionamiento into the IV diagnostic view.

## Current state

The project already has a mature IV engine and a real implementation path in the Python codebase:

- `bipv_python/calculos/modelo_iv.py` contains the SDM calibration and transfer logic for the panel model.
- `bipv_python/calculos/produccion_iv.py` reuses the same underlying electrical model for hourly production in IV mode.
- `bipv_python/pages/3_🔬_Motor_IV.py` is the technical UI for validation, calibration, and IV curve display.
- `bipv_python/pages/4_📐_Dimensionamiento.py` detects whether the selected panel has enough IV data to auto-enable the IV engine.
- The repo contains evidence of real fixes and validations around the IV model, including `DIAGNOSTICO_MOTOR_PVSYST.md` and related regression tests.

The core risk is not UI-only: the engine is part of the calculation path used by production, mismatch, and 3D/MPPT related views, and therefore it must be validated at the shared/server level before any UI adjustment.

## Affected modules

### Shared

- `shared/shading-engine-contract.ts`
- `shared/colombianRegions.ts`

### Server / calculation

- `bipv_python/calculos/modelo_iv.py`
- `bipv_python/calculos/produccion_iv.py`
- `bipv_python/calculos/panel_iv_check.py`
- `bipv_python/calculos/temperatura.py`
- `bipv_python/calculos/validador_panel.py`
- `bipv_python/calculos/produccion.py`
- `bipv_python/calculos/mismatch_bypass.py`

### Client / presentation

- `bipv_python/pages/3_🔬_Motor_IV.py`
- `bipv_python/pages/4_📐_Dimensionamiento.py`
- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`

### Tests and documentation

- `bipv_python/tests/test_modelo_iv.py`
- `bipv_python/tests/test_validacion_sdm_alarma.py`
- `DIAGNOSTICO_MOTOR_PVSYST.md`
- `bipv_python/datos/base_conocimiento_asistente.md`

## Constraints

- Preserve the current SDM / single-diode contract.
- Do not treat the UI as the source of truth for the IV engine.
- Respect the existing architecture boundary: shared and server first, UI last.
- Keep the calibration logic compatible with the current catalog and panel validation rules.
- Do not add dependencies unless there is a strong, explicit reason.

## Proposed change

Create a disciplined OpenSpec for the Motor IV module that documents:

1. the real calculation path from panel selection to IV curve and production result,
2. the validation rules for SDM completeness and physical consistency,
3. the auto-activation logic from Dimensionamiento,
4. the minimal regression tests needed before approving a fix,
5. the expected behavior for valid and invalid panel data.

## Expected behavior

The module should ensure that:

- a panel with valid IV data can be auto-activated from Dimensionamiento,
- incomplete or inconsistent data is rejected with explicit diagnostics,
- the estimated SDM remains consistent with the real panel datasheet within the accepted tolerances,
- the IV model used by Motor IV, production IV mode, mismatch, and combined MPPT logic remains aligned,
- any UI message reflects the real engine state and not a stale or misleading status.

## Validation path

Before considering the proposal approved, validate at least:

- the shared/server path for the IV model,
- the panel completeness and validation logic,
- the correlation between the technical IV page and the dimensioning screen,
- the focused tests around `modelo_iv.py` and the IV production path.

## Compatibility risks

- A UI-only patch can hide a real SDM calibration problem.
- An incorrect `N_s` or thermal parameter can make a valid panel fail IV activation.
- Different modules may reuse the same SDM but drift in how they interpret irradiance, temperature, or shunt behavior.

## Summary

This is a real calculation engine, not just a visualization page. The OpenSpec should protect the technical contract, the validation rules, and the regression path of the Motor IV module before the implementation is approved.
