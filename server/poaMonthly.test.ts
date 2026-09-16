import { describe, expect, it } from "vitest";
import { calculateMonthlyPOA, POA_MONTH_LABELS } from "../client/src/lib/poaMonthly";
import type { EPWData, WeatherData } from "../client/src/lib/epwParser";
import * as fs from "fs";
import * as path from "path";

function hour(overrides: Partial<WeatherData> & { month: number; day: number; hour: number }): WeatherData {
  return {
    year: 2020,
    minute: 0,
    temperature: 20,
    dewPoint: 15,
    relativeHumidity: 70,
    atmosphericPressure: 101325,
    directNormalIrradiance: 0,
    diffuseHorizontalIrradiance: 0,
    globalHorizontalIrradiance: 0,
    windSpeed: 2,
    cloudCover: 5,
    ...overrides,
  };
}

// Un mes sintético con 3 días: 1 hora de sol (GHI/DNI>0) y 1 hora nocturna
// (todo en 0) por día -- suficiente para probar agregación sin 8760 filas.
function buildMonth(month: number, opts: { temp: number; wind: number }): WeatherData[] {
  const rows: WeatherData[] = [];
  for (let day = 1; day <= 3; day++) {
    rows.push(hour({
      month, day, hour: 12,
      temperature: opts.temp, windSpeed: opts.wind,
      directNormalIrradiance: 700, diffuseHorizontalIrradiance: 120, globalHorizontalIrradiance: 650,
    }));
    rows.push(hour({
      month, day, hour: 0,
      temperature: opts.temp - 5, windSpeed: opts.wind + 1,
      directNormalIrradiance: 0, diffuseHorizontalIrradiance: 0, globalHorizontalIrradiance: 0,
    }));
  }
  return rows;
}

function buildEPW(): EPWData {
  const weatherData: WeatherData[] = [];
  for (let m = 1; m <= 12; m++) {
    weatherData.push(...buildMonth(m, { temp: 15 + m, wind: 1 + m * 0.1 }));
  }
  return {
    location: { city: 'Test', state: '', country: 'COL', latitude: 4.6, longitude: -74.1, timezone: -5, elevation: 2600 },
    weatherData,
  };
}

describe("calculateMonthlyPOA -- contrato de agregación mensual", () => {
  const epw = buildEPW();
  const result = calculateMonthlyPOA(epw, 10, 0, 0.2, false);

  it("devuelve exactamente 12 meses, en el orden Ene..Dic", () => {
    expect(result).toHaveLength(12);
    expect(result.map(r => r.month)).toEqual(POA_MONTH_LABELS);
  });

  it("cada mes tiene los 7 campos completos del contrato", () => {
    for (const m of result) {
      expect(m).toHaveProperty('month');
      expect(m).toHaveProperty('directPOA');
      expect(m).toHaveProperty('diffusePOA');
      expect(m).toHaveProperty('reflectedPOA');
      expect(m).toHaveProperty('totalPOA');
      expect(m).toHaveProperty('avgTemp');
      expect(m).toHaveProperty('avgWindSpeed');
    }
  });

  it("directPOA + diffusePOA + reflectedPOA es coherente con totalPOA (tolerancia de redondeo)", () => {
    for (const m of result) {
      if (m.totalPOA === 0) continue;
      const sumaComponentes = m.directPOA + m.diffusePOA + m.reflectedPOA;
      // Cada componente se redondea por separado (Math.round independiente),
      // así que puede diferir del total redondeado por el error de redondeo
      // acumulado de hasta 3 términos -- no por un error real del modelo.
      expect(Math.abs(sumaComponentes - m.totalPOA)).toBeLessThanOrEqual(2);
    }
  });

  it("avgTemp y avgWindSpeed promedian TODAS las horas del mes, incluida la nocturna", () => {
    // Enero: temp=16 a mediodía, 11 en la hora nocturna -> promedio 13.5
    const enero = result[0];
    expect(enero.avgTemp).toBeCloseTo(13.5, 1);
    // wind=1.1 a mediodía, 2.1 en la hora nocturna -> promedio 1.6
    expect(enero.avgWindSpeed).toBeCloseTo(1.6, 1);
  });

  it("las horas sin irradiancia no aportan a las componentes solares, pero SÍ cuentan en el denominador", () => {
    // 3 días x 1 hora con sol de 2 -> denominador = 6 horas totales del mes,
    // no 3 -- por eso el promedio es la mitad de lo que sería si solo se
    // promediara sobre las horas con sol.
    const soloHorasConSol = calculateMonthlyPOA({
      ...epw,
      weatherData: epw.weatherData.filter(w => w.month === 1 && w.globalHorizontalIrradiance > 0),
    }, 10, 0, 0.2, false)[0];
    const conNoche = result[0];
    expect(Math.abs(conNoche.totalPOA - soloHorasConSol.totalPOA / 2)).toBeLessThanOrEqual(1);
  });

  it("un mes sin registros devuelve todo en cero y avgWindSpeed=1 (sentinel, no un valor medido)", () => {
    const epwSinDiciembre: EPWData = { ...epw, weatherData: epw.weatherData.filter(w => w.month !== 12) };
    const diciembre = calculateMonthlyPOA(epwSinDiciembre, 10, 0, 0.2, false)[11];
    expect(diciembre).toEqual({
      month: 'Dic', directPOA: 0, diffusePOA: 0, reflectedPOA: 0, totalPOA: 0, avgTemp: 0, avgWindSpeed: 1,
    });
  });

  it("usePerezModel=true produce un resultado distinto (y finito) al de Liu-Jordan para el mismo EPW", () => {
    const perez = calculateMonthlyPOA(epw, 10, 0, 0.2, true);
    for (const m of perez) {
      expect(Number.isFinite(m.totalPOA)).toBe(true);
    }
    // Liu-Jordan y Perez no deberían coincidir exactamente en la componente difusa.
    expect(perez[0].diffusePOA).not.toBe(result[0].diffusePOA);
  });
});

describe("calculateMonthlyPOA -- regresión de no-duplicación (Home.tsx / POAAnalyzer.tsx)", () => {
  const homeSrc = fs.readFileSync(
    path.join(__dirname, "..", "client", "src", "pages", "Home.tsx"), "utf-8");
  const poaAnalyzerSrc = fs.readFileSync(
    path.join(__dirname, "..", "client", "src", "components", "POAAnalyzer.tsx"), "utf-8");

  it("Home.tsx consume calculateMonthlyPOA para el contrato poaData", () => {
    expect(homeSrc).toContain("calculateMonthlyPOA(weatherData, effectiveTilt, poaAzimuth, poaAlbedo, poaUsePerez)");
  });

  it("POAAnalyzer.tsx consume calculateMonthlyPOA en vez de reimplementar el agregado mensual", () => {
    expect(poaAnalyzerSrc).toContain("calculateMonthlyPOA(weatherData, tilt, azimuth, albedo, usePerezModel)");
    // Ya no debe llamar a calculateHourlyPOA directamente -- esa era la
    // implementación duplicada que este cambio elimina.
    expect(poaAnalyzerSrc).not.toContain("calculateHourlyPOA(");
  });

  it("Home.tsx conserva exactamente una llamada a calculateHourlyPOA (multiFacadeReportData, fuera de este contrato)", () => {
    const ocurrencias = (homeSrc.match(/calculateHourlyPOA\(/g) || []).length;
    expect(ocurrencias).toBe(1);
  });
});
