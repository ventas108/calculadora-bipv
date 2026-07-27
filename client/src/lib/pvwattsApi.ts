/**
 * PVWatts API Client - Frontend wrapper para consultar PVWatts v8 via proxy backend
 * 
 * PVWatts (NREL) proporciona estimaciones de producción solar basadas en datos satelitales TMY.
 * Los datos mensuales incluyen: AC, DC, POA, DNI, DHI, T_amb, WindSpeed, SolRad.
 */

// Tipos normalizados para PVWatts
export interface PVWattsMonthlyData {
  month: number;           // 1-12
  monthName: string;       // Enero, Febrero, ...
  ac_kWh: number;          // Producción AC mensual (kWh)
  dc_kWh: number;          // Producción DC mensual (kWh)
  poa_kWhm2: number;       // Irradiación POA mensual (kWh/m²)
  dn_kWhm2: number;        // Irradiación directa normal (kWh/m²)
  df_kWhm2: number;        // Irradiación difusa (kWh/m²)
  tamb_C: number;          // Temperatura ambiente promedio (°C)
  tcell_C: number;         // Temperatura de celda promedio (°C)
  wspd_ms: number;         // Velocidad del viento promedio (m/s)
}

export interface PVWattsResult {
  // Datos anuales
  annualAC_kWh: number;        // Producción AC anual (kWh)
  annualDC_kWh: number;        // Producción DC anual (kWh)
  annualPOA_kWhm2: number;     // Irradiación POA anual (kWh/m²)
  annualGHI_kWhm2: number;     // Irradiación GHI anual (kWh/m²) = solrad_annual
  specificYield: number;        // Specific Yield (kWh/kWp/año) = annualAC / system_capacity
  capacityFactor: number;       // Factor de capacidad (%)
  
  // Datos mensuales
  monthly: PVWattsMonthlyData[];
  
  // Parámetros de entrada usados
  params: {
    lat: number;
    lon: number;
    systemCapacity: number;  // kW
    azimuth: number;
    tilt: number;
    arrayType: number;
    moduleType: number;
    losses: number;
  };
  
  // Metadata
  stationInfo: {
    city: string;
    state: string;
    country: string;
    lat: number;
    lon: number;
    elev: number;
    tz: number;
    distance: number;  // km to station
    weatherDataSource: string;
  };
}

export interface PVWattsParams {
  lat: number;
  lon: number;
  system_capacity?: number;  // kW DC (default: 1)
  azimuth?: number;          // degrees (default: 180 for southern hemisphere, 0 for northern)
  tilt?: number;             // degrees (default: lat)
  array_type?: number;       // 0=Fixed Open Rack (default)
  module_type?: number;      // 0=Standard (default)
  losses?: number;           // % (default: 14.08)
  dc_ac_ratio?: number;
  inv_eff?: number;
}

const MONTH_NAMES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

/**
 * Consultar PVWatts v8 via proxy backend
 */
export async function getPVWattsCalculation(params: PVWattsParams): Promise<PVWattsResult> {
  const queryParams = new URLSearchParams();
  queryParams.set('lat', params.lat.toFixed(4));
  queryParams.set('lon', params.lon.toFixed(4));
  queryParams.set('system_capacity', (params.system_capacity ?? 1).toString());
  queryParams.set('azimuth', (params.azimuth ?? (params.lat < 0 ? 0 : 180)).toString());
  queryParams.set('tilt', (params.tilt ?? Math.abs(params.lat)).toString());
  queryParams.set('array_type', (params.array_type ?? 0).toString());
  queryParams.set('module_type', (params.module_type ?? 0).toString());
  queryParams.set('losses', (params.losses ?? 14.08).toString());
  queryParams.set('timeframe', 'monthly');

  if (params.dc_ac_ratio !== undefined) {
    queryParams.set('dc_ac_ratio', params.dc_ac_ratio.toString());
  }
  if (params.inv_eff !== undefined) {
    queryParams.set('inv_eff', params.inv_eff.toString());
  }

  const url = `/api/pvwatts?${queryParams.toString()}`;
  const resp = await fetch(url);

  if (!resp.ok) {
    const errData = await resp.json().catch(() => ({}));
    throw new Error(errData.error || `PVWatts error HTTP ${resp.status}`);
  }

  const data = await resp.json();
  return normalizePVWattsResponse(data, params);
}

/**
 * Normalizar la respuesta raw de PVWatts a nuestro formato tipado
 */
export function normalizePVWattsResponse(raw: any, params: PVWattsParams): PVWattsResult {
  const outputs = raw.outputs || {};
  const inputs = raw.inputs || {};
  const stationInfo = raw.station_info || {};

  // Arrays mensuales (12 elementos)
  const acMonthly: number[] = outputs.ac_monthly || outputs.ac || [];
  const dcMonthly: number[] = outputs.dc_monthly || outputs.dc || [];
  const poaMonthly: number[] = outputs.poa_monthly || outputs.poa || [];
  const dnMonthly: number[] = outputs.dn_monthly || outputs.dn || [];
  const dfMonthly: number[] = outputs.df_monthly || outputs.df || [];
  const tambMonthly: number[] = outputs.tamb_monthly || outputs.tamb || [];
  const tcellMonthly: number[] = outputs.tcell_monthly || outputs.tcell || [];
  const wspdMonthly: number[] = outputs.wspd_monthly || outputs.wspd || [];

  // Construir datos mensuales normalizados
  const monthly: PVWattsMonthlyData[] = [];
  for (let i = 0; i < 12; i++) {
    monthly.push({
      month: i + 1,
      monthName: MONTH_NAMES[i],
      ac_kWh: acMonthly[i] || 0,
      dc_kWh: dcMonthly[i] || 0,
      poa_kWhm2: poaMonthly[i] || 0,
      dn_kWhm2: dnMonthly[i] || 0,
      df_kWhm2: dfMonthly[i] || 0,
      tamb_C: tambMonthly[i] || 0,
      tcell_C: tcellMonthly[i] || 0,
      wspd_ms: wspdMonthly[i] || 0,
    });
  }

  // Totales anuales
  const annualAC = outputs.ac_annual ?? monthly.reduce((s, m) => s + m.ac_kWh, 0);
  const annualDC = outputs.dc_annual ?? monthly.reduce((s, m) => s + m.dc_kWh, 0);
  const annualPOA = monthly.reduce((s, m) => s + m.poa_kWhm2, 0);
  // PVWatts solrad_annual es kWh/m²/día promedio, NO anual.
  // Lo convertimos a kWh/m²/año para ser consistente con PVGIS.
  const solradAnnualRaw = outputs.solrad_annual;
  const annualGHI = solradAnnualRaw != null
    ? (solradAnnualRaw < 50 ? solradAnnualRaw * 365 : solradAnnualRaw) // Si < 50, es diario → × 365
    : annualPOA; // Fallback: usar POA anual como proxy
  const systemCapacity = params.system_capacity ?? 1;
  const specificYield = annualAC / systemCapacity; // kWh/kWp/año
  const capacityFactor = (annualAC / (systemCapacity * 8760)) * 100; // %

  return {
    annualAC_kWh: annualAC,
    annualDC_kWh: annualDC,
    annualPOA_kWhm2: annualPOA,
    annualGHI_kWhm2: annualGHI,
    specificYield,
    capacityFactor,
    monthly,
    params: {
      lat: params.lat,
      lon: params.lon,
      systemCapacity,
      azimuth: params.azimuth ?? (params.lat < 0 ? 0 : 180),
      tilt: params.tilt ?? Math.abs(params.lat),
      arrayType: params.array_type ?? 0,
      moduleType: params.module_type ?? 0,
      losses: params.losses ?? 14.08,
    },
    stationInfo: {
      city: stationInfo.city || '',
      state: stationInfo.state || '',
      country: stationInfo.country || '',
      lat: stationInfo.lat || params.lat,
      lon: stationInfo.lon || params.lon,
      elev: stationInfo.elev || 0,
      tz: stationInfo.tz || 0,
      distance: stationInfo.distance ? stationInfo.distance * 1.60934 : 0, // miles to km
      weatherDataSource: stationInfo.solar_resource_file || stationInfo.weather_data_source || 'TMY',
    },
  };
}

/**
 * Clasificar Specific Yield (kWh/kWp/año) para colorear el heatmap
 */
export function classifySpecificYield(sy: number): { category: string; color: string; rating: string } {
  if (sy >= 1800) return { category: 'Excelente', color: '#d32f2f', rating: '★★★★★' };
  if (sy >= 1600) return { category: 'Muy Buena', color: '#f57c00', rating: '★★★★' };
  if (sy >= 1400) return { category: 'Buena', color: '#fbc02d', rating: '★★★' };
  if (sy >= 1200) return { category: 'Aceptable', color: '#7cb342', rating: '★★★' };
  if (sy >= 1000) return { category: 'Limitada', color: '#1976d2', rating: '★★' };
  return { category: 'Muy Limitada', color: '#616161', rating: '★' };
}

// ===== DATOS HORARIOS PARA PR_T IEC 61724-1:2021 =====

/**
 * Datos horarios de PVWatts (8760 registros por año TMY)
 */
export interface PVWattsHourlyRecord {
  hour: number;        // 0-8759 (hora del año)
  month: number;       // 1-12
  day: number;         // 1-31
  hourOfDay: number;   // 0-23
  ac_W: number;        // Potencia AC (W)
  dc_W: number;        // Potencia DC (W)
  poa_Wm2: number;     // Irradiancia POA (W/m²)
  tamb_C: number;      // Temperatura ambiente (°C)
  tcell_C: number;     // Temperatura de celda (°C)
  wspd_ms: number;     // Velocidad del viento (m/s)
}

export interface PVWattsHourlyData {
  records: PVWattsHourlyRecord[];
  params: PVWattsParams;
  stationInfo: PVWattsResult['stationInfo'];
}

/**
 * Obtener datos horarios de PVWatts (8760 registros TMY)
 * Usado para calcular PR_T paso a paso temporal (IEC 61724-1:2021)
 */
export async function getPVWattsHourlyData(params: PVWattsParams): Promise<PVWattsHourlyData> {
  const queryParams = new URLSearchParams();
  queryParams.set('lat', params.lat.toFixed(4));
  queryParams.set('lon', params.lon.toFixed(4));
  queryParams.set('system_capacity', (params.system_capacity ?? 1).toString());
  queryParams.set('azimuth', (params.azimuth ?? (params.lat < 0 ? 0 : 180)).toString());
  queryParams.set('tilt', (params.tilt ?? Math.abs(params.lat)).toString());
  queryParams.set('array_type', (params.array_type ?? 0).toString());
  queryParams.set('module_type', (params.module_type ?? 0).toString());
  queryParams.set('losses', (params.losses ?? 14.08).toString());
  queryParams.set('timeframe', 'hourly');

  if (params.dc_ac_ratio !== undefined) {
    queryParams.set('dc_ac_ratio', params.dc_ac_ratio.toString());
  }
  if (params.inv_eff !== undefined) {
    queryParams.set('inv_eff', params.inv_eff.toString());
  }

  const url = `/api/pvwatts?${queryParams.toString()}`;
  const resp = await fetch(url);

  if (!resp.ok) {
    const errData = await resp.json().catch(() => ({}));
    throw new Error(errData.error || `PVWatts hourly error HTTP ${resp.status}`);
  }

  const data = await resp.json();
  const outputs = data.outputs || {};
  const stationInfo = data.station_info || {};

  // Arrays horarios (8760 elementos)
  const acHourly: number[] = outputs.ac || [];
  const dcHourly: number[] = outputs.dc || [];
  const poaHourly: number[] = outputs.poa || [];
  const tambHourly: number[] = outputs.tamb || [];
  const tcellHourly: number[] = outputs.tcell || [];
  const wspdHourly: number[] = outputs.wspd || [];

  // Construir registros horarios con mes/día/hora
  const daysInMonths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const records: PVWattsHourlyRecord[] = [];
  let hourIndex = 0;

  for (let m = 0; m < 12; m++) {
    for (let d = 0; d < daysInMonths[m]; d++) {
      for (let h = 0; h < 24; h++) {
        if (hourIndex < acHourly.length) {
          records.push({
            hour: hourIndex,
            month: m + 1,
            day: d + 1,
            hourOfDay: h,
            ac_W: acHourly[hourIndex] || 0,
            dc_W: dcHourly[hourIndex] || 0,
            poa_Wm2: poaHourly[hourIndex] || 0,
            tamb_C: tambHourly[hourIndex] || 0,
            tcell_C: tcellHourly[hourIndex] || 0,
            wspd_ms: wspdHourly[hourIndex] || 0,
          });
        }
        hourIndex++;
      }
    }
  }

  return {
    records,
    params,
    stationInfo: {
      city: stationInfo.city || '',
      state: stationInfo.state || '',
      country: stationInfo.country || '',
      lat: stationInfo.lat || params.lat,
      lon: stationInfo.lon || params.lon,
      elev: stationInfo.elev || 0,
      tz: stationInfo.tz || 0,
      distance: stationInfo.distance ? stationInfo.distance * 1.60934 : 0,
      weatherDataSource: stationInfo.solar_resource_file || stationInfo.weather_data_source || 'TMY',
    },
  };
}

/**
 * Obtener GHI anual rápido para un punto (system_capacity=1 kW)
 * Retorna el Specific Yield (kWh/kWp/año) para colorear el heatmap.
 * 
 * IMPORTANTE: PVWatts solrad_annual es irradiación en el plano del arreglo (POA),
 * NO GHI (Global Horizontal Irradiance). Para obtener GHI real, hacemos una
 * consulta adicional con tilt=0 (horizontal), lo que convierte POA en GHI.
 */
export async function getPVWattsQuickEstimate(lat: number, lon: number): Promise<{
  specificYield: number;
  annualAC: number;
  annualGHI: number;  // GHI real (tilt=0)
  avgTamb: number;
} | null> {
  try {
    // Consulta principal: con tilt=lat para producción óptima
    const result = await getPVWattsCalculation({
      lat,
      lon,
      system_capacity: 1,
      losses: 14.08,
    });
    
    // Consulta GHI: con tilt=0 para obtener irradiación horizontal global real
    const ghiResult = await getPVWattsCalculation({
      lat,
      lon,
      system_capacity: 1,
      losses: 14.08,
      tilt: 0,
      azimuth: 180,
    });
    
    const avgTamb = result.monthly.reduce((s, m) => s + m.tamb_C, 0) / 12;
    // GHI real = solrad_annual con tilt=0 (horizontal)
    const realGHI = ghiResult.annualGHI_kWhm2;
    
    return {
      specificYield: result.specificYield,
      annualAC: result.annualAC_kWh,
      annualGHI: realGHI,
      avgTamb,
    };
  } catch {
    return null;
  }
}
