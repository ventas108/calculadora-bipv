/**
 * Tests unitarios para calculatePR_T_Hourly (IEC 61724-1:2021)
 * PR_T = Σ(E_AC_h) / Σ((G_POA_h/G_ref) × P_nom × (1 + γ × (T_cell_h - 25)))
 */
import { describe, it, expect } from 'vitest';
import {
  calculatePR_T_Hourly,
  HourlyRecord,
  HourlyPR_T_Result,
  calculateCellTemperature,
} from '../client/src/lib/energyProduction';

// Helper: genera registros horarios para un mes completo
function generateMonthlyRecords(
  month: number,
  daysInMonth: number,
  opts: {
    poa_Wm2?: number;
    tamb_C?: number;
    tcell_C?: number;
    ac_W?: number;
    wspd_ms?: number;
    sunHoursPerDay?: number;
  } = {}
): HourlyRecord[] {
  const {
    poa_Wm2 = 600,
    tamb_C = 25,
    tcell_C,
    ac_W,
    wspd_ms = 2,
    sunHoursPerDay = 12,
  } = opts;

  const records: HourlyRecord[] = [];
  for (let day = 0; day < daysInMonth; day++) {
    for (let hour = 0; hour < 24; hour++) {
      const isSunHour = hour >= (12 - sunHoursPerDay / 2) && hour < (12 + sunHoursPerDay / 2);
      records.push({
        month,
        poa_Wm2: isSunHour ? poa_Wm2 : 0,
        tamb_C,
        tcell_C: isSunHour ? tcell_C : undefined,
        ac_W: isSunHour ? ac_W : 0,
        wspd_ms,
      });
    }
  }
  return records;
}

// Helper: genera un año completo de registros horarios
function generateYearlyRecords(opts: {
  poa_Wm2?: number;
  tamb_C?: number;
  tcell_C?: number;
  ac_W?: number;
  wspd_ms?: number;
  sunHoursPerDay?: number;
} = {}): HourlyRecord[] {
  const daysPerMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const records: HourlyRecord[] = [];
  for (let m = 0; m < 12; m++) {
    records.push(...generateMonthlyRecords(m + 1, daysPerMonth[m], opts));
  }
  return records;
}

describe('calculatePR_T_Hourly - IEC 61724-1:2021', () => {
  describe('Estructura de resultado', () => {
    it('devuelve todas las propiedades requeridas', () => {
      const records = generateYearlyRecords({ poa_Wm2: 600, tamb_C: 25, ac_W: 3000 });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');

      expect(result).toHaveProperty('annualPR_T');
      expect(result).toHaveProperty('annualPR');
      expect(result).toHaveProperty('monthly');
      expect(result).toHaveProperty('source');
      expect(result).toHaveProperty('totalRecords');
      expect(result).toHaveProperty('sunHours');
      expect(result).toHaveProperty('avgCellTempWeighted');
      expect(result).toHaveProperty('systemCapacity_kW');
    });

    it('devuelve 12 meses en el desglose mensual', () => {
      const records = generateYearlyRecords({ poa_Wm2: 600, tamb_C: 25, ac_W: 3000 });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      expect(result.monthly).toHaveLength(12);
    });

    it('cada mes tiene todas las propiedades requeridas', () => {
      const records = generateYearlyRecords({ poa_Wm2: 600, tamb_C: 25, ac_W: 3000 });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      for (const m of result.monthly) {
        expect(m).toHaveProperty('month');
        expect(m).toHaveProperty('monthName');
        expect(m).toHaveProperty('pr');
        expect(m).toHaveProperty('pr_t');
        expect(m).toHaveProperty('avgTcell');
        expect(m).toHaveProperty('avgTamb');
        expect(m).toHaveProperty('totalPOA_kWhm2');
        expect(m).toHaveProperty('totalAC_kWh');
        expect(m).toHaveProperty('hoursWithSun');
        expect(m).toHaveProperty('referenceYield');
        expect(m).toHaveProperty('finalYield');
      }
    });

    it('preserva la fuente de datos', () => {
      const records = generateYearlyRecords({ poa_Wm2: 600, tamb_C: 25, ac_W: 3000 });
      const pvw = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      const pvg = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvgis');
      expect(pvw.source).toBe('pvwatts');
      expect(pvg.source).toBe('pvgis');
    });
  });

  describe('Umbral de irradiancia (50 W/m²)', () => {
    it('excluye horas con POA < 50 W/m²', () => {
      const records: HourlyRecord[] = [
        { month: 1, poa_Wm2: 49, tamb_C: 25, ac_W: 100 },  // Excluida
        { month: 1, poa_Wm2: 50, tamb_C: 25, ac_W: 100 },  // Incluida
        { month: 1, poa_Wm2: 600, tamb_C: 25, ac_W: 3000 }, // Incluida
      ];
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      expect(result.sunHours).toBe(2);
    });

    it('excluye horas nocturnas (POA = 0)', () => {
      const records: HourlyRecord[] = [
        { month: 6, poa_Wm2: 0, tamb_C: 20, ac_W: 0 },
        { month: 6, poa_Wm2: 0, tamb_C: 20, ac_W: 0 },
        { month: 6, poa_Wm2: 800, tamb_C: 30, ac_W: 4000 },
      ];
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      expect(result.sunHours).toBe(1);
    });
  });

  describe('Cálculo de PR_T vs PR', () => {
    it('PR_T > PR cuando T_cell > 25°C (clima cálido)', () => {
      // En clima cálido, T_cell > 25°C, γ < 0, por lo que el denominador de PR_T
      // es menor que el de PR → PR_T > PR
      const records = generateYearlyRecords({
        poa_Wm2: 800,
        tamb_C: 35,
        tcell_C: 55, // Muy caliente
        ac_W: 3000,
      });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      expect(result.annualPR_T).toBeGreaterThan(result.annualPR);
    });

    it('PR_T ≈ PR cuando T_cell ≈ 25°C', () => {
      // Cuando la celda está a 25°C, la corrección de temperatura es 1.0
      const records = generateYearlyRecords({
        poa_Wm2: 600,
        tamb_C: 10,
        tcell_C: 25, // Exactamente STC
        ac_W: 3000,
      });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      expect(Math.abs(result.annualPR_T - result.annualPR)).toBeLessThan(0.001);
    });

    it('PR_T < PR cuando T_cell < 25°C (clima frío)', () => {
      // En clima frío, T_cell < 25°C, γ < 0, denominador de PR_T > denominador de PR
      const records = generateYearlyRecords({
        poa_Wm2: 600,
        tamb_C: 5,
        tcell_C: 15, // Frío
        ac_W: 3000,
      });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      expect(result.annualPR_T).toBeLessThan(result.annualPR);
    });
  });

  describe('Cálculo manual verificado', () => {
    it('calcula PR_T correctamente con valores conocidos', () => {
      // Caso simple: 1 hora, 1 mes
      // POA = 800 W/m², T_cell = 45°C, AC = 3200 W, P_nom = 5000 W
      // γ = -0.004 /°C
      // PR = E_AC / ((POA/G_ref) × P_nom) = 3200 / (0.8 × 5000) = 0.80
      // PR_T = E_AC / ((POA/G_ref) × P_nom × (1 + γ × (45-25)))
      //      = 3200 / (0.8 × 5000 × (1 + (-0.004) × 20))
      //      = 3200 / (4000 × 0.92) = 3200 / 3680 = 0.8696
      const records: HourlyRecord[] = [
        { month: 6, poa_Wm2: 800, tamb_C: 30, tcell_C: 45, ac_W: 3200 },
      ];
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');

      expect(result.annualPR).toBeCloseTo(0.80, 2);
      expect(result.annualPR_T).toBeCloseTo(0.8696, 3);
    });

    it('calcula PR correctamente con múltiples horas', () => {
      // 2 horas con diferentes condiciones
      // Hora 1: POA=600, T_cell=40, AC=2400 → ref=3000, refT=3000×(1-0.004×15)=3000×0.94=2820
      // Hora 2: POA=1000, T_cell=50, AC=3800 → ref=5000, refT=5000×(1-0.004×25)=5000×0.90=4500
      // PR = (2400+3800) / (3000+5000) = 6200/8000 = 0.775
      // PR_T = (2400+3800) / (2820+4500) = 6200/7320 = 0.8470
      const records: HourlyRecord[] = [
        { month: 3, poa_Wm2: 600, tamb_C: 25, tcell_C: 40, ac_W: 2400 },
        { month: 3, poa_Wm2: 1000, tamb_C: 35, tcell_C: 50, ac_W: 3800 },
      ];
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');

      expect(result.annualPR).toBeCloseTo(0.775, 2);
      expect(result.annualPR_T).toBeCloseTo(0.847, 2);
    });
  });

  describe('Temperatura de celda', () => {
    it('usa tcell_C cuando está disponible', () => {
      const records: HourlyRecord[] = [
        { month: 1, poa_Wm2: 800, tamb_C: 25, tcell_C: 50, ac_W: 3200 },
      ];
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      expect(result.avgCellTempWeighted).toBeCloseTo(50, 0);
    });

    it('calcula tcell con NOCT cuando tcell_C no está disponible', () => {
      const records: HourlyRecord[] = [
        { month: 1, poa_Wm2: 800, tamb_C: 25, wspd_ms: 1, ac_W: 3200 },
      ];
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      // T_cell = 25 + (47-20) × (800/800) × (1-0.20) × 1/(1+0.05×1)
      // = 25 + 27 × 1 × 0.80 × 0.9524 = 25 + 20.57 = 45.57
      const expectedTcell = calculateCellTemperature(25, 800, 1, 47, 20);
      expect(result.avgCellTempWeighted).toBeCloseTo(expectedTcell, 1);
    });
  });

  describe('Horas de sol y registros', () => {
    it('cuenta correctamente el total de registros', () => {
      const records = generateYearlyRecords({ poa_Wm2: 600, tamb_C: 25, ac_W: 3000 });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      expect(result.totalRecords).toBe(8760); // 365 × 24
    });

    it('cuenta correctamente las horas de sol', () => {
      const records = generateYearlyRecords({
        poa_Wm2: 600,
        tamb_C: 25,
        ac_W: 3000,
        sunHoursPerDay: 12,
      });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      // 365 días × 12 horas de sol = 4380
      expect(result.sunHours).toBe(4380);
    });
  });

  describe('Desglose mensual', () => {
    it('los meses están correctamente numerados 1-12', () => {
      const records = generateYearlyRecords({ poa_Wm2: 600, tamb_C: 25, ac_W: 3000 });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      for (let i = 0; i < 12; i++) {
        expect(result.monthly[i].month).toBe(i + 1);
      }
    });

    it('los nombres de meses están en español', () => {
      const records = generateYearlyRecords({ poa_Wm2: 600, tamb_C: 25, ac_W: 3000 });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      expect(result.monthly[0].monthName).toBe('Enero');
      expect(result.monthly[5].monthName).toBe('Junio');
      expect(result.monthly[11].monthName).toBe('Diciembre');
    });

    it('la irradiación POA mensual es coherente', () => {
      const records = generateYearlyRecords({
        poa_Wm2: 600,
        tamb_C: 25,
        ac_W: 3000,
        sunHoursPerDay: 12,
      });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      // Enero: 31 días × 12 horas × 600 W/m² = 223200 Wh/m² = 223.2 kWh/m²
      expect(result.monthly[0].totalPOA_kWhm2).toBeCloseTo(223.2, 0);
    });

    it('las horas de sol mensuales son coherentes', () => {
      const records = generateYearlyRecords({
        poa_Wm2: 600,
        tamb_C: 25,
        ac_W: 3000,
        sunHoursPerDay: 12,
      });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      // Enero: 31 días × 12 horas = 372
      expect(result.monthly[0].hoursWithSun).toBe(372);
      // Febrero: 28 días × 12 horas = 336
      expect(result.monthly[1].hoursWithSun).toBe(336);
    });
  });

  describe('Casos límite', () => {
    it('devuelve PR_T = 0 cuando no hay registros', () => {
      const result = calculatePR_T_Hourly([], 5, -0.004, 47, 20, 'pvwatts');
      expect(result.annualPR_T).toBe(0);
      expect(result.annualPR).toBe(0);
      expect(result.sunHours).toBe(0);
    });

    it('devuelve PR_T = 0 cuando toda la irradiancia está bajo el umbral', () => {
      const records: HourlyRecord[] = Array.from({ length: 100 }, () => ({
        month: 1,
        poa_Wm2: 30, // Bajo umbral de 50
        tamb_C: 25,
        ac_W: 10,
      }));
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      expect(result.annualPR_T).toBe(0);
      expect(result.sunHours).toBe(0);
    });

    it('maneja systemCapacity_kW = 0 sin errores', () => {
      const records: HourlyRecord[] = [
        { month: 1, poa_Wm2: 800, tamb_C: 25, tcell_C: 45, ac_W: 3200 },
      ];
      const result = calculatePR_T_Hourly(records, 0, -0.004, 47, 20, 'pvwatts');
      expect(result.systemCapacity_kW).toBe(0);
      // finalYield será 0 por la división por 0
      expect(result.monthly[0].finalYield).toBe(0);
    });

    it('maneja meses sin datos (registros solo en algunos meses)', () => {
      const records: HourlyRecord[] = [
        { month: 6, poa_Wm2: 800, tamb_C: 30, tcell_C: 45, ac_W: 3200 },
        { month: 6, poa_Wm2: 700, tamb_C: 28, tcell_C: 42, ac_W: 2800 },
      ];
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      // Solo junio tiene datos
      expect(result.monthly[5].hoursWithSun).toBe(2);
      // Enero no tiene datos
      expect(result.monthly[0].hoursWithSun).toBe(0);
      expect(result.monthly[0].pr).toBe(0);
      expect(result.monthly[0].pr_t).toBe(0);
    });
  });

  describe('Consistencia energética', () => {
    it('la suma de AC mensual ≈ AC anual', () => {
      const records = generateYearlyRecords({
        poa_Wm2: 700,
        tamb_C: 28,
        ac_W: 3500,
        sunHoursPerDay: 11,
      });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      const sumMonthlyAC = result.monthly.reduce((s, m) => s + m.totalAC_kWh, 0);
      // La energía anual total debería ser sunHours × ac_W / 1000
      const expectedAC = result.sunHours * 3.5; // 3500W = 3.5 kWh/h
      expect(sumMonthlyAC).toBeCloseTo(expectedAC, 0);
    });

    it('PR anual está entre 0 y 1 para datos realistas', () => {
      const records = generateYearlyRecords({
        poa_Wm2: 700,
        tamb_C: 28,
        tcell_C: 45,
        ac_W: 2800, // ~80% de 5kW × 0.7
      });
      const result = calculatePR_T_Hourly(records, 5, -0.004, 47, 20, 'pvwatts');
      expect(result.annualPR).toBeGreaterThan(0);
      expect(result.annualPR).toBeLessThan(1);
      expect(result.annualPR_T).toBeGreaterThan(0);
      expect(result.annualPR_T).toBeLessThan(1.5); // PR_T puede ser > 1 en climas muy cálidos
    });
  });
});
