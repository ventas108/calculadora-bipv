# Ampliación real del catálogo con 80 paneles SunPower (NREL/SAM + Sandia JPV 2025)

**Fecha**: 3 de septiembre de 2026
**Fuentes**: las mismas 2 de todos los imports anteriores — NREL/SAM `CEC Modules.csv` y Deville
et al. 2025 IEEE JPV (`PVS_params_translated.csv`, Zenodo 10.5281/zenodo.14173605).

## Dos criterios de exclusión, de naturaleza distinta

107 candidatos con match normalizado (`Manufacturer` = "SunPower"). Se excluyeron 27, por dos
razones distintas — es la primera vez que aparece la exclusión #1:

### 1. Familia "-R" — AC Module con microinversor integrado (21 excluidos)

La familia Maxeon 3 tiene variantes con y sin sufijo "-R" (`SPR-MAX3-400` vs `SPR-MAX3-400-R`).
Auditando la tolerancia SDM, las variantes "-R" fallaban con errores de Voc de **hasta 56%** —
mucho más grave que cualquier caso visto en los 6 imports anteriores. Se verificó contra la ficha
pública real de Maxeon 3 (secondsol.com, enfsolar.com):

| | Ficha real (Maxeon 3, 104 celdas) | CEC sin "-R" | CEC con "-R" |
|---|---|---|---|
| Voc | 75.6 V | 81.09 V (Ns=112) | 40.55 V (Ns=112) |
| Isc | 6.58 A | 6.53 A | 13.06 A |
| V/celda | 0.727 V | 0.724 V | **0.362 V** |

Las variantes sin "-R" coinciden con la ficha real (V/celda≈0.72-0.73V, consistente en toda la
familia). Las variantes "-R" dan **siempre** V/celda≈0.362V (exactamente la mitad) e Isc casi el
doble, en las 21 filas sin excepción. A diferencia del patrón half-cut de Trina/Jinko (un defecto
de traducción del paper), esto **no es un error de dato** — la búsqueda confirmó que "-R" identifica
la línea "Residential AC Module" de SunPower: un panel con microinversor integrado por unidad. Eso
cambia la arquitectura eléctrica real del producto (2 strings en paralelo alimentando el
microinversor), y **no encaja en el modelo de la app**, que asume paneles DC conectados en serie
(`N_serie`) a un inversor central de string. Se excluyó por incompatibilidad de arquitectura, no
por tolerancia.

### 2. Tolerancia SDM 6% — familia SPR-A-COM (6 excluidos)

Las 6 excluidas son la variante "-COM" (72 celdas) del A-Series, con `Pmax` error 7.7-10.0%. Se
verificó que el problema está en el propio dato fuente de CEC, no en el ajuste del modelo:

```
SPR-A400 (66 celdas):     Voc=47.60V  Vmp=39.60V  Imp=10.10A  Vmp×Imp=400.0W  Pmax nameplate=400W ✓
SPR-A400-COM (72 celdas): Voc=52.10V  Vmp=43.30V  Imp=10.10A  Vmp×Imp=437.3W  Pmax nameplate=400W ✗
```

CEC escaló Voc/Vmp al pasar de 66 a 72 celdas (proporcionalmente correcto: 47.60×72/66=51.9≈52.1),
pero dejó el campo `Pmax` nameplate igual al de la versión de 66 celdas (400W) en vez de escalarlo
también (~437W esperado). Es una inconsistencia real de la fuente CEC, exactamente el tipo de caso
para el que existe la tolerancia del 6% — mismo criterio usado en los 5 imports cristalinos previos.

## Resultado

- 80/107 importados (75%). 76/80 (95%) sin dimensiones físicas — la peor cobertura de los 7 lotes
  hasta ahora (peor que LONGi, 86%).
- Verificado: 0 variantes "-R" colaron al catálogo, 0 sin `Pmax_stc`, tecnología correctamente
  `Mono-Si` en las 80.
- `paneles_excluidos_por_ficha_incompleta()`: 1.266 → **1.342** (1.266 + 76).
- Catálogo real: 2.811 → **2.891** paneles.
- Suite completa: **942/942** (1182.71s / ~19m 42s).

## Script de import

`datos/agregar_paneles_sunpower_nrel.py` — mismo esquema de trazabilidad y protección contra
duplicados que los 6 imports anteriores, con los dos filtros de exclusión descritos arriba.
