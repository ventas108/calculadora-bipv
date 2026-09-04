# Diagnóstico: Bug de timezone en TMY de PVGIS (scripts de análisis Urabá)

**Fecha:** 26-ago-2026
**Origen:** comparación manual contra un resultado de PVsyst para el proyecto Agrivoltaico Urabá (220,32 kWp DC, 306× JA Solar JAM66D46-720/LB, 2× Growatt MAX 100KTL3 LV).

## El bug

En `bipv_python/scripts/barrido_dcac_uraba.py` y `bipv_python/scripts/comparar_alt_b_uraba.py`:

```python
tmy, meta = pvlib.iotools.get_pvgis_tmy(LAT, LON, map_variables=True)[:2]
tmy.index = pd.date_range("2023-01-01", periods=len(tmy), freq="h", tz="America/Bogota")
```

`get_pvgis_tmy` devuelve el índice en **UTC**. La línea de arriba no convierte esa hora a hora local — **re-etiqueta** la fila N como si ya fuera la hora local N (asume implícitamente que UTC == America/Bogota). Bogotá es UTC−5, así que cada valor de irradiancia queda emparejado con la posición solar de una hora que no le corresponde (desfase de 5h).

**Fix correcto:**
```python
tmy.index = tmy.index.tz_convert("America/Bogota")
```

## Verificación (cierre físico GHI = DNI·cosZ + DHI)

Con el bug:
- GHI real (suma anual): 1.683,0 kWh/m²
- GHI reconstruida a partir de DNI·cosZ+DHI con la posición solar de cada timestamp: 1.383,2 kWh/m² → **inconsistente** (confirma el desfase)

Con el fix (`tz_convert`):
- GHI real: 1.683,0 kWh/m²
- GHI reconstruida: 1.683,6 kWh/m² → consistente

## Impacto medido (proyecto Urabá 220,32 kWp, TILT=10°, AZ=180°, albedo=0.20)

| | Con bug | Corregido (Haydavies) | Corregido (Perez) |
|---|---|---|---|
| POA anual (kWh/m²) | 1.363,0 | 1.704,1 | 1.716,1 |
| E_ac anual (2×100kW, +8% bifacial fijo, 8% pérd. DC, η_inv 98,2%) | 278.591 kWh | 345.729 kWh | 347.978 kWh |
| PR (sobre POA propio) | 92,77% | 92,08% | 92,04% |

El bug subestimaba la producción anual del script en **~20-25%**.

## Contraste contra PVsyst (resultado real del usuario, misma config física, mismo TMY PVGIS)

PVsyst: E_ac = 315.074 kWh/año, Yield = 1.421 kWh/kWp/año, PR = 82,78% → GlobInc implícito (Yf/PR) = **1.716,6 kWh/m²/año**.

El POA corregido con modelo Perez (1.716,1) coincide casi exactamente con el GlobInc implícito de PVsyst (1.716,6) — confirma que el bug de timezone era la causa raíz de la discrepancia grande, no una diferencia de modelo de transposición.

**Lo que queda como diferencia de supuestos (no bug):** con POA ya corregido, el script da 347.978 kWh (+10,5% vs PVsyst) usando +8% bifacial fijo y 8% pérdidas DC combinadas. PVsyst, con PR=82,78%, está aplicando un derate total mayor (~17%) que el ~10% neto de este script. Pendiente decidir si se ajustan supuestos de bifacialidad/pérdidas DC del script para acercarse más a PVsyst, o si PVsyst está siendo conservador.

## Alcance — qué SÍ y qué NO está afectado

Busqué `get_pvgis_tmy` en todo el repo. Solo 4 archivos lo usan, todos scripts sueltos de análisis/generación de entregables, **ninguno es el motor de producción real de la app**:

- `bipv_python/scripts/barrido_dcac_uraba.py` — bug confirmado y verificado arriba
- `bipv_python/scripts/comparar_alt_b_uraba.py` — mismo patrón de código, bug presente (no verificado numéricamente todavía, pero es el mismo código)
- `scripts/generar_plan_bipv.py` — mismo patrón, **sin verificar todavía**
- `scripts/generar_plan_maestro_completo.py` — mismo patrón, **sin verificar todavía**

**Corrección (26-ago-2026, verificado corriendo el motor real):** el motor real usado por el Streamlit app (`calculos/solar.py::obtener_tmy_pvgis()`) **sí usa PVGIS** (no Open-Meteo como se dijo antes en esta misma nota — error de esta misma investigación, corregido tras revisar el código). La diferencia importante es CÓMO maneja el tiempo: parsea `time(UTC)` con `utc=True` y solo cambia el año (a 2001) sin tocar hora/tz — el índice queda correctamente tz-aware en UTC. `calcular_poa()` calcula la posición solar sobre ESE MISMO índice UTC (`loc.get_solarposition(tmy.index)`), así que irradiancia y posición solar quedan siempre correctamente emparejadas — **nunca reetiqueta, nunca tiene el desfase de 5h**. Es el mismo patrón correcto que ya usan `calculos/escenarios_fase4.py`, `calculos/contrato_sombreado.py`, `calculos/sombras_3d.py` y `pages/9_🗺️_Vista_3D.py`. **La app web que ven los clientes no tiene este bug**, aunque sí use PVGIS.

## Validación adicional: motor real de la app corrido para este proyecto (26-ago-2026)

Además de los scripts sueltos, se corrió el pipeline real (`calculos/solar.py::calcular_poa()` con el modelo bifacial `infinite_sheds` de pvlib + `calculos/produccion.py::simular_produccion_anual()`) para el mismo proyecto, con los mismos parámetros bifaciales validados contra PVsyst (altura 3,0 m, GCR 0,39, ancho colector 2,606 m, albedo 0,20, φ=0,80), panel sin SDM completo en catálogo (usa el modelo fallback `Pmax=Pmax_stc×G/1000×(1+γΔT)`, `factor_pr_mismatch=0,92` como estimado manual):

| | App real (motor de la calculadora) | PVsyst | Diferencia |
|---|---|---|---|
| Bifacial | 349.496 kWh/año | 339.033 kWh/año | **+3,1%** |
| Monofacial | 320.838 kWh/año | 315.074 kWh/año | **+1,8%** |

Más optimista que los scripts corregidos (334.846/310.037, a −1,2%/−1,6% de PVsyst). Causa: el flujo de trabajo que el propio manual recomienda para proyectos agrivoltaicos (`base_conocimiento_asistente.md`, sección 2) **salta la página 5b Motor Óptico**, así que no se aplica IAM (~−2,35% según el diagrama de PVsyst) ni soiling. Nota positiva: el PR de la app (84,9%) usa como referencia la irradiancia bifacial total (frontal+trasera), por lo que ya es comparable al "PR Bifacial" correcto de PVsyst (81,99%), no al PR estándar inflado (89,08%) — la app no tiene el problema de PR inflado que sí tiene el reporte estándar de PVsyst.

**Confirmación (26-ago-2026):** se corrió la misma app con IAM agregado (reutilizando `iam_ashrae()` de Motor Óptico sobre la descomposición direct/diffuse informativa de `calcular_poa()`, aplicado como derate multiplicativo sobre `poa_global` bifacial real para no perder la ganancia trasera). Resultado: POA global 1.868,9→1.797,8 kWh/m² (−3,80%, algo mayor que el −2,35% de PVsyst por la simplificación de aplicar el mismo factor también a la componente trasera), **E_ac = 336.662 kWh/año → −0,70% vs PVsyst** (339.033). Cierra casi por completo el +3,1% de brecha, incluso mejor que los scripts corregidos (−1,2%). Confirma que el IAM faltante era la causa dominante del gap.

**Recomendación:** el flujo agrivoltaico recomendado en el manual del asistente debería incluir Motor Óptico (IAM) — sin él, la app sobreestima producción ~3% para este tipo de proyecto. Pendiente decidir si se actualiza el manual/flujo, y si se recalculan los entregables (Ficha v2.1, Informe Final) con este número más preciso (336.662 en vez de 334.846 — diferencia de 1.816 kWh/año, no material para el caso financiero, pero más exacto).

## Desglose crudo de PVsyst (bifacial) — evidencia de auditoría

Export VC0 (diagrama de pérdidas) de la corrida bifacial de PVsyst, verificado línea por línea (cada etapa se recalculó a partir de la anterior — cierra exacto hasta 339.033 kWh sin ningún salto sin explicar):

```
GlobHor  1.683,0 kWh/m²  (irradiación horizontal global)
  +1,979% (incidencia en plano)      → GlobInc  1.716,3 kWh/m²
  -0,201% (sombreados cercanos)      →          1.713   kWh/m²
  -2,351% (IAM global)               →          1.673   kWh/m²
  +0,025% (reflejo frontal)          →          1.673,0 kWh/m²  ← lado frontal final

Lado trasero (bifacial):
  GlobGnd 1.000,4 kWh/m² (incidente en tierra, área ref. 2.386,5 m²)
  -80,000% (pérdida reflexión suelo = albedo 0,20)   → 200,1 kWh/m²
  -63,640% (factor de vista trasero)                  → 181,5 kWh/m²
  +2,220% (cielo difuso trasero)                       → 185,5 kWh/m²
  +0,002% (haz directo trasero)                        → 185,5 kWh/m²
  -5,000% (sombreados posteriores)                     → 176,2 kWh/m²  = GlobBak
  × 80,0% factor de bifacialidad (φ)                   → 141,0 kWh/m²  usable

GlobEff = 1.673,0 (frontal) + 141,0 (trasero) = 1.814,0 kWh/m²
Energía en colectores (956,8 m² × 1.814,0 kWh/m² ≈ 1.735.529 kWh) × 23,20% eficiencia STC
  → EArrNom 402.596 kWh
  -0,597% (nivel de irradiancia)   → 400.192 kWh
  -6,517% (temperatura)            → 374.111 kWh
   0,000% (sombreado eléctrico)    → 374.111 kWh
  -3,000% (calidad de módulo)      → 362.888 kWh
  -2,100% (mismatch módulos/strings)→ 355.267 kWh
  -0,778% (mismatch irradiancia trasera) → 352.505 kWh
  -0,988% (pérdida óhmica)         → 349.024 kWh  = EArrMPP
  -2,850% (eficiencia inversor)    → 339.076 kWh
  -0,007% (Pmax inversor)          → 339.052 kWh
  -0,006% (umbral de potencia)     → 339.033 kWh  = EOutInv = E_Grid (final)
```

Verificaciones cruzadas: GlobInc (1.716,3) ≈ POA corregido del script (1.716,1); ReflLss −80,000% confirma exacto el albedo 0,20 usado; factor de bifacialidad 80,0% confirma exacto φ=0,80 de la ficha JA Solar. Ningún salto de la cascada queda sin explicar — el dato es consistente y auditable.

## Consecuencia concreta

La **Ficha Técnica Preliminar Agrivoltaico Urabá v2** (`entregables/generar_ficha_uraba_docx.py`, ya generada y entregada) usó `comparar_alt_b_uraba.py`/`barrido_dcac_uraba.py` para sus cifras de producción (≈278.600 kWh/año, 1.265 kWh/kWp·año). Esas cifras están subestimadas por el bug — la producción real esperada (con POA corregido) ronda 345.000-348.000 kWh/año antes de recalibrar supuestos de pérdidas contra PVsyst.

## Corrección aplicada (26-ago-2026)

Se corrigieron `barrido_dcac_uraba.py` y `comparar_alt_b_uraba.py`:
1. `tmy.index = tmy.index.tz_convert("America/Bogota")` en vez de re-etiquetar con `pd.date_range(...)`.
2. Se agregó pérdida IAM (ASHRAE, b0=0,05 vidrio estándar liso, + factor difusa 0,95 IEC 61853-3) reutilizando `iam_ashrae()` de `calculos/motor_optico.py` — no se escribió una fórmula nueva.

`generar_plan_bipv.py` y `generar_plan_maestro_completo.py` **no tenían el bug ejecutándose**: las líneas que hicieron match con `get_pvgis_tmy`/`date_range` ahí son texto dentro de strings que el script escribe como contenido de un documento (ejemplo de código para un manual), no código que se ejecuta. Uno de esos ejemplos ni siquiera es de Colombia (`tz="America/Santiago"`, Chile). No requieren cambio.

### Resultado tras el fix (2× Growatt MAX 100KTL3 LV, ratio 1,10 — mismo caso que corrió el usuario en PVsyst)

| | Con bug (antes) | Corregido (con bifacial +8%) | Corregido sin bifacial (comparable a PVsyst) | PVsyst (monofacial) |
|---|---|---|---|---|
| E_ac anual | 278.591 kWh | 334.846 kWh | **310.043 kWh** | **315.074 kWh** |

Sin el +8% bifacial (que PVsyst no está modelando — ver hallazgo de la sección anterior), la calculadora corregida queda **1,6% por debajo** de PVsyst — diferencia pequeña y explicable por modelado de pérdida por nivel de irradiancia (~0,71% en PVsyst, que el script sigue sin modelar) y pequeñas diferencias en el resto de la cascada. Ya no hay brecha grande sin explicar.

Verificado con la suite completa de tests (`pytest tests/`): 636/636 passed sin regresiones (estos scripts de `scripts/` no están cubiertos por la suite, es verificación de que no se rompió nada del motor compartido que sí importan, `calculos.motor_optico`).

**Nota:** los cambios están en el working tree local, sin commitear ni pushear todavía.

## Validación bifacial (26-ago-2026)

El usuario corrió PVsyst en modo bifacial con los inputs derivados del plano de disposición real
(`entregables/Plano_Disposicion_Uraba_32x100.pdf`): altura 3,0 m, pitch 6,6 m (huella matriz 2,6 m +
corredor de cultivo 4,0 m), GCR≈0,39, albedo 0,20 (pasto verde), φ=0,80 (ficha oficial JA Solar).

Resultado PVsyst bifacial: E_ac=339.033 kWh/año, Yield=1.529 kWh/kWp, PR=89,08% (estándar, Yr
solo-frontal — inflado, efecto conocido en bifaciales), PR Bifacial=81,99% (Yr con GlobEff
frontal+trasero, comparable a monofacial). Ganancia bifacial real: **+7,60%** sobre el caso
monofacial de PVsyst (315.074 kWh/año).

Verificación cruzada: Yr implícito de PR=89,08% (1.716,4 kWh/m²) coincide con el POA frontal ya
validado en la corrida monofacial (1.716,1-1.716,6) — confirma que el lado frontal no cambió entre
corridas, como debía ser.

Contra la calculadora (mismo caso, 2×Growatt 100kW): 334.846 kWh/año (con el supuesto plano de +8%)
vs 339.033 kWh/año de PVsyst → diferencia de solo **-1,2%**. El supuesto de +8% bifacial queda
**validado** (la física real de PVsyst da +7,6%, muy cerca del supuesto plano).

## Pendiente — decisión del usuario

1. ~~¿Corregir el timezone en los 4 scripts?~~ → Hecho. Commiteado y pusheado (`0fe3edd4`).
2. ~~¿Recalibrar o validar la bifacialidad +8%?~~ → Validada contra PVsyst bifacial real: +7,6% físico vs +8% supuesto, -1,2% de diferencia final. Commiteado (`73ff51ad`).
3. ~~¿Regenerar la Ficha Técnica v2 y el Informe Final?~~ → Hecho, incluyendo corrección de TRM (4.000 hardcodeado → 3.118,24 real, vía la misma fuente que usa `trm_utils.py`). Commiteado (`87f74afa`, `81ca8935`).
4. ~~¿Motor real sin IAM vs con IAM?~~ → Confirmado: sin IAM +3,1% vs PVsyst; con IAM (Motor Óptico) −0,70%. La brecha era casi enteramente el IAM faltante. ~~Pendiente decidir: actualizar el flujo recomendado del manual...~~ → Hecho: Motor Óptico ahora es obligatorio en el flujo agrivoltaico recomendado (sección 2 del manual del asistente), commiteado (`9806895a`).
5. ~~¿Verificar `generar_plan_bipv.py` y `generar_plan_maestro_completo.py` a fondo?~~ → Hecho (4-sep-2026), lectura completa de ambos archivos. Confirmado con certeza: ninguno ejecuta pvlib/pandas real, son generadores de documentos Word (solo importan `docx`; todo el código pvlib/pandas, incluido `get_pvgis_tmy`/`get_solarposition`, vive dentro de strings pasados a helpers `cod()`/`codigo()` que se escriben como texto de ejemplo en el `.docx`, nunca se ejecuta). `generar_plan_maestro_completo.py` no tiene ni siquiera el patrón buggy como texto de ejemplo (cero ocurrencias de `date_range`/`tz_convert`/`tz_localize`), corrigiendo lo que decía esta nota antes. Sin otros bugs reales ni valores mágicos relevantes (las constantes tipo `FACTOR_CO2`/`CIUDADES_COLOMBIA` que aparecen son también contenido textual de ejemplo, para archivos que el plan *propone crear*, no las constantes reales de la app). No requieren fix.
6. ~~Este archivo está sin commitear/pushear todavía.~~ → Nota desactualizada (encontrada en auditoría, 27-ago-2026): el archivo está commiteado desde hace tiempo (último commit que lo tocó: `9c11f9c9`), `git status` limpio. Corregido para no confundir a futuras lecturas.
