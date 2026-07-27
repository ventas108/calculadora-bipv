/**
 * Componente Optimizador de ROI para Vidrios Fotovoltaicos BIPV
 * 
 * Muestra:
 * - Tabla comparativa de escenarios arquitectónicos
 * - Análisis de sensibilidad (gráficos)
 * - Recomendaciones priorizadas
 * - Parámetros financieros editables
 */

import { useState, useMemo } from 'react';
import {
  generateArchitecturalAlternatives,
  generateSensitivityAnalysis,
  generateRecommendations,
  calculateBIPVSHGC,
  DEFAULT_BIPV_COSTS,
  DEFAULT_ENERGY_PARAMS,
  DEFAULT_INCENTIVES_COLOMBIA,
  DEFAULT_INCENTIVES_NONE,
  DEFAULT_HVAC_PARAMS,
  type BIPVCostAssumptions,
  type EnergyValorizationParams,
  type IncentiveParams,
  type ROIScenarioResult,
  type OptimizationRecommendation,
  type SensitivityPoint,
} from '@/lib/bipvROIOptimizer';
import type { BIPVSimulationSummary } from '@/lib/iamSoilingEngine';

interface BIPVROIOptimizerProps {
  results: BIPVSimulationSummary[];
  area: number;
  tilt: number;
  azimuth: number;
  latitude: number;
}

export default function BIPVROIOptimizer({ results, area, tilt, azimuth, latitude }: BIPVROIOptimizerProps) {
  // Parámetros financieros editables
  const [costs, setCosts] = useState<BIPVCostAssumptions>(DEFAULT_BIPV_COSTS);
  const [energyParams, setEnergyParams] = useState<EnergyValorizationParams>(DEFAULT_ENERGY_PARAMS);
  const [incentives, setIncentives] = useState<IncentiveParams>(DEFAULT_INCENTIVES_COLOMBIA);
  const [useIncentives, setUseIncentives] = useState(true);
  const [coolingMonths, setCoolingMonths] = useState(12);
  const [showParams, setShowParams] = useState(false);
  const [activeView, setActiveView] = useState<'scenarios' | 'sensitivity' | 'recommendations'>('scenarios');

  // Generar escenarios
  const scenarios = useMemo(() => {
    if (!results || results.length === 0) return [];
    return generateArchitecturalAlternatives(
      results, area, tilt, azimuth, latitude,
      costs, energyParams,
      useIncentives ? incentives : DEFAULT_INCENTIVES_NONE,
      coolingMonths
    );
  }, [results, area, tilt, azimuth, latitude, costs, energyParams, incentives, useIncentives, coolingMonths]);

  // Análisis de sensibilidad
  const sensitivity = useMemo(() => {
    if (!results || results.length === 0) return null;
    const best = results.reduce((b, r) => r.energiaAnualKwh > b.energiaAnualKwh ? r : b, results[0]);
    return generateSensitivityAnalysis(best, area, tilt, latitude, costs, energyParams, useIncentives ? incentives : DEFAULT_INCENTIVES_NONE);
  }, [results, area, tilt, latitude, costs, energyParams, incentives, useIncentives]);

  // Recomendaciones
  const recommendations = useMemo(() => {
    if (scenarios.length === 0) return [];
    const best = results.reduce((b, r) => r.energiaAnualKwh > b.energiaAnualKwh ? r : b, results[0]);
    return generateRecommendations(scenarios, tilt, best.transparencia, latitude);
  }, [scenarios, results, tilt, latitude]);

  if (!results || results.length === 0) {
    return (
      <div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-6 text-center">
        <p className="text-amber-800 font-medium">Ejecute una simulación BIPV primero para generar el análisis de optimización ROI.</p>
      </div>
    );
  }

  const bestScenario = scenarios[0];
  const currentScenario = scenarios.find(s => s.name.includes('Actual'));

  return (
    <div className="space-y-4">
      {/* Header con resumen */}
      <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border-2 border-emerald-200 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
            💰 Optimizador ROI — Alternativas Arquitectónicas
          </h3>
          <button
            onClick={() => setShowParams(!showParams)}
            className="text-xs px-3 py-1.5 bg-white border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors"
          >
            {showParams ? '▲ Ocultar Parámetros' : '⚙️ Parámetros Financieros'}
          </button>
        </div>

        {/* KPIs rápidos */}
        {currentScenario && bestScenario && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-white rounded-lg p-3 border border-emerald-100">
              <p className="text-[10px] text-gray-500 uppercase font-semibold">ROI Actual (25a)</p>
              <p className={`text-xl font-bold font-mono ${currentScenario.roi25Years >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>
                {currentScenario.roi25Years.toFixed(0)}%
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-emerald-100">
              <p className="text-[10px] text-gray-500 uppercase font-semibold">Mejor Alternativa</p>
              <p className={`text-xl font-bold font-mono ${bestScenario.roi25Years >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>
                {bestScenario.roi25Years.toFixed(0)}%
              </p>
              <p className="text-[9px] text-gray-500 truncate">{bestScenario.name}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-emerald-100">
              <p className="text-[10px] text-gray-500 uppercase font-semibold">Payback Mejor</p>
              <p className="text-xl font-bold font-mono text-blue-700">
                {bestScenario.paybackYears < 99 ? `${bestScenario.paybackYears.toFixed(1)}a` : 'N/A'}
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-emerald-100">
              <p className="text-[10px] text-gray-500 uppercase font-semibold">Ahorro HVAC/año</p>
              <p className="text-xl font-bold font-mono text-cyan-700">
                ${currentScenario.annualHVACSaving.toFixed(0)}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Panel de parámetros financieros (colapsable) */}
      {showParams && (
        <div className="bg-white border-2 border-gray-200 rounded-xl p-5 shadow-sm">
          <h4 className="text-sm font-bold text-gray-800 mb-4">Parámetros Financieros</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Costos */}
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-700 uppercase">Costos BIPV</p>
              <label className="block text-xs text-gray-600">
                Vidrio BIPV ($/m²): 
                <input type="number" value={costs.glassCostPerM2} onChange={e => setCosts({...costs, glassCostPerM2: +e.target.value})}
                  className="ml-2 w-20 border rounded px-2 py-0.5 text-xs font-mono" />
              </label>
              <label className="block text-xs text-gray-600">
                Instalación ($/m²): 
                <input type="number" value={costs.installationCostPerM2} onChange={e => setCosts({...costs, installationCostPerM2: +e.target.value})}
                  className="ml-2 w-20 border rounded px-2 py-0.5 text-xs font-mono" />
              </label>
              <label className="block text-xs text-gray-600">
                Inversor ($/kWp): 
                <input type="number" value={costs.inverterCostPerKWp} onChange={e => setCosts({...costs, inverterCostPerKWp: +e.target.value})}
                  className="ml-2 w-20 border rounded px-2 py-0.5 text-xs font-mono" />
              </label>
              <label className="block text-xs text-gray-600">
                BOS ($/m²): 
                <input type="number" value={costs.bosCostPerM2} onChange={e => setCosts({...costs, bosCostPerM2: +e.target.value})}
                  className="ml-2 w-20 border rounded px-2 py-0.5 text-xs font-mono" />
              </label>
              <label className="block text-xs text-gray-600">
                Vidrio convencional ($/m²): 
                <input type="number" value={costs.conventionalGlassCostPerM2} onChange={e => setCosts({...costs, conventionalGlassCostPerM2: +e.target.value})}
                  className="ml-2 w-20 border rounded px-2 py-0.5 text-xs font-mono" />
              </label>
            </div>

            {/* Energía */}
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-700 uppercase">Valorización Energética</p>
              <label className="block text-xs text-gray-600">
                Tarifa compra ($/kWh): 
                <input type="number" step="0.01" value={energyParams.electricityBuyRate} onChange={e => setEnergyParams({...energyParams, electricityBuyRate: +e.target.value})}
                  className="ml-2 w-20 border rounded px-2 py-0.5 text-xs font-mono" />
              </label>
              <label className="block text-xs text-gray-600">
                Tarifa venta ($/kWh): 
                <input type="number" step="0.01" value={energyParams.electricitySellRate} onChange={e => setEnergyParams({...energyParams, electricitySellRate: +e.target.value})}
                  className="ml-2 w-20 border rounded px-2 py-0.5 text-xs font-mono" />
              </label>
              <label className="block text-xs text-gray-600">
                Autoconsumo (%): 
                <input type="number" value={energyParams.selfConsumptionPercent} onChange={e => setEnergyParams({...energyParams, selfConsumptionPercent: +e.target.value})}
                  className="ml-2 w-20 border rounded px-2 py-0.5 text-xs font-mono" />
              </label>
              <label className="block text-xs text-gray-600">
                Escalamiento tarifa (%/año): 
                <input type="number" step="0.5" value={energyParams.electricityEscalation} onChange={e => setEnergyParams({...energyParams, electricityEscalation: +e.target.value})}
                  className="ml-2 w-20 border rounded px-2 py-0.5 text-xs font-mono" />
              </label>
              <label className="block text-xs text-gray-600">
                Meses refrigeración: 
                <input type="number" min={0} max={12} value={coolingMonths} onChange={e => setCoolingMonths(+e.target.value)}
                  className="ml-2 w-20 border rounded px-2 py-0.5 text-xs font-mono" />
              </label>
            </div>

            {/* Incentivos */}
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-700 uppercase">Incentivos Tributarios</p>
              <label className="flex items-center gap-2 text-xs text-gray-600">
                <input type="checkbox" checked={useIncentives} onChange={e => setUseIncentives(e.target.checked)}
                  className="rounded border-gray-400 text-emerald-600" />
                Aplicar Ley 1715 Colombia
              </label>
              {useIncentives && (
                <>
                  <label className="block text-xs text-gray-600">
                    Deducción renta (%): 
                    <input type="number" value={incentives.taxDeductionPercent} onChange={e => setIncentives({...incentives, taxDeductionPercent: +e.target.value})}
                      className="ml-2 w-16 border rounded px-2 py-0.5 text-xs font-mono" />
                  </label>
                  <label className="block text-xs text-gray-600">
                    Tasa impositiva (%): 
                    <input type="number" value={incentives.marginalTaxRate} onChange={e => setIncentives({...incentives, marginalTaxRate: +e.target.value})}
                      className="ml-2 w-16 border rounded px-2 py-0.5 text-xs font-mono" />
                  </label>
                  <label className="flex items-center gap-2 text-xs text-gray-600">
                    <input type="checkbox" checked={incentives.vatExemption} onChange={e => setIncentives({...incentives, vatExemption: e.target.checked})}
                      className="rounded border-gray-400 text-emerald-600" />
                    Exclusión IVA ({incentives.vatRate}%)
                  </label>
                  <label className="flex items-center gap-2 text-xs text-gray-600">
                    <input type="checkbox" checked={incentives.importDutyExemption} onChange={e => setIncentives({...incentives, importDutyExemption: e.target.checked})}
                      className="rounded border-gray-400 text-emerald-600" />
                    Exención aranceles ({incentives.importDutyRate}%)
                  </label>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tabs de vista */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        {(['scenarios', 'sensitivity', 'recommendations'] as const).map(view => (
          <button key={view}
            onClick={() => setActiveView(view)}
            className={`flex-1 py-2 px-3 rounded-md text-xs font-semibold transition-all ${
              activeView === view ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-800'
            }`}>
            {view === 'scenarios' ? '🏗️ Escenarios' : view === 'sensitivity' ? '📊 Sensibilidad' : '💡 Recomendaciones'}
          </button>
        ))}
      </div>

      {/* Vista: Escenarios */}
      {activeView === 'scenarios' && scenarios.length > 0 && (
        <div className="space-y-3">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-600 font-semibold border-b-2 border-gray-200">
                  <th className="text-left py-2.5 px-2">#</th>
                  <th className="text-left py-2.5 px-2">Escenario</th>
                  <th className="text-right py-2.5 px-1">kWh/año</th>
                  <th className="text-right py-2.5 px-1">Costo Neto</th>
                  <th className="text-right py-2.5 px-1">Ingreso/año</th>
                  <th className="text-right py-2.5 px-1">HVAC/año</th>
                  <th className="text-right py-2.5 px-1">Payback</th>
                  <th className="text-right py-2.5 px-1">ROI 25a</th>
                  <th className="text-right py-2.5 px-1">VAN</th>
                  <th className="text-right py-2.5 px-1">TIR</th>
                  <th className="text-right py-2.5 px-1">LCOE</th>
                </tr>
              </thead>
              <tbody>
                {scenarios.map((s, i) => (
                  <tr key={i} className={`border-b border-gray-100 ${
                    s.isViable ? 'bg-emerald-50/50' : 'bg-red-50/30'
                  } ${s.name.includes('Actual') ? 'ring-2 ring-indigo-300 ring-inset' : ''}`}>
                    <td className="py-2 px-2 text-gray-500 font-bold">{s.rank}</td>
                    <td className="py-2 px-2">
                      <div className="flex items-center gap-1.5">
                        <span className="text-base">{s.icon}</span>
                        <div>
                          <p className="font-semibold text-gray-800 text-[11px] leading-tight">{s.name}</p>
                          <p className="text-[9px] text-gray-500 leading-tight">{s.tilt}° | τ={( s.transparency * 100).toFixed(0)}%</p>
                        </div>
                      </div>
                    </td>
                    <td className="text-right font-mono text-amber-700 font-medium">{s.annualProduction.toFixed(0)}</td>
                    <td className="text-right font-mono text-gray-700">${s.netCost.toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
                    <td className="text-right font-mono text-emerald-700">${s.annualEnergyRevenue.toFixed(0)}</td>
                    <td className="text-right font-mono text-cyan-700">${s.annualHVACSaving.toFixed(0)}</td>
                    <td className={`text-right font-mono font-bold ${s.paybackYears < 15 ? 'text-emerald-700' : s.paybackYears < 25 ? 'text-amber-600' : 'text-red-600'}`}>
                      {s.paybackYears < 99 ? `${s.paybackYears.toFixed(1)}a` : '—'}
                    </td>
                    <td className={`text-right font-mono font-bold ${s.roi25Years >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>
                      {s.roi25Years.toFixed(0)}%
                    </td>
                    <td className={`text-right font-mono ${s.npv25Years >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>
                      ${(s.npv25Years / 1000).toFixed(1)}k
                    </td>
                    <td className={`text-right font-mono ${s.irr >= 8 ? 'text-emerald-700' : s.irr >= 0 ? 'text-amber-600' : 'text-red-600'}`}>
                      {s.irr > -50 ? `${s.irr.toFixed(1)}%` : '—'}
                    </td>
                    <td className="text-right font-mono text-gray-600">${s.lcoe.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Leyenda */}
          <div className="flex flex-wrap gap-3 text-[10px] text-gray-600 bg-gray-50 rounded-lg p-3">
            <span className="flex items-center gap-1"><span className="w-3 h-2 bg-emerald-100 border border-emerald-300 rounded inline-block" /> Viable (ROI &gt; 0)</span>
            <span className="flex items-center gap-1"><span className="w-3 h-2 bg-red-50 border border-red-200 rounded inline-block" /> No viable</span>
            <span className="flex items-center gap-1"><span className="w-3 h-2 ring-2 ring-indigo-300 rounded inline-block" /> Configuración actual</span>
            <span>| VAN = Valor Actual Neto (8%) | TIR = Tasa Interna Retorno | LCOE = Costo Nivelado Energía</span>
          </div>

          {/* Desglose del mejor escenario */}
          {bestScenario && (
            <div className="bg-emerald-50 border-2 border-emerald-200 rounded-xl p-4">
              <h4 className="text-sm font-bold text-emerald-800 mb-3">🏆 Mejor Escenario: {bestScenario.name}</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div>
                  <p className="text-gray-600">Costo Total Sistema</p>
                  <p className="font-bold text-gray-800">${bestScenario.totalSystemCost.toLocaleString(undefined, {maximumFractionDigits: 0})}</p>
                </div>
                <div>
                  <p className="text-gray-600">Ahorro Vidrio Conv.</p>
                  <p className="font-bold text-emerald-700">-${bestScenario.conventionalGlassSaving.toLocaleString(undefined, {maximumFractionDigits: 0})}</p>
                </div>
                <div>
                  <p className="text-gray-600">Ahorro Incentivos</p>
                  <p className="font-bold text-emerald-700">-${bestScenario.incentiveSaving.toLocaleString(undefined, {maximumFractionDigits: 0})}</p>
                </div>
                <div>
                  <p className="text-gray-600">Costo Neto Efectivo</p>
                  <p className="font-bold text-indigo-700">${(bestScenario.netCost - bestScenario.incentiveSaving).toLocaleString(undefined, {maximumFractionDigits: 0})}</p>
                </div>
              </div>
              <p className="text-xs text-gray-600 mt-3 italic">{bestScenario.description}</p>
            </div>
          )}
        </div>
      )}

      {/* Vista: Sensibilidad */}
      {activeView === 'sensitivity' && sensitivity && (
        <div className="space-y-4">
          {/* Sensibilidad a inclinación */}
          <SensitivityChart
            title="Sensibilidad a Inclinación"
            subtitle="ROI 25 años vs ángulo de inclinación"
            data={sensitivity.tiltSensitivity}
            xLabel="Inclinación"
            currentValue={tilt}
          />

          {/* Sensibilidad a transparencia */}
          <SensitivityChart
            title="Sensibilidad a Transparencia"
            subtitle="ROI 25 años vs nivel de transparencia del vidrio"
            data={sensitivity.transparencySensitivity}
            xLabel="Transparencia"
            currentValue={results[0]?.transparencia}
          />

          {/* Sensibilidad a tarifa */}
          <SensitivityChart
            title="Sensibilidad a Tarifa Eléctrica"
            subtitle="ROI 25 años vs tarifa de compra"
            data={sensitivity.rateSensitivity}
            xLabel="Tarifa"
            currentValue={energyParams.electricityBuyRate}
          />

          {/* Sensibilidad a autoconsumo */}
          <SensitivityChart
            title="Sensibilidad a % Autoconsumo"
            subtitle="ROI 25 años vs porcentaje de autoconsumo"
            data={sensitivity.selfConsumptionSensitivity}
            xLabel="Autoconsumo"
            currentValue={energyParams.selfConsumptionPercent}
          />
        </div>
      )}

      {/* Vista: Recomendaciones */}
      {activeView === 'recommendations' && (
        <div className="space-y-3">
          {recommendations.length === 0 && (
            <div className="text-center py-6 text-gray-500 bg-gray-50 rounded-xl border border-gray-200">
              <p className="font-medium">No hay recomendaciones disponibles. Ejecute la simulación primero.</p>
            </div>
          )}
          {recommendations.map((rec, i) => (
            <div key={i} className={`border-2 rounded-xl p-4 ${
              rec.priority === 'high' ? 'border-red-200 bg-red-50/50' :
              rec.priority === 'medium' ? 'border-amber-200 bg-amber-50/50' :
              'border-gray-200 bg-gray-50/50'
            }`}>
              <div className="flex items-start gap-3">
                <span className="text-xl">{rec.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h5 className="text-sm font-bold text-gray-900">{rec.title}</h5>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase ${
                      rec.priority === 'high' ? 'bg-red-200 text-red-800' :
                      rec.priority === 'medium' ? 'bg-amber-200 text-amber-800' :
                      'bg-gray-200 text-gray-700'
                    }`}>
                      {rec.priority === 'high' ? 'Alta' : rec.priority === 'medium' ? 'Media' : 'Baja'}
                    </span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${
                      rec.type === 'architectural' ? 'bg-blue-100 text-blue-700' :
                      rec.type === 'technical' ? 'bg-purple-100 text-purple-700' :
                      rec.type === 'financial' ? 'bg-emerald-100 text-emerald-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {rec.type === 'architectural' ? 'Arquitectónica' :
                       rec.type === 'technical' ? 'Técnica' :
                       rec.type === 'financial' ? 'Financiera' : 'Operacional'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-700 mb-2">{rec.description}</p>
                  <p className="text-xs font-semibold text-emerald-700 bg-emerald-50 inline-block px-2 py-0.5 rounded">
                    {rec.impact}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Componente auxiliar: Gráfico de sensibilidad ───────────────────────────

function SensitivityChart({ title, subtitle, data, xLabel, currentValue }: {
  title: string;
  subtitle: string;
  data: SensitivityPoint[];
  xLabel: string;
  currentValue?: number;
}) {
  const maxROI = Math.max(...data.map(d => d.roi25), 0);
  const minROI = Math.min(...data.map(d => d.roi25), 0);
  const range = maxROI - minROI || 1;
  
  // Encontrar el punto de equilibrio (ROI = 0)
  const breakEvenIdx = data.findIndex((d, i) => {
    if (i === 0) return false;
    return (data[i - 1].roi25 < 0 && d.roi25 >= 0) || (data[i - 1].roi25 >= 0 && d.roi25 < 0);
  });

  return (
    <div className="bg-white border-2 border-gray-200 rounded-xl p-4 shadow-sm">
      <h4 className="text-sm font-bold text-gray-800">{title}</h4>
      <p className="text-[10px] text-gray-500 mb-3">{subtitle}</p>
      
      {/* Gráfico de barras horizontal */}
      <div className="space-y-1.5">
        {data.map((point, i) => {
          const isPositive = point.roi25 >= 0;
          const barWidth = Math.abs(point.roi25) / range * 80;
          const isCurrent = currentValue !== undefined && Math.abs(point.value - currentValue) < 0.01;
          
          return (
            <div key={i} className={`flex items-center gap-2 ${isCurrent ? 'bg-indigo-50 rounded px-1 -mx-1' : ''}`}>
              <span className={`text-[10px] w-14 shrink-0 text-right font-medium ${isCurrent ? 'text-indigo-700 font-bold' : 'text-gray-600'}`}>
                {point.label}{isCurrent ? ' ◄' : ''}
              </span>
              <div className="flex-1 flex items-center h-5">
                <div className="w-full bg-gray-100 rounded-full h-4 relative overflow-hidden">
                  {isPositive ? (
                    <div className="absolute inset-y-0 left-0 bg-emerald-500 rounded-full transition-all"
                      style={{ width: `${Math.min(barWidth, 100)}%` }} />
                  ) : (
                    <div className="absolute inset-y-0 right-0 bg-red-400 rounded-full transition-all"
                      style={{ width: `${Math.min(barWidth, 100)}%` }} />
                  )}
                </div>
              </div>
              <span className={`text-[10px] w-16 shrink-0 text-right font-bold font-mono ${isPositive ? 'text-emerald-700' : 'text-red-600'}`}>
                {point.roi25.toFixed(0)}%
              </span>
              <span className="text-[9px] w-14 shrink-0 text-right text-gray-500 font-mono">
                {point.payback < 99 ? `${point.payback.toFixed(1)}a` : '—'}
              </span>
            </div>
          );
        })}
      </div>
      
      {/* Leyenda */}
      <div className="flex gap-4 mt-2 text-[9px] text-gray-500">
        <span className="flex items-center gap-1"><span className="w-3 h-2 bg-emerald-500 rounded inline-block" /> ROI positivo</span>
        <span className="flex items-center gap-1"><span className="w-3 h-2 bg-red-400 rounded inline-block" /> ROI negativo</span>
        {breakEvenIdx > 0 && <span className="font-semibold text-indigo-700">Punto equilibrio: ~{data[breakEvenIdx]?.label}</span>}
      </div>
    </div>
  );
}
