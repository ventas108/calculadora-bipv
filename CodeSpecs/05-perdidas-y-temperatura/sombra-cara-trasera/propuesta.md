# Propuesta — Sombra falsa con el sol detrás del plano del módulo

**Estado:** validación

## Objetivo

Que `FS_geometrico` represente solo sombra de haz directo físicamente posible:
cero cuando el sol está detrás del plano del módulo, sin alterar ninguna hora
con el sol delante, y que ninguna sombra calculada con el algoritmo anterior
siga usándose en Producción ni en el modo físico multi-superficie.

## Alternativas consideradas

1. **Recortar después, en Producción o en el bypass** (multiplicar `p_shade`
   por `AOI < 90°`). Deja CSV, gráficas, horas críticas y contratos con sombras
   imposibles; cada consumidor tendría que repetir la regla. Rechazada.
2. **Quitar el edificio propio de la malla.** No resuelve obstáculos reales
   situados detrás (el árbol de la prueba sintética) y obliga a cada usuario a
   editar la escena. Rechazada.
3. **Deducir la normal de la malla más cercana al punto.** Frágil con puntos
   flotantes, escenas sin muro o superficies inclinadas. Rechazada.
4. **Filtrar en el origen, con la orientación explícita del módulo.**
   `calcular_fs_horario` recibe `tilt_deg`/`azimuth_deg` opcionales (misma
   convención pvlib que `calcular_svf_difuso`); con sol detrás del plano,
   `FS_geometrico = 0` y la hora se marca. Sin orientación, comportamiento
   actual con advertencia explícita. Recomendada.

## Alternativa recomendada

La alternativa 4:

1. `calcular_fs_horario` acepta `tilt_deg` y `azimuth_deg` opcionales, y
   también por punto (claves `tilt_deg`/`azimuth_deg` del dict, con prioridad
   sobre los argumentos).
2. Con orientación conocida: `sol · normal ≤ 0` ⇒ `FS_geometrico = 0`, `FS = 0`,
   `sol_detras_plano = True`, sin obstáculo ni distancia de impacto. Las horas
   se siguen exportando (se conserva “una fila por punto y hora con sol”).
3. Sin orientación: resultado idéntico al actual, columna
   `sol_detras_plano` vacía y advertencia `orientacion_desconocida` en
   `df.attrs`. Ningún cambio silencioso para llamadores existentes.
4. `calcular_fs_horario_por_superficie` pasa siempre la orientación de
   `geometria_por_superficie`; si falta, la superficie queda con estado
   `error_geometrico` (el modo físico no debe aceptar sombra sin orientación).
5. `VERSION_ALGORITMO_FS_POR_SUPERFICIE` pasa a `v2`, e
   `invalidar_sombra_por_cambio_tmy` (o una función hermana llamada en los
   mismos puntos) también retira sombras cuya `version_algoritmo` no sea la
   vigente, con motivo explícito.
6. El contrato web (`run_shading_contract.py`) acepta `tilt_deg`/`azimuth_deg`
   opcionales por punto. Que la interfaz React los envíe queda para una Spec
   de `08-interfaz`.
7. La página `5a_🌳_Sombras_SketchUp` pasa la orientación que ya pide para el
   SVF.

Fuera de alcance: difusa en el bypass, cadena de pérdidas/PR, base climática,
escena de Torre 5 con torres vecinas y cambios en React.
