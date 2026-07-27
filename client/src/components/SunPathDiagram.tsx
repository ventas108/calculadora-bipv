import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { calculateSolarPosition, getDailySolarPath, SolarPosition } from '@/lib/solarPosition';

/** A polygon obstacle drawn on the sun path diagram, in solar coordinates */
export interface ObstaclePolygon {
  id: string;
  name: string;
  color: string;
  /** Vertices in solar coordinates (azimuth 0=S neg=E pos=W, altitude 0-90) */
  vertices: Array<{ azimuth: number; altitude: number }>;
  visible: boolean;
}

interface SunPathDiagramProps {
  latitude: number;
  longitude: number;
  timezone: number;
  /** Existing analysis points to show on the diagram */
  analysisPoints?: Array<{
    month: string;
    day: number;
    hour: number;
    heightSolar: number;
    azimuthSolar: number;
    fs: number;
  }>;
  /** Called when user clicks on a sun position in the diagram */
  onPositionSelect?: (data: {
    month: string;
    day: number;
    hour: number;
    altitude: number;
    azimuth: number;
  }) => void;
  /** Obstacle polygons managed by parent */
  obstacles?: ObstaclePolygon[];
  /** Called when obstacles change */
  onObstaclesChange?: (obstacles: ObstaclePolygon[]) => void;
}

const MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
const MONTH_COLORS = [
  '#1e40af', // Ene - azul oscuro
  '#2563eb', // Feb - azul
  '#3b82f6', // Mar - azul claro
  '#10b981', // Abr - verde
  '#22c55e', // May - verde claro
  '#eab308', // Jun - amarillo (solsticio verano)
  '#f59e0b', // Jul - ámbar
  '#ef4444', // Ago - rojo
  '#dc2626', // Sep - rojo oscuro
  '#9333ea', // Oct - púrpura
  '#7c3aed', // Nov - violeta
  '#4f46e5', // Dic - índigo (solsticio invierno)
];

const OBSTACLE_COLORS = [
  { name: 'Rojo', value: '#ef4444' },
  { name: 'Azul', value: '#3b82f6' },
  { name: 'Verde', value: '#22c55e' },
  { name: 'Púrpura', value: '#a855f7' },
  { name: 'Naranja', value: '#f97316' },
  { name: 'Rosa', value: '#ec4899' },
  { name: 'Cian', value: '#06b6d4' },
  { name: 'Marrón', value: '#92400e' },
];

const OBSTACLE_PRESETS = [
  'Edificio',
  'Árbol',
  'Montaña',
  'Muro',
  'Torre',
  'Chimenea',
  'Otro',
];

// Representative day for each month (21st)
const REP_DAY = 21;

// SVG dimensions
const SVG_SIZE = 600;
const CENTER = SVG_SIZE / 2;
const RADIUS = SVG_SIZE / 2 - 50; // Margin for labels

/**
 * Stereographic projection: maps (azimuth, altitude) to (x, y) on the diagram.
 */
function projectToSVG(azimuth: number, altitude: number): { x: number; y: number } {
  const compassAzimuth = (azimuth + 180) % 360;
  const r = RADIUS * (90 - altitude) / 90;
  const angleRad = (compassAzimuth - 90) * Math.PI / 180;
  return {
    x: CENTER + r * Math.cos(angleRad),
    y: CENTER + r * Math.sin(angleRad),
  };
}

/**
 * Inverse projection: maps SVG (x, y) back to (azimuth, altitude)
 */
function svgToPosition(x: number, y: number): { azimuth: number; altitude: number } | null {
  const dx = x - CENTER;
  const dy = y - CENTER;
  const r = Math.sqrt(dx * dx + dy * dy);

  if (r > RADIUS) return null;

  const altitude = 90 - (r / RADIUS) * 90;
  if (altitude < 0) return null;

  let angleRad = Math.atan2(dy, dx);
  let compassAzimuth = (angleRad * 180 / Math.PI + 90 + 360) % 360;

  let solarAzimuth = compassAzimuth - 180;
  if (solarAzimuth > 180) solarAzimuth -= 360;
  if (solarAzimuth < -180) solarAzimuth += 360;

  return { azimuth: Math.round(solarAzimuth * 100) / 100, altitude: Math.round(altitude * 100) / 100 };
}

/**
 * Point-in-polygon test using ray casting algorithm.
 * Works in SVG coordinate space.
 */
function pointInPolygon(px: number, py: number, polygon: Array<{ x: number; y: number }>): boolean {
  if (polygon.length < 3) return false;
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x, yi = polygon[i].y;
    const xj = polygon[j].x, yj = polygon[j].y;
    if (((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) {
      inside = !inside;
    }
  }
  return inside;
}

/**
 * Check if a solar point (azimuth, altitude) is inside any visible obstacle polygon.
 * Returns the list of obstacle IDs that contain the point.
 */
export function getObstaclesAtPoint(
  azimuth: number,
  altitude: number,
  obstacles: ObstaclePolygon[]
): string[] {
  const { x, y } = projectToSVG(azimuth, altitude);
  const hits: string[] = [];
  for (const obs of obstacles) {
    if (!obs.visible || obs.vertices.length < 3) continue;
    const svgPoly = obs.vertices.map(v => projectToSVG(v.azimuth, v.altitude));
    if (pointInPolygon(x, y, svgPoly)) {
      hits.push(obs.id);
    }
  }
  return hits;
}

/**
 * Calculate what percentage of solar hours in a given month/day are blocked by obstacles.
 * Returns a value 0-100 representing the percentage of daylight hours that are shaded.
 */
export function calculateShadedPercentage(
  latitude: number,
  longitude: number,
  timezone: number,
  month: number,
  day: number,
  hour: number,
  obstacles: ObstaclePolygon[]
): number {
  // Check if the specific hour is inside any obstacle
  const pos = calculateSolarPosition(latitude, longitude, timezone, month, day, hour);
  if (pos.altitude <= 0) return 0;

  const hits = getObstaclesAtPoint(pos.azimuth, pos.altitude, obstacles);
  if (hits.length === 0) return 0;

  // The point is shaded — estimate percentage based on how many obstacles cover it
  // Simple model: each obstacle contributes a base shading percentage
  // For a single obstacle covering the point, we estimate ~80-100% shading
  // We sample nearby points to estimate partial shading
  const sampleOffsets = [-0.25, -0.125, 0, 0.125, 0.25]; // ±15 min around the hour
  let shadedSamples = 0;
  let totalSamples = 0;

  for (const offset of sampleOffsets) {
    const sampleHour = hour + offset;
    const samplePos = calculateSolarPosition(latitude, longitude, timezone, month, day, sampleHour);
    if (samplePos.altitude > 0) {
      totalSamples++;
      const sampleHits = getObstaclesAtPoint(samplePos.azimuth, samplePos.altitude, obstacles);
      if (sampleHits.length > 0) shadedSamples++;
    }
  }

  if (totalSamples === 0) return 0;
  return Math.round((shadedSamples / totalSamples) * 100);
}

type DrawingMode = 'select' | 'draw';

export default function SunPathDiagram({
  latitude,
  longitude,
  timezone,
  analysisPoints = [],
  onPositionSelect,
  obstacles = [],
  onObstaclesChange,
}: SunPathDiagramProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredPoint, setHoveredPoint] = useState<{
    month: number;
    hour: number;
    pos: SolarPosition;
    svgX: number;
    svgY: number;
  } | null>(null);
  const [selectedMonths, setSelectedMonths] = useState<Set<number>>(
    new Set([0, 2, 5, 8, 11]) // Ene, Mar, Jun, Sep, Dic by default
  );
  const [showAllMonths, setShowAllMonths] = useState(false);
  const [showHourLines, setShowHourLines] = useState(true);
  const [showAnalogic, setShowAnalogic] = useState(false);

  // Drawing state
  const [drawingMode, setDrawingMode] = useState<DrawingMode>('select');
  const [currentVertices, setCurrentVertices] = useState<Array<{ azimuth: number; altitude: number; x: number; y: number }>>([]);
  const [newObstacleName, setNewObstacleName] = useState('Edificio');
  const [newObstacleColor, setNewObstacleColor] = useState(OBSTACLE_COLORS[0].value);
  const [editingObstacleId, setEditingObstacleId] = useState<string | null>(null);
  const [cursorPos, setCursorPos] = useState<{ x: number; y: number } | null>(null);
  const [showObstaclePanel, setShowObstaclePanel] = useState(false);

  // Generate solar paths for all 12 months
  const monthlyPaths = useMemo(() => {
    const paths: Array<{
      month: number;
      positions: Array<SolarPosition & { hour: number }>;
    }> = [];

    for (let m = 0; m < 12; m++) {
      const positions: Array<SolarPosition & { hour: number }> = [];
      for (let h = 4; h <= 20; h += 0.25) {
        const pos = calculateSolarPosition(latitude, longitude, timezone, m + 1, REP_DAY, h);
        if (pos.altitude > 0) {
          positions.push({ ...pos, hour: h });
        }
      }
      paths.push({ month: m, positions });
    }
    return paths;
  }, [latitude, longitude, timezone]);

  // Generate hour lines
  const hourLines = useMemo(() => {
    if (!showHourLines) return [];
    const lines: Array<{ hour: number; points: Array<{ x: number; y: number; month: number }> }> = [];
    for (let h = 5; h <= 19; h++) {
      const points: Array<{ x: number; y: number; month: number }> = [];
      for (let m = 0; m < 12; m++) {
        const pos = calculateSolarPosition(latitude, longitude, timezone, m + 1, REP_DAY, h);
        if (pos.altitude > 0) {
          const { x, y } = projectToSVG(pos.azimuth, pos.altitude);
          points.push({ x, y, month: m });
        }
      }
      if (points.length > 1) {
        lines.push({ hour: h, points });
      }
    }
    return lines;
  }, [latitude, longitude, timezone, showHourLines]);

  // Current sun position
  const currentSunPos = useMemo(() => {
    const now = new Date();
    const month = now.getMonth() + 1;
    const day = now.getDate();
    const hour = now.getHours() + now.getMinutes() / 60;
    const pos = calculateSolarPosition(latitude, longitude, timezone, month, day, hour);
    if (pos.altitude > 0) {
      const { x, y } = projectToSVG(pos.azimuth, pos.altitude);
      return { pos, x, y, hour, month, day };
    }
    return null;
  }, [latitude, longitude, timezone]);

  // Get SVG coordinates from mouse event
  const getSVGCoords = useCallback((e: React.MouseEvent<SVGSVGElement>): { svgX: number; svgY: number } | null => {
    if (!svgRef.current) return null;
    const rect = svgRef.current.getBoundingClientRect();
    const scaleX = SVG_SIZE / rect.width;
    const scaleY = SVG_SIZE / rect.height;
    return {
      svgX: (e.clientX - rect.left) * scaleX,
      svgY: (e.clientY - rect.top) * scaleY,
    };
  }, []);

  // Handle click on diagram
  const handleSVGClick = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    const coords = getSVGCoords(e);
    if (!coords) return;
    const { svgX, svgY } = coords;

    // Drawing mode: add vertex to current polygon
    if (drawingMode === 'draw') {
      const pos = svgToPosition(svgX, svgY);
      if (!pos) return; // Outside the diagram circle

      setCurrentVertices(prev => [...prev, { ...pos, x: svgX, y: svgY }]);
      return;
    }

    // Select mode: add analysis point (original behavior)
    if (!onPositionSelect) return;

    let nearest: {
      month: number;
      hour: number;
      pos: SolarPosition;
      dist: number;
    } | null = null;

    const visibleMonths = showAllMonths ? new Set(Array.from({ length: 12 }, (_, i) => i)) : selectedMonths;

    for (const path of monthlyPaths) {
      if (!visibleMonths.has(path.month)) continue;
      for (const pos of path.positions) {
        const { x, y } = projectToSVG(pos.azimuth, pos.altitude);
        const dist = Math.sqrt((x - svgX) ** 2 + (y - svgY) ** 2);
        if (dist < 20 && (!nearest || dist < nearest.dist)) {
          nearest = { month: path.month, hour: pos.hour, pos, dist };
        }
      }
    }

    if (nearest) {
      const roundedHour = Math.round(nearest.hour);
      const exactPos = calculateSolarPosition(
        latitude, longitude, timezone, nearest.month + 1, REP_DAY, roundedHour
      );
      onPositionSelect({
        month: MONTH_NAMES[nearest.month],
        day: REP_DAY,
        hour: roundedHour,
        altitude: exactPos.altitude,
        azimuth: exactPos.azimuth,
      });
    }
  }, [drawingMode, getSVGCoords, monthlyPaths, selectedMonths, showAllMonths, latitude, longitude, timezone, onPositionSelect]);

  // Handle double-click to close polygon
  const handleSVGDoubleClick = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (drawingMode !== 'draw' || currentVertices.length < 3) return;
    e.preventDefault();
    e.stopPropagation();

    // Close the polygon and save as obstacle
    const newObstacle: ObstaclePolygon = {
      id: Date.now().toString() + Math.random().toString(36).slice(2),
      name: newObstacleName,
      color: newObstacleColor,
      vertices: currentVertices.map(v => ({ azimuth: v.azimuth, altitude: v.altitude })),
      visible: true,
    };

    onObstaclesChange?.([...obstacles, newObstacle]);
    setCurrentVertices([]);
    // Pick next color automatically
    const usedColors = obstacles.map(o => o.color);
    const nextColor = OBSTACLE_COLORS.find(c => !usedColors.includes(c.value))?.value || OBSTACLE_COLORS[0].value;
    setNewObstacleColor(nextColor);
  }, [drawingMode, currentVertices, newObstacleName, newObstacleColor, obstacles, onObstaclesChange]);

  // Handle mouse move
  const handleSVGMouseMove = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    const coords = getSVGCoords(e);
    if (!coords) return;
    const { svgX, svgY } = coords;

    // Update cursor position for drawing preview
    if (drawingMode === 'draw') {
      setCursorPos({ x: svgX, y: svgY });
      return;
    }

    // Select mode: hover tooltip
    const visibleMonths = showAllMonths ? new Set(Array.from({ length: 12 }, (_, i) => i)) : selectedMonths;

    let nearest: {
      month: number;
      hour: number;
      pos: SolarPosition;
      dist: number;
      svgX: number;
      svgY: number;
    } | null = null;

    for (const path of monthlyPaths) {
      if (!visibleMonths.has(path.month)) continue;
      for (const pos of path.positions) {
        const { x, y } = projectToSVG(pos.azimuth, pos.altitude);
        const dist = Math.sqrt((x - svgX) ** 2 + (y - svgY) ** 2);
        if (dist < 15 && (!nearest || dist < nearest.dist)) {
          nearest = { month: path.month, hour: pos.hour, pos, dist, svgX: x, svgY: y };
        }
      }
    }

    if (nearest) {
      setHoveredPoint({
        month: nearest.month,
        hour: nearest.hour,
        pos: nearest.pos,
        svgX: nearest.svgX,
        svgY: nearest.svgY,
      });
    } else {
      setHoveredPoint(null);
    }
  }, [drawingMode, getSVGCoords, monthlyPaths, selectedMonths, showAllMonths]);

  // Cancel drawing with Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && drawingMode === 'draw') {
        setCurrentVertices([]);
        setDrawingMode('select');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [drawingMode]);

  const toggleMonth = (m: number) => {
    setSelectedMonths(prev => {
      const next = new Set(prev);
      if (next.has(m)) {
        next.delete(m);
      } else {
        next.add(m);
      }
      return next;
    });
  };

  const visibleMonths = showAllMonths ? new Set(Array.from({ length: 12 }, (_, i) => i)) : selectedMonths;

  const generatePathD = (positions: Array<SolarPosition & { hour: number }>): string => {
    if (positions.length === 0) return '';
    const points = positions.map(p => projectToSVG(p.azimuth, p.altitude));
    return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
  };

  const deleteObstacle = (id: string) => {
    onObstaclesChange?.(obstacles.filter(o => o.id !== id));
  };

  const toggleObstacleVisibility = (id: string) => {
    onObstaclesChange?.(obstacles.map(o => o.id === id ? { ...o, visible: !o.visible } : o));
  };

  const renameObstacle = (id: string, name: string) => {
    onObstaclesChange?.(obstacles.map(o => o.id === id ? { ...o, name } : o));
    setEditingObstacleId(null);
  };

  const undoLastVertex = () => {
    setCurrentVertices(prev => prev.slice(0, -1));
  };

  const cancelDrawing = () => {
    setCurrentVertices([]);
    setDrawingMode('select');
  };

  const finishPolygon = () => {
    if (currentVertices.length < 3) return;
    const newObstacle: ObstaclePolygon = {
      id: Date.now().toString() + Math.random().toString(36).slice(2),
      name: newObstacleName,
      color: newObstacleColor,
      vertices: currentVertices.map(v => ({ azimuth: v.azimuth, altitude: v.altitude })),
      visible: true,
    };
    onObstaclesChange?.([...obstacles, newObstacle]);
    setCurrentVertices([]);
    const usedColors = [...obstacles, newObstacle].map(o => o.color);
    const nextColor = OBSTACLE_COLORS.find(c => !usedColors.includes(c.value))?.value || OBSTACLE_COLORS[0].value;
    setNewObstacleColor(nextColor);
  };

  // Count shaded analysis points
  const shadedPointsCount = useMemo(() => {
    if (obstacles.length === 0) return 0;
    return analysisPoints.filter(pt => {
      const hits = getObstaclesAtPoint(pt.azimuthSolar, pt.heightSolar, obstacles);
      return hits.length > 0;
    }).length;
  }, [analysisPoints, obstacles]);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
          ☀️ Diagrama de Trayectoria Solar
        </h3>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-gray-500">Lat: {latitude.toFixed(2)}° | Lon: {longitude.toFixed(2)}°</span>
        </div>
      </div>

      <p className="text-xs text-gray-500 mb-3">
        {drawingMode === 'draw'
          ? 'Modo dibujo: Haz clic para agregar vértices del polígono de sombra. Doble-clic o botón "Cerrar" para finalizar. Esc para cancelar.'
          : 'Haz clic en cualquier punto de la trayectoria para agregar un punto de análisis. Usa "Dibujar Obstáculo" para trazar polígonos de sombra.'
        }
      </p>

      {/* Controls Row 1: View modes */}
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <button
          onClick={() => setShowAllMonths(!showAllMonths)}
          className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
            showAllMonths
              ? 'bg-amber-100 text-amber-800 border border-amber-300'
              : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
          }`}
        >
          {showAllMonths ? '12 meses' : 'Selección'}
        </button>
        <button
          onClick={() => setShowHourLines(!showHourLines)}
          className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
            showHourLines
              ? 'bg-blue-100 text-blue-800 border border-blue-300'
              : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
          }`}
        >
          Líneas horarias
        </button>
        <button
          onClick={() => setShowAnalogic(!showAnalogic)}
          className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
            showAnalogic
              ? 'bg-purple-100 text-purple-800 border border-purple-300'
              : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
          }`}
        >
          Analema
        </button>

        <div className="w-px h-5 bg-gray-300 mx-1" />

        {/* Drawing controls */}
        {onObstaclesChange && (
          <>
            <button
              onClick={() => {
                if (drawingMode === 'draw') {
                  cancelDrawing();
                } else {
                  setDrawingMode('draw');
                  setShowObstaclePanel(true);
                }
              }}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                drawingMode === 'draw'
                  ? 'bg-red-100 text-red-800 border border-red-300'
                  : 'bg-orange-100 text-orange-700 border border-orange-300 hover:bg-orange-200'
              }`}
            >
              {drawingMode === 'draw' ? '✕ Cancelar Dibujo' : '✏️ Dibujar Obstáculo'}
            </button>

            {obstacles.length > 0 && (
              <button
                onClick={() => setShowObstaclePanel(!showObstaclePanel)}
                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                  showObstaclePanel
                    ? 'bg-gray-200 text-gray-800 border border-gray-400'
                    : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
                }`}
              >
                🏗️ Obstáculos ({obstacles.length})
              </button>
            )}
          </>
        )}
      </div>

      {/* Drawing toolbar (when in draw mode) */}
      {drawingMode === 'draw' && onObstaclesChange && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 mb-3 space-y-2">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1.5">
              <label className="text-xs font-medium text-gray-700">Nombre:</label>
              <select
                value={newObstacleName}
                onChange={(e) => setNewObstacleName(e.target.value)}
                className="text-xs border border-gray-300 rounded px-1.5 py-0.5 bg-white"
              >
                {OBSTACLE_PRESETS.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-1.5">
              <label className="text-xs font-medium text-gray-700">Color:</label>
              <div className="flex gap-1">
                {OBSTACLE_COLORS.map(c => (
                  <button
                    key={c.value}
                    onClick={() => setNewObstacleColor(c.value)}
                    className={`w-5 h-5 rounded-full border-2 transition-all ${
                      newObstacleColor === c.value ? 'border-gray-800 scale-110' : 'border-gray-300'
                    }`}
                    style={{ backgroundColor: c.value }}
                    title={c.name}
                  />
                ))}
              </div>
            </div>
            <div className="flex items-center gap-1.5 ml-auto">
              <span className="text-xs text-gray-500">
                {currentVertices.length} vértice{currentVertices.length !== 1 ? 's' : ''}
              </span>
              {currentVertices.length > 0 && (
                <button
                  onClick={undoLastVertex}
                  className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200"
                >
                  ↩ Deshacer
                </button>
              )}
              {currentVertices.length >= 3 && (
                <button
                  onClick={finishPolygon}
                  className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 border border-green-300 hover:bg-green-200"
                >
                  ✓ Cerrar Polígono
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Obstacle management panel */}
      {showObstaclePanel && obstacles.length > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-3">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-bold text-gray-700">🏗️ Obstáculos Dibujados</h4>
            {shadedPointsCount > 0 && (
              <span className="text-[10px] bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
                {shadedPointsCount} punto{shadedPointsCount !== 1 ? 's' : ''} sombreado{shadedPointsCount !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <div className="space-y-1.5">
            {obstacles.map(obs => (
              <div key={obs.id} className="flex items-center gap-2 bg-white rounded px-2 py-1.5 border border-gray-100">
                <span
                  className="w-3 h-3 rounded-sm flex-shrink-0"
                  style={{ backgroundColor: obs.color, opacity: obs.visible ? 1 : 0.3 }}
                />
                {editingObstacleId === obs.id ? (
                  <input
                    autoFocus
                    className="text-xs border border-blue-300 rounded px-1 py-0.5 flex-1 min-w-0"
                    defaultValue={obs.name}
                    onBlur={(e) => renameObstacle(obs.id, e.target.value || obs.name)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') renameObstacle(obs.id, (e.target as HTMLInputElement).value || obs.name);
                      if (e.key === 'Escape') setEditingObstacleId(null);
                    }}
                  />
                ) : (
                  <span
                    className="text-xs text-gray-700 flex-1 min-w-0 truncate cursor-pointer hover:text-blue-600"
                    onClick={() => setEditingObstacleId(obs.id)}
                    title="Clic para renombrar"
                  >
                    {obs.name}
                  </span>
                )}
                <span className="text-[10px] text-gray-400">{obs.vertices.length}v</span>
                <button
                  onClick={() => toggleObstacleVisibility(obs.id)}
                  className={`text-xs px-1 rounded ${obs.visible ? 'text-blue-600 hover:text-blue-800' : 'text-gray-400 hover:text-gray-600'}`}
                  title={obs.visible ? 'Ocultar' : 'Mostrar'}
                >
                  {obs.visible ? '👁️' : '👁️‍🗨️'}
                </button>
                <button
                  onClick={() => deleteObstacle(obs.id)}
                  className="text-xs text-red-400 hover:text-red-600 px-1"
                  title="Eliminar"
                >
                  🗑️
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Month selector */}
      {!showAllMonths && (
        <div className="flex flex-wrap gap-1 mb-3">
          {MONTH_NAMES.map((name, i) => (
            <button
              key={i}
              onClick={() => toggleMonth(i)}
              className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors border ${
                selectedMonths.has(i)
                  ? 'text-white border-transparent'
                  : 'bg-gray-50 text-gray-400 border-gray-200 hover:bg-gray-100'
              }`}
              style={selectedMonths.has(i) ? { backgroundColor: MONTH_COLORS[i] } : {}}
            >
              {name}
            </button>
          ))}
          <button
            onClick={() => setSelectedMonths(new Set(Array.from({ length: 12 }, (_, i) => i)))}
            className="px-2 py-0.5 rounded text-[10px] font-medium text-blue-600 bg-blue-50 border border-blue-200 hover:bg-blue-100"
          >
            Todos
          </button>
          <button
            onClick={() => setSelectedMonths(new Set([0, 2, 5, 8, 11]))}
            className="px-2 py-0.5 rounded text-[10px] font-medium text-gray-600 bg-gray-50 border border-gray-200 hover:bg-gray-100"
          >
            Solsticios/Equinoccios
          </button>
        </div>
      )}

      {/* SVG Diagram */}
      <div className="relative flex justify-center">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${SVG_SIZE} ${SVG_SIZE}`}
          className={`w-full max-w-[550px] ${drawingMode === 'draw' ? 'cursor-crosshair' : 'cursor-crosshair'}`}
          onClick={handleSVGClick}
          onDoubleClick={handleSVGDoubleClick}
          onMouseMove={handleSVGMouseMove}
          onMouseLeave={() => {
            setHoveredPoint(null);
            setCursorPos(null);
          }}
        >
          {/* Background */}
          <rect width={SVG_SIZE} height={SVG_SIZE} fill="#f8fafc" rx="8" />

          {/* Altitude circles (every 10°) */}
          {[0, 10, 20, 30, 40, 50, 60, 70, 80, 90].map(alt => {
            const r = RADIUS * (90 - alt) / 90;
            return (
              <g key={`alt-${alt}`}>
                <circle
                  cx={CENTER}
                  cy={CENTER}
                  r={r}
                  fill="none"
                  stroke={alt === 0 ? '#94a3b8' : '#e2e8f0'}
                  strokeWidth={alt === 0 ? 1.5 : 0.5}
                  strokeDasharray={alt === 0 ? 'none' : '4 4'}
                />
                {alt > 0 && alt < 90 && (
                  <text
                    x={CENTER + 4}
                    y={CENTER - r + 12}
                    fill="#94a3b8"
                    fontSize="9"
                    fontFamily="monospace"
                  >
                    {alt}°
                  </text>
                )}
              </g>
            );
          })}

          {/* Azimuth lines (every 30°) */}
          {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map(az => {
            const angleRad = (az - 90) * Math.PI / 180;
            const x2 = CENTER + RADIUS * Math.cos(angleRad);
            const y2 = CENTER + RADIUS * Math.sin(angleRad);
            const labelR = RADIUS + 18;
            const lx = CENTER + labelR * Math.cos(angleRad);
            const ly = CENTER + labelR * Math.sin(angleRad);

            const labels: Record<number, string> = {
              0: 'N', 30: '30°', 60: '60°', 90: 'E', 120: '120°', 150: '150°',
              180: 'S', 210: '210°', 240: '240°', 270: 'O', 300: '300°', 330: '330°',
            };

            const isCardinal = [0, 90, 180, 270].includes(az);

            return (
              <g key={`az-${az}`}>
                <line
                  x1={CENTER}
                  y1={CENTER}
                  x2={x2}
                  y2={y2}
                  stroke={isCardinal ? '#cbd5e1' : '#e2e8f0'}
                  strokeWidth={isCardinal ? 1 : 0.5}
                  strokeDasharray={isCardinal ? 'none' : '2 4'}
                />
                <text
                  x={lx}
                  y={ly}
                  fill={isCardinal ? '#475569' : '#94a3b8'}
                  fontSize={isCardinal ? '12' : '9'}
                  fontWeight={isCardinal ? 'bold' : 'normal'}
                  fontFamily="monospace"
                  textAnchor="middle"
                  dominantBaseline="middle"
                >
                  {labels[az]}
                </text>
              </g>
            );
          })}

          {/* Saved obstacle polygons */}
          {obstacles.map(obs => {
            if (!obs.visible || obs.vertices.length < 3) return null;
            const svgPoints = obs.vertices.map(v => projectToSVG(v.azimuth, v.altitude));
            const pathD = svgPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ') + ' Z';
            return (
              <g key={`obs-${obs.id}`}>
                <path
                  d={pathD}
                  fill={obs.color}
                  fillOpacity={0.2}
                  stroke={obs.color}
                  strokeWidth="2"
                  strokeDasharray="6 3"
                  strokeOpacity={0.8}
                />
                {/* Vertex dots */}
                {svgPoints.map((p, i) => (
                  <circle
                    key={`obs-v-${obs.id}-${i}`}
                    cx={p.x}
                    cy={p.y}
                    r="3"
                    fill={obs.color}
                    stroke="white"
                    strokeWidth="1"
                  />
                ))}
                {/* Label at centroid */}
                {(() => {
                  const cx = svgPoints.reduce((s, p) => s + p.x, 0) / svgPoints.length;
                  const cy = svgPoints.reduce((s, p) => s + p.y, 0) / svgPoints.length;
                  return (
                    <text
                      x={cx}
                      y={cy}
                      fill={obs.color}
                      fontSize="10"
                      fontWeight="bold"
                      fontFamily="sans-serif"
                      textAnchor="middle"
                      dominantBaseline="middle"
                      style={{ textShadow: '0 0 3px white, 0 0 3px white, 0 0 3px white' }}
                    >
                      {obs.name}
                    </text>
                  );
                })()}
              </g>
            );
          })}

          {/* Current drawing polygon (in progress) */}
          {drawingMode === 'draw' && currentVertices.length > 0 && (
            <g>
              {/* Filled preview if 3+ vertices */}
              {currentVertices.length >= 3 && (
                <path
                  d={currentVertices.map((v, i) => `${i === 0 ? 'M' : 'L'} ${v.x.toFixed(1)} ${v.y.toFixed(1)}`).join(' ') + ' Z'}
                  fill={newObstacleColor}
                  fillOpacity={0.15}
                  stroke="none"
                />
              )}
              {/* Lines between vertices */}
              <path
                d={
                  currentVertices.map((v, i) => `${i === 0 ? 'M' : 'L'} ${v.x.toFixed(1)} ${v.y.toFixed(1)}`).join(' ')
                  + (cursorPos ? ` L ${cursorPos.x.toFixed(1)} ${cursorPos.y.toFixed(1)}` : '')
                }
                fill="none"
                stroke={newObstacleColor}
                strokeWidth="2"
                strokeDasharray="4 2"
                opacity={0.8}
              />
              {/* Closing line preview (from cursor to first vertex) */}
              {currentVertices.length >= 2 && cursorPos && (
                <line
                  x1={cursorPos.x}
                  y1={cursorPos.y}
                  x2={currentVertices[0].x}
                  y2={currentVertices[0].y}
                  stroke={newObstacleColor}
                  strokeWidth="1"
                  strokeDasharray="2 4"
                  opacity={0.4}
                />
              )}
              {/* Vertex dots */}
              {currentVertices.map((v, i) => (
                <circle
                  key={`cv-${i}`}
                  cx={v.x}
                  cy={v.y}
                  r="4"
                  fill={newObstacleColor}
                  stroke="white"
                  strokeWidth="2"
                />
              ))}
              {/* Cursor dot */}
              {cursorPos && (
                <circle
                  cx={cursorPos.x}
                  cy={cursorPos.y}
                  r="3"
                  fill={newObstacleColor}
                  opacity={0.5}
                />
              )}
            </g>
          )}

          {/* Hour lines */}
          {hourLines.map(({ hour, points }) => {
            if (points.length < 2) return null;
            const d = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
            const midIdx = Math.floor(points.length / 2);
            const midPoint = points[midIdx];
            return (
              <g key={`hour-${hour}`}>
                <path
                  d={d}
                  fill="none"
                  stroke="#d1d5db"
                  strokeWidth="0.7"
                  strokeDasharray="3 3"
                />
                {midPoint && (
                  <text
                    x={midPoint.x}
                    y={midPoint.y - 6}
                    fill="#9ca3af"
                    fontSize="8"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    {hour}h
                  </text>
                )}
              </g>
            );
          })}

          {/* Analemma */}
          {showAnalogic && (() => {
            const points: Array<{ x: number; y: number }> = [];
            for (let m = 0; m < 12; m++) {
              for (let d = 1; d <= 28; d += 7) {
                const pos = calculateSolarPosition(latitude, longitude, timezone, m + 1, d, 12);
                if (pos.altitude > 0) {
                  points.push(projectToSVG(pos.azimuth, pos.altitude));
                }
              }
            }
            if (points.length > 2) {
              const first = calculateSolarPosition(latitude, longitude, timezone, 1, 1, 12);
              if (first.altitude > 0) points.push(projectToSVG(first.azimuth, first.altitude));
            }
            if (points.length < 2) return null;
            const d = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
            return (
              <path
                d={d}
                fill="none"
                stroke="#a855f7"
                strokeWidth="1.5"
                strokeDasharray="4 2"
                opacity={0.7}
              />
            );
          })()}

          {/* Solar paths for each visible month */}
          {monthlyPaths.map(({ month, positions }) => {
            if (!visibleMonths.has(month) || positions.length === 0) return null;
            const pathD = generatePathD(positions);
            return (
              <g key={`path-${month}`}>
                <path
                  d={pathD}
                  fill="none"
                  stroke={MONTH_COLORS[month]}
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  opacity={0.85}
                />
                {/* Hour markers */}
                {positions
                  .filter(p => p.hour === Math.round(p.hour) && p.hour >= 5 && p.hour <= 19)
                  .map(p => {
                    const { x, y } = projectToSVG(p.azimuth, p.altitude);
                    // Check if this point is inside an obstacle
                    const isShaded = obstacles.some(obs =>
                      obs.visible && obs.vertices.length >= 3 &&
                      pointInPolygon(x, y, obs.vertices.map(v => projectToSVG(v.azimuth, v.altitude)))
                    );
                    return (
                      <g key={`dot-${month}-${p.hour}`}>
                        <circle
                          cx={x}
                          cy={y}
                          r="3.5"
                          fill={isShaded ? '#6b7280' : MONTH_COLORS[month]}
                          stroke={isShaded ? '#374151' : 'white'}
                          strokeWidth="1.5"
                          className="cursor-pointer"
                        />
                        {isShaded && (
                          <line
                            x1={x - 2.5}
                            y1={y - 2.5}
                            x2={x + 2.5}
                            y2={y + 2.5}
                            stroke="#374151"
                            strokeWidth="1"
                          />
                        )}
                      </g>
                    );
                  })}
                {/* Month label at solar noon */}
                {(() => {
                  const noonPos = positions.find(p => Math.abs(p.hour - 12) < 0.3);
                  if (!noonPos) return null;
                  const { x, y } = projectToSVG(noonPos.azimuth, noonPos.altitude);
                  return (
                    <text
                      x={x}
                      y={y - 10}
                      fill={MONTH_COLORS[month]}
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="sans-serif"
                      textAnchor="middle"
                    >
                      {MONTH_NAMES[month]}
                    </text>
                  );
                })()}
              </g>
            );
          })}

          {/* Analysis points from shading table */}
          {analysisPoints.map((pt, i) => {
            const { x, y } = projectToSVG(pt.azimuthSolar, pt.heightSolar);
            if (x < 0 || x > SVG_SIZE || y < 0 || y > SVG_SIZE) return null;
            const fsColor = pt.fs >= 0.9 ? '#22c55e' : pt.fs >= 0.7 ? '#eab308' : '#ef4444';
            return (
              <g key={`ap-${i}`}>
                <circle cx={x} cy={y} r="7" fill={fsColor} stroke="white" strokeWidth="2" opacity={0.9} />
                <text
                  x={x}
                  y={y + 18}
                  fill="#374151"
                  fontSize="8"
                  fontWeight="bold"
                  fontFamily="monospace"
                  textAnchor="middle"
                >
                  {pt.month} {pt.hour}h FS:{pt.fs.toFixed(2)}
                </text>
              </g>
            );
          })}

          {/* Current sun position */}
          {currentSunPos && (
            <g>
              <circle cx={currentSunPos.x} cy={currentSunPos.y} r="10" fill="#fbbf24" stroke="#f59e0b" strokeWidth="2" opacity={0.9}>
                <animate attributeName="r" values="8;12;8" dur="2s" repeatCount="indefinite" />
              </circle>
              <circle cx={currentSunPos.x} cy={currentSunPos.y} r="4" fill="#f59e0b" />
              <text
                x={currentSunPos.x}
                y={currentSunPos.y - 16}
                fill="#92400e"
                fontSize="9"
                fontWeight="bold"
                fontFamily="sans-serif"
                textAnchor="middle"
              >
                Ahora
              </text>
            </g>
          )}

          {/* Hover tooltip (only in select mode) */}
          {drawingMode === 'select' && hoveredPoint && (
            <g>
              <circle
                cx={hoveredPoint.svgX}
                cy={hoveredPoint.svgY}
                r="6"
                fill="none"
                stroke="#1e40af"
                strokeWidth="2"
              >
                <animate attributeName="r" values="5;8;5" dur="1s" repeatCount="indefinite" />
              </circle>
              <rect
                x={Math.min(hoveredPoint.svgX + 12, SVG_SIZE - 155)}
                y={Math.max(hoveredPoint.svgY - 40, 5)}
                width="140"
                height="55"
                rx="4"
                fill="white"
                stroke="#cbd5e1"
                strokeWidth="1"
                opacity={0.95}
              />
              <text x={Math.min(hoveredPoint.svgX + 18, SVG_SIZE - 149)} y={Math.max(hoveredPoint.svgY - 24, 21)} fill="#1e3a5f" fontSize="10" fontWeight="bold" fontFamily="sans-serif">
                {MONTH_NAMES[hoveredPoint.month]} 21 — {Math.round(hoveredPoint.hour)}:00h
              </text>
              <text x={Math.min(hoveredPoint.svgX + 18, SVG_SIZE - 149)} y={Math.max(hoveredPoint.svgY - 10, 35)} fill="#475569" fontSize="9" fontFamily="monospace">
                Alt: {hoveredPoint.pos.altitude.toFixed(1)}° | Az: {hoveredPoint.pos.azimuth.toFixed(1)}°
              </text>
              <text x={Math.min(hoveredPoint.svgX + 18, SVG_SIZE - 149)} y={Math.max(hoveredPoint.svgY + 4, 49)} fill="#2563eb" fontSize="9" fontWeight="bold" fontFamily="sans-serif">
                Clic para agregar punto
              </text>
            </g>
          )}

          {/* Drawing mode cursor tooltip */}
          {drawingMode === 'draw' && cursorPos && (
            <g>
              {(() => {
                const pos = svgToPosition(cursorPos.x, cursorPos.y);
                if (!pos) return null;
                return (
                  <>
                    <rect
                      x={Math.min(cursorPos.x + 15, SVG_SIZE - 130)}
                      y={Math.max(cursorPos.y - 30, 5)}
                      width="120"
                      height="35"
                      rx="4"
                      fill="white"
                      stroke={newObstacleColor}
                      strokeWidth="1"
                      opacity={0.9}
                    />
                    <text
                      x={Math.min(cursorPos.x + 21, SVG_SIZE - 124)}
                      y={Math.max(cursorPos.y - 14, 21)}
                      fill="#374151"
                      fontSize="9"
                      fontFamily="monospace"
                    >
                      Alt: {pos.altitude.toFixed(1)}°
                    </text>
                    <text
                      x={Math.min(cursorPos.x + 21, SVG_SIZE - 124)}
                      y={Math.max(cursorPos.y - 2, 33)}
                      fill="#374151"
                      fontSize="9"
                      fontFamily="monospace"
                    >
                      Az: {pos.azimuth.toFixed(1)}°
                    </text>
                  </>
                );
              })()}
            </g>
          )}

          {/* Horizon label */}
          <text x={CENTER} y={SVG_SIZE - 8} fill="#64748b" fontSize="10" textAnchor="middle" fontFamily="sans-serif">
            Horizonte (0°) — Proyección estereográfica
          </text>
        </svg>
      </div>

      {/* Legend */}
      <div className="mt-3 flex flex-wrap items-center gap-3 text-[10px]">
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-yellow-400 border border-yellow-500 inline-block animate-pulse" />
          <span className="text-gray-600">Sol actual</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-green-500 inline-block" />
          <span className="text-gray-600">Punto FS ≥ 0.9</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-yellow-500 inline-block" />
          <span className="text-gray-600">Punto FS 0.7-0.9</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
          <span className="text-gray-600">Punto FS &lt; 0.7</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-6 h-0.5 bg-gray-300 inline-block" style={{ borderTop: '1px dashed #d1d5db' }} />
          <span className="text-gray-600">Líneas horarias</span>
        </div>
        {obstacles.length > 0 && (
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm inline-block border-2 border-dashed" style={{ borderColor: OBSTACLE_COLORS[0].value, backgroundColor: `${OBSTACLE_COLORS[0].value}33` }} />
            <span className="text-gray-600">Obstáculo</span>
          </div>
        )}
        {obstacles.length > 0 && (
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-gray-500 inline-block relative">
              <span className="absolute inset-0 flex items-center justify-center text-white" style={{ fontSize: '6px' }}>✕</span>
            </span>
            <span className="text-gray-600">Hora sombreada</span>
          </div>
        )}
      </div>

      {/* Info about interaction */}
      {drawingMode === 'select' && onPositionSelect && (
        <div className="mt-2 bg-blue-50 rounded-lg p-2 border border-blue-100 text-xs text-blue-700 flex items-center gap-2">
          <span className="text-lg">👆</span>
          <span>
            <strong>Interactivo:</strong> Haz clic en cualquier punto de una trayectoria solar para agregar
            automáticamente un nuevo punto de análisis con la altura y azimut calculados.
          </span>
        </div>
      )}

      {drawingMode === 'draw' && (
        <div className="mt-2 bg-orange-50 rounded-lg p-2 border border-orange-100 text-xs text-orange-700 flex items-center gap-2">
          <span className="text-lg">✏️</span>
          <span>
            <strong>Dibujando obstáculo:</strong> Haz clic en el diagrama para agregar vértices del polígono.
            Necesitas al menos 3 vértices. Doble-clic o botón "Cerrar Polígono" para finalizar.
            Presiona <kbd className="bg-orange-200 px-1 rounded">Esc</kbd> para cancelar.
          </span>
        </div>
      )}
    </div>
  );
}
