import { EPWData, WeatherData } from './epwParser';

export type SolarCalculationScope = 'annual_8760' | 'critical_dates';
export type RigorCheckStatus = 'pass' | 'warning' | 'error';

export interface SolarRigorCheck {
  key: string;
  label: string;
  status: RigorCheckStatus;
  message: string;
}

export interface SolarRigorInput {
  epwData: EPWData | null;
  tilt?: number | null;
  azimuth?: number | null;
  northOffset?: number | null;
  scaleFactor?: number | null;
  facades?: Array<{
    name?: string;
    azimuthNormal?: number;
    tilt?: number;
    area?: number;
  }>;
  analysisPoints?: Array<{
    month?: number;
    day?: number;
    hour?: number;
    solarHeight?: number;
    solarAzimuth?: number;
  }>;
}

export interface SolarRigorReport {
  checks: SolarRigorCheck[];
  canCalculate: boolean;
  scope: SolarCalculationScope;
  scopeLabel: string;
  validHourlyYear: boolean;
  recordCount: number;
  errorCount: number;
  warningCount: number;
  datasetLabel: string;
}

const EXPECTED_MONTH_COUNTS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  .map(days => days * 24);

const isFiniteNumber = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value);

const pushCheck = (
  checks: SolarRigorCheck[],
  key: string,
  label: string,
  status: RigorCheckStatus,
  message: string,
) => checks.push({ key, label, status, message });

const validateWeatherUnits = (records: WeatherData[]): SolarRigorCheck => {
  const invalid = records.findIndex(record =>
    !isFiniteNumber(record.temperature) ||
    !isFiniteNumber(record.dewPoint) ||
    !isFiniteNumber(record.relativeHumidity) ||
    !isFiniteNumber(record.atmosphericPressure) ||
    !isFiniteNumber(record.directNormalIrradiance) ||
    !isFiniteNumber(record.diffuseHorizontalIrradiance) ||
    !isFiniteNumber(record.globalHorizontalIrradiance) ||
    !isFiniteNumber(record.windSpeed) ||
    !isFiniteNumber(record.cloudCover) ||
    record.relativeHumidity < 0 || record.relativeHumidity > 100 ||
    record.atmosphericPressure <= 0 ||
    record.directNormalIrradiance < 0 ||
    record.diffuseHorizontalIrradiance < 0 ||
    record.globalHorizontalIrradiance < 0 ||
    record.windSpeed < 0 ||
    record.cloudCover < 0 || record.cloudCover > 10,
  );

  return {
    key: 'units',
    label: 'Unidades y rangos',
    status: invalid >= 0 ? 'error' : 'pass',
    message: invalid >= 0
      ? `Registro ${invalid + 1} fuera de rango. EPW esperado: irradiancia Wh/m² por hora, temperatura °C, presión Pa, viento m/s y nubosidad 0–10.`
      : 'Irradiancia en Wh/m² por intervalo horario; temperatura °C; presión Pa; viento m/s; nubosidad 0–10.',
  };
};

const validateHourlyAlignment = (records: WeatherData[]): SolarRigorCheck => {
  const keys = new Set<string>();
  const monthCounts = Array(12).fill(0) as number[];
  let invalid = false;

  for (const record of records) {
    const key = `${record.month}-${record.day}-${record.hour}`;
    if (keys.has(key) || record.month < 1 || record.month > 12 ||
        record.day < 1 || record.day > EXPECTED_MONTH_COUNTS[record.month - 1] / 24 ||
        record.hour < 1 || record.hour > 24) {
      invalid = true;
    }
    keys.add(key);
    if (record.month >= 1 && record.month <= 12) monthCounts[record.month - 1]++;
  }

  const missingMonths = monthCounts.some((count, index) => count !== EXPECTED_MONTH_COUNTS[index]);
  return {
    key: 'hourly_alignment',
    label: 'Alineación horaria',
    status: invalid || missingMonths ? 'error' : 'pass',
    message: invalid || missingMonths
      ? `La serie tiene duplicados, horas inválidas o cobertura mensual incompleta (${monthCounts.join('/')} registros por mes).`
      : 'Una observación por cada hora 1–24, sin duplicados, con 8.760 posiciones mensuales completas.',
  };
};

export const dayOfYear = (month: number, day: number): number => {
  const daysBefore = EXPECTED_MONTH_COUNTS
    .slice(0, Math.max(0, month - 1))
    .reduce((sum, hours) => sum + hours / 24, 0);
  return daysBefore + day;
};

export function validateSolarRigor(input: SolarRigorInput): SolarRigorReport {
  const checks: SolarRigorCheck[] = [];
  const epw = input.epwData;
  const records = epw?.weatherData ?? [];

  if (!epw) {
    pushCheck(checks, 'epw', 'EPW', 'error', 'No hay un archivo EPW cargado.');
  } else {
    const has8760 = records.length === 8760;
    pushCheck(
      checks,
      'epw',
      'EPW',
      has8760 ? 'pass' : 'error',
      has8760
        ? 'EPW cargado con 8.760 registros horarios.'
        : `El EPW contiene ${records.length.toLocaleString()} registros; se requieren 8.760 para declarar cálculo anual.`,
    );

    const { location } = epw;
    const isTypicalYear = epw.metadata?.isTypicalMeteorologicalYear ?? false;
    pushCheck(
      checks,
      'period',
      'Periodo meteorológico',
      isTypicalYear ? 'pass' : 'warning',
      isTypicalYear
        ? 'TMY/TMYx: año meteorológico típico representativo, no una secuencia cronológica medida.'
        : 'El encabezado no identifica TMY/TMYx; confirmar si representa un año cronológico o típico.',
    );
    const validCoordinates =
      isFiniteNumber(location.latitude) && location.latitude >= -90 && location.latitude <= 90 &&
      isFiniteNumber(location.longitude) && location.longitude >= -180 && location.longitude <= 180;
    pushCheck(checks, 'coordinates', 'Coordenadas', validCoordinates ? 'pass' : 'error',
      validCoordinates
        ? `Lat ${location.latitude.toFixed(5)}°, Lon ${location.longitude.toFixed(5)}°.`
        : 'Latitud o longitud ausente/fuera de rango.');

    const validTimezone = isFiniteNumber(location.timezone) &&
      location.timezone >= -12 && location.timezone <= 14;
    pushCheck(checks, 'timezone', 'Zona horaria', validTimezone ? 'pass' : 'error',
      validTimezone ? `UTC${location.timezone >= 0 ? '+' : ''}${location.timezone}.` : 'Zona horaria fuera del rango IANA/EPW UTC−12…UTC+14.');

    const validElevation = isFiniteNumber(location.elevation) &&
      location.elevation >= -500 && location.elevation <= 9000;
    pushCheck(checks, 'elevation', 'Elevación', validElevation ? 'pass' : 'error',
      validElevation ? `${location.elevation.toFixed(1)} m s.n.m.` : 'Elevación ausente o físicamente inválida.');

    checks.push(validateWeatherUnits(records));
    if (records.length > 0) checks.push(validateHourlyAlignment(records));
  }

  const northOffset = input.northOffset ?? 0;
  const validNorth = isFiniteNumber(northOffset) && northOffset >= -180 && northOffset <= 180;
  pushCheck(checks, 'north', 'Norte', validNorth ? 'pass' : 'error',
    validNorth ? `Desfase de norte ${northOffset.toFixed(1)}°.` : 'El desfase de norte debe estar entre −180° y 180°.');

  const scaleFactor = input.scaleFactor ?? 1;
  const validScale = isFiniteNumber(scaleFactor) && scaleFactor > 0 && scaleFactor <= 1000;
  pushCheck(checks, 'scale', 'Escala', validScale ? 'pass' : 'error',
    validScale ? `Factor de escala ${scaleFactor}.` : 'El factor de escala debe ser positivo y razonable (por ejemplo 0.001 para mm→m).');

  if (input.tilt === null || input.tilt === undefined) {
    pushCheck(checks, 'tilt', 'Inclinación', 'warning', 'No se ha declarado inclinación de superficie.');
  } else {
    const validTilt = isFiniteNumber(input.tilt) && input.tilt >= 0 && input.tilt <= 90;
    pushCheck(checks, 'tilt', 'Inclinación', validTilt ? 'pass' : 'error',
      validTilt ? `${input.tilt.toFixed(1)}°.` : 'La inclinación debe estar entre 0° y 90°.');
  }

  if (input.azimuth === null || input.azimuth === undefined) {
    pushCheck(checks, 'azimuth', 'Acimut', 'warning', 'No se ha declarado acimut de superficie.');
  } else {
    const validAzimuth = isFiniteNumber(input.azimuth) && input.azimuth >= -180 && input.azimuth <= 180;
    pushCheck(checks, 'azimuth', 'Acimut', validAzimuth ? 'pass' : 'error',
      validAzimuth ? `${input.azimuth.toFixed(1)}° (0° = Sur).` : 'El acimut debe estar entre −180° y 180°.');
  }

  if (!input.facades || input.facades.length === 0) {
    pushCheck(checks, 'facades', 'Fachadas', 'warning', 'No hay fachadas 3D declaradas; se usa la orientación manual.');
  } else {
    const invalidFacade = input.facades.find(facade =>
      !facade.name ||
      !isFiniteNumber(facade.azimuthNormal) || facade.azimuthNormal < -180 || facade.azimuthNormal > 180 ||
      !isFiniteNumber(facade.tilt) || facade.tilt < 0 || facade.tilt > 90 ||
      !isFiniteNumber(facade.area) || facade.area <= 0,
    );
    pushCheck(checks, 'facades', 'Fachadas',
      invalidFacade ? 'error' : 'pass',
      invalidFacade
        ? 'Una fachada tiene nombre, área, inclinación o acimut inválido.'
        : `${input.facades.length} fachada(s) con área, inclinación y acimut válidos.`,
    );
  }

  if (!input.analysisPoints || input.analysisPoints.length === 0) {
    pushCheck(checks, 'analysis_points', 'Puntos de análisis', 'warning', 'No hay puntos críticos o puntos 3D declarados.');
  } else {
    const invalidPoint = input.analysisPoints.find(point =>
      !isFiniteNumber(point.month) || point.month < 1 || point.month > 12 ||
      !isFiniteNumber(point.day) || point.day < 1 || point.day > 31 ||
      !isFiniteNumber(point.hour) || point.hour < 0 || point.hour >= 24 ||
      (point.solarHeight !== undefined && !isFiniteNumber(point.solarHeight)) ||
      (point.solarAzimuth !== undefined && !isFiniteNumber(point.solarAzimuth)),
    );
    pushCheck(checks, 'analysis_points', 'Puntos de análisis',
      invalidPoint ? 'error' : 'pass',
      invalidPoint ? 'Existe un punto con fecha, hora o ángulos inválidos.' : `${input.analysisPoints.length} punto(s) de análisis válidos.`,
    );
  }

  const epwChecksPass = checks
    .filter(check => ['epw', 'coordinates', 'timezone', 'elevation', 'units', 'hourly_alignment'].includes(check.key))
    .every(check => check.status === 'pass');
  const errorCount = checks.filter(check => check.status === 'error').length;
  const warningCount = checks.filter(check => check.status === 'warning').length;
  const validHourlyYear = epwChecksPass && records.length === 8760;

  return {
    checks,
    canCalculate: errorCount === 0,
    scope: validHourlyYear ? 'annual_8760' : 'critical_dates',
    scopeLabel: validHourlyYear
      ? 'Cálculo anual de 8.760 horas'
      : 'Cálculo representativo de fechas y horas críticas',
    validHourlyYear,
    recordCount: records.length,
    errorCount,
    warningCount,
    datasetLabel: epw?.metadata?.isTypicalMeteorologicalYear
      ? 'TMY/TMYx representativo'
      : 'Serie meteorológica cargada',
  };
}