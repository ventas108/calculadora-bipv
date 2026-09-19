# Proposal: Caso concreto de granja agrivoltaica en Urabá

## Objective

Define and validate the engineering assumptions for the agrivoltaic farm case in Urabá, ensuring the calculation pipeline uses the correct land occupation logic, solar assumptions, electrical sizing, and financial interpretation without breaking the existing architecture.

## Current state

The repository already contains a real agrivoltaic/Urabá case with documented evidence in:

- `informe_granja_fv_uraba_2026.md`
- `DIAGNOSTICO_NSERIE_URABA_TEMPERATURA_REAL.md`
- `DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md`
- `.agents/memory/bipv-agrivoltaica.md`

The working logic already recognizes the special treatment for "Granja fotovoltaica" and the occupation factor logic (`factor_ocupacion_pct` and `area_util_m2`). The project has a real calibration path involving layout, resource solar, dimensioning, and production assumptions.

## Affected modules

The relevant calculation pipeline spans several modules and must be reviewed together instead of in isolation:

- `bipv_python/pages/1_🏠_Proyecto.py`
- `bipv_python/pages/2_☀️_Recurso_Solar.py`
- `bipv_python/pages/4_📐_Dimensionamiento.py`
- `bipv_python/pages/5b_🔆_Motor_Optico.py`
- `bipv_python/pages/6_📊_Produccion.py`
- `bipv_python/pages/7_💰_Financiero.py`
- `bipv_python/pages/8_💼_Presupuesto.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/calculos/produccion.py`
- `bipv_python/calculos/dimensionamiento.py`
- `bipv_python/calculos/solar.py`
- `bipv_python/simulation/bipv_simulator.py`
- `shared/shading-engine-contract.ts`
- `shared/colombianRegions.ts`

## Constraints

- Keep the calculation model architecture intact.
- Do not break the existing shading contract.
- Do not treat the frontend as the source of truth for calculation logic.
- Preserve the distinction between net usable area and gross land area in agrivoltaic projects.
- Keep the gridded and regional assumptions aligned with Colombia and Urabá-specific operating conditions.
- Do not add dependencies unless strictly required.

## Proposed change

Create a concrete OpenSpec for the agrivoltaic Urabá use case that documents:

1. the real project assumptions,
2. the affected calculation path,
3. the compatibility constraints,
4. the minimum validation checks required before merge,
5. the expected outputs for land occupation, sizing, production, and financial estimation.

## Expected behavior

The case should preserve the current logic that:

- agrivoltaic projects use usable area rather than gross land area for panel count and throughput calculations,
- crop/land occupation is represented by a factor that is not confused with gross site area,
- production and design remain consistent with the real Urabá scenario,
- any UI presentation must reflect the underlying shared/server model rather than contradict it.

## Validation path

Before considering the case complete, validate at least:

- the shared contract and any data model involved in project area/occupation,
- the server-side sizing and production logic,
- the UI mapping for agrivoltaic mode where relevant,
- the project’s existing focused tests or direct simulation checks related to Urabá.

## Compatibility risks

- Incorrectly treating land area as usable area could overcount panels and production.
- Mismatch between solar assumptions and land occupation logic could distort the financial model.
- UI-only adjustments without validating the shared/server calculation pipeline could conceal real calculation drift.

## Summary

This is a concrete real-world case that already exists in the project history. The OpenSpec should document the proven assumptions and the exact validation path needed to preserve the current working behavior while allowing disciplined improvements.
