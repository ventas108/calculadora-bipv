# Análisis del Problema: Irradiancia PVWatts vs PVGIS

## Diagnóstico

### Heatmap PVGIS (IrradianceHeatmap.tsx):
- Consulta: `/api/pvgis/MRcalc?lat=...&lon=...&horirrad=1`
- Respuesta: `H(h)_m` = irradiación horizontal mensual en kWh/m²
- Cálculo: Suma de promedios mensuales → GHI anual (kWh/m²/año)
- **Valores típicos Colombia: 1400-1900 kWh/m²/año** ✓

### Heatmap PVWatts (PVWattsSatellite.tsx):
- Los marcadores muestran `specificYield` (kWh/kWp/año), NO GHI
- `specificYield` = annualAC / system_capacity
- **Valores típicos Colombia: 1100-1500 kWh/kWp/año** ← ESTOS son los que ve el usuario
- El GHI real se obtiene con tilt=0 pero NO se muestra en los marcadores

### El problema:
1. Los marcadores del mapa PVWatts muestran **Specific Yield** (producción AC por kWp)
2. Los marcadores del mapa PVGIS muestran **GHI** (irradiación solar horizontal)
3. Son métricas DIFERENTES que no se pueden comparar directamente
4. Specific Yield siempre será menor que GHI porque incluye pérdidas del sistema

### Solución:
Los marcadores del mapa PVWatts deberían mostrar **GHI** (annualGHI) para ser comparables con PVGIS.
El GHI ya se calcula correctamente en getPVWattsQuickEstimate (con tilt=0).
Solo hay que cambiar qué se muestra en los marcadores y estadísticas.

Además, las estadísticas de la región (Promedio, Máximo, Mínimo, Mediana) también usan specificYield.
Deben cambiarse a annualGHI.
