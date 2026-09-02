# Bug real: el modelo Rsh de capa fina (CdTe) se aplicaba a silicio cristalino

**Fecha**: 1 de septiembre de 2026
**Disparador**: el usuario corrió PVsyst 8.1.5 en paralelo con esta app, con un panel de
silicio cristalino real del propio catálogo de PVsyst (XTP 50-17B, Sun Tech Solar, Si-poly),
mismo inversor, mismo sitio real (Teusaquillo, Bogotá) — como forma de aislar si el PR>100%
del proyecto Teusaquillo (CdTe) era un problema del panel raro o del motor de la app. PVsyst
dio PR=77,03% (típico); esta app, para el mismo panel/sitio, dio PR=104,4%.

## Camino de la investigación (incluye un error propio, corregido en el camino)

1. **Hipótesis descartada — modelo de temperatura**: cambiar solo la fórmula de T_celda (NOCT
   de esta app vs. Faiman con los mismos Uc=20/Uv=0 de PVsyst) apenas cerró 2 de ~13 puntos
   porcentuales de la brecha. No era la causa principal.
2. **Falsa alarma propia, corregida**: al comparar el factor de idealidad (Gamma) del ajuste
   SDM de esta app contra el de PVsyst para el mismo panel, un error de unidades en el propio
   cálculo de verificación (dividir dos veces por el voltaje térmico) hizo parecer que Gamma
   salía en 36,45 (físicamente imposible) cuando el valor real, con la convención correcta
   (`a_ref` ya almacenado como "n×Ns" adimensional, documentado en el propio código), era 0,94
   — razonablemente cercano al 1,070 real de PVsyst. Se corrigió y se re-auditaron los 76
   paneles reales del catálogo con la fórmula correcta: la mayoría cae en un rango razonable
   (0,48–1,37), sin la falla sistémica que se había reportado por error.
3. **La causa real, confirmada de forma decisiva**: insertando los parámetros EXACTOS que
   PVsyst calculó (Rs=0,716Ω, Rsh=190Ω, Gamma=1,070) directamente en el motor SDM de esta app,
   con T=25°C fijo (para aislar solo el efecto de irradiancia, sin temperatura), el resultado
   seguía siendo una ganancia de +3,2% — donde PVsyst, con esos MISMOS parámetros, midió una
   pérdida real de -3,90%. El problema no estaba en los parámetros ajustados ni en el modelo de
   temperatura — estaba en cómo el motor de esta app responde a la irradiancia por sí sola.

## El bug real

`calculos/modelo_iv.py::calcular_rsh_cdte()` implementa el modelo Rsh exponencial saturado
(Mermoud 2005) que hace que la resistencia shunt SUBA a baja irradiancia — un comportamiento
real, documentado y validado de los paneles CdTe de capa fina (curva de Fill Factor "jorobada",
Batzner et al. 2001: FF sube desde baja luz, hace pico, y baja de nuevo hacia irradiancias
altas). **Ese modelo se aplicaba en las 5 implementaciones del SDM de esta app (`modelo_iv.py`,
`produccion.py`, `produccion_iv.py`, `mismatch_bypass.py`, `mppt_combinado.py`) sin verificar
la tecnología del panel** — se usaba igual para CdTe, CIGS, Mono-Si y Poli-Si.

`datos/tecnologias_bipv.py::CONSTANTES_TECNOLOGIA` ya tenía `c_Rsh=5.5` idéntico para CdTe,
Mono-Si y Poli-Si (CIGS con `c_Rsh=4.0`) — pero nada evitaba que la fórmula exponencial se
aplicara también a silicio cristalino, que no tiene ese comportamiento real: su Rsh real sigue
mucho más de cerca el modelo lineal estándar que `pvlib.pvsystem.calcparams_desoto()` ya calcula
por sí solo (y que las 5 implementaciones descartaban con una variable con guion bajo,
`_rsh_pvlib`/`_`, sin usarla nunca).

## Verificación de la corrección

Con el mismo aislamiento (parámetros de PVsyst, T=25°C fijo, solo irradiancia):

| Modelo de Rsh | Resultado |
|---|---|
| CdTe (el que se usaba para TODAS las tecnologías) | +3,2% (ganancia irreal) |
| Estándar de pvlib (ahora usado para Mono-Si/Poli-Si) | +0,5% |
| PVsyst real | -3,90% |

El fix cierra ~38% de la brecha de irradiancia — real y confirmado, pero no explica el 100% de
la diferencia restante (esperable: pvlib y el motor interno de PVsyst no son la misma
implementación, y siguen faltando por aplicar en la comparación rápida el IAM, calidad de
módulo, mismatch y óhmico que PVsyst sí modela y esta app no, ya documentados en
`DIAGNOSTICO_LOSS_DIAGRAM_PVSYST.md`).

**Resultado end-to-end real** (mismo panel XTP 50-17B, mismo sitio, ajuste Batzelis propio de
esta app, sin IAM/calidad/mismatch/óhmico — comparación simplificada, no la corrida completa):

| | Antes del fix | Después del fix | PVsyst real |
|---|---|---|---|
| PR | 104,4% | **95,9%** | 77,03% |
| E_ac anual | 444 kWh | **407 kWh** | 344,81 kWh |
| Y_f | 739 kWh/kWp/año | **679 kWh/kWp/año** | 575 kWh/kWp/año |

## Corrección aplicada

En las 5 implementaciones, `calcular_rsh_cdte()` ahora solo se llama si
`panel["tecnologia"] in ("CdTe", "CIGS")` — las dos tecnologías de capa fina con `c_Rsh`
definido y comportamiento de Rsh documentado. Para Mono-Si/Poli-Si (y cualquier tecnología
futura que no sea capa fina) se usa el Rsh estándar que `calcparams_desoto()` ya calculaba
internamente y se descartaba.

**Ningún panel CdTe/CIGS cambia de comportamiento** — el modelo exponencial sigue aplicándose
exactamente igual para ellos (verificado con test de regresión anclado a ASP_ST1_T40, el panel
real de Teusaquillo). El cambio real es solo para Mono-Si/Poli-Si.

## Verificación

- 10 tests nuevos/extendidos: `tests/test_rsh_gating_tecnologia.py` (5, incluyendo un panel real
  XTP_50_17B con los parámetros SDM verificados) + `tests/test_consistencia_sdm_entre_modulos.py`
  extendido con el caso Poli-Si además del CdTe existente (5 tests, antes 3).
- La suite de consistencia cruzada (que ya existía para detectar "una fórmula corregida en un
  lugar pero no en sus copias") ahora cubre ambas tecnologías en las 5 implementaciones.
- Suite completa: **927/927**.

## Alcance — qué proyectos reales se ven afectados

Cualquier panel real del catálogo Excel con tecnología Mono-Si o Poli-Si que pase por el ajuste
SDM on-demand (la gran mayoría de los paneles cristalinos del catálogo). Los paneles CdTe/CIGS
(incluido el ASP-ST1-T40 de Teusaquillo) no cambian — para ellos el modelo exponencial siempre
fue el correcto. El PR>100% de Teusaquillo en sí sigue sin explicarse del todo por este fix (es
CdTe, no afectado) — pero confirma que el motor SDM de esta app tenía una fuente real de
optimismo en la respuesta a la irradiancia, independiente del panel específico, que ahora está
corregida para cristalino.
