# Diseño — Pérdidas y temperatura

**Estado:** completado

## Entradas

- TMY y POA bruta de `02-recurso-solar`.
- Parámetros ópticos y térmicos: IAM, soiling, NOCT, `k_BIPV` y coeficiente de
	temperatura.
- Para bypass: sombra, panel y geometría eléctrica confirmada.

## Salidas

- `poa_efectiva_df`: cascada completa para visualización y resúmenes.
- `poa_sin_termico_df`: IAM + soiling, sin término térmico; única entrada
	válida al SDM de Producción y bypass con Motor Óptico activo.
- Resumen de pérdidas ópticas/térmicas y estado `motor_optico_ok`.
- Invalidación de resultados de Producción, bypass monofacial, Finanzas y CO₂
	al reemplazar la POA óptica.

## Unidades

- POA e irradiancia: `W/m²` por hora y `kWh/m²` anual; temperatura: `°C`;
	factores y pérdidas relativas: fracción o porcentaje.

## Tipos de datos

- Series horarias: `pandas.DataFrame`; resúmenes y configuraciones:
	diccionarios en `session_state`.

## Errores posibles

- `motor_optico_ok=True` sin `poa_sin_termico_df`: estado inconsistente; se
	bloquea Producción y se invalidan resultados de bypass relacionados.
- Usar `poa_efectiva_df` como entrada SDM: doble conteo térmico; prohibido por
	contrato.

## Dependencias

- Módulos previos: `02-recurso-solar`, `04-produccion-energia`
- Módulos dependientes: `06-analisis-financiero`

## Criterios de aceptación

- Motor Óptico activo entrega POA sin térmico y `k_BIPV` a Producción.
- Producción y bypass calculan `T_cell` con la misma fuente de verdad.
- Recalcular la cascada invalida resultados dependientes sin borrar estados
	multi-superficie que usan una POA independiente.

## Pruebas requeridas

- `test_mismatch_bypass_termico.py` protege la coherencia de `T_cell` y el
	doble conteo térmico.
- `test_seleccion_poa_bypass_pagina5.py` protege gates, invalidación y alcance
	de claves downstream.
