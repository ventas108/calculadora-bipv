import { useState, useCallback, useMemo, useRef } from 'react';
import { toast } from 'sonner';
import { Globe, Sun, Zap, TrendingUp, Download, Loader2, MapPin, Thermometer, Wind, ArrowRight } from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ComposedChart, AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Radar,
} from 'recharts';
import {
  getMonthlyRadiation,
  getPVCalculation,
  getHorizonProfile,
  getPVGISHourlyData,
  classifyAnnualIrradiance,
  MONTH_NAMES,
  PVGISMonthlyRadResult,
  PVGISPVCalcResult,
} from '@/lib/pvgisApi';
import {
  PanelTechnology,
  DEFAULT_PANEL_TECHNOLOGIES,
  calculateCorrectedProduction,
} from '@/lib/panelTechnologies';
import PanelTechSelector from './PanelTechSelector';
import { detectColombianRegion, ColombianRegionKey } from '@/lib/colombianRegions';
import type { RegionalCompatibility } from '@/lib/panelTechnologies';

/**
 * Datos que se envían del PVGISAnalyzer al Simulador de Energía
 * PVGIS reporta producción AC (post-inversor, post-pérdidas del sistema)
 */
export interface PVGISToSimulatorData {
  // Configuración del sistema PVGIS
  latitude: number;
  longitude: number;
  tilt: number; // grados
  azimuth: number; // grados
  peakPowerKwp: number; // kWp
  systemLoss: number; // %
  technology: string; // pvtechchoice
  panelName: string; // nombre del panel seleccionado
  // Producción anual
  annualProductionAC: number; // kWh/año AC (PVGIS estándar)
  annualProductionCorrected: number; // kWh/año AC (corregido con panel real)
  annualIrradiationPOA: number; // kWh/m²/año en plano inclinado
  correctionFactor: number; // factor de corrección promedio (0-1+)
  // Datos mensuales
  monthlyData: {
    month: number; // 1-12
    productionAC_kWh: number; // kWh AC mensual (PVGIS)
    productionCorrectedAC_kWh: number; // kWh AC mensual (corregido)
    irradiationPOA_kWhm2: number; // kWh/m² mensual en plano
    temperature: number; // °C ambiente mensual
  }[];
  // Datos horarios para PR_T IEC 61724-1:2021 (8760 registros)
  hourlyRecords?: {
    month: number;
    poa_Wm2: number;
    tamb_C: number;
    wspd_ms: number;
    ac_W?: number;
  }[];
  // Fuente de datos
  radiationDB: string;
  yearMin: number;
  yearMax: number;
  // Área disponible para auto-cálculo de paneles en el Simulador
  availableArea?: number; // m²
}

interface PVGISAnalyzerProps {
  initialLat?: number;
  initialLng?: number;
  cityName?: string;
  onSendToSimulator?: (data: PVGISToSimulatorData) => void;
  /** Fachadas detectadas del modelo 3D para importar área */
  modelFacades?: import('@/lib/buildingModelImporter').DetectedFacade[];
}

/**
 * PVGISAnalyzer - Componente para consultar datos reales de PVGIS.
 * 
 * NOTA IMPORTANTE: Este componente usa CSS display:none/block para ocultar/mostrar
 * secciones en lugar de renderizado condicional de React ({condition && <Component/>}).
 * Esto previene el error "insertBefore" de React que ocurre cuando extensiones del
 * navegador (como Google Translate) manipulan el DOM.
 */
export default function PVGISAnalyzer({ initialLat, initialLng, cityName, onSendToSimulator, modelFacades }: PVGISAnalyzerProps) {
  const [lat, setLat] = useState(initialLat?.toString() || '6.2518');
  const [lng, setLng] = useState(initialLng?.toString() || '-75.5636');

  // Auto-detección de región climática colombiana
  const detectedRegion = useMemo(() => {
    const latNum = parseFloat(lat) || 0;
    const lngNum = parseFloat(lng) || 0;
    return detectColombianRegion(latNum, lngNum);
  }, [lat, lng]);
  const [regionOverride, setRegionOverride] = useState<ColombianRegionKey | null>(null);
  const activeRegion: keyof Omit<RegionalCompatibility, 'notes'> = regionOverride ?? detectedRegion.region;
  const [angle, setAngle] = useState(10);
  const [aspect, setAspect] = useState(0);
  const [peakPower, setPeakPower] = useState(1);
  const [loss, setLoss] = useState(14);
  const [loading, setLoading] = useState(false);
  const [monthlyData, setMonthlyData] = useState<PVGISMonthlyRadResult | null>(null);
  const [pvCalcData, setPvCalcData] = useState<PVGISPVCalcResult | null>(null);
  const [horizonData, setHorizonData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'radiation' | 'pvcalc' | 'horizon'>('radiation');

  // Estado de tecnología del panel
  const [selectedTech, setSelectedTech] = useState<PanelTechnology>(DEFAULT_PANEL_TECHNOLOGIES[0]);
  const [yearsFromInstall, setYearsFromInstall] = useState(0);

  // Refs para evitar problemas de DOM con Recharts
  const radiationChartRef = useRef<HTMLDivElement>(null);
  const pvCalcChartRef = useRef<HTMLDivElement>(null);
  const horizonChartRef = useRef<HTMLDivElement>(null);

  // Consultar radiación mensual
  const fetchMonthlyRadiation = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMonthlyRadiation(parseFloat(lat), parseFloat(lng), angle);
      setMonthlyData(data);
      toast.success('Datos de radiación mensual obtenidos de PVGIS');
    } catch (err: any) {
      const msg = err.message || 'Error al consultar PVGIS';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [lat, lng, angle]);

  // Consultar cálculo PV (ahora usa pvtechchoice y mountingplace del panel seleccionado)
  const fetchPVCalc = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPVCalculation(
        parseFloat(lat), parseFloat(lng), peakPower, loss, angle, aspect,
        false,
        selectedTech.pvgisTechchoice,
        selectedTech.pvgisMountingplace,
      );
      setPvCalcData(data);
      toast.success(`Cálculo PV obtenido (${selectedTech.pvgisTechchoice} / ${selectedTech.pvgisMountingplace})`);
    } catch (err: any) {
      const msg = err.message || 'Error al consultar PVGIS';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [lat, lng, peakPower, loss, angle, aspect, selectedTech]);

  // Consultar perfil de horizonte
  const fetchHorizon = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getHorizonProfile(parseFloat(lat), parseFloat(lng));
      setHorizonData(data);
      toast.success('Perfil de horizonte obtenido de PVGIS');
    } catch (err: any) {
      const msg = err.message || 'Error al consultar PVGIS';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [lat, lng]);

  // Ejecutar todas las consultas
  const fetchAllData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [radData, pvData, horData] = await Promise.all([
        getMonthlyRadiation(parseFloat(lat), parseFloat(lng), angle),
        getPVCalculation(
          parseFloat(lat), parseFloat(lng), peakPower, loss, angle, aspect,
          false,
          selectedTech.pvgisTechchoice,
          selectedTech.pvgisMountingplace,
        ),
        getHorizonProfile(parseFloat(lat), parseFloat(lng)),
      ]);
      setMonthlyData(radData);
      setPvCalcData(pvData);
      setHorizonData(horData);
      toast.success('Todos los datos PVGIS obtenidos correctamente');
    } catch (err: any) {
      const msg = err.message || 'Error al consultar PVGIS';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [lat, lng, angle, aspect, peakPower, loss, selectedTech]);

  // Exportar datos a CSV
  const exportToCSV = () => {
    if (!monthlyData) return;
    const headers = 'Mes,Irrad. Horizontal (kWh/m²),Irrad. Óptima (kWh/m²),DNI (kWh/m²),Ratio Difusa/Global,Temperatura (°C)\n';
    const rows = monthlyData.outputs.monthly.map(m =>
      `${MONTH_NAMES[m.month - 1]},${m.H_h.toFixed(2)},${m.H_i_opt.toFixed(2)},${m.Hb_n.toFixed(2)},${m.Kd.toFixed(3)},${m.T2m.toFixed(1)}`
    ).join('\n');
    const csv = headers + rows;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `PVGIS_radiacion_${lat}_${lng}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Datos exportados a CSV');
  };

  // Datos calculados
  const annualIrradiance = useMemo(() => {
    if (!monthlyData) return 0;
    return monthlyData.outputs.monthly.reduce((sum, m) => sum + m.H_h, 0);
  }, [monthlyData]);

  const classification = useMemo(() => {
    return classifyAnnualIrradiance(annualIrradiance);
  }, [annualIrradiance]);

  const chartData = useMemo(() => {
    if (!monthlyData) return [];
    return monthlyData.outputs.monthly.map(m => ({
      mes: MONTH_NAMES[m.month - 1],
      horizontal: parseFloat(m.H_h.toFixed(2)),
      optima: parseFloat(m.H_i_opt.toFixed(2)),
      dni: parseFloat(m.Hb_n.toFixed(2)),
      ratioDifusa: parseFloat((m.Kd * 100).toFixed(1)),
      temperatura: parseFloat(m.T2m.toFixed(1)),
    }));
  }, [monthlyData]);

  const pvChartData = useMemo(() => {
    if (!pvCalcData) return [];
    return pvCalcData.outputs.monthly.fixed.map(m => ({
      mes: MONTH_NAMES[m.month - 1],
      produccionMensual: parseFloat(m.E_m.toFixed(2)),
      produccionDiaria: parseFloat(m.E_d.toFixed(2)),
      irradiacionMensual: parseFloat(m.H_i_m.toFixed(2)),
      irradiacionDiaria: parseFloat(m.H_i_d.toFixed(2)),
      desviacion: parseFloat(m.SD_m.toFixed(2)),
    }));
  }, [pvCalcData]);

  // Producción corregida con parámetros reales del panel
  const correctedPvData = useMemo(() => {
    if (!pvCalcData || !monthlyData) return null;

    const monthlyCorrections = pvCalcData.outputs.monthly.fixed.map((m, idx) => {
      const ambTemp = monthlyData.outputs.monthly[idx]?.T2m ?? 25;
      const correction = calculateCorrectedProduction(
        m.E_m,
        selectedTech,
        ambTemp,
        selectedTech.pvgisTechchoice,
        yearsFromInstall,
      );
      return {
        month: m.month,
        mes: MONTH_NAMES[m.month - 1],
        pvgisKwh: m.E_m,
        correctedKwh: correction.correctedKwh,
        tempFactor: correction.tempCorrectionFactor,
        noctFactor: correction.noctCorrectionFactor,
        degradFactor: correction.degradationFactor,
        lossFactor: correction.lossAdjustment,
        totalFactor: correction.totalCorrectionFactor,
        ambTemp,
      };
    });

    const totalPvgis = monthlyCorrections.reduce((s, m) => s + m.pvgisKwh, 0);
    const totalCorrected = monthlyCorrections.reduce((s, m) => s + m.correctedKwh, 0);
    const avgFactor = totalCorrected / (totalPvgis || 1);

    return { monthly: monthlyCorrections, totalPvgis, totalCorrected, avgFactor };
  }, [pvCalcData, monthlyData, selectedTech, yearsFromInstall]);

  const correctedChartData = useMemo(() => {
    if (!correctedPvData) return [];
    return correctedPvData.monthly.map(m => ({
      mes: m.mes,
      pvgis: parseFloat(m.pvgisKwh.toFixed(2)),
      corregido: parseFloat(m.correctedKwh.toFixed(2)),
      factorCorreccion: parseFloat((m.totalFactor * 100).toFixed(1)),
    }));
  }, [correctedPvData]);

  const horizonChartData = useMemo(() => {
    if (!horizonData?.outputs?.horizon_profile) return [];
    return horizonData.outputs.horizon_profile.map((p: any) => ({
      azimut: p.A,
      horizonte: p.H_hor,
    }));
  }, [horizonData]);

  const hasResults = !!(monthlyData || pvCalcData || horizonData);

  // Estado para carga de datos horarios PVGIS
  const [loadingHourlyPVGIS, setLoadingHourlyPVGIS] = useState(false);
  // Área disponible para auto-cálculo de paneles en el Simulador
  const [availableAreaInput, setAvailableAreaInput] = useState<number>(100);

  // Enviar datos al Simulador de Energía (incluye datos horarios para PR_T)
  const handleSendToSimulator = useCallback(async () => {
    if (!pvCalcData || !monthlyData || !correctedPvData || !onSendToSimulator) return;

    const payload: PVGISToSimulatorData = {
      latitude: parseFloat(lat),
      longitude: parseFloat(lng),
      tilt: angle,
      azimuth: aspect,
      peakPowerKwp: peakPower,
      systemLoss: loss,
      technology: selectedTech.pvgisTechchoice,
      panelName: selectedTech.name,
      annualProductionAC: pvCalcData.outputs.totals.fixed.E_y,
      annualProductionCorrected: correctedPvData.totalCorrected,
      annualIrradiationPOA: pvCalcData.outputs.totals.fixed.H_i_y,
      correctionFactor: correctedPvData.avgFactor,
      monthlyData: pvCalcData.outputs.monthly.fixed.map((m, idx) => ({
        month: m.month,
        productionAC_kWh: m.E_m,
        productionCorrectedAC_kWh: correctedPvData.monthly[idx]?.correctedKwh ?? m.E_m,
        irradiationPOA_kWhm2: m.H_i_m,
        temperature: monthlyData.outputs.monthly[idx]?.T2m ?? 25,
      })),
      radiationDB: monthlyData.inputs?.meteo_data?.radiation_db || 'PVGIS-ERA5',
      yearMin: monthlyData.inputs?.meteo_data?.year_min || 2005,
      yearMax: monthlyData.inputs?.meteo_data?.year_max || 2023,
      availableArea: availableAreaInput > 0 ? availableAreaInput : undefined,
    };

    // Obtener datos horarios PVGIS para PR_T IEC 61724-1:2021
    try {
      setLoadingHourlyPVGIS(true);
      toast.info('Obteniendo datos horarios PVGIS (seriescalc) para PR_T...');
      const hourlyData = await getPVGISHourlyData(
        parseFloat(lat),
        parseFloat(lng),
        angle,
        aspect,
        peakPower,
        loss,
      );
      payload.hourlyRecords = hourlyData.records.map(r => ({
        month: r.month,
        poa_Wm2: r.G_i,
        tamb_C: r.T2m,
        wspd_ms: r.WS10m,
        ac_W: r.P_W,
      }));
      toast.success(`Datos horarios PVGIS cargados: ${hourlyData.records.length} registros`);
    } catch (err) {
      console.warn('No se pudieron obtener datos horarios PVGIS:', err);
      toast.warning('PR_T horario PVGIS no disponible. Se usará cálculo mensual.');
    } finally {
      setLoadingHourlyPVGIS(false);
    }

    onSendToSimulator(payload);
    toast.success('Datos PVGIS enviados al Simulador de Energía');
  }, [pvCalcData, monthlyData, correctedPvData, onSendToSimulator, lat, lng, angle, aspect, peakPower, loss, selectedTech, availableAreaInput]);

  // Helpers para datos derivados
  const annualOptima = monthlyData
    ? monthlyData.outputs.monthly.reduce((s, m) => s + m.H_i_opt, 0)
    : 0;
  const annualDNI = monthlyData
    ? monthlyData.outputs.monthly.reduce((s, m) => s + m.Hb_n, 0)
    : 0;
  const avgKd = monthlyData
    ? monthlyData.outputs.monthly.reduce((s, m) => s + m.Kd, 0) / 12
    : 0;
  const avgT2m = monthlyData
    ? monthlyData.outputs.monthly.reduce((s, m) => s + m.T2m, 0) / 12
    : 0;

  return (
    <div className="space-y-6" translate="no">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <Globe size={24} className="text-indigo-600" />
          <span>PVGIS - Datos Reales de Irradiancia Solar</span>
        </h3>
        <p className="text-sm text-gray-700">
          <span>Consulta datos satelitales reales del Photovoltaic Geographical Information System (Comisión Europea). </span>
          <span>Base de datos: PVGIS-ERA5 (global) y PVGIS-SARAH3 (Europa/África/Asia). Selección automática según ubicación.</span>
        </p>
      </div>

      {/* Selector de Tecnología del Panel */}
      <PanelTechSelector
        selectedTech={selectedTech}
        onSelectTech={setSelectedTech}
        yearsFromInstall={yearsFromInstall}
        onYearsChange={setYearsFromInstall}
        selectedRegion={activeRegion}
        onRegionChange={(r) => setRegionOverride(r)}
        detectedRegionInfo={detectedRegion}
      />

      {/* Parámetros de entrada */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <MapPin size={18} className="text-blue-600" />
          <span>Parámetros de Consulta</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1"><span>Latitud</span></label>
            <input
              type="number"
              step="0.0001"
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono"
              placeholder="6.2518"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1"><span>Longitud</span></label>
            <input
              type="number"
              step="0.0001"
              value={lng}
              onChange={(e) => setLng(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono"
              placeholder="-75.5636"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1"><span>Ciudad</span></label>
            <input
              type="text"
              value={cityName || ''}
              disabled
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50"
              placeholder="Seleccionar en mapa"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              <span>Inclinación: </span><span className="text-blue-600 font-bold">{angle}°</span>
            </label>
            <input
              type="range"
              min="0"
              max="90"
              value={angle}
              onChange={(e) => setAngle(Number(e.target.value))}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              <span>Azimut: </span><span className="text-blue-600 font-bold">{aspect}°</span>
            </label>
            <input
              type="range"
              min="-90"
              max="90"
              value={aspect}
              onChange={(e) => setAspect(Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-gray-400 mt-1"><span>0=Sur, -90=Este, 90=Oeste</span></p>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              <span>Potencia Pico: </span><span className="text-blue-600 font-bold">{peakPower} kWp</span>
            </label>
            <input
              type="range"
              min="0.5"
              max="100"
              step="0.5"
              value={peakPower}
              onChange={(e) => setPeakPower(Number(e.target.value))}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              <span>Pérdidas: </span><span className="text-blue-600 font-bold">{loss}%</span>
            </label>
            <input
              type="range"
              min="0"
              max="50"
              value={loss}
              onChange={(e) => setLoss(Number(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        {/* Indicador de tecnología seleccionada para PVGIS */}
        <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3 mb-4 flex items-center gap-3 text-sm">
          <div
            className="w-6 h-6 rounded flex items-center justify-center text-[8px] font-bold flex-shrink-0"
            style={{ backgroundColor: selectedTech.color + '20', color: selectedTech.color, border: `1px solid ${selectedTech.color}` }}
          >
            {selectedTech.hiitioId || 'G'}
          </div>
          <div className="flex-1">
            <span className="text-indigo-700">
              <span>PVGIS consultará con: </span>
              <strong>{selectedTech.pvgisTechchoice}</strong>
              <span> / montaje: </span>
              <strong>{selectedTech.pvgisMountingplace === 'building' ? 'BIPV integrado' : 'Rack abierto'}</strong>
            </span>
          </div>
          <ArrowRight size={14} className="text-indigo-400" />
          <span className="text-xs text-indigo-600 font-medium">{selectedTech.name}</span>
        </div>

        {/* Botones de consulta */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={fetchAllData}
            disabled={loading}
            className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            <span style={{ display: loading ? 'inline-flex' : 'none' }}>
              <Loader2 size={16} className="animate-spin" />
            </span>
            <span style={{ display: loading ? 'none' : 'inline-flex' }}>
              <Globe size={16} />
            </span>
            <span>Consultar PVGIS (Todos)</span>
          </button>
          <button
            onClick={fetchMonthlyRadiation}
            disabled={loading}
            className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            <Sun size={16} />
            <span>Solo Radiación</span>
          </button>
          <button
            onClick={fetchPVCalc}
            disabled={loading}
            className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            <Zap size={16} />
            <span>Solo PV Calc</span>
          </button>
          <button
            onClick={fetchHorizon}
            disabled={loading}
            className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            <TrendingUp size={16} />
            <span>Solo Horizonte</span>
          </button>
          <button
            onClick={exportToCSV}
            style={{ display: monthlyData ? 'inline-flex' : 'none' }}
            className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 items-center gap-2 transition-colors"
          >
            <Download size={16} />
            <span>Exportar CSV</span>
          </button>
        </div>
      </div>

      {/* Error */}
      <div
        style={{ display: error ? 'block' : 'none' }}
        className="bg-red-50 border border-red-200 rounded-lg p-4"
      >
        <p className="text-sm text-red-800 font-medium"><span>Error: </span><span>{error || ''}</span></p>
        <p className="text-xs text-red-600 mt-1">
          <span>Verifica las coordenadas e intenta nuevamente. PVGIS puede no tener datos para todas las ubicaciones.</span>
        </p>
      </div>

      {/* Resultados */}
      <div style={{ display: hasResults ? 'block' : 'none' }}>
        {/* Tabs de navegación */}
        <div className="flex gap-2 border-b border-gray-200 pb-2 mb-6">
          <button
            onClick={() => setActiveTab('radiation')}
            className={`px-4 py-2 rounded-t-lg font-medium text-sm transition-colors ${
              activeTab === 'radiation'
                ? 'bg-indigo-100 text-indigo-800 border-b-2 border-indigo-600'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Sun size={14} className="inline mr-1" />
            <span>Radiación Mensual</span>
          </button>
          <button
            onClick={() => setActiveTab('pvcalc')}
            className={`px-4 py-2 rounded-t-lg font-medium text-sm transition-colors ${
              activeTab === 'pvcalc'
                ? 'bg-green-100 text-green-800 border-b-2 border-green-600'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Zap size={14} className="inline mr-1" />
            <span>Producción PV</span>
          </button>
          <button
            onClick={() => setActiveTab('horizon')}
            className={`px-4 py-2 rounded-t-lg font-medium text-sm transition-colors ${
              activeTab === 'horizon'
                ? 'bg-teal-100 text-teal-800 border-b-2 border-teal-600'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <TrendingUp size={14} className="inline mr-1" />
            <span>Perfil Horizonte</span>
          </button>
        </div>

        {/* ===== Tab: Radiación Mensual ===== */}
        <div
          ref={radiationChartRef}
          style={{ display: (activeTab === 'radiation' && monthlyData) ? 'block' : 'none' }}
        >
          <div className="space-y-6">
            {/* Resumen */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-xs text-yellow-700 mb-1"><span>GHI Anual</span></p>
                <p className="text-2xl font-bold text-yellow-800 font-mono">{annualIrradiance.toFixed(0)}</p>
                <p className="text-xs text-yellow-600"><span>kWh/m²/año</span></p>
              </div>
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <p className="text-xs text-orange-700 mb-1"><span>Irrad. Óptima Anual</span></p>
                <p className="text-2xl font-bold text-orange-800 font-mono">{annualOptima.toFixed(0)}</p>
                <p className="text-xs text-orange-600"><span>kWh/m²/año</span></p>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-xs text-blue-700 mb-1"><span>DNI Anual</span></p>
                <p className="text-2xl font-bold text-blue-800 font-mono">{annualDNI.toFixed(0)}</p>
                <p className="text-xs text-blue-600"><span>kWh/m²/año</span></p>
              </div>
              <div className="border rounded-lg p-4" style={{ backgroundColor: classification.color + '15', borderColor: classification.color + '40' }}>
                <p className="text-xs mb-1" style={{ color: classification.color }}><span>Clasificación</span></p>
                <p className="text-2xl font-bold" style={{ color: classification.color }}>{classification.category}</p>
                <p className="text-xs" style={{ color: classification.color }}>{classification.description}</p>
              </div>
            </div>

            {/* Gráfico de Radiación */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-4"><span>Irradiancia Mensual (kWh/m²)</span></h4>
              <div style={{ display: chartData.length > 0 ? 'block' : 'none' }}>
                <ResponsiveContainer width="100%" height={320}>
                  <ComposedChart data={chartData.length > 0 ? chartData : []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="horizontal" name="Horizontal" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="optima" name="Ángulo Óptimo" fill="#ef4444" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="dni" name="DNI" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Gráfico Temperatura y Ratio Difusa */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Thermometer size={16} className="text-red-500" />
                  <span>Temperatura Media Mensual</span>
                </h4>
                <div style={{ display: chartData.length > 0 ? 'block' : 'none' }}>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={chartData.length > 0 ? chartData : []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="mes" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} unit="°C" />
                      <Tooltip />
                      <Line type="monotone" dataKey="temperatura" name="Temp. (°C)" stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Sun size={16} className="text-yellow-500" />
                  <span>Ratio Difusa/Global (%)</span>
                </h4>
                <div style={{ display: chartData.length > 0 ? 'block' : 'none' }}>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={chartData.length > 0 ? chartData : []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="mes" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} unit="%" />
                      <Tooltip />
                      <Bar dataKey="ratioDifusa" name="Difusa/Global (%)" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Tabla de datos */}
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <h4 className="font-semibold text-gray-900 p-4 border-b border-gray-200">
                <span>Datos Mensuales PVGIS (Valores Reales Satelitales)</span>
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-gray-700"><span>Mes</span></th>
                      <th className="px-4 py-3 text-right font-medium text-gray-700"><span>H_h (kWh/m²)</span></th>
                      <th className="px-4 py-3 text-right font-medium text-gray-700"><span>H_opt (kWh/m²)</span></th>
                      <th className="px-4 py-3 text-right font-medium text-gray-700"><span>DNI (kWh/m²)</span></th>
                      <th className="px-4 py-3 text-right font-medium text-gray-700"><span>Kd</span></th>
                      <th className="px-4 py-3 text-right font-medium text-gray-700"><span>Temp (°C)</span></th>
                    </tr>
                  </thead>
                  <tbody>
                    {(monthlyData?.outputs?.monthly ?? []).map((m, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-4 py-2 font-medium"><span>{MONTH_NAMES[m.month - 1]}</span></td>
                        <td className="px-4 py-2 text-right font-mono">{m.H_h.toFixed(2)}</td>
                        <td className="px-4 py-2 text-right font-mono">{m.H_i_opt.toFixed(2)}</td>
                        <td className="px-4 py-2 text-right font-mono">{m.Hb_n.toFixed(2)}</td>
                        <td className="px-4 py-2 text-right font-mono">{m.Kd.toFixed(3)}</td>
                        <td className="px-4 py-2 text-right font-mono">{m.T2m.toFixed(1)}</td>
                      </tr>
                    ))}
                    <tr className="bg-indigo-50 font-bold">
                      <td className="px-4 py-2"><span>TOTAL</span></td>
                      <td className="px-4 py-2 text-right font-mono">{annualIrradiance.toFixed(1)}</td>
                      <td className="px-4 py-2 text-right font-mono">{annualOptima.toFixed(1)}</td>
                      <td className="px-4 py-2 text-right font-mono">{annualDNI.toFixed(1)}</td>
                      <td className="px-4 py-2 text-right font-mono">{avgKd.toFixed(3)}</td>
                      <td className="px-4 py-2 text-right font-mono">{avgT2m.toFixed(1)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Info de fuente */}
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
              <p className="text-xs text-indigo-800">
                <span><strong>Fuente:</strong> PVGIS © European Commission, Joint Research Centre (JRC). </span>
                <span>Base de datos: {monthlyData?.inputs?.meteo_data?.radiation_db || 'PVGIS-ERA5'}. </span>
                <span>Período: {monthlyData?.inputs?.meteo_data?.year_min || '2005'}-{monthlyData?.inputs?.meteo_data?.year_max || '2023'}. </span>
                <span>Elevación: {monthlyData?.inputs?.location?.elevation || 0}m.</span>
              </p>
            </div>
          </div>
        </div>

        {/* Mensaje cuando no hay datos para radiación */}
        <div style={{ display: (activeTab === 'radiation' && !monthlyData) ? 'block' : 'none' }}>
          <div className="text-center py-12 text-gray-500">
            <Sun size={48} className="mx-auto mb-4 opacity-30" />
            <p><span>Presiona "Consultar PVGIS" para obtener datos de radiación mensual.</span></p>
          </div>
        </div>

        {/* ===== Tab: Producción PV ===== */}
        <div
          ref={pvCalcChartRef}
          style={{ display: (activeTab === 'pvcalc' && pvCalcData) ? 'block' : 'none' }}
        >
          <div className="space-y-6">
            {/* Resumen de producción */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-xs text-green-700 mb-1"><span>Producción PVGIS Anual</span></p>
                <p className="text-2xl font-bold text-green-800 font-mono">
                  {pvCalcData ? pvCalcData.outputs.totals.fixed.E_y.toFixed(0) : '0'}
                </p>
                <p className="text-xs text-green-600"><span>kWh/año (referencia)</span></p>
              </div>
              <div className="bg-emerald-50 border border-emerald-300 rounded-lg p-4">
                <p className="text-xs text-emerald-700 mb-1"><span>Producción Corregida</span></p>
                <p className="text-2xl font-bold text-emerald-800 font-mono">
                  {correctedPvData ? correctedPvData.totalCorrected.toFixed(0) : '0'}
                </p>
                <p className="text-xs text-emerald-600">
                  <span>kWh/año ({selectedTech.hiitioId || 'panel'})</span>
                </p>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-xs text-yellow-700 mb-1"><span>Factor Corrección</span></p>
                <p className="text-2xl font-bold text-yellow-800 font-mono">
                  {correctedPvData ? (correctedPvData.avgFactor * 100).toFixed(1) : '100.0'}%
                </p>
                <p className="text-xs text-yellow-600"><span>vs PVGIS estándar</span></p>
              </div>
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-xs text-purple-700 mb-1"><span>Irrad. en Plano Anual</span></p>
                <p className="text-2xl font-bold text-purple-800 font-mono">
                  {pvCalcData ? pvCalcData.outputs.totals.fixed.H_i_y.toFixed(0) : '0'}
                </p>
                <p className="text-xs text-purple-600"><span>kWh/m²/año</span></p>
              </div>
            </div>

            {/* Gráfico comparativo PVGIS vs Corregido */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-2"><span>Producción PV: PVGIS vs Corregida ({selectedTech.name})</span></h4>
              <p className="text-xs text-gray-500 mb-4">
                <span>Comparación mensual entre la producción estándar PVGIS y la corregida con los parámetros reales del panel seleccionado.</span>
              </p>
              <div style={{ display: correctedChartData.length > 0 ? 'block' : 'none' }}>
                <ResponsiveContainer width="100%" height={350}>
                  <ComposedChart data={correctedChartData.length > 0 ? correctedChartData : []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                    <YAxis yAxisId="left" tick={{ fontSize: 12 }} label={{ value: 'kWh', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} domain={[80, 120]} label={{ value: 'Factor %', angle: 90, position: 'insideRight', fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="pvgis" name="PVGIS Estándar (kWh)" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                    <Bar yAxisId="left" dataKey="corregido" name={`Corregido ${selectedTech.hiitioId || 'panel'} (kWh)`} fill="#10b981" radius={[4, 4, 0, 0]} />
                    <Line yAxisId="right" type="monotone" dataKey="factorCorreccion" name="Factor Corrección (%)" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Gráfico original de producción PVGIS */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-4"><span>Producción PV Mensual (PVGIS base)</span></h4>
              <div style={{ display: pvChartData.length > 0 ? 'block' : 'none' }}>
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={pvChartData.length > 0 ? pvChartData : []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                    <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="produccionMensual" name="Producción (kWh)" fill="#22c55e" radius={[4, 4, 0, 0]} />
                    <Line yAxisId="right" type="monotone" dataKey="irradiacionMensual" name="Irrad. Plano (kWh/m²)" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Tabla detallada de correcciones */}
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <h4 className="font-semibold text-gray-900 p-4 border-b border-gray-200">
                <span>Desglose de Correcciones por Mes</span>
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-700"><span>Mes</span></th>
                      <th className="px-3 py-2 text-right font-medium text-gray-700"><span>PVGIS (kWh)</span></th>
                      <th className="px-3 py-2 text-right font-medium text-gray-700"><span>Corregido (kWh)</span></th>
                      <th className="px-3 py-2 text-right font-medium text-gray-700"><span>F. Temp</span></th>
                      <th className="px-3 py-2 text-right font-medium text-gray-700"><span>F. NOCT</span></th>
                      <th className="px-3 py-2 text-right font-medium text-gray-700"><span>F. Degr.</span></th>
                      <th className="px-3 py-2 text-right font-medium text-gray-700"><span>F. Pérd.</span></th>
                      <th className="px-3 py-2 text-right font-medium text-gray-700"><span>F. Total</span></th>
                      <th className="px-3 py-2 text-right font-medium text-gray-700"><span>T amb (°C)</span></th>
                    </tr>
                  </thead>
                  <tbody>
                    {(correctedPvData?.monthly ?? []).map((m, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-3 py-2 font-medium"><span>{m.mes}</span></td>
                        <td className="px-3 py-2 text-right font-mono">{m.pvgisKwh.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right font-mono font-bold text-emerald-700">{m.correctedKwh.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right font-mono text-xs">{(m.tempFactor * 100).toFixed(1)}%</td>
                        <td className="px-3 py-2 text-right font-mono text-xs">{(m.noctFactor * 100).toFixed(1)}%</td>
                        <td className="px-3 py-2 text-right font-mono text-xs">{(m.degradFactor * 100).toFixed(1)}%</td>
                        <td className="px-3 py-2 text-right font-mono text-xs">{(m.lossFactor * 100).toFixed(1)}%</td>
                        <td className="px-3 py-2 text-right font-mono text-xs font-bold">{(m.totalFactor * 100).toFixed(1)}%</td>
                        <td className="px-3 py-2 text-right font-mono text-xs">{m.ambTemp.toFixed(1)}</td>
                      </tr>
                    ))}
                    <tr className="bg-emerald-50 font-bold">
                      <td className="px-3 py-2"><span>TOTAL</span></td>
                      <td className="px-3 py-2 text-right font-mono">{correctedPvData ? correctedPvData.totalPvgis.toFixed(1) : '0'}</td>
                      <td className="px-3 py-2 text-right font-mono text-emerald-700">{correctedPvData ? correctedPvData.totalCorrected.toFixed(1) : '0'}</td>
                      <td colSpan={5} className="px-3 py-2 text-center text-xs text-gray-500">
                        <span>Factor promedio: {correctedPvData ? (correctedPvData.avgFactor * 100).toFixed(1) : '100.0'}%</span>
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-xs">{avgT2m.toFixed(1)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Botón Aplicar al Simulador */}
            {onSendToSimulator && pvCalcData && correctedPvData && (
              <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border-2 border-emerald-300 rounded-lg p-4 space-y-3">
                {/* Área disponible para auto-cálculo de paneles */}
                <div className="p-3 bg-emerald-100/50 border border-emerald-200 rounded-lg">
                  <label className="block text-sm font-semibold text-emerald-800 mb-1">
                    Área disponible para paneles (m²)
                  </label>
                  <p className="text-xs text-emerald-600 mb-2">
                    Ingresa el área de la cubierta/techo donde se instalarán los paneles. El Simulador calculará automáticamente cuántos paneles caben.
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min={1}
                      max={100000}
                      step={10}
                      value={availableAreaInput}
                      onChange={(e) => setAvailableAreaInput(Math.max(1, Number(e.target.value)))}
                      className="flex-1 px-3 py-2 border border-emerald-300 rounded-md text-sm font-mono focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    />
                    {modelFacades && modelFacades.length > 0 && (
                      <button
                        type="button"
                        className="px-3 py-2 bg-emerald-100 hover:bg-emerald-200 text-emerald-700 border border-emerald-300 rounded-md text-xs font-medium transition-colors whitespace-nowrap"
                        onClick={() => {
                          const el = document.getElementById('pvgis-facade-picker');
                          if (el) el.classList.toggle('hidden');
                        }}
                      >
                        🏢 Importar del Modelo 3D
                      </button>
                    )}
                  </div>
                  {/* Selector de fachada del modelo 3D */}
                  {modelFacades && modelFacades.length > 0 && (
                    <div id="pvgis-facade-picker" className="hidden mt-2 p-2 bg-white border border-emerald-200 rounded-md shadow-sm max-h-48 overflow-y-auto">
                      <p className="text-xs text-gray-500 mb-1 font-medium">Selecciona una superficie del modelo 3D:</p>
                      {modelFacades.map((facade, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className="w-full text-left px-2 py-1.5 text-xs hover:bg-emerald-50 rounded flex items-center gap-2 transition-colors"
                          onClick={() => {
                            setAvailableAreaInput(Math.round(facade.area));
                            document.getElementById('pvgis-facade-picker')?.classList.add('hidden');
                            toast.success(`Área importada: ${facade.name} — ${Math.round(facade.area)} m²`);
                          }}
                        >
                          <span className="w-3 h-3 rounded-sm flex-shrink-0" style={{ backgroundColor: facade.color }}></span>
                          <span className="font-medium text-gray-800">{facade.name}</span>
                          <span className="ml-auto text-gray-500 font-mono">{Math.round(facade.area)} m²</span>
                          <span className="text-gray-400">| {facade.tilt.toFixed(0)}° tilt</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-emerald-900 flex items-center gap-2">
                      <ArrowRight size={16} className="text-emerald-600" />
                      <span>Transferir al Simulador de Energía</span>
                    </h4>
                    <p className="text-xs text-emerald-700 mt-1">
                      <span>Envía la producción AC mensual PVGIS ({correctedPvData.totalCorrected.toFixed(0)} kWh/año AC corregido) como referencia comparativa al Simulador.</span>
                    </p>
                  </div>
                  <button
                    onClick={handleSendToSimulator}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-2 whitespace-nowrap"
                  >
                    <Zap size={14} />
                    <span>Aplicar al Simulador</span>
                  </button>
                </div>
              </div>
            )}

            {/* Configuración del sistema */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-3"><span>Configuración del Sistema PVGIS</span></h4>
              <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-sm">
                <div>
                  <p className="text-gray-600"><span>Tecnología PVGIS</span></p>
                  <p className="font-medium">{pvCalcData?.inputs?.pv_module?.technology || selectedTech.pvgisTechchoice}</p>
                </div>
                <div>
                  <p className="text-gray-600"><span>Panel HIITIO</span></p>
                  <p className="font-medium">{selectedTech.hiitioId || 'Genérico'}</p>
                </div>
                <div>
                  <p className="text-gray-600"><span>Potencia Pico</span></p>
                  <p className="font-medium">{peakPower} kWp</p>
                </div>
                <div>
                  <p className="text-gray-600"><span>Montaje</span></p>
                  <p className="font-medium">{selectedTech.pvgisMountingplace === 'building' ? 'BIPV' : 'Rack'}</p>
                </div>
                <div>
                  <p className="text-gray-600"><span>Inclinación</span></p>
                  <p className="font-medium">{angle}°</p>
                </div>
                <div>
                  <p className="text-gray-600"><span>Azimut</span></p>
                  <p className="font-medium">{aspect}°</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Mensaje cuando no hay datos para PV Calc */}
        <div style={{ display: (activeTab === 'pvcalc' && !pvCalcData) ? 'block' : 'none' }}>
          <div className="text-center py-12 text-gray-500">
            <Zap size={48} className="mx-auto mb-4 opacity-30" />
            <p><span>Presiona "Consultar PVGIS" para obtener cálculos de producción PV.</span></p>
          </div>
        </div>

        {/* ===== Tab: Perfil Horizonte ===== */}
        <div
          ref={horizonChartRef}
          style={{ display: (activeTab === 'horizon' && horizonData) ? 'block' : 'none' }}
        >
          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Wind size={18} className="text-teal-600" />
                <span>Perfil de Horizonte (Obstrucciones)</span>
              </h4>
              <p className="text-sm text-gray-600 mb-4">
                <span>Muestra la elevación del horizonte en cada dirección. Valores altos indican obstrucciones (montañas, edificios).</span>
              </p>
              <div style={{ display: horizonChartData.length > 0 ? 'block' : 'none' }}>
                <ResponsiveContainer width="100%" height={350}>
                  <RadarChart data={horizonChartData.length > 0 ? horizonChartData.filter((_: any, i: number) => i % 3 === 0) : []}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="azimut" tick={{ fontSize: 10 }} />
                    <PolarRadiusAxis angle={90} tick={{ fontSize: 10 }} />
                    <Radar
                      name="Horizonte (°)"
                      dataKey="horizonte"
                      stroke="#0d9488"
                      fill="#0d9488"
                      fillOpacity={0.3}
                    />
                    <Tooltip />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Gráfico lineal del horizonte */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-4"><span>Elevación del Horizonte por Azimut</span></h4>
              <div style={{ display: horizonChartData.length > 0 ? 'block' : 'none' }}>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={horizonChartData.length > 0 ? horizonChartData : []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="azimut" tick={{ fontSize: 11 }} label={{ value: 'Azimut (°)', position: 'bottom', fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 11 }} label={{ value: 'Elevación (°)', angle: -90, position: 'insideLeft', fontSize: 12 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="horizonte" name="Horizonte (°)" stroke="#0d9488" fill="#0d9488" fillOpacity={0.2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>

        {/* Mensaje cuando no hay datos para horizonte */}
        <div style={{ display: (activeTab === 'horizon' && !horizonData) ? 'block' : 'none' }}>
          <div className="text-center py-12 text-gray-500">
            <TrendingUp size={48} className="mx-auto mb-4 opacity-30" />
            <p><span>Presiona "Consultar PVGIS" para obtener el perfil de horizonte.</span></p>
          </div>
        </div>
      </div>

      {/* Información sobre PVGIS */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-2"><span>Acerca de PVGIS</span></h4>
        <p className="text-sm text-gray-700">
          <span>PVGIS (Photovoltaic Geographical Information System) es una herramienta desarrollada por el Joint Research Centre de la Comisión Europea. </span>
          <span>Proporciona datos de radiación solar basados en mediciones satelitales con cobertura global. </span>
          <span>Los datos son gratuitos y se actualizan periódicamente con nuevas mediciones.</span>
        </p>
      </div>
    </div>
  );
}
