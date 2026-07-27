/**
 * Cross-Validation: Comparación lado a lado Simulador vs PVWatts vs PVGIS
 * 
 * Funciones puras para construir datos de comparación y calcular métricas
 * estadísticas (RMSE, MAE, R², Δ%) entre las tres fuentes de datos.
 */

import type { MonthlyProduction, AnnualProduction, HourlyPR_T_Result } from './energyProduction';
import type { PVWattsToSimulatorData } from '@/components/PVWattsSatellite';
import type { PVGISToSimulatorData } from '@/components/PVGISAnalyzer';
import type { BIPVToEnergyData } from '@/lib/bipvToEnergyBridge';

const MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

// ============================================================
// INTERFACES
// ============================================================

/** Datos mensuales unificados de una fuente */
export interface SourceMonthlyData {
  ac_kWh: number | null;
  dc_kWh: number | null;
  poa_kWhm2: number | null;
  pr_pct: number | null;
  pr_t_pct: number | null;
  tamb_C: number | null;
  tcell_C: number | null;
  /** Yield específico mensual (kWh/kWp) - IEC 61724 */
  yield_kwh_kwp: number | null;
}

/** Fila de la tabla comparativa (un mes) */
export interface ComparisonRow {
  month: number;       // 1-12
  monthName: string;
  simulator: SourceMonthlyData;
  pvwatts: SourceMonthlyData;
  pvgis: SourceMonthlyData;
  bipv: SourceMonthlyData;
  /** Δ% Simulador vs PVWatts (AC) */
  delta_sim_pvw_pct: number | null;
  /** Δ% Simulador vs PVGIS (AC) */
  delta_sim_pvg_pct: number | null;
  /** Δ% PVWatts vs PVGIS (AC) */
  delta_pvw_pvg_pct: number | null;
  /** Δ% Simulador vs BIPV IAM+Soiling (AC) */
  delta_sim_bipv_pct: number | null;
  /** Δ Yield Simulador vs PVWatts (kWh/kWp) */
  delta_yield_sim_pvw_pct: number | null;
  /** Δ Yield Simulador vs PVGIS (kWh/kWp) */
  delta_yield_sim_pvg_pct: number | null;
  /** Δ Yield PVWatts vs PVGIS (kWh/kWp) */
  delta_yield_pvw_pvg_pct: number | null;
  /** Δ Yield Simulador vs BIPV (kWh/kWp) */
  delta_yield_sim_bipv_pct: number | null;
}

/** Resumen anual de una fuente */
export interface SourceAnnualSummary {
  ac_kWh: number | null;
  dc_kWh: number | null;
  poa_kWhm2: number | null;
  pr_pct: number | null;
  pr_t_pct: number | null;
  tamb_C: number | null;
  tcell_C: number | null;
  /** Yield específico anual (kWh/kWp) - IEC 61724 */
  yield_kwh_kwp: number | null;
}

/** Métricas estadísticas entre dos series */
export interface PairwiseStats {
  label: string;
  rmse: number | null;
  mae: number | null;
  r2: number | null;
  meanDelta_pct: number | null;
  n: number;
}

/** Resultado completo de la comparación */
/** Alerta de coherencia para datos mensuales sospechosos */
export interface DataCoherenceAlert {
  /** Fuente con datos sospechosos */
  source: 'bipv' | 'pvwatts' | 'pvgis' | 'simulator';
  /** Tipo de anomalía detectada */
  type: 'flat_distribution' | 'negative_values' | 'extreme_outlier';
  /** Coeficiente de variación (%) de la serie mensual */
  cv_pct: number;
  /** Mensaje descriptivo para el usuario */
  message: string;
  /** Severidad: warning (<5% CV) o critical (0% CV = constante) */
  severity: 'warning' | 'critical';
}

export interface ComparisonResult {
  rows: ComparisonRow[];
  annualSimulator: SourceAnnualSummary;
  annualPVWatts: SourceAnnualSummary;
  annualPVGIS: SourceAnnualSummary;
  annualBIPV: SourceAnnualSummary;
  stats: {
    sim_vs_pvwatts: PairwiseStats;
    sim_vs_pvgis: PairwiseStats;
    pvwatts_vs_pvgis: PairwiseStats;
    sim_vs_bipv: PairwiseStats;
  };
  hasPVWatts: boolean;
  hasPVGIS: boolean;
  hasBIPV: boolean;
  sourceCount: number;
  /** Alertas de coherencia de datos (series planas, valores negativos, outliers) */
  coherenceAlerts: DataCoherenceAlert[];
  /** Si la producción BIPV fue normalizada al kWp del Simulador */
  bipvNormalized: boolean;
  /** Factor de escala aplicado a la producción BIPV (simKwp/bipvKwp) */
  bipvScaleFactor: number;
  /** kWp del sistema BIPV (potenciaPicoW/1000) */
  bipvKwp: number | null;
  /** kWp del Simulador (panelPower * panelQuantity / 1000) */
  simKwp: number | null;
}

// ============================================================
// FUNCIONES AUXILIARES
// ============================================================

/** Calcula Δ% = (a - b) / b × 100. Retorna null si b ≈ 0. */
export function deltaPct(a: number | null, b: number | null): number | null {
  if (a === null || b === null || Math.abs(b) < 0.01) return null;
  return ((a - b) / b) * 100;
}

/** Calcula RMSE entre dos arrays de valores (ignora pares con null) */
export function calcRMSE(a: (number | null)[], b: (number | null)[]): number | null {
  let sumSq = 0;
  let n = 0;
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    if (a[i] !== null && b[i] !== null) {
      sumSq += (a[i]! - b[i]!) ** 2;
      n++;
    }
  }
  return n > 0 ? Math.sqrt(sumSq / n) : null;
}

/** Calcula MAE (Mean Absolute Error) entre dos arrays */
export function calcMAE(a: (number | null)[], b: (number | null)[]): number | null {
  let sumAbs = 0;
  let n = 0;
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    if (a[i] !== null && b[i] !== null) {
      sumAbs += Math.abs(a[i]! - b[i]!);
      n++;
    }
  }
  return n > 0 ? sumAbs / n : null;
}

/** Calcula R² (coeficiente de determinación) entre dos arrays */
export function calcR2(a: (number | null)[], b: (number | null)[]): number | null {
  const pairs: [number, number][] = [];
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    if (a[i] !== null && b[i] !== null) {
      pairs.push([a[i]!, b[i]!]);
    }
  }
  if (pairs.length < 3) return null;

  const meanB = pairs.reduce((s, p) => s + p[1], 0) / pairs.length;
  const ssTot = pairs.reduce((s, p) => s + (p[1] - meanB) ** 2, 0);
  const ssRes = pairs.reduce((s, p) => s + (p[1] - p[0]) ** 2, 0);

  if (ssTot < 0.001) return null; // Varianza ≈ 0
  return 1 - ssRes / ssTot;
}

/** Calcula Δ% medio entre dos arrays */
export function calcMeanDeltaPct(a: (number | null)[], b: (number | null)[]): number | null {
  let sum = 0;
  let n = 0;
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    const d = deltaPct(a[i], b[i]);
    if (d !== null) {
      sum += d;
      n++;
    }
  }
  return n > 0 ? sum / n : null;
}

/** Calcula estadísticas entre dos series de AC mensual */
function calcPairwiseStats(
  label: string,
  acA: (number | null)[],
  acB: (number | null)[]
): PairwiseStats {
  const n = acA.filter((v, i) => v !== null && acB[i] !== null).length;
  return {
    label,
    rmse: calcRMSE(acA, acB),
    mae: calcMAE(acA, acB),
    r2: calcR2(acA, acB),
    meanDelta_pct: calcMeanDeltaPct(acA, acB),
    n,
  };
}

/** Suma valores no-null de un array, retorna null si todos son null */
function sumNonNull(arr: (number | null)[]): number | null {
  const valid = arr.filter((v): v is number => v !== null);
  return valid.length > 0 ? valid.reduce((s, v) => s + v, 0) : null;
}

/** Promedio ponderado de valores no-null */
function avgNonNull(arr: (number | null)[]): number | null {
  const valid = arr.filter((v): v is number => v !== null);
  return valid.length > 0 ? valid.reduce((s, v) => s + v, 0) / valid.length : null;
}

// ============================================================
// DETECCIÓN DE COHERENCIA DE DATOS
// ============================================================

/**
 * Calcula el coeficiente de variación (CV%) de una serie mensual.
 * CV = (desviación estándar / media) × 100
 * Un CV < 5% indica distribución sospechosamente plana.
 */
function calcCV(values: (number | null)[]): number | null {
  const valid = values.filter((v): v is number => v !== null && v > 0);
  if (valid.length < 6) return null; // Necesitamos al menos 6 meses para evaluar
  const mean = valid.reduce((s, v) => s + v, 0) / valid.length;
  if (mean < 1) return null; // Evitar división por valores muy pequeños
  const variance = valid.reduce((s, v) => s + (v - mean) ** 2, 0) / valid.length;
  const stdDev = Math.sqrt(variance);
  return (stdDev / mean) * 100;
}

/**
 * Detecta problemas de coherencia en las series mensuales de cada fuente.
 * Verifica:
 * 1. Distribución plana (CV < 5%) — indica datos sintéticos/constantes
 * 2. Valores negativos — indica error de cálculo
 * 3. Outliers extremos (valor > 3× la mediana) — indica dato corrupto
 */
function detectDataCoherenceIssues(
  simAC: (number | null)[],
  pvwAC: (number | null)[],
  pvgAC: (number | null)[],
  bipvAC: (number | null)[],
  hasPVWatts: boolean,
  hasPVGIS: boolean,
  hasBIPV: boolean,
): DataCoherenceAlert[] {
  const alerts: DataCoherenceAlert[] = [];

  const sources: Array<{
    name: 'simulator' | 'pvwatts' | 'pvgis' | 'bipv';
    label: string;
    data: (number | null)[];
    active: boolean;
  }> = [
    { name: 'simulator', label: 'Simulador', data: simAC, active: true },
    { name: 'pvwatts', label: 'PVWatts', data: pvwAC, active: hasPVWatts },
    { name: 'pvgis', label: 'PVGIS', data: pvgAC, active: hasPVGIS },
    { name: 'bipv', label: 'IAM+Soiling BIPV', data: bipvAC, active: hasBIPV },
  ];

  for (const src of sources) {
    if (!src.active) continue;
    const valid = src.data.filter((v): v is number => v !== null);
    if (valid.length < 6) continue;

    // 1. Detección de distribución plana (CV < 5%)
    const cv = calcCV(src.data);
    if (cv !== null && cv < 5) {
      const isConstant = cv < 0.1;
      alerts.push({
        source: src.name,
        type: 'flat_distribution',
        cv_pct: cv,
        severity: isConstant ? 'critical' : 'warning',
        message: isConstant
          ? `⚠️ ${src.label}: Producción mensual CONSTANTE (${valid[0]?.toFixed(0)} kWh todos los meses). ` +
            `Esto indica datos sintéticos (división anual/12). Re-ejecute la simulación completa para obtener la distribución estacional real.`
          : `⚠️ ${src.label}: Variación mensual muy baja (CV=${cv.toFixed(1)}%). ` +
            `La producción solar debería variar estacionalmente (CV típico: 15-40%). ` +
            `Verifique que los datos de irradiación de entrada sean horarios reales y no promedios anuales.`,
      });
    }

    // 2. Detección de valores negativos
    const negCount = valid.filter(v => v < 0).length;
    if (negCount > 0) {
      alerts.push({
        source: src.name,
        type: 'negative_values',
        cv_pct: cv ?? 0,
        severity: 'critical',
        message: `❌ ${src.label}: ${negCount} mes(es) con producción negativa. ` +
          `Esto es físicamente imposible y sugiere un error en el cálculo de pérdidas o en los datos de entrada.`,
      });
    }

    // 3. Detección de outliers extremos (> 3× mediana)
    if (valid.length >= 6) {
      const sorted = [...valid].sort((a, b) => a - b);
      const median = sorted[Math.floor(sorted.length / 2)];
      if (median > 0) {
        const extremeOutliers = valid.filter(v => v > median * 3);
        if (extremeOutliers.length > 0) {
          alerts.push({
            source: src.name,
            type: 'extreme_outlier',
            cv_pct: cv ?? 0,
            severity: 'warning',
            message: `⚠️ ${src.label}: ${extremeOutliers.length} mes(es) con producción > 3× la mediana. ` +
              `Verifique que no haya duplicación de área o potencia en la configuración.`,
          });
        }
      }
    }
  }

  return alerts;
}

// ============================================================
// FUNCIÓN PRINCIPAL
// ============================================================

/**
 * Construye los datos de comparación cruzada unificando las tres fuentes.
 * 
 * @param simProduction - Resultado del motor de producción del Simulador
 * @param pvwattsData - Datos PVWatts (puede ser null)
 * @param pvgisData - Datos PVGIS (puede ser null)
 * @param hourlyPR_T_PVWatts - PR_T horario PVWatts (puede ser null)
 * @param hourlyPR_T_PVGIS - PR_T horario PVGIS (puede ser null)
 */
export function buildComparisonData(
  simProduction: AnnualProduction,
  pvwattsData: PVWattsToSimulatorData | null | undefined,
  pvgisData: PVGISToSimulatorData | null | undefined,
  hourlyPR_T_PVWatts: HourlyPR_T_Result | null | undefined,
  hourlyPR_T_PVGIS: HourlyPR_T_Result | null | undefined,
  bipvData?: BIPVToEnergyData | null,
  simKwp?: number,
): ComparisonResult {
  const hasPVWatts = !!pvwattsData;
  const hasPVGIS = !!pvgisData;
  const hasBIPV = !!(bipvData && bipvData.produccionMensualKwh && bipvData.produccionMensualKwh.length === 12);
  const sourceCount = 1 + (hasPVWatts ? 1 : 0) + (hasPVGIS ? 1 : 0) + (hasBIPV ? 1 : 0);

  // ===== NORMALIZACIÓN DE CAPACIDAD BIPV vs SIMULADOR =====
  // Si el kWp del BIPV difiere >20% del kWp del Simulador, escalar la producción BIPV
  // para que la comparación sea justa (misma capacidad instalada)
  let bipvScaleFactor = 1.0;
  let bipvNormalized = false;
  if (hasBIPV && simKwp && simKwp > 0) {
    const bipvKwp = bipvData!.potenciaPicoW / 1000;
    if (bipvKwp > 0) {
      const ratio = bipvKwp / simKwp;
      // Si difieren más del 20%, normalizar
      if (ratio > 1.2 || ratio < 0.8) {
        bipvScaleFactor = simKwp / bipvKwp;
        bipvNormalized = true;
      }
    }
  }

  // Construir filas mensuales
  const rows: ComparisonRow[] = Array.from({ length: 12 }, (_, i) => {
    const simMonth = simProduction.monthlyData[i];
    const pvwMonth = pvwattsData?.monthlyData?.[i];
    const pvgMonth = pvgisData?.monthlyData?.[i];
    const prT_pvwM = hourlyPR_T_PVWatts?.monthly?.[i];
    const prT_pvgM = hourlyPR_T_PVGIS?.monthly?.[i];

    // PR del Simulador: Yf/Yr mensual
    const simRefEnergy = simMonth?.referenceEnergy || 0;
    const simPR = simRefEnergy > 0 ? (simMonth.energyProduced / simRefEnergy) * 100 : null;
    // PR_T del Simulador: usamos el PR_T mensual del motor (promedio ponderado)
    // Aproximación: PR_T_sim ≈ PR_sim / (1 + γ × (T_cell - 25))
    // Pero es mejor usar el valor directo si está disponible

    const simAcMonth = simMonth?.energyProduced ?? null;
    const simulator: SourceMonthlyData = {
      ac_kWh: simAcMonth,
      dc_kWh: simMonth?.dcEnergy ?? null,
      poa_kWhm2: simMonth ? simMonth.rawPOA * getDaysInMonth(i) * 24 / 1000 : null,
      pr_pct: simPR,
      pr_t_pct: null, // El simulador no tiene PR_T mensual directo, se deja null
      tamb_C: simMonth?.avgTemp ?? null,
      tcell_C: simMonth?.cellTemperature ?? null,
      yield_kwh_kwp: (simAcMonth !== null && simKwp && simKwp > 0) ? simAcMonth / simKwp : null,
    };

    const pvwAcMonth = pvwMonth?.ac_kWh ?? null;
    const pvwatts: SourceMonthlyData = {
      ac_kWh: pvwAcMonth,
      dc_kWh: pvwMonth?.dc_kWh ?? null,
      poa_kWhm2: pvwMonth?.poa_kWhm2 ?? null,
      pr_pct: prT_pvwM ? prT_pvwM.pr * 100 : null,
      pr_t_pct: prT_pvwM ? prT_pvwM.pr_t * 100 : null,
      tamb_C: pvwMonth?.tamb_C ?? null,
      tcell_C: pvwMonth?.tcell_C ?? (prT_pvwM?.avgTcell ?? null),
      yield_kwh_kwp: (pvwAcMonth !== null && simKwp && simKwp > 0) ? pvwAcMonth / simKwp : null,
    };

    const pvgAcMonth = pvgMonth?.productionCorrectedAC_kWh ?? null;
    const pvgis: SourceMonthlyData = {
      ac_kWh: pvgAcMonth,
      dc_kWh: null, // PVGIS no reporta DC separado
      poa_kWhm2: pvgMonth?.irradiationPOA_kWhm2 ?? null,
      pr_pct: prT_pvgM ? prT_pvgM.pr * 100 : null,
      pr_t_pct: prT_pvgM ? prT_pvgM.pr_t * 100 : null,
      tamb_C: pvgMonth?.temperature ?? null,
      tcell_C: prT_pvgM?.avgTcell ?? null,
      yield_kwh_kwp: (pvgAcMonth !== null && simKwp && simKwp > 0) ? pvgAcMonth / simKwp : null,
    };

    const bipvRawAc = hasBIPV ? (bipvData!.produccionMensualKwh[i] ?? null) : null;
    const bipvAcNormalized = bipvRawAc !== null ? bipvRawAc * bipvScaleFactor : null;
    const bipvKwpVal = hasBIPV ? bipvData!.potenciaPicoW / 1000 : null;
    const bipv: SourceMonthlyData = {
      ac_kWh: bipvAcNormalized,
      dc_kWh: null,
      poa_kWhm2: null,
      pr_pct: null,
      pr_t_pct: null,
      tamb_C: null,
      tcell_C: null,
      yield_kwh_kwp: (bipvRawAc !== null && bipvKwpVal && bipvKwpVal > 0) ? bipvRawAc / bipvKwpVal : null,
    };

    return {
      month: i + 1,
      monthName: MONTH_NAMES[i],
      simulator,
      pvwatts,
      pvgis,
      bipv,
      delta_sim_pvw_pct: deltaPct(simulator.ac_kWh, pvwatts.ac_kWh),
      delta_sim_pvg_pct: deltaPct(simulator.ac_kWh, pvgis.ac_kWh),
      delta_pvw_pvg_pct: deltaPct(pvwatts.ac_kWh, pvgis.ac_kWh),
      delta_sim_bipv_pct: deltaPct(simulator.ac_kWh, bipv.ac_kWh),
      // Δ Yield (comparación de rendimiento específico)
      delta_yield_sim_pvw_pct: deltaPct(simulator.yield_kwh_kwp, pvwatts.yield_kwh_kwp),
      delta_yield_sim_pvg_pct: deltaPct(simulator.yield_kwh_kwp, pvgis.yield_kwh_kwp),
      delta_yield_pvw_pvg_pct: deltaPct(pvwatts.yield_kwh_kwp, pvgis.yield_kwh_kwp),
      delta_yield_sim_bipv_pct: deltaPct(simulator.yield_kwh_kwp, bipv.yield_kwh_kwp),
    };
  });

  // Resúmenes anuales
  const annualSimulator: SourceAnnualSummary = {
    ac_kWh: simProduction.totalACEnergy,
    dc_kWh: simProduction.totalDCEnergy,
    poa_kWhm2: sumNonNull(rows.map(r => r.simulator.poa_kWhm2)),
    pr_pct: simProduction.performanceRatio, // ya en %
    pr_t_pct: simProduction.prTemperatureCorrected, // ya en %
    tamb_C: avgNonNull(rows.map(r => r.simulator.tamb_C)),
    tcell_C: avgNonNull(rows.map(r => r.simulator.tcell_C)),
    yield_kwh_kwp: (simProduction.totalACEnergy !== null && simKwp && simKwp > 0) ? simProduction.totalACEnergy / simKwp : null,
  };

  const annualPVWatts: SourceAnnualSummary = {
    ac_kWh: pvwattsData?.annualAC_kWh ?? null,
    dc_kWh: pvwattsData?.annualDC_kWh ?? null,
    poa_kWhm2: pvwattsData?.annualPOA_kWhm2 ?? null,
    pr_pct: hourlyPR_T_PVWatts ? hourlyPR_T_PVWatts.annualPR * 100 : null,
    pr_t_pct: hourlyPR_T_PVWatts ? hourlyPR_T_PVWatts.annualPR_T * 100 : null,
    tamb_C: avgNonNull(rows.map(r => r.pvwatts.tamb_C)),
    tcell_C: hourlyPR_T_PVWatts?.avgCellTempWeighted ?? null,
    yield_kwh_kwp: (pvwattsData?.annualAC_kWh != null && simKwp && simKwp > 0) ? pvwattsData.annualAC_kWh / simKwp : null,
  };

  const annualPVGIS: SourceAnnualSummary = {
    ac_kWh: pvgisData?.annualProductionCorrected ?? null,
    dc_kWh: null,
    poa_kWhm2: pvgisData?.annualIrradiationPOA ?? null,
    pr_pct: hourlyPR_T_PVGIS ? hourlyPR_T_PVGIS.annualPR * 100 : null,
    pr_t_pct: hourlyPR_T_PVGIS ? hourlyPR_T_PVGIS.annualPR_T * 100 : null,
    tamb_C: avgNonNull(rows.map(r => r.pvgis.tamb_C)),
    tcell_C: hourlyPR_T_PVGIS?.avgCellTempWeighted ?? null,
    yield_kwh_kwp: (pvgisData?.annualProductionCorrected != null && simKwp && simKwp > 0) ? pvgisData.annualProductionCorrected / simKwp : null,
  };

  const bipvKwpAnnual = hasBIPV ? bipvData!.potenciaPicoW / 1000 : null;
  const annualBIPV: SourceAnnualSummary = {
    ac_kWh: hasBIPV ? bipvData!.energiaAnualKwh * bipvScaleFactor : null,
    dc_kWh: null,
    poa_kWhm2: null,
    pr_pct: null,
    pr_t_pct: null,
    tamb_C: null,
    tcell_C: null,
    yield_kwh_kwp: (hasBIPV && bipvKwpAnnual && bipvKwpAnnual > 0) ? bipvData!.energiaAnualKwh / bipvKwpAnnual : null,
  };

  // Estadísticas por pares (AC mensual)
  const simAC = rows.map(r => r.simulator.ac_kWh);
  const pvwAC = rows.map(r => r.pvwatts.ac_kWh);
  const pvgAC = rows.map(r => r.pvgis.ac_kWh);
  const bipvAC = rows.map(r => r.bipv.ac_kWh);

  const stats = {
    sim_vs_pvwatts: calcPairwiseStats('Simulador vs PVWatts', simAC, pvwAC),
    sim_vs_pvgis: calcPairwiseStats('Simulador vs PVGIS', simAC, pvgAC),
    pvwatts_vs_pvgis: calcPairwiseStats('PVWatts vs PVGIS', pvwAC, pvgAC),
    sim_vs_bipv: calcPairwiseStats('Simulador vs IAM+Soiling BIPV', simAC, bipvAC),
  };

  // Detección de coherencia de datos mensuales
  const coherenceAlerts: DataCoherenceAlert[] = detectDataCoherenceIssues(
    simAC, pvwAC, pvgAC, bipvAC, hasPVWatts, hasPVGIS, hasBIPV
  );

  return {
    rows,
    annualSimulator,
    annualPVWatts,
    annualPVGIS,
    annualBIPV,
    stats,
    hasPVWatts,
    hasPVGIS,
    hasBIPV,
    sourceCount,
    coherenceAlerts,
    bipvNormalized,
    bipvScaleFactor,
    bipvKwp: hasBIPV ? bipvData!.potenciaPicoW / 1000 : null,
    simKwp: simKwp ?? null,
  };
}

// ============================================================
// EXPORTAR CSV
// ============================================================

/**
 * Genera CSV de la tabla comparativa con BOM UTF-8 para Excel
 */
export function exportComparisonCSV(comparison: ComparisonResult): string {
  const BOM = '\uFEFF';
  const sep = ',';

  // Cabecera
  const headers = [
    'Mes',
    'Sim AC (kWh)', 'Sim DC (kWh)', 'Sim POA (kWh/m²)', 'Sim PR (%)', 'Sim T_amb (°C)', 'Sim T_cell (°C)',
  ];
  if (comparison.hasPVWatts) {
    headers.push(
      'PVW AC (kWh)', 'PVW DC (kWh)', 'PVW POA (kWh/m²)', 'PVW PR (%)', 'PVW PR_T (%)', 'PVW T_amb (°C)', 'PVW T_cell (°C)',
      'Δ% Sim-PVW'
    );
  }
  if (comparison.hasPVGIS) {
    headers.push(
      'PVG AC (kWh)', 'PVG POA (kWh/m²)', 'PVG PR (%)', 'PVG PR_T (%)', 'PVG T_amb (°C)', 'PVG T_cell (°C)',
      'Δ% Sim-PVG'
    );
  }
  if (comparison.hasPVWatts && comparison.hasPVGIS) {
    headers.push('Δ% PVW-PVG');
  }

  const lines: string[] = [headers.join(sep)];

  // Filas mensuales
  for (const r of comparison.rows) {
    const vals: string[] = [
      r.monthName,
      fmt(r.simulator.ac_kWh, 1), fmt(r.simulator.dc_kWh, 1), fmt(r.simulator.poa_kWhm2, 1),
      fmt(r.simulator.pr_pct, 1), fmt(r.simulator.tamb_C, 1), fmt(r.simulator.tcell_C, 1),
    ];
    if (comparison.hasPVWatts) {
      vals.push(
        fmt(r.pvwatts.ac_kWh, 1), fmt(r.pvwatts.dc_kWh, 1), fmt(r.pvwatts.poa_kWhm2, 1),
        fmt(r.pvwatts.pr_pct, 1), fmt(r.pvwatts.pr_t_pct, 1), fmt(r.pvwatts.tamb_C, 1), fmt(r.pvwatts.tcell_C, 1),
        fmt(r.delta_sim_pvw_pct, 1)
      );
    }
    if (comparison.hasPVGIS) {
      vals.push(
        fmt(r.pvgis.ac_kWh, 1), fmt(r.pvgis.poa_kWhm2, 1),
        fmt(r.pvgis.pr_pct, 1), fmt(r.pvgis.pr_t_pct, 1), fmt(r.pvgis.tamb_C, 1), fmt(r.pvgis.tcell_C, 1),
        fmt(r.delta_sim_pvg_pct, 1)
      );
    }
    if (comparison.hasPVWatts && comparison.hasPVGIS) {
      vals.push(fmt(r.delta_pvw_pvg_pct, 1));
    }
    lines.push(vals.join(sep));
  }

  // Fila anual
  const annual: string[] = [
    'ANUAL',
    fmt(comparison.annualSimulator.ac_kWh, 0), fmt(comparison.annualSimulator.dc_kWh, 0),
    fmt(comparison.annualSimulator.poa_kWhm2, 0), fmt(comparison.annualSimulator.pr_pct, 1),
    fmt(comparison.annualSimulator.tamb_C, 1), fmt(comparison.annualSimulator.tcell_C, 1),
  ];
  if (comparison.hasPVWatts) {
    annual.push(
      fmt(comparison.annualPVWatts.ac_kWh, 0), fmt(comparison.annualPVWatts.dc_kWh, 0),
      fmt(comparison.annualPVWatts.poa_kWhm2, 0), fmt(comparison.annualPVWatts.pr_pct, 1),
      fmt(comparison.annualPVWatts.pr_t_pct, 1), fmt(comparison.annualPVWatts.tamb_C, 1),
      fmt(comparison.annualPVWatts.tcell_C, 1),
      fmt(deltaPct(comparison.annualSimulator.ac_kWh, comparison.annualPVWatts.ac_kWh), 1)
    );
  }
  if (comparison.hasPVGIS) {
    annual.push(
      fmt(comparison.annualPVGIS.ac_kWh, 0), fmt(comparison.annualPVGIS.poa_kWhm2, 0),
      fmt(comparison.annualPVGIS.pr_pct, 1), fmt(comparison.annualPVGIS.pr_t_pct, 1),
      fmt(comparison.annualPVGIS.tamb_C, 1), fmt(comparison.annualPVGIS.tcell_C, 1),
      fmt(deltaPct(comparison.annualSimulator.ac_kWh, comparison.annualPVGIS.ac_kWh), 1)
    );
  }
  if (comparison.hasPVWatts && comparison.hasPVGIS) {
    annual.push(fmt(deltaPct(comparison.annualPVWatts.ac_kWh, comparison.annualPVGIS.ac_kWh), 1));
  }
  lines.push(annual.join(sep));

  return BOM + lines.join('\n');
}

function fmt(v: number | null | undefined, decimals: number): string {
  if (v === null || v === undefined) return '';
  return v.toFixed(decimals);
}

function getDaysInMonth(monthIndex: number): number {
  const days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return days[monthIndex] ?? 30;
}
