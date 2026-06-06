/**
 * Motor de Diagnóstico de Rendimiento para Mediciones de Campo
 *
 * Analiza mediciones de campo y detecta desviaciones significativas
 * en PR, P_exp y temperatura, generando alertas con causas probables
 * y recomendaciones de acción.
 *
 * Umbrales basados en estándares IEC 61724 y modelo Mulcue-Llanos.
 */

// ============================================================
// TIPOS
// ============================================================

export type AlertSeverity = 'ok' | 'leve' | 'moderada' | 'severa' | 'critica';

export interface DiagnosticCause {
  /** Identificador de la causa */
  id: string;
  /** Nombre de la causa */
  name: string;
  /** Probabilidad estimada (0-1) */
  probability: number;
  /** Descripción detallada */
  description: string;
  /** Recomendación de acción */
  recommendation: string;
  /** Categoría de la causa */
  category: 'ambiental' | 'equipo' | 'instalacion' | 'mantenimiento' | 'diseno';
  /** Icono representativo */
  icon: string;
}

export interface PerformanceAlert {
  /** Nivel de severidad */
  severity: AlertSeverity;
  /** Color asociado */
  color: string;
  /** Color de fondo */
  bgColor: string;
  /** Título de la alerta */
  title: string;
  /** Mensaje principal */
  message: string;
  /** Desviación del PR respecto al esperado (%) */
  prDeviation: number;
  /** PR medido */
  prMeasured: number;
  /** PR esperado (referencia) */
  prExpected: number;
  /** Causas probables ordenadas por probabilidad */
  causes: DiagnosticCause[];
  /** Puntuación de salud general (0-100) */
  healthScore: number;
}

export interface DiagnosticInput {
  /** PR medido en campo (0-1) */
  prMeasured: number;
  /** GHI medido en campo (W/m²) */
  ghiField: number;
  /** Temperatura ambiente medida (°C) */
  tempAmbient: number;
  /** Temperatura de celda (°C) */
  tempCell: number;
  /** Si la T_cell fue medida manualmente */
  tempCellManual: boolean;
  /** P_exp calculado (W) */
  pExp: number;
  /** P_nom STC del panel (W) */
  pNom: number;
  /** Coeficiente de temperatura (%/°C, negativo) */
  tempCoeff: number;
  /** NOCT del panel (°C) */
  noct: number;
  /** Factor de pérdida por temperatura (0-1) */
  tempLoss: number;
  /** Tipo de instalación (opcional) */
  installationType?: string;
  /** Pérdidas del sistema configuradas (%) */
  systemLosses?: {
    soiling?: number;
    mismatch?: number;
    dcWiring?: number;
    acWiring?: number;
    inverterEfficiency?: number;
  };
  /** Latitud de la ubicación */
  latitude?: number;
}

// ============================================================
// CONSTANTES
// ============================================================

/** Umbrales de desviación de PR (%) */
export const PR_THRESHOLDS = {
  ok: 10,        // < 10% desviación = OK
  leve: 15,      // 10-15% = alerta leve
  moderada: 25,  // 15-25% = alerta moderada
  severa: 40,    // 25-40% = alerta severa
  critica: 100,  // > 40% = alerta crítica
} as const;

/** PR de referencia esperado para sistemas bien diseñados */
export const PR_REFERENCE = 0.80;

/** Temperatura STC de referencia */
const T_STC = 25;

/** GHI STC de referencia */
const G_STC = 1000;

// ============================================================
// FUNCIONES DE DIAGNÓSTICO
// ============================================================

/**
 * Analiza una medición de campo y genera alertas de rendimiento.
 *
 * El análisis compara el PR medido contra el PR esperado para las
 * condiciones de campo (GHI, temperatura), y si la desviación supera
 * los umbrales, genera una alerta con causas probables ponderadas.
 */
export function diagnosePerformance(input: DiagnosticInput): PerformanceAlert {
  const {
    prMeasured,
    ghiField,
    tempAmbient,
    tempCell,
    tempCellManual,
    pExp,
    pNom,
    tempCoeff,
    noct,
    tempLoss,
    installationType,
    systemLosses,
    latitude,
  } = input;

  // PR esperado ajustado por condiciones de campo
  // Para condiciones de alta temperatura, el PR esperado baja naturalmente
  const prExpected = calculateExpectedPR(tempAmbient, tempCoeff);

  // Desviación porcentual del PR
  const prDeviation = prExpected > 0
    ? ((prExpected - prMeasured) / prExpected) * 100
    : 0;

  // Determinar severidad
  const severity = classifySeverity(prDeviation);

  // Analizar causas probables
  const causes = analyzeCauses(input, prDeviation, prExpected);

  // Calcular puntuación de salud (0-100)
  const healthScore = calculateHealthScore(prMeasured, prExpected, prDeviation);

  // Generar alerta
  return {
    severity,
    ...getSeverityStyle(severity),
    title: getSeverityTitle(severity, prDeviation),
    message: getSeverityMessage(severity, prMeasured, prExpected, prDeviation),
    prDeviation: Math.round(prDeviation * 10) / 10,
    prMeasured: Math.round(prMeasured * 1000) / 1000,
    prExpected: Math.round(prExpected * 1000) / 1000,
    causes: causes.sort((a, b) => b.probability - a.probability),
    healthScore: Math.round(healthScore),
  };
}

/**
 * Calcula el PR esperado ajustado por temperatura ambiente.
 * Basado en el modelo Mulcue-Llanos simplificado.
 */
function calculateExpectedPR(tempAmbient: number, tempCoeff: number): number {
  const gammaDecimal = Math.abs(tempCoeff) > 0.01
    ? tempCoeff / 100
    : tempCoeff;

  // PR base del modelo Mulcue-Llanos
  const ksist = 0.82;
  const prMax = ksist * (1 + gammaDecimal * (1.12 * tempAmbient - 10));
  const prCorrected = prMax + 0.0006 * tempAmbient - 0.017;

  return Math.max(0.10, Math.min(0.95, prCorrected));
}

/**
 * Clasifica la severidad según la desviación del PR.
 */
function classifySeverity(deviationPercent: number): AlertSeverity {
  const absDeviation = Math.abs(deviationPercent);
  if (absDeviation < PR_THRESHOLDS.ok) return 'ok';
  if (absDeviation < PR_THRESHOLDS.leve) return 'leve';
  if (absDeviation < PR_THRESHOLDS.moderada) return 'moderada';
  if (absDeviation < PR_THRESHOLDS.severa) return 'severa';
  return 'critica';
}

/**
 * Analiza las causas probables de la desviación.
 */
function analyzeCauses(
  input: DiagnosticInput,
  prDeviation: number,
  prExpected: number,
): DiagnosticCause[] {
  const causes: DiagnosticCause[] = [];
  const {
    ghiField,
    tempAmbient,
    tempCell,
    tempCellManual,
    pExp,
    pNom,
    tempCoeff,
    noct,
    tempLoss,
    installationType,
    systemLosses,
    latitude,
  } = input;

  // Si no hay desviación significativa, no hay causas
  if (Math.abs(prDeviation) < PR_THRESHOLDS.ok) return causes;

  // ---- 1. SUCIEDAD / SOILING ----
  const soilingProb = calculateSoilingProbability(
    prDeviation,
    installationType,
    systemLosses?.soiling,
    latitude,
  );
  if (soilingProb > 0.05) {
    causes.push({
      id: 'soiling',
      name: 'Suciedad en paneles',
      probability: soilingProb,
      description: `La acumulación de polvo, hojas, excrementos de aves o contaminación reduce la irradiancia efectiva sobre las celdas. ${
        installationType === 'facade_vertical'
          ? 'Las fachadas verticales tienen auto-limpieza parcial por lluvia.'
          : installationType === 'carport'
            ? 'Los carports son propensos a mayor acumulación de polvo por tráfico vehicular.'
            : 'La inclinación del panel afecta la capacidad de auto-limpieza.'
      }`,
      recommendation: 'Realizar limpieza de los módulos con agua desmineralizada y esponja suave. Verificar frecuencia de limpieza recomendada para la zona.',
      category: 'mantenimiento',
      icon: '🧹',
    });
  }

  // ---- 2. SOMBREADO PARCIAL ----
  const shadingProb = calculateShadingProbability(
    prDeviation,
    ghiField,
    installationType,
  );
  if (shadingProb > 0.05) {
    causes.push({
      id: 'partial_shading',
      name: 'Sombreado parcial',
      probability: shadingProb,
      description: `Obstrucciones parciales (edificios, árboles, antenas, cables) generan puntos calientes y reducen la producción de toda la cadena de módulos conectados en serie. ${
        ghiField < 400
          ? 'La baja irradiancia medida sugiere posible sombreado activo durante la medición.'
          : 'Verificar si hay obstrucciones que generen sombras intermitentes.'
      }`,
      recommendation: 'Inspeccionar visualmente el campo solar en la hora de la medición. Usar cámara termográfica para detectar puntos calientes. Considerar optimizadores de potencia o microinversores.',
      category: 'instalacion',
      icon: '🏢',
    });
  }

  // ---- 3. DEGRADACIÓN DEL MÓDULO ----
  const degradationProb = calculateDegradationProbability(prDeviation, pExp, pNom);
  if (degradationProb > 0.05) {
    causes.push({
      id: 'module_degradation',
      name: 'Degradación del módulo',
      probability: degradationProb,
      description: 'Los módulos fotovoltaicos pierden eficiencia con el tiempo (LID, PID, microfisuras, delaminación, amarillamiento del encapsulante). La degradación típica es 0.5-0.8%/año para cristalino y 1-2%/año para película delgada.',
      recommendation: 'Comparar con mediciones anteriores para verificar tendencia. Solicitar inspección con electroluminiscencia (EL) para detectar microfisuras. Verificar garantía de potencia del fabricante.',
      category: 'equipo',
      icon: '📉',
    });
  }

  // ---- 4. TEMPERATURA EXCESIVA ----
  const tempProb = calculateTempProbability(
    tempCell,
    tempAmbient,
    noct,
    ghiField,
    tempCellManual,
    prDeviation,
  );
  if (tempProb > 0.05) {
    causes.push({
      id: 'excessive_temp',
      name: 'Temperatura excesiva de celda',
      probability: tempProb,
      description: `La temperatura de celda de ${tempCell.toFixed(1)}°C ${
        tempCell > 70 ? 'es extremadamente alta' : tempCell > 55 ? 'es elevada' : 'está por encima de lo esperado'
      }. La pérdida por temperatura es ${((1 - tempLoss) * 100).toFixed(1)}%. ${
        !tempCellManual
          ? 'La T_cell fue estimada con NOCT; una medición directa con termopar sería más precisa.'
          : 'La T_cell fue medida directamente, lo cual es más confiable.'
      }`,
      recommendation: 'Verificar ventilación posterior de los módulos. Asegurar separación mínima de 10cm entre módulo y superficie. Considerar paneles con mejor coeficiente de temperatura. En climas cálidos, priorizar tecnologías HJT o CIGS.',
      category: 'ambiental',
      icon: '🌡️',
    });
  }

  // ---- 5. PROBLEMAS DE INVERSOR ----
  const inverterProb = calculateInverterProbability(prDeviation, systemLosses);
  if (inverterProb > 0.05) {
    causes.push({
      id: 'inverter_issue',
      name: 'Eficiencia del inversor',
      probability: inverterProb,
      description: 'El inversor puede estar operando fuera de su rango óptimo de eficiencia, especialmente a cargas parciales (<30% de capacidad nominal) o cuando la tensión DC está fuera del rango MPPT óptimo.',
      recommendation: 'Verificar que el inversor esté dimensionado correctamente (ratio DC/AC entre 1.0 y 1.3). Revisar logs del inversor para errores o limitaciones de potencia. Verificar que la tensión de string esté dentro del rango MPPT.',
      category: 'equipo',
      icon: '⚡',
    });
  }

  // ---- 6. CABLEADO Y CONEXIONES ----
  const wiringProb = calculateWiringProbability(prDeviation, installationType, systemLosses);
  if (wiringProb > 0.05) {
    causes.push({
      id: 'wiring_losses',
      name: 'Pérdidas en cableado/conexiones',
      probability: wiringProb,
      description: `Las pérdidas en cableado DC y AC pueden ser significativas, especialmente en ${
        installationType === 'facade_vertical' || installationType === 'facade_inclined'
          ? 'fachadas donde las distancias de cableado son mayores'
          : 'instalaciones con recorridos largos de cable'
      }. Conexiones flojas o corroídas aumentan la resistencia.`,
      recommendation: 'Inspeccionar conexiones MC4 y terminales. Medir caída de tensión en strings con multímetro. Verificar que la sección del cable sea adecuada para la distancia. Revisar puesta a tierra.',
      category: 'instalacion',
      icon: '🔌',
    });
  }

  // ---- 7. MISMATCH DE MÓDULOS ----
  const mismatchProb = calculateMismatchProbability(prDeviation, installationType);
  if (mismatchProb > 0.05) {
    causes.push({
      id: 'module_mismatch',
      name: 'Desajuste entre módulos (mismatch)',
      probability: mismatchProb,
      description: 'Diferencias de rendimiento entre módulos del mismo string reducen la producción total. Puede deberse a tolerancias de fabricación, envejecimiento diferencial, o sombreado parcial que afecta solo algunos módulos.',
      recommendation: 'Medir corriente de cortocircuito (Isc) de cada string para detectar módulos débiles. Considerar reordenar módulos por potencia medida. Evaluar uso de optimizadores de potencia.',
      category: 'diseno',
      icon: '🔀',
    });
  }

  // ---- 8. BAJA IRRADIANCIA ----
  if (ghiField < 300 && prDeviation > 10) {
    causes.push({
      id: 'low_irradiance',
      name: 'Baja irradiancia (condiciones nubladas)',
      probability: Math.min(0.7, ghiField < 200 ? 0.65 : 0.4),
      description: `La irradiancia medida de ${ghiField} W/m² es significativamente inferior a las condiciones STC (1000 W/m²). A baja irradiancia, los inversores operan con menor eficiencia y las pérdidas relativas del sistema son proporcionalmente mayores.`,
      recommendation: 'Esta es una condición ambiental normal, no un defecto del sistema. Repetir la medición en condiciones de cielo despejado (GHI > 700 W/m²) para una evaluación más representativa.',
      category: 'ambiental',
      icon: '☁️',
    });
  }

  return causes;
}

// ============================================================
// FUNCIONES AUXILIARES DE PROBABILIDAD
// ============================================================

function calculateSoilingProbability(
  prDeviation: number,
  installationType?: string,
  soilingLoss?: number,
  latitude?: number,
): number {
  let base = 0;
  if (prDeviation > 15) base = 0.35;
  else if (prDeviation > 10) base = 0.20;
  else return 0;

  // Ajustar por tipo de instalación
  if (installationType === 'carport') base += 0.15; // Más polvo por tráfico
  if (installationType === 'rooftop_flat') base += 0.10; // Menos auto-limpieza
  if (installationType === 'facade_vertical') base -= 0.10; // Auto-limpieza por lluvia

  // Ajustar por zona tropical (más polvo/humedad)
  if (latitude !== undefined && Math.abs(latitude) < 15) base += 0.05;

  // Si las pérdidas por soiling configuradas son altas, más probable
  if (soilingLoss !== undefined && soilingLoss > 3) base += 0.10;

  return Math.max(0, Math.min(0.85, base));
}

function calculateShadingProbability(
  prDeviation: number,
  ghiField: number,
  installationType?: string,
): number {
  let base = 0;
  if (prDeviation > 25) base = 0.45;
  else if (prDeviation > 15) base = 0.30;
  else if (prDeviation > 10) base = 0.15;
  else return 0;

  // Baja irradiancia sugiere sombreado
  if (ghiField < 400) base += 0.20;
  else if (ghiField < 600) base += 0.10;

  // Fachadas tienen más riesgo de sombreado por edificios adyacentes
  if (installationType === 'facade_vertical' || installationType === 'facade_inclined') {
    base += 0.15;
  }

  return Math.max(0, Math.min(0.90, base));
}

function calculateDegradationProbability(
  prDeviation: number,
  pExp: number,
  pNom: number,
): number {
  let base = 0;
  if (prDeviation > 20) base = 0.25;
  else if (prDeviation > 15) base = 0.15;
  else return 0;

  // Si P_exp es significativamente menor que P_nom (ajustado por condiciones)
  const pExpRatio = pExp / pNom;
  if (pExpRatio < 0.5) base += 0.15;
  else if (pExpRatio < 0.7) base += 0.10;

  return Math.max(0, Math.min(0.70, base));
}

function calculateTempProbability(
  tempCell: number,
  tempAmbient: number,
  noct: number,
  ghiField: number,
  tempCellManual: boolean,
  prDeviation: number,
): number {
  if (prDeviation < 10) return 0;

  let base = 0;

  // Temperatura de celda excesiva
  if (tempCell > 70) base = 0.50;
  else if (tempCell > 60) base = 0.35;
  else if (tempCell > 50) base = 0.20;
  else return 0;

  // Si la T_cell es mucho mayor que la esperada por NOCT
  const expectedTcell = tempAmbient + (noct - 20) * (ghiField / 800);
  if (tempCellManual && tempCell > expectedTcell + 10) {
    base += 0.15; // Ventilación deficiente probable
  }

  // NOCT alto indica panel que se calienta más
  if (noct > 47) base += 0.10;

  return Math.max(0, Math.min(0.80, base));
}

function calculateInverterProbability(
  prDeviation: number,
  systemLosses?: DiagnosticInput['systemLosses'],
): number {
  if (prDeviation < 15) return 0;

  let base = 0;
  if (prDeviation > 30) base = 0.30;
  else if (prDeviation > 20) base = 0.20;
  else base = 0.10;

  // Si la eficiencia del inversor configurada es baja
  if (systemLosses?.inverterEfficiency !== undefined && systemLosses.inverterEfficiency > 5) {
    base += 0.10;
  }

  return Math.max(0, Math.min(0.60, base));
}

function calculateWiringProbability(
  prDeviation: number,
  installationType?: string,
  systemLosses?: DiagnosticInput['systemLosses'],
): number {
  if (prDeviation < 15) return 0;

  let base = 0.10;

  // Fachadas tienen cableado más largo
  if (installationType === 'facade_vertical' || installationType === 'facade_inclined') {
    base += 0.15;
  }

  // Pérdidas de cableado configuradas altas
  const dcLoss = systemLosses?.dcWiring ?? 0;
  const acLoss = systemLosses?.acWiring ?? 0;
  if (dcLoss + acLoss > 4) base += 0.10;

  return Math.max(0, Math.min(0.50, base));
}

function calculateMismatchProbability(
  prDeviation: number,
  installationType?: string,
): number {
  if (prDeviation < 15) return 0;

  let base = 0.10;

  // BIPV integrado tiene más mismatch por orientaciones mixtas
  if (installationType === 'facade_vertical' || installationType === 'facade_inclined') {
    base += 0.15;
  }

  if (prDeviation > 25) base += 0.10;

  return Math.max(0, Math.min(0.50, base));
}

// ============================================================
// FUNCIONES DE PRESENTACIÓN
// ============================================================

function getSeverityStyle(severity: AlertSeverity): { color: string; bgColor: string } {
  switch (severity) {
    case 'ok': return { color: '#16a34a', bgColor: '#f0fdf4' };
    case 'leve': return { color: '#ca8a04', bgColor: '#fefce8' };
    case 'moderada': return { color: '#ea580c', bgColor: '#fff7ed' };
    case 'severa': return { color: '#dc2626', bgColor: '#fef2f2' };
    case 'critica': return { color: '#991b1b', bgColor: '#fef2f2' };
  }
}

function getSeverityTitle(severity: AlertSeverity, deviation: number): string {
  switch (severity) {
    case 'ok': return 'Rendimiento Normal';
    case 'leve': return 'Desviación Leve Detectada';
    case 'moderada': return 'Alerta de Rendimiento';
    case 'severa': return 'Alerta Severa de Rendimiento';
    case 'critica': return 'Alerta Crítica — Rendimiento Muy Bajo';
  }
}

function getSeverityMessage(
  severity: AlertSeverity,
  prMeasured: number,
  prExpected: number,
  deviation: number,
): string {
  const prMeasuredPct = (prMeasured * 100).toFixed(1);
  const prExpectedPct = (prExpected * 100).toFixed(1);
  const devPct = Math.abs(deviation).toFixed(1);

  switch (severity) {
    case 'ok':
      return `El PR medido (${prMeasuredPct}%) está dentro del rango esperado (${prExpectedPct}%). El sistema opera correctamente.`;
    case 'leve':
      return `El PR medido (${prMeasuredPct}%) se desvía ${devPct}% del esperado (${prExpectedPct}%). Monitorear evolución.`;
    case 'moderada':
      return `El PR medido (${prMeasuredPct}%) se desvía ${devPct}% del esperado (${prExpectedPct}%). Se recomienda inspección.`;
    case 'severa':
      return `El PR medido (${prMeasuredPct}%) se desvía ${devPct}% del esperado (${prExpectedPct}%). Requiere atención inmediata.`;
    case 'critica':
      return `El PR medido (${prMeasuredPct}%) se desvía ${devPct}% del esperado (${prExpectedPct}%). El sistema tiene un problema grave que requiere intervención urgente.`;
  }
}

function calculateHealthScore(
  prMeasured: number,
  prExpected: number,
  deviation: number,
): number {
  // Score base: 100 si PR = esperado, decrece con la desviación
  if (deviation <= 0) return 100; // PR mejor que esperado

  // Escala no lineal: penaliza más las desviaciones grandes
  const score = 100 * Math.exp(-deviation / 30);
  return Math.max(0, Math.min(100, score));
}

/**
 * Genera un resumen rápido de la alerta para mostrar en la tabla del historial.
 */
export function getAlertBadge(prMeasured: number, tempAmbient: number, tempCoeff: number): {
  severity: AlertSeverity;
  color: string;
  bgColor: string;
  label: string;
  icon: string;
} {
  const prExpected = calculateExpectedPR(tempAmbient, tempCoeff);
  const deviation = prExpected > 0
    ? ((prExpected - prMeasured) / prExpected) * 100
    : 0;
  const severity = classifySeverity(deviation);

  const styles = getSeverityStyle(severity);
  const labels: Record<AlertSeverity, string> = {
    ok: 'OK',
    leve: 'Leve',
    moderada: 'Alerta',
    severa: 'Severa',
    critica: 'Crítica',
  };
  const icons: Record<AlertSeverity, string> = {
    ok: '✓',
    leve: '⚠',
    moderada: '⚠',
    severa: '⛔',
    critica: '🚨',
  };

  return {
    severity,
    ...styles,
    label: labels[severity],
    icon: icons[severity],
  };
}
