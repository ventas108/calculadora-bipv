# Diseño — Escena de Site Designer vigente

**Estado:** validación

## Entradas

- El JSON de Site Designer (`Blocks` y `Location`).
- La ubicación del proyecto.
- `multisup_malla_meta.malla_fingerprint`.
- La `firma_sombra.malla_horizonte` de cada superficie.

## Salidas

- `meta["malla_fingerprint"]`
- `invalidar_sombra_por_cambio_malla(superficies, huella_actual) -> list[dict]`,
  llamada en `construir_y_recalcular_proyecto_fisico` después de las
  invalidaciones por TMY y por versión de algoritmo.

## Tipos de datos

Huella: «externa_marsh-» + 16 caracteres hexadecimales.

## Errores posibles

- Escena de otra ubicación: no se guarda, error visible.
- Firma de otra escena: se retiran `p_shade`, `firma_sombra` y la cobertura,
  con `sombra_bloqueo_motivo`.
- Sin escena cargada o firma sin prefijo «externa_marsh-»: sin cambios.

## Dependencias

`calculos/sitedesigner_marsh.py`,
`calculos/vinculador_sombra_multisuperficie.py`,
`pages/9_🗺️_Vista_3D.py`.

## Criterios de aceptación

1. Escenas distintas → huellas distintas; la misma escena → la misma huella;
   el norte cuenta.
2. Otra escena cargada → sombra retirada con motivo; la misma, sin escena,
   otra fuente o sin firma → se conserva.
3. El proyecto físico rechaza la sombra de otra escena; con la misma escena,
   el resultado es idéntico.
4. La protección contra sombras v1 sigue aplicando con escenas de Site Designer.
5. Vista 3D rechaza otra ubicación y firma con la huella.
6. Sección 122 del manual, con el alcance radiativo del bypass.
