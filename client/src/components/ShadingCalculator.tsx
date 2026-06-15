import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Button } from '@/components/ui/button';
import * as XLSX from 'xlsx';
import { Input } from '@/components/ui/input';
import { Trash2, Plus, Download, Upload, Sun, Zap, MapPin, Building2, FileText, RefreshCw } from 'lucide-react';
import { FSDistributionChart } from './ShadingChart';
import { toast } from 'sonner';
import { EPWData, getWeatherForDateTime, getWeatherCorrectionFactor } from '@/lib/epwParser';
import { calculateSolarPosition, SolarPosition } from '@/lib/solarPosition';
import SunPathDiagram, { ObstaclePolygon, calculateShadedPercentage } from './SunPathDiagram';
import {
  MarshSiteDesignerJSON,
  MarshParseResult,
  validateMarshJSON,
  parseMarshSiteDesigner,
  getMarshFileSummary,
} from '@/lib/marshSiteDesigner';
import {
  SunPath3DJSON,
  SunPath3DParseResult,
  validateSunPath3DJSON,
  isSunPath3DJSON,
  parseSunPath3D,
  getSunPath3DSummary,
} from '@/lib/sunPath3DParser';
import {
  OBJParseResult,
  OBJObstacleResult,
  parseOBJText,
  validateOBJText,
  convertOBJToObstacles,
  getOBJSummary,
} from '@/lib/objParser';
import CrossingModal from './CrossingModal';
import { crossingResultsToAnalysisPoints, CrossingResult, FacadeDefinition } from '@/lib/shadingMaskCrossing';
import { generateShadingCrossingReport, type ShadingCrossingReportData } from '@/lib/shadingCrossingReportSection';
import EvaluationModelImporter from './EvaluationModelImporter';
import { EvaluationModel, DetectedFacade, Vertex3D, recalculateForFacade } from '@/lib/buildingModelImporter';
import FacadeComparisonTable from './FacadeComparisonTable';
import { parseGLTF, validateGLTF, getGLTFSummary } from '@/lib/gltfParser';
import { detectFormat, isUnsupportedFormat, getConversionAdvice, parseMultiFormat } from '@/lib/multiFormatParser';
import { FacadeFullAnalysis, calculateMonthlyShadingFactorsForFacade } from '@/lib/facadeShadingAnalysis';
import { normalizeMonthToAbbr } from '@/lib/monthHelper';

interface AnalysisPoint {
  id: string;
  month: string;
  day: number;
  hour: number;
  heightSolar: number;
  azimuthSolar: number;
  obstacle: string;
  shadowedArea: number;
  fs: number;
  autoCalculated?: boolean; // indica si altura/azimut fueron auto-calculados
  obstacleAutoCalculated?: boolean; // indica si el obstáculo fue auto-calculado desde polígonos
  // Campos extendidos para importación CSV/XLSX de días críticos
  evento?: string; // Equinoccio de Marzo, Solsticio de Junio, etc.
  fsGeometrico?: number; // FS geométrico (sombra por obstáculos físicos)
  fsClimatico?: number; // FS climático (sombra por nubosidad)
  situacion?: string; // Muy nublado, Parcialmente nublado, Cielo despejado, etc.
  hourStr?: string; // Hora en formato string original (ej: "07:30")
}

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

export default function ShadingCalculator({ initialPoints, templateData, weatherData, onPointsChange, onWeatherDataOverride, onFacadeAnalysis3D, onModelDataReady, externalActiveFacadeIdx }: { initialPoints?: any[] | null; templateData?: string[][] | null; weatherData?: EPWData | null; onPointsChange?: (points: Array<{month: string; day: number; hour: number; solarHeight: number; solarAzimuth: number; obstacle: string; shadedArea: number; fs: number}>) => void; onWeatherDataOverride?: (data: EPWData) => void; onFacadeAnalysis3D?: (analysis: FacadeFullAnalysis | null) => void; onModelDataReady?: (data: { facades: DetectedFacade[]; obstacleVertices3D: Vertex3D[][] | undefined; northOffset: number }) => void; externalActiveFacadeIdx?: number | null }) {
  const [autoCalcEnabled, setAutoCalcEnabled] = useState(true);
  const [showSunPath, setShowSunPath] = useState(false);
  const [obstacles, setObstacles] = useState<ObstaclePolygon[]>([]);

  // Sun Path 3D import state
  const sunPath3DFileInputRef = useRef<HTMLInputElement>(null);
  const [sunPath3DPreview, setSunPath3DPreview] = useState<SunPath3DParseResult | null>(null);
  const [sunPath3DFileName, setSunPath3DFileName] = useState<string>('');

  // OBJ import state
  const objFileInputRef = useRef<HTMLInputElement>(null);
  const [objPreview, setObjPreview] = useState<OBJObstacleResult | null>(null);
  const [objFileName, setObjFileName] = useState<string>('');
  const [objSwapYZ, setObjSwapYZ] = useState(false);
  const [objUpAxis, setObjUpAxis] = useState<'X' | 'Y' | 'Z' | 'Y_simple'>('Z');
  const [objRotationDeg, setObjRotationDeg] = useState(0);
  const [objScale, setObjScale] = useState(1.0);
  const [objNorthOffset, setObjNorthOffset] = useState(0);
  const [isDraggingObj, setIsDraggingObj] = useState(false);

  // Crossing modal state
  const [showCrossingModal, setShowCrossingModal] = useState(false);

  // Evaluation model state (edificio a evaluar)
  const [evaluationModel, setEvaluationModel] = useState<EvaluationModel | null>(null);
  const [obstacleVertices3D, setObstacleVertices3D] = useState<Vertex3D[][] | undefined>(undefined);
  const [modelFacadeDefinitions, setModelFacadeDefinitions] = useState<FacadeDefinition[] | null>(null);
  const [lastCrossingResults, setLastCrossingResults] = useState<CrossingResult[] | null>(null);
  const [lastCrossingFacades, setLastCrossingFacades] = useState<FacadeDefinition[] | null>(null);
  // Fachada/techo activa para proyección de obstáculos en el diagrama solar
  const [activeFacadeIdx, setActiveFacadeIdx] = useState<number | null>(null);

  // Función para calcular posición solar si hay datos EPW disponibles
  const getSolarPos = useCallback((month: string, day: number, hour: number): SolarPosition | null => {
    if (!weatherData || !autoCalcEnabled) return null;
    const { latitude, longitude, timezone } = weatherData.location;
    try {
      const pos = calculateSolarPosition(latitude, longitude, timezone, month, day, hour);
      return pos.altitude > -1 ? pos : null;
    } catch {
      return null;
    }
  }, [weatherData, autoCalcEnabled]);

  const getDefaultPoints = useCallback((): AnalysisPoint[] => {
    // Tabla inicia vacía - los datos se agregan manualmente, por importación CSV o por el cruce Máscara+EPW
    return [];
  }, []);

  const [points, setPoints] = useState<AnalysisPoint[]>(() => {
    if (initialPoints && initialPoints.length > 0) {
      return initialPoints.map(p => ({
        id: p.id || (Date.now().toString() + Math.random()),
        month: p.month,
        day: p.day,
        hour: p.hour,
        heightSolar: p.solarHeight,
        azimuthSolar: p.solarAzimuth,
        obstacle: p.obstacle,
        shadowedArea: p.shadedArea,
        fs: p.fs,
        autoCalculated: p.autoCalculated,
      }));
    }
    return getDefaultPoints();
  });
  const fileInputRef = useRef<HTMLInputElement>(null);
  const obstacleFileInputRef = useRef<HTMLInputElement>(null);
  const marshFileInputRef = useRef<HTMLInputElement>(null);
  const [marshPreview, setMarshPreview] = useState<MarshParseResult | null>(null);
  const [marshFileName, setMarshFileName] = useState<string>('');

  function calculateFS(shadowedArea: number): number {
    return Math.max(0, Math.min(1, 1 - shadowedArea / 100));
  }

  // Recalcular posiciones solares cuando cambian los datos EPW o se activa auto-cálculo
  useEffect(() => {
    if (!weatherData || !autoCalcEnabled) return;
    setPoints(prev => prev.map(p => {
      const pos = getSolarPos(p.month, p.day, p.hour);
      if (pos) {
        return { ...p, heightSolar: pos.altitude, azimuthSolar: pos.azimuth, autoCalculated: true };
      }
      return p;
    }));
  }, [weatherData, autoCalcEnabled, getSolarPos]);

  // Recalcular sombreado cuando cambian los obstáculos
  useEffect(() => {
    if (obstacles.length === 0) return;
    if (!weatherData) return;

    const { latitude, longitude, timezone } = weatherData.location;

    setPoints(prev => prev.map(p => {
      const monthIdx = MONTHS.indexOf(p.month) + 1;
      const shadedPct = calculateShadedPercentage(
        latitude, longitude, timezone,
        monthIdx, p.day, p.hour,
        obstacles
      );

      if (shadedPct > 0) {
        // Find which obstacle names cover this point
        const pos = calculateSolarPosition(latitude, longitude, timezone, monthIdx, p.day, p.hour);
        const obstacleNames: string[] = [];
        for (const obs of obstacles) {
          if (!obs.visible || obs.vertices.length < 3) continue;
          // Use the exported function from SunPathDiagram
          const svgPoly = obs.vertices.map(v => {
            const compassAz = (v.azimuth + 180) % 360;
            const r = 250 * (90 - v.altitude) / 90;
            const angleRad = (compassAz - 90) * Math.PI / 180;
            return { x: 300 + r * Math.cos(angleRad), y: 300 + r * Math.sin(angleRad) };
          });
          // Point in polygon check
          const compassAzPt = (pos.azimuth + 180) % 360;
          const rPt = 250 * (90 - pos.altitude) / 90;
          const angleRadPt = (compassAzPt - 90) * Math.PI / 180;
          const px = 300 + rPt * Math.cos(angleRadPt);
          const py = 300 + rPt * Math.sin(angleRadPt);
          let inside = false;
          for (let i = 0, j = svgPoly.length - 1; i < svgPoly.length; j = i++) {
            const xi = svgPoly[i].x, yi = svgPoly[i].y;
            const xj = svgPoly[j].x, yj = svgPoly[j].y;
            if (((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) {
              inside = !inside;
            }
          }
          if (inside) obstacleNames.push(obs.name);
        }

        const newShadowedArea = Math.max(p.obstacleAutoCalculated ? 0 : p.shadowedArea, shadedPct);
        return {
          ...p,
          obstacle: obstacleNames.length > 0 ? obstacleNames.join(', ') : p.obstacle,
          shadowedArea: newShadowedArea,
          fs: calculateFS(newShadowedArea),
          obstacleAutoCalculated: true,
        };
      } else if (p.obstacleAutoCalculated) {
        // Point was previously auto-shaded but obstacle no longer covers it
        return {
          ...p,
          obstacle: '',
          shadowedArea: 0,
          fs: 1.0,
          obstacleAutoCalculated: false,
        };
      }
      return p;
    }));
  }, [obstacles, weatherData]);

  useEffect(() => {
    if (templateData && templateData.length > 1) {
      const newPoints: AnalysisPoint[] = [];
      
      for (let i = 1; i < templateData.length; i++) {
        const values = templateData[i];
        const month = normalizeMonthToAbbr(values[0]);
        const day = parseInt(values[1]) || 21;
        const hour = parseInt(values[2]) || 12;
        const pos = getSolarPos(month, day, hour);
        const heightSolar = pos ? pos.altitude : (parseFloat(values[3]) || 45);
        const azimuthSolar = pos ? pos.azimuth : (parseFloat(values[4]) || 0);
        const obstacle = values[5] || '';
        const shadowedArea = parseFloat(values[6]) || 0;

        newPoints.push({
          id: Date.now().toString() + Math.random(),
          month,
          day,
          hour,
          heightSolar,
          azimuthSolar,
          obstacle,
          shadowedArea,
          fs: calculateFS(shadowedArea),
          autoCalculated: !!pos,
        });
      }
      
      if (newPoints.length > 0) {
        setPoints(newPoints);
        toast.success(`Se cargaron ${newPoints.length} puntos de análisis${weatherData ? ' (posición solar auto-calculada)' : ''}`);
      }
    }
  }, [templateData]);

  const updatePoint = (id: string, field: keyof AnalysisPoint, value: any) => {
    setPoints(prev => prev.map(p => {
      if (p.id === id) {
        const updated = { ...p, [field]: value };
        if (field === 'shadowedArea') {
          updated.fs = calculateFS(Number(value));
          updated.obstacleAutoCalculated = false; // Manual override
        }
        if ((field === 'month' || field === 'day' || field === 'hour') && autoCalcEnabled && weatherData) {
          const newMonth = field === 'month' ? String(value) : updated.month;
          const newDay = field === 'day' ? Number(value) : updated.day;
          const newHour = field === 'hour' ? Number(value) : updated.hour;
          const pos = getSolarPos(newMonth, newDay, newHour);
          if (pos) {
            updated.heightSolar = pos.altitude;
            updated.azimuthSolar = pos.azimuth;
            updated.autoCalculated = true;
          }
        }
        if (field === 'heightSolar' || field === 'azimuthSolar') {
          updated.autoCalculated = false;
        }
        if (field === 'obstacle') {
          updated.obstacleAutoCalculated = false;
        }
        return updated;
      }
      return p;
    }));
  };

  const addPoint = () => {
    const pos = getSolarPos('Ene', 21, 12);
    const newPoint: AnalysisPoint = {
      id: Date.now().toString(),
      month: 'Ene',
      day: 21,
      hour: 12,
      heightSolar: pos ? pos.altitude : 45,
      azimuthSolar: pos ? pos.azimuth : 0,
      obstacle: '',
      shadowedArea: 0,
      fs: 1.0,
      autoCalculated: !!pos,
    };
    setPoints(prev => [...prev, newPoint]);
  };

  const deletePoint = (id: string) => {
    setPoints(prev => prev.filter(p => p.id !== id));
  };

  // Handler para resultados del cruce máscara + EPW
  const handleCrossingResults = (crossingPoints: ReturnType<typeof crossingResultsToAnalysisPoints>) => {
    setPoints(crossingPoints as AnalysisPoint[]);
    toast.success(`Se generaron ${crossingPoints.length} puntos de análisis desde el cruce Máscara + EPW`);
  };

  // Handler para almacenar resultados crudos del cruce (para PDF)
  const handleRawCrossingResults = (results: CrossingResult[], facades: FacadeDefinition[]) => {
    setLastCrossingResults(results);
    setLastCrossingFacades(facades);
  };

  // Exportar PDF con resultados del cruce
  const exportCrossingPDF = () => {
    if (!lastCrossingResults || lastCrossingResults.length === 0) {
      toast.error('No hay resultados del cruce Máscara + EPW para exportar. Ejecuta el cruce primero.');
      return;
    }
    try {
      const reportData: ShadingCrossingReportData = {
        crossingResults: lastCrossingResults,
        facades: lastCrossingFacades || [],
        evaluationModel: evaluationModel,
        latitude: weatherData?.location.latitude || 0,
        longitude: weatherData?.location.longitude || 0,
        cityName: weatherData?.location.city || 'Solar Site',
        elevation: weatherData?.location.elevation || 0,
      };
      generateShadingCrossingReport(reportData);
      toast.success('PDF de análisis de sombreado generado correctamente');
    } catch (err: any) {
      toast.error(`Error al generar PDF: ${err.message}`);
    }
  };

  const handleModelImported = (result: {
    model: EvaluationModel;
    recalculatedObstacles: ObstaclePolygon[];
    facadeDefinitions: FacadeDefinition[];
    selectedFacade: DetectedFacade | null;
  }) => {
    setEvaluationModel(result.model);
    setModelFacadeDefinitions(result.facadeDefinitions);
    
    // Si hay obstáculos recalculados desde la perspectiva del modelo, actualizar
    if (result.recalculatedObstacles.length > 0) {
      setObstacles(result.recalculatedObstacles);
      toast.info(
        `Obstáculos recalculados desde la perspectiva del modelo (${result.recalculatedObstacles.length} visibles)`
      );
    }
    
    // Seleccionar la primera fachada por defecto para el diagrama solar
    if (result.model.detectedFacades.length > 0) {
      setActiveFacadeIdx(0);
    }
    
    // Notificar al padre con la lista de fachadas para el selector del Simulador
    if (onModelDataReady) {
      onModelDataReady({
        facades: result.model.detectedFacades,
        obstacleVertices3D: undefined, // Se actualizará en el useEffect
        northOffset: result.model.config.northOffset,
      });
    }
    
    // Mostrar diagrama solar
    if (!showSunPath && weatherData) {
      setShowSunPath(true);
    }
  };

  // Cuando cambia la fachada activa, recalcular obstáculos desde esa perspectiva
  const handleActiveFacadeChange = useCallback((idx: number) => {
    if (!evaluationModel) return;
    setActiveFacadeIdx(idx);
    
    const facade = evaluationModel.detectedFacades[idx];
    if (!facade) return;
    
    if (obstacleVertices3D && obstacleVertices3D.length > 0) {
      // Recalcular obstáculos del entorno desde el punto de evaluación de esta fachada
      const northOff = evaluationModel.config.northOffset;
      const recalculated = recalculateForFacade(facade, obstacleVertices3D, northOff);
      setObstacles(recalculated);
      toast.info(
        `Vista desde ${facade.name}: ${recalculated.length} obstáculo(s) visible(s) desde el punto de evaluación`
      );
    } else {
      // No hay obstáculos 3D del entorno, pero mostramos info de la fachada
      toast.info(
        `Fachada activa: ${facade.name} (Az: ${facade.azimuthNormal.toFixed(0)}°, Incl: ${facade.tilt.toFixed(0)}°, Área: ${facade.area.toFixed(1)} m²)`
      );
    }
  }, [evaluationModel, obstacleVertices3D]);

  const recalculateAllPositions = () => {
    if (!weatherData) {
      toast.error('Carga un archivo EPW primero para calcular posiciones solares');
      return;
    }
    setPoints(prev => prev.map(p => {
      const pos = getSolarPos(p.month, p.day, p.hour);
      if (pos) {
        return { ...p, heightSolar: pos.altitude, azimuthSolar: pos.azimuth, autoCalculated: true };
      }
      return p;
    }));
    toast.success('Posiciones solares recalculadas para todos los puntos');
  };

  const stats = useMemo(() => {
    if (points.length === 0) return { avg: 0, min: 0, max: 0, count: 0 };
    const fsValues = points.map(p => p.fs);
    return {
      avg: (fsValues.reduce((a, b) => a + b, 0) / fsValues.length).toFixed(3),
      min: Math.min(...fsValues).toFixed(3),
      max: Math.max(...fsValues).toFixed(3),
      count: points.length,
    };
  }, [points]);

  // Notificar al padre cuando cambian los puntos de sombreado
  useEffect(() => {
    if (onPointsChange) {
      onPointsChange(points.map(p => ({
        month: p.month,
        day: p.day,
        hour: p.hour,
        solarHeight: p.heightSolar,
        solarAzimuth: p.azimuthSolar,
        obstacle: p.obstacle,
        shadedArea: p.shadowedArea,
        fs: p.fs,
      })));
    }
  }, [points, onPointsChange]);

  // === NOTIFICAR AL PADRE CUANDO CAMBIAN LOS DATOS DEL MODELO ===
  useEffect(() => {
    if (!evaluationModel || !onModelDataReady) return;
    onModelDataReady({
      facades: evaluationModel.detectedFacades,
      obstacleVertices3D,
      northOffset: evaluationModel.config.northOffset,
    });
  }, [evaluationModel, obstacleVertices3D, onModelDataReady]);

  // === REACCIONAR A CAMBIO DE FACHADA DESDE EL SIMULADOR ===
  useEffect(() => {
    if (externalActiveFacadeIdx !== undefined && externalActiveFacadeIdx !== null && externalActiveFacadeIdx !== activeFacadeIdx) {
      handleActiveFacadeChange(externalActiveFacadeIdx);
    }
  }, [externalActiveFacadeIdx]);

  // === AUTO-CÁLCULO DE FS MENSUALES DESDE MODELO 3D ===
  // Cuando hay modelo 3D + obstáculos + fachada activa + EPW,
  // calcular automáticamente los FS mensuales y enviarlos al Simulador de Energía
  useEffect(() => {
    if (!evaluationModel || activeFacadeIdx === null || !weatherData || !onFacadeAnalysis3D) return;
    const facade = evaluationModel.detectedFacades[activeFacadeIdx];
    if (!facade) return;

    // Calcular FS mensuales para la fachada activa
    const analysis = calculateMonthlyShadingFactorsForFacade(
      facade,
      weatherData,
      obstacleVertices3D || [],
      0, // northOffset (0 si no hay rotación del modelo)
    );
    analysis.facadeIdx = activeFacadeIdx;
    onFacadeAnalysis3D(analysis);
  }, [evaluationModel, activeFacadeIdx, weatherData, obstacleVertices3D, onFacadeAnalysis3D]);

  const exportToCSV = () => {
    // Detectar si hay datos extendidos (formato días críticos)
    const hasExtended = points.some(p => p.evento || p.fsClimatico !== undefined);

    const headers = hasExtended
      ? ['Evento', 'Mes', 'Dia', 'Hora', 'Altura Solar (deg)', 'Acimut Solar (deg)', 'Obstaculo', 'FS_geometrico', 'FS_climatico', 'FS', 'Situacion']
      : ['Mes', 'Dia', 'Hora', 'Altura Solar', 'Acimut Solar', 'Obstaculo', 'Area Sombreada', 'FS'];

    const rows = hasExtended
      ? points.map(p => [
          p.evento || '',
          p.month,
          p.day,
          p.hourStr || `${p.hour}:00`,
          p.heightSolar.toFixed(2),
          p.azimuthSolar.toFixed(2),
          p.obstacle,
          (p.fsGeometrico ?? 0).toFixed(3),
          (p.fsClimatico ?? 0).toFixed(3),
          p.fs.toFixed(3),
          p.situacion || '',
        ])
      : points.map(p => [
          p.month,
          p.day,
          p.hour,
          p.heightSolar,
          p.azimuthSolar,
          p.obstacle,
          p.shadowedArea,
          p.fs.toFixed(3),
        ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analisis_sombreado_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const downloadTemplate = () => {
    const headers = ['Mes', 'Dia', 'Hora', 'Altura Solar', 'Acimut Solar', 'Obstaculo', 'Area Sombreada'];
    const templateRows = [
      ['Ene', '21', '9', '15', '-60', 'Edificio A', '30'],
      ['Ene', '21', '12', '30', '0', 'Ninguno', '0'],
      ['Jul', '21', '12', '75', '0', 'Ninguno', '0'],
    ];

    const csv = [
      headers.join(','),
      ...templateRows.map(row => row.join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'plantilla_sombreado.csv';
    a.click();
  };

  // Mapeo de nombres de mes completos/abreviados a abreviatura de 3 letras
  const monthNameToAbbr = (name: string): string => {
    return normalizeMonthToAbbr(name);
  };

  // Normalizar números con locale colombiano (punto=miles, coma=decimal)
  const parseLocalizedNumber = (val: string): number => {
    if (!val || val.trim() === '') return 0;
    let s = val.trim();
    // Si tiene coma Y punto: determinar cuál es decimal
    const hasComma = s.includes(',');
    const hasDot = s.includes('.');
    if (hasComma && hasDot) {
      // Si la coma viene después del punto: formato 1.234,56 (ES)
      if (s.lastIndexOf(',') > s.lastIndexOf('.')) {
        s = s.replace(/\./g, '').replace(',', '.');
      } else {
        // formato 1,234.56 (EN)
        s = s.replace(/,/g, '');
      }
    } else if (hasComma && !hasDot) {
      // Solo coma: puede ser decimal (0,632) o miles (1,000)
      // Si hay exactamente 3 dígitos después de la coma y más de 1 antes, es miles
      const parts = s.split(',');
      if (parts.length === 2 && parts[1].length === 3 && parts[0].length > 1 && !parts[0].includes(' ')) {
        // Ambiguo: 146,300 podría ser 146.300 (miles) o 146.3
        // Para FS (esperamos 0-1): si la parte entera > 1, probablemente es miles
        const intPart = parseInt(parts[0]);
        if (intPart > 1) {
          s = s.replace(',', ''); // separador de miles
        } else {
          s = s.replace(',', '.'); // decimal
        }
      } else {
        s = s.replace(',', '.'); // decimal normal (0,632)
      }
    } else if (hasDot && !hasComma) {
      // Solo punto: puede ser decimal (0.632) o miles (146.300)
      const parts = s.split('.');
      if (parts.length === 2 && parts[1].length === 3 && parseInt(parts[0]) > 1) {
        // Podría ser separador de miles (146.300 = 146300)
        // PERO para nuestro caso, los valores esperados son:
        // - Altura solar: 0-90 (19.96, 34.85, etc.) → decimal
        // - Azimut: 0-360 (92.35, 253.39) → decimal
        // - FS: 0-1 (0.632) → decimal
        // Entonces si es < 360 y tiene sentido como decimal, dejarlo como decimal
        s = s; // dejar como está (parseFloat lo maneja)
      }
    }
    const result = parseFloat(s);
    return isNaN(result) ? 0 : result;
  };

  // Validar que un FS esté en rango 0-1, si es > 1 probablemente es porcentaje
  const normalizeFS = (val: number): number => {
    if (val > 1 && val <= 100) return val / 100;
    if (val > 100) return 1; // valor erróneo, cap a 1
    return Math.max(0, Math.min(1, val));
  };

  // Parser unificado que procesa filas (arrays de strings) independientemente del formato de origen
  const parseRowsToPoints = (rows: string[][]): AnalysisPoint[] => {
    const newPoints: AnalysisPoint[] = [];

    for (const values of rows) {
      if (values.length < 7) continue;

      // Detectar formato extendido (11 columnas): Evento, Mes, Dia, Hora, Altura, Azimut, Obstaculo, FS_geom, FS_clim, FS, Situacion
      const isExtendedFormat = values.length >= 10;

      if (isExtendedFormat) {
        const evento = values[0] || '';
        const month = normalizeMonthToAbbr(values[1]);
        const day = parseInt(values[2]) || 21;
        const hourStr = values[3] || '12:00';
        const hour = parseInt(hourStr.split(':')[0]) || 12;
        const heightSolar = parseLocalizedNumber(values[4]);
        const azimuthSolar = parseLocalizedNumber(values[5]);
        const obstacle = values[6] || '';
        const rawFsGeom = parseLocalizedNumber(values[7]);
        const rawFsClim = parseLocalizedNumber(values[8]);
        const rawFs = parseLocalizedNumber(values[9]);
        const fsGeometrico = normalizeFS(rawFsGeom);
        const fsClimatico = normalizeFS(rawFsClim);
        const fs = normalizeFS(rawFs) || Math.max(fsGeometrico, fsClimatico);
        const situacion = values[10] || '';

        newPoints.push({
          id: Date.now().toString() + Math.random(),
          month,
          day,
          hour,
          heightSolar,
          azimuthSolar,
          obstacle,
          shadowedArea: fs * 100,
          fs,
          autoCalculated: false,
          evento,
          fsGeometrico,
          fsClimatico,
          situacion,
          hourStr,
        });
      } else {
        // Formato simple (7-8 columnas): Mes, Dia, Hora, Altura, Azimut, Obstaculo, AreaSombreada, [FS]
        const month = normalizeMonthToAbbr(values[0]);
        const day = parseInt(values[1]) || 21;
        const hour = parseInt(values[2]) || 12;
        const pos = getSolarPos(month, day, hour);
        const heightSolar = pos ? pos.altitude : (parseFloat(values[3]) || 45);
        const azimuthSolar = pos ? pos.azimuth : (parseFloat(values[4]) || 0);
        const obstacle = values[5] || '';
        const shadowedArea = parseFloat(values[6]) || 0;

        newPoints.push({
          id: Date.now().toString() + Math.random(),
          month,
          day,
          hour,
          heightSolar,
          azimuthSolar,
          obstacle,
          shadowedArea,
          fs: calculateFS(shadowedArea),
          autoCalculated: !!pos,
        });
      }
    }

    return newPoints;
  };

  const importFromCSV = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const isXLSX = file.name.endsWith('.xlsx') || file.name.endsWith('.xls');

    if (isXLSX) {
      // Leer como ArrayBuffer para xlsx
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer);
          const workbook = XLSX.read(data, { type: 'array' });
          const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
          const jsonRows: string[][] = XLSX.utils.sheet_to_json(firstSheet, { header: 1, raw: false });

          if (jsonRows.length < 2) {
            toast.error('El archivo debe contener al menos una fila de datos');
            return;
          }

          // Saltar encabezado
          const dataRows = jsonRows.slice(1).filter(row => row.length >= 7);
          const newPoints = parseRowsToPoints(dataRows);

          if (newPoints.length === 0) {
            toast.error('No se encontraron datos válidos en el archivo');
            return;
          }

          setPoints(newPoints);
          const hasExtended = newPoints[0].evento !== undefined;
          toast.success(`Se importaron ${newPoints.length} puntos de análisis${hasExtended ? ' (formato días críticos con FS climático)' : ''}`);
        } catch (error) {
          toast.error('Error al importar el archivo XLSX');
          console.error(error);
        }
      };
      reader.readAsArrayBuffer(file);
    } else {
      // Leer como texto para CSV
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = e.target?.result as string;
          const lines = text.trim().split('\n');

          if (lines.length < 2) {
            toast.error('El archivo CSV debe contener al menos una fila de datos');
            return;
          }

          // Detectar separador (coma o punto y coma)
          const separator = lines[0].includes(';') ? ';' : ',';
          const dataRows = lines.slice(1).map(line => line.split(separator).map(v => v.trim()));
          const newPoints = parseRowsToPoints(dataRows);

          if (newPoints.length === 0) {
            toast.error('No se encontraron datos válidos en el archivo');
            return;
          }

          setPoints(newPoints);
          const hasExtended = newPoints[0].evento !== undefined;
          toast.success(`Se importaron ${newPoints.length} puntos de análisis${hasExtended ? ' (formato días críticos con FS climático)' : ''}`);
        } catch (error) {
          toast.error('Error al importar el archivo CSV');
          console.error(error);
        }
      };
      reader.readAsText(file);
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getColorFS = (fs: number) => {
    if (fs >= 0.9) return 'bg-green-50 border-green-200';
    if (fs >= 0.7) return 'bg-yellow-50 border-yellow-200';
    return 'bg-orange-50 border-orange-200';
  };

  const getTextColorFS = (fs: number) => {
    if (fs >= 0.9) return 'text-green-700 font-semibold';
    if (fs >= 0.7) return 'text-yellow-700 font-semibold';
    return 'text-orange-700 font-semibold';
  };

  // Handle obstacle changes from the diagram
  const handleObstaclesChange = useCallback((newObstacles: ObstaclePolygon[]) => {
    setObstacles(newObstacles);
    if (newObstacles.length > obstacles.length) {
      const newest = newObstacles[newObstacles.length - 1];
      toast.success(`Obstáculo "${newest.name}" dibujado con ${newest.vertices.length} vértices`);
    }
  }, [obstacles.length]);

  // Export obstacles as JSON
  const exportObstacles = () => {
    if (obstacles.length === 0) {
      toast.error('No hay obstáculos para exportar');
      return;
    }
    const data = JSON.stringify(obstacles, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `obstaculos_sombreado_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
    toast.success(`${obstacles.length} obstáculo(s) exportados`);
  };

  // Import obstacles from JSON
  const importObstacles = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const imported = JSON.parse(text);

        if (!Array.isArray(imported)) {
          toast.error('El archivo no contiene un arreglo válido de obstáculos');
          return;
        }

        const validObstacles: ObstaclePolygon[] = imported
          .filter((o: any) =>
            o && typeof o.name === 'string' &&
            typeof o.color === 'string' &&
            Array.isArray(o.vertices) &&
            o.vertices.length >= 3 &&
            o.vertices.every((v: any) => typeof v.azimuth === 'number' && typeof v.altitude === 'number')
          )
          .map((o: any) => ({
            id: o.id || (Date.now().toString() + Math.random().toString(36).slice(2)),
            name: o.name,
            color: o.color,
            vertices: o.vertices.map((v: any) => ({ azimuth: v.azimuth, altitude: v.altitude })),
            visible: o.visible !== false,
          }));

        if (validObstacles.length === 0) {
          toast.error('No se encontraron obstáculos válidos en el archivo');
          return;
        }

        setObstacles(prev => [...prev, ...validObstacles]);
        toast.success(`${validObstacles.length} obstáculo(s) importados`);
      } catch (error) {
        toast.error('Error al importar el archivo de obstáculos');
        console.error(error);
      }
    };

    reader.readAsText(file);
    if (obstacleFileInputRef.current) {
      obstacleFileInputRef.current.value = '';
    }
  };

  // Import Andrew Marsh Site Designer JSON
  const importMarshFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setMarshFileName(file.name);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const json = JSON.parse(text);

        if (!validateMarshJSON(json)) {
          toast.error('El archivo no es un JSON válido de Andrew Marsh Site Designer');
          setMarshPreview(null);
          return;
        }

        const result = parseMarshSiteDesigner(json as MarshSiteDesignerJSON);

        if (result.obstacles.length === 0) {
          toast.error('No se encontraron obstáculos sólidos en el archivo');
          setMarshPreview(null);
          return;
        }

        setMarshPreview(result);
        toast.info(`Archivo cargado: ${result.solidBlocks.length} bloques sólidos detectados. Revisa la previsualización y confirma la importación.`);
      } catch (error) {
        toast.error('Error al leer el archivo JSON de Andrew Marsh');
        console.error(error);
        setMarshPreview(null);
      }
    };

    reader.readAsText(file);
    if (marshFileInputRef.current) {
      marshFileInputRef.current.value = '';
    }
  };

  const confirmMarshImport = () => {
    if (!marshPreview) return;
    setObstacles(prev => [...prev, ...marshPreview.obstacles]);
    
    // Extraer vértices 3D de los bloques sólidos para recalcular desde otro punto de observación
    if (marshPreview.solidBlocks.length > 0) {
      const vertices3D: Vertex3D[][] = marshPreview.solidBlocks.map(block => {
        // Generar 8 esquinas del bloque 3D usando min/max
        const { min, max } = block;
        return [
          { x: min.x, y: min.y, z: min.z },
          { x: max.x, y: min.y, z: min.z },
          { x: max.x, y: max.y, z: min.z },
          { x: min.x, y: max.y, z: min.z },
          { x: min.x, y: min.y, z: max.z },
          { x: max.x, y: min.y, z: max.z },
          { x: max.x, y: max.y, z: max.z },
          { x: min.x, y: max.y, z: max.z },
        ];
      });
      setObstacleVertices3D(prev => prev ? [...prev, ...vertices3D] : vertices3D);
    }
    
    toast.success(
      `${marshPreview.obstacles.length} obstáculo(s) importados desde Andrew Marsh Site Designer`
    );
    // Auto-show the sun path diagram if not already visible
    if (!showSunPath && weatherData) {
      setShowSunPath(true);
    }
    setMarshPreview(null);
  };

  const cancelMarshImport = () => {
    setMarshPreview(null);
    setMarshFileName('');
    toast.info('Importación cancelada');
  };

  // ── Sun Path 3D JSON import ────────────────────────────────────────
  const importSunPath3DFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSunPath3DFileName(file.name);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const json = JSON.parse(text);

        // Check if it's a Sun Path 3D JSON (not Site Designer)
        if (!validateSunPath3DJSON(json)) {
          // Maybe it's a Site Designer JSON? Auto-detect
          if (validateMarshJSON(json)) {
            toast.info('Este archivo parece ser de Site Designer, no de Sun Path 3D. Usa el botón "Cargar JSON de Site Designer" en su lugar.');
          } else {
            toast.error('El archivo no es un JSON válido de Sun Path 3D');
          }
          setSunPath3DPreview(null);
          return;
        }

        const result = parseSunPath3D(json as SunPath3DJSON);
        setSunPath3DPreview(result);

        // If the JSON also has northOffset, save it for OBJ imports
        if (result.location.northOffset !== 0) {
          setObjNorthOffset(result.location.northOffset);
        }

        toast.info(
          `Sun Path 3D cargado: ${result.location.latitude.toFixed(2)}°, ${result.location.longitude.toFixed(2)}° — ${result.dateTime.monthName} ${result.dateTime.day}, ${result.dateTime.hour}:00h`
        );
      } catch (error) {
        toast.error('Error al leer el archivo JSON de Sun Path 3D');
        console.error(error);
        setSunPath3DPreview(null);
      }
    };

    reader.readAsText(file);
    if (sunPath3DFileInputRef.current) {
      sunPath3DFileInputRef.current.value = '';
    }
  };

  const confirmSunPath3DImport = () => {
    if (!sunPath3DPreview) return;

    const { location, dateTime } = sunPath3DPreview;

    // Create a synthetic EPWData with the location from Sun Path 3D
    const syntheticEPW: EPWData = {
      location: {
        city: `Sun Path 3D (${location.latitude.toFixed(2)}°, ${location.longitude.toFixed(2)}°)`,
        state: '',
        country: '',
        latitude: location.latitude,
        longitude: location.longitude,
        timezone: location.timezone,
        elevation: 0,
      },
      weatherData: [], // No hourly weather data from Sun Path 3D
    };

    // Notify parent to update global weather data
    if (onWeatherDataOverride) {
      onWeatherDataOverride(syntheticEPW);
    }

    // Add the specific date/time as an analysis point
    const pos = calculateSolarPosition(
      location.latitude,
      location.longitude,
      location.timezone,
      dateTime.month,
      dateTime.day,
      dateTime.hour
    );

    if (pos.altitude > 0) {
      const newPoint: AnalysisPoint = {
        id: Date.now().toString() + Math.random(),
        month: dateTime.monthName,
        day: dateTime.day,
        hour: dateTime.hour,
        heightSolar: pos.altitude,
        azimuthSolar: pos.azimuth,
        obstacle: '',
        shadowedArea: 0,
        fs: 1.0,
        autoCalculated: true,
      };
      setPoints(prev => [...prev, newPoint]);
    }

    // Auto-show the sun path diagram
    setShowSunPath(true);

    toast.success(
      `Ubicación aplicada: ${location.latitude.toFixed(4)}°, ${location.longitude.toFixed(4)}° (UTC${location.timezone >= 0 ? '+' : ''}${location.timezone}). ` +
      `Punto de análisis agregado: ${dateTime.monthName} ${dateTime.day}, ${dateTime.hour}:00h`
    );

    setSunPath3DPreview(null);
    setSunPath3DFileName('');
  };

  const cancelSunPath3DImport = () => {
    setSunPath3DPreview(null);
    setSunPath3DFileName('');
    toast.info('Importación de Sun Path 3D cancelada');
  };

  // ── OBJ file import ────────────────────────────────────────────────
  const [objRawParse, setObjRawParse] = useState<OBJParseResult | null>(null);

  const importOBJFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    let initialScale = objScale;
    let initialUpAxis = objUpAxis;
    let initialRot = objRotationDeg;

    // Si ya existe un modelo de edificio cargado, inicializar la configuración de importación del obstáculo con la del edificio
    if (evaluationModel) {
      const buildScale = evaluationModel.config.scaleFactor;
      const buildUpAxis = evaluationModel.config.upAxis === 'auto' ? 'Z' : evaluationModel.config.upAxis;
      const buildRot = evaluationModel.config.rotationDeg;
      
      initialScale = buildScale;
      initialUpAxis = buildUpAxis as any;
      initialRot = buildRot;

      setObjScale(buildScale);
      setObjUpAxis(buildUpAxis as any);
      setObjRotationDeg(buildRot);
      setObjSwapYZ(buildUpAxis === 'Y_simple');
    }

    setObjFileName(file.name);
    const ext = file.name.toLowerCase().split('.').pop() || '';
    const isGLTFFile = ext === 'gltf' || ext === 'glb';
    const isOBJFile = ext === 'obj';
    const detectedFmt = detectFormat(file.name);
    const isNewFormat = detectedFmt && !isOBJFile && !isGLTFFile;

    // Check unsupported formats (DWG, XSI)
    if (detectedFmt && isUnsupportedFormat(detectedFmt)) {
      toast.error(getConversionAdvice(detectedFmt), { duration: 10000 });
      if (objFileInputRef.current) objFileInputRef.current.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        if (isNewFormat && detectedFmt) {
          // ===== NUEVOS FORMATOS: DXF, FBX, STL, DAE, VRML, 3DS =====
          const rawResult = e.target?.result;
          if (!rawResult) {
            toast.error('No se pudo leer el archivo');
            setObjPreview(null);
            return;
          }

          try {
            const { result: parsed, formatName } = await parseMultiFormat(file.name, rawResult);
            setObjRawParse(parsed);

            const northOff = sunPath3DPreview?.location.northOffset || objNorthOffset;
            const result = convertOBJToObstacles(parsed, undefined, northOff, initialUpAxis, initialScale, initialRot);
            setObjPreview(result);

            toast.info(
              `${formatName} cargado: ${parsed.vertices.length} vértices, ${parsed.totalFaces} caras, ${parsed.objects.length} objeto(s). Revisa la previsualización.`
            );
          } catch (parseError: any) {
            toast.error(parseError.message || 'Error al parsear el archivo');
            setObjPreview(null);
          }
        } else if (isGLTFFile) {
          // glTF/GLB path
          const rawResult = e.target?.result;
          if (!rawResult) {
            toast.error('No se pudo leer el archivo');
            setObjPreview(null);
            return;
          }

          let input: ArrayBuffer | string;
          if (rawResult instanceof ArrayBuffer) {
            input = rawResult;
          } else {
            input = rawResult as string;
          }

          const validationError = validateGLTF(input);
          if (validationError) {
            toast.error(validationError);
            setObjPreview(null);
            return;
          }

          const gltfResult = parseGLTF(input);
          const parsed = gltfResult.objResult;
          setObjRawParse(parsed);

          const northOff = sunPath3DPreview?.location.northOffset || objNorthOffset;
          const result = convertOBJToObstacles(parsed, undefined, northOff, initialUpAxis, initialScale, initialRot);
          setObjPreview(result);

          const summary = getGLTFSummary(gltfResult);
          toast.info(
            `glTF cargado: ${summary.split('\n').slice(0, 3).join(' | ')}. Revisa la previsualización.`
          );
        } else {
          // OBJ path (original)
          const text = e.target?.result as string;

          if (!validateOBJText(text)) {
            toast.error('El archivo no es un OBJ válido (debe contener vértices y caras)');
            setObjPreview(null);
            return;
          }

          const parsed = parseOBJText(text);
          setObjRawParse(parsed);

          const northOff = sunPath3DPreview?.location.northOffset || objNorthOffset;
          const result = convertOBJToObstacles(parsed, undefined, northOff, initialUpAxis, initialScale, initialRot);
          setObjPreview(result);

          const summary = getOBJSummary(parsed);
          toast.info(
            `OBJ cargado: ${summary.vertexCount} vértices, ${summary.faceCount} caras, ${summary.objectCount} objeto(s). Revisa la previsualización.`
          );
        }
      } catch (error: any) {
        toast.error(`Error al leer el archivo: ${error.message || 'Error desconocido'}`);
        console.error(error);
        setObjPreview(null);
      }
    };

    // Read as ArrayBuffer for binary formats, as text for text formats
    const binaryFormats = ['glb', 'fbx', '3ds', 'stl'];
    if (binaryFormats.includes(ext)) {
      reader.readAsArrayBuffer(file);
    } else {
      reader.readAsText(file);
    }
    if (objFileInputRef.current) {
      objFileInputRef.current.value = '';
    }
  };

  // Reconvert OBJ when settings change
  const reconvertOBJ = useCallback(() => {
    if (!objRawParse) return;
    const northOff = sunPath3DPreview?.location.northOffset || objNorthOffset;
    const result = convertOBJToObstacles(objRawParse, undefined, northOff, objUpAxis, objScale, objRotationDeg);
    setObjPreview(result);
  }, [objRawParse, objUpAxis, objScale, objRotationDeg, objNorthOffset, sunPath3DPreview]);

  const confirmOBJImport = () => {
    if (!objPreview) return;
    setObstacles(prev => [...prev, ...objPreview.obstacles]);
    
    // Extraer vértices 3D de los objetos OBJ para poder recalcular desde otro punto de observación
    if (objRawParse) {
      const vertices3D: Vertex3D[][] = objRawParse.objects.map(obj => {
        const objVerts: Vertex3D[] = [];
        for (const face of obj.faces) {
          for (const idx of face.vertexIndices) {
            const v = objRawParse.vertices[idx];
            if (v) {
              let pt = {
                x: v.x * objScale,
                y: v.y * objScale,
                z: v.z * objScale,
              };
              // remapAxes logic
              if (objUpAxis === 'Y_simple') {
                pt = { x: pt.x, y: pt.z, z: pt.y };
              } else if (objUpAxis === 'Y') {
                pt = { x: pt.x, y: -pt.z, z: pt.y };
              } else if (objUpAxis === 'X') {
                pt = { x: pt.y, y: pt.z, z: pt.x };
              }
              // rotateAroundVertical logic
              if (objRotationDeg !== 0) {
                const rad = (objRotationDeg * Math.PI) / 180;
                const cos = Math.cos(rad);
                const sin = Math.sin(rad);
                pt = {
                  x: pt.x * cos - pt.y * sin,
                  y: pt.x * sin + pt.y * cos,
                  z: pt.z,
                };
              }
              objVerts.push(pt);
            }
          }
        }
        return objVerts;
      });
      setObstacleVertices3D(prev => prev ? [...prev, ...vertices3D] : vertices3D);
    }
    
    toast.success(
      `${objPreview.obstacles.length} obstáculo(s) importados desde archivo OBJ`
    );
    if (!showSunPath && weatherData) {
      setShowSunPath(true);
    }
    setObjPreview(null);
    setObjRawParse(null);
    setObjFileName('');
  };

  const cancelOBJImport = () => {
    setObjPreview(null);
    setObjRawParse(null);
    setObjFileName('');
    toast.info('Importación de OBJ cancelada');
  };

  return (
    <div className="w-full space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-gray-900">Calculadora de Factores de Sombreado</h1>
        <p className="text-lg text-gray-600">Analisis dinamico de puntos solares y calculo automatico del factor de sombreado (FS)</p>
      </div>

      {/* Banner de Auto-Cálculo Solar */}
      <div className={`rounded-xl border-2 p-4 transition-all ${
        weatherData && autoCalcEnabled
          ? 'bg-gradient-to-r from-amber-50 to-orange-50 border-amber-300'
          : 'bg-gray-50 border-gray-200'
      }`}>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${weatherData && autoCalcEnabled ? 'bg-amber-200 text-amber-800' : 'bg-gray-200 text-gray-500'}`}>
              <Sun size={24} />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 text-sm">
                {weatherData
                  ? `Posición Solar Automática — ${weatherData.location.city}, ${weatherData.location.country}`
                  : 'Posición Solar Automática — Sin datos EPW'
                }
              </h3>
              <p className="text-xs text-gray-600">
                {weatherData
                  ? `Lat: ${weatherData.location.latitude.toFixed(2)}° | Lon: ${weatherData.location.longitude.toFixed(2)}° | UTC${weatherData.location.timezone >= 0 ? '+' : ''}${weatherData.location.timezone} | Elev: ${weatherData.location.elevation}m`
                  : 'Carga un archivo EPW en "Datos Meteorológicos" para activar el cálculo automático de altura y azimut solar'
                }
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {weatherData && (
              <>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoCalcEnabled}
                    onChange={(e) => setAutoCalcEnabled(e.target.checked)}
                    className="accent-amber-600 w-4 h-4"
                  />
                  <span className="text-xs font-medium text-gray-700">Auto-cálculo</span>
                </label>
                <Button
                  onClick={recalculateAllPositions}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-1 text-xs border-amber-300 text-amber-800 hover:bg-amber-100"
                  disabled={!autoCalcEnabled}
                >
                  <Zap size={14} />
                  Recalcular Todo
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-gray-600 font-medium">Total de Puntos</p>
          <p className="text-2xl font-mono font-bold text-blue-700">{stats.count}</p>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-gray-600 font-medium">FS Promedio</p>
          <p className="text-2xl font-mono font-bold text-blue-700">{stats.avg}</p>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-sm text-gray-600 font-medium">FS Maximo</p>
          <p className="text-2xl font-mono font-bold text-green-700">{stats.max}</p>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <p className="text-sm text-gray-600 font-medium">FS Minimo</p>
          <p className="text-2xl font-mono font-bold text-orange-700">{stats.min}</p>
        </div>
      </div>

      {/* Andrew Marsh Site Designer Import */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-xl p-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-200 text-indigo-800">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                <line x1="12" y1="22.08" x2="12" y2="12" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 text-sm">
                Importar Modelo 3D — Andrew Marsh Site Designer
              </h3>
              <p className="text-xs text-gray-600">
                Carga un archivo JSON exportado desde <a href="https://andrewmarsh.com/software/site-designer-web/" target="_blank" rel="noopener noreferrer" className="text-indigo-600 underline">Site Designer</a> para convertir bloques 3D en obstáculos solares automáticamente.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <input
              ref={marshFileInputRef}
              type="file"
              accept=".json"
              onChange={importMarshFile}
              className="hidden"
            />
            <Button
              onClick={() => marshFileInputRef.current?.click()}
              variant="outline"
              size="sm"
              className="flex items-center gap-1 text-xs border-indigo-300 text-indigo-800 hover:bg-indigo-100"
            >
              <Upload size={14} />
              Cargar JSON de Site Designer
            </Button>
          </div>
        </div>

        {/* Marsh Preview Panel */}
        {marshPreview && (
          <div className="mt-4 bg-white border border-indigo-200 rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-900 text-sm">Previsualización: {marshFileName}</h4>
              <div className="flex gap-2">
                <Button
                  onClick={confirmMarshImport}
                  size="sm"
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs"
                >
                  Confirmar Importación ({marshPreview.obstacles.length} obstáculos)
                </Button>
                <Button
                  onClick={cancelMarshImport}
                  variant="outline"
                  size="sm"
                  className="text-xs border-gray-300"
                >
                  Cancelar
                </Button>
              </div>
            </div>

            {/* Location info */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-indigo-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Ubicación</p>
                <p className="text-sm font-mono font-semibold text-indigo-800">
                  {marshPreview.location.latitude.toFixed(4)}°, {marshPreview.location.longitude.toFixed(4)}°
                </p>
              </div>
              <div className="bg-indigo-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Zona Horaria</p>
                <p className="text-sm font-mono font-semibold text-indigo-800">
                  UTC{marshPreview.location.timezone >= 0 ? '+' : ''}{marshPreview.location.timezone}
                </p>
              </div>
              <div className="bg-indigo-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Bloques Sólidos</p>
                <p className="text-sm font-mono font-semibold text-indigo-800">{marshPreview.solidBlocks.length}</p>
              </div>
              <div className="bg-indigo-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Punto de Observación</p>
                <p className="text-sm font-mono font-semibold text-indigo-800">
                  ({marshPreview.observationPoint.x.toFixed(1)}, {marshPreview.observationPoint.y.toFixed(1)}, {marshPreview.observationPoint.z.toFixed(1)})m
                </p>
              </div>
            </div>

            {/* Blocks table */}
            <div className="overflow-x-auto border border-gray-200 rounded-lg">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">#</th>
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">Nombre</th>
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">Color</th>
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">Dimensiones (m)</th>
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">Vértices</th>
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">Rango Azimut</th>
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">Rango Altitud</th>
                  </tr>
                </thead>
                <tbody>
                  {marshPreview.obstacles.map((obs, idx) => {
                    const azMin = Math.min(...obs.vertices.map(v => v.azimuth));
                    const azMax = Math.max(...obs.vertices.map(v => v.azimuth));
                    const altMin = Math.min(...obs.vertices.map(v => v.altitude));
                    const altMax = Math.max(...obs.vertices.map(v => v.altitude));
                    const block = marshPreview.solidBlocks[idx];
                    return (
                      <tr key={obs.id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-3 py-2 font-mono">{idx + 1}</td>
                        <td className="px-3 py-2 font-medium">{obs.name}</td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-1">
                            <span
                              className="inline-block w-4 h-4 rounded border border-gray-300"
                              style={{ backgroundColor: obs.color }}
                            />
                            <span className="font-mono text-gray-500">{obs.color}</span>
                          </div>
                        </td>
                        <td className="px-3 py-2 font-mono">
                          {block ? `${block.dimensions.width.toFixed(1)} × ${block.dimensions.height.toFixed(1)} × ${block.dimensions.depth.toFixed(1)}` : '-'}
                        </td>
                        <td className="px-3 py-2 font-mono">{obs.vertices.length}</td>
                        <td className="px-3 py-2 font-mono">{azMin.toFixed(1)}° a {azMax.toFixed(1)}°</td>
                        <td className="px-3 py-2 font-mono">{altMin.toFixed(1)}° a {altMax.toFixed(1)}°</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Analysis grids info */}
            {marshPreview.analysisGrids.length > 0 && (
              <div className="text-xs text-gray-500 bg-gray-50 rounded p-2">
                <strong>Superficies de análisis detectadas:</strong>{' '}
                {marshPreview.analysisGrids.map((g, i) =>
                  `Grid ${i + 1}: ${g.width.toFixed(0)}m × ${g.height.toFixed(0)}m (az: ${g.azimuth}°, alt: ${g.altitude}°)`
                ).join(' | ')}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sun Path 3D Import */}
      <div className="bg-gradient-to-r from-teal-50 to-cyan-50 border-2 border-teal-200 rounded-xl p-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-teal-200 text-teal-800">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
                <path d="M2 12h20" />
                <circle cx="12" cy="5" r="1.5" fill="currentColor" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 text-sm">
                Importar Configuración — Andrew Marsh Sun Path 3D
              </h3>
              <p className="text-xs text-gray-600">
                Carga un JSON de <a href="https://drajmarsh.bitbucket.io/sunpath3d.html" target="_blank" rel="noopener noreferrer" className="text-teal-600 underline">Sun Path 3D</a> para aplicar ubicación, zona horaria y fecha/hora de análisis automáticamente.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <input
              ref={sunPath3DFileInputRef}
              type="file"
              accept=".json"
              onChange={importSunPath3DFile}
              className="hidden"
            />
            <Button
              onClick={() => sunPath3DFileInputRef.current?.click()}
              variant="outline"
              size="sm"
              className="flex items-center gap-1 text-xs border-teal-300 text-teal-800 hover:bg-teal-100"
            >
              <Upload size={14} />
              Cargar JSON de Sun Path 3D
            </Button>
          </div>
        </div>

        {/* Sun Path 3D Preview Panel */}
        {sunPath3DPreview && (
          <div className="mt-4 bg-white border border-teal-200 rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-900 text-sm">Previsualización: {sunPath3DFileName}</h4>
              <div className="flex gap-2">
                <Button
                  onClick={confirmSunPath3DImport}
                  size="sm"
                  className="bg-teal-600 hover:bg-teal-700 text-white text-xs"
                >
                  Aplicar Ubicación y Fecha
                </Button>
                <Button
                  onClick={cancelSunPath3DImport}
                  variant="outline"
                  size="sm"
                  className="text-xs border-gray-300"
                >
                  Cancelar
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-teal-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Ubicación</p>
                <p className="text-sm font-mono font-semibold text-teal-800">
                  {sunPath3DPreview.location.latitude.toFixed(4)}°, {sunPath3DPreview.location.longitude.toFixed(4)}°
                </p>
              </div>
              <div className="bg-teal-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Zona Horaria</p>
                <p className="text-sm font-mono font-semibold text-teal-800">
                  UTC{sunPath3DPreview.location.timezone >= 0 ? '+' : ''}{sunPath3DPreview.location.timezone}
                </p>
              </div>
              <div className="bg-teal-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Fecha / Hora</p>
                <p className="text-sm font-mono font-semibold text-teal-800">
                  {sunPath3DPreview.dateTime.monthName} {sunPath3DPreview.dateTime.day}, {sunPath3DPreview.dateTime.year} — {sunPath3DPreview.dateTime.hour}:00h
                </p>
              </div>
              <div className="bg-teal-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">North Offset</p>
                <p className="text-sm font-mono font-semibold text-teal-800">
                  {sunPath3DPreview.location.northOffset.toFixed(1)}°
                </p>
              </div>
            </div>

            <div className="text-xs text-gray-500 bg-gray-50 rounded p-2">
              <strong>Al confirmar:</strong> Se aplicará la ubicación ({sunPath3DPreview.location.latitude.toFixed(2)}°, {sunPath3DPreview.location.longitude.toFixed(2)}°) como datos de localización para la calculadora, y se agregará un punto de análisis para {sunPath3DPreview.dateTime.monthName} {sunPath3DPreview.dateTime.day} a las {sunPath3DPreview.dateTime.hour}:00h.
              {sunPath3DPreview.shadowsEnabled && ' Las sombras estaban habilitadas en Sun Path 3D.'}
            </div>
          </div>
        )}
      </div>

      {/* OBJ File Import */}
      <div className="bg-gradient-to-r from-emerald-50 to-green-50 border-2 border-emerald-200 rounded-xl p-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-200 text-emerald-800">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z" />
                <path d="M12 12l8-4.5" />
                <path d="M12 12v9" />
                <path d="M12 12L4 7.5" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 text-sm">
                Importar Modelo 3D — Obstáculos de Sombra
              </h3>
              <p className="text-xs text-gray-600">
                Carga un archivo 3D (<code className="bg-gray-100 px-1 rounded">.obj</code>, <code className="bg-gray-100 px-1 rounded">.gltf/.glb</code>, <code className="bg-gray-100 px-1 rounded">.dxf</code>, <code className="bg-gray-100 px-1 rounded">.fbx</code>, <code className="bg-gray-100 px-1 rounded">.stl</code>, <code className="bg-gray-100 px-1 rounded">.dae</code>, <code className="bg-gray-100 px-1 rounded">.wrl</code>, <code className="bg-gray-100 px-1 rounded">.3ds</code>) exportado desde Sun Path 3D, SketchUp, Blender, Rhino, Revit o AutoCAD para convertir la geometría en obstáculos solares.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <input
              ref={objFileInputRef}
              type="file"
              accept=".obj,.gltf,.glb,.dxf,.dwg,.fbx,.stl,.dae,.wrl,.vrml,.3ds,.xsi"
              onChange={importOBJFile}
              className="hidden"
            />
            <Button
              onClick={() => objFileInputRef.current?.click()}
              variant="outline"
              size="sm"
              className="flex items-center gap-1 text-xs border-emerald-300 text-emerald-800 hover:bg-emerald-100"
            >
              <Upload size={14} />
              Cargar Modelo 3D
            </Button>
          </div>
        </div>

        {/* Drag & Drop Zone */}
        {!objPreview && (
          <div
            className={`mt-3 border-2 border-dashed rounded-lg p-5 text-center transition-colors cursor-pointer ${
              isDraggingObj
                ? 'border-emerald-500 bg-emerald-50'
                : 'border-gray-300 hover:border-emerald-300 hover:bg-emerald-50/30'
            }`}
            onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingObj(true); }}
            onDragEnter={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingObj(true); }}
            onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingObj(false); }}
            onDrop={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setIsDraggingObj(false);
              const file = e.dataTransfer.files?.[0];
              if (file) {
                const dt = new DataTransfer();
                dt.items.add(file);
                if (objFileInputRef.current) {
                  objFileInputRef.current.files = dt.files;
                  objFileInputRef.current.dispatchEvent(new Event('change', { bubbles: true }));
                }
              }
            }}
            onClick={() => objFileInputRef.current?.click()}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`mx-auto mb-2 ${isDraggingObj ? 'text-emerald-500' : 'text-gray-400'}`}>
              <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z" />
              <path d="M12 12l8-4.5" />
              <path d="M12 12v9" />
              <path d="M12 12L4 7.5" />
            </svg>
            <p className={`text-sm font-medium ${isDraggingObj ? 'text-emerald-700' : 'text-gray-600'}`}>
              {isDraggingObj ? 'Suelta el archivo aquí' : 'Arrastra un modelo 3D aquí o haz clic para seleccionar'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              OBJ · glTF/GLB · DXF · FBX · STL · DAE · WRL · 3DS
            </p>
          </div>
        )}

        {/* OBJ Preview Panel */}
        {objPreview && (
          <div className="mt-4 bg-white border border-emerald-200 rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-900 text-sm">Previsualización: {objFileName}</h4>
              <div className="flex gap-2">
                <Button
                  onClick={confirmOBJImport}
                  size="sm"
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
                  disabled={objPreview.obstacles.length === 0}
                >
                  Confirmar Importación ({objPreview.obstacles.length} obstáculos)
                </Button>
                <Button
                  onClick={cancelOBJImport}
                  variant="outline"
                  size="sm"
                  className="text-xs border-gray-300"
                >
                  Cancelar
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="bg-emerald-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Vértices</p>
                <p className="text-sm font-mono font-semibold text-emerald-800">
                  {objPreview.parseResult.vertices.length.toLocaleString()}
                </p>
              </div>
              <div className="bg-emerald-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Caras</p>
                <p className="text-sm font-mono font-semibold text-emerald-800">
                  {objPreview.parseResult.totalFaces.toLocaleString()}
                </p>
              </div>
              <div className="bg-emerald-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Objetos</p>
                <p className="text-sm font-mono font-semibold text-emerald-800">
                  {objPreview.parseResult.objects.length}
                </p>
              </div>
              <div className="bg-emerald-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Dimensiones</p>
                <p className="text-[11px] font-mono font-semibold text-emerald-800">
                  {objPreview.parseResult.boundingBox.dimensions.x.toFixed(1)} × {objPreview.parseResult.boundingBox.dimensions.y.toFixed(1)} × {objPreview.parseResult.boundingBox.dimensions.z.toFixed(1)}
                </p>
              </div>
              <div className="bg-emerald-50 rounded-lg p-3">
                <p className="text-[10px] text-gray-500 uppercase tracking-wide">Observador</p>
                <p className="text-[11px] font-mono font-semibold text-emerald-800">
                  ({objPreview.observationPoint.x.toFixed(1)}, {objPreview.observationPoint.y.toFixed(1)}, {objPreview.observationPoint.z.toFixed(1)})
                </p>
              </div>
            </div>

            {/* OBJ Settings */}
            <div className="flex flex-wrap items-center gap-4 bg-gray-50 rounded-lg p-3">
              <label className="flex items-center gap-2 text-xs">
                <span className="text-gray-700 font-medium">Eje Vertical:</span>
                <select
                  value={objUpAxis}
                  onChange={(e) => {
                    const val = e.target.value as 'X' | 'Y' | 'Z' | 'Y_simple';
                    setObjUpAxis(val);
                    setObjSwapYZ(val === 'Y_simple');
                    if (objRawParse) {
                      const northOff = sunPath3DPreview?.location.northOffset || objNorthOffset;
                      const result = convertOBJToObstacles(objRawParse, undefined, northOff, val, objScale, objRotationDeg);
                      setObjPreview(result);
                    }
                  }}
                  className="px-2 py-1 border border-gray-300 rounded text-xs bg-white"
                >
                  <option value="Z">Z-up (SketchUp, standard)</option>
                  <option value="Y">Y-up (Blender, glTF, Rhino)</option>
                  <option value="Y_simple">Intercambio Y/Z simple (Legacy)</option>
                  <option value="X">X-up (Raro)</option>
                </select>
              </label>
              <label className="flex items-center gap-2 text-xs">
                <span className="text-gray-700 font-medium">Rotación:</span>
                <input
                  type="number"
                  value={objRotationDeg}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value) || 0;
                    setObjRotationDeg(val);
                    if (objRawParse) {
                      const northOff = sunPath3DPreview?.location.northOffset || objNorthOffset;
                      const result = convertOBJToObstacles(objRawParse, undefined, northOff, objUpAxis, objScale, val);
                      setObjPreview(result);
                    }
                  }}
                  className="w-16 px-2 py-1 border border-gray-300 rounded text-xs font-mono bg-white"
                  step="90"
                />
                <span className="text-gray-500">°</span>
              </label>
              <label className="flex items-center gap-2 text-xs">
                <span className="text-gray-700">Escala:</span>
                <select
                  value={objScale}
                  onChange={(e) => {
                    const newScale = parseFloat(e.target.value);
                    setObjScale(newScale);
                    if (objRawParse) {
                      const northOff = sunPath3DPreview?.location.northOffset || objNorthOffset;
                      const result = convertOBJToObstacles(objRawParse, undefined, northOff, objUpAxis, newScale, objRotationDeg);
                      setObjPreview(result);
                    }
                  }}
                  className="px-2 py-1 border border-gray-300 rounded text-xs bg-white"
                >
                  <option value="0.001">mm → m (×0.001)</option>
                  <option value="0.01">cm → m (×0.01)</option>
                  <option value="0.0254">in → m (×0.0254)</option>
                  <option value="0.3048">ft → m (×0.3048)</option>
                  <option value="1">metros (×1)</option>
                </select>
              </label>
              <label className="flex items-center gap-2 text-xs">
                <span className="text-gray-700">North Offset:</span>
                <input
                  type="number"
                  value={objNorthOffset}
                  onChange={(e) => {
                    const newOffset = parseFloat(e.target.value) || 0;
                    setObjNorthOffset(newOffset);
                    if (objRawParse) {
                      const result = convertOBJToObstacles(objRawParse, undefined, newOffset, objUpAxis, objScale, objRotationDeg);
                      setObjPreview(result);
                    }
                  }}
                  className="w-16 px-2 py-1 border border-gray-300 rounded text-xs font-mono bg-white"
                  step="1"
                />
                <span className="text-gray-500">°</span>
              </label>
              {evaluationModel && (
                <button
                  type="button"
                  className="text-xs h-7 bg-violet-50 hover:bg-violet-100 border border-violet-200 text-violet-700 flex items-center gap-1 ml-auto px-2 rounded-md font-medium transition-colors"
                  onClick={() => {
                    const buildScale = evaluationModel.config.scaleFactor;
                    const buildUpAxis = evaluationModel.config.upAxis === 'auto' ? 'Z' : evaluationModel.config.upAxis;
                    const buildRot = evaluationModel.config.rotationDeg;
                    
                    setObjScale(buildScale);
                    setObjUpAxis(buildUpAxis as any);
                    setObjRotationDeg(buildRot);
                    setObjSwapYZ(buildUpAxis === 'Y_simple');
                    
                    if (objRawParse) {
                      const northOff = sunPath3DPreview?.location.northOffset || objNorthOffset;
                      const result = convertOBJToObstacles(objRawParse, undefined, northOff, buildUpAxis as any, buildScale, buildRot);
                      setObjPreview(result);
                    }
                    
                    toast.success("¡Configuración del Edificio sincronizada con el Obstáculo!");
                  }}
                >
                  <RefreshCw size={10} className="mr-1" />
                  Sincronizar con Edificio
                </button>
              )}
            </div>

            {/* Objects table */}
            {objPreview.obstacles.length > 0 && (
              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">#</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Nombre</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Color</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Vértices Hull</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Rango Azimut</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Rango Altitud</th>
                    </tr>
                  </thead>
                  <tbody>
                    {objPreview.obstacles.map((obs, idx) => {
                      const azMin = Math.min(...obs.vertices.map(v => v.azimuth));
                      const azMax = Math.max(...obs.vertices.map(v => v.azimuth));
                      const altMin = Math.min(...obs.vertices.map(v => v.altitude));
                      const altMax = Math.max(...obs.vertices.map(v => v.altitude));
                      return (
                        <tr key={obs.id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="px-3 py-2 font-mono">{idx + 1}</td>
                          <td className="px-3 py-2 font-medium">{obs.name}</td>
                          <td className="px-3 py-2">
                            <div className="flex items-center gap-1">
                              <span
                                className="inline-block w-4 h-4 rounded border border-gray-300"
                                style={{ backgroundColor: obs.color }}
                              />
                              <span className="font-mono text-gray-500">{obs.color}</span>
                            </div>
                          </td>
                          <td className="px-3 py-2 font-mono">{obs.vertices.length}</td>
                          <td className="px-3 py-2 font-mono">{azMin.toFixed(1)}° a {azMax.toFixed(1)}°</td>
                          <td className="px-3 py-2 font-mono">{altMin.toFixed(1)}° a {altMax.toFixed(1)}°</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {objPreview.obstacles.length === 0 && (
              <div className="text-xs text-orange-600 bg-orange-50 rounded p-2">
                <strong>Nota:</strong> No se generaron obstáculos visibles. Prueba ajustando la escala, intercambiando Y/Z, o modificando el North Offset.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Evaluation Model Importer (Edificio a evaluar) */}
      <EvaluationModelImporter
        existingObstacles={obstacles}
        existingObstacleVertices3D={obstacleVertices3D}
        onModelImported={handleModelImported}
        northOffset={sunPath3DPreview?.location.northOffset || objNorthOffset}
      />

      {/* Evaluation Model Summary + Facade Selector for Sun Path */}
      {evaluationModel && (
        <div className="bg-gradient-to-r from-violet-50 to-purple-50 border-2 border-violet-200 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-violet-200 text-violet-800">
                <Building2 size={20} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-sm">
                  Modelo a Evaluar: {evaluationModel.fileName}
                </h3>
                <p className="text-xs text-gray-600">
                  {evaluationModel.detectedFacades.length} superficie(s) detectada(s)
                  {' \u2014 '}
                  Dimensiones: {evaluationModel.dimensions.x.toFixed(1)} \u00d7 {evaluationModel.dimensions.y.toFixed(1)} \u00d7 {evaluationModel.dimensions.z.toFixed(1)} m
                </p>
              </div>
            </div>
            <Button
              onClick={() => { setEvaluationModel(null); setModelFacadeDefinitions(null); setActiveFacadeIdx(null); toast.info('Modelo de evaluaci\u00f3n removido'); }}
              variant="outline"
              size="sm"
              className="text-xs border-violet-300 text-violet-700 hover:bg-violet-100"
            >
              Remover Modelo
            </Button>
          </div>

          {/* Facade/Roof selector for Sun Path Diagram projection */}
          <div className="border-t border-violet-200 pt-3">
            <p className="text-xs font-semibold text-violet-800 mb-2">
              \ud83c\udfaf Seleccionar superficie para proyecci\u00f3n en Diagrama Solar:
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {evaluationModel.detectedFacades.map((facade, idx) => (
                <button
                  key={idx}
                  onClick={() => handleActiveFacadeChange(idx)}
                  className={`text-left px-3 py-2 rounded-lg border-2 transition-all text-xs ${
                    activeFacadeIdx === idx
                      ? 'border-violet-500 bg-violet-100 shadow-sm'
                      : 'border-gray-200 bg-white hover:border-violet-300 hover:bg-violet-50'
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: facade.color }}
                    />
                    <span className="font-medium text-gray-800 truncate">{facade.name}</span>
                  </div>
                  <div className="text-[10px] text-gray-500 mt-0.5 pl-4.5">
                    Az: {facade.azimuthNormal.toFixed(0)}\u00b0 | Incl: {facade.tilt.toFixed(0)}\u00b0 | {facade.area.toFixed(1)} m\u00b2
                  </div>
                </button>
              ))}
            </div>
            {activeFacadeIdx !== null && evaluationModel.detectedFacades[activeFacadeIdx] && (
              <div className="mt-2 px-3 py-2 bg-violet-100/50 rounded-lg border border-violet-200">
                <p className="text-[11px] text-violet-700">
                  <strong>Punto de evaluaci\u00f3n activo:</strong>{' '}
                  {evaluationModel.detectedFacades[activeFacadeIdx].name}{' \u2014 '}
                  Los obst\u00e1culos del diagrama solar se proyectan desde este punto.
                  {obstacleVertices3D && obstacleVertices3D.length > 0
                    ? ` (${obstacles.length} obst\u00e1culo(s) visible(s))`
                    : ' (Sin obst\u00e1culos 3D importados a\u00fan \u2014 importa obst\u00e1culos OBJ/Marsh para ver la proyecci\u00f3n)'
                  }
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Facade Comparison Table */}
      {evaluationModel && weatherData && (
        <FacadeComparisonTable
          facades={evaluationModel.detectedFacades}
          weatherData={weatherData}
          obstacleVertices3D={obstacleVertices3D}
          northOffset={evaluationModel.config.northOffset}
          activeFacadeIdx={activeFacadeIdx}
          onFacadeSelect={handleActiveFacadeChange}
        />
      )}

      {/* Obstacles summary banner */}
      {obstacles.length > 0 && (
        <div className="bg-gradient-to-r from-red-50 to-orange-50 border-2 border-red-200 rounded-xl p-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-200 text-red-800">
                <span className="text-lg">🏗️</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-sm">
                  {obstacles.length} obstáculo{obstacles.length !== 1 ? 's' : ''} dibujado{obstacles.length !== 1 ? 's' : ''} en el diagrama solar
                </h3>
                <p className="text-xs text-gray-600">
                  {obstacles.map(o => `${o.name} (${o.vertices.length}v)`).join(' · ')}
                  {' — '}
                  Los puntos de análisis dentro de un obstáculo se actualizan automáticamente.
                </p>
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              <input
                ref={obstacleFileInputRef}
                type="file"
                accept=".json"
                onChange={importObstacles}
                className="hidden"
              />
              <Button
                onClick={exportObstacles}
                variant="outline"
                size="sm"
                className="text-xs border-blue-300 text-blue-700 hover:bg-blue-100 flex items-center gap-1"
              >
                <Download size={12} />
                Exportar
              </Button>
              <Button
                onClick={() => obstacleFileInputRef.current?.click()}
                variant="outline"
                size="sm"
                className="text-xs border-green-300 text-green-700 hover:bg-green-100 flex items-center gap-1"
              >
                <Upload size={12} />
                Importar
              </Button>
              <Button
                onClick={() => {
                  setObstacles([]);
                  toast.info('Todos los obstáculos han sido eliminados');
                }}
                variant="outline"
                size="sm"
                className="text-xs border-red-300 text-red-700 hover:bg-red-100"
              >
                Limpiar Todos
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        <div className="flex justify-between items-center flex-wrap gap-2">
          <h2 className="text-2xl font-bold text-gray-900">Puntos de Analisis</h2>
          <div className="flex gap-2 flex-wrap">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={importFromCSV}
              className="hidden"
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Upload size={16} />
              Importar CSV/XLSX
            </Button>
            <Button
              onClick={downloadTemplate}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Download size={16} />
              Descargar Plantilla
            </Button>
            <Button
              onClick={exportToCSV}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Download size={16} />
              Exportar CSV
            </Button>
            <Button
              onClick={() => setShowCrossingModal(true)}
              className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700 text-white"
            >
              <Zap size={16} />
              Cruzar Máscara + EPW
            </Button>
            {lastCrossingResults && lastCrossingResults.length > 0 && (
              <Button
                onClick={exportCrossingPDF}
                className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white"
              >
                <FileText size={16} />
                Exportar PDF Sombreado
              </Button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                {points.some(p => p.evento) && (
                  <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">Evento</th>
                )}
                <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">Mes</th>
                <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">Día</th>
                <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">Hora</th>
                <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">
                  <div className="flex items-center gap-0.5">
                    Alt. Solar
                    {weatherData && autoCalcEnabled && (
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400" title="Auto-calculado desde EPW" />
                    )}
                  </div>
                </th>
                <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">
                  <div className="flex items-center gap-0.5">
                    Azimut
                    {weatherData && autoCalcEnabled && (
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400" title="Auto-calculado desde EPW" />
                    )}
                  </div>
                </th>
                <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">
                  <div className="flex items-center gap-0.5">
                    Obstáculo
                    {obstacles.length > 0 && (
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-400" title="Auto-detectado desde diagrama" />
                    )}
                  </div>
                </th>
                <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">
                  <div className="flex items-center gap-0.5">
                    Área Somb.
                    {obstacles.length > 0 && (
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-400" title="Auto-calculado desde obstáculos" />
                    )}
                  </div>
                </th>
                {points.some(p => p.fsGeometrico !== undefined) && (
                  <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">FS Geom.</th>
                )}
                {points.some(p => p.fsClimatico !== undefined) && (
                  <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">FS Clim.</th>
                )}
                <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">FS</th>
                {points.some(p => p.situacion) && (
                  <th className="px-1.5 py-1.5 text-left text-[10px] font-semibold text-gray-700">Situación</th>
                )}
                <th className="px-1.5 py-1.5 text-center text-[10px] font-semibold text-gray-700">Acc.</th>
              </tr>
            </thead>
            <tbody>
              {points.map((point, idx) => (
                <tr key={point.id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'} style={{ borderBottom: '1px solid #E5E7EB' }}>
                  {points.some(p => p.evento) && (
                    <td className="px-1 py-1">
                      <span className="text-[10px] text-gray-600 whitespace-nowrap">{point.evento || ''}</span>
                    </td>
                  )}
                  <td className="px-1 py-1">
                    <select
                      value={point.month}
                      onChange={(e) => updatePoint(point.id, 'month', e.target.value)}
                      className="w-14 px-1 py-0.5 border border-gray-300 rounded text-[11px] font-mono bg-white"
                    >
                      {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </td>
                  <td className="px-1 py-1">
                    <Input
                      type="number"
                      min="1"
                      max="31"
                      value={point.day}
                      onChange={(e) => updatePoint(point.id, 'day', Number(e.target.value))}
                      className="w-12 px-1 py-0.5 font-mono text-[11px]"
                    />
                  </td>
                  <td className="px-1 py-1">
                    {point.hourStr ? (
                      <span className="font-mono text-[11px] text-gray-700">{point.hourStr}</span>
                    ) : (
                      <Input
                        type="number"
                        min="0"
                        max="23"
                        value={point.hour}
                        onChange={(e) => updatePoint(point.id, 'hour', Number(e.target.value))}
                        className="w-12 px-1 py-0.5 font-mono text-[11px]"
                      />
                    )}
                  </td>
                  <td className="px-1 py-1">
                    <div className="relative">
                      <Input
                        type="number"
                        min="-5"
                        max="90"
                        step="0.1"
                        value={point.heightSolar}
                        onChange={(e) => updatePoint(point.id, 'heightSolar', Number(e.target.value))}
                        className={`w-14 px-1 py-0.5 font-mono text-[11px] ${
                          point.autoCalculated ? 'bg-amber-50 border-amber-200' : ''
                        }`}
                        title={point.autoCalculated ? 'Auto-calculado desde EPW' : 'Valor manual'}
                      />
                      {point.autoCalculated && (
                        <span className="absolute right-0.5 top-1/2 -translate-y-1/2 text-amber-500" title="Auto-calculado">
                          <Sun size={10} />
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-1 py-1">
                    <div className="relative">
                      <Input
                        type="number"
                        min="-180"
                        max="360"
                        step="0.1"
                        value={point.azimuthSolar}
                        onChange={(e) => updatePoint(point.id, 'azimuthSolar', Number(e.target.value))}
                        className={`w-16 px-1 py-0.5 font-mono text-[11px] ${
                          point.autoCalculated ? 'bg-amber-50 border-amber-200' : ''
                        }`}
                        title={point.autoCalculated ? 'Auto-calculado desde EPW' : 'Valor manual'}
                      />
                      {point.autoCalculated && (
                        <span className="absolute right-0.5 top-1/2 -translate-y-1/2 text-amber-500" title="Auto-calculado">
                          <Sun size={10} />
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-1 py-1">
                    <div className="relative">
                      <Input
                        type="text"
                        value={point.obstacle}
                        onChange={(e) => updatePoint(point.id, 'obstacle', e.target.value)}
                        placeholder="Obst."
                        className={`w-24 px-1 py-0.5 text-[10px] ${
                          point.obstacleAutoCalculated ? 'bg-red-50 border-red-200' : ''
                        }`}
                      />
                      {point.obstacleAutoCalculated && (
                        <span className="absolute right-0.5 top-1/2 -translate-y-1/2 text-red-400 text-[8px]" title="Auto-detectado desde diagrama">
                          🏗️
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-1 py-1">
                    <div className="relative">
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={point.shadowedArea}
                        onChange={(e) => updatePoint(point.id, 'shadowedArea', Number(e.target.value))}
                        className={`w-14 px-1 py-0.5 font-mono text-[11px] ${
                          point.obstacleAutoCalculated ? 'bg-red-50 border-red-200' : ''
                        }`}
                      />
                      {point.obstacleAutoCalculated && (
                        <span className="absolute right-0.5 top-1/2 -translate-y-1/2 text-red-400 text-[8px]" title="Auto-calculado desde obstáculos">
                          ⬛
                        </span>
                      )}
                    </div>
                  </td>
                  {points.some(p => p.fsGeometrico !== undefined) && (
                    <td className="px-1 py-1 text-center">
                      <span className="font-mono text-[11px] text-gray-700">{(point.fsGeometrico ?? 0).toFixed(3)}</span>
                    </td>
                  )}
                  {points.some(p => p.fsClimatico !== undefined) && (
                    <td className={`px-1 py-1 text-center ${(point.fsClimatico ?? 0) > 0.5 ? 'bg-red-50' : (point.fsClimatico ?? 0) > 0.2 ? 'bg-amber-50' : ''}`}>
                      <span className="font-mono text-[11px] text-gray-700">{(point.fsClimatico ?? 0).toFixed(3)}</span>
                    </td>
                  )}
                  <td className={`px-1 py-1 ${getColorFS(point.fs)} border rounded text-center`}>
                    <span className={`font-mono text-[11px] font-bold ${getTextColorFS(point.fs)}`}>
                      {point.fs.toFixed(3)}
                    </span>
                  </td>
                  {points.some(p => p.situacion) && (
                    <td className="px-1 py-1">
                      <span className={`text-[9px] whitespace-nowrap px-1 py-0.5 rounded ${
                        point.situacion?.includes('despejado') ? 'bg-green-100 text-green-700' :
                        point.situacion?.includes('Parcialmente') ? 'bg-amber-100 text-amber-700' :
                        point.situacion?.includes('nublado') ? 'bg-blue-100 text-blue-700' :
                        point.situacion?.includes('cubierto') ? 'bg-gray-200 text-gray-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>{point.situacion || ''}</span>
                    </td>
                  )}
                  <td className="px-1 py-1 text-center">
                    <button
                      onClick={() => deletePoint(point.id)}
                      className="inline-flex items-center justify-center w-6 h-6 rounded hover:bg-red-100 text-red-600 transition-colors"
                      title="Eliminar fila"
                    >
                      <Trash2 size={12} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Button
        onClick={addPoint}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center gap-2 py-2 rounded-lg"
      >
        <Plus size={18} />
        Agregar Punto de Analisis
      </Button>

      {/* Sun Path Diagram Toggle Button + Diagram */}
      {weatherData && (
        <div className="space-y-3">
          <Button
            onClick={() => setShowSunPath(!showSunPath)}
            variant="outline"
            className={`w-full flex items-center justify-center gap-2 py-3 rounded-lg border-2 transition-all ${
              showSunPath
                ? 'bg-amber-50 border-amber-400 text-amber-800 hover:bg-amber-100'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <MapPin size={18} />
            {showSunPath ? 'Ocultar Diagrama de Trayectoria Solar' : 'Mostrar Diagrama de Trayectoria Solar'}
          </Button>
          {showSunPath && (
            <SunPathDiagram
              latitude={weatherData.location.latitude}
              longitude={weatherData.location.longitude}
              timezone={weatherData.location.timezone}
              analysisPoints={points.map(p => ({
                month: p.month,
                day: p.day,
                hour: p.hour,
                heightSolar: p.heightSolar,
                azimuthSolar: p.azimuthSolar,
                fs: p.fs,
              }))}
              onPositionSelect={(data) => {
                const newPoint: AnalysisPoint = {
                  id: Date.now().toString() + Math.random(),
                  month: data.month,
                  day: data.day,
                  hour: data.hour,
                  heightSolar: data.altitude,
                  azimuthSolar: data.azimuth,
                  obstacle: '',
                  shadowedArea: 0,
                  fs: 1.0,
                  autoCalculated: true,
                };
                setPoints(prev => [...prev, newPoint]);
                toast.success(
                  `Punto agregado: ${data.month} ${data.day}, ${data.hour}:00h — Alt: ${data.altitude.toFixed(1)}° Az: ${data.azimuth.toFixed(1)}°`
                );
              }}
              obstacles={obstacles}
              onObstaclesChange={handleObstaclesChange}
            />
          )}
        </div>
      )}

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <FSDistributionChart data={points} />
      </div>

      {/* Crossing Modal */}
      <CrossingModal
        open={showCrossingModal}
        onOpenChange={setShowCrossingModal}
        weatherData={weatherData || null}
        obstacles={obstacles}
        onResultsGenerated={handleCrossingResults}
        onRawCrossingResults={handleRawCrossingResults}
        modelFacades={modelFacadeDefinitions || undefined}
      />

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Como usar esta calculadora:</h3>
        <div className="text-sm text-gray-700 space-y-2">
          <p><strong>1. Carga un archivo EPW:</strong> Ve a "Datos Meteorológicos" y carga un archivo EPW. La latitud, longitud y zona horaria se usarán para calcular automáticamente la posición solar (altura y azimut) para cada punto de análisis.</p>
          <p><strong>2. Selecciona mes, día y hora:</strong> Al cambiar estos valores, la altura solar y el azimut se recalculan automáticamente usando el algoritmo de posición solar (SPA). Los campos auto-calculados se muestran con fondo ámbar y un icono de sol.</p>
          <p><strong>3. Especifica el obstáculo:</strong> Nombre del elemento que proyecta sombra (edificio, árbol, chimenea, etc.).</p>
          <p><strong>4. Indica el área sombreada:</strong> Porcentaje del panel solar que está sombreado (0-100%).</p>
          <p><strong>5. Dibuja obstáculos en el diagrama:</strong> Abre el Diagrama de Trayectoria Solar y usa el botón "Dibujar Obstáculo" para trazar polígonos de sombra. Los puntos de análisis que caigan dentro de un obstáculo se actualizarán automáticamente con el nombre del obstáculo y el porcentaje de sombreado.</p>
          <p><strong>5b. Importa desde Andrew Marsh Site Designer:</strong> Carga un archivo JSON exportado desde la herramienta <a href="https://andrewmarsh.com/software/site-designer-web/" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Site Designer</a> de Andrew Marsh. Los bloques 3D del modelo se convierten automáticamente en polígonos de obstáculo proyectados sobre el diagrama de trayectoria solar.</p>
          <p><strong>5c. Importa desde Sun Path 3D:</strong> Carga un JSON de <a href="https://drajmarsh.bitbucket.io/sunpath3d.html" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Sun Path 3D</a> de Andrew Marsh para aplicar automáticamente la ubicación (latitud, longitud, zona horaria) y agregar un punto de análisis con la fecha/hora configurada en la herramienta.</p>
          <p><strong>5d. Importa modelos OBJ:</strong> Carga archivos <code className="bg-gray-100 px-1 rounded">.obj</code> (Wavefront) exportados desde Sun Path 3D, SketchUp, Blender u otro software 3D. La geometría 3D se proyecta desde el punto de observación para generar polígonos de obstáculo en el diagrama solar. Puedes ajustar la escala, intercambiar ejes Y/Z y rotar el norte.</p>
          <p><strong>6. Cálculo automático:</strong> El Factor de Sombreado (FS) se calcula como: FS = 1 - (Área Sombreada / 100)</p>
          <p><strong>7. Modo manual:</strong> Puedes desactivar el auto-cálculo con el checkbox o editar manualmente los campos de altura/azimut (se desactiva el auto-cálculo para ese punto).</p>
          <p><strong>Interpretación:</strong> FS = 1.0 significa sin sombreado (máximo rendimiento). FS menor a 0.9 indica sombreado significativo que reduce la producción de energía.</p>
        </div>
      </div>
    </div>
  );
}
