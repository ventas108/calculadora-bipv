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

El motor real usado por el Streamlit app (`bipv_python/calculos/`, `simulation/`, `pages/`) usa Open-Meteo como fuente de TMY, no `get_pvgis_tmy`, y en los lugares donde sí maneja timestamps tz-aware usa `tz_convert` correctamente (`calculos/escenarios_fase4.py`, `calculos/contrato_sombreado.py`, `calculos/sombras_3d.py`, `pages/9_🗺️_Vista_3D.py`). **La app web que ven los clientes no está afectada por este bug.**

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

## Pendiente — decisión del usuario

1. ~~¿Corregir el timezone en los 4 scripts?~~ → Hecho en los 2 que lo tenían.
2. ¿Recalibrar bifacialidad/pérdidas DC del script para acercarse más a PVsyst, o dejar el +8% bifacial como upside no validado y reportarlo aparte?
3. ¿Regenerar la Ficha Técnica v2 con las cifras corregidas (310.043-334.846 kWh/año según se decida el punto 2)?
4. ¿Commitear y pushear estos cambios?
