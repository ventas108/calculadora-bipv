# Tareas — Recurso Solar (React)

**Estado:** aprobado

## Alcance de implementación

- [ ] Confirmar el contrato actual de `poaData` y localizar el código duplicado
	entre `Home.tsx` y `POAAnalyzer.tsx` sin cambiar todavía comportamiento.
- [ ] Extraer a `client/src/lib/` una función pura compartida para agregar el POA
	mensual desde `EPWData`, preservando campos, unidades, redondeos y parámetros.
- [ ] Sustituir las dos implementaciones duplicadas para que `Home.tsx` y
	`POAAnalyzer.tsx` consuman la función compartida.
- [ ] Mantener separadas las rutas `prospectorData`/PVGIS, IAM/soiling, `PR_T` y
	producción eléctrica; no incluirlas en esta implementación.

## Cobertura de pruebas

- [ ] Añadir pruebas unitarias para `calculateHourlyPOA()` y sus componentes,
	incluyendo irradiancia nula y Liu-Jordan/Perez.
- [ ] Añadir pruebas del parser EPW para cabecera, registros horarios y entradas
	inválidas o incompletas.
- [ ] Añadir prueba de contrato de la función mensual: 12 meses, campos completos,
	agregación de temperatura/viento y coherencia de componentes.
- [ ] Corregir el alcance/nombre de la prueba del proxy PVGIS para que pruebe
	`server/pvgisProxy.ts`; conservar cualquier cobertura útil de código sintético
	solo si se justifica por un consumidor real.

## Verificación

- [ ] Ejecutar tests Vitest relevantes, `pnpm check` y `pnpm build`.
- [ ] Comparar resultados antes/después con un EPW de referencia y confirmar que no
	cambia el contrato consumido por Producción y Reportes.
- [ ] Dejar `implementacion.md` y `validacion.md` pendientes hasta que Claude
	termine, el diff sea revisado y la verificación funcional sea ejecutada.
