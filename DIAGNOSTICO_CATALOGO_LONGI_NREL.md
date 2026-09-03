# Ampliación real del catálogo de paneles: 244 módulos LONGi (NREL/SAM + Sandia JPV 2025)

**Fecha**: 3 de septiembre de 2026
**Disparador**: cierre de la ronda de fabricantes Tier 1 confirmados como dominantes en el mercado
colombiano — con JA Solar, Trina Solar, Jinko Solar y Canadian Solar ya importados, LONGi es el 5° y
último de los 5.

## Mismas 2 fuentes, mismo método de cruce normalizado

`PVS_params_translated.csv` (Deville et al. 2025 IEEE JPV) + `CEC Modules.csv` (NREL/SAM), cruzadas por
nombre normalizado. Nombre legal real del fabricante en ambas fuentes: "LONGi Green Energy Technology
Co Ltd". 244 módulos con match real.

## Auditoría real: el único fabricante con cero exclusiones eléctricas

| Resultado | Cantidad |
|---|---|
| 🔴 Fuera de tolerancia real (>6%) | **0 de 244** |
| ⚠️ Dentro de tolerancia, a revisar (>2%) | **0 de 244** |
| Sin dimensiones físicas en la fuente (solo área) | **209 de 244 (86%)** |
| **Importados** | **244 (todos)** |

De los 5 fabricantes importados hoy (JA Solar, Trina, Jinko, Canadian Solar, LONGi), LONGi es el único
sin ninguna exclusión por tolerancia eléctrica — ni siquiera desviaciones menores (>2%). A cambio, tiene
la tasa de cobertura de dimensiones más baja de los 5 (86% sin `Length`/`Width`, contra 81% de Canadian
Solar, 41% de JA Solar, 35% de Trina, 23% de Jinko) — consistente con el 14% de cobertura ya observado
en el sondeo inicial de mercado, verificado real en la fuente.

## Sin bugs nuevos de código

Reutiliza el mismo patrón ya corregido (sección 39 del manual). Confirmado: 0 paneles LONGi con
tecnología vacía tras el import.

## Verificación

- `tests/test_comparador_paneles.py::test_paneles_excluidos_por_ficha_incompleta_refleja_el_catalogo_real`
  actualizado: 1.166 excluidos reales (957 previos + 209 de LONGi, todos por `area_m2=None`).
- Catálogo real: 2.397 (previos) + 244 (LONGi) = **2.641 paneles**.
- Suite completa: **942/942** (1133.28s / 19 min).

## Cierre de la ronda de 5 fabricantes Tier 1

Con este import quedan cubiertos los 5 fabricantes confirmados como dominantes en el mercado
colombiano: Jinko Solar (408), LONGi (244), Trina Solar (1.255), Canadian Solar (380) y JA Solar (278)
— 2.565 paneles reales de marcas Tier 1, sumados a los 76 originales del catálogo.

## Script de import

`datos/agregar_paneles_longi_nrel.py` — mismo patrón que los 4 anteriores, protegido contra
duplicados.
