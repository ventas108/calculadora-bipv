/**
 * Motor de Cálculo IAM + Soiling para Vidrios Fotovoltaicos BIPV
 * 
 * Implementa:
 * - Modelo IAM ASHRAE: reflexión geométrica de la luz según ángulo de incidencia
 * - Soiling estacional: pérdidas por suciedad/contaminación con corrección climática
 * - Modelo térmico confinado BIPV: temperatura de celda en fachada (k_bipv = 1.3)
 * - Ecuación extendida de producción BIPV con transparencia
 * - Ganancia lumínica pasiva transmitida al interior
 * 
 * Basado en: "ORCHESTRATOR: SIMULACIÓN BIPV DE ALTA PRECISIÓN (CON IAM, SOILING Y MONGODB)"
 */

import { calculateSolarPosition } from './solarPosition';

const DEG2RAD = Math.PI / 180;
const RAD2DEG = 180 / Math.PI;

// ─── Tipos ──────────────────────────────────────────────────────────────────

export interface BIPVGlassTechnology {
  id: string;
  name: string;
  brand?: 'hiitio' | 'einnova' | 'soltech' | 'generic';
  generation: '1G' | '2G' | '3G';
  generationLabel: string;
  eficienciaBase: number;       // Eficiencia STC base (0-1)
  coefTemperatura: number;      // Coeficiente de temperatura (%/°C, negativo)
  noct: number;                 // Temperatura nominal de operación (°C)
  b0Ashrae: number;             // Coeficiente de reflexión ASHRAE
  description: string;
}

export interface SoilingConfig {
  /** Factores de suciedad base mensual (1-12), valores 0-1 */
  monthlyFactors: Record<number, number>;
  /** Umbral de agua precipitable para autolavado (mm) */
  precipitableWaterThreshold: number;
  /** Factor de reducción por autolavado (0-1, ej: 0.15 = reduce 85%) */
  autoWashReduction: number;
}

export interface IAMResult {
  /** Ángulo de incidencia en grados */
  aoiDeg: number;
  /** Factor IAM ASHRAE (0-1) */
  fIam: number;
  /** POA directa neta después de IAM */
  poaDirectaNeta: number;
  /** POA total óptica (directa_neta + difusa) */
  poaTotalOptica: number;
}

export interface SoilingResult {
  /** Factor de soiling estacional base */
  soilingEstacional: number;
  /** Factor de soiling real (después de corrección climática) */
  soilingReal: number;
  /** Si hubo autolavado por lluvia */
  autoWash: boolean;
}

export interface ThermalResult {
  /** Temperatura de celda (°C) */
  tCell: number;
  /** Factor térmico (multiplicador de eficiencia) */
  factorTermico: number;
}

export interface BIPVHourlyResult {
  timestamp: Date;
  month: number;
  hour: number;
  // Posición solar
  elevacionSolar: number;
  azimutSolar: number;
  zenithSolar: number;
  // Irradiancias
  dniOriginal: number;
  dniConSombra: number;
  ghi: number;
  dhi: number;
  poaDirecta: number;
  poaDifusa: number;
  poaTotal: number;
  poaTotalOptica: number;
  // Factores de reducción
  factorSombraSF: number;
  fIamAshrae: number;
  soilingReal: number;
  factorTermico: number;
  // Temperaturas
  tAmb: number;
  tCell: number;
  // Resultados
  potenciaDcW: number;
  potenciaIluminacionPasivaW: number;
  eficienciaStcAjustada: number;
  // AOI
  aoiDeg: number;
}

export type TranspositionModel = 'isotropic' | 'perez';

export interface BIPVSimulationConfig {
  /** Tecnología de vidrio BIPV seleccionada */
  technology: BIPVGlassTechnology;
  /** Nivel de transparencia (0-1) */
  transparencia: number;
  /** Área de fachada en m² */
  areaM2: number;
  /** Inclinación de la fachada en grados (90 = vertical) */
  inclinacionFachada: number;
  /** Azimut de la fachada en grados */
  azimutFachada: number;
  /** Configuración de soiling */
  soiling: SoilingConfig;
  /** Factor k_bipv para modelo térmico (1.0=ventilado, 1.3=confinado) */
  kBipv: number;
  /** Modelo de transposición: 'isotropic' (Liu-Jordan) o 'perez' (anisótropo) */
  transpositionModel?: TranspositionModel;
  /** Si true, genera resultados horarios detallados (mayor uso de memoria) */
  generateHourlyResults?: boolean;
}

export interface BIPVSimulationSummary {
  technology: string;
  generation: string;
  transparencia: number;
  eficienciaAjustada: number;
  // Producción
  energiaAnualKwh: number;
  energiaAnualKwhM2: number;
  potenciaPicoW: number;
  // Ganancia lumínica
  iluminacionPasivaAnualKwh: number;
  // Factores promedio
  iamPromedio: number;
  soilingPromedio: number;
  factorTermicoPromedio: number;
  factorSombraPromedio: number;
  // Pérdidas ópticas (nuevo del script Python)
  irradianciaReflejadaAnualKwhM2: number; // Pérdida por reflexión geométrica (IAM loss)
  perdidasSoilingAnualKwhM2: number;      // Pérdida por suciedad
  perdidasTermicasAnualKwhM2: number;     // Pérdida por temperatura
  // Desglose mensual
  produccionMensualKwh: number[];
  iluminacionMensualKwh: number[];
  // Factores mensuales variables (12 valores)
  iamMensual: number[]; // Factor de retención IAM por mes (0-1)
  soilingMensual: number[]; // Pérdida fraccional soiling por mes (0-1)
  // Horas simuladas
  horasSimuladas: number;
  // Modelo de transposición usado
  transpositionModel: TranspositionModel;
  // Resultados horarios detallados (opcional)
  hourlyResults?: BIPVHourlyResult[];
}

// ─── Constantes por defecto ─────────────────────────────────────────────────

export const DEFAULT_SOILING_CONFIG: SoilingConfig = {
  monthlyFactors: {
    1: 0.05, 2: 0.06, 3: 0.04, 4: 0.02, 5: 0.02, 6: 0.04,
    7: 0.05, 8: 0.06, 9: 0.04, 10: 0.02, 11: 0.01, 12: 0.04
  },
  precipitableWaterThreshold: 25.0,
  autoWashReduction: 0.15,
};

export const TRANSPARENCY_LEVELS = [0.10, 0.20, 0.40, 0.60];

// ─── Funciones de Cálculo ───────────────────────────────────────────────────

/**
 * Calcula el Ángulo de Incidencia (AOI) sobre una superficie inclinada.
 * 
 * cos(AOI) = cos(zenith) * cos(tilt) + sin(zenith) * sin(tilt) * cos(azimut_sol - azimut_superficie)
 */
export function calculateAOI(
  solarZenithDeg: number,
  solarAzimuthDeg: number,
  surfaceTiltDeg: number,
  surfaceAzimuthDeg: number
): number {
  const zenithRad = solarZenithDeg * DEG2RAD;
  const tiltRad = surfaceTiltDeg * DEG2RAD;
  const deltaAzRad = (solarAzimuthDeg - surfaceAzimuthDeg) * DEG2RAD;

  const cosAOI = Math.cos(zenithRad) * Math.cos(tiltRad)
    + Math.sin(zenithRad) * Math.sin(tiltRad) * Math.cos(deltaAzRad);

  // Clamp para evitar errores numéricos
  const aoiRad = Math.acos(Math.max(-1, Math.min(1, cosAOI)));
  return aoiRad * RAD2DEG;
}

/**
 * Calcula el Factor IAM según modelo ASHRAE.
 * 
 * f_IAM = 1 - b0 * (1/cos(AOI) - 1)
 * 
 * Para AOI >= 85°, se asume reflexión total (f_IAM = 0).
 * 
 * @param aoiDeg Ángulo de incidencia en grados
 * @param b0Ashrae Coeficiente de reflexión ASHRAE del vidrio
 * @returns Factor IAM en rango [0, 1]
 */
export function calculateIAM_ASHRAE(aoiDeg: number, b0Ashrae: number): number {
  if (aoiDeg >= 85.0 || aoiDeg < 0) return 0.0;

  const cosAOI = Math.cos(aoiDeg * DEG2RAD);
  if (cosAOI <= 0) return 0.0;

  const fIam = 1.0 - b0Ashrae * ((1.0 / cosAOI) - 1.0);
  return Math.max(0.0, Math.min(1.0, fIam));
}

/**
 * Aplica el modelo IAM a la irradiancia POA.
 * 
 * Solo la componente directa se ve afectada por el IAM.
 * La componente difusa no se modifica (ya es omnidireccional).
 */
export function applyIAM(
  poaDirecta: number,
  poaDifusa: number,
  solarZenithDeg: number,
  solarAzimuthDeg: number,
  surfaceTiltDeg: number,
  surfaceAzimuthDeg: number,
  b0Ashrae: number
): IAMResult {
  const aoiDeg = calculateAOI(solarZenithDeg, solarAzimuthDeg, surfaceTiltDeg, surfaceAzimuthDeg);
  const fIam = calculateIAM_ASHRAE(aoiDeg, b0Ashrae);

  const poaDirectaNeta = poaDirecta * fIam;
  const poaTotalOptica = poaDirectaNeta + poaDifusa;

  return { aoiDeg, fIam, poaDirectaNeta, poaTotalOptica };
}

/**
 * Calcula el factor de soiling (suciedad) con corrección climática.
 * 
 * Si hay agua precipitable > umbral, se simula autolavado natural
 * que reduce la suciedad acumulada significativamente.
 */
export function calculateSoiling(
  month: number,
  precipitableWater: number | undefined,
  config: SoilingConfig
): SoilingResult {
  const soilingEstacional = config.monthlyFactors[month] || 0.04;

  let autoWash = false;
  let soilingReal = soilingEstacional;

  if (precipitableWater != null && precipitableWater > config.precipitableWaterThreshold) {
    soilingReal = soilingEstacional * config.autoWashReduction;
    autoWash = true;
  }

  return { soilingEstacional, soilingReal, autoWash };
}

/**
 * Modelo térmico confinado para fachada BIPV.
 * 
 * T_cell = T_amb + POA_total_optica × ((NOCT - 20) / 800) × k_bipv
 * factor_termico = 1 + coef_temperatura × (T_cell - 25)
 * 
 * @param kBipv Factor de confinamiento (1.0=ventilado libre, 1.3=fachada confinada, 1.5=sin ventilación)
 */
export function calculateThermalBIPV(
  tAmb: number,
  poaTotalOptica: number,
  noct: number,
  coefTemperatura: number,
  kBipv: number = 1.3
): ThermalResult {
  const tCell = tAmb + poaTotalOptica * ((noct - 20) / 800.0) * kBipv;
  const factorTermico = 1.0 + coefTemperatura * (tCell - 25.0);

  return { tCell, factorTermico };
}

/**
 * Calcula la eficiencia STC ajustada por transparencia.
 * 
 * η_adj = η_base × (1 - τ)
 * 
 * Donde τ es la transparencia del vidrio (porción que deja pasar la luz
 * y por tanto NO tiene material semiconductor activo).
 */
export function calculateAdjustedEfficiency(
  eficienciaBase: number,
  transparencia: number
): number {
  return eficienciaBase * (1.0 - transparencia);
}

/**
 * Ecuación extendida de producción BIPV.
 * 
 * P_dc = POA_total_optica × área × η_adj × factor_termico × (1 - soiling_real)
 */
export function calculateBIPVPower(
  poaTotalOptica: number,
  areaM2: number,
  eficienciaAjustada: number,
  factorTermico: number,
  soilingReal: number
): number {
  const potencia = poaTotalOptica * areaM2 * eficienciaAjustada * factorTermico * (1.0 - soilingReal);
  return Math.max(0.0, potencia);
}

/**
 * Calcula la ganancia lumínica pasiva transmitida al interior del edificio.
 * 
 * P_luz = POA_total × área × τ
 */
export function calculatePassiveLighting(
  poaTotal: number,
  areaM2: number,
  transparencia: number
): number {
  return poaTotal * areaM2 * transparencia;
}

/**
 * Calcula la transposición POA (Plane of Array) usando modelo isótropo (Liu-Jordan).
 * Equivalente simplificado de pvlib.irradiance.get_total_irradiance con model='isotropic'.
 */
export function calculatePOATransposition(
  dni: number,
  ghi: number,
  dhi: number,
  solarZenithDeg: number,
  solarAzimuthDeg: number,
  surfaceTiltDeg: number,
  surfaceAzimuthDeg: number,
  albedo: number = 0.2
): { poaDirecta: number; poaDifusa: number; poaReflejada: number; poaTotal: number } {
  const zenithRad = solarZenithDeg * DEG2RAD;
  const tiltRad = surfaceTiltDeg * DEG2RAD;
  const deltaAzRad = (solarAzimuthDeg - surfaceAzimuthDeg) * DEG2RAD;

  // Componente directa: DNI × cos(AOI)
  const cosAOI = Math.cos(zenithRad) * Math.cos(tiltRad)
    + Math.sin(zenithRad) * Math.sin(tiltRad) * Math.cos(deltaAzRad);
  const poaDirecta = dni * Math.max(0, cosAOI);

  // Componente difusa (modelo isótropo Liu-Jordan)
  const poaDifusa = dhi * (1 + Math.cos(tiltRad)) / 2;

  // Componente reflejada del suelo
  const poaReflejada = ghi * albedo * (1 - Math.cos(tiltRad)) / 2;

  const poaTotal = poaDirecta + poaDifusa + poaReflejada;

  return { poaDirecta, poaDifusa, poaReflejada, poaTotal };
}

/**
 * Modelo de transposición Perez (anisótropo) para difusa.
 * 
 * Implementa el modelo simplificado de Perez et al. (1990) que divide la radiación
 * difusa en tres componentes: isotrópica, circunsolar, y horizonte.
 * 
 * Equivalente a pvlib.irradiance.get_total_irradiance con model='perez'.
 * 
 * Referencia: Perez, R., et al. (1990). "Modeling daylight availability and
 * irradiance components from direct and global irradiance." Solar Energy, 44(5), 271-289.
 */
export function calculatePOAPerez(
  dni: number,
  ghi: number,
  dhi: number,
  solarZenithDeg: number,
  solarAzimuthDeg: number,
  surfaceTiltDeg: number,
  surfaceAzimuthDeg: number,
  dayOfYear: number,
  albedo: number = 0.2
): { poaDirecta: number; poaDifusa: number; poaReflejada: number; poaTotal: number; poaCircunsolar: number; poaHorizonte: number } {
  const zenithRad = solarZenithDeg * DEG2RAD;
  const tiltRad = surfaceTiltDeg * DEG2RAD;
  const deltaAzRad = (solarAzimuthDeg - surfaceAzimuthDeg) * DEG2RAD;

  // Componente directa: DNI × cos(AOI)
  const cosAOI = Math.cos(zenithRad) * Math.cos(tiltRad)
    + Math.sin(zenithRad) * Math.sin(tiltRad) * Math.cos(deltaAzRad);
  const poaDirecta = dni * Math.max(0, cosAOI);

  // --- Modelo Perez para difusa ---
  // Factor de corrección de distancia Tierra-Sol
  const B = (2 * Math.PI * dayOfYear) / 365;
  const E0 = 1.00011 + 0.034221 * Math.cos(B) + 0.00128 * Math.sin(B)
    + 0.000719 * Math.cos(2 * B) + 0.000077 * Math.sin(2 * B);

  // Irradiancia extraterrestre horizontal
  const cosZenith = Math.cos(zenithRad);
  const I0h = 1367 * E0 * Math.max(0.001, cosZenith);

  // Índice de claridad (epsilon) - mide la anisotropía del cielo
  const kappa = 1.041; // constante para zenith en radianes
  const zenithCubed = Math.pow(zenithRad, 3);
  let epsilon = 1.0;
  if (dhi > 0) {
    epsilon = ((dhi + dni) / dhi + kappa * zenithCubed) / (1 + kappa * zenithCubed);
  }

  // Índice de brillo (delta) - normaliza la difusa
  const AM = 1.0 / Math.max(0.001, cosZenith); // Masa de aire simplificada
  const delta = dhi * AM / I0h;

  // Coeficientes Perez F1 (circunsolar) y F2 (horizonte) según bin de epsilon
  const { f1, f2 } = getPerezCoefficients(epsilon, delta, zenithRad);

  // Ratio a/b para componente circunsolar
  const a = Math.max(0, cosAOI);
  const b = Math.max(0.087, cosZenith);

  // Componentes difusas Perez
  const poaDifusaIsotropica = dhi * (1 - f1) * (1 + Math.cos(tiltRad)) / 2;
  const poaCircunsolar = dhi * f1 * (a / b);
  const poaHorizonte = dhi * f2 * Math.sin(tiltRad);

  const poaDifusa = Math.max(0, poaDifusaIsotropica + poaCircunsolar + poaHorizonte);

  // Componente reflejada del suelo (igual que isótropo)
  const poaReflejada = ghi * albedo * (1 - Math.cos(tiltRad)) / 2;

  const poaTotal = poaDirecta + poaDifusa + poaReflejada;

  return { poaDirecta, poaDifusa, poaReflejada, poaTotal, poaCircunsolar, poaHorizonte };
}

/**
 * Coeficientes empíricos del modelo Perez (1990) simplificado.
 * Basado en los 8 bins de epsilon del modelo original.
 */
function getPerezCoefficients(
  epsilon: number,
  delta: number,
  zenithRad: number
): { f1: number; f2: number } {
  // Coeficientes Perez simplificados (8 bins de epsilon)
  // Fuente: Perez et al. 1990, Tabla 1
  const perezTable: Array<{ epsilonMax: number; f11: number; f12: number; f13: number; f21: number; f22: number; f23: number }> = [
    { epsilonMax: 1.065, f11: -0.0083, f12: 0.5877, f13: -0.0621, f21: -0.0596, f22: 0.0721, f23: -0.0220 },
    { epsilonMax: 1.230, f11: 0.1299, f12: 0.6826, f13: -0.1514, f21: -0.0189, f22: 0.0660, f23: -0.0289 },
    { epsilonMax: 1.500, f11: 0.3297, f12: 0.4869, f13: -0.2211, f21: 0.0554, f22: -0.0640, f23: -0.0261 },
    { epsilonMax: 1.950, f11: 0.5682, f12: 0.1875, f13: -0.2951, f21: 0.1089, f22: -0.1519, f23: -0.0140 },
    { epsilonMax: 2.800, f11: 0.8730, f12: -0.3920, f13: -0.3616, f21: 0.2256, f22: -0.4620, f23: 0.0012 },
    { epsilonMax: 4.500, f11: 1.1326, f12: -1.2367, f13: -0.4118, f21: 0.2878, f22: -0.8230, f23: 0.0559 },
    { epsilonMax: 6.200, f11: 1.0602, f12: -1.5999, f13: -0.3589, f21: 0.2642, f22: -1.1272, f23: 0.1311 },
    { epsilonMax: Infinity, f11: 0.6777, f12: -0.3273, f13: -0.2504, f21: 0.1561, f22: -1.3765, f23: 0.2506 },
  ];

  // Encontrar el bin correcto
  const bin = perezTable.find(b => epsilon < b.epsilonMax) || perezTable[perezTable.length - 1];

  // Calcular F1 y F2
  const f1 = Math.max(0, bin.f11 + bin.f12 * delta + bin.f13 * zenithRad);
  const f2 = bin.f21 + bin.f22 * delta + bin.f23 * zenithRad;

  return { f1, f2 };
}

/**
 * Calcula el día del año a partir de mes y día.
 */
export function dayOfYear(month: number, day: number): number {
  const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let doy = day;
  for (let m = 0; m < month - 1; m++) {
    doy += daysInMonth[m];
  }
  return doy;
}

/**
 * Evalúa si un obstáculo bloquea el sol en una posición dada.
 * Retorna el factor de sombra (1.0 = sin sombra, 0.0 = totalmente sombreado).
 */
export function evaluateObstacleShading(
  solarAzimuthDeg: number,
  solarElevationDeg: number,
  obstacles: Array<{ azimutInicio: number; azimutFin: number; alturaAngular: number }>
): number {
  if (solarElevationDeg <= 0) return 0.0;

  const azNorm = ((solarAzimuthDeg % 360) + 360) % 360;

  for (const obs of obstacles) {
    if (azNorm >= obs.azimutInicio && azNorm <= obs.azimutFin) {
      if (solarElevationDeg < obs.alturaAngular) {
        return 0.0; // Sombreado por obstáculo
      }
    }
  }

  return 1.0; // Sin sombra
}

// ─── Simulación Completa ────────────────────────────────────────────────────

export interface WeatherHourData {
  month: number;
  day: number;
  hour: number;
  dni: number;
  ghi: number;
  dhi: number;
  tempAir: number;
  windSpeed?: number;
  precipitableWater?: number;
}

/**
 * Ejecuta la simulación BIPV completa para un conjunto de datos horarios.
 * Equivalente al motor Python simulador_bipv.py del orquestador.
 * 
 * Soporta dos modelos de transposición:
 * - 'isotropic': Liu-Jordan (rápido, conservador)
 * - 'perez': Perez et al. 1990 (preciso, anisótropo)
 * 
 * Opcionalmente genera resultados horarios detallados (estructura BSON del script Python).
 */
export function runBIPVSimulation(
  weatherData: WeatherHourData[],
  latitude: number,
  longitude: number,
  timezone: number,
  config: BIPVSimulationConfig,
  obstacles: Array<{ azimutInicio: number; azimutFin: number; alturaAngular: number }> = [],
  monthlyShadingFactors3D: number[] = Array(12).fill(1.0)
): BIPVSimulationSummary {
  const { technology, transparencia, areaM2, inclinacionFachada, azimutFachada, soiling, kBipv } = config;
  const usePerez = config.transpositionModel === 'perez';
  const generateHourly = config.generateHourlyResults === true;

  const eficienciaAjustada = calculateAdjustedEfficiency(technology.eficienciaBase, transparencia);

  let totalEnergyWh = 0;
  let totalLightingWh = 0;
  let peakPowerW = 0;
  let totalIam = 0;
  let totalSoiling = 0;
  let totalThermal = 0;
  let totalShadow = 0;
  let horasSimuladas = 0;
  // Pérdidas acumuladas (W·h)
  let totalIrradianciaReflejadaWh = 0; // Pérdida por reflexión geométrica (IAM)
  let totalPerdidasSoilingWh = 0;      // Pérdida por suciedad
  let totalPerdidasTermicasWh = 0;     // Pérdida por temperatura

  const produccionMensualWh = new Array(12).fill(0);
  const iluminacionMensualWh = new Array(12).fill(0);
  const iamMensualSum = new Array(12).fill(0);
  const soilingMensualSum = new Array(12).fill(0);
  const horasMensuales = new Array(12).fill(0);
  const hourlyResults: BIPVHourlyResult[] = [];

  for (const record of weatherData) {
    // Calcular posición solar
    const solarPos = calculateSolarPosition(
      latitude, longitude, timezone,
      record.month, record.day, record.hour
    );

    if (solarPos.altitude <= 0) continue; // Noche

    const zenithDeg = 90 - solarPos.altitude;

    // A) Factor de sombra por obstáculos (equivalente a calcular_sombreado del Python)
    const sf = evaluateObstacleShading(solarPos.azimuth, solarPos.altitude, obstacles);
    // A2) Factor de sombreado 3D mensual (del análisis de fachada con modelo importado)
    const sf3D = monthlyShadingFactors3D[record.month - 1] ?? 1.0;
    const dniConSombra = record.dni * sf * sf3D;

    // B) Transposición POA (modelo seleccionable)
    let poa: { poaDirecta: number; poaDifusa: number; poaReflejada: number; poaTotal: number };
    if (usePerez) {
      const doy = dayOfYear(record.month, record.day);
      poa = calculatePOAPerez(
        dniConSombra, record.ghi, record.dhi,
        zenithDeg, solarPos.azimuth,
        inclinacionFachada, azimutFachada,
        doy
      );
    } else {
      poa = calculatePOATransposition(
        dniConSombra, record.ghi, record.dhi,
        zenithDeg, solarPos.azimuth,
        inclinacionFachada, azimutFachada
      );
    }

    if (poa.poaTotal <= 0) continue;

    // C) IAM ASHRAE (modelo matemático de reflexión geométrica)
    const iamResult = applyIAM(
      poa.poaDirecta, poa.poaDifusa,
      zenithDeg, solarPos.azimuth,
      inclinacionFachada, azimutFachada,
      technology.b0Ashrae
    );

    // D) Soiling
    const soilingResult = calculateSoiling(record.month, record.precipitableWater, soiling);

    // E) Modelo térmico confinado
    const thermalResult = calculateThermalBIPV(
      record.tempAir, iamResult.poaTotalOptica,
      technology.noct, technology.coefTemperatura, kBipv
    );

    // F) Producción DC
    const potenciaDcW = calculateBIPVPower(
      iamResult.poaTotalOptica, areaM2,
      eficienciaAjustada, thermalResult.factorTermico,
      soilingResult.soilingReal
    );

    // G) Ganancia lumínica pasiva
    const potenciaLuzW = calculatePassiveLighting(poa.poaTotal, areaM2, transparencia);

    // H) Cálculo de pérdidas detalladas (equivalente al BSON del Python)
    // irradiancia_reflejada = poa_total - poa_total_optica (pérdida IAM)
    const irradianciaReflejadaW = (poa.poaTotal - iamResult.poaTotalOptica) * areaM2;
    // Pérdida por soiling: potencia sin soiling - potencia con soiling
    const potenciaSinSoiling = iamResult.poaTotalOptica * areaM2 * eficienciaAjustada * thermalResult.factorTermico;
    const perdidaSoilingW = potenciaSinSoiling * soilingResult.soilingReal;
    // Pérdida térmica: potencia a 25°C - potencia real
    const potenciaA25C = iamResult.poaTotalOptica * areaM2 * eficienciaAjustada * (1.0 - soilingResult.soilingReal);
    const perdidaTermicaW = potenciaA25C - potenciaDcW;

    // Acumular
    totalEnergyWh += potenciaDcW;
    totalLightingWh += potenciaLuzW;
    if (potenciaDcW > peakPowerW) peakPowerW = potenciaDcW;

    totalIam += iamResult.fIam;
    totalSoiling += soilingResult.soilingReal;
    totalThermal += thermalResult.factorTermico;
    totalShadow += sf;
    totalIrradianciaReflejadaWh += Math.max(0, irradianciaReflejadaW);
    totalPerdidasSoilingWh += Math.max(0, perdidaSoilingW);
    totalPerdidasTermicasWh += Math.max(0, perdidaTermicaW);
    horasSimuladas++;

    const monthIdx = record.month - 1;
    produccionMensualWh[monthIdx] += potenciaDcW;
    iluminacionMensualWh[monthIdx] += potenciaLuzW;
    iamMensualSum[monthIdx] += iamResult.fIam;
    soilingMensualSum[monthIdx] += soilingResult.soilingReal;
    horasMensuales[monthIdx]++;

    // I) Registro horario detallado (estructura equivalente al documento BSON del Python)
    if (generateHourly) {
      hourlyResults.push({
        timestamp: new Date(2026, record.month - 1, record.day, record.hour),
        month: record.month,
        hour: record.hour,
        elevacionSolar: solarPos.altitude,
        azimutSolar: solarPos.azimuth,
        zenithSolar: zenithDeg,
        dniOriginal: record.dni,
        dniConSombra,
        ghi: record.ghi,
        dhi: record.dhi,
        poaDirecta: poa.poaDirecta,
        poaDifusa: poa.poaDifusa,
        poaTotal: poa.poaTotal,
        poaTotalOptica: iamResult.poaTotalOptica,
        factorSombraSF: sf,
        fIamAshrae: iamResult.fIam,
        soilingReal: soilingResult.soilingReal,
        factorTermico: thermalResult.factorTermico,
        tAmb: record.tempAir,
        tCell: thermalResult.tCell,
        potenciaDcW,
        potenciaIluminacionPasivaW: potenciaLuzW,
        eficienciaStcAjustada: eficienciaAjustada,
        aoiDeg: iamResult.aoiDeg,
      });
    }
  }

  const energiaAnualKwh = totalEnergyWh / 1000;
  const iluminacionPasivaAnualKwh = totalLightingWh / 1000;

  const result: BIPVSimulationSummary = {
    technology: technology.name,
    generation: technology.generation,
    transparencia,
    eficienciaAjustada,
    energiaAnualKwh,
    energiaAnualKwhM2: areaM2 > 0 ? energiaAnualKwh / areaM2 : 0,
    potenciaPicoW: peakPowerW,
    iluminacionPasivaAnualKwh,
    iamPromedio: horasSimuladas > 0 ? totalIam / horasSimuladas : 0,
    soilingPromedio: horasSimuladas > 0 ? totalSoiling / horasSimuladas : 0,
    factorTermicoPromedio: horasSimuladas > 0 ? totalThermal / horasSimuladas : 0,
    factorSombraPromedio: horasSimuladas > 0 ? totalShadow / horasSimuladas : 0,
    // Pérdidas ópticas detalladas (del script Python multivariable)
    irradianciaReflejadaAnualKwhM2: areaM2 > 0 ? (totalIrradianciaReflejadaWh / 1000) / areaM2 : 0,
    perdidasSoilingAnualKwhM2: areaM2 > 0 ? (totalPerdidasSoilingWh / 1000) / areaM2 : 0,
    perdidasTermicasAnualKwhM2: areaM2 > 0 ? (totalPerdidasTermicasWh / 1000) / areaM2 : 0,
    produccionMensualKwh: produccionMensualWh.map(wh => wh / 1000),
    iluminacionMensualKwh: iluminacionMensualWh.map(wh => wh / 1000),
    iamMensual: iamMensualSum.map((sum, i) => horasMensuales[i] > 0 ? sum / horasMensuales[i] : 0),
    soilingMensual: soilingMensualSum.map((sum, i) => horasMensuales[i] > 0 ? sum / horasMensuales[i] : 0),
    horasSimuladas,
    transpositionModel: usePerez ? 'perez' : 'isotropic',
  };

  if (generateHourly) {
    result.hourlyResults = hourlyResults;
  }

  return result;
}

/**
 * Ejecuta simulación comparativa multi-tecnología × multi-transparencia.
 * Equivalente al loop principal del orquestador Python.
 */
export function runComparativeSimulation(
  weatherData: WeatherHourData[],
  latitude: number,
  longitude: number,
  timezone: number,
  technologies: BIPVGlassTechnology[],
  transparencies: number[],
  areaM2: number,
  inclinacionFachada: number,
  azimutFachada: number,
  obstacles: Array<{ azimutInicio: number; azimutFin: number; alturaAngular: number }> = [],
  soilingConfig: SoilingConfig = DEFAULT_SOILING_CONFIG,
  kBipv: number = 1.3
): BIPVSimulationSummary[] {
  const results: BIPVSimulationSummary[] = [];

  for (const tech of technologies) {
    for (const tau of transparencies) {
      const config: BIPVSimulationConfig = {
        technology: tech,
        transparencia: tau,
        areaM2,
        inclinacionFachada,
        azimutFachada,
        soiling: soilingConfig,
        kBipv,
      };

      const summary = runBIPVSimulation(weatherData, latitude, longitude, timezone, config, obstacles);
      results.push(summary);
    }
  }

  return results;
}
