import { useMemo, useState } from 'react';
import { DetectedFacade, Vertex3D } from '@/lib/buildingModelImporter';
import { EPWData } from '@/lib/epwParser';
import { calculateMonthlyShadingFactorsForFacade, FacadeFullAnalysis } from '@/lib/facadeShadingAnalysis';
import { calculateAnnualProduction, PanelSpecifications, SystemLosses } from '@/lib/energyProduction';
import { calculateHourlyPOA } from '@/lib/liuJordanModel';
import { Table, TableBody, TableCell, TableFooter, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Building2, TrendingUp, Zap, Sun, ArrowUpDown, ChevronDown, ChevronUp } from 'lucide-react';

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

interface FacadeProductionResult {
  facadeIdx: number;
  facade: DetectedFacade;
  analysis: FacadeFullAnalysis;
  poaAnnual: number; // kWh/m²/año
  productionDC: number; // kWh/año
  productionAC: number; // kWh/año
  specificYield: number; // kWh/kWp/año
  performanceRatio: number; // %
  kwhPerM2Year: number; // kWh/m²/año producción
  capacityFactor: number; // %
  rank: number;
}

interface MultiFacadeComparisonProps {
  modelFacades: DetectedFacade[];
  modelObstacles3D?: Vertex3D[][];
  modelNorthOffset: number;
  weatherData: EPWData;
  panelSpecs: PanelSpecifications;
  systemLosses: SystemLosses;
  onFacadeSelect?: (idx: number) => void;
  activeFacadeIdx?: number | null;
}

export default function MultiFacadeComparison({
  modelFacades,
  modelObstacles3D,
  modelNorthOffset,
  weatherData,
  panelSpecs,
  systemLosses,
  onFacadeSelect,
  activeFacadeIdx,
}: MultiFacadeComparisonProps) {
  const [sortBy, setSortBy] = useState<'rank' | 'area' | 'poa' | 'production' | 'specific'>('rank');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [expanded, setExpanded] = useState(true);

  // Calcular producción para cada fachada
  const facadeResults = useMemo(() => {
    if (!modelFacades || modelFacades.length === 0 || !weatherData) return [];

    const lat = weatherData.location.latitude;
    const lon = weatherData.location.longitude;
    const stdMeridian = weatherData.location.timezone * 15;

    const results: FacadeProductionResult[] = modelFacades.map((facade, idx) => {
      // 1. Calcular FS mensuales para esta fachada
      const analysis = calculateMonthlyShadingFactorsForFacade(
        facade,
        weatherData,
        modelObstacles3D || [],
        modelNorthOffset
      );

      // 2. Calcular POA mensual con la inclinación y azimut de esta fachada
      const tiltRad = (facade.tilt * Math.PI) / 180;
      const azimuthRad = (facade.azimuthNormal * Math.PI) / 180;

      const monthlyPOA = MONTHS.map((month, monthIdx) => {
        const monthData = weatherData.weatherData.filter(w => w.month === monthIdx + 1);
        if (monthData.length === 0) {
          return { month, avgPOA: 0, avgTemp: 0, avgWindSpeed: 1 };
        }

        let sumTotal = 0, sumTemp = 0, sumWind = 0, validCount = 0;

        for (const w of monthData) {
          if (w.globalHorizontalIrradiance > 0 || w.directNormalIrradiance > 0) {
            const dayOfYear = Math.floor((monthIdx * 30.44) + (w.day || 15));
            const hourlyPOA = calculateHourlyPOA(
              lat, lon, stdMeridian,
              dayOfYear,
              w.hour - 1,
              w.minute || 0,
              w.directNormalIrradiance,
              w.diffuseHorizontalIrradiance,
              w.globalHorizontalIrradiance,
              tiltRad,
              azimuthRad,
              0.2,
              false
            );
            sumTotal += hourlyPOA.totalPOA;
            validCount++;
          }
          sumTemp += w.temperature;
          sumWind += w.windSpeed;
        }

        // Dividir por TODAS las horas del mes para consistencia con calculateAnnualProduction
        const n = monthData.length || 1;
        return {
          month,
          avgPOA: Math.round(sumTotal / n),
          avgTemp: Math.round((sumTemp / monthData.length) * 10) / 10,
          avgWindSpeed: Math.round((sumWind / monthData.length) * 10) / 10,
        };
      });

      // 3. Calcular producción anual con FS
      const production = calculateAnnualProduction(
        monthlyPOA,
        panelSpecs,
        systemLosses,
        analysis.monthlyShadingFactors
      );

      // POA anual (kWh/m²/año)
      const daysInMonths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
      const poaAnnual = monthlyPOA.reduce((sum, m, i) => sum + (m.avgPOA * daysInMonths[i] * 24) / 1000, 0);

      // kWh/m² de superficie de fachada por año
      const installedKwp = (panelSpecs.powerRating * panelSpecs.quantity) / 1000;
      const kwhPerM2Year = facade.area > 0 ? production.totalACEnergy / facade.area : 0;

      return {
        facadeIdx: idx,
        facade,
        analysis,
        poaAnnual,
        productionDC: production.totalDCEnergy,
        productionAC: production.totalACEnergy,
        specificYield: production.specificYield,
        performanceRatio: production.performanceRatio,
        kwhPerM2Year,
        capacityFactor: production.capacityFactor,
        rank: 0,
      };
    });

    // Asignar ranking por producción AC
    const sorted = [...results].sort((a, b) => b.productionAC - a.productionAC);
    sorted.forEach((r, i) => { r.rank = i + 1; });

    return results;
  }, [modelFacades, modelObstacles3D, modelNorthOffset, weatherData, panelSpecs, systemLosses]);

  // Ordenar resultados
  const sortedResults = useMemo(() => {
    const copy = [...facadeResults];
    copy.sort((a, b) => {
      let valA = 0, valB = 0;
      switch (sortBy) {
        case 'rank': valA = a.rank; valB = b.rank; break;
        case 'area': valA = a.facade.area; valB = b.facade.area; break;
        case 'poa': valA = a.poaAnnual; valB = b.poaAnnual; break;
        case 'production': valA = a.productionAC; valB = b.productionAC; break;
        case 'specific': valA = a.specificYield; valB = b.specificYield; break;
      }
      return sortDir === 'asc' ? valA - valB : valB - valA;
    });
    return copy;
  }, [facadeResults, sortBy, sortDir]);

  // Totales del edificio
  const totals = useMemo(() => {
    if (facadeResults.length === 0) return null;
    const totalArea = facadeResults.reduce((s, r) => s + r.facade.area, 0);
    const totalAC = facadeResults.reduce((s, r) => s + r.productionAC, 0);
    const totalDC = facadeResults.reduce((s, r) => s + r.productionDC, 0);
    const avgPR = facadeResults.reduce((s, r) => s + r.performanceRatio * r.productionAC, 0) / (totalAC || 1);
    const avgFS = facadeResults.reduce((s, r) => s + r.analysis.annualFS * r.facade.area, 0) / (totalArea || 1);
    const bestFacade = facadeResults.reduce((best, r) => r.productionAC > best.productionAC ? r : best, facadeResults[0]);
    return { totalArea, totalAC, totalDC, avgPR, avgFS, bestFacade };
  }, [facadeResults]);

  const handleSort = (col: typeof sortBy) => {
    if (sortBy === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortDir(col === 'rank' ? 'asc' : 'desc');
    }
  };

  const SortIcon = ({ col }: { col: typeof sortBy }) => {
    if (sortBy !== col) return <ArrowUpDown className="w-3 h-3 opacity-40" />;
    return sortDir === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />;
  };

  if (!modelFacades || modelFacades.length === 0) return null;

  const maxProduction = Math.max(...facadeResults.map(r => r.productionAC), 1);

  // Colores por fachada (consistentes con el selector)
  const FACADE_COLORS = ['#ef4444', '#3b82f6', '#22c55e', '#eab308', '#a855f7', '#f97316', '#06b6d4', '#ec4899'];

  return (
    <div className="border-2 border-emerald-300 rounded-xl overflow-hidden bg-gradient-to-br from-emerald-50 to-teal-50">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-5 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-700 hover:to-teal-700 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Building2 className="w-5 h-5" />
          <span className="font-bold text-sm">Comparativa Multi-Fachada — Producción Estimada ({modelFacades.length} superficies)</span>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {expanded && (
        <div className="p-4 space-y-4">
          {/* Resumen del edificio */}
          {totals && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="bg-white rounded-lg p-3 border border-emerald-200 text-center">
                <div className="text-xs text-gray-500 mb-1">Producción Total</div>
                <div className="text-lg font-bold text-emerald-700">{totals.totalAC.toFixed(0)} <span className="text-xs font-normal">kWh/año</span></div>
              </div>
              <div className="bg-white rounded-lg p-3 border border-emerald-200 text-center">
                <div className="text-xs text-gray-500 mb-1">Área Total</div>
                <div className="text-lg font-bold text-teal-700">{totals.totalArea.toFixed(1)} <span className="text-xs font-normal">m²</span></div>
              </div>
              <div className="bg-white rounded-lg p-3 border border-emerald-200 text-center">
                <div className="text-xs text-gray-500 mb-1">FS Promedio</div>
                <div className="text-lg font-bold text-blue-700">{(totals.avgFS * 100).toFixed(1)}<span className="text-xs font-normal">%</span></div>
              </div>
              <div className="bg-white rounded-lg p-3 border border-emerald-200 text-center">
                <div className="text-xs text-gray-500 mb-1">PR Promedio</div>
                <div className="text-lg font-bold text-purple-700">{totals.avgPR.toFixed(1)}<span className="text-xs font-normal">%</span></div>
              </div>
              <div className="bg-white rounded-lg p-3 border border-emerald-200 text-center">
                <div className="text-xs text-gray-500 mb-1">Mejor Superficie</div>
                <div className="text-sm font-bold text-amber-700 truncate">{totals.bestFacade.facade.name}</div>
              </div>
            </div>
          )}

          {/* Tabla comparativa */}
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-emerald-100/50">
                  <TableHead className="w-8 cursor-pointer" onClick={() => handleSort('rank')}>
                    <div className="flex items-center gap-1"># <SortIcon col="rank" /></div>
                  </TableHead>
                  <TableHead>Superficie</TableHead>
                  <TableHead className="text-center">Az / Incl</TableHead>
                  <TableHead className="text-center cursor-pointer" onClick={() => handleSort('area')}>
                    <div className="flex items-center justify-center gap-1">Área <SortIcon col="area" /></div>
                  </TableHead>
                  <TableHead className="text-center">FS Anual</TableHead>
                  <TableHead className="text-center cursor-pointer" onClick={() => handleSort('poa')}>
                    <div className="flex items-center justify-center gap-1">POA <SortIcon col="poa" /></div>
                  </TableHead>
                  <TableHead className="text-center cursor-pointer" onClick={() => handleSort('production')}>
                    <div className="flex items-center justify-center gap-1">Prod. AC <SortIcon col="production" /></div>
                  </TableHead>
                  <TableHead className="text-center cursor-pointer" onClick={() => handleSort('specific')}>
                    <div className="flex items-center justify-center gap-1">Yield <SortIcon col="specific" /></div>
                  </TableHead>
                  <TableHead className="text-center">PR</TableHead>
                  <TableHead className="w-32">Comparativa</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedResults.map((result) => {
                  const isActive = activeFacadeIdx === result.facadeIdx;
                  const barWidth = (result.productionAC / maxProduction) * 100;
                  const color = FACADE_COLORS[result.facadeIdx % FACADE_COLORS.length];

                  return (
                    <TableRow
                      key={result.facadeIdx}
                      className={`cursor-pointer transition-colors ${isActive ? 'bg-emerald-100 ring-2 ring-emerald-400 ring-inset' : 'hover:bg-emerald-50'}`}
                      onClick={() => onFacadeSelect?.(result.facadeIdx)}
                    >
                      <TableCell className="font-bold text-center">
                        {result.rank === 1 ? '🥇' : result.rank === 2 ? '🥈' : result.rank === 3 ? '🥉' : result.rank}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                          <span className="font-medium text-sm truncate max-w-[140px]">{result.facade.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center text-xs">
                        <span className="text-gray-600">{result.facade.azimuthNormal.toFixed(0)}° / {result.facade.tilt.toFixed(0)}°</span>
                      </TableCell>
                      <TableCell className="text-center text-sm">{result.facade.area.toFixed(1)} m²</TableCell>
                      <TableCell className="text-center">
                        <span className={`text-sm font-medium ${result.analysis.annualFS >= 0.9 ? 'text-green-600' : result.analysis.annualFS >= 0.7 ? 'text-amber-600' : 'text-red-600'}`}>
                          {(result.analysis.annualFS * 100).toFixed(1)}%
                        </span>
                      </TableCell>
                      <TableCell className="text-center text-sm">{result.poaAnnual.toFixed(0)} <span className="text-xs text-gray-400">kWh/m²</span></TableCell>
                      <TableCell className="text-center">
                        <span className="font-bold text-sm text-emerald-700">{result.productionAC.toFixed(0)}</span>
                        <span className="text-xs text-gray-400 ml-1">kWh</span>
                      </TableCell>
                      <TableCell className="text-center text-sm">{result.specificYield.toFixed(0)} <span className="text-xs text-gray-400">kWh/kWp</span></TableCell>
                      <TableCell className="text-center text-sm">{result.performanceRatio.toFixed(1)}%</TableCell>
                      <TableCell>
                        <div className="w-full bg-gray-200 rounded-full h-3 relative overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{ width: `${barWidth}%`, backgroundColor: color }}
                          />
                          <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-gray-700">
                            {barWidth.toFixed(0)}%
                          </span>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
              {totals && (
                <TableFooter>
                  <TableRow className="bg-emerald-100/80 font-bold">
                    <TableCell colSpan={3} className="text-right text-sm">TOTAL EDIFICIO</TableCell>
                    <TableCell className="text-center text-sm">{totals.totalArea.toFixed(1)} m²</TableCell>
                    <TableCell className="text-center text-sm">{(totals.avgFS * 100).toFixed(1)}%</TableCell>
                    <TableCell className="text-center text-sm">—</TableCell>
                    <TableCell className="text-center text-sm text-emerald-800">{totals.totalAC.toFixed(0)} kWh</TableCell>
                    <TableCell className="text-center text-sm">—</TableCell>
                    <TableCell className="text-center text-sm">{totals.avgPR.toFixed(1)}%</TableCell>
                    <TableCell className="text-center text-sm">100%</TableCell>
                  </TableRow>
                </TableFooter>
              )}
            </Table>
          </div>

          {/* Nota informativa */}
          <p className="text-xs text-gray-500 italic px-2">
            * La producción se calcula con el panel y pérdidas configurados actualmente ({panelSpecs.quantity} paneles de {panelSpecs.powerRating}W = {((panelSpecs.powerRating * panelSpecs.quantity) / 1000).toFixed(2)} kWp).
            El POA se calcula individualmente para cada superficie usando su azimut e inclinación específicos con el modelo Liu-Jordan isotrópico.
            Haz clic en una fila para seleccionar esa superficie como activa en el Simulador.
          </p>
        </div>
      )}
    </div>
  );
}
