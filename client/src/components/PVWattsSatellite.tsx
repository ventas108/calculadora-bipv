import { useState, useRef, useCallback, useMemo } from 'react';
import { toast } from 'sonner';
import { MapPin, TrendingUp, Loader2, RefreshCw, Thermometer, Sun, Globe, Satellite, Zap, ArrowRight } from 'lucide-react';
import { MapView } from '@/components/Map';
import SolarProspector from '@/components/SolarProspector';
import { getPVWattsQuickEstimate, getPVWattsCalculation, getPVWattsHourlyData, classifySpecificYield, PVWattsResult } from '@/lib/pvwattsApi';
import { classifyAnnualIrradiance } from '@/lib/pvgisApi';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
} from 'recharts';

// ============================================================
// INTERFACES
// ============================================================

/** Datos que se envían del PVWattsSatellite al Simulador de Energía */
export interface PVWattsToSimulatorData {
  // Ubicación
  latitude: number;
  longitude: number;
  // Configuración del sistema PVWatts
  tilt: number;
  azimuth: number;
  systemCapacity: number; // kWp
  losses: number; // %
  arrayType: number;
  moduleType: number;
  // Producción anual
  annualAC_kWh: number;
  annualDC_kWh: number;
  annualPOA_kWhm2: number;
  annualGHI_kWhm2: number;
  specificYield: number; // kWh/kWp/año
  capacityFactor: number; // %
  // Datos mensuales (12 meses)
  monthlyData: {
    month: number;
    monthName: string;
    ac_kWh: number;
    dc_kWh: number;
    poa_kWhm2: number;
    tamb_C: number;
    tcell_C: number;
    wspd_ms: number;
  }[];
  // Datos horarios para PR_T IEC 61724-1:2021 (8760 registros)
  hourlyRecords?: {
    month: number;
    poa_Wm2: number;
    tamb_C: number;
    tcell_C: number;
    wspd_ms: number;
    ac_W: number;
    dc_W: number;
  }[];
  // Metadata de la estación
  stationCity: string;
  stationDistance: number; // km
  weatherSource: string;
  // Área disponible para auto-cálculo de paneles en el Simulador
  availableArea?: number; // m²
}

interface PVWattsDataPoint {
  lat: number;
  lng: number;
  specificYield: number;
  annualAC: number;
  annualGHI: number;
  avgTamb: number;
  category: string;
  color: string;
}

interface RegionStats {
  average: number;
  min: number;
  max: number;
  median: number;
  stdDev: number;
  pointCount: number;
}

/** Clasificar punto del heatmap por GHI (kWh/m²/año) para ser comparable con PVGIS */
function classifyPointByGHI(ghi: number): { category: string; color: string } {
  const c = classifyAnnualIrradiance(ghi);
  return { category: c.category, color: c.color };
}

interface PVWattsSatelliteProps {
  initialLat?: number;
  initialLng?: number;
  cityName?: string;
  /** Callback para enviar datos al Simulador via Prospector (compatibilidad) */
  onUseInSimulator?: (data: any) => void;
  /** Callback directo para enviar datos PVWatts completos al Simulador */
  onSendPVWattsToSimulator?: (data: PVWattsToSimulatorData) => void;
  /** Fachadas detectadas del modelo 3D para importar área */
  modelFacades?: import('@/lib/buildingModelImporter').DetectedFacade[];
}

export default function PVWattsSatellite({
  initialLat, initialLng, cityName,
  onUseInSimulator, onSendPVWattsToSimulator, modelFacades,
}: PVWattsSatelliteProps) {
  const [centerLat, setCenterLat] = useState(initialLat || 6.2518);
  const [centerLng, setCenterLng] = useState(initialLng || -75.5636);
  const [radiusKm, setRadiusKm] = useState(100);
  const [gridSize, setGridSize] = useState(4);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [dataPoints, setDataPoints] = useState<PVWattsDataPoint[]>([]);
  const [regionStats, setRegionStats] = useState<RegionStats | null>(null);
  const [selectedPoint, setSelectedPoint] = useState<PVWattsDataPoint | null>(null);
  // Datos completos PVWatts del punto seleccionado (para enviar al simulador)
  const [selectedPointFullData, setSelectedPointFullData] = useState<PVWattsResult | null>(null);
  const [loadingFullData, setLoadingFullData] = useState(false);

  const mapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.marker.AdvancedMarkerElement[]>([]);
  const circlesRef = useRef<google.maps.Circle[]>([]);

  const clearMapOverlays = useCallback(() => {
    markersRef.current.forEach(m => (m.map = null));
    markersRef.current = [];
    circlesRef.current.forEach(c => c.setMap(null));
    circlesRef.current = [];
  }, []);

  // Cuando se selecciona un punto, cargar datos completos de PVWatts
  const handleSelectPoint = useCallback(async (point: PVWattsDataPoint) => {
    setSelectedPoint(point);
    setSelectedPointFullData(null);
    setLoadingFullData(true);
    try {
      const fullData = await getPVWattsCalculation({
        lat: point.lat,
        lon: point.lng,
        system_capacity: 1,
        losses: 14.08,
      });
      setSelectedPointFullData(fullData);
    } catch (err) {
      console.error('Error cargando datos PVWatts completos:', err);
      toast.error('Error al cargar datos detallados de PVWatts');
    } finally {
      setLoadingFullData(false);
    }
  }, []);

  // Estado para carga de datos horarios
  const [loadingHourly, setLoadingHourly] = useState(false);
  const [availableAreaInput, setAvailableAreaInput] = useState<number>(100); // m² por defecto

  // Enviar datos PVWatts directamente al Simulador (incluye datos horarios para PR_T)
  const handleSendToSimulator = useCallback(async () => {
    if (!selectedPoint || !selectedPointFullData) {
      toast.error('Selecciona un punto del mapa y espera a que carguen los datos completos');
      return;
    }

    const data: PVWattsToSimulatorData = {
      latitude: selectedPoint.lat,
      longitude: selectedPoint.lng,
      tilt: selectedPointFullData.params.tilt,
      azimuth: selectedPointFullData.params.azimuth,
      systemCapacity: selectedPointFullData.params.systemCapacity,
      losses: selectedPointFullData.params.losses,
      arrayType: selectedPointFullData.params.arrayType,
      moduleType: selectedPointFullData.params.moduleType,
      annualAC_kWh: selectedPointFullData.annualAC_kWh,
      annualDC_kWh: selectedPointFullData.annualDC_kWh,
      annualPOA_kWhm2: selectedPointFullData.annualPOA_kWhm2,
      annualGHI_kWhm2: selectedPointFullData.annualGHI_kWhm2,
      specificYield: selectedPointFullData.specificYield,
      capacityFactor: selectedPointFullData.capacityFactor,
      monthlyData: selectedPointFullData.monthly.map(m => ({
        month: m.month,
        monthName: m.monthName,
        ac_kWh: m.ac_kWh,
        dc_kWh: m.dc_kWh,
        poa_kWhm2: m.poa_kWhm2,
        tamb_C: m.tamb_C,
        tcell_C: m.tcell_C,
        wspd_ms: m.wspd_ms,
      })),
      stationCity: selectedPointFullData.stationInfo.city,
      stationDistance: selectedPointFullData.stationInfo.distance,
      weatherSource: selectedPointFullData.stationInfo.weatherDataSource,
      availableArea: availableAreaInput > 0 ? availableAreaInput : undefined,
    };

    // Obtener datos horarios para PR_T IEC 61724-1:2021
    try {
      setLoadingHourly(true);
      toast.info('Obteniendo datos horarios PVWatts (8760 registros) para PR_T...');
      const hourlyData = await getPVWattsHourlyData({
        lat: selectedPoint.lat,
        lon: selectedPoint.lng,
        system_capacity: selectedPointFullData.params.systemCapacity,
        tilt: selectedPointFullData.params.tilt,
        azimuth: selectedPointFullData.params.azimuth,
        losses: selectedPointFullData.params.losses,
        array_type: selectedPointFullData.params.arrayType,
        module_type: selectedPointFullData.params.moduleType,
      });
      data.hourlyRecords = hourlyData.records.map(r => ({
        month: r.month,
        poa_Wm2: r.poa_Wm2,
        tamb_C: r.tamb_C,
        tcell_C: r.tcell_C,
        wspd_ms: r.wspd_ms,
        ac_W: r.ac_W,
        dc_W: r.dc_W,
      }));
      toast.success(`Datos horarios PVWatts cargados: ${hourlyData.records.length} registros`);
    } catch (err) {
      console.warn('No se pudieron obtener datos horarios PVWatts:', err);
      toast.warning('PR_T horario no disponible. Se usará cálculo mensual.');
    } finally {
      setLoadingHourly(false);
    }

    if (onSendPVWattsToSimulator) {
      onSendPVWattsToSimulator(data);
      toast.success('Datos PVWatts enviados al Simulador de Energía');
    }
  }, [selectedPoint, selectedPointFullData, onSendPVWattsToSimulator, availableAreaInput]);

  const generateHeatmap = useCallback(async () => {
    if (!mapRef.current) {
      toast.error('El mapa no está listo. Espera un momento.');
      return;
    }

    setLoading(true);
    clearMapOverlays();
    setDataPoints([]);
    setRegionStats(null);
    setSelectedPoint(null);
    setSelectedPointFullData(null);

    const radiusDeg = radiusKm / 111;
    const step = (radiusDeg * 2) / (gridSize - 1);
    setProgress({ current: 0, total: gridSize * gridSize });

    const points: PVWattsDataPoint[] = [];
    let completed = 0;

    const coords: { lat: number; lng: number }[] = [];
    for (let i = 0; i < gridSize; i++) {
      for (let j = 0; j < gridSize; j++) {
        const lat = centerLat - radiusDeg + i * step;
        const lng = centerLng - radiusDeg + j * step;
        if (lat >= -60 && lat <= 60) {
          coords.push({ lat, lng });
        }
      }
    }

    setProgress({ current: 0, total: coords.length });

    const batchSize = 3;
    for (let i = 0; i < coords.length; i += batchSize) {
      const batch = coords.slice(i, i + batchSize);
      const results = await Promise.all(
        batch.map(async (c) => {
          const estimate = await getPVWattsQuickEstimate(c.lat, c.lng);
          return { ...c, estimate };
        })
      );

      for (const r of results) {
        if (r.estimate && r.estimate.annualGHI > 0) {
          const classification = classifyPointByGHI(r.estimate.annualGHI);
          points.push({
            lat: r.lat,
            lng: r.lng,
            specificYield: r.estimate.specificYield,
            annualAC: r.estimate.annualAC,
            annualGHI: r.estimate.annualGHI,
            avgTamb: r.estimate.avgTamb,
            ...classification,
          });
        }
        completed++;
      }

      setProgress({ current: completed, total: coords.length });

      if (i + batchSize < coords.length) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }

    if (points.length > 0) {
      const values = points.map(p => p.annualGHI).sort((a, b) => a - b);
      const avg = values.reduce((a, b) => a + b, 0) / values.length;
      const variance = values.reduce((s, v) => s + (v - avg) ** 2, 0) / values.length;
      setRegionStats({
        average: avg,
        min: values[0],
        max: values[values.length - 1],
        median: values[Math.floor(values.length / 2)],
        stdDev: Math.sqrt(variance),
        pointCount: values.length,
      });
    }

    setDataPoints(points);
    renderOnMap(points);
    setLoading(false);
    toast.success(`Heatmap PVWatts generado con ${points.length} puntos satelitales NREL`);
  }, [centerLat, centerLng, radiusKm, gridSize, clearMapOverlays]);

  const renderOnMap = useCallback((points: PVWattsDataPoint[]) => {
    if (!mapRef.current || !window.google) return;

    clearMapOverlays();

    const cellSizeKm = (radiusKm * 2) / (gridSize - 1);
    const circleRadius = Math.max(cellSizeKm * 500, 5000);

    for (const point of points) {
      const circle = new google.maps.Circle({
        map: mapRef.current,
        center: { lat: point.lat, lng: point.lng },
        radius: circleRadius,
        fillColor: point.color,
        fillOpacity: 0.55,
        strokeColor: point.color,
        strokeWeight: 1,
        strokeOpacity: 0.8,
        clickable: true,
      });

      circle.addListener('click', () => {
        handleSelectPoint(point);
        mapRef.current?.panTo({ lat: point.lat, lng: point.lng });
      });

      circlesRef.current.push(circle);

      const markerDiv = document.createElement('div');
      markerDiv.style.cssText = `
        background: ${point.color};
        color: white;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
        font-family: monospace;
        border: 2px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        cursor: pointer;
        white-space: nowrap;
      `;
      markerDiv.textContent = `${point.annualGHI.toFixed(0)}`;

      const marker = new google.maps.marker.AdvancedMarkerElement({
        map: mapRef.current,
        position: { lat: point.lat, lng: point.lng },
        content: markerDiv,
        title: `GHI: ${point.annualGHI.toFixed(0)} kWh/m\u00b2/a\u00f1o - ${point.category}`,
      });

      marker.addListener('click', () => {
        handleSelectPoint(point);
      });

      markersRef.current.push(marker);
    }

    if (points.length > 0) {
      const bounds = new google.maps.LatLngBounds();
      points.forEach(p => bounds.extend({ lat: p.lat, lng: p.lng }));
      mapRef.current.fitBounds(bounds, 50);
    }
  }, [radiusKm, gridSize, clearMapOverlays, handleSelectPoint]);

  const handleMapReady = useCallback((map: google.maps.Map) => {
    mapRef.current = map;
    map.addListener('click', (e: google.maps.MapMouseEvent) => {
      if (e.latLng) {
        setCenterLat(e.latLng.lat());
        setCenterLng(e.latLng.lng());
        toast.info(`Centro actualizado: ${e.latLng.lat().toFixed(4)}, ${e.latLng.lng().toFixed(4)}`);
      }
    });
  }, []);

  // Convertir selectedPoint a formato que espera SolarProspector
  const prospectorPoint = useMemo(() => {
    if (!selectedPoint) return null;
    // annualGHI ya viene en kWh/m²/año desde pvwattsApi.ts (corregido)
    return {
      lat: selectedPoint.lat,
      lng: selectedPoint.lng,
      annualGHI: selectedPoint.annualGHI,
      category: selectedPoint.category,
      color: selectedPoint.color,
    };
  }, [selectedPoint]);

  const chartData = dataPoints.length > 0
    ? dataPoints
        .sort((a, b) => b.annualGHI - a.annualGHI)
        .slice(0, 15)
        .map((p) => ({
          name: `(${p.lat.toFixed(2)}, ${p.lng.toFixed(2)})`,
          ghi: Math.round(p.annualGHI),
          sy: Math.round(p.specificYield),
          color: p.color,
        }))
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <Satellite size={24} className="text-indigo-600" />
          PVWatts Satelital - Datos NREL (TMY)
        </h3>
        <p className="text-sm text-gray-700">
          Simulación de producción solar basada en datos satelitales TMY de NREL (National Renewable Energy Laboratory).
          Cada punto consulta la API PVWatts v8 para obtener producción AC/DC real con modelo de nubosidad satelital.
        </p>
      </div>

      {/* Controles */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Globe size={18} className="text-indigo-600" />
          Configuración del Análisis PVWatts
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Latitud Centro</label>
            <input
              type="number" step="0.01" value={centerLat}
              onChange={(e) => setCenterLat(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Longitud Centro</label>
            <input
              type="number" step="0.01" value={centerLng}
              onChange={(e) => setCenterLng(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Radio: <span className="text-indigo-600 font-bold">{radiusKm} km</span>
            </label>
            <input type="range" min="25" max="500" step="25" value={radiusKm}
              onChange={(e) => setRadiusKm(Number(e.target.value))} className="w-full" />
            <div className="flex justify-between text-xs text-gray-400">
              <span>25 km</span><span>500 km</span>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Resolución: <span className="text-indigo-600 font-bold">{gridSize}x{gridSize}</span> = {gridSize * gridSize} puntos
            </label>
            <input type="range" min="3" max="6" value={gridSize}
              onChange={(e) => setGridSize(Number(e.target.value))} className="w-full" />
            <div className="flex justify-between text-xs text-gray-400">
              <span>3x3 (rápido)</span><span>6x6 (detallado)</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <button onClick={generateHeatmap} disabled={loading}
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-colors">
            {loading ? (
              <><Loader2 size={18} className="animate-spin" /> Consultando PVWatts... ({progress.current}/{progress.total})</>
            ) : (
              <><Satellite size={18} /> Generar Heatmap con PVWatts (NREL)</>
            )}
          </button>

          {dataPoints.length > 0 && (
            <button onClick={() => {
              clearMapOverlays();
              setDataPoints([]);
              setRegionStats(null);
              setSelectedPoint(null);
              setSelectedPointFullData(null);
            }} className="flex items-center gap-2 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
              <RefreshCw size={18} /> Limpiar
            </button>
          )}
        </div>

        {loading && (
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div className="bg-indigo-600 h-3 rounded-full transition-all duration-300"
                style={{ width: `${progress.total > 0 ? (progress.current / progress.total) * 100 : 0}%` }} />
            </div>
            <p className="text-xs text-gray-500 mt-1 text-center">
              Consultando punto {progress.current} de {progress.total} en PVWatts NREL...
            </p>
          </div>
        )}

        <p className="text-xs text-gray-500 mt-3">
          Haz clic en el mapa para cambiar el centro del análisis. Cada punto consulta datos TMY satelitales de NREL.
        </p>
      </div>

      {/* Mapa */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="h-[500px]">
          <MapView
            onMapReady={handleMapReady}
            initialCenter={{ lat: centerLat, lng: centerLng }}
            initialZoom={radiusKm > 300 ? 5 : radiusKm > 150 ? 7 : 8}
          />
        </div>
      </div>

      {/* Estadísticas de la región */}
      {regionStats && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-600 mb-1">Puntos</p>
            <p className="text-xl font-bold text-indigo-600 font-mono">{regionStats.pointCount}</p>
            <p className="text-xs text-gray-500">consultados</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-600 mb-1">Promedio GHI</p>
            <p className="text-xl font-bold text-orange-600 font-mono">{regionStats.average.toFixed(0)}</p>
            <p className="text-xs text-gray-500">kWh/m²/año</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-600 mb-1">Máximo GHI</p>
            <p className="text-xl font-bold text-red-600 font-mono">{regionStats.max.toFixed(0)}</p>
            <p className="text-xs text-gray-500">kWh/m²/año</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-600 mb-1">Mínimo GHI</p>
            <p className="text-xl font-bold text-blue-600 font-mono">{regionStats.min.toFixed(0)}</p>
            <p className="text-xs text-gray-500">kWh/m²/año</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-600 mb-1">Mediana GHI</p>
            <p className="text-xl font-bold text-yellow-600 font-mono">{regionStats.median.toFixed(0)}</p>
            <p className="text-xs text-gray-500">kWh/m²/año</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-600 mb-1">Desv. Est.</p>
            <p className="text-xl font-bold text-gray-600 font-mono">{regionStats.stdDev.toFixed(0)}</p>
            <p className="text-xs text-gray-500">variabilidad</p>
          </div>
        </div>
      )}

      {/* Detalle del punto seleccionado */}
      {selectedPoint && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
          <h4 className="font-semibold text-indigo-900 mb-3 flex items-center gap-2">
            <Zap size={18} className="text-indigo-600" />
            Punto Seleccionado - Datos PVWatts NREL
            {loadingFullData && <Loader2 size={14} className="animate-spin text-indigo-500" />}
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-white rounded-lg p-3 text-center border border-indigo-100">
              <p className="text-xs text-gray-600">GHI Anual (PVWatts)</p>
              <p className="text-lg font-bold text-orange-700 font-mono">{selectedPoint.annualGHI.toFixed(0)}</p>
              <p className="text-xs text-gray-500">kWh/m²/año</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center border border-indigo-100">
              <p className="text-xs text-gray-600">Specific Yield</p>
              <p className="text-lg font-bold text-indigo-700 font-mono">{selectedPoint.specificYield.toFixed(0)}</p>
              <p className="text-xs text-gray-500">kWh/kWp/año AC</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center border border-indigo-100">
              <p className="text-xs text-gray-600">Producción AC</p>
              <p className="text-lg font-bold text-green-700 font-mono">{selectedPoint.annualAC.toFixed(0)}</p>
              <p className="text-xs text-gray-500">kWh/año (1 kWp)</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center border border-indigo-100">
              <p className="text-xs text-gray-600">T. Ambiente</p>
              <p className="text-lg font-bold text-red-700 font-mono">{selectedPoint.avgTamb.toFixed(1)}</p>
              <p className="text-xs text-gray-500">°C promedio</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center border border-indigo-100">
              <p className="text-xs text-gray-600">Clasificación</p>
              <p className="text-lg font-bold font-mono" style={{ color: selectedPoint.color }}>
                {selectedPoint.category}
              </p>
              <p className="text-xs text-gray-500">
                ({selectedPoint.lat.toFixed(3)}, {selectedPoint.lng.toFixed(3)})
              </p>
            </div>
          </div>

          {/* Datos mensuales completos del punto seleccionado */}
          {selectedPointFullData && (
            <div className="mt-3 overflow-x-auto">
              <p className="text-[10px] text-indigo-700 font-medium mb-1">Datos Mensuales PVWatts (1 kWp, TMY)</p>
              <table className="w-full text-[10px] border-collapse">
                <thead>
                  <tr className="bg-indigo-100">
                    <th className="px-1 py-0.5 text-left text-indigo-800">Mes</th>
                    <th className="px-1 py-0.5 text-right text-green-700">AC (kWh)</th>
                    <th className="px-1 py-0.5 text-right text-blue-700">DC (kWh)</th>
                    <th className="px-1 py-0.5 text-right text-orange-700">POA (kWh/m²)</th>
                    <th className="px-1 py-0.5 text-right text-red-600">T.Amb (°C)</th>
                    <th className="px-1 py-0.5 text-right text-purple-700">T.Cell (°C)</th>
                    <th className="px-1 py-0.5 text-right text-cyan-700">Viento (m/s)</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedPointFullData.monthly.map((m, idx) => (
                    <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-indigo-50/30'}>
                      <td className="px-1 py-0.5 font-medium text-gray-700">{m.monthName.substring(0, 3)}</td>
                      <td className="px-1 py-0.5 text-right font-mono text-green-700">{m.ac_kWh.toFixed(1)}</td>
                      <td className="px-1 py-0.5 text-right font-mono text-blue-700">{m.dc_kWh.toFixed(1)}</td>
                      <td className="px-1 py-0.5 text-right font-mono text-orange-700">{m.poa_kWhm2.toFixed(1)}</td>
                      <td className="px-1 py-0.5 text-right font-mono text-red-600">{m.tamb_C.toFixed(1)}</td>
                      <td className="px-1 py-0.5 text-right font-mono text-purple-700">{m.tcell_C.toFixed(1)}</td>
                      <td className="px-1 py-0.5 text-right font-mono text-cyan-700">{m.wspd_ms.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-indigo-100 font-bold">
                    <td className="px-1 py-0.5 text-indigo-800">ANUAL</td>
                    <td className="px-1 py-0.5 text-right font-mono text-green-800">{selectedPointFullData.annualAC_kWh.toFixed(0)}</td>
                    <td className="px-1 py-0.5 text-right font-mono text-blue-800">{selectedPointFullData.annualDC_kWh.toFixed(0)}</td>
                    <td className="px-1 py-0.5 text-right font-mono text-orange-800">{selectedPointFullData.annualPOA_kWhm2.toFixed(0)}</td>
                    <td className="px-1 py-0.5 text-right font-mono text-red-700">
                      {(selectedPointFullData.monthly.reduce((s, m) => s + m.tamb_C, 0) / 12).toFixed(1)}
                    </td>
                    <td className="px-1 py-0.5 text-right font-mono text-purple-700">
                      {(selectedPointFullData.monthly.reduce((s, m) => s + m.tcell_C, 0) / 12).toFixed(1)}
                    </td>
                    <td className="px-1 py-0.5 text-right font-mono text-cyan-700">
                      {(selectedPointFullData.monthly.reduce((s, m) => s + m.wspd_ms, 0) / 12).toFixed(1)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}

          {/* Área disponible para auto-cálculo de paneles */}
          {onSendPVWattsToSimulator && selectedPointFullData && (
            <div className="mt-4 p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
              <label className="block text-sm font-semibold text-indigo-800 mb-1">
                Área disponible para paneles (m²)
              </label>
              <p className="text-xs text-indigo-600 mb-2">
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
                  className="flex-1 px-3 py-2 border border-indigo-300 rounded-md text-sm font-mono focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                {modelFacades && modelFacades.length > 0 && (
                  <div className="relative group">
                    <button
                      type="button"
                      className="px-3 py-2 bg-indigo-100 hover:bg-indigo-200 text-indigo-700 border border-indigo-300 rounded-md text-xs font-medium transition-colors whitespace-nowrap"
                      onClick={() => {
                        const el = document.getElementById('pvwatts-facade-picker');
                        if (el) el.classList.toggle('hidden');
                      }}
                    >
                      🏢 Importar del Modelo 3D
                    </button>
                  </div>
                )}
              </div>
              {/* Selector de fachada del modelo 3D */}
              {modelFacades && modelFacades.length > 0 && (
                <div id="pvwatts-facade-picker" className="hidden mt-2 p-2 bg-white border border-indigo-200 rounded-md shadow-sm max-h-48 overflow-y-auto">
                  <p className="text-xs text-gray-500 mb-1 font-medium">Selecciona una superficie del modelo 3D:</p>
                  {modelFacades.map((facade, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="w-full text-left px-2 py-1.5 text-xs hover:bg-indigo-50 rounded flex items-center gap-2 transition-colors"
                      onClick={() => {
                        setAvailableAreaInput(Math.round(facade.area));
                        document.getElementById('pvwatts-facade-picker')?.classList.add('hidden');
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
          )}

          {/* Botón Usar en Simulador */}
          <div className="mt-4 flex flex-wrap gap-3">
            {onSendPVWattsToSimulator && (
              <button
                onClick={handleSendToSimulator}
                disabled={!selectedPointFullData || loadingFullData || loadingHourly}
                className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-colors shadow-sm"
              >
                {loadingFullData || loadingHourly ? (
                  <><Loader2 size={16} className="animate-spin" /> {loadingHourly ? 'Cargando datos horarios (8760 reg.)...' : 'Cargando datos...'}</>
                ) : (
                  <><ArrowRight size={16} /> Usar datos PVWatts en Simulador de Energía (+ PR_T horario)</>
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Prospector Solar — Modelo Mulcue-Llanos */}
      <SolarProspector
        selectedPoint={prospectorPoint}
        ambientTemp={selectedPoint?.avgTamb}
        source="heatmap_pvwatts"
        onUseInSimulator={onUseInSimulator}
        modelFacades={modelFacades}
      />

      {/* Gráfico de barras */}
      {chartData.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp size={18} />
            Ranking de GHI por Ubicación (Top 15) — Datos PVWatts NREL
          </h4>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 80, right: 20, top: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 'auto']} label={{ value: 'kWh/m²/año (GHI)', position: 'insideBottom', offset: -5 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={80} />
              <Tooltip formatter={(value: number, name: string) => {
                if (name === 'GHI') return [`${value} kWh/m²/año`, 'GHI (Irradiancia Horizontal)'];
                return [`${value} kWh/kWp/año`, 'Specific Yield AC'];
              }} />
              <Bar dataKey="ghi" name="GHI" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Leyenda de colores */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Thermometer size={18} />
          Escala de Irradiancia Solar (GHI — PVWatts NREL)
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          {[
            { color: '#d32f2f', label: 'Excelente', range: '≥2000 kWh/m²' },
            { color: '#f57c00', label: 'Muy Buena', range: '1800-2000' },
            { color: '#fbc02d', label: 'Buena', range: '1600-1800' },
            { color: '#7cb342', label: 'Aceptable', range: '1400-1600' },
            { color: '#1976d2', label: 'Limitada', range: '1200-1400' },
            { color: '#424242', label: 'Muy Limitada', range: '<1200' },
          ].map((item, idx) => (
            <div key={idx} className="flex items-center gap-2 bg-gray-50 rounded-lg p-2">
              <div className="w-6 h-6 rounded-full border-2 border-white shadow-md flex-shrink-0"
                style={{ backgroundColor: item.color }} />
              <div>
                <span className="text-xs font-semibold text-gray-800 block">{item.label}</span>
                <span className="text-xs text-gray-500">{item.range}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Consejos */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
        <h4 className="font-semibold text-indigo-900 mb-2">Fuente de Datos y Consejos</h4>
        <div className="text-sm text-indigo-800 space-y-1">
          <p>- Los datos provienen de <strong>PVWatts v8</strong> (NREL), usando datos meteorológicos TMY satelitales.</p>
          <p>- Cada punto consulta GHI (irradiancia horizontal global) con tilt=0°, comparable directamente con PVGIS.</p>
          <p>- El GHI (kWh/m²/año) mide la irradiación solar total en superficie horizontal, sin pérdidas del sistema.</p>
          <p>- Haz clic en los círculos o marcadores para ver datos mensuales completos del punto.</p>
          <p>- Usa <strong>"Usar datos PVWatts en Simulador"</strong> para enviar datos mensuales AC/DC/POA al Simulador.</p>
          <p>- También puedes usar el <strong>Prospector Solar (Mulcue-Llanos)</strong> abajo para cálculos P_exp y PR.</p>
        </div>
      </div>
    </div>
  );
}
