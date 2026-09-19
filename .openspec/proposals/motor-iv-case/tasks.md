# Tasks: Módulo 3 — Motor IV

## Goal

Protect and validate the Motor IV model and its auto-activation path before any implementation change is approved.

## Checklist

### Analysis
- [ ] Confirm the current repository state and branch status.
- [ ] Review the real IV engine entry points and data flow.
- [ ] Identify the modules involved in panel validation, calibration, and production IV mode.
- [ ] Confirm the shared/server boundary before changing UI behavior.

### Contract and model checks
- [ ] Review `bipv_python/calculos/modelo_iv.py` for the owner logic of the SDM behavior.
- [ ] Review `bipv_python/calculos/panel_iv_check.py` for completeness rules.
- [ ] Review `bipv_python/pages/3_🔬_Motor_IV.py` for UI behavior and warnings.
- [ ] Review `bipv_python/pages/4_📐_Dimensionamiento.py` for auto-activation and messaging.
- [ ] Review `bipv_python/calculos/produccion_iv.py` for downstream consumption of the same model.

### Regression and validation
- [ ] Identify the smallest relevant existing test covering IV calibration or validation.
- [ ] Add or update a test if a real regression is discovered.
- [ ] Run the focused validation command for the affected IV behavior.
- [ ] Run the smallest typecheck or project check required by the changed layer.

### Implementation if needed
- [ ] Apply the minimal fix in the owning calculation module.
- [ ] Keep UI changes secondary and only after logic validation.
- [ ] Preserve compatibility with current panel catalog assumptions.

### Documentation and closure
- [ ] Record the final reasoning and actual validation evidence.
- [ ] Capture remaining risks and any open follow-up items.
- [ ] Archive the proposal after implementation and validation.

## Reference evidence

- `bipv_python/calculos/modelo_iv.py`
- `bipv_python/calculos/produccion_iv.py`
- `bipv_python/pages/3_🔬_Motor_IV.py`
- `bipv_python/pages/4_📐_Dimensionamiento.py`
- `bipv_python/tests/test_modelo_iv.py`
- `bipv_python/tests/test_validacion_sdm_alarma.py`
- `DIAGNOSTICO_MOTOR_PVSYST.md`
