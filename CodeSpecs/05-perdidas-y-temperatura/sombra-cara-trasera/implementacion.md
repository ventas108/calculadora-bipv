# Implementación — Sombra falsa con el sol detrás del plano del módulo

**Estado:** validación

## Cambios realizados

- `calcular_fs_horario` acepta `tilt_deg`/`azimuth_deg` opcionales
  (solo por palabra clave) y también por punto; la del punto manda. Con
  orientación conocida solo se lanzan rayos en horas con el sol delante del
  plano (`sol · normal > EPS_PLANO`); las demás salen con `FS_geometrico = 0`,
  `FS = 0`, sin obstáculo, distancia `NaN` y `sol_detras_plano = True`. Como
  cada rayo es independiente, las horas con el sol delante quedan idénticas
  a un cálculo sin orientación (verificado por prueba).
- Nueva función pública `normal_modulo(tilt, azimuth, contexto)`: misma
  expresión de normal que `calcular_svf_difuso`; exige ambos valores,
  numéricos, finitos y en rango (tilt 0–180, azimut 0–360); nunca asume una
  orientación.
- Sin orientación: resultado igual al anterior, `sol_detras_plano` nulo y
  `df.attrs["advertencias"]` con `orientacion_desconocida` y los puntos
  afectados.
- `calcular_fs_horario_por_superficie` pasa la orientación de
  `geometria_por_superficie` a cada punto (copias: la firma conserva los
  puntos originales). Si falta `tilt_deg` o `azimuth_deg`, la superficie queda
  en `error_geometrico` con advertencia y calidad `baja`.
- `VERSION_ALGORITMO_FS_POR_SUPERFICIE` pasa a
  `sombras_3d.ray_casting_por_superficie.v2`.
- `invalidar_sombra_por_version_algoritmo` (vinculador) retira `p_shade`,
  firma y estado de sombra de superficies cuya firma es de `sombras_3d`
  (`fuente` o `proveedor`) con versión distinta de la vigente, con
  `sombra_bloqueo_motivo`. Se llama en `construir_y_recalcular_proyecto_fisico`
  justo después de la invalidación por TMY.
  Precisión de diseño: la regla aplica solo a firmas de `sombras_3d`; las
  sombras de otras fuentes (CSV externo, pruebas) no dependen de este
  algoritmo y se conservan, lo que además mantiene intactas las firmas de la
  prueba end-to-end existente.
- Contrato web: `validar_solicitud` acepta `tilt_deg`/`azimuth_deg` opcionales
  por punto (ambos o ninguno, numéricos, en rango) y `run_shading_contract.py`
  los pasa al motor. El payload de salida y `CONTRACT_VERSION` no cambian.
- Página `5a_🌳_Sombras_SketchUp`: pide la orientación del módulo antes del
  cálculo de FS (por defecto `tilt_fachada`/`azimuth_fachada`), la incluye en
  la firma de entradas junto con la versión del algoritmo y la pasa al
  motor; si la tabla de puntos trae columnas `tilt_deg`/`azimuth_deg`
  numéricas, cada punto usa la suya. Una orientación inválida en la tabla no
  descarta el punto: usa la de la página.
- `pages/9_🗺️_Vista_3D.py` sin cambios: ya envía `tilt_deg`/`azimuth_deg`
  por superficie a `calcular_fs_horario_por_superficie`.
- No se tocó `mismatch_bypass.py` ni ningún archivo de `ARCHIVOS_FISICOS`
  (`physics-guard` local: sin fórmulas físicas del SDM modificadas).

## Archivos modificados

- `bipv_python/calculos/sombras_3d.py`
- `bipv_python/calculos/vinculador_sombra_multisuperficie.py`
- `bipv_python/calculos/contrato_sombreado.py`
- `bipv_python/scripts/run_shading_contract.py`
- `bipv_python/pages/5a_🌳_Sombras_SketchUp.py`
- `bipv_python/tests/test_sombra_cara_trasera.py` (nuevo, 30 pruebas)
- `CodeSpecs/05-perdidas-y-temperatura/sombra-cara-trasera/` (Spec completa)
- `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue

- Solo Python; sin migraciones, variables de entorno ni recompilación del
  cliente React.
- Hay que actualizar las dos copias del servidor: Streamlit
  (`/var/www/bipv/calculadora-bipv`, reinicio de `streamlit-bipv`) y la app web
  (`/var/www/bipv/calculadora`), que ejecuta `run_shading_contract.py` en cada
  solicitud; no requiere `pnpm build`.
- Sombras multi-superficie persistidas con `v1` se retiran al recalcular el
  proyecto físico y piden recalcular la sombra.
