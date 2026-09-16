# Propuesta — Recurso Solar (React)

**Estado:** aprobado

## Objetivo

Establecer un único cálculo de referencia para el POA mensual de la aplicación
React y proteger su contrato con pruebas automatizadas. La vista Análisis POA,
Producción y Reportes deben consumir resultados generados por la misma función,
con los mismos datos EPW y parámetros de orientación, albedo y modelo de
transposición.

La propuesta también debe cubrir con pruebas mínimas el parsing de EPW, el modelo
Liu-Jordan/Perez, la normalización de respuestas PVGIS y el proxy PVGIS real.
La corrección debe conservar los reintentos y la pausa entre lotes que resolvieron
el incidente `ECONNRESET` en producción.

## Alternativas consideradas

1. **Mantener las dos implementaciones y añadir únicamente tests de comparación.**
	Detectaría una divergencia después de que ocurra, pero mantendría dos fuentes
	de verdad y permitiría que el problema reaparezca en futuras modificaciones.

2. **Mover todo el cálculo al componente `POAAnalyzer.tsx`.** Reduciría la
	duplicación en la interfaz, pero convertiría un componente visual en dueño de
	un contrato consumido por Producción y Reportes, aumentando el acoplamiento.

3. **Extraer el cálculo mensual de POA a una función pura compartida en
	`client/src/lib/`.** `Home.tsx` y `POAAnalyzer.tsx` consumirían esa función,
	que recibiría `EPWData` y los parámetros físicos necesarios y devolvería el
	contrato mensual `poaData`. La función quedaría cubierta por pruebas físicas y
	de invariantes; el proxy y el parser tendrían pruebas separadas.

4. **Reescribir simultáneamente todo el flujo climático, incluido PVGIS y el
	Prospector.** Podría homogeneizar más componentes, pero mezcla adquisición
	climática, estimación rápida y producción en una sola modificación de alto
	riesgo. Además, el incidente PVGIS ya está resuelto y no requiere reabrirse.

## Alternativa recomendada

La alternativa 3, en una secuencia incremental:

1. Definir el contrato de la función pura compartida para el cálculo mensual de
	POA, preservando los campos actuales: `month`, `directPOA`, `diffusePOA`,
	`reflectedPOA`, `totalPOA`, `avgTemp` y `avgWindSpeed`.
2. Extraer la lógica actualmente duplicada sin cambiar las fórmulas de
	`calculateHourlyPOA()`, los parámetros ni las unidades.
3. Hacer que `Home.tsx` y `POAAnalyzer.tsx` consuman la función compartida y
	eliminar el cálculo duplicado de ambos componentes.
4. Añadir pruebas para invariantes del modelo, parsing de EPW y normalización de
	respuestas PVGIS. Renombrar o sustituir el test que hoy no prueba el proxy,
	sin borrar cobertura útil sin verificar antes su única referencia.
5. Mantener fuera de esta Spec IAM/soiling, PR_T, producción eléctrica y la ruta
	de estimación rápida del Prospector.

La implementación debe ser compatible con el contrato que ya consume
`EnergyProductionSimulator`, `ReportGenerator` y el estado compartido de
orientación. Cualquier cambio de contrato o de resultados numéricos debe quedar
bloqueado para revisión humana antes de continuar a `diseno.md`.
