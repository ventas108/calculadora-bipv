import { useState, useMemo, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Zap, AlertCircle, CheckCircle2, Settings2 } from 'lucide-react';
import { EPWData } from '@/lib/epwParser';
import { ObstaclePolygon } from './SunPathDiagram';
import {
  CrossingConfig,
  CrossingResult,
  CriticalDay,
  FacadeDefinition,
  CRITICAL_DAYS,
  MONTHLY_CRITICAL_DAYS,
  DEFAULT_CROSSING_CONFIG,
  executeCrossing,
  crossingResultsToAnalysisPoints,
} from '@/lib/shadingMaskCrossing';

interface CrossingModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  weatherData: EPWData | null;
  obstacles: ObstaclePolygon[];
  onResultsGenerated: (points: ReturnType<typeof crossingResultsToAnalysisPoints>) => void;
  /** Callback con los resultados crudos del cruce y las fachadas usadas */
  onRawCrossingResults?: (results: CrossingResult[], facades: FacadeDefinition[]) => void;
  /** Fachadas detectadas automáticamente desde un modelo 3D importado */
  modelFacades?: FacadeDefinition[];
}

type DayPreset = 'solsticios_equinoccios' | 'solsticios' | 'mensual' | 'custom';

export default function CrossingModal({
  open,
  onOpenChange,
  weatherData,
  obstacles,
  onResultsGenerated,
  onRawCrossingResults,
  modelFacades,
}: CrossingModalProps) {
  // ─── Config State ────────────────────────────────────────────────────
  const [dayPreset, setDayPreset] = useState<DayPreset>('solsticios_equinoccios');
  const [selectedDays, setSelectedDays] = useState<CriticalDay[]>(CRITICAL_DAYS);
  const [hourStart, setHourStart] = useState(6);
  const [hourEnd, setHourEnd] = useState(18);
  const [hourStep, setHourStep] = useState(1);
  const [albedo, setAlbedo] = useState(0.2);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Facades - use model facades if available, otherwise default cardinal directions
  const [facades, setFacades] = useState<FacadeDefinition[]>(
    modelFacades && modelFacades.length > 0 ? modelFacades : DEFAULT_CROSSING_CONFIG.facades
  );
  const [facadeEnabled, setFacadeEnabled] = useState<boolean[]>(
    modelFacades && modelFacades.length > 0
      ? modelFacades.map(() => true)
      : [true, true, true, true]
  );
  const [usingModelFacades, setUsingModelFacades] = useState(!!modelFacades && modelFacades.length > 0);

  // Sync facades when modelFacades prop changes
  useEffect(() => {
    if (modelFacades && modelFacades.length > 0) {
      setFacades(modelFacades);
      setFacadeEnabled(modelFacades.map(() => true));
      setUsingModelFacades(true);
    }
  }, [modelFacades]);

  // Results
  const [results, setResults] = useState<CrossingResult[] | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // ─── Derived ─────────────────────────────────────────────────────────
  const canExecute = !!weatherData;
  const hasObstacles = obstacles.length > 0;

  const activeFacades = useMemo(
    () => facades.filter((_, i) => facadeEnabled[i]),
    [facades, facadeEnabled]
  );

  const estimatedPoints = useMemo(() => {
    const hoursCount = Math.floor((hourEnd - hourStart) / hourStep) + 1;
    // Rough estimate: ~60% of hours will have sun above horizon for each facade
    return selectedDays.length * hoursCount * activeFacades.length * 0.6;
  }, [selectedDays, hourStart, hourEnd, hourStep, activeFacades]);

  // ─── Handlers ────────────────────────────────────────────────────────
  const handlePresetChange = (preset: DayPreset) => {
    setDayPreset(preset);
    switch (preset) {
      case 'solsticios_equinoccios':
        setSelectedDays(CRITICAL_DAYS);
        break;
      case 'solsticios':
        setSelectedDays(CRITICAL_DAYS.filter(d => d.name.includes('Solsticio')));
        break;
      case 'mensual':
        setSelectedDays(MONTHLY_CRITICAL_DAYS);
        break;
      case 'custom':
        // Keep current selection
        break;
    }
  };

  const toggleDay = (day: CriticalDay) => {
    setSelectedDays(prev => {
      const exists = prev.find(d => d.month === day.month && d.day === day.day);
      if (exists) return prev.filter(d => !(d.month === day.month && d.day === day.day));
      return [...prev, day];
    });
    setDayPreset('custom');
  };

  const executeCrossingHandler = () => {
    if (!weatherData) return;

    setIsProcessing(true);
    setResults(null);

    // Use setTimeout to allow UI to update
    setTimeout(() => {
      try {
        const config: CrossingConfig = {
          facades: activeFacades,
          criticalDays: selectedDays,
          hourRange: [hourStart, hourEnd],
          hourStep,
          albedo,
          elevation: weatherData.location.elevation,
        };

        // Validate that EPW has sufficient data
        const epwRecordCount = weatherData.weatherData?.length || 0;
        if (epwRecordCount === 0) {
          console.error('EPW sin registros de datos meteorológicos');
          setResults([]);
          setIsProcessing(false);
          return;
        }

        const crossingResults = executeCrossing(weatherData, obstacles, config);
        
        // If 0 results, log diagnostic info
        if (crossingResults.length === 0) {
          console.warn('[Cruce EPW] 0 resultados generados. Diagnóstico:', {
            epwRecords: epwRecordCount,
            facades: activeFacades.map(f => ({ name: f.name, az: f.azimuthNormal, tilt: f.tilt })),
            days: selectedDays.map(d => `${d.month}/${d.day}`),
            hourRange: [hourStart, hourEnd],
            location: weatherData.location,
          });
        }
        
        setResults(crossingResults);
      } catch (error) {
        console.error('Error en cruce:', error);
      } finally {
        setIsProcessing(false);
      }
    }, 50);
  };

  const applyResults = () => {
    if (!results) return;
    const analysisPoints = crossingResultsToAnalysisPoints(results);
    onResultsGenerated(analysisPoints);
    // Pasar resultados crudos y fachadas al padre para exportación PDF
    if (onRawCrossingResults) {
      onRawCrossingResults(results, facades);
    }
    onOpenChange(false);
    setResults(null);
  };

  // ─── Render ──────────────────────────────────────────────────────────
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap size={20} className="text-amber-500" />
            Cruzar Máscara de Sombreado + EPW
          </DialogTitle>
          <DialogDescription>
            Genera factores de sombreado geométricos y climáticos cruzando las máscaras de
            obstáculos importadas con los datos climáticos del archivo EPW.
          </DialogDescription>
        </DialogHeader>

        {/* Status indicators */}
        <div className="space-y-2 py-2">
          <div className={`flex items-center gap-2 text-sm ${
            !weatherData ? 'text-red-600' :
            (weatherData.weatherData?.length || 0) === 0 ? 'text-amber-600' :
            (weatherData.weatherData?.length || 0) < 200 ? 'text-blue-600' :
            'text-green-700'
          }`}>
            {!weatherData ? <AlertCircle size={14} /> :
             (weatherData.weatherData?.length || 0) === 0 ? <AlertCircle size={14} /> :
             <CheckCircle2 size={14} />}
            <span>
              {!weatherData
                ? 'No hay archivo EPW cargado — requerido para FS climático'
                : (weatherData.weatherData?.length || 0) === 0
                  ? `Ubicación: ${weatherData.location.city} — Sin datos horarios (reimporta Sun Path 3D para generar datos sintéticos)`
                  : (weatherData.weatherData?.length || 0) < 200
                    ? `EPW sintético (cielo claro): ${weatherData.location.city} — ${weatherData.weatherData.length} registros para días críticos`
                    : `EPW real: ${weatherData.location.city} (${weatherData.location.latitude.toFixed(2)}°, ${weatherData.location.longitude.toFixed(2)}°, elev. ${weatherData.location.elevation}m, ${weatherData.weatherData.length} registros)`
              }
            </span>
          </div>
          <div className={`flex items-center gap-2 text-sm ${hasObstacles ? 'text-green-700' : 'text-amber-600'}`}>
            {hasObstacles ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
            <span>
              {hasObstacles
                ? `${obstacles.length} obstáculo(s) cargados — se usarán para FS geométrico`
                : 'Sin obstáculos — FS geométrico será 0 (solo se calculará FS climático)'}
            </span>
          </div>
        </div>

        {/* Day selection */}
        <div className="space-y-3 border-t pt-3">
          <h4 className="text-sm font-semibold text-gray-800">Días Críticos a Evaluar</h4>
          <Select value={dayPreset} onValueChange={(v) => handlePresetChange(v as DayPreset)}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Seleccionar preset" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="solsticios_equinoccios">Solsticios + Equinoccios (4 días)</SelectItem>
              <SelectItem value="solsticios">Solo Solsticios (2 días)</SelectItem>
              <SelectItem value="mensual">Día 21 de cada mes (12 días)</SelectItem>
              <SelectItem value="custom">Personalizado</SelectItem>
            </SelectContent>
          </Select>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
            {CRITICAL_DAYS.map(day => (
              <label
                key={`${day.month}-${day.day}`}
                className="flex items-center gap-1.5 text-xs cursor-pointer hover:bg-gray-50 rounded px-1.5 py-1"
              >
                <Checkbox
                  checked={!!selectedDays.find(d => d.month === day.month && d.day === day.day)}
                  onCheckedChange={() => toggleDay(day)}
                />
                <span>{day.name}</span>
              </label>
            ))}
          </div>

          {dayPreset === 'mensual' && (
            <p className="text-xs text-gray-500">
              Se evaluarán los 12 meses (día 21 de cada mes): {selectedDays.length} días seleccionados
            </p>
          )}
        </div>

        {/* Hour range */}
        <div className="space-y-3 border-t pt-3">
          <h4 className="text-sm font-semibold text-gray-800">Rango Horario</h4>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-gray-600 block mb-1">Hora inicio</label>
              <Input
                type="number"
                min={0}
                max={23}
                value={hourStart}
                onChange={(e) => setHourStart(Number(e.target.value))}
                className="h-8 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600 block mb-1">Hora fin</label>
              <Input
                type="number"
                min={1}
                max={23}
                value={hourEnd}
                onChange={(e) => setHourEnd(Number(e.target.value))}
                className="h-8 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600 block mb-1">Paso (h)</label>
              <Select value={String(hourStep)} onValueChange={(v) => setHourStep(Number(v))}>
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="0.5">0.5 h (30 min)</SelectItem>
                  <SelectItem value="1">1 h</SelectItem>
                  <SelectItem value="2">2 h</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Facades */}
        <div className="space-y-3 border-t pt-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-gray-800">Fachadas a Evaluar</h4>
            {usingModelFacades && (
              <span className="text-[10px] bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full font-medium">
                Detectadas del modelo 3D
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2">
            {facades.map((facade, i) => (
              <label
                key={facade.name}
                className="flex items-center gap-2 text-xs cursor-pointer hover:bg-gray-50 rounded px-2 py-1.5 border border-gray-200"
              >
                <Checkbox
                  checked={facadeEnabled[i]}
                  onCheckedChange={(checked) => {
                    setFacadeEnabled(prev => {
                      const next = [...prev];
                      next[i] = !!checked;
                      return next;
                    });
                  }}
                />
                <div>
                  <span className="font-medium">{facade.name}</span>
                  <span className="text-gray-500 ml-1">
                    (Az: {facade.azimuthNormal}°, Tilt: {facade.tilt}°)
                  </span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Advanced settings */}
        <div className="border-t pt-3">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-1.5 text-xs text-gray-600 hover:text-gray-900"
          >
            <Settings2 size={12} />
            {showAdvanced ? 'Ocultar' : 'Mostrar'} configuración avanzada
          </button>
          {showAdvanced && (
            <div className="grid grid-cols-2 gap-3 mt-2">
              <div>
                <label className="text-xs text-gray-600 block mb-1">Albedo del suelo</label>
                <Input
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={albedo}
                  onChange={(e) => setAlbedo(Number(e.target.value))}
                  className="h-8 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 block mb-1">Elevación (m)</label>
                <Input
                  type="number"
                  value={weatherData?.location.elevation || 0}
                  disabled
                  className="h-8 text-sm bg-gray-100"
                />
              </div>
            </div>
          )}
        </div>

        {/* Estimation */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-800">
          Se generarán aproximadamente <strong>{Math.round(estimatedPoints)}</strong> puntos de análisis
          ({selectedDays.length} días × {Math.floor((hourEnd - hourStart) / hourStep) + 1} horas × {activeFacades.length} fachadas,
          filtrado por sol sobre horizonte y fachada expuesta).
        </div>

        {/* Results preview */}
        {results && results.length > 0 && (
          <div className="border-t pt-3 space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-green-600" />
              <span className="text-sm font-semibold text-green-800">
                Cruce completado: {results.length} puntos generados
              </span>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-xs space-y-1">
              <p><strong>Resumen:</strong></p>
              <p>• Eventos evaluados: {Array.from(new Set(results.map(r => r.evento))).join(', ')}</p>
              <p>• Fachadas: {Array.from(new Set(results.map(r => r.facade))).join(', ')}</p>
              <p>• FS Geométrico promedio: {(results.reduce((s, r) => s + r.fsGeometrico, 0) / results.length).toFixed(3)}</p>
              <p>• FS Climático promedio: {(results.reduce((s, r) => s + r.fsClimatico, 0) / results.length).toFixed(3)}</p>
              <p>• FS Combinado promedio: {(results.reduce((s, r) => s + r.fs, 0) / results.length).toFixed(3)}</p>
              <p>• Puntos con sombra geométrica: {results.filter(r => r.fsGeometrico > 0).length}</p>
            </div>
          </div>
        )}

        {/* Zero results diagnostic */}
        {results && results.length === 0 && (
          <div className="border-t pt-3 space-y-2">
            <div className="flex items-center gap-2">
              <AlertCircle size={16} className="text-amber-600" />
              <span className="text-sm font-semibold text-amber-800">
                Cruce completado: 0 puntos generados
              </span>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs space-y-2">
              <p><strong>Posibles causas:</strong></p>
              <p>• El archivo EPW no contiene datos para los días críticos seleccionados ({weatherData?.weatherData?.length || 0} registros totales)</p>
              {(weatherData?.weatherData?.length || 0) === 0 && (
                <p className="text-red-700 font-medium">⚠ La ubicación fue importada desde Sun Path 3D pero sin datos horarios. Confirma la importación de Sun Path 3D nuevamente — ahora genera datos sintéticos de cielo claro automáticamente.</p>
              )}
              <p>• Las fachadas seleccionadas no reciben sol directo en el rango horario configurado</p>
              <p>• Verifique que el EPW corresponde a la ubicación del proyecto</p>
              <p className="mt-1 text-amber-700 font-medium">
                Sugerencia: Intente ampliar el rango horario (6–18h), seleccionar más días críticos,
                o verificar que el archivo EPW se cargó correctamente.
              </p>
            </div>
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-0">
          {results ? (
            <>
              <Button variant="outline" onClick={() => setResults(null)}>
                Recalcular
              </Button>
              <Button onClick={applyResults} className="bg-green-600 hover:bg-green-700">
                Aplicar a Tabla de Análisis
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancelar
              </Button>
              <Button
                onClick={executeCrossingHandler}
                disabled={!canExecute || isProcessing || selectedDays.length === 0 || activeFacades.length === 0}
                className="bg-amber-600 hover:bg-amber-700"
              >
                {isProcessing ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin">⏳</span> Procesando...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Zap size={14} />
                    Ejecutar Cruce
                  </span>
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
