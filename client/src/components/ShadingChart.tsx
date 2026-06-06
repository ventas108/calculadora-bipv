import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface AnalysisPoint {
  month: string;
  fs: number;
}

interface ShadingChartProps {
  data: AnalysisPoint[];
}

export function FSDistributionChart({ data }: ShadingChartProps) {
  // Agrupar por mes y calcular promedio
  const monthlyData = data.reduce((acc, point) => {
    const existing = acc.find(d => d.month === point.month);
    if (existing) {
      existing.fsValues.push(point.fs);
    } else {
      acc.push({ month: point.month, fsValues: [point.fs] });
    }
    return acc;
  }, [] as Array<{ month: string; fsValues: number[] }>);

  const chartData = monthlyData.map(d => ({
    month: d.month,
    avg: parseFloat((d.fsValues.reduce((a, b) => a + b, 0) / d.fsValues.length).toFixed(3)),
    min: Math.min(...d.fsValues),
    max: Math.max(...d.fsValues),
  }));

  // Colores basados en FS
  const getBarColor = (value: number) => {
    if (value >= 0.9) return '#10B981'; // Verde
    if (value >= 0.7) return '#F59E0B'; // Naranja
    return '#EF4444'; // Rojo
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Distribución de FS por Mes</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="month" stroke="#6B7280" />
            <YAxis stroke="#6B7280" domain={[0, 1]} />
            <Tooltip
              contentStyle={{ backgroundColor: '#FFFFFF', border: '1px solid #E5E7EB' }}
              formatter={(value: number) => value.toFixed(3)}
            />
            <Bar dataKey="avg" name="FS Promedio" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.avg)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Rango de FS (Mín-Máx) por Mes</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="month" stroke="#6B7280" />
            <YAxis stroke="#6B7280" domain={[0, 1]} />
            <Tooltip
              contentStyle={{ backgroundColor: '#FFFFFF', border: '1px solid #E5E7EB' }}
              formatter={(value: number) => value.toFixed(3)}
            />
            <Legend />
            <Line type="monotone" dataKey="max" stroke="#10B981" name="FS Máximo" strokeWidth={2} />
            <Line type="monotone" dataKey="avg" stroke="#0066CC" name="FS Promedio" strokeWidth={2} />
            <Line type="monotone" dataKey="min" stroke="#EF4444" name="FS Mínimo" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
