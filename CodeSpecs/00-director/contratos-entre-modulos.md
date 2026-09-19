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
- La infraestructura compartida de Interfaz no restaura ni invalida datos por su
	cuenta; toda vigencia se garantiza en `03`–`06` antes de que estas claves lleguen
	a `session_state`. Son excepción los comandos explícitos de adopción definidos en
	el contrato transversal de comparadores: mutan el proyecto y ejecutan la
	invalidación central correspondiente como una sola operación.
- Cualquier texto de usuario interpolado en HTML debe quedar escapado.

### Contrato transversal — comparadores Streamlit

Este contrato pertenece exclusivamente a la app hermana Streamlit. Los comparadores
son superficies de decisión de `08-interfaz` que consumen contratos de `02`–`06`; no
son motores físicos alternativos ni autorizan duplicar fórmulas en la app React.

#### Comparador de inversores

Entrada:
- Diseño eléctrico confirmado, panel vigente y serie horaria de Producción previa al
  límite AC del inversor actualmente seleccionado (`P_ac_sin_recorte_kW`).

Salida:
- Compatibilidad eléctrica, energía con el límite propio de cada candidato, clipping
  e indicadores económicos comparables.

Invariantes:
- Cada candidato aplica su propio límite a la serie previa al recorte. La serie ya
	recortada nunca se usa para reconstruir potencia perdida.
- Un resultado legacy sin la serie previa al recorte bloquea la comparación y exige
	volver a ejecutar Producción.
- Como regla física, cambiar de inversor no cambia la POA. La implementación actual
	conserva la POA solar base y `poa_efectiva_df`, pero todavía invalida parte del
	estado óptico; se aplica la desviación activa documentada más abajo. Producción,
	Financiero, CO₂ y demás resultados dependientes del inversor sí deben invalidarse.

#### Comparador de paneles

Entrada:
- Recurso solar vigente, diseño base e inversor configurado; cada candidato se evalúa
  con el motor común de simulación y con la ficha exacta del catálogo unido.

Salida:
- Energía AC, PR y compatibilidad eléctrica en tres estados: `✅` compatible y
  adoptable, `❌` incompatible, `—` no evaluable y no adoptable con motivo explícito.

Invariantes:
- Adoptar usa la misma ficha completa que produjo la fila comparada; nunca vuelve a
  resolverla solo por nombre contra otro catálogo.
- Un resultado de sesión legacy sin ficha exacta o motivo eléctrico se descarta y se
  vuelve a calcular; nunca se reconstruye con el estado vigente.
- Adoptar un panel conserva la POA solar base del sitio, pero invalida la POA
  efectiva/óptica dependiente del panel, Producción, Financiero, CO₂ y sus derivados.

#### Comparador de orientación

Entrada:
- TMY vigente, geometría actual y hardware confirmado. La malla debe incluir la
  orientación actual como referencia.

Salida:
- Energía AC y PR por combinación de tilt/azimuth. No publica compatibilidad eléctrica
  porque la orientación no cambia panel, string ni inversor.

Invariantes:
- Adoptar recalcula primero la POA con el TMY y la geometría elegidos; solo después
  actualiza la geometría oficial e invalida Producción, Financiero, CO₂ y derivados.
- En proyectos multi-superficie, las geometrías y POA por superficie pertenecen al
  flujo Multi-Superficie; este comparador no las reconfigura implícitamente.

#### Asistentes y autoridad sobre resultados

- El Asistente general consulta el manual y un resumen del estado de flujo; no recibe
	las tablas de comparación ni debe inventar una recomendación sobre candidatos.
- Cada Analista local recibe únicamente la tabla actual de su comparador y no conserva
	memoria de tablas anteriores ni de otros comparadores.
- Ningún asistente o analista modifica el proyecto. Solo los controles explícitos de
	adopción aplican cambios y deben cumplir las invalidaciones anteriores.

#### Desviaciones activas que bloquean declarar cumplimiento total

- **Adopción de inversor:** la implementación conserva `poa_efectiva_df`, pero elimina
	otras claves del Motor Óptico, incluida `poa_sin_termico_df`. Debe resolverse mediante
	una Spec vertical que defina y pruebe el conjunto atómico de estado óptico que se
	conserva; hasta entonces no se presume que toda la POA efectiva quede reutilizable.
- **Orientación con multi-superficie:** la página no bloquea actualmente este modo y la
	adopción elimina estado multi-superficie mediante la invalidación general. Una Spec
	debe decidir entre bloquear/derivar al flujo Multi-Superficie o implementar adopción
	por superficie; no se permite asumir que la geometría global representa el proyecto.
- **Vigencia de tablas y análisis IA:** los DataFrames y textos de los tres comparadores
	no tienen todavía una firma común de entradas. Una Spec debe invalidarlos al cambiar
	sus insumos y al recalcular, antes de afirmar que una tabla guardada sigue siendo la
	comparación actual.

### 09-despliegue
_(pendiente — ver [../09-despliegue/diseno.md](../09-despliegue/diseno.md))_
