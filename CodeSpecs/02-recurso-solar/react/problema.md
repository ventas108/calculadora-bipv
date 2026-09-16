# Módulo 02 (React) — Recurso Solar

**Estado:** aprobado

## Alcance de la fase

App en producción `client/src` (`calculadora-bipv`, pm2): carga de EPW, cálculo
de irradiancia en el plano de la fachada (POA), zona horaria y las claves de
estado que expone a `03-dimensionamiento`/`04-produccion-energia`. No incluye
motor óptico (IAM/soiling) ni simulación de producción (E_ac, PR).

## Problema a resolver

El flujo de recurso solar tiene actualmente dos implementaciones independientes
del cálculo mensual de POA:

- `client/src/pages/Home.tsx`, cuyo `poaData` alimenta Producción y Reportes.
- `client/src/components/POAAnalyzer.tsx`, que recalcula el POA para los gráficos
	de la vista Análisis POA.

Ambas rutas llaman actualmente a `calculateHourlyPOA()` y reciben los mismos
parámetros compartidos de inclinación, azimut, albedo y modelo de transposición.
Sin embargo, la duplicación permite que una futura modificación de una ruta no se
refleje en la otra. En ese caso, el gráfico de Análisis POA podría mostrar valores
distintos de los que realmente consume Producción o el Reporte, sin que exista
una prueba automática que detecte la divergencia.

La confianza del módulo también está limitada por la falta de cobertura específica
para el motor físico de transposición (`liuJordanModel.ts`), el parser EPW
(`epwParser.ts`), la normalización de respuestas PVGIS (`pvgisApi.ts`) y el proxy
PVGIS real. Además, `server/pvgisProxy.test.ts` está mal delimitado: su contenido
prueba `irradianceHeatmap.ts`, una librería sintética que no utiliza el componente
real `IrradianceHeatmap.tsx`, y no valida el comportamiento del proxy.

## Contexto

La exploración observacional del 16-sep-2026 confirmó que el incidente de
`ECONNRESET` causado por ráfagas de peticiones PVGIS ya fue resuelto mediante
reintentos, backoff y pausas entre lotes, y fue verificado en producción. También
confirmó que el diagnóstico histórico sobre POA simplificado, orientación,
albedo, modelo Perez, viento y eficiencia del panel ya no describe el código
actual.

El problema vigente no es una falla observada en los valores actuales, sino una
brecha de arquitectura y verificación: el cálculo que constituye el contrato
del recurso solar está duplicado y carece de pruebas suficientes para proteger
su comportamiento físico y sus entradas climáticas.
