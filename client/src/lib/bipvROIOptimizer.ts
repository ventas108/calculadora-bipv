/**
 * Motor de Optimización ROI para Vidrios Fotovoltaicos BIPV
 * 
 * Implementa:
 * - Análisis de sensibilidad multi-variable (inclinación, transparencia, orientación, montaje)
 * - Cálculo de ahorro HVAC por reducción de carga solar (SHGC)
 * - Comparación de alternativas arquitectónicas (fachada, pérgola, marquesina, cubierta)
 * - Escenarios de valorización energética (autoconsumo, inyección, net-metering)
 * - Incentivos tributarios (Ley 1715 Colombia, ITC, depreciación acelerada)
 * - Punto de equilibrio ROI y recomendaciones de optimización
 */

import { INSTALLATION_CONFIGS, InstallationConfig, estimateProductionFactor } from './installationConfigs';
import { BIPV_GLASS_CATALOG, TRANSPARENCY_LEVELS, THERMAL_MOUNTING_TYPES } from './bipvGlassCatalog';
import type { BIPVSimulationSummary } from './iamSoilingEngine';

// ─── Tipos ──────────────────────────────────────────────────────────────────

export interface BIPVCostAssumptions {
  /** Costo del vidrio BIPV por m² (USD) */
  glassCostPerM2: number;
  /** Costo de instalación por m² (USD) */
  installationCostPerM2: number;
  /** Costo del inversor por kWp (USD) */
  inverterCostPerKWp: number;
  /** Costo de cableado y BOS por m² (USD) */
  bosCostPerM2: number;
  /** Costo de vidrio convencional que se reemplaza por m² (USD) - ahorro */
  conventionalGlassCostPerM2: number;
  /** Mantenimiento anual (% del costo total) */
  maintenancePercent: number;
  /** Degradación anual del panel (%) */
  degradationPercent: number;
}

export interface EnergyValorizationParams {
  /** Tarifa eléctrica de compra (USD/kWh) */
  electricityBuyRate: number;
  /** Tarifa de inyección/venta (USD/kWh) - típicamente menor */
  electricitySellRate: number;
  /** % de autoconsumo (0-100) */
  selfConsumptionPercent: number;
  /** Escalamiento anual de tarifa eléctrica (%) */
  electricityEscalation: number;
}

export interface HVACSavingsParams {
  /** Factor SHGC del vidrio convencional que se reemplaza (0-1, típico 0.6-0.8) */
  conventionalSHGC: number;
  /** Factor SHGC del vidrio BIPV (depende de transparencia, típico 0.1-0.4) */
  bipvSHGC: number;
  /** Área de vidrio BIPV (m²) */
  area: number;
  /** Irradiancia solar anual en la superficie (kWh/m²/año) */
  annualPOA: number;
  /** COP del sistema de aire acondicionado */
  coolingCOP: number;
  /** Costo eléctrico (USD/kWh) */
  electricityRate: number;
  /** Meses con necesidad de refrigeración (1-12) */
  coolingMonths: number;
}

export interface IncentiveParams {
  /** Deducción fiscal por inversión (% del costo, ej: 50% Ley 1715 Colombia) */
  taxDeductionPercent: number;
  /** Depreciación acelerada (años, 0=no aplica) */
  acceleratedDepreciationYears: number;
  /** Tasa impositiva marginal (%) */
  marginalTaxRate: number;
  /** Exclusión de IVA (true/false) */
  vatExemption: boolean;
  /** Tasa de IVA (%) */
  vatRate: number;
  /** Exención de aranceles de importación (true/false) */
  importDutyExemption: boolean;
  /** Arancel de importación (%) */
  importDutyRate: number;
}

export interface ROIScenarioResult {
  /** Nombre del escenario */
  name: string;
  /** Descripción */
  description: string;
  /** Tipo de superficie */
  surfaceType: string;
  /** Icono */
  icon: string;
  /** Costo total del sistema (USD) */
  totalSystemCost: number;
  /** Ahorro neto por reemplazo de vidrio convencional (USD) */
  conventionalGlassSaving: number;
  /** Costo neto después de ahorros (USD) */
  netCost: number;
  /** Ingreso anual por energía (USD/año) */
  annualEnergyRevenue: number;
  /** Ahorro anual HVAC (USD/año) */
  annualHVACSaving: number;
  /** Ahorro por incentivos tributarios (USD, one-time) */
  incentiveSaving: number;
  /** Ingreso total anual (energía + HVAC) */
  totalAnnualBenefit: number;
  /** Payback simple (años) */
  paybackYears: number;
  /** ROI a 10 años (%) */
  roi10Years: number;
  /** ROI a 25 años (%) */
  roi25Years: number;
  /** LCOE (USD/kWh) */
  lcoe: number;
  /** VAN a 25 años con tasa de descuento 8% (USD) */
  npv25Years: number;
  /** TIR estimada (%) */
  irr: number;
  /** Producción anual estimada (kWh) */
  annualProduction: number;
  /** Producción por m² (kWh/m²) */
  productionPerM2: number;
  /** Área (m²) */
  area: number;
  /** Inclinación (°) */
  tilt: number;
  /** Azimut (°) */
  azimuth: number;
  /** Transparencia */
  transparency: number;
  /** Es viable (ROI 25 > 0) */
  isViable: boolean;
  /** Ranking de viabilidad (1=mejor) */
  rank: number;
}

export interface OptimizationRecommendation {
  type: 'architectural' | 'technical' | 'financial' | 'operational';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  impact: string;
  icon: string;
}

export interface SensitivityPoint {
  variable: string;
  value: number;
  label: string;
  roi25: number;
  payback: number;
  production: number;
}

// ─── Constantes por defecto ─────────────────────────────────────────────────

export const DEFAULT_BIPV_COSTS: BIPVCostAssumptions = {
  glassCostPerM2: 250,          // Vidrio BIPV CdTe semitransparente
  installationCostPerM2: 80,    // Instalación especializada BIPV
  inverterCostPerKWp: 200,      // Micro-inversores para BIPV
  bosCostPerM2: 45,             // Cableado, conectores, estructura
  conventionalGlassCostPerM2: 120, // Vidrio doble convencional que se reemplaza
  maintenancePercent: 1.0,      // 1% anual
  degradationPercent: 0.5,      // 0.5% degradación anual
};

export const DEFAULT_ENERGY_PARAMS: EnergyValorizationParams = {
  electricityBuyRate: 0.18,     // USD/kWh (tarifa Colombia comercial)
  electricitySellRate: 0.08,    // USD/kWh (inyección a red)
  selfConsumptionPercent: 70,   // 70% autoconsumo típico en edificio
  electricityEscalation: 3.5,   // 3.5% anual
};

export const DEFAULT_HVAC_PARAMS: Partial<HVACSavingsParams> = {
  conventionalSHGC: 0.65,       // Vidrio doble convencional
  coolingCOP: 3.2,              // COP típico split
  coolingMonths: 12,            // Tropical = todo el año
};

export const DEFAULT_INCENTIVES_COLOMBIA: IncentiveParams = {
  taxDeductionPercent: 50,      // Ley 1715/2014 - 50% deducción renta
  acceleratedDepreciationYears: 5, // Depreciación acelerada 5 años
  marginalTaxRate: 35,          // Tasa impositiva corporativa Colombia
  vatExemption: true,           // Exclusión IVA equipos FNCER
  vatRate: 19,                  // IVA Colombia
  importDutyExemption: true,    // Exención aranceles
  importDutyRate: 5,            // Arancel base
};

export const DEFAULT_INCENTIVES_NONE: IncentiveParams = {
  taxDeductionPercent: 0,
  acceleratedDepreciationYears: 0,
  marginalTaxRate: 25,
  vatExemption: false,
  vatRate: 19,
  importDutyExemption: false,
  importDutyRate: 5,
};

// ─── Funciones de Cálculo ───────────────────────────────────────────────────

/**
 * Calcula el SHGC efectivo del vidrio BIPV según transparencia
 * El vidrio BIPV absorbe parte de la radiación para generar electricidad,
 * reduciendo la ganancia solar al interior
 */
export function calculateBIPVSHGC(transparency: number): number {
  // SHGC = transmitancia solar directa + re-emisión térmica
  // Para vidrio BIPV: la parte opaca (1-τ) absorbe y convierte a electricidad
  // Solo la parte transparente (τ) transmite calor al interior
  // Factor de re-emisión interna ≈ 0.15 para vidrio doble
  const directTransmittance = transparency * 0.85; // τ × factor vidrio
  const reEmission = (1 - transparency) * 0.12;    // absorción × re-emisión
  return directTransmittance + reEmission;
}

/**
 * Calcula el ahorro anual en HVAC por reducción de carga solar
 */
export function calculateHVACSavings(params: HVACSavingsParams): number {
  const { conventionalSHGC, bipvSHGC, area, annualPOA, coolingCOP, electricityRate, coolingMonths } = params;
  
  // Reducción de ganancia solar (kWh térmicos/año)
  const solarGainReduction = area * annualPOA * (conventionalSHGC - bipvSHGC) * (coolingMonths / 12);
  
  // Ahorro eléctrico en refrigeración (kWh eléctricos)
  const electricitySaved = solarGainReduction / coolingCOP;
  
  // Ahorro monetario (USD/año)
  return electricitySaved * electricityRate;
}

/**
 * Calcula el ahorro por incentivos tributarios (one-time)
 */
export function calculateIncentiveSavings(
  totalCost: number,
  incentives: IncentiveParams
): number {
  let savings = 0;
  
  // Deducción fiscal (Ley 1715 Colombia: 50% deducción en renta)
  if (incentives.taxDeductionPercent > 0) {
    savings += totalCost * (incentives.taxDeductionPercent / 100) * (incentives.marginalTaxRate / 100);
  }
  
  // Exclusión IVA
  if (incentives.vatExemption) {
    savings += totalCost * (incentives.vatRate / 100) / (1 + incentives.vatRate / 100);
  }
  
  // Exención aranceles
  if (incentives.importDutyExemption) {
    // Solo aplica a componentes importados (~60% del costo)
    savings += totalCost * 0.6 * (incentives.importDutyRate / 100);
  }
  
  return savings;
}

/**
 * Calcula el flujo de caja anual con degradación y escalamiento de tarifa
 */
function calculateAnnualCashflow(
  year: number,
  baseEnergyRevenue: number,
  baseHVACSaving: number,
  maintenanceCost: number,
  degradation: number,
  electricityEscalation: number
): number {
  const degradationFactor = Math.pow(1 - degradation / 100, year - 1);
  const escalationFactor = Math.pow(1 + electricityEscalation / 100, year - 1);
  
  const energyRevenue = baseEnergyRevenue * degradationFactor * escalationFactor;
  const hvacSaving = baseHVACSaving * escalationFactor; // HVAC no degrada
  const maintenance = maintenanceCost * Math.pow(1.02, year - 1); // 2% inflación
  
  return energyRevenue + hvacSaving - maintenance;
}

/**
 * Calcula la TIR (Internal Rate of Return) usando método de bisección
 */
function calculateIRR(cashflows: number[]): number {
  let low = -0.5;
  let high = 2.0;
  
  for (let iter = 0; iter < 100; iter++) {
    const mid = (low + high) / 2;
    let npv = 0;
    for (let t = 0; t < cashflows.length; t++) {
      npv += cashflows[t] / Math.pow(1 + mid, t);
    }
    if (Math.abs(npv) < 0.01) return mid * 100;
    if (npv > 0) low = mid;
    else high = mid;
  }
  return ((low + high) / 2) * 100;
}

/**
 * Calcula el ingreso anual por energía considerando autoconsumo vs inyección
 */
function calculateEnergyRevenue(
  annualProduction: number,
  params: EnergyValorizationParams
): number {
  const selfConsumed = annualProduction * (params.selfConsumptionPercent / 100);
  const injected = annualProduction - selfConsumed;
  
  return selfConsumed * params.electricityBuyRate + injected * params.electricitySellRate;
}

/**
 * Ejecuta un escenario completo de ROI para una configuración dada
 */
export function runROIScenario(
  name: string,
  description: string,
  icon: string,
  surfaceType: string,
  annualProductionKwh: number,
  productionPerM2: number,
  area: number,
  tilt: number,
  azimuth: number,
  transparency: number,
  costs: BIPVCostAssumptions,
  energyParams: EnergyValorizationParams,
  hvacParams: HVACSavingsParams | null,
  incentives: IncentiveParams
): ROIScenarioResult {
  // Costo total del sistema
  const capacityKWp = (productionPerM2 * area) / 1200; // estimación de capacidad
  const totalSystemCost = 
    area * costs.glassCostPerM2 +
    area * costs.installationCostPerM2 +
    capacityKWp * costs.inverterCostPerKWp +
    area * costs.bosCostPerM2;
  
  // Ahorro por reemplazo de vidrio convencional
  const conventionalGlassSaving = area * costs.conventionalGlassCostPerM2;
  
  // Costo neto
  const netCost = totalSystemCost - conventionalGlassSaving;
  
  // Ingreso anual por energía
  const annualEnergyRevenue = calculateEnergyRevenue(annualProductionKwh, energyParams);
  
  // Ahorro HVAC
  const annualHVACSaving = hvacParams ? calculateHVACSavings(hvacParams) : 0;
  
  // Incentivos
  const incentiveSaving = calculateIncentiveSavings(totalSystemCost, incentives);
  
  // Beneficio total anual
  const totalAnnualBenefit = annualEnergyRevenue + annualHVACSaving;
  
  // Mantenimiento anual
  const maintenanceCost = totalSystemCost * (costs.maintenancePercent / 100);
  
  // Costo neto después de incentivos
  const effectiveNetCost = netCost - incentiveSaving;
  
  // Payback simple
  const netAnnualBenefit = totalAnnualBenefit - maintenanceCost;
  const paybackYears = netAnnualBenefit > 0 ? effectiveNetCost / netAnnualBenefit : 999;
  
  // ROI a 10 y 25 años con degradación y escalamiento
  let cumulative10 = 0;
  let cumulative25 = 0;
  const cashflows: number[] = [-effectiveNetCost];
  
  for (let year = 1; year <= 25; year++) {
    const cf = calculateAnnualCashflow(
      year,
      annualEnergyRevenue,
      annualHVACSaving,
      maintenanceCost,
      costs.degradationPercent,
      energyParams.electricityEscalation
    );
    cashflows.push(cf);
    if (year <= 10) cumulative10 += cf;
    cumulative25 += cf;
  }
  
  const roi10Years = ((cumulative10 - effectiveNetCost) / effectiveNetCost) * 100;
  const roi25Years = ((cumulative25 - effectiveNetCost) / effectiveNetCost) * 100;
  
  // VAN a 25 años (tasa descuento 8%)
  const discountRate = 0.08;
  let npv25 = -effectiveNetCost;
  for (let year = 1; year <= 25; year++) {
    npv25 += cashflows[year] / Math.pow(1 + discountRate, year);
  }
  
  // TIR
  const irr = calculateIRR(cashflows);
  
  // LCOE
  let totalEnergy = 0;
  let totalCostDiscounted = effectiveNetCost;
  for (let year = 1; year <= 25; year++) {
    const energyYear = annualProductionKwh * Math.pow(1 - costs.degradationPercent / 100, year - 1);
    totalEnergy += energyYear / Math.pow(1 + discountRate, year);
    totalCostDiscounted += maintenanceCost / Math.pow(1 + discountRate, year);
  }
  const lcoe = totalEnergy > 0 ? totalCostDiscounted / totalEnergy : 999;
  
  return {
    name,
    description,
    surfaceType,
    icon,
    totalSystemCost,
    conventionalGlassSaving,
    netCost,
    annualEnergyRevenue,
    annualHVACSaving,
    incentiveSaving,
    totalAnnualBenefit,
    paybackYears: Math.min(paybackYears, 99),
    roi10Years,
    roi25Years,
    lcoe,
    npv25Years: npv25,
    irr,
    annualProduction: annualProductionKwh,
    productionPerM2,
    area,
    tilt,
    azimuth,
    transparency,
    isViable: roi25Years > 0,
    rank: 0, // se asigna después de ordenar
  };
}

/**
 * Genera escenarios alternativos arquitectónicos a partir de los resultados BIPV
 */
export function generateArchitecturalAlternatives(
  currentResults: BIPVSimulationSummary[],
  area: number,
  tilt: number,
  azimuth: number,
  latitude: number,
  costs: BIPVCostAssumptions,
  energyParams: EnergyValorizationParams,
  incentives: IncentiveParams,
  coolingMonths: number = 12
): ROIScenarioResult[] {
  const scenarios: ROIScenarioResult[] = [];
  
  // Tomar el mejor resultado actual como base
  const bestResult = currentResults.reduce((best, r) => 
    r.energiaAnualKwh > best.energiaAnualKwh ? r : best, currentResults[0]);
  
  if (!bestResult) return scenarios;
  
  // Escenario 1: Configuración actual (fachada)
  const currentPOA = bestResult.energiaAnualKwhM2 / bestResult.eficienciaAjustada;
  const hvacCurrent: HVACSavingsParams = {
    conventionalSHGC: DEFAULT_HVAC_PARAMS.conventionalSHGC!,
    bipvSHGC: calculateBIPVSHGC(bestResult.transparencia),
    area,
    annualPOA: currentPOA,
    coolingCOP: DEFAULT_HVAC_PARAMS.coolingCOP!,
    electricityRate: energyParams.electricityBuyRate,
    coolingMonths,
  };
  
  scenarios.push(runROIScenario(
    'Configuración Actual (Fachada)',
    `Fachada vertical ${bestResult.technology} τ=${(bestResult.transparencia * 100).toFixed(0)}%`,
    '🏗️',
    'facade_vertical',
    bestResult.energiaAnualKwh,
    bestResult.energiaAnualKwhM2,
    area,
    tilt,
    azimuth,
    bestResult.transparencia,
    costs,
    energyParams,
    hvacCurrent,
    incentives
  ));
  
  // Escenario 2: Pérgola con misma tecnología
  const pergolaConfig = INSTALLATION_CONFIGS.find(c => c.id === 'pergola')!;
  const pergolaProductionFactor = estimateProductionFactor(pergolaConfig.defaultTilt, latitude) /
    estimateProductionFactor(tilt, latitude);
  const pergolaProduction = bestResult.energiaAnualKwh * pergolaProductionFactor;
  const pergolaPOA = currentPOA * pergolaProductionFactor;
  
  scenarios.push(runROIScenario(
    'Pérgola Solar',
    `Pérgola ${pergolaConfig.defaultTilt}° con ${bestResult.technology}. Doble función: energía + sombra exterior.`,
    '🌿',
    'pergola',
    pergolaProduction,
    pergolaProduction / area,
    area,
    pergolaConfig.defaultTilt,
    azimuth,
    bestResult.transparencia,
    { ...costs, installationCostPerM2: costs.installationCostPerM2 * 1.3, conventionalGlassCostPerM2: 0 },
    energyParams,
    null, // pérgola no reemplaza vidrio interior
    incentives
  ));
  
  // Escenario 3: Marquesina/Carport
  const canopyConfig = INSTALLATION_CONFIGS.find(c => c.id === 'canopy')!;
  const canopyProductionFactor = estimateProductionFactor(canopyConfig.defaultTilt, latitude) /
    estimateProductionFactor(tilt, latitude);
  const canopyProduction = bestResult.energiaAnualKwh * canopyProductionFactor;
  
  scenarios.push(runROIScenario(
    'Marquesina / Carport',
    `Marquesina ${canopyConfig.defaultTilt}° con ${bestResult.technology}. Protección vehicular + generación.`,
    '🅿️',
    'canopy',
    canopyProduction,
    canopyProduction / area,
    area,
    canopyConfig.defaultTilt,
    azimuth,
    bestResult.transparencia,
    { ...costs, installationCostPerM2: costs.installationCostPerM2 * 1.5, conventionalGlassCostPerM2: 0 },
    energyParams,
    null,
    incentives
  ));
  
  // Escenario 4: Cubierta inclinada óptima
  const rooftopConfig = INSTALLATION_CONFIGS.find(c => c.id === 'rooftop_tilted')!;
  const optimalTilt = Math.abs(latitude);
  const rooftopProductionFactor = estimateProductionFactor(optimalTilt, latitude) /
    estimateProductionFactor(tilt, latitude);
  const rooftopProduction = bestResult.energiaAnualKwh * rooftopProductionFactor;
  
  scenarios.push(runROIScenario(
    'Cubierta Inclinada Óptima',
    `Cubierta ${optimalTilt.toFixed(0)}° orientación sur. Máxima captación solar.`,
    '🏠',
    'rooftop_tilted',
    rooftopProduction,
    rooftopProduction / area,
    area,
    optimalTilt,
    180,
    0.1, // opaco en cubierta
    { ...costs, glassCostPerM2: costs.glassCostPerM2 * 0.7, installationCostPerM2: costs.installationCostPerM2 * 0.8, conventionalGlassCostPerM2: 0 },
    energyParams,
    null,
    incentives
  ));
  
  // Escenario 5: Fachada inclinada (compromiso)
  const facadeIncConfig = INSTALLATION_CONFIGS.find(c => c.id === 'facade_inclined')!;
  const facadeIncProductionFactor = estimateProductionFactor(facadeIncConfig.defaultTilt, latitude) /
    estimateProductionFactor(tilt, latitude);
  const facadeIncProduction = bestResult.energiaAnualKwh * facadeIncProductionFactor;
  const facadeIncPOA = currentPOA * facadeIncProductionFactor;
  
  const hvacFacadeInc: HVACSavingsParams = {
    conventionalSHGC: DEFAULT_HVAC_PARAMS.conventionalSHGC!,
    bipvSHGC: calculateBIPVSHGC(bestResult.transparencia),
    area,
    annualPOA: facadeIncPOA,
    coolingCOP: DEFAULT_HVAC_PARAMS.coolingCOP!,
    electricityRate: energyParams.electricityBuyRate,
    coolingMonths,
  };
  
  scenarios.push(runROIScenario(
    'Fachada Inclinada 60°',
    `Fachada inclinada ${facadeIncConfig.defaultTilt}° con ${bestResult.technology}. Mejor captación que vertical.`,
    '📐',
    'facade_inclined',
    facadeIncProduction,
    facadeIncProduction / area,
    area,
    facadeIncConfig.defaultTilt,
    azimuth,
    bestResult.transparencia,
    costs,
    energyParams,
    hvacFacadeInc,
    incentives
  ));
  
  // Escenario 6: Misma fachada con menor transparencia (más producción)
  if (bestResult.transparencia > 0.15) {
    const lowerTransparency = Math.max(0.1, bestResult.transparencia - 0.2);
    const efficiencyBoost = (1 - lowerTransparency) / (1 - bestResult.transparencia);
    const lowerTProduction = bestResult.energiaAnualKwh * efficiencyBoost;
    
    const hvacLowerT: HVACSavingsParams = {
      conventionalSHGC: DEFAULT_HVAC_PARAMS.conventionalSHGC!,
      bipvSHGC: calculateBIPVSHGC(lowerTransparency),
      area,
      annualPOA: currentPOA,
      coolingCOP: DEFAULT_HVAC_PARAMS.coolingCOP!,
      electricityRate: energyParams.electricityBuyRate,
      coolingMonths,
    };
    
    scenarios.push(runROIScenario(
      `Fachada τ=${(lowerTransparency * 100).toFixed(0)}% (Menos Transparente)`,
      `Misma fachada con transparencia reducida a ${(lowerTransparency * 100).toFixed(0)}%. Mayor generación, menor luz natural.`,
      '🔲',
      'facade_vertical',
      lowerTProduction,
      lowerTProduction / area,
      area,
      tilt,
      azimuth,
      lowerTransparency,
      costs,
      energyParams,
      hvacLowerT,
      incentives
    ));
  }
  
  // Escenario 7: Sin incentivos (para comparar impacto)
  scenarios.push(runROIScenario(
    'Fachada SIN Incentivos',
    `Mismo escenario actual pero sin beneficios tributarios (Ley 1715).`,
    '⚠️',
    'facade_vertical',
    bestResult.energiaAnualKwh,
    bestResult.energiaAnualKwhM2,
    area,
    tilt,
    azimuth,
    bestResult.transparencia,
    costs,
    energyParams,
    hvacCurrent,
    DEFAULT_INCENTIVES_NONE
  ));
  
  // Ordenar por ROI 25 años descendente y asignar ranking
  scenarios.sort((a, b) => b.roi25Years - a.roi25Years);
  scenarios.forEach((s, i) => { s.rank = i + 1; });
  
  return scenarios;
}

/**
 * Genera análisis de sensibilidad para una variable
 */
export function generateSensitivityAnalysis(
  baseResult: BIPVSimulationSummary,
  area: number,
  tilt: number,
  latitude: number,
  costs: BIPVCostAssumptions,
  energyParams: EnergyValorizationParams,
  incentives: IncentiveParams
): { tiltSensitivity: SensitivityPoint[]; transparencySensitivity: SensitivityPoint[]; rateSensitivity: SensitivityPoint[]; selfConsumptionSensitivity: SensitivityPoint[] } {
  
  const basePOA = baseResult.energiaAnualKwhM2 / baseResult.eficienciaAjustada;
  
  // Sensibilidad a inclinación
  const tiltSensitivity: SensitivityPoint[] = [];
  for (let t = 0; t <= 90; t += 10) {
    const factor = estimateProductionFactor(t, latitude) / estimateProductionFactor(tilt, latitude);
    const production = baseResult.energiaAnualKwh * factor;
    const scenario = runROIScenario('', '', '', '', production, production / area, area, t, 180, baseResult.transparencia, costs, energyParams, null, incentives);
    tiltSensitivity.push({ variable: 'tilt', value: t, label: `${t}°`, roi25: scenario.roi25Years, payback: scenario.paybackYears, production });
  }
  
  // Sensibilidad a transparencia
  const transparencySensitivity: SensitivityPoint[] = [];
  for (const tl of TRANSPARENCY_LEVELS) {
    const effFactor = (1 - tl.value) / (1 - baseResult.transparencia);
    const production = baseResult.energiaAnualKwh * effFactor;
    const scenario = runROIScenario('', '', '', '', production, production / area, area, tilt, 180, tl.value, costs, energyParams, null, incentives);
    transparencySensitivity.push({ variable: 'transparency', value: tl.value, label: tl.label, roi25: scenario.roi25Years, payback: scenario.paybackYears, production });
  }
  
  // Sensibilidad a tarifa eléctrica
  const rateSensitivity: SensitivityPoint[] = [];
  for (let rate = 0.08; rate <= 0.50; rate += 0.04) {
    const modParams = { ...energyParams, electricityBuyRate: rate };
    const scenario = runROIScenario('', '', '', '', baseResult.energiaAnualKwh, baseResult.energiaAnualKwhM2, area, tilt, 180, baseResult.transparencia, costs, modParams, null, incentives);
    rateSensitivity.push({ variable: 'rate', value: rate, label: `$${rate.toFixed(2)}`, roi25: scenario.roi25Years, payback: scenario.paybackYears, production: baseResult.energiaAnualKwh });
  }
  
  // Sensibilidad a autoconsumo
  const selfConsumptionSensitivity: SensitivityPoint[] = [];
  for (let sc = 20; sc <= 100; sc += 10) {
    const modParams = { ...energyParams, selfConsumptionPercent: sc };
    const scenario = runROIScenario('', '', '', '', baseResult.energiaAnualKwh, baseResult.energiaAnualKwhM2, area, tilt, 180, baseResult.transparencia, costs, modParams, null, incentives);
    selfConsumptionSensitivity.push({ variable: 'selfConsumption', value: sc, label: `${sc}%`, roi25: scenario.roi25Years, payback: scenario.paybackYears, production: baseResult.energiaAnualKwh });
  }
  
  return { tiltSensitivity, transparencySensitivity, rateSensitivity, selfConsumptionSensitivity };
}

/**
 * Genera recomendaciones de optimización basadas en los resultados
 */
export function generateRecommendations(
  scenarios: ROIScenarioResult[],
  currentTilt: number,
  currentTransparency: number,
  latitude: number
): OptimizationRecommendation[] {
  const recommendations: OptimizationRecommendation[] = [];
  const current = scenarios.find(s => s.name.includes('Actual'));
  const best = scenarios[0]; // ya ordenados por ROI
  
  if (!current) return recommendations;
  
  // Recomendación 1: Si la fachada vertical tiene ROI negativo
  if (current.roi25Years < 0 && currentTilt >= 75) {
    recommendations.push({
      type: 'architectural',
      priority: 'high',
      title: 'Reducir inclinación de la superficie',
      description: `La fachada vertical (${currentTilt}°) recibe ~40-60% menos irradiancia que una superficie inclinada a ${Math.abs(latitude).toFixed(0)}°. Considere pérgolas, marquesinas o fachadas inclinadas para mejorar la captación solar.`,
      impact: `Potencial mejora de ROI: +${(best.roi25Years - current.roi25Years).toFixed(0)}% a 25 años`,
      icon: '📐',
    });
  }
  
  // Recomendación 2: Transparencia excesiva
  if (currentTransparency > 0.4) {
    const lowerTScenario = scenarios.find(s => s.name.includes('Menos Transparente'));
    if (lowerTScenario && lowerTScenario.roi25Years > current.roi25Years) {
      recommendations.push({
        type: 'technical',
        priority: 'high',
        title: 'Reducir transparencia del vidrio',
        description: `Con τ=${(currentTransparency * 100).toFixed(0)}%, la mayor parte de la radiación pasa sin convertirse en electricidad. Reducir a τ=${(lowerTScenario.transparency * 100).toFixed(0)}% aumenta la producción en ~${((lowerTScenario.annualProduction / current.annualProduction - 1) * 100).toFixed(0)}%.`,
        impact: `Mejora ROI 25: ${current.roi25Years.toFixed(0)}% → ${lowerTScenario.roi25Years.toFixed(0)}%`,
        icon: '🔲',
      });
    }
  }
  
  // Recomendación 3: Incentivos tributarios
  const noIncentiveScenario = scenarios.find(s => s.name.includes('SIN Incentivos'));
  if (noIncentiveScenario && current.incentiveSaving > 0) {
    recommendations.push({
      type: 'financial',
      priority: 'medium',
      title: 'Aprovechar incentivos Ley 1715 (Colombia)',
      description: `Los beneficios tributarios (50% deducción renta + exclusión IVA + exención aranceles) reducen el costo efectivo en $${current.incentiveSaving.toLocaleString(undefined, {maximumFractionDigits: 0})} USD. Sin ellos, el ROI sería ${noIncentiveScenario.roi25Years.toFixed(0)}%.`,
      impact: `Ahorro fiscal: $${current.incentiveSaving.toLocaleString(undefined, {maximumFractionDigits: 0})} USD`,
      icon: '📋',
    });
  }
  
  // Recomendación 4: Autoconsumo
  if (current.annualEnergyRevenue > 0) {
    recommendations.push({
      type: 'operational',
      priority: 'medium',
      title: 'Maximizar autoconsumo',
      description: 'La energía autoconsumida vale más que la inyectada a red. Sincronice cargas (iluminación, HVAC, equipos) con las horas de producción solar para aumentar el % de autoconsumo.',
      impact: 'Cada 10% adicional de autoconsumo mejora el ingreso anual en ~$' + ((current.annualProduction * 0.1 * (DEFAULT_ENERGY_PARAMS.electricityBuyRate - DEFAULT_ENERGY_PARAMS.electricitySellRate)).toFixed(0)) + ' USD',
      icon: '⚡',
    });
  }
  
  // Recomendación 5: Ahorro HVAC
  if (current.annualHVACSaving > 0) {
    recommendations.push({
      type: 'technical',
      priority: 'medium',
      title: 'Valorizar ahorro en climatización',
      description: `El vidrio BIPV reduce la ganancia solar al interior (SHGC ${calculateBIPVSHGC(currentTransparency).toFixed(2)} vs ${DEFAULT_HVAC_PARAMS.conventionalSHGC} convencional), ahorrando $${current.annualHVACSaving.toFixed(0)}/año en aire acondicionado.`,
      impact: `Ahorro HVAC anual: $${current.annualHVACSaving.toFixed(0)} USD/año`,
      icon: '❄️',
    });
  }
  
  // Recomendación 6: Pérgola como alternativa
  const pergolaScenario = scenarios.find(s => s.surfaceType === 'pergola');
  if (pergolaScenario && pergolaScenario.roi25Years > current.roi25Years + 20) {
    recommendations.push({
      type: 'architectural',
      priority: 'high',
      title: 'Considerar pérgola solar como alternativa',
      description: `Una pérgola solar con la misma tecnología produce ${((pergolaScenario.annualProduction / current.annualProduction - 1) * 100).toFixed(0)}% más energía por su menor inclinación, con ROI de ${pergolaScenario.roi25Years.toFixed(0)}% a 25 años.`,
      impact: `ROI pérgola: ${pergolaScenario.roi25Years.toFixed(0)}% vs fachada: ${current.roi25Years.toFixed(0)}%`,
      icon: '🌿',
    });
  }
  
  // Recomendación 7: Escalamiento de tarifa
  recommendations.push({
    type: 'financial',
    priority: 'low',
    title: 'Considerar escalamiento tarifario',
    description: `Con un aumento anual de tarifa del ${DEFAULT_ENERGY_PARAMS.electricityEscalation}%, la energía generada vale más cada año. En 10 años la tarifa será ~${(DEFAULT_ENERGY_PARAMS.electricityBuyRate * Math.pow(1.035, 10)).toFixed(3)} USD/kWh.`,
    impact: 'El ROI mejora significativamente en la segunda mitad de la vida útil',
    icon: '📈',
  });
  
  return recommendations;
}
