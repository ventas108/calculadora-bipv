import { useState, useMemo, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import html2canvas from 'html2canvas';
import {
  Building2, MapPin, Sun, Zap, TrendingUp, AlertTriangle, Loader2,
  ChevronDown, ChevronUp, Download, BarChart3, Thermometer, Target,
  Shield, Globe, Satellite, ClipboardCheck, PanelTop, Calculator,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ComposedChart, Line, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import PanelTechSelector from '@/components/PanelTechSelector';
import { DEFAULT_PANEL_TECHNOLOGIES, PanelTechnology } from '@/lib/panelTechnologies';
import { INSTALLATION_CONFIGS, InstallationConfig } from '@/lib/installationConfigs';
import { detectColombianRegion, ColombianRegionKey } from '@/lib/colombianRegions';
import { getPVWattsCalculation, getPVWattsHourlyData } from '@/lib/pvwattsApi';
import { getPVCalculation, getMonthlyRadiation } from '@/lib/pvgisApi';
import {
  BIPVPanelConfig, BIPVSiteConfig, BIPVMonthlyExpected, BIPVFieldMeasurement,
  BIPVComparisonResult, calculateMulcueExpected, integratePVGISData,
  integratePVWattsData, calculateAnnualSummary, compareBIPVPerformance,
  estimateGHIFromLatitude,
} from '@/lib/bipvDiagnostic';
import { diagnosePerformance, type PerformanceAlert } from '@shared/performanceDiagnostic';
import { useCustomPanels, CustomPanelLocal } from '@/hooks/useCustomPanels';
import { generateBIPVReport, type BIPVReportData } from '@/lib/bipvReportGenerator';
import PerformanceAlertPanel from '@/components/PerformanceAlertPanel';
import { calculateMulcuePR, calculateCellTemp, calculateExpectedPower, REGION_FI_TABLE } from '@shared/mulcueLlanos';
import type { RegionalCompatibility } from '@/lib/panelTechnologies';

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
const MONTH_FULL = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

export default function BIPVDiagnostic() {
  // Ref para capturar el gráfico radar como imagen
  const radarChartRef = useRef<HTMLDivElement>(null);

  // ============================================================
  // PANELES PERSONALIZADOS PERSISTENTES
  // ============================================================
  const { panels: savedPanelsRaw, savePanel, deletePanel, isSyncing, panelCount } = useCustomPanels();

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
      hiitioId: undefined as any,
      regionalCompatibility: {
        caribe: 2 as const, andina: 3 as const, pacifica: 2 as const,
        orinoquia: 2 as const, amazonia: 2 as const, insular: 2 as const,
        notes: 'Panel personalizado guardado',
      },
    }));
  }, [savedPanelsRaw]);

  const handleSavePanelPersist = useCallback((panel: PanelTechnology) => {
    savePanel({
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
    toast.success(`Panel "${panel.name}" guardado permanentemente`);
  }, [savePanel]);

  const handleDeletePanelPersist = useCallback((panelId: string) => {
    const localId = panelId.replace('saved_', '');
    deletePanel(localId);
    toast.success('Panel eliminado');
  }, [deletePanel]);

  // ============================================================
  // ESTADO: Panel
  // ============================================================
  const [selectedTech, setSelectedTech] = useState<PanelTechnology>(DEFAULT_PANEL_TECHNOLOGIES[0]);
  const [panelQuantity, setPanelQuantity] = useState(10);
  const [yearsInstalled, setYearsInstalled] = useState(0);

  // ============================================================
  // ESTADO: Ubicación y Configuración
  // ============================================================
  const [latitude, setLatitude] = useState(6.25);
  const [longitude, setLongitude] = useState(-75.56);
  const [siteName, setSiteName] = useState('Sistema BIPV');
  const [tiltField, setTiltField] = useState(10);
  const [azimuthField, setAzimuthField] = useState(0);
  const [shadowFactor, setShadowFactor] = useState(0.95);
  const [installationType, setInstallationType] = useState('rooftop_tilted');
  const [ghiOverride, setGhiOverride] = useState<number | null>(null);
  const [tempOverride, setTempOverride] = useState<number | null>(null);

  // ============================================================
  // ESTADO: Datos satelitales
  // ============================================================
  const [pvgisLoading, setPvgisLoading] = useState(false);
  const [pvwattsLoading, setPvwattsLoading] = useState(false);
  const [pvgisMonthly, setPvgisMonthly] = useState<{ month: number; productionAC_kWh: number; irradiationPOA_kWhm2: number; temperature: number }[] | null>(null);
  const [pvwattsMonthly, setPvwattsMonthly] = useState<{ month: number; ac_kWh: number; dc_kWh: number; poa_kWhm2: number; tamb_C: number; tcell_C: number }[] | null>(null);

  // ============================================================
  // ESTADO: Mediciones de campo
  // ============================================================
  const [monthlyReal, setMonthlyReal] = useState<(number | null)[]>(Array(12).fill(null));
  const [annualRealOverride, setAnnualRealOverride] = useState<number | null>(null);

  // ============================================================
  // ESTADO: UI
  // ============================================================
  const [expandedSection, setExpandedSection] = useState<string | null>('panel');
  const [showDiagnostic, setShowDiagnostic] = useState(false);

  // ============================================================
  // CÁLCULOS DERIVADOS
  // ============================================================
  const detectedRegion = useMemo(() => detectColombianRegion(latitude, longitude), [latitude, longitude]);
  const regionFI = useMemo(() => REGION_FI_TABLE.find(r => r.key === detectedRegion.region), [detectedRegion]);

  const panelConfig: BIPVPanelConfig = useMemo(() => ({
    name: selectedTech.name,
    powerRating: selectedTech.pmax,
    efficiency: selectedTech.efficiencySTC,
    tempCoeff: selectedTech.tempCoeffPmax,
    noct: selectedTech.noct,
    area: (selectedTech.lengthMm * selectedTech.widthMm) / 1_000_000,
    quantity: panelQuantity,
    yearsInstalled,
    annualDegradation: selectedTech.degradationAnnual ?? 0.5,
  }), [selectedTech, panelQuantity, yearsInstalled]);

  const siteConfig: BIPVSiteConfig = useMemo(() => ({
    latitude,
    longitude,
    siteName,
    tiltField,
    azimuthField,
    shadowFactor,
    installationType,
  }), [latitude, longitude, siteName, tiltField, azimuthField, shadowFactor, installationType]);

  const ghiAnnual = ghiOverride ?? estimateGHIFromLatitude(latitude);
  const ambientTemp = tempOverride ?? (regionFI?.avgTemp ?? 25);

  // Producción esperada mensual
  const monthlyExpected: BIPVMonthlyExpected[] = useMemo(() => {
    let monthly = calculateMulcueExpected(panelConfig, siteConfig, ghiAnnual, ambientTemp, regionFI?.fi ?? 0.95);

    if (pvgisMonthly) {
      const degradationFactor = Math.pow(1 - panelConfig.annualDegradation / 100, panelConfig.yearsInstalled);
      monthly = integratePVGISData(monthly, pvgisMonthly, degradationFactor);
    }

    if (pvwattsMonthly) {
      const degradationFactor = Math.pow(1 - panelConfig.annualDegradation / 100, panelConfig.yearsInstalled);
      monthly = integratePVWattsData(monthly, pvwattsMonthly, degradationFactor);
    }

    return monthly;
  }, [panelConfig, siteConfig, ghiAnnual, ambientTemp, regionFI, pvgisMonthly, pvwattsMonthly]);

  const annualSummary = useMemo(() => calculateAnnualSummary(monthlyExpected, panelConfig), [monthlyExpected, panelConfig]);

  // Comparación real vs esperada
  const fieldData: BIPVFieldMeasurement = useMemo(() => {
    const annualFromMonthly = monthlyReal.some(v => v !== null)
      ? monthlyReal.reduce<number>((s, v) => s + (v ?? 0), 0)
      : null;
    return {
      monthlyProduction_kWh: monthlyReal,
      annualProduction_kWh: annualRealOverride ?? annualFromMonthly,
    };
  }, [monthlyReal, annualRealOverride]);

  const comparison: BIPVComparisonResult | null = useMemo(() => {
    if (fieldData.annualProduction_kWh === null && !monthlyReal.some(v => v !== null)) return null;
    return compareBIPVPerformance(monthlyExpected, fieldData, panelConfig, ghiAnnual);
  }, [monthlyExpected, fieldData, panelConfig, monthlyReal, ghiAnnual]);

  // Diagnóstico de rendimiento
  const performanceAlert: PerformanceAlert | null = useMemo(() => {
    if (!comparison || comparison.annual.pr_real === null) return null;
    return diagnosePerformance({
      prMeasured: comparison.annual.pr_real,
      ghiField: ghiAnnual / 365 * 1000 / 8, // W/m² promedio
      tempAmbient: ambientTemp,
      tempCell: calculateCellTemp(ambientTemp, panelConfig.noct, 800),
      tempCellManual: false,
      pExp: calculateExpectedPower(panelConfig.powerRating, panelConfig.tempCoeff, calculateCellTemp(ambientTemp, panelConfig.noct, 800), 800),
      pNom: panelConfig.powerRating,
      tempCoeff: panelConfig.tempCoeff,
      noct: panelConfig.noct,
      tempLoss: 1,
      installationType,
      latitude,
    });
  }, [comparison, ghiAnnual, ambientTemp, panelConfig, installationType, latitude]);

  // ============================================================
  // HANDLERS
  // ============================================================
  const handleConsultPVGIS = useCallback(async () => {
    setPvgisLoading(true);
    try {
      const capacityKwp = (panelConfig.powerRating * panelConfig.quantity) / 1000;
      const pvTech = selectedTech.pvgisTechchoice || 'crystSi';
      const result = await getPVCalculation(latitude, longitude, capacityKwp, 14, tiltField, azimuthField, false, pvTech);
      
      if (result && result.outputs?.monthly?.fixed && result.outputs.monthly.fixed.length === 12) {
        const monthly = result.outputs.monthly.fixed.map((m) => ({
          month: m.month,
          productionAC_kWh: m.E_m,
          irradiationPOA_kWhm2: m.H_i_m,
          temperature: 25, // PVGIS PVcalc no devuelve T2m mensual directamente
        }));
        setPvgisMonthly(monthly);
        toast.success('Datos PVGIS cargados correctamente');
      } else {
        toast.error('No se obtuvieron datos mensuales de PVGIS');
      }
    } catch (err: any) {
      toast.error(`Error PVGIS: ${err.message || 'Error desconocido'}`);
    } finally {
      setPvgisLoading(false);
    }
  }, [latitude, longitude, tiltField, azimuthField, panelConfig, selectedTech]);

  const handleConsultPVWatts = useCallback(async () => {
    setPvwattsLoading(true);
    try {
      const capacityKwp = (panelConfig.powerRating * panelConfig.quantity) / 1000;
      const result = await getPVWattsCalculation({
        lat: latitude,
        lon: longitude,
        system_capacity: capacityKwp,
        tilt: tiltField,
        azimuth: azimuthField + 180, // PVWatts usa 180=Sur
        losses: 14,
        array_type: 1,
        module_type: 0,
      });

      if (result && result.monthly && result.monthly.length === 12) {
        const monthly = result.monthly.map((m) => ({
          month: m.month,
          ac_kWh: m.ac_kWh,
          dc_kWh: m.dc_kWh,
          poa_kWhm2: m.poa_kWhm2,
          tamb_C: m.tamb_C,
          tcell_C: m.tcell_C,
        }));
        setPvwattsMonthly(monthly);
        toast.success('Datos PVWatts cargados correctamente');
      } else {
        toast.error('No se obtuvieron datos mensuales de PVWatts');
      }
    } catch (err: any) {
      toast.error(`Error PVWatts: ${err.message || 'Error desconocido'}`);
    } finally {
      setPvwattsLoading(false);
    }
  }, [latitude, longitude, tiltField, azimuthField, panelConfig]);

  const handleMonthlyRealChange = useCallback((monthIdx: number, value: string) => {
    setMonthlyReal(prev => {
      const next = [...prev];
      next[monthIdx] = value === '' ? null : parseFloat(value);
      return next;
    });
  }, []);

  const handleExportCSV = useCallback(() => {
    const headers = ['Mes', 'Mulcue AC (kWh)', 'PVGIS AC (kWh)', 'PVWatts AC (kWh)', 'Esperado Prom (kWh)', 'Real (kWh)', 'Δ (kWh)', 'Δ (%)'];
    const rows = monthlyExpected.map((m, i) => {
      const real = monthlyReal[i];
      const delta = real !== null ? real - m.expected_ac_kWh : '';
      const deltaPct = real !== null && m.expected_ac_kWh > 0 ? (((real - m.expected_ac_kWh) / m.expected_ac_kWh) * 100).toFixed(1) : '';
      return [
        MONTH_FULL[i],
        m.mulcue_ac_kWh.toFixed(1),
        m.pvgis_ac_kWh?.toFixed(1) ?? '',
        m.pvwatts_ac_kWh?.toFixed(1) ?? '',
        m.expected_ac_kWh.toFixed(1),
        real?.toFixed(1) ?? '',
        typeof delta === 'number' ? delta.toFixed(1) : '',
        deltaPct,
      ].join(',');
    });
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `diagnostico_bipv_${siteName.replace(/\s+/g, '_')}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('CSV exportado');
  }, [monthlyExpected, monthlyReal, siteName]);

  const handleExportPDF = useCallback(async () => {
    try {
      // Capturar gráfico radar como imagen
      let radarImageBase64: string | undefined;
      if (radarChartRef.current) {
        const canvas = await html2canvas(radarChartRef.current, {
          backgroundColor: '#ffffff',
          scale: 2,
          useCORS: true,
          logging: false,
        });
        radarImageBase64 = canvas.toDataURL('image/png');
      }

      const reportData: BIPVReportData = {
        panelConfig,
        siteConfig,
        monthlyExpected,
        annualSummary,
        comparison,
        performanceAlert,
        ghiAnnual,
        ambientTemp,
        regionName: detectedRegion.label || 'Colombia',
        hasPVGIS: pvgisMonthly !== null,
        hasPVWatts: pvwattsMonthly !== null,
        radarImageBase64,
      };
      generateBIPVReport(reportData);
      toast.success('PDF generado correctamente');
    } catch (err: any) {
      toast.error(`Error al generar PDF: ${err.message}`);
    }
  }, [panelConfig, siteConfig, monthlyExpected, annualSummary, comparison, performanceAlert, ghiAnnual, ambientTemp, detectedRegion, pvgisMonthly, pvwattsMonthly]);

  const toggleSection = (section: string) => {
    setExpandedSection(prev => prev === section ? null : section);
  };

  const installConfig = INSTALLATION_CONFIGS.find(c => c.id === installationType) || INSTALLATION_CONFIGS[0];
  const degradationFactor = Math.pow(1 - (selectedTech.degradationAnnual ?? 0.5) / 100, yearsInstalled);
  const capacityKwp = (selectedTech.pmax * degradationFactor * panelQuantity) / 1000;
  const sourcesCount = 1 + (pvgisMonthly ? 1 : 0) + (pvwattsMonthly ? 1 : 0);

  // Datos para gráfico
  const chartData = monthlyExpected.map((m, i) => ({
    name: m.monthName,
    'Mulcue-Llanos': m.mulcue_ac_kWh,
    'PVGIS': m.pvgis_ac_kWh ?? undefined,
    'PVWatts': m.pvwatts_ac_kWh ?? undefined,
    'Real': monthlyReal[i] ?? undefined,
  }));

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-2">
          <ClipboardCheck className="w-8 h-8 text-amber-600" />
          <h2 className="text-2xl font-bold text-gray-900">Diagnóstico BIPV — Sistemas Instalados</h2>
        </div>
        <p className="text-gray-600">
          Evalúa el rendimiento de sistemas fotovoltaicos ya instalados comparando la producción real
          contra la esperada según tres modelos: <strong>Mulcue-Llanos</strong>, <strong>PVGIS</strong> y <strong>PVWatts</strong>.
        </p>
        <div className="mt-3 flex flex-wrap gap-3 text-sm">
          <span className="px-3 py-1 bg-amber-100 text-amber-800 rounded-full font-medium">IEC 61724</span>
          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium">Mulcue-Llanos</span>
          <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full font-medium">PVGIS JRC</span>
          <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full font-medium">PVWatts NREL</span>
        </div>
      </div>

      {/* SECCIÓN 1: PANEL */}
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <button
          onClick={() => toggleSection('panel')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center gap-3">
            <PanelTop className="w-5 h-5 text-blue-600" />
            <span className="font-semibold text-gray-900">1. Especificaciones del Panel</span>
            <span className="text-sm text-gray-500">— {selectedTech.name} × {panelQuantity} = {capacityKwp.toFixed(2)} kWp</span>
          </div>
          {expandedSection === 'panel' ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
        {expandedSection === 'panel' && (
          <div className="p-4 space-y-4">
            <PanelTechSelector
              selectedTech={selectedTech}
              onSelectTech={setSelectedTech}
              yearsFromInstall={yearsInstalled}
              onYearsChange={setYearsInstalled}
              detectedRegionInfo={detectedRegion}
              savedPanels={savedPanelsTech}
              onSavePanel={handleSavePanelPersist}
              onDeletePanel={handleDeletePanelPersist}
            />
            {/* Indicador de paneles guardados */}
            {panelCount > 0 && (
              <div className="mt-2 flex items-center gap-2 text-sm text-gray-600">
                <Shield className="w-4 h-4 text-green-500" />
                <span>{panelCount} panel{panelCount !== 1 ? 'es' : ''} personalizado{panelCount !== 1 ? 's' : ''} guardado{panelCount !== 1 ? 's' : ''}</span>
                {isSyncing && <span className="text-blue-500 text-xs">(sincronizando...)</span>}
              </div>
            )}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Cantidad de Paneles</label>
                <Input
                  type="number"
                  min={1}
                  max={10000}
                  value={panelQuantity}
                  onChange={e => setPanelQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Años Instalado</label>
                <Input
                  type="number"
                  min={0}
                  max={30}
                  value={yearsInstalled}
                  onChange={e => setYearsInstalled(Math.max(0, parseInt(e.target.value) || 0))}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Capacidad Instalada</label>
                <div className="mt-1 px-3 py-2 bg-blue-50 border border-blue-200 rounded-md text-blue-800 font-mono font-bold">
                  {capacityKwp.toFixed(2)} kWp
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Degradación Acumulada</label>
                <div className="mt-1 px-3 py-2 bg-orange-50 border border-orange-200 rounded-md text-orange-800 font-mono font-bold">
                  {((1 - degradationFactor) * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* SECCIÓN 2: UBICACIÓN Y CONFIGURACIÓN */}
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <button
          onClick={() => toggleSection('site')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center gap-3">
            <MapPin className="w-5 h-5 text-green-600" />
            <span className="font-semibold text-gray-900">2. Ubicación y Configuración de Campo</span>
            <span className="text-sm text-gray-500">— {latitude.toFixed(4)}°, {longitude.toFixed(4)}° | Tilt: {tiltField}° | Az: {azimuthField}°</span>
          </div>
          {expandedSection === 'site' ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
        {expandedSection === 'site' && (
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Nombre del Sitio</label>
                <Input value={siteName} onChange={e => setSiteName(e.target.value)} className="mt-1" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Latitud (°N)</label>
                <Input type="number" step="0.0001" value={latitude} onChange={e => setLatitude(parseFloat(e.target.value) || 0)} className="mt-1" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Longitud (°E)</label>
                <Input type="number" step="0.0001" value={longitude} onChange={e => setLongitude(parseFloat(e.target.value) || 0)} className="mt-1" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Región Detectada</label>
                <div className="mt-1 px-3 py-2 bg-green-50 border border-green-200 rounded-md text-green-800 font-medium text-sm">
                  {detectedRegion.label} (FI: {regionFI?.fi ?? 0.95})
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Inclinación en Campo (°)</label>
                <Input type="number" min={0} max={90} value={tiltField} onChange={e => setTiltField(Math.max(0, Math.min(90, parseInt(e.target.value) || 0)))} className="mt-1" />
                <Slider value={[tiltField]} onValueChange={([v]) => setTiltField(v)} min={0} max={90} step={1} className="mt-2" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Azimut en Campo (°)</label>
                <Input type="number" min={-180} max={180} value={azimuthField} onChange={e => setAzimuthField(parseInt(e.target.value) || 0)} className="mt-1" />
                <p className="text-xs text-gray-500 mt-1">0°=Sur, -90°=Este, 90°=Oeste</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Factor de Sombreado (FS)</label>
                <Input type="number" min={0} max={1} step={0.05} value={shadowFactor} onChange={e => setShadowFactor(Math.max(0, Math.min(1, parseFloat(e.target.value) || 0)))} className="mt-1" />
                <Slider value={[shadowFactor * 100]} onValueChange={([v]) => setShadowFactor(v / 100)} min={0} max={100} step={5} className="mt-2" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Tipo de Instalación</label>
                <select
                  value={installationType}
                  onChange={e => setInstallationType(e.target.value)}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  {INSTALLATION_CONFIGS.map(c => (
                    <option key={c.id} value={c.id}>{c.icon} {c.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">GHI Anual (kWh/m²/año)</label>
                <Input
                  type="number"
                  min={500}
                  max={3000}
                  value={ghiOverride ?? ''}
                  placeholder={`Auto: ${estimateGHIFromLatitude(latitude)}`}
                  onChange={e => setGhiOverride(e.target.value === '' ? null : parseFloat(e.target.value))}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">Dejar vacío para estimación automática</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">T° Ambiente Promedio (°C)</label>
                <Input
                  type="number"
                  min={-10}
                  max={50}
                  value={tempOverride ?? ''}
                  placeholder={`Auto: ${regionFI?.avgTemp ?? 25}°C`}
                  onChange={e => setTempOverride(e.target.value === '' ? null : parseFloat(e.target.value))}
                  className="mt-1"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* SECCIÓN 3: PRODUCCIÓN ESPERADA */}
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <button
          onClick={() => toggleSection('expected')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Calculator className="w-5 h-5 text-purple-600" />
            <span className="font-semibold text-gray-900">3. Producción Esperada</span>
            <span className="text-sm text-gray-500">— {annualSummary.expected_annual_kWh.toFixed(0)} kWh/año ({sourcesCount} fuente{sourcesCount > 1 ? 's' : ''})</span>
          </div>
          {expandedSection === 'expected' ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
        {expandedSection === 'expected' && (
          <div className="p-4 space-y-4">
            {/* Botones de consulta satelital */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleConsultPVGIS}
                disabled={pvgisLoading}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                {pvgisLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
                {pvgisLoading ? 'Consultando PVGIS...' : pvgisMonthly ? '✓ PVGIS Cargado — Reconsultar' : 'Consultar PVGIS'}
              </button>
              <button
                onClick={handleConsultPVWatts}
                disabled={pvwattsLoading}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {pvwattsLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Satellite className="w-4 h-4" />}
                {pvwattsLoading ? 'Consultando PVWatts...' : pvwattsMonthly ? '✓ PVWatts Cargado — Reconsultar' : 'Consultar PVWatts'}
              </button>
            </div>

            {/* Resumen anual */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-center">
                <p className="text-xs text-blue-600 font-medium">Mulcue-Llanos</p>
                <p className="text-lg font-bold text-blue-800">{annualSummary.mulcue_annual_kWh.toFixed(0)} kWh</p>
                <p className="text-xs text-blue-500">PR: {(annualSummary.mulcue_pr * 100).toFixed(1)}%</p>
              </div>
              {annualSummary.pvgis_annual_kWh !== null && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-center">
                  <p className="text-xs text-green-600 font-medium">PVGIS</p>
                  <p className="text-lg font-bold text-green-800">{annualSummary.pvgis_annual_kWh.toFixed(0)} kWh</p>
                  <p className="text-xs text-green-500">SY: {annualSummary.pvgis_specificYield?.toFixed(0)} kWh/kWp</p>
                </div>
              )}
              {annualSummary.pvwatts_annual_kWh !== null && (
                <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-center">
                  <p className="text-xs text-indigo-600 font-medium">PVWatts</p>
                  <p className="text-lg font-bold text-indigo-800">{annualSummary.pvwatts_annual_kWh.toFixed(0)} kWh</p>
                  <p className="text-xs text-indigo-500">SY: {annualSummary.pvwatts_specificYield?.toFixed(0)} kWh/kWp</p>
                </div>
              )}
              <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg text-center">
                <p className="text-xs text-purple-600 font-medium">Promedio Esperado</p>
                <p className="text-lg font-bold text-purple-800">{annualSummary.expected_annual_kWh.toFixed(0)} kWh</p>
                <p className="text-xs text-purple-500">SY: {annualSummary.expected_specificYield.toFixed(0)} kWh/kWp</p>
              </div>
              <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-center">
                <p className="text-xs text-gray-600 font-medium">Capacidad</p>
                <p className="text-lg font-bold text-gray-800">{annualSummary.installedCapacity_kWp.toFixed(2)} kWp</p>
                <p className="text-xs text-gray-500">{panelQuantity} paneles</p>
              </div>
            </div>

            {/* Tabla mensual */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="px-3 py-2 text-left font-medium text-gray-700 border">Mes</th>
                    <th className="px-3 py-2 text-right font-medium text-blue-700 border">Mulcue (kWh)</th>
                    <th className="px-3 py-2 text-right font-medium text-green-700 border">PVGIS (kWh)</th>
                    <th className="px-3 py-2 text-right font-medium text-indigo-700 border">PVWatts (kWh)</th>
                    <th className="px-3 py-2 text-right font-medium text-purple-700 border">Esperado (kWh)</th>
                    <th className="px-3 py-2 text-right font-medium text-gray-700 border">PR Mulcue</th>
                    <th className="px-3 py-2 text-right font-medium text-orange-700 border">T° Celda (°C)</th>
                  </tr>
                </thead>
                <tbody>
                  {monthlyExpected.map(m => (
                    <tr key={m.month} className="hover:bg-gray-50">
                      <td className="px-3 py-1.5 font-medium border">{m.monthName}</td>
                      <td className="px-3 py-1.5 text-right font-mono border">{m.mulcue_ac_kWh.toFixed(1)}</td>
                      <td className="px-3 py-1.5 text-right font-mono border">{m.pvgis_ac_kWh?.toFixed(1) ?? '—'}</td>
                      <td className="px-3 py-1.5 text-right font-mono border">{m.pvwatts_ac_kWh?.toFixed(1) ?? '—'}</td>
                      <td className="px-3 py-1.5 text-right font-mono font-bold border">{m.expected_ac_kWh.toFixed(1)}</td>
                      <td className="px-3 py-1.5 text-right font-mono border">{(m.mulcue_pr * 100).toFixed(1)}%</td>
                      <td className="px-3 py-1.5 text-right font-mono border">{m.mulcue_cellTemp.toFixed(1)}</td>
                    </tr>
                  ))}
                  <tr className="bg-gray-100 font-bold">
                    <td className="px-3 py-2 border">ANUAL</td>
                    <td className="px-3 py-2 text-right font-mono border">{annualSummary.mulcue_annual_kWh.toFixed(0)}</td>
                    <td className="px-3 py-2 text-right font-mono border">{annualSummary.pvgis_annual_kWh?.toFixed(0) ?? '—'}</td>
                    <td className="px-3 py-2 text-right font-mono border">{annualSummary.pvwatts_annual_kWh?.toFixed(0) ?? '—'}</td>
                    <td className="px-3 py-2 text-right font-mono border">{annualSummary.expected_annual_kWh.toFixed(0)}</td>
                    <td className="px-3 py-2 text-right font-mono border">{(annualSummary.mulcue_pr * 100).toFixed(1)}%</td>
                    <td className="px-3 py-2 text-right font-mono border">—</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Gráfico */}
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis label={{ value: 'kWh', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Mulcue-Llanos" fill="#3b82f6" opacity={0.7} />
                  {pvgisMonthly && <Bar dataKey="PVGIS" fill="#22c55e" opacity={0.7} />}
                  {pvwattsMonthly && <Bar dataKey="PVWatts" fill="#6366f1" opacity={0.7} />}
                  {monthlyReal.some(v => v !== null) && <Line type="monotone" dataKey="Real" stroke="#dc2626" strokeWidth={3} dot={{ r: 5 }} />}
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* SECCIÓN 4: MEDICIONES DE CAMPO Y DIAGNÓSTICO */}
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <button
          onClick={() => toggleSection('field')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Target className="w-5 h-5 text-red-600" />
            <span className="font-semibold text-gray-900">4. Mediciones de Campo y Diagnóstico</span>
            {comparison && (
              <span className={`text-sm font-medium px-2 py-0.5 rounded-full`} style={{ backgroundColor: comparison.healthColor + '20', color: comparison.healthColor }}>
                Salud: {comparison.healthScore}/100 — {comparison.healthStatus.toUpperCase()}
              </span>
            )}
          </div>
          {expandedSection === 'field' ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
        {expandedSection === 'field' && (
          <div className="p-4 space-y-4">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
              <strong>Instrucciones:</strong> Ingrese la producción real mensual medida en campo (kWh AC del inversor o medidor).
              También puede ingresar solo el total anual si no tiene datos mensuales.
            </div>

            {/* Entrada de producción real mensual */}
            <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
              {MONTHS.map((month, i) => (
                <div key={i}>
                  <label className="text-xs font-medium text-gray-600">{month} (kWh)</label>
                  <Input
                    type="number"
                    min={0}
                    step={0.1}
                    value={monthlyReal[i] ?? ''}
                    placeholder="—"
                    onChange={e => handleMonthlyRealChange(i, e.target.value)}
                    className="mt-1 text-sm"
                  />
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Total Anual Real (kWh)</label>
                <Input
                  type="number"
                  min={0}
                  value={annualRealOverride ?? ''}
                  placeholder={monthlyReal.some(v => v !== null) ? `Suma: ${monthlyReal.reduce<number>((s, v) => s + (v ?? 0), 0).toFixed(0)}` : 'Ingrese total anual'}
                  onChange={e => setAnnualRealOverride(e.target.value === '' ? null : parseFloat(e.target.value))}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">Dejar vacío para sumar los mensuales</p>
              </div>
              <div className="flex items-end gap-2">
                <button
                  onClick={handleExportCSV}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  CSV
                </button>
                <button
                  onClick={handleExportPDF}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  PDF
                </button>
              </div>
            </div>

            {/* Resultados de comparación */}
            {comparison && (
              <div className="space-y-4 mt-6">
                {/* Health Score */}
                <div className="flex items-center gap-6 p-4 rounded-xl" style={{ backgroundColor: comparison.healthColor + '10', border: `2px solid ${comparison.healthColor}` }}>
                  <div className="flex-shrink-0">
                    <div
                      className="w-20 h-20 rounded-full flex items-center justify-center text-white font-bold text-2xl"
                      style={{ backgroundColor: comparison.healthColor }}
                    >
                      {comparison.healthScore}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold" style={{ color: comparison.healthColor }}>
                      Estado: {comparison.healthStatus.toUpperCase()}
                    </h3>
                    <p className="text-gray-600 text-sm mt-1">
                      {comparison.annual.delta_pct !== null && (
                        <>
                          Desviación anual: <strong>{comparison.annual.delta_pct > 0 ? '+' : ''}{comparison.annual.delta_pct.toFixed(1)}%</strong>
                          {comparison.annual.delta_kWh !== null && <> ({comparison.annual.delta_kWh > 0 ? '+' : ''}{comparison.annual.delta_kWh.toFixed(0)} kWh)</>}
                        </>
                      )}
                    </p>
                    {comparison.annual.pr_real !== null && (
                      <p className="text-gray-600 text-sm">
                        PR Real: <strong>{(comparison.annual.pr_real * 100).toFixed(1)}%</strong> vs PR Esperado: <strong>{(comparison.annual.pr_expected * 100).toFixed(1)}%</strong>
                      </p>
                    )}
                    <div className="flex flex-wrap gap-4 mt-2">
                      {comparison.annual.pr_conventional !== null && (
                        <div className="px-3 py-1.5 rounded-lg" style={{ backgroundColor: comparison.annual.pr_conventional >= 0.70 ? '#dcfce7' : comparison.annual.pr_conventional >= 0.55 ? '#fef9c3' : '#fecaca' }}>
                          <p className="text-xs font-medium text-gray-600">PR Convencional</p>
                          <p className="text-lg font-bold" style={{ color: comparison.annual.pr_conventional >= 0.70 ? '#16a34a' : comparison.annual.pr_conventional >= 0.55 ? '#ca8a04' : '#dc2626' }}>
                            {(comparison.annual.pr_conventional * 100).toFixed(1)}%
                          </p>
                          <p className="text-[10px] text-gray-500">E<sub>inv</sub> / P<sub>m</sub> (irradiancia)</p>
                        </div>
                      )}
                      {comparison.annual.pr_corrected !== null && (
                        <div className="px-3 py-1.5 rounded-lg" style={{ backgroundColor: comparison.annual.pr_corrected >= 0.85 ? '#dcfce7' : comparison.annual.pr_corrected >= 0.70 ? '#fef9c3' : '#fecaca' }}>
                          <p className="text-xs font-medium text-gray-600">PR Corregido</p>
                          <p className="text-lg font-bold" style={{ color: comparison.annual.pr_corrected >= 0.85 ? '#16a34a' : comparison.annual.pr_corrected >= 0.70 ? '#ca8a04' : '#dc2626' }}>
                            {(comparison.annual.pr_corrected * 100).toFixed(1)}%
                          </p>
                          <p className="text-[10px] text-gray-500">E<sub>inv</sub> / E<sub>esperada</sub> (modelos)</p>
                        </div>
                      )}
                      <div className="px-3 py-1.5 rounded-lg bg-gray-100">
                        <p className="text-xs font-medium text-gray-600">P<sub>m</sub> Anual</p>
                        <p className="text-lg font-bold text-gray-800">{comparison.annual.pm_annual_kWh.toFixed(0)} kWh</p>
                        <p className="text-[10px] text-gray-500">P<sub>ref</sub> × N × (G/G<sub>ref</sub>)</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-4 ml-auto">
                    {comparison.metrics.map((m, i) => (
                      <div key={i} className="text-center">
                        <p className="text-xs text-gray-500">{m.label}</p>
                        <p className="text-lg font-bold" style={{ color: m.color }}>{m.value.toFixed(1)}{m.unit}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Tabla comparativa mensual */}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="px-3 py-2 text-left font-medium border">Mes</th>
                        <th className="px-3 py-2 text-right font-medium border">P<sub>m</sub> (kWh)</th>
                        <th className="px-3 py-2 text-right font-medium border">Esperado (kWh)</th>
                        <th className="px-3 py-2 text-right font-medium border">Real Inv. (kWh)</th>
                        <th className="px-3 py-2 text-right font-medium border">Δ (%)</th>
                        <th className="px-3 py-2 text-right font-medium border bg-blue-50">PR Conv.</th>
                        <th className="px-3 py-2 text-right font-medium border bg-green-50">PR Corr.</th>
                        <th className="px-3 py-2 text-center font-medium border">Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.monthly.map(m => (
                        <tr key={m.month} className="hover:bg-gray-50">
                          <td className="px-3 py-1.5 font-medium border">{m.monthName}</td>
                          <td className="px-3 py-1.5 text-right font-mono border text-gray-500">{m.pm_kWh.toFixed(1)}</td>
                          <td className="px-3 py-1.5 text-right font-mono border">{m.expected_kWh.toFixed(1)}</td>
                          <td className="px-3 py-1.5 text-right font-mono border">{m.real_kWh?.toFixed(1) ?? '—'}</td>
                          <td className="px-3 py-1.5 text-right font-mono border" style={{ color: m.color }}>
                            {m.delta_pct !== null ? `${m.delta_pct > 0 ? '+' : ''}${m.delta_pct.toFixed(1)}%` : '—'}
                          </td>
                          <td className="px-3 py-1.5 text-right font-mono border bg-blue-50" style={{ color: m.pr_conventional !== null ? (m.pr_conventional >= 0.70 ? '#16a34a' : m.pr_conventional >= 0.55 ? '#ca8a04' : '#dc2626') : '#9ca3af' }}>
                            {m.pr_conventional !== null ? `${(m.pr_conventional * 100).toFixed(1)}%` : '—'}
                          </td>
                          <td className="px-3 py-1.5 text-right font-mono border bg-green-50" style={{ color: m.pr_corrected !== null ? (m.pr_corrected >= 0.85 ? '#16a34a' : m.pr_corrected >= 0.70 ? '#ca8a04' : '#dc2626') : '#9ca3af' }}>
                            {m.pr_corrected !== null ? `${(m.pr_corrected * 100).toFixed(1)}%` : '—'}
                          </td>
                          <td className="px-3 py-1.5 text-center border">
                            {m.real_kWh !== null && (
                              <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: m.color }} />
                            )}
                          </td>
                        </tr>
                      ))}
                      {/* Fila de totales anuales */}
                      <tr className="bg-gray-100 font-bold">
                        <td className="px-3 py-2 border">ANUAL</td>
                        <td className="px-3 py-2 text-right font-mono border text-gray-600">{comparison.annual.pm_annual_kWh.toFixed(0)}</td>
                        <td className="px-3 py-2 text-right font-mono border">{comparison.annual.expected_kWh.toFixed(0)}</td>
                        <td className="px-3 py-2 text-right font-mono border">{comparison.annual.real_kWh?.toFixed(0) ?? '—'}</td>
                        <td className="px-3 py-2 text-right font-mono border" style={{ color: comparison.healthColor }}>
                          {comparison.annual.delta_pct !== null ? `${comparison.annual.delta_pct > 0 ? '+' : ''}${comparison.annual.delta_pct.toFixed(1)}%` : '—'}
                        </td>
                        <td className="px-3 py-2 text-right font-mono border bg-blue-50" style={{ color: comparison.annual.pr_conventional !== null ? (comparison.annual.pr_conventional >= 0.70 ? '#16a34a' : comparison.annual.pr_conventional >= 0.55 ? '#ca8a04' : '#dc2626') : '#9ca3af' }}>
                          {comparison.annual.pr_conventional !== null ? `${(comparison.annual.pr_conventional * 100).toFixed(1)}%` : '—'}
                        </td>
                        <td className="px-3 py-2 text-right font-mono border bg-green-50" style={{ color: comparison.annual.pr_corrected !== null ? (comparison.annual.pr_corrected >= 0.85 ? '#16a34a' : comparison.annual.pr_corrected >= 0.70 ? '#ca8a04' : '#dc2626') : '#9ca3af' }}>
                          {comparison.annual.pr_corrected !== null ? `${(comparison.annual.pr_corrected * 100).toFixed(1)}%` : '—'}
                        </td>
                        <td className="px-3 py-2 text-center border">
                          <span className="inline-block w-4 h-4 rounded-full" style={{ backgroundColor: comparison.healthColor }} />
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Gráfico Radar Comparativo */}
                {monthlyReal.some(v => v !== null) && (
                  <div ref={radarChartRef} className="mt-6 p-4 bg-white border border-gray-200 rounded-xl">
                    <h3 className="text-lg font-bold text-gray-900 mb-1 flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-indigo-600" />
                      Radar de Producción Mensual — Patrón Estacional
                    </h3>
                    <p className="text-xs text-gray-500 mb-4">
                      Valores normalizados (% del máximo mensual). Identifique meses donde la producción real se aleja de las fuentes esperadas.
                    </p>
                    <div className="h-96">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart
                          data={(() => {
                            const maxVal = Math.max(
                              ...monthlyExpected.map(m => m.mulcue_ac_kWh),
                              ...(pvgisMonthly ? monthlyExpected.map(m => m.pvgis_ac_kWh ?? 0) : [0]),
                              ...(pvwattsMonthly ? monthlyExpected.map(m => m.pvwatts_ac_kWh ?? 0) : [0]),
                              ...monthlyReal.map(v => v ?? 0),
                            ) || 1;
                            return MONTHS.map((name, i) => ({
                              month: name,
                              'Mulcue-Llanos': (monthlyExpected[i]?.mulcue_ac_kWh ?? 0) / maxVal * 100,
                              ...(pvgisMonthly ? { 'PVGIS': ((monthlyExpected[i]?.pvgis_ac_kWh ?? 0) / maxVal * 100) } : {}),
                              ...(pvwattsMonthly ? { 'PVWatts': ((monthlyExpected[i]?.pvwatts_ac_kWh ?? 0) / maxVal * 100) } : {}),
                              'Real (Inversor)': ((monthlyReal[i] ?? 0) / maxVal * 100),
                            }));
                          })()}
                        >
                          <PolarGrid stroke="#e5e7eb" />
                          <PolarAngleAxis dataKey="month" tick={{ fontSize: 11, fill: '#374151' }} />
                          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 9 }} />
                          <Radar name="Mulcue-Llanos" dataKey="Mulcue-Llanos" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.1} strokeWidth={2} />
                          {pvgisMonthly && <Radar name="PVGIS" dataKey="PVGIS" stroke="#22c55e" fill="#22c55e" fillOpacity={0.1} strokeWidth={2} />}
                          {pvwattsMonthly && <Radar name="PVWatts" dataKey="PVWatts" stroke="#6366f1" fill="#6366f1" fillOpacity={0.1} strokeWidth={2} />}
                          <Radar name="Real (Inversor)" dataKey="Real (Inversor)" stroke="#dc2626" fill="#dc2626" fillOpacity={0.15} strokeWidth={3} dot={{ r: 4 }} />
                          <Legend wrapperStyle={{ fontSize: 12 }} />
                          <Tooltip
                            formatter={(value: number) => `${value.toFixed(1)}%`}
                            labelFormatter={(label) => `Mes: ${label}`}
                          />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                    {/* Indicador de meses críticos */}
                    {comparison && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        <span className="text-xs font-medium text-gray-600">Meses críticos (Δ &gt; 15%):</span>
                        {comparison.monthly
                          .filter(m => m.delta_pct !== null && Math.abs(m.delta_pct) > 15)
                          .map(m => (
                            <span key={m.month} className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">
                              {m.monthName}: {m.delta_pct! > 0 ? '+' : ''}{m.delta_pct!.toFixed(0)}%
                            </span>
                          ))
                        }
                        {comparison.monthly.filter(m => m.delta_pct !== null && Math.abs(m.delta_pct) > 15).length === 0 && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-medium">
                            Ninguno — Sistema operando dentro de tolerancia
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Panel de diagnóstico de rendimiento */}
                {performanceAlert && (
                  <div className="mt-4">
                    <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-amber-500" />
                      Diagnóstico de Rendimiento
                    </h3>
                    <PerformanceAlertPanel alert={performanceAlert} />
                  </div>
                )}
              </div>
            )}

            {!comparison && (
              <div className="text-center py-8 text-gray-400">
                <Target className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p className="text-lg font-medium">Ingrese datos de producción real para ver el diagnóstico</p>
                <p className="text-sm mt-1">Complete al menos el total anual o algunos meses</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
