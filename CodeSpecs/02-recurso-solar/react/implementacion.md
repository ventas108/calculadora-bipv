# Implementación — Recurso Solar (React)

**Estado:** implementado

## Cambios realizados

- Se extrajo `calculateMonthlyPOA()` a `client/src/lib/poaMonthly.ts` como única
	fuente de agregación mensual desde `EPWData`.
- `Home.tsx` y `POAAnalyzer.tsx` consumen la función compartida y conservan el
	contrato `poaData` (`month`, componentes POA, temperatura y viento).
- Se preservaron las ramas de Prospector/PVGIS, los reintentos PVGIS y los
	parámetros `tilt`, `azimuth`, `albedo` y `usePerez`.
- `calculatePOARadiationPerez()` ahora evita `NaN` cuando `GHI <= 0`, sin alterar
	el comportamiento para entradas con irradiancia válida.
- Se añadieron pruebas del modelo POA, parser EPW, agregación mensual y proxy
	PVGIS real. La prueba sintética existente fue renombrada para reflejar su
	alcance real.

## Archivos modificados

- `client/src/lib/poaMonthly.ts`
- `client/src/lib/liuJordanModel.ts`
- `client/src/pages/Home.tsx`
- `client/src/components/POAAnalyzer.tsx`
- `server/liuJordanModel.test.ts`
- `server/epwParser.test.ts`
- `server/poaMonthly.test.ts`
- `server/pvgisProxy.test.ts`
- `server/irradianceHeatmapSynthetic.test.ts`
