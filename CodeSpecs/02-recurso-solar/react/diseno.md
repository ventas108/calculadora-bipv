# Diseño — Recurso Solar (React)

**Estado:** aprobado

## Entradas

- `EPWData` validado por `solarRigor.ts`, con ubicación y registros horarios de
	temperatura, viento, DNI, DHI y GHI.
- `tilt` e `azimuth` de la superficie, en grados.
- `albedo`, como fracción adimensional.
- `usePerez`, selector del modelo de transposición; `false` conserva Liu-Jordan.
- Para la ruta Prospector/PVGIS: `prospectorData` queda explícitamente fuera del
	cálculo físico compartido de EPW y conserva su comportamiento de estimación
	rápida hasta que se asigne a otra Spec.

## Salidas

- Función pura compartida de cálculo mensual que devuelve un arreglo de 12
	registros `poaData` con `month`, `directPOA`, `diffusePOA`, `reflectedPOA`,
	`totalPOA`, `avgTemp` y `avgWindSpeed`.
- `solarRigorReport`, producido por el gate existente, con `canCalculate` y los
	diagnósticos de calidad de la entrada.
- `weatherData.location` sin transformación, incluyendo latitud, longitud,
	elevación y zona horaria.
- Los parámetros físicos compartidos (`tilt`, `azimuth`, `albedo`, `usePerez`)
	permanecen sincronizados entre Home y `POAAnalyzer`.

## Unidades

- Irradiancia y POA: W/m² en promedios horarios/mensuales.
- Energía acumulada cuando se derive fuera de esta función: Wh/m² o kWh/m²,
	según el contrato existente del consumidor.
- Temperatura: °C. Viento: m/s.
- Área y coordenadas: no se recalculan aquí; coordenadas en grados decimales y
	elevación en metros.
- Ángulos: grados de entrada; radianes solo internamente al modelo físico.
- Albedo: fracción entre 0 y 1.

## Tipos de datos

- La entrada climática es `EPWData` de `client/src/lib/epwParser.ts`.
- La salida mensual debe conservar el tipo estructural que ya consumen
	`EnergyProductionSimulator` y `ReportGenerator`.
- El cálculo compartido debe ser una función pura: sin React state, efectos,
	fetch, mutaciones de objetos de entrada ni dependencias del DOM.
- `calculateHourlyPOA()` continúa siendo la unidad física horaria; la nueva
	función solo orquesta el agrupamiento mensual y la agregación de sus
	componentes.

## Errores posibles

- Entrada EPW inválida, incompleta o rechazada por `solarRigorReport`: no se
	calcula POA y se conserva `canCalculate = false`.
- Registros con irradiancia nocturna o valores no válidos: se excluyen del
	acumulado solar, pero las horas válidas del mes siguen determinando temperatura
	y viento según el comportamiento actual.
- Parámetros físicos fuera de rango: deben seguir siendo rechazados o advertidos
	por los controles/gate existentes; la función compartida no debe corregirlos
	silenciosamente.
- Respuesta PVGIS no válida o error de red: pertenece al proxy/cliente PVGIS y
	debe producir un error manejable; no puede contaminar el cálculo EPW.
- No se considera error el `ECONNRESET` histórico ya resuelto; cualquier regresión
	deberá demostrarse con logs o una prueba reproducible.

## Dependencias

- Módulos previos: `01-datos-proyecto`
- Módulos dependientes: `03-dimensionamiento`, `04-produccion-energia`

## Criterios de aceptación

- `Home.tsx` y `POAAnalyzer.tsx` consumen una única función compartida para la
	ruta EPW, sin duplicar el bucle mensual de cálculo POA.
- Para el mismo `EPWData`, `tilt`, `azimuth`, `albedo` y `usePerez`, la salida
	mensual compartida conserva los campos y valores esperados por Producción,
	Reportes y la vista Análisis POA.
- `directPOA + diffusePOA + reflectedPOA` es coherente con `totalPOA` dentro de
	la tolerancia numérica definida por el modelo y el redondeo de presentación.
- El promedio de `avgWindSpeed` usa los datos del EPW y no introduce un valor
	fijo en la ruta activa.
- Los parámetros de orientación y transposición continúan sincronizados entre
	la vista Análisis POA y los consumidores aguas abajo.
- La corrección no modifica el proxy PVGIS, los reintentos existentes, IAM/soiling,
	PR_T ni la ruta Prospector sin una decisión SDD independiente.

## Pruebas requeridas

- Pruebas unitarias de invariantes y casos límite de `calculateHourlyPOA()` para
	irradiancia nula, componentes y modelos Liu-Jordan/Perez.
- Pruebas del parser EPW con cabecera válida, registros horarios y entradas
	inválidas/incompletas.
- Prueba de contrato de la función mensual compartida: 12 meses, campos completos,
	unidades y agregación de viento/temperatura.
- Prueba de regresión que garantice que Home y `POAAnalyzer` consumen la misma
	función, no dos implementaciones equivalentes duplicadas.
- Pruebas del proxy/normalizador PVGIS en archivos correctamente nombrados, sin
	confundir la librería sintética `irradianceHeatmap.ts` con el componente real.
- `pnpm check`, `pnpm build` y la suite Vitest relevante antes de implementación
	y nuevamente después del cambio.
