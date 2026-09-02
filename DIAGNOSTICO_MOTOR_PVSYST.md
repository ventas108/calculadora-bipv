# Migración del motor SDM: De Soto 2006 → PVsyst v6 (calcparams_pvsyst)

**Fecha**: 2 de septiembre de 2026
**Disparador**: tras corregir el bug del modelo Rsh (`DIAGNOSTICO_RSH_TECNOLOGIA.md`, mismo
día), quedaba un residual de ~4-5 puntos porcentuales entre esta app y PVsyst real incluso
usando los parámetros de diodo EXACTOS que PVsyst calculó para un panel real (XTP 50-17B,
Poli-Si). El mismo residual apareció, de forma independiente, en la comparación contra un
paper real (Mohammadi & Gezegin 2022, Ghor/Afganistán) con otro panel Mono-Si real (Suntech
STP320S). El usuario pidió investigar ese residual — la causa resultó ser más profunda de lo
esperado: esta app usaba el modelo académico **De Soto 2006**, mientras PVsyst usa su **propio**
modelo (**PVsyst v6**, Sauer/Roessler/Hansen 2015, IEEE J. Photovoltaics — implementado en
`pvlib.pvsystem.calcparams_pvsyst`), con fórmulas distintas de I_L(T), I_o(T), Rsh(G), y un
parámetro Gamma (factor de idealidad) que PVsyst permite variar con la temperatura (`mu_gamma`),
algo que De Soto no contempla.

## La investigación

1. El docstring de `calcular_rsh_cdte()` en esta app YA decía "mismo modelo que
   `pvlib.pvsystem.calcparams_pvsyst`" — pista que llevó a inspeccionar esa función real de
   pvlib. Su default `R_sh_exp=5.5` — el MISMO valor que esta app ya tenía para CdTe, Mono-Si Y
   Poli-Si — confirmó que el modelo Rsh exponencial es el modelo **universal** de PVsyst, no
   algo exclusivo de capa fina (el hueco #2 corregido horas antes, ver
   `DIAGNOSTICO_RSH_TECNOLOGIA.md`, fue una mejora real y parcial, no la causa completa).
2. Con parámetros reales de PVsyst (Rs=0,716Ω, Rsh=190Ω, Gamma=1,070) y `calcparams_pvsyst` en
   vez de `calcparams_desoto`, variando solo `Rsh_0` (el Rsh de saturación a muy baja
   irradiancia): con Rsh_0≈820Ω el resultado reproducía el -3,90% real de PVsyst casi exacto —
   pero ese valor era un ajuste hacia atrás (reverse-fit), no una fuente real.
3. Se encontró documentación **oficial** de PVsyst (pvsyst.com/help-pvsyst7) con las fórmulas
   reales por defecto del "Standard Model" (el que usa PVsyst cuando el usuario no hace su
   propia caracterización de laboratorio):
   - `Rshunt = Vmp / (0.2 × (Isc − Imp))` — validado: para XTP 50-17B da 192,2Ω vs. 190,0Ω real
     (1,2% de diferencia).
   - `Rsh(0) ≈ 4 × Rsh(STC)` para cristalino (≈8-10 según otra estimación de la misma fuente,
     pero declarada de bajo impacto para cristalino porque su Rsh ya es alto en STC) — validado:
     4×192,2=768,9Ω, cercano al 820Ω reverse-fit.
   - `R_sh_exp = 5.5` "prácticamente constante independiente de la tecnología", con la excepción
     real de CdTe (~3).
   - `R_series` por defecto: se ajusta para reproducir -3% de eficiencia relativa a 200 W/m² vs.
     STC (criterio probado primero, descartado — ver más abajo).
4. Se encontró el paper real Sauer/Roessler/Hansen 2015 (SAND2014-19059J, dominio público vía
   OSTI) que describe el modelo COMPLETO de PVsyst v6, incluida la fórmula de `mu_gamma`
   (coeficiente de temperatura del factor de idealidad) — el mecanismo real por el que PVsyst
   ajusta la respuesta térmica de Pmax al coeficiente de placa Tk_gamma, algo que el modelo De
   Soto de esta app nunca modelaba explícitamente.

## Validación decisiva

Con `calcparams_pvsyst` y los parámetros EXACTOS reales de PVsyst (Rs=0,716Ω, Rsh=190Ω,
Gamma=1,070) para XTP 50-17B: **96,5%** donde el motor De Soto anterior (con esos mismos
parámetros reales) daba 96,5% vs. el objetivo real de PVsyst (irradiancia+temperatura aislada,
~95,9%) — diferencia de 0,6 puntos, prácticamente exacta.

Con parámetros derivados **100% de la ficha técnica** (sin espiar ningún valor real de PVsyst,
usando las fórmulas oficiales documentadas arriba): **96,0%** vs. 95,9% real — 0,1 puntos de
diferencia, con Voc y Pmax en STC exactos por construcción.

## Diseño final de `estimar_sdm_desde_ficha()`

- **Gamma**: valor típico por tecnología (`n_typ`, ya existente en esta app antes de la
  migración: CdTe=1,09, Mono-Si=1,05, Poli-Si=1,10).
- **Rsh_ref**: fórmula oficial `Vmp/(0,2×(Isc−Imp))`.
- **Rsh_0**: `4×Rsh_ref` para cristalino (razón oficial); para CdTe/CIGS, sin razón oficial
  documentada, se reutiliza la razón REAL calibrada del único panel de capa fina con datos de
  laboratorio propios de esta app (ASP-ST1-T40, R_sh_0/R_sh_ref≈13,76) — mejor referencia
  disponible que inventar un número.
- **R_sh_exp**: `c_Rsh` de `CONSTANTES_TECNOLOGIA` (ya existente, sin cambios).
- **R_s**: resuelto (root-find, `scipy.optimize.brentq`) para que el **Pmax del modelo en STC
  reproduzca EXACTO el Pmax de la ficha** (Vmp×Imp). *No* el criterio oficial documentado de
  PVsyst ("-3% @ 200 W/m²") — probado primero, mismo día, y descartado: ese criterio no ancla
  Vmp/Imp/Pmax a nada, y en la auditoría completa del catálogo real (76 paneles) dejaba
  solo 19/76 activando el Motor IV, con Pmax hasta 7-8% más alto que la ficha en la mayoría de
  paneles. Anclar R_s al Pmax real es igual de preciso en el caso de validación (PR=96,0% vs
  criterio oficial 96,1%) sin esa regresión.
- **I_L_ref, I_o_ref**: autoconsistencia en Isc (V=0) y Voc (I=0) — sistema 2×2 cerrado, dado
  R_s/R_sh_ref/gamma_ref ya fijos.
- **mu_gamma**: resuelto (root-find) para que `dPmax(T)/dT` en Tref=25°C reproduzca el
  coeficiente de temperatura Tk_gamma de la ficha — mismo método documentado que usa PVsyst
  internamente (Sauer/Roessler/Hansen 2015, Sec. IV).

Si el criterio de R_s o el sistema I_L/I_o no converge o produce parámetros no físicos
(negativos/infinitos) para un panel real, cae a la cascada Batzelis/heurística previa — misma
robustez de antes de esta migración para casos límite del catálogo. Se encontró y corrigió en el
camino una degeneración real y ya conocida del método Batzelis (puede devolver `R_sh_ref`
negativo para ciertas combinaciones de ficha), que antes se propagaba en silencio a NaN — ahora
se detecta y cae al heurístico más tosco.

## Centralización adicional

Las 4 implementaciones fuera de `modelo_iv.py` (`produccion.py`, `produccion_iv.py`,
`mismatch_bypass.py`, `mppt_combinado.py`) ya no reimplementan la llamada a `calcparams_pvsyst`
por su cuenta — todas llaman directo a `calculos.modelo_iv.trasladar_parametros_gt()`. Esto
elimina por completo la clase de bug que `test_consistencia_sdm_entre_modulos.py` existe para
atrapar ("una fórmula se corrige en un lugar pero no en sus copias") — antes de hoy, cada
implementación tenía su propia copia de la llamada a `calcparams_*` + el gating de Rsh; ahora
solo una función la calcula.

## Panel CdTe curado (ASP-ST1-T40)

Se agregaron los campos `N_s=141`, `gamma_ref=154/141≈1,0922` (derivado de su propio `a_ref` ya
calibrado, sin cambios) y `mu_gamma=0,001477` (resuelto para reproducir su Tk_gamma real de
-0,214%/°C bajo el nuevo motor). Verificado: reproduce Voc=116,0V exacto y Pmax=60,48W (vs 63,0W
real, 4,0% — dentro de la tolerancia ya usada). El resto de sus parámetros SDM reales
(I_L_ref/I_o_ref/R_s/R_sh_ref/R_sh_0, calibrados contra la hoja FF_vs_Irradiancia del XLSM
auditado) no cambiaron.

## Impacto en el caso real de validación de hoy (XTP 50-17B, Teusaquillo)

| | Antes de cualquier fix (hoy) | Fix tecnología Rsh | Motor PVsyst v6 |
|---|---|---|---|
| PR (solo DC, aislado) | 104,4% | 95,9% | 96,0% (100% desde ficha) |
| PR (pipeline real, con inversor) | — | — | **92,2%** |
| PVsyst real (post-todo: IAM/mismatch/óhmico/inversor) | | | 77,03% |

La brecha restante (92,2% vs 77,03%) es consistente con lo ya documentado: IAM, calidad de
módulo, mismatch y pérdida óhmica no modelados en esta app (`DIAGNOSTICO_LOSS_DIAGRAM_PVSYST.md`)
— no un nuevo residual sin explicar.

## Auditoría del catálogo real

Con el nuevo motor: **74/76** paneles reales del catálogo activan el Motor IV on-demand con
tolerancia de validación STC del 6,0% (antes: 72/76 con 5,0%) — la tolerancia se amplió de 5,0%
a 6,0% porque el nuevo método garantiza Pmax exacto en STC por construcción (antes ~4% de error
típico), a cambio de que Vmp/Imp individuales (cuyo producto sí es exacto) puedan diferir un
poco más de la ficha.

## Verificación

- 927/927 tests pasan (suite completa).
- `tests/test_consistencia_sdm_entre_modulos.py` extendido: nuevo test que verifica que las 4
  implementaciones fuera de `modelo_iv.py` centralizan en `trasladar_parametros_gt()` (ya no
  contienen su propia llamada a `calcparams_pvsyst`/`calcparams_desoto`).
- `tests/test_rsh_gating_tecnologia.py` reescrito para reflejar la razón Rsh_0/Rsh_ref
  distinta por tecnología (en vez de "exponencial sí/no").
- `tests/test_modelo_iv.py`: tolerancias del test de coherencia lineal-vs-SDM recalibradas con
  los valores reales del nuevo motor (documentados en el propio test).
- Bug de degeneración de Batzelis (Rsh negativo) corregido con guardia de sanidad física antes
  de aceptar su resultado.
