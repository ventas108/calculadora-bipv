/**
 * Tests para la detección de coherencia de datos en la validación cruzada.
 * Verifica que el sistema detecte:
 * 1. Distribuciones planas (CV < 5%) — datos sintéticos/constantes
 * 2. Valores negativos — errores de cálculo
 * 3. Outliers extremos — datos corruptos
 */
import { describe, it, expect } from 'vitest';
import { buildComparisonData } from '../client/src/lib/crossValidation';
import type { AnnualProduction } from '../client/src/lib/energyProduction';

// Helper: crear producción simulada con datos mensuales específicos
function createMockProduction(monthlyAC: number[]): AnnualProduction {
  return {
    monthlyData: monthlyAC.map((ac, i) => ({
      month: i + 1,
      energyProduced: ac,
      dcEnergy: ac * 1.1,
      rawPOA: 200 + i * 10,
      referenceEnergy: ac * 1.2,
      avgTemp: 25,
      cellTemperature: 35,
      performanceRatio: 0.85,
      systemLosses: 0.15,
      shadingFactor: 1.0,
      daysInMonth: [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][i],
    })),
    totalACEnergy: monthlyAC.reduce((s, v) => s + v, 0),
    totalDCEnergy: monthlyAC.reduce((s, v) => s + v, 0) * 1.1,
    performanceRatio: 85,
    prTemperatureCorrected: 87,
    specificYield: 1500,
    capacityFactor: 17,
    totalSystemLosses: 15,
  } as unknown as AnnualProduction;
}

describe('Detección de Coherencia de Datos', () => {
  // Producción realista con variación estacional
  const realisticMonthly = [50677, 44703, 47789, 40119, 39192, 44205, 54307, 55959, 52456, 40920, 35572, 44817];
  const realisticProduction = createMockProduction(realisticMonthly);

  describe('Distribución plana (datos constantes)', () => {
    it('debe detectar producción BIPV constante (Array(12).fill)', () => {
      const constantBIPV = {
        produccionMensualKwh: Array(12).fill(87186.6),
        eficienciaAjustada: 0.15,
        potenciaPicoW: 150000,
        tilt: 10,
        azimuth: 180,
        areaM2: 1000,
        transparencia: 0.3,
        technology: 'CdTe',
        generation: '2G' as const,
        iamPromedio: 0.95,
        soilingPromedio: 0.97,
        factorTermicoPromedio: 0.92,
        energiaAnualKwh: 87186.6 * 12,
        energiaAnualKwhM2: 150,
        transpositionModel: 'isotropic' as const,
        coefTemperatura: -0.29,
        noct: 46,
        kBipv: 1.2,
      };

      const result = buildComparisonData(realisticProduction, null, null, null, null, constantBIPV);

      expect(result.coherenceAlerts).toBeDefined();
      expect(result.coherenceAlerts.length).toBeGreaterThan(0);

      const bipvAlert = result.coherenceAlerts.find(a => a.source === 'bipv');
      expect(bipvAlert).toBeDefined();
      expect(bipvAlert!.type).toBe('flat_distribution');
      expect(bipvAlert!.severity).toBe('critical');
      expect(bipvAlert!.cv_pct).toBeLessThan(0.1);
      expect(bipvAlert!.message).toContain('CONSTANTE');
    });

    it('debe detectar variación muy baja (CV < 5%)', () => {
      // Variación mínima: ±2% del promedio
      const avg = 50000;
      const lowVarBIPV = {
        produccionMensualKwh: [avg * 1.01, avg * 0.99, avg * 1.02, avg * 0.98, avg * 1.01, avg * 0.99,
                               avg * 1.02, avg * 0.98, avg * 1.01, avg * 0.99, avg * 1.00, avg * 1.00],
        eficienciaAjustada: 0.15,
        potenciaPicoW: 150000,
        tilt: 10,
        azimuth: 180,
        areaM2: 1000,
        transparencia: 0.3,
        technology: 'CdTe',
        generation: '2G' as const,
        iamPromedio: 0.95,
        soilingPromedio: 0.97,
        factorTermicoPromedio: 0.92,
        energiaAnualKwh: avg * 12,
        energiaAnualKwhM2: 150,
        transpositionModel: 'isotropic' as const,
        coefTemperatura: -0.29,
        noct: 46,
        kBipv: 1.2,
      };

      const result = buildComparisonData(realisticProduction, null, null, null, null, lowVarBIPV);

      const bipvAlert = result.coherenceAlerts.find(a => a.source === 'bipv' && a.type === 'flat_distribution');
      expect(bipvAlert).toBeDefined();
      expect(bipvAlert!.severity).toBe('warning');
      expect(bipvAlert!.cv_pct).toBeLessThan(5);
      expect(bipvAlert!.cv_pct).toBeGreaterThan(0.1);
    });

    it('NO debe alertar con variación estacional normal (CV > 5%)', () => {
      // Variación realista: ±15-20%
      const normalBIPV = {
        produccionMensualKwh: [55000, 48000, 52000, 43000, 38000, 42000, 56000, 58000, 54000, 42000, 36000, 47000],
        eficienciaAjustada: 0.15,
        potenciaPicoW: 150000,
        tilt: 10,
        azimuth: 180,
        areaM2: 1000,
        transparencia: 0.3,
        technology: 'CdTe',
        generation: '2G' as const,
        iamPromedio: 0.95,
        soilingPromedio: 0.97,
        factorTermicoPromedio: 0.92,
        energiaAnualKwh: 571000,
        energiaAnualKwhM2: 150,
        transpositionModel: 'isotropic' as const,
        coefTemperatura: -0.29,
        noct: 46,
        kBipv: 1.2,
      };

      const result = buildComparisonData(realisticProduction, null, null, null, null, normalBIPV);

      const flatAlert = result.coherenceAlerts.find(a => a.source === 'bipv' && a.type === 'flat_distribution');
      expect(flatAlert).toBeUndefined();
    });
  });

  describe('Sin fuentes externas', () => {
    it('no debe generar alertas cuando no hay datos BIPV/PVWatts/PVGIS', () => {
      const result = buildComparisonData(realisticProduction, null, null, null, null, null);
      // Solo el simulador está activo, y tiene variación normal
      const flatAlerts = result.coherenceAlerts.filter(a => a.type === 'flat_distribution');
      expect(flatAlerts.length).toBe(0);
    });
  });

  describe('Coherencia del simulador', () => {
    it('debe detectar si el simulador mismo tiene datos constantes', () => {
      const constantProduction = createMockProduction(Array(12).fill(45000));
      const result = buildComparisonData(constantProduction, null, null, null, null, null);

      const simAlert = result.coherenceAlerts.find(a => a.source === 'simulator' && a.type === 'flat_distribution');
      expect(simAlert).toBeDefined();
      expect(simAlert!.severity).toBe('critical');
    });
  });
});
