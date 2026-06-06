/**
 * Tests para PVWatts Proxy y normalización de respuestas
 */
import { describe, it, expect } from 'vitest';
import { normalizePVWattsResponse, classifySpecificYield } from '../client/src/lib/pvwattsApi';

describe('PVWatts API - Normalización de respuestas', () => {
  const mockPVWattsResponse = {
    inputs: {
      lat: '6.25',
      lon: '-75.56',
      system_capacity: '1',
      azimuth: '180',
      tilt: '6.25',
      array_type: '0',
      module_type: '0',
      losses: '14.08',
    },
    outputs: {
      ac_monthly: [120, 110, 125, 118, 115, 108, 112, 115, 118, 122, 116, 119],
      dc_monthly: [135, 124, 141, 133, 130, 122, 126, 130, 133, 137, 131, 134],
      poa_monthly: [155, 142, 162, 153, 150, 140, 145, 150, 153, 158, 151, 154],
      dn_monthly: [90, 82, 95, 88, 85, 78, 82, 85, 88, 92, 87, 89],
      df_monthly: [65, 60, 67, 65, 65, 62, 63, 65, 65, 66, 64, 65],
      tamb_monthly: [22, 22.5, 22, 21.5, 21, 20.5, 20, 20.5, 21, 21.5, 22, 22],
      tcell_monthly: [35, 35.5, 36, 34.5, 34, 33, 33.5, 34, 34.5, 35, 35.5, 35],
      wspd_monthly: [2.1, 2.0, 1.9, 1.8, 1.7, 1.8, 2.0, 2.1, 1.9, 1.8, 1.9, 2.0],
      ac_annual: 1398,
      dc_annual: 1576,
      solrad_annual: 4.8,
    },
    station_info: {
      city: 'Medellin',
      state: 'Antioquia',
      country: 'Colombia',
      lat: 6.25,
      lon: -75.56,
      elev: 1495,
      tz: -5,
      distance: 10,
      solar_resource_file: 'TMY3',
    },
  };

  const params = { lat: 6.25, lon: -75.56, system_capacity: 1 };

  it('normaliza respuesta PVWatts correctamente', () => {
    const result = normalizePVWattsResponse(mockPVWattsResponse, params);

    expect(result.annualAC_kWh).toBe(1398);
    expect(result.annualDC_kWh).toBe(1576);
    expect(result.monthly).toHaveLength(12);
    expect(result.monthly[0].month).toBe(1);
    expect(result.monthly[0].monthName).toBe('Enero');
    expect(result.monthly[0].ac_kWh).toBe(120);
    expect(result.monthly[0].dc_kWh).toBe(135);
    expect(result.monthly[0].tamb_C).toBe(22);
    expect(result.monthly[0].tcell_C).toBe(35);
  });

  it('calcula Specific Yield correctamente', () => {
    const result = normalizePVWattsResponse(mockPVWattsResponse, params);
    // specificYield = annualAC / system_capacity = 1398 / 1 = 1398
    expect(result.specificYield).toBe(1398);
  });

  it('calcula Capacity Factor correctamente', () => {
    const result = normalizePVWattsResponse(mockPVWattsResponse, params);
    // CF = (1398 / (1 * 8760)) * 100 ≈ 15.96%
    expect(result.capacityFactor).toBeCloseTo(15.96, 1);
  });

  it('normaliza station_info con conversión de millas a km', () => {
    const result = normalizePVWattsResponse(mockPVWattsResponse, params);
    expect(result.stationInfo.city).toBe('Medellin');
    expect(result.stationInfo.country).toBe('Colombia');
    // 10 miles * 1.60934 = 16.09 km
    expect(result.stationInfo.distance).toBeCloseTo(16.09, 1);
  });

  it('maneja respuesta con campos faltantes', () => {
    const minimal = { outputs: {}, inputs: {}, station_info: {} };
    const result = normalizePVWattsResponse(minimal, { lat: 4, lon: -74 });

    expect(result.monthly).toHaveLength(12);
    expect(result.monthly[0].ac_kWh).toBe(0);
    expect(result.annualAC_kWh).toBe(0);
    expect(result.stationInfo.city).toBe('');
  });

  it('usa defaults correctos para parámetros opcionales', () => {
    const result = normalizePVWattsResponse(mockPVWattsResponse, { lat: 6.25, lon: -75.56 });
    expect(result.params.systemCapacity).toBe(1);
    expect(result.params.azimuth).toBe(180); // lat > 0 → 180
    expect(result.params.tilt).toBeCloseTo(6.25); // |lat|
    expect(result.params.losses).toBe(14.08);
  });

  it('azimuth default 0 para hemisferio sur', () => {
    const result = normalizePVWattsResponse(mockPVWattsResponse, { lat: -33.45, lon: -70.66 });
    expect(result.params.azimuth).toBe(0); // lat < 0 → 0
  });
});

describe('PVWatts API - Clasificación de Specific Yield', () => {
  it('clasifica ≥1800 como Excelente', () => {
    expect(classifySpecificYield(1800).category).toBe('Excelente');
    expect(classifySpecificYield(2000).category).toBe('Excelente');
  });

  it('clasifica 1600-1799 como Muy Buena', () => {
    expect(classifySpecificYield(1600).category).toBe('Muy Buena');
    expect(classifySpecificYield(1799).category).toBe('Muy Buena');
  });

  it('clasifica 1400-1599 como Buena', () => {
    expect(classifySpecificYield(1400).category).toBe('Buena');
    expect(classifySpecificYield(1599).category).toBe('Buena');
  });

  it('clasifica 1200-1399 como Aceptable', () => {
    expect(classifySpecificYield(1200).category).toBe('Aceptable');
    expect(classifySpecificYield(1399).category).toBe('Aceptable');
  });

  it('clasifica 1000-1199 como Limitada', () => {
    expect(classifySpecificYield(1000).category).toBe('Limitada');
    expect(classifySpecificYield(1199).category).toBe('Limitada');
  });

  it('clasifica <1000 como Muy Limitada', () => {
    expect(classifySpecificYield(999).category).toBe('Muy Limitada');
    expect(classifySpecificYield(500).category).toBe('Muy Limitada');
  });

  it('retorna colores correctos', () => {
    expect(classifySpecificYield(1900).color).toBe('#d32f2f');
    expect(classifySpecificYield(1700).color).toBe('#f57c00');
    expect(classifySpecificYield(1500).color).toBe('#fbc02d');
    expect(classifySpecificYield(1300).color).toBe('#7cb342');
    expect(classifySpecificYield(1100).color).toBe('#1976d2');
    expect(classifySpecificYield(800).color).toBe('#616161');
  });
});

describe('PVWatts API - Corrección GHI diario a anual', () => {
  it('convierte solrad_annual diario (< 50) a anual multiplicando por 365', () => {
    const response = {
      outputs: {
        ac_monthly: [120, 110, 125, 118, 115, 108, 112, 115, 118, 122, 116, 119],
        dc_monthly: [135, 124, 141, 133, 130, 122, 126, 130, 133, 137, 131, 134],
        poa_monthly: [155, 142, 162, 153, 150, 140, 145, 150, 153, 158, 151, 154],
        solrad_annual: 4.8, // kWh/m²/día
      },
      inputs: {},
      station_info: {},
    };
    const result = normalizePVWattsResponse(response, { lat: 6.25, lon: -75.56 });
    // 4.8 * 365 = 1752
    expect(result.annualGHI_kWhm2).toBe(4.8 * 365);
  });

  it('no multiplica si solrad_annual ya es anual (>= 50)', () => {
    const response = {
      outputs: {
        ac_monthly: [120, 110, 125, 118, 115, 108, 112, 115, 118, 122, 116, 119],
        dc_monthly: [135, 124, 141, 133, 130, 122, 126, 130, 133, 137, 131, 134],
        poa_monthly: [155, 142, 162, 153, 150, 140, 145, 150, 153, 158, 151, 154],
        solrad_annual: 1752, // ya es anual
      },
      inputs: {},
      station_info: {},
    };
    const result = normalizePVWattsResponse(response, { lat: 6.25, lon: -75.56 });
    expect(result.annualGHI_kWhm2).toBe(1752);
  });

  it('usa POA anual como fallback cuando solrad_annual no existe', () => {
    const response = {
      outputs: {
        ac_monthly: [120, 110, 125, 118, 115, 108, 112, 115, 118, 122, 116, 119],
        dc_monthly: [135, 124, 141, 133, 130, 122, 126, 130, 133, 137, 131, 134],
        poa_monthly: [155, 142, 162, 153, 150, 140, 145, 150, 153, 158, 151, 154],
        // sin solrad_annual
      },
      inputs: {},
      station_info: {},
    };
    const result = normalizePVWattsResponse(response, { lat: 6.25, lon: -75.56 });
    const expectedPOA = [155, 142, 162, 153, 150, 140, 145, 150, 153, 158, 151, 154].reduce((a, b) => a + b, 0);
    expect(result.annualGHI_kWhm2).toBe(expectedPOA);
  });
});

describe('PVWatts Proxy - Validación de API key', () => {
  it('NREL_API_KEY está configurada en el entorno', () => {
    // Este test valida que la secret fue configurada correctamente
    const key = process.env.NREL_API_KEY;
    expect(key).toBeDefined();
    expect(key!.length).toBeGreaterThan(5);
  });
});
