# Diseño — Informes

**Estado:** completado

## Entradas

- Banderas de completitud: `recurso_solar_ok`, `motor_optico_ok`, `produccion_ok`,
  `financiero_ok`, `impacto_co2_ok`, `balance_ok`, `bypass_ok`, `multisup_activo`.
- Energía anual con prioridad fija: `E_ac_anual_kWh_multisup` >
  `E_ac_anual_kWh_bypass` > `E_ac_anual_kWh` (misma prioridad que usa Financiero).
- Resultados financieros y de CO₂ ya calculados en `session_state`
  (`comp_financiero`, `co2_anual_t`, etc.).
- Datos de proyecto/empresa para el encabezado del reporte (sin dependencia de otros módulos).

## Salidas

- Reporte HTML/PDF descargable con las secciones marcadas como completas.
- Eslabón opcional en el Ledger de Auditoría: hash de insumos+resultados en el
  momento de generación (`calculos/ledger_auditoria.py`).

## Unidades

- Energía: `kWh`; potencia: `kW`; CO₂: toneladas; moneda: USD/COP según sección.

## Tipos de datos

- Lectura directa de `session_state` (dict); sin estructuras propias de Informes.

## Errores posibles

- Sección marcada como incompleta (`_ok=False`): el reporte la omite u ofrece
  incluirla vacía, nunca inventa un valor.
- TRM no confirmada: bloquea la generación del reporte hasta confirmarla
  (guardia ya existente en `10_📄_Reporte_PDF.py`).

## Dependencias

- Módulos previos: `04-produccion-energia`, `05-perdidas-y-temperatura`, `06-analisis-financiero`
- Módulos dependientes: `08-interfaz`

## Criterios de aceptación

- Informes no introduce una vía propia de restauración de resultados
  persistidos; toda vigencia se garantiza en `04`/`06` antes de que estas
  claves lleguen a `session_state`.
- La prioridad de energía (`multisuperficie > bypass > base`) es idéntica a la
  que ya usa Financiero, sin una tercera implementación divergente.
- El sellado del Ledger de Auditoría captura el estado real al momento de
  generar el reporte, no un snapshot desincronizado.

## Pruebas requeridas

- Ninguna nueva identificada: no hay cambio de código en esta ronda. Si se
  encuentra evidencia de restauración propia en una página de Informes, esta
  Spec debe reabrirse con pruebas de vigencia equivalentes a las de `06`.


## Pruebas requeridas

- 
