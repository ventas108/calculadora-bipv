# Ampliación real del catálogo con 137 paneles Risen Energy (NREL/SAM + Sandia JPV 2025)

**Fecha**: 3 de septiembre de 2026
**Fuentes**: las mismas 2 de todos los imports anteriores — NREL/SAM `CEC Modules.csv` y Deville
et al. 2025 IEEE JPV (`PVS_params_translated.csv`, Zenodo 10.5281/zenodo.14173605).

## Por qué Risen Energy (elección basada en mercado real, no en volumen)

Entre los fabricantes restantes con buen volumen (United Renewable Energy 705, LG Electronics 650,
Hyundai Energy Solutions 424, Vietnam Sunergy 412, Phono Solar 293, Mission Solar 236, Boviet Solar
233, Suzhou Talesun 231, Risen Energy 148), se investigó cuál tiene presencia real confirmada en el
mercado colombiano (no solo reputación Tier-1 general):

- **Risen Energy**: proyecto real confirmado — 492 MW suministrados a la planta Guayepo I y II en
  Colombia; 2 distribuidores locales nombrados (Energía Solar Colombia, Ferragro); cobertura
  repetida en prensa especializada colombiana/LatAm.
- Boviet Solar, Phono Solar, Hyundai Energy Solutions: sin distribuidor o proyecto colombiano
  verificable en la búsqueda.

Se eligió Risen Energy por evidencia real de mercado, no por ser el de mayor volumen disponible.

## Auditoría

148 candidatos con match normalizado. 11 excluidos por tolerancia SDM (6%, `validar_sdm_vs_ficha`)
— mismo patrón half-cut ya documentado en Trina/Jinko: familias `RSM120-6` y `RSM144-6` dan
V/celda≈0.33-0.34V (la mitad de lo físicamente plausible, ~0.6-0.65V esperado para Mono-Si) — el
paper tradujo el conteo físico de medias-celdas (120/144) en vez de la profundidad eléctrica real
(60/72). Mismo mecanismo, mismo criterio de exclusión ya validado en 2 imports previos.

Dato adicional verificado (no un bug): 35 de los 137 importados son la línea `RSM60-6-XXXP`
(sufijo "P" = policristalina, potencias 230-275W típicas de módulos de 60 celdas poli de esa
generación) — Risen fabrica ambas tecnologías, confirmado real, no un error de mapeo.

## Resultado

- 137/148 importados (93%). 88/137 (64%) sin dimensiones físicas — mejor cobertura que SunPower
  (95%) y LONGi (86%).
- Verificado: 0 sin `Pmax_stc`, tecnologías `Mono-Si` (102) y `Poli-Si` (35) correctamente
  clasificadas.
- `paneles_excluidos_por_ficha_incompleta()`: 1.342 → **1.430** (1.342 + 88).
- Catálogo real: 2.891 → **3.028** paneles.
- Suite completa: **942/942** (1240.98s / ~20m 40s).

## Script de import

`datos/agregar_paneles_risen_nrel.py` — mismo esquema de trazabilidad y protección contra
duplicados que los 7 imports anteriores.
