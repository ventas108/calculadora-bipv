import { describe, expect, it } from "vitest";
import { parseEPW } from "../client/src/lib/epwParser";

// Construye una fila de datos EPW válida (>=23 campos), con las columnas que
// epwParser.ts realmente lee: 0 Year, 1 Month, 2 Day, 3 Hour, 4 Minute,
// 6 DryBulb, 7 DewPoint, 8 RH, 9 Pressure, 13 GHI, 14 DNI, 15 DHI,
// 21 WindSpeed, 22 TotSkyCvr.
function dataRow(overrides: Partial<{
  year: number; month: number; day: number; hour: number; minute: number;
  dryBulb: number; dewPoint: number; rh: number; pressure: number;
  ghi: number; dni: number; dhi: number; windSpeed: number; cloudCover: number;
}> = {}): string {
  const v = {
    year: 2020, month: 1, day: 1, hour: 1, minute: 0,
    dryBulb: 20, dewPoint: 15, rh: 80, pressure: 101325,
    ghi: 0, dni: 0, dhi: 0, windSpeed: 2, cloudCover: 5,
    ...overrides,
  };
  // índices: 0    1       2     3     4       5    6          7           8   9          10 11 12  13     14     15     16 17 18 19 20  21          22
  const fields = [
    v.year, v.month, v.day, v.hour, v.minute, '?', v.dryBulb, v.dewPoint, v.rh, v.pressure,
    0, 0, 0, v.ghi, v.dni, v.dhi, 0, 0, 0, 0, 0, v.windSpeed, v.cloudCover,
  ];
  return fields.join(',');
}

const LOCATION_LINE = 'LOCATION,Bogota,Cundinamarca,COL,IWEC Data,802220,4.71,-74.15,-5.0,2547.0';
const HEADER_LINES = [
  LOCATION_LINE,
  'DESIGN CONDITIONS,1,Climate Design Data',
  'TYPICAL/EXTREME PERIODS,0',
  'GROUND TEMPERATURES,0',
  'HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0',
  'COMMENTS 1,Fuente sintetica para tests',
  'COMMENTS 2,Period of Record=2005-2020; TMY/TMYx representative',
  'DATA PERIODS,1,1,Data,Sunday, 1/ 1,12/31',
];

function buildEPW(dataLines: string[], headerLines: string[] = HEADER_LINES): string {
  return [...headerLines, ...dataLines].join('\n');
}

describe("epwParser", () => {
  describe("parseEPW -- cabecera de ubicación", () => {
    it("extrae ciudad, estado, país, lat, lon, timezone y elevación", () => {
      const epw = parseEPW(buildEPW([dataRow()]));
      expect(epw.location).toEqual({
        city: 'Bogota',
        state: 'Cundinamarca',
        country: 'COL',
        latitude: 4.71,
        longitude: -74.15,
        timezone: -5.0,
        elevation: 2547.0,
      });
    });

    it("usa 'Unknown' si falta el nombre de ciudad", () => {
      const badHeader = [',,,COL,IWEC,802220,4.71,-74.15,-5.0,2547.0', ...HEADER_LINES.slice(1)];
      const epw = parseEPW(buildEPW([dataRow()], badHeader));
      expect(epw.location.city).toBe('Unknown');
    });
  });

  describe("parseEPW -- registros horarios", () => {
    it("parsea correctamente todas las columnas usadas de una fila válida", () => {
      const epw = parseEPW(buildEPW([dataRow({
        dryBulb: 22.5, dewPoint: 16.2, rh: 70, pressure: 90000,
        ghi: 650, dni: 800, dhi: 120, windSpeed: 3.4, cloudCover: 4,
      })]));
      expect(epw.weatherData).toHaveLength(1);
      const w = epw.weatherData[0];
      expect(w).toMatchObject({
        year: 2020, month: 1, day: 1, hour: 1, minute: 0,
        temperature: 22.5, dewPoint: 16.2, relativeHumidity: 70,
        atmosphericPressure: 90000,
        globalHorizontalIrradiance: 650,
        directNormalIrradiance: 800,
        diffuseHorizontalIrradiance: 120,
        windSpeed: 3.4, cloudCover: 4,
      });
    });

    it("preserva 0°C y temperaturas negativas (no las trata como ausentes)", () => {
      const epw = parseEPW(buildEPW([dataRow({ dryBulb: 0 }), dataRow({ hour: 2, dryBulb: -8.3 })]));
      expect(epw.weatherData[0].temperature).toBe(0);
      expect(epw.weatherData[1].temperature).toBe(-8.3);
    });

    it("ignora filas con menos de 23 campos", () => {
      const shortRow = '2020,1,1,3,0,?,20,15,80,101325';
      const epw = parseEPW(buildEPW([dataRow(), shortRow]));
      expect(epw.weatherData).toHaveLength(1);
    });

    it("ignora filas con año fuera de rango o no numérico", () => {
      const badYearRow = dataRow({ year: 1899 });
      const futureYearRow = dataRow({ year: 2101 });
      const nonNumericRow = dataRow().replace(/^2020/, 'ABCD');
      const epw = parseEPW(buildEPW([dataRow(), badYearRow, futureYearRow, nonNumericRow]));
      expect(epw.weatherData).toHaveLength(1);
    });

    it("acumula múltiples registros en el orden del archivo", () => {
      const rows = [
        dataRow({ hour: 1, month: 1, day: 1 }),
        dataRow({ hour: 2, month: 1, day: 1 }),
        dataRow({ hour: 1, month: 6, day: 15 }),
      ];
      const epw = parseEPW(buildEPW(rows));
      expect(epw.weatherData).toHaveLength(3);
      expect(epw.weatherData.map(w => `${w.month}-${w.day}-${w.hour}`)).toEqual(['1-1-1', '1-1-2', '6-15-1']);
    });
  });

  describe("parseEPW -- detección de inicio de datos", () => {
    it("detecta el inicio de datos aunque el bloque de cabecera no tenga exactamente 8 líneas", () => {
      // Cabecera recortada a 5 líneas (no las 8 del formato estándar): el
      // parser debe encontrar igual la primera fila cuyo campo inicial es un
      // año de 4 dígitos, en vez de asumir ciegamente la línea 8.
      const headerRecortado = HEADER_LINES.slice(0, 5);
      const epw = parseEPW(buildEPW([dataRow()], headerRecortado));
      expect(epw.weatherData).toHaveLength(1);
      expect(epw.weatherData[0].month).toBe(1);
    });
  });

  describe("parseEPW -- metadata", () => {
    it("marca isTypicalMeteorologicalYear=true cuando el header/comentarios mencionan TMY", () => {
      const epw = parseEPW(buildEPW([dataRow()]));
      expect(epw.metadata?.isTypicalMeteorologicalYear).toBe(true);
    });

    it("marca isTypicalMeteorologicalYear=false cuando no hay ninguna mención de TMY", () => {
      const headerSinTMY = HEADER_LINES.map(l =>
        l.startsWith('COMMENTS 2') ? 'COMMENTS 2,Serie cronologica medida, no representativa' : l);
      const epw = parseEPW(buildEPW([dataRow()], headerSinTMY));
      expect(epw.metadata?.isTypicalMeteorologicalYear).toBe(false);
    });
  });

  describe("parseEPW -- entradas inválidas", () => {
    it("lanza un error si el archivo tiene menos de 3 líneas", () => {
      expect(() => parseEPW('solo,una,linea')).toThrow(/menos de 3 líneas/);
    });

    it("devuelve weatherData vacío (sin lanzar) si no hay ninguna fila de datos válida", () => {
      const epw = parseEPW(buildEPW(['linea,de,texto,sin,anio,valido']));
      expect(epw.weatherData).toHaveLength(0);
    });
  });
});
