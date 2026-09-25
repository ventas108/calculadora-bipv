# Propuesta — Panel y strings del proyecto en bypass y MPPT por superficie

**Estado:** completado

## Objetivo

Que el bypass y el MPPT por superficie usen por defecto el mismo panel y la
misma configuración de strings que el resto del proyecto, y que cualquier
diferencia sea una elección visible del usuario.

## Alternativas consideradas

1. **Solo cambiar el índice por defecto.** No cubre paneles del catálogo
   Excel ni los strings por superficie.
2. **Heredar panel y strings del proyecto, con opción explícita de
   sobrescribir.** Recomendada.

## Alternativa recomendada

1. Primera opción de ambos selectores: «Panel del proyecto (nombre)», que
   usa `panel_dict` tal cual (esté o no en `MODULOS_BIPV`). Como el bypass y
   el MPPT resuelven el circuito con el SDM del panel, se exige ficha SDM
   completa (`tiene_sdm_completo`); si no la tiene, se avisa y se ofrece el
   catálogo.
2. Por superficie, `N_series` y `N_parallel` se toman de su configuración
   eléctrica (⚙️ Superficies BIPV). Si falta, se usa `N_serie` de
   Dimensionamiento y el paralelo por área, con aviso de que es una
   estimación.
3. Si el usuario elige otro panel u otro N, la tabla de resultados lo indica
   por superficie («panel distinto al del proyecto»).
4. Los resultados registran el panel y los N usados.

Fuera de alcance: la física del bypass y del MPPT combinado.
