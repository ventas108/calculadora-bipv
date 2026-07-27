import { useState, useMemo, useEffect, useCallback } from 'react';
import { Slider } from '@/components/ui/slider';
import { Card } from '@/components/ui/card';
import { EPWData } from '@/lib/epwParser';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  ComposedChart,
  Bar,
} from 'recharts';
import { Compass, Sliders, Zap, ArrowRight, RotateCw, Target, TrendingUp, AlertTriangle, Lock } from 'lucide-react';

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

/** Datos de orientación óptima para enviar al Simulador */
export interface OptimizerResult {
  optimalTilt: number;
  optimalAzimuth: number;
  currentTilt: number;
  currentAzimuth: number;
  optimalPOA: number; // W/m² promedio anual en orientación óptima
  currentPOA: number; // W/m² promedio anual en orientación actual
  gainPercent: number; // Ganancia % del óptimo vs actual
  monthlyPOA: Array<{
    month: string;
    totalPOA: number;
    directPOA: number;
    diffusePOA: number;
    reflectedPOA: number;
    avgTemp: number;
    avgWindSpeed: number;
  }>;
}

interface OrientationOptimizerProps {
  weatherData: EPWData;
  // Sincronización con estado compartido POA
  sharedTilt?: number;
  sharedAzimuth?: number;
  onConfigChange?: (config: { tilt: number; azimuth: number }) => void;
  // Restricciones de instalación del Simulador
  tiltRange?: [number, number];
  azimuthLocked?: boolean;
  installationType?: string;
  // Callback para enviar datos al Simulador
  onSendToSimulator?: (result: OptimizerResult) => void;
}

/**
 * Calcula la irradiancia en una superficie inclinada
 * Usando modelo de ángulo de incidencia + isotrópico difuso + reflejado
 */
const calculateInclinedIrradiance = (
  directNormal: number,
  diffuseHorizontal: number,
  zenithAngle: number,
  tiltAngle: number,
  azimuthSurface: number,
  azimuthSun: number,
  albedo: number = 0.2
): { direct: number; diffuse: number; reflected: number; total: number } => {
  // Ángulo de incidencia
  const incidenceAngle = Math.acos(
    Math.min(1, Math.max(-1,
      Math.cos(zenithAngle) * Math.cos(tiltAngle) +
      Math.sin(zenithAngle) * Math.sin(tiltAngle) *
      Math.cos(azimuthSun - azimuthSurface)
    ))
  );

  // Componente directa
  const direct = directNormal * Math.max(0, Math.cos(incidenceAngle));

  // Componente difusa (isotrópica)
  const diffuse = diffuseHorizontal * (1 + Math.cos(tiltAngle)) / 2;

  // Componente reflejada
  const ghi = directNormal * Math.max(0, Math.cos(zenithAngle)) + diffuseHorizontal;
  const reflected = ghi * albedo * (1 - Math.cos(tiltAngle)) / 2;

  const total = Math.max(0, direct + diffuse + reflected);
  return { direct, diffuse, reflected, total };
};

/**
 * Calcula irradiancia mensual promedio para una orientación dada
 */
function calculateMonthlyForOrientation(
  weatherData: EPWData,
  tilt: number,
  azimuth: number,
  albedo: number = 0.2
): Array<{ month: string; totalPOA: number; directPOA: number; diffusePOA: number; reflectedPOA: number; avgTemp: number; avgWindSpeed: number }> {
  const tiltRad = (tilt * Math.PI) / 180;
  const azimuthRad = (azimuth * Math.PI) / 180;
  const latitude = weatherData.location.latitude * (Math.PI / 180);

  return MONTHS.map((month, monthIdx) => {
    const monthData = weatherData.weatherData.filter(w => w.month === monthIdx + 1);

    if (monthData.length === 0) {
      return { month, totalPOA: 0, directPOA: 0, diffusePOA: 0, reflectedPOA: 0, avgTemp: 0, avgWindSpeed: 1 };
    }

    let sumDirect = 0, sumDiffuse = 0, sumReflected = 0, sumTotal = 0;
    let sumTemp = 0, sumWind = 0;
    let validCount = 0;

    for (const w of monthData) {
      if (w.globalHorizontalIrradiance > 0 || w.directNormalIrradiance > 0) {
        const dayOfYear = Math.floor((monthIdx * 30.44) + (w.day || 15));
        const solarDeclination = 23.45 * Math.sin((2 * Math.PI * (dayOfYear - 81)) / 365) * (Math.PI / 180);
        const hourAngle = ((w.hour + (w.minute || 0) / 60) - 12) * 15 * (Math.PI / 180);

        const zenithAngle = Math.acos(
          Math.min(1, Math.max(-1,
            Math.sin(latitude) * Math.sin(solarDeclination) +
            Math.cos(latitude) * Math.cos(solarDeclination) * Math.cos(hourAngle)
          ))
        );

        const azimuthSun = Math.atan2(
          Math.sin(hourAngle),
          Math.cos(latitude) * Math.tan(solarDeclination) - Math.sin(latitude) * Math.cos(hourAngle)
        );

        const result = calculateInclinedIrradiance(
          w.directNormalIrradiance,
          w.diffuseHorizontalIrradiance,
          zenithAngle,
          tiltRad,
          azimuthRad,
          azimuthSun,
          albedo
        );

        sumDirect += result.direct;
        sumDiffuse += result.diffuse;
        sumReflected += result.reflected;
        sumTotal += result.total;
        validCount++;
      }
      sumTemp += w.temperature;
      sumWind += w.windSpeed;
    }

    const n = validCount || 1;
    return {
      month,
      totalPOA: Math.round(sumTotal / n),
      directPOA: Math.round(sumDirect / n),
      diffusePOA: Math.round(sumDiffuse / n),
      reflectedPOA: Math.round(sumReflected / n),
      avgTemp: Math.round((sumTemp / monthData.length) * 10) / 10,
      avgWindSpeed: Math.round((sumWind / monthData.length) * 10) / 10,
    };
  });
}

/**
 * Calcula POA anual promedio para una orientación
 */
function calculateAnnualPOA(
  weatherData: EPWData,
  tilt: number,
  azimuth: number,
  albedo: number = 0.2
): number {
  const monthly = calculateMonthlyForOrientation(weatherData, tilt, azimuth, albedo);
  return monthly.reduce((sum, m) => sum + m.totalPOA, 0) / 12;
}

export default function OrientationOptimizer({
  weatherData,
  sharedTilt,
  sharedAzimuth,
  onConfigChange,
  tiltRange,
  azimuthLocked,
  installationType,
  onSendToSimulator,
}: OrientationOptimizerProps) {
  const defaultTilt = Math.round(Math.abs(weatherData.location.latitude));
  const [azimuth, setAzimuth] = useState(sharedAzimuth ?? 0);
  const [tilt, setTilt] = useState(sharedTilt ?? defaultTilt);
  const [isSearching, setIsSearching] = useState(false);
  const [optimumFound, setOptimumFound] = useState<{ tilt: number; azimuth: number; poa: number } | null>(null);
  const [showComparison, setShowComparison] = useState(false);

  // Restricciones de instalación
  const effectiveTiltRange: [number, number] = tiltRange ?? [0, 60];
  const effectiveAzimuthLocked = azimuthLocked ?? false;

  // Sincronizar con props compartidos
  useEffect(() => {
    if (sharedTilt !== undefined && sharedTilt !== tilt) setTilt(sharedTilt);
  }, [sharedTilt]);
  useEffect(() => {
    if (sharedAzimuth !== undefined && sharedAzimuth !== azimuth) setAzimuth(sharedAzimuth);
  }, [sharedAzimuth]);

  // Propagar cambios al estado compartido
  useEffect(() => {
    if (onConfigChange) {
      onConfigChange({ tilt, azimuth });
    }
  }, [tilt, azimuth]);

  // Datos mensuales para la orientación actual
  const monthlyData = useMemo(() => {
    return calculateMonthlyForOrientation(weatherData, tilt, azimuth);
  }, [weatherData, tilt, azimuth]);

  const stats = useMemo(() => {
    const productions = monthlyData.map(d => d.totalPOA);
    const totalAnnual = productions.reduce((a, b) => a + b, 0);

    return {
      avgMonthly: Math.round(totalAnnual / 12),
      maxMonth: Math.max(...productions),
      minMonth: Math.min(...productions),
      totalAnnual: Math.round(totalAnnual),
      variance: Math.round(((Math.max(...productions) - Math.min(...productions)) / Math.max(...productions, 1)) * 100),
    };
  }, [monthlyData]);

  // Datos mensuales para la orientación óptima (si se encontró)
  const optimalMonthlyData = useMemo(() => {
    if (!optimumFound) return null;
    return calculateMonthlyForOrientation(weatherData, optimumFound.tilt, optimumFound.azimuth);
  }, [weatherData, optimumFound]);

  // === BÚSQUEDA AUTOMÁTICA DEL ÓPTIMO ===
  const searchOptimum = useCallback(() => {
    setIsSearching(true);

    // Usar setTimeout para no bloquear la UI
    setTimeout(() => {
      let bestTilt = tilt;
      let bestAzimuth = azimuth;
      let bestPOA = 0;

      // Fase 1: Barrido grueso (paso 5°)
      const tiltMin = effectiveTiltRange[0];
      const tiltMax = effectiveTiltRange[1];
      const azMin = effectiveAzimuthLocked ? azimuth : -90;
      const azMax = effectiveAzimuthLocked ? azimuth : 90;
      const azStep = effectiveAzimuthLocked ? 1 : 10;

      for (let t = tiltMin; t <= tiltMax; t += 5) {
        for (let a = azMin; a <= azMax; a += azStep) {
          const poa = calculateAnnualPOA(weatherData, t, a);
          if (poa > bestPOA) {
            bestPOA = poa;
            bestTilt = t;
            bestAzimuth = a;
          }
        }
      }

      // Fase 2: Refinamiento fino (paso 1°) alrededor del mejor encontrado
      const fineRangeTilt = 5;
      const fineRangeAz = effectiveAzimuthLocked ? 0 : 10;
      for (let t = Math.max(tiltMin, bestTilt - fineRangeTilt); t <= Math.min(tiltMax, bestTilt + fineRangeTilt); t += 1) {
        for (let a = Math.max(azMin, bestAzimuth - fineRangeAz); a <= Math.min(azMax, bestAzimuth + fineRangeAz); a += 1) {
          const poa = calculateAnnualPOA(weatherData, t, a);
          if (poa > bestPOA) {
            bestPOA = poa;
            bestTilt = t;
            bestAzimuth = a;
          }
        }
      }

      setOptimumFound({ tilt: bestTilt, azimuth: bestAzimuth, poa: bestPOA });
      setIsSearching(false);
      setShowComparison(true);
    }, 50);
  }, [weatherData, tilt, azimuth, effectiveTiltRange, effectiveAzimuthLocked]);

  // Aplicar orientación óptima
  const applyOptimum = useCallback(() => {
    if (!optimumFound) return;
    setTilt(optimumFound.tilt);
    if (!effectiveAzimuthLocked) {
      setAzimuth(optimumFound.azimuth);
    }
  }, [optimumFound, effectiveAzimuthLocked]);

  // Enviar datos al Simulador
  const sendToSimulator = useCallback(() => {
    if (!onSendToSimulator) return;
    const currentPOA = stats.avgMonthly;
    const optPOA = optimumFound?.poa ?? currentPOA;
    const gainPercent = currentPOA > 0 ? Math.round(((optPOA - currentPOA) / currentPOA) * 1000) / 10 : 0;

    const result: OptimizerResult = {
      optimalTilt: optimumFound?.tilt ?? tilt,
      optimalAzimuth: optimumFound?.azimuth ?? azimuth,
      currentTilt: tilt,
      currentAzimuth: azimuth,
      optimalPOA: optPOA,
      currentPOA: currentPOA,
      gainPercent,
      monthlyPOA: monthlyData,
    };
    onSendToSimulator(result);
  }, [onSendToSimulator, optimumFound, tilt, azimuth, stats, monthlyData]);

  const getAzimuthLabel = (value: number): string => {
    if (value === 0) return 'Sur (Óptimo)';
    if (value > 0) return `${value}° Oeste`;
    return `${Math.abs(value)}° Este`;
  };

  // Datos de comparación para gráfico
  const comparisonData = useMemo(() => {
    if (!showComparison || !optimalMonthlyData) return null;
    return monthlyData.map((current, i) => ({
      month: current.month,
      actual: current.totalPOA,
      optimo: optimalMonthlyData[i].totalPOA,
      ganancia: optimalMonthlyData[i].totalPOA - current.totalPOA,
    }));
  }, [monthlyData, optimalMonthlyData, showComparison]);

  const currentPOAAvg = stats.avgMonthly;
  const optimalPOAAvg = optimumFound?.poa ?? 0;
  const gainPercent = currentPOAAvg > 0 && optimumFound ? Math.round(((optimalPOAAvg - currentPOAAvg) / currentPOAAvg) * 1000) / 10 : 0;

  return (
    <div className="space-y-6">
      {/* Header con búsqueda automática */}
      <div className="bg-gradient-to-r from-cyan-50 to-blue-50 border border-cyan-200 rounded-lg p-6">
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Sliders size={20} className="text-cyan-600" />
            Optimizador de Orientación Solar
          </h3>
          <div className="flex gap-2">
            <button
              onClick={searchOptimum}
              disabled={isSearching}
              className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors disabled:opacity-50 text-sm font-medium"
            >
              {isSearching ? (
                <><RotateCw size={16} className="animate-spin" /> Buscando...</>
              ) : (
                <><Target size={16} /> Buscar Óptimo</>
              )}
            </button>
            {onSendToSimulator && (
              <button
                onClick={sendToSimulator}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
              >
                <ArrowRight size={16} /> Aplicar al Simulador
              </button>
            )}
          </div>
        </div>

        {/* Restricciones de instalación activas */}
        {(tiltRange || azimuthLocked) && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 text-sm">
            <p className="font-semibold text-amber-900 flex items-center gap-1">
              <AlertTriangle size={14} /> Restricciones de Instalación Activas
              {installationType && <span className="font-normal text-amber-700 ml-1">({installationType})</span>}
            </p>
            <div className="flex gap-4 mt-1 text-amber-800">
              {tiltRange && (
                <span>Inclinación: {tiltRange[0]}° – {tiltRange[1]}°</span>
              )}
              {azimuthLocked && (
                <span className="flex items-center gap-1"><Lock size={12} /> Azimut fijo: {azimuth}°</span>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="font-semibold text-gray-900 flex items-center gap-2">
                  <Compass size={18} className="text-blue-600" />
                  Azimut: {getAzimuthLabel(azimuth)}
                  {effectiveAzimuthLocked && <Lock size={14} className="text-amber-500" />}
                </label>
                <span className="text-sm font-mono bg-blue-100 text-blue-700 px-2 py-1 rounded">{azimuth}°</span>
              </div>
              <Slider
                value={[azimuth]}
                onValueChange={(value) => !effectiveAzimuthLocked && setAzimuth(value[0])}
                min={-90}
                max={90}
                step={5}
                className="w-full"
                disabled={effectiveAzimuthLocked}
              />
              <p className="text-xs text-gray-600 mt-2">-90° (Este) → 0° (Sur) → 90° (Oeste)</p>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="font-semibold text-gray-900">Inclinación (Tilt)</label>
                <span className="text-sm font-mono bg-orange-100 text-orange-700 px-2 py-1 rounded">{tilt}°</span>
              </div>
              <Slider
                value={[tilt]}
                onValueChange={(value) => setTilt(value[0])}
                min={effectiveTiltRange[0]}
                max={effectiveTiltRange[1]}
                step={1}
                className="w-full"
              />
              <p className="text-xs text-gray-600 mt-2">
                Rango: {effectiveTiltRange[0]}° – {effectiveTiltRange[1]}° | Recomendado: {defaultTilt}° (latitud local)
              </p>
            </div>
          </div>

          <div className="bg-white rounded-lg p-4 border border-cyan-100 space-y-3">
            <h4 className="font-semibold text-gray-900">Resumen de Producción</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <p className="text-gray-600">Promedio Mensual</p>
                <p className="text-xl font-mono font-bold text-cyan-700">{stats.avgMonthly}</p>
                <p className="text-xs text-gray-500">W/m²</p>
              </div>
              <div>
                <p className="text-gray-600">Máximo</p>
                <p className="text-xl font-mono font-bold text-green-700">{stats.maxMonth}</p>
                <p className="text-xs text-gray-500">W/m²</p>
              </div>
              <div>
                <p className="text-gray-600">Mínimo</p>
                <p className="text-xl font-mono font-bold text-orange-700">{stats.minMonth}</p>
                <p className="text-xs text-gray-500">W/m²</p>
              </div>
              <div>
                <p className="text-gray-600">Variación</p>
                <p className="text-xl font-mono font-bold text-purple-700">{stats.variance}%</p>
                <p className="text-xs text-gray-500">Estacional</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Resultado de la búsqueda del óptimo */}
      {optimumFound && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg p-5 shadow-sm">
          <h4 className="font-bold text-green-900 flex items-center gap-2 mb-3">
            <Target size={18} className="text-green-600" />
            Orientación Óptima Encontrada
            {(tiltRange || azimuthLocked) && (
              <span className="text-xs font-normal bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
                Con restricciones de {installationType || 'instalación'}
              </span>
            )}
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg p-3 border border-green-200">
              <p className="text-xs text-gray-600">Tilt Óptimo</p>
              <p className="text-2xl font-mono font-bold text-green-700">{optimumFound.tilt}°</p>
              <p className="text-xs text-gray-500">vs actual: {tilt}°</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-green-200">
              <p className="text-xs text-gray-600">Azimut Óptimo</p>
              <p className="text-2xl font-mono font-bold text-green-700">{optimumFound.azimuth}°</p>
              <p className="text-xs text-gray-500">vs actual: {azimuth}°</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-green-200">
              <p className="text-xs text-gray-600">POA Óptimo</p>
              <p className="text-2xl font-mono font-bold text-green-700">{Math.round(optimumFound.poa)}</p>
              <p className="text-xs text-gray-500">W/m² promedio</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-green-200">
              <p className="text-xs text-gray-600">Ganancia vs Actual</p>
              <p className={`text-2xl font-mono font-bold ${gainPercent > 0 ? 'text-green-700' : gainPercent < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                {gainPercent > 0 ? '+' : ''}{gainPercent}%
              </p>
              <p className="text-xs text-gray-500">{Math.round(optimumFound.poa - currentPOAAvg)} W/m²</p>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={applyOptimum}
              className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm font-medium"
            >
              <RotateCw size={14} /> Aplicar Orientación Óptima
            </button>
            {onSendToSimulator && (
              <button
                onClick={() => {
                  applyOptimum();
                  // Pequeño delay para que el estado se actualice antes de enviar
                  setTimeout(() => {
                    const optMonthly = calculateMonthlyForOrientation(weatherData, optimumFound.tilt, optimumFound.azimuth);
                    onSendToSimulator({
                      optimalTilt: optimumFound.tilt,
                      optimalAzimuth: optimumFound.azimuth,
                      currentTilt: tilt,
                      currentAzimuth: azimuth,
                      optimalPOA: optimumFound.poa,
                      currentPOA: currentPOAAvg,
                      gainPercent,
                      monthlyPOA: optMonthly,
                    });
                  }, 100);
                }}
                className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                <ArrowRight size={14} /> Aplicar Óptimo al Simulador
              </button>
            )}
          </div>
        </div>
      )}

      {/* Gráfico de comparación Actual vs Óptimo */}
      {showComparison && comparisonData && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-green-600" />
            Comparación: Orientación Actual vs Óptima
          </h4>
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="month" stroke="#6B7280" />
              <YAxis stroke="#6B7280" label={{ value: 'Irradiancia (W/m²)', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: '8px' }}
                formatter={(value: number, name: string) => [
                  `${value.toLocaleString()} W/m²`,
                  name === 'actual' ? `Actual (${tilt}°/${azimuth}°)` :
                  name === 'optimo' ? `Óptimo (${optimumFound?.tilt}°/${optimumFound?.azimuth}°)` :
                  'Ganancia'
                ]}
              />
              <Legend formatter={(value) =>
                value === 'actual' ? `Actual (${tilt}°/${azimuth}°)` :
                value === 'optimo' ? `Óptimo (${optimumFound?.tilt}°/${optimumFound?.azimuth}°)` :
                'Ganancia'
              } />
              <Bar dataKey="ganancia" fill="#86EFAC" name="ganancia" opacity={0.5} />
              <Line type="monotone" dataKey="actual" stroke="#F97316" strokeWidth={2} name="actual" dot={{ r: 4 }} />
              <Line type="monotone" dataKey="optimo" stroke="#10B981" strokeWidth={2} name="optimo" dot={{ r: 4 }} strokeDasharray="5 5" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Gráfico de producción mensual */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-semibold text-gray-900 mb-4">Producción Mensual (Irradiancia en Plano Inclinado)</h4>
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={monthlyData}>
            <defs>
              <linearGradient id="colorProduction" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#06B6D4" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="month" stroke="#6B7280" />
            <YAxis stroke="#6B7280" label={{ value: 'Irradiancia (W/m²)', angle: -90, position: 'insideLeft' }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: '8px' }}
              formatter={(value: number) => [`${value.toLocaleString()} W/m²`]}
            />
            <Area
              type="monotone"
              dataKey="totalPOA"
              stroke="#0891B2"
              fillOpacity={1}
              fill="url(#colorProduction)"
              name="Irradiancia Inclinada"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h4 className="font-semibold text-gray-900 mb-3">Componentes de Radiación</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="month" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip contentStyle={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: '8px' }} />
              <Legend />
              <Line type="monotone" dataKey="directPOA" stroke="#F97316" name="Directa" strokeWidth={2} />
              <Line type="monotone" dataKey="diffusePOA" stroke="#3B82F6" name="Difusa" strokeWidth={2} />
              <Line type="monotone" dataKey="reflectedPOA" stroke="#8B5CF6" name="Reflejada" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <div className="space-y-4">
          <Card className="p-6">
            <h4 className="font-semibold text-gray-900 mb-3">Recomendaciones</h4>
            <div className="space-y-3 text-sm">
              <div className="bg-green-50 border border-green-200 rounded p-3">
                <p className="font-semibold text-green-900">Orientación Actual</p>
                <p className="text-green-800 mt-1">Azimut: {azimuth}° | Inclinación: {tilt}°</p>
                <p className="text-green-700 text-xs mt-1">POA promedio: {stats.avgMonthly} W/m²</p>
              </div>

              {optimumFound && (
                <div className="bg-emerald-50 border border-emerald-300 rounded p-3">
                  <p className="font-semibold text-emerald-900 flex items-center gap-1">
                    <Target size={14} /> Orientación Óptima
                  </p>
                  <p className="text-emerald-800 mt-1">Azimut: {optimumFound.azimuth}° | Inclinación: {optimumFound.tilt}°</p>
                  <p className="text-emerald-700 text-xs mt-1">
                    POA promedio: {Math.round(optimumFound.poa)} W/m² ({gainPercent > 0 ? '+' : ''}{gainPercent}%)
                  </p>
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 rounded p-3">
                <p className="font-semibold text-blue-900">Referencia Latitud</p>
                <p className="text-blue-800 mt-1">Azimut: 0° (Sur) | Inclinación: {defaultTilt}°</p>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded p-3">
                <p className="font-semibold text-purple-900">Tracking Dinámico</p>
                <p className="text-purple-800 mt-1">Variación estacional: {stats.variance}% - {stats.variance > 25 ? 'Considera tracking' : 'Orientación fija es adecuada'}</p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Tabla de datos mensuales detallados */}
      <Card className="p-6">
        <h4 className="font-semibold text-gray-900 mb-3">Datos Mensuales Detallados</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-3 font-semibold text-gray-700">Mes</th>
                <th className="text-right py-2 px-3 font-semibold text-gray-700">POA Total</th>
                <th className="text-right py-2 px-3 font-semibold text-gray-700">Directa</th>
                <th className="text-right py-2 px-3 font-semibold text-gray-700">Difusa</th>
                <th className="text-right py-2 px-3 font-semibold text-gray-700">Reflejada</th>
                <th className="text-right py-2 px-3 font-semibold text-gray-700">T. Amb.</th>
                <th className="text-right py-2 px-3 font-semibold text-gray-700">Viento</th>
              </tr>
            </thead>
            <tbody>
              {monthlyData.map((d, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 px-3 font-medium">{d.month}</td>
                  <td className="py-2 px-3 text-right font-mono font-bold text-cyan-700">{d.totalPOA}</td>
                  <td className="py-2 px-3 text-right font-mono text-orange-600">{d.directPOA}</td>
                  <td className="py-2 px-3 text-right font-mono text-blue-600">{d.diffusePOA}</td>
                  <td className="py-2 px-3 text-right font-mono text-purple-600">{d.reflectedPOA}</td>
                  <td className="py-2 px-3 text-right font-mono text-red-600">{d.avgTemp}°C</td>
                  <td className="py-2 px-3 text-right font-mono text-gray-600">{d.avgWindSpeed} m/s</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-gray-300 font-bold">
                <td className="py-2 px-3">Promedio</td>
                <td className="py-2 px-3 text-right font-mono text-cyan-700">{stats.avgMonthly}</td>
                <td className="py-2 px-3 text-right font-mono text-orange-600">
                  {Math.round(monthlyData.reduce((s, d) => s + d.directPOA, 0) / 12)}
                </td>
                <td className="py-2 px-3 text-right font-mono text-blue-600">
                  {Math.round(monthlyData.reduce((s, d) => s + d.diffusePOA, 0) / 12)}
                </td>
                <td className="py-2 px-3 text-right font-mono text-purple-600">
                  {Math.round(monthlyData.reduce((s, d) => s + d.reflectedPOA, 0) / 12)}
                </td>
                <td className="py-2 px-3 text-right font-mono text-red-600">
                  {(monthlyData.reduce((s, d) => s + d.avgTemp, 0) / 12).toFixed(1)}°C
                </td>
                <td className="py-2 px-3 text-right font-mono text-gray-600">
                  {(monthlyData.reduce((s, d) => s + d.avgWindSpeed, 0) / 12).toFixed(1)} m/s
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </Card>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-900">
        <p><strong>Nota:</strong> La búsqueda del óptimo realiza un barrido completo de inclinación ({effectiveTiltRange[0]}°–{effectiveTiltRange[1]}°) × azimut ({effectiveAzimuthLocked ? 'fijo' : '-90° a 90°'}) usando datos horarios reales del EPW. Los resultados incluyen temperatura y viento mensual para alimentar directamente el Simulador de Energía.</p>
      </div>
    </div>
  );
}
