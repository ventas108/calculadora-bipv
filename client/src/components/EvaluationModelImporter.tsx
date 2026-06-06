/**
 * EvaluationModelImporter Component
 * 
 * UI para importar un modelo 3D del edificio a evaluar (OBJ desde SketchUp, Blender, etc.)
 * Detecta fachadas automáticamente y recalcula obstáculos desde la perspectiva del modelo.
 * Incluye auto-detección y corrección manual del eje vertical (Z-up/Y-up/X-up).
 */

import { useState, useRef, useCallback, lazy, Suspense } from 'react';
import { Button } from '@/components/ui/button';
import { Upload, Building2, Eye, RotateCcw, Check, X, ChevronDown, ChevronUp, Box, SlidersHorizontal, RefreshCw, Compass } from 'lucide-react';

// Lazy load the 3D viewer to avoid loading Three.js until needed
const ModelViewer3D = lazy(() => import('./ModelViewer3D'));
import { toast } from 'sonner';
import { ObstaclePolygon } from './SunPathDiagram';
import {
  EvaluationModel,
  ImportConfig,
  DEFAULT_IMPORT_CONFIG,
  Vertex3D,
  DetectedFacade,
  importBuildingModel,
  validateBuildingModel,
  getModelSummary,
  recalculateForFacade,
  UpAxis,
} from '@/lib/buildingModelImporter';
import { OBJParseResult } from '@/lib/objParser';
import { FacadeDefinition } from '@/lib/shadingMaskCrossing';
import { parseGLTF, validateGLTF, isGLB, getGLTFSummary } from '@/lib/gltfParser';
import {
  detectFormat,
  isUnsupportedFormat,
  getConversionAdvice,
  parseMultiFormat,
  getAcceptedExtensions,
  SUPPORTED_FORMATS,
} from '@/lib/multiFormatParser';

interface EvaluationModelImporterProps {
  /** Obstáculos actuales del diagrama solar (entorno) */
  existingObstacles: ObstaclePolygon[];
  /** Vértices 3D de los obstáculos (si están disponibles desde importación OBJ/Marsh) */
  existingObstacleVertices3D?: Vertex3D[][];
  /** Callback cuando se confirma la importación */
  onModelImported: (result: {
    model: EvaluationModel;
    recalculatedObstacles: ObstaclePolygon[];
    facadeDefinitions: FacadeDefinition[];
    selectedFacade: DetectedFacade | null;
  }) => void;
  /** North offset actual (desde Sun Path 3D u otra fuente) */
  northOffset?: number;
}

interface AxisDetectionInfo {
  axis: string;
  confidence: string;
  scores?: Record<string, { roofFaces: number; verticalFaces: number; heightRatio: number; score: number }>;
}

export default function EvaluationModelImporter({
  existingObstacles,
  existingObstacleVertices3D,
  onModelImported,
  northOffset = 0,
}: EvaluationModelImporterProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [model, setModel] = useState<EvaluationModel | null>(null);
  const [fileName, setFileName] = useState('');
  const [config, setConfig] = useState<ImportConfig>({
    ...DEFAULT_IMPORT_CONFIG,
    northOffset,
  });
  const [selectedFacadeIdx, setSelectedFacadeIdx] = useState<number | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [show3DViewer, setShow3DViewer] = useState(true);

  // Raw parse result for re-processing without file reload
  const [rawParseResult, setRawParseResult] = useState<OBJParseResult | null>(null);
  // Auto-detection result info
  const [detectedAxisInfo, setDetectedAxisInfo] = useState<AxisDetectionInfo | null>(null);

  // Roof tilt overrides: { [facadeIdx]: { tilt, azimuth, roofType } }
  interface RoofOverride {
    tilt: number; // 0-45°
    azimuth: number; // azimut de la pendiente (dirección hacia donde baja el agua)
    roofType: 'flat' | 'single_slope' | 'gable' | 'hip';
  }
  const [roofOverrides, setRoofOverrides] = useState<Record<number, RoofOverride>>({});
  const [showRoofEditor, setShowRoofEditor] = useState<number | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  /** Process a parsed OBJParseResult with the given config */
  const processParseResult = useCallback((parseResult: OBJParseResult, importConfig: ImportConfig, fName: string): EvaluationModel | null => {
    try {
      const result = importBuildingModel(parseResult, importConfig, existingObstacleVertices3D);
      result.fileName = fName;

      // Extract auto-detection info from parseResult metadata
      const detectedAxis = (parseResult as any).__detectedUpAxis;
      const confidence = (parseResult as any).__detectionConfidence;
      const scores = (parseResult as any).__detectionScores;
      if (detectedAxis) {
        setDetectedAxisInfo({ axis: detectedAxis, confidence, scores });
      }

      return result;
    } catch (error: any) {
      toast.error(`Error al procesar el modelo: ${error.message || 'Error desconocido'}`);
      console.error(error);
      return null;
    }
  }, [existingObstacleVertices3D]);

  const handleFileImport = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setIsProcessing(true);
    setDetectedAxisInfo(null);

    const ext = file.name.toLowerCase().split('.').pop() || '';
    const isGLTFFile = ext === 'gltf' || ext === 'glb';
    const isOBJFile = ext === 'obj';
    const detectedFormat = detectFormat(file.name);
    const isNewFormat = detectedFormat && !isOBJFile && !isGLTFFile;

    // Check if format is unsupported (DWG, XSI) and show conversion advice
    if (detectedFormat && isUnsupportedFormat(detectedFormat)) {
      toast.error(getConversionAdvice(detectedFormat), { duration: 10000 });
      setIsProcessing(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const currentConfig = { ...config, northOffset: northOffset || config.northOffset };
        let parseResult: OBJParseResult;

        if (isNewFormat && detectedFormat) {
          // ===== NUEVOS FORMATOS: DXF, FBX, STL, DAE, VRML, 3DS =====
          const rawResult = e.target?.result;
          if (!rawResult) {
            toast.error('No se pudo leer el archivo');
            setIsProcessing(false);
            return;
          }

          try {
            const { result: parsed, formatName } = await parseMultiFormat(file.name, rawResult);
            parseResult = parsed;
            toast.info(`${formatName}: ${parsed.vertices.length} vértices, ${parsed.totalFaces} caras, ${parsed.objects.length} objeto(s)`);
          } catch (parseError: any) {
            toast.error(parseError.message || 'Error al parsear el archivo');
            setModel(null);
            setIsProcessing(false);
            return;
          }

          // Process with auto-detect axis (same as OBJ)
          const result = processParseResult(parseResult, currentConfig, file.name);
          if (result) {
            // Extract detection info
            const detectedAxis = (parseResult as any).__detectedUpAxis;
            const confidence = (parseResult as any).__detectionConfidence;
            const scores = (parseResult as any).__detectionScores;
            if (detectedAxis) {
              setDetectedAxisInfo({ axis: detectedAxis, confidence, scores });
            }

            setRawParseResult(parseResult);
            setModel(result);
            setSelectedFacadeIdx(null);
            setRoofOverrides({});

            const summary = getModelSummary(result);
            if (result.detectedFacades.length > 0) {
              toast.success(
                `Modelo cargado: ${summary.dimensions}. Se detectaron ${summary.facadeCount} superficie(s): ${summary.facadeNames.join(', ')}`
              );
            } else {
              toast.warning(
                `Modelo cargado (${summary.vertexCount} vértices, ${summary.faceCount} caras) pero no se detectaron superficies evaluables. Prueba cambiar el eje vertical en Configuración Avanzada.`
              );
            }
          }
          setIsProcessing(false);
          return;
        } else if (isGLTFFile) {
          // Parse glTF/GLB
          const rawResult = e.target?.result;
          if (!rawResult) {
            toast.error('No se pudo leer el archivo');
            setIsProcessing(false);
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
            setModel(null);
            setIsProcessing(false);
            return;
          }

          const gltfResult = parseGLTF(input);
          const gltfSummary = getGLTFSummary(gltfResult);
          parseResult = gltfResult.objResult;
          toast.info(`glTF: ${gltfSummary.split('\n').slice(0, 2).join(' | ')}`);
        } else {
          // OBJ format
          const text = e.target?.result as string;
          const validation = validateBuildingModel(text);
          if (!validation.valid) {
            toast.error(validation.message);
            setModel(null);
            setIsProcessing(false);
            return;
          }
          const result = importBuildingModel(text, currentConfig, existingObstacleVertices3D);
          result.fileName = file.name;
          parseResult = result.parseResult;

          // Extract detection info
          const detectedAxis = (parseResult as any).__detectedUpAxis;
          const confidence = (parseResult as any).__detectionConfidence;
          const scores = (parseResult as any).__detectionScores;
          if (detectedAxis) {
            setDetectedAxisInfo({ axis: detectedAxis, confidence, scores });
          }

          setRawParseResult(parseResult);
          setModel(result);
          setSelectedFacadeIdx(null);
          setRoofOverrides({});

          const summary = getModelSummary(result);
          if (result.detectedFacades.length > 0) {
            toast.success(
              `Modelo cargado: ${summary.dimensions}. Se detectaron ${summary.facadeCount} superficie(s): ${summary.facadeNames.join(', ')}`
            );
          } else {
            toast.warning(
              `Modelo cargado (${summary.vertexCount} vértices, ${summary.faceCount} caras) pero no se detectaron superficies evaluables. Prueba cambiar el eje vertical en Configuración Avanzada.`
            );
          }
          setIsProcessing(false);
          return; // Early return for OBJ since we already processed it
        }

        // For glTF/GLB: forzar Y-up (es la especificación del formato glTF)
        // La especificación glTF define que Y es el eje vertical (arriba)
        const gltfConfig = { ...currentConfig, upAxis: 'Y' as const };
        setRawParseResult(parseResult);
        setConfig(prev => ({ ...prev, upAxis: 'Y' }));
        setDetectedAxisInfo({ axis: 'Y', confidence: 'high', scores: {} });
        const result = processParseResult(parseResult, gltfConfig, file.name);
        if (result) {
          setModel(result);
          setSelectedFacadeIdx(null);
          setRoofOverrides({});

          const summary = getModelSummary(result);
          if (result.detectedFacades.length > 0) {
            toast.success(
              `Modelo cargado: ${summary.dimensions}. Se detectaron ${summary.facadeCount} superficie(s): ${summary.facadeNames.join(', ')}`
            );
          } else {
            toast.warning(
              `Modelo cargado (${summary.vertexCount} vértices, ${summary.faceCount} caras) pero no se detectaron superficies evaluables. Prueba cambiar el eje vertical en Configuración Avanzada.`
            );
          }
        }
        setIsProcessing(false);
      } catch (error: any) {
        toast.error(`Error al procesar el archivo: ${error.message || 'Error desconocido'}`);
        console.error(error);
        setModel(null);
        setIsProcessing(false);
      }
    };

    // Read as ArrayBuffer for binary formats, as text for text formats
    const binaryFormats = ['glb', 'fbx', '3ds', 'stl'];
    if (binaryFormats.includes(ext)) {
      reader.readAsArrayBuffer(file);
    } else {
      reader.readAsText(file);
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [config, northOffset, existingObstacleVertices3D, processParseResult]);

  /** Re-process the model with updated config (no file reload needed) */
  const reconvertModel = useCallback((newConfig?: ImportConfig) => {
    if (!rawParseResult) {
      toast.error('Carga un archivo primero para poder re-procesar.');
      return;
    }
    setIsProcessing(true);
    const effectiveConfig = newConfig || config;
    const importConfig = { ...effectiveConfig, northOffset: northOffset || effectiveConfig.northOffset };

    // Clear previous detection info for fresh auto-detect
    delete (rawParseResult as any).__detectedUpAxis;
    delete (rawParseResult as any).__detectionConfidence;
    delete (rawParseResult as any).__detectionScores;

    const result = processParseResult(rawParseResult, importConfig, fileName);
    if (result) {
      setModel(result);
      setSelectedFacadeIdx(null);
      setRoofOverrides({});

      const summary = getModelSummary(result);
      if (result.detectedFacades.length > 0) {
        toast.success(
          `Modelo re-procesado: ${summary.facadeCount} superficie(s) detectadas. ${summary.dimensions}`
        );
      } else {
        toast.warning(
          'Modelo re-procesado pero no se detectaron superficies evaluables. Prueba otro eje vertical o escala.'
        );
      }
    }
    setIsProcessing(false);
  }, [rawParseResult, config, northOffset, fileName, processParseResult]);

  const handleFacadeSelect = (idx: number) => {
    setSelectedFacadeIdx(idx === selectedFacadeIdx ? null : idx);

    if (model && existingObstacleVertices3D && idx !== selectedFacadeIdx) {
      const facade = model.detectedFacades[idx];
      const recalculated = recalculateForFacade(facade, existingObstacleVertices3D, config.northOffset);
      setModel(prev => prev ? { ...prev, recalculatedObstacles: recalculated } : null);
      toast.info(`Obstáculos recalculados desde ${facade.name} (${recalculated.length} obstáculos visibles)`);
    }
  };

  const confirmImport = () => {
    if (!model) return;

    const selectedFacade = selectedFacadeIdx !== null
      ? model.detectedFacades[selectedFacadeIdx]
      : null;

    // Apply roof overrides to facadeDefinitions
    const adjustedFacadeDefinitions = model.facadeDefinitions.map((fd, idx) => {
      const override = roofOverrides[idx];
      if (!override) return fd;

      if (override.roofType === 'flat') {
        return { ...fd, tilt: 0 };
      }
      return {
        ...fd,
        tilt: override.tilt,
        azimuthNormal: override.azimuth,
      };
    });

    // Expand gable/hip roofs into multiple surfaces
    const expandedDefinitions: typeof adjustedFacadeDefinitions = [];
    for (let i = 0; i < adjustedFacadeDefinitions.length; i++) {
      const fd = adjustedFacadeDefinitions[i];
      const override = roofOverrides[i];
      if (override && override.roofType === 'gable') {
        expandedDefinitions.push({
          ...fd,
          name: `${fd.name} (Agua 1)`,
          tilt: override.tilt,
          azimuthNormal: override.azimuth,
        });
        expandedDefinitions.push({
          ...fd,
          name: `${fd.name} (Agua 2)`,
          tilt: override.tilt,
          azimuthNormal: (override.azimuth + 180) % 360 - (override.azimuth + 180 >= 180 ? 360 : 0),
        });
      } else if (override && override.roofType === 'hip') {
        expandedDefinitions.push({
          ...fd,
          name: `${fd.name} (Agua N)`,
          tilt: override.tilt,
          azimuthNormal: override.azimuth,
        });
        expandedDefinitions.push({
          ...fd,
          name: `${fd.name} (Agua S)`,
          tilt: override.tilt,
          azimuthNormal: (override.azimuth + 180) % 360 - (override.azimuth + 180 >= 180 ? 360 : 0),
        });
        expandedDefinitions.push({
          ...fd,
          name: `${fd.name} (Agua E)`,
          tilt: override.tilt,
          azimuthNormal: (override.azimuth + 90) % 360 - (override.azimuth + 90 >= 180 ? 360 : 0),
        });
        expandedDefinitions.push({
          ...fd,
          name: `${fd.name} (Agua O)`,
          tilt: override.tilt,
          azimuthNormal: (override.azimuth - 90 + 360) % 360 - (override.azimuth - 90 + 360 >= 180 ? 360 : 0),
        });
      } else {
        expandedDefinitions.push(fd);
      }
    }

    onModelImported({
      model,
      recalculatedObstacles: model.recalculatedObstacles,
      facadeDefinitions: expandedDefinitions,
      selectedFacade,
    });

    const roofCount = Object.keys(roofOverrides).length;
    const roofMsg = roofCount > 0 ? ` (${roofCount} techo(s) con inclinación ajustada)` : '';
    toast.success(
      `Modelo "${model.fileName}" importado. ${expandedDefinitions.length} superficie(s) disponibles para el cruce Máscara + EPW.${roofMsg}`
    );
  };

  const cancelImport = () => {
    setModel(null);
    setFileName('');
    setSelectedFacadeIdx(null);
    setRawParseResult(null);
    setDetectedAxisInfo(null);
    toast.info('Importación del modelo cancelada');
  };

  /** Handle upAxis change and re-process */
  const handleUpAxisChange = (newAxis: UpAxis) => {
    const newConfig = { ...config, upAxis: newAxis, swapYZ: false };
    setConfig(newConfig);
    if (rawParseResult) {
      reconvertModel(newConfig);
    }
  };

  /** Handle rotation change and re-process */
  const handleRotationChange = (deg: number) => {
    const newConfig = { ...config, rotationDeg: deg };
    setConfig(newConfig);
    if (rawParseResult) {
      reconvertModel(newConfig);
    }
  };

  const confidenceLabel = (c: string) => {
    switch (c) {
      case 'high': return { text: 'Alta', color: 'bg-green-100 text-green-800 border-green-300' };
      case 'medium': return { text: 'Media', color: 'bg-yellow-100 text-yellow-800 border-yellow-300' };
      default: return { text: 'Baja', color: 'bg-red-100 text-red-800 border-red-300' };
    }
  };

  const axisLabel = (a: string) => {
    switch (a) {
      case 'Z': return 'Z-up (SketchUp, algunos OBJ)';
      case 'Y': return 'Y-up (Blender, glTF, Unity)';
      case 'X': return 'X-up (raro)';
      default: return a;
    }
  };

  return (
    <div className="bg-gradient-to-r from-violet-50 to-purple-50 border-2 border-violet-200 rounded-xl p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-violet-200 text-violet-800">
            <Building2 size={22} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-sm">
              Importar Modelo 3D a Evaluar — Edificio Propio
            </h3>
            <p className="text-xs text-gray-600">
              Carga un archivo 3D del edificio a evaluar ({' '}
              <code className="bg-gray-100 px-1 rounded">.obj</code>,{' '}
              <code className="bg-gray-100 px-1 rounded">.gltf/.glb</code>,{' '}
              <code className="bg-gray-100 px-1 rounded">.dxf</code>,{' '}
              <code className="bg-gray-100 px-1 rounded">.fbx</code>,{' '}
              <code className="bg-gray-100 px-1 rounded">.stl</code>,{' '}
              <code className="bg-gray-100 px-1 rounded">.dae</code>,{' '}
              <code className="bg-gray-100 px-1 rounded">.wrl</code>,{' '}
              <code className="bg-gray-100 px-1 rounded">.3ds</code>)
              exportado desde SketchUp, Blender, Rhino, Revit, AutoCAD, Sun Path 3D, 3ds Max.
              Se detectarán fachadas, techos/cubiertas y superficies curvas automáticamente.
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".obj,.gltf,.glb,.dxf,.dwg,.fbx,.stl,.dae,.wrl,.vrml,.3ds,.xsi"
            onChange={handleFileImport}
            className="hidden"
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            variant="outline"
            size="sm"
            className="flex items-center gap-1 text-xs border-violet-300 text-violet-800 hover:bg-violet-100"
            disabled={isProcessing}
          >
            <Upload size={14} />
            {isProcessing ? 'Procesando...' : 'Cargar Modelo 3D'}
          </Button>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      {!model && (
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${
            isDragging
              ? 'border-violet-500 bg-violet-50'
              : 'border-gray-300 hover:border-violet-300 hover:bg-violet-50/30'
          }`}
          onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); }}
          onDragEnter={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); }}
          onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); }}
          onDrop={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setIsDragging(false);
            const file = e.dataTransfer.files?.[0];
            if (file) {
              // Create a synthetic event-like object for handleFileImport
              const dt = new DataTransfer();
              dt.items.add(file);
              if (fileInputRef.current) {
                fileInputRef.current.files = dt.files;
                fileInputRef.current.dispatchEvent(new Event('change', { bubbles: true }));
              }
            }
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <Box size={24} className={`mx-auto mb-2 ${isDragging ? 'text-violet-500' : 'text-gray-400'}`} />
          <p className={`text-sm font-medium ${isDragging ? 'text-violet-700' : 'text-gray-600'}`}>
            {isDragging ? 'Suelta el archivo aquí' : 'Arrastra un modelo 3D aquí o haz clic para seleccionar'}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            OBJ · glTF/GLB · DXF · FBX · STL · DAE · WRL · 3DS
          </p>
        </div>
      )}

      {/* Model Preview */}
      {model && (
        <div className="bg-white border border-violet-200 rounded-lg p-4 space-y-4">
          {/* Summary header */}
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-gray-900 text-sm">
              Modelo: {fileName}
            </h4>
            <div className="flex gap-2">
              <Button
                onClick={confirmImport}
                size="sm"
                className="bg-violet-600 hover:bg-violet-700 text-white text-xs"
                disabled={model.detectedFacades.length === 0}
              >
                <Check size={12} className="mr-1" />
                Confirmar Importación ({model.detectedFacades.length} superficies)
              </Button>
              <Button
                onClick={cancelImport}
                variant="outline"
                size="sm"
                className="text-xs border-gray-300"
              >
                <X size={12} className="mr-1" />
                Cancelar
              </Button>
            </div>
          </div>

          {/* Auto-detection result badge */}
          {detectedAxisInfo && (
            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center gap-1.5 bg-violet-50 border border-violet-200 rounded-lg px-3 py-1.5">
                <Compass size={14} className="text-violet-600" />
                <span className="text-xs text-gray-700">Eje vertical:</span>
                <span className="text-xs font-semibold text-violet-800">
                  {axisLabel(detectedAxisInfo.axis)}
                </span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${confidenceLabel(detectedAxisInfo.confidence).color}`}>
                  Confianza: {confidenceLabel(detectedAxisInfo.confidence).text}
                </span>
              </div>
              {detectedAxisInfo.confidence === 'low' && (
                <div className="w-full bg-amber-50 border border-amber-300 rounded-lg px-3 py-2 mt-1">
                  <p className="text-xs text-amber-800 font-medium">
                    ⚠️ La detección automática tiene baja confianza. Verifica que el techo esté arriba en el visor 3D.
                  </p>
                  <p className="text-[10px] text-amber-700 mt-0.5">
                    Si el modelo se ve incorrecto (techo en dirección lateral), cambia el eje vertical en <strong>Configuración Avanzada</strong> abajo.
                    Prueba: <button onClick={() => handleUpAxisChange('Y')} className="underline font-semibold text-amber-900 hover:text-amber-600">Y-up (Blender)</button> | <button onClick={() => handleUpAxisChange('Z')} className="underline font-semibold text-amber-900 hover:text-amber-600">Z-up (SketchUp)</button>
                  </p>
                </div>
              )}
              {detectedAxisInfo.confidence === 'medium' && (
                <p className="text-[10px] text-amber-700">
                  Si el modelo se ve incorrecto, cambia el eje vertical en Configuración Avanzada.
                </p>
              )}
            </div>
          )}

          {/* Stats grid */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-violet-50 rounded-lg p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wide">Vértices</p>
              <p className="text-sm font-mono font-semibold text-violet-800">
                {model.parseResult.vertices.length.toLocaleString()}
              </p>
            </div>
            <div className="bg-violet-50 rounded-lg p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wide">Caras</p>
              <p className="text-sm font-mono font-semibold text-violet-800">
                {model.parseResult.totalFaces.toLocaleString()}
              </p>
            </div>
            <div className="bg-violet-50 rounded-lg p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wide">Dimensiones</p>
              <p className="text-[11px] font-mono font-semibold text-violet-800">
                {model.dimensions.x.toFixed(1)} × {model.dimensions.y.toFixed(1)} × {model.dimensions.z.toFixed(1)} m
              </p>
            </div>
            <div className="bg-violet-50 rounded-lg p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wide">Fachadas</p>
              <p className="text-sm font-mono font-semibold text-violet-800">
                {model.detectedFacades.length}
              </p>
            </div>
            <div className="bg-violet-50 rounded-lg p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wide">Área Fachadas</p>
              <p className="text-sm font-mono font-semibold text-violet-800">
                {model.detectedFacades.reduce((s, f) => s + f.area, 0).toFixed(1)} m²
              </p>
            </div>
          </div>

          {/* Detected Facades Table */}
          {model.detectedFacades.length > 0 && (
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                Fachadas Detectadas (clic para seleccionar punto de evaluación)
              </h5>
              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">#</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Fachada</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Azimut Normal</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Inclinación</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Área</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Punto Eval.</th>
                      <th className="px-3 py-2 text-center font-semibold text-gray-600">Seleccionar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {model.detectedFacades.map((facade, idx) => (
                      <tr
                        key={idx}
                        className={`cursor-pointer transition-colors ${
                          selectedFacadeIdx === idx
                            ? 'bg-violet-100 border-l-4 border-l-violet-500'
                            : idx % 2 === 0 ? 'bg-white hover:bg-violet-50' : 'bg-gray-50 hover:bg-violet-50'
                        }`}
                        onClick={() => handleFacadeSelect(idx)}
                      >
                        <td className="px-3 py-2 font-mono">
                          <span
                            className="inline-block w-4 h-4 rounded border border-gray-300"
                            style={{ backgroundColor: facade.color }}
                          />
                        </td>
                        <td className="px-3 py-2 font-medium">{facade.name}</td>
                        <td className="px-3 py-2 font-mono">{facade.azimuthNormal.toFixed(1)}°</td>
                        <td className="px-3 py-2 font-mono">{facade.tilt.toFixed(1)}°</td>
                        <td className="px-3 py-2 font-mono">{facade.area.toFixed(1)} m²</td>
                        <td className="px-3 py-2 font-mono text-[10px]">
                          ({facade.evaluationPoint.x.toFixed(1)}, {facade.evaluationPoint.y.toFixed(1)}, {facade.evaluationPoint.z.toFixed(1)})
                        </td>
                        <td className="px-3 py-2 text-center">
                          {selectedFacadeIdx === idx ? (
                            <Eye size={14} className="inline text-violet-600" />
                          ) : (
                            <span className="text-gray-400">○</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Roof Tilt Editor */}
          {model.detectedFacades.some(f => f.tilt < 30) && (
            <div className="space-y-2 bg-amber-50 border border-amber-200 rounded-lg p-3">
              <h5 className="text-xs font-semibold text-amber-800 uppercase tracking-wide flex items-center gap-1">
                <SlidersHorizontal size={12} className="text-amber-600" />
                Ajuste de Inclinación de Techos
              </h5>
              <p className="text-[10px] text-amber-700">
                Defina la pendiente real del techo cuando el modelo 3D no la refleja exactamente.
                Esto afecta el cálculo de radiación POA en el cruce Máscara+EPW.
              </p>
              <div className="space-y-2">
                {model.detectedFacades.map((facade, idx) => {
                  if (facade.tilt >= 30) return null; // Solo mostrar techos
                  const override = roofOverrides[idx];
                  const isEditing = showRoofEditor === idx;
                  return (
                    <div key={idx} className="bg-white border border-amber-100 rounded-md p-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span
                            className="inline-block w-3 h-3 rounded border border-gray-300"
                            style={{ backgroundColor: facade.color }}
                          />
                          <span className="text-xs font-medium text-gray-700">{facade.name}</span>
                          <span className="text-[10px] text-gray-500">
                            ({facade.area.toFixed(1)} m²)
                          </span>
                          {override && (
                            <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-medium">
                              {override.roofType === 'flat' ? 'Plano (0°)' :
                               override.roofType === 'single_slope' ? `Una agua (${override.tilt}°)` :
                               override.roofType === 'gable' ? `Dos aguas (${override.tilt}°)` :
                               `Cuatro aguas (${override.tilt}°)`}
                            </span>
                          )}
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-[10px] h-6 px-2 border-amber-300 hover:bg-amber-50"
                          onClick={() => setShowRoofEditor(isEditing ? null : idx)}
                        >
                          {isEditing ? 'Cerrar' : override ? 'Editar' : 'Definir Pendiente'}
                        </Button>
                      </div>

                      {isEditing && (
                        <div className="mt-2 pt-2 border-t border-amber-100 space-y-3">
                          {/* Roof Type Selector */}
                          <div>
                            <label className="text-[10px] font-medium text-gray-600 block mb-1">Tipo de Techo</label>
                            <div className="grid grid-cols-4 gap-1">
                              {[
                                { value: 'flat' as const, label: 'Plano', icon: '━' },
                                { value: 'single_slope' as const, label: 'Una Agua', icon: '╱' },
                                { value: 'gable' as const, label: 'Dos Aguas', icon: '⋀' },
                                { value: 'hip' as const, label: 'Cuatro Aguas', icon: '◇' },
                              ].map(({ value, label, icon }) => (
                                <button
                                  key={value}
                                  className={`text-[10px] py-1.5 px-1 rounded border transition-colors ${
                                    (override?.roofType || 'flat') === value
                                      ? 'bg-amber-200 border-amber-400 text-amber-900 font-semibold'
                                      : 'bg-white border-gray-200 text-gray-600 hover:bg-amber-50'
                                  }`}
                                  onClick={() => {
                                    const current = override || { tilt: 15, azimuth: 0, roofType: 'flat' as const };
                                    setRoofOverrides(prev => ({
                                      ...prev,
                                      [idx]: { ...current, roofType: value, tilt: value === 'flat' ? 0 : current.tilt || 15 }
                                    }));
                                  }}
                                >
                                  <div className="text-lg leading-none">{icon}</div>
                                  <div className="mt-0.5">{label}</div>
                                </button>
                              ))}
                            </div>
                          </div>

                          {/* Tilt Slider - only for non-flat */}
                          {(override?.roofType || 'flat') !== 'flat' && (
                            <div>
                              <label className="text-[10px] font-medium text-gray-600 flex items-center justify-between">
                                <span>Inclinación de la Pendiente</span>
                                <span className="font-mono text-amber-700">{override?.tilt || 15}°</span>
                              </label>
                              <input
                                type="range"
                                min="1"
                                max="45"
                                step="1"
                                value={override?.tilt || 15}
                                onChange={(e) => {
                                  const tilt = parseInt(e.target.value);
                                  const current = override || { tilt: 15, azimuth: 0, roofType: 'single_slope' as const };
                                  setRoofOverrides(prev => ({ ...prev, [idx]: { ...current, tilt } }));
                                }}
                                className="w-full h-1.5 bg-amber-200 rounded-lg appearance-none cursor-pointer accent-amber-600"
                              />
                              <div className="flex justify-between text-[9px] text-gray-400 mt-0.5">
                                <span>1° (casi plano)</span>
                                <span>15° (típico)</span>
                                <span>30° (pronunciado)</span>
                                <span>45°</span>
                              </div>
                            </div>
                          )}

                          {/* Azimuth Selector - only for non-flat */}
                          {(override?.roofType || 'flat') !== 'flat' && (
                            <div>
                              <label className="text-[10px] font-medium text-gray-600 flex items-center justify-between">
                                <span>Orientación de la Pendiente (hacia dónde baja el agua)</span>
                                <span className="font-mono text-amber-700">{override?.azimuth || 0}°</span>
                              </label>
                              <input
                                type="range"
                                min="-180"
                                max="180"
                                step="5"
                                value={override?.azimuth || 0}
                                onChange={(e) => {
                                  const azimuth = parseInt(e.target.value);
                                  const current = override || { tilt: 15, azimuth: 0, roofType: 'single_slope' as const };
                                  setRoofOverrides(prev => ({ ...prev, [idx]: { ...current, azimuth } }));
                                }}
                                className="w-full h-1.5 bg-amber-200 rounded-lg appearance-none cursor-pointer accent-amber-600"
                              />
                              <div className="flex justify-between text-[9px] text-gray-400 mt-0.5">
                                <span>-180° (N)</span>
                                <span>-90° (E)</span>
                                <span>0° (S)</span>
                                <span>90° (O)</span>
                                <span>180° (N)</span>
                              </div>
                            </div>
                          )}

                          {/* Preview of what will be generated */}
                          {override && override.roofType !== 'flat' && (
                            <div className="bg-amber-50 border border-amber-100 rounded p-2">
                              <p className="text-[10px] text-amber-800 font-medium mb-1">Superficies generadas para el cruce:</p>
                              <ul className="text-[10px] text-amber-700 space-y-0.5">
                                {override.roofType === 'single_slope' && (
                                  <li>• {facade.name}: inclinación {override.tilt}°, orientación {override.azimuth}°</li>
                                )}
                                {override.roofType === 'gable' && (
                                  <>
                                    <li>• {facade.name} (Agua 1): inclinación {override.tilt}°, orientación {override.azimuth}°</li>
                                    <li>• {facade.name} (Agua 2): inclinación {override.tilt}°, orientación {((override.azimuth + 180) % 360 - (override.azimuth + 180 >= 180 ? 360 : 0)).toFixed(0)}°</li>
                                  </>
                                )}
                                {override.roofType === 'hip' && (
                                  <>
                                    <li>• {facade.name} (Agua N): inclinación {override.tilt}°, orientación {override.azimuth}°</li>
                                    <li>• {facade.name} (Agua S): inclinación {override.tilt}°, orientación {((override.azimuth + 180) % 360 - (override.azimuth + 180 >= 180 ? 360 : 0)).toFixed(0)}°</li>
                                    <li>• {facade.name} (Agua E): inclinación {override.tilt}°, orientación {((override.azimuth + 90) % 360 - (override.azimuth + 90 >= 180 ? 360 : 0)).toFixed(0)}°</li>
                                    <li>• {facade.name} (Agua O): inclinación {override.tilt}°, orientación {((override.azimuth - 90 + 360) % 360 - (override.azimuth - 90 + 360 >= 180 ? 360 : 0)).toFixed(0)}°</li>
                                  </>
                                )}
                              </ul>
                            </div>
                          )}

                          {/* Reset button */}
                          {override && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-[10px] h-5 px-2 text-amber-700 hover:text-amber-900"
                              onClick={() => {
                                setRoofOverrides(prev => {
                                  const next = { ...prev };
                                  delete next[idx];
                                  return next;
                                });
                              }}
                            >
                              <RotateCcw size={10} className="mr-1" />
                              Restablecer (usar valor detectado: {facade.tilt.toFixed(1)}°)
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 3D Viewer */}
          {model.detectedFacades.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h5 className="text-xs font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-1">
                  <Box size={12} className="text-violet-600" />
                  Vista 3D del Modelo
                </h5>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-[10px] h-6 px-2 border-violet-300"
                  onClick={() => setShow3DViewer(!show3DViewer)}
                >
                  {show3DViewer ? 'Ocultar' : 'Mostrar'} Vista 3D
                </Button>
              </div>
              {show3DViewer && (
                <Suspense fallback={
                  <div className="h-[350px] rounded-xl border border-violet-200 bg-gradient-to-b from-sky-50 to-white flex items-center justify-center">
                    <div className="text-center">
                      <div className="animate-spin w-6 h-6 border-2 border-violet-400 border-t-transparent rounded-full mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Cargando visor 3D...</p>
                    </div>
                  </div>
                }>
                  <ModelViewer3D
                    model={model}
                    obstacleVertices3D={existingObstacleVertices3D}
                    selectedFacadeIdx={selectedFacadeIdx}
                    onFacadeSelect={(idx) => setSelectedFacadeIdx(idx)}
                    northOffset={config.northOffset}
                    height={350}
                  />
                </Suspense>
              )}
            </div>
          )}

          {/* Obstacle recalculation info */}
          {existingObstacleVertices3D && existingObstacleVertices3D.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <RotateCcw size={14} className="text-blue-600" />
                <p className="text-xs text-blue-800">
                  <strong>{existingObstacleVertices3D.length} obstáculo(s)</strong> del entorno serán recalculados
                  desde la perspectiva del modelo importado.
                  {model.recalculatedObstacles.length > 0 && (
                    <> → <strong>{model.recalculatedObstacles.length}</strong> obstáculo(s) visibles desde el punto de evaluación.</>
                  )}
                </p>
              </div>
            </div>
          )}

          {!existingObstacleVertices3D && existingObstacles.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-xs text-amber-800">
                <strong>Nota:</strong> Los obstáculos actuales fueron dibujados manualmente (sin datos 3D).
                Se usarán tal cual sin recalcular la perspectiva. Para un ajuste automático,
                importa los obstáculos desde un archivo OBJ o JSON de Site Designer.
              </p>
            </div>
          )}

          {/* No facades detected warning */}
          {model.detectedFacades.length === 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
              <p className="text-xs text-orange-800">
                <strong>No se detectaron superficies evaluables (fachadas ni techos).</strong> Prueba:
              </p>
              <ul className="text-xs text-orange-700 mt-1 ml-4 list-disc">
                <li>Cambiar el eje vertical en Configuración Avanzada (Auto/Z-up/Y-up)</li>
                <li>Ajustar la escala si las unidades no son metros</li>
                <li>Aplicar una rotación horizontal (90°/180°/270°)</li>
                <li>Verificar que el modelo tiene caras (no solo aristas)</li>
              </ul>
            </div>
          )}

          {/* Advanced settings */}
          <div>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900 transition-colors"
            >
              {showAdvanced ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              Configuración avanzada
            </button>

            {showAdvanced && (
              <div className="mt-2 space-y-3 bg-gray-50 rounded-lg p-3">
                {/* Axis Orientation Section */}
                <div className="space-y-2">
                  <h6 className="text-[10px] font-semibold text-gray-600 uppercase tracking-wide flex items-center gap-1">
                    <Compass size={10} className="text-violet-500" />
                    Eje Vertical (Arriba)
                  </h6>
                  <div className="grid grid-cols-4 gap-1.5">
                    {([
                      { value: 'auto' as UpAxis, label: 'Auto', desc: 'Detectar' },
                      { value: 'Z' as UpAxis, label: 'Z-up', desc: 'SketchUp' },
                      { value: 'Y' as UpAxis, label: 'Y-up', desc: 'Blender/glTF' },
                      { value: 'X' as UpAxis, label: 'X-up', desc: 'Raro' },
                    ]).map(({ value, label, desc }) => (
                      <button
                        key={value}
                        className={`text-[10px] py-1.5 px-2 rounded border transition-colors text-center ${
                          config.upAxis === value
                            ? 'bg-violet-200 border-violet-400 text-violet-900 font-semibold'
                            : 'bg-white border-gray-200 text-gray-600 hover:bg-violet-50'
                        }`}
                        onClick={() => handleUpAxisChange(value)}
                        disabled={isProcessing}
                      >
                        <div className="font-mono font-bold text-xs">{label}</div>
                        <div className="text-[9px] text-gray-500 mt-0.5">{desc}</div>
                      </button>
                    ))}
                  </div>
                  {detectedAxisInfo && config.upAxis === 'auto' && (
                    <p className="text-[10px] text-violet-700">
                      Auto-detectado: <strong>{detectedAxisInfo.axis}-up</strong> (confianza {confidenceLabel(detectedAxisInfo.confidence).text.toLowerCase()})
                    </p>
                  )}
                </div>

                {/* Horizontal Rotation Section */}
                <div className="space-y-2">
                  <h6 className="text-[10px] font-semibold text-gray-600 uppercase tracking-wide flex items-center gap-1">
                    <RefreshCw size={10} className="text-violet-500" />
                    Rotación Horizontal
                  </h6>
                  <div className="grid grid-cols-4 gap-1.5">
                    {[0, 90, 180, 270].map((deg) => (
                      <button
                        key={deg}
                        className={`text-[10px] py-1.5 px-2 rounded border transition-colors text-center ${
                          config.rotationDeg === deg
                            ? 'bg-violet-200 border-violet-400 text-violet-900 font-semibold'
                            : 'bg-white border-gray-200 text-gray-600 hover:bg-violet-50'
                        }`}
                        onClick={() => handleRotationChange(deg)}
                        disabled={isProcessing}
                      >
                        <div className="font-mono font-bold text-xs">{deg}°</div>
                        <div className="text-[9px] text-gray-500 mt-0.5">
                          {deg === 0 ? 'Sin rotar' : deg === 90 ? 'Girar 90°' : deg === 180 ? 'Girar 180°' : 'Girar 270°'}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Scale, North Offset, and other settings */}
                <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-gray-200">
                  <label className="flex items-center gap-2 text-xs">
                    <span className="text-gray-700">Escala:</span>
                    <select
                      value={config.scaleFactor}
                      onChange={(e) => {
                        const newConfig = { ...config, scaleFactor: parseFloat(e.target.value) };
                        setConfig(newConfig);
                        if (rawParseResult) reconvertModel(newConfig);
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
                      value={config.northOffset}
                      onChange={(e) => {
                        const newConfig = { ...config, northOffset: parseFloat(e.target.value) || 0 };
                        setConfig(newConfig);
                      }}
                      className="w-16 px-2 py-1 border border-gray-300 rounded text-xs font-mono bg-white"
                      step="1"
                    />
                    <span className="text-gray-500">°</span>
                  </label>
                  <label className="flex items-center gap-2 text-xs">
                    <span className="text-gray-700">Altura eval.:</span>
                    <input
                      type="number"
                      value={config.evaluationHeight}
                      onChange={(e) => {
                        const newConfig = { ...config, evaluationHeight: parseFloat(e.target.value) || 1.5 };
                        setConfig(newConfig);
                      }}
                      className="w-14 px-2 py-1 border border-gray-300 rounded text-xs font-mono bg-white"
                      step="0.5"
                      min="0"
                    />
                    <span className="text-gray-500">m</span>
                  </label>
                  <label className="flex items-center gap-2 text-xs">
                    <span className="text-gray-700">Offset fachada:</span>
                    <input
                      type="number"
                      value={config.evaluationOffset}
                      onChange={(e) => {
                        const newConfig = { ...config, evaluationOffset: parseFloat(e.target.value) || 0.5 };
                        setConfig(newConfig);
                      }}
                      className="w-14 px-2 py-1 border border-gray-300 rounded text-xs font-mono bg-white"
                      step="0.1"
                      min="0"
                    />
                    <span className="text-gray-500">m</span>
                  </label>
                </div>

                {/* Re-apply button for North Offset / Height / Offset changes */}
                {rawParseResult && (
                  <div className="flex justify-end pt-1">
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-[10px] h-6 px-3 border-violet-300 text-violet-700 hover:bg-violet-50"
                      onClick={() => reconvertModel()}
                      disabled={isProcessing}
                    >
                      <RefreshCw size={10} className="mr-1" />
                      Aplicar cambios
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
