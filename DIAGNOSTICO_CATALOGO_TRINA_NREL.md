# Ampliación real del catálogo de paneles: 1.255 módulos Trina Solar (NREL/SAM + Sandia JPV 2025)

**Fecha**: 3 de septiembre de 2026
**Disparador**: continuación del import de JA Solar (`DIAGNOSTICO_CATALOGO_JA_SOLAR_NREL.md`). Se pidió un
sondeo de qué fabricantes tienen mejor posicionamiento real en LatAm para priorizar el siguiente lote —
Trina Solar confirma presencia regional real (oficinas en Santiago de Chile y Ciudad de México, ~500 MW
desplegados en la región), y resultó ser también el pool más grande disponible tras corregir un problema
real de cruce (ver abajo).

## El hallazgo técnico: el cruce por nombre exacto subestimaba el overlap real

El cruce inicial (nombre exacto entre `PVS_params_translated.csv` y `CEC Modules.csv`) solo encontraba 269
módulos Trina — muy por debajo de lo esperado para el fabricante Tier 1 más grande de la lista. La causa:
diferencias de puntuación entre las 2 fuentes (`"Jinko Solar Co. Ltd"` vs `"Jinko Solar Co Ltd"`, `"TSM-
225PA05.38"` vs `"TSM-225PA0538"`). Normalizando (quitando puntuación, minúsculas) el overlap real subió a
**1.312 módulos Trina** (y de paso reveló Jinko, LONGi, Risen y ZNShine, ausentes del cruce anterior).

## Investigación de 2 casos reales antes de confiar en el cruce normalizado

Se temía que la normalización generara colisiones falsas entre productos distintos. Se investigaron 2 casos
reales contra fichas oficiales de Trina descargadas directamente (no resúmenes de buscador):

1. **`TSM-480DE15V(II)`**: CEC coincide EXACTO con la ficha real (Voc=43.2V, Isc=13.92A, Vmp=36.3V,
   Imp=13.23A, 252 celdas). El error está en el paper: tradujo `cells_in_series=126` para una arquitectura
   de alta potencia con strings en paralelo — error de traducción del paper, no de CEC ni del cruce.
2. **`TSM-320PD1405C`**: CEC reporta Isc=12.0A; la ficha oficial real de la familia PD14 (320W) da Isc=9.10A
   — 32% de diferencia. Es un dato propio de CEC que no coincide con el fabricante para esa fila específica
   — tampoco es un problema del cruce normalizado.

**Conclusión de la investigación**: la diferencia de puntuación, por sí sola, NO es señal de colisión — de
960 pares con ese patrón, solo 57 fallan la auditoría física real (los otros 903 pasan limpio). El chequeo
de tolerancia (`validar_sdm_vs_ficha`, 6%) atrapa los casos problemáticos sin importar su causa exacta.

## Auditoría real y resultado del import

| Resultado | Cantidad |
|---|---|
| 🔴 Fuera de tolerancia real (>6%) — **excluidos** | 57 de 1.312 |
| ⚠️ Dentro de tolerancia, a revisar (>2%) | 280 de 1.312 |
| Sin dimensiones físicas en la fuente (solo área) | 437 de 1.312 |
| **Importados** | **1.255** |

## Bug real encontrado y corregido: columna "Tecnologia" con espacio, escrita en blanco

Al escribir las 1.255 filas (y, se descubrió después, también las 278 de JA Solar), el script construía el
mapa de columnas con `.strip()` sobre los encabezados leídos del Excel — pero el encabezado real de la
columna que usa el cargador de producción es `"Tecnologia "` (con un espacio al final, un typo histórico
del archivo). Al stripear, la clave quedaba `"Tecnologia"` (sin espacio), que nunca coincidía con la clave
`"Tecnologia "` del diccionario de cada fila — la columna se escribía en blanco, **sin ningún aviso**,
tanto para JA Solar como para Trina.

**Alcance real**: 1.533 filas (278 JA Solar + 1.255 Trina) quedaron sin tecnología asignada en la columna
que el cargador de producción realmente lee — `cargar_catalogo_paneles()` mostraba `tecnologia='nan'` para
todas ellas. La columna gemela con tilde (`"Tecnología"`, sin espacio, sí escrita correctamente) tenía el
dato correcto pero el cargador nunca la usaba en la práctica porque la primaria "existía" (vacía) y el
`.get()` de pandas no cae al respaldo cuando la clave está presente con NaN.

**Corregido en 2 partes**: (1) se reparon en el Excel real las 1.533 filas ya escritas, copiando el valor
correcto desde la columna con tilde; (2) se corrigieron ambos scripts de import
(`agregar_paneles_ja_solar_nrel.py`, `agregar_paneles_trina_nrel.py`) para construir el mapa de columnas
SIN `.strip()`, y se agregó un aviso explícito (`AVISO: columna '...' no encontrada`) si algún nombre de
columna del diccionario de fila no encuentra su columna real — para que un problema similar nunca vuelva a
pasar en silencio.

## Verificación

- Re-ejecutar ambos scripts de import ahora es idempotente y confirma "Agregados: 0 / Ya existían: N" sin
  ningún aviso de columna faltante — verificado para ambos.
- `tests/test_comparador_paneles.py::test_paneles_excluidos_por_ficha_incompleta_refleja_el_catalogo_real`
  actualizado: 552 excluidos reales (115 JA Solar + 437 Trina, ambos por `area_m2=None`, ninguno por
  `Pmax_stc`).
- Catálogo real: 76 (original) + 278 (JA Solar) + 1.255 (Trina) = **1.609 paneles**, todos con tecnología
  correctamente asignada (verificado: 0 con `tecnologia` vacía tras la reparación).
- Suite completa: **942/942** (785s / 13 min — más lento que antes por el catálogo 4.5x más grande;
  `comparar_paneles()` con el catálogo completo mide 89.4s reales, contra 20.8s con 285 paneles).
