# Ampliación real del catálogo de paneles: 380 módulos Canadian Solar (NREL/SAM + Sandia JPV 2025)

**Fecha**: 3 de septiembre de 2026
**Disparador**: continuación de JA Solar, Trina Solar y Jinko Solar. Canadian Solar es el 4° de los 5
fabricantes Tier 1 confirmados como dominantes en el mercado colombiano (junto a Jinko, LONGi, Trina y
JA Solar — ya cubiertos 3 de esos 5 antes de este lote).

## Hallazgo real: el nombre legal en las fuentes NO es "Canadian Solar"

Buscar "Canadian Solar" literal en `CEC Modules.csv` o `PVS_params_translated.csv` no encuentra nada.
El nombre real del fabricante que usan ambas fuentes es **"CSI Solar Co Ltd"** — el brazo manufacturero
legal real de Canadian Solar Inc. (confirmado por investigación de mercado el mismo día, ver historial
de la sesión). El script de import filtra explícitamente por ese nombre real.

## Mismas 2 fuentes, mismo método de cruce normalizado

`PVS_params_translated.csv` (Deville et al. 2025 IEEE JPV) + `CEC Modules.csv` (NREL/SAM), cruzadas por
nombre normalizado. 384 módulos con match real.

## Auditoría real: el lote más limpio en tolerancia eléctrica, el más pobre en dimensiones

| Resultado | Cantidad |
|---|---|
| 🔴 Fuera de tolerancia real (>6%) — **excluidos** | 4 de 384 (1%) |
| ⚠️ Dentro de tolerancia, a revisar (>2%) | 25 de 384 |
| Sin dimensiones físicas en la fuente (solo área) | **310 de 384 (81%)** |
| **Importados** | **380** |

Los 4 excluidos (familia `CS6X-300P/305P/310P/315P`) muestran sobrepasos menores de tolerancia
(Vmp/Pmax 6-7%), **sin** el patrón de half-cut visto en Trina/Jinko — es un caso límite normal de
ajuste, no un mecanismo sistemático nuevo, no requirió investigación adicional.

**El 81% sin dimensiones es real, verificado directamente en la fuente** (no un error de este script):
para Canadian Solar, `CEC Modules.csv` casi nunca reporta `Length`/`Width` por separado, solo el área
total (`A_c`). Es la tasa más alta de los 4 fabricantes importados hoy (JA Solar 41%, Trina 35%, Jinko
23%, Canadian Solar 81%).

## Sin bugs nuevos de código

Reutiliza exactamente el mismo patrón ya corregido (JA Solar/Trina, sección 39 del manual) — sin
`.strip()` en el mapa de columnas, aviso explícito si algo no mapea. Confirmado: 0 paneles Canadian
Solar con tecnología vacía tras el import.

## Verificación

- `tests/test_comparador_paneles.py::test_paneles_excluidos_por_ficha_incompleta_refleja_el_catalogo_real`
  actualizado: 957 excluidos reales (647 previos + 310 de Canadian Solar, todos por `area_m2=None`).
- Catálogo real: 2.017 (previos) + 380 (Canadian Solar) = **2.397 paneles**.
- Suite completa: **942/942** (1081.66s / 18 min).

## Script de import

`datos/agregar_paneles_canadian_nrel.py` — mismo patrón que los 3 anteriores, filtra por el nombre
legal real "CSI Solar Co Ltd", protegido contra duplicados.
