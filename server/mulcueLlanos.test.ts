import { describe, it, expect } from 'vitest';
import {
  calculateMulcuePR,
  calculateProduction,
  calculateDiagnostic,
  calculateCellTemp,
  calculateTempLossFactor,
  quickEstimate,
  DEFAULT_KSIST,
  MULCUE_T_REF,
  DEFAULT_NOCT,
  G_NOCT_REF,
  T_REF_STC,
  REGION_FI_TABLE,
  SHADOW_FACTOR_TABLE,
} from '../shared/mulcueLlanos';

/**
 * Tests unitarios para el modelo Mulcue-Llanos.
 * Importan la implementación REAL desde shared/mulcueLlanos.ts.
 * Valores esperados verificados contra:
 * - Ejercicio 5 del curso BIPV Global (Dr. Luis Fernando Mulcue Nieto)
 * - calculadora_fotovoltaicaexcelopus.xlsx (fórmulas NOCT y pérdidas por T°)
 */

// ============================================================
// TESTS — PR (Performance Ratio)
// ============================================================

describe('Modelo Mulcue-Llanos — PR (implementación real)', () => {
  it('PR con γ=-0.36%/°C y Ta=28°C produce PR en rango bueno', () => {
    const result = calculateMulcuePR({ tempCoeffGamma: -0.36, ambientTemp: 28 });
    expect(result.prMax).toBeCloseTo(0.7569, 3);
    expect(result.prCorrected).toBeCloseTo(0.7567, 3);
    expect(result.interpretation).toBe('bueno');
  });

  it('PR con γ=-0.36%/°C y Ta=20°C produce PR más alto (menos pérdidas térmicas)', () => {
    const pr20 = calculateMulcuePR({ tempCoeffGamma: -0.36, ambientTemp: 20 });
    const pr34 = calculateMulcuePR({ tempCoeffGamma: -0.36, ambientTemp: 34 });
    expect(pr20.prCorrected).toBeGreaterThan(pr34.prCorrected);
  });

  it('PR con γ=-0.0036 (decimal) y γ=-0.36 (%/°C) producen el mismo resultado', () => {
    const prDecimal = calculateMulcuePR({ tempCoeffGamma: -0.0036, ambientTemp: 25 });
    const prPercent = calculateMulcuePR({ tempCoeffGamma: -0.36, ambientTemp: 25 });
    expect(prDecimal.prCorrected).toBeCloseTo(prPercent.prCorrected, 4);
  });

  it('PR con Ksist=0.82 y Ta=0°C no supera 0.95', () => {
    const result = calculateMulcuePR({ tempCoeffGamma: -0.36, ambientTemp: 0 });
    expect(result.prCorrected).toBeLessThanOrEqual(0.95);
  });

  it('PR para diferentes temperaturas colombianas', () => {
    const prBogota = calculateMulcuePR({ tempCoeffGamma: -0.36, ambientTemp: 14 });
    expect(prBogota.prCorrected).toBeGreaterThan(0.78);

    const prCartagena = calculateMulcuePR({ tempCoeffGamma: -0.36, ambientTemp: 28 });
    expect(prCartagena.prCorrected).toBeGreaterThan(0.70);
    expect(prCartagena.prCorrected).toBeLessThan(prBogota.prCorrected);
  });

  it('PR devuelve color e interpretación correctos', () => {
    const optimo = calculateMulcuePR({ tempCoeffGamma: -0.36, ambientTemp: 5 });
    expect(optimo.interpretation).toBe('optimo');
    expect(optimo.color).toBe('#16a34a');

    const bueno = calculateMulcuePR({ tempCoeffGamma: -0.36, ambientTemp: 28 });
    expect(bueno.interpretation).toBe('bueno');
    expect(bueno.color).toBe('#2563eb');
  });
});

// ============================================================
// TESTS — Producción (Ejercicio 5)
// ============================================================

describe('Modelo Mulcue-Llanos — Producción (Ejercicio 5, implementación real)', () => {
  const n_modulos = 314;
  const P_mod = 365; // W
  const FI = 0.95;
  const Ga0 = 4.66; // kWh/m²/día
  const FS = 0.85;
  const PR = 0.78;

  it('G_a corregida = G_a(0) × FI × FS = 3.7630', () => {
    const result = calculateProduction({
      ghiDaily: Ga0, irradiationFactor: FI, shadowFactor: FS,
      modulePower: P_mod, moduleCount: n_modulos, pr: PR,
    });
    expect(result.gaCorr).toBeCloseTo(3.7630, 2);
  });

  it('HSP total = G_a_corr × 365 = 1373.48 h', () => {
    const result = calculateProduction({
      ghiDaily: Ga0, irradiationFactor: FI, shadowFactor: FS,
      modulePower: P_mod, moduleCount: n_modulos, pr: PR,
    });
    expect(result.hspTotal).toBeCloseTo(1373.48, 0);
  });

  it('P_pico = 314 × 365 / 1000 = 114.61 kW', () => {
    const result = calculateProduction({
      ghiDaily: Ga0, irradiationFactor: FI, shadowFactor: FS,
      modulePower: P_mod, moduleCount: n_modulos, pr: PR,
    });
    expect(result.peakPowerKw).toBeCloseTo(114.61, 1);
  });

  it('E_PV = HSP × P_pico × PR = 122,783 kWh', () => {
    const result = calculateProduction({
      ghiDaily: Ga0, irradiationFactor: FI, shadowFactor: FS,
      modulePower: P_mod, moduleCount: n_modulos, pr: PR,
    });
    expect(result.energyKwh).toBeCloseTo(122783, -1);
  });

  it('Producción mensual (30 días) es ~1/12 de la anual', () => {
    const anual = calculateProduction({
      ghiDaily: Ga0, irradiationFactor: FI, shadowFactor: FS,
      modulePower: P_mod, moduleCount: n_modulos, pr: PR, days: 365,
    });
    const mensual = calculateProduction({
      ghiDaily: Ga0, irradiationFactor: FI, shadowFactor: FS,
      modulePower: P_mod, moduleCount: n_modulos, pr: PR, days: 30,
    });
    expect(mensual.energyKwh).toBeCloseTo(anual.energyKwh * 30 / 365, 0);
  });
});

// ============================================================
// TESTS — Diagnóstico Módulo (Ejercicio 5)
// ============================================================

describe('Modelo Mulcue-Llanos — Diagnóstico Módulo (Ejercicio 5, implementación real)', () => {
  const P_nom = 365;
  const gamma = -0.36;
  const G = 500;
  const Tc = 54;
  const P_real = 125.834;
  const eta_ideal = 22.44;

  it('Factor de temperatura con T_ref=21°C = 0.8812', () => {
    const result = calculateDiagnostic({
      nominalPower: P_nom, tempCoeffGamma: gamma,
      irradiance: G, cellTemp: Tc, realPower: P_real, idealEfficiency: eta_ideal,
    });
    expect(result.tempFactor).toBeCloseTo(0.8812, 4);
  });

  it('Potencia corregida por temperatura = 321.638 W', () => {
    const result = calculateDiagnostic({
      nominalPower: P_nom, tempCoeffGamma: gamma,
      irradiance: G, cellTemp: Tc, realPower: P_real, idealEfficiency: eta_ideal,
    });
    expect(result.tempCorrectedPower).toBeCloseTo(321.638, 1);
  });

  it('Potencia esperada = 160.819 W', () => {
    const result = calculateDiagnostic({
      nominalPower: P_nom, tempCoeffGamma: gamma,
      irradiance: G, cellTemp: Tc, realPower: P_real, idealEfficiency: eta_ideal,
    });
    expect(result.expectedPower).toBeCloseTo(160.819, 1);
  });

  it('Rendimiento = P_real / P_exp = 0.7825', () => {
    const result = calculateDiagnostic({
      nominalPower: P_nom, tempCoeffGamma: gamma,
      irradiance: G, cellTemp: Tc, realPower: P_real, idealEfficiency: eta_ideal,
    });
    expect(result.performance).toBeCloseTo(0.7825, 3);
  });

  it('T_ref es 21°C (modelo Mulcue-Llanos), no 25°C (STC)', () => {
    const result = calculateDiagnostic({
      nominalPower: P_nom, tempCoeffGamma: gamma,
      irradiance: G, cellTemp: Tc, realPower: P_real, idealEfficiency: eta_ideal,
    });
    const factorSTC = 1 - (0.36 / 100) * (Tc - 25);
    expect(result.tempFactor).not.toBeCloseTo(factorSTC, 3);
    expect(result.tempFactor).toBeCloseTo(0.8812, 4);
  });
});

// ============================================================
// TESTS — Temperatura de Celda (modelo NOCT IEC 61215)
// ============================================================

describe('Modelo NOCT — Temperatura de celda (IEC 61215)', () => {
  it('T_cell = T_amb + (NOCT - 20) × G/800 con valores por defecto', () => {
    // NOCT=45°C, G=800 W/m² → T_cell = T_amb + 25
    expect(calculateCellTemp(20)).toBe(45);  // 20 + (45-20) × 800/800 = 45
    expect(calculateCellTemp(25)).toBe(50);  // 25 + 25 = 50
    expect(calculateCellTemp(30)).toBe(55);  // 30 + 25 = 55
  });

  it('T_cell con NOCT=43°C (panel típico c-Si)', () => {
    // T_cell = 25 + (43 - 20) × 800/800 = 25 + 23 = 48°C
    expect(calculateCellTemp(25, 43)).toBe(48);
  });

  it('T_cell con NOCT=47°C (panel CdTe)', () => {
    // T_cell = 25 + (47 - 20) × 800/800 = 25 + 27 = 52°C
    expect(calculateCellTemp(25, 47)).toBe(52);
  });

  it('T_cell varía con irradiancia', () => {
    // G=600 W/m², NOCT=45 → T_cell = 25 + 25 × 600/800 = 25 + 18.75 = 43.75
    expect(calculateCellTemp(25, 45, 600)).toBeCloseTo(43.75, 2);
    // G=1000 W/m², NOCT=45 → T_cell = 25 + 25 × 1000/800 = 25 + 31.25 = 56.25
    expect(calculateCellTemp(25, 45, 1000)).toBeCloseTo(56.25, 2);
  });

  it('Verificación contra Excel: T_amb=30°C, NOCT=45°C, G=800 → T_cell=55°C', () => {
    expect(calculateCellTemp(30, 45, 800)).toBe(55);
  });

  it('Verificación contra Excel: T_amb=35°C, NOCT=43°C, G=1000 → T_cell=63.75°C', () => {
    // T_cell = 35 + (43-20) × 1000/800 = 35 + 28.75 = 63.75
    expect(calculateCellTemp(35, 43, 1000)).toBeCloseTo(63.75, 2);
  });

  it('Medellín: T_amb=18°C, NOCT=45°C, G=800 → T_cell=43°C', () => {
    expect(calculateCellTemp(18, 45, 800)).toBe(43);
  });

  it('Cartagena: T_amb=28°C, NOCT=45°C, G=800 → T_cell=53°C', () => {
    expect(calculateCellTemp(28, 45, 800)).toBe(53);
  });
});

// ============================================================
// TESTS — Pérdida por Alta Temperatura
// ============================================================

describe('Pérdida por alta temperatura (calculateTempLossFactor)', () => {
  it('Factor = 1.0 cuando T_cell = 25°C (STC)', () => {
    const factor = calculateTempLossFactor(25, -0.36);
    expect(factor).toBeCloseTo(1.0, 4);
  });

  it('Factor < 1.0 cuando T_cell > 25°C', () => {
    const factor = calculateTempLossFactor(55, -0.36);
    // factor = 1 + (-0.0036) × (55 - 25) = 1 - 0.108 = 0.892
    expect(factor).toBeCloseTo(0.892, 3);
    expect(factor).toBeLessThan(1.0);
  });

  it('Factor > 1.0 cuando T_cell < 25°C (ganancia por frío)', () => {
    const factor = calculateTempLossFactor(15, -0.36);
    // factor = 1 + (-0.0036) × (15 - 25) = 1 + 0.036 = 1.036 → capped at 1.0
    expect(factor).toBe(1.0);
  });

  it('Verificación contra Excel: γ=-0.31%/°C, T_cell=65°C → pérdida 12.4%', () => {
    const factor = calculateTempLossFactor(65, -0.31);
    // factor = 1 + (-0.0031) × (65 - 25) = 1 - 0.124 = 0.876
    expect(factor).toBeCloseTo(0.876, 3);
    const lossPercent = (1 - factor) * 100;
    expect(lossPercent).toBeCloseTo(12.4, 1);
  });

  it('Verificación: γ=-0.26%/°C (CdTe), T_cell=55°C → pérdida 7.8%', () => {
    const factor = calculateTempLossFactor(55, -0.26);
    // factor = 1 + (-0.0026) × (55 - 25) = 1 - 0.078 = 0.922
    expect(factor).toBeCloseTo(0.922, 3);
    const lossPercent = (1 - factor) * 100;
    expect(lossPercent).toBeCloseTo(7.8, 1);
  });

  it('Verificación: γ=-0.36%/°C (c-Si), T_cell=43°C (Medellín) → pérdida 6.48%', () => {
    const factor = calculateTempLossFactor(43, -0.36);
    // factor = 1 + (-0.0036) × (43 - 25) = 1 - 0.0648 = 0.9352
    expect(factor).toBeCloseTo(0.9352, 3);
    const lossPercent = (1 - factor) * 100;
    expect(lossPercent).toBeCloseTo(6.48, 1);
  });

  it('Pérdida mínima clamped a factor 0.5', () => {
    // Temperatura extrema → factor no baja de 0.5
    const factor = calculateTempLossFactor(200, -0.50);
    expect(factor).toBe(0.5);
  });

  it('Acepta γ en formato decimal (-0.0036) y porcentual (-0.36)', () => {
    const factorDecimal = calculateTempLossFactor(55, -0.0036);
    const factorPercent = calculateTempLossFactor(55, -0.36);
    expect(factorDecimal).toBeCloseTo(factorPercent, 4);
  });
});

// ============================================================
// TESTS — Constantes
// ============================================================

describe('Modelo Mulcue-Llanos — Constantes (implementación real)', () => {
  it('Ksist por defecto es 0.82', () => {
    expect(DEFAULT_KSIST).toBe(0.82);
  });

  it('T_ref del modelo es 21°C', () => {
    expect(MULCUE_T_REF).toBe(21);
  });

  it('NOCT por defecto es 45°C', () => {
    expect(DEFAULT_NOCT).toBe(45);
  });

  it('G_NOCT_REF es 800 W/m²', () => {
    expect(G_NOCT_REF).toBe(800);
  });

  it('T_REF_STC es 25°C', () => {
    expect(T_REF_STC).toBe(25);
  });

  it('Tabla REGION_FI_TABLE tiene 6 regiones colombianas', () => {
    expect(REGION_FI_TABLE).toHaveLength(6);
    const keys = REGION_FI_TABLE.map(r => r.key);
    expect(keys).toContain('caribe');
    expect(keys).toContain('andina');
    expect(keys).toContain('pacifica');
    expect(keys).toContain('orinoquia');
    expect(keys).toContain('amazonia');
    expect(keys).toContain('insular');
  });

  it('Tabla SHADOW_FACTOR_TABLE tiene 7 niveles de sombreado', () => {
    expect(SHADOW_FACTOR_TABLE).toHaveLength(7);
    expect(SHADOW_FACTOR_TABLE[0].fs).toBe(1.00);
    expect(SHADOW_FACTOR_TABLE[6].fs).toBe(0.60);
  });
});

// ============================================================
// TESTS — calculateExpectedPower (P_exp = P_nom × [1 + γ(T_c − 21)] × (G/1000))
// ============================================================

import { calculateExpectedPower, G_STC } from '../shared/mulcueLlanos';

describe('Modelo Mulcue-Llanos — calculateExpectedPower (P_exp)', () => {
  it('P_exp a STC (1000 W/m²) y T_cell=21°C devuelve P_nom exacta', () => {
    // T_c = T_ref = 21°C, G = 1000 W/m² → P_exp = P_nom
    const pExp = calculateExpectedPower(365, -0.36, 21, 1000);
    expect(pExp).toBeCloseTo(365, 1);
  });

  it('P_exp con T_cell > 21°C reduce la potencia', () => {
    // P_exp = 365 × [1 + (-0.0036)(47 - 21)] × (800/1000)
    // = 365 × [1 - 0.0936] × 0.8 = 365 × 0.9064 × 0.8 = 264.67 W
    const pExp = calculateExpectedPower(365, -0.36, 47, 800);
    expect(pExp).toBeCloseTo(264.67, 0);
    expect(pExp).toBeLessThan(365);
  });

  it('P_exp del Ejercicio 5: P_nom=365W, γ=-0.36, T_c=54°C, G=500 → 160.82W', () => {
    // P_exp = 365 × [1 + (-0.0036)(54 - 21)] × (500/1000)
    // = 365 × [1 - 0.1188] × 0.5 = 365 × 0.8812 × 0.5 = 160.819 W
    const pExp = calculateExpectedPower(365, -0.36, 54, 500);
    expect(pExp).toBeCloseTo(160.82, 0);
  });

  it('P_exp acepta γ en formato decimal (-0.0036) y porcentual (-0.36)', () => {
    const pExpDecimal = calculateExpectedPower(365, -0.0036, 47, 800);
    const pExpPercent = calculateExpectedPower(365, -0.36, 47, 800);
    expect(pExpDecimal).toBeCloseTo(pExpPercent, 2);
  });

  it('P_exp a G=1200 W/m² y T_cell=21°C supera P_nom', () => {
    // G > STC → irradianceFactor > 1 → P_exp > P_nom
    const pExp = calculateExpectedPower(365, -0.36, 21, 1200);
    expect(pExp).toBeCloseTo(365 * 1.2, 1);
    expect(pExp).toBeGreaterThan(365);
  });

  it('P_exp con CdTe (γ=-0.26%/°C) tiene menor degradación que c-Si (γ=-0.36%/°C)', () => {
    const pExpCdTe = calculateExpectedPower(365, -0.26, 55, 800);
    const pExpCSi = calculateExpectedPower(365, -0.36, 55, 800);
    expect(pExpCdTe).toBeGreaterThan(pExpCSi);
  });
});

// ============================================================
// TESTS — quickEstimate integración
// ============================================================

describe('Modelo Mulcue-Llanos — quickEstimate integración', () => {
  it('Estimación rápida para Medellín con NOCT produce T_cell y P_exp correctos', () => {
    const result = quickEstimate({
      ghiAnnualKwhM2: 1700,
      ambientTemp: 22,
      tempCoeffGamma: -0.36,
      modulePowerW: 365,
      moduleCount: 10,
      regionKey: 'andina',
      shadowFactor: 0.90,
      noct: 45,
    });

    // T_cell = 22 + (45-20) × 800/800 = 22 + 25 = 47°C
    expect(result.cellTemp).toBe(47);

    // Pérdida por T° = 0.36% × (47 - 25) = 7.92%
    expect(result.tempLossPercent).toBeCloseTo(7.92, 1);
    expect(result.tempLossFactor).toBeCloseTo(0.9208, 3);

    // P_exp = 365 × [1 + (-0.0036)(47 - 21)] × (800/1000) = 264.67 W
    expect(result.pExp).toBeCloseTo(264.67, 0);
    expect(result.pExpTotal).toBeCloseTo(2646.7, 0);
    expect(result.pNom).toBe(365);
    expect(result.pNomTotal).toBe(3650);

    // tempDegradation > 0 (hay pérdida por T°)
    expect(result.tempDegradation).toBeGreaterThan(0);

    // PR debe estar en rango bueno para 22°C
    expect(result.pr.prCorrected).toBeGreaterThan(0.70);
    expect(result.pr.prCorrected).toBeLessThan(0.85);

    // Producción usa P_exp (no P_nom) → peakPowerKw refleja P_exp
    // peakPowerKw en calculateProduction = modulePower * moduleCount / 1000
    // = pExp * 10 / 1000 = 264.67 * 10 / 1000 = 2.647 kWp
    expect(result.production.peakPowerKw).toBeCloseTo(2.647, 1);
    expect(result.production.energyKwh).toBeGreaterThan(2000);
    expect(result.production.energyKwh).toBeLessThan(5000);

    // Región info
    expect(result.regionInfo?.region).toBe('Andina');
    expect(result.regionInfo?.fi).toBe(0.95);
  });

  it('Estimación con NOCT=43°C produce T_cell menor que NOCT=47°C', () => {
    const lowNOCT = quickEstimate({
      ghiAnnualKwhM2: 1700, ambientTemp: 25, tempCoeffGamma: -0.36,
      modulePowerW: 365, moduleCount: 10, regionKey: 'andina', shadowFactor: 0.90,
      noct: 43,
    });
    const highNOCT = quickEstimate({
      ghiAnnualKwhM2: 1700, ambientTemp: 25, tempCoeffGamma: -0.36,
      modulePowerW: 365, moduleCount: 10, regionKey: 'andina', shadowFactor: 0.90,
      noct: 47,
    });
    expect(lowNOCT.cellTemp).toBeLessThan(highNOCT.cellTemp);
    expect(lowNOCT.tempLossPercent).toBeLessThan(highNOCT.tempLossPercent);
  });

  it('Cartagena vs Medellín: Cartagena tiene mayor T_cell y mayor pérdida por T°', () => {
    const medellin = quickEstimate({
      ghiAnnualKwhM2: 1700, ambientTemp: 22, tempCoeffGamma: -0.36,
      modulePowerW: 365, moduleCount: 10, regionKey: 'andina', shadowFactor: 0.90,
      noct: 45,
    });
    const cartagena = quickEstimate({
      ghiAnnualKwhM2: 2000, ambientTemp: 28, tempCoeffGamma: -0.36,
      modulePowerW: 365, moduleCount: 10, regionKey: 'caribe', shadowFactor: 0.90,
      noct: 45,
    });

    expect(cartagena.cellTemp).toBeGreaterThan(medellin.cellTemp);
    expect(cartagena.tempLossPercent).toBeGreaterThan(medellin.tempLossPercent);
    // Cartagena tiene peor PR por mayor temperatura
    expect(cartagena.pr.prCorrected).toBeLessThan(medellin.pr.prCorrected);
    // Pero mayor GHI compensa → más energía total
    expect(cartagena.production.energyKwh).toBeGreaterThan(medellin.production.energyKwh);
  });

  it('quickEstimate sin NOCT usa DEFAULT_NOCT=45', () => {
    const withDefault = quickEstimate({
      ghiAnnualKwhM2: 1700, ambientTemp: 25, tempCoeffGamma: -0.36,
      modulePowerW: 365, moduleCount: 10, regionKey: 'andina', shadowFactor: 0.90,
    });
    const withExplicit = quickEstimate({
      ghiAnnualKwhM2: 1700, ambientTemp: 25, tempCoeffGamma: -0.36,
      modulePowerW: 365, moduleCount: 10, regionKey: 'andina', shadowFactor: 0.90,
      noct: 45,
    });
    expect(withDefault.cellTemp).toBe(withExplicit.cellTemp);
    expect(withDefault.tempLossFactor).toBe(withExplicit.tempLossFactor);
  });
});

// ============================================================
// TESTS — Escenarios de Mediciones de Campo (Field Measurements)
// Validan que las funciones Mulcue-Llanos producen resultados correctos
// cuando se usan con valores medidos en campo (GHI, T_amb, T_cell).
// ============================================================

describe('Escenarios de campo — P_exp con valores medidos', () => {
  // Escenario: Medellín campo, piranómetro mide GHI=650 W/m², T_amb=24°C
  it('Campo Medellín: GHI=650, T_amb=24°C, NOCT=45 → T_cell y P_exp correctos', () => {
    const T_amb = 24;
    const GHI = 650;
    const NOCT = 45;
    const P_nom = 365;
    const gamma = -0.36; // %/°C

    // T_cell = 24 + (45-20) × 650/800 = 24 + 20.3125 = 44.3125°C
    const cellTemp = calculateCellTemp(T_amb, NOCT, GHI);
    expect(cellTemp).toBeCloseTo(44.3125, 2);

    // P_exp = 365 × [1 + (-0.0036)(44.3125 - 21)] × (650/1000)
    // = 365 × [1 - 0.08393] × 0.65 = 365 × 0.91607 × 0.65 = 217.44 W
    const pExp = calculateExpectedPower(P_nom, gamma, cellTemp, GHI);
    expect(pExp).toBeCloseTo(217.44, 0);
    expect(pExp).toBeLessThan(P_nom);
  });

  // Escenario: Cartagena campo, GHI=1050 W/m², T_amb=33°C
  it('Campo Cartagena: GHI=1050, T_amb=33°C, NOCT=45 → alta T_cell y P_exp degradado', () => {
    const T_amb = 33;
    const GHI = 1050;
    const NOCT = 45;
    const P_nom = 365;
    const gamma = -0.36;

    // T_cell = 33 + (45-20) × 1050/800 = 33 + 32.8125 = 65.8125°C
    const cellTemp = calculateCellTemp(T_amb, NOCT, GHI);
    expect(cellTemp).toBeCloseTo(65.8125, 2);

    // P_exp = 365 × [1 + (-0.0036)(65.8125 - 21)] × (1050/1000)
    // = 365 × [1 - 0.16133] × 1.05 = 365 × 0.83867 × 1.05 = 321.42 W
    const pExp = calculateExpectedPower(P_nom, gamma, cellTemp, GHI);
    expect(pExp).toBeCloseTo(321.42, 0);
  });

  // Escenario: T_cell medida directamente con termopar (sin calcular con NOCT)
  it('T_cell manual con termopar: T_cell=58°C, GHI=900 → P_exp correcto', () => {
    const T_cell_manual = 58; // Medida directamente
    const GHI = 900;
    const P_nom = 365;
    const gamma = -0.36;

    // P_exp = 365 × [1 + (-0.0036)(58 - 21)] × (900/1000)
    // = 365 × [1 - 0.1332] × 0.9 = 365 × 0.8668 × 0.9 = 284.74 W
    const pExp = calculateExpectedPower(P_nom, gamma, T_cell_manual, GHI);
    expect(pExp).toBeCloseTo(284.74, 0);
  });

  // Escenario: Panel CdTe en campo (menor degradación por T°)
  it('CdTe en campo: γ=-0.26, GHI=800, T_amb=30°C, NOCT=47 → menor degradación', () => {
    const T_amb = 30;
    const GHI = 800;
    const NOCT = 47;
    const P_nom = 120; // CdTe típico
    const gamma_CdTe = -0.26;
    const gamma_cSi = -0.36;

    const cellTemp = calculateCellTemp(T_amb, NOCT, GHI);
    // T_cell = 30 + (47-20) × 800/800 = 30 + 27 = 57°C
    expect(cellTemp).toBe(57);

    const pExpCdTe = calculateExpectedPower(P_nom, gamma_CdTe, cellTemp, GHI);
    const pExpCSi = calculateExpectedPower(P_nom, gamma_cSi, cellTemp, GHI);

    // CdTe pierde menos por temperatura
    expect(pExpCdTe).toBeGreaterThan(pExpCSi);
  });

  // Escenario: PR de campo con Mulcue-Llanos
  it('PR de campo: T_amb=30°C, γ=-0.36 → PR menor que T_amb=18°C', () => {
    const prHot = calculateMulcuePR({ tempCoeffGamma: -0.36, ambientTemp: 30 });
    const prCool = calculateMulcuePR({ tempCoeffGamma: -0.36, ambientTemp: 18 });
    expect(prCool.prCorrected).toBeGreaterThan(prHot.prCorrected);
  });

  // Escenario: Factor de pérdida por temperatura de campo
  it('Factor de pérdida: T_cell=57°C (campo) → pérdida 11.52% con γ=-0.36', () => {
    const factor = calculateTempLossFactor(57, -0.36);
    // factor = 1 + (-0.0036) × (57 - 25) = 1 - 0.1152 = 0.8848
    expect(factor).toBeCloseTo(0.8848, 3);
    const lossPercent = (1 - factor) * 100;
    expect(lossPercent).toBeCloseTo(11.52, 1);
  });

  // Escenario: Producción con valores de campo constantes (simula 12 meses iguales)
  it('Producción anual con GHI de campo constante para 12 meses', () => {
    const GHI_field = 750; // W/m²
    const T_amb_field = 26;
    const NOCT = 45;
    const P_nom = 365;
    const gamma = -0.36;
    const moduleCount = 10;

    // T_cell de campo
    const cellTemp = calculateCellTemp(T_amb_field, NOCT, GHI_field);
    // T_cell = 26 + 25 × 750/800 = 26 + 23.4375 = 49.4375°C
    expect(cellTemp).toBeCloseTo(49.4375, 2);

    // P_exp por módulo
    const pExp = calculateExpectedPower(P_nom, gamma, cellTemp, GHI_field);
    expect(pExp).toBeGreaterThan(0);
    expect(pExp).toBeLessThan(P_nom);

    // P_exp total
    const pExpTotal = pExp * moduleCount;
    expect(pExpTotal).toBeGreaterThan(0);
    expect(pExpTotal).toBeLessThan(P_nom * moduleCount);
  });
});
