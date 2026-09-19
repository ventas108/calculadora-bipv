# Contratos entre módulos

Cada módulo publica su contrato completo (entradas, salidas, unidades, tipos de datos,
errores posibles) en su propio `diseno.md`. Este archivo resume únicamente los
contratos **vigentes** (diseño aprobado) que otros módulos consumen.

## Formato de referencia

```text
Entrada:
- variable_1

Salida:
- variable_2

Unidades:
- ...
```

## Contratos publicados

### 01-datos-proyecto
_(pendiente — ver [../01-datos-proyecto/diseno.md](../01-datos-proyecto/diseno.md))_

### 02-recurso-solar
_(pendiente — ver [../02-recurso-solar/diseno.md](../02-recurso-solar/diseno.md))_

### 03-dimensionamiento

Entrada:
- Catálogo eléctrico, temperaturas de diseño, área y configuración de strings.

Salida:
- Diseño confirmado (`N_serie`, `N_strings_tracker`), compatibilidad y vigencia.

Regla de consumo:
- Los módulos downstream usan exclusivamente
	`diseno_electrico_confirmado(session_state)`. Un diseño no vigente no puede
	producir resultados persistibles.

### 04-produccion-energia

Entrada:
- Recurso solar, diseño eléctrico confirmado y, cuando aplique, POA sin térmico
	del Motor Óptico.

Salida:
- Energía AC/DC, PR, pérdidas, resultados persistidos y firma
	`produccion_run_signature_v1`.

Regla de consumo:
- Producción valida la vigencia reconstruyendo la firma en vivo desde su propia
	configuración visible. Consumidores que no tienen esos insumos en sesión
	(Finanzas/Presupuesto, ver `06-analisis-financiero`) no reconstruyen la firma:
	verifican la integridad del payload canónico persistido junto a ella. Sin esa
	verificación exitosa, ningún agregado de Producción se restaura.

### 05-perdidas-y-temperatura

Entrada:
- TMY/POA bruta y parámetros ópticos/térmicos.

Salida:
- `poa_sin_termico_df`, `poa_efectiva_df`, `k_BIPV`, resumen óptico y estado
	de vigencia.

Regla de consumo:
- Con Motor Óptico activo, Producción y bypass consumen solo
	`poa_sin_termico_df`; el término térmico se calcula una única vez dentro del
	SDM. Recalcular la cascada invalida resultados dependientes de su POA.

### 06-analisis-financiero

Entrada:
- Resultados persistidos de Producción (`04-produccion-energia`): agregados
	(`E_ac_anual_kWh`, `P_stc_kW_sistema`, etc.), `produccion_run_signature_v1` y
	su payload canónico (`payload_firma`).

Salida:
- Agregados restaurados en `session_state` de Finanzas/Presupuesto, solo
	cuando el payload persistido verifica contra la firma persistida.

Regla de consumo:
- Finanzas y Presupuesto nunca reconstruyen la firma en vivo (no cargan
	panel/inversor/TMY/POA). Restauran únicamente si
	`firma_desde_payload(payload_persistido) == firma_persistida`; payload
	ausente (legacy) o alterado nunca restaura.

### 07-informes

Entrada:
- Banderas `_ok` (`produccion_ok`, `financiero_ok`, `impacto_co2_ok`, etc.) y
	energía anual con prioridad `multisuperficie > bypass > base`.

Salida:
- Reporte HTML/PDF descargable y, opcionalmente, un eslabón en el Ledger de
	Auditoría con hash de insumos+resultados al momento de generación.

Regla de consumo:
- Informes no restaura resultados persistidos por su cuenta; toda vigencia se
	garantiza aguas arriba, en `04-produccion-energia` y `06-analisis-financiero`.

### 08-interfaz

Entrada:
- `session_state` ya poblado por módulos previos; sesión autenticada.

Salida:
- Bloqueo de traducción del navegador y banner de proyecto activo.

Regla de consumo:
- Interfaz no restaura ni invalida datos por su cuenta; toda vigencia se
	garantiza en `03`–`06` antes de que estas claves lleguen a `session_state`.
	Cualquier texto de usuario interpolado en HTML debe quedar escapado.

### 09-despliegue
_(pendiente — ver [../09-despliegue/diseno.md](../09-despliegue/diseno.md))_
