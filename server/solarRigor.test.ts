import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { parseEPW } from '@/lib/epwParser';
import { validateSolarRigor } from '@/lib/solarRigor';

const bogotaZip = path.resolve(
  'attached_assets/COL_CUN_Bogota-Eldorado.Intl.AP.802220_TMYx.2009-2023_1786197954787.zip',
);

function loadBogotaEPW() {
  const content = execFileSync('unzip', ['-p', bogotaZip, '*.epw'], {
    encoding: 'utf8',
    maxBuffer: 4 * 1024 * 1024,
  });
  return parseEPW(content);
}

describe('validación de rigor solar EPW', () => {
  it('valida el EPW TMYx de Bogotá como una serie representativa de 8.760 horas', () => {
    const epw = loadBogotaEPW();
    const report = validateSolarRigor({ epwData: epw });

    expect(epw.weatherData).toHaveLength(8760);
    expect(epw.location.latitude).toBeCloseTo(4.702, 5);
    expect(epw.location.longitude).toBeCloseTo(-74.147, 5);
    expect(epw.location.timezone).toBe(-5);
    expect(epw.location.elevation).toBeCloseTo(2548.4, 1);
    expect(epw.metadata?.isTypicalMeteorologicalYear).toBe(true);
    expect(report.validHourlyYear).toBe(true);
    expect(report.scope).toBe('annual_8760');
    expect(report.scopeLabel).toBe('Cálculo anual de 8.760 horas');
    expect(report.errorCount).toBe(0);
  });

  it('rechaza un EPW incompleto y lo clasifica como fechas críticas', () => {
    const epw = loadBogotaEPW();
    const report = validateSolarRigor({
      epwData: { ...epw, weatherData: epw.weatherData.slice(0, -1) },
    });

    expect(report.validHourlyYear).toBe(false);
    expect(report.scope).toBe('critical_dates');
    expect(report.canCalculate).toBe(false);
    expect(report.checks.find(check => check.key === 'epw')?.status).toBe('error');
  });

  it('detecta una hora duplicada aunque el total siga siendo 8.760', () => {
    const epw = loadBogotaEPW();
    const records = [...epw.weatherData];
    records[records.length - 1] = { ...records[0] };
    const report = validateSolarRigor({ epwData: { ...epw, weatherData: records } });

    expect(report.validHourlyYear).toBe(false);
    expect(report.checks.find(check => check.key === 'hourly_alignment')?.status).toBe('error');
  });
});