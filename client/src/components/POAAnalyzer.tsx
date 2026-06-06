import { useEffect, useMemo, useState } from 'react';
import { EPWData } from '@/lib/epwParser';
import { calculateHourlyPOA } from '@/lib/liuJordanModel';
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
  Area,
  AreaChart,
} from 'recharts';
import { Zap, Settings } from 'lucide-react';
import { Slider } from '@/components/ui/slider';

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

interface POAAnalyzerProps {
  weatherData: EPWData;
  tiltAngle?: number;
  surfaceAzimuth?: number;
  sharedAlbedo?: number;
  sharedUsePerez?: boolean;
  onConfigChange?: (config: { tilt?: number; azimuth?: number; albedo?: number; usePerez?: boolean }) => void;
}

export default function POAAnalyzer({ weatherData, tiltAngle: initialTilt = 0, surfaceAzimuth: initialAzimuth = 0, sharedAlbedo, sharedUsePerez, onConfigChange }: POAAnalyzerProps) {
  const [tilt, setTilt] = useState(initialTilt || Math.round(weatherData.location.latitude));
  const [azimuth, setAzimuth] = useState(initialAzimuth);
  const [albedo, setAlbedo] = useState(sharedAlbedo ?? 0.2);
  const [usePerezModel, setUsePerezModel] = useState(sharedUsePerez ?? false);

  // Sincronizar estado local cuando cambien props desde Home.tsx (ej: cambios desde el Simulador)
  useEffect(() => {
    if (initialTilt && initialTilt !== tilt) setTilt(initialTilt);
  }, [initialTilt]);
  useEffect(() => {
    if (initialAzimuth !== undefined && initialAzimuth !== azimuth) setAzimuth(initialAzimuth);
  }, [initialAzimuth]);
  useEffect(() => {
    if (sharedAlbedo !== undefined && sharedAlbedo !== albedo) setAlbedo(sharedAlbedo);
  }, [sharedAlbedo]);
  useEffect(() => {
    if (sharedUsePerez !== undefined && sharedUsePerez !== usePerezModel) setUsePerezModel(sharedUsePerez);
  }, [sharedUsePerez]);

  // Propagar cambios de configuración al estado compartido en Home.tsx
  useEffect(() => {
    if (onConfigChange) {
      onConfigChange({ tilt, azimuth, albedo, usePerez: usePerezModel });
    }
  }, [tilt, azimuth, albedo, usePerezModel]);

  const poaData = useMemo(() => {
    const tiltRad = (tilt * Math.PI) / 180;
    const azimuthRad = (azimuth * Math.PI) / 180;

    const monthlyData = MONTHS.map((month, monthIdx) => {
      const monthWeatherData = weatherData.weatherData.filter(w => w.month === monthIdx + 1);

      if (monthWeatherData.length === 0) {
        return {
          month,
          directPOA: 0,
          diffusePOA: 0,
          reflectedPOA: 0,
          totalPOA: 0,
          avgTemp: 0,
        };
      }

      let totalDirectPOA = 0;
      let totalDiffusePOA = 0;
      let totalReflectedPOA = 0;
      let totalTotalPOA = 0;
      let totalTemp = 0;

      monthWeatherData.forEach(w => {
        // Calcular día del año
        const daysInMonths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
        let dayOfYear = w.day;
        for (let i = 0; i < w.month - 1; i++) {
          dayOfYear += daysInMonths[i];
        }

        const poa = calculateHourlyPOA(
          weatherData.location.latitude,
          weatherData.location.longitude,
          -75, // Zona horaria estándar para Colombia (UTC-5)
          dayOfYear,
          w.hour,
          w.minute,
          w.directNormalIrradiance,
          w.diffuseHorizontalIrradiance,
          w.globalHorizontalIrradiance,
          tiltRad,
          azimuthRad,
          albedo,
          usePerezModel
        );

        totalDirectPOA += poa.directPOA;
        totalDiffusePOA += poa.diffusePOA;
        totalReflectedPOA += poa.reflectedPOA;
        totalTotalPOA += poa.totalPOA;
        totalTemp += w.temperature;
      });

      return {
        month,
        directPOA: Math.round(totalDirectPOA / monthWeatherData.length),
        diffusePOA: Math.round(totalDiffusePOA / monthWeatherData.length),
        reflectedPOA: Math.round(totalReflectedPOA / monthWeatherData.length),
        totalPOA: Math.round(totalTotalPOA / monthWeatherData.length),
        avgTemp: Math.round((totalTemp / monthWeatherData.length) * 10) / 10,
      };
    });

    return monthlyData;
  }, [weatherData, tilt, azimuth, albedo, usePerezModel]);

  const stats = useMemo(() => {
    const totalPOAValues = poaData.map(d => d.totalPOA);
    const directPOAValues = poaData.map(d => d.directPOA);
    const diffusePOAValues = poaData.map(d => d.diffusePOA);

    const avgTotal = Math.round(totalPOAValues.reduce((a, b) => a + b, 0) / totalPOAValues.length);
    const avgDirect = Math.round(directPOAValues.reduce((a, b) => a + b, 0) / directPOAValues.length);
    const avgDiffuse = Math.round(diffusePOAValues.reduce((a, b) => a + b, 0) / diffusePOAValues.length);

    return {
      avgTotal,
      maxTotal: Math.max(...totalPOAValues),
      minTotal: Math.min(...totalPOAValues),
      avgDirect,
      avgDiffuse,
      directRatio: ((avgDirect / avgTotal) * 100).toFixed(1),
      diffuseRatio: ((avgDiffuse / avgTotal) * 100).toFixed(1),
      annualPOA: Math.round(totalPOAValues.reduce((a, b) => a + b, 0) * 30), // Aproximación anual
    };
  }, [poaData]);

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Zap size={20} className="text-amber-600" />
          Análisis de Radiación POA (Plane of Array)
        </h3>

        <div className="bg-white rounded-lg p-4 border border-amber-100 mb-4">
          <p className="text-sm text-gray-700 mb-3">
            <strong>Modelo Liu-Jordan Isotrópico</strong> - Estándar BIPV para cálculo de radiación en plano inclinado
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Inclinación: {tilt}°
              </label>
              <Slider
                value={[tilt]}
                onValueChange={(value) => setTilt(value[0])}
                min={0}
                max={60}
                step={1}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Azimut: {azimuth}°
              </label>
              <Slider
                value={[azimuth]}
                onValueChange={(value) => setAzimuth(value[0])}
                min={-90}
                max={90}
                step={5}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Albedo (Reflectancia): {albedo.toFixed(2)}
              </label>
              <Slider
                value={[albedo]}
                onValueChange={(value) => setAlbedo(value[0])}
                min={0}
                max={1}
                step={0.05}
              />
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-blue-50 border border-blue-200 rounded">
            <input
              type="checkbox"
              id="perezModel"
              checked={usePerezModel}
              onChange={(e) => setUsePerezModel(e.target.checked)}
              className="w-4 h-4 cursor-pointer"
            />
            <label htmlFor="perezModel" className="text-sm text-gray-700 cursor-pointer flex-1">
              <strong>Usar modelo Perez mejorado</strong> (incluye componentes circunsolar y horizonte)
            </label>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-yellow-50 rounded p-3 border border-yellow-200">
            <p className="text-xs text-gray-600 mb-1">POA Total Prom.</p>
            <p className="text-2xl font-mono font-bold text-yellow-700">{stats.avgTotal}</p>
            <p className="text-xs text-gray-500">W/m²</p>
          </div>

          <div className="bg-orange-50 rounded p-3 border border-orange-200">
            <p className="text-xs text-gray-600 mb-1">Componente Directa</p>
            <p className="text-2xl font-mono font-bold text-orange-700">{stats.avgDirect}</p>
            <p className="text-xs text-gray-500">{stats.directRatio}% del total</p>
          </div>

          <div className="bg-blue-50 rounded p-3 border border-blue-200">
            <p className="text-xs text-gray-600 mb-1">Componente Difusa</p>
            <p className="text-2xl font-mono font-bold text-blue-700">{stats.avgDiffuse}</p>
            <p className="text-xs text-gray-500">{stats.diffuseRatio}% del total</p>
          </div>

          <div className="bg-green-50 rounded p-3 border border-green-200">
            <p className="text-xs text-gray-600 mb-1">POA Anual Aprox.</p>
            <p className="text-2xl font-mono font-bold text-green-700">{stats.annualPOA}</p>
            <p className="text-xs text-gray-500">kWh/m²</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-semibold text-gray-900 mb-4">Radiación POA Mensual (Componentes)</h4>
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={poaData}>
            <defs>
              <linearGradient id="colorDirect" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F97316" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#F97316" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorDiffuse" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorReflected" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="month" stroke="#6B7280" />
            <YAxis stroke="#6B7280" label={{ value: 'Irradiancia (W/m²)', angle: -90, position: 'insideLeft' }} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: '8px' }}
              formatter={(value) => value.toLocaleString()}
            />
            <Legend />
            <Area type="monotone" dataKey="directPOA" stackId="1" stroke="#F97316" fill="url(#colorDirect)" name="Directa POA" />
            <Area type="monotone" dataKey="diffusePOA" stackId="1" stroke="#3B82F6" fill="url(#colorDiffuse)" name="Difusa POA" />
            <Area type="monotone" dataKey="reflectedPOA" stackId="1" stroke="#8B5CF6" fill="url(#colorReflected)" name="Reflejada POA" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-semibold text-gray-900 mb-4">Comparación: POA Total vs Componentes</h4>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={poaData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="month" stroke="#6B7280" />
            <YAxis stroke="#6B7280" label={{ value: 'Irradiancia (W/m²)', angle: -90, position: 'insideLeft' }} />
            <Tooltip contentStyle={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: '8px' }} />
            <Legend />
            <Bar dataKey="directPOA" fill="#F97316" name="Directa" radius={[8, 8, 0, 0]} />
            <Bar dataKey="diffusePOA" fill="#3B82F6" name="Difusa" radius={[8, 8, 0, 0]} />
            <Bar dataKey="reflectedPOA" fill="#8B5CF6" name="Reflejada" radius={[8, 8, 0, 0]} />
            <Line type="monotone" dataKey="totalPOA" stroke="#10B981" strokeWidth={3} name="Total POA" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 mb-3">Configuración Actual</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Inclinación:</span>
              <span className="font-mono font-semibold text-gray-900">{tilt}°</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Azimut:</span>
              <span className="font-mono font-semibold text-gray-900">{azimuth}°</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Albedo:</span>
              <span className="font-mono font-semibold text-gray-900">{albedo.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Modelo:</span>
              <span className="font-mono font-semibold text-gray-900">{usePerezModel ? 'Perez' : 'Liu-Jordan'}</span>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 mb-3">Notas Técnicas</h4>
          <div className="space-y-2 text-xs text-gray-700">
            <p>
              <strong>Liu-Jordan:</strong> Modelo isotrópico estándar BIPV. Asume radiación difusa uniformemente distribuida.
            </p>
            <p>
              <strong>Perez:</strong> Modelo anisotrópico mejorado. Incluye componentes circunsolar y de horizonte para mayor precisión.
            </p>
            <p>
              <strong>Albedo:</strong> Reflectancia del suelo. 0.2 (pasto), 0.7 (nieve), 0.9 (agua).
            </p>
          </div>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-900">
        <p><strong>Referencia:</strong> Liu, B.Y.H. & Jordan, R.C. (1961). The interrelationship and characteristic distribution of direct, diffuse and total solar radiation. Solar Energy, 4(3), 1-19.</p>
      </div>
    </div>
  );
}
