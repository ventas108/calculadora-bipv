import { useState, useCallback, useRef, useEffect } from 'react';
import { toast } from 'sonner';
import { MapPin, TrendingUp, Loader2, RefreshCw, Thermometer, Sun, Globe } from 'lucide-react';
import { MapView } from '@/components/Map';
import SolarProspector from '@/components/SolarProspector';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
} from 'recharts';

// Interfaces
interface IrradianceDataPoint {
  lat: number;
  lng: number;
  annualGHI: number; // kWh/m²/año
  category: string;
  color: string;
  description: string;
  marker?: google.maps.marker.AdvancedMarkerElement;
}

interface RegionStats {
  average: number;
  min: number;
  max: number;
  median: number;
  stdDev: number;
  pointCount: number;
}

// Clasificación de irradiancia
function classifyIrradiance(ghiAnnual: number) {
  if (ghiAnnual >= 2000) return { category: 'Excelente', color: '#d32f2f', description: 'Ubicación óptima para solar' };
  if (ghiAnnual >= 1800) return { category: 'Muy Buena', color: '#f57c00', description: 'Alto potencial solar' };
  if (ghiAnnual >= 1600) return { category: 'Buena', color: '#fbc02d', description: 'Buen potencial solar' };
  if (ghiAnnual >= 1400) return { category: 'Aceptable', color: '#7cb342', description: 'Potencial solar moderado' };
  if (ghiAnnual >= 1200) return { category: 'Limitada', color: '#1976d2', description: 'Potencial solar limitado' };
  return { category: 'Muy Limitada', color: '#616161', description: 'Potencial solar muy bajo' };
}

// Calcular irradiancia anual desde respuesta PVGIS
function parseAnnualGHI(pvgisData: any): number {
  const monthly = pvgisData?.outputs?.monthly;
  if (!monthly || !Array.isArray(monthly) || monthly.length === 0) return 0;

  // PVGIS devuelve múltiples años - agrupar por mes y promediar
  const byMonth: Record<number, number[]> = {};
  for (const rec of monthly) {
    const m = rec.month;
    const hh = rec['H(h)_m'] || 0;
    if (!byMonth[m]) byMonth[m] = [];
    byMonth[m].push(hh);
  }

  let total = 0;
  for (const vals of Object.values(byMonth)) {
    total += vals.reduce((a, b) => a + b, 0) / vals.length;
  }
  return total;
}

interface IrradianceHeatmapProps {
  initialLat?: number;
  initialLng?: number;
  cityName?: string;
  onUseInSimulator?: (data: any) => void;
  modelFacades?: import('@/lib/buildingModelImporter').DetectedFacade[];
}

export default function IrradianceHeatmap({ initialLat, initialLng, cityName, onUseInSimulator, modelFacades }: IrradianceHeatmapProps) {
  const [centerLat, setCenterLat] = useState(initialLat || 6.2518);
  const [centerLng, setCenterLng] = useState(initialLng || -75.5636);
  const [radiusKm, setRadiusKm] = useState(100);
  const [gridSize, setGridSize] = useState(5); // 5x5 = 25 puntos
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [dataPoints, setDataPoints] = useState<IrradianceDataPoint[]>([]);
  const [regionStats, setRegionStats] = useState<RegionStats | null>(null);
  const [selectedPoint, setSelectedPoint] = useState<IrradianceDataPoint | null>(null);

  const mapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.marker.AdvancedMarkerElement[]>([]);
  const circlesRef = useRef<google.maps.Circle[]>([]);

  // Limpiar marcadores y círculos del mapa
  const clearMapOverlays = useCallback(() => {
    markersRef.current.forEach(m => (m.map = null));
    markersRef.current = [];
    circlesRef.current.forEach(c => c.setMap(null));
    circlesRef.current = [];
  }, []);

  // Consultar PVGIS para un punto
  const fetchPVGISPoint = async (lat: number, lng: number): Promise<number> => {
    try {
      const url = `/api/pvgis/MRcalc?lat=${lat.toFixed(4)}&lon=${lng.toFixed(4)}&horirrad=1`;
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      return parseAnnualGHI(data);
    } catch {
      return 0; // Punto fallido
    }
  };

  // Generar grilla de puntos y consultar PVGIS para cada uno
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

    const radiusDeg = radiusKm / 111;
    const step = (radiusDeg * 2) / (gridSize - 1);
    const totalPoints = gridSize * gridSize;
    setProgress({ current: 0, total: totalPoints });

    const points: IrradianceDataPoint[] = [];
    let completed = 0;

    // Generar coordenadas de la grilla
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

    // Consultar PVGIS en lotes de 5 para no saturar
    const batchSize = 5;
    for (let i = 0; i < coords.length; i += batchSize) {
      const batch = coords.slice(i, i + batchSize);
      const results = await Promise.all(
        batch.map(async (c) => {
          const ghi = await fetchPVGISPoint(c.lat, c.lng);
          return { ...c, ghi };
        })
      );

      for (const r of results) {
        if (r.ghi > 0) {
          const classification = classifyIrradiance(r.ghi);
          points.push({
            lat: r.lat,
            lng: r.lng,
            annualGHI: r.ghi,
            ...classification,
          });
        }
        completed++;
      }

      setProgress({ current: completed, total: coords.length });
    }

    // Calcular estadísticas
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

    // Renderizar en el mapa
    renderOnMap(points);

    setLoading(false);
    toast.success(`Heatmap generado con ${points.length} puntos PVGIS reales`);
  }, [centerLat, centerLng, radiusKm, gridSize, clearMapOverlays]);

  // Renderizar puntos en el mapa con círculos coloreados
  const renderOnMap = useCallback((points: IrradianceDataPoint[]) => {
    if (!mapRef.current || !window.google) return;

    clearMapOverlays();

    // Calcular radio de cada círculo basado en la grilla
    const radiusDeg = radiusKm / 111;
    const cellSizeKm = (radiusKm * 2) / (gridSize - 1);
    const circleRadius = Math.max(cellSizeKm * 500, 5000); // metros, mínimo 5km

    for (const point of points) {
      // Crear círculo coloreado
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
        setSelectedPoint(point);
        mapRef.current?.panTo({ lat: point.lat, lng: point.lng });
      });

      circlesRef.current.push(circle);

      // Crear marcador con etiqueta de valor
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
        title: `${point.annualGHI.toFixed(0)} kWh/m²/año - ${point.category}`,
      });

      marker.addListener('click', () => {
        setSelectedPoint(point);
      });

      markersRef.current.push(marker);
    }

    // Ajustar vista del mapa
    if (points.length > 0) {
      const bounds = new google.maps.LatLngBounds();
      points.forEach(p => bounds.extend({ lat: p.lat, lng: p.lng }));
      mapRef.current.fitBounds(bounds, 50);
    }
  }, [radiusKm, gridSize, clearMapOverlays]);

  // Manejar mapa listo
  const handleMapReady = useCallback((map: google.maps.Map) => {
    mapRef.current = map;

    // Click en mapa para seleccionar nuevo centro
    map.addListener('click', (e: google.maps.MapMouseEvent) => {
      if (e.latLng) {
        setCenterLat(e.latLng.lat());
        setCenterLng(e.latLng.lng());
        toast.info(`Centro actualizado: ${e.latLng.lat().toFixed(4)}, ${e.latLng.lng().toFixed(4)}`);
      }
    });
  }, []);

  // Datos para gráfico de barras
  const chartData = dataPoints.length > 0
    ? dataPoints
        .sort((a, b) => b.annualGHI - a.annualGHI)
        .slice(0, 15)
        .map((p, i) => ({
          name: `(${p.lat.toFixed(2)}, ${p.lng.toFixed(2)})`,
          ghi: Math.round(p.annualGHI),
          color: p.color,
        }))
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <Sun size={24} className="text-red-600" />
          Mapa de Irradiancia Solar - Datos PVGIS Reales
        </h3>
        <p className="text-sm text-gray-700">
          Visualiza la irradiancia solar anual (GHI) en una región usando datos satelitales reales de PVGIS
          (Comisión Europea). Cada punto es una consulta real al servidor PVGIS.
        </p>
      </div>

      {/* Controles */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Globe size={18} className="text-blue-600" />
          Configuración del Análisis
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Latitud Centro</label>
            <input
              type="number"
              step="0.01"
              value={centerLat}
              onChange={(e) => setCenterLat(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Longitud Centro</label>
            <input
              type="number"
              step="0.01"
              value={centerLng}
              onChange={(e) => setCenterLng(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Radio: <span className="text-blue-600 font-bold">{radiusKm} km</span>
            </label>
            <input
              type="range"
              min="25"
              max="500"
              step="25"
              value={radiusKm}
              onChange={(e) => setRadiusKm(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>25 km</span>
              <span>500 km</span>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Resolución: <span className="text-blue-600 font-bold">{gridSize}x{gridSize}</span> = {gridSize * gridSize} puntos
            </label>
            <input
              type="range"
              min="3"
              max="7"
              value={gridSize}
              onChange={(e) => setGridSize(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>3x3 (rápido)</span>
              <span>7x7 (detallado)</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={generateHeatmap}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-colors"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Consultando PVGIS... ({progress.current}/{progress.total})
              </>
            ) : (
              <>
                <Sun size={18} />
                Generar Heatmap con PVGIS Real
              </>
            )}
          </button>

          {dataPoints.length > 0 && (
            <button
              onClick={() => {
                clearMapOverlays();
                setDataPoints([]);
                setRegionStats(null);
                setSelectedPoint(null);
              }}
              className="flex items-center gap-2 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              <RefreshCw size={18} />
              Limpiar
            </button>
          )}
        </div>

        {/* Barra de progreso */}
        {loading && (
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-red-600 h-3 rounded-full transition-all duration-300"
                style={{ width: `${progress.total > 0 ? (progress.current / progress.total) * 100 : 0}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1 text-center">
              Consultando punto {progress.current} de {progress.total} en PVGIS...
            </p>
          </div>
        )}

        {/* Nota informativa */}
        <p className="text-xs text-gray-500 mt-3">
          Haz clic en el mapa para cambiar el centro del análisis. Cada punto consulta datos reales de PVGIS (puede tardar 30-60 segundos).
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
            <p className="text-xs text-gray-600 mb-1">Promedio</p>
            <p className="text-xl font-bold text-orange-600 font-mono">{regionStats.average.toFixed(0)}</p>
            <p className="text-xs text-gray-500">kWh/m²/año</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-600 mb-1">Máximo</p>
            <p className="text-xl font-bold text-red-600 font-mono">{regionStats.max.toFixed(0)}</p>
            <p className="text-xs text-gray-500">kWh/m²/año</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-600 mb-1">Mínimo</p>
            <p className="text-xl font-bold text-blue-600 font-mono">{regionStats.min.toFixed(0)}</p>
            <p className="text-xs text-gray-500">kWh/m²/año</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-600 mb-1">Mediana</p>
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

      {/* Prospector Solar — Modelo Mulcue-Llanos */}
      <SolarProspector
        selectedPoint={selectedPoint}
        source="heatmap_pvgis"
        onUseInSimulator={onUseInSimulator}
        modelFacades={modelFacades}
      />

      {/* Gráfico de barras */}
      {chartData.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp size={18} />
            Ranking de Irradiancia por Ubicación (Top 15)
          </h4>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 80, right: 20, top: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 'auto']} label={{ value: 'kWh/m²/año', position: 'insideBottom', offset: -5 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={80} />
              <Tooltip
                formatter={(value: number) => [`${value} kWh/m²/año`, 'GHI Anual']}
              />
              <Bar dataKey="ghi" name="GHI Anual" radius={[0, 4, 4, 0]}>
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
          Escala de Irradiancia Solar (GHI Anual)
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          {[
            { color: '#d32f2f', label: 'Excelente', range: '≥2000 kWh/m²' },
            { color: '#f57c00', label: 'Muy Buena', range: '1800-2000' },
            { color: '#fbc02d', label: 'Buena', range: '1600-1800' },
            { color: '#7cb342', label: 'Aceptable', range: '1400-1600' },
            { color: '#1976d2', label: 'Limitada', range: '1200-1400' },
            { color: '#616161', label: 'Muy Limitada', range: '<1200' },
          ].map((item, idx) => (
            <div key={idx} className="flex items-center gap-2 bg-gray-50 rounded-lg p-2">
              <div
                className="w-6 h-6 rounded-full border-2 border-white shadow-md flex-shrink-0"
                style={{ backgroundColor: item.color }}
              />
              <div>
                <span className="text-xs font-semibold text-gray-800 block">{item.label}</span>
                <span className="text-xs text-gray-500">{item.range}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Consejos */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h4 className="font-semibold text-green-900 mb-2">Fuente de Datos y Consejos</h4>
        <div className="text-sm text-green-800 space-y-1">
          <p>- Los datos provienen de <strong>PVGIS v5.3</strong> (Comisión Europea), base de datos ERA5.</p>
          <p>- Cada punto es una consulta real al servidor PVGIS con datos satelitales promediados (2005-2023).</p>
          <p>- Busca ubicaciones en zonas rojas/naranjas para máxima producción solar.</p>
          <p>- Usa resolución 5x5 o 7x7 para mayor detalle (más tiempo de consulta).</p>
          <p>- Haz clic en los círculos o marcadores para ver datos detallados de cada punto.</p>
          <p>- Haz clic en el mapa para cambiar el centro del análisis.</p>
        </div>
      </div>
    </div>
  );
}
