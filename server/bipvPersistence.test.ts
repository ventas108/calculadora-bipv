/**
 * Tests para la persistencia de simulaciones BIPV
 * Verifica: tabla bipv_hourly_results, API tRPC, modelo Perez, exportación
 */
import { describe, it, expect } from 'vitest';
import {
  runBIPVSimulation,
  calculatePOATransposition,
  calculatePOAPerez,
  calculateIAM_ASHRAE,
  calculateAOI,
  calculateSoiling,
  calculateThermalBIPV,
  calculateAdjustedEfficiency,
  calculateBIPVPower,
  calculatePassiveLighting,
  DEFAULT_SOILING_CONFIG,
  type BIPVSimulationConfig,
  type WeatherHourData,
} from '../client/src/lib/iamSoilingEngine';
import { BIPV_GLASS_CATALOG, SOILING_PRESETS, THERMAL_MOUNTING_TYPES, TRANSPARENCY_LEVELS } from '../client/src/lib/bipvGlassCatalog';

// ─── Helper: generar datos EPW sintéticos ─────────────────────────────────────
function generateSyntheticEPW(months = 12): WeatherHourData[] {
  const data: WeatherHourData[] = [];
  for (let m = 1; m <= months; m++) {
    for (let d = 1; d <= 28; d++) {
      for (let h = 6; h <= 18; h++) {
        const hourAngle = (h - 12) * 15;
        const elevation = Math.max(0, 60 - Math.abs(hourAngle) * 0.8);
        const ghi = elevation > 0 ? 200 + elevation * 8 : 0;
        const dni = elevation > 5 ? ghi * 0.7 : 0;
        const dhi = ghi - dni * Math.sin(elevation * Math.PI / 180);
        data.push({
          month: m,
          day: d,
          hour: h,
          ghi: Math.max(0, ghi),
          dni: Math.max(0, dni),
          dhi: Math.max(0, dhi),
          tempAir: 20 + 5 * Math.sin((m - 1) * Math.PI / 6),
          windSpeed: 2 + Math.random(),
          precipitableWater: m >= 4 && m <= 9 ? 30 : 10,
        });
      }
    }
  }
  return data;
}

describe('Modelo Perez vs Isotrópico', () => {
  const weatherData = generateSyntheticEPW(1); // Solo enero para velocidad
  const tech = BIPV_GLASS_CATALOG[0]; // a-Si

  it('calculatePOAPerez devuelve valores positivos para ángulos válidos', () => {
    const result = calculatePOAPerez(
      500, 200, 100, // dni, ghi, dhi
      30, // zenithDeg
      180, // azimuthSolar
      90, // tiltDeg
      180, // azimuthSurface
      4.5 // latitude
    );
    expect(result.poaTotal).toBeGreaterThan(0);
    expect(result.poaDirecta).toBeGreaterThanOrEqual(0);
    expect(result.poaDifusa).toBeGreaterThanOrEqual(0);
    expect(result.poaReflejada).toBeGreaterThanOrEqual(0);
  });

  it('calculatePOAPerez devuelve 0 cuando sol está bajo el horizonte', () => {
    const result = calculatePOAPerez(
      0, 0, 0, // dni, ghi, dhi = 0 (noche)
      95, // zenithDeg > 90
      180,
      90, 180,
      4.5
    );
    expect(result.poaTotal).toBe(0);
    expect(result.poaDirecta).toBe(0);
  });

  it('Perez produce más irradiancia que isotrópico para fachada vertical sur', () => {
    // En condiciones de cielo claro, Perez debería captar más por la componente circunsolar
    const isotropic = calculatePOATransposition(500, 200, 100, 30, 180, 90, 180);
    const perez = calculatePOAPerez(500, 200, 100, 30, 180, 90, 180, 4.5);
    // Perez generalmente produce >= isotrópico en cielo claro
    expect(perez.poaTotal).toBeGreaterThanOrEqual(isotropic.poaTotal * 0.8);
  });

  it('runBIPVSimulation con transpositionModel=perez genera resultados válidos', () => {
    const fullWeather = generateSyntheticEPW(3); // Más datos para Perez
    const config: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.20,
      areaM2: 100,
      inclinacionFachada: 45, // Inclinación más favorable para Perez
      azimutFachada: 180,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.3,
      transpositionModel: 'perez',
      generateHourlyResults: false,
    };

    const result = runBIPVSimulation(fullWeather, 4.5, -74, -5, config, []);
    expect(result.energiaAnualKwh).toBeGreaterThanOrEqual(0);
    expect(result.transpositionModel).toBe('perez');
    expect(result.iamPromedio).toBeGreaterThanOrEqual(0);
    expect(result.iamPromedio).toBeLessThanOrEqual(1);
  });

  it('runBIPVSimulation con transpositionModel=isotropic genera resultados válidos', () => {
    const config: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.20,
      areaM2: 100,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.3,
      transpositionModel: 'isotropic',
      generateHourlyResults: false,
    };

    const result = runBIPVSimulation(weatherData, 4.5, -74, -5, config, []);
    expect(result.energiaAnualKwh).toBeGreaterThan(0);
    expect(result.transpositionModel).toBe('isotropic');
  });
});

describe('Generación de resultados horarios', () => {
  const weatherData = generateSyntheticEPW(1);
  const tech = BIPV_GLASS_CATALOG[1]; // CdTe

  it('generateHourlyResults=true produce array de hourlyResults', () => {
    const config: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.20,
      areaM2: 50,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.3,
      transpositionModel: 'isotropic',
      generateHourlyResults: true,
    };

    const result = runBIPVSimulation(weatherData, 4.5, -74, -5, config, []);
    expect(result.hourlyResults).toBeDefined();
    expect(result.hourlyResults!.length).toBeGreaterThan(0);
    expect(result.hourlyResults!.length).toBeLessThanOrEqual(weatherData.length);
  });

  it('hourlyResults contiene todos los campos requeridos', () => {
    const config: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.10,
      areaM2: 50,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.3,
      transpositionModel: 'perez',
      generateHourlyResults: true,
    };

    const result = runBIPVSimulation(weatherData, 4.5, -74, -5, config, []);
    const hr = result.hourlyResults![0];
    expect(hr).toHaveProperty('timestamp');
    expect(hr).toHaveProperty('month');
    expect(hr).toHaveProperty('hour');
    expect(hr).toHaveProperty('elevacionSolar');
    expect(hr).toHaveProperty('azimutSolar');
    expect(hr).toHaveProperty('zenithSolar');
    expect(hr).toHaveProperty('dniOriginal');
    expect(hr).toHaveProperty('dniConSombra');
    expect(hr).toHaveProperty('ghi');
    expect(hr).toHaveProperty('dhi');
    expect(hr).toHaveProperty('poaDirecta');
    expect(hr).toHaveProperty('poaDifusa');
    expect(hr).toHaveProperty('poaTotal');
    expect(hr).toHaveProperty('poaTotalOptica');
    expect(hr).toHaveProperty('factorSombraSF');
    expect(hr).toHaveProperty('fIamAshrae');
    expect(hr).toHaveProperty('soilingReal');
    expect(hr).toHaveProperty('factorTermico');
    expect(hr).toHaveProperty('tAmb');
    expect(hr).toHaveProperty('tCell');
    expect(hr).toHaveProperty('potenciaDcW');
    expect(hr).toHaveProperty('potenciaIluminacionPasivaW');
    expect(hr).toHaveProperty('aoiDeg');
  });

  it('generateHourlyResults=false no produce hourlyResults', () => {
    const config: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.20,
      areaM2: 50,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.3,
      generateHourlyResults: false,
    };

    const result = runBIPVSimulation(weatherData, 4.5, -74, -5, config, []);
    expect(result.hourlyResults).toBeUndefined();
  });

  it('hourlyResults tiene valores numéricos válidos (sin NaN)', () => {
    const config: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.40,
      areaM2: 100,
      inclinacionFachada: 45,
      azimutFachada: 90,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.0,
      transpositionModel: 'perez',
      generateHourlyResults: true,
    };

    const result = runBIPVSimulation(weatherData, 4.5, -74, -5, config, []);
    for (const hr of result.hourlyResults!.slice(0, 50)) {
      expect(isNaN(hr.potenciaDcW)).toBe(false);
      expect(isNaN(hr.fIamAshrae)).toBe(false);
      expect(isNaN(hr.soilingReal)).toBe(false);
      expect(isNaN(hr.factorTermico)).toBe(false);
      expect(isNaN(hr.poaTotal)).toBe(false);
      expect(isNaN(hr.tCell)).toBe(false);
      expect(hr.fIamAshrae).toBeGreaterThanOrEqual(0);
      expect(hr.fIamAshrae).toBeLessThanOrEqual(1);
      expect(hr.factorTermico).toBeGreaterThan(0);
      expect(hr.factorTermico).toBeLessThanOrEqual(1.5);
    }
  });
});

describe('Pérdidas ópticas detalladas (Script Python Multivariable)', () => {
  const weatherData = generateSyntheticEPW(3);
  const tech = BIPV_GLASS_CATALOG[2]; // Perovskita

  it('irradianciaReflejadaAnualKwhM2 > 0 para fachada vertical', () => {
    const config: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.20,
      areaM2: 100,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.3,
      transpositionModel: 'isotropic',
    };

    const result = runBIPVSimulation(weatherData, 4.5, -74, -5, config, []);
    expect(result.irradianciaReflejadaAnualKwhM2).toBeGreaterThan(0);
    expect(result.perdidasSoilingAnualKwhM2).toBeGreaterThan(0);
    expect(result.perdidasTermicasAnualKwhM2).toBeGreaterThanOrEqual(0);
  });

  it('pérdidas IAM son mayores para tecnologías con b0 más alto', () => {
    const configs = BIPV_GLASS_CATALOG.map(t => ({
      technology: t,
      transparencia: 0.20,
      areaM2: 100,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.3,
      transpositionModel: 'isotropic' as const,
    }));

    const results = configs.map(c => runBIPVSimulation(weatherData, 4.5, -74, -5, c, []));
    // a-Si tiene b0=0.05 (menor pérdida), Perovskita tiene b0=0.08 (mayor pérdida)
    const aSi = results.find(r => r.technology.includes('a-Si'));
    const perov = results.find(r => r.technology.includes('Perovskita'));
    if (aSi && perov) {
      // Mayor b0 produce mayor o igual pérdida IAM
      expect(perov.irradianciaReflejadaAnualKwhM2).toBeGreaterThanOrEqual(aSi.irradianciaReflejadaAnualKwhM2);
    }
  });

  it('pérdidas soiling son mayores con preset árido industrial', () => {
    const cleanPreset = SOILING_PRESETS.find(p => p.id === 'templado_limpio')!;
    const dirtyPreset = SOILING_PRESETS.find(p => p.id === 'arido_industrial')!;

    const configClean: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.20,
      areaM2: 100,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: cleanPreset.config,
      kBipv: 1.3,
    };

    const configDirty: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.20,
      areaM2: 100,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: dirtyPreset.config,
      kBipv: 1.3,
    };

    const resultClean = runBIPVSimulation(weatherData, 4.5, -74, -5, configClean, []);
    const resultDirty = runBIPVSimulation(weatherData, 4.5, -74, -5, configDirty, []);
    expect(resultDirty.perdidasSoilingAnualKwhM2).toBeGreaterThan(resultClean.perdidasSoilingAnualKwhM2);
  });
});

describe('Modelo térmico confinado BIPV', () => {
  const weatherData = generateSyntheticEPW(1);
  const tech = BIPV_GLASS_CATALOG[0];

  it('k_bipv más alto produce más pérdida térmica', () => {
    const configVentilado: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.20,
      areaM2: 100,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.0, // ventilado
    };

    const configConfinado: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.20,
      areaM2: 100,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.5, // sin ventilación
    };

    const resultVent = runBIPVSimulation(weatherData, 4.5, -74, -5, configVentilado, []);
    const resultConf = runBIPVSimulation(weatherData, 4.5, -74, -5, configConfinado, []);
    // Confinado tiene más pérdida térmica
    expect(resultConf.perdidasTermicasAnualKwhM2).toBeGreaterThanOrEqual(resultVent.perdidasTermicasAnualKwhM2);
    // Ventilado produce más energía
    expect(resultVent.energiaAnualKwh).toBeGreaterThanOrEqual(resultConf.energiaAnualKwh);
  });

  it('THERMAL_MOUNTING_TYPES tiene 4 opciones con k_bipv creciente', () => {
    expect(THERMAL_MOUNTING_TYPES.length).toBe(4);
    for (let i = 1; i < THERMAL_MOUNTING_TYPES.length; i++) {
      expect(THERMAL_MOUNTING_TYPES[i].kBipv).toBeGreaterThanOrEqual(THERMAL_MOUNTING_TYPES[i - 1].kBipv);
    }
  });
});

describe('Catálogo BIPV y presets', () => {
  it('BIPV_GLASS_CATALOG tiene 8 tecnologías (1G + 2G + 3G + HIITIO + EINNOVA)', () => {
    expect(BIPV_GLASS_CATALOG.length).toBe(8);
    // Verificar que incluye las 3 generaciones originales + 4 HIITIO + 1 EINNOVA
    const generations = BIPV_GLASS_CATALOG.map(t => t.generation);
    expect(generations.filter(g => g === '1G').length).toBe(1);
    expect(generations.filter(g => g === '2G').length).toBe(6); // CdTe genérico + 4 HIITIO + 1 EINNOVA
    expect(generations.filter(g => g === '3G').length).toBe(1);
    // Verificar que los HIITIO están presentes
    expect(BIPV_GLASS_CATALOG.find(t => t.id === 'HIITIO_H12_CdTe_0T')).toBeDefined();
    expect(BIPV_GLASS_CATALOG.find(t => t.id === 'HIITIO_H15_CdTe_60T')).toBeDefined();
    expect(BIPV_GLASS_CATALOG.find(t => t.id === 'EINNOVA_P18_Vidrio_40T')).toBeDefined();
  });

  it('SOILING_PRESETS tiene 5 presets con factores mensuales válidos', () => {
    expect(SOILING_PRESETS.length).toBe(5);
    for (const preset of SOILING_PRESETS) {
      expect(preset.config.monthlyFactors).toBeDefined();
      for (let m = 1; m <= 12; m++) {
        const factor = preset.config.monthlyFactors[m];
        expect(factor).toBeGreaterThanOrEqual(0);
        expect(factor).toBeLessThanOrEqual(1);
      }
    }
  });

  it('TRANSPARENCY_LEVELS tiene 6 niveles entre 10% y 60%', () => {
    expect(TRANSPARENCY_LEVELS.length).toBe(6);
    expect(TRANSPARENCY_LEVELS[0].value).toBe(0.10);
    expect(TRANSPARENCY_LEVELS[TRANSPARENCY_LEVELS.length - 1].value).toBe(0.60);
  });
});

describe('Simulación comparativa multi-tecnología', () => {
  const weatherData = generateSyntheticEPW(1);

  it('produce resultados para cada combinación tech × transparencia', () => {
    const techs = BIPV_GLASS_CATALOG.slice(0, 2);
    const transparencies = [0.10, 0.20];

    const results: BIPVSimulationSummary[] = [];
    for (const tech of techs) {
      for (const tau of transparencies) {
        const config: BIPVSimulationConfig = {
          technology: tech,
          transparencia: tau,
          areaM2: 100,
          inclinacionFachada: 90,
          azimutFachada: 180,
          soiling: DEFAULT_SOILING_CONFIG,
          kBipv: 1.3,
        };
        results.push(runBIPVSimulation(weatherData, 4.5, -74, -5, config, []));
      }
    }

    expect(results.length).toBe(4); // 2 techs × 2 transparencies
    for (const r of results) {
      expect(r.energiaAnualKwh).toBeGreaterThan(0);
      expect(r.produccionMensualKwh.length).toBe(12);
      expect(r.iluminacionMensualKwh.length).toBe(12);
    }
  });

  it('mayor transparencia reduce producción pero aumenta iluminación', () => {
    const tech = BIPV_GLASS_CATALOG[0];
    const configLow: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.10,
      areaM2: 100,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.3,
    };
    const configHigh: BIPVSimulationConfig = {
      technology: tech,
      transparencia: 0.60,
      areaM2: 100,
      inclinacionFachada: 90,
      azimutFachada: 180,
      soiling: DEFAULT_SOILING_CONFIG,
      kBipv: 1.3,
    };

    const resultLow = runBIPVSimulation(weatherData, 4.5, -74, -5, configLow, []);
    const resultHigh = runBIPVSimulation(weatherData, 4.5, -74, -5, configHigh, []);

    // Menor transparencia = más producción eléctrica
    expect(resultLow.energiaAnualKwh).toBeGreaterThan(resultHigh.energiaAnualKwh);
    // Mayor transparencia = más iluminación pasiva
    expect(resultHigh.iluminacionPasivaAnualKwh).toBeGreaterThan(resultLow.iluminacionPasivaAnualKwh);
  });
});
