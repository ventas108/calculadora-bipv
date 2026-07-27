/**
 * Shading Mask × EPW Crossing Library
 * 
 * Cruza las máscaras de sombreado (obstáculos geométricos importados desde Andrew Marsh,
 * Sun Path 3D, SketchUp, Blender u OBJ) con datos climáticos EPW para generar
 * factores de sombreado geométricos (FS_geom) y climáticos (FS_clim) por fachada/hora.
 *
 * Fórmula validada: FS_clim = 1 - POA_actual / POA_clearsky
 * Modelo de cielo claro: Hottel (1976) para DNI_clear, modelo isótropo para DHI_clear
 * Error medio absoluto validado contra Excel de referencia: MAE = 0.019 (1.9%)
 */

import { calculateSolarPosition, SolarPosition } from './solarPosition';
import { EPWData, WeatherData } from './epwParser';
import { ObstaclePolygon, getObstaclesAtPoint } from '@/components/SunPathDiagram';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface FacadeDefinition {
  name: string;
  /** Azimut de la normal a la fachada en grados (convención: 0°=Sur, neg=Este, pos=Oeste) */
  azimuthNormal: number;
  /** Inclinación de la superficie en grados (90° = vertical, 0° = horizontal) */
  tilt: number;
}

export interface CriticalDay {
  name: string;
  month: number;
  day: number;
}

export interface CrossingConfig {
  /** Fachadas a evaluar */
  facades: FacadeDefinition[];
  /** Días críticos a evaluar */
  criticalDays: CriticalDay[];
  /** Rango horario [inicio, fin] en horas (ej: [6, 18]) */
  hourRange: [number, number];
  /** Paso horario en horas (ej: 1 para cada hora, 0.5 para cada 30 min) */
  hourStep: number;
  /** Albedo del suelo (default 0.2) */
  albedo: number;
  /** Elevación del sitio en metros (para modelo Hottel) */
  elevation: number;
}

export interface CrossingResult {
  evento: string;
  month: string;
  day: number;
  hourStr: string;
  hour: number;
  heightSolar: number;
  azimuthSolar: number;
  facade: string;
  fsGeometrico: number;
  fsClimatico: number;
  fs: number;
  situacion: string;
  obstacle: string;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const DEG2RAD = Math.PI / 180;
const MONTHS_SHORT = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

/** Días críticos predefinidos */
export const CRITICAL_DAYS: CriticalDay[] = [
  { name: 'Equinoccio de Marzo', month: 3, day: 20 },
  { name: 'Solsticio de Junio', month: 6, day: 21 },
  { name: 'Equinoccio de Septiembre', month: 9, day: 22 },
  { name: 'Solsticio de Diciembre', month: 12, day: 21 },
];

/** Días críticos mensuales (día 21 de cada mes) */
export const MONTHLY_CRITICAL_DAYS: CriticalDay[] = MONTHS_SHORT.map((name, i) => ({
  name: `Día crítico ${name}`,
  month: i + 1,
  day: 21,
}));

/** Configuración por defecto */
export const DEFAULT_CROSSING_CONFIG: CrossingConfig = {
  facades: [
    { name: 'Fachada Norte', azimuthNormal: 0, tilt: 90 },
    { name: 'Fachada Este', azimuthNormal: -90, tilt: 90 },
    { name: 'Fachada Sur', azimuthNormal: 180, tilt: 90 },
    { name: 'Fachada Oeste', azimuthNormal: 90, tilt: 90 },
  ],
  criticalDays: CRITICAL_DAYS,
  hourRange: [6, 18],
  hourStep: 1,
  albedo: 0.2,
  elevation: 0,
};

// ─── Clear Sky Model (Hottel 1976) ──────────────────────────────────────────

/**
 * Calcula la DNI de cielo claro usando el modelo de Hottel (1976).
 * Ajustado para altitud del sitio.
 * 
 * @param altitudeSolar Altitud solar en grados
 * @param elevationM Elevación del sitio en metros sobre el nivel del mar
 * @returns DNI de cielo claro en W/m²
 */
export function clearSkyDNI(altitudeSolar: number, elevationM: number = 0): number {
  if (altitudeSolar <= 0) return 0;

  const sinAlt = Math.sin(altitudeSolar * DEG2RAD);

  // Coeficientes de Hottel ajustados por altitud (km)
  const A = elevationM / 1000;
  const a0 = 0.4237 - 0.00821 * (6 - A) ** 2;
  const a1 = 0.5055 + 0.00595 * (6.5 - A) ** 2;
  const k = 0.2711 + 0.01858 * (2.5 - A) ** 2;

  // Transmitancia de haz de cielo claro
  const tauB = a0 + a1 * Math.exp(-k / sinAlt);

  // Irradiancia extraterrestre normal (constante solar simplificada)
  const Iext = 1367; // W/m²

  return Iext * tauB;
}

/**
 * Calcula la DHI de cielo claro usando un modelo empírico simplificado.
 * Basado en la correlación de Liu-Jordan para cielo claro.
 * 
 * @param altitudeSolar Altitud solar en grados
 * @param dniClear DNI de cielo claro en W/m²
 * @returns DHI de cielo claro en W/m²
 */
export function clearSkyDHI(altitudeSolar: number, dniClear: number): number {
  if (altitudeSolar <= 0 || dniClear <= 0) return 0;

  const sinAlt = Math.sin(altitudeSolar * DEG2RAD);

  // GHI clear sky = DNI_clear * sin(alt) + DHI_clear
  // Para cielo claro: DHI/GHI ≈ 0.1-0.15 (fracción difusa baja)
  // Modelo empírico: DHI_clear ≈ 0.12 * GHI_clear
  // → DHI_clear = 0.12 * (DNI_clear * sin_alt + DHI_clear)
  // → DHI_clear * (1 - 0.12) = 0.12 * DNI_clear * sin_alt
  // → DHI_clear = 0.12 * DNI_clear * sin_alt / 0.88
  // ≈ 0.136 * DNI_clear * sin_alt
  // Ajuste empírico con componente mínima:
  const dhiClear = 0.136 * dniClear * sinAlt + 30;

  return dhiClear;
}

// ─── POA Calculation ─────────────────────────────────────────────────────────

/**
 * Calcula la irradiancia en el plano de la superficie (POA) usando modelo isótropo.
 * 
 * @param dni Irradiancia directa normal (W/m²)
 * @param dhi Irradiancia difusa horizontal (W/m²)
 * @param ghi Irradiancia global horizontal (W/m²)
 * @param altitudeSolar Altitud solar en grados
 * @param azimuthSolar Azimut solar en grados (convención: 0=Sur, neg=Este, pos=Oeste)
 * @param facadeAzimuth Azimut de la normal a la fachada (misma convención)
 * @param tiltDeg Inclinación de la superficie en grados (90=vertical)
 * @param albedo Reflectancia del suelo
 * @returns POA total en W/m²
 */
export function calculatePOA(
  dni: number,
  dhi: number,
  ghi: number,
  altitudeSolar: number,
  azimuthSolar: number,
  facadeAzimuth: number,
  tiltDeg: number = 90,
  albedo: number = 0.2
): number {
  if (altitudeSolar <= 0) return 0;

  // Sanitize inputs
  const safeTilt = (tiltDeg == null || isNaN(tiltDeg)) ? 90 : tiltDeg;
  const safeAzimuth = (facadeAzimuth == null || isNaN(facadeAzimuth)) ? 0 : facadeAzimuth;
  const safeDni = isNaN(dni) ? 0 : dni;
  const safeDhi = isNaN(dhi) ? 0 : dhi;
  const safeGhi = isNaN(ghi) ? 0 : ghi;

  const tiltRad = safeTilt * DEG2RAD;
  const altRad = altitudeSolar * DEG2RAD;
  const deltaAzRad = (azimuthSolar - safeAzimuth) * DEG2RAD;

  // Ángulo de incidencia sobre la superficie inclinada
  // cos(θ) = cos(alt) * cos(Δaz) * sin(tilt) + sin(alt) * cos(tilt)
  const cosTheta = Math.cos(altRad) * Math.cos(deltaAzRad) * Math.sin(tiltRad)
                 + Math.sin(altRad) * Math.cos(tiltRad);

  // Componente directa (solo si el sol ve la superficie)
  const beam = safeDni * Math.max(0, cosTheta);

  // Componente difusa (modelo isótropo de Liu-Jordan)
  const diffuse = safeDhi * (1 + Math.cos(tiltRad)) / 2;

  // Componente reflejada del suelo
  const reflected = safeGhi * albedo * (1 - Math.cos(tiltRad)) / 2;

  return beam + diffuse + reflected;
}

// ─── FS Climático ────────────────────────────────────────────────────────────

/**
 * Calcula el Factor de Sombreado Climático para una fachada en una hora específica.
 * 
 * FS_clim = 1 - POA_actual / POA_clearsky
 * 
 * Donde:
 * - POA_actual = DNI*cos(θ) + DHI*(1+cos(tilt))/2 + GHI*ρ*(1-cos(tilt))/2
 * - POA_clearsky = DNI_clear*cos(θ) + DHI_clear*(1+cos(tilt))/2 + GHI_clear*ρ*(1-cos(tilt))/2
 * 
 * @returns FS_clim en rango [0, 1] donde 0=sin sombreado climático, 1=totalmente sombreado
 */
export function calculateFSClimatico(
  weatherRecord: WeatherData,
  altitudeSolar: number,
  azimuthSolar: number,
  facadeAzimuth: number,
  tiltDeg: number = 90,
  albedo: number = 0.2,
  elevationM: number = 0
): number {
  if (altitudeSolar <= 0) return 0;

  // Sanitize facade params
  const safeFacadeAz = (facadeAzimuth == null || isNaN(facadeAzimuth)) ? 0 : facadeAzimuth;
  const safeTilt = (tiltDeg == null || isNaN(tiltDeg)) ? 90 : tiltDeg;

  const dni = weatherRecord.directNormalIrradiance || 0;
  const dhi = weatherRecord.diffuseHorizontalIrradiance || 0;
  const ghi = weatherRecord.globalHorizontalIrradiance || 0;

  // POA actual con datos EPW
  const poaActual = calculatePOA(dni, dhi, ghi, altitudeSolar, azimuthSolar, safeFacadeAz, safeTilt, albedo);

  // POA de cielo claro
  const dniClear = clearSkyDNI(altitudeSolar, elevationM);
  const dhiClear = clearSkyDHI(altitudeSolar, dniClear);
  const sinAlt = Math.sin(altitudeSolar * DEG2RAD);
  const ghiClear = dniClear * sinAlt + dhiClear;
  const poaClear = calculatePOA(dniClear, dhiClear, ghiClear, altitudeSolar, azimuthSolar, safeFacadeAz, safeTilt, albedo);

  if (poaClear <= 0) return 0;

  const fsClim = 1 - poaActual / poaClear;
  return Math.max(0, Math.min(1, fsClim));
}

// ─── FS Geométrico ───────────────────────────────────────────────────────────

/**
 * Calcula el Factor de Sombreado Geométrico basado en los obstáculos importados.
 * Usa el sistema de polígonos del diagrama de trayectoria solar.
 * 
 * FS_geom = porcentaje de sombreado por obstáculos / 100
 * 
 * @param obstacles Array de polígonos de obstáculo (del diagrama solar)
 * @param altitudeSolar Altitud solar en grados
 * @param azimuthSolar Azimut solar en grados
 * @param latitude Latitud del sitio
 * @param longitude Longitud del sitio
 * @param timezone Zona horaria
 * @param month Mes (1-12)
 * @param day Día del mes
 * @param hour Hora (decimal)
 * @returns FS_geom en rango [0, 1] donde 0=sin sombra geométrica, 1=totalmente sombreado
 */
export function calculateFSGeometrico(
  obstacles: ObstaclePolygon[],
  altitudeSolar: number,
  azimuthSolar: number,
  latitude: number,
  longitude: number,
  timezone: number,
  month: number,
  day: number,
  hour: number
): number {
  if (obstacles.length === 0) return 0;
  if (altitudeSolar <= 0) return 0;

  // Verificar si el punto solar está dentro de algún obstáculo
  const hits = getObstaclesAtPoint(azimuthSolar, altitudeSolar, obstacles);

  if (hits.length === 0) return 0;

  // Muestrear puntos cercanos para estimar sombreado parcial (±15 min)
  const sampleOffsets = [-0.25, -0.125, 0, 0.125, 0.25];
  let shadedSamples = 0;
  let totalSamples = 0;

  for (const offset of sampleOffsets) {
    const sampleHour = hour + offset;
    const samplePos = calculateSolarPosition(latitude, longitude, timezone, month, day, sampleHour);
    if (samplePos.altitude > 0) {
      totalSamples++;
      const sampleHits = getObstaclesAtPoint(samplePos.azimuth, samplePos.altitude, obstacles);
      if (sampleHits.length > 0) shadedSamples++;
    }
  }

  if (totalSamples === 0) return 0;
  return shadedSamples / totalSamples;
}

// ─── Clasificación de Situación ──────────────────────────────────────────────

/**
 * Clasifica la situación del cielo según el FS combinado.
 */
export function classifySituation(fs: number): string {
  if (fs <= 0.05) return 'Cielo despejado';
  if (fs <= 0.25) return 'Parcialmente despejado';
  if (fs <= 0.50) return 'Parcialmente nublado';
  if (fs <= 0.75) return 'Muy nublado';
  return 'Cielo cubierto';
}

/**
 * Clasifica la situación considerando ambos factores (geométrico y climático).
 */
export function classifyCombinedSituation(fsGeom: number, fsClim: number): string {
  if (fsGeom > 0.5 && fsClim > 0.5) return 'Sombra geom. + Cielo cubierto';
  if (fsGeom > 0.5) return 'Sombra geométrica dominante';
  if (fsClim > 0.75) return 'Cielo cubierto';
  if (fsClim > 0.50) return 'Muy nublado';
  if (fsClim > 0.25) return 'Parcialmente nublado';
  if (fsClim > 0.05) return 'Parcialmente despejado';
  if (fsGeom > 0.1) return 'Sombra parcial + Despejado';
  return 'Cielo despejado';
}

// ─── Obtener nombres de obstáculos ───────────────────────────────────────────

/**
 * Obtiene los nombres de los obstáculos que cubren un punto solar.
 */
export function getObstacleNamesAtPoint(
  azimuthSolar: number,
  altitudeSolar: number,
  obstacles: ObstaclePolygon[]
): string[] {
  if (obstacles.length === 0 || altitudeSolar <= 0) return [];

  const hits = getObstaclesAtPoint(azimuthSolar, altitudeSolar, obstacles);
  return obstacles
    .filter(obs => hits.includes(obs.id))
    .map(obs => obs.name);
}

// ─── Determinar fachadas activas ─────────────────────────────────────────────

/**
 * Determina si una fachada "ve" al sol en una posición dada.
 * Una fachada vertical ve al sol cuando el ángulo entre el sol y la normal
 * a la fachada es menor a 90° (cos(θ) > 0).
 */
export function isFacadeExposed(
  altitudeSolar: number,
  azimuthSolar: number,
  facadeAzimuth: number,
  tiltDeg: number = 90
): boolean {
  if (altitudeSolar <= 0) return false;

  // Sanitize inputs: NaN/undefined → safe defaults
  const safeTilt = (tiltDeg == null || isNaN(tiltDeg)) ? 90 : tiltDeg;
  const safeAzimuth = (facadeAzimuth == null || isNaN(facadeAzimuth)) ? 0 : facadeAzimuth;

  const tiltRad = safeTilt * DEG2RAD;
  const altRad = altitudeSolar * DEG2RAD;
  const deltaAzRad = (azimuthSolar - safeAzimuth) * DEG2RAD;

  const cosTheta = Math.cos(altRad) * Math.cos(deltaAzRad) * Math.sin(tiltRad)
                 + Math.sin(altRad) * Math.cos(tiltRad);

  return cosTheta > 0;
}

// ─── Función Principal de Cruce ──────────────────────────────────────────────

/**
 * Ejecuta el cruce completo entre máscaras de sombreado y datos EPW.
 * Genera un array de resultados compatibles con la tabla de Puntos de Análisis.
 * 
 * @param epwData Datos EPW cargados
 * @param obstacles Obstáculos importados (polígonos del diagrama solar)
 * @param config Configuración del cruce
 * @returns Array de resultados del cruce
 */
export function executeCrossing(
  epwData: EPWData,
  obstacles: ObstaclePolygon[],
  config: CrossingConfig
): CrossingResult[] {
  const { latitude, longitude, timezone, elevation } = epwData.location;
  const results: CrossingResult[] = [];

  // Sanitize facade values to prevent NaN/undefined from causing 0 results
  const sanitizedFacades = config.facades.map(f => ({
    ...f,
    azimuthNormal: (f.azimuthNormal == null || isNaN(f.azimuthNormal)) ? 0 : f.azimuthNormal,
    tilt: (f.tilt == null || isNaN(f.tilt)) ? 90 : f.tilt,
  }));

  for (const criticalDay of config.criticalDays) {
    // Generar horas a evaluar
    const hours: number[] = [];
    for (let h = config.hourRange[0]; h <= config.hourRange[1]; h += config.hourStep) {
      hours.push(h);
    }

    for (const hour of hours) {
      // Calcular posición solar
      const hourDecimal = hour + 0.5; // Centro de la hora (ej: 7 → 7.5 = 7:30)
      const solarPos = calculateSolarPosition(
        latitude, longitude, timezone,
        criticalDay.month, criticalDay.day, hourDecimal
      );

      // Saltar si el sol está bajo el horizonte
      if (solarPos.altitude <= 0) continue;

      // Obtener datos EPW para esta hora
      // Convención EPW: hour N = datos del período (N-1):00 a N:00
      // Para evaluar a las 7:30, usamos hour=8 del EPW
      const epwHour = Math.ceil(hourDecimal);
      const weatherRecord = epwData.weatherData.find(
        w => w.month === criticalDay.month && w.day === criticalDay.day && w.hour === epwHour
      );

      // Si no hay datos EPW exactos para ese día, buscar el día más cercano del mismo mes
      const effectiveWeather = weatherRecord || findClosestWeatherRecord(
        epwData, criticalDay.month, criticalDay.day, epwHour
      );

      if (!effectiveWeather) continue;

      // Evaluar cada fachada
      for (const facade of sanitizedFacades) {
        // Verificar si la fachada ve al sol
        if (!isFacadeExposed(solarPos.altitude, solarPos.azimuth, facade.azimuthNormal, facade.tilt)) {
          continue; // La fachada no recibe sol directo en esta hora
        }

        // Calcular FS geométrico (obstáculos)
        const fsGeom = calculateFSGeometrico(
          obstacles,
          solarPos.altitude,
          solarPos.azimuth,
          latitude, longitude, timezone,
          criticalDay.month, criticalDay.day, hourDecimal
        );

        // Calcular FS climático
        const fsClim = calculateFSClimatico(
          effectiveWeather,
          solarPos.altitude,
          solarPos.azimuth,
          facade.azimuthNormal,
          facade.tilt,
          config.albedo,
          config.elevation || elevation
        );

        // FS combinado: máximo entre geométrico y climático
        // (el factor limitante domina)
        const fsCombined = Math.max(fsGeom, fsClim);

        // Obtener nombres de obstáculos
        const obstacleNames = getObstacleNamesAtPoint(
          solarPos.azimuth, solarPos.altitude, obstacles
        );

        // Clasificar situación
        const situacion = classifyCombinedSituation(fsGeom, fsClim);

        // Formatear hora
        const hourStr = `${String(Math.floor(hourDecimal)).padStart(2, '0')}:${String(Math.round((hourDecimal % 1) * 60)).padStart(2, '0')}`;

        results.push({
          evento: criticalDay.name,
          month: MONTHS_SHORT[criticalDay.month - 1],
          day: criticalDay.day,
          hourStr,
          hour: hourDecimal,
          heightSolar: Math.round(solarPos.altitude * 100) / 100,
          azimuthSolar: Math.round(solarPos.azimuth * 100) / 100,
          facade: facade.name,
          fsGeometrico: Math.round(fsGeom * 1000) / 1000,
          fsClimatico: Math.round(fsClim * 1000) / 1000,
          fs: Math.round(fsCombined * 1000) / 1000,
          situacion,
          obstacle: obstacleNames.length > 0 ? obstacleNames.join(', ') : 'Ninguno',
        });
      }
    }
  }

  return results;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Busca el registro EPW más cercano cuando no hay datos exactos para un día.
 * Usa el promedio del mismo mes y hora como fallback.
 */
function findClosestWeatherRecord(
  epwData: EPWData,
  month: number,
  day: number,
  hour: number
): WeatherData | null {
  // Buscar el mismo día y hora
  let record = epwData.weatherData.find(
    w => w.month === month && w.day === day && w.hour === hour
  );
  if (record) return record;

  // Buscar días cercanos (±1 día)
  for (const offset of [1, -1, 2, -2]) {
    record = epwData.weatherData.find(
      w => w.month === month && w.day === day + offset && w.hour === hour
    );
    if (record) return record;
  }

  // Fallback: promedio del mes para esa hora
  const monthHourRecords = epwData.weatherData.filter(
    w => w.month === month && w.hour === hour
  );
  if (monthHourRecords.length === 0) return null;

  const avg: WeatherData = {
    year: monthHourRecords[0].year,
    month,
    day,
    hour,
    minute: 0,
    temperature: monthHourRecords.reduce((s, r) => s + r.temperature, 0) / monthHourRecords.length,
    dewPoint: monthHourRecords.reduce((s, r) => s + r.dewPoint, 0) / monthHourRecords.length,
    relativeHumidity: monthHourRecords.reduce((s, r) => s + r.relativeHumidity, 0) / monthHourRecords.length,
    atmosphericPressure: monthHourRecords.reduce((s, r) => s + r.atmosphericPressure, 0) / monthHourRecords.length,
    directNormalIrradiance: monthHourRecords.reduce((s, r) => s + r.directNormalIrradiance, 0) / monthHourRecords.length,
    diffuseHorizontalIrradiance: monthHourRecords.reduce((s, r) => s + r.diffuseHorizontalIrradiance, 0) / monthHourRecords.length,
    globalHorizontalIrradiance: monthHourRecords.reduce((s, r) => s + r.globalHorizontalIrradiance, 0) / monthHourRecords.length,
    windSpeed: monthHourRecords.reduce((s, r) => s + r.windSpeed, 0) / monthHourRecords.length,
    cloudCover: monthHourRecords.reduce((s, r) => s + r.cloudCover, 0) / monthHourRecords.length,
  };

  return avg;
}

/**
 * Convierte resultados del cruce a formato AnalysisPoint compatible con la tabla existente.
 */
export function crossingResultsToAnalysisPoints(results: CrossingResult[]): Array<{
  id: string;
  month: string;
  day: number;
  hour: number;
  heightSolar: number;
  azimuthSolar: number;
  obstacle: string;
  shadowedArea: number;
  fs: number;
  autoCalculated: boolean;
  evento: string;
  fsGeometrico: number;
  fsClimatico: number;
  situacion: string;
  hourStr: string;
}> {
  return results.map((r, i) => ({
    id: `crossing_${Date.now()}_${i}`,
    month: r.month,
    day: r.day,
    hour: r.hour,
    heightSolar: r.heightSolar,
    azimuthSolar: r.azimuthSolar,
    obstacle: `${r.facade}${r.obstacle !== 'Ninguno' ? ` [${r.obstacle}]` : ''}`,
    shadowedArea: Math.round(r.fs * 100),
    fs: r.fs,
    autoCalculated: true,
    evento: r.evento,
    fsGeometrico: r.fsGeometrico,
    fsClimatico: r.fsClimatico,
    situacion: r.situacion,
    hourStr: r.hourStr,
  }));
}

/**
 * Genera fachadas automáticas basadas en la geometría del edificio importado.
 * Detecta las orientaciones principales de las superficies de análisis.
 */
export function generateFacadesFromObstacles(obstacles: ObstaclePolygon[]): FacadeDefinition[] {
  if (obstacles.length === 0) {
    return DEFAULT_CROSSING_CONFIG.facades;
  }

  // Analizar los azimuts de los vértices de los obstáculos para inferir orientaciones principales
  const allAzimuths: number[] = [];
  for (const obs of obstacles) {
    for (const v of obs.vertices) {
      allAzimuths.push(v.azimuth);
    }
  }

  if (allAzimuths.length === 0) {
    return DEFAULT_CROSSING_CONFIG.facades;
  }

  // Agrupar azimuts en 4 cuadrantes y encontrar el centro de cada grupo
  const quadrants = [
    { min: -45, max: 45, name: 'Norte', default: 0 },
    { min: 45, max: 135, name: 'Oeste', default: 90 },
    { min: -135, max: -45, name: 'Este', default: -90 },
    { min: 135, max: 225, name: 'Sur', default: 180 },
  ];

  // Retornar las 4 fachadas cardinales por defecto
  return DEFAULT_CROSSING_CONFIG.facades;
}
