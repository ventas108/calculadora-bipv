import { useMemo } from 'react';
import { DetectedFacade, Vertex3D, recalculateForFacade } from '@/lib/buildingModelImporter';
import { EPWData, getWeatherForDateTime } from '@/lib/epwParser';
import { calculateSolarPosition } from '@/lib/solarPosition';
import { ObstaclePolygon } from './SunPathDiagram';
import { Sun, Zap, Clock, Trophy, TrendingUp } from 'lucide-react';

interface FacadeComparisonTableProps {
  facades: DetectedFacade[];
  weatherData: EPWData;
  obstacleVertices3D?: Vertex3D[][];
  northOffset: number;
  activeFacadeIdx: number | null;
  onFacadeSelect: (idx: number) => void;
}

interface FacadeMetrics {
  facade: DetectedFacade;
  idx: number;
  fsAverage: number;
  effectiveSunHours: number;
  totalSunHours: number;
  estimatedPOA: number; // kWh/m²/año
  estimatedProduction: number; // kWh/año (POA × área × 0.18 eficiencia típica)
  shadingLoss: number; // % de pérdida por sombreado
}

/**
 * Calcula la radiación POA (Plane of Array) para una superficie inclinada
 * usando el modelo isotrópico simplificado de Liu-Jordan
 */
function calculatePOAForSurface(
  weatherData: EPWData,
  azimuthNormal: number,
  tilt: number,
  obstacles: ObstaclePolygon[]
): { poaAnnual: number; sunHoursTotal: number; sunHoursEffective: number } {
  const { latitude, longitude, timezone } = weatherData.location;
  const albedo = 0.2; // Reflectancia típica del suelo

  let poaAnnual = 0;
  let sunHoursTotal = 0;
  let sunHoursEffective = 0;

  // Iterar por cada hora del año representativa (día 15 de cada mes)
  for (let month = 1; month <= 12; month++) {
    const day = 15; // Día representativo del mes
    const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];

    for (let hour = 5; hour <= 20; hour++) {
      const solarPos = calculateSolarPosition(latitude, longitude, timezone, month, day, hour);
      if (solarPos.altitude <= 0) continue;

      const weather = getWeatherForDateTime(weatherData, month, day, hour);
      if (!weather) continue;

      const GHI = weather.globalHorizontalIrradiance;
      const DNI = weather.directNormalIrradiance;
      const DHI = weather.diffuseHorizontalIrradiance;

      if (GHI <= 0) continue;

      sunHoursTotal += daysInMonth;

      // Ángulo de incidencia sobre la superficie
      const tiltRad = tilt * Math.PI / 180;
      const altRad = solarPos.altitude * Math.PI / 180;
      const zenithRad = (90 - solarPos.altitude) * Math.PI / 180;

      // Azimut solar (convención: 0=Sur, neg=Este, pos=Oeste)
      const solarAzRad = solarPos.azimuth * Math.PI / 180;
      // Azimut de la superficie (normal exterior)
      const surfAzRad = azimuthNormal * Math.PI / 180;

      // Ángulo de incidencia (cos θi)
      const cosIncidence = Math.sin(altRad) * Math.cos(tiltRad) +
        Math.cos(altRad) * Math.sin(tiltRad) * Math.cos(solarAzRad - surfAzRad);

      // Componente directa sobre la superficie
      const directPOA = Math.max(0, DNI * cosIncidence);

      // Componente difusa (modelo isotrópico)
      const diffusePOA = DHI * (1 + Math.cos(tiltRad)) / 2;

      // Componente reflejada
      const reflectedPOA = GHI * albedo * (1 - Math.cos(tiltRad)) / 2;

      // POA total para esta hora
      const poaHour = directPOA + diffusePOA + reflectedPOA;

      // Verificar si hay sombreado en esta hora
      let shadingFactor = 1.0;
      if (obstacles.length > 0) {
        // Verificar si el punto solar está dentro de algún obstáculo
        const isShaded = checkPointInObstacles(solarPos.azimuth, solarPos.altitude, obstacles);
        shadingFactor = isShaded ? 0.15 : 1.0; // 85% de pérdida si está sombreado (queda difusa)
      }

      if (shadingFactor >= 1.0) {
        sunHoursEffective += daysInMonth;
      }

      // Acumular POA anual (Wh/m² → kWh/m²)
      poaAnnual += (poaHour * shadingFactor * daysInMonth) / 1000;
    }
  }

  return {
    poaAnnual,
    sunHoursTotal: sunHoursTotal / 365, // Horas de sol promedio diarias
    sunHoursEffective: sunHoursEffective / 365,
  };
}

/**
 * Verifica si un punto solar (azimut, altitud) está dentro de algún polígono de obstáculo
 */
function checkPointInObstacles(azimuth: number, altitude: number, obstacles: ObstaclePolygon[]): boolean {
  for (const obs of obstacles) {
    if (!obs.visible || obs.vertices.length < 3) continue;

    // Convertir a coordenadas SVG para el test de punto en polígono
    const compassAz = (azimuth + 180) % 360;
    const r = 250 * (90 - altitude) / 90;
    const angleRad = (compassAz - 90) * Math.PI / 180;
    const px = 300 + r * Math.cos(angleRad);
    const py = 300 + r * Math.sin(angleRad);

    const svgPoly = obs.vertices.map(v => {
      const cAz = (v.azimuth + 180) % 360;
      const rV = 250 * (90 - v.altitude) / 90;
      const aRad = (cAz - 90) * Math.PI / 180;
      return { x: 300 + rV * Math.cos(aRad), y: 300 + rV * Math.sin(aRad) };
    });

    // Ray casting algorithm
    let inside = false;
    for (let i = 0, j = svgPoly.length - 1; i < svgPoly.length; j = i++) {
      const xi = svgPoly[i].x, yi = svgPoly[i].y;
      const xj = svgPoly[j].x, yj = svgPoly[j].y;
      if (((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) {
        inside = !inside;
      }
    }
    if (inside) return true;
  }
  return false;
}

export default function FacadeComparisonTable({
  facades,
  weatherData,
  obstacleVertices3D,
  northOffset,
  activeFacadeIdx,
  onFacadeSelect,
}: FacadeComparisonTableProps) {
  const metrics = useMemo<FacadeMetrics[]>(() => {
    return facades.map((facade, idx) => {
      // Calcular obstáculos desde la perspectiva de esta fachada
      let facadeObstacles: ObstaclePolygon[] = [];
      if (obstacleVertices3D && obstacleVertices3D.length > 0) {
        facadeObstacles = recalculateForFacade(facade, obstacleVertices3D, northOffset);
      }

      // Calcular POA y horas de sol
      const { poaAnnual, sunHoursTotal, sunHoursEffective } = calculatePOAForSurface(
        weatherData,
        facade.azimuthNormal,
        facade.tilt,
        facadeObstacles
      );

      // Calcular POA sin obstáculos para determinar pérdida por sombreado
      const { poaAnnual: poaNoShading } = calculatePOAForSurface(
        weatherData,
        facade.azimuthNormal,
        facade.tilt,
        []
      );

      const shadingLoss = poaNoShading > 0
        ? ((poaNoShading - poaAnnual) / poaNoShading) * 100
        : 0;

      // FS promedio = 1 - (pérdida por sombreado / 100)
      const fsAverage = 1 - shadingLoss / 100;

      // Producción estimada: POA × área × eficiencia típica (18%) × PR (0.80)
      const efficiency = 0.18;
      const performanceRatio = 0.80;
      const estimatedProduction = poaAnnual * facade.area * efficiency * performanceRatio;

      return {
        facade,
        idx,
        fsAverage,
        effectiveSunHours: sunHoursEffective,
        totalSunHours: sunHoursTotal,
        estimatedPOA: poaAnnual,
        estimatedProduction,
        shadingLoss,
      };
    });
  }, [facades, weatherData, obstacleVertices3D, northOffset]);

  // Encontrar la mejor fachada (mayor producción)
  const bestIdx = useMemo(() => {
    if (metrics.length === 0) return -1;
    return metrics.reduce((best, m, i) => m.estimatedProduction > metrics[best].estimatedProduction ? i : best, 0);
  }, [metrics]);

  if (metrics.length === 0) return null;

  // Totales
  const totalArea = metrics.reduce((s, m) => s + m.facade.area, 0);
  const totalProduction = metrics.reduce((s, m) => s + m.estimatedProduction, 0);
  const avgFS = metrics.reduce((s, m) => s + m.fsAverage * m.facade.area, 0) / totalArea;

  return (
    <div className="bg-white border-2 border-indigo-200 rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-3">
        <div className="flex items-center gap-2 text-white">
          <TrendingUp size={18} />
          <h3 className="font-semibold text-sm">Comparativa de Superficies BIPV</h3>
        </div>
        <p className="text-indigo-100 text-[11px] mt-0.5">
          Análisis de potencial fotovoltaico por fachada/techo del edificio importado
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-indigo-50 border-b border-indigo-200">
              <th className="px-3 py-2 text-left font-semibold text-indigo-900">Superficie</th>
              <th className="px-2 py-2 text-center font-semibold text-indigo-900">Az.</th>
              <th className="px-2 py-2 text-center font-semibold text-indigo-900">Incl.</th>
              <th className="px-2 py-2 text-center font-semibold text-indigo-900">Área</th>
              <th className="px-2 py-2 text-center font-semibold text-indigo-900">
                <div className="flex items-center justify-center gap-1">
                  <Sun size={12} />
                  FS Prom.
                </div>
              </th>
              <th className="px-2 py-2 text-center font-semibold text-indigo-900">
                <div className="flex items-center justify-center gap-1">
                  <Clock size={12} />
                  Horas Sol
                </div>
              </th>
              <th className="px-2 py-2 text-center font-semibold text-indigo-900">
                POA
              </th>
              <th className="px-2 py-2 text-center font-semibold text-indigo-900">
                <div className="flex items-center justify-center gap-1">
                  <Zap size={12} />
                  Producción
                </div>
              </th>
              <th className="px-2 py-2 text-center font-semibold text-indigo-900">
                Pérdida Sombra
              </th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m) => (
              <tr
                key={m.idx}
                onClick={() => onFacadeSelect(m.idx)}
                className={`border-b border-gray-100 cursor-pointer transition-all ${
                  activeFacadeIdx === m.idx
                    ? 'bg-indigo-50 ring-1 ring-inset ring-indigo-300'
                    : 'hover:bg-gray-50'
                } ${m.idx === bestIdx ? 'relative' : ''}`}
              >
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0 border border-gray-300"
                      style={{ backgroundColor: m.facade.color }}
                    />
                    <span className="font-medium text-gray-800">{m.facade.name}</span>
                    {m.idx === bestIdx && (
                      <Trophy size={12} className="text-amber-500 flex-shrink-0" />
                    )}
                  </div>
                </td>
                <td className="px-2 py-2.5 text-center text-gray-600">
                  {m.facade.azimuthNormal.toFixed(0)}°
                </td>
                <td className="px-2 py-2.5 text-center text-gray-600">
                  {m.facade.tilt.toFixed(0)}°
                </td>
                <td className="px-2 py-2.5 text-center text-gray-600">
                  {m.facade.area.toFixed(1)} m²
                </td>
                <td className="px-2 py-2.5 text-center">
                  <span className={`font-semibold ${
                    m.fsAverage >= 0.95 ? 'text-green-700' :
                    m.fsAverage >= 0.85 ? 'text-yellow-700' :
                    m.fsAverage >= 0.70 ? 'text-orange-700' :
                    'text-red-700'
                  }`}>
                    {m.fsAverage.toFixed(3)}
                  </span>
                </td>
                <td className="px-2 py-2.5 text-center">
                  <span className="text-gray-700">
                    {m.effectiveSunHours.toFixed(1)}/{m.totalSunHours.toFixed(1)} h
                  </span>
                </td>
                <td className="px-2 py-2.5 text-center">
                  <span className="font-medium text-gray-700">
                    {m.estimatedPOA.toFixed(0)}
                  </span>
                  <span className="text-[10px] text-gray-500 block">kWh/m²/año</span>
                </td>
                <td className="px-2 py-2.5 text-center">
                  <span className="font-bold text-indigo-700">
                    {m.estimatedProduction.toFixed(0)}
                  </span>
                  <span className="text-[10px] text-gray-500 block">kWh/año</span>
                </td>
                <td className="px-2 py-2.5 text-center">
                  <span className={`font-medium ${
                    m.shadingLoss <= 5 ? 'text-green-700' :
                    m.shadingLoss <= 15 ? 'text-yellow-700' :
                    m.shadingLoss <= 30 ? 'text-orange-700' :
                    'text-red-700'
                  }`}>
                    {m.shadingLoss.toFixed(1)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
          {/* Totals row */}
          <tfoot>
            <tr className="bg-indigo-50 border-t-2 border-indigo-200 font-semibold">
              <td className="px-3 py-2.5 text-indigo-900">
                TOTAL / PROMEDIO
              </td>
              <td className="px-2 py-2.5 text-center text-gray-500">—</td>
              <td className="px-2 py-2.5 text-center text-gray-500">—</td>
              <td className="px-2 py-2.5 text-center text-indigo-800">
                {totalArea.toFixed(1)} m²
              </td>
              <td className="px-2 py-2.5 text-center text-indigo-800">
                {avgFS.toFixed(3)}
              </td>
              <td className="px-2 py-2.5 text-center text-gray-500">—</td>
              <td className="px-2 py-2.5 text-center text-gray-500">—</td>
              <td className="px-2 py-2.5 text-center text-indigo-800">
                {totalProduction.toFixed(0)}
                <span className="text-[10px] text-gray-500 block">kWh/año</span>
              </td>
              <td className="px-2 py-2.5 text-center text-gray-500">—</td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Legend / Notes */}
      <div className="px-4 py-2.5 bg-gray-50 border-t border-gray-200">
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-gray-500">
          <span><strong>FS:</strong> Factor de Sombreado (1.0 = sin sombra)</span>
          <span><strong>Horas Sol:</strong> Efectivas/Totales (promedio diario)</span>
          <span><strong>POA:</strong> Radiación en Plano del Array</span>
          <span><strong>Producción:</strong> POA × Área × η(18%) × PR(0.80)</span>
          <span><Trophy size={10} className="inline text-amber-500" /> Mejor superficie para BIPV</span>
        </div>
        {!obstacleVertices3D || obstacleVertices3D.length === 0 ? (
          <p className="text-[10px] text-amber-600 mt-1 font-medium">
            ⚠️ Sin obstáculos 3D importados — Los valores de FS y pérdida por sombra asumen cielo despejado.
            Importa obstáculos OBJ/Marsh para un cálculo preciso.
          </p>
        ) : null}
      </div>
    </div>
  );
}
