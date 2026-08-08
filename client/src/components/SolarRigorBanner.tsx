import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import { SolarRigorReport } from '@/lib/solarRigor';

interface SolarRigorBannerProps {
  report: SolarRigorReport;
  compact?: boolean;
}

export default function SolarRigorBanner({ report, compact = false }: SolarRigorBannerProps) {
  const tone = report.errorCount > 0
    ? 'border-red-200 bg-red-50 text-red-900'
    : report.warningCount > 0
      ? 'border-amber-200 bg-amber-50 text-amber-900'
      : 'border-green-200 bg-green-50 text-green-900';
  const Icon = report.errorCount > 0 ? XCircle : report.warningCount > 0 ? AlertTriangle : CheckCircle2;

  return (
    <section className={`rounded-lg border p-4 ${tone}`} aria-label="Validación de rigor solar">
      <div className="flex items-start gap-3">
        <Icon size={18} className="mt-0.5 shrink-0" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <h3 className="font-semibold">Rigor solar</h3>
            <span className="font-mono text-sm font-bold">{report.scopeLabel}</span>
            <span className="text-xs font-medium">{report.datasetLabel}</span>
            <span className="text-xs">
              {report.recordCount.toLocaleString()} registros · {report.errorCount} errores · {report.warningCount} advertencias
            </span>
          </div>
          {!compact && (
            <div className="mt-3 grid gap-1 sm:grid-cols-2 lg:grid-cols-3">
              {report.checks.map(check => (
                <div key={check.key} className="text-xs">
                  <strong>{check.label}:</strong> {check.message}
                </div>
              ))}
            </div>
          )}
          {report.errorCount > 0 && (
            <p className="mt-2 text-sm font-medium">
              El cálculo se bloquea hasta corregir las validaciones marcadas como error.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}