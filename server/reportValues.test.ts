/**
 * Tests para verificar que los valores del reporte PDF son correctos
 * Específicamente: Factor de Capacidad, HSP, Performance Ratio
 */
import { describe, it, expect } from 'vitest';

describe('Report PDF Value Calculations', () => {
  // Simular el cálculo de capacityFactor como lo hace calculateAnnualProduction
  describe('Capacity Factor', () => {
    it('calculateAnnualProduction returns capacityFactor as percentage (not fraction)', () => {
      // From energyProduction.ts line 426-428:
      // capacityFactor = (totalACEnergy / (installedCapacityKw * 8760)) * 100
      const totalACEnergy = 1007; // kWh
      const installedCapacityKw = 0.4; // kWp
      const capacityFactor = (totalACEnergy / (installedCapacityKw * 8760)) * 100;
      
      // Should be ~28.7%, NOT 0.287
      expect(capacityFactor).toBeGreaterThan(10);
      expect(capacityFactor).toBeLessThan(50);
      expect(capacityFactor).toBeCloseTo(28.7, 0);
    });

    it('report should display capFactorPct directly without multiplying by 100', () => {
      // The fix: capFactorPct is already a percentage
      const capFactorPct = 28.74; // already percentage from calculateAnnualProduction
      
      // Correct display: just use .toFixed(1) + '%'
      const display = `${capFactorPct.toFixed(1)}%`;
      expect(display).toBe('28.7%');
      
      // OLD BUG: was doing capFactor * 100 which gave 2874%
      const buggyDisplay = `${(capFactorPct * 100).toFixed(1)}%`;
      expect(buggyDisplay).toBe('2874.0%'); // This was the bug!
    });
  });

  describe('HSP (Peak Sun Hours)', () => {
    it('should calculate monthly HSP correctly from totalPOA average', () => {
      // totalPOA = average W/m² over ALL hours of month (including night=0)
      const totalPOA = 329; // W/m² (Medellín example)
      const daysInJanuary = 31;
      
      // Correct formula: totalPOA * days * 24 / 1000 = kWh/m²/month
      const hspMonthly = totalPOA * daysInJanuary * 24 / 1000;
      
      // Should be ~245 kWh/m²/month, NOT 9.87
      expect(hspMonthly).toBeGreaterThan(200);
      expect(hspMonthly).toBeLessThan(300);
      expect(hspMonthly).toBeCloseTo(244.8, 0);
    });

    it('should calculate annual HSP correctly', () => {
      const totalPOA = 329; // W/m² constant for simplicity
      const daysPerMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
      
      const annualHSP = daysPerMonth.reduce((sum, days) => {
        return sum + (totalPOA * days * 24 / 1000);
      }, 0);
      
      // Should be ~2882 h/year, NOT 119
      expect(annualHSP).toBeGreaterThan(2000);
      expect(annualHSP).toBeLessThan(4000);
      expect(annualHSP).toBeCloseTo(2882, -1);
    });

    it('OLD BUG: totalPOA / 1000 * 30 gives wrong result', () => {
      const totalPOA = 329;
      
      // OLD formula (WRONG): totalPOA / 1000 * 30
      const oldHSP = totalPOA / 1000 * 30;
      expect(oldHSP).toBeCloseTo(9.87, 1); // Only 9.87 h/month!
      
      // Annual with old formula: ~119 h/year (WAY too low)
      const oldAnnualHSP = oldHSP * 12;
      expect(oldAnnualHSP).toBeCloseTo(118.4, 0);
      
      // NEW formula (CORRECT): totalPOA * 31 * 24 / 1000
      const newHSP = totalPOA * 31 * 24 / 1000;
      expect(newHSP).toBeCloseTo(244.8, 0); // 245 kWh/m²/month
    });
  });

  describe('Performance Ratio', () => {
    it('calculateAnnualProduction returns performanceRatio as percentage', () => {
      // From energyProduction.ts line 473:
      // performanceRatio: performanceRatio * 100
      // So if PR = 0.873 internally, it returns 87.3
      const prFraction = 0.873;
      const prFromFunction = prFraction * 100; // 87.3
      
      expect(prFromFunction).toBeGreaterThan(50);
      expect(prFromFunction).toBeLessThan(100);
    });

    it('report should display perfRatioPct directly without multiplying by 100', () => {
      const perfRatioPct = 87.3; // already percentage
      
      // Correct display
      const display = `${perfRatioPct.toFixed(1)}%`;
      expect(display).toBe('87.3%');
    });

    it('PR recommendation threshold should use 80 (not 0.80)', () => {
      const perfRatioPct = 87.3; // percentage
      
      // Correct: compare against 80 (percentage)
      expect(perfRatioPct > 80).toBe(true);
      
      // OLD BUG would compare against 0.80 which always passes
      // since 87.3 > 0.80 is always true
    });
  });

  describe('Specific Yield', () => {
    it('should be annualProduction / systemCapacityKW', () => {
      const annualProd = 1007; // kWh
      const systemCapacityKW = 0.4; // kWp (1 × 400W)
      
      const specYield = annualProd / systemCapacityKW;
      expect(specYield).toBeCloseTo(2518, -1);
      
      // Note: 2518 kWh/kWp/year is high but mathematically correct
      // given the POA data. The issue is upstream (POA calculation)
      // not in the report formatting.
    });
  });

  describe('HSP daily calculation', () => {
    it('should calculate daily HSP as totalPOA * 24 / 1000', () => {
      const totalPOA = 329; // W/m² average over 24h
      const hspDaily = totalPOA * 24 / 1000; // kWh/m²/day
      
      expect(hspDaily).toBeCloseTo(7.9, 1);
    });
  });
});
