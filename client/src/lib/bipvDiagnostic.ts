/**
 * Módulo de Diagnóstico BIPV — Evaluación de Sistemas Instalados
 *
 * Calcula la producción esperada mensual/anual usando tres modelos:
 *   1. Mulcue-Llanos (modelo colombiano)
 *   2. PVGIS (datos satelitales europeos)
 *   3. PVWatts (datos NREL)
 *
 * Compara la producción real medida contra la esperada y genera
 * métricas de desviación, semáforo de salud y diagnóstico.
 *
 * Referencias:
 * - IEC 61724-1:2021 — Performance Ratio & Weather-corrected PR
 * - Mulcue-Llanos — Universidad Nacional de Colombia
 * - PVGIS — JRC European Commission
 * - PVWatts — NREL (National Renewable Energy Laboratory)
 */

// ============================================================
// TIPOS
// ============================================================

export interface BIPVPanelConfig {
  /** Nombre del panel */
  name: string;
  /** Potencia nominal STC (W) */
  powerRating: number;
  /** Eficiencia nominal (%, ej: 20.5) */
  efficiency: number;
  /** Coeficiente de temperatura (%/°C, negativo, ej: -0.36) */
  tempCoeff: number;
  /** NOCT (°C) */
  noct: number;
  /** Área del panel (m²) */
  area: number;
  /** Cantidad de paneles instalados */
  quantity: number;
  /** Años desde la instalación */
  yearsInstalled: number;
  /** Degradación anual (%/año) */
  annualDegradation: number;
}

export interface BIPVSiteConfig {
  /** Latitud del sitio */
  latitude: number;
  /** Longitud del sitio */
  longitude: number;
  /** Nombre del sitio */
  siteName: string;
  /** Ángulo de inclinación medido en campo (grados) */
  tiltField: number;
  /** Azimut medido en campo (grados, 0=Sur) */
  azimuthField: number;
  /** Factor de sombreado estimado (0-1, 1=sin sombras) */
  shadowFactor: number;
  /** Tipo de instalación */
  installationType: string;
}

export interface BIPVMonthlyExpected {
  month: number; // 1-12
  monthName: string;
  // Mulcue-Llanos
  mulcue_ac_kWh: number;
  mulcue_pr: number;
  mulcue_cellTemp: number;
  // PVGIS (null si no disponible)
  pvgis_ac_kWh: number | null;
  pvgis_poa_kWhm2: number | null;
  pvgis_tamb: number | null;
  // PVWatts (null si no disponible)
  pvwatts_ac_kWh: number | null;
  pvwatts_dc_kWh: number | null;
  pvwatts_poa_kWhm2: number | null;
  pvwatts_tamb: number | null;
  pvwatts_tcell: number | null;
  // Promedio ponderado de los modelos disponibles
  expected_ac_kWh: number;
}

export interface BIPVAnnualSummary {
  // Mulcue-Llanos
  mulcue_annual_kWh: number;
  mulcue_pr: number;
  mulcue_specificYield: number; // kWh/kWp/año
  // PVGIS
  pvgis_annual_kWh: number | null;
  pvgis_specificYield: number | null;
  // PVWatts
  pvwatts_annual_kWh: number | null;
  pvwatts_specificYield: number | null;
  // Promedio
  expected_annual_kWh: number;
  expected_specificYield: number;
  // Capacidad instalada
  installedCapacity_kWp: number;
}

export interface BIPVFieldMeasurement {
  /** Producción real mensual medida (kWh) — array de 12 */
  monthlyProduction_kWh: (number | null)[];
  /** Producción real anual total (kWh) */
  annualProduction_kWh: number | null;
}

export interface BIPVHealthMetric {
  label: string;
  value: number;
  unit: string;
  color: string; // verde, amarillo, rojo
  status: 'ok' | 'warning' | 'critical';
}

export interface BIPVComparisonResult {
  monthly: BIPVMonthlyComparison[];
  annual: BIPVAnnualComparison;
  healthScore: number; // 0-100
  healthStatus: 'excelente' | 'bueno' | 'regular' | 'deficiente' | 'critico';
  healthColor: string;
  metrics: BIPVHealthMetric[];
}

export interface BIPVMonthlyComparison {
  month: number;
  monthName: string;
  expected_kWh: number;
  real_kWh: number | null;
  delta_kWh: number | null;
  delta_pct: number | null;
  color: string;
  /** P_m mensual = P_ref × N × (G_mes / G_ref) — producción por irradiancia sin pérdidas (kWh) */
  pm_kWh: number;
  /** PR Convencional mensual = E_inversor / P_m */
  pr_conventional: number | null;
  /** PR Corregido mensual = E_inversor / Producción_esperada (promedio modelos) */
  pr_corrected: number | null;
}

export interface BIPVAnnualComparison {
  expected_kWh: number;
  real_kWh: number | null;
  delta_kWh: number | null;
  delta_pct: number | null;
  pr_real: number | null;
  pr_expected: number;
  energyRatio: number | null; // real/expected
  /** P_m anual = P_ref × N × (G_anual / G_ref) — producción teórica por irradiancia (kWh) */
  pm_annual_kWh: number;
  /** PR Convencional anual = E_inversor_anual / P_m_anual */
  pr_conventional: number | null;
  /** PR Corregido anual = E_inversor_anual / Producción_esperada_anual (promedio modelos) */
  pr_corrected: number | null;
}

// ============================================================
// CONSTANTES
// ============================================================

const MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
const DAYS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

/** Distribución mensual típica tropical (fracciones del GHI anual por mes) */
const MONTHLY_GHI_FRACTIONS = [0.085, 0.082, 0.088, 0.083, 0.080, 0.078, 0.080, 0.083, 0.082, 0.083, 0.080, 0.096];

/** Variación de temperatura mensual típica (°C respecto a la media) */
const MONTHLY_TEMP_VARIATION = [-0.5, 0.0, 0.5, 0.5, 0.0, -0.5, -1.0, -0.5, 0.0, 0.5, 0.5, 0.0];

// ============================================================
// FUNCIONES DE CÁLCULO
// ============================================================

/**
 * Calcula la producción esperada mensual usando el modelo Mulcue-Llanos.
 * Incluye degradación por años de operación.
 */
export function calculateMulcueExpected(
  panel: BIPVPanelConfig,
  site: BIPVSiteConfig,
  ghiAnnual_kWhm2: number,
  ambientTemp: number,
  fi: number = 0.95,
): BIPVMonthlyExpected[] {
  // Coeficiente de temperatura en decimal
  const gammaDecimal = Math.abs(panel.tempCoeff) > 0.01
    ? panel.tempCoeff / 100
    : panel.tempCoeff;

  // Degradación acumulada
  const degradationFactor = Math.pow(1 - panel.annualDegradation / 100, panel.yearsInstalled);

  // Potencia efectiva después de degradación
  const effectivePower = panel.powerRating * degradationFactor;

  // Capacidad instalada (kWp)
  const capacityKwp = (effectivePower * panel.quantity) / 1000;

  // PR Mulcue-Llanos
  const ksist = 0.82;
  const prMax = ksist * (1 + gammaDecimal * (1.12 * ambientTemp - 10));
  const prCorrected = Math.max(0.10, Math.min(0.95, prMax + 0.0006 * ambientTemp - 0.017));

  return Array.from({ length: 12 }, (_, i) => {
    const monthGHI = ghiAnnual_kWhm2 * MONTHLY_GHI_FRACTIONS[i];
    const monthTemp = ambientTemp + MONTHLY_TEMP_VARIATION[i];

    // Temperatura de celda NOCT
    const avgIrradiance = (monthGHI * 1000) / (DAYS_PER_MONTH[i] * 8); // W/m² promedio en 8h sol
    const cellTemp = monthTemp + (panel.noct - 20) * (Math.min(avgIrradiance, 1000) / 800);

    // HSP mensual = GHI_mes * FI * FS
    const hspMonth = monthGHI * fi * site.shadowFactor;

    // Producción AC = HSP * kWp * PR
    const ac_kWh = hspMonth * capacityKwp * prCorrected;

    return {
      month: i + 1,
      monthName: MONTH_NAMES[i],
      mulcue_ac_kWh: Math.round(ac_kWh * 100) / 100,
      mulcue_pr: Math.round(prCorrected * 10000) / 10000,
      mulcue_cellTemp: Math.round(cellTemp * 10) / 10,
      pvgis_ac_kWh: null,
      pvgis_poa_kWhm2: null,
      pvgis_tamb: null,
      pvwatts_ac_kWh: null,
      pvwatts_dc_kWh: null,
      pvwatts_poa_kWhm2: null,
      pvwatts_tamb: null,
      pvwatts_tcell: null,
      expected_ac_kWh: Math.round(ac_kWh * 100) / 100,
    };
  });
}

/**
 * Integra datos de PVGIS en la tabla de producción esperada.
 */
export function integratePVGISData(
  monthly: BIPVMonthlyExpected[],
  pvgisMonthly: { month: number; productionAC_kWh: number; irradiationPOA_kWhm2: number; temperature: number }[],
  degradationFactor: number = 1.0,
): BIPVMonthlyExpected[] {
  return monthly.map((m, i) => {
    const pvgis = pvgisMonthly.find(p => p.month === m.month);
    if (!pvgis) return m;

    const pvgis_ac = pvgis.productionAC_kWh * degradationFactor;

    return {
      ...m,
      pvgis_ac_kWh: Math.round(pvgis_ac * 100) / 100,
      pvgis_poa_kWhm2: Math.round(pvgis.irradiationPOA_kWhm2 * 100) / 100,
      pvgis_tamb: Math.round(pvgis.temperature * 10) / 10,
      expected_ac_kWh: Math.round(((m.mulcue_ac_kWh + pvgis_ac) / 2) * 100) / 100,
    };
  });
}

/**
 * Integra datos de PVWatts en la tabla de producción esperada.
 */
export function integratePVWattsData(
  monthly: BIPVMonthlyExpected[],
  pvwattsMonthly: { month: number; ac_kWh: number; dc_kWh: number; poa_kWhm2: number; tamb_C: number; tcell_C: number }[],
  degradationFactor: number = 1.0,
): BIPVMonthlyExpected[] {
  return monthly.map((m) => {
    const pw = pvwattsMonthly.find(p => p.month === m.month);
    if (!pw) return m;

    const pw_ac = pw.ac_kWh * degradationFactor;
    const pw_dc = pw.dc_kWh * degradationFactor;

    // Recalcular promedio con todas las fuentes disponibles
    const sources: number[] = [m.mulcue_ac_kWh];
    if (m.pvgis_ac_kWh !== null) sources.push(m.pvgis_ac_kWh);
    sources.push(pw_ac);
    const avgExpected = sources.reduce((a, b) => a + b, 0) / sources.length;

    return {
      ...m,
      pvwatts_ac_kWh: Math.round(pw_ac * 100) / 100,
      pvwatts_dc_kWh: Math.round(pw_dc * 100) / 100,
      pvwatts_poa_kWhm2: Math.round(pw.poa_kWhm2 * 100) / 100,
      pvwatts_tamb: Math.round(pw.tamb_C * 10) / 10,
      pvwatts_tcell: Math.round(pw.tcell_C * 10) / 10,
      expected_ac_kWh: Math.round(avgExpected * 100) / 100,
    };
  });
}

/**
 * Calcula el resumen anual de producción esperada.
 */
export function calculateAnnualSummary(
  monthly: BIPVMonthlyExpected[],
  panel: BIPVPanelConfig,
): BIPVAnnualSummary {
  const degradationFactor = Math.pow(1 - panel.annualDegradation / 100, panel.yearsInstalled);
  const capacityKwp = (panel.powerRating * degradationFactor * panel.quantity) / 1000;

  const mulcue_annual = monthly.reduce((s, m) => s + m.mulcue_ac_kWh, 0);
  const pvgis_annual = monthly.every(m => m.pvgis_ac_kWh !== null)
    ? monthly.reduce((s, m) => s + (m.pvgis_ac_kWh ?? 0), 0)
    : null;
  const pvwatts_annual = monthly.every(m => m.pvwatts_ac_kWh !== null)
    ? monthly.reduce((s, m) => s + (m.pvwatts_ac_kWh ?? 0), 0)
    : null;
  const expected_annual = monthly.reduce((s, m) => s + m.expected_ac_kWh, 0);

  return {
    mulcue_annual_kWh: Math.round(mulcue_annual * 100) / 100,
    mulcue_pr: monthly[0]?.mulcue_pr ?? 0,
    mulcue_specificYield: capacityKwp > 0 ? Math.round((mulcue_annual / capacityKwp) * 100) / 100 : 0,
    pvgis_annual_kWh: pvgis_annual !== null ? Math.round(pvgis_annual * 100) / 100 : null,
    pvgis_specificYield: pvgis_annual !== null && capacityKwp > 0
      ? Math.round((pvgis_annual / capacityKwp) * 100) / 100
      : null,
    pvwatts_annual_kWh: pvwatts_annual !== null ? Math.round(pvwatts_annual * 100) / 100 : null,
    pvwatts_specificYield: pvwatts_annual !== null && capacityKwp > 0
      ? Math.round((pvwatts_annual / capacityKwp) * 100) / 100
      : null,
    expected_annual_kWh: Math.round(expected_annual * 100) / 100,
    expected_specificYield: capacityKwp > 0 ? Math.round((expected_annual / capacityKwp) * 100) / 100 : 0,
    installedCapacity_kWp: Math.round(capacityKwp * 100) / 100,
  };
}

/**
 * Compara producción real vs esperada y genera métricas de salud.
 */
export function compareBIPVPerformance(
  monthly: BIPVMonthlyExpected[],
  field: BIPVFieldMeasurement,
  panel: BIPVPanelConfig,
  ghiAnnual_kWhm2: number,
): BIPVComparisonResult {
  const summary = calculateAnnualSummary(monthly, panel);
  const degradationFactor = Math.pow(1 - panel.annualDegradation / 100, panel.yearsInstalled);
  const capacityKwp = (panel.powerRating * degradationFactor * panel.quantity) / 1000;

  // G_ref = 1000 W/m² = 1 kW/m² (condiciones STC)
  const G_REF = 1; // kW/m²
  // P_ref en kW (potencia nominal del sistema)
  const P_ref_kW = (panel.powerRating * panel.quantity) / 1000;

  // Comparación mensual con P_m, PR Convencional y PR Corregido
  const monthlyComp: BIPVMonthlyComparison[] = monthly.map((m, i) => {
    const real = field.monthlyProduction_kWh[i];
    const expected = m.expected_ac_kWh;
    const delta_kWh = real !== null ? real - expected : null;
    const delta_pct = real !== null && expected > 0 ? ((real - expected) / expected) * 100 : null;

    // P_m mensual = P_ref × (G_mes / G_ref)
    // G_mes en kWh/m²/mes, convertido a horas pico solares (HSP)
    // P_m = P_ref_kW × HSP_mes (donde HSP = GHI_mes en kWh/m²)
    const monthGHI_kWhm2 = ghiAnnual_kWhm2 * MONTHLY_GHI_FRACTIONS[i];
    // Usar POA si está disponible (más preciso), sino GHI
    const bestIrradiance = m.pvwatts_poa_kWhm2 ?? m.pvgis_poa_kWhm2 ?? monthGHI_kWhm2;
    const pm_kWh = P_ref_kW * (bestIrradiance / G_REF);

    // PR Convencional = E_inversor / P_m
    const pr_conventional = real !== null && pm_kWh > 0
      ? real / pm_kWh
      : null;

    // PR Corregido = E_inversor / Producción_esperada (promedio de modelos disponibles)
    const pr_corrected = real !== null && expected > 0
      ? real / expected
      : null;

    return {
      month: m.month,
      monthName: m.monthName,
      expected_kWh: expected,
      real_kWh: real,
      delta_kWh: delta_kWh !== null ? Math.round(delta_kWh * 100) / 100 : null,
      delta_pct: delta_pct !== null ? Math.round(delta_pct * 10) / 10 : null,
      color: getDeviationColor(delta_pct),
      pm_kWh: Math.round(pm_kWh * 100) / 100,
      pr_conventional: pr_conventional !== null ? Math.round(pr_conventional * 10000) / 10000 : null,
      pr_corrected: pr_corrected !== null ? Math.round(pr_corrected * 10000) / 10000 : null,
    };
  });

  // P_m anual = suma de P_m mensuales
  const pm_annual_kWh = monthlyComp.reduce((s, m) => s + m.pm_kWh, 0);

  // Comparación anual
  const realAnnual = field.annualProduction_kWh;
  const expectedAnnual = summary.expected_annual_kWh;
  const annualDelta = realAnnual !== null ? realAnnual - expectedAnnual : null;
  const annualDeltaPct = realAnnual !== null && expectedAnnual > 0
    ? ((realAnnual - expectedAnnual) / expectedAnnual) * 100
    : null;

  // PR real estimado (método antiguo, se mantiene por compatibilidad)
  const pr_real = realAnnual !== null && capacityKwp > 0 && summary.mulcue_specificYield > 0
    ? realAnnual / (capacityKwp * summary.mulcue_specificYield / summary.mulcue_pr)
    : null;

  // PR Convencional anual = E_inversor_anual / P_m_anual
  const pr_conventional_annual = realAnnual !== null && pm_annual_kWh > 0
    ? realAnnual / pm_annual_kWh
    : null;

  // PR Corregido anual = E_inversor_anual / Producción_esperada_anual
  const pr_corrected_annual = realAnnual !== null && expectedAnnual > 0
    ? realAnnual / expectedAnnual
    : null;

  const annualComp: BIPVAnnualComparison = {
    expected_kWh: expectedAnnual,
    real_kWh: realAnnual,
    delta_kWh: annualDelta !== null ? Math.round(annualDelta * 100) / 100 : null,
    delta_pct: annualDeltaPct !== null ? Math.round(annualDeltaPct * 10) / 10 : null,
    pr_real: pr_real !== null ? Math.round(pr_real * 10000) / 10000 : null,
    pr_expected: summary.mulcue_pr,
    energyRatio: realAnnual !== null && expectedAnnual > 0
      ? Math.round((realAnnual / expectedAnnual) * 10000) / 10000
      : null,
    pm_annual_kWh: Math.round(pm_annual_kWh * 100) / 100,
    pr_conventional: pr_conventional_annual !== null ? Math.round(pr_conventional_annual * 10000) / 10000 : null,
    pr_corrected: pr_corrected_annual !== null ? Math.round(pr_corrected_annual * 10000) / 10000 : null,
  };

  // Health score (0-100)
  const healthScore = calculateHealthScore(annualDeltaPct);
  const { status, color } = classifyHealth(healthScore);

  // Métricas de salud
  const metrics: BIPVHealthMetric[] = [
    {
      label: 'PR Conv.',
      value: pr_conventional_annual !== null ? pr_conventional_annual * 100 : 0,
      unit: '%',
      color: pr_conventional_annual !== null && pr_conventional_annual >= 0.70 ? '#16a34a' : pr_conventional_annual !== null && pr_conventional_annual >= 0.55 ? '#f59e0b' : '#dc2626',
      status: pr_conventional_annual !== null && pr_conventional_annual >= 0.70 ? 'ok' : pr_conventional_annual !== null && pr_conventional_annual >= 0.55 ? 'warning' : 'critical',
    },
    {
      label: 'PR Corr.',
      value: pr_corrected_annual !== null ? pr_corrected_annual * 100 : 0,
      unit: '%',
      color: pr_corrected_annual !== null && pr_corrected_annual >= 0.85 ? '#16a34a' : pr_corrected_annual !== null && pr_corrected_annual >= 0.70 ? '#f59e0b' : '#dc2626',
      status: pr_corrected_annual !== null && pr_corrected_annual >= 0.85 ? 'ok' : pr_corrected_annual !== null && pr_corrected_annual >= 0.70 ? 'warning' : 'critical',
    },
    {
      label: 'Ratio Energ.',
      value: annualComp.energyRatio !== null ? annualComp.energyRatio * 100 : 0,
      unit: '%',
      color: annualComp.energyRatio !== null && annualComp.energyRatio >= 0.9 ? '#16a34a' : annualComp.energyRatio !== null && annualComp.energyRatio >= 0.75 ? '#f59e0b' : '#dc2626',
      status: annualComp.energyRatio !== null && annualComp.energyRatio >= 0.9 ? 'ok' : annualComp.energyRatio !== null && annualComp.energyRatio >= 0.75 ? 'warning' : 'critical',
    },
    {
      label: 'Desv. Anual',
      value: annualDeltaPct ?? 0,
      unit: '%',
      color: annualDeltaPct !== null && Math.abs(annualDeltaPct) < 10 ? '#16a34a' : annualDeltaPct !== null && Math.abs(annualDeltaPct) < 20 ? '#f59e0b' : '#dc2626',
      status: annualDeltaPct !== null && Math.abs(annualDeltaPct) < 10 ? 'ok' : annualDeltaPct !== null && Math.abs(annualDeltaPct) < 20 ? 'warning' : 'critical',
    },
  ];

  return {
    monthly: monthlyComp,
    annual: annualComp,
    healthScore,
    healthStatus: status,
    healthColor: color,
    metrics,
  };
}

// ============================================================
// FUNCIONES AUXILIARES
// ============================================================

function getDeviationColor(deltaPct: number | null): string {
  if (deltaPct === null) return '#9ca3af'; // gris
  const abs = Math.abs(deltaPct);
  if (abs < 5) return '#16a34a'; // verde
  if (abs < 10) return '#22c55e'; // verde claro
  if (abs < 15) return '#f59e0b'; // amarillo
  if (abs < 25) return '#f97316'; // naranja
  return '#dc2626'; // rojo
}

function calculateHealthScore(deltaPct: number | null): number {
  if (deltaPct === null) return 50; // sin datos
  const abs = Math.abs(deltaPct);
  // Producción real >= esperada → bonus
  if (deltaPct >= 0) return Math.min(100, 90 + deltaPct * 0.5);
  // Producción real < esperada → penalización
  if (abs < 5) return 85;
  if (abs < 10) return 75;
  if (abs < 15) return 60;
  if (abs < 25) return 40;
  if (abs < 40) return 20;
  return 5;
}

function classifyHealth(score: number): { status: BIPVComparisonResult['healthStatus']; color: string } {
  if (score >= 85) return { status: 'excelente', color: '#16a34a' };
  if (score >= 70) return { status: 'bueno', color: '#22c55e' };
  if (score >= 50) return { status: 'regular', color: '#f59e0b' };
  if (score >= 30) return { status: 'deficiente', color: '#f97316' };
  return { status: 'critico', color: '#dc2626' };
}

/**
 * Genera un GHI anual estimado a partir de la latitud (para Colombia).
 * Rango típico: 1400-2000 kWh/m²/año
 */
export function estimateGHIFromLatitude(lat: number): number {
  const absLat = Math.abs(lat);
  // Colombia: 1° a 12° N, GHI varía por altitud y nubosidad
  if (absLat < 3) return 1650; // Amazonía/Pacífica
  if (absLat < 6) return 1750; // Andina central
  if (absLat < 8) return 1800; // Andina norte
  if (absLat < 10) return 1900; // Caribe interior
  if (absLat < 13) return 2000; // Guajira/Caribe
  return 1700; // Default
}

/**
 * Estima la temperatura ambiente promedio a partir de la latitud (Colombia).
 */
export function estimateTempFromLatitude(lat: number, elevation: number = 0): number {
  // Gradiente adiabático: ~6.5°C por 1000m
  const baseTemp = 28; // Nivel del mar tropical
  const elevationCorrection = elevation * 0.0065;
  return Math.round((baseTemp - elevationCorrection) * 10) / 10;
}
