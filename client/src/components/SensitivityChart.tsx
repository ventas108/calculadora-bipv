import { useMemo } from 'react';
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ReferenceDot,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import {
  quickEstimate,
  G_NOCT_REF,
  G_STC,
} from '@/lib/mulcueLlanos';

// ============================================================
// INTERFACES
// ============================================================

interface SensitivityChartProps {
  /** GHI anual del punto PVGIS (kWh/m²/año) */
  ghiAnnualKwhM2: number;
  /** Temperatura ambiente promedio (°C) */
  ambientTemp: number;
  /** Coeficiente de temperatura del panel (%/°C, negativo) */
  tempCoeffGamma: number;
  /** Potencia nominal del módulo (W) */
  modulePowerW: number;
  /** Cantidad de módulos */
  moduleCount: number;
  /** Clave de región colombiana */
  regionKey: string;
  /** Factor de sombreado FS (0-1) */
  shadowFactor: number;
  /** NOCT del panel (°C) */
  noct: number;
  /** Valor actual de irradiancia G seleccionado (W/m²) */
  currentG: number;
}

interface DataPoint {
  g: number;
  energy: number;
  cellTemp: number;
  tempLoss: number;
  pr: number;
}

// ============================================================
// TOOLTIP PERSONALIZADO
// ============================================================

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0]?.payload as DataPoint;
  if (!data) return null;

  const isNOCT = data.g === G_NOCT_REF;
  const isSTC = data.g === G_STC;

  return (
    <div className="bg-white border border-gray-300 rounded-lg shadow-lg p-3 text-xs max-w-[220px]">
      <p className="font-bold text-gray-900 mb-1.5 border-b border-gray-200 pb-1">
        G = {data.g} W/m²
        {isNOCT && <span className="text-blue-600 ml-1">(NOCT)</span>}
        {isSTC && <span className="text-orange-600 ml-1">(STC)</span>}
      </p>
      <div className="space-y-1">
        <p className="flex justify-between">
          <span className="text-green-700">Energía:</span>
          <span className="font-mono font-bold text-green-800">
            {data.energy >= 1000
              ? `${(data.energy / 1000).toFixed(2)} MWh`
              : `${data.energy.toFixed(0)} kWh`}
          </span>
        </p>
        <p className="flex justify-between">
          <span className="text-orange-700">T. celda:</span>
          <span className="font-mono font-bold text-orange-800">{data.cellTemp.toFixed(1)}°C</span>
        </p>
        <p className="flex justify-between">
          <span className="text-red-700">Pérdida T°:</span>
          <span className="font-mono font-bold text-red-800">{data.tempLoss.toFixed(1)}%</span>
        </p>
        <p className="flex justify-between">
          <span className="text-blue-700">PR:</span>
          <span className="font-mono font-bold text-blue-800">{(data.pr * 100).toFixed(1)}%</span>
        </p>
      </div>
    </div>
  );
}

// ============================================================
// COMPONENTE PRINCIPAL
// ============================================================

export default function SensitivityChart({
  ghiAnnualKwhM2,
  ambientTemp,
  tempCoeffGamma,
  modulePowerW,
  moduleCount,
  regionKey,
  shadowFactor,
  noct,
  currentG,
}: SensitivityChartProps) {
  // Generar datos de sensibilidad: G de 200 a 1200 W/m², paso 50
  const data = useMemo(() => {
    const points: DataPoint[] = [];
    for (let g = 200; g <= 1200; g += 50) {
      const est = quickEstimate({
        ghiAnnualKwhM2,
        ambientTemp,
        tempCoeffGamma,
        modulePowerW,
        moduleCount,
        regionKey,
        shadowFactor,
        noct,
        avgIrradiance: g,
      });
      points.push({
        g,
        energy: est.production.energyKwh,
        cellTemp: est.cellTemp,
        tempLoss: est.tempLossPercent,
        pr: est.pr.prCorrected,
      });
    }
    return points;
  }, [ghiAnnualKwhM2, ambientTemp, tempCoeffGamma, modulePowerW, moduleCount, regionKey, shadowFactor, noct]);

  // Encontrar el punto actual (o el más cercano)
  const currentPoint = useMemo(() => {
    const closest = data.reduce((prev, curr) =>
      Math.abs(curr.g - currentG) < Math.abs(prev.g - currentG) ? curr : prev
    );
    return closest;
  }, [data, currentG]);

  // Calcular el punto exacto para currentG si no está en los datos
  const exactCurrentPoint = useMemo(() => {
    const est = quickEstimate({
      ghiAnnualKwhM2,
      ambientTemp,
      tempCoeffGamma,
      modulePowerW,
      moduleCount,
      regionKey,
      shadowFactor,
      noct,
      avgIrradiance: currentG,
    });
    return {
      g: currentG,
      energy: est.production.energyKwh,
      cellTemp: est.cellTemp,
      tempLoss: est.tempLossPercent,
      pr: est.pr.prCorrected,
    };
  }, [ghiAnnualKwhM2, ambientTemp, tempCoeffGamma, modulePowerW, moduleCount, regionKey, shadowFactor, noct, currentG]);

  // Rango de energía para el eje Y
  const minEnergy = Math.min(...data.map(d => d.energy));
  const maxEnergy = Math.max(...data.map(d => d.energy));
  const energyPadding = (maxEnergy - minEnergy) * 0.1;

  // Rango de T_cell para el eje Y derecho
  const maxTemp = Math.max(...data.map(d => d.cellTemp));

  return (
    <div className="bg-gradient-to-br from-slate-50 to-gray-50 border border-slate-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h5 className="text-sm font-semibold text-slate-800 flex items-center gap-1.5">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-600">
              <path d="M3 3v18h18" />
              <path d="M18 17V9" />
              <path d="M13 17V5" />
              <path d="M8 17v-3" />
            </svg>
            Sensibilidad: Irradiancia G vs Producción
          </h5>
          <p className="text-[10px] text-slate-500 mt-0.5">
            Impacto de la irradiancia de referencia en T_celda, pérdidas y producción anual
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px]">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
            NOCT ({G_NOCT_REF})
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-orange-500 inline-block" />
            STC ({G_STC})
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-500 inline-block border-2 border-white shadow" />
            Actual ({currentG})
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={data} margin={{ top: 10, right: 50, left: 10, bottom: 5 }}>
          <defs>
            <linearGradient id="energyGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#16a34a" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#16a34a" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f97316" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#f97316" stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />

          <XAxis
            dataKey="g"
            tick={{ fontSize: 10, fill: '#64748b' }}
            tickLine={{ stroke: '#94a3b8' }}
            label={{
              value: 'Irradiancia G (W/m²)',
              position: 'insideBottom',
              offset: -2,
              style: { fontSize: 10, fill: '#475569' },
            }}
          />

          {/* Eje Y izquierdo: Energía */}
          <YAxis
            yAxisId="energy"
            orientation="left"
            tick={{ fontSize: 10, fill: '#16a34a' }}
            tickLine={{ stroke: '#16a34a' }}
            domain={[
              Math.floor((minEnergy - energyPadding) / 100) * 100,
              Math.ceil((maxEnergy + energyPadding) / 100) * 100,
            ]}
            tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : `${v}`}
            label={{
              value: 'Energía (kWh/año)',
              angle: -90,
              position: 'insideLeft',
              offset: 5,
              style: { fontSize: 10, fill: '#16a34a' },
            }}
          />

          {/* Eje Y derecho: T_cell */}
          <YAxis
            yAxisId="temp"
            orientation="right"
            tick={{ fontSize: 10, fill: '#f97316' }}
            tickLine={{ stroke: '#f97316' }}
            domain={[0, Math.ceil(maxTemp / 10) * 10 + 10]}
            tickFormatter={(v: number) => `${v}°C`}
            label={{
              value: 'T. celda (°C)',
              angle: 90,
              position: 'insideRight',
              offset: 10,
              style: { fontSize: 10, fill: '#f97316' },
            }}
          />

          <Tooltip content={<CustomTooltip />} />

          {/* Área de energía */}
          <Area
            yAxisId="energy"
            type="monotone"
            dataKey="energy"
            stroke="#16a34a"
            strokeWidth={2.5}
            fill="url(#energyGradient)"
            name="Energía (kWh/año)"
            dot={false}
            activeDot={{ r: 5, fill: '#16a34a', stroke: '#fff', strokeWidth: 2 }}
          />

          {/* Línea de T_cell */}
          <Line
            yAxisId="temp"
            type="monotone"
            dataKey="cellTemp"
            stroke="#f97316"
            strokeWidth={2}
            strokeDasharray="5 3"
            name="T. celda (°C)"
            dot={false}
            activeDot={{ r: 4, fill: '#f97316', stroke: '#fff', strokeWidth: 2 }}
          />

          {/* Línea de pérdida por temperatura */}
          <Line
            yAxisId="temp"
            type="monotone"
            dataKey="tempLoss"
            stroke="#dc2626"
            strokeWidth={1.5}
            strokeDasharray="2 2"
            name="Pérdida T° (%)"
            dot={false}
            activeDot={{ r: 3, fill: '#dc2626', stroke: '#fff', strokeWidth: 2 }}
          />

          {/* Líneas de referencia NOCT y STC */}
          <ReferenceLine
            x={G_NOCT_REF}
            yAxisId="energy"
            stroke="#3b82f6"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            label={{
              value: 'NOCT',
              position: 'top',
              fill: '#3b82f6',
              fontSize: 10,
              fontWeight: 600,
            }}
          />
          <ReferenceLine
            x={G_STC}
            yAxisId="energy"
            stroke="#f97316"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            label={{
              value: 'STC',
              position: 'top',
              fill: '#f97316',
              fontSize: 10,
              fontWeight: 600,
            }}
          />

          {/* Punto actual */}
          <ReferenceDot
            x={exactCurrentPoint.g}
            y={exactCurrentPoint.energy}
            yAxisId="energy"
            r={7}
            fill="#dc2626"
            stroke="#fff"
            strokeWidth={3}
          />

          <Legend
            verticalAlign="bottom"
            height={24}
            iconSize={10}
            wrapperStyle={{ fontSize: 10, paddingTop: 8 }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Resumen numérico debajo del gráfico */}
      <div className="grid grid-cols-3 gap-2 mt-3">
        <div className="bg-blue-50 border border-blue-200 rounded p-2 text-center">
          <p className="text-[10px] text-blue-600">@ NOCT ({G_NOCT_REF} W/m²)</p>
          <p className="text-xs font-bold text-blue-800 font-mono">
            {(() => {
              const noctPt = data.find(d => d.g === G_NOCT_REF);
              if (!noctPt) return '—';
              return noctPt.energy >= 1000
                ? `${(noctPt.energy / 1000).toFixed(2)} MWh`
                : `${noctPt.energy.toFixed(0)} kWh`;
            })()}
          </p>
          <p className="text-[10px] text-blue-500 font-mono">
            T_c: {data.find(d => d.g === G_NOCT_REF)?.cellTemp.toFixed(1) || '—'}°C
          </p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded p-2 text-center">
          <p className="text-[10px] text-red-600">@ Actual ({currentG} W/m²)</p>
          <p className="text-xs font-bold text-red-800 font-mono">
            {exactCurrentPoint.energy >= 1000
              ? `${(exactCurrentPoint.energy / 1000).toFixed(2)} MWh`
              : `${exactCurrentPoint.energy.toFixed(0)} kWh`}
          </p>
          <p className="text-[10px] text-red-500 font-mono">
            T_c: {exactCurrentPoint.cellTemp.toFixed(1)}°C | -{exactCurrentPoint.tempLoss.toFixed(1)}%
          </p>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded p-2 text-center">
          <p className="text-[10px] text-orange-600">@ STC ({G_STC} W/m²)</p>
          <p className="text-xs font-bold text-orange-800 font-mono">
            {(() => {
              const stcPt = data.find(d => d.g === G_STC);
              if (!stcPt) return '—';
              return stcPt.energy >= 1000
                ? `${(stcPt.energy / 1000).toFixed(2)} MWh`
                : `${stcPt.energy.toFixed(0)} kWh`;
            })()}
          </p>
          <p className="text-[10px] text-orange-500 font-mono">
            T_c: {data.find(d => d.g === G_STC)?.cellTemp.toFixed(1) || '—'}°C
          </p>
        </div>
      </div>
    </div>
  );
}
