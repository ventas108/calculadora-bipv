# Design: Módulo 3 — Motor IV

## Context

The Motor IV module is the electrical model that validates and simulates the I-V curve of a photovoltaic panel using a single-diode model. It is not a cosmetic feature. The module is involved in technical validation, hourly production, mismatch/bypass logic, and combined MPPT/3D logic.

This design keeps the current architecture intact while clarifying the ownership and validation path of the IV engine.

## Objective

Ensure that the IV engine remains the single source of truth for panel electrical behavior in the BIPV workflow, while keeping the auto-activation logic and validation diagnostics aligned with the catalog data and the technical model.

## Design principles

1. Shared/server logic is authoritative; UI only reflects it.
2. The IV model must be compatible with the real datasheet values and with the existing production engine.
3. Panel-level validation must happen before trusting any forward calculation.
4. Changes must be minimal, traceable, and testable.
5. The module must not silently accept inconsistent data.

## Affected system boundaries

### Shared layer

- `shared/shading-engine-contract.ts`: unchanged unless a real contract issue is proven.
- `shared/colombianRegions.ts`: only relevant if region logic affects the panel/production context; otherwise out of scope.

### Server-side business logic

- `bipv_python/calculos/modelo_iv.py`: owns the SDM calibration and transfer logic.
- `bipv_python/calculos/produccion_iv.py`: consumes the same calibrated model in IV production mode.
- `bipv_python/calculos/panel_iv_check.py`: validates whether a panel has enough data for IV simulation.
- `bipv_python/calculos/validador_panel.py`: strong panel-level validation and consistency checks.

### UI layer

- `bipv_python/pages/3_🔬_Motor_IV.py`: technical visualization and validation view.
- `bipv_python/pages/4_📐_Dimensionamiento.py`: auto-activation and warnings.
- `bipv_python/pages/6_📊_Produccion.py`: exposure of the IV mode for production.

## Proposed technical approach

1. Treat `modelo_iv.py` as the owner of the electrical behavior and the calibration contract.
2. Keep the current pattern of auto-detecting panel completeness in Dimensionamiento and letting Motor IV estimate the SDM when needed.
3. Preserve the distinction between:
   - a panel with complete SDM calibration,
   - a panel with raw datasheet data that can be estimated,
   - and a panel that is not valid for IV mode.
4. Keep the validation tolerance and explanatory diagnostics aligned with the real project logic.
5. If a change is needed, implement it in the calculation path first and validate it with targeted tests before adjusting UI messaging.

## Expected outputs

The Motor IV module should continue to support:

- SDM completeness validation,
- auto-activation from Dimensionamiento,
- explicit warnings for half-cut or physically inconsistent `N_s`,
- IV curve generation and model validation against datasheet values,
- consistent behavior in production IV mode and downstream mismatch/MPPT-related calculations.

## Validation strategy

The design requires checks in three layers:

- panel completeness and physical plausibility checks,
- calibration logic in `modelo_iv.py` and related production code,
- UI status and messaging in the relevant pages.

## Risks and mitigations

### Risk: silent calibration drift
If the model is modified without checking the panel data lifecycle, the IV engine may silently produce unrealistic Pmax/Vmp/Imp.

Mitigation:
- preserve the existing validation routines,
- add or update a focused regression test,
- validate against known panel examples before approving the patch.

### Risk: false activation
A panel may appear valid because it has enough fields, but still be physically inconsistent.

Mitigation:
- require plausibility checks, not only field presence,
- use the technical diagnostics already present in the code.

### Risk: UI mismatch
The UI may show a valid or invalid status that does not match the real engine state.

Mitigation:
- keep the UI reading from the same validation state used in the engine,
- confirm the message and state match before finalizing.
