# Validación — Recurso Solar (React)

**Estado:** validado

## Checklist de validación del módulo

- [x] Tests focalizados: `43/43` pasaron (`liuJordanModel`, `poaMonthly`,
	`pvgisProxy` y `epwParser`).
- [x] Suite completa: `850 passed`, con 2 fallos preexistentes no relacionados
	(`NREL_API_KEY` ausente y `sddAgent`).
- [x] `pnpm check` sin errores.
- [x] `pnpm build` exitoso, sin warnings nuevos.
- [x] Contrato de `poaData` preservado; comparación byte a byte de `Home.tsx`
	idéntica en 4 combinaciones de parámetros con un EPW sintético de 8760
	horas.
- [x] Corrección funcional verificada: Perez con `GHI<=0` devuelve resultados
	finitos y `POAAnalyzer` ya no produce `NaN` en modo Perez.
- [ ] Verificación funcional en producción tras desplegar este cambio.

## Resultado

Validación local completada. La implementación queda lista para commit, pero el
último ítem requiere despliegue y prueba funcional en producción: cargar un EPW,
activar Perez y confirmar que la vista Análisis POA muestra valores numéricos y
que Producción/Reporte conservan sus resultados esperados. IAM/soiling, PR_T,
Prospector y Streamlit no forman parte de esta validación.
