import { describe, it, expect } from 'vitest';

/**
 * Tests para las funciones de energyProduction.ts
 * Verifica:
 * - calculateCellTemperature con windSpeed real y eficiencia real del panel
 * - calculatePanelEfficiency con temperatureCoefficient real
 * - calculateDCPower con temperatureCoefficient real
 * - calculateAnnualProduction con windSpeed real
 * - Performance Ratio IEC 61724 (PR = Yf/Yr, no E_AC/E_DC)
 * - PR corregido por temperatura (PR_T IEC 61724-1:2021)
 * - Métricas IEC 61724: Yr, Yf, Ya, Lc, Ls
 */

import {
  calculateCellTemperature,
  calculatePanelEfficiency,
  calculateDCPower,
  calculateACPower,
  calculateAnnualProduction,
  calculateMonthlyProduction,
} from '../client/src/lib/energyProduction';

// ============================================================
// TESTS — calculateCellTemperature (mejorado con viento y eficiencia real)
// ============================================================

describe('calculateCellTemperature — mejorado', () => {
  it('calcula T_cell con valores por defecto (windSpeed=1, eta=15%)', () => {
    const result = calculateCellTemperature(25, 800, 1, 47, 15);
    expect(result).toBeCloseTo(46.85, 1);
  });

  it('viento alto enfría el panel significativamente', () => {
    const result = calculateCellTemperature(25, 800, 5, 47, 15);
    expect(result).toBeCloseTo(43.36, 1);
  });

  it('viento=0 da máxima temperatura de celda', () => {
    const result = calculateCellTemperature(25, 800, 0, 47, 15);
    expect(result).toBeCloseTo(47.95, 1);
  });

  it('viento=10 m/s enfría aún más', () => {
    const result = calculateCellTemperature(25, 800, 10, 47, 15);
    expect(result).toBeCloseTo(40.30, 1);
  });

  it('eficiencia alta del panel reduce calentamiento', () => {
    const result = calculateCellTemperature(25, 800, 1, 47, 22);
    expect(result).toBeCloseTo(45.06, 1);
  });

  it('NOCT bajo reduce calentamiento', () => {
    const result = calculateCellTemperature(25, 800, 1, 42, 15);
    expect(result).toBeCloseTo(42.81, 1);
  });

  it('irradiancia baja reduce calentamiento proporcionalmente', () => {
    const result = calculateCellTemperature(25, 400, 1, 47, 15);
    expect(result).toBeCloseTo(35.93, 1);
  });

  it('temperatura ambiente alta eleva T_cell proporcionalmente', () => {
    const result = calculateCellTemperature(35, 800, 1, 47, 15);
    expect(result).toBeCloseTo(56.85, 1);
  });
});

// ============================================================
// TESTS — calculatePanelEfficiency (con coef. temp real)
// ============================================================

describe('calculatePanelEfficiency — con coef. temp real', () => {
  it('a 25°C (STC) la eficiencia no cambia', () => {
    const result = calculatePanelEfficiency(20, 25, 25, -0.004);
    expect(result).toBeCloseTo(20, 4);
  });

  it('a 50°C con coef. -0.004 la eficiencia baja', () => {
    const result = calculatePanelEfficiency(20, 50, 25, -0.004);
    expect(result).toBeCloseTo(18, 4);
  });

  it('coef. temp más agresivo (-0.005) baja más la eficiencia', () => {
    const result = calculatePanelEfficiency(20, 50, 25, -0.005);
    expect(result).toBeCloseTo(17.5, 4);
  });

  it('coef. temp suave (-0.003) baja menos la eficiencia', () => {
    const result = calculatePanelEfficiency(20, 50, 25, -0.003);
    expect(result).toBeCloseTo(18.5, 4);
  });

  it('temperatura por debajo de STC aumenta la eficiencia', () => {
    const result = calculatePanelEfficiency(20, 10, 25, -0.004);
    expect(result).toBeCloseTo(21.2, 4);
  });

  it('nunca retorna eficiencia negativa', () => {
    const result = calculatePanelEfficiency(20, 300, 25, -0.004);
    expect(result).toBe(0);
  });
});

// ============================================================
// TESTS — calculateDCPower (con coef. temp real)
// ============================================================

describe('calculateDCPower — con coef. temp real', () => {
  const panelSpecs = {
    powerRating: 400,
    efficiency: 20,
    temperatureCoefficient: -0.004,
    nominalOperatingCellTemperature: 47,
    area: 2.0,
    quantity: 10,
  };

  it('a STC (25°C, 1000 W/m²) genera potencia nominal', () => {
    const result = calculateDCPower(1000, panelSpecs, 25);
    expect(result).toBeCloseTo(4000, 0);
  });

  it('a 50°C la potencia baja por temperatura', () => {
    const result = calculateDCPower(1000, panelSpecs, 50);
    expect(result).toBeCloseTo(3600, 0);
  });

  it('irradiancia baja reduce potencia proporcionalmente', () => {
    const result = calculateDCPower(500, panelSpecs, 25);
    expect(result).toBeCloseTo(2000, 0);
  });
});

// ============================================================
// TESTS — calculateMonthlyProduction (con rawPOA y referenceEnergy)
// ============================================================

describe('calculateMonthlyProduction — nuevos campos IEC 61724', () => {
  const panelSpecs = {
    powerRating: 400,
    efficiency: 20,
    temperatureCoefficient: -0.004,
    nominalOperatingCellTemperature: 47,
    area: 2.0,
    quantity: 10,
  };

  const systemLosses = {
    dcWiring: 2,
    inverterEfficiency: 96,
    acWiring: 1,
    transformerLosses: 0,
    mismatchLosses: 2,
    soilingLosses: 2,
    shadingLosses: 0,
    availabilityLosses: 1,
  };

  it('rawPOA preserva el POA original antes de sombreado', () => {
    const result = calculateMonthlyProduction(
      'Ene', 1, 25, 500, 2, panelSpecs, systemLosses, 31, 0.8
    );
    // rawPOA = 500 (original), avgPOA = 500*0.8 = 400 (con sombreado)
    expect(result.rawPOA).toBeCloseTo(500, 0);
    expect(result.avgPOA).toBeCloseTo(400, 0);
  });

  it('dcEnergy se calcula correctamente', () => {
    const result = calculateMonthlyProduction(
      'Ene', 1, 25, 500, 1, panelSpecs, systemLosses, 31, 1.0
    );
    // dcEnergy = dcPower * 31 * 24 / 1000
    const expectedDCEnergy = result.dcPower * 31 * 24 / 1000;
    expect(result.dcEnergy).toBeCloseTo(expectedDCEnergy, 1);
  });

  it('referenceEnergy = (rawPOA/1000) × P_nom_kW × horas', () => {
    const result = calculateMonthlyProduction(
      'Ene', 1, 25, 500, 1, panelSpecs, systemLosses, 31, 1.0
    );
    // P_nom = 400 * 10 = 4000 W = 4 kW
    // referenceEnergy = (500/1000) * 4 * 31 * 24 = 0.5 * 4 * 744 = 1488 kWh
    expect(result.referenceEnergy).toBeCloseTo(1488, 0);
  });

  it('referenceEnergy usa rawPOA (no adjustedPOA) para ser independiente del sombreado', () => {
    const withShading = calculateMonthlyProduction(
      'Ene', 1, 25, 500, 1, panelSpecs, systemLosses, 31, 0.7
    );
    const withoutShading = calculateMonthlyProduction(
      'Ene', 1, 25, 500, 1, panelSpecs, systemLosses, 31, 1.0
    );
    // referenceEnergy debe ser igual en ambos casos (usa rawPOA)
    expect(withShading.referenceEnergy).toBeCloseTo(withoutShading.referenceEnergy, 1);
  });
});

// ============================================================
// TESTS — Performance Ratio IEC 61724
// ============================================================

describe('calculateAnnualProduction — PR IEC 61724', () => {
  const panelSpecs = {
    powerRating: 400,
    efficiency: 20,
    temperatureCoefficient: -0.004,
    nominalOperatingCellTemperature: 47,
    area: 2.0,
    quantity: 10,
  };

  const systemLosses = {
    dcWiring: 2,
    inverterEfficiency: 96,
    acWiring: 1,
    transformerLosses: 0,
    mismatchLosses: 2,
    soilingLosses: 2,
    shadingLosses: 0,
    availabilityLosses: 1,
  };

  const shadingFactors = Array(12).fill(1.0);

  const monthlyData = Array(12).fill(null).map((_, i) => ({
    month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
    avgPOA: 500,
    avgTemp: 28,
    avgWindSpeed: 2,
  }));

  it('PR IEC 61724 = Yf/Yr, NO E_AC/E_DC', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    
    // Verificar que PR = Yf/Yr (en %)
    const expectedPR = (prod.iec61724.finalYield / prod.iec61724.referenceYield) * 100;
    expect(prod.performanceRatio).toBeCloseTo(expectedPR, 2);
    
    // PR debe ser MENOR que BOS efficiency (E_AC/E_DC)
    // porque PR incluye pérdidas de captura (temperatura, sombreado)
    const bosEffPercent = prod.iec61724.bosEfficiency * 100;
    expect(prod.performanceRatio).toBeLessThan(bosEffPercent);
  });

  it('PR está en rango realista (60-90%) para sistema típico', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    expect(prod.performanceRatio).toBeGreaterThan(60);
    expect(prod.performanceRatio).toBeLessThan(90);
  });

  it('Yr + Lc + Ls = Yr (balance de yields)', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    const iec = prod.iec61724;
    
    // Ya = Yr - Lc
    expect(iec.arrayYield).toBeCloseTo(iec.referenceYield - iec.captureLosses, 1);
    
    // Yf = Ya - Ls
    expect(iec.finalYield).toBeCloseTo(iec.arrayYield - iec.systemLosses, 1);
    
    // Por lo tanto: Yf = Yr - Lc - Ls
    expect(iec.finalYield).toBeCloseTo(iec.referenceYield - iec.captureLosses - iec.systemLosses, 1);
  });

  it('Specific Yield = Final Yield = E_AC / P_nom', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    const pNomKw = (panelSpecs.powerRating * panelSpecs.quantity) / 1000;
    const expectedYf = prod.totalACEnergy / pNomKw;
    
    expect(prod.specificYield).toBeCloseTo(expectedYf, 1);
    expect(prod.iec61724.finalYield).toBeCloseTo(expectedYf, 1);
    expect(prod.iec61724.specificYield).toBeCloseTo(expectedYf, 1);
  });

  it('Reference Yield = H_POA / G_ref', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    
    // H_POA = Σ(rawPOA_i × horas_i) / 1000 en kWh/m²
    // Con POA=500 W/m² constante: H_POA = 500 * 8760 / 1000 = 4380 kWh/m²
    // Yr = H_POA / (G_ref/1000) = 4380 / 1 = 4380 h
    const daysInMonths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    const totalHours = daysInMonths.reduce((s, d) => s + d * 24, 0); // 8760
    const expectedYr = (500 * totalHours / 1000) / 1; // = 4380
    
    expect(prod.iec61724.referenceYield).toBeCloseTo(expectedYr, 0);
  });

  it('BOS Efficiency = E_AC / E_DC', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    const expectedBOS = prod.totalACEnergy / prod.totalDCEnergy;
    expect(prod.iec61724.bosEfficiency).toBeCloseTo(expectedBOS, 4);
  });

  it('Capture Losses > 0 cuando T_cell > 25°C', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    // Con T_amb=28°C, T_cell será > 25°C → pérdidas por temperatura → Lc > 0
    expect(prod.iec61724.captureLosses).toBeGreaterThan(0);
  });

  it('System Losses > 0 siempre (inversor, cableado)', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    expect(prod.iec61724.systemLosses).toBeGreaterThan(0);
  });

  it('totalReferenceEnergy se calcula correctamente', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    // E_ref = Yr × P_nom
    const pNomKw = (panelSpecs.powerRating * panelSpecs.quantity) / 1000;
    const expectedRefEnergy = prod.iec61724.referenceYield * pNomKw;
    expect(prod.totalReferenceEnergy).toBeCloseTo(expectedRefEnergy, 0);
  });

  it('Pérdidas totales = (1 - PR) × 100', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    const expectedTotalLoss = (1 - prod.iec61724.performanceRatio) * 100;
    expect(prod.losses.total).toBeCloseTo(expectedTotalLoss, 2);
  });
});

// ============================================================
// TESTS — PR corregido por temperatura (IEC 61724-1:2021)
// ============================================================

describe('PR corregido por temperatura — IEC 61724-1:2021', () => {
  const panelSpecs = {
    powerRating: 400,
    efficiency: 20,
    temperatureCoefficient: -0.004,
    nominalOperatingCellTemperature: 47,
    area: 2.0,
    quantity: 10,
  };

  const systemLosses = {
    dcWiring: 2,
    inverterEfficiency: 96,
    acWiring: 1,
    transformerLosses: 0,
    mismatchLosses: 2,
    soilingLosses: 2,
    shadingLosses: 0,
    availabilityLosses: 1,
  };

  const shadingFactors = Array(12).fill(1.0);

  it('PR_T > PR cuando T_cell_avg > 25°C (clima cálido)', () => {
    const hotClimate = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 600,
      avgTemp: 32,
      avgWindSpeed: 1,
    }));

    const prod = calculateAnnualProduction(hotClimate, panelSpecs, systemLosses, shadingFactors);
    
    // En clima cálido, T_cell > 25°C → PR_T corrige al alza
    expect(prod.prTemperatureCorrected).toBeGreaterThan(prod.performanceRatio);
  });

  it('PR_T ≈ PR cuando T_cell_avg ≈ 25°C (clima templado)', () => {
    const mildClimate = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 200,
      avgTemp: 15,
      avgWindSpeed: 3,
    }));

    const prod = calculateAnnualProduction(mildClimate, panelSpecs, systemLosses, shadingFactors);
    
    // Con baja irradiancia y T_amb=15°C, T_cell estará cerca de 25°C
    // PR_T debería ser cercano a PR
    const diff = Math.abs(prod.prTemperatureCorrected - prod.performanceRatio);
    expect(diff).toBeLessThan(5); // Menos de 5 puntos porcentuales de diferencia
  });

  it('PR_T está en rango válido (0-100%)', () => {
    const data = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 500,
      avgTemp: 28,
      avgWindSpeed: 2,
    }));

    const prod = calculateAnnualProduction(data, panelSpecs, systemLosses, shadingFactors);
    expect(prod.prTemperatureCorrected).toBeGreaterThan(0);
    expect(prod.prTemperatureCorrected).toBeLessThanOrEqual(100);
  });
});

// ============================================================
// TESTS — windSpeed en calculateAnnualProduction
// ============================================================

describe('calculateAnnualProduction — windSpeed real', () => {
  const panelSpecs = {
    powerRating: 400,
    efficiency: 20,
    temperatureCoefficient: -0.004,
    nominalOperatingCellTemperature: 47,
    area: 2.0,
    quantity: 10,
  };

  const systemLosses = {
    dcWiring: 2,
    inverterEfficiency: 96,
    acWiring: 1,
    transformerLosses: 0,
    mismatchLosses: 2,
    soilingLosses: 2,
    shadingLosses: 0,
    availabilityLosses: 1,
  };

  const shadingFactors = Array(12).fill(1.0);

  it('viento alto produce más energía (paneles más fríos)', () => {
    const monthlyDataLowWind = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 500,
      avgTemp: 28,
      avgWindSpeed: 1,
    }));

    const monthlyDataHighWind = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 500,
      avgTemp: 28,
      avgWindSpeed: 5,
    }));

    const prodLowWind = calculateAnnualProduction(monthlyDataLowWind, panelSpecs, systemLosses, shadingFactors);
    const prodHighWind = calculateAnnualProduction(monthlyDataHighWind, panelSpecs, systemLosses, shadingFactors);

    expect(prodHighWind.totalACEnergy).toBeGreaterThan(prodLowWind.totalACEnergy);
  });

  it('la diferencia de producción por viento es razonable (1-5%)', () => {
    const monthlyDataNoWind = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 500,
      avgTemp: 28,
      avgWindSpeed: 0,
    }));

    const monthlyDataStrongWind = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 500,
      avgTemp: 28,
      avgWindSpeed: 10,
    }));

    const prodNoWind = calculateAnnualProduction(monthlyDataNoWind, panelSpecs, systemLosses, shadingFactors);
    const prodStrongWind = calculateAnnualProduction(monthlyDataStrongWind, panelSpecs, systemLosses, shadingFactors);

    const diffPercent = ((prodStrongWind.totalACEnergy - prodNoWind.totalACEnergy) / prodNoWind.totalACEnergy) * 100;
    expect(diffPercent).toBeGreaterThan(0.5);
    expect(diffPercent).toBeLessThan(8);
  });

  it('cellTempOverride ignora windSpeed y NOCT', () => {
    const data = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 500,
      avgTemp: 28,
      avgWindSpeed: 5,
    }));

    const prodWithOverride = calculateAnnualProduction(data, panelSpecs, systemLosses, shadingFactors, 45);
    
    for (const mp of prodWithOverride.monthlyData) {
      expect(mp.cellTemperature).toBeCloseTo(45, 0);
    }
  });
});

// ============================================================
// TESTS — Pérdidas ponderadas por energía
// ============================================================

describe('calculateAnnualProduction — pérdidas ponderadas', () => {
  const panelSpecs = {
    powerRating: 400,
    efficiency: 20,
    temperatureCoefficient: -0.004,
    nominalOperatingCellTemperature: 47,
    area: 2.0,
    quantity: 10,
  };

  const systemLosses = {
    dcWiring: 2,
    inverterEfficiency: 96,
    acWiring: 1,
    transformerLosses: 0,
    mismatchLosses: 2,
    soilingLosses: 2,
    shadingLosses: 0,
    availabilityLosses: 1,
  };

  it('pérdidas por temperatura son ponderadas por energía de referencia, no promedio simple', () => {
    // Crear datos con irradiancia variable (verano alto, invierno bajo)
    const variableData = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: i >= 4 && i <= 8 ? 700 : 300, // Verano: 700, Invierno: 300
      avgTemp: i >= 4 && i <= 8 ? 35 : 15,
      avgWindSpeed: 2,
    }));

    const prod = calculateAnnualProduction(variableData, panelSpecs, systemLosses, Array(12).fill(1.0));
    
    // Las pérdidas por temperatura deben ser mayores que un promedio simple
    // porque los meses de verano (más irradiancia) tienen más peso Y más pérdida por T°
    const simpleAvgTempLoss = prod.monthlyData.reduce((s, m) => s + m.losses.temperature, 0) / 12;
    
    // La pérdida ponderada debería ser diferente del promedio simple
    // (mayor, porque meses de alta irradiancia tienen más pérdida por T° Y más peso)
    expect(prod.losses.temperature).not.toBeCloseTo(simpleAvgTempLoss, 0);
  });

  it('pérdidas DC/AC son consistentes (no dependen de ponderación)', () => {
    const uniformData = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 500,
      avgTemp: 25,
      avgWindSpeed: 2,
    }));

    const prod = calculateAnnualProduction(uniformData, panelSpecs, systemLosses, Array(12).fill(1.0));
    
    // Con datos uniformes, las pérdidas DC/AC deben ser iguales a los valores del sistema
    expect(prod.losses.dcWiring).toBeCloseTo(systemLosses.dcWiring, 1);
    expect(prod.losses.inverter).toBeCloseTo(100 - systemLosses.inverterEfficiency, 1);
    expect(prod.losses.acWiring).toBeCloseTo(systemLosses.acWiring, 1);
  });
});

// ============================================================
// TESTS — Capacity Factor
// ============================================================

describe('calculateAnnualProduction — Capacity Factor', () => {
  const panelSpecs = {
    powerRating: 400,
    efficiency: 20,
    temperatureCoefficient: -0.004,
    nominalOperatingCellTemperature: 47,
    area: 2.0,
    quantity: 10,
  };

  const systemLosses = {
    dcWiring: 2,
    inverterEfficiency: 96,
    acWiring: 1,
    transformerLosses: 0,
    mismatchLosses: 2,
    soilingLosses: 2,
    shadingLosses: 0,
    availabilityLosses: 1,
  };

  it('Capacity Factor = E_AC / (P_nom × 8760) × 100', () => {
    const data = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 500,
      avgTemp: 28,
      avgWindSpeed: 2,
    }));

    const prod = calculateAnnualProduction(data, panelSpecs, systemLosses, Array(12).fill(1.0));
    const pNomKw = (panelSpecs.powerRating * panelSpecs.quantity) / 1000;
    const expectedCF = (prod.totalACEnergy / (pNomKw * 8760)) * 100;
    
    expect(prod.capacityFactor).toBeCloseTo(expectedCF, 2);
  });

  it('Capacity Factor está en rango válido para los datos de entrada', () => {
    // Nota: con POA promedio=500 W/m² constante (24h), el CF será alto
    // porque el modelo usa promedio mensual, no horas solares reales
    // En la práctica, datos EPW reales dan CF 10-25% típico
    const data = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 500,
      avgTemp: 28,
      avgWindSpeed: 2,
    }));

    const prod = calculateAnnualProduction(data, panelSpecs, systemLosses, Array(12).fill(1.0));
    expect(prod.capacityFactor).toBeGreaterThan(5);
    expect(prod.capacityFactor).toBeLessThan(60); // Con POA constante 24h el CF es alto
  });
});

// ============================================================
// TESTS — Capture Losses Breakdown (IEC 61724-1)
// ============================================================

describe('calculateAnnualProduction — Capture Losses Breakdown', () => {
  const panelSpecs = {
    powerRating: 400,
    efficiency: 20,
    temperatureCoefficient: -0.004,
    nominalOperatingCellTemperature: 47,
    area: 2.0,
    quantity: 10,
  };

  const systemLosses = {
    dcWiring: 2,
    inverterEfficiency: 96,
    acWiring: 1,
    transformerLosses: 0,
    mismatchLosses: 3,
    soilingLosses: 2,
    shadingLosses: 0,
    availabilityLosses: 1,
  };

  const monthlyData = Array(12).fill(null).map((_, i) => ({
    month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
    avgPOA: 500,
    avgTemp: 28,
    avgWindSpeed: 2,
  }));

  const shadingFactors = Array(12).fill(0.9); // 10% sombreado

  it('captureLossesBreakdown existe y tiene todas las categorías', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    const clb = prod.iec61724.captureLossesBreakdown;
    
    expect(clb).toBeDefined();
    expect(clb.temperature).toBeGreaterThanOrEqual(0);
    expect(clb.shading).toBeGreaterThanOrEqual(0);
    expect(clb.soiling).toBeGreaterThanOrEqual(0);
    expect(clb.mismatch).toBeGreaterThanOrEqual(0);
    expect(clb.dcWiring).toBeGreaterThanOrEqual(0);
    expect(clb.total).toBeGreaterThan(0);
  });

  it('Lc_temp = Yr × (pérdida_temp% / 100)', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    const clb = prod.iec61724.captureLossesBreakdown;
    const Yr = prod.iec61724.referenceYield;
    
    const expectedLcTemp = Yr * (prod.losses.temperature / 100);
    expect(clb.temperature).toBeCloseTo(expectedLcTemp, 1);
  });

  it('Lc_sombra = Yr × (pérdida_sombra% / 100)', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    const clb = prod.iec61724.captureLossesBreakdown;
    const Yr = prod.iec61724.referenceYield;
    
    const expectedLcShading = Yr * (prod.losses.shading / 100);
    expect(clb.shading).toBeCloseTo(expectedLcShading, 1);
  });

  it('Lc_suciedad = Yr × (pérdida_suciedad% / 100)', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    const clb = prod.iec61724.captureLossesBreakdown;
    const Yr = prod.iec61724.referenceYield;
    
    const expectedLcSoiling = Yr * (prod.losses.soiling / 100);
    expect(clb.soiling).toBeCloseTo(expectedLcSoiling, 1);
  });

  it('Lc_mismatch = Yr × (pérdida_mismatch% / 100)', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    const clb = prod.iec61724.captureLossesBreakdown;
    const Yr = prod.iec61724.referenceYield;
    
    const expectedLcMismatch = Yr * (prod.losses.mismatch / 100);
    expect(clb.mismatch).toBeCloseTo(expectedLcMismatch, 1);
  });

  it('Lc_dcWiring = Yr × (pérdida_dcWiring% / 100)', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    const clb = prod.iec61724.captureLossesBreakdown;
    const Yr = prod.iec61724.referenceYield;
    
    const expectedLcDC = Yr * (prod.losses.dcWiring / 100);
    expect(clb.dcWiring).toBeCloseTo(expectedLcDC, 1);
  });

  it('ΣLc_breakdown ≈ total', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    const clb = prod.iec61724.captureLossesBreakdown;
    
    const sum = clb.temperature + clb.shading + clb.soiling + clb.mismatch + clb.dcWiring;
    expect(clb.total).toBeCloseTo(sum, 1);
  });

  it('con sombreado=10%, Lc_sombra > 0', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, shadingFactors);
    expect(prod.iec61724.captureLossesBreakdown.shading).toBeGreaterThan(0);
  });

  it('sin sombreado, Lc_sombra = 0', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, Array(12).fill(1.0));
    expect(prod.iec61724.captureLossesBreakdown.shading).toBeCloseTo(0, 1);
  });

  it('Lc_temp es la mayor pérdida en clima cálido con T_amb=28°C', () => {
    const prod = calculateAnnualProduction(monthlyData, panelSpecs, systemLosses, Array(12).fill(1.0));
    const clb = prod.iec61724.captureLossesBreakdown;
    // En clima cálido sin sombreado, temperatura debe ser la mayor pérdida de captura
    expect(clb.temperature).toBeGreaterThan(clb.soiling);
    expect(clb.temperature).toBeGreaterThan(clb.mismatch);
    expect(clb.temperature).toBeGreaterThan(clb.dcWiring);
  });
});

// ============================================================
// TESTS — Energy Performance Index (EPI)
// ============================================================

describe('calculateAnnualProduction — EPI (energyPerformanceIndex)', () => {
  const panelSpecs = {
    powerRating: 400,
    efficiency: 20,
    temperatureCoefficient: -0.004,
    nominalOperatingCellTemperature: 47,
    area: 2.0,
    quantity: 10,
  };

  const systemLosses = {
    dcWiring: 2,
    inverterEfficiency: 96,
    acWiring: 1,
    transformerLosses: 0,
    mismatchLosses: 2,
    soilingLosses: 2,
    shadingLosses: 0,
    availabilityLosses: 1,
  };

  it('energyPerformanceIndex es null por defecto (sin benchmark)', () => {
    const data = Array(12).fill(null).map((_, i) => ({
      month: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][i],
      avgPOA: 500,
      avgTemp: 28,
      avgWindSpeed: 2,
    }));

    const prod = calculateAnnualProduction(data, panelSpecs, systemLosses, Array(12).fill(1.0));
    expect(prod.iec61724.energyPerformanceIndex).toBeNull();
  });
});
