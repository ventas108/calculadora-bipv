import { EPWData, getMonthlyWeatherSummary, getWeatherCorrectionFactor } from '@/lib/epwParser';
import { Cloud, Droplets, Sun, Wind, Zap } from 'lucide-react';

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

interface WeatherAnalysisProps {
  weatherData: EPWData;
  points: Array<{ month: string; day: number; hour: number; fs: number }>;
}

export default function WeatherAnalysis({ weatherData, points }: WeatherAnalysisProps) {
  // Calcular correcciones meteorológicas para cada punto
  const correctedPoints = points.map(p => {
    const monthNum = MONTHS.indexOf(p.month) + 1;
    const correction = getWeatherCorrectionFactor(weatherData, monthNum, p.day, p.hour);
    return {
      ...p,
      correction,
      correctedFS: p.fs * correction,
    };
  });

  // Calcular impacto promedio
  const avgCorrection = correctedPoints.length > 0
    ? correctedPoints.reduce((a, b) => a + b.correction, 0) / correctedPoints.length
    : 1;

  const impactPercentage = ((1 - avgCorrection) * 100).toFixed(1);

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Análisis de Impacto Meteorológico</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="bg-white rounded-lg p-4 border border-purple-100">
            <div className="flex items-center gap-2 mb-2">
              <Cloud size={18} className="text-gray-500" />
              <p className="text-sm text-gray-600">Factor Promedio</p>
            </div>
            <p className="text-2xl font-mono font-bold text-purple-700">{avgCorrection.toFixed(3)}</p>
            <p className="text-xs text-gray-500 mt-1">1.0 = Sin impacto</p>
          </div>

          <div className="bg-white rounded-lg p-4 border border-purple-100">
            <div className="flex items-center gap-2 mb-2">
              <Zap size={18} className="text-yellow-500" />
              <p className="text-sm text-gray-600">Impacto</p>
            </div>
            <p className="text-2xl font-mono font-bold text-yellow-600">{impactPercentage}%</p>
            <p className="text-xs text-gray-500 mt-1">Reducción de FS</p>
          </div>

          <div className="bg-white rounded-lg p-4 border border-purple-100">
            <div className="flex items-center gap-2 mb-2">
              <Sun size={18} className="text-orange-500" />
              <p className="text-sm text-gray-600">FS Original</p>
            </div>
            <p className="text-2xl font-mono font-bold text-orange-600">
              {(points.reduce((a, b) => a + b.fs, 0) / points.length).toFixed(3)}
            </p>
            <p className="text-xs text-gray-500 mt-1">Promedio</p>
          </div>

          <div className="bg-white rounded-lg p-4 border border-purple-100">
            <div className="flex items-center gap-2 mb-2">
              <Zap size={18} className="text-purple-500" />
              <p className="text-sm text-gray-600">FS Corregido</p>
            </div>
            <p className="text-2xl font-mono font-bold text-purple-600">
              {(correctedPoints.reduce((a, b) => a + b.correctedFS, 0) / correctedPoints.length).toFixed(3)}
            </p>
            <p className="text-xs text-gray-500 mt-1">Con meteorología</p>
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-purple-100">
          <p className="text-sm text-gray-700">
            <strong>Interpretación:</strong> Los datos meteorológicos reducen el Factor de Sombreado en un {impactPercentage}% en promedio.
            Esto se debe principalmente a la nubosidad y humedad que afectan la radiación solar disponible.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        <h4 className="font-semibold text-gray-900">Detalles por Punto de Análisis</h4>
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Mes</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Día</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Hora</th>
                <th className="px-4 py-2 text-right font-semibold text-gray-700">FS Original</th>
                <th className="px-4 py-2 text-right font-semibold text-gray-700">Factor Meteo</th>
                <th className="px-4 py-2 text-right font-semibold text-gray-700">FS Corregido</th>
                <th className="px-4 py-2 text-right font-semibold text-gray-700">Cambio</th>
              </tr>
            </thead>
            <tbody>
              {correctedPoints.map((point, idx) => (
                <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-4 py-2 font-mono text-gray-900">{point.month}</td>
                  <td className="px-4 py-2 font-mono text-gray-900">{point.day}</td>
                  <td className="px-4 py-2 font-mono text-gray-900">{point.hour}:00</td>
                  <td className="px-4 py-2 text-right font-mono font-semibold text-gray-900">
                    {point.fs.toFixed(3)}
                  </td>
                  <td className="px-4 py-2 text-right font-mono font-semibold text-purple-600">
                    {point.correction.toFixed(3)}
                  </td>
                  <td className="px-4 py-2 text-right font-mono font-semibold text-blue-600">
                    {point.correctedFS.toFixed(3)}
                  </td>
                  <td className="px-4 py-2 text-right font-mono font-semibold text-orange-600">
                    {((point.fs - point.correctedFS) / point.fs * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
        <h4 className="font-semibold text-gray-900 flex items-center gap-2">
          <Cloud size={18} className="text-blue-600" />
          Factores Meteorológicos Considerados
        </h4>
        <ul className="text-sm text-gray-700 space-y-2">
          <li><strong>Nubosidad:</strong> Reduce la radiación directa disponible (máximo 30% de reducción)</li>
          <li><strong>Humedad:</strong> Aumenta la difusión de la luz solar (máximo 10% de reducción)</li>
          <li><strong>Temperatura:</strong> Afecta la eficiencia del panel fotovoltaico (datos incluidos en EPW)</li>
          <li><strong>Viento:</strong> Ayuda a enfriar los paneles mejorando eficiencia (datos incluidos en EPW)</li>
          <li><strong>Presión Atmosférica:</strong> Influye en la transmisión de radiación (datos incluidos en EPW)</li>
        </ul>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <p className="text-sm text-amber-900">
          <strong>Nota:</strong> Los valores corregidos reflejan un análisis más realista del rendimiento solar considerando
          las condiciones climáticas típicas de Medellín. Estos datos provienen del archivo EPW (Energy Plus Weather) que
          contiene un año meteorológico típico para la ubicación.
        </p>
      </div>
    </div>
  );
}
