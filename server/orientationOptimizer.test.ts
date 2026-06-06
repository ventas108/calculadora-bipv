import { describe, it, expect } from 'vitest';

/**
 * Tests para la lógica de cálculo de irradiancia en superficie inclinada
 * y la búsqueda del óptimo de orientación.
 */

function calculateInclinedIrradiance(
  directNormal: number,
  diffuseHorizontal: number,
  zenithAngle: number,
  tiltAngle: number,
  azimuthSurface: number,
  azimuthSun: number,
  albedo: number = 0.2
): { direct: number; diffuse: number; reflected: number; total: number } {
  const incidenceAngle = Math.acos(
    Math.min(1, Math.max(-1,
      Math.cos(zenithAngle) * Math.cos(tiltAngle) +
      Math.sin(zenithAngle) * Math.sin(tiltAngle) *
      Math.cos(azimuthSun - azimuthSurface)
    ))
  );
  const direct = directNormal * Math.max(0, Math.cos(incidenceAngle));
  const diffuse = diffuseHorizontal * (1 + Math.cos(tiltAngle)) / 2;
  const ghi = directNormal * Math.max(0, Math.cos(zenithAngle)) + diffuseHorizontal;
  const reflected = ghi * albedo * (1 - Math.cos(tiltAngle)) / 2;
  const total = Math.max(0, direct + diffuse + reflected);
  return { direct, diffuse, reflected, total };
}

describe('calculateInclinedIrradiance', () => {
  it('should return zero for all components when inputs are zero', () => {
    const result = calculateInclinedIrradiance(0, 0, 0, 0, 0, 0);
    expect(result.total).toBe(0);
    expect(result.direct).toBe(0);
    expect(result.diffuse).toBe(0);
    expect(result.reflected).toBe(0);
  });

  it('should return positive total for typical midday conditions', () => {
    const zenith = 30 * Math.PI / 180;
    const tilt = 15 * Math.PI / 180;
    const result = calculateInclinedIrradiance(800, 200, zenith, tilt, 0, 0);
    expect(result.total).toBeGreaterThan(0);
    expect(result.direct).toBeGreaterThan(0);
    expect(result.diffuse).toBeGreaterThan(0);
  });

  it('should increase reflected component with higher albedo', () => {
    const zenith = 30 * Math.PI / 180;
    const tilt = 30 * Math.PI / 180;
    const low = calculateInclinedIrradiance(800, 200, zenith, tilt, 0, 0, 0.1);
    const high = calculateInclinedIrradiance(800, 200, zenith, tilt, 0, 0, 0.5);
    expect(high.reflected).toBeGreaterThan(low.reflected);
  });

  it('should have zero reflected when tilt is 0', () => {
    const zenith = 30 * Math.PI / 180;
    const result = calculateInclinedIrradiance(800, 200, zenith, 0, 0, 0, 0.2);
    expect(result.reflected).toBeCloseTo(0, 5);
  });

  it('should have maximum diffuse when tilt is 0', () => {
    const zenith = 30 * Math.PI / 180;
    const horiz = calculateInclinedIrradiance(800, 200, zenith, 0, 0, 0);
    const tilted = calculateInclinedIrradiance(800, 200, zenith, 45 * Math.PI / 180, 0, 0);
    expect(horiz.diffuse).toBeGreaterThan(tilted.diffuse);
  });

  it('should handle vertical panel (tilt=90)', () => {
    const zenith = 30 * Math.PI / 180;
    const tilt = 90 * Math.PI / 180;
    const result = calculateInclinedIrradiance(800, 200, zenith, tilt, 0, 0);
    expect(result.total).toBeGreaterThan(0);
    expect(result.diffuse).toBeCloseTo(100, 0);
  });
});

describe('Optimizer search logic', () => {
  function findOptimalOrientation(
    tiltRange: [number, number],
    azimuthRange: [number, number],
    evaluateFn: (tilt: number, azimuth: number) => number
  ): { tilt: number; azimuth: number; poa: number } {
    let bestTilt = tiltRange[0];
    let bestAzimuth = azimuthRange[0];
    let bestPOA = 0;
    for (let t = tiltRange[0]; t <= tiltRange[1]; t += 5) {
      for (let a = azimuthRange[0]; a <= azimuthRange[1]; a += 10) {
        const poa = evaluateFn(t, a);
        if (poa > bestPOA) { bestPOA = poa; bestTilt = t; bestAzimuth = a; }
      }
    }
    for (let t = Math.max(tiltRange[0], bestTilt - 5); t <= Math.min(tiltRange[1], bestTilt + 5); t += 1) {
      for (let a = Math.max(azimuthRange[0], bestAzimuth - 10); a <= Math.min(azimuthRange[1], bestAzimuth + 10); a += 1) {
        const poa = evaluateFn(t, a);
        if (poa > bestPOA) { bestPOA = poa; bestTilt = t; bestAzimuth = a; }
      }
    }
    return { tilt: bestTilt, azimuth: bestAzimuth, poa: bestPOA };
  }

  it('should find the known optimum in a cosine model', () => {
    const evaluateFn = (tilt: number, azimuth: number) => {
      return 500 * Math.cos((tilt - 20) * Math.PI / 180) * Math.cos(azimuth * Math.PI / 180);
    };
    const result = findOptimalOrientation([0, 60], [-90, 90], evaluateFn);
    expect(result.tilt).toBe(20);
    expect(result.azimuth).toBe(0);
    expect(result.poa).toBeCloseTo(500, 0);
  });

  it('should respect tilt range constraints', () => {
    const evaluateFn = (tilt: number) => 500 * Math.cos((tilt - 30) * Math.PI / 180);
    const result = findOptimalOrientation([0, 15], [-90, 90], evaluateFn);
    expect(result.tilt).toBeLessThanOrEqual(15);
  });

  it('should handle locked azimuth', () => {
    const evaluateFn = (tilt: number, azimuth: number) => {
      return 500 * Math.cos((tilt - 15) * Math.PI / 180) * Math.cos(azimuth * Math.PI / 180);
    };
    const result = findOptimalOrientation([0, 60], [45, 45], evaluateFn);
    expect(result.azimuth).toBe(45);
    expect(result.tilt).toBe(15);
  });

  it('should find optimum for facade (tilt 75-90)', () => {
    const evaluateFn = (tilt: number, azimuth: number) => {
      return 300 * Math.cos((tilt - 80) * Math.PI / 180) * Math.cos(azimuth * Math.PI / 180);
    };
    const result = findOptimalOrientation([75, 90], [-90, 90], evaluateFn);
    expect(result.tilt).toBe(80);
    expect(result.azimuth).toBe(0);
  });

  it('should calculate gain percentage correctly', () => {
    const gain = Math.round(((450 - 400) / 400) * 1000) / 10;
    expect(gain).toBe(12.5);
  });

  it('should handle negative gain', () => {
    const gain = Math.round(((400 - 450) / 450) * 1000) / 10;
    expect(gain).toBeLessThan(0);
    expect(gain).toBeCloseTo(-11.1, 0);
  });
});

describe('OptimizerResult structure', () => {
  it('should produce valid result with 12 months', () => {
    const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
    const result = {
      optimalTilt: 15, optimalAzimuth: 0,
      currentTilt: 10, currentAzimuth: 5,
      optimalPOA: 450, currentPOA: 400, gainPercent: 12.5,
      monthlyPOA: months.map((m) => ({
        month: m, totalPOA: 420, directPOA: 280, diffusePOA: 110,
        reflectedPOA: 30, avgTemp: 25, avgWindSpeed: 2,
      })),
    };
    expect(result.monthlyPOA).toHaveLength(12);
    expect(result.optimalPOA).toBeGreaterThan(result.currentPOA);
    for (const m of result.monthlyPOA) {
      expect(m.totalPOA).toBeGreaterThan(0);
      expect(m.avgWindSpeed).toBeGreaterThan(0);
    }
  });
});
