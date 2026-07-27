import { useState, useMemo } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp, Wrench, Thermometer, CloudRain, Sun, Layers, Zap, Info } from 'lucide-react';
import type { ComparisonResult, ComparisonRow } from '@/lib/crossValidation';

interface BIPVDeviationAlertProps {
  comparison: ComparisonResult;
  /** Callback para re-sincronizar parámetros BIPV→Simulador cuando Δ% > 50% */
  onResyncParams?: () => void;
  /** Indica si la re-sincronización está en progreso */
  isResyncing?: boolean;
}

interface DeviationCause {
  id: string;
  name: string;
  probability: number;
  description: string;
  recommendation: string;
  icon: React.ReactNode;
  category: 'modelo' | 'ambiental' | 'configuracion' | 'datos';
}

interface FlaggedMonth {
  month: number;
  monthName: string;
  delta: number;
  simAC: number | null;
  bipvAC: number | null;
  direction: 'over' | 'under'; // Simulador produce más o menos que BIPV
}

const THRESHOLD_WARNING = 15;
const THRESHOLD_CRITICAL = 25;

const MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

function analyzeBIPVDeviation(rows: ComparisonRow[]): {
  flaggedMonths: FlaggedMonth[];
  maxDelta: number;
  avgDelta: number;
  severity: 'warning' | 'critical' | 'none';
  pattern: 'seasonal' | 'systematic' | 'isolated' | 'none';
  direction: 'over' | 'under' | 'mixed';
} {
  const flaggedMonths: FlaggedMonth[] = [];
  let sumAbsDelta = 0;
  let countValid = 0;

  for (const row of rows) {
    if (row.delta_sim_bipv_pct !== null) {
      const absDelta = Math.abs(row.delta_sim_bipv_pct);
      sumAbsDelta += absDelta;
      countValid++;
      if (absDelta > THRESHOLD_WARNING) {
        flaggedMonths.push({
          month: row.month,
          monthName: row.monthName,
          delta: row.delta_sim_bipv_pct,
          simAC: row.simulator.ac_kWh,
          bipvAC: row.bipv.ac_kWh,
          direction: row.delta_sim_bipv_pct > 0 ? 'over' : 'under',
        });
      }
    }
  }

  const maxDelta = flaggedMonths.length > 0
    ? Math.max(...flaggedMonths.map(m => Math.abs(m.delta)))
    : 0;
  const avgDelta = countValid > 0 ? sumAbsDelta / countValid : 0;

  // Determinar severidad
  const severity = maxDelta > THRESHOLD_CRITICAL ? 'critical'
    : flaggedMonths.length > 0 ? 'warning' : 'none';

  // Detectar patrón
  let pattern: 'seasonal' | 'systematic' | 'isolated' | 'none' = 'none';
  if (flaggedMonths.length >= 8) {
    pattern = 'systematic';
  } else if (flaggedMonths.length >= 3) {
    // Verificar si son meses consecutivos (estacional)
    const months = flaggedMonths.map(m => m.month).sort((a, b) => a - b);
    let consecutive = 0;
    for (let i = 1; i < months.length; i++) {
      if (months[i] - months[i - 1] <= 2) consecutive++;
    }
    pattern = consecutive >= 2 ? 'seasonal' : 'isolated';
  } else if (flaggedMonths.length > 0) {
    pattern = 'isolated';
  }

  // Dirección predominante
  const overCount = flaggedMonths.filter(m => m.direction === 'over').length;
  const underCount = flaggedMonths.filter(m => m.direction === 'under').length;
  const direction = overCount > underCount * 2 ? 'over'
    : underCount > overCount * 2 ? 'under' : 'mixed';

  return { flaggedMonths, maxDelta, avgDelta, severity, pattern, direction };
}

function generateCauses(
  pattern: 'seasonal' | 'systematic' | 'isolated' | 'none',
  direction: 'over' | 'under' | 'mixed',
  avgDelta: number
): DeviationCause[] {
  const causes: DeviationCause[] = [];

  if (direction === 'over' || direction === 'mixed') {
    // Simulador produce MÁS que BIPV
    causes.push({
      id: 'soiling_underestimated',
      name: 'Soiling subestimado en Simulador',
      probability: pattern === 'seasonal' ? 0.85 : 0.6,
      description: 'El Simulador de Energía no aplica pérdidas por soiling estacional. IAM+Soiling incluye un modelo de ensuciamiento que reduce la producción en meses secos.',
      recommendation: 'Aumentar el % de pérdida por suciedad en "Pérdidas Aplicadas" del Simulador (actualmente puede estar en 2-3%, considerar 5-8% para meses secos).',
      icon: <CloudRain className="w-4 h-4" />,
      category: 'modelo',
    });
    causes.push({
      id: 'iam_losses',
      name: 'Pérdidas IAM no modeladas en Simulador',
      probability: 0.7,
      description: 'El modelo IAM (Incidence Angle Modifier) reduce la transmitancia del vidrio BIPV a ángulos de incidencia altos. El Simulador no incluye este efecto.',
      recommendation: 'Considerar agregar 2-4% adicional en "Desajuste" para compensar las pérdidas IAM no modeladas.',
      icon: <Sun className="w-4 h-4" />,
      category: 'modelo',
    });
  }

  if (direction === 'under' || direction === 'mixed') {
    // Simulador produce MENOS que BIPV
    causes.push({
      id: 'losses_overestimated',
      name: 'Pérdidas sobreestimadas en Simulador',
      probability: 0.75,
      description: 'El Simulador aplica pérdidas acumulativas (cableado DC+AC, inversor, mismatch, disponibilidad) que pueden ser excesivas para instalaciones BIPV bien diseñadas.',
      recommendation: 'Revisar los valores de pérdidas en el Simulador. Para BIPV integrado, las pérdidas de cableado suelen ser menores (1-1.5% DC, 1% AC).',
      icon: <Zap className="w-4 h-4" />,
      category: 'configuracion',
    });
    causes.push({
      id: 'temperature_model_diff',
      name: 'Modelo de temperatura diferente',
      probability: 0.6,
      description: 'IAM+Soiling usa un modelo de temperatura de celda diferente al del Simulador. BIPV integrado tiene mejor ventilación trasera que reduce T_cell.',
      recommendation: 'Verificar que el NOCT configurado sea consistente entre ambos módulos. Para BIPV ventilado usar NOCT 42-45°C.',
      icon: <Thermometer className="w-4 h-4" />,
      category: 'modelo',
    });
  }

  if (pattern === 'systematic') {
    causes.push({
      id: 'systematic_bias',
      name: 'Sesgo sistemático entre modelos',
      probability: 0.9,
      description: 'La desviación es consistente en todos los meses, indicando una diferencia fundamental en los supuestos de cálculo entre ambos módulos.',
      recommendation: 'Verificar que la potencia del panel (Wp), el área, y la eficiencia STC sean idénticos en ambos módulos. Revisar si el factor de separación se aplica correctamente.',
      icon: <Layers className="w-4 h-4" />,
      category: 'configuracion',
    });
  }

  if (pattern === 'seasonal') {
    causes.push({
      id: 'seasonal_soiling',
      name: 'Soiling estacional (época seca)',
      probability: 0.8,
      description: 'Los meses con mayor desviación coinciden con la época seca, donde la acumulación de polvo es mayor. IAM+Soiling modela esto pero el Simulador usa un valor fijo anual.',
      recommendation: 'Ajustar la pérdida por suciedad en el Simulador según la estacionalidad: usar 2% en época lluviosa y 6-10% en época seca.',
      icon: <CloudRain className="w-4 h-4" />,
      category: 'ambiental',
    });
  }

  if (avgDelta > 50) {
    // Desalineación crítica de parámetros (>50% indica error de configuración, no solo modelo)
    causes.push({
      id: 'parameter_desync',
      name: '⚠️ Desalineación crítica de parámetros',
      probability: 0.95,
      description: `La desviación promedio es ${avgDelta.toFixed(0)}% — esto excede cualquier diferencia normal entre modelos de simulación. ` +
        `La causa más probable es que el área (m²), la potencia instalada (kWp), o la cantidad de paneles NO coinciden entre el Simulador y el módulo IAM+Soiling BIPV. ` +
        `Posibles causas específicas: (1) El área total BIPV se usó como área de UN panel; (2) La potencia pico del SISTEMA se asignó como potencia de UN panel; ` +
        `(3) El factor de separación (spacing) reduce excesivamente la cantidad de paneles calculada.`,
      recommendation: 'SOLUCIÓN: Vuelva al módulo IAM+Soiling BIPV y re-envíe los datos al Simulador. Si el problema persiste, verifique manualmente: ' +
        '(1) Cantidad de paneles en el Simulador vs área total BIPV / área de un panel; ' +
        '(2) Potencia por panel (debe ser 300-600W, NO miles de watts); ' +
        '(3) Área por panel (debe ser 1.5-2.5 m², NO cientos de m²). ' +
        'Si usa el auto-optimizador, presione "Aplicar configuración óptima" nuevamente para re-sincronizar.',
      icon: <AlertTriangle className="w-4 h-4" />,
      category: 'configuracion',
    });
  } else if (avgDelta > 20) {
    causes.push({
      id: 'data_mismatch',
      name: 'Datos de entrada inconsistentes',
      probability: 0.5,
      description: 'La desviación promedio es alta (>' + avgDelta.toFixed(0) + '%). Puede haber una inconsistencia en los datos meteorológicos o parámetros del panel entre ambos módulos.',
      recommendation: 'Verificar que ambos módulos usan los mismos datos EPW/meteorológicos y el mismo panel. Usar el botón "← Volver al BIPV" para comparar configuraciones.',
      icon: <Info className="w-4 h-4" />,
      category: 'datos',
    });
  }

  // Ordenar por probabilidad descendente
  return causes.sort((a, b) => b.probability - a.probability);
}

export default function BIPVDeviationAlert({ comparison, onResyncParams, isResyncing }: BIPVDeviationAlertProps) {
  const [expanded, setExpanded] = useState(false);

  const analysis = useMemo(() => {
    if (!comparison.hasBIPV) return null;
    return analyzeBIPVDeviation(comparison.rows);
  }, [comparison]);

  if (!analysis || analysis.severity === 'none') return null;

  const causes = useMemo(() => {
    if (!analysis) return [];
    return generateCauses(analysis.pattern, analysis.direction, analysis.avgDelta);
  }, [analysis]);

  const isCritical = analysis.severity === 'critical';
  const borderColor = isCritical ? 'border-red-300' : 'border-amber-300';
  const bgColor = isCritical ? 'bg-red-50' : 'bg-amber-50';
  const headerBg = isCritical ? 'bg-red-100' : 'bg-amber-100';
  const textColor = isCritical ? 'text-red-800' : 'text-amber-800';
  const iconColor = isCritical ? 'text-red-600' : 'text-amber-600';

  const patternLabel = {
    seasonal: '📅 Estacional',
    systematic: '🔄 Sistemático',
    isolated: '📍 Aislado',
    none: '',
  }[analysis.pattern];

  const directionLabel = {
    over: 'Simulador sobreestima vs BIPV',
    under: 'Simulador subestima vs BIPV',
    mixed: 'Desviación mixta (ambas direcciones)',
  }[analysis.direction];

  return (
    <div className={`rounded-lg border ${borderColor} overflow-hidden mt-4`}>
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={`w-full ${headerBg} px-4 py-3 flex items-center justify-between cursor-pointer hover:opacity-90 transition-opacity`}
      >
        <div className="flex items-center gap-3">
          <AlertTriangle className={`w-5 h-5 ${iconColor}`} />
          <div className="text-left">
            <h5 className={`text-sm font-bold ${textColor}`}>
              ⚠️ Desviación Excesiva S-BIPV — {analysis.flaggedMonths.length} mes{analysis.flaggedMonths.length !== 1 ? 'es' : ''} &gt;{THRESHOLD_WARNING}%
            </h5>
            <p className={`text-xs ${textColor} opacity-80 mt-0.5`}>
              Máx: {analysis.maxDelta.toFixed(1)}% | Promedio: {analysis.avgDelta.toFixed(1)}% | Patrón: {patternLabel} | {directionLabel}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-mono px-2 py-0.5 rounded ${isCritical ? 'bg-red-200 text-red-900' : 'bg-amber-200 text-amber-900'}`}>
            {isCritical ? 'CRÍTICO' : 'ADVERTENCIA'}
          </span>
          {expanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
        </div>
      </button>

      {/* Contenido expandible */}
      {expanded && (
        <div className={`${bgColor} px-4 py-4 space-y-4`}>
          {/* Meses flaggeados */}
          <div>
            <h6 className="text-xs font-semibold text-gray-700 mb-2">Meses con desviación &gt;{THRESHOLD_WARNING}%:</h6>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {analysis.flaggedMonths.map(m => (
                <div
                  key={m.month}
                  className={`rounded-md px-2 py-1.5 border text-center ${
                    Math.abs(m.delta) > THRESHOLD_CRITICAL
                      ? 'bg-red-100 border-red-300'
                      : 'bg-amber-100 border-amber-300'
                  }`}
                >
                  <span className="text-xs font-bold text-gray-800">{m.monthName}</span>
                  <p className={`text-sm font-mono font-bold ${m.delta > 0 ? 'text-red-700' : 'text-blue-700'}`}>
                    {m.delta > 0 ? '+' : ''}{m.delta.toFixed(1)}%
                  </p>
                  <p className="text-[9px] text-gray-500">
                    S:{m.simAC?.toFixed(0)} / B:{m.bipvAC?.toFixed(0)}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Causas probables */}
          <div>
            <h6 className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1">
              <Wrench className="w-3.5 h-3.5" /> Causas probables y sugerencias de calibración:
            </h6>
            <div className="space-y-2">
              {causes.map(cause => (
                <div
                  key={cause.id}
                  className="bg-white rounded-md border border-gray-200 p-3"
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-shrink-0 mt-0.5 text-gray-500">{cause.icon}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-bold text-gray-800">{cause.name}</span>
                        <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${
                          cause.probability >= 0.8 ? 'bg-red-100 text-red-700' :
                          cause.probability >= 0.6 ? 'bg-amber-100 text-amber-700' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {(cause.probability * 100).toFixed(0)}% prob.
                        </span>
                        <span className="text-[9px] text-gray-400 capitalize">{cause.category}</span>
                      </div>
                      <p className="text-[10px] text-gray-600 mb-1">{cause.description}</p>
                      <p className="text-[10px] text-blue-700 font-medium bg-blue-50 rounded px-2 py-1">
                        💡 {cause.recommendation}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Botón Re-sincronizar parámetros (solo cuando avgDelta > 50%) */}
          {analysis.avgDelta > 50 && onResyncParams && (
            <div className="bg-blue-50 rounded-md border border-blue-200 p-3">
              <div className="flex items-center justify-between">
                <div>
                  <h6 className="text-xs font-semibold text-blue-800 mb-0.5">
                    ⚡ Corrección automática disponible
                  </h6>
                  <p className="text-[10px] text-blue-700">
                    Re-aplicar datos BIPV al Simulador con sincronización corregida de panel/área/potencia.
                  </p>
                </div>
                <button
                  onClick={onResyncParams}
                  disabled={isResyncing}
                  className={`ml-3 px-4 py-2 rounded-md text-xs font-bold transition-all shadow-sm ${
                    isResyncing
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 text-white hover:shadow-md'
                  }`}
                >
                  {isResyncing ? (
                    <span className="flex items-center gap-1.5">
                      <span className="animate-spin w-3 h-3 border-2 border-white border-t-transparent rounded-full" />
                      Sincronizando...
                    </span>
                  ) : (
                    <span>⚡ Re-sincronizar parámetros</span>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Resumen de acción */}
          <div className="bg-white/80 rounded-md border border-gray-200 p-3">
            <h6 className="text-xs font-semibold text-gray-700 mb-1">📋 Resumen de calibración recomendada:</h6>
            <ul className="text-[10px] text-gray-600 space-y-0.5 list-disc list-inside">
              {analysis.direction !== 'under' && (
                <li>Aumentar pérdida por suciedad en Simulador: de 2-3% a 5-8% (o usar valores estacionales)</li>
              )}
              {analysis.direction !== 'over' && (
                <li>Reducir pérdidas acumulativas del Simulador: verificar cableado DC (1-1.5%), AC (1%), mismatch (1%)</li>
              )}
              <li>Verificar consistencia de NOCT y coef. temperatura entre ambos módulos</li>
              <li>Confirmar que el área, potencia Wp y eficiencia STC son idénticos en ambos</li>
              {analysis.pattern === 'seasonal' && (
                <li>Considerar usar pérdidas por suciedad variables por mes (mayor en época seca)</li>
              )}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
