/**
 * Tests unitarios para crossValidation.ts
 * Funciones: buildComparisonData, deltaPct, calcRMSE, calcMAE, calcR2, calcMeanDeltaPct, exportComparisonCSV
 */
import { describe, it, expect } from 'vitest';
import {
  deltaPct,
  calcRMSE,
  calcMAE,
  calcR2,
  calcMeanDeltaPct,
  buildComparisonData,
  exportComparisonCSV,
} from '../client/src/lib/crossValidation';
import type { AnnualProduction } from '../client/src/lib/energyProduction';
import type { PVWattsToSimulatorData } from '../client/src/components/PVWattsSatellite';
import type { PVGISToSimulatorData } from '../client/src/components/PVGISAnalyzer';

// ============================================================
// HELPERS PARA CREAR DATOS DE PRUEBA
// ============================================================

function makeSimProduction(acPerMonth: number = 500, dcPerMonth: number = 550): AnnualProduction {
  const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
  const monthlyData = months.map((month, i) => ({
    month,
    avgTemp: 25 + (i % 3),
    avgPOA: 180 + (i * 5),
    rawPOA: 200 + (i * 5),
    cellTemperature: 40 + (i % 4),
    panelEfficiency: 19.5,
    dcPower: dcPerMonth * 1000 / (30 * 24),
    acPower: acPerMonth * 1000 / (30 * 24),
    energyProduced: acPerMonth,
    dcEnergy: dcPerMonth,
    referenceEnergy: acPerMonth / 0.82,
    losses: {
      temperature: 5, dcWiring: 2, inverter: 3, acWiring: 1,
      mismatch: 1, soiling: 2, shading: 3, availability: 1,
    },
  }));

  return {
    totalDCEnergy: dcPerMonth * 12,
    totalACEnergy: acPerMonth * 12,
    totalReferenceEnergy: (acPerMonth / 0.82) * 12,
    systemEfficiency: 90,
    performanceRatio: 82,
    prTemperatureCorrected: 85,
    capacityFactor: 18,
    specificYield: 1500,
    iec61724: {
      referenceYield: 1800,
      finalYield: 1500,
      arrayYield: 1650,
      captureLosses: 150,
      captureLossesBreakdown: { temperature: 50, shading: 30, soiling: 20, mismatch: 15, dcWiring: 10, total: 125 },
      systemLosses: 150,
      performanceRatio: 0.82,
      prTemperatureCorrected: 0.85,
      specificYield: 1500,
      bosEfficiency: 0.91,
      energyPerformanceIndex: null,
    },
    monthlyData,
    losses: {
      temperature: 5, dcWiring: 2, inverter: 3, acWiring: 1,
      mismatch: 1, soiling: 2, shading: 3, availability: 1, total: 18,
    },
  };
}

function makePVWattsData(acPerMonth: number = 520): PVWattsToSimulatorData {
  return {
    latitude: 6.25,
    longitude: -75.56,
    tilt: 10,
    azimuth: 180,
    systemCapacity: 5,
    losses: 14,
    arrayType: 0,
    moduleType: 0,
    annualAC_kWh: acPerMonth * 12,
    annualDC_kWh: acPerMonth * 12 * 1.1,
    annualPOA_kWhm2: 1900,
    annualGHI_kWhm2: 1800,
    specificYield: acPerMonth * 12 / 5,
    capacityFactor: 18,
    monthlyData: Array.from({ length: 12 }, (_, i) => ({
      month: i + 1,
      monthName: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'][i],
      ac_kWh: acPerMonth + (i * 5 - 30),
      dc_kWh: (acPerMonth + (i * 5 - 30)) * 1.1,
      poa_kWhm2: 150 + (i * 3),
      tamb_C: 24 + (i % 3),
      tcell_C: 38 + (i % 4),
      wspd_ms: 2.5,
    })),
    stationCity: 'Medellín',
    stationDistance: 5,
    weatherSource: 'NSRDB TMY',
  };
}

function makePVGISData(acPerMonth: number = 510): PVGISToSimulatorData {
  return {
    latitude: 6.25,
    longitude: -75.56,
    tilt: 10,
    azimuth: 180,
    peakPowerKwp: 5,
    systemLoss: 14,
    technology: 'crystSi',
    panelName: 'c-Si Genérico',
    annualProductionAC: acPerMonth * 12,
    annualProductionCorrected: acPerMonth * 12 * 0.98,
    annualIrradiationPOA: 1850,
    correctionFactor: 0.98,
    monthlyData: Array.from({ length: 12 }, (_, i) => ({
      month: i + 1,
      productionAC_kWh: acPerMonth + (i * 4 - 25),
      productionCorrectedAC_kWh: (acPerMonth + (i * 4 - 25)) * 0.98,
      irradiationPOA_kWhm2: 145 + (i * 3),
      temperature: 23 + (i % 3),
    })),
    radiationDB: 'PVGIS-ERA5',
    yearMin: 2005,
    yearMax: 2020,
  };
}

// ============================================================
// TESTS: deltaPct
// ============================================================

describe('deltaPct', () => {
  it('calcula Δ% correctamente', () => {
    expect(deltaPct(110, 100)).toBeCloseTo(10, 1);
    expect(deltaPct(90, 100)).toBeCloseTo(-10, 1);
    expect(deltaPct(100, 100)).toBeCloseTo(0, 1);
  });

  it('retorna null cuando b ≈ 0', () => {
    expect(deltaPct(100, 0)).toBeNull();
    expect(deltaPct(100, 0.005)).toBeNull();
  });

  it('retorna null cuando a o b es null', () => {
    expect(deltaPct(null, 100)).toBeNull();
    expect(deltaPct(100, null)).toBeNull();
    expect(deltaPct(null, null)).toBeNull();
  });
});

// ============================================================
// TESTS: calcRMSE
// ============================================================

describe('calcRMSE', () => {
  it('calcula RMSE correctamente con valores conocidos', () => {
    // RMSE([10,20,30], [12,18,33]) = sqrt(((10-12)²+(20-18)²+(30-33)²)/3) = sqrt((4+4+9)/3) = sqrt(17/3) ≈ 2.38
    const rmse = calcRMSE([10, 20, 30], [12, 18, 33]);
    expect(rmse).toBeCloseTo(2.38, 1);
  });

  it('retorna 0 para arrays idénticos', () => {
    expect(calcRMSE([100, 200, 300], [100, 200, 300])).toBeCloseTo(0, 5);
  });

  it('ignora pares con null', () => {
    const rmse = calcRMSE([10, null, 30], [12, 18, 33]);
    // Solo usa pares (10,12) y (30,33): sqrt((4+9)/2) = sqrt(6.5) ≈ 2.55
    expect(rmse).toBeCloseTo(2.55, 1);
  });

  it('retorna null para arrays vacíos', () => {
    expect(calcRMSE([], [])).toBeNull();
  });

  it('retorna null si todos son null', () => {
    expect(calcRMSE([null, null], [null, null])).toBeNull();
  });
});

// ============================================================
// TESTS: calcMAE
// ============================================================

describe('calcMAE', () => {
  it('calcula MAE correctamente', () => {
    // MAE([10,20,30], [12,18,33]) = (|10-12|+|20-18|+|30-33|)/3 = (2+2+3)/3 ≈ 2.33
    const mae = calcMAE([10, 20, 30], [12, 18, 33]);
    expect(mae).toBeCloseTo(2.33, 1);
  });

  it('retorna 0 para arrays idénticos', () => {
    expect(calcMAE([100, 200, 300], [100, 200, 300])).toBeCloseTo(0, 5);
  });

  it('retorna null para arrays vacíos', () => {
    expect(calcMAE([], [])).toBeNull();
  });
});

// ============================================================
// TESTS: calcR2
// ============================================================

describe('calcR2', () => {
  it('retorna R² ≈ 1 para correlación perfecta', () => {
    const r2 = calcR2([10, 20, 30, 40, 50], [10, 20, 30, 40, 50]);
    expect(r2).toBeCloseTo(1.0, 3);
  });

  it('retorna R² alto para correlación fuerte', () => {
    // a ≈ b con pequeña diferencia
    const r2 = calcR2([10, 20, 30, 40, 50], [11, 19, 31, 39, 51]);
    expect(r2).toBeGreaterThan(0.95);
  });

  it('retorna null con menos de 3 pares', () => {
    expect(calcR2([10, 20], [10, 20])).toBeNull();
  });

  it('retorna null si varianza de b ≈ 0', () => {
    expect(calcR2([10, 20, 30], [5, 5, 5])).toBeNull();
  });
});

// ============================================================
// TESTS: calcMeanDeltaPct
// ============================================================

describe('calcMeanDeltaPct', () => {
  it('calcula Δ% medio correctamente', () => {
    // deltaPct(110,100)=10%, deltaPct(90,100)=-10% → media = 0%
    const mean = calcMeanDeltaPct([110, 90], [100, 100]);
    expect(mean).toBeCloseTo(0, 1);
  });

  it('retorna null si no hay pares válidos', () => {
    expect(calcMeanDeltaPct([null, null], [null, null])).toBeNull();
  });
});

// ============================================================
// TESTS: buildComparisonData
// ============================================================

describe('buildComparisonData', () => {
  it('retorna 12 filas mensuales', () => {
    const sim = makeSimProduction();
    const pvw = makePVWattsData();
    const result = buildComparisonData(sim, pvw, null, null, null);
    expect(result.rows).toHaveLength(12);
  });

  it('detecta correctamente las fuentes disponibles', () => {
    const sim = makeSimProduction();
    const pvw = makePVWattsData();
    const pvg = makePVGISData();

    const r1 = buildComparisonData(sim, pvw, null, null, null);
    expect(r1.hasPVWatts).toBe(true);
    expect(r1.hasPVGIS).toBe(false);
    expect(r1.sourceCount).toBe(2);

    const r2 = buildComparisonData(sim, null, pvg, null, null);
    expect(r2.hasPVWatts).toBe(false);
    expect(r2.hasPVGIS).toBe(true);
    expect(r2.sourceCount).toBe(2);

    const r3 = buildComparisonData(sim, pvw, pvg, null, null);
    expect(r3.hasPVWatts).toBe(true);
    expect(r3.hasPVGIS).toBe(true);
    expect(r3.sourceCount).toBe(3);
  });

  it('calcula Δ% entre fuentes', () => {
    const sim = makeSimProduction(500);
    const pvw = makePVWattsData(520);
    const result = buildComparisonData(sim, pvw, null, null, null);
    // Cada mes tiene delta_sim_pvw_pct
    for (const row of result.rows) {
      if (row.simulator.ac_kWh !== null && row.pvwatts.ac_kWh !== null && Math.abs(row.pvwatts.ac_kWh) > 0.01) {
        expect(row.delta_sim_pvw_pct).not.toBeNull();
      }
    }
  });

  it('incluye resúmenes anuales correctos', () => {
    const sim = makeSimProduction(500);
    const pvw = makePVWattsData(520);
    const result = buildComparisonData(sim, pvw, null, null, null);

    expect(result.annualSimulator.ac_kWh).toBe(6000); // 500 × 12
    expect(result.annualPVWatts.ac_kWh).toBe(520 * 12);
  });

  it('calcula estadísticas RMSE, MAE, R² entre pares', () => {
    const sim = makeSimProduction(500);
    const pvw = makePVWattsData(520);
    const pvg = makePVGISData(510);
    const result = buildComparisonData(sim, pvw, pvg, null, null);

    expect(result.stats.sim_vs_pvwatts.rmse).not.toBeNull();
    expect(result.stats.sim_vs_pvwatts.mae).not.toBeNull();
    expect(result.stats.sim_vs_pvwatts.r2).not.toBeNull();
    expect(result.stats.sim_vs_pvwatts.n).toBe(12);

    expect(result.stats.sim_vs_pvgis.rmse).not.toBeNull();
    expect(result.stats.pvwatts_vs_pvgis.rmse).not.toBeNull();
  });

  it('los datos del simulador siempre están presentes', () => {
    const sim = makeSimProduction(500);
    const result = buildComparisonData(sim, makePVWattsData(), null, null, null);
    for (const row of result.rows) {
      expect(row.simulator.ac_kWh).not.toBeNull();
      expect(row.simulator.dc_kWh).not.toBeNull();
      expect(row.simulator.tamb_C).not.toBeNull();
      expect(row.simulator.tcell_C).not.toBeNull();
    }
  });

  it('PVGIS no tiene DC (es null)', () => {
    const sim = makeSimProduction();
    const pvg = makePVGISData();
    const result = buildComparisonData(sim, null, pvg, null, null);
    for (const row of result.rows) {
      expect(row.pvgis.dc_kWh).toBeNull();
    }
  });

  it('delta_pvw_pvg_pct es null cuando falta una fuente', () => {
    const sim = makeSimProduction();
    const pvw = makePVWattsData();
    const result = buildComparisonData(sim, pvw, null, null, null);
    for (const row of result.rows) {
      expect(row.delta_pvw_pvg_pct).toBeNull();
    }
  });
});

// ============================================================
// TESTS: exportComparisonCSV
// ============================================================

describe('exportComparisonCSV', () => {
  it('genera CSV con BOM UTF-8', () => {
    const sim = makeSimProduction();
    const pvw = makePVWattsData();
    const result = buildComparisonData(sim, pvw, null, null, null);
    const csv = exportComparisonCSV(result);
    expect(csv.startsWith('\uFEFF')).toBe(true);
  });

  it('tiene 14 líneas (1 header + 12 meses + 1 anual)', () => {
    const sim = makeSimProduction();
    const pvw = makePVWattsData();
    const result = buildComparisonData(sim, pvw, null, null, null);
    const csv = exportComparisonCSV(result);
    const lines = csv.split('\n');
    expect(lines).toHaveLength(14);
  });

  it('incluye columnas PVWatts cuando hay datos PVWatts', () => {
    const sim = makeSimProduction();
    const pvw = makePVWattsData();
    const result = buildComparisonData(sim, pvw, null, null, null);
    const csv = exportComparisonCSV(result);
    expect(csv).toContain('PVW AC');
    expect(csv).toContain('Δ% Sim-PVW');
  });

  it('incluye columnas PVGIS cuando hay datos PVGIS', () => {
    const sim = makeSimProduction();
    const pvg = makePVGISData();
    const result = buildComparisonData(sim, null, pvg, null, null);
    const csv = exportComparisonCSV(result);
    expect(csv).toContain('PVG AC');
    expect(csv).toContain('Δ% Sim-PVG');
  });

  it('incluye columna PVW-PVG cuando hay ambas fuentes', () => {
    const sim = makeSimProduction();
    const pvw = makePVWattsData();
    const pvg = makePVGISData();
    const result = buildComparisonData(sim, pvw, pvg, null, null);
    const csv = exportComparisonCSV(result);
    expect(csv).toContain('Δ% PVW-PVG');
  });

  it('la última línea contiene ANUAL', () => {
    const sim = makeSimProduction();
    const pvw = makePVWattsData();
    const result = buildComparisonData(sim, pvw, null, null, null);
    const csv = exportComparisonCSV(result);
    const lines = csv.split('\n');
    expect(lines[lines.length - 1]).toContain('ANUAL');
  });
});
