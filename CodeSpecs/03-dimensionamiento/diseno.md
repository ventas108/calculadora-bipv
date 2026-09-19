# Diseño — Dimensionamiento eléctrico

**Estado:** completado

## Entradas

- Catálogo de paneles e inversores, incluyendo límites eléctricos y trackers.
- Temperaturas de diseño de ciudad/TMY, editables por el usuario, en `°C`.
- Área, ocupación, tipo de instalación y configuración del proyecto.
- Cadenas totales, strings por tracker y rango de exploración de módulos en serie.

## Salidas

- Compatibilidad por string: `Voc`, `Vmp`, corriente y mensajes de límite.
- `N_serie` y `N_strings_tracker` confirmados; vigencia y aviso de diseño.
- Totales de proyecto: paneles, inversores, potencia DC y relación DC/AC.
- Mapeo de catálogo con estados compatible, no compatible o no evaluable.

## Unidades

- Tensión: `V`; corriente: `A`; potencia: `W` y `kW`; área: `m²`; temperatura: `°C`.

## Tipos de datos

- Catálogos y resultados: diccionarios serializables.
- Estado de interfaz: `session_state`; valores eléctricos y conteos numéricos.

## Errores posibles

- Ficha de inversor incompleta o con valores no finitos: estado `No evaluable`,
	sin recomendación.
- Diseño confirmado desactualizado por cambio de panel o inversor: `vigente=False`
	y aviso explícito.

## Dependencias

- Módulos previos: `01-datos-proyecto`, `02-recurso-solar`
- Módulos dependientes: `04-produccion-energia`

## Criterios de aceptación

- Los consumidores downstream usan solo `diseno_electrico_confirmado()`; nunca el
	widget vivo `N_str_tr`.
- El prorrateo preliminar se invalida cuando cambia panel, inversor o el valor
	efectivo de strings por tracker.
- Un catálogo incompleto no genera una recomendación de compatibilidad.

## Pruebas requeridas

- `test_compatibilidad_string.py` cubre estado confirmado, vigencia, prorrateo y
	fichas incompletas.
