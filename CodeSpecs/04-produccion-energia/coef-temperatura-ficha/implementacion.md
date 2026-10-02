# Implementación — Coeficientes de temperatura de la ficha en el modelo IV

**Estado:** validación

## Cambios realizados

- `_voc_pvsyst_a_T` y `_coeficientes_temperatura_modelo`.
- Paso final en `estimar_sdm_desde_ficha`:
  - secante en Eg desde la nominal (2 a 4 ajustes, límites ±0,4 eV); si β ya
    está a ±0,003 de la ficha no se re-ajusta (0,25 s por panel, antes 0,12 s);
  - mu_gamma re-ajustado a γ en cada Eg.
- `EgRef` en el resolutor común.
- `_rs_min = 0,01 · Vmp/Imp` en el ajuste de baja luz. La teja ya no
  sigue su curva con ±1,5 sino con ±2 puntos a 500 W/m²; se actualizó la
  prueba de la Spec `04/curva-baja-irradiancia-ficha`.
- 🔬 Motor IV: líneas de temperatura en «Origen del modelo».

Resultados (resolutor común):

| Panel | β ficha | β antes | β ahora | γ ficha | γ ahora |
|---|---|---|---|---|---|
| JA Solar 730 W | −0,25 | −0,255 | −0,255 (dentro de ±0,005) | −0,29 | −0,290 |
| LR6-60HIBD 305 | −0,267 | −0,289 | −0,267 | −0,338 | −0,338 |
| EINNOVA ESM-550T | −0,26 | −0,752 | −0,259 | −0,36 | −0,359 (antes −0,88) |
| Teja Hanergy 32 W | −0,36 | −0,248 | −0,299 ⚠️ | −0,40 | −0,400 |
| FLEX-03 70N | −0,28 | −0,195 | −0,255 | −0,38 | −0,380 |
| ASP-LAM3-T0 (CdTe) | −0,321 | −0,101 | −0,101 ⚠️ | −0,214 | −0,213 |

## Archivos modificados

- `bipv_python/calculos/modelo_iv.py`
- `bipv_python/pages/3_🔬_Motor_IV.py`
- `bipv_python/tests/test_coef_temperatura_ficha.py`
- `bipv_python/tests/test_consistencia_sdm_entre_modulos.py`
- `bipv_python/tests/test_curva_baja_irradiancia.py`
- `bipv_python/datos/base_conocimiento_asistente.md` (sección 115)
- `CodeSpecs/04-produccion-energia/curva-baja-irradiancia-ficha/diseno.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
