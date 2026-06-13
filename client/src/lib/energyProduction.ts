/**
 * Simulador de Producción Energética Fotovoltaica
 * Calcula kWh anuales considerando radiación POA, eficiencia y pérdidas del sistema
 * 
 * Referencias:
 * - IEC 61724-1:2017 - Photovoltaic system performance monitoring
 * - IEC 61724-1:2021 Ed.2 - Weather-corrected Performance Ratio
 * - PVsyst Simulation Software Documentation
 * - NREL Performance Model Documentation
 * - Sandia PV Performance Modeling Collaborative (PVPMC)
 */

export interface PanelSpecifications {
  powerRating: number; // Potencia nominal del panel (W)
  efficiency: number; // Eficiencia nominal del panel (%)
  temperatureCoefficient: number; // Coeficiente de temperatura (%/°C)
  nominalOperatingCellTemperature: number; // NOCT (°C)
  area: number; // Área del panel (m²)
  quantity: number; // Cantidad de paneles
}

export interface SystemLosses {
  dcWiring: number; // Pérdidas en cableado DC (%)
  inverterEfficiency: number; // Eficiencia del inversor (%)
  acWiring: number; // Pérdidas en cableado AC (%)
  transformerLosses: number; // Pérdidas en transformador (%)
  mismatchLosses: number; // Pérdidas por desajuste (%)
  soilingLosses: number; // Pérdidas por suciedad (%)
  shadingLosses: number; // Pérdidas por sombreado (%)
  availabilityLosses: number; // Pérdidas por disponibilidad (%)
  iamLosses: number; // Pérdidas por IAM ASHRAE - Incidence Angle Modifier (%)
}

export interface MonthlyProduction {
  month: string;
  avgTemp: number;
  avgPOA: number; // POA efectivo después de sombreado (W/m²)
  rawPOA: number; // POA antes de sombreado (W/m²) — para cálculo de Yr
  H_i_m: number; // Irradiación mensual POA (kWh/m²/mes) — para Yr IEC 61724
  cellTemperature: number;
  panelEfficiency: number;
  dcPower: number;
  acPower: number;
  energyProduced: number; // kWh AC
  dcEnergy: number; // kWh DC
  referenceEnergy: number; // kWh referencia STC (para PR)
  losses: {
    temperature: number; // %
    dcWiring: number; // %
    inverter: number; // %
    acWiring: number; // %
    mismatch: number; // %
    soiling: number; // %
    shading: number; // %
    availability: number; // %
    iam: number; // % - IAM ASHRAE (Incidence Angle Modifier)
  };
}

/**
 * Métricas IEC 61724 completas
 */
export interface CaptureLossesBreakdown {
  /** Lc_temp: pérdidas por temperatura en horas equivalentes */
  temperature: number;
  /** Lc_sombra: pérdidas por sombreado en horas equivalentes */
  shading: number;
  /** Lc_suciedad: pérdidas por suciedad en horas equivalentes */
  soiling: number;
  /** Lc_mismatch: pérdidas por desajuste entre módulos en horas equivalentes */
  mismatch: number;
  /** Lc_dcWiring: pérdidas en cableado DC en horas equivalentes */
  dcWiring: number;
  /** Lc_iam: pérdidas por IAM (Incidence Angle Modifier) en horas equivalentes */
  iam: number;
  /** Total = suma de todas las Capture Losses (debe ≈ Lc) */
  total: number;
}

export interface IEC61724Metrics {
  /** Reference Yield: Yr = H_POA / G_ref (horas equivalentes) */
  referenceYield: number;
  /** Final Yield: Yf = E_AC / P_nom (kWh/kWp) */
  finalYield: number;
  /** Array Yield: Ya = E_DC / P_nom (kWh/kWp) */
  arrayYield: number;
  /** Capture Losses: Lc = Yr - Ya (horas) */
  captureLosses: number;
  /** Desglose de Capture Losses por categoría (IEC 61724) */
  captureLossesBreakdown: CaptureLossesBreakdown;
  /** System Losses: Ls = Ya - Yf (horas) */
  systemLosses: number;
  /** Performance Ratio: PR = Yf / Yr (0-1) */
  performanceRatio: number;
  /** PR corregido por temperatura: PR_T (IEC 61724-1:2021) */
  prTemperatureCorrected: number;
  /** Specific Yield: kWh/kWp/año */
  specificYield: number;
  /** BOS Efficiency: E_AC / E_DC (0-1) */
  bosEfficiency: number;
  /** Energy Performance Index: EPI = E_AC_simulador / E_AC_benchmark (IEC 61724-1:2021) */
  energyPerformanceIndex: number | null;
}

export interface AnnualProduction {
  totalDCEnergy: number; // kWh
  totalACEnergy: number; // kWh
  totalReferenceEnergy: number; // kWh referencia STC
  systemEfficiency: number; // % (BOS efficiency)
  performanceRatio: number; // % (IEC 61724)
  prTemperatureCorrected: number; // % (PR_T IEC 61724-1:2021)
  capacityFactor: number; // %
  specificYield: number; // kWh/kWp/año
  iec61724: IEC61724Metrics;
  monthlyData: MonthlyProduction[];
  losses: {
    temperature: number; // %
    dcWiring: number; // %
    inverter: number; // %
    acWiring: number; // %
    mismatch: number; // %
    soiling: number; // %
    shading: number; // %
    availability: number; // %
    iam: number; // % - IAM (Incidence Angle Modifier)
    total: number; // %
  };
}

/**
 * Calcula la temperatura de la célula solar basada en temperatura ambiente
 * Usando modelo NOCT (Nominal Operating Cell Temperature)
 * Ref: IEC 61215 / Sandia PV Performance Model
 * 
 * T_cell = T_amb + (NOCT - 20) × (G / 800) × (1 - η_real) × windFactor
 * windFactor = 1 / (1 + 0.05 × windSpeed) — viento enfría el panel
 */
export const calculateCellTemperature = (
  ambientTemp: number, // °C
  poaIrradiance: number, // W/m²
  windSpeed: number = 1, // m/s
  noct: number = 47, // °C
  panelEfficiency: number = 15 // % eficiencia real del panel
): number => {
  const windFactor = 1 / (1 + 0.05 * Math.max(0, windSpeed));
  const eta = panelEfficiency / 100;
  const cellTemp = ambientTemp + ((noct - 20) * (poaIrradiance / 800)) * (1 - eta) * windFactor;
  return cellTemp;
};

/**
 * Calcula la eficiencia del panel considerando temperatura
 */
export const calculatePanelEfficiency = (
  nominalEfficiency: number, // %
  cellTemperature: number, // °C
  referenceTemperature: number = 25, // °C
  temperatureCoefficient: number = -0.004 // %/°C
): number => {
  const efficiency = nominalEfficiency * (1 + temperatureCoefficient * (cellTemperature - referenceTemperature));
  return Math.max(0, efficiency);
};

/**
 * Calcula la potencia DC generada por los paneles
 */
export const calculateDCPower = (
  poaIrradiance: number, // W/m²
  panelSpecs: PanelSpecifications,
  cellTemperature: number // °C
): number => {
  const panelEfficiency = calculatePanelEfficiency(
    panelSpecs.efficiency,
    cellTemperature,
    25,
    panelSpecs.temperatureCoefficient
  );
  const totalArea = panelSpecs.area * panelSpecs.quantity;
  const dcPower = (poaIrradiance * totalArea * panelEfficiency) / 100;
  return Math.max(0, dcPower);
};

/**
 * Calcula la potencia AC considerando pérdidas del sistema
 */
export const calculateACPower = (
  dcPower: number, // W
  systemLosses: SystemLosses
): number => {
  let power = dcPower;
  power *= (1 - systemLosses.dcWiring / 100);
  power *= (systemLosses.inverterEfficiency / 100);
  power *= (1 - systemLosses.acWiring / 100);
  power *= (1 - systemLosses.transformerLosses / 100);
  power *= (1 - systemLosses.mismatchLosses / 100);
  power *= (1 - systemLosses.soilingLosses / 100);
  power *= (1 - systemLosses.shadingLosses / 100);
  power *= (1 - systemLosses.availabilityLosses / 100);
  power *= (1 - (systemLosses.iamLosses || 0) / 100);
  return Math.max(0, power);
};

/**
 * Calcula la producción mensual de energía
 * Ahora incluye rawPOA, dcEnergy y referenceEnergy para cálculo IEC 61724
 */
export const calculateMonthlyProduction = (
  month: string,
  monthNumber: number,
  avgTemp: number, // °C
  avgPOA: number, // W/m² (POA antes de sombreado)
  avgWindSpeed: number, // m/s
  panelSpecs: PanelSpecifications,
  systemLosses: SystemLosses,
  daysInMonth: number,
  shadingFactor: number = 1.0,
  cellTempOverride?: number,
  /** POA original antes de pérdidas pre-cálculo (IAM/soiling). Si se proporciona, se usa para Yr (IEC 61724) */
  rawPOAOverride?: number,
  H_i_m?: number
): MonthlyProduction => {
  // POA para Reference Yield IEC 61724: usar el original (antes de IAM/soiling) si está disponible
  const rawPOA = rawPOAOverride !== undefined ? rawPOAOverride : avgPOA;
  
  // Ajustar POA por sombreado
  const adjustedPOA = avgPOA * shadingFactor;

  // Calcular temperatura de la célula
  const cellTemp = cellTempOverride !== undefined
    ? cellTempOverride
    : calculateCellTemperature(
        avgTemp,
        adjustedPOA,
        avgWindSpeed,
        panelSpecs.nominalOperatingCellTemperature,
        panelSpecs.efficiency
      );

  // Calcular eficiencia del panel con coeficiente de temperatura real
  const panelEfficiency = calculatePanelEfficiency(
    panelSpecs.efficiency,
    cellTemp,
    25,
    panelSpecs.temperatureCoefficient
  );

  // Calcular potencia DC
  const dcPower = calculateDCPower(adjustedPOA, panelSpecs, cellTemp);

  // Calcular potencia AC
  const acPower = calculateACPower(dcPower, systemLosses);

  // Calcular energía (kWh)
  const solarHoursMonth = (H_i_m ?? (rawPOA * daysInMonth * 24 / 1000)) / (rawPOA > 0 ? rawPOA / 1000 : 1);
  const dcEnergy = (dcPower * solarHoursMonth) / 1000; // kWh
  const acEnergy = (acPower * solarHoursMonth) / 1000; // kWh

  // Energía de referencia STC: lo que produciría el sistema a eficiencia nominal
  const installedCapacityW = panelSpecs.powerRating * panelSpecs.quantity;
  const referenceEnergy = (rawPOA / 1000) * (installedCapacityW / 1000) * solarHoursMonth; // kWh

  // Calcular pérdidas individuales
  const losses = {
    temperature: ((panelSpecs.efficiency - panelEfficiency) / panelSpecs.efficiency) * 100,
    dcWiring: systemLosses.dcWiring,
    inverter: 100 - systemLosses.inverterEfficiency,
    acWiring: systemLosses.acWiring,
    mismatch: systemLosses.mismatchLosses,
    soiling: systemLosses.soilingLosses,
    shading: (1 - shadingFactor) * 100,
    availability: systemLosses.availabilityLosses,
    iam: systemLosses.iamLosses || 0,
  };

  return {
    month,
    avgTemp,
    avgPOA: adjustedPOA,
    rawPOA,
    H_i_m: H_i_m ?? (rawPOA * daysInMonth * 24) / 1000,
    cellTemperature: cellTemp,
    panelEfficiency,
    dcPower,
    acPower,
    energyProduced: acEnergy,
    dcEnergy,
    referenceEnergy,
    losses,
  };
};

/**
 * Calcula la producción anual completa con métricas IEC 61724
 * 
 * PR IEC 61724: PR = Yf / Yr = E_AC / (H_POA × P_nom / G_ref)
 * 
 * Donde:
 * - Yf (Final Yield) = E_AC / P_nom (kWh/kWp)
 * - Yr (Reference Yield) = H_POA / G_ref (horas equivalentes)
 * - Ya (Array Yield) = E_DC / P_nom (kWh/kWp)
 * - Lc (Capture Losses) = Yr - Ya
 * - Ls (System Losses) = Ya - Yf
 * - PR_T (Temperature-corrected PR) = PR / (1 + γ × (T_cell_avg - 25))
 */
export const calculateAnnualProduction = (
  monthlyPOAData: Array<{
    month: string;
    avgPOA: number;
    avgTemp: number;
    avgWindSpeed?: number;
    /** Componente directa del POA (W/m²) — para aplicación horaria de IAM */
    directPOA?: number;
    /** Componente difusa del POA (W/m²) — no afectada por IAM */
    diffusePOA?: number;
    /** Componente reflejada del POA (W/m²) — no afectada por IAM */
    reflectedPOA?: number;
    H_i_m?: number;
  }>,
  panelSpecs: PanelSpecifications,
  systemLosses: SystemLosses,
  shadingFactors: number[] = Array(12).fill(1.0),
  cellTempOverride?: number,
  /** IAM mensual variable: 12 valores de pérdida % por mes (si se proporciona, se aplica PRE-cálculo sobre componente directa) */
  iamMensual?: number[],
  /** Soiling mensual variable: 12 valores de pérdida % por mes (si se proporciona, se aplica PRE-cálculo sobre POA total) */
  soilingMensual?: number[]
): AnnualProduction => {
  const daysInMonths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const monthlyData: MonthlyProduction[] = [];

  let totalDCEnergy = 0;
  let totalACEnergy = 0;
  let totalReferenceEnergy = 0;

  // Para pérdidas ponderadas por energía
  let weightedLosses = {
    temperature: 0,
    dcWiring: 0,
    inverter: 0,
    acWiring: 0,
    mismatch: 0,
    soiling: 0,
    shading: 0,
    availability: 0,
    iam: 0,
  };

  // Para PR_T: acumular T_cell ponderada por irradiancia
  let weightedCellTemp = 0;
  let totalIrradianceWeight = 0;

  // Determinar si IAM/soiling se aplican pre-cálculo (sobre POA) o post-cálculo (sobre AC)
  const usePreCalcIAM = !!(iamMensual && iamMensual.length === 12);
  const usePreCalcSoiling = !!(soilingMensual && soilingMensual.length === 12);

  monthlyPOAData.forEach((data, idx) => {
    // === APLICACIÓN PRE-CÁLCULO DE IAM Y SOILING (como motor BIPV) ===
    // IAM se aplica SOLO a la componente directa del POA
    // Soiling se aplica al POA total (afecta toda la superficie)
    let effectivePOA = data.avgPOA;

    if (usePreCalcIAM && data.directPOA !== undefined && data.diffusePOA !== undefined) {
      // Aplicar IAM solo a componente directa (como hace el motor BIPV)
      const iamLossFraction = iamMensual![idx] / 100;
      const directAfterIAM = data.directPOA * (1 - iamLossFraction);
      const reflected = data.reflectedPOA || (data.avgPOA - data.directPOA - data.diffusePOA);
      effectivePOA = directAfterIAM + data.diffusePOA + reflected;
    } else if (usePreCalcIAM) {
      // Fallback: si no hay componentes separadas, aplicar IAM al total
      const iamLossFraction = iamMensual![idx] / 100;
      effectivePOA = data.avgPOA * (1 - iamLossFraction);
    }

    if (usePreCalcSoiling) {
      // Soiling se aplica al POA total (suciedad cubre toda la superficie)
      const soilingLossFraction = soilingMensual![idx] / 100;
      effectivePOA = effectivePOA * (1 - soilingLossFraction);
    }

    // Crear systemLosses SIN IAM/soiling post-cálculo cuando se usa pre-cálculo
    // para evitar doble conteo
    let monthSystemLosses: SystemLosses = {
      ...systemLosses,
      iamLosses: usePreCalcIAM ? 0 : systemLosses.iamLosses,
      soilingLosses: usePreCalcSoiling ? 0 : systemLosses.soilingLosses,
    };

    // POA original antes de IAM/soiling para cálculo de Yr (IEC 61724)
    // Solo se pasa cuando hay pérdidas pre-cálculo aplicadas, para que Yr refleje
    // la irradiación total disponible (antes de IAM+soiling)
    const originalPOA = (usePreCalcIAM || usePreCalcSoiling) ? data.avgPOA : undefined;

    const monthly = calculateMonthlyProduction(
      data.month,
      idx + 1,
      data.avgTemp,
      effectivePOA,
      data.avgWindSpeed || 1,
      panelSpecs,
      monthSystemLosses,
      daysInMonths[idx],
      shadingFactors[idx],
      cellTempOverride,
      originalPOA,
      data.H_i_m
    );

    // Sobreescribir H_i_m con el valor real de PVGIS si está disponible
    if (data.H_i_m !== undefined) monthly.H_i_m = data.H_i_m;

    monthlyData.push(monthly);
    totalDCEnergy += monthly.dcEnergy;
    totalACEnergy += monthly.energyProduced;
    totalReferenceEnergy += monthly.referenceEnergy;

    // Pérdidas ponderadas por energía de referencia mensual
    const weight = monthly.referenceEnergy;
    weightedLosses.temperature += monthly.losses.temperature * weight;
    weightedLosses.dcWiring += monthly.losses.dcWiring * weight;
    weightedLosses.inverter += monthly.losses.inverter * weight;
    weightedLosses.acWiring += monthly.losses.acWiring * weight;
    weightedLosses.mismatch += monthly.losses.mismatch * weight;
    // Para soiling e IAM: reportar el valor real aplicado (pre-cálculo) aunque no esté en monthSystemLosses
    const realSoilingLoss = usePreCalcSoiling ? soilingMensual![idx] : monthly.losses.soiling;
    weightedLosses.soiling += realSoilingLoss * weight;
    weightedLosses.shading += monthly.losses.shading * weight;
    weightedLosses.availability += monthly.losses.availability * weight;
    // IAM: reportar el valor real aplicado (pre-cálculo) aunque no esté en monthSystemLosses
    const realIAMLoss = usePreCalcIAM ? iamMensual![idx] : monthly.losses.iam;
    weightedLosses.iam += realIAMLoss * weight;

    // T_cell ponderada por irradiancia para PR_T
    const irradianceWeight = monthly.rawPOA * daysInMonths[idx] * 24;
    weightedCellTemp += monthly.cellTemperature * irradianceWeight;
    totalIrradianceWeight += irradianceWeight;
  });

  // Normalizar pérdidas ponderadas
  const totalWeight = totalReferenceEnergy > 0 ? totalReferenceEnergy : 1;
  const losses = {
    temperature: weightedLosses.temperature / totalWeight,
    dcWiring: weightedLosses.dcWiring / totalWeight,
    inverter: weightedLosses.inverter / totalWeight,
    acWiring: weightedLosses.acWiring / totalWeight,
    mismatch: weightedLosses.mismatch / totalWeight,
    soiling: weightedLosses.soiling / totalWeight,
    shading: weightedLosses.shading / totalWeight,
    availability: weightedLosses.availability / totalWeight,
    iam: weightedLosses.iam / totalWeight,
    total: 0,
  };

  // ===== MÉTRICAS IEC 61724 =====
  const installedCapacityKw = (panelSpecs.powerRating * panelSpecs.quantity) / 1000;
  const G_REF = 1000; // W/m² (irradiancia de referencia STC)

  // Reference Yield: Yr = H_POA / G_ref
  // H_POA = Σ(POA_raw_i × horas_i) en Wh/m², dividido por 1000 para kWh/m²
  const totalPOAIrradiation = monthlyData.reduce((sum, m, idx) => {
    return sum + (m.H_i_m ?? (m.rawPOA * daysInMonths[idx] * 24) / 1000); // kWh/m²
  }, 0);
  const referenceYield = totalPOAIrradiation / (G_REF / 1000); // horas equivalentes = kWh/m² / (kW/m²)

  // Final Yield: Yf = E_AC / P_nom
  const finalYield = installedCapacityKw > 0 ? totalACEnergy / installedCapacityKw : 0;

  // Array Yield: Ya = E_DC / P_nom
  const arrayYield = installedCapacityKw > 0 ? totalDCEnergy / installedCapacityKw : 0;

  // Capture Losses: Lc = Yr - Ya (pérdidas en el array: temperatura, sombreado, suciedad, mismatch)
  const captureLosses = referenceYield - arrayYield;

  // System Losses: Ls = Ya - Yf (pérdidas del sistema: inversor, cableado, transformador)
  const systemLossesIEC = arrayYield - finalYield;

  // Performance Ratio IEC 61724: PR = Yf / Yr
  const performanceRatio = referenceYield > 0 ? (finalYield / referenceYield) : 0;

  // PR corregido por temperatura (IEC 61724-1:2021)
  // PR_T = PR / (1 + γ × (T_cell_avg_weighted - T_ref_STC))
  // Esto normaliza el PR para que sea independiente de la temperatura
  const avgCellTempWeighted = totalIrradianceWeight > 0
    ? weightedCellTemp / totalIrradianceWeight
    : 25;
  const gamma = panelSpecs.temperatureCoefficient; // %/°C (negativo, ej: -0.004)
  const tempCorrectionFactor = 1 + gamma * (avgCellTempWeighted - 25);
  const prTemperatureCorrected = tempCorrectionFactor !== 0
    ? performanceRatio / tempCorrectionFactor
    : performanceRatio;

  // BOS Efficiency: E_AC / E_DC
  const bosEfficiency = totalDCEnergy > 0 ? totalACEnergy / totalDCEnergy : 0;

  // Specific Yield: kWh/kWp/año (= Final Yield)
  const specificYield = finalYield;

  // Capacity Factor: E_AC / (P_nom × 8760)
  const capacityFactor = installedCapacityKw > 0
    ? (totalACEnergy / (installedCapacityKw * 8760)) * 100
    : 0;

  // Total losses = 1 - PR (en %)
  losses.total = (1 - performanceRatio) * 100;

  // System Efficiency = BOS efficiency (%)
  const systemEfficiency = bosEfficiency * 100;

  // ===== DESGLOSE DE CAPTURE LOSSES (IEC 61724) =====
  // Lc = Yr - Ya. Descomponemos Lc en sus componentes:
  // Lc_tipo = Yr × (pérdida_tipo_ponderada% / 100)
  // Las pérdidas de captura son las que ocurren ANTES del inversor (en el array DC)
  // Nota: cuando IAM/soiling se aplican pre-cálculo, Yr refleja el POA original
  // y las pérdidas IAM/soiling se incluyen explícitamente en el desglose
  const captureLossesBreakdown: CaptureLossesBreakdown = {
    temperature: referenceYield * (losses.temperature / 100),
    shading: referenceYield * (losses.shading / 100),
    soiling: referenceYield * (losses.soiling / 100),
    mismatch: referenceYield * (losses.mismatch / 100),
    dcWiring: referenceYield * (losses.dcWiring / 100),
    iam: referenceYield * (losses.iam / 100),
    total: 0,
  };
  captureLossesBreakdown.total = captureLossesBreakdown.temperature
    + captureLossesBreakdown.shading
    + captureLossesBreakdown.soiling
    + captureLossesBreakdown.mismatch
    + captureLossesBreakdown.dcWiring
    + captureLossesBreakdown.iam;

  const iec61724: IEC61724Metrics = {
    referenceYield,
    finalYield,
    arrayYield,
    captureLosses,
    captureLossesBreakdown,
    systemLosses: systemLossesIEC,
    performanceRatio,
    prTemperatureCorrected: Math.min(1, Math.max(0, prTemperatureCorrected)),
    specificYield,
    bosEfficiency,
    energyPerformanceIndex: null, // Se calcula externamente con datos PVWatts
  };

  return {
    totalDCEnergy,
    totalACEnergy,
    totalReferenceEnergy,
    systemEfficiency,
    performanceRatio: performanceRatio * 100, // % para compatibilidad UI
    prTemperatureCorrected: Math.min(100, Math.max(0, prTemperatureCorrected * 100)), // %
    capacityFactor,
    specificYield,
    iec61724,
    monthlyData,
    losses,
  };
};

/**
 * Calcula el ROI y payback period
 */
export const calculateFinancials = (
  annualACEnergy: number, // kWh
  systemCost: number, // USD
  electricityRate: number, // USD/kWh
  maintenanceCostAnnual: number = 0, // USD/año
  systemDegradation: number = 0.5 // %/año
): {
  annualRevenue: number;
  paybackPeriod: number;
  roi10Years: number;
  roi25Years: number;
} => {
  const annualRevenue = annualACEnergy * electricityRate;
  const paybackPeriod = systemCost / (annualRevenue - maintenanceCostAnnual);

  let roi10 = 0;
  for (let year = 1; year <= 10; year++) {
    const energyThisYear = annualACEnergy * Math.pow(1 - systemDegradation / 100, year - 1);
    roi10 += energyThisYear * electricityRate - maintenanceCostAnnual;
  }
  roi10 = ((roi10 - systemCost) / systemCost) * 100;

  let roi25 = 0;
  for (let year = 1; year <= 25; year++) {
    const energyThisYear = annualACEnergy * Math.pow(1 - systemDegradation / 100, year - 1);
    roi25 += energyThisYear * electricityRate - maintenanceCostAnnual;
  }
  roi25 = ((roi25 - systemCost) / systemCost) * 100;

  return {
    annualRevenue,
    paybackPeriod,
    roi10Years: roi10,
    roi25Years: roi25,
  };
};

// ===== PR_T HORARIO IEC 61724-1:2021 =====

/**
 * Registro horario genérico para cálculo de PR_T
 * Compatible con datos de PVWatts y PVGIS
 */
export interface HourlyRecord {
  month: number;       // 1-12
  poa_Wm2: number;     // Irradiancia POA (W/m²)
  tamb_C: number;      // Temperatura ambiente (°C)
  tcell_C?: number;    // Temperatura de celda (°C) - si está disponible
  wspd_ms?: number;    // Velocidad del viento (m/s)
  ac_W?: number;       // Potencia AC (W) - si viene del modelo externo
  dc_W?: number;       // Potencia DC (W) - si viene del modelo externo
}

/**
 * Resultado mensual del cálculo PR_T horario
 */
export interface MonthlyPR_T {
  month: number;           // 1-12
  monthName: string;
  pr: number;              // PR convencional (0-1)
  pr_t: number;            // PR_T corregido por temperatura (0-1)
  avgTcell: number;        // T_cell promedio ponderada por irradiancia (°C)
  avgTamb: number;         // T_amb promedio (°C)
  totalPOA_kWhm2: number;  // Irradiación POA total del mes (kWh/m²)
  totalAC_kWh: number;     // Energía AC total del mes (kWh)
  hoursWithSun: number;    // Horas con irradiancia > 0
  referenceYield: number;  // Yr mensual (horas eq.)
  finalYield: number;      // Yf mensual (kWh/kWp)
}

/**
 * Resultado completo del cálculo PR_T horario
 */
export interface HourlyPR_T_Result {
  /** PR_T anual (IEC 61724-1:2021) calculado paso a paso horario */
  annualPR_T: number;
  /** PR convencional anual calculado paso a paso horario */
  annualPR: number;
  /** Desglose mensual */
  monthly: MonthlyPR_T[];
  /** Fuente de datos */
  source: 'pvwatts' | 'pvgis';
  /** Número total de registros horarios procesados */
  totalRecords: number;
  /** Horas con irradiancia > umbral (50 W/m²) */
  sunHours: number;
  /** Temperatura de celda promedio anual ponderada por irradiancia */
  avgCellTempWeighted: number;
  /** Capacidad instalada usada en el cálculo (kW) */
  systemCapacity_kW: number;
}

const MONTH_NAMES_ES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

/**
 * Calcula PR_T paso a paso temporal según IEC 61724-1:2021
 * 
 * Fórmula IEC 61724-1:2021 Ed.2:
 * 
 *   PR_T = Σ(E_AC_h) / Σ(G_POA_h × A × η_ref × (1 + γ × (T_cell_h - T_ref)))
 * 
 * Simplificado con P_nom = A × η_ref × G_ref:
 * 
 *   PR_T = Σ(E_AC_h) / Σ((G_POA_h / G_ref) × P_nom × (1 + γ × (T_cell_h - 25)))
 * 
 * Donde:
 * - E_AC_h = energía AC en la hora h (Wh)
 * - G_POA_h = irradiancia POA en la hora h (W/m²)
 * - G_ref = 1000 W/m² (STC)
 * - P_nom = potencia nominal del sistema (W)
 * - γ = coeficiente de temperatura del panel (%/°C, valor negativo)
 * - T_cell_h = temperatura de celda en la hora h (°C)
 * - T_ref = 25°C (STC)
 * 
 * El umbral de irradiancia es 50 W/m² (IEC 61724 recomienda excluir horas nocturnas
 * y de muy baja irradiancia para evitar divisiones por valores cercanos a cero).
 * 
 * @param hourlyRecords - Array de registros horarios (8760 para un año TMY)
 * @param systemCapacity_kW - Capacidad nominal del sistema (kW DC)
 * @param gamma - Coeficiente de temperatura (%/°C, ej: -0.004 para -0.4%/°C)
 * @param noct - NOCT del panel (°C) - usado si tcell_C no está disponible
 * @param panelEfficiency - Eficiencia nominal del panel (%) - para cálculo de T_cell
 * @param source - Fuente de datos ('pvwatts' | 'pvgis')
 */
export function calculatePR_T_Hourly(
  hourlyRecords: HourlyRecord[],
  systemCapacity_kW: number,
  gamma: number,
  noct: number = 47,
  panelEfficiency: number = 20,
  source: 'pvwatts' | 'pvgis' = 'pvwatts'
): HourlyPR_T_Result {
  const G_REF = 1000; // W/m² (STC)
  const P_nom_W = systemCapacity_kW * 1000; // W
  const POA_THRESHOLD = 50; // W/m² - umbral mínimo IEC 61724

  // Acumuladores anuales
  let sumEAC = 0;           // Σ E_AC_h (Wh)
  let sumRefTempCorr = 0;   // Σ (G_POA_h/G_ref × P_nom × (1+γ×(ΔT)))
  let sumRef = 0;           // Σ (G_POA_h/G_ref × P_nom) para PR convencional
  let sunHours = 0;
  let weightedTcell = 0;
  let totalIrrWeight = 0;

  // Acumuladores mensuales (12 meses)
  const monthAcc = Array.from({ length: 12 }, () => ({
    sumEAC: 0,
    sumRefTempCorr: 0,
    sumRef: 0,
    sumTcell: 0,
    sumTamb: 0,
    sumPOA: 0,
    irrWeight: 0,
    sunHours: 0,
    count: 0,
  }));

  for (const rec of hourlyRecords) {
    // Filtrar horas nocturnas / muy baja irradiancia
    if (rec.poa_Wm2 < POA_THRESHOLD) continue;

    const mi = rec.month - 1; // 0-indexed
    if (mi < 0 || mi > 11) continue;

    // Temperatura de celda: usar la proporcionada o calcular con NOCT
    const tcell = rec.tcell_C !== undefined && rec.tcell_C !== 0
      ? rec.tcell_C
      : calculateCellTemperature(
          rec.tamb_C,
          rec.poa_Wm2,
          rec.wspd_ms ?? 1,
          noct,
          panelEfficiency
        );

    // Energía AC horaria (Wh): si viene del modelo externo, usar directamente
    // Si no, estimar con PR típico (esto es una aproximación)
    const eac_Wh = rec.ac_W !== undefined && rec.ac_W > 0
      ? rec.ac_W  // PVWatts ya da W promedio por hora = Wh
      : (rec.poa_Wm2 / G_REF) * P_nom_W * 0.80; // Estimación con PR=0.80

    // Referencia con corrección de temperatura
    const tempCorr = 1 + gamma * (tcell - 25);
    const refTempCorr = (rec.poa_Wm2 / G_REF) * P_nom_W * tempCorr;
    const ref = (rec.poa_Wm2 / G_REF) * P_nom_W;

    // Acumular anual
    sumEAC += eac_Wh;
    sumRefTempCorr += refTempCorr;
    sumRef += ref;
    sunHours++;
    weightedTcell += tcell * rec.poa_Wm2;
    totalIrrWeight += rec.poa_Wm2;

    // Acumular mensual
    monthAcc[mi].sumEAC += eac_Wh;
    monthAcc[mi].sumRefTempCorr += refTempCorr;
    monthAcc[mi].sumRef += ref;
    monthAcc[mi].sumTcell += tcell * rec.poa_Wm2;
    monthAcc[mi].sumTamb += rec.tamb_C;
    monthAcc[mi].sumPOA += rec.poa_Wm2;
    monthAcc[mi].irrWeight += rec.poa_Wm2;
    monthAcc[mi].sunHours++;
    monthAcc[mi].count++;
  }

  // PR_T anual
  const annualPR_T = sumRefTempCorr > 0 ? sumEAC / sumRefTempCorr : 0;
  const annualPR = sumRef > 0 ? sumEAC / sumRef : 0;
  const avgCellTempWeighted = totalIrrWeight > 0 ? weightedTcell / totalIrrWeight : 25;

  // Desglose mensual
  const monthly: MonthlyPR_T[] = monthAcc.map((acc, i) => {
    const pr = acc.sumRef > 0 ? acc.sumEAC / acc.sumRef : 0;
    const pr_t = acc.sumRefTempCorr > 0 ? acc.sumEAC / acc.sumRefTempCorr : 0;
    const avgTcell = acc.irrWeight > 0 ? acc.sumTcell / acc.irrWeight : 25;
    const avgTamb = acc.count > 0 ? acc.sumTamb / acc.count : 25;
    const totalPOA_kWhm2 = acc.sumPOA / 1000; // Wh/m² → kWh/m²
    const totalAC_kWh = acc.sumEAC / 1000; // Wh → kWh
    const referenceYield = acc.sumPOA / G_REF; // horas eq.
    const finalYield = systemCapacity_kW > 0 ? totalAC_kWh / systemCapacity_kW : 0;

    return {
      month: i + 1,
      monthName: MONTH_NAMES_ES[i],
      pr,
      pr_t,
      avgTcell,
      avgTamb,
      totalPOA_kWhm2,
      totalAC_kWh,
      hoursWithSun: acc.sunHours,
      referenceYield,
      finalYield,
    };
  });

  return {
    annualPR_T,
    annualPR,
    monthly,
    source,
    totalRecords: hourlyRecords.length,
    sunHours,
    avgCellTempWeighted,
    systemCapacity_kW,
  };
}
