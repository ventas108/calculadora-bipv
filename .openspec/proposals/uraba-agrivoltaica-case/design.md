# Design: Caso concreto de granja agrivoltaica en Urabá

## Context

The project includes a real agrivoltaic farm case in Urabá with documented operating assumptions and an established path across project config, solar resource, dimensioning, optical behavior, production, financial estimation, and report generation.

The main design principle is that the project must preserve the distinction between:

- gross land area,
- usable/occupied area for solar panel layout,
- and the modeled production and financial outputs derived from that usable area.

## Objective

Document and protect the real Urabá agrivoltaic case so future changes do not regress the logic for land occupation, panel count, electrical configuration, or production assumptions.

## Design principles

1. Shared and server logic are the source of truth for calculation behavior.
2. UI only reflects validated underlying assumptions.
3. Agrivoltaic projects must not be treated like standard building facades.
4. Productive energy, area, and finance must remain internally consistent.
5. The change should be traceable through OpenSpec and verifiable with targeted validation.

## Affected system boundaries

### Shared layer

- `shared/shading-engine-contract.ts`: must not be violated.
- `shared/colombianRegions.ts`: must remain consistent with the regional assumptions used by the project.

### Server-side business logic

- sizing and layout calculations
- production model inputs and outputs
- input normalization for agrivoltaic mode
- any assumptions attached to region, irradiance, and temperature

### UI layer

- agrivoltaic-related selections and captions
- report sections that display calculation outcomes
- any form fields that map to the underlying job configuration

## Proposed technical approach

1. Keep the current agrivoltaic model intact.
2. Treat the Urabá case as a regression fixture for land occupation and production logic.
3. Ensure the occupation factor and usable area are mapped correctly before dimensioning.
4. Validate that output metrics remain consistent with the real case already documented in the repo.
5. Preserve the architecture boundary: no UI-only bug fix if the calculation path is wrong.

## Expected outputs

The solved case should remain capable of producing outputs consistent with:

- usable area driven by the occupation factor,
- correct number of panels, strings, and inverters,
- resource assumptions for Urabá,
- production and financial outputs tied to the real agrivoltaic scenario.

## Validation strategy

The design requires checks at the following layers:

- project input normalization
- solar/POA calculation assumptions
- dimensioning logic for panel count and string sizing
- production and financial outputs
- compatibility with the real Urabá dataset already described in the repo

## Risks and mitigations

### Risk: area logic drift

If the model uses gross land area instead of usable area, panel count and production will be inflated.

Mitigation:
- preserve the established `factor_ocupacion_pct` and `area_util_m2` logic
- validate the calculations with the Urabá agrivoltaic dataset

### Risk: UI misrepresentation

A UI-only tweak could hide real calculation drift.

Mitigation:
- validate shared and server logic first
- only then adjust display strings or report wording

### Risk: contract breakage

A change in shading or region assumptions could affect downstream simulation logic.

Mitigation:
- keep the contract stable
- run targeted validation around the affected modules
