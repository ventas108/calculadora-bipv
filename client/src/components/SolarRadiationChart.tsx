import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { EPWData, getMonthlyWeatherSummary } from '@/lib/epwParser';

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

interface SolarRadiationChartProps {
  weatherData: EPWData;
}

export default function SolarRadiationChart({ weatherData }: SolarRadiationChartProps) {
  const chartData = useMemo(() => {
    return MONTHS.map((month, idx) => {
      const monthData = weatherData.weatherData.filter(w => w.month === idx + 1);
      
      if (monthData.length === 0) {
        return {
          month,
          direct: 0,
          diffuse: 0,
          global: 0,
          avgTemp: 0,
        };
      }

      const avgDirect = monthData.reduce((a, w) => a + w.directNormalIrradiance, 0) / monthData.length;
      const avgDiffuse = monthData.reduce((a, w) => a + w.diffuseHorizontalIrradiance, 0) / monthData.length;
      const avgGlobal = monthData.reduce((a, w) => a + w.globalHorizontalIrradiance, 0) / monthData.length;
      const avgTemp = monthData.reduce((a, w) => a + w.temperature, 0) / monthData.length;

      return {
        month,
        direct: Math.round(avgDirect),
        diffuse: Math.round(avgDiffuse),
        global: Math.round(avgGlobal),
        avgTemp: Math.round(avgTemp * 10) / 10,
      };
    });
  }, [weatherData]);

  const stats = useMemo(() => {
    const directValues = chartData.map(d => d.direct);
    const diffuseValues = chartData.map(d => d.diffuse);
    const globalValues = chartData.map(d => d.global);

    return {
      directAvg: Math.round(directValues.reduce((a, b) => a + b, 0) / directValues.length),
      directMax: Math.max(...directValues),
      directMin: Math.min(...directValues),
      diffuseAvg: Math.round(diffuseValues.reduce((a, b) => a + b, 0) / diffuseValues.length),
      diffuseMax: Math.max(...diffuseValues),
      globalAvg: Math.round(globalValues.reduce((a, b) => a + b, 0) / globalValues.length),
      ratio: ((diffuseValues.reduce((a, b) => a + b, 0) / diffuseValues.length) / 
              (directValues.reduce((a, b) => a + b, 0) / directValues.length) * 100).toFixed(1),
    };
  }, [chartData]);

  const bestMonths = useMemo(() => {
    return chartData
      .map((d, idx) => ({ ...d, idx }))
      .sort((a, b) => b.global - a.global)
      .slice(0, 3);
  }, [chartData]);

  const worstMonths = useMemo(() => {
    return chartData
      .map((d, idx) => ({ ...d, idx }))
      .sort((a, b) => a.global - b.global)
      .slice(0, 3);
  }, [chartData]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">Radiación Directa Prom.</p>
          <p className="text-2xl font-mono font-bold text-orange-700">{stats.directAvg}</p>
          <p className="text-xs text-gray-500 mt-1">W/m²</p>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">Radiación Difusa Prom.</p>
          <p className="text-2xl font-mono font-bold text-blue-700">{stats.diffuseAvg}</p>
          <p className="text-xs text-gray-500 mt-1">W/m²</p>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">Radiación Global Prom.</p>
          <p className="text-2xl font-mono font-bold text-yellow-700">{stats.globalAvg}</p>
          <p className="text-xs text-gray-500 mt-1">W/m²</p>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">Ratio Difusa/Directa</p>
          <p className="text-2xl font-mono font-bold text-purple-700">{stats.ratio}%</p>
          <p className="text-xs text-gray-500 mt-1">Nubosidad relativa</p>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Radiación Solar Mensual</h3>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="month" stroke="#6B7280" />
            <YAxis yAxisId="left" stroke="#6B7280" label={{ value: 'Irradiancia (W/m²)', angle: -90, position: 'insideLeft' }} />
            <YAxis yAxisId="right" orientation="right" stroke="#6B7280" label={{ value: 'Temperatura (°C)', angle: 90, position: 'insideRight' }} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: '8px' }}
              formatter={(value) => value.toLocaleString()}
            />
            <Legend />
            <Bar yAxisId="left" dataKey="direct" fill="#F97316" name="Radiación Directa" radius={[8, 8, 0, 0]} />
            <Bar yAxisId="left" dataKey="diffuse" fill="#3B82F6" name="Radiación Difusa" radius={[8, 8, 0, 0]} />
            <Line yAxisId="right" type="monotone" dataKey="avgTemp" stroke="#EF4444" name="Temperatura" strokeWidth={2} dot={{ fill: '#EF4444', r: 4 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">📈</span> Mejores Meses
          </h4>
          <div className="space-y-3">
            {bestMonths.map((month, idx) => (
              <div key={idx} className="bg-white rounded-lg p-3 border border-green-100">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-semibold text-gray-900">{idx + 1}. {month.month}</span>
                  <span className="text-lg font-mono font-bold text-green-700">{month.global} W/m²</span>
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div className="flex justify-between">
                    <span>Directa:</span>
                    <span className="font-mono text-orange-600">{month.direct} W/m²</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Difusa:</span>
                    <span className="font-mono text-blue-600">{month.diffuse} W/m²</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">📉</span> Peores Meses
          </h4>
          <div className="space-y-3">
            {worstMonths.map((month, idx) => (
              <div key={idx} className="bg-white rounded-lg p-3 border border-red-100">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-semibold text-gray-900">{idx + 1}. {month.month}</span>
                  <span className="text-lg font-mono font-bold text-red-700">{month.global} W/m²</span>
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div className="flex justify-between">
                    <span>Directa:</span>
                    <span className="font-mono text-orange-600">{month.direct} W/m²</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Difusa:</span>
                    <span className="font-mono text-blue-600">{month.diffuse} W/m²</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 space-y-4">
        <h4 className="font-semibold text-gray-900">Recomendaciones de Orientación</h4>
        <div className="space-y-3 text-sm text-gray-700">
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <p className="font-semibold text-gray-900 mb-1">Azimut Óptimo:</p>
            <p>Para Medellín (6.22°N), el azimut óptimo es <strong>0° (Sur)</strong> para maximizar radiación durante todo el año.</p>
          </div>
          
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <p className="font-semibold text-gray-900 mb-1">Inclinación Recomendada:</p>
            <p>Una inclinación de <strong>{Math.round(weatherData.location.latitude)}° (igual a la latitud)</strong> es óptima para producción anual. Para verano, aumenta a 15-20°; para invierno, reduce a 0-5°.</p>
          </div>

          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <p className="font-semibold text-gray-900 mb-1">Ratio Directo/Difuso:</p>
            <p>El {stats.ratio}% de radiación difusa indica <strong>{parseFloat(stats.ratio) > 30 ? 'alta nubosidad' : 'baja nubosidad'}</strong>. Esto afecta la orientación óptima: con más difusa, la inclinación es menos crítica.</p>
          </div>

          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <p className="font-semibold text-gray-900 mb-1">Variación Estacional:</p>
            <p>La diferencia entre mejores y peores meses es de <strong>{stats.directMax - stats.directMin} W/m²</strong>. Considera seguimiento solar (tracking) para sitios con alta variación.</p>
          </div>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-900">
        <p><strong>Nota:</strong> Estos datos provienen del archivo EPW de Medellín y representan un año meteorológico típico. La radiación directa es más sensible a la nubosidad, mientras que la difusa es más consistente durante todo el año.</p>
      </div>
    </div>
  );
}
