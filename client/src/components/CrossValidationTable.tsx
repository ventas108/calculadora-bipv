/**
 * CrossValidationTable — Tabla comparativa lado a lado
 * Simulador vs PVWatts vs PVGIS
 * 
 * Muestra producción AC/DC mensual, PR, PR_T, temperaturas y Δ%
 * con resaltado condicional y métricas estadísticas (RMSE, MAE, R²).
 */
import { useState, useMemo, useCallback } from 'react';
import {
  ComparisonResult,
  ComparisonRow,
  SourceMonthlyData,
  SourceAnnualSummary,
  PairwiseStats,
  exportComparisonCSV,
  deltaPct,
} from '@/lib/crossValidation';
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ChevronDown, ChevronUp, Download, BarChart3, Eye, EyeOff } from 'lucide-react';

// ============================================================
// TIPOS
// ============================================================

interface CrossValidationTableProps {
  comparison: ComparisonResult;
  /** Callback para re-simular BIPV con datos reales cuando se detecta distribución plana */
  onResimultateBIPV?: () => void;
  /** Indica si la re-simulación está en progreso */
  isResimulating?: boolean;
}

type ColumnGroup = 'ac' | 'dc' | 'poa' | 'pr' | 'pr_t' | 'tamb' | 'tcell' | 'yield' | 'delta' | 'delta_yield';

const COLUMN_GROUPS: { key: ColumnGroup; label: string; defaultVisible: boolean }[] = [
  { key: 'ac', label: 'AC (kWh)', defaultVisible: true },
  { key: 'dc', label: 'DC (kWh)', defaultVisible: true },
  { key: 'poa', label: 'POA (kWh/m²)', defaultVisible: true },
  { key: 'pr', label: 'PR (%)', defaultVisible: true },
  { key: 'pr_t', label: 'PR_T (%)', defaultVisible: true },
  { key: 'tamb', label: 'T_amb (°C)', defaultVisible: false },
  { key: 'tcell', label: 'T_cell (°C)', defaultVisible: true },
  { key: 'yield', label: 'Yield (kWh/kWp)', defaultVisible: true },
  { key: 'delta', label: 'Δ% AC', defaultVisible: true },
  { key: 'delta_yield', label: 'Δ Yield', defaultVisible: true },
];

// ============================================================
// HELPERS
// ============================================================

/** Clase CSS para Δ%: verde < 5%, amarillo 5-15%, rojo > 15% */
function deltaColorClass(delta: number | null): string {
  if (delta === null) return '';
  const abs = Math.abs(delta);
  if (abs < 5) return 'text-green-700 bg-green-50';
  if (abs < 15) return 'text-yellow-700 bg-yellow-50';
  return 'text-red-700 bg-red-50';
}

/** Formatea un número con decimales, o '—' si null */
function fmtVal(v: number | null | undefined, decimals: number = 1): string {
  if (v === null || v === undefined) return '—';
  return v.toFixed(decimals);
}

/** Formatea Δ% con signo */
function fmtDelta(v: number | null): string {
  if (v === null) return '—';
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`;
}

// ============================================================
// COMPONENTE
// ============================================================

export default function CrossValidationTable({ comparison, onResimultateBIPV, isResimulating }: CrossValidationTableProps) {
  const [expanded, setExpanded] = useState(true);
  const [visibleGroups, setVisibleGroups] = useState<Set<ColumnGroup>>(() => {
    return new Set(COLUMN_GROUPS.filter(g => g.defaultVisible).map(g => g.key));
  });

  const toggleGroup = useCallback((key: ColumnGroup) => {
    setVisibleGroups(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  const handleExportCSV = useCallback(() => {
    const csv = exportComparisonCSV(comparison);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `comparativa_solar_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [comparison]);

  const show = (g: ColumnGroup) => visibleGroups.has(g);
  const { hasPVWatts, hasPVGIS, hasBIPV, rows, annualSimulator, annualPVWatts, annualPVGIS, annualBIPV, stats } = comparison;

  // Colores de fuente
  const SIM_BG = 'bg-violet-50';
  const SIM_TEXT = 'text-violet-800';
  const PVW_BG = 'bg-cyan-50';
  const PVW_TEXT = 'text-cyan-800';
  const PVG_BG = 'bg-emerald-50';
  const PVG_TEXT = 'text-emerald-800';
  const BIPV_BG = 'bg-teal-50';
  const BIPV_TEXT = 'text-teal-800';

  return (
    <div className="bg-gradient-to-r from-slate-50 to-gray-50 border border-slate-300 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-slate-700" />
          <h5 className="text-sm font-semibold text-slate-900">
            Tabla Comparativa — Validación Cruzada ({comparison.sourceCount} fuentes)
          </h5>
          <span className="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full font-medium">
            Simulador{hasPVWatts ? ' + PVWatts' : ''}{hasPVGIS ? ' + PVGIS' : ''}{hasBIPV ? ' + IAM+Soiling' : ''}
          </span>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4">
          {/* Toolbar: toggles + export */}
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className="text-[10px] text-gray-500 font-medium mr-1">Columnas:</span>
            {COLUMN_GROUPS.map(g => (
              <button
                key={g.key}
                onClick={() => toggleGroup(g.key)}
                className={`text-[10px] px-2 py-0.5 rounded-full border transition-colors ${
                  visibleGroups.has(g.key)
                    ? 'bg-slate-700 text-white border-slate-700'
                    : 'bg-white text-slate-500 border-slate-300 hover:border-slate-400'
                }`}
              >
                {visibleGroups.has(g.key) ? <Eye className="w-3 h-3 inline mr-0.5" /> : <EyeOff className="w-3 h-3 inline mr-0.5" />}
                {g.label}
              </button>
            ))}
            <div className="flex-1" />
            <button
              onClick={handleExportCSV}
              className="text-[10px] px-3 py-1 rounded bg-slate-700 text-white hover:bg-slate-800 transition-colors flex items-center gap-1"
            >
              <Download className="w-3 h-3" /> CSV
            </button>
          </div>

          {/* Alertas de coherencia de datos */}
          {comparison.coherenceAlerts && comparison.coherenceAlerts.length > 0 && (
            <div className="mb-3 space-y-2">
              {comparison.coherenceAlerts.map((alert, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-2 p-3 rounded-lg border text-xs ${
                    alert.severity === 'critical'
                      ? 'bg-red-50 border-red-300 text-red-800'
                      : 'bg-amber-50 border-amber-300 text-amber-800'
                  }`}
                >
                  <span className="text-base flex-shrink-0 mt-0.5">
                    {alert.severity === 'critical' ? '🚨' : '⚠️'}
                  </span>
                  <div className="flex-1">
                    <div className="font-semibold mb-0.5">
                      {alert.severity === 'critical' ? 'Error de Coherencia' : 'Advertencia de Coherencia'}
                      {' — '}
                      {alert.type === 'flat_distribution' && 'Distribución Plana Detectada'}
                      {alert.type === 'negative_values' && 'Valores Negativos'}
                      {alert.type === 'extreme_outlier' && 'Outlier Extremo'}
                    </div>
                    <p className="leading-relaxed">{alert.message}</p>
                    {alert.type === 'flat_distribution' && (
                      <p className="mt-1 text-[10px] opacity-75">
                        CV = {alert.cv_pct.toFixed(2)}% (esperado: 15-40% para variación estacional normal)
                      </p>
                    )}
                    {alert.type === 'flat_distribution' && alert.source === 'bipv' && onResimultateBIPV && (
                      <button
                        onClick={onResimultateBIPV}
                        disabled={isResimulating}
                        className={`mt-2 px-3 py-1.5 rounded-md text-[11px] font-semibold transition-colors ${
                          isResimulating
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm'
                        }`}
                      >
                        {isResimulating ? (
                          <span className="flex items-center gap-1.5">
                            <span className="animate-spin w-3 h-3 border-2 border-white border-t-transparent rounded-full" />
                            Re-simulando con datos horarios reales...
                          </span>
                        ) : (
                          <span>⚡ Re-simular con datos reales (corregir distribución plana)</span>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Indicador de normalización BIPV */}
          {comparison.bipvNormalized && (
            <div className="mb-3 p-3 rounded-lg border border-blue-300 bg-blue-50 text-xs text-blue-800">
              <div className="flex items-start gap-2">
                <span className="text-base flex-shrink-0">📐</span>
                <div>
                  <div className="font-semibold mb-0.5">Normalización de Capacidad Aplicada</div>
                  <p className="leading-relaxed">
                    El sistema BIPV tiene <strong>{comparison.bipvKwp?.toFixed(1)} kWp</strong> pero el Simulador tiene{' '}
                    <strong>{comparison.simKwp?.toFixed(1)} kWp</strong> ({((comparison.bipvKwp || 0) / (comparison.simKwp || 1)).toFixed(1)}× mayor).
                    La producción BIPV se escaló por <strong>×{comparison.bipvScaleFactor.toFixed(4)}</strong> para comparar
                    al mismo kWp y obtener un Δ% justo (diferencia de modelo, no de tamaño).
                  </p>
                  <p className="mt-1 text-[10px] opacity-75">
                    Sin normalizar, el Δ% sería ~{((1 - comparison.bipvScaleFactor) * -100).toFixed(0)}% solo por la diferencia de capacidad.
                    Para eliminar esta normalización, configure ambos módulos con la misma potencia instalada.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Tabla principal */}
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full text-[11px] border-collapse">
              {/* Encabezado de grupo (fuentes) */}
              <thead>
                <tr className="bg-slate-100">
                  <th rowSpan={2} className="border border-slate-200 px-2 py-1.5 text-left font-semibold text-slate-700 sticky left-0 bg-slate-100 z-10 min-w-[48px]">
                    Mes
                  </th>
                  {/* Simulador */}
                  {(show('ac') || show('dc') || show('poa') || show('pr') || show('tamb') || show('tcell') || show('yield')) && (
                    <th
                      colSpan={
                        (show('ac') ? 1 : 0) + (show('dc') ? 1 : 0) + (show('poa') ? 1 : 0) +
                        (show('pr') ? 1 : 0) + (show('tamb') ? 1 : 0) + (show('tcell') ? 1 : 0) + (show('yield') ? 1 : 0)
                      }
                      className={`border border-slate-200 px-2 py-1 text-center font-bold ${SIM_TEXT} ${SIM_BG}`}
                    >
                      Simulador
                    </th>
                  )}
                  {/* PVWatts */}
                  {hasPVWatts && (show('ac') || show('dc') || show('poa') || show('pr') || show('pr_t') || show('tamb') || show('tcell') || show('yield')) && (
                    <th
                      colSpan={
                        (show('ac') ? 1 : 0) + (show('dc') ? 1 : 0) + (show('poa') ? 1 : 0) +
                        (show('pr') ? 1 : 0) + (show('pr_t') ? 1 : 0) + (show('tamb') ? 1 : 0) + (show('tcell') ? 1 : 0) + (show('yield') ? 1 : 0)
                      }
                      className={`border border-slate-200 px-2 py-1 text-center font-bold ${PVW_TEXT} ${PVW_BG}`}
                    >
                      PVWatts (NREL)
                    </th>
                  )}
                  {/* PVGIS */}
                  {hasPVGIS && (show('ac') || show('poa') || show('pr') || show('pr_t') || show('tamb') || show('tcell') || show('yield')) && (
                    <th
                      colSpan={
                        (show('ac') ? 1 : 0) + (show('poa') ? 1 : 0) +
                        (show('pr') ? 1 : 0) + (show('pr_t') ? 1 : 0) + (show('tamb') ? 1 : 0) + (show('tcell') ? 1 : 0) + (show('yield') ? 1 : 0)
                      }
                      className={`border border-slate-200 px-2 py-1 text-center font-bold ${PVG_TEXT} ${PVG_BG}`}
                    >
                      PVGIS (JRC)
                    </th>
                  )}
                  {/* BIPV IAM+Soiling */}
                  {hasBIPV && (show('ac') || show('yield')) && (
                    <th
                      colSpan={(show('ac') ? 1 : 0) + (show('yield') ? 1 : 0)}
                      className={`border border-slate-200 px-2 py-1 text-center font-bold ${BIPV_TEXT} ${BIPV_BG}`}
                    >
                      IAM+Soiling
                    </th>
                  )}
                  {/* Deltas */}
                  {show('delta') && (hasPVWatts || hasPVGIS || hasBIPV) && (
                    <th
                      colSpan={(hasPVWatts ? 1 : 0) + (hasPVGIS ? 1 : 0) + (hasPVWatts && hasPVGIS ? 1 : 0) + (hasBIPV ? 1 : 0)}
                      className="border border-slate-200 px-2 py-1 text-center font-bold text-gray-700 bg-gray-50"
                    >
                      Δ% AC
                    </th>
                  )}
                  {/* Delta Yield */}
                  {show('delta_yield') && (hasPVWatts || hasPVGIS || hasBIPV) && (
                    <th
                      colSpan={(hasPVWatts ? 1 : 0) + (hasPVGIS ? 1 : 0) + (hasPVWatts && hasPVGIS ? 1 : 0) + (hasBIPV ? 1 : 0)}
                      className="border border-slate-200 px-2 py-1 text-center font-bold text-purple-700 bg-purple-50"
                    >
                      Δ Yield (kWh/kWp)
                    </th>
                  )}
                </tr>
                {/* Sub-encabezados */}
                <tr className="bg-slate-50">
                  {/* Simulador sub-cols */}
                  {show('ac') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${SIM_TEXT} font-medium`}>AC</th>}
                  {show('dc') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${SIM_TEXT} font-medium`}>DC</th>}
                  {show('poa') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${SIM_TEXT} font-medium`}>POA</th>}
                  {show('pr') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${SIM_TEXT} font-medium`}>PR</th>}
                  {show('tamb') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${SIM_TEXT} font-medium`}>T_amb</th>}
                  {show('tcell') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${SIM_TEXT} font-medium`}>T_cell</th>}
                  {show('yield') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${SIM_TEXT} font-medium`}>Yield</th>}
                  {/* PVWatts sub-cols */}
                  {hasPVWatts && show('ac') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVW_TEXT} font-medium`}>AC</th>}
                  {hasPVWatts && show('dc') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVW_TEXT} font-medium`}>DC</th>}
                  {hasPVWatts && show('poa') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVW_TEXT} font-medium`}>POA</th>}
                  {hasPVWatts && show('pr') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVW_TEXT} font-medium`}>PR</th>}
                  {hasPVWatts && show('pr_t') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVW_TEXT} font-medium`}>PR_T</th>}
                  {hasPVWatts && show('tamb') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVW_TEXT} font-medium`}>T_amb</th>}
                  {hasPVWatts && show('tcell') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVW_TEXT} font-medium`}>T_cell</th>}
                  {hasPVWatts && show('yield') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVW_TEXT} font-medium`}>Yield</th>}
                  {/* PVGIS sub-cols */}
                  {hasPVGIS && show('ac') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVG_TEXT} font-medium`}>AC</th>}
                  {hasPVGIS && show('poa') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVG_TEXT} font-medium`}>POA</th>}
                  {hasPVGIS && show('pr') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVG_TEXT} font-medium`}>PR</th>}
                  {hasPVGIS && show('pr_t') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVG_TEXT} font-medium`}>PR_T</th>}
                  {hasPVGIS && show('tamb') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVG_TEXT} font-medium`}>T_amb</th>}
                  {hasPVGIS && show('tcell') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVG_TEXT} font-medium`}>T_cell</th>}
                  {hasPVGIS && show('yield') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${PVG_TEXT} font-medium`}>Yield</th>}
                  {/* BIPV sub-cols */}
                  {hasBIPV && show('ac') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${BIPV_TEXT} font-medium`}>AC</th>}
                  {hasBIPV && show('yield') && <th className={`border border-slate-200 px-1.5 py-1 text-center ${BIPV_TEXT} font-medium`}>Yield</th>}
                  {/* Delta sub-cols */}
                  {show('delta') && hasPVWatts && <th className="border border-slate-200 px-1.5 py-1 text-center text-gray-600 font-medium">S-PVW</th>}
                  {show('delta') && hasPVGIS && <th className="border border-slate-200 px-1.5 py-1 text-center text-gray-600 font-medium">S-PVG</th>}
                  {show('delta') && hasPVWatts && hasPVGIS && <th className="border border-slate-200 px-1.5 py-1 text-center text-gray-600 font-medium">PVW-PVG</th>}
                  {show('delta') && hasBIPV && <th className="border border-slate-200 px-1.5 py-1 text-center text-gray-600 font-medium">S-BIPV</th>}
                  {/* Delta Yield sub-cols */}
                  {show('delta_yield') && hasPVWatts && <th className="border border-slate-200 px-1.5 py-1 text-center text-purple-600 font-medium">S-PVW</th>}
                  {show('delta_yield') && hasPVGIS && <th className="border border-slate-200 px-1.5 py-1 text-center text-purple-600 font-medium">S-PVG</th>}
                  {show('delta_yield') && hasPVWatts && hasPVGIS && <th className="border border-slate-200 px-1.5 py-1 text-center text-purple-600 font-medium">PVW-PVG</th>}
                  {show('delta_yield') && hasBIPV && <th className="border border-slate-200 px-1.5 py-1 text-center text-purple-600 font-medium">S-BIPV</th>}
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={r.month} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                    <td className="border border-slate-200 px-2 py-1 font-semibold text-slate-700 sticky left-0 bg-inherit z-10">
                      {r.monthName}
                    </td>
                    {/* Simulador */}
                    {show('ac') && <td className="border border-slate-200 px-1.5 py-1 text-center font-mono">{fmtVal(r.simulator.ac_kWh)}</td>}
                    {show('dc') && <td className="border border-slate-200 px-1.5 py-1 text-center font-mono">{fmtVal(r.simulator.dc_kWh)}</td>}
                    {show('poa') && <td className="border border-slate-200 px-1.5 py-1 text-center font-mono">{fmtVal(r.simulator.poa_kWhm2)}</td>}
                    {show('pr') && <td className="border border-slate-200 px-1.5 py-1 text-center font-mono">{fmtVal(r.simulator.pr_pct)}</td>}
                    {show('tamb') && <td className="border border-slate-200 px-1.5 py-1 text-center font-mono">{fmtVal(r.simulator.tamb_C)}</td>}
                    {show('tcell') && <td className="border border-slate-200 px-1.5 py-1 text-center font-mono">{fmtVal(r.simulator.tcell_C)}</td>}
                    {show('yield') && <td className="border border-slate-200 px-1.5 py-1 text-center font-mono font-bold text-indigo-700">{fmtVal(r.simulator.yield_kwh_kwp)}</td>}
                    {/* PVWatts */}
                    {hasPVWatts && show('ac') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${PVW_TEXT}`}>{fmtVal(r.pvwatts.ac_kWh)}</td>}
                    {hasPVWatts && show('dc') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${PVW_TEXT}`}>{fmtVal(r.pvwatts.dc_kWh)}</td>}
                    {hasPVWatts && show('poa') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${PVW_TEXT}`}>{fmtVal(r.pvwatts.poa_kWhm2)}</td>}
                    {hasPVWatts && show('pr') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${PVW_TEXT}`}>{fmtVal(r.pvwatts.pr_pct)}</td>}
                    {hasPVWatts && show('pr_t') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold ${PVW_TEXT}`}>{fmtVal(r.pvwatts.pr_t_pct)}</td>}
                    {hasPVWatts && show('tamb') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${PVW_TEXT}`}>{fmtVal(r.pvwatts.tamb_C)}</td>}
                    {hasPVWatts && show('tcell') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${PVW_TEXT}`}>{fmtVal(r.pvwatts.tcell_C)}</td>}
                    {hasPVWatts && show('yield') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold text-indigo-700`}>{fmtVal(r.pvwatts.yield_kwh_kwp)}</td>}
                    {/* PVGIS */}
                    {hasPVGIS && show('ac') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${PVG_TEXT}`}>{fmtVal(r.pvgis.ac_kWh)}</td>}
                    {hasPVGIS && show('poa') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${PVG_TEXT}`}>{fmtVal(r.pvgis.poa_kWhm2)}</td>}
                    {hasPVGIS && show('pr') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${PVG_TEXT}`}>{fmtVal(r.pvgis.pr_pct)}</td>}
                    {hasPVGIS && show('pr_t') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold ${PVG_TEXT}`}>{fmtVal(r.pvgis.pr_t_pct)}</td>}
                    {hasPVGIS && show('tamb') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${PVG_TEXT}`}>{fmtVal(r.pvgis.tamb_C)}</td>}
                    {hasPVGIS && show('tcell') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${PVG_TEXT}`}>{fmtVal(r.pvgis.tcell_C)}</td>}
                    {hasPVGIS && show('yield') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold text-indigo-700`}>{fmtVal(r.pvgis.yield_kwh_kwp)}</td>}
                    {/* BIPV */}
                    {hasBIPV && show('ac') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono ${BIPV_TEXT}`}>{fmtVal(r.bipv.ac_kWh)}</td>}
                    {hasBIPV && show('yield') && <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold text-indigo-700`}>{fmtVal(r.bipv.yield_kwh_kwp)}</td>}
                    {/* Deltas */}
                    {show('delta') && hasPVWatts && (
                      <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold ${deltaColorClass(r.delta_sim_pvw_pct)}`}>
                        {fmtDelta(r.delta_sim_pvw_pct)}
                      </td>
                    )}
                    {show('delta') && hasPVGIS && (
                      <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold ${deltaColorClass(r.delta_sim_pvg_pct)}`}>
                        {fmtDelta(r.delta_sim_pvg_pct)}
                      </td>
                    )}
                    {show('delta') && hasPVWatts && hasPVGIS && (
                      <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold ${deltaColorClass(r.delta_pvw_pvg_pct)}`}>
                        {fmtDelta(r.delta_pvw_pvg_pct)}
                      </td>
                    )}
                    {show('delta') && hasBIPV && (
                      <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold ${deltaColorClass(r.delta_sim_bipv_pct)}`}>
                        {fmtDelta(r.delta_sim_bipv_pct)}
                      </td>
                    )}
                    {/* Delta Yield cells */}
                    {show('delta_yield') && hasPVWatts && (
                      <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold ${deltaColorClass(r.delta_yield_sim_pvw_pct)}`}>
                        {fmtDelta(r.delta_yield_sim_pvw_pct)}
                      </td>
                    )}
                    {show('delta_yield') && hasPVGIS && (
                      <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold ${deltaColorClass(r.delta_yield_sim_pvg_pct)}`}>
                        {fmtDelta(r.delta_yield_sim_pvg_pct)}
                      </td>
                    )}
                    {show('delta_yield') && hasPVWatts && hasPVGIS && (
                      <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold ${deltaColorClass(r.delta_yield_pvw_pvg_pct)}`}>
                        {fmtDelta(r.delta_yield_pvw_pvg_pct)}
                      </td>
                    )}
                    {show('delta_yield') && hasBIPV && (
                      <td className={`border border-slate-200 px-1.5 py-1 text-center font-mono font-bold ${deltaColorClass(r.delta_yield_sim_bipv_pct)}`}>
                        {fmtDelta(r.delta_yield_sim_bipv_pct)}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
              {/* Fila Anual */}
              <tfoot>
                <tr className="bg-slate-200/70 font-bold">
                  <td className="border border-slate-300 px-2 py-1.5 font-bold text-slate-800 sticky left-0 bg-slate-200/70 z-10">ANUAL</td>
                  {/* Simulador */}
                  {show('ac') && <td className="border border-slate-300 px-1.5 py-1.5 text-center font-mono">{fmtVal(annualSimulator.ac_kWh, 0)}</td>}
                  {show('dc') && <td className="border border-slate-300 px-1.5 py-1.5 text-center font-mono">{fmtVal(annualSimulator.dc_kWh, 0)}</td>}
                  {show('poa') && <td className="border border-slate-300 px-1.5 py-1.5 text-center font-mono">{fmtVal(annualSimulator.poa_kWhm2, 0)}</td>}
                  {show('pr') && <td className="border border-slate-300 px-1.5 py-1.5 text-center font-mono">{fmtVal(annualSimulator.pr_pct)}</td>}
                  {show('tamb') && <td className="border border-slate-300 px-1.5 py-1.5 text-center font-mono">{fmtVal(annualSimulator.tamb_C)}</td>}
                  {show('tcell') && <td className="border border-slate-300 px-1.5 py-1.5 text-center font-mono">{fmtVal(annualSimulator.tcell_C)}</td>}
                  {show('yield') && <td className="border border-slate-300 px-1.5 py-1.5 text-center font-mono font-bold text-indigo-700">{fmtVal(annualSimulator.yield_kwh_kwp, 0)}</td>}
                  {/* PVWatts */}
                  {hasPVWatts && show('ac') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${PVW_TEXT}`}>{fmtVal(annualPVWatts.ac_kWh, 0)}</td>}
                  {hasPVWatts && show('dc') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${PVW_TEXT}`}>{fmtVal(annualPVWatts.dc_kWh, 0)}</td>}
                  {hasPVWatts && show('poa') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${PVW_TEXT}`}>{fmtVal(annualPVWatts.poa_kWhm2, 0)}</td>}
                  {hasPVWatts && show('pr') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${PVW_TEXT}`}>{fmtVal(annualPVWatts.pr_pct)}</td>}
                  {hasPVWatts && show('pr_t') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono font-bold ${PVW_TEXT}`}>{fmtVal(annualPVWatts.pr_t_pct)}</td>}
                  {hasPVWatts && show('tamb') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${PVW_TEXT}`}>{fmtVal(annualPVWatts.tamb_C)}</td>}
                  {hasPVWatts && show('tcell') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${PVW_TEXT}`}>{fmtVal(annualPVWatts.tcell_C)}</td>}
                  {hasPVWatts && show('yield') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono font-bold text-indigo-700`}>{fmtVal(annualPVWatts.yield_kwh_kwp, 0)}</td>}
                  {/* PVGIS */}
                  {hasPVGIS && show('ac') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${PVG_TEXT}`}>{fmtVal(annualPVGIS.ac_kWh, 0)}</td>}
                  {hasPVGIS && show('poa') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${PVG_TEXT}`}>{fmtVal(annualPVGIS.poa_kWhm2, 0)}</td>}
                  {hasPVGIS && show('pr') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${PVG_TEXT}`}>{fmtVal(annualPVGIS.pr_pct)}</td>}
                  {hasPVGIS && show('pr_t') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono font-bold ${PVG_TEXT}`}>{fmtVal(annualPVGIS.pr_t_pct)}</td>}
                  {hasPVGIS && show('tamb') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${PVG_TEXT}`}>{fmtVal(annualPVGIS.tamb_C)}</td>}
                  {hasPVGIS && show('tcell') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${PVG_TEXT}`}>{fmtVal(annualPVGIS.tcell_C)}</td>}
                  {hasPVGIS && show('yield') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono font-bold text-indigo-700`}>{fmtVal(annualPVGIS.yield_kwh_kwp, 0)}</td>}
                  {/* BIPV */}
                  {hasBIPV && show('ac') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono font-bold ${BIPV_TEXT}`}>{fmtVal(annualBIPV.ac_kWh, 0)}</td>}
                  {hasBIPV && show('yield') && <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono font-bold text-indigo-700`}>{fmtVal(annualBIPV.yield_kwh_kwp, 0)}</td>}
                  {/* Deltas anuales */}
                  {show('delta') && hasPVWatts && (
                    <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${deltaColorClass(deltaPct(annualSimulator.ac_kWh, annualPVWatts.ac_kWh))}`}>
                      {fmtDelta(deltaPct(annualSimulator.ac_kWh, annualPVWatts.ac_kWh))}
                    </td>
                  )}
                  {show('delta') && hasPVGIS && (
                    <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${deltaColorClass(deltaPct(annualSimulator.ac_kWh, annualPVGIS.ac_kWh))}`}>
                      {fmtDelta(deltaPct(annualSimulator.ac_kWh, annualPVGIS.ac_kWh))}
                    </td>
                  )}
                  {show('delta') && hasPVWatts && hasPVGIS && (
                    <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${deltaColorClass(deltaPct(annualPVWatts.ac_kWh, annualPVGIS.ac_kWh))}`}>
                      {fmtDelta(deltaPct(annualPVWatts.ac_kWh, annualPVGIS.ac_kWh))}
                    </td>
                  )}
                  {show('delta') && hasBIPV && (
                    <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${deltaColorClass(deltaPct(annualSimulator.ac_kWh, annualBIPV.ac_kWh))}`}>
                      {fmtDelta(deltaPct(annualSimulator.ac_kWh, annualBIPV.ac_kWh))}
                    </td>
                  )}
                  {/* Delta Yield anuales */}
                  {show('delta_yield') && hasPVWatts && (
                    <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${deltaColorClass(deltaPct(annualSimulator.yield_kwh_kwp, annualPVWatts.yield_kwh_kwp))}`}>
                      {fmtDelta(deltaPct(annualSimulator.yield_kwh_kwp, annualPVWatts.yield_kwh_kwp))}
                    </td>
                  )}
                  {show('delta_yield') && hasPVGIS && (
                    <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${deltaColorClass(deltaPct(annualSimulator.yield_kwh_kwp, annualPVGIS.yield_kwh_kwp))}`}>
                      {fmtDelta(deltaPct(annualSimulator.yield_kwh_kwp, annualPVGIS.yield_kwh_kwp))}
                    </td>
                  )}
                  {show('delta_yield') && hasPVWatts && hasPVGIS && (
                    <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${deltaColorClass(deltaPct(annualPVWatts.yield_kwh_kwp, annualPVGIS.yield_kwh_kwp))}`}>
                      {fmtDelta(deltaPct(annualPVWatts.yield_kwh_kwp, annualPVGIS.yield_kwh_kwp))}
                    </td>
                  )}
                  {show('delta_yield') && hasBIPV && (
                    <td className={`border border-slate-300 px-1.5 py-1.5 text-center font-mono ${deltaColorClass(deltaPct(annualSimulator.yield_kwh_kwp, annualBIPV.yield_kwh_kwp))}`}>
                      {fmtDelta(deltaPct(annualSimulator.yield_kwh_kwp, annualBIPV.yield_kwh_kwp))}
                    </td>
                  )}
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Métricas estadísticas */}
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { s: stats.sim_vs_pvwatts, show: hasPVWatts, color: 'cyan' },
              { s: stats.sim_vs_pvgis, show: hasPVGIS, color: 'emerald' },
              { s: stats.pvwatts_vs_pvgis, show: hasPVWatts && hasPVGIS, color: 'amber' },
              { s: stats.sim_vs_bipv, show: hasBIPV, color: 'teal' },
            ].filter(x => x.show).map(({ s, color }) => (
              <div key={s.label} className={`bg-white rounded-lg border border-${color}-200 p-3`}>
                <p className={`text-[10px] font-semibold text-${color}-800 mb-2`}>{s.label}</p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
                  <span className="text-gray-500">RMSE (kWh):</span>
                  <span className="font-mono font-bold text-gray-800">{s.rmse !== null ? s.rmse.toFixed(1) : '—'}</span>
                  <span className="text-gray-500">MAE (kWh):</span>
                  <span className="font-mono font-bold text-gray-800">{s.mae !== null ? s.mae.toFixed(1) : '—'}</span>
                  <span className="text-gray-500">R²:</span>
                  <span className="font-mono font-bold text-gray-800">{s.r2 !== null ? s.r2.toFixed(4) : '—'}</span>
                  <span className="text-gray-500">Δ% medio:</span>
                  <span className={`font-mono font-bold ${s.meanDelta_pct !== null ? deltaColorClass(s.meanDelta_pct) : ''} px-1 rounded`}>
                    {s.meanDelta_pct !== null ? `${s.meanDelta_pct >= 0 ? '+' : ''}${s.meanDelta_pct.toFixed(1)}%` : '—'}
                  </span>
                  <span className="text-gray-500">Meses (n):</span>
                  <span className="font-mono text-gray-800">{s.n}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Leyenda */}
          <div className="mt-2 flex flex-wrap gap-3 text-[9px] text-gray-500">
            <span>Δ%: <span className="text-green-700 font-bold">&lt;5% verde</span>, <span className="text-yellow-700 font-bold">5-15% amarillo</span>, <span className="text-red-700 font-bold">&gt;15% rojo</span></span>
            <span>RMSE = Root Mean Square Error. MAE = Mean Absolute Error. R² = Coeficiente de determinación.</span>
            <span>S = Simulador, PVW = PVWatts (NREL), PVG = PVGIS (JRC), BIPV = IAM+Soiling BIPV.</span>
          </div>
        </div>
      )}
    </div>
  );
}
