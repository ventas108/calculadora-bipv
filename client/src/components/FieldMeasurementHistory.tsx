import { useState, useMemo } from 'react';
import { FieldMeasurementRecord } from '@/hooks/useFieldMeasurementHistory';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Trash2, Download, RotateCcw, Clock, Sun, Thermometer, Zap, ChevronDown, ChevronUp, Eye, ArrowUpDown, AlertTriangle, CheckCircle2, Shield } from 'lucide-react';
import { getAlertBadge } from '@shared/performanceDiagnostic';

interface FieldMeasurementHistoryProps {
  records: FieldMeasurementRecord[];
  onRemove: (id: string) => void;
  onClearAll: () => void;
  onLoadRecord: (record: FieldMeasurementRecord) => void;
  onExportCSV: () => string;
}

type SortField = 'timestamp' | 'ghi' | 'tempAmbient' | 'tempCell' | 'pExp' | 'prMulcue';
type SortDir = 'asc' | 'desc';

export default function FieldMeasurementHistory({
  records,
  onRemove,
  onClearAll,
  onLoadRecord,
  onExportCSV,
}: FieldMeasurementHistoryProps) {
  const [expanded, setExpanded] = useState(true);
  const [chartExpanded, setChartExpanded] = useState(true);
  const [sortField, setSortField] = useState<SortField>('timestamp');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [selectedDay, setSelectedDay] = useState<string | null>(null);

  // Agrupar por día
  const groupedByDay = useMemo(() => {
    const groups: Record<string, FieldMeasurementRecord[]> = {};
    records.forEach(r => {
      const dateKey = new Date(r.timestamp).toLocaleDateString('es-CO');
      if (!groups[dateKey]) groups[dateKey] = [];
      groups[dateKey].push(r);
    });
    Object.values(groups).forEach(group => group.sort((a, b) => a.timestamp - b.timestamp));
    return groups;
  }, [records]);

  const dayKeys = useMemo(() => Object.keys(groupedByDay).sort((a, b) => {
    // Más reciente primero
    const da = groupedByDay[a][0].timestamp;
    const db = groupedByDay[b][0].timestamp;
    return db - da;
  }), [groupedByDay]);

  // Auto-seleccionar el día más reciente
  const activeDay = selectedDay && groupedByDay[selectedDay] ? selectedDay : dayKeys[0] || null;

  // Datos del día seleccionado para el gráfico
  const chartData = useMemo(() => {
    if (!activeDay || !groupedByDay[activeDay]) return [];
    return groupedByDay[activeDay].map(r => {
      const date = new Date(r.timestamp);
      return {
        time: date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }),
        timestamp: r.timestamp,
        ghi: r.ghi,
        tempAmbient: r.tempAmbient,
        tempCell: r.tempCell,
        pExp: r.pExp,
        pExpPercent: (r.pExp / r.panelPower) * 100,
        prMulcue: r.prMulcue * 100,
        tempLoss: (1 - r.tempLoss) * 100,
        label: r.label,
      };
    });
  }, [activeDay, groupedByDay]);

  // Estadísticas del día
  const dayStats = useMemo(() => {
    if (chartData.length === 0) return null;
    const ghiValues = chartData.map(d => d.ghi);
    const tempValues = chartData.map(d => d.tempCell);
    const pExpValues = chartData.map(d => d.pExp);
    return {
      count: chartData.length,
      ghiMin: Math.min(...ghiValues),
      ghiMax: Math.max(...ghiValues),
      ghiAvg: ghiValues.reduce((a, b) => a + b, 0) / ghiValues.length,
      tempMin: Math.min(...tempValues),
      tempMax: Math.max(...tempValues),
      tempAvg: tempValues.reduce((a, b) => a + b, 0) / tempValues.length,
      pExpMin: Math.min(...pExpValues),
      pExpMax: Math.max(...pExpValues),
      pExpAvg: pExpValues.reduce((a, b) => a + b, 0) / pExpValues.length,
    };
  }, [chartData]);

  // Ordenar registros para la tabla
  const sortedRecords = useMemo(() => {
    return [...records].sort((a, b) => {
      const mul = sortDir === 'asc' ? 1 : -1;
      switch (sortField) {
        case 'timestamp': return mul * (a.timestamp - b.timestamp);
        case 'ghi': return mul * (a.ghi - b.ghi);
        case 'tempAmbient': return mul * (a.tempAmbient - b.tempAmbient);
        case 'tempCell': return mul * (a.tempCell - b.tempCell);
        case 'pExp': return mul * (a.pExp - b.pExp);
        case 'prMulcue': return mul * (a.prMulcue - b.prMulcue);
        default: return 0;
      }
    });
  }, [records, sortField, sortDir]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  const handleExport = () => {
    const csv = onExportCSV();
    if (!csv) return;
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mediciones_campo_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const SortIcon = ({ field }: { field: SortField }) => (
    <ArrowUpDown
      size={10}
      className={`inline ml-0.5 cursor-pointer ${sortField === field ? 'text-teal-600' : 'text-gray-400'}`}
      onClick={() => toggleSort(field)}
    />
  );

  if (records.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 text-center text-sm text-gray-500">
        <Clock size={24} className="mx-auto mb-2 text-gray-400" />
        <p className="font-medium">Sin mediciones guardadas</p>
        <p className="text-xs mt-1">Ingresa valores de GHI, T_amb y T_cell arriba, luego haz clic en "Guardar Medición" para registrar la primera medición.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header con controles */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-teal-900 flex items-center gap-2">
          <Clock size={14} className="text-teal-600" />
          Historial de Mediciones ({records.length})
        </h4>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            className="flex items-center gap-1 px-2 py-1 text-[10px] rounded bg-teal-100 text-teal-700 hover:bg-teal-200 transition-colors"
            title="Exportar CSV"
          >
            <Download size={10} />
            CSV
          </button>
          <button
            onClick={() => {
              if (window.confirm('¿Eliminar todas las mediciones del historial?')) {
                onClearAll();
              }
            }}
            className="flex items-center gap-1 px-2 py-1 text-[10px] rounded bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
            title="Limpiar historial"
          >
            <Trash2 size={10} />
            Limpiar
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 rounded hover:bg-gray-100"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {expanded && (
        <>
          {/* Selector de día + Gráfico temporal */}
          {dayKeys.length > 0 && (
            <div className="bg-white rounded-lg border border-teal-100 overflow-hidden">
              <button
                onClick={() => setChartExpanded(!chartExpanded)}
                className="w-full flex items-center justify-between p-3 hover:bg-teal-50/50 transition-colors"
              >
                <span className="text-xs font-medium text-teal-800 flex items-center gap-2">
                  <Sun size={12} className="text-amber-500" />
                  Evolución Temporal del Día
                </span>
                <span className={`text-xs transition-transform ${chartExpanded ? 'rotate-180' : ''}`}>▼</span>
              </button>

              {chartExpanded && (
                <div className="px-3 pb-3 space-y-3">
                  {/* Day selector tabs */}
                  <div className="flex gap-1 overflow-x-auto pb-1">
                    {dayKeys.map(day => (
                      <button
                        key={day}
                        onClick={() => setSelectedDay(day)}
                        className={`px-3 py-1 text-[10px] rounded-full whitespace-nowrap transition-colors ${
                          activeDay === day
                            ? 'bg-teal-600 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-teal-100'
                        }`}
                      >
                        {day} ({groupedByDay[day].length})
                      </button>
                    ))}
                  </div>

                  {/* Day stats summary */}
                  {dayStats && (
                    <div className="grid grid-cols-3 gap-2">
                      <div className="bg-amber-50 rounded p-2 text-center">
                        <p className="text-[9px] text-amber-700">GHI (W/m²)</p>
                        <p className="text-xs font-mono font-bold text-amber-900">
                          {dayStats.ghiMin.toFixed(0)} — {dayStats.ghiMax.toFixed(0)}
                        </p>
                        <p className="text-[9px] text-amber-600">prom: {dayStats.ghiAvg.toFixed(0)}</p>
                      </div>
                      <div className="bg-red-50 rounded p-2 text-center">
                        <p className="text-[9px] text-red-700">T_cell (°C)</p>
                        <p className="text-xs font-mono font-bold text-red-900">
                          {dayStats.tempMin.toFixed(1)} — {dayStats.tempMax.toFixed(1)}
                        </p>
                        <p className="text-[9px] text-red-600">prom: {dayStats.tempAvg.toFixed(1)}</p>
                      </div>
                      <div className="bg-teal-50 rounded p-2 text-center">
                        <p className="text-[9px] text-teal-700">P_exp (W)</p>
                        <p className="text-xs font-mono font-bold text-teal-900">
                          {dayStats.pExpMin.toFixed(0)} — {dayStats.pExpMax.toFixed(0)}
                        </p>
                        <p className="text-[9px] text-teal-600">prom: {dayStats.pExpAvg.toFixed(0)}</p>
                      </div>
                    </div>
                  )}

                  {/* Chart */}
                  {chartData.length >= 2 ? (
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                          <XAxis
                            dataKey="time"
                            tick={{ fontSize: 10 }}
                            stroke="#6b7280"
                          />
                          <YAxis
                            yAxisId="left"
                            tick={{ fontSize: 10 }}
                            stroke="#f59e0b"
                            label={{ value: 'W/m² | W', angle: -90, position: 'insideLeft', style: { fontSize: 9 } }}
                          />
                          <YAxis
                            yAxisId="right"
                            orientation="right"
                            tick={{ fontSize: 10 }}
                            stroke="#ef4444"
                            label={{ value: '°C', angle: 90, position: 'insideRight', style: { fontSize: 9 } }}
                          />
                          <Tooltip
                            contentStyle={{ fontSize: 11, borderRadius: 8 }}
                            formatter={(value: number, name: string) => {
                              const labels: Record<string, string> = {
                                ghi: 'GHI',
                                pExp: 'P_exp',
                                tempCell: 'T_cell',
                                tempAmbient: 'T_amb',
                              };
                              const units: Record<string, string> = {
                                ghi: ' W/m²',
                                pExp: ' W',
                                tempCell: ' °C',
                                tempAmbient: ' °C',
                              };
                              return [`${value.toFixed(1)}${units[name] || ''}`, labels[name] || name];
                            }}
                            labelFormatter={(label, payload) => {
                              const item = payload?.[0]?.payload;
                              return item?.label ? `${label} — ${item.label}` : label;
                            }}
                          />
                          <Legend
                            wrapperStyle={{ fontSize: 10 }}
                            formatter={(value: string) => {
                              const labels: Record<string, string> = {
                                ghi: 'GHI (W/m²)',
                                pExp: 'P_exp (W)',
                                tempCell: 'T_cell (°C)',
                                tempAmbient: 'T_amb (°C)',
                              };
                              return labels[value] || value;
                            }}
                          />
                          <Line yAxisId="left" type="monotone" dataKey="ghi" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} name="ghi" />
                          <Line yAxisId="left" type="monotone" dataKey="pExp" stroke="#0d9488" strokeWidth={2} dot={{ r: 3 }} name="pExp" />
                          <Line yAxisId="right" type="monotone" dataKey="tempCell" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} name="tempCell" />
                          <Line yAxisId="right" type="monotone" dataKey="tempAmbient" stroke="#3b82f6" strokeWidth={1.5} strokeDasharray="5 5" dot={{ r: 2 }} name="tempAmbient" />
                          <ReferenceLine yAxisId="left" y={1000} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'STC 1000', position: 'right', style: { fontSize: 9, fill: '#f59e0b' } }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="h-32 flex items-center justify-center bg-gray-50 rounded text-xs text-gray-500">
                      Se necesitan al menos 2 mediciones en el mismo día para generar el gráfico temporal.
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Tabla del historial */}
          <div className="overflow-x-auto rounded-lg border border-teal-100">
            <Table>
              <TableHeader>
                <TableRow className="bg-teal-50">
                  <TableHead className="text-[10px] font-bold text-teal-800 w-[100px]">
                    Fecha/Hora <SortIcon field="timestamp" />
                  </TableHead>
                  <TableHead className="text-[10px] font-bold text-teal-800">Etiqueta</TableHead>
                  <TableHead className="text-[10px] font-bold text-amber-700 text-right">
                    GHI <SortIcon field="ghi" />
                  </TableHead>
                  <TableHead className="text-[10px] font-bold text-blue-700 text-right">
                    T_amb <SortIcon field="tempAmbient" />
                  </TableHead>
                  <TableHead className="text-[10px] font-bold text-red-700 text-right">
                    T_cell <SortIcon field="tempCell" />
                  </TableHead>
                  <TableHead className="text-[10px] font-bold text-teal-700 text-right">
                    P_exp <SortIcon field="pExp" />
                  </TableHead>
                  <TableHead className="text-[10px] font-bold text-indigo-700 text-right">
                    PR <SortIcon field="prMulcue" />
                  </TableHead>
                  <TableHead className="text-[10px] font-bold text-gray-600 text-center w-[60px]">Estado</TableHead>
                  <TableHead className="text-[10px] font-bold text-gray-600 text-center w-[80px]">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedRecords.map((r, i) => {
                  const date = new Date(r.timestamp);
                  return (
                    <TableRow key={r.id} className={`${i % 2 === 0 ? 'bg-white' : 'bg-teal-50/30'} hover:bg-teal-100/50 transition-colors`}>
                      <TableCell className="text-[10px] font-mono">
                        <div>{date.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })}</div>
                        <div className="text-gray-400">{date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</div>
                      </TableCell>
                      <TableCell className="text-[10px] max-w-[120px] truncate" title={r.label}>
                        {r.label || '—'}
                      </TableCell>
                      <TableCell className="text-[10px] font-mono text-right text-amber-700 font-medium">
                        {r.ghi.toFixed(0)}
                        <span className="text-gray-400 font-normal"> W/m²</span>
                      </TableCell>
                      <TableCell className="text-[10px] font-mono text-right text-blue-700">
                        {r.tempAmbient.toFixed(1)}°C
                      </TableCell>
                      <TableCell className="text-[10px] font-mono text-right text-red-700">
                        {r.tempCell.toFixed(1)}°C
                        {r.tempCellManual && <span className="text-[8px] text-red-400 ml-0.5" title="Medida manualmente">✎</span>}
                      </TableCell>
                      <TableCell className="text-[10px] font-mono text-right text-teal-700 font-medium">
                        {r.pExp.toFixed(1)}
                        <span className="text-gray-400 font-normal"> W</span>
                        <div className="text-[8px] text-gray-400">
                          {((r.pExp / r.panelPower - 1) * 100).toFixed(1)}% vs STC
                        </div>
                      </TableCell>
                      <TableCell className="text-[10px] font-mono text-right text-indigo-700">
                        {(r.prMulcue * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell className="text-center">
                        {(() => {
                          const badge = getAlertBadge(r.prMulcue, r.tempAmbient, r.tempCoeff);
                          return (
                            <span
                              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[9px] font-bold"
                              style={{ backgroundColor: badge.bgColor, color: badge.color, border: `1px solid ${badge.color}30` }}
                              title={`Desviación PR: ${badge.severity}`}
                            >
                              {badge.icon} {badge.label}
                            </span>
                          );
                        })()}
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={() => onLoadRecord(r)}
                            className="p-1 rounded hover:bg-teal-200 text-teal-600 transition-colors"
                            title="Cargar esta medición"
                          >
                            <Eye size={12} />
                          </button>
                          <button
                            onClick={() => onRemove(r.id)}
                            className="p-1 rounded hover:bg-red-200 text-red-500 transition-colors"
                            title="Eliminar"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>

          {/* Nota informativa */}
          <p className="text-[9px] text-gray-400 text-center">
            Las mediciones se guardan en el navegador (localStorage). Exporta a CSV para respaldo permanente.
            El gráfico temporal muestra la evolución de las condiciones durante un día seleccionado.
          </p>
        </>
      )}
    </div>
  );
}
