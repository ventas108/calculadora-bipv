# Ampliación real del catálogo con 99 paneles ZNSHINE (NREL/SAM + Sandia JPV 2025)

**Fecha**: 3 de septiembre de 2026
**Fuentes**: las mismas 2 de todos los imports anteriores — NREL/SAM `CEC Modules.csv` y Deville
et al. 2025 IEEE JPV (`PVS_params_translated.csv`, Zenodo 10.5281/zenodo.14173605).

## Por qué ZNSHINE (2ª iteración de la elección de mercado)

Se evaluó primero LG Electronics como candidato (proyecto real confirmado: Universidad EAN,
Bogotá, instalación NeON2 operativa). El usuario objetó, correctamente: LG salió del negocio de
fabricación de paneles solares en 2022 — sin fabricante activo, no hay garantía ni reposición real
para un modelo específico hoy. Se descartó el candidato.

Se investigaron después Talesun, AXITEC, Suntech, GCL y ZNSHINE. **ZNSHINE fue el único con
evidencia sólida y verificable de presencia real en Colombia**:

- Oficina propia confirmada en Bogotá (Cra.15#97-40, of.406, +57 316 581 1899).
- 6 distribuidores colombianos nombrados y activos: Energitel Solar, Emergente Energía Sostenible,
  Ferragro, Solar On Colombia, Eco Green Solar, Colpilastiendasolar — vendiendo módulos de 200W a
  730W en Bogotá, Medellín, Cali, Barranquilla y más.
- Fabricante **actualmente activo** (a diferencia de LG) — sin el riesgo de garantía señalado.
- Aparece directamente en el listado real de marcas Tier-1 que comercializan los mayoristas
  colombianos en 2026, junto a los 6 fabricantes ya incorporados al catálogo (Jinko, LONGi, Trina,
  Canadian Solar, JA Solar, Risen Energy).

Talesun, AXITEC, Suntech y GCL no mostraron evidencia comparable (GCL solo tuvo 1 distribuidor
mencionado, más débil que la red confirmada de ZNSHINE).

## Auditoría

99 candidatos con match normalizado. **0 excluidos** por tolerancia SDM (6%,
`validar_sdm_vs_ficha`) — el lote más limpio junto con LONGi.

## Resultado

- 99/99 importados (100%). 76/99 (77%) sin dimensiones físicas.
- Verificado: 0 sin `Pmax_stc`, tecnología correctamente `Mono-Si` en las 99.
- `paneles_excluidos_por_ficha_incompleta()`: 1.430 → **1.506** (1.430 + 76).
- Catálogo real: 3.028 → **3.127** paneles.
- Suite completa: **942/942** (1270.26s / ~21m 10s).

## Script de import

`datos/agregar_paneles_znshine_nrel.py` — mismo esquema de trazabilidad y protección contra
duplicados que los 8 imports anteriores.
