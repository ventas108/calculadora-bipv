/**
 * Modelo Mulcue-Llanos para estimación de Performance Ratio (PR)
 * y producción energética fotovoltaica.
 *
 * Referencia: Dr. Luis Fernando Mulcue Nieto
 * Tesis de maestría/doctorado - Universidad Nacional de Colombia
 *
 * Fórmulas verificadas contra Ejercicio 5 del curso BIPV Global.
 */

// ============================================================
// TIPOS
// ============================================================

export interface MulcuePRInput {
  /** Coeficiente de temperatura del panel (%/°C, valor negativo, ej: -0.36) */
  tempCoeffGamma: number;
  /** Temperatura ambiente promedio (°C) */
  ambientTemp: number;
  /** Factor de sistema Ksist (0.82 = sistema óptimo con excelentes equipos) */
  ksist?: number;
}

export interface MulcuePRResult {
  /** PR máximo estimado (0-1) */
  prMax: number;
  /** PR corregido (0-1) */
  prCorrected: number;
  /** Interpretación cualitativa */
  interpretation: 'optimo' | 'bueno' | 'medio' | 'problema' | 'falla';
  /** Descripción legible */
  description: string;
  /** Color asociado */
  color: string;
}

export interface ProductionInput {
  /** Irradiación horizontal diaria GHI (kWh/m²/día) - dato PVGIS */
  ghiDaily: number;
  /** Factor de irradiación FI (inclinación/orientación) - típico 0.85-1.15 */
  irradiationFactor: number;
  /** Factor de sombreado FS (0-1, donde 1 = sin sombras) */
  shadowFactor: number;
  /** Potencia nominal del módulo (W) */
  modulePower: number;
  /** Cantidad de módulos */
  moduleCount: number;
  /** Performance Ratio (0-1) */
  pr: number;
  /** Período en días (365 = anual, 30 = mensual) */
  days?: number;
}

export interface ProductionResult {
  /** Irradiación corregida sobre el generador (kWh/m²/día) = HSP/día */
  gaCorr: number;
  /** Horas Sol Pico totales del período (h) */
  hspTotal: number;
  /** Potencia pico instalada (kW) */
  peakPowerKw: number;
  /** Energía producida (kWh) */
  energyKwh: number;
  /** Energía producida (MWh) */
  energyMwh: number;
  /** Días del período */
  days: number;
}

export interface DiagnosticInput {
  /** Potencia nominal STC (W) */
  nominalPower: number;
  /** Coeficiente de temperatura γ (%/°C, valor negativo) */
  tempCoeffGamma: number;
  /** Irradiancia medida (W/m²) */
  irradiance: number;
  /** Temperatura de celda (°C) */
  cellTemp: number;
  /** Potencia real medida (W) */
  realPower: number;
  /** Eficiencia ideal del módulo (%) */
  idealEfficiency: number;
}

export interface DiagnosticResult {
  /** Factor de corrección por temperatura */
  tempFactor: number;
  /** Potencia corregida por temperatura (W) */
  tempCorrectedPower: number;
  /** Potencia esperada (W) */
  expectedPower: number;
  /** Rendimiento (0-1) */
  performance: number;
  /** Eficiencia real (%) */
  realEfficiency: number;
  /** Interpretación */
  interpretation: string;
  /** Color */
  color: string;
}

// ============================================================
// CONSTANTES
// ============================================================

/** Factor de sistema para equipos óptimos (Mulcue-Llanos) */
export const DEFAULT_KSIST = 0.82;

/** Temperatura de referencia del modelo Mulcue-Llanos (°C) - NO es 25°C STC */
export const MULCUE_T_REF = 21;

/** Irradiancia de referencia para cálculo NOCT (W/m²) */
export const G_NOCT_REF = 800;

/** Irradiancia STC de referencia (W/m²) */
export const G_STC = 1000;

/** NOCT por defecto si el panel no lo especifica (°C) */
export const DEFAULT_NOCT = 45;

/** Temperatura de referencia STC (°C) - para pérdidas por temperatura */
export const T_REF_STC = 25;

// ============================================================
// TABLAS DE REFERENCIA
// ============================================================

/** Factor de irradiación FI recomendado por región colombiana */
export const REGION_FI_TABLE: {
  region: string;
  key: string;
  tiltRecommended: number;
  fi: number;
  avgTemp: number;
  description: string;
}[] = [
  {
    region: 'Caribe',
    key: 'caribe',
    tiltRecommended: 10,
    fi: 0.98,
    avgTemp: 28,
    description: 'Baja latitud, alta irradiancia, inclinación mínima',
  },
  {
    region: 'Andina',
    key: 'andina',
    tiltRecommended: 10,
    fi: 0.95,
    avgTemp: 18,
    description: 'Altiplano, temperatura moderada, buena irradiancia',
  },
  {
    region: 'Pacífica',
    key: 'pacifica',
    tiltRecommended: 5,
    fi: 0.90,
    avgTemp: 26,
    description: 'Alta nubosidad, predomina irradiancia difusa',
  },
  {
    region: 'Orinoquía',
    key: 'orinoquia',
    tiltRecommended: 8,
    fi: 0.96,
    avgTemp: 27,
    description: 'Llanos, buena irradiancia, temperatura alta',
  },
  {
    region: 'Amazonía',
    key: 'amazonia',
    tiltRecommended: 5,
    fi: 0.88,
    avgTemp: 26,
    description: 'Selva húmeda, alta nubosidad, irradiancia moderada',
  },
  {
    region: 'Insular',
    key: 'insular',
    tiltRecommended: 12,
    fi: 1.00,
    avgTemp: 27,
    description: 'Islas, excelente irradiancia, mínima obstrucción',
  },
];

/** Tabla de factores de sombreado FS con descripciones */
export const SHADOW_FACTOR_TABLE: {
  fs: number;
  label: string;
  description: string;
  icon: string;
}[] = [
  { fs: 1.00, label: 'Sin sombras', description: 'Horizonte completamente despejado, sin obstrucciones', icon: '☀️' },
  { fs: 0.95, label: 'Sombras mínimas', description: 'Obstrucciones lejanas, < 5% de pérdida', icon: '🌤️' },
  { fs: 0.90, label: 'Sombras leves', description: 'Edificios lejanos o vegetación baja', icon: '⛅' },
  { fs: 0.85, label: 'Sombras moderadas', description: 'Edificios cercanos o árboles medianos', icon: '🌥️' },
  { fs: 0.80, label: 'Sombras significativas', description: 'Obstrucciones importantes en horas pico', icon: '☁️' },
  { fs: 0.70, label: 'Sombras severas', description: 'Entorno urbano denso o vegetación alta', icon: '🌧️' },
  { fs: 0.60, label: 'Sombras muy severas', description: 'Sombreado parcial constante durante el día', icon: '🌑' },
];

/** Tabla de referencia PR (Mulcue-Llanos) */
export const PR_REFERENCE_TABLE: {
  min: number;
  max: number;
  label: string;
  color: string;
  cause: string;
}[] = [
  { min: 0.80, max: 1.00, label: 'Óptimo', color: '#16a34a', cause: 'Mínimas pérdidas de sistema' },
  { min: 0.75, max: 0.80, label: 'Bueno', color: '#2563eb', cause: 'Pérdidas normales de operación' },
  { min: 0.65, max: 0.75, label: 'Medio', color: '#f59e0b', cause: 'Posible suciedad, temperatura alta' },
  { min: 0.50, max: 0.65, label: 'Problema serio', color: '#f97316', cause: 'Revisar sombras, módulos o inversor' },
  { min: 0.00, max: 0.50, label: 'Falla grave', color: '#dc2626', cause: 'Sombreado extremo o inversor apagado' },
];

// ============================================================
// FUNCIONES DE CÁLCULO
// ============================================================

/**
 * Calcula el Performance Ratio estimado según el modelo Mulcue-Llanos.
 *
 * PR_max = Ksist × (1 + γ × (1.12 × Ta - 10))
 * PR_C   = PR_max + 0.0006 × Ta - 0.017
 *
 * @param input Parámetros de entrada
 * @returns Resultado con PR_max, PR_C e interpretación
 */
export function calculateMulcuePR(input: MulcuePRInput): MulcuePRResult {
  const { tempCoeffGamma, ambientTemp, ksist = DEFAULT_KSIST } = input;

  // γ en el modelo se usa como valor decimal (ej: -0.0036 para -0.36%/°C)
  const gammaDecimal = Math.abs(tempCoeffGamma) <= 0.01
    ? tempCoeffGamma  // Ya está en decimal
    : tempCoeffGamma / 100;  // Convertir de %/°C a decimal

  const prMax = ksist * (1 + gammaDecimal * (1.12 * ambientTemp - 10));
  const prCorrected = prMax + 0.0006 * ambientTemp - 0.017;

  // Limitar a rango razonable
  const prFinal = Math.max(0.10, Math.min(0.95, prCorrected));

  // Interpretación
  let interpretation: MulcuePRResult['interpretation'];
  let description: string;
  let color: string;

  if (prFinal > 0.80) {
    interpretation = 'optimo';
    description = 'Óptimo — mínimas pérdidas de sistema';
    color = '#16a34a';
  } else if (prFinal >= 0.75) {
    interpretation = 'bueno';
    description = 'Bueno — pérdidas normales de operación';
    color = '#2563eb';
  } else if (prFinal >= 0.65) {
    interpretation = 'medio';
    description = 'Medio — posible suciedad o temperatura alta';
    color = '#f59e0b';
  } else if (prFinal >= 0.50) {
    interpretation = 'problema';
    description = 'Problema serio — revisar sombras, módulos o inversor';
    color = '#f97316';
  } else {
    interpretation = 'falla';
    description = 'Falla grave — sombreado extremo o inversor apagado';
    color = '#dc2626';
  }

  return {
    prMax: Math.round(prMax * 10000) / 10000,
    prCorrected: Math.round(prFinal * 10000) / 10000,
    interpretation,
    description,
    color,
  };
}

/**
 * Calcula la temperatura de celda según el modelo NOCT estándar (IEC 61215).
 *
 * T_cell = T_amb + (NOCT - 20) × (G / 800)
 *
 * Donde:
 * - T_amb: temperatura ambiente (°C)
 * - NOCT: Nominal Operating Cell Temperature del panel (°C), típico 43-47°C
 * - G: irradiancia incidente (W/m²)
 *
 * Para estimaciones anuales se usa G como irradiancia promedio en horas de sol.
 * Referencia: Fórmula 3 del Excel "calculadora_fotovoltaicaexcelopus.xlsx"
 *
 * @param ambientTemp Temperatura ambiente promedio (°C)
 * @param noct NOCT del panel (°C), por defecto 45°C
 * @param irradiance Irradiancia promedio durante horas de sol (W/m²), por defecto 800 W/m²
 * @returns Temperatura de celda estimada (°C)
 */
export function calculateCellTemp(
  ambientTemp: number,
  noct: number = DEFAULT_NOCT,
  irradiance: number = G_NOCT_REF,
): number {
  return ambientTemp + (noct - 20) * (irradiance / G_NOCT_REF);
}

/**
 * Calcula la pérdida de potencia por alta temperatura (%).
 *
 * P_loss = γ × (T_cell - 25°C)
 *
 * Referencia: Fórmula 3 del Excel: P_m = P_ref × [1 + γ(T_c − T_ref)]
 * Donde T_ref = 25°C (STC) y γ es negativo.
 *
 * @param cellTemp Temperatura de celda (°C)
 * @param tempCoeffGamma Coeficiente de temperatura (%/°C, valor negativo, ej: -0.26)
 * @returns Factor de corrección (0-1), ej: 0.92 significa 8% de pérdida
 */
export function calculateTempLossFactor(
  cellTemp: number,
  tempCoeffGamma: number,
): number {
  // γ puede venir como -0.26 (%/°C) o como -0.0026 (decimal)
  const gammaDecimal = Math.abs(tempCoeffGamma) > 0.01
    ? tempCoeffGamma / 100  // Convertir de %/°C a decimal (ej: -0.26 → -0.0026)
    : tempCoeffGamma;       // Ya está en decimal

  // Factor = 1 + γ × (T_cell - 25)
  // Ejemplo: 1 + (-0.0026) × (56 - 25) = 1 - 0.0806 = 0.9194
  const factor = 1 + gammaDecimal * (cellTemp - T_REF_STC);
  return Math.max(0.5, Math.min(1.0, factor));
}

/**
 * Calcula la producción energética según el modelo Mulcue-Llanos.
 *
 * G_a(α,β) = G_a(0) × FI × FS
 * HSP_total = G_a(α,β) × días
 * E_PV = HSP_total × P_pico(kW) × PR
 *
 * @param input Parámetros de entrada
 * @returns Resultado con energía producida y métricas intermedias
 */
export function calculateProduction(input: ProductionInput): ProductionResult {
  const {
    ghiDaily,
    irradiationFactor,
    shadowFactor,
    modulePower,
    moduleCount,
    pr,
    days = 365,
  } = input;

  // Irradiación corregida (HSP/día)
  const gaCorr = ghiDaily * irradiationFactor * shadowFactor;

  // HSP total del período
  const hspTotal = gaCorr * days;

  // Potencia pico instalada
  const peakPowerKw = (moduleCount * modulePower) / 1000;

  // Energía producida
  const energyKwh = hspTotal * peakPowerKw * pr;

  return {
    gaCorr: Math.round(gaCorr * 10000) / 10000,
    hspTotal: Math.round(hspTotal * 100) / 100,
    peakPowerKw: Math.round(peakPowerKw * 100) / 100,
    energyKwh: Math.round(energyKwh * 100) / 100,
    energyMwh: Math.round((energyKwh / 1000) * 100) / 100,
    days,
  };
}

/**
 * Diagnóstico de módulo fotovoltaico según modelo Mulcue-Llanos.
 *
 * Factor_temp = 1 - (-γ/100) × (T_celda - 21)
 * P_temp = P_nom × Factor_temp
 * P_exp = P_temp × (G / 1000)
 * Rendimiento = P_real / P_exp
 * η_real = η_ideal × Rendimiento
 *
 * NOTA: Usa T_ref = 21°C (modelo Mulcue-Llanos), no 25°C (STC estándar)
 */
export function calculateDiagnostic(input: DiagnosticInput): DiagnosticResult {
  const {
    nominalPower,
    tempCoeffGamma,
    irradiance,
    cellTemp,
    realPower,
    idealEfficiency,
  } = input;

  // Factor de corrección por temperatura (T_ref = 21°C en Mulcue-Llanos)
  const gammaAbs = Math.abs(tempCoeffGamma);
  const tempFactor = 1 - (gammaAbs / 100) * (cellTemp - MULCUE_T_REF);

  // Potencia corregida por temperatura
  const tempCorrectedPower = nominalPower * tempFactor;

  // Potencia esperada (corregida por irradiancia y temperatura)
  const expectedPower = tempCorrectedPower * (irradiance / 1000);

  // Rendimiento
  const performance = expectedPower > 0 ? realPower / expectedPower : 0;

  // Eficiencia real
  const realEfficiency = idealEfficiency * performance;

  // Interpretación
  let interpretation: string;
  let color: string;

  if (performance >= 0.90) {
    interpretation = 'Buen rendimiento (≥ 90%) — módulo funcionando correctamente';
    color = '#16a34a';
  } else if (performance >= 0.75) {
    interpretation = 'Rendimiento aceptable (75–90%) — vigilar evolución';
    color = '#f59e0b';
  } else {
    interpretation = 'Rendimiento bajo (< 75%) — revisar módulo, inversor o sombras';
    color = '#dc2626';
  }

  return {
    tempFactor: Math.round(tempFactor * 10000) / 10000,
    tempCorrectedPower: Math.round(tempCorrectedPower * 1000) / 1000,
    expectedPower: Math.round(expectedPower * 1000) / 1000,
    performance: Math.round(performance * 10000) / 10000,
    realEfficiency: Math.round(realEfficiency * 100) / 100,
    interpretation,
    color,
  };
}

/**
 * Calcula la potencia esperada del módulo según modelo Mulcue-Llanos.
 *
 * P_exp = P_nom × [1 + γ(T_c − 21)] × (G / 1000)
 *
 * Donde:
 * - P_nom: Potencia nominal STC del módulo (W)
 * - γ: Coeficiente de temperatura (%/°C, valor negativo, ej: -0.36)
 * - T_c: Temperatura de celda (°C)
 * - T_ref = 21°C (modelo Mulcue-Llanos, NO 25°C STC)
 * - G: Irradiancia incidente (W/m²)
 *
 * Esta fórmula aplica simultáneamente:
 * 1. Degradación por alta temperatura respecto a T_ref=21°C
 * 2. Corrección por irradiancia respecto a STC (1000 W/m²)
 *
 * @param nominalPowerW Potencia nominal STC del módulo (W)
 * @param tempCoeffGamma Coeficiente de temperatura (%/°C, negativo, ej: -0.36)
 * @param cellTemp Temperatura de celda (°C)
 * @param irradiance Irradiancia incidente (W/m²)
 * @returns Potencia esperada del módulo (W)
 */
export function calculateExpectedPower(
  nominalPowerW: number,
  tempCoeffGamma: number,
  cellTemp: number,
  irradiance: number = G_STC,
): number {
  // γ puede venir como -0.36 (%/°C) o como -0.0036 (decimal)
  const gammaDecimal = Math.abs(tempCoeffGamma) > 0.01
    ? tempCoeffGamma / 100  // Convertir de %/°C a decimal (ej: -0.36 → -0.0036)
    : tempCoeffGamma;       // Ya está en decimal

  // Factor de temperatura con T_ref = 21°C (Mulcue-Llanos)
  const tempFactor = 1 + gammaDecimal * (cellTemp - MULCUE_T_REF);

  // Factor de irradiancia respecto a STC
  const irradianceFactor = irradiance / G_STC;

  // Potencia esperada
  return nominalPowerW * tempFactor * irradianceFactor;
}

/**
 * Obtiene el factor FI recomendado para una región colombiana.
 */
export function getRegionFI(regionKey: string): typeof REGION_FI_TABLE[0] | undefined {
  return REGION_FI_TABLE.find(r => r.key === regionKey);
}

/**
 * Estimación rápida completa: dado un punto PVGIS y un panel,
 * calcula PR (Mulcue-Llanos) y producción anual estimada.
 */
export function quickEstimate(params: {
  ghiAnnualKwhM2: number;  // GHI anual del punto PVGIS (kWh/m²/año)
  ambientTemp: number;     // Temperatura ambiente promedio (°C)
  tempCoeffGamma: number;  // Coef. temperatura del panel (%/°C, negativo)
  modulePowerW: number;    // Potencia nominal del módulo (W)
  moduleCount: number;     // Cantidad de módulos
  regionKey: string;       // Clave de región colombiana
  shadowFactor: number;    // Factor de sombreado FS (0-1)
  noct?: number;           // NOCT del panel (°C), por defecto 45°C
  avgIrradiance?: number;  // Irradiancia promedio en horas de sol (W/m²), por defecto 800
}): {
  pr: MulcuePRResult;
  production: ProductionResult;
  cellTemp: number;
  tempLossFactor: number;
  tempLossPercent: number;
  regionInfo: typeof REGION_FI_TABLE[0] | undefined;
  pExp: number;
  pExpTotal: number;
  pNom: number;
  pNomTotal: number;
  tempDegradation: number;
} {
  const regionInfo = getRegionFI(params.regionKey);
  const fi = regionInfo?.fi ?? 0.95;
  const noct = params.noct ?? DEFAULT_NOCT;
  const avgIrradiance = params.avgIrradiance ?? G_NOCT_REF;

  // Convertir GHI anual a diario
  const ghiDaily = params.ghiAnnualKwhM2 / 365;

  // Calcular PR con Mulcue-Llanos
  const pr = calculateMulcuePR({
    tempCoeffGamma: params.tempCoeffGamma,
    ambientTemp: params.ambientTemp,
  });

  // Temperatura de celda con modelo NOCT estándar IEC
  const cellTemp = calculateCellTemp(params.ambientTemp, noct, avgIrradiance);

  // Factor de pérdida por alta temperatura
  const tempLossFactor = calculateTempLossFactor(cellTemp, params.tempCoeffGamma);
  const tempLossPercent = (1 - tempLossFactor) * 100;

  // Calcular P_exp = P_nom × [1 + γ(T_c − 21)] × (G/1000)
  // Potencia esperada del módulo degradada por temperatura y ajustada por irradiancia
  const pExp = calculateExpectedPower(
    params.modulePowerW,
    params.tempCoeffGamma,
    cellTemp,
    avgIrradiance,
  );

  // Calcular producción usando P_exp (potencia degradada) en vez de P_nom
  const production = calculateProduction({
    ghiDaily,
    irradiationFactor: fi,
    shadowFactor: params.shadowFactor,
    modulePower: pExp,  // ← Usa P_exp (degradada por T° e irradiancia) en vez de P_nom
    moduleCount: params.moduleCount,
    pr: pr.prCorrected,
  });

  return {
    pr,
    production,
    cellTemp,
    tempLossFactor,
    tempLossPercent,
    regionInfo,
    pExp,                                                    // Potencia esperada por módulo (W)
    pExpTotal: pExp * params.moduleCount,                    // Potencia esperada total (W)
    pNom: params.modulePowerW,                               // Potencia nominal STC (W)
    pNomTotal: params.modulePowerW * params.moduleCount,     // Potencia nominal total (W)
    tempDegradation: (1 - pExp / (params.modulePowerW * (avgIrradiance / G_STC))) * 100,  // % degradación solo por T°
  };
}
