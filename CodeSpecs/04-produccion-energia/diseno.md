# Diseño — Producción de energía

**Estado:** completado

## Entradas

- TMY y POA del módulo `02-recurso-solar`.
- Panel, número de módulos, potencia DC e inversor del diseño confirmado de
	`03-dimensionamiento`.
- Temperaturas de diseño, eficiencia de inversor y factores eléctricos.
- Opcionalmente, POA sin térmico y resumen de `05-perdidas-y-temperatura`
	cuando el Motor Óptico está vigente.

## Salidas

- Energía DC/AC anual, horaria y mensual.
- `PR`, yields IEC 61724, factor de capacidad y pérdidas por temperatura,
  inversor, clipping, mismatch y cableado.
- Estado persistido: `res_produccion`, `E_ac_anual_kWh`, `PR_sistema`,
  `produccion_ok` y modo de simulación.

## Unidades

- Energía: `kWh`; potencia: `W` y `kW`; irradiancia: `W/m²`; POA: `kWh/m²`;
	temperatura: `°C`; pérdidas y PR: fracción o porcentaje según el campo.

## Tipos de datos

- TMY/POA y resultados horarios/mensuales: `pandas.DataFrame`.
- Configuración y resultados anuales: diccionarios serializables en
	`session_state`.

## Errores posibles

- TMY, POA o ficha del inversor ausentes: la simulación no se certifica.
- Diseño eléctrico incompatible o vencido: se bloquea la simulación y se
	invalidan sus resultados persistidos.
- Motor Óptico marcado vigente sin `poa_sin_termico_df`: se bloquea para evitar
	doble conteo o pérdida de correcciones ópticas.

## Dependencias

- Módulos previos: `02-recurso-solar`, `03-dimensionamiento`
- Módulos dependientes: `05-perdidas-y-temperatura`, `06-analisis-financiero`

## Criterios de aceptación

- Producción consume exclusivamente el diseño confirmado de `03` y no simula
	si su vigencia es falsa.
- La salida AC respeta la eficiencia y el límite nominal del inversor.
- `PR` referencia la POA bruta real cuando está disponible y las pérdidas se
	mantienen reconciliables con el resultado horario.
- Finanzas e Informes pueden consumir las claves históricas sin conocer la
	implementación interna del motor.

## Pruebas requeridas

- Gate de diseño vencido e incompatibilidad eléctrica.
- Conservación de energía, clipping y pérdidas óhmicas en el motor anual.
- Integración con POA/Motor Óptico y persistencia para consumidores downstream.
