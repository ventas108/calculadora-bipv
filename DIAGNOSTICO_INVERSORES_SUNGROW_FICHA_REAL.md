# 4 inversores Sungrow con ficha mecánica real completa (SG5.0/7.0/8.0/10RT)

**Fecha**: 4 de septiembre de 2026
**Contexto**: primer completado real de un fabricante tras el import masivo CEC/Sandia (2.343
inversores sin datos mecánicos). Se eligió Sungrow con la misma metodología de mercado usada para
paneles.

## Por qué Sungrow

Investigación real de mercado colombiano (misma rigurosidad que paneles): Sungrow tiene **~1.5 GW
ya instalados** en Colombia (plantas utility-scale), **Bemco** nombrado nuevo distribuidor oficial
en 2026 para expandir a residencial/comercial/industrial (100 MW adicionales), y 25 GW entregados
en LatAm. Evidencia más fuerte que Huawei (1.5 GW comprometidos, sin cifra de instalado) o Deye
(entrando recién al mercado). Ya había 1 modelo Sungrow en el catálogo (`SG110CX`, utility-scale
de 110kW) — se buscó completar el segmento comercial/residencial que Bemco está expandiendo ahora.

## Fuente

Ficha oficial real, alojada en el propio dominio de soporte del fabricante (no un revendedor):
`info-support.sungrowpower.com/.../DS_20220818_SG5.0_7.0_8.0_10RT_Datasheet_V11_EN(AU).pdf` —
"SG5.0/7.0/8.0/10RT — Multi-MPPT String Inverter for 1000 Vdc System", versión 11, 2022.

## Los 4 modelos

| Modelo | P_ac nominal | P_dc máx recomendada | N_mppt | Strings/tracker | I_max/tracker |
|---|---|---|---|---|---|
| SG5.0RT | 5.0 kW | 7.5 kWp | 2 | 1 | 12.5 A |
| SG7.0RT | 6.999 kW | 10.5 kWp | 2 | 1* | 12.5 A* |
| SG8.0RT | 8.0 kW | 12 kWp | 2 | 1* | 12.5 A* |
| SG10RT | 10.0 kW | 15 kWp | 2 | 1* | 12.5 A* |

Comunes a los 4: Vdc_max=1100V, tensión de arranque=180V, ventana MPPT=160-1000V.

## Decisión de diseño: asimetría real de MPPT no representable en el esquema

La ficha oficial confirma que en SG7.0RT/8.0RT/10RT el **MPPT1 real soporta 2 strings/25A** y el
**MPPT2 real soporta 1 string/12.5A** (asimétrico, columna "No. of PV strings per MPPT" = "2/1").
El catálogo Excel solo tiene un campo por inversor para "N Strings/Tracker" y "Corriente Máxima
Tracker" (no uno por MPPT individual) — no es un dato faltante, es una limitación real del
esquema. Se optó por el valor **más conservador** (1 string, 12.5 A) para ambos trackers, para que
el chequeo automático de compatibilidad **nunca sobreestime** la capacidad real. La asimetría
completa (y la capacidad extra real del MPPT1) queda documentada explícitamente en `Notas` de cada
fila, para que un ingeniero la verifique y aproveche manualmente en un proyecto real si aplica.

## Verificación

- Los 4 quedan con `Datos completos`="Si" — confirmado `datos_completos=True` vía el loader real.
- `variable_inversor()`: los 4 aparecen en las opciones del optimizador de Fase 4 (no excluidos).
- `inversores_excluidos_por_ficha_incompleta()`: conteo total sin cambio (2.347) — los 4 nuevos NO
  se suman a los excluidos, exactamente lo esperado.
- `filtrar_inversores_compatibles()` verificado en vivo con SG5.0RT contra un panel real
  (ASP-ST1-T40, N_serie=8): `compatible=True`, `strings_max=2` (N_mppt=2 × N_strings_tracker=1) —
  sin ningún dato inventado.
- Catálogo real: 2.451 → **2.455** inversores.
- 4 tests nuevos dedicados (`tests/test_inversores_sungrow_ficha_real.py`), suite completa
  ejecutada tras el cambio.

## Script

`datos/agregar_inversores_sungrow_ficha_real.py` — protegido contra duplicados por (Marca,
Modelo), mismo patrón que el resto de scripts de import.
