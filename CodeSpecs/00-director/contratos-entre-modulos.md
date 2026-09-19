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
_(pendiente — ver [../04-produccion-energia/diseno.md](../04-produccion-energia/diseno.md))_

### 05-perdidas-y-temperatura
_(pendiente — ver [../05-perdidas-y-temperatura/diseno.md](../05-perdidas-y-temperatura/diseno.md))_

### 06-analisis-financiero
_(pendiente — ver [../06-analisis-financiero/diseno.md](../06-analisis-financiero/diseno.md))_

### 07-informes
_(pendiente — ver [../07-informes/diseno.md](../07-informes/diseno.md))_

### 08-interfaz
_(pendiente — ver [../08-interfaz/diseno.md](../08-interfaz/diseno.md))_

### 09-despliegue
_(pendiente — ver [../09-despliegue/diseno.md](../09-despliegue/diseno.md))_
