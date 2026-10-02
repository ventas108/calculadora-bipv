# Implementación — Coherencia del Reporte

**Estado:** validación

## Cambios realizados

- `calculos/coherencia_reporte.py`: `energia_vigente` y
  `revisar_coherencia_reporte`.
- 📄 Reporte:
  - revisión antes de «Generar»;
  - casilla `rep_generar_incoherente`;
  - etiqueta «POA PVGIS — cara frontal»;
  - sujeto del texto de CO₂ según `tipo_instalacion`.
- 🌿 Impacto CO₂: `co2_e_ac_kWh` y `co2_e_ac_manual`.
- 💰 Financiero: `fin_e_ac_kWh` y `fin_e_ac_manual`.
- ☀️ Recurso Solar: `poa_pvgis_frontal_mensual` (suma mensual de `poa_front`
  con el modelo bifacial) y `solo_cara_frontal` en la comparación.

## Archivos modificados

- `bipv_python/calculos/coherencia_reporte.py`
- `bipv_python/pages/10_📄_Reporte_PDF.py`
- `bipv_python/pages/12_🌿_Impacto_CO2.py`
- `bipv_python/pages/7_💰_Financiero.py`
- `bipv_python/pages/2_☀️_Recurso_Solar.py`
- `bipv_python/tests/test_coherencia_reporte.py`
- `bipv_python/datos/base_conocimiento_asistente.md` (sección 118)
- `CodeSpecs/00-director/registro-de-decisiones.md`
