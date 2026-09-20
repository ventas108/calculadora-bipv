# Diseño — Conservación óptica al adoptar inversor

**Estado:** completado

## Entradas

- `session_state` mutable de Streamlit.
- Inversor, número de unidades y `N_serie` seleccionados para adopción.
- Estado óptico vigente publicado por Motor Óptico:
  - `motor_optico_ok`, `motor_optico_result_df`, `motor_optico_summary`;
  - `poa_efectiva_df`, `poa_sin_termico_df`, `poa_efectiva_anual_kWh_m2`;
  - parámetros `motor_optico_*` publicados por la corrida vigente.
- Resultados downstream incluidos en `KEYS_DERIVADOS_POA`.

## Salidas

- Nueva configuración oficial de inversor y referencias de diseño eléctrico.
- Mismo estado óptico, con identidad/valor sin mutación.
- Producción, bypass, pérdida óhmica, Finanzas, CO₂ y demás resultados
  dependientes eliminados de `session_state`.
- Lista de claves realmente eliminadas para el mensaje de interfaz y pruebas.

## Unidades

No se convierten ni recalculan magnitudes. Las series POA conservan sus unidades
y granularidad originales; la función solo clasifica y elimina claves de estado.

## Tipos de datos

- Entrada de estado: `MutableMapping[str, Any]` compatible con
  `st.session_state` y diccionarios de prueba.
- Constantes de claves: tuplas inmutables de `str`.
- Salida de invalidación: `list[str]` con claves existentes que fueron
  eliminadas.

## Errores posibles

- Una clave óptica nueva no incorporada a la fuente central podría borrarse al
  adoptar. La composición y las pruebas de invariantes deben impedirlo.
- Conservar un resultado downstream por clasificación incorrecta podría mostrar
  energía o finanzas del inversor anterior. La prueba debe verificar el conjunto
  completo de claves derivadas no ópticas.
- Duplicar listas entre página y módulo central permitiría divergencias futuras;
  la página no puede mantener una copia local.
- La función debe aceptar estados parciales y repetirse sin `KeyError`.

## Dependencias

- Módulos previos: `03-dimensionamiento`, `04-produccion-energia`,
  `05-perdidas-y-temperatura`.
- Módulos dependientes: `06-analisis-financiero`, `07-informes`, `08-interfaz`.
- Implementación Streamlit exclusiva; no modifica React ni sus contratos.

## Invariantes de transición

- `ESTADO_MOTOR_OPTICO` es subconjunto de `KEYS_DERIVADOS_POA` y es disjunto
  del conjunto invalidado por cambio de inversor.
- Después de adoptar, todas las claves ópticas que existían conservan el mismo
  objeto o valor.
- Toda clave no óptica de `KEYS_DERIVADOS_POA` que existía queda eliminada.
- TMY, POA solar base y claves ajenas a la transición no se modifican.
- Si cambia `N_serie`, los resultados eléctricos ya incluidos (bypass y pérdida
  óhmica) caducan; no se necesita una segunda ruta de invalidación.
- La función es idempotente y no ejecuta simulaciones.

## Criterios de aceptación

- Adoptar inversor conserva conjuntamente `motor_optico_ok`,
  `poa_sin_termico_df`, `poa_efectiva_df`, resumen y parámetros ópticos.
- Producción posterior reconoce el Motor Óptico vigente y consume
  `poa_sin_termico_df`; no cae silenciosamente a POA base.
- Producción, clipping, bypass, pérdida óhmica, Finanzas y CO₂ anteriores quedan
  invalidados.
- La página usa exclusivamente la función central de invalidación y no define
  una lista local “todo menos una clave”.
- La adopción conserva su comportamiento de confirmación del diseño eléctrico.
- No cambian fórmulas, valores numéricos ni resultados del comparador antes de
  adoptar.
- La transición produce el mismo estado previo a una nueva Producción que una
  sesión equivalente donde el Motor Óptico ya estaba calculado y el nuevo
  inversor acababa de seleccionarse.

## Pruebas requeridas

- Prueba unitaria del conjunto óptico y su pertenencia a
  `KEYS_DERIVADOS_POA`.
- Prueba unitaria de conservación exacta del estado óptico.
- Prueba de eliminación de todas las claves derivadas no ópticas.
- Prueba de estado parcial e idempotencia.
- Prueba de página: adopción delega a la función central, conserva las referencias
  de vigencia y no contiene la exclusión local de `poa_efectiva_df`.
- Prueba de integración: con Motor Óptico activo, adoptar y volver a Producción
  selecciona `poa_sin_termico_df`.
- Suites vecinas de comparador de inversores, selección POA/bypass, producción y
  coherencia térmica.
