# Ampliación real del catálogo de paneles CdTe: 170 módulos First Solar (NREL/SAM + Sandia JPV 2025)

**Fecha**: 3 de septiembre de 2026
**Disparador**: el usuario pidió ampliar el abanico de paneles CdTe, explícitamente indicando que
Producción ya usa el motor JRC/Huld (no SDM) para esta tecnología — resolviendo así la objeción
inicial de esta sesión ("importar First Solar por esta vía repetiría el defecto de la joroba SDM").
El usuario adjuntó 2 fichas oficiales reales de First Solar (Series 6 Plus, Series 7 TR1) para
verificar los datos antes de proceder.

## Verificación real contra 2 fichas oficiales (no resúmenes de buscador)

Se extrajo el texto de los PDF reales entregados y se cruzó contra `CEC Modules.csv`:

| | Ficha oficial real | CEC (fuente del import) |
|---|---|---|
| Series 6 Plus, bin 470W | Voc=224.3V, Vmp=191.1V, Isc=2.61A, Imp=2.46A, N_s=268 | **idéntico exacto** (`FS-6470A-P`) |
| Series 7 TR1, bin 530W | Voc=226.7V, Vmp=186.9V, Isc=3.05A, Imp=2.84A | **idéntico exacto** (`FS-7530A-TR1`) |

Ambas fichas confirman: 268 celdas ("Thin film CdTe semiconductor, up to 268 cells"), NOCT oficial
real = **45°C** (condición de referencia explícita: "NOMINAL OPERATING CELL TEMPERATURE OF 45°C").

## Criterio de import DISTINTO al de los 5 fabricantes cristalinos ya importados

1. **Sin exclusión por tolerancia SDM (6%)**. Los 5 imports cristalinos previos (JA Solar, Trina,
   Jinko, Canadian Solar, LONGi) excluían módulos que no ajustaban bien en `validar_sdm_vs_ficha()`
   porque **SDM es el motor real de energía para cristalino**. Para CdTe, **Producción ya usa
   JRC/Huld, no SDM** (migrado el 2-sep-2026, ver `DIAGNOSTICO_JRC_HULD_PRIMARIO_CDTE.md`, por un
   defecto estructural real del SDM para esta tecnología — la "joroba" de eficiencia >100%).
   Excluir First Solar por un chequeo de ajuste SDM habría descartado paneles CdTe reales buenos por
   una métrica irrelevante para su uso principal. Se calcula igual (59/170, 35%, no ajustan bien en
   SDM — esperado, es el mismo defecto ya conocido) y queda como aviso informativo en `Notas`, **sin
   bloquear el import**. Los 170 candidatos reales entraron.
2. **Reclasificación de Tecnología a "CdTe"** para los 70 módulos que la fuente etiqueta
   genéricamente "Thin Film" — verificado real: son módulos First Solar más antiguos y más pequeños
   (formato clásico 1.2×0.6m, series 2-4), no un producto distinto — First Solar solo fabrica CdTe.
   Sin esto, `clasificar_tecnologia_jrc()` no los reconocería como CdTe y `produccion.py` los dejaría
   caer en SDM por defecto (repitiendo el problema que motivó todo este ajuste).

## Verificación end-to-end real (no solo en el papel)

Se corrió `calculos.produccion._calcular_pmax_vectorizado()` directamente sobre un panel First Solar
recién importado (`FS-6405A`, Pmax_stc=405W) a G=[1000, 500, 200] W/m², T=25°C:

```
Pmax:            405.00 W → 201.97 W → 71.80 W
Eficiencia rel.: 100.0%   → 99.7%    → 88.6%
```

Curva **monótona decreciente, sin joroba** — confirma que el enrutamiento a JRC/Huld funciona
correctamente para los paneles nuevos, no solo en teoría.

## NOCT: mismo patrón ya visto con JA Solar, documentado, no oculto

CEC reporta NOCT hasta varios grados por encima del real: mediana del lote 47.3°C contra el 45°C
oficial confirmado en ambas fichas (~2.3°C de diferencia). Como Producción sigue usando el modelo
térmico NOCT+k_BIPV (JRC/Huld no trae su propio modelo térmico, ver diseño documentado en
`DIAGNOSTICO_JRC_HULD_PRIMARIO_CDTE.md`), esto sí afecta la energía calculada — cada fila lo declara
explícitamente en `Notas`.

## Verificación

- `clasificar_tecnologia_jrc()`: **0/170** paneles First Solar quedan sin clasificar como CdTe tras
  el import (verificado programáticamente, no solo revisado a ojo).
- `tests/test_comparador_paneles.py::test_paneles_excluidos_por_ficha_incompleta_refleja_el_catalogo_real`
  actualizado: 1.266 excluidos reales (1.166 previos + 100 de First Solar sin dimensiones, todos por
  `area_m2=None`).
- Catálogo real: 2.641 (previos) + 170 (First Solar) = **2.811 paneles**.
- Suite completa: **942/942** (1205.05s / 20 min).

## Script de import

`datos/agregar_paneles_firstsolar_nrel.py` — mismo esquema de trazabilidad que los 5 imports
anteriores, con la lógica CdTe-aware descrita arriba, protegido contra duplicados.
