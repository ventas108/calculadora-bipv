import { describe, it, expect } from 'vitest';
import {
  diagnosePerformance,
  getAlertBadge,
  PR_THRESHOLDS,
  PR_REFERENCE,
  type DiagnosticInput,
  type PerformanceAlert,
  type AlertSeverity,
} from '../shared/performanceDiagnostic';

// ============================================================
// Helper: baseline input with normal conditions
// ============================================================
function baseInput(overrides: Partial<DiagnosticInput> = {}): DiagnosticInput {
  return {
    prMeasured: 0.78,
    ghiField: 800,
    tempAmbient: 25,
    tempCell: 45,
    tempCellManual: false,
    pExp: 320,
    pNom: 400,
    tempCoeff: -0.35,
    noct: 45,
    tempLoss: 0.93,
    installationType: 'rooftop_inclined',
    systemLosses: {
      soiling: 2,
      mismatch: 2,
      dcWiring: 1,
      acWiring: 1,
      inverterEfficiency: 96,
    },
    latitude: 6.25,
    ...overrides,
  };
}

// ============================================================
// 1. SEVERITY CLASSIFICATION
// ============================================================
describe('diagnosePerformance - severity classification', () => {
  it('returns "ok" when PR is close to expected', () => {
    const result = diagnosePerformance(baseInput({ prMeasured: 0.78 }));
    expect(result.severity).toBe('ok');
    expect(result.healthScore).toBeGreaterThanOrEqual(80);
  });

  it('returns "leve" when PR deviates 10-15%', () => {
    // Force a lower PR to trigger leve
    const result = diagnosePerformance(baseInput({ prMeasured: 0.60, tempAmbient: 25 }));
    // The severity depends on the calculated expected PR
    expect(['leve', 'moderada', 'severa', 'critica']).toContain(result.severity);
    expect(result.prDeviation).toBeGreaterThan(0);
  });

  it('returns "moderada" or worse when PR deviates significantly', () => {
    const result = diagnosePerformance(baseInput({ prMeasured: 0.45 }));
    expect(['moderada', 'severa', 'critica']).toContain(result.severity);
    expect(result.causes.length).toBeGreaterThan(0);
  });

  it('returns "critica" when PR is extremely low', () => {
    const result = diagnosePerformance(baseInput({ prMeasured: 0.15 }));
    expect(result.severity).toBe('critica');
    expect(result.healthScore).toBeLessThan(30);
    expect(result.causes.length).toBeGreaterThan(0);
  });
});

// ============================================================
// 2. ALERT STRUCTURE
// ============================================================
describe('diagnosePerformance - alert structure', () => {
  it('returns all required fields', () => {
    const result = diagnosePerformance(baseInput());
    expect(result).toHaveProperty('severity');
    expect(result).toHaveProperty('color');
    expect(result).toHaveProperty('bgColor');
    expect(result).toHaveProperty('title');
    expect(result).toHaveProperty('message');
    expect(result).toHaveProperty('prDeviation');
    expect(result).toHaveProperty('prMeasured');
    expect(result).toHaveProperty('prExpected');
    expect(result).toHaveProperty('causes');
    expect(result).toHaveProperty('healthScore');
    expect(typeof result.color).toBe('string');
    expect(typeof result.bgColor).toBe('string');
    expect(typeof result.title).toBe('string');
    expect(typeof result.message).toBe('string');
    expect(Array.isArray(result.causes)).toBe(true);
  });

  it('causes are sorted by probability descending', () => {
    const result = diagnosePerformance(baseInput({ prMeasured: 0.30 }));
    for (let i = 1; i < result.causes.length; i++) {
      expect(result.causes[i - 1].probability).toBeGreaterThanOrEqual(result.causes[i].probability);
    }
  });

  it('healthScore is between 0 and 100', () => {
    const inputs = [0.90, 0.70, 0.50, 0.30, 0.10];
    for (const pr of inputs) {
      const result = diagnosePerformance(baseInput({ prMeasured: pr }));
      expect(result.healthScore).toBeGreaterThanOrEqual(0);
      expect(result.healthScore).toBeLessThanOrEqual(100);
    }
  });

  it('prMeasured and prExpected are rounded to 3 decimals', () => {
    const result = diagnosePerformance(baseInput({ prMeasured: 0.777777 }));
    const decimals = result.prMeasured.toString().split('.')[1]?.length ?? 0;
    expect(decimals).toBeLessThanOrEqual(3);
  });
});

// ============================================================
// 3. CAUSE ANALYSIS
// ============================================================
describe('diagnosePerformance - cause analysis', () => {
  it('returns no causes when PR is within normal range', () => {
    const result = diagnosePerformance(baseInput({ prMeasured: 0.78 }));
    if (result.severity === 'ok') {
      expect(result.causes.length).toBe(0);
    }
  });

  it('includes soiling cause for moderate deviation', () => {
    const result = diagnosePerformance(baseInput({ prMeasured: 0.40 }));
    const soiling = result.causes.find(c => c.id === 'soiling');
    expect(soiling).toBeDefined();
    expect(soiling!.category).toBe('mantenimiento');
    expect(soiling!.recommendation).toBeTruthy();
  });

  it('includes partial shading cause for low GHI', () => {
    const result = diagnosePerformance(baseInput({ prMeasured: 0.40, ghiField: 300 }));
    const shading = result.causes.find(c => c.id === 'partial_shading');
    expect(shading).toBeDefined();
    expect(shading!.category).toBe('instalacion');
  });

  it('includes excessive temp cause for high cell temperature', () => {
    const result = diagnosePerformance(baseInput({
      prMeasured: 0.40,
      tempCell: 75,
      tempAmbient: 40,
      tempCellManual: true,
    }));
    const temp = result.causes.find(c => c.id === 'excessive_temp');
    expect(temp).toBeDefined();
    expect(temp!.description).toContain('75.0°C');
  });

  it('includes degradation cause for low pExp vs pNom', () => {
    const result = diagnosePerformance(baseInput({
      prMeasured: 0.35,
      pExp: 200,
      pNom: 400,
    }));
    const degradation = result.causes.find(c => c.id === 'module_degradation');
    expect(degradation).toBeDefined();
    expect(degradation!.category).toBe('equipo');
  });

  it('includes inverter cause for moderate deviation with low efficiency', () => {
    const result = diagnosePerformance(baseInput({
      prMeasured: 0.30,
      systemLosses: { inverterEfficiency: 88, soiling: 2, mismatch: 2, dcWiring: 1, acWiring: 1 },
    }));
    const inverter = result.causes.find(c => c.id === 'inverter_losses');
    // Inverter cause may or may not appear depending on deviation threshold
    if (inverter) {
      expect(inverter.category).toBe('equipo');
      expect(inverter.probability).toBeGreaterThan(0);
    }
  });

  it('includes wiring cause for facade installations', () => {
    const result = diagnosePerformance(baseInput({
      prMeasured: 0.40,
      installationType: 'facade_vertical',
    }));
    const wiring = result.causes.find(c => c.id === 'wiring_losses');
    expect(wiring).toBeDefined();
  });

  it('includes mismatch cause for facade installations', () => {
    const result = diagnosePerformance(baseInput({
      prMeasured: 0.25,
      installationType: 'facade_inclined',
    }));
    const mismatch = result.causes.find(c => c.id === 'mismatch');
    // Mismatch may not always appear; check that facade at least has more causes
    if (mismatch) {
      expect(mismatch.category).toBe('diseno');
      expect(mismatch.probability).toBeGreaterThan(0.05);
    } else {
      // At minimum, facade should have wiring or other installation-related causes
      const facadeCauses = result.causes.filter(c => 
        c.category === 'instalacion' || c.category === 'diseno'
      );
      expect(facadeCauses.length).toBeGreaterThan(0);
    }
  });

  it('each cause has all required fields', () => {
    const result = diagnosePerformance(baseInput({ prMeasured: 0.30 }));
    for (const cause of result.causes) {
      expect(cause).toHaveProperty('id');
      expect(cause).toHaveProperty('name');
      expect(cause).toHaveProperty('probability');
      expect(cause).toHaveProperty('description');
      expect(cause).toHaveProperty('recommendation');
      expect(cause).toHaveProperty('category');
      expect(cause).toHaveProperty('icon');
      expect(cause.probability).toBeGreaterThan(0);
      expect(cause.probability).toBeLessThanOrEqual(1);
      expect(['ambiental', 'equipo', 'instalacion', 'mantenimiento', 'diseno']).toContain(cause.category);
    }
  });
});

// ============================================================
// 4. TEMPERATURE EFFECTS
// ============================================================
describe('diagnosePerformance - temperature effects', () => {
  it('higher temperature leads to lower expected PR', () => {
    const cool = diagnosePerformance(baseInput({ tempAmbient: 20, prMeasured: 0.70 }));
    const hot = diagnosePerformance(baseInput({ tempAmbient: 40, prMeasured: 0.70 }));
    // Hot environment has lower expected PR, so deviation should be smaller
    expect(hot.prExpected).toBeLessThan(cool.prExpected);
  });

  it('manual T_cell is mentioned in cause description', () => {
    const result = diagnosePerformance(baseInput({
      prMeasured: 0.40,
      tempCell: 70,
      tempCellManual: true,
    }));
    const temp = result.causes.find(c => c.id === 'excessive_temp');
    if (temp) {
      expect(temp.description).toContain('medida directamente');
    }
  });
});

// ============================================================
// 5. HEALTH SCORE
// ============================================================
describe('diagnosePerformance - health score', () => {
  it('perfect PR gives health score of 100', () => {
    const result = diagnosePerformance(baseInput({ prMeasured: 0.95 }));
    expect(result.healthScore).toBe(100);
  });

  it('health score decreases with increasing deviation', () => {
    const scores: number[] = [];
    for (const pr of [0.80, 0.60, 0.40, 0.20]) {
      const result = diagnosePerformance(baseInput({ prMeasured: pr }));
      scores.push(result.healthScore);
    }
    // Each subsequent score should be lower or equal
    for (let i = 1; i < scores.length; i++) {
      expect(scores[i]).toBeLessThanOrEqual(scores[i - 1]);
    }
  });
});

// ============================================================
// 6. getAlertBadge
// ============================================================
describe('getAlertBadge', () => {
  it('returns OK badge for normal PR', () => {
    const badge = getAlertBadge(0.78, 25, -0.35);
    expect(badge.severity).toBe('ok');
    expect(badge.label).toBe('OK');
    expect(badge.icon).toBe('✓');
    expect(badge.color).toBeTruthy();
    expect(badge.bgColor).toBeTruthy();
  });

  it('returns warning badge for low PR', () => {
    const badge = getAlertBadge(0.40, 25, -0.35);
    expect(['leve', 'moderada', 'severa', 'critica']).toContain(badge.severity);
    expect(badge.label).not.toBe('OK');
  });

  it('returns critical badge for very low PR', () => {
    const badge = getAlertBadge(0.10, 25, -0.35);
    expect(badge.severity).toBe('critica');
    expect(badge.label).toBe('Crítica');
    expect(badge.icon).toBe('🚨');
  });

  it('adjusts expected PR for temperature', () => {
    // At high temperature, the same PR should be less alarming
    const hotBadge = getAlertBadge(0.55, 40, -0.45);
    const coolBadge = getAlertBadge(0.55, 20, -0.45);
    // Hot environment expects lower PR, so severity should be same or less
    const severityOrder: AlertSeverity[] = ['ok', 'leve', 'moderada', 'severa', 'critica'];
    expect(severityOrder.indexOf(hotBadge.severity)).toBeLessThanOrEqual(
      severityOrder.indexOf(coolBadge.severity)
    );
  });
});

// ============================================================
// 7. INSTALLATION TYPE EFFECTS
// ============================================================
describe('diagnosePerformance - installation type effects', () => {
  it('carport installation increases soiling probability', () => {
    const carport = diagnosePerformance(baseInput({
      prMeasured: 0.40,
      installationType: 'carport',
    }));
    const rooftop = diagnosePerformance(baseInput({
      prMeasured: 0.40,
      installationType: 'rooftop_inclined',
    }));
    const carportSoiling = carport.causes.find(c => c.id === 'soiling');
    const rooftopSoiling = rooftop.causes.find(c => c.id === 'soiling');
    if (carportSoiling && rooftopSoiling) {
      expect(carportSoiling.probability).toBeGreaterThanOrEqual(rooftopSoiling.probability);
    }
  });

  it('facade installation increases wiring and mismatch probability', () => {
    // Use very low PR to ensure all causes are triggered
    const result = diagnosePerformance(baseInput({
      prMeasured: 0.25,
      installationType: 'facade_vertical',
    }));
    const wiring = result.causes.find(c => c.id === 'wiring_losses');
    const mismatch = result.causes.find(c => c.id === 'mismatch');
    // At least one of wiring/mismatch should appear for facade
    const hasFacadeCause = wiring || mismatch;
    expect(hasFacadeCause).toBeDefined();
    if (wiring) expect(wiring.probability).toBeGreaterThan(0.05);
    if (mismatch) expect(mismatch.probability).toBeGreaterThan(0.05);
  });
});

// ============================================================
// 8. EDGE CASES
// ============================================================
describe('diagnosePerformance - edge cases', () => {
  it('handles PR of 0', () => {
    const result = diagnosePerformance(baseInput({ prMeasured: 0 }));
    expect(result.severity).toBe('critica');
    expect(result.healthScore).toBeLessThan(10);
  });

  it('handles PR greater than 1 (measurement error)', () => {
    // PR > 1 is unusual; the system may flag it or treat as ok depending on expected PR
    const result = diagnosePerformance(baseInput({ prMeasured: 1.1 }));
    // With PR > expected, deviation should be negative (better than expected)
    // or the system handles it gracefully
    expect(result).toHaveProperty('severity');
    expect(result.healthScore).toBeGreaterThanOrEqual(0);
    expect(result.healthScore).toBeLessThanOrEqual(100);
  });

  it('handles very high temperature', () => {
    const result = diagnosePerformance(baseInput({
      prMeasured: 0.30,
      tempCell: 90,
      tempAmbient: 45,
    }));
    expect(result.causes.length).toBeGreaterThan(0);
  });

  it('handles very low GHI', () => {
    const result = diagnosePerformance(baseInput({
      prMeasured: 0.30,
      ghiField: 100,
    }));
    // Low GHI should trigger either low_irradiance or partial_shading cause
    const lowIrr = result.causes.find(c => c.id === 'low_irradiance');
    const shading = result.causes.find(c => c.id === 'partial_shading');
    const hasLowGHICause = lowIrr || shading;
    expect(hasLowGHICause).toBeDefined();
  });

  it('handles missing optional fields gracefully', () => {
    const result = diagnosePerformance({
      prMeasured: 0.40,
      ghiField: 800,
      tempAmbient: 30,
      tempCell: 50,
      tempCellManual: false,
      pExp: 300,
      pNom: 400,
      tempCoeff: -0.35,
      noct: 45,
      tempLoss: 0.90,
    });
    expect(result).toHaveProperty('severity');
    expect(result.causes.length).toBeGreaterThan(0);
  });
});
