import { useState } from 'react';
import {
  PerformanceAlert,
  DiagnosticCause,
  AlertSeverity,
} from '@shared/performanceDiagnostic';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Shield,
  Activity,
  Wrench,
  Info,
} from 'lucide-react';

interface PerformanceAlertPanelProps {
  alert: PerformanceAlert;
  compact?: boolean;
}

export default function PerformanceAlertPanel({ alert, compact = false }: PerformanceAlertPanelProps) {
  const [causesExpanded, setCausesExpanded] = useState(!compact);

  if (alert.severity === 'ok' && compact) return null;

  const SeverityIcon = getSeverityIcon(alert.severity);

  return (
    <div
      className="rounded-lg border overflow-hidden transition-all"
      style={{
        backgroundColor: alert.bgColor,
        borderColor: alert.color + '40',
      }}
    >
      {/* Header */}
      <div className="p-3">
        <div className="flex items-start gap-3">
          {/* Health Score Circle */}
          <div className="flex-shrink-0">
            <div
              className="relative w-12 h-12 rounded-full flex items-center justify-center"
              style={{
                background: `conic-gradient(${alert.color} ${alert.healthScore * 3.6}deg, #e5e7eb ${alert.healthScore * 3.6}deg)`,
              }}
            >
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold"
                style={{ backgroundColor: alert.bgColor, color: alert.color }}
              >
                {alert.healthScore}
              </div>
            </div>
            <p className="text-[8px] text-center mt-0.5" style={{ color: alert.color }}>
              Salud
            </p>
          </div>

          {/* Alert Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <SeverityIcon size={16} style={{ color: alert.color }} />
              <h4 className="text-sm font-semibold" style={{ color: alert.color }}>
                {alert.title}
              </h4>
            </div>
            <p className="text-xs text-gray-700 leading-relaxed">
              {alert.message}
            </p>

            {/* PR Comparison Bar */}
            <div className="mt-2 flex items-center gap-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, (alert.prMeasured / Math.max(alert.prExpected, 0.01)) * 100)}%`,
                    backgroundColor: alert.color,
                  }}
                />
              </div>
              <span className="text-[10px] font-mono whitespace-nowrap" style={{ color: alert.color }}>
                {(alert.prMeasured * 100).toFixed(1)}% / {(alert.prExpected * 100).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between mt-0.5">
              <span className="text-[9px] text-gray-500">PR medido</span>
              <span className="text-[9px] text-gray-500">
                Desviación: {alert.prDeviation > 0 ? '-' : '+'}{Math.abs(alert.prDeviation).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Causes Section */}
      {alert.causes.length > 0 && (
        <div className="border-t" style={{ borderColor: alert.color + '20' }}>
          <button
            onClick={() => setCausesExpanded(!causesExpanded)}
            className="w-full flex items-center justify-between px-3 py-2 hover:opacity-80 transition-opacity"
          >
            <span className="text-xs font-medium flex items-center gap-1.5" style={{ color: alert.color }}>
              <Wrench size={12} />
              {alert.causes.length} causa{alert.causes.length > 1 ? 's' : ''} probable{alert.causes.length > 1 ? 's' : ''} detectada{alert.causes.length > 1 ? 's' : ''}
            </span>
            {causesExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>

          {causesExpanded && (
            <div className="px-3 pb-3 space-y-2">
              {alert.causes.map((cause, idx) => (
                <CauseCard key={cause.id} cause={cause} rank={idx + 1} alertColor={alert.color} />
              ))}

              {/* General recommendation */}
              {alert.severity !== 'ok' && (
                <div className="mt-3 p-2 bg-white/60 rounded border border-gray-200">
                  <div className="flex items-start gap-2">
                    <Info size={12} className="text-gray-500 mt-0.5 flex-shrink-0" />
                    <p className="text-[10px] text-gray-600 leading-relaxed">
                      <strong>Nota:</strong> Las probabilidades son estimaciones basadas en las condiciones medidas.
                      Para un diagnóstico definitivo, se recomienda realizar mediciones con equipos calibrados
                      (curva I-V, cámara termográfica, electroluminiscencia) y comparar con el datasheet del fabricante.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================
// Sub-componentes
// ============================================================

function CauseCard({ cause, rank, alertColor }: { cause: DiagnosticCause; rank: number; alertColor: string }) {
  const [expanded, setExpanded] = useState(rank <= 2); // Auto-expandir top 2

  const categoryColors: Record<string, string> = {
    ambiental: '#0ea5e9',
    equipo: '#8b5cf6',
    instalacion: '#f59e0b',
    mantenimiento: '#10b981',
    diseno: '#6366f1',
  };

  const categoryLabels: Record<string, string> = {
    ambiental: 'Ambiental',
    equipo: 'Equipo',
    instalacion: 'Instalación',
    mantenimiento: 'Mantenimiento',
    diseno: 'Diseño',
  };

  const probPercent = (cause.probability * 100).toFixed(0);
  const catColor = categoryColors[cause.category] || '#6b7280';

  return (
    <div className="bg-white/80 rounded border border-gray-100 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-2.5 py-2 hover:bg-gray-50/50 transition-colors"
      >
        {/* Rank */}
        <span
          className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold text-white"
          style={{ backgroundColor: alertColor }}
        >
          {rank}
        </span>

        {/* Icon */}
        <span className="text-sm flex-shrink-0">{cause.icon}</span>

        {/* Name */}
        <span className="text-xs font-medium text-gray-800 flex-1 text-left truncate">
          {cause.name}
        </span>

        {/* Category badge */}
        <span
          className="text-[8px] px-1.5 py-0.5 rounded-full font-medium flex-shrink-0"
          style={{ backgroundColor: catColor + '15', color: catColor }}
        >
          {categoryLabels[cause.category]}
        </span>

        {/* Probability bar */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <div className="w-12 bg-gray-200 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.min(100, cause.probability * 100)}%`,
                backgroundColor: alertColor,
              }}
            />
          </div>
          <span className="text-[9px] font-mono w-7 text-right" style={{ color: alertColor }}>
            {probPercent}%
          </span>
        </div>

        {expanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
      </button>

      {expanded && (
        <div className="px-2.5 pb-2.5 space-y-2">
          <p className="text-[10px] text-gray-600 leading-relaxed pl-7">
            {cause.description}
          </p>
          <div className="flex items-start gap-1.5 pl-7 bg-green-50 rounded p-1.5">
            <Wrench size={10} className="text-green-600 mt-0.5 flex-shrink-0" />
            <p className="text-[10px] text-green-800 leading-relaxed">
              <strong>Acción:</strong> {cause.recommendation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function getSeverityIcon(severity: AlertSeverity) {
  switch (severity) {
    case 'ok': return CheckCircle2;
    case 'leve': return Activity;
    case 'moderada': return AlertTriangle;
    case 'severa': return AlertTriangle;
    case 'critica': return Shield;
  }
}
