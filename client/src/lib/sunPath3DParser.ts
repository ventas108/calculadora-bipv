/**
 * Parser para archivos JSON de Andrew Marsh Sun Path 3D
 * https://drajmarsh.bitbucket.io/sunpath3d.html
 *
 * El JSON de Sun Path 3D es un archivo de configuración/settings que contiene:
 * - Location: latitud, longitud, zona horaria, northOffset
 * - DateTime: fecha y hora específica del análisis
 * - SunPath: configuración del domo solar (radio, centro, opciones de visualización)
 * - Display: opciones de renderizado
 * - Model: configuración de sombras y mapa
 * - Animation: configuración de animación
 *
 * Los modelos 3D de sombra se cargan por separado (OBJ/STL/PLY) en la herramienta.
 * Este parser extrae los datos de ubicación y fecha/hora para aplicarlos a la calculadora.
 */

export interface SunPath3DLocation {
  latitude: number;
  longitude: number;
  timezone: number;
  northOffset: number;
}

export interface SunPath3DDateTime {
  clockTime: number;
  dayOfMonth: number;
  monthOfYear: number; // 0-indexed (0=Jan, 1=Feb, ...)
  year: number;
}

export interface SunPath3DSunPathConfig {
  showSunPos: boolean;
  showSunDirection: boolean;
  showSunAngles: boolean;
  showSunPath: boolean;
  showAnnualArea: boolean;
  showAnnualLines: boolean;
  showAxis: boolean;
  radius: number;
  solarChart: number;
  center: [number, number, number];
}

export interface SunPath3DJSON {
  Location: SunPath3DLocation;
  DateTime: SunPath3DDateTime;
  SunPath: SunPath3DSunPathConfig;
  Display?: {
    surfaceOpacity?: number;
    outlineOpacity?: number;
    surfaceShininess?: number;
    ambientFactor?: number;
  };
  Model?: {
    shadowsShow?: boolean;
    mapTiles?: string;
  };
  Animation?: {
    animateTime?: boolean;
    animateDate?: boolean;
    animateLatitude?: boolean;
    animateLongitude?: boolean;
    daylightOnly?: boolean;
    speed?: number;
  };
}

export interface SunPath3DParseResult {
  location: {
    latitude: number;
    longitude: number;
    timezone: number;
    northOffset: number;
  };
  dateTime: {
    year: number;
    month: number; // 1-indexed (1=Jan, 2=Feb, ...)
    day: number;
    hour: number;
    monthName: string;
  };
  sunPathConfig: {
    center: [number, number, number];
    radius: number;
    solarChart: number;
  };
  shadowsEnabled: boolean;
}

const MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

/**
 * Valida que un objeto sea un JSON válido de Sun Path 3D
 */
export function validateSunPath3DJSON(data: unknown): boolean {
  if (!data || typeof data !== 'object') return false;
  const obj = data as Record<string, unknown>;

  // Must have Location
  if (!obj.Location || typeof obj.Location !== 'object') return false;
  const loc = obj.Location as Record<string, unknown>;
  if (typeof loc.latitude !== 'number' || typeof loc.longitude !== 'number') return false;
  if (typeof loc.timezone !== 'number') return false;

  // Must have DateTime
  if (!obj.DateTime || typeof obj.DateTime !== 'object') return false;
  const dt = obj.DateTime as Record<string, unknown>;
  if (typeof dt.clockTime !== 'number' || typeof dt.dayOfMonth !== 'number') return false;
  if (typeof dt.monthOfYear !== 'number') return false;

  // Must have SunPath
  if (!obj.SunPath || typeof obj.SunPath !== 'object') return false;

  return true;
}

/**
 * Determina si un JSON es de Sun Path 3D (vs Site Designer)
 * Sun Path 3D tiene DateTime y SunPath pero NO tiene Blocks
 */
export function isSunPath3DJSON(data: unknown): boolean {
  if (!data || typeof data !== 'object') return false;
  const obj = data as Record<string, unknown>;
  return (
    'DateTime' in obj &&
    'SunPath' in obj &&
    !('Blocks' in obj)
  );
}

/**
 * Parsea un archivo JSON de Sun Path 3D
 */
export function parseSunPath3D(data: SunPath3DJSON): SunPath3DParseResult {
  const monthIndex = data.DateTime.monthOfYear; // 0-indexed in Sun Path 3D
  const month1Indexed = monthIndex + 1; // Convert to 1-indexed

  return {
    location: {
      latitude: data.Location.latitude,
      longitude: data.Location.longitude,
      timezone: data.Location.timezone,
      northOffset: data.Location.northOffset || 0,
    },
    dateTime: {
      year: data.DateTime.year,
      month: month1Indexed,
      day: data.DateTime.dayOfMonth,
      hour: data.DateTime.clockTime,
      monthName: MONTH_NAMES[monthIndex] || 'Ene',
    },
    sunPathConfig: {
      center: data.SunPath.center || [0, 0, 0],
      radius: data.SunPath.radius || 1,
      solarChart: data.SunPath.solarChart || 0,
    },
    shadowsEnabled: data.Model?.shadowsShow !== false,
  };
}

/**
 * Genera un resumen legible del archivo Sun Path 3D
 */
export function getSunPath3DSummary(data: SunPath3DJSON): {
  location: string;
  timezone: string;
  dateTime: string;
  center: string;
  shadowsEnabled: boolean;
} {
  const result = parseSunPath3D(data);
  return {
    location: `${result.location.latitude.toFixed(4)}°, ${result.location.longitude.toFixed(4)}°`,
    timezone: `UTC${result.location.timezone >= 0 ? '+' : ''}${result.location.timezone}`,
    dateTime: `${result.dateTime.monthName} ${result.dateTime.day}, ${result.dateTime.year} — ${result.dateTime.hour}:00h`,
    center: `(${result.sunPathConfig.center[0]}, ${result.sunPathConfig.center[1]}, ${result.sunPathConfig.center[2]})`,
    shadowsEnabled: result.shadowsEnabled,
  };
}
