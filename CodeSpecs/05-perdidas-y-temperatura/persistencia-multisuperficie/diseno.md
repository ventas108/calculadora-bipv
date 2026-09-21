# Diseño — Payload canónico y restauración multi-superficie

**Estado:** aprobado para implementación después de revisión

## Frontera

La Spec añade un módulo puro de persistencia y lo conecta al flujo existente de proyectos. La lógica de cálculo físico permanece en `calculos/transicion_multisuperficie.py` y `calculos/adaptador_multisuperficie.py`. Los consumidores de `multisup_*` no se modifican.

## Payload raíz

El payload JSON debe contener exactamente, como mínimo:

```text
schema_version
payload_kind = "bipv_multisuperficie"
inputs
results
validity
provider_metadata
payload_signature
```

No se guardan objetos Python, DataFrames, índices pandas ni modelos de catálogo directamente.

### `inputs`

Debe contener todos los datos que determinan el cálculo:

- `project_identity`: usuario/proyecto, ciudad, latitud, longitud y altitud;
- `tmy`: proveedor, período/fuente y `tmy_fingerprint` calculado sobre el TMY real;
- `surfaces`: lista completa y ordenada por `uid`, con `nombre`, `tipo`, `activa`, `area_m2`, `tilt_deg`, `azimuth_deg`, puntos/malla de sombra y su representación canónica;
- `electrical`: panel, `n_serie`, `n_paralelo`, inversores completos y asignaciones por superficie;
- configuración física y eléctrica que consuma el motor, sin completar ausencias con defaults.

### `results`

Debe separar por superficie y conservar la forma canónica necesaria para restaurar o volver a validar:

- `p_shade` y estado/calidad de sombra;
- `firma_sombra`;
- POA geométrica y, si aplica explícitamente, POA óptica sin térmico;
- `firma_poa` y metadatos de cálculo;
- resultados DC/AC, clipping y agregados físicos;
- firmas de producción derivadas.

Las series y tablas se codifican como listas/objetos JSON deterministas con columnas, índice, dtype lógico y valores. Nunca se serializa un DataFrame directamente.

### `validity` y `provider_metadata`

`validity` contiene firmas individuales y `firma_global`. `provider_metadata` identifica proveedor, algoritmo, versión y parámetros relevantes de TMY, sombra y POA. La metadata no sustituye la validación de los datos.

## Funciones puras obligatorias

Implementar en un módulo dedicado, con errores explícitos y sin mutar `session_state` durante la validación:

```python
construir_payload_multisuperficie(session_state, resultados) -> dict
firmar_payload_multisuperficie(payload) -> str
validar_payload_multisuperficie(payload, contexto_actual) -> ResultadoValidacion
restaurar_multisuperficie(payload, session_state) -> ResultadoRestauracion
```

`contexto_actual` debe aportar TMY, geometría y configuración real vigente cuando sean necesarios para comparar firmas. La restauración debe construir un snapshot candidato y publicarlo solo después de que todas las validaciones terminen correctamente.

## Reglas de firma

1. La firma se calcula sobre una serialización canónica JSON, ordenada y sin campos volátiles.
2. La firma global cubre `schema_version`, entradas, resultados y firmas individuales.
3. Cada superficie debe validar geometría, configuración eléctrica, sombra, POA y TMY contra sus firmas.
4. TMY diferente, geometría diferente, tilt/azimuth diferentes, inversor diferente o `N_serie` diferente invalidan el payload.
5. Campos obligatorios ausentes, campos desconocidos críticos, firmas alteradas y schema no soportado rechazan la carga.
6. No se aceptan resultados sin sus entradas y firmas correspondientes.

## Restauración todo-o-nada

- Validar sin escribir.
- Construir todas las claves candidatas en memoria.
- Verificar que todas las superficies activas y asignaciones existen.
- Publicar en `session_state` mediante una única operación de commit.
- Ante cualquier error, no escribir ninguna clave física ni `multisup_*` y dejar intacto el estado anterior.
- Un payload rechazado no puede alimentar downstream; `multisup_activo` debe permanecer falso o ausente.

## Evolución

`schema_version` usa una lista explícita de versiones soportadas. Una versión no soportada se rechaza; no se migra implícitamente. Toda migración futura debe ser función pura, versionada, probada y separada de la restauración.

## Integridad y HMAC

La versión actual usa SHA-256 sobre el payload canónico para detectar corrupción
accidental y modificaciones que no recalculen la firma. No se presenta como una
protección contra un usuario con acceso de escritura al JSON, porque ese actor
podría recalcular un SHA-256 válido. HMAC con un secreto del servidor queda como
decisión futura separada: exigiría gestión de secretos, rotación, recuperación y
una nueva versión de schema; no se introduce en esta ronda.

## Integración

Guardar proyecto: `session_state -> construir_payload -> firma -> escritura atómica`.

Cargar proyecto: `lectura -> schema -> firma global -> TMY/geometría/sombra/POA/electricidad -> snapshot -> commit`.

El flujo existente de resultados de Producción conserva su contrato y no debe mezclarse con el archivo físico multi-superficie.
