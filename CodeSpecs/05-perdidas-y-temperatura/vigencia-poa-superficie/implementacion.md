# Implementación — Vigencia de la POA por superficie

**Estado:** validación

## Cambios realizados

- `calculos/multi_superficie.py`:
  - Motivos `sin_calcular`, `geometria_cambiada`, `tmy_cambiado` y
    `error_calculo` con su texto (`TEXTO_MOTIVO_POA`).
  - `config_bifacial_superficie`: la regla de factor de vista trasero por
    superficie que antes vivía en la página (tilt < 80° ⇒ 1,0; Adosada ⇒ 0 y
    albedo trasero 0,05; Ventilada ⇒ 1,0; Heredar ⇒ el global).
  - `firma_poa_superficie` → `{"sitio", "geometria", "firma"}`. La firma de
    sitio cubre latitud, longitud, altitud y la huella horaria de `T2m`,
    `G_h`, `Gb_n` y `Gd_h`; la de geometría cubre tipo, tilt, azimuth, área,
    montaje, albedo y bifacial efectivo. Mismo mecanismo que
    `produccion_vigencia` (`fingerprint_mapping`, `huella_horaria`).
  - `calcular_poa_superficies_firmadas` → `(resultados[uid], errores[uid])`;
    cada resultado lleva nombre, POA y las tres firmas. Un fallo nunca se
    convierte en una POA vacía.
  - `poas_vigentes` → `(vigentes[nombre], motivos[nombre])` para las
    superficies activas, y `poas_vigentes_estado` que lee todo de la sesión
    con `parametros_poa_estado` (fuente única de albedo y bifacial para el
    cálculo y para la vigencia).
- `calculos/vinculador_sombra_multisuperficie.py`:
  `preservar_o_invalidar_campos_fisicos` conserva `firma_poa` mientras tipo,
  tilt, azimuth, área y montaje no cambien y la retira si cambian.
- `pages/9_🗺️_Vista_3D.py`: el botón «⚡ Calcular POA» usa el cálculo
  firmado, guarda `poa_superficies` (por `uid`), `poa_superficies_errores` y
  `firma_poa` en cada superficie. Resumen, «Usar sistema multi-superficie»,
  vista 3D, producción, bypass y mapa de calor solo leen POA vigentes; las
  demás superficies aparecen en un aviso con su motivo (y la causa si el
  cálculo falló). «Usar sistema multi-superficie» queda deshabilitado
  mientras una superficie activa no tenga POA vigente.
- `calculos/proyectos_manager.py`: `poa_superficies`,
  `poa_superficies_errores` y `poa_superficies_ok` no se guardan y se
  reinician al cargar otro proyecto.

Desviaciones del diseño, con motivo:

- Cada entrada de `poa_superficies` guarda, además de la POA y la firma
  combinada, la firma de sitio y la de geometría: así el motivo distingue
  `tmy_cambiado` de `geometria_cambiada` sin recalcular la POA.
- La firma de sitio incluye la huella de las columnas de irradiancia, no solo
  de `T2m`: un TMY con la misma temperatura y otra irradiancia también debe
  invalidar la POA.
- `poa_superficies` no se agrega a `KEYS_DERIVADOS_POA`: esa lista también
  se aplica al cambiar de inversor, que no altera la POA. El cambio de
  coordenadas o TMY queda cubierto por la firma de sitio
  (`tmy_cambiado`, con prueba), y el cambio de proyecto por el reinicio en
  `proyectos_manager`.
- `calcular_poa_todas` se conserva sin cambios porque la usan
  `scripts/test_bifacial.py` y `scripts/patch_vista3d.py`; la página ya no la
  usa.
- `poa_vigente` (una superficie) se implementó como `poas_vigentes` (todas
  las activas) y `poas_vigentes_estado`, que es lo que necesitan los
  consumidores.

## Archivos modificados

- `bipv_python/calculos/multi_superficie.py`
- `bipv_python/calculos/vinculador_sombra_multisuperficie.py`
- `bipv_python/calculos/proyectos_manager.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_vigencia_poa_superficie.py` (nuevo)
- `bipv_python/tests/test_persistencia_multisuperficie.py` (prueba de
  `firma_poa` distinta)
- `bipv_python/tests/test_asistente_retrieval.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `docs/MANUAL_VISTA_3D.md`, `entregables/MANUAL_VISTA_3D_BIPV.docx`
- `CodeSpecs/05-perdidas-y-temperatura/vigencia-poa-superficie/`
- `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue

- Solo la app Streamlit (`/var/www/bipv/calculadora-bipv`, reinicio de
  `streamlit-bipv`). La app web no usa estos módulos.
- Las POA por superficie de sesiones abiertas antes del despliegue aparecen
  como «POA sin calcular» y piden recalcular.
