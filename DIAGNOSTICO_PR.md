# Diagnóstico del Performance Ratio (PR) — Simulador de Energía

## Definición IEC 61724 (Estándar)

**PR = E_AC / (GlobInc × P_nom_STC)**

Donde:
- **E_AC** = Energía AC producida (kWh)
- **GlobInc** = Irradiación global incidente en el plano del array (kWh/m²)
- **P_nom_STC** = Potencia nominal instalada STC (kW)

Equivalentemente:
- **PR = Yf / Yr**
- **Yf** (Final Yield) = E_AC / P_nom_STC (kWh/kWp)
- **Yr** (Reference Yield) = GlobInc / G_ref = POA_total / 1000 (horas)

## Implementación Actual (energyProduction.ts, línea 315)

```typescript
const performanceRatio = (totalACEnergy / totalDCEnergy) * 100;
```

### PROBLEMA CRÍTICO: El denominador está MAL

El código calcula:
- **PR_actual = E_AC / E_DC**

Esto NO es el Performance Ratio IEC 61724. Esto es simplemente la **eficiencia BOS (Balance of System)**, es decir, la relación entre energía AC y DC. Solo captura las pérdidas post-panel (inversor, cableado AC, etc.), pero **NO incluye**:

1. **Pérdidas por temperatura** (ya incluidas en E_DC porque dcPower usa calculateDCPower con T_cell)
2. **Pérdidas por sombreado** (ya incluidas en adjustedPOA)
3. **Pérdidas por suciedad** (aplicadas en calculateACPower)
4. **Pérdidas por mismatch** (aplicadas en calculateACPower)

El resultado es un PR artificialmente ALTO porque E_DC ya tiene descontadas las pérdidas por temperatura y sombreado.

### Cálculo Correcto IEC 61724:

```
PR = E_AC / (Σ_mes(POA_mes × horas_mes) / 1000 × P_nom_kW)
```

Donde:
- POA_mes = Irradiancia POA promedio del mes (W/m²)
- horas_mes = días × 24 (o mejor: días × horas_sol_pico)
- P_nom_kW = powerRating × quantity / 1000

### Segundo problema: totalDCEnergy se calcula dos veces

Línea 292: `totalDCEnergy += monthly.dcPower * daysInMonths[idx] * 24 / 1000;`

Pero dcPower ya incluye pérdidas por temperatura (calculateDCPower usa calculatePanelEfficiency con T_cell). Entonces totalDCEnergy NO es la energía de referencia STC.

### Tercer problema: systemEfficiency es idéntico al PR

Línea 314: `const systemEfficiency = (totalACEnergy / (totalDCEnergy * 1000)) * 100;`
Línea 315: `const performanceRatio = (totalACEnergy / totalDCEnergy) * 100;`

systemEfficiency tiene un factor ×1000 en el denominador que parece un error de unidades, y performanceRatio es E_AC/E_DC que no es PR.

## Resumen de Errores

| # | Error | Impacto |
|---|-------|---------|
| 1 | PR = E_AC/E_DC en vez de E_AC/(GlobInc × P_nom) | PR inflado ~10-20 pp |
| 2 | totalDCEnergy incluye pérdidas por T° (no es referencia STC) | Denominador reducido |
| 3 | systemEfficiency tiene error de unidades (×1000) | Valor sin sentido |
| 4 | No se calcula Yr (Reference Yield) ni Yf (Final Yield) | Faltan métricas IEC |
| 5 | Pérdidas promediadas aritméticamente (no ponderadas por energía) | Pérdidas inexactas |
| 6 | No hay PR corregido por temperatura (IEC 61724-1:2021) | Falta PR_T |

## Correcciones a Implementar

1. **PR IEC 61724**: PR = E_AC / (Yr × P_nom_kW) donde Yr = Σ(POA_i × h_i) / G_ref
2. **Reference Yield (Yr)**: Calcular correctamente como POA total / 1000
3. **Final Yield (Yf)**: E_AC / P_nom_kW
4. **PR corregido por temperatura (PR_T)**: Ajustar por T_cell vs 25°C
5. **Promediar pérdidas ponderadas por energía** (no aritmético)
6. **Corregir systemEfficiency**: Debería ser E_AC / E_DC (eficiencia BOS)
7. **Agregar Specific Yield**: kWh/kWp/año
8. **Agregar métricas IEC completas**: Yr, Yf, Ya, Lc, Ls
