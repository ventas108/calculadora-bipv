/**
 * PVGIS API Integration - Frontend Client
 * Photovoltaic Geographical Information System - European Commission
 * https://re.jrc.ec.europa.eu/pvg_tools/en/
 * 
 * Usa el proxy backend local (/api/pvgis/:endpoint) para evitar problemas CORS.
 * PVGIS selecciona automáticamente la base de datos más adecuada (ERA5 o SARAH3).
 */

// Interfaces de respuesta PVGIS (normalizadas)
export interface PVGISMonthlyData {
  month: number;
  H_h: number;       // Irradiación horizontal (kWh/m²)
  H_i_opt: number;   // Irradiación en ángulo óptimo (kWh/m²)
  H_i: number;       // Irradiación en plano inclinado seleccionado (kWh/m²)
  Hb_n: number;      // Irradiación directa normal (kWh/m²)
  Kd: number;        // Ratio difusa/global
  T2m: number;       // Temperatura media (°C)
}

export interface PVGISPVCalcMonthly {
  month: number;
  E_d: number;       // Producción diaria promedio (kWh)
  E_m: number;       // Producción mensual (kWh)
  H_i_d: number;     // Irradiación diaria en plano (kWh/m²)
  H_i_m: number;     // Irradiación mensual en plano (kWh/m²)
  SD_m: number;      // Desviación estándar mensual (kWh)
}

export interface PVGISPVCalcResult {
  inputs: {
    location: { latitude: number; longitude: number; elevation: number };
    meteo_data: { radiation_db: string; meteo_db: string; year_min: number; year_max: number };
    mounting_system: { fixed: { slope: { value: number }; azimuth: { value: number } } };
    pv_module: { technology: string; peak_power: number; system_loss: number };
  };
  outputs: {
    monthly: { fixed: PVGISPVCalcMonthly[] };
    totals: { fixed: { E_d: number; E_m: number; E_y: number; H_i_d: number; H_i_y: number; SD_y: number } };
  };
}

export interface PVGISMonthlyRadResult {
  inputs: {
    location: { latitude: number; longitude: number; elevation: number };
    meteo_data: { radiation_db: string; year_min: number; year_max: number };
  };
  outputs: {
    monthly: PVGISMonthlyData[];
  };
}

export interface PVGISHourlyData {
  time: string;
  G_i: number;
  Gb_i: number;
  Gd_i: number;
  Gr_i: number;
  T2m: number;
  WS10m: number;
}

/**
 * Función para hacer fetch a PVGIS usando el proxy backend local.
 */
async function pvgisFetch(endpoint: string, params: Record<string, string | number>): Promise<any> {
  const queryString = Object.entries(params)
    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
    .join('&');

  const url = `/api/pvgis/${endpoint}?${queryString}`;

  const response = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    throw new Error(errorData.error || `Error ${response.status} al consultar PVGIS`);
  }

  return await response.json();
}

/**
 * Normalizar datos mensuales de MRcalc.
 * PVGIS devuelve 228 registros (19 años x 12 meses) con claves como H(h)_m.
 * Esta función agrupa por mes y promedia, devolviendo 12 registros normalizados.
 */
function normalizeMonthlyRadiation(rawMonthly: any[]): PVGISMonthlyData[] {
  if (!rawMonthly || rawMonthly.length === 0) return [];

  // Si ya tiene 12 registros con formato normalizado, devolverlos directamente
  if (rawMonthly.length === 12 && 'H_h' in rawMonthly[0]) {
    return rawMonthly;
  }

  // Agrupar por mes y promediar (formato PVGIS real: H(h)_m, H(i_opt)_m, etc.)
  const monthlyAvg: PVGISMonthlyData[] = [];
  for (let m = 1; m <= 12; m++) {
    const monthData = rawMonthly.filter((d: any) => d.month === m);
    if (monthData.length > 0) {
      monthlyAvg.push({
        month: m,
        H_h: monthData.reduce((s: number, d: any) => s + (d['H(h)_m'] || d['H_h'] || 0), 0) / monthData.length,
        H_i_opt: monthData.reduce((s: number, d: any) => s + (d['H(i_opt)_m'] || d['H_i_opt'] || 0), 0) / monthData.length,
        H_i: monthData.reduce((s: number, d: any) => s + (d['H(i)_m'] || d['H_i'] || d['H(h)_m'] || d['H_h'] || 0), 0) / monthData.length,
        Hb_n: monthData.reduce((s: number, d: any) => s + (d['Hb(n)_m'] || d['Hb_n'] || 0), 0) / monthData.length,
        Kd: monthData.reduce((s: number, d: any) => s + (d['Kd'] || 0.5), 0) / monthData.length,
        T2m: monthData.reduce((s: number, d: any) => s + (d['T2m'] || 25), 0) / monthData.length,
      });
    }
  }
  return monthlyAvg;
}

/**
 * Normalizar datos mensuales de PVcalc.
 * PVGIS devuelve claves como H(i)_d y H(i)_m en lugar de H_i_d y H_i_m.
 */
function normalizePVCalcMonthly(rawMonthly: any[]): PVGISPVCalcMonthly[] {
  if (!rawMonthly || rawMonthly.length === 0) return [];

  return rawMonthly.map((d: any) => ({
    month: d.month,
    E_d: d.E_d || 0,
    E_m: d.E_m || 0,
    H_i_d: d['H(i)_d'] || d.H_i_d || 0,
    H_i_m: d['H(i)_m'] || d.H_i_m || 0,
    SD_m: d.SD_m || 0,
  }));
}

/**
 * Normalizar totales de PVcalc.
 */
function normalizePVCalcTotals(rawTotals: any): PVGISPVCalcResult['outputs']['totals']['fixed'] {
  if (!rawTotals) return { E_d: 0, E_m: 0, E_y: 0, H_i_d: 0, H_i_y: 0, SD_y: 0 };

  return {
    E_d: rawTotals.E_d || 0,
    E_m: rawTotals.E_m || 0,
    E_y: rawTotals.E_y || 0,
    H_i_d: rawTotals['H(i)_d'] || rawTotals.H_i_d || 0,
    H_i_y: rawTotals['H(i)_y'] || rawTotals.H_i_y || 0,
    SD_y: rawTotals.SD_y || 0,
  };
}

/**
 * Obtener radiación mensual para una ubicación
 */
export async function getMonthlyRadiation(
  lat: number,
  lon: number,
  angle?: number,
): Promise<PVGISMonthlyRadResult> {
  const params: Record<string, string | number> = {
    lat: lat.toFixed(4),
    lon: lon.toFixed(4),
    horirrad: 1,
    optrad: 1,
    mr_dni: 1,
    d2g: 1,
    avtemp: 1,
  };

  if (angle !== undefined) {
    params.selectrad = 1;
    params.angle = angle;
  }

  const data = await pvgisFetch('MRcalc', params);

  // Normalizar datos mensuales
  const normalizedMonthly = normalizeMonthlyRadiation(data.outputs?.monthly || []);

  return {
    inputs: data.inputs || {
      location: { latitude: lat, longitude: lon, elevation: 0 },
      meteo_data: { radiation_db: 'PVGIS-ERA5', year_min: 2005, year_max: 2023 },
    },
    outputs: {
      monthly: normalizedMonthly,
    },
  };
}

/**
 * Calcular producción PV para una ubicación
 */
export async function getPVCalculation(
  lat: number,
  lon: number,
  peakPower: number,
  loss: number,
  angle?: number,
  aspect?: number,
  optimalAngles?: boolean,
  pvtechchoice?: string,
  mountingplace?: 'free' | 'building',
): Promise<PVGISPVCalcResult> {
  const params: Record<string, string | number> = {
    lat: lat.toFixed(4),
    lon: lon.toFixed(4),
    peakpower: peakPower,
    loss: loss,
  };

  // Tecnología del panel (crystSi, CdTe, CIS, Unknown)
  if (pvtechchoice) {
    params.pvtechchoice = pvtechchoice;
  }

  // Tipo de montaje (free = rack abierto, building = integrado BIPV)
  if (mountingplace) {
    params.mountingplace = mountingplace;
  }

  if (optimalAngles) {
    params.optimalangles = 1;
  } else {
    if (angle !== undefined) params.angle = angle;
    if (aspect !== undefined) params.aspect = aspect;
  }

  const data = await pvgisFetch('PVcalc', params);

  // Normalizar datos de PVcalc
  const normalizedMonthly = normalizePVCalcMonthly(data.outputs?.monthly?.fixed || []);
  const normalizedTotals = normalizePVCalcTotals(data.outputs?.totals?.fixed || {});

  return {
    inputs: data.inputs || {
      location: { latitude: lat, longitude: lon, elevation: 0 },
      meteo_data: { radiation_db: 'PVGIS-ERA5', meteo_db: 'ERA5', year_min: 2005, year_max: 2023 },
      mounting_system: { fixed: { slope: { value: angle || 0 }, azimuth: { value: aspect || 0 } } },
      pv_module: { technology: 'c-Si', peak_power: peakPower, system_loss: loss },
    },
    outputs: {
      monthly: { fixed: normalizedMonthly },
      totals: { fixed: normalizedTotals },
    },
  };
}

/**
 * Obtener perfil de horizonte para una ubicación
 */
export async function getHorizonProfile(
  lat: number,
  lon: number,
): Promise<{ outputs: { horizon_profile: { A: number; H_hor: number }[] }; inputs: any }> {
  const params: Record<string, string | number> = {
    lat: lat.toFixed(4),
    lon: lon.toFixed(4),
  };

  const data = await pvgisFetch('printhorizon', params);
  return data;
}

/**
 * Obtener datos TMY (Typical Meteorological Year)
 */
export async function getTMYData(
  lat: number,
  lon: number,
): Promise<any> {
  const params: Record<string, string | number> = {
    lat: lat.toFixed(4),
    lon: lon.toFixed(4),
  };

  const data = await pvgisFetch('tmy', params);
  return data;
}

// ===== DATOS HORARIOS PARA PR_T IEC 61724-1:2021 =====

/**
 * Datos horarios de PVGIS (seriescalc - 1 año TMY)
 */
export interface PVGISHourlyRecord {
  time: string;        // "20050101:0000" (UTC)
  month: number;       // 1-12
  day: number;         // 1-31
  hourOfDay: number;   // 0-23
  G_i: number;         // Global in-plane irradiance (W/m²)
  Gb_i: number;        // Direct in-plane irradiance (W/m²)
  Gd_i: number;        // Diffuse in-plane irradiance (W/m²)
  Gr_i: number;        // Reflected in-plane irradiance (W/m²)
  T2m: number;         // Air temperature (°C)
  WS10m: number;       // Wind speed at 10m (m/s)
  H_sun: number;       // Sun height/elevation (°)
  P_W?: number;        // PV power output (W) - if pvcalculation=1
}

export interface PVGISHourlySeries {
  records: PVGISHourlyRecord[];
  location: { latitude: number; longitude: number; elevation: number };
  radiationDb: string;
  yearMin: number;
  yearMax: number;
}

/**
 * Obtener datos horarios de PVGIS (seriescalc - 1 año)
 * Usado para calcular PR_T paso a paso temporal (IEC 61724-1:2021)
 * 
 * PVGIS seriescalc devuelve datos horarios para un rango de años.
 * Para PR_T usamos solo 1 año representativo.
 */
export async function getPVGISHourlyData(
  lat: number,
  lon: number,
  angle?: number,
  aspect?: number,
  peakpower?: number,
  loss?: number,
): Promise<PVGISHourlySeries> {
  const params: Record<string, string | number> = {
    lat: lat.toFixed(4),
    lon: lon.toFixed(4),
    components: 1,  // Return Gb(i), Gd(i), Gr(i)
  };

  // Usar un solo año reciente para datos representativos
  params.startyear = 2020;
  params.endyear = 2020;

  if (angle !== undefined) params.angle = angle;
  if (aspect !== undefined) params.aspect = aspect;

  // Si se pide cálculo PV, agregar parámetros
  if (peakpower !== undefined) {
    params.pvcalculation = 1;
    params.peakpower = peakpower;
    if (loss !== undefined) params.loss = loss;
  }

  const data = await pvgisFetch('seriescalc', params);

  const rawHourly: any[] = data.outputs?.hourly || [];
  const location = data.inputs?.location || { latitude: lat, longitude: lon, elevation: 0 };
  const meteo = data.inputs?.meteo_data || {};

  // Parsear registros horarios
  const records: PVGISHourlyRecord[] = rawHourly.map((h: any) => {
    const timeStr = h.time || '';
    // Format: "20200101:0010" -> year=2020, month=01, day=01, hour=00, min=10
    const month = parseInt(timeStr.substring(4, 6), 10) || 1;
    const day = parseInt(timeStr.substring(6, 8), 10) || 1;
    const hourOfDay = parseInt(timeStr.substring(9, 11), 10) || 0;

    // PVGIS uses keys like "Gb(i)", "Gd(i)", "Gr(i)"
    const G_i = h['G(i)'] ?? (h['Gb(i)'] || 0) + (h['Gd(i)'] || 0) + (h['Gr(i)'] || 0);
    const Gb_i = h['Gb(i)'] || 0;
    const Gd_i = h['Gd(i)'] || 0;
    const Gr_i = h['Gr(i)'] || 0;

    return {
      time: timeStr,
      month,
      day,
      hourOfDay,
      G_i: G_i,
      Gb_i,
      Gd_i,
      Gr_i,
      T2m: h.T2m || 0,
      WS10m: h.WS10m || 0,
      H_sun: h.H_sun || h['H_sun'] || 0,
      P_W: h.P !== undefined ? h.P : undefined,
    };
  });

  return {
    records,
    location,
    radiationDb: meteo.radiation_db || 'PVGIS-ERA5',
    yearMin: meteo.year_min || 2020,
    yearMax: meteo.year_max || 2020,
  };
}

// Nombres de meses en español
export const MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

// Clasificación de irradiancia anual
export function classifyAnnualIrradiance(annualKwh: number): {
  category: string;
  color: string;
  description: string;
} {
  if (annualKwh >= 2000) return { category: 'Excelente', color: '#d32f2f', description: 'Condiciones óptimas para energía solar' };
  if (annualKwh >= 1800) return { category: 'Muy Buena', color: '#f57c00', description: 'Alto potencial solar' };
  if (annualKwh >= 1600) return { category: 'Buena', color: '#fbc02d', description: 'Buen potencial solar' };
  if (annualKwh >= 1400) return { category: 'Aceptable', color: '#7cb342', description: 'Potencial solar moderado' };
  if (annualKwh >= 1200) return { category: 'Limitada', color: '#1976d2', description: 'Potencial solar limitado' };
  return { category: 'Muy Limitada', color: '#424242', description: 'Potencial solar muy bajo' };
}
