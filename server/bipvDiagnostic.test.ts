/**
 * Tests unitarios para client/src/lib/bipvDiagnostic.ts
 * Módulo de Diagnóstico BIPV — Evaluación de Sistemas Instalados
 */
import { describe, it, expect } from 'vitest';
import {
  calculateMulcueExpected,
  integratePVGISData,
  integratePVWattsData,
  calculateAnnualSummary,
  compareBIPVPerformance,
  estimateGHIFromLatitude,
  estimateTempFromLatitude,
  type BIPVPanelConfig,
  type BIPVSiteConfig,
  type BIPVFieldMeasurement,
  type BIPVMonthlyExpected,
} from '../client/src/lib/bipvDiagnostic';

// ============================================================
// Fixtures
// ============================================================

function makePanel(overrides: Partial<BIPVPanelConfig> = {}): BIPVPanelConfig {
  return {
    name: 'Test Panel 400W',
    powerRating: 400,
    efficiency: 20.5,
    tempCoeff: -0.36,
    noct: 45,
    area: 2.0,
    quantity: 10,
    yearsInstalled: 0,
    annualDegradation: 0.5,
    ...overrides,
  };
}

function makeSite(overrides: Partial<BIPVSiteConfig> = {}): BIPVSiteConfig {
  return {
    latitude: 6.25,
    longitude: -75.56,
    siteName: 'Medellín Test',
    tiltField: 10,
    azimuthField: 0,
    shadowFactor: 1.0,
    installationType: 'roof_tilted',
    ...overrides,
  };
}

function makeField(monthly: (number | null)[], annual?: number | null): BIPVFieldMeasurement {
  return {
    monthlyProduction_kWh: monthly,
    annualProduction_kWh: annual ?? (monthly.some(v => v !== null) ? monthly.reduce<number>((s, v) => s + (v ?? 0), 0) : null),
  };
}

function makePVGISMonthly() {
  return Array.from({ length: 12 }, (_, i) => ({
    month: i + 1,
    productionAC_kWh: 400 + Math.sin(i) * 50,
    irradiationPOA_kWhm2: 140 + Math.sin(i) * 20,
    temperature: 22 + Math.sin(i) * 3,
  }));
}

function makePVWattsMonthly() {
  return Array.from({ length: 12 }, (_, i) => ({
    month: i + 1,
    ac_kWh: 420 + Math.cos(i) * 40,
    dc_kWh: 450 + Math.cos(i) * 45,
    poa_kWhm2: 150 + Math.cos(i) * 15,
    tamb_C: 23 + Math.cos(i) * 2,
    tcell_C: 35 + Math.cos(i) * 3,
  }));
}

// ============================================================
// calculateMulcueExpected
// ============================================================

describe('calculateMulcueExpected', () => {
  it('devuelve 12 registros mensuales', () => {
    const result = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    expect(result).toHaveLength(12);
  });

  it('cada registro tiene los campos requeridos', () => {
    const result = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    for (const m of result) {
      expect(m.month).toBeGreaterThanOrEqual(1);
      expect(m.month).toBeLessThanOrEqual(12);
      expect(m.monthName).toBeTruthy();
      expect(m.mulcue_ac_kWh).toBeGreaterThan(0);
      expect(m.mulcue_pr).toBeGreaterThan(0);
      expect(m.mulcue_pr).toBeLessThanOrEqual(1);
      expect(m.mulcue_cellTemp).toBeGreaterThan(0);
      expect(m.pvgis_ac_kWh).toBeNull();
      expect(m.pvwatts_ac_kWh).toBeNull();
      expect(m.expected_ac_kWh).toBe(m.mulcue_ac_kWh);
    }
  });

  it('producción anual es razonable para 4 kWp en Medellín', () => {
    const result = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    const annual = result.reduce((s, m) => s + m.mulcue_ac_kWh, 0);
    // 4 kWp × ~1200-1600 kWh/kWp/año → 4800-6400 kWh/año
    expect(annual).toBeGreaterThan(3000);
    expect(annual).toBeLessThan(8000);
  });

  it('degradación reduce la producción', () => {
    const panelNew = makePanel({ yearsInstalled: 0 });
    const panelOld = makePanel({ yearsInstalled: 10, annualDegradation: 1.0 });
    const resultNew = calculateMulcueExpected(panelNew, makeSite(), 1750, 22);
    const resultOld = calculateMulcueExpected(panelOld, makeSite(), 1750, 22);
    const annualNew = resultNew.reduce((s, m) => s + m.mulcue_ac_kWh, 0);
    const annualOld = resultOld.reduce((s, m) => s + m.mulcue_ac_kWh, 0);
    expect(annualOld).toBeLessThan(annualNew);
  });

  it('factor de sombra reduce la producción', () => {
    const siteNoShadow = makeSite({ shadowFactor: 1.0 });
    const siteShadow = makeSite({ shadowFactor: 0.7 });
    const resultClean = calculateMulcueExpected(makePanel(), siteNoShadow, 1750, 22);
    const resultShaded = calculateMulcueExpected(makePanel(), siteShadow, 1750, 22);
    const annualClean = resultClean.reduce((s, m) => s + m.mulcue_ac_kWh, 0);
    const annualShaded = resultShaded.reduce((s, m) => s + m.mulcue_ac_kWh, 0);
    expect(annualShaded).toBeLessThan(annualClean);
    // La reducción debe ser proporcional al factor de sombra
    const ratio = annualShaded / annualClean;
    expect(ratio).toBeCloseTo(0.7, 1);
  });

  it('mayor GHI produce más energía', () => {
    const resultLow = calculateMulcueExpected(makePanel(), makeSite(), 1400, 22);
    const resultHigh = calculateMulcueExpected(makePanel(), makeSite(), 2000, 22);
    const annualLow = resultLow.reduce((s, m) => s + m.mulcue_ac_kWh, 0);
    const annualHigh = resultHigh.reduce((s, m) => s + m.mulcue_ac_kWh, 0);
    expect(annualHigh).toBeGreaterThan(annualLow);
  });

  it('PR está en rango razonable (0.60-0.95)', () => {
    const result = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    for (const m of result) {
      expect(m.mulcue_pr).toBeGreaterThanOrEqual(0.10);
      expect(m.mulcue_pr).toBeLessThanOrEqual(0.95);
    }
  });

  it('más paneles producen más energía proporcionalmente', () => {
    const panel5 = makePanel({ quantity: 5 });
    const panel20 = makePanel({ quantity: 20 });
    const result5 = calculateMulcueExpected(panel5, makeSite(), 1750, 22);
    const result20 = calculateMulcueExpected(panel20, makeSite(), 1750, 22);
    const annual5 = result5.reduce((s, m) => s + m.mulcue_ac_kWh, 0);
    const annual20 = result20.reduce((s, m) => s + m.mulcue_ac_kWh, 0);
    expect(annual20 / annual5).toBeCloseTo(4.0, 1);
  });
});

// ============================================================
// integratePVGISData
// ============================================================

describe('integratePVGISData', () => {
  it('integra datos PVGIS en los 12 meses', () => {
    const base = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    const pvgis = makePVGISMonthly();
    const result = integratePVGISData(base, pvgis);
    expect(result).toHaveLength(12);
    for (const m of result) {
      expect(m.pvgis_ac_kWh).not.toBeNull();
      expect(m.pvgis_poa_kWhm2).not.toBeNull();
      expect(m.pvgis_tamb).not.toBeNull();
    }
  });

  it('expected_ac_kWh es el promedio de Mulcue y PVGIS', () => {
    const base = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    const pvgis = makePVGISMonthly();
    const result = integratePVGISData(base, pvgis);
    for (let i = 0; i < 12; i++) {
      const avg = (base[i].mulcue_ac_kWh + (result[i].pvgis_ac_kWh ?? 0)) / 2;
      expect(result[i].expected_ac_kWh).toBeCloseTo(avg, 1);
    }
  });

  it('aplica factor de degradación a datos PVGIS', () => {
    const base = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    const pvgis = makePVGISMonthly();
    const resultFull = integratePVGISData(base, pvgis, 1.0);
    const resultDegraded = integratePVGISData(base, pvgis, 0.9);
    for (let i = 0; i < 12; i++) {
      expect(resultDegraded[i].pvgis_ac_kWh!).toBeLessThan(resultFull[i].pvgis_ac_kWh!);
    }
  });

  it('no modifica campos PVWatts (siguen null)', () => {
    const base = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    const pvgis = makePVGISMonthly();
    const result = integratePVGISData(base, pvgis);
    for (const m of result) {
      expect(m.pvwatts_ac_kWh).toBeNull();
      expect(m.pvwatts_dc_kWh).toBeNull();
    }
  });
});

// ============================================================
// integratePVWattsData
// ============================================================

describe('integratePVWattsData', () => {
  it('integra datos PVWatts en los 12 meses', () => {
    const base = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    const pvwatts = makePVWattsMonthly();
    const result = integratePVWattsData(base, pvwatts);
    expect(result).toHaveLength(12);
    for (const m of result) {
      expect(m.pvwatts_ac_kWh).not.toBeNull();
      expect(m.pvwatts_dc_kWh).not.toBeNull();
      expect(m.pvwatts_poa_kWhm2).not.toBeNull();
      expect(m.pvwatts_tamb).not.toBeNull();
      expect(m.pvwatts_tcell).not.toBeNull();
    }
  });

  it('expected_ac_kWh promedia Mulcue + PVWatts (sin PVGIS)', () => {
    const base = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    const pvwatts = makePVWattsMonthly();
    const result = integratePVWattsData(base, pvwatts);
    for (let i = 0; i < 12; i++) {
      const avg = (base[i].mulcue_ac_kWh + (result[i].pvwatts_ac_kWh ?? 0)) / 2;
      expect(result[i].expected_ac_kWh).toBeCloseTo(avg, 0);
    }
  });

  it('expected_ac_kWh promedia las 3 fuentes cuando PVGIS está integrado', () => {
    const base = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    const pvgis = makePVGISMonthly();
    const withPVGIS = integratePVGISData(base, pvgis);
    const pvwatts = makePVWattsMonthly();
    const result = integratePVWattsData(withPVGIS, pvwatts);
    for (let i = 0; i < 12; i++) {
      const avg = (base[i].mulcue_ac_kWh + (result[i].pvgis_ac_kWh ?? 0) + (result[i].pvwatts_ac_kWh ?? 0)) / 3;
      expect(result[i].expected_ac_kWh).toBeCloseTo(avg, 0);
    }
  });

  it('aplica factor de degradación a datos PVWatts', () => {
    const base = calculateMulcueExpected(makePanel(), makeSite(), 1750, 22);
    const pvwatts = makePVWattsMonthly();
    const resultFull = integratePVWattsData(base, pvwatts, 1.0);
    const resultDegraded = integratePVWattsData(base, pvwatts, 0.85);
    for (let i = 0; i < 12; i++) {
      expect(resultDegraded[i].pvwatts_ac_kWh!).toBeLessThan(resultFull[i].pvwatts_ac_kWh!);
    }
  });
});

// ============================================================
// calculateAnnualSummary
// ============================================================

describe('calculateAnnualSummary', () => {
  it('calcula totales anuales correctamente (solo Mulcue)', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const summary = calculateAnnualSummary(monthly, panel);
    const expectedTotal = monthly.reduce((s, m) => s + m.mulcue_ac_kWh, 0);
    expect(summary.mulcue_annual_kWh).toBeCloseTo(expectedTotal, 1);
    expect(summary.pvgis_annual_kWh).toBeNull();
    expect(summary.pvwatts_annual_kWh).toBeNull();
    expect(summary.installedCapacity_kWp).toBeGreaterThan(0);
  });

  it('incluye PVGIS cuando está disponible', () => {
    const panel = makePanel();
    const base = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const withPVGIS = integratePVGISData(base, makePVGISMonthly());
    const summary = calculateAnnualSummary(withPVGIS, panel);
    expect(summary.pvgis_annual_kWh).not.toBeNull();
    expect(summary.pvgis_specificYield).not.toBeNull();
  });

  it('incluye PVWatts cuando está disponible', () => {
    const panel = makePanel();
    const base = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const withPW = integratePVWattsData(base, makePVWattsMonthly());
    const summary = calculateAnnualSummary(withPW, panel);
    expect(summary.pvwatts_annual_kWh).not.toBeNull();
    expect(summary.pvwatts_specificYield).not.toBeNull();
  });

  it('specific yield es producción / capacidad', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const summary = calculateAnnualSummary(monthly, panel);
    const expectedSY = summary.mulcue_annual_kWh / summary.installedCapacity_kWp;
    expect(summary.mulcue_specificYield).toBeCloseTo(expectedSY, 0);
  });

  it('capacidad instalada refleja degradación', () => {
    const panelNew = makePanel({ yearsInstalled: 0 });
    const panelOld = makePanel({ yearsInstalled: 10, annualDegradation: 1.0 });
    const monthlyNew = calculateMulcueExpected(panelNew, makeSite(), 1750, 22);
    const monthlyOld = calculateMulcueExpected(panelOld, makeSite(), 1750, 22);
    const summaryNew = calculateAnnualSummary(monthlyNew, panelNew);
    const summaryOld = calculateAnnualSummary(monthlyOld, panelOld);
    expect(summaryOld.installedCapacity_kWp).toBeLessThan(summaryNew.installedCapacity_kWp);
  });
});

// ============================================================
// compareBIPVPerformance
// ============================================================

describe('compareBIPVPerformance', () => {
  it('genera comparación con datos reales completos', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    // Producción real = 95% de la esperada
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.95);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, 1750);

    expect(result.monthly).toHaveLength(12);
    expect(result.annual.real_kWh).not.toBeNull();
    expect(result.annual.delta_pct).not.toBeNull();
    expect(result.healthScore).toBeGreaterThan(0);
    expect(result.healthScore).toBeLessThanOrEqual(100);
    expect(result.healthStatus).toBeTruthy();
    expect(result.metrics).toHaveLength(4);
  });

  it('sistema con 95% de producción esperada → salud buena/excelente', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.95);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, 1750);
    expect(result.healthScore).toBeGreaterThanOrEqual(75);
    expect(['excelente', 'bueno']).toContain(result.healthStatus);
  });

  it('sistema con 50% de producción esperada → salud deficiente/crítico', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.50);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, 1750);
    expect(result.healthScore).toBeLessThanOrEqual(40);
    expect(['deficiente', 'critico']).toContain(result.healthStatus);
  });

  it('sistema con 110% de producción esperada → salud excelente', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 1.10);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, 1750);
    expect(result.healthScore).toBeGreaterThanOrEqual(85);
    expect(result.healthStatus).toBe('excelente');
  });

  it('delta_pct mensual es correcto', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.80);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, 1750);
    for (const m of result.monthly) {
      expect(m.delta_pct).not.toBeNull();
      expect(m.delta_pct!).toBeCloseTo(-20, 0);
    }
  });

  it('maneja datos mensuales parciales (algunos null)', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const partial: (number | null)[] = [400, 380, null, null, 350, 360, null, 370, 380, null, 390, 400];
    const field = makeField(partial);
    const result = compareBIPVPerformance(monthly, field, panel, 1750);
    expect(result.monthly[2].real_kWh).toBeNull();
    expect(result.monthly[2].delta_pct).toBeNull();
    expect(result.monthly[0].real_kWh).toBe(400);
    expect(result.monthly[0].delta_pct).not.toBeNull();
  });

  it('maneja campo sin datos reales', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const field = makeField(Array(12).fill(null), null);
    const result = compareBIPVPerformance(monthly, field, panel, 1750);
    expect(result.annual.real_kWh).toBeNull();
    expect(result.annual.delta_pct).toBeNull();
    expect(result.healthScore).toBe(50); // sin datos → 50
  });

  it('PR real estimado es razonable', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.90);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, 1750);
    expect(result.annual.pr_real).not.toBeNull();
    expect(result.annual.pr_real!).toBeGreaterThan(0.3);
    expect(result.annual.pr_real!).toBeLessThan(1.2);
  });

  it('energy ratio es real/expected', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.85);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, 1750);
    expect(result.annual.energyRatio).not.toBeNull();
    expect(result.annual.energyRatio!).toBeCloseTo(0.85, 1);
  });
});

// ============================================================
// estimateGHIFromLatitude
// ============================================================

describe('estimateGHIFromLatitude', () => {
  it('Medellín (6.25°N) → ~1750 kWh/m²/año', () => {
    expect(estimateGHIFromLatitude(6.25)).toBe(1800);
  });

  it('Bogotá (4.6°N) → ~1750 kWh/m²/año', () => {
    expect(estimateGHIFromLatitude(4.6)).toBe(1750);
  });

  it('Guajira (12°N) → ~2000 kWh/m²/año', () => {
    expect(estimateGHIFromLatitude(12)).toBe(2000);
  });

  it('Amazonía (1°N) → ~1650 kWh/m²/año', () => {
    expect(estimateGHIFromLatitude(1)).toBe(1650);
  });

  it('latitud fuera de Colombia → default 1700', () => {
    expect(estimateGHIFromLatitude(30)).toBe(1700);
  });

  it('valores siempre en rango razonable', () => {
    for (let lat = -10; lat <= 40; lat += 5) {
      const ghi = estimateGHIFromLatitude(lat);
      expect(ghi).toBeGreaterThanOrEqual(1600);
      expect(ghi).toBeLessThanOrEqual(2100);
    }
  });
});

// ============================================================
// estimateTempFromLatitude
// ============================================================

describe('estimateTempFromLatitude', () => {
  it('nivel del mar → ~28°C', () => {
    expect(estimateTempFromLatitude(6, 0)).toBe(28);
  });

  it('Medellín (~1500m) → ~18°C', () => {
    const temp = estimateTempFromLatitude(6.25, 1500);
    expect(temp).toBeCloseTo(18.25, 0);
  });

  it('Bogotá (~2600m) → ~11°C', () => {
    const temp = estimateTempFromLatitude(4.6, 2600);
    expect(temp).toBeCloseTo(11.1, 0);
  });

  it('mayor elevación → menor temperatura', () => {
    const tempLow = estimateTempFromLatitude(6, 0);
    const tempHigh = estimateTempFromLatitude(6, 3000);
    expect(tempHigh).toBeLessThan(tempLow);
  });
});

// ============================================================
// Flujo completo: Mulcue → PVGIS → PVWatts → Comparación
// ============================================================

describe('Flujo completo de diagnóstico BIPV', () => {
  it('integra las 3 fuentes y genera diagnóstico coherente', () => {
    const panel = makePanel({ quantity: 20 });
    const site = makeSite();

    // Paso 1: Calcular Mulcue
    let monthly = calculateMulcueExpected(panel, site, 1750, 22);
    expect(monthly).toHaveLength(12);
    expect(monthly[0].pvgis_ac_kWh).toBeNull();

    // Paso 2: Integrar PVGIS
    monthly = integratePVGISData(monthly, makePVGISMonthly());
    expect(monthly[0].pvgis_ac_kWh).not.toBeNull();
    expect(monthly[0].pvwatts_ac_kWh).toBeNull();

    // Paso 3: Integrar PVWatts
    monthly = integratePVWattsData(monthly, makePVWattsMonthly());
    expect(monthly[0].pvwatts_ac_kWh).not.toBeNull();

    // Paso 4: Resumen anual
    const summary = calculateAnnualSummary(monthly, panel);
    expect(summary.mulcue_annual_kWh).toBeGreaterThan(0);
    expect(summary.pvgis_annual_kWh).not.toBeNull();
    expect(summary.pvwatts_annual_kWh).not.toBeNull();
    expect(summary.expected_annual_kWh).toBeGreaterThan(0);

    // Paso 5: Comparar con producción real (90%)
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.90);
    const field = makeField(realMonthly);
    const comparison = compareBIPVPerformance(monthly, field, panel, 1750);

    expect(comparison.healthScore).toBeGreaterThan(50);
    expect(comparison.annual.delta_pct).not.toBeNull();
    expect(comparison.annual.delta_pct!).toBeCloseTo(-10, 0);
    expect(comparison.metrics.length).toBe(4);
  });

  it('funciona solo con Mulcue (sin datos satelitales)', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), 1750, 22);
    const summary = calculateAnnualSummary(monthly, panel);
    expect(summary.pvgis_annual_kWh).toBeNull();
    expect(summary.pvwatts_annual_kWh).toBeNull();
    expect(summary.expected_annual_kWh).toBeGreaterThan(0);

    const realMonthly = monthly.map(m => m.expected_ac_kWh * 1.0);
    const field = makeField(realMonthly);
    const comparison = compareBIPVPerformance(monthly, field, panel, 1750);
    expect(comparison.healthScore).toBeGreaterThanOrEqual(85);
  });
});

// ============================================================
// PR Convencional y PR Corregido
// ============================================================

describe('PR Convencional y PR Corregido', () => {
  const GHI = 1750;

  it('PR Convencional = E_inv / P_m, donde P_m = P_ref × N × (G/G_ref)', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), GHI, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.90);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, GHI);

    for (const m of result.monthly) {
      expect(m.pm_kWh).toBeGreaterThan(0);
      expect(m.pr_conventional).not.toBeNull();
      expect(m.pr_conventional!).toBeGreaterThan(0);
      expect(m.pr_conventional!).toBeLessThan(1.5);
    }
    expect(result.annual.pr_conventional).not.toBeNull();
    expect(result.annual.pm_annual_kWh).toBeGreaterThan(0);
  });

  it('PR Corregido = E_inv / E_esperada (promedio modelos)', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), GHI, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.90);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, GHI);

    for (const m of result.monthly) {
      expect(m.pr_corrected).not.toBeNull();
      expect(m.pr_corrected!).toBeCloseTo(0.90, 1);
    }
    expect(result.annual.pr_corrected).not.toBeNull();
    expect(result.annual.pr_corrected!).toBeCloseTo(0.90, 1);
  });

  it('PR Convencional < 1 cuando sistema tiene pérdidas normales', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), GHI, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.80);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, GHI);
    expect(result.annual.pr_conventional).not.toBeNull();
    expect(result.annual.pr_conventional!).toBeLessThan(1.0);
  });

  it('PR Convencional siempre ≤ PR Corregido (P_m > E_esperada)', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), GHI, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.85);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, GHI);
    expect(result.annual.pr_conventional!).toBeLessThanOrEqual(result.annual.pr_corrected!);
  });

  it('P_m anual = suma de P_m mensuales', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), GHI, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.90);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, GHI);
    const sumPm = result.monthly.reduce((s, m) => s + m.pm_kWh, 0);
    expect(result.annual.pm_annual_kWh).toBeCloseTo(sumPm, 0);
  });

  it('P_m usa POA de PVWatts cuando está disponible', () => {
    const panel = makePanel();
    let monthly = calculateMulcueExpected(panel, makeSite(), GHI, 22);
    const pvwatts = makePVWattsMonthly();
    monthly = integratePVWattsData(monthly, pvwatts);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.90);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, GHI);
    for (let i = 0; i < 12; i++) {
      const P_ref_kW = (panel.powerRating * panel.quantity) / 1000;
      const expectedPm = P_ref_kW * (monthly[i].pvwatts_poa_kWhm2! / 1);
      expect(result.monthly[i].pm_kWh).toBeCloseTo(expectedPm, 0);
    }
  });

  it('sin datos reales, PR Convencional y PR Corregido son null', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), GHI, 22);
    const field = makeField(Array(12).fill(null), null);
    const result = compareBIPVPerformance(monthly, field, panel, GHI);
    for (const m of result.monthly) {
      expect(m.pr_conventional).toBeNull();
      expect(m.pr_corrected).toBeNull();
    }
    expect(result.annual.pr_conventional).toBeNull();
    expect(result.annual.pr_corrected).toBeNull();
  });

  it('métricas incluyen PR Conv. y PR Corr.', () => {
    const panel = makePanel();
    const monthly = calculateMulcueExpected(panel, makeSite(), GHI, 22);
    const realMonthly = monthly.map(m => m.expected_ac_kWh * 0.90);
    const field = makeField(realMonthly);
    const result = compareBIPVPerformance(monthly, field, panel, GHI);
    const labels = result.metrics.map(m => m.label);
    expect(labels).toContain('PR Conv.');
    expect(labels).toContain('PR Corr.');
    expect(result.metrics).toHaveLength(4);
  });
});
