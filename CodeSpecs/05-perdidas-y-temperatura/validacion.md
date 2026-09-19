# Validación — Pérdidas y temperatura

**Estado:** en validación

## Checklist de validación del módulo

- [x] Evidencia estática: Producción exige `poa_sin_termico_df` cuando Motor
	Óptico está activo y bloquea si falta.
- [x] Evidencia estática: el bypass y Producción reciben `k_BIPV` y calculan
	temperatura desde la misma fuente de verdad.
- [x] Evidencia estática: recalcular Motor Óptico invalida resultados downstream
	sin borrar multi-superficie independiente.
- [ ] Ejecutar pruebas focales con `pvlib` y `pytest` en un entorno compatible.
- [ ] Confirmar en la app que recalcular Motor Óptico exige volver a simular
	Producción antes de consumir resultados downstream.

## Resultado

Regularización retrospectiva documentada. El módulo no se cerrará hasta contar
con ejecución fresca de sus pruebas térmicas y validación funcional de la
invalidación en la app Streamlit.
