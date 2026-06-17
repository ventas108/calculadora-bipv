import { describe, it, expect } from 'vitest';
import {
  calculateAOI,
  calculateIAM_ASHRAE,
  applyIAM,
  calculateSoiling,
  calculateThermalBIPV,
  calculateAdjustedEfficiency,
  calculateBIPVPower,
  calculatePassiveLighting,
  calculatePOATransposition,
  evaluateObstacleShading,
  DEFAULT_SOILING_CONFIG,
} from '../client/src/lib/iamSoilingEngine';
import {
  BIPV_GLASS_CATALOG,
  TRANSPARENCY_LEVELS,
  SOILING_PRESETS,
  THERMAL_MOUNTING_TYPES,
  getTechnologyById,
  getTechnologiesByGeneration,
  getSoilingPresetById,
  getMountingTypeById,
} from '../client/src/lib/bipvGlassCatalog';

// ─── calculateAOI ─────────────────────────────────────────────────────────────

describe('calculateAOI', () => {
  it('returns 0° when sun is perpendicular to surface (normal incidence)', () => {
    // Sun at zenith (0° zenith), horizontal surface (0° tilt)
    const aoi = calculateAOI(0, 0, 0, 0);
    expect(aoi).toBeCloseTo(0, 1);
  });

  it('returns surface tilt when sun is at zenith and surface is tilted', () => {
    // Sun at zenith (0°), surface tilted 30° facing south (180°)
    const aoi = calculateAOI(0, 180, 30, 180);
    expect(aoi).toBeCloseTo(30, 1);
  });

  it('returns 90° when sun is parallel to vertical surface (grazing)', () => {
    // Sun at zenith 90° (horizon), surface vertical (90°) facing same azimuth
    // cos(AOI) = cos(90)*cos(90) + sin(90)*sin(90)*cos(0) = 0 + 1*1*1 = 1 → AOI=0
    // Actually this is normal incidence for vertical surface when sun is at horizon
    const aoi = calculateAOI(90, 180, 90, 180);
    expect(aoi).toBeCloseTo(0, 1);
  });

  it('returns value between 0 and 180', () => {
    const aoi = calculateAOI(45, 120, 30, 200);
    expect(aoi).toBeGreaterThanOrEqual(0);
    expect(aoi).toBeLessThanOrEqual(180);
  });

  it('AOI increases when sun moves away from surface normal', () => {
    const aoiAligned = calculateAOI(30, 180, 30, 180);
    const aoiMisaligned = calculateAOI(30, 90, 30, 180); // 90° azimuth difference
    expect(aoiMisaligned).toBeGreaterThan(aoiAligned);
  });
});

// ─── calculateIAM_ASHRAE ──────────────────────────────────────────────────────

describe('calculateIAM_ASHRAE', () => {
  const b0 = 0.05; // Typical value for glass

  it('returns ~1.0 at normal incidence (AOI=0)', () => {
    const iam = calculateIAM_ASHRAE(0, b0);
    // At AOI=0, cos(0)=1, so 1/cos(0)-1 = 0, f_IAM = 1
    expect(iam).toBeCloseTo(1.0, 4);
  });

  it('returns 0.0 at AOI >= 85° (total reflection)', () => {
    expect(calculateIAM_ASHRAE(85, b0)).toBe(0.0);
    expect(calculateIAM_ASHRAE(90, b0)).toBe(0.0);
  });

  it('returns 0.0 for negative AOI', () => {
    expect(calculateIAM_ASHRAE(-5, b0)).toBe(0.0);
  });

  it('decreases monotonically as AOI increases from 0 to 84', () => {
    let prev = calculateIAM_ASHRAE(0, b0);
    for (let aoi = 10; aoi <= 84; aoi += 10) {
      const curr = calculateIAM_ASHRAE(aoi, b0);
      expect(curr).toBeLessThanOrEqual(prev);
      prev = curr;
    }
  });

  it('is always in range [0, 1]', () => {
    for (let aoi = 0; aoi <= 90; aoi += 5) {
      const iam = calculateIAM_ASHRAE(aoi, b0);
      expect(iam).toBeGreaterThanOrEqual(0);
      expect(iam).toBeLessThanOrEqual(1);
    }
  });

  it('higher b0 means more reflection loss', () => {
    const iamLow = calculateIAM_ASHRAE(60, 0.03);
    const iamHigh = calculateIAM_ASHRAE(60, 0.10);
    expect(iamHigh).toBeLessThan(iamLow);
  });

  it('at 60° with b0=0.05, IAM ≈ 0.95 (typical value)', () => {
    const iam = calculateIAM_ASHRAE(60, 0.05);
    expect(iam).toBeGreaterThan(0.90);
    expect(iam).toBeLessThan(1.0);
  });
});

// ─── applyIAM ─────────────────────────────────────────────────────────────────

describe('applyIAM', () => {
  it('reduces direct component but preserves diffuse', () => {
    const result = applyIAM(500, 200, 45, 180, 30, 180, 0.05);
    // Directa neta should be <= directa original
    expect(result.poaDirectaNeta).toBeLessThanOrEqual(500);
    expect(result.poaDirectaNeta).toBeGreaterThan(0);
    // Total óptica = directa_neta + difusa
    expect(result.poaTotalOptica).toBeCloseTo(result.poaDirectaNeta + 200, 1);
  });

  it('returns AOI in valid range', () => {
    const result = applyIAM(500, 200, 30, 120, 45, 180, 0.05);
    expect(result.aoiDeg).toBeGreaterThanOrEqual(0);
    expect(result.aoiDeg).toBeLessThanOrEqual(180);
  });

  it('fIam is in [0, 1]', () => {
    const result = applyIAM(500, 200, 60, 90, 90, 180, 0.08);
    expect(result.fIam).toBeGreaterThanOrEqual(0);
    expect(result.fIam).toBeLessThanOrEqual(1);
  });
});

// ─── calculateSoiling ─────────────────────────────────────────────────────────

describe('calculateSoiling', () => {
  it('returns base seasonal soiling when no precipitable water', () => {
    const result = calculateSoiling(1, undefined, DEFAULT_SOILING_CONFIG);
    expect(result.soilingEstacional).toBe(0.05);
    expect(result.soilingReal).toBe(0.05);
    expect(result.autoWash).toBe(false);
  });

  it('applies auto-wash when precipitable water exceeds threshold', () => {
    const result = calculateSoiling(1, 30, DEFAULT_SOILING_CONFIG); // 30 > 25 threshold
    expect(result.autoWash).toBe(true);
    expect(result.soilingReal).toBeLessThan(result.soilingEstacional);
    expect(result.soilingReal).toBeCloseTo(0.05 * 0.15, 4);
  });

  it('does not apply auto-wash when precipitable water is below threshold', () => {
    const result = calculateSoiling(1, 20, DEFAULT_SOILING_CONFIG); // 20 < 25 threshold
    expect(result.autoWash).toBe(false);
    expect(result.soilingReal).toBe(result.soilingEstacional);
  });

  it('returns correct monthly factor for each month', () => {
    for (let m = 1; m <= 12; m++) {
      const result = calculateSoiling(m, undefined, DEFAULT_SOILING_CONFIG);
      expect(result.soilingEstacional).toBe(DEFAULT_SOILING_CONFIG.monthlyFactors[m]);
    }
  });

  it('soiling is always in range [0, 1]', () => {
    for (let m = 1; m <= 12; m++) {
      const result = calculateSoiling(m, 50, DEFAULT_SOILING_CONFIG);
      expect(result.soilingReal).toBeGreaterThanOrEqual(0);
      expect(result.soilingReal).toBeLessThanOrEqual(1);
    }
  });
});

// ─── calculateThermalBIPV ─────────────────────────────────────────────────────

describe('calculateThermalBIPV', () => {
  it('cell temperature is higher than ambient when POA > 0', () => {
    const result = calculateThermalBIPV(25, 500, 45, -0.004, 1.3);
    expect(result.tCell).toBeGreaterThan(25);
  });

  it('cell temperature equals ambient when POA = 0', () => {
    const result = calculateThermalBIPV(25, 0, 45, -0.004, 1.3);
    expect(result.tCell).toBeCloseTo(25, 4);
  });

  it('thermal factor < 1 when cell temp > 25°C (negative coef)', () => {
    const result = calculateThermalBIPV(30, 500, 45, -0.004, 1.3);
    expect(result.factorTermico).toBeLessThan(1.0);
  });

  it('thermal factor > 1 when cell temp < 25°C (cold conditions)', () => {
    const result = calculateThermalBIPV(5, 50, 45, -0.004, 1.3);
    // With very low POA and cold ambient, tCell can be < 25
    expect(result.tCell).toBeLessThan(25);
    expect(result.factorTermico).toBeGreaterThan(1.0);
  });

  it('higher kBipv (confined) means higher cell temperature', () => {
    const ventilated = calculateThermalBIPV(25, 500, 45, -0.004, 1.0);
    const confined = calculateThermalBIPV(25, 500, 45, -0.004, 1.3);
    const noVent = calculateThermalBIPV(25, 500, 45, -0.004, 1.5);
    expect(confined.tCell).toBeGreaterThan(ventilated.tCell);
    expect(noVent.tCell).toBeGreaterThan(confined.tCell);
  });

  it('higher NOCT means higher cell temperature', () => {
    const lowNoct = calculateThermalBIPV(25, 500, 40, -0.004, 1.3);
    const highNoct = calculateThermalBIPV(25, 500, 50, -0.004, 1.3);
    expect(highNoct.tCell).toBeGreaterThan(lowNoct.tCell);
  });
});

// ─── calculateAdjustedEfficiency ──────────────────────────────────────────────

describe('calculateAdjustedEfficiency', () => {
  it('returns full efficiency at 0% transparency', () => {
    expect(calculateAdjustedEfficiency(0.20, 0)).toBeCloseTo(0.20, 4);
  });

  it('returns 0 at 100% transparency', () => {
    expect(calculateAdjustedEfficiency(0.20, 1.0)).toBeCloseTo(0.0, 4);
  });

  it('reduces efficiency proportionally to transparency', () => {
    expect(calculateAdjustedEfficiency(0.20, 0.40)).toBeCloseTo(0.12, 4);
  });

  it('efficiency decreases monotonically with transparency', () => {
    let prev = calculateAdjustedEfficiency(0.20, 0);
    for (const t of [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]) {
      const curr = calculateAdjustedEfficiency(0.20, t);
      expect(curr).toBeLessThanOrEqual(prev);
      prev = curr;
    }
  });
});

// ─── calculateBIPVPower ───────────────────────────────────────────────────────

describe('calculateBIPVPower', () => {
  it('returns 0 when POA is 0', () => {
    expect(calculateBIPVPower(0, 10, 0.12, 0.95, 0.05)).toBe(0);
  });

  it('returns positive power with valid inputs', () => {
    const power = calculateBIPVPower(500, 10, 0.12, 0.95, 0.05);
    expect(power).toBeGreaterThan(0);
  });

  it('power scales linearly with area', () => {
    const p1 = calculateBIPVPower(500, 5, 0.12, 0.95, 0.05);
    const p2 = calculateBIPVPower(500, 10, 0.12, 0.95, 0.05);
    expect(p2).toBeCloseTo(p1 * 2, 1);
  });

  it('higher soiling reduces power', () => {
    const pClean = calculateBIPVPower(500, 10, 0.12, 0.95, 0.01);
    const pDirty = calculateBIPVPower(500, 10, 0.12, 0.95, 0.10);
    expect(pDirty).toBeLessThan(pClean);
  });

  it('never returns negative power', () => {
    const power = calculateBIPVPower(500, 10, 0.12, 0.5, 0.99);
    expect(power).toBeGreaterThanOrEqual(0);
  });
});

// ─── calculatePassiveLighting ─────────────────────────────────────────────────

describe('calculatePassiveLighting', () => {
  it('returns 0 at 0% transparency', () => {
    expect(calculatePassiveLighting(500, 10, 0.0)).toBe(0);
  });

  it('returns full POA × area at 100% transparency', () => {
    expect(calculatePassiveLighting(500, 10, 1.0)).toBeCloseTo(5000, 1);
  });

  it('scales linearly with transparency', () => {
    const l1 = calculatePassiveLighting(500, 10, 0.2);
    const l2 = calculatePassiveLighting(500, 10, 0.4);
    expect(l2).toBeCloseTo(l1 * 2, 1);
  });
});

// ─── calculatePOATransposition ────────────────────────────────────────────────

describe('calculatePOATransposition', () => {
  it('returns positive POA for sun above horizon', () => {
    const result = calculatePOATransposition(500, 600, 200, 30, 180, 30, 180);
    expect(result.poaTotal).toBeGreaterThan(0);
    expect(result.poaDirecta).toBeGreaterThanOrEqual(0);
    expect(result.poaDifusa).toBeGreaterThanOrEqual(0);
    expect(result.poaReflejada).toBeGreaterThanOrEqual(0);
  });

  it('total = directa + difusa + reflejada', () => {
    const result = calculatePOATransposition(500, 600, 200, 45, 180, 30, 180);
    expect(result.poaTotal).toBeCloseTo(result.poaDirecta + result.poaDifusa + result.poaReflejada, 4);
  });

  it('horizontal surface gets maximum diffuse', () => {
    const horizontal = calculatePOATransposition(0, 0, 200, 30, 180, 0, 180);
    const vertical = calculatePOATransposition(0, 0, 200, 30, 180, 90, 180);
    expect(horizontal.poaDifusa).toBeGreaterThan(vertical.poaDifusa);
  });

  it('vertical surface gets maximum ground-reflected', () => {
    const horizontal = calculatePOATransposition(0, 500, 0, 30, 180, 0, 180, 0.2);
    const vertical = calculatePOATransposition(0, 500, 0, 30, 180, 90, 180, 0.2);
    expect(vertical.poaReflejada).toBeGreaterThan(horizontal.poaReflejada);
  });

  it('higher albedo increases reflected component', () => {
    const lowAlbedo = calculatePOATransposition(500, 600, 200, 30, 180, 45, 180, 0.1);
    const highAlbedo = calculatePOATransposition(500, 600, 200, 30, 180, 45, 180, 0.5);
    expect(highAlbedo.poaReflejada).toBeGreaterThan(lowAlbedo.poaReflejada);
  });
});

// ─── evaluateObstacleShading ──────────────────────────────────────────────────

describe('evaluateObstacleShading', () => {
  const obstacles = [
    { azimutInicio: 150, azimutFin: 210, alturaAngular: 30 },
  ];

  it('returns 1.0 (no shade) when sun is above obstacle', () => {
    expect(evaluateObstacleShading(180, 45, obstacles)).toBe(1.0);
  });

  it('returns 0.0 (shaded) when sun is below obstacle angular height', () => {
    expect(evaluateObstacleShading(180, 20, obstacles)).toBe(0.0);
  });

  it('returns 1.0 when sun is outside obstacle azimuth range', () => {
    expect(evaluateObstacleShading(90, 10, obstacles)).toBe(1.0);
  });

  it('returns 0.0 when sun is below horizon', () => {
    expect(evaluateObstacleShading(180, -5, obstacles)).toBe(0.0);
  });

  it('returns 1.0 with no obstacles', () => {
    expect(evaluateObstacleShading(180, 30, [])).toBe(1.0);
  });
});

// ─── BIPV Glass Catalog ───────────────────────────────────────────────────────

describe('BIPV Glass Catalog', () => {
  it('contains at least one technology per generation', () => {
    const gen1 = getTechnologiesByGeneration('1G');
    const gen2 = getTechnologiesByGeneration('2G');
    const gen3 = getTechnologiesByGeneration('3G');
    expect(gen1.length).toBeGreaterThanOrEqual(1);
    expect(gen2.length).toBeGreaterThanOrEqual(1);
    expect(gen3.length).toBeGreaterThanOrEqual(1);
  });

  it('all technologies have valid efficiency ranges', () => {
    for (const tech of BIPV_GLASS_CATALOG) {
      expect(tech.eficienciaBase).toBeGreaterThan(0);
      expect(tech.eficienciaBase).toBeLessThan(0.50); // No tech exceeds 50%
    }
  });

  it('all technologies have valid b0Ashrae in [0.01, 0.20]', () => {
    for (const tech of BIPV_GLASS_CATALOG) {
      expect(tech.b0Ashrae).toBeGreaterThanOrEqual(0.01);
      expect(tech.b0Ashrae).toBeLessThanOrEqual(0.20);
    }
  });

  it('all technologies have negative temperature coefficient', () => {
    for (const tech of BIPV_GLASS_CATALOG) {
      expect(tech.coefTemperatura).toBeLessThan(0);
    }
  });

  it('all technologies have NOCT in [40, 55]°C', () => {
    for (const tech of BIPV_GLASS_CATALOG) {
      expect(tech.noct).toBeGreaterThanOrEqual(40);
      expect(tech.noct).toBeLessThanOrEqual(55);
    }
  });

  it('getTechnologyById returns correct technology', () => {
    const tech = getTechnologyById('1G_Silicio_Amorfo');
    expect(tech).toBeDefined();
    expect(tech!.generation).toBe('1G');
  });

  it('getTechnologyById returns undefined for invalid id', () => {
    expect(getTechnologyById('nonexistent')).toBeUndefined();
  });

  it('all technology IDs are unique', () => {
    const ids = BIPV_GLASS_CATALOG.map(t => t.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe('Transparency Levels', () => {
  it('all levels are between 0 and 1', () => {
    for (const level of TRANSPARENCY_LEVELS) {
      expect(level.value).toBeGreaterThanOrEqual(0);
      expect(level.value).toBeLessThan(1);
    }
  });

  it('levels are sorted ascending', () => {
    for (let i = 1; i < TRANSPARENCY_LEVELS.length; i++) {
      expect(TRANSPARENCY_LEVELS[i].value).toBeGreaterThan(TRANSPARENCY_LEVELS[i - 1].value);
    }
  });

  it('all levels have a label and description', () => {
    for (const level of TRANSPARENCY_LEVELS) {
      expect(level.label).toBeTruthy();
      expect(level.description).toBeTruthy();
    }
  });
});

describe('Soiling Presets', () => {
  it('all presets have 12 monthly factors', () => {
    for (const preset of SOILING_PRESETS) {
      const keys = Object.keys(preset.config.monthlyFactors).map(Number);
      expect(keys.length).toBe(12);
      for (let m = 1; m <= 12; m++) {
        expect(keys).toContain(m);
      }
    }
  });

  it('all monthly factors are in [0, 0.30]', () => {
    for (const preset of SOILING_PRESETS) {
      for (let m = 1; m <= 12; m++) {
        const factor = preset.config.monthlyFactors[m];
        expect(factor).toBeGreaterThanOrEqual(0);
        expect(factor).toBeLessThanOrEqual(0.30);
      }
    }
  });

  it('getSoilingPresetById returns correct preset', () => {
    const preset = getSoilingPresetById('tropical_urbano');
    expect(preset).toBeDefined();
    expect(preset!.name).toContain('Tropical');
  });

  it('auto-wash reduction is in [0, 1]', () => {
    for (const preset of SOILING_PRESETS) {
      expect(preset.config.autoWashReduction).toBeGreaterThanOrEqual(0);
      expect(preset.config.autoWashReduction).toBeLessThanOrEqual(1);
    }
  });
});

describe('Thermal Mounting Types', () => {
  it('all kBipv values are in [0.8, 2.0]', () => {
    for (const mount of THERMAL_MOUNTING_TYPES) {
      expect(mount.kBipv).toBeGreaterThanOrEqual(0.8);
      expect(mount.kBipv).toBeLessThanOrEqual(2.0);
    }
  });

  it('getMountingTypeById returns correct type', () => {
    const mount = getMountingTypeById('fachada_confinada');
    expect(mount).toBeDefined();
    expect(mount!.kBipv).toBeGreaterThan(1.0);
  });
});
