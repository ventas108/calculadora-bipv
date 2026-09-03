# Ampliación real del catálogo de paneles: 408 módulos Jinko Solar (NREL/SAM + Sandia JPV 2025)

**Fecha**: 3 de septiembre de 2026
**Disparador**: continuación de JA Solar y Trina Solar (`DIAGNOSTICO_CATALOGO_JA_SOLAR_NREL.md`,
`DIAGNOSTICO_CATALOGO_TRINA_NREL.md`). Jinko Solar es el fabricante más grande del mundo por volumen
de embarques (13% del mercado global) y Tier 1 confirmado en el mercado colombiano, con la mejor
cobertura de dimensiones entre los candidatos grandes restantes (67% en el cruce inicial).

## Mismas 2 fuentes, mismo método de cruce normalizado

`PVS_params_translated.csv` (Deville et al. 2025 IEEE JPV) + `CEC Modules.csv` (NREL/SAM), cruzadas por
nombre normalizado (sin puntuación). 470 módulos Jinko con match real.

## Auditoría real: tasa de fallo más alta que Trina, pero mismo mecanismo ya identificado

| Resultado | Cantidad |
|---|---|
| 🔴 Fuera de tolerancia real (>6%) — **excluidos** | 62 de 470 (13.2%) |
| ⚠️ Dentro de tolerancia, a revisar (>2%) | 101 de 470 |
| Sin dimensiones físicas en la fuente (solo área) | 95 de 470 |
| **Importados** | **408** |

13.2% de fallo (vs. 4.3% en Trina) — investigado, mismo mecanismo ya identificado con Trina
`TSM-480DE15V(II)`: módulos **half-cut** con sufijo **"H"** en la nomenclatura de Jinko (ej.
`JKM335M-72H`), donde el paper tradujo `cells_in_series=144` (el conteo físico de medias-celdas) en
vez de la profundidad eléctrica real. Verificado con un caso real: CEC y el paper coinciden en
N_s=144 para `JKM335M-72H` (Voc real=46.9V), pero 46.9V/144=0.33V por celda es físicamente
implausible (una celda de silicio real da ~0.6-0.7V); 46.9V/72=0.65V sí es real — confirma que la
arquitectura real es 2 strings de 72 celdas en paralelo, no 144 en serie recta. Jinko tiene una
proporción mayor de línea half-cut en su catálogo que Trina, de ahí la tasa de fallo más alta — no es
un problema nuevo, es el mismo mecanismo con mayor incidencia.

## Sin bugs nuevos de código esta vez

A diferencia de JA Solar/Trina (bug real de la columna "Tecnologia " con espacio, corregido el mismo
día), este import no encontró ningún bug nuevo — los 2 scripts anteriores ya quedaron corregidos
(sin `.strip()` en el mapa de columnas, con aviso explícito si algo no mapea) y `agregar_paneles_
jinko_nrel.py` reutiliza exactamente el mismo patrón ya verificado. Confirmado: 0 paneles Jinko con
tecnología vacía tras el import.

## Verificación

- `tests/test_comparador_paneles.py::test_paneles_excluidos_por_ficha_incompleta_refleja_el_catalogo_real`
  actualizado: 647 excluidos reales (552 previos + 95 de Jinko, todos por `area_m2=None`).
- Catálogo real: 1.609 (JA Solar + Trina + originales) + 408 (Jinko) = **2.017 paneles**.
- Suite completa: **942/942** (1024.66s / 17 min — más lento por el catálogo aún más grande; escala
  proporcional a lo ya observado con Trina).

## Script de import

`datos/agregar_paneles_jinko_nrel.py` — mismo patrón que JA Solar/Trina, protegido contra duplicados.
