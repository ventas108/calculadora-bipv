/**
 * Solar Position Algorithm (SPA) simplificado
 * Calcula la posición del sol (altura y azimut) para una ubicación y fecha/hora dadas.
 * Basado en las ecuaciones astronómicas estándar de Meeus (1991) y NOAA Solar Calculator.
 * Precisión: ±0.5° para altitud y azimut (suficiente para análisis de sombreado).
 */

import { normalizeMonthToAbbr } from './monthHelper';

export interface SolarPosition {
  altitude: number;   // Altura solar en grados (0° = horizonte, 90° = cénit)
  azimuth: number;    // Azimut solar en grados (0° = Sur, negativo = Este, positivo = Oeste)
  zenith: number;     // Ángulo cenital en grados (90° - altitude)
  hourAngle: number;  // Ángulo horario en grados
  declination: number; // Declinación solar en grados
  sunrise: number;    // Hora de salida del sol (hora decimal)
  sunset: number;     // Hora de puesta del sol (hora decimal)
  daylightHours: number; // Horas de luz solar
}

const DEG2RAD = Math.PI / 180;
const RAD2DEG = 180 / Math.PI;

/**
 * Calcula el día juliano a partir de año, mes, día
 */
function julianDay(year: number, month: number, day: number): number {
  if (month <= 2) {
    year -= 1;
    month += 12;
  }
  const A = Math.floor(year / 100);
  const B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (year + 4716)) + Math.floor(30.6001 * (month + 1)) + day + B - 1524.5;
}

/**
 * Calcula el siglo juliano
 */
function julianCentury(jd: number): number {
  return (jd - 2451545.0) / 36525.0;
}

/**
 * Longitud media geométrica del sol (grados)
 */
function sunGeomMeanLon(T: number): number {
  let L0 = 280.46646 + T * (36000.76983 + 0.0003032 * T);
  while (L0 > 360) L0 -= 360;
  while (L0 < 0) L0 += 360;
  return L0;
}

/**
 * Anomalía media geométrica del sol (grados)
 */
function sunGeomMeanAnomaly(T: number): number {
  return 357.52911 + T * (35999.05029 - 0.0001537 * T);
}

/**
 * Excentricidad de la órbita terrestre
 */
function earthOrbitEccentricity(T: number): number {
  return 0.016708634 - T * (0.000042037 + 0.0000001267 * T);
}

/**
 * Ecuación del centro del sol (grados)
 */
function sunEquationOfCenter(T: number): number {
  const M = sunGeomMeanAnomaly(T);
  const Mrad = M * DEG2RAD;
  const sinM = Math.sin(Mrad);
  const sin2M = Math.sin(2 * Mrad);
  const sin3M = Math.sin(3 * Mrad);
  return sinM * (1.914602 - T * (0.004817 + 0.000014 * T))
       + sin2M * (0.019993 - 0.000101 * T)
       + sin3M * 0.000289;
}

/**
 * Longitud verdadera del sol (grados)
 */
function sunTrueLon(T: number): number {
  return sunGeomMeanLon(T) + sunEquationOfCenter(T);
}

/**
 * Longitud aparente del sol (grados)
 */
function sunApparentLon(T: number): number {
  const omega = 125.04 - 1934.136 * T;
  return sunTrueLon(T) - 0.00569 - 0.00478 * Math.sin(omega * DEG2RAD);
}

/**
 * Oblicuidad media de la eclíptica (grados)
 */
function meanObliquityOfEcliptic(T: number): number {
  const seconds = 21.448 - T * (46.8150 + T * (0.00059 - T * 0.001813));
  return 23 + (26 + seconds / 60) / 60;
}

/**
 * Oblicuidad corregida (grados)
 */
function obliquityCorrection(T: number): number {
  const omega = 125.04 - 1934.136 * T;
  return meanObliquityOfEcliptic(T) + 0.00256 * Math.cos(omega * DEG2RAD);
}

/**
 * Declinación solar (grados)
 */
function sunDeclination(T: number): number {
  const e = obliquityCorrection(T) * DEG2RAD;
  const lambda = sunApparentLon(T) * DEG2RAD;
  return Math.asin(Math.sin(e) * Math.sin(lambda)) * RAD2DEG;
}

/**
 * Ecuación del tiempo (minutos)
 */
function equationOfTime(T: number): number {
  const epsilon = obliquityCorrection(T) * DEG2RAD;
  const L0 = sunGeomMeanLon(T) * DEG2RAD;
  const e = earthOrbitEccentricity(T);
  const M = sunGeomMeanAnomaly(T) * DEG2RAD;

  const y = Math.tan(epsilon / 2) ** 2;

  const sin2L0 = Math.sin(2 * L0);
  const sinM = Math.sin(M);
  const cos2L0 = Math.cos(2 * L0);
  const sin4L0 = Math.sin(4 * L0);
  const sin2M = Math.sin(2 * M);

  const Etime = y * sin2L0
              - 2 * e * sinM
              + 4 * e * y * sinM * cos2L0
              - 0.5 * y * y * sin4L0
              - 1.25 * e * e * sin2M;

  return 4 * Etime * RAD2DEG; // en minutos
}

/**
 * Ángulo horario de salida del sol (grados)
 */
function sunriseHourAngle(lat: number, decl: number): number {
  const latRad = lat * DEG2RAD;
  const declRad = decl * DEG2RAD;
  const cosHA = (Math.cos(90.833 * DEG2RAD) / (Math.cos(latRad) * Math.cos(declRad)))
              - Math.tan(latRad) * Math.tan(declRad);
  // Clamp para latitudes extremas (sol circumpolar)
  if (cosHA > 1) return 0;   // Sol nunca sale
  if (cosHA < -1) return 180; // Sol nunca se pone
  return Math.acos(cosHA) * RAD2DEG;
}

/**
 * Convierte mes (nombre corto español) a número
 */
const MONTH_MAP: Record<string, number> = {
  'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6,
  'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12,
};

/**
 * Calcula la posición solar para una ubicación y fecha/hora dadas.
 * 
 * @param latitude  Latitud en grados (positivo = Norte)
 * @param longitude Longitud en grados (positivo = Este, negativo = Oeste)
 * @param timezone  Zona horaria en horas respecto a UTC (ej: -5 para Colombia)
 * @param month     Mes (nombre corto: 'Ene', 'Feb', etc. o número 1-12)
 * @param day       Día del mes (1-31)
 * @param hour      Hora local (0-23, puede ser decimal, ej: 9.5 = 9:30)
 * @param year      Año (por defecto 2024 - año típico TMY)
 */
export function calculateSolarPosition(
  latitude: number,
  longitude: number,
  timezone: number,
  month: string | number,
  day: number,
  hour: number,
  year: number = 2024,
): SolarPosition {
  // Convertir mes si es string normalizándolo primero
  const normalizedMonth = typeof month === 'string' ? normalizeMonthToAbbr(month) : month;
  const monthNum = typeof normalizedMonth === 'string' ? (MONTH_MAP[normalizedMonth] || 1) : normalizedMonth;

  // Día juliano
  const JD = julianDay(year, monthNum, day) + (hour - timezone) / 24;
  const T = julianCentury(JD);

  // Declinación solar
  const decl = sunDeclination(T);
  const declRad = decl * DEG2RAD;

  // Ecuación del tiempo
  const eqTime = equationOfTime(T);

  // Tiempo solar verdadero (minutos)
  const trueSolarTime = ((hour * 60) + eqTime + (4 * longitude) - (60 * timezone)) % 1440;

  // Ángulo horario (grados)
  let hourAngle: number;
  if (trueSolarTime / 4 < 0) {
    hourAngle = trueSolarTime / 4 + 180;
  } else {
    hourAngle = trueSolarTime / 4 - 180;
  }

  const latRad = latitude * DEG2RAD;
  const haRad = hourAngle * DEG2RAD;

  // Ángulo cenital solar
  const cosZenith = Math.sin(latRad) * Math.sin(declRad)
                   + Math.cos(latRad) * Math.cos(declRad) * Math.cos(haRad);
  const zenith = Math.acos(Math.max(-1, Math.min(1, cosZenith))) * RAD2DEG;
  const altitude = 90 - zenith;

  // Azimut solar (convención: 0° = Sur, negativo = Este, positivo = Oeste)
  let azimuth: number;
  if (hourAngle > 0) {
    // Tarde: azimut positivo (Oeste)
    azimuth = (Math.acos(
      ((Math.sin(latRad) * Math.cos(zenith * DEG2RAD)) - Math.sin(declRad))
      / (Math.cos(latRad) * Math.sin(zenith * DEG2RAD))
    ) * RAD2DEG + 180) % 360 - 180;
  } else {
    // Mañana: azimut negativo (Este)
    azimuth = (540 - Math.acos(
      ((Math.sin(latRad) * Math.cos(zenith * DEG2RAD)) - Math.sin(declRad))
      / (Math.cos(latRad) * Math.sin(zenith * DEG2RAD))
    ) * RAD2DEG) % 360 - 180;
  }

  // Corrección de refracción atmosférica para altitudes bajas
  let altitudeCorrected = altitude;
  if (altitude > -0.575) {
    const tanAlt = Math.tan(altitude * DEG2RAD);
    let refractionCorrection: number;
    if (altitude > 85) {
      refractionCorrection = 0;
    } else if (altitude > 5) {
      refractionCorrection = 58.1 / tanAlt - 0.07 / (tanAlt ** 3) + 0.000086 / (tanAlt ** 5);
    } else if (altitude > -0.575) {
      refractionCorrection = 1735 + altitude * (-518.2 + altitude * (103.4 + altitude * (-12.79 + altitude * 0.711)));
    } else {
      refractionCorrection = 0;
    }
    altitudeCorrected = altitude + refractionCorrection / 3600;
  }

  // Salida y puesta del sol
  const haRise = sunriseHourAngle(latitude, decl);
  const solarNoon = (720 - 4 * longitude - eqTime + timezone * 60) / 1440;
  const sunrise = (solarNoon - haRise * 4 / 1440) * 24;
  const sunset = (solarNoon + haRise * 4 / 1440) * 24;
  const daylightHours = haRise * 8 / 60;

  return {
    altitude: Math.round(altitudeCorrected * 100) / 100,
    azimuth: Math.round(azimuth * 100) / 100,
    zenith: Math.round(zenith * 100) / 100,
    hourAngle: Math.round(hourAngle * 100) / 100,
    declination: Math.round(decl * 100) / 100,
    sunrise: Math.round(sunrise * 100) / 100,
    sunset: Math.round(sunset * 100) / 100,
    daylightHours: Math.round(daylightHours * 100) / 100,
  };
}

/**
 * Genera posiciones solares para cada hora del día en una fecha y ubicación dadas.
 * Útil para generar diagramas de trayectoria solar.
 */
export function getDailySolarPath(
  latitude: number,
  longitude: number,
  timezone: number,
  month: string | number,
  day: number,
  year: number = 2024,
): SolarPosition[] {
  const positions: SolarPosition[] = [];
  for (let h = 0; h < 24; h++) {
    const pos = calculateSolarPosition(latitude, longitude, timezone, month, day, h, year);
    if (pos.altitude > 0) {
      positions.push(pos);
    }
  }
  return positions;
}
