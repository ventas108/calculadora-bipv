# Diseño — Sombra falsa con el sol detrás del plano del módulo

**Estado:** diseño

## Entradas

- `calcular_fs_horario(malla, puntos, lat, lon, indice_tmy=None,
  transparencia=0.0, altura_min_deg=..., tilt_deg=None, azimuth_deg=None)`:
  - `tilt_deg`: inclinación del módulo, 0 = horizontal, 90 = vertical (°).
  - `azimuth_deg`: azimut del módulo, convención pvlib (0 = N, 90 = E,
    180 = S, 270 = O) (°).
  - Cada punto puede traer sus propias claves `tilt_deg`/`azimuth_deg`; si
    están, tienen prioridad sobre los argumentos de la función.
- `calcular_fs_horario_por_superficie(...)`: sin cambio de firma; toma la
  orientación de `geometria_por_superficie[nombre]["tilt_deg"|"azimuth_deg"]`.
- Contrato web (`run_shading_contract.py`): cada punto puede traer
  `tilt_deg` y `azimuth_deg` opcionales.
- Página `5a_🌳_Sombras_SketchUp`: la orientación que hoy se pide para el SVF
  (`tilt_fachada` / `svf_tilt_input`, azimut) se pide antes del cálculo de FS
  y se pasa a ambos cálculos; columnas `tilt_deg`/`azimuth_deg` opcionales en
  la tabla de puntos, por punto.
- Superficies persistidas con `firma_sombra["version_algoritmo"]`.

## Salidas

- DataFrame de `calcular_fs_horario` con las mismas columnas actuales más
  `sol_detras_plano` (`bool`, o `pd.NA` si no se conoce la orientación).
- Con sol detrás del plano: `FS_geometrico = 0`, `FS = 0`,
  `obstacle_id = None`, `obstacle_name = None`, `first_hit_distance_m = NaN`.
- Con sol delante del plano: valores idénticos a los actuales, bit a bit.
- Sin orientación: resultado idéntico al actual y
  `df.attrs["advertencias"]` con `orientacion_desconocida`.
- `VERSION_ALGORITMO_FS_POR_SUPERFICIE = "sombras_3d.ray_casting_por_superficie.v2"`.
- Superficies con sombra de una versión distinta a la vigente: se retiran los
  campos de `_CAMPOS_SOMBRA` y se escribe `sombra_bloqueo_motivo` explicando
  que la sombra fue calculada con un algoritmo anterior y debe recalcularse.

## Unidades

Grados sexagesimales para `tilt_deg`, `azimuth_deg`, altura y acimut solar;
metros para coordenadas; `FS_geometrico` adimensional en [0, 1]. No se
introducen conversiones nuevas: la normal se obtiene con la misma expresión que
ya usa `calcular_svf_difuso`, `vector_al_sol(90 − tilt, azimut)`.

## Tipos de datos

- `tilt_deg`, `azimuth_deg`: `float | None`; finitos; `tilt_deg` en [0, 180],
  `azimuth_deg` en [0, 360).
- Criterio por hora: `np.dot(dir_sol, normal) <= EPS_PLANO`, con
  `EPS_PLANO = 1e-9` (sol rasante sobre el plano cuenta como detrás, sin haz).
- `sol_detras_plano`: columna `boolean` de pandas (admite `pd.NA`).
- Advertencias: `list[str]` en `df.attrs["advertencias"]`.

## Errores posibles

- Orientación no numérica, no finita o fuera de rango: `ValueError` con el
  punto o superficie afectados; nunca se asume una orientación.
- Solo uno de los dos valores (`tilt` sin `azimuth` o al revés): `ValueError`.
- Superficie del flujo multi-superficie sin `tilt_deg`/`azimuth_deg` en su
  geometría: estado `error_geometrico`, calidad `baja`, sin `p_shade`
  aceptable.
- Convención de azimut equivocada (p. ej. 0 = S): invierte el filtro. Se
  protege con pruebas de orientación conocida (fachada sur con sol al norte
  en junio y sol al sur en diciembre en Bogotá).
- Sombras persistidas con `v1` restauradas tras el despliegue: deben quedar
  retiradas antes de cualquier Producción; la prueba de persistencia lo
  verifica.
- El cambio no toca `mismatch_bypass.py`; si una implementación lo tocara,
  `physics-guard` exige test de validación en el mismo PR.

## Dependencias

- Módulos previos: `02-recurso-solar` (TMY y posiciones solares),
  `05-perdidas-y-temperatura/transicion-multisuperficie` y
  `persistencia-multisuperficie` (estados, firmas, invalidación).
- Módulos dependientes: `04-produccion-energia` (bypass con `p_shade`),
  `06-analisis-financiero` y `07-informes`, que heredan energía con menos
  pérdida falsa; `08-interfaz` (Spec posterior para que React envíe la
  orientación).
- Capas afectadas: cálculo (`calculos/sombras_3d.py`), estado
  (`calculos/vinculador_sombra_multisuperficie.py`), API
  (`scripts/run_shading_contract.py`), interfaz Streamlit
  (`pages/5a_🌳_Sombras_SketchUp.py`; `pages/9_🗺️_Vista_3D.py` ya envía la
  geometría y solo se verifica).
- Sin migraciones de base de datos ni variables de entorno.

## Invariantes

- Un volumen convexo aislado con puntos en sus caras y orientación correcta
  produce 0 horas con `FS_geometrico > 0`.
- Toda hora con sol delante del plano conserva exactamente el valor actual.
- Toda hora con `FS_geometrico > 0` cumple `sol · normal > 0` cuando la
  orientación es conocida.
- El número de filas del resultado no cambia (una por punto y hora con sol).
- Sin orientación, la salida es idéntica a la de `main` `9398948e`.

## Criterios de aceptación

- Torre convexa (17,29 × 17,29 × 36,42 m, `northOffset` 160,5°): 0 horas
  sombreadas en las 4 caras (hoy 2.021–2.302).
- Escena sintética de la prueba de cierre, Fachada Sur (tilt 90°, azimut
  180°): 678 horas-punto sombreadas, antes 4.080; con el edificio de la
  fachada también 678, antes 10.908.
- Pruebas actuales de contrato, Site Designer y comparativo SketchUp/Marsh
  pasan sin cambios (no pasan orientación).
- Las 10 suites de la prueba de cierre multisuperficie siguen en verde
  (línea base `110 passed`) más las pruebas nuevas.
- Una superficie persistida con `version_algoritmo` `v1` queda sin
  `p_shade` y con motivo de bloqueo tras restaurar.
- Suite completa en verde en CI (gate de cero tolerancia).

## Pruebas requeridas

- Invariante de la caja convexa (4 caras, orientación correcta).
- Obstáculo real delante del módulo: `FS_geometrico = 1` sin cambios.
- Obstáculo detrás del módulo: `FS_geometrico = 0` y `sol_detras_plano = True`.
- Filas y columnas: mismo número de filas; columna nueva presente.
- Sin orientación: igualdad exacta con el comportamiento previo más advertencia.
- Orientación por punto con prioridad sobre la de la función.
- Validación de entradas: no numérica, fuera de rango, solo uno de los dos.
- Cubierta inclinada 10° al sur: horas con sol detrás del plano filtradas y
  resto intacto.
- Por superficie: la orientación de la geometría llega al ray-casting; sin
  orientación, estado `error_geometrico`; versión `v2` en la firma.
- Persistencia: firma `v1` retirada con motivo; firma `v2` conservada.
- Contrato web: punto con y sin orientación.
- Regresión: 10 suites de cierre multisuperficie y suite completa.
