import { useState, useMemo, useCallback } from 'react';
import { PanelTechnology, DEFAULT_PANEL_TECHNOLOGIES } from '@/lib/panelTechnologies';
import { detectColombianRegion, COLOMBIAN_REGION_OPTIONS, ColombianRegionKey } from '@/lib/colombianRegions';
import { useCustomPanels } from '@/hooks/useCustomPanels';
import PanelTechSelector from './PanelTechSelector';
import {
  quickEstimate,
  calculateMulcuePR,
  calculateCellTemp,
  calculateTempLossFactor,
  REGION_FI_TABLE,
  SHADOW_FACTOR_TABLE,
  PR_REFERENCE_TABLE,
  DEFAULT_NOCT,
  T_REF_STC,
  G_NOCT_REF,
  G_STC,
} from '@/lib/mulcueLlanos';
import {
  Zap, Sun, Thermometer, MapPin, TrendingUp, Shield, DollarSign,
  ChevronDown, ChevronUp, Info, BarChart3, Plus, X, ArrowRight,
} from 'lucide-react';
import { Slider } from '@/components/ui/slider';
import SensitivityChart from '@/components/SensitivityChart';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

// ============================================================
// INTERFACES
// ============================================================

interface SelectedPointData {
  lat: number;
  lng: number;
  annualGHI: number; // kWh/m²/año
  category: string;
  color: string;
}

interface PinnedEstimate {
  id: string;
  point: SelectedPointData;
  estimate: ReturnType<typeof quickEstimate>;
  shadowFactor: number;
  moduleCount: number;
}

/** Datos que se envían al Simulador de Energía */
export interface ProspectorToSimulatorData {
  source: 'heatmap_pvgis' | 'heatmap_pvwatts';
  ghiAnnualKwhM2: number;
  ghiDailyKwhM2: number;
  prCorrected: number;
  ambientTemp: number;
  cellTemp: number;
  tempLossFactor: number;
  tempLossPercent: number;
  noct: number;
  irradianceG: number;
  regionKey: string;
  regionLabel: string;
  fi: number;
  fs: number;
  tiltRecommended: number;
  panelId: string;
  panelName: string;
  panelPowerW: number;
  pExpPerModule: number;
  pExpTotal: number;
  tempDegradation: number;
  moduleCount: number;
  peakPowerKw: number;
  estimatedEnergyKwh: number;
  hspTotal: number;
  lat: number;
  lng: number;
  availableArea?: number; // m² de área disponible para paneles
}

interface SolarProspectorProps {
  /** Punto seleccionado del heatmap (o null si no hay) */
  selectedPoint: SelectedPointData | null;
  /** Temperatura ambiente promedio de la zona (°C) - del EPW o estimación regional */
  ambientTemp?: number;
  /** Tarifa eléctrica (USD/kWh) para cálculo financiero */
  electricityRate?: number;
  /** Fuente de datos: 'heatmap_pvgis' o 'heatmap_pvwatts' */
  source?: 'heatmap_pvgis' | 'heatmap_pvwatts';
  /** Callback para enviar datos al Simulador de Energía */
  onUseInSimulator?: (data: ProspectorToSimulatorData) => void;
  /** Fachadas del modelo 3D para importar área */
  modelFacades?: import('@/lib/buildingModelImporter').DetectedFacade[];
}

// ============================================================
// COMPONENTE PRINCIPAL
// ============================================================

export default function SolarProspector({
  selectedPoint,
  ambientTemp: propAmbientTemp,
  electricityRate = 0.15,
  source = 'heatmap_pvgis' as const,
  onUseInSimulator,
  modelFacades,
}: SolarProspectorProps) {
  // Estado del panel seleccionado
  const [selectedPanel, setSelectedPanel] = useState<PanelTechnology>(DEFAULT_PANEL_TECHNOLOGIES[0]);
  const [yearsFromInstall, setYearsFromInstall] = useState(0);

  // === PANELES PERSONALIZADOS PERSISTENTES ===
  const { panels: savedPanelsRaw, savePanel: savePanelPersist, deletePanel: deletePanelPersist } = useCustomPanels();

  // Convertir CustomPanelLocal[] a PanelTechnology[] para el selector
  const savedPanelsTech = useMemo<PanelTechnology[]>(() => {
    return savedPanelsRaw.map(p => ({
      id: `saved_${p.localId}`,
      name: p.name,
      category: 'generic' as const,
      brand: 'generic' as const,
      description: `Panel personalizado guardado`,
      pmax: p.powerRating,
      voc: p.voc ?? 40,
      isc: p.isc ?? 10,
      vmp: p.vmp ?? 33,
      imp: p.imp ?? 9.5,
      efficiencySTC: p.efficiency,
      tempCoeffPmax: p.tempCoeff,
      lengthMm: p.lengthMm ?? 1700,
      widthMm: p.widthMm ?? 1000,
      weightKg: p.weightKg ?? 20,
      noct: p.noct,
      systemLoss: p.systemLoss ?? 14,
      degradationAnnual: p.degradationAnnual,
      pvgisTechchoice: 'crystSi',
      pvgisMountingplace: 'building' as const,
      priceUSD: 0,
      pricePerWp: 0,
      application: p.application ?? 'BIPV personalizado',
      color: '#6B7280',
      isCustom: true,
      hiitioId: '' as any,
      regionalCompatibility: {
        caribe: 2 as const, andina: 3 as const, pacifica: 2 as const,
        orinoquia: 2 as const, amazonia: 2 as const, insular: 2 as const,
        notes: 'Panel personalizado guardado',
      },
    }));
  }, [savedPanelsRaw]);

  const handleSavePanelPersist = useCallback((panel: PanelTechnology) => {
    savePanelPersist({
      name: panel.name,
      powerRating: panel.pmax,
      efficiency: panel.efficiencySTC,
      tempCoeff: panel.tempCoeffPmax,
      noct: panel.noct,
      area: (panel.lengthMm * panel.widthMm) / 1e6,
      degradationAnnual: panel.degradationAnnual,
      voc: panel.voc,
      isc: panel.isc,
      vmp: panel.vmp,
      imp: panel.imp,
      lengthMm: panel.lengthMm,
      widthMm: panel.widthMm,
      weightKg: panel.weightKg,
      systemLoss: panel.systemLoss,
      application: panel.application,
    });
  }, [savePanelPersist]);

  const handleDeletePanelPersist = useCallback((panelId: string) => {
    const localId = panelId.replace('saved_', '');
    deletePanelPersist(localId);
  }, [deletePanelPersist]);

  const [moduleCount, setModuleCount] = useState(10);
  const [shadowFactor, setShadowFactor] = useState(0.90);
  const [customAmbientTemp, setCustomAmbientTemp] = useState<number | null>(null);
  const [showFormulas, setShowFormulas] = useState(false);
  const [showPRTable, setShowPRTable] = useState(false);
  const [irradianceG, setIrradianceG] = useState(G_NOCT_REF); // W/m², default NOCT=800
  const [availableAreaInput, setAvailableAreaInput] = useState('');
  const [showFacadeSelector, setShowFacadeSelector] = useState(false);

  // Puntos anclados para comparación
  const [pinnedEstimates, setPinnedEstimates] = useState<PinnedEstimate[]>([]);

  // Detectar región del punto seleccionado
  const regionDetection = useMemo(() => {
    if (!selectedPoint) return null;
    return detectColombianRegion(selectedPoint.lat, selectedPoint.lng);
  }, [selectedPoint?.lat, selectedPoint?.lng]);

  // Temperatura ambiente: prop > custom > regional > default 25°C
  const ambientTemp = useMemo(() => {
    if (customAmbientTemp !== null) return customAmbientTemp;
    if (propAmbientTemp) return propAmbientTemp;
    if (regionDetection) {
      const regionFI = REGION_FI_TABLE.find(r => r.key === regionDetection.region);
      if (regionFI) return regionFI.avgTemp;
    }
    return 25;
  }, [customAmbientTemp, propAmbientTemp, regionDetection]);

  // Estimación rápida
  const estimate = useMemo(() => {
    if (!selectedPoint || selectedPoint.annualGHI <= 0) return null;

    const regionKey = regionDetection?.region || 'andina';

    return quickEstimate({
      ghiAnnualKwhM2: selectedPoint.annualGHI,
      ambientTemp,
      tempCoeffGamma: selectedPanel.tempCoeffPmax,
      modulePowerW: selectedPanel.pmax,
      moduleCount,
      regionKey,
      shadowFactor,
      noct: selectedPanel.noct,
      avgIrradiance: irradianceG,
    });
  }, [selectedPoint, ambientTemp, selectedPanel, moduleCount, shadowFactor, regionDetection, irradianceG]);

  // Anclar punto actual
  const pinCurrentEstimate = () => {
    if (!selectedPoint || !estimate) return;
    if (pinnedEstimates.length >= 3) {
      return; // Máximo 3 puntos
    }
    const id = `${selectedPoint.lat.toFixed(4)}_${selectedPoint.lng.toFixed(4)}_${Date.now()}`;
    setPinnedEstimates(prev => [...prev, {
      id,
      point: { ...selectedPoint },
      estimate,
      shadowFactor,
      moduleCount,
    }]);
  };

  const removePinnedEstimate = (id: string) => {
    setPinnedEstimates(prev => prev.filter(p => p.id !== id));
  };

  // Datos financieros rápidos
  const financials = useMemo(() => {
    if (!estimate) return null;
    const annualRevenue = estimate.production.energyKwh * electricityRate;
    const systemCost = moduleCount * selectedPanel.priceUSD;
    const payback = systemCost > 0 ? systemCost / annualRevenue : 0;
    return { annualRevenue, systemCost, payback };
  }, [estimate, electricityRate, moduleCount, selectedPanel.priceUSD]);

  // Shadow factor label
  const sfLabel = SHADOW_FACTOR_TABLE.find(s => s.fs === shadowFactor)
    || SHADOW_FACTOR_TABLE.find(s => Math.abs(s.fs - shadowFactor) < 0.03)
    || { label: 'Personalizado', description: '', icon: '⚙️' };

  if (!selectedPoint) {
    return (
      <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-6">
        <h3 className="text-lg font-bold text-amber-900 mb-2 flex items-center gap-2">
          <Zap size={20} className="text-amber-600" />
          Prospector Solar — Modelo Mulcue-Llanos
        </h3>
        <p className="text-sm text-amber-800">
          Haz clic en un punto del heatmap o en un marcador para ver la estimación de producción
          energética basada en el modelo Mulcue-Llanos con datos {source === 'heatmap_pvwatts' ? 'PVWatts (NREL TMY)' : 'PVGIS'} reales.
        </p>
        <div className="mt-3 p-3 bg-white/60 rounded-lg">
          <p className="text-xs text-amber-700">
            <strong>Fórmula:</strong> E_PV = G_a(0) × FI × FS × 365 × P_pico(kW) × PR
          </p>
          <p className="text-xs text-amber-700 mt-1">
            <strong>PR (Mulcue-Llanos):</strong> PR = K_sist × (1 + γ × (1.12 × Ta - 10)) + 0.0006 × Ta - 0.017
          </p>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="space-y-4">
        {/* Header con punto seleccionado */}
        <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-5">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-amber-900 flex items-center gap-2">
                <Zap size={20} className="text-amber-600" />
                Prospector Solar — Modelo Mulcue-Llanos
              </h3>
              <p className="text-xs text-amber-700 mt-1">
                Estimación rápida de producción sin necesidad de archivo EPW
              </p>
            </div>
            <button
              onClick={pinCurrentEstimate}
              disabled={pinnedEstimates.length >= 3}
              className="flex items-center gap-1 px-3 py-1.5 bg-amber-600 text-white text-xs rounded-lg hover:bg-amber-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              title={pinnedEstimates.length >= 3 ? 'Máximo 3 puntos' : 'Anclar para comparar'}
            >
              <Plus size={14} />
              Anclar ({pinnedEstimates.length}/3)
            </button>
          </div>

          {/* Datos del punto seleccionado */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div className="bg-white/70 rounded-lg p-3">
              <p className="text-xs text-gray-500 flex items-center gap-1"><MapPin size={12} /> Coordenadas</p>
              <p className="font-mono text-sm font-bold text-gray-900">
                {selectedPoint.lat.toFixed(4)}°, {selectedPoint.lng.toFixed(4)}°
              </p>
            </div>
            <div className="bg-white/70 rounded-lg p-3">
              <p className="text-xs text-gray-500 flex items-center gap-1"><Sun size={12} /> GHI Anual ({source === 'heatmap_pvwatts' ? 'PVWatts' : 'PVGIS'})</p>
              <p className="font-mono text-lg font-bold" style={{ color: selectedPoint.color }}>
                {selectedPoint.annualGHI.toFixed(0)}
                <span className="text-xs font-normal text-gray-500 ml-1">kWh/m²/año</span>
              </p>
            </div>
            <div className="bg-white/70 rounded-lg p-3">
              <p className="text-xs text-gray-500 flex items-center gap-1"><Sun size={12} /> HSP/día</p>
              <p className="font-mono text-lg font-bold text-blue-700">
                {(selectedPoint.annualGHI / 365).toFixed(2)}
                <span className="text-xs font-normal text-gray-500 ml-1">h</span>
              </p>
            </div>
            <div className="bg-white/70 rounded-lg p-3">
              <p className="text-xs text-gray-500">Clasificación</p>
              <Badge
                className="text-white text-xs mt-1"
                style={{ backgroundColor: selectedPoint.color }}
              >
                {selectedPoint.category}
              </Badge>
              {regionDetection && (
                <p className="text-xs text-gray-500 mt-1">
                  Región: <strong>{regionDetection.label}</strong>
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Parámetros de configuración */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Shield size={16} className="text-blue-600" />
            Parámetros del Sistema
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Panel seleccionado con selector rico */}
            <div className="md:col-span-2 lg:col-span-3 border-b border-gray-100 pb-3 mb-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Tecnología del Panel (Catálogo y Personalizados)</label>
              <PanelTechSelector
                selectedTech={selectedPanel}
                onSelectTech={setSelectedPanel}
                yearsFromInstall={yearsFromInstall}
                onYearsChange={setYearsFromInstall}
                savedPanels={savedPanelsTech}
                onSavePanel={handleSavePanelPersist}
                onDeletePanel={handleDeletePanelPersist}
              />
            </div>

            {/* Cantidad de módulos */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Módulos: <span className="text-blue-600 font-bold">{moduleCount}</span>
                <span className="text-gray-400 ml-1">
                  ({(moduleCount * selectedPanel.pmax / 1000).toFixed(2)} kWp)
                </span>
              </label>
              <Slider
                value={[moduleCount]}
                onValueChange={([v]) => setModuleCount(v)}
                min={1}
                max={500}
                step={1}
                className="mt-2"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>1</span>
                <span>500</span>
              </div>
            </div>

            {/* Temperatura ambiente */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                T. Ambiente: <span className="text-orange-600 font-bold">{ambientTemp}°C</span>
                <span className="text-gray-400 ml-1">
                  (T. celda: {calculateCellTemp(ambientTemp, selectedPanel.noct, irradianceG).toFixed(1)}°C @ {irradianceG} W/m²)
                </span>
              </label>
              <Slider
                value={[customAmbientTemp ?? ambientTemp]}
                onValueChange={([v]) => setCustomAmbientTemp(v)}
                min={10}
                max={45}
                step={0.5}
                className="mt-2"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>10°C</span>
                {customAmbientTemp !== null && (
                  <button
                    onClick={() => setCustomAmbientTemp(null)}
                    className="text-blue-500 hover:text-blue-700 underline"
                  >
                    Usar regional ({REGION_FI_TABLE.find(r => r.key === regionDetection?.region)?.avgTemp ?? 25}°C)
                  </button>
                )}
                <span>45°C</span>
              </div>
            </div>

            {/* Factor de sombreado */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Factor Sombras (FS): <span className="text-green-600 font-bold">{shadowFactor.toFixed(2)}</span>
                <span className="text-gray-400 ml-1">{sfLabel.icon} {sfLabel.label}</span>
              </label>
              <Slider
                value={[shadowFactor * 100]}
                onValueChange={([v]) => setShadowFactor(v / 100)}
                min={50}
                max={100}
                step={5}
                className="mt-2"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0.50 (severo)</span>
                <span>1.00 (sin sombras)</span>
              </div>
            </div>

            {/* Irradiancia de referencia G */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Irradiancia G: <span className="text-red-600 font-bold">{irradianceG} W/m²</span>
                <span className="text-gray-400 ml-1">
                  {irradianceG === G_NOCT_REF ? '(NOCT)' : irradianceG === G_STC ? '(STC)' : ''}
                </span>
              </label>
              <Slider
                value={[irradianceG]}
                onValueChange={([v]) => setIrradianceG(v)}
                min={200}
                max={1200}
                step={25}
                className="mt-2"
              />
              <div className="flex justify-between items-center text-xs text-gray-400 mt-1">
                <span>200</span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setIrradianceG(G_NOCT_REF)}
                    className={`px-1.5 py-0.5 rounded text-xs transition-colors ${
                      irradianceG === G_NOCT_REF
                        ? 'bg-blue-100 text-blue-700 font-semibold'
                        : 'text-blue-500 hover:text-blue-700 hover:bg-blue-50'
                    }`}
                  >
                    NOCT (800)
                  </button>
                  <button
                    onClick={() => setIrradianceG(G_STC)}
                    className={`px-1.5 py-0.5 rounded text-xs transition-colors ${
                      irradianceG === G_STC
                        ? 'bg-orange-100 text-orange-700 font-semibold'
                        : 'text-orange-500 hover:text-orange-700 hover:bg-orange-50'
                    }`}
                  >
                    STC (1000)
                  </button>
                </div>
                <span>1200</span>
              </div>
              <div className="mt-1.5 p-2 rounded-lg text-xs" style={{
                backgroundColor: irradianceG > G_STC ? '#fef2f2' : irradianceG >= G_NOCT_REF ? '#fffbeb' : '#f0fdf4',
                color: irradianceG > G_STC ? '#991b1b' : irradianceG >= G_NOCT_REF ? '#92400e' : '#166534',
              }}>
                <strong>T. celda:</strong> {calculateCellTemp(ambientTemp, selectedPanel.noct, irradianceG).toFixed(1)}°C
                {' | '}
                <strong>Pérdida T°:</strong> {estimate ? estimate.tempLossPercent.toFixed(1) : '—'}%
                {irradianceG !== G_NOCT_REF && (
                  <span className="ml-1 opacity-70">
                    (vs {calculateCellTemp(ambientTemp, selectedPanel.noct, G_NOCT_REF).toFixed(1)}°C @ NOCT)
                  </span>
                )}
              </div>
            </div>

            {/* Factor de irradiación FI */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Factor Irradiación (FI)
              </label>
              <div className="bg-gray-50 rounded-lg p-2">
                {estimate?.regionInfo ? (
                  <div>
                    <p className="text-sm font-bold text-indigo-700">{estimate.regionInfo.fi.toFixed(2)}</p>
                    <p className="text-xs text-gray-500">
                      Región {estimate.regionInfo.region} — Inclinación recomendada: {estimate.regionInfo.tiltRecommended}°
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">{estimate.regionInfo.description}</p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">0.95 (por defecto)</p>
                )}
              </div>
            </div>

            {/* Tarifa eléctrica */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Tarifa eléctrica
              </label>
              <div className="bg-gray-50 rounded-lg p-2">
                <p className="text-sm font-bold text-green-700">${electricityRate.toFixed(2)} USD/kWh</p>
                <p className="text-xs text-gray-400">Para estimación financiera rápida</p>
              </div>
            </div>
          </div>

          {/* Tabla de FS */}
          <div className="mt-4">
            <p className="text-xs text-gray-500 mb-2">
              <strong>Referencia Factor de Sombreado (FS):</strong>
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-1">
              {SHADOW_FACTOR_TABLE.map(sf => (
                <button
                  key={sf.fs}
                  onClick={() => setShadowFactor(sf.fs)}
                  className={`text-xs p-1.5 rounded border transition-colors ${
                    Math.abs(shadowFactor - sf.fs) < 0.01
                      ? 'bg-blue-100 border-blue-400 text-blue-800'
                      : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <span className="block font-bold">{sf.icon} {sf.fs.toFixed(2)}</span>
                  <span className="block text-[10px] text-gray-500 leading-tight">{sf.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* RESULTADOS */}
        {estimate && (
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 size={16} className="text-green-600" />
              Resultados — Estimación Rápida
            </h4>

            {/* Métricas principales */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg p-3 text-center">
                <p className="text-xs text-green-700 mb-1">Energía Anual</p>
                <p className="text-2xl font-bold text-green-800 font-mono">
                  {estimate.production.energyKwh >= 1000
                    ? `${estimate.production.energyMwh}`
                    : estimate.production.energyKwh.toFixed(0)}
                </p>
                <p className="text-xs text-green-600">
                  {estimate.production.energyKwh >= 1000 ? 'MWh/año' : 'kWh/año'}
                </p>
              </div>

              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-3 text-center">
                <p className="text-xs text-blue-700 mb-1">PR (Mulcue-Llanos)</p>
                <p className="text-2xl font-bold font-mono" style={{ color: estimate.pr.color }}>
                  {(estimate.pr.prCorrected * 100).toFixed(1)}%
                </p>
                <p className="text-xs" style={{ color: estimate.pr.color }}>
                  {estimate.pr.interpretation === 'optimo' ? 'Óptimo' :
                   estimate.pr.interpretation === 'bueno' ? 'Bueno' :
                   estimate.pr.interpretation === 'medio' ? 'Medio' : 'Bajo'}
                </p>
              </div>

              <div className="bg-gradient-to-br from-amber-50 to-yellow-50 border border-amber-200 rounded-lg p-3 text-center">
                <p className="text-xs text-amber-700 mb-1">HSP Total</p>
                <p className="text-2xl font-bold text-amber-800 font-mono">
                  {estimate.production.hspTotal.toFixed(0)}
                </p>
                <p className="text-xs text-amber-600">horas/año</p>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-fuchsia-50 border border-purple-200 rounded-lg p-3 text-center">
                <p className="text-xs text-purple-700 mb-1">P_exp (real)</p>
                <p className="text-2xl font-bold text-purple-800 font-mono">
                  {(estimate.pExpTotal / 1000).toFixed(2)}
                </p>
                <p className="text-xs text-purple-600">kWp</p>
                <p className="text-[10px] text-gray-400 mt-0.5">P_nom: {(estimate.pNomTotal / 1000).toFixed(2)} kWp</p>
              </div>
            </div>

            {/* Desglose de cálculo */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="text-xs font-semibold text-gray-700 mb-2">Desglose del cálculo:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1 text-xs text-gray-600">
                <p>GHI {source === 'heatmap_pvwatts' ? 'PVWatts' : 'PVGIS'}: <strong className="text-gray-900">{selectedPoint.annualGHI.toFixed(0)} kWh/m²/año</strong> → <strong>{(selectedPoint.annualGHI / 365).toFixed(2)} kWh/m²/día</strong></p>
                <p>FI (región {estimate.regionInfo?.region || '—'}): <strong className="text-gray-900">{estimate.regionInfo?.fi.toFixed(2) || '0.95'}</strong></p>
                <p>FS (sombreado): <strong className="text-gray-900">{shadowFactor.toFixed(2)}</strong> — {sfLabel.label}</p>
                <p>G_a corregida: <strong className="text-gray-900">{estimate.production.gaCorr.toFixed(4)} kWh/m²/día</strong></p>
                <p>HSP = G_a × 365: <strong className="text-gray-900">{estimate.production.hspTotal.toFixed(2)} h</strong></p>
                <p>P_nom (STC): <strong className="text-gray-900">{moduleCount} × {selectedPanel.pmax}W = {(moduleCount * selectedPanel.pmax / 1000).toFixed(2)} kWp</strong></p>
                <p>T. ambiente: <strong className="text-gray-900">{ambientTemp}°C</strong></p>
                <p>NOCT panel: <strong className="text-gray-900">{selectedPanel.noct || DEFAULT_NOCT}°C</strong></p>
                <p>Irradiancia G: <strong className="text-red-700">{irradianceG} W/m²</strong> {irradianceG === G_NOCT_REF ? '(NOCT)' : irradianceG === G_STC ? '(STC)' : ''}</p>
                <p>T. celda = {ambientTemp} + ({selectedPanel.noct || DEFAULT_NOCT}−20)×{irradianceG}/800: <strong className="text-orange-700">{estimate.cellTemp.toFixed(1)}°C</strong></p>
                <p>γ panel: <strong className="text-gray-900">{selectedPanel.tempCoeffPmax}%/°C</strong></p>
                <p className="md:col-span-2 mt-1 pt-1 border-t border-gray-200 bg-red-50 p-2 rounded">
                  <strong className="text-red-700">P_exp = P_nom × [1 + γ(T_c − 21)] × (G/1000)</strong><br />
                  <span className="text-red-600">
                    P_exp = {selectedPanel.pmax}W × [1 + ({(selectedPanel.tempCoeffPmax / 100).toFixed(4)}) × ({estimate.cellTemp.toFixed(1)} − 21)] × ({irradianceG}/1000)
                  </span><br />
                  <span className="text-red-600">
                    P_exp = {selectedPanel.pmax}W × {(1 + (selectedPanel.tempCoeffPmax / 100) * (estimate.cellTemp - 21)).toFixed(4)} × {(irradianceG / 1000).toFixed(3)}
                  </span><br />
                  <strong className="text-red-800">P_exp = {estimate.pExp.toFixed(1)}W por módulo</strong>
                  <span className="text-red-600 ml-2">(degradación por T°: {estimate.tempDegradation.toFixed(1)}%)</span>
                </p>
                <p>P_exp total: <strong className="text-orange-700">{moduleCount} × {estimate.pExp.toFixed(1)}W = {(estimate.pExpTotal / 1000).toFixed(3)} kWp</strong></p>
                <p>PR_max = 0.82 × (1 + γ × (1.12×Ta - 10)): <strong className="text-gray-900">{estimate.pr.prMax.toFixed(4)}</strong></p>
                <p>PR_C = PR_max + 0.0006×Ta - 0.017: <strong className="text-blue-700">{estimate.pr.prCorrected.toFixed(4)}</strong></p>
                <p className="md:col-span-2 mt-1 pt-1 border-t border-gray-200">
                  <strong>E_PV = HSP × P_exp_total × PR = {estimate.production.hspTotal.toFixed(1)} × {(estimate.pExpTotal / 1000).toFixed(3)} × {estimate.pr.prCorrected.toFixed(4)} = </strong>
                  <strong className="text-green-700 text-sm">{estimate.production.energyKwh.toFixed(1)} kWh/año</strong>
                </p>
              </div>
            </div>

            {/* Gráfico de sensibilidad G vs Producción */}
            <SensitivityChart
              ghiAnnualKwhM2={selectedPoint.annualGHI}
              ambientTemp={ambientTemp}
              tempCoeffGamma={selectedPanel.tempCoeffPmax}
              modulePowerW={selectedPanel.pmax}
              moduleCount={moduleCount}
              regionKey={regionDetection?.region || 'andina'}
              shadowFactor={shadowFactor}
              noct={selectedPanel.noct || DEFAULT_NOCT}
              currentG={irradianceG}
            />

            {/* Estimación financiera rápida */}
            {financials && (
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                  <p className="text-xs text-green-700">Ahorro Anual</p>
                  <p className="text-lg font-bold text-green-800 font-mono">
                    ${financials.annualRevenue.toFixed(0)}
                  </p>
                  <p className="text-xs text-green-600">USD/año</p>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
                  <p className="text-xs text-blue-700">Costo Sistema</p>
                  <p className="text-lg font-bold text-blue-800 font-mono">
                    ${financials.systemCost.toFixed(0)}
                  </p>
                  <p className="text-xs text-blue-600">USD (ref.)</p>
                </div>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-center">
                  <p className="text-xs text-amber-700">Payback</p>
                  <p className="text-lg font-bold text-amber-800 font-mono">
                    {financials.payback.toFixed(1)}
                  </p>
                  <p className="text-xs text-amber-600">años</p>
                </div>
              </div>
            )}

            {/* Campo de Área Disponible para el Simulador */}
            {onUseInSimulator && (
              <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <label className="block text-xs font-semibold text-blue-800 mb-1">
                  Área disponible para paneles (m²)
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    min="0"
                    step="10"
                    value={availableAreaInput}
                    onChange={(e) => setAvailableAreaInput(e.target.value)}
                    placeholder="Ej: 500"
                    className="flex-1 px-3 py-2 text-sm border border-blue-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  {modelFacades && modelFacades.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setShowFacadeSelector(!showFacadeSelector)}
                      className="px-3 py-2 text-xs bg-green-100 text-green-700 border border-green-300 rounded-md hover:bg-green-200 transition-colors whitespace-nowrap"
                    >
                      Importar del Modelo 3D
                    </button>
                  )}
                </div>
                {showFacadeSelector && modelFacades && modelFacades.length > 0 && (
                  <div className="mt-2 max-h-32 overflow-y-auto border border-green-200 rounded-md bg-white">
                    {modelFacades.map((f, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => {
                          setAvailableAreaInput(f.area.toFixed(1));
                          setShowFacadeSelector(false);
                        }}
                        className="w-full text-left px-3 py-1.5 text-xs hover:bg-green-50 border-b border-gray-100 last:border-0"
                      >
                        <span className="font-medium">{f.name || `Fachada ${i + 1}`}</span>
                        <span className="text-gray-500 ml-2">{f.area.toFixed(1)} m² | Tilt: {f.tilt.toFixed(0)}°</span>
                      </button>
                    ))}
                  </div>
                )}
                <p className="text-[10px] text-blue-600 mt-1">Se usará para auto-calcular la cantidad de paneles en el Simulador</p>
              </div>
            )}

            {/* Botón Usar en Simulador */}
            {onUseInSimulator && (
              <button
                onClick={() => {
                  if (!estimate || !selectedPoint) return;
                  const regionKey = regionDetection?.region || 'andina';
                  const regionLabel = regionDetection?.label || 'Andina';
                  const fi = estimate.regionInfo?.fi || 0.95;
                  const tiltRec = estimate.regionInfo?.tiltRecommended || 10;
                  const areaVal = parseFloat(availableAreaInput);
                  onUseInSimulator({
                    source,
                    ghiAnnualKwhM2: selectedPoint.annualGHI,
                    ghiDailyKwhM2: selectedPoint.annualGHI / 365,
                    prCorrected: estimate.pr.prCorrected,
                    ambientTemp,
                    cellTemp: estimate.cellTemp,
                    tempLossFactor: estimate.tempLossFactor,
                    tempLossPercent: estimate.tempLossPercent,
                    noct: selectedPanel.noct || DEFAULT_NOCT,
                    irradianceG,
                    regionKey,
                    regionLabel,
                    fi,
                    fs: shadowFactor,
                    tiltRecommended: tiltRec,
                    panelId: selectedPanel.id,
                    panelName: selectedPanel.name,
                    panelPowerW: selectedPanel.pmax,
                    pExpPerModule: estimate.pExp,
                    pExpTotal: estimate.pExpTotal,
                    tempDegradation: estimate.tempDegradation,
                    moduleCount,
                    peakPowerKw: estimate.production.peakPowerKw,
                    estimatedEnergyKwh: estimate.production.energyKwh,
                    hspTotal: estimate.production.hspTotal,
                    lat: selectedPoint.lat,
                    lng: selectedPoint.lng,
                    availableArea: areaVal > 0 ? areaVal : undefined,
                  });
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg mb-4"
              >
                <ArrowRight size={18} />
                Usar en Simulador de Energía
                <span className="text-xs opacity-80 ml-1">({estimate?.production.energyKwh.toFixed(0)} kWh/año)</span>
              </button>
            )}

            {/* Botón para ver fórmulas */}
            <div className="flex gap-2">
              <button
                onClick={() => setShowFormulas(!showFormulas)}
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 transition-colors"
              >
                {showFormulas ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {showFormulas ? 'Ocultar' : 'Ver'} fórmulas de referencia
              </button>
              <button
                onClick={() => setShowPRTable(!showPRTable)}
                className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 transition-colors"
              >
                {showPRTable ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {showPRTable ? 'Ocultar' : 'Ver'} tabla PR
              </button>
            </div>

            {/* Fórmulas de referencia */}
            {showFormulas && (
              <div className="mt-3 bg-slate-50 border border-slate-200 rounded-lg p-4 text-xs">
                <p className="font-semibold text-slate-800 mb-2">Fórmulas — Modelo Mulcue-Llanos</p>
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-slate-300">
                      <th className="py-1 pr-2 text-slate-600">#</th>
                      <th className="py-1 pr-2 text-slate-600">Concepto</th>
                      <th className="py-1 text-slate-600">Fórmula</th>
                    </tr>
                  </thead>
                  <tbody className="font-mono text-[11px]">
                    <tr className="border-b border-slate-100">
                      <td className="py-1 pr-2">1</td>
                      <td className="py-1 pr-2 font-sans">Irradiación sobre generador</td>
                      <td className="py-1">G_a(α,β) = G_a(0) × FI × FS</td>
                    </tr>
                    <tr className="border-b border-slate-100">
                      <td className="py-1 pr-2">2</td>
                      <td className="py-1 pr-2 font-sans">HSP total</td>
                      <td className="py-1">HSP = G_a(α,β) × 365</td>
                    </tr>
                    <tr className="border-b border-slate-100">
                      <td className="py-1 pr-2">3</td>
                      <td className="py-1 pr-2 font-sans">PR máximo</td>
                      <td className="py-1">PR_max = K_sist × (1 + γ × (1.12×Ta - 10))</td>
                    </tr>
                    <tr className="border-b border-slate-100">
                      <td className="py-1 pr-2">4</td>
                      <td className="py-1 pr-2 font-sans">PR corregido</td>
                      <td className="py-1">PR_C = PR_max + 0.0006×Ta - 0.017</td>
                    </tr>
                    <tr className="border-b border-slate-100">
                      <td className="py-1 pr-2">5</td>
                      <td className="py-1 pr-2 font-sans">Energía producida</td>
                      <td className="py-1">E_PV = HSP × P_pico(kW) × PR</td>
                    </tr>
                    <tr className="border-b border-slate-100">
                      <td className="py-1 pr-2">6</td>
                      <td className="py-1 pr-2 font-sans">T. celda</td>
                      <td className="py-1">T_c = T_a × 1.40</td>
                    </tr>
                    <tr>
                      <td className="py-1 pr-2">7</td>
                      <td className="py-1 pr-2 font-sans">Diagnóstico módulo</td>
                      <td className="py-1">P_exp = P_nom × [1 + γ(T_c − 21)] × (G/1000)</td>
                    </tr>
                  </tbody>
                </table>
                <p className="text-[10px] text-slate-500 mt-2">
                  K_sist = 0.82 (sistema óptimo) | T_ref = 21°C (Mulcue-Llanos) | γ = coef. temperatura del panel
                </p>
                <p className="text-[10px] text-slate-500">
                  Ref: Dr. Luis Fernando Mulcue Nieto — Universidad Nacional de Colombia
                </p>
              </div>
            )}

            {/* Tabla PR */}
            {showPRTable && (
              <div className="mt-3 bg-slate-50 border border-slate-200 rounded-lg p-4 text-xs">
                <p className="font-semibold text-slate-800 mb-2">Tabla de Referencia PR</p>
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-slate-300">
                      <th className="py-1 pr-2 text-slate-600">Rango PR</th>
                      <th className="py-1 pr-2 text-slate-600">Calificación</th>
                      <th className="py-1 text-slate-600">Posible causa</th>
                    </tr>
                  </thead>
                  <tbody>
                    {PR_REFERENCE_TABLE.map((row, i) => (
                      <tr key={i} className="border-b border-slate-100">
                        <td className="py-1 pr-2 font-mono">
                          {row.min.toFixed(2)} – {row.max.toFixed(2)}
                        </td>
                        <td className="py-1 pr-2">
                          <span className="inline-block px-2 py-0.5 rounded text-white text-[10px] font-semibold" style={{ backgroundColor: row.color }}>
                            {row.label}
                          </span>
                        </td>
                        <td className="py-1 text-slate-600">{row.cause}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Comparador de ubicaciones */}
        {pinnedEstimates.length > 0 && (
          <div className="bg-white border border-indigo-200 rounded-xl p-5">
            <h4 className="font-semibold text-indigo-900 mb-4 flex items-center gap-2">
              <TrendingUp size={16} className="text-indigo-600" />
              Comparador de Ubicaciones ({pinnedEstimates.length} puntos)
            </h4>

            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b-2 border-indigo-200">
                    <th className="py-2 px-2 text-left text-indigo-700">Parámetro</th>
                    {pinnedEstimates.map((pe, i) => (
                      <th key={pe.id} className="py-2 px-2 text-center text-indigo-700">
                        <div className="flex items-center justify-center gap-1">
                          <span>Punto {i + 1}</span>
                          <button
                            onClick={() => removePinnedEstimate(pe.id)}
                            className="text-red-400 hover:text-red-600"
                          >
                            <X size={12} />
                          </button>
                        </div>
                      </th>
                    ))}
                    {estimate && (
                      <th className="py-2 px-2 text-center text-amber-700 bg-amber-50">
                        Actual
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-gray-100">
                    <td className="py-1.5 px-2 text-gray-600">Coordenadas</td>
                    {pinnedEstimates.map(pe => (
                      <td key={pe.id} className="py-1.5 px-2 text-center font-mono">
                        {pe.point.lat.toFixed(2)}°, {pe.point.lng.toFixed(2)}°
                      </td>
                    ))}
                    {estimate && selectedPoint && (
                      <td className="py-1.5 px-2 text-center font-mono bg-amber-50">
                        {selectedPoint.lat.toFixed(2)}°, {selectedPoint.lng.toFixed(2)}°
                      </td>
                    )}
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="py-1.5 px-2 text-gray-600">GHI (kWh/m²/año)</td>
                    {pinnedEstimates.map(pe => (
                      <td key={pe.id} className="py-1.5 px-2 text-center font-mono font-bold" style={{ color: pe.point.color }}>
                        {pe.point.annualGHI.toFixed(0)}
                      </td>
                    ))}
                    {estimate && selectedPoint && (
                      <td className="py-1.5 px-2 text-center font-mono font-bold bg-amber-50" style={{ color: selectedPoint.color }}>
                        {selectedPoint.annualGHI.toFixed(0)}
                      </td>
                    )}
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="py-1.5 px-2 text-gray-600">PR Mulcue-Llanos</td>
                    {pinnedEstimates.map(pe => (
                      <td key={pe.id} className="py-1.5 px-2 text-center font-mono" style={{ color: pe.estimate.pr.color }}>
                        {(pe.estimate.pr.prCorrected * 100).toFixed(1)}%
                      </td>
                    ))}
                    {estimate && (
                      <td className="py-1.5 px-2 text-center font-mono bg-amber-50" style={{ color: estimate.pr.color }}>
                        {(estimate.pr.prCorrected * 100).toFixed(1)}%
                      </td>
                    )}
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="py-1.5 px-2 text-gray-600">FS (sombreado)</td>
                    {pinnedEstimates.map(pe => (
                      <td key={pe.id} className="py-1.5 px-2 text-center font-mono">
                        {pe.shadowFactor.toFixed(2)}
                      </td>
                    ))}
                    {estimate && (
                      <td className="py-1.5 px-2 text-center font-mono bg-amber-50">
                        {shadowFactor.toFixed(2)}
                      </td>
                    )}
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="py-1.5 px-2 text-gray-600">Módulos</td>
                    {pinnedEstimates.map(pe => (
                      <td key={pe.id} className="py-1.5 px-2 text-center font-mono">
                        {pe.moduleCount}
                      </td>
                    ))}
                    {estimate && (
                      <td className="py-1.5 px-2 text-center font-mono bg-amber-50">
                        {moduleCount}
                      </td>
                    )}
                  </tr>
                  <tr className="border-b border-gray-100 bg-green-50">
                    <td className="py-1.5 px-2 text-green-800 font-semibold">Energía (kWh/año)</td>
                    {pinnedEstimates.map(pe => (
                      <td key={pe.id} className="py-1.5 px-2 text-center font-mono font-bold text-green-800">
                        {pe.estimate.production.energyKwh.toFixed(0)}
                      </td>
                    ))}
                    {estimate && (
                      <td className="py-1.5 px-2 text-center font-mono font-bold text-green-800 bg-amber-50">
                        {estimate.production.energyKwh.toFixed(0)}
                      </td>
                    )}
                  </tr>
                  <tr className="bg-blue-50">
                    <td className="py-1.5 px-2 text-blue-800 font-semibold">Ahorro (USD/año)</td>
                    {pinnedEstimates.map(pe => (
                      <td key={pe.id} className="py-1.5 px-2 text-center font-mono font-bold text-blue-800">
                        ${(pe.estimate.production.energyKwh * electricityRate).toFixed(0)}
                      </td>
                    ))}
                    {estimate && (
                      <td className="py-1.5 px-2 text-center font-mono font-bold text-blue-800 bg-amber-50">
                        ${financials?.annualRevenue.toFixed(0) || '—'}
                      </td>
                    )}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tabla FI por región */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Info size={16} className="text-gray-500" />
            Factor de Irradiación (FI) por Región Colombiana
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="py-2 px-2 text-left text-gray-600">Región</th>
                  <th className="py-2 px-2 text-center text-gray-600">FI</th>
                  <th className="py-2 px-2 text-center text-gray-600">Inclinación</th>
                  <th className="py-2 px-2 text-center text-gray-600">T. Promedio</th>
                  <th className="py-2 px-2 text-left text-gray-600">Descripción</th>
                </tr>
              </thead>
              <tbody>
                {REGION_FI_TABLE.map(r => (
                  <tr
                    key={r.key}
                    className={`border-b border-gray-100 ${
                      regionDetection?.region === r.key ? 'bg-amber-50 font-semibold' : ''
                    }`}
                  >
                    <td className="py-1.5 px-2">
                      {r.region}
                      {regionDetection?.region === r.key && (
                        <Badge className="ml-1 text-[9px] bg-amber-500 text-white">Actual</Badge>
                      )}
                    </td>
                    <td className="py-1.5 px-2 text-center font-mono font-bold text-indigo-700">{r.fi.toFixed(2)}</td>
                    <td className="py-1.5 px-2 text-center font-mono">{r.tiltRecommended}°</td>
                    <td className="py-1.5 px-2 text-center font-mono">{r.avgTemp}°C</td>
                    <td className="py-1.5 px-2 text-gray-500">{r.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}
