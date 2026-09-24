# Diseño — Vigencia de la POA por superficie

**Estado:** validación

## Entradas

- Superficie: `uid`, `nombre`, `tipo`, `tilt_deg`, `azimuth_deg`, `area_m2`,
  `activa`, `montaje_fachada`.
- TMY vigente (`tmy_df`, con `T2m`), `lat`, `lon`, `alt_m`.
- `albedo_suelo`, configuración bifacial efectiva por superficie.

## Salidas

- `st.session_state["poa_superficies"]`: `dict[uid, {"poa": DataFrame,
  "firma": str}]` (antes `dict[nombre, DataFrame]`).
- `superficie["firma_poa"]`: `str` con la misma huella.
- `st.session_state["poa_superficies_errores"]`: `dict[uid, str]` con la causa
  de cada cálculo fallido.
- `poa_vigente(...)`: `DataFrame | None` y, si es `None`, un motivo legible
  (`sin_calcular`, `geometria_cambiada`, `tmy_cambiado`, `error_calculo`).

## Tipos de datos

- Firma: `str` (hash hexadecimal de `fingerprint_mapping`), calculada sobre
  geometría + montaje + albedo + bifacial + `lat`/`lon`/`alt_m` +
  `huella_horaria(tmy.index, tmy["T2m"])`.
- Clave del diccionario: `uid` (`int`), estable ante renombrados.

## Errores posibles

- Sesiones antiguas con `poa_superficies` indexado por nombre: se tratan como
  POA sin firma → `sin_calcular`, con aviso para recalcular (sin migración
  silenciosa).
- Superficie inactiva: no se calcula ni se exige.
- Error de pvlib en una superficie: queda en `poa_superficies_errores` y la
  UI lo muestra; las demás superficies siguen calculándose.

## Dependencias

- Módulos previos: `02-recurso-solar` (TMY), `05/transicion-multisuperficie`,
  `05/persistencia-multisuperficie` (campo `firma_poa`).
- Módulos dependientes: la Spec `publicacion-energia-multisuperficie`,
  `08-interfaz` (Vista 3D), `06-analisis-financiero` vía la energía publicada.
- Capas: cálculo (`multi_superficie.py`), estado (`invalidacion.py`,
  `session_state`), interfaz (`pages/9_🗺️_Vista_3D.py`).

## Criterios de aceptación

- Cambiar tilt, azimuth, área, tipo o montaje de una superficie deja su POA
  en `geometria_cambiada`; las demás superficies conservan la suya.
- Cambiar el TMY o las coordenadas deja todas las POA en `tmy_cambiado` o
  invalidadas.
- Renombrar una superficie conserva su POA vigente.
- Ningún consumidor de la página muestra ni usa una POA no vigente; cada uno
  indica qué superficie hay que recalcular.
- Un fallo de cálculo aparece con su causa y no como POA vacía.
- `superficie["firma_poa"]` queda escrita y la restauración de la persistencia
  rechaza un proyecto cuya POA firmada no coincide.

## Pruebas requeridas

- Firma: estable ante renombrado; cambia con cada entrada firmada.
- `poa_vigente` para los cuatro motivos.
- `calcular_poa_todas` con una superficie que falla: error reportado, resto
  calculado.
- Invalidación por coordenadas incluye `poa_superficies`.
- Persistencia: `firma_poa` distinta rechaza la restauración.
- Regresión: suites de multi-superficie, persistencia y página Vista 3D.
