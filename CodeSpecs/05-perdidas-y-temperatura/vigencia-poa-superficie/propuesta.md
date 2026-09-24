# Propuesta — Vigencia de la POA por superficie

**Estado:** diseño

## Objetivo

Que ninguna POA por superficie se use si no corresponde a la geometría, el
TMY, la ubicación y la configuración óptica vigentes, y que cada fallo de
cálculo sea visible.

## Alternativas consideradas

1. **Borrar `poa_superficies` ante cualquier edición.** Simple, pero borra
   también la POA de superficies que no cambiaron y no resuelve TMY ni
   persistencia.
2. **Recalcular automáticamente en cada rerun.** Costoso (pvlib × superficies
   × 8760 h en cada interacción) y con efectos implícitos.
3. **Firma de POA por superficie, indexada por `uid`, y verificación de
   vigencia en cada consumidor.** Recomendada.

## Alternativa recomendada

La alternativa 3:

1. Nueva función pura `firma_poa_superficie(sup, tmy, lat, lon, alt_m,
   albedo, bifacial_cfg)` → huella determinista (mismo mecanismo
   `fingerprint_mapping` / `huella_horaria` de `produccion_vigencia`).
2. `calcular_poa_todas` devuelve, por `uid`, la POA **y** su firma; los fallos
   se reportan como error explícito por superficie, no como DataFrame vacío.
3. La firma se escribe también en `superficie["firma_poa"]`, con lo que la
   verificación ya existente de la persistencia pasa a ser efectiva.
4. Nueva función `poa_vigente(sup, poa_superficies, contexto)` que devuelve la
   POA solo si su firma coincide con la actual; los consumidores de la página
   la usan en lugar de leer el diccionario directamente.
5. `poa_superficies` se añade a las listas de invalidación por cambio de
   coordenadas/TMY de `calculos/invalidacion.py`.

Fuera de alcance: la física de la POA, el modo físico y el Motor Óptico.
