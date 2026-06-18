import { useMemo, useState, useCallback, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { EPWData } from '@/lib/epwParser';
import { ProspectorToSimulatorData } from '@/components/SolarProspector';
import type { PVWattsToSimulatorData } from '@/components/PVWattsSatellite';
import { calculateAnnualProduction, calculateFinancials, PanelSpecifications, SystemLosses, calculatePR_T_Hourly, HourlyPR_T_Result, HourlyRecord } from '@/lib/energyProduction';
import { DEFAULT_PANEL_TECHNOLOGIES, PanelTechnology, RegionalCompatibility } from '@/lib/panelTechnologies';
import { BIPVToEnergyData } from '@/lib/bipvToEnergyBridge';
import { useCustomPanels, CustomPanelLocal } from '@/hooks/useCustomPanels';
import { detectColombianRegion, ColombianRegionKey } from '@/lib/colombianRegions';
import { INSTALLATION_CONFIGS, InstallationConfig, getDefaultInstallationConfig, estimateProductionFactor } from '@/lib/installationConfigs';
import PanelTechSelector from '@/components/PanelTechSelector';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Slider } from '@/components/ui/slider';
import { Zap, DollarSign, TrendingUp, Shield, Sun, Thermometer, LayoutGrid, Maximize2, RotateCcw, Plus, Trash2, ChevronDown, ChevronUp, Calculator, Building2, Home, Warehouse, PanelTop, TreePine, Car, Info, MapPin, Pencil, RotateCw, AlertTriangle, Target, Compass, Save, Clock, Globe, Satellite, Microscope } from 'lucide-react';
import { OptimizerResult } from '@/components/OrientationOptimizer';
import { useFieldMeasurementHistory, FieldMeasurementRecord } from '@/hooks/useFieldMeasurementHistory';
import FieldMeasurementHistory from '@/components/FieldMeasurementHistory';
import { calculateCellTemp as mulcueCellTemp, calculateExpectedPower, calculateMulcuePR, calculateTempLossFactor, MULCUE_T_REF, G_STC, G_NOCT_REF } from '@shared/mulcueLlanos';
import { diagnosePerformance, getAlertBadge, type PerformanceAlert as PerformanceAlertType } from '@shared/performanceDiagnostic';
import PerformanceAlertPanel from '@/components/PerformanceAlertPanel';
import CrossValidationTable from '@/components/CrossValidationTable';
import BIPVDeviationAlert from '@/components/BIPVDeviationAlert';
import { buildComparisonData } from '@/lib/crossValidation';
import { Table, TableBody, TableCell, TableFooter, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import MultiFacadeComparison from '@/components/MultiFacadeComparison';

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

export interface POAConfig {
  tilt: number;
  azimuth: number;
  albedo: number;
  usePerez: boolean;
  source: 'epw_hourly' | 'prospector' | 'field' | 'optimizer';
}

interface EnergyProductionSimulatorProps {
  weatherData: EPWData;
  poaData: Array<{
    month: string;
    directPOA: number;
    diffusePOA: number;
    reflectedPOA: number;
    totalPOA: number;
    avgTemp: number;
    avgWindSpeed: number;
  }>;
  shadingFactors?: number[];
  prospectorData?: ProspectorToSimulatorData | null;
  onDiscardProspector?: () => void;
  optimizerResult?: OptimizerResult | null;
  onDiscardOptimizer?: () => void;
  pvgisData?: import('@/components/PVGISAnalyzer').PVGISToSimulatorData | null;
  onDiscardPvgis?: () => void;
  pvwattsData?: PVWattsToSimulatorData | null;
  onDiscardPvwatts?: () => void;
  onInstallConfigChange?: (config: { tiltRange?: [number, number]; azimuthLocked?: boolean; name?: string }) => void;
  poaConfig?: POAConfig;
  onPoaConfigChange?: (config: Partial<POAConfig>) => void;
  facadeAnalysis3D?: import('@/lib/facadeShadingAnalysis').FacadeFullAnalysis | null;
  modelFacades?: import('@/lib/buildingModelImporter').DetectedFacade[];
  modelObstacles3D?: import('@/lib/buildingModelImporter').Vertex3D[][];
  modelNorthOffset?: number;
  onFacadeSelectFromSimulator?: (idx: number) => void;
  onFinancialParamsChange?: (params: { electricityRate: number; systemCost: number; costPerWp: number }) => void;
  onEnergyDataChange?: (data: {
    panelPower: number;
    panelEfficiency: number;
    panelArea: number;
    panelQuantity: number;
    tilt: number;
    azimuth: number;
    annualProduction: number;
    capacityFactor: number;
    performanceRatio: number;
    systemLosses: number;
    paybackPeriod: number;
    roi10Year: number;
    roi25Year: number;
  }) => void;
  /** Datos del simulador BIPV IAM+Soiling */
  bipvData?: BIPVToEnergyData | null;
  /** Callback para descartar datos BIPV */
  onDiscardBipv?: () => void;
  /** Callback para volver al módulo IAM+Soiling BIPV */
  onReturnToBIPV?: () => void;
  /** Callback para re-simular BIPV con datos reales cuando se detecta distribución plana */
  onResimultateBIPV?: () => void;
}

export default function EnergyProductionSimulator({ weatherData, poaData, shadingFactors = Array(12).fill(1.0), prospectorData, onDiscardProspector, optimizerResult, onDiscardOptimizer, pvgisData, onDiscardPvgis, pvwattsData, onDiscardPvwatts, onInstallConfigChange, poaConfig, onPoaConfigChange, facadeAnalysis3D, modelFacades = [], modelObstacles3D, modelNorthOffset = 0, onFacadeSelectFromSimulator, onFinancialParamsChange, onEnergyDataChange, bipvData, onDiscardBipv, onReturnToBIPV, onResimultateBIPV }: EnergyProductionSimulatorProps) {
  // Panel technology selection
  const [selectedTech, setSelectedTech] = useState<PanelTechnology>(DEFAULT_PANEL_TECHNOLOGIES[0]);
  const [yearsFromInstall, setYearsFromInstall] = useState(0);

  // Toggle for 3D model vs manual shading (default to false/manual on mount)
  const [use3DShading, setUse3DShading] = useState(false);
  const lastFacadeIdxRef = useRef<number | null>(null);

  useEffect(() => {
    if (facadeAnalysis3D) {
      if (lastFacadeIdxRef.current !== null && facadeAnalysis3D.facadeIdx !== lastFacadeIdxRef.current) {
        setUse3DShading(true);
      }
      lastFacadeIdxRef.current = facadeAnalysis3D.facadeIdx;
    } else {
      setUse3DShading(false);
      lastFacadeIdxRef.current = null;
    }
  }, [facadeAnalysis3D]);

  const activeShadingFactors = useMemo(() => {
    if (use3DShading && facadeAnalysis3D) {
      return facadeAnalysis3D.monthlyShadingFactors;
    }
    return shadingFactors;
  }, [use3DShading, facadeAnalysis3D, shadingFactors]);

  // Auto-detección de región climática colombiana
  const detectedRegion = useMemo(() => {
    return detectColombianRegion(weatherData.location.latitude, weatherData.location.longitude);
  }, [weatherData.location.latitude, weatherData.location.longitude]);
  const [regionOverride, setRegionOverride] = useState<ColombianRegionKey | null>(null);
  const activeRegion: keyof Omit<RegionalCompatibility, 'notes'> = regionOverride ?? detectedRegion.region;

  // Panel specifications
  const [panelQuantity, setPanelQuantity] = useState(10);
  const [useCustomSpecs, setUseCustomSpecs] = useState(false);

  // Custom overrides
  const [customPower, setCustomPower] = useState(selectedTech.pmax);
  const [customEfficiency, setCustomEfficiency] = useState(selectedTech.efficiencySTC);
  const [customArea, setCustomArea] = useState((selectedTech.lengthMm * selectedTech.widthMm) / 1_000_000);
  const [customTempCoeff, setCustomTempCoeff] = useState(selectedTech.tempCoeffPmax / 100);
  const [customNoct, setCustomNoct] = useState(selectedTech.noct);

  // ===== AREA CALCULATOR STATE =====
  const [availableArea, setAvailableArea] = useState<number>(100); // m²
  const [panelOrientation, setPanelOrientation] = useState<'landscape' | 'portrait'>('landscape');
  const [spacingFactor, setSpacingFactor] = useState<number>(1.2); // 1.0 = sin separación, 1.5 = 50% extra
  const [areaCalcExpanded, setAreaCalcExpanded] = useState(false);
  const [autoSyncQuantity, setAutoSyncQuantity] = useState(!prospectorData); // Auto-sync quantity with area calc (disabled when prospector active)
  const [availableWidth, setAvailableWidth] = useState<number>(10); // m
  const [availableLength, setAvailableLength] = useState<number>(10); // m
  const [useRectangular, setUseRectangular] = useState(false);

  // Installation configuration
  const [selectedInstallation, setSelectedInstallation] = useState<InstallationConfig>(getDefaultInstallationConfig());
  const [installTilt, setInstallTilt] = useState(poaConfig?.tilt ?? getDefaultInstallationConfig().defaultTilt);
  const [installAzimuth, setInstallAzimuth] = useState(poaConfig?.azimuth ?? getDefaultInstallationConfig().defaultAzimuth);
  const [installConfigExpanded, setInstallConfigExpanded] = useState(true);

  // Sincronizar cambios de tilt/azimuth con el cálculo POA en Home.tsx
  useEffect(() => {
    if (onPoaConfigChange) {
      onPoaConfigChange({ tilt: installTilt, azimuth: installAzimuth });
    }
  }, [installTilt, installAzimuth]);

  const INSTALL_ICONS: Record<string, React.ReactNode> = {
    rooftop_tilted: <Home size={18} />,
    rooftop_flat: <Building2 size={18} />,
    facade_vertical: <Warehouse size={18} />,
    facade_inclined: <PanelTop size={18} />,
    pergola: <TreePine size={18} />,
    canopy: <Car size={18} />,
    bipv_imported: <Microscope size={18} />,
  };

  // Apply installation config
  const applyInstallationConfig = useCallback((config: InstallationConfig) => {
    setSelectedInstallation(config);
    setInstallTilt(config.defaultTilt);
    setInstallAzimuth(config.defaultAzimuth);
    // Apply losses
    setDcWiring(config.losses.dcWiring);
    setInverterEfficiency(config.losses.inverterEfficiency);
    setAcWiring(config.losses.acWiring);
    setTransformerLosses(config.losses.transformerLosses);
    setMismatchLosses(config.losses.mismatch);
    setSoilingLosses(config.losses.soiling);
    setAvailabilityLosses(config.losses.availabilityLosses);
    // Apply spacing
    setSpacingFactor(config.recommendedSpacing);
    // Apply structure and labor costs
    setCostItems(items => items.map(item => {
      if (item.id === 'structure') {
        return { ...item, unitCost: config.structureCostPerPanel };
      }
      if (item.id === 'labor') {
        return { ...item, unitCost: config.laborCostPerPanel };
      }
      return item;
    }));
    // Propagar restricciones de instalación al Optimizador via Home.tsx
    if (onInstallConfigChange) {
      onInstallConfigChange({
        tiltRange: config.tiltRange,
        azimuthLocked: config.azimuthLocked,
        name: config.name,
      });
    }
  }, [onInstallConfigChange]);

  // ===== PROSPECTOR DATA BRIDGE =====
  // === PVWATTS PRELOAD BRIDGE ===
  const [pvwattsApplied, setPvwattsApplied] = useState(false);
  useEffect(() => {
    if (pvwattsData && !pvwattsApplied) {
      // Pre-llenar inclinación y azimut del sistema PVWatts
      setInstallTilt(pvwattsData.tilt);
      setInstallAzimuth(pvwattsData.azimuth);
      // Pre-llenar área disponible si viene del PVWatts
      if (pvwattsData.availableArea && pvwattsData.availableArea > 0) {
        setAvailableArea(pvwattsData.availableArea);
        // Activar auto-sync para que calcule paneles automáticamente desde el área
        setAutoSyncQuantity(true);
        setAreaCalcExpanded(true);
      } else {
        // Sin área: estimar paneles desde capacidad del sistema
        const panelWp = useCustomSpecs ? customPower : selectedTech.pmax;
        const estimatedPanels = Math.max(1, Math.round((pvwattsData.systemCapacity * 1000) / panelWp));
        setPanelQuantity(estimatedPanels);
        setAutoSyncQuantity(false);
      }
      setPvwattsApplied(true);
    }
  }, [pvwattsData, pvwattsApplied]);

  // === PVGIS PRELOAD BRIDGE ===
  const [pvgisApplied, setPvgisApplied] = useState(false);
  useEffect(() => {
    if (pvgisData && !pvgisApplied) {
      // Pre-llenar inclinación y azimut del sistema PVGIS
      setInstallTilt(pvgisData.tilt);
      setInstallAzimuth(pvgisData.azimuth);
      // Pre-llenar área disponible si viene del PVGIS
      if (pvgisData.availableArea && pvgisData.availableArea > 0) {
        setAvailableArea(pvgisData.availableArea);
        setAutoSyncQuantity(true);
        setAreaCalcExpanded(true);
      } else {
        // Sin área: estimar paneles desde peakPowerKwp
        const panelWp = useCustomSpecs ? customPower : selectedTech.pmax;
        const estimatedPanels = Math.max(1, Math.round((pvgisData.peakPowerKwp * 1000) / panelWp));
        setPanelQuantity(estimatedPanels);
        setAutoSyncQuantity(false);
      }
      setPvgisApplied(true);
    }
  }, [pvgisData, pvgisApplied]);

  const [prospectorApplied, setProspectorApplied] = useState(false);
  useEffect(() => {
    if (prospectorData && !prospectorApplied) {
      // Pre-llenar panel seleccionado
      const panel = DEFAULT_PANEL_TECHNOLOGIES.find(p => p.id === prospectorData.panelId);
      if (panel) {
        setSelectedTech(panel);
        setCustomPower(panel.pmax);
        setCustomEfficiency(panel.efficiencySTC);
        setCustomArea((panel.lengthMm * panel.widthMm) / 1_000_000);
        setCustomTempCoeff(panel.tempCoeffPmax / 100);
        setCustomNoct(panel.noct);
      }
      // Si hay availableArea, activar auto-sync y pre-llenar área
      if (prospectorData.availableArea && prospectorData.availableArea > 0) {
        setAvailableArea(prospectorData.availableArea);
        setAutoSyncQuantity(true);
      } else {
        // Pre-llenar cantidad de módulos y desactivar auto-sync del área
        setPanelQuantity(prospectorData.moduleCount);
        setAutoSyncQuantity(false);
      }
      // Pre-llenar inclinación recomendada
      setInstallTilt(prospectorData.tiltRecommended);
      // Marcar como aplicado
      setProspectorApplied(true);
    }
  }, [prospectorData, prospectorApplied]);

  // === BIPV IAM+SOILING PRELOAD BRIDGE ===
  const [bipvApplied, setBipvApplied] = useState(false);
  const [isResimulatingBIPV, setIsResimulatingBIPV] = useState(false);
  const [isResyncingParams, setIsResyncingParams] = useState(false);
  // Panel baseline para comparación BIPV vs estándar (null = genérico 400W)
  const [baselinePanelId, setBaselinePanelId] = useState<string | null>(null);
  const [showPRDiagnostic, setShowPRDiagnostic] = useState(false);
  useEffect(() => {
    if (bipvData && !bipvApplied) {
      // 1. Normalizar azimut: IAM+Soiling usa convención solar (-180 a +180, 0=Sur)
      //    Simulador usa convención geográfica (0-360, 0=Norte, 180=Sur)
      //    Conversión: azimut_geo = (azimut_solar + 180) % 360
      const rawTilt = Math.abs(bipvData.tilt);
      let rawAzimuth = bipvData.azimuth;
      // Si el azimut viene en convención solar (-180..+180 con 0=Sur), convertir a 0-360 (0=Norte)
      if (rawAzimuth < 0 || rawAzimuth > 360) {
        rawAzimuth = ((rawAzimuth + 180) % 360 + 360) % 360;
      }

      // 2. Seleccionar tipo de instalación "BIPV (Importado)" — rangos libres 0-90° tilt, 0-360° azimut
      //    Esto garantiza compatibilidad con cualquier ángulo del modelo 3D
      const bestConfig = INSTALLATION_CONFIGS.find(c => c.id === 'bipv_imported') || getDefaultInstallationConfig();
      
      // Aplicar la configuración de instalación (pérdidas, costos, etc.)
      // PERO sin usar sus ángulos por defecto
      setSelectedInstallation(bestConfig);
      setDcWiring(bestConfig.losses.dcWiring);
      setInverterEfficiency(bestConfig.losses.inverterEfficiency);
      setAcWiring(bestConfig.losses.acWiring);
      setTransformerLosses(bestConfig.losses.transformerLosses);
      setMismatchLosses(bestConfig.losses.mismatch);
      setSpacingFactor(bestConfig.recommendedSpacing);
      setCostItems(items => items.map(item => {
        if (item.id === 'structure') return { ...item, unitCost: bestConfig.structureCostPerPanel };
        if (item.id === 'labor') return { ...item, unitCost: bestConfig.laborCostPerPanel };
        return item;
      }));
      if (onInstallConfigChange) {
        onInstallConfigChange({
          tiltRange: bestConfig.tiltRange,
          azimuthLocked: bestConfig.azimuthLocked,
          name: bestConfig.name,
        });
      }

      // 3. AHORA aplicar los ángulos reales del BIPV (DESPUÉS de la config de instalación)
      setInstallTilt(rawTilt);
      setInstallAzimuth(rawAzimuth);

      // 4. Pre-llenar área disponible (solo para referencia visual del área calculator)
      if (bipvData.areaM2 > 0) {
        setAvailableArea(bipvData.areaM2);
        setAreaCalcExpanded(true);
        // NO activar autoSyncQuantity aquí - la cantidad de paneles se calcula
        // correctamente en el paso 5 basado en el tipo de panel
      }
      
      // 5. SINCRONIZAR PANEL DEL CATÁLOGO
      if (bipvData.panelId) {
        const matchedPanel = DEFAULT_PANEL_TECHNOLOGIES.find(p => p.id === bipvData.panelId);
        if (matchedPanel) {
          setSelectedTech(matchedPanel);
          setUseCustomSpecs(false);
          setCustomPower(matchedPanel.pmax);
          setCustomEfficiency(matchedPanel.efficiencySTC);
          setCustomArea((matchedPanel.lengthMm * matchedPanel.widthMm) / 1_000_000);
          setCustomTempCoeff(matchedPanel.tempCoeffPmax / 100);
          setCustomNoct(matchedPanel.noct);
          // Calcular cantidad de paneles: área total / área de un panel (con spacing)
          const panelAreaM2 = (matchedPanel.lengthMm * matchedPanel.widthMm) / 1_000_000;
          const estimatedPanels = Math.max(1, Math.round(bipvData.areaM2 / panelAreaM2));
          setPanelQuantity(estimatedPanels);
          setAutoSyncQuantity(false); // No re-calcular desde el área calculator
        } else {
          // Panel no encontrado en catálogo: usar datos individuales del panel si están disponibles
          setUseCustomSpecs(true);
          if (bipvData.panelPmax && bipvData.panelPmax < 1000) {
            // panelPmax es potencia de UN panel individual (< 1000W es razonable)
            setCustomPower(bipvData.panelPmax);
            const panelAreaM2 = (bipvData.panelLengthMm && bipvData.panelWidthMm)
              ? (bipvData.panelLengthMm * bipvData.panelWidthMm) / 1_000_000
              : bipvData.panelPmax / ((bipvData.panelEfficiencySTC || bipvData.eficienciaAjustada * 100) / 100 * 1000);
            setCustomArea(panelAreaM2);
            setCustomEfficiency(bipvData.panelEfficiencySTC || bipvData.eficienciaAjustada * 100);
            // Calcular cantidad de paneles
            const estimatedPanels = Math.max(1, Math.round(bipvData.potenciaPicoW / bipvData.panelPmax));
            setPanelQuantity(estimatedPanels);
            setAutoSyncQuantity(false);
          } else {
            // Fallback: usar panel de referencia del catálogo y derivar cantidad
            const refPanel = DEFAULT_PANEL_TECHNOLOGIES[0];
            setSelectedTech(refPanel);
            setUseCustomSpecs(false);
            setCustomPower(refPanel.pmax);
            setCustomEfficiency(refPanel.efficiencySTC);
            setCustomArea((refPanel.lengthMm * refPanel.widthMm) / 1_000_000);
            const estimatedPanels = Math.max(1, Math.round(bipvData.potenciaPicoW / refPanel.pmax));
            setPanelQuantity(estimatedPanels);
            setAutoSyncQuantity(false);
          }
          setCustomTempCoeff(bipvData.coefTemperatura / 100);
          setCustomNoct(bipvData.noct);
        }
      } else {
        // Sin panelId: BIPV puro (vidrio fotovoltaico sin panel convencional)
        // Usar un panel virtual derivado de los parámetros BIPV
        // La potenciaPicoW es la potencia TOTAL del sistema, NO de un panel individual
        // Derivar un "panel virtual" de 1 m² y calcular la cantidad correcta
        setUseCustomSpecs(true);
        const eficiencia = bipvData.eficienciaAjustada; // 0-1
        // Panel virtual de 1 m²: potencia = 1000 W/m² × eficiencia × 1 m²
        const virtualPanelPowerW = 1000 * eficiencia; // Potencia STC de 1 m² de vidrio BIPV
        const virtualPanelAreaM2 = 1.0; // 1 m² por "panel virtual"
        setCustomPower(virtualPanelPowerW);
        setCustomEfficiency(eficiencia * 100);
        setCustomArea(virtualPanelAreaM2);
        setCustomTempCoeff(bipvData.coefTemperatura / 100);
        setCustomNoct(bipvData.noct);
        // Cantidad de paneles = área total en m² (cada "panel" = 1 m²)
        const virtualPanelCount = Math.max(1, Math.round(bipvData.areaM2));
        setPanelQuantity(virtualPanelCount);
        setAutoSyncQuantity(false); // No re-calcular, ya está correcto
      }
      
      // 6. Pre-llenar soiling desde IAM+Soiling
      // soilingPromedio es la pérdida fraccional (ej: 0.038 = 3.8% de pérdida)
      // El Simulador espera soilingLosses en % de pérdida directamente
      setSoilingLosses(bipvData.soilingPromedio * 100);

      // 6b. Pre-llenar IAM ASHRAE desde IAM+Soiling
      // iamPromedio es factor de retención (0.81 = 81% retenido, pérdida = 19%)
      // El Simulador espera iamLosses en % de pérdida
      setIamLosses((1 - bipvData.iamPromedio) * 100);

      // 6c. IAM mensual variable: si hay datos mensuales, convertir de factor de retención a % pérdida
      // iamMensual del motor IAM+Soiling es factor de retención (0.78 = 78% retenido)
      // Convertir a pérdida %: (1 - 0.78) * 100 = 22% pérdida
      if (bipvData.iamMensual && bipvData.iamMensual.length === 12) {
        const iamLossesMensual = bipvData.iamMensual.map(factor => (1 - factor) * 100);
        setIamMensualData(iamLossesMensual);
      } else {
        setIamMensualData(undefined);
      }

      // 6d. Soiling mensual variable: si hay datos mensuales, convertir de pérdida fraccional a %
      // soilingMensual del motor IAM+Soiling es pérdida fraccional (0.04 = 4% pérdida)
      // Convertir a %: 0.04 * 100 = 4%
      if (bipvData.soilingMensual && bipvData.soilingMensual.length === 12) {
        const soilingLossesMensual = bipvData.soilingMensual.map(factor => factor * 100);
        setSoilingMensualData(soilingLossesMensual);
      } else {
        setSoilingMensualData(undefined);
      }

      // 7. VALIDACIÓN PREVENTIVA: detectar parámetros sospechosos
      // Si la potencia por panel > 1000W o área por panel > 5m², algo está mal
      const finalPanelPower = bipvData.panelPmax && bipvData.panelPmax < 1000
        ? bipvData.panelPmax
        : bipvData.panelId
          ? (DEFAULT_PANEL_TECHNOLOGIES.find(p => p.id === bipvData.panelId)?.pmax || 0)
          : 1000 * bipvData.eficienciaAjustada;
      const finalPanelArea = bipvData.panelId
        ? (() => {
            const mp = DEFAULT_PANEL_TECHNOLOGIES.find(p => p.id === bipvData.panelId);
            return mp ? (mp.lengthMm * mp.widthMm) / 1_000_000 : 1.0;
          })()
        : 1.0;

      if (finalPanelPower > 1000) {
        toast.warning(
          `⚠️ Validación preventiva: Potencia por panel = ${finalPanelPower.toFixed(0)}W (>1000W). ` +
          `Esto podría indicar que se asignó la potencia TOTAL del sistema como potencia de un panel. ` +
          `Se aplicó corrección automática (panel virtual de 1m²).`,
          { duration: 8000 }
        );
        // Auto-corregir: forzar panel virtual de 1m²
        setUseCustomSpecs(true);
        const eficiencia = bipvData.eficienciaAjustada;
        setCustomPower(1000 * eficiencia);
        setCustomArea(1.0);
        setPanelQuantity(Math.max(1, Math.round(bipvData.areaM2)));
        setAutoSyncQuantity(false);
      } else if (finalPanelArea > 5) {
        toast.warning(
          `⚠️ Validación preventiva: Área por panel = ${finalPanelArea.toFixed(1)}m² (>5m²). ` +
          `Esto podría indicar que se asignó el área TOTAL del sistema como área de un panel. ` +
          `Se aplicó corrección automática (panel virtual de 1m²).`,
          { duration: 8000 }
        );
        // Auto-corregir: forzar panel virtual de 1m²
        setUseCustomSpecs(true);
        const eficiencia = bipvData.eficienciaAjustada;
        setCustomPower(1000 * eficiencia);
        setCustomArea(1.0);
        setPanelQuantity(Math.max(1, Math.round(bipvData.areaM2)));
        setAutoSyncQuantity(false);
      }

      setBipvApplied(true);
    }
  }, [bipvData, bipvApplied]);

  // === PANELES PERSONALIZADOS PERSISTENTES ===
  const { panels: savedPanelsRaw, savePanel: savePanelPersist, deletePanel: deletePanelPersist, isSyncing: panelsSyncing } = useCustomPanels();

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

  // System losses
  const [dcWiring, setDcWiring] = useState(getDefaultInstallationConfig().losses.dcWiring);
  const [inverterEfficiency, setInverterEfficiency] = useState(getDefaultInstallationConfig().losses.inverterEfficiency);
  const [acWiring, setAcWiring] = useState(getDefaultInstallationConfig().losses.acWiring);
  const [transformerLosses, setTransformerLosses] = useState(getDefaultInstallationConfig().losses.transformerLosses);
  const [mismatchLosses, setMismatchLosses] = useState(getDefaultInstallationConfig().losses.mismatch);
  const [soilingLosses, setSoilingLosses] = useState(getDefaultInstallationConfig().losses.soiling);
  const [availabilityLosses, setAvailabilityLosses] = useState(getDefaultInstallationConfig().losses.availabilityLosses);
  const [iamLosses, setIamLosses] = useState(0); // IAM ASHRAE losses (%) - se aplica cuando se importan datos BIPV
  const [iamMensualData, setIamMensualData] = useState<number[] | undefined>(undefined); // 12 valores de pérdida IAM % por mes
  const [soilingMensualData, setSoilingMensualData] = useState<number[] | undefined>(undefined); // 12 valores de pérdida soiling % por mes

  // ===== FIELD MEASUREMENTS STATE =====
  const [fieldMeasurementsEnabled, setFieldMeasurementsEnabled] = useState(false);
  const [fieldGHI, setFieldGHI] = useState<number>(800); // W/m² irradiancia medida en campo
  const [fieldTempAmbient, setFieldTempAmbient] = useState<number>(25); // °C temperatura ambiente medida
  const [fieldTempCell, setFieldTempCell] = useState<number | null>(null); // °C temperatura de celda medida (null = calcular automáticamente)
  const [useManualCellTemp, setUseManualCellTemp] = useState(false); // Si el usuario ingresa T_cell manualmente
  const [fieldMeasurementsExpanded, setFieldMeasurementsExpanded] = useState(true);
  const [fieldLabel, setFieldLabel] = useState(''); // Etiqueta para la medición actual
  const measurementHistory = useFieldMeasurementHistory();

  // Financial parameters - BIPV Cost Breakdown
  interface CostLineItem {
    id: string;
    category: 'panels' | 'inverter' | 'structure' | 'electrical' | 'engineering' | 'permits' | 'labor' | 'transport' | 'contingency' | 'other';
    description: string;
    unitCost: number;
    quantity: number;
    unit: string;
    isAutoCalc: boolean; // auto-calculated from panel quantity
  }

  const defaultCostItems: CostLineItem[] = [
    { id: 'panels', category: 'panels', description: 'Paneles Solares BIPV', unitCost: selectedTech.priceUSD, quantity: panelQuantity, unit: 'ud', isAutoCalc: true },
    { id: 'inverter', category: 'inverter', description: 'Inversor(es) + Optimizadores', unitCost: 0.12, quantity: Math.round(panelQuantity * selectedTech.pmax), unit: 'Wp', isAutoCalc: false },
    { id: 'structure', category: 'structure', description: 'Estructura de Montaje BIPV', unitCost: 35, quantity: panelQuantity, unit: 'ud', isAutoCalc: true },
    { id: 'electrical', category: 'electrical', description: 'Cableado DC/AC + Protecciones', unitCost: 18, quantity: panelQuantity, unit: 'ud', isAutoCalc: true },
    { id: 'engineering', category: 'engineering', description: 'Ingeniería y Diseño', unitCost: 1500, quantity: 1, unit: 'global', isAutoCalc: false },
    { id: 'permits', category: 'permits', description: 'Permisos y Trámites', unitCost: 800, quantity: 1, unit: 'global', isAutoCalc: false },
    { id: 'labor', category: 'labor', description: 'Mano de Obra Instalación', unitCost: 45, quantity: panelQuantity, unit: 'ud', isAutoCalc: true },
    { id: 'transport', category: 'transport', description: 'Transporte y Logística', unitCost: 500, quantity: 1, unit: 'global', isAutoCalc: false },
    { id: 'contingency', category: 'contingency', description: 'Imprevistos / Contingencia (5%)', unitCost: 0, quantity: 1, unit: 'global', isAutoCalc: false },
  ];

  const [costItems, setCostItems] = useState<CostLineItem[]>(defaultCostItems);
  const [costTableExpanded, setCostTableExpanded] = useState(false);
  const [electricityRate, setElectricityRate] = useState(0.15);
  const [maintenanceCostPercent, setMaintenanceCostPercent] = useState(1.5); // % del costo total

  // Auto-update panel cost and quantities when panel or quantity changes
  const prevPanelRef = useRef({ techId: selectedTech.id, qty: panelQuantity });
  useEffect(() => {
    const prev = prevPanelRef.current;
    if (prev.techId !== selectedTech.id || prev.qty !== panelQuantity) {
      setCostItems(items => items.map(item => {
        if (item.id === 'panels') {
          return { ...item, unitCost: selectedTech.priceUSD, quantity: panelQuantity };
        }
        if (item.isAutoCalc && item.id !== 'panels') {
          if (item.id === 'inverter') {
            return { ...item, quantity: Math.round(panelQuantity * selectedTech.pmax) };
          }
          return { ...item, quantity: panelQuantity };
        }
        return item;
      }));
      prevPanelRef.current = { techId: selectedTech.id, qty: panelQuantity };
    }
  }, [selectedTech.id, selectedTech.priceUSD, selectedTech.pmax, panelQuantity]);

  // Auto-calculate contingency (5% of subtotal excluding contingency itself)
  useEffect(() => {
    setCostItems(items => {
      const subtotalWithoutContingency = items
        .filter(i => i.category !== 'contingency')
        .reduce((sum, i) => sum + (i.unitCost * i.quantity), 0);
      const contingencyAmount = Math.round(subtotalWithoutContingency * 0.05);
      return items.map(item => {
        if (item.category === 'contingency' && item.id === 'contingency') {
          return { ...item, unitCost: contingencyAmount, quantity: 1 };
        }
        return item;
      });
    });
  }, [costItems.filter(i => i.category !== 'contingency').map(i => i.unitCost * i.quantity).join(',')]);

  // Calculate total system cost from cost items
  const systemCost = useMemo(() => {
    return costItems.reduce((sum, item) => sum + (item.unitCost * item.quantity), 0);
  }, [costItems]);

  const maintenanceCost = useMemo(() => {
    return systemCost * (maintenanceCostPercent / 100);
  }, [systemCost, maintenanceCostPercent]);

  const updateCostItem = (id: string, field: 'unitCost' | 'quantity' | 'description', value: number | string) => {
    setCostItems(items => items.map(item =>
      item.id === id ? { ...item, [field]: value } : item
    ));
  };

  const addCostItem = () => {
    const newItem: CostLineItem = {
      id: `custom_${Date.now()}`,
      category: 'other',
      description: 'Nuevo ítem',
      unitCost: 0,
      quantity: 1,
      unit: 'global',
      isAutoCalc: false,
    };
    setCostItems(items => [...items, newItem]);
  };

  const removeCostItem = (id: string) => {
    // Don't allow removing the panels line
    if (id === 'panels') return;
    setCostItems(items => items.filter(item => item.id !== id));
  };

  const handleSelectTech = (tech: PanelTechnology) => {
    setSelectedTech(tech);
    setCustomPower(tech.pmax);
    setCustomEfficiency(tech.efficiencySTC);
    setCustomArea((tech.lengthMm * tech.widthMm) / 1_000_000);
    setCustomTempCoeff(tech.tempCoeffPmax / 100);
    setCustomNoct(tech.noct);
    setUseCustomSpecs(false);
  };

  // Effective panel values
  const panelPower = useCustomSpecs ? customPower : selectedTech.pmax;
  const panelEfficiency = useCustomSpecs ? customEfficiency : selectedTech.efficiencySTC;
  const panelArea = useCustomSpecs ? customArea : (selectedTech.lengthMm * selectedTech.widthMm) / 1_000_000;
  const tempCoefficient = useCustomSpecs ? customTempCoeff : selectedTech.tempCoeffPmax / 100;
  const noct = useCustomSpecs ? customNoct : selectedTech.noct;

  // ===== FIELD MEASUREMENTS DERIVED CALCULATIONS =====
  const fieldCellTemp = useMemo(() => {
    if (!fieldMeasurementsEnabled) return null;
    if (useManualCellTemp && fieldTempCell !== null) return fieldTempCell;
    // Calcular T_cell con modelo NOCT: T_cell = T_amb + (NOCT - 20) × (G / 800)
    return mulcueCellTemp(fieldTempAmbient, noct, fieldGHI);
  }, [fieldMeasurementsEnabled, useManualCellTemp, fieldTempCell, fieldTempAmbient, noct, fieldGHI]);

  // P_exp de campo usando Mulcue-Llanos
  const fieldPExp = useMemo(() => {
    if (!fieldMeasurementsEnabled || fieldCellTemp === null) return null;
    return calculateExpectedPower(
      panelPower,
      selectedTech.tempCoeffPmax, // en %/°C
      fieldCellTemp,
      fieldGHI,
    );
  }, [fieldMeasurementsEnabled, fieldCellTemp, panelPower, selectedTech.tempCoeffPmax, fieldGHI]);

  // PR de campo usando Mulcue-Llanos
  const fieldPR = useMemo(() => {
    if (!fieldMeasurementsEnabled) return null;
    return calculateMulcuePR({
      tempCoeffGamma: selectedTech.tempCoeffPmax,
      ambientTemp: fieldTempAmbient,
    });
  }, [fieldMeasurementsEnabled, selectedTech.tempCoeffPmax, fieldTempAmbient]);

  // Factor de pérdida por temperatura de campo
  const fieldTempLoss = useMemo(() => {
    if (!fieldMeasurementsEnabled || fieldCellTemp === null) return null;
    return calculateTempLossFactor(fieldCellTemp, selectedTech.tempCoeffPmax);
  }, [fieldMeasurementsEnabled, fieldCellTemp, selectedTech.tempCoeffPmax]);

  // ===== FIELD PERFORMANCE DIAGNOSTIC =====
  const fieldPerformanceAlert = useMemo((): PerformanceAlertType | null => {
    if (!fieldMeasurementsEnabled || fieldCellTemp === null || fieldPExp === null || fieldPR === null || fieldTempLoss === null) return null;
    return diagnosePerformance({
      prMeasured: fieldPR.prCorrected,
      ghiField: fieldGHI,
      tempAmbient: fieldTempAmbient,
      tempCell: fieldCellTemp,
      tempCellManual: useManualCellTemp,
      pExp: fieldPExp,
      pNom: panelPower,
      tempCoeff: selectedTech.tempCoeffPmax,
      noct: noct,
      tempLoss: fieldTempLoss,
      installationType: selectedInstallation.id,
      systemLosses: {
        soiling: soilingLosses,
        mismatch: mismatchLosses,
        dcWiring: dcWiring,
        acWiring: acWiring,
        inverterEfficiency: inverterEfficiency,
      },
      latitude: weatherData.location.latitude,
    });
  }, [
    fieldMeasurementsEnabled, fieldCellTemp, fieldPExp, fieldPR, fieldTempLoss,
    fieldGHI, fieldTempAmbient, useManualCellTemp, panelPower, selectedTech.tempCoeffPmax,
    noct, selectedInstallation.id, soilingLosses, mismatchLosses, dcWiring,
    acWiring, inverterEfficiency, weatherData.location.latitude,
  ]);

  // ===== AREA CALCULATOR LOGIC =====
  const areaCalcResult = useMemo(() => {
    const panelLengthM = selectedTech.lengthMm / 1000;
    const panelWidthM = selectedTech.widthMm / 1000;

    // Dimensions based on orientation
    const panelW = panelOrientation === 'landscape' ? panelLengthM : panelWidthM;
    const panelH = panelOrientation === 'landscape' ? panelWidthM : panelLengthM;

    // Effective dimensions with spacing
    const effectiveW = panelW * spacingFactor;
    const effectiveH = panelH * spacingFactor;

    // Single panel area with spacing
    const singlePanelAreaWithSpacing = effectiveW * effectiveH;
    const singlePanelAreaNet = panelW * panelH;

    let panelsInRow = 0;
    let panelsInCol = 0;
    let totalPanels = 0;

    if (useRectangular) {
      // Rectangular layout: use width x length
      panelsInRow = Math.floor(availableWidth / effectiveW);
      panelsInCol = Math.floor(availableLength / effectiveH);
      totalPanels = panelsInRow * panelsInCol;
    } else {
      // Simple area-based calculation
      totalPanels = Math.floor(availableArea / singlePanelAreaWithSpacing);
      // Estimate rows/cols for visualization
      const side = Math.sqrt(availableArea);
      panelsInRow = Math.floor(side / effectiveW);
      panelsInCol = totalPanels > 0 && panelsInRow > 0 ? Math.ceil(totalPanels / panelsInRow) : 0;
    }

    const totalPanelArea = totalPanels * singlePanelAreaNet;
    const totalOccupiedArea = totalPanels * singlePanelAreaWithSpacing;
    const effectiveAreaUsed = useRectangular ? availableWidth * availableLength : availableArea;
    const coverageRatio = effectiveAreaUsed > 0 ? (totalPanelArea / effectiveAreaUsed) * 100 : 0;
    const totalPowerKWp = (totalPanels * selectedTech.pmax) / 1000;

    return {
      panelW,
      panelH,
      effectiveW,
      effectiveH,
      singlePanelAreaNet,
      singlePanelAreaWithSpacing,
      panelsInRow,
      panelsInCol,
      totalPanels,
      totalPanelArea,
      totalOccupiedArea,
      coverageRatio,
      totalPowerKWp,
      effectiveAreaUsed,
    };
  }, [selectedTech, panelOrientation, spacingFactor, availableArea, availableWidth, availableLength, useRectangular]);

  const applyAreaCalculation = useCallback(() => {
    setPanelQuantity(areaCalcResult.totalPanels);
    setAutoSyncQuantity(true);
  }, [areaCalcResult.totalPanels]);

  // Auto-sync: when autoSync is on, update panelQuantity whenever area calc result changes
  // Skip sync when prospector data is active (user chose specific module count from Prospector)
  useEffect(() => {
    if (autoSyncQuantity && areaCalcResult.totalPanels > 0 && !prospectorApplied) {
      setPanelQuantity(areaCalcResult.totalPanels);
    }
  }, [autoSyncQuantity, areaCalcResult.totalPanels, prospectorApplied]);

  const panelSpecs: PanelSpecifications = {
    powerRating: panelPower,
    efficiency: panelEfficiency,
    temperatureCoefficient: tempCoefficient,
    nominalOperatingCellTemperature: noct,
    area: panelArea,
    quantity: panelQuantity,
  };

  const systemLosses: SystemLosses = {
    dcWiring,
    inverterEfficiency,
    acWiring,
    transformerLosses,
    mismatchLosses,
    soilingLosses,
    shadingLosses: 0,
    availabilityLosses,
    iamLosses,
  };

  const monthlyPOAData = useMemo(() => {
    if (fieldMeasurementsEnabled && fieldCellTemp !== null) {
      // Cuando hay mediciones de campo, usar GHI y T_amb de campo para todos los meses
      // Los factores de sombreado (FS) de la Calculadora se siguen aplicando
      return poaData.map((data) => ({
        month: data.month,
        avgPOA: fieldGHI, // Irradiancia medida en campo
        avgTemp: fieldTempAmbient, // Temperatura ambiente medida en campo
        avgWindSpeed: data.avgWindSpeed ?? 1, // Viento real del EPW
      }));
    }
    // Usar windSpeed real del EPW (ya viene calculado en poaData desde Home.tsx)
    // Pasar componentes POA separadas para aplicación pre-cálculo de IAM (solo afecta directa)
    return poaData.map((data) => ({
      month: data.month,
      avgPOA: data.totalPOA,
      avgTemp: data.avgTemp,
      avgWindSpeed: data.avgWindSpeed ?? 1, // Viento real del EPW
      directPOA: data.directPOA,
      diffusePOA: data.diffusePOA,
      reflectedPOA: data.reflectedPOA,
    }));
  }, [poaData, fieldMeasurementsEnabled, fieldGHI, fieldTempAmbient, fieldCellTemp]);

  const production = useMemo(() => {
    // Cuando hay mediciones de campo activas, pasar T_cell como override
    // para que el motor de producción use la T_cell de campo (manual o calculada con NOCT)
    // en vez de recalcularla internamente con su propia fórmula
    const cellTempFieldOverride = (fieldMeasurementsEnabled && fieldCellTemp !== null)
      ? fieldCellTemp
      : undefined;
    return calculateAnnualProduction(monthlyPOAData, panelSpecs, systemLosses, activeShadingFactors, cellTempFieldOverride, iamMensualData, soilingMensualData);
  }, [monthlyPOAData, panelSpecs, systemLosses, activeShadingFactors, fieldMeasurementsEnabled, fieldCellTemp, iamMensualData, soilingMensualData]);

  // ===== ENERGY PERFORMANCE INDEX (EPI) - IEC 61724-1:2021 =====
  // EPI = E_AC_simulador / E_AC_benchmark (PVWatts como benchmark satelital)
  const epi = useMemo(() => {
    if (!pvwattsData || pvwattsData.annualAC_kWh <= 0) return null;
    return production.totalACEnergy / pvwattsData.annualAC_kWh;
  }, [production.totalACEnergy, pvwattsData]);

  // ===== PR_T HORARIO IEC 61724-1:2021 =====
  // Calcula PR_T paso a paso temporal con datos horarios de PVWatts o PVGIS
  const hourlyPR_T_PVWatts = useMemo<HourlyPR_T_Result | null>(() => {
    if (!pvwattsData?.hourlyRecords || pvwattsData.hourlyRecords.length < 1000) return null;
    const gamma = panelSpecs.temperatureCoefficient; // ej: -0.004
    const records: HourlyRecord[] = pvwattsData.hourlyRecords.map(r => ({
      month: r.month,
      poa_Wm2: r.poa_Wm2,
      tamb_C: r.tamb_C,
      tcell_C: r.tcell_C,
      wspd_ms: r.wspd_ms,
      ac_W: r.ac_W,
      dc_W: r.dc_W,
    }));
    return calculatePR_T_Hourly(records, pvwattsData.systemCapacity, gamma, panelSpecs.nominalOperatingCellTemperature, panelSpecs.efficiency * 100, 'pvwatts');
  }, [pvwattsData, panelSpecs.temperatureCoefficient, panelSpecs.nominalOperatingCellTemperature, panelSpecs.efficiency]);

  const hourlyPR_T_PVGIS = useMemo<HourlyPR_T_Result | null>(() => {
    if (!pvgisData?.hourlyRecords || pvgisData.hourlyRecords.length < 1000) return null;
    const gamma = panelSpecs.temperatureCoefficient;
    const records: HourlyRecord[] = pvgisData.hourlyRecords.map(r => ({
      month: r.month,
      poa_Wm2: r.poa_Wm2,
      tamb_C: r.tamb_C,
      wspd_ms: r.wspd_ms,
      ac_W: r.ac_W,
    }));
    return calculatePR_T_Hourly(records, pvgisData.peakPowerKwp, gamma, panelSpecs.nominalOperatingCellTemperature, panelSpecs.efficiency * 100, 'pvgis');
  }, [pvgisData, panelSpecs.temperatureCoefficient, panelSpecs.nominalOperatingCellTemperature, panelSpecs.efficiency]);

  // ===== TABLA COMPARATIVA (VALIDACIÓN CRUZADA) =====
  const crossValidation = useMemo(() => {
    const hasPVW = !!pvwattsData;
    const hasPVG = !!pvgisData;
    const hasBIPV = !!(bipvData && bipvData.produccionMensualKwh && bipvData.produccionMensualKwh.length === 12);
    if (!hasPVW && !hasPVG && !hasBIPV) return null;
    const simKwp = (panelPower * panelQuantity) / 1000;
    return buildComparisonData(production, pvwattsData, pvgisData, hourlyPR_T_PVWatts, hourlyPR_T_PVGIS, bipvData, simKwp);
  }, [production, pvwattsData, pvgisData, hourlyPR_T_PVWatts, hourlyPR_T_PVGIS, bipvData, panelPower, panelQuantity]);

  const financials = useMemo(() => {
    return calculateFinancials(production.totalACEnergy, systemCost, electricityRate, maintenanceCost);
  }, [production.totalACEnergy, systemCost, electricityRate, maintenanceCost]);

  // Notificar al padre cuando cambian los parámetros financieros
  useEffect(() => {
    if (onFinancialParamsChange) {
      const capacityWp = panelPower * panelQuantity;
      const costPerWp = capacityWp > 0 ? systemCost / capacityWp : 0;
      onFinancialParamsChange({ electricityRate, systemCost, costPerWp });
    }
  }, [electricityRate, systemCost, panelPower, panelQuantity, onFinancialParamsChange]);

  // Notificar al padre con todos los datos de energía para el reporte
  // Usar useRef para el callback para evitar bucle infinito de re-renders
  const onEnergyDataChangeRef = useRef(onEnergyDataChange);
  onEnergyDataChangeRef.current = onEnergyDataChange;

  const prevEnergyDataRef = useRef<string>('');
  useEffect(() => {
    if (!onEnergyDataChangeRef.current) return;
    const totalLoss = (dcWiring + (100 - inverterEfficiency) + acWiring + mismatchLosses + soilingLosses + availabilityLosses) / 100;
    const tiltVal = poaConfig?.tilt ?? installTilt;
    const azVal = poaConfig?.azimuth ?? installAzimuth;
    const newData = {
      panelPower,
      panelEfficiency,
      panelArea,
      panelQuantity,
      tilt: tiltVal,
      azimuth: azVal,
      annualProduction: production.totalACEnergy,
      capacityFactor: production.capacityFactor,
      performanceRatio: production.performanceRatio,
      systemLosses: totalLoss,
      paybackPeriod: financials.paybackPeriod,
      roi10Year: financials.roi10Years,
      roi25Year: financials.roi25Years,
    };
    const key = JSON.stringify(newData);
    if (key !== prevEnergyDataRef.current) {
      prevEnergyDataRef.current = key;
      onEnergyDataChangeRef.current(newData);
    }
  }, [panelPower, panelEfficiency, panelArea, panelQuantity, installTilt, installAzimuth, poaConfig?.tilt, poaConfig?.azimuth, production.totalACEnergy, production.capacityFactor, production.performanceRatio, financials.paybackPeriod, financials.roi10Years, financials.roi25Years, dcWiring, inverterEfficiency, acWiring, mismatchLosses, soilingLosses, availabilityLosses]);

  const lossesData = [
    { name: 'Temperatura', value: Math.round(production.losses.temperature * 10) / 10 },
    { name: 'Cableado DC', value: production.losses.dcWiring },
    { name: 'Inversor', value: production.losses.inverter },
    { name: 'Cableado AC', value: production.losses.acWiring },
    { name: 'Desajuste', value: production.losses.mismatch },
    { name: 'Suciedad', value: production.losses.soiling },
    { name: 'Sombreado', value: production.losses.shading },
    { name: 'Disponibilidad', value: production.losses.availability },
  ].filter(d => d.value > 0);

  const COLORS = ['#EF4444', '#F97316', '#F59E0B', '#FBBF24', '#A3E635', '#4ADE80', '#22C55E', '#10B981'];

  const hasShadingData = activeShadingFactors.some(f => f < 1.0);
  const avgShadingFactor = activeShadingFactors.reduce((a, b) => a + b, 0) / 12;

  return (
    <div className="space-y-6">
      {/* Prospector Solar Bridge Banner — diferenciado por fuente PVGIS vs PVWatts */}
      {prospectorData && prospectorApplied && (() => {
        const isPVWatts = prospectorData.source === 'heatmap_pvwatts';
        const bannerGradient = isPVWatts
          ? 'bg-gradient-to-r from-indigo-50 to-violet-50 border-2 border-indigo-300'
          : 'bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300';
        const titleColor = isPVWatts ? 'text-indigo-900' : 'text-amber-900';
        const iconColor = isPVWatts ? 'text-indigo-600' : 'text-amber-600';
        const subtitleColor = isPVWatts ? 'text-indigo-700' : 'text-amber-700';
        const ghiAccent = isPVWatts ? 'text-indigo-800' : 'text-amber-800';
        const sourceLabel = isPVWatts ? 'PVWatts (NREL TMY)' : 'PVGIS (Satelital)';
        const sourceIcon = isPVWatts ? <Satellite size={16} className={iconColor} /> : <Globe size={16} className={iconColor} />;
        const heatmapLabel = isPVWatts ? 'Heatmap PVWatts Satelital (NREL)' : 'Heatmap de Irradiancia (PVGIS)';
        return (
          <div className={`${bannerGradient} rounded-lg p-4 shadow-sm`}>
            <div className="flex items-start justify-between">
              <div>
                <h3 className={`text-sm font-bold ${titleColor} flex items-center gap-2`}>
                  {sourceIcon}
                  <Zap size={16} className={iconColor} />
                  Datos del Prospector Solar (Modelo Mulcue-Llanos)
                  <span className={`ml-2 text-[10px] font-semibold px-2 py-0.5 rounded-full ${isPVWatts ? 'bg-indigo-200 text-indigo-800' : 'bg-amber-200 text-amber-800'}`}>
                    Fuente: {sourceLabel}
                  </span>
                </h3>
                <p className={`text-xs ${subtitleColor} mt-1`}>
                  Los parámetros iniciales fueron pre-llenados desde el <strong>{heatmapLabel}</strong>.
                  Fuente GHI: <strong>{prospectorData.lat && prospectorData.lng ? `(${prospectorData.lat.toFixed(2)}°, ${prospectorData.lng.toFixed(2)}°)` : 'N/A'}</strong>.
                  Puedes ajustarlos manualmente si lo necesitas.
                </p>
              </div>
              <button
                onClick={() => {
                  setProspectorApplied(false);
                  setAutoSyncQuantity(true);
                  if (onDiscardProspector) onDiscardProspector();
                }}
                className="text-xs bg-red-100 text-red-700 hover:bg-red-200 px-3 py-1 rounded-md font-medium transition-colors whitespace-nowrap"
              >
                ✕ Descartar datos del Prospector
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2 mt-3">
              <div className="bg-white/70 rounded p-2 text-center">
                <p className="text-[10px] text-gray-500">GHI ({isPVWatts ? 'PVWatts' : 'PVGIS'})</p>
                <p className={`text-sm font-bold ${ghiAccent}`}>{prospectorData.ghiAnnualKwhM2.toFixed(0)} <span className="text-[10px] font-normal">kWh/m²/a</span></p>
              </div>
              <div className="bg-white/70 rounded p-2 text-center">
                <p className="text-[10px] text-gray-500">PR Mulcue-Llanos</p>
                <p className="text-sm font-bold text-blue-700">{(prospectorData.prCorrected * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-white/70 rounded p-2 text-center">
                <p className="text-[10px] text-gray-500">Región</p>
                <p className="text-sm font-bold text-indigo-700">{prospectorData.regionLabel}</p>
              </div>
              <div className="bg-white/70 rounded p-2 text-center">
                <p className="text-[10px] text-gray-500">T. Ambiente</p>
                <p className="text-sm font-bold text-orange-700">{prospectorData.ambientTemp.toFixed(1)}°C</p>
              </div>
              <div className="bg-white/70 rounded p-2 text-center">
                <p className="text-[10px] text-gray-500">T. Celda (NOCT={prospectorData.noct}°C)</p>
                <p className="text-sm font-bold text-red-700">{prospectorData.cellTemp.toFixed(1)}°C</p>
              </div>
              <div className="bg-white/70 rounded p-2 text-center">
                <p className="text-[10px] text-gray-500">Pérdida por T°</p>
                <p className="text-sm font-bold text-red-600">{prospectorData.tempLossPercent.toFixed(1)}%</p>
              </div>
              <div className="bg-white/70 rounded p-2 text-center">
                <p className="text-[10px] text-gray-500">Estimación Prospector</p>
                <p className="text-sm font-bold text-green-700">{prospectorData.estimatedEnergyKwh.toFixed(0)} <span className="text-[10px] font-normal">kWh/a</span></p>
              </div>
              <div className="bg-white/70 rounded p-2 text-center">
                <p className="text-[10px] text-gray-500">Coordenadas</p>
                <p className="text-xs font-mono font-bold text-gray-700">{prospectorData.lat.toFixed(2)}°, {prospectorData.lng.toFixed(2)}°</p>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Optimizer Result Banner */}
      {optimizerResult && (
        <div className="bg-gradient-to-r from-cyan-50 to-teal-50 border-2 border-cyan-300 rounded-lg p-4 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-bold text-cyan-900 flex items-center gap-2">
                <Target size={16} className="text-cyan-600" />
                Datos del Optimizador de Orientación
              </h3>
              <p className="text-xs text-cyan-700 mt-1">
                Orientación óptima aplicada automáticamente. Tilt y azimut sincronizados con el cálculo POA.
              </p>
            </div>
            <button
              onClick={() => {
                if (onDiscardOptimizer) onDiscardOptimizer();
              }}
              className="text-xs bg-red-100 text-red-700 hover:bg-red-200 px-3 py-1 rounded-md font-medium transition-colors whitespace-nowrap"
            >
              ✕ Descartar datos del Optimizador
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 mt-3">
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Tilt Óptimo</p>
              <p className="text-sm font-bold text-cyan-800">{optimizerResult.optimalTilt}°</p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Azimut Óptimo</p>
              <p className="text-sm font-bold text-cyan-800">{optimizerResult.optimalAzimuth}°</p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">POA Óptimo</p>
              <p className="text-sm font-bold text-green-700">{Math.round(optimizerResult.optimalPOA)} <span className="text-[10px] font-normal">W/m²</span></p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">POA Anterior</p>
              <p className="text-sm font-bold text-gray-600">{Math.round(optimizerResult.currentPOA)} <span className="text-[10px] font-normal">W/m²</span></p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Ganancia</p>
              <p className={`text-sm font-bold ${optimizerResult.gainPercent > 0 ? 'text-green-700' : 'text-red-600'}`}>
                {optimizerResult.gainPercent > 0 ? '+' : ''}{optimizerResult.gainPercent}%
              </p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Tilt/Az Anterior</p>
              <p className="text-xs font-mono font-bold text-gray-500">{optimizerResult.currentTilt}° / {optimizerResult.currentAzimuth}°</p>
            </div>
          </div>
        </div>
      )}

      {/* Banner PVGIS Real */}
      {pvgisData && (
        <div className="bg-gradient-to-r from-emerald-50 to-green-50 border-2 border-emerald-300 rounded-lg p-4 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-bold text-emerald-900 flex items-center gap-2">
                <Globe size={16} className="text-emerald-600" />
                Datos PVGIS Real (Producción AC Satelital)
              </h3>
              <p className="text-xs text-emerald-700 mt-1">
                Producción AC real de PVGIS ({pvgisData.radiationDB}, {pvgisData.yearMin}-{pvgisData.yearMax}). Panel: {pvgisData.panelName}. Pérdidas sistema: {pvgisData.systemLoss}%.
              </p>
            </div>
            <button
              onClick={() => { if (onDiscardPvgis) onDiscardPvgis(); }}
              className="text-xs bg-red-100 text-red-700 hover:bg-red-200 px-3 py-1 rounded-md font-medium transition-colors whitespace-nowrap"
            >
              ✕ Descartar PVGIS
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 mt-3">
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Producción PVGIS</p>
              <p className="text-sm font-bold text-emerald-800">{pvgisData.annualProductionAC.toFixed(0)} <span className="text-[10px] font-normal">kWh/año AC</span></p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Corregida (Panel Real)</p>
              <p className="text-sm font-bold text-green-700">{pvgisData.annualProductionCorrected.toFixed(0)} <span className="text-[10px] font-normal">kWh/año AC</span></p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Irrad. POA</p>
              <p className="text-sm font-bold text-yellow-700">{pvgisData.annualIrradiationPOA.toFixed(0)} <span className="text-[10px] font-normal">kWh/m²/año</span></p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Factor Corrección</p>
              <p className="text-sm font-bold text-purple-700">{(pvgisData.correctionFactor * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Tilt / Azimut</p>
              <p className="text-sm font-bold text-gray-700">{pvgisData.tilt}° / {pvgisData.azimuth}°</p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Potencia Pico</p>
              <p className="text-sm font-bold text-blue-700">{pvgisData.peakPowerKwp} <span className="text-[10px] font-normal">kWp</span></p>
            </div>
          </div>
        </div>
      )}

      {/* Banner PVWatts Satelital */}
      {pvwattsData && (
        <div className="bg-gradient-to-r from-indigo-50 to-violet-50 border-2 border-indigo-300 rounded-lg p-4 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-bold text-indigo-900 flex items-center gap-2">
                <Satellite size={16} className="text-indigo-600" />
                Datos PVWatts Satelital (NREL TMY)
              </h3>
              <p className="text-xs text-indigo-700 mt-1">
                Producción AC/DC de PVWatts v8 ({pvwattsData.weatherSource}). Pérdidas: {pvwattsData.losses}%. Estación: {pvwattsData.stationCity || 'N/A'} ({pvwattsData.stationDistance.toFixed(0)} km).
              </p>
            </div>
            <button
              onClick={() => { if (onDiscardPvwatts) onDiscardPvwatts(); }}
              className="text-xs bg-red-100 text-red-700 hover:bg-red-200 px-3 py-1 rounded-md font-medium transition-colors whitespace-nowrap"
            >
              ✕ Descartar PVWatts
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2 mt-3">
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Producción AC</p>
              <p className="text-sm font-bold text-indigo-800">{pvwattsData.annualAC_kWh.toFixed(0)} <span className="text-[10px] font-normal">kWh/año</span></p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Producción DC</p>
              <p className="text-sm font-bold text-blue-700">{pvwattsData.annualDC_kWh.toFixed(0)} <span className="text-[10px] font-normal">kWh/año</span></p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Specific Yield</p>
              <p className="text-sm font-bold text-green-700">{pvwattsData.specificYield.toFixed(0)} <span className="text-[10px] font-normal">kWh/kWp</span></p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">POA Anual</p>
              <p className="text-sm font-bold text-yellow-700">{pvwattsData.annualPOA_kWhm2.toFixed(0)} <span className="text-[10px] font-normal">kWh/m²</span></p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">GHI Anual</p>
              <p className="text-sm font-bold text-orange-700">{pvwattsData.annualGHI_kWhm2.toFixed(0)} <span className="text-[10px] font-normal">kWh/m²</span></p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Cap. Factor</p>
              <p className="text-sm font-bold text-purple-700">{pvwattsData.capacityFactor.toFixed(1)}%</p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Tilt / Azimut</p>
              <p className="text-sm font-bold text-gray-700">{pvwattsData.tilt}° / {pvwattsData.azimuth}°</p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Coordenadas</p>
              <p className="text-xs font-mono font-bold text-gray-700">{pvwattsData.latitude.toFixed(2)}°, {pvwattsData.longitude.toFixed(2)}°</p>
            </div>
          </div>
        </div>
      )}

      {/* Banner BIPV IAM+Soiling */}
      {bipvData && (
        <div className="bg-gradient-to-r from-teal-50 to-cyan-50 border-2 border-teal-300 rounded-lg p-4 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-bold text-teal-900 flex items-center gap-2">
                <Sun size={16} className="text-teal-600" />
                <Zap size={16} className="text-teal-600" />
                Datos IAM+Soiling BIPV
              </h3>
              <p className="text-xs text-teal-700 mt-1">
                Tecnología: <strong>{bipvData.technology}</strong> ({bipvData.generation}) | τ={( bipvData.transparencia * 100).toFixed(0)}% | Modelo: {bipvData.transpositionModel === 'perez' ? 'Perez' : 'Isotrópico'}
              </p>
              {bipvData.panelId && (
                <p className="text-[10px] text-teal-600 mt-0.5 flex items-center gap-1">
                  <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
                  Panel sincronizado: <strong>{selectedTech.name}</strong>
                  {bipvData.panelId === selectedTech.id ? ' ✔' : ' (manual override)'}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              {onReturnToBIPV && (
                <button
                  onClick={onReturnToBIPV}
                  className="text-xs bg-teal-100 text-teal-700 hover:bg-teal-200 px-3 py-1 rounded-md font-medium transition-colors whitespace-nowrap flex items-center gap-1"
                >
                  ← Volver al BIPV
                </button>
              )}
              <button
                onClick={() => { if (onDiscardBipv) onDiscardBipv(); setBipvApplied(false); }}
                className="text-xs bg-red-100 text-red-700 hover:bg-red-200 px-3 py-1 rounded-md font-medium transition-colors whitespace-nowrap"
              >
                ✕ Descartar BIPV
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 mt-3">
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Energía Anual</p>
              <p className="text-sm font-bold text-teal-800">{bipvData.energiaAnualKwh.toFixed(0)} <span className="text-[10px] font-normal">kWh</span></p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">kWh/m²</p>
              <p className="text-sm font-bold text-cyan-700">{bipvData.energiaAnualKwhM2.toFixed(1)}</p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">η Ajustada</p>
              <p className="text-sm font-bold text-green-700">{(bipvData.eficienciaAjustada * 100).toFixed(1)}%</p>
            </div>
            <div className={`rounded p-2 text-center ${(1 - bipvData.iamPromedio) * 100 > 25 ? 'bg-red-100 border border-red-300' : (1 - bipvData.iamPromedio) * 100 > 15 ? 'bg-amber-100 border border-amber-300' : 'bg-green-100 border border-green-300'}`}>
              <p className="text-[10px] text-gray-500">IAM Aplicado</p>
              <p className={`text-sm font-bold ${(1 - bipvData.iamPromedio) * 100 > 25 ? 'text-red-700' : (1 - bipvData.iamPromedio) * 100 > 15 ? 'text-amber-700' : 'text-green-700'}`}>{((1 - bipvData.iamPromedio) * 100).toFixed(1)}%</p>
              <p className="text-[9px] text-gray-400">pérdida angular</p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Soiling Prom.</p>
              <p className="text-sm font-bold text-orange-700">{(bipvData.soilingPromedio * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">F. Térmico</p>
              <p className="text-sm font-bold text-red-700">{(bipvData.factorTermicoPromedio * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Área</p>
              <p className="text-xs font-bold text-gray-700">{bipvData.areaM2.toFixed(1)} m²</p>
            </div>
            <div className="bg-white/70 rounded p-2 text-center">
              <p className="text-[10px] text-gray-500">Tilt / Az BIPV</p>
              <p className="text-xs font-bold text-indigo-700">{Math.abs(bipvData.tilt)}° / {bipvData.azimuth < 0 || bipvData.azimuth > 360 ? (((bipvData.azimuth + 180) % 360 + 360) % 360).toFixed(0) : bipvData.azimuth.toFixed(0)}°</p>
            </div>
          </div>
          {iamMensualData && (
            <div className="mt-2 px-3 py-1.5 bg-violet-50 border border-violet-200 rounded-md text-xs text-violet-800 flex items-center gap-2">
              <span className="font-semibold">✓ IAM mensual variable activo:</span>
              <span className="font-mono text-[10px]">
                [{iamMensualData.map(v => v.toFixed(1) + '%').join(', ')}]
              </span>
            </div>
          )}
          {soilingMensualData && (
            <div className="mt-2 px-3 py-1.5 bg-teal-50 border border-teal-200 rounded-md text-xs text-teal-800 flex items-center gap-2">
              <span className="font-semibold">✓ Soiling mensual variable activo:</span>
              <span className="font-mono text-[10px]">
                [{soilingMensualData.map(v => v.toFixed(1) + '%').join(', ')}]
              </span>
            </div>
          )}
        </div>
      )}

      {/* ===== COMPARACIÓN IMPACTO BIPV vs ESTÁNDAR ===== */}
      {bipvData && production && (() => {
        // Escenario "Con BIPV": usa los parámetros actuales del simulador (ya aplicados desde bipvData)
        const conBIPV = production;
        
        // Panel baseline: seleccionado por el usuario o genérico
        const baselinePanel = baselinePanelId ? DEFAULT_PANEL_TECHNOLOGIES.find(p => p.id === baselinePanelId) : null;
        const baselineName = baselinePanel ? `${baselinePanel.name} (${baselinePanel.pmax}W)` : 'Genérico 400W/20%';
        
        // Escenario "Sin BIPV": simular con panel baseline seleccionado
        // NOTA: calculateAnnualProduction espera efficiency en % (ej: 20, 23.2), NO en fracción (0.20)
        const panelEstandar: PanelSpecifications = baselinePanel ? {
          powerRating: baselinePanel.pmax,
          efficiency: baselinePanel.efficiencySTC, // % directo (ej: 23.2)
          temperatureCoefficient: baselinePanel.tempCoeffPmax / 100, // convertir de %/°C a fracción/°C
          nominalOperatingCellTemperature: baselinePanel.noct,
          area: (baselinePanel.lengthMm * baselinePanel.widthMm) / 1_000_000,
          quantity: Math.max(1, Math.round(bipvData.areaM2 / ((baselinePanel.lengthMm * baselinePanel.widthMm) / 1_000_000))),
        } : {
          powerRating: 400,
          efficiency: 20, // 20% en unidades de porcentaje
          temperatureCoefficient: -0.004,
          nominalOperatingCellTemperature: 45,
          area: 2.0,
          quantity: Math.max(1, Math.round(bipvData.areaM2 / 2.0)),
        };
        const lossesEstandar: SystemLosses = {
          dcWiring: 2.0,
          inverterEfficiency: 96.5,
          acWiring: 1.5,
          transformerLosses: 0.5,
          mismatchLosses: 2.0,
          soilingLosses: 3.0,
          shadingLosses: 0,
          availabilityLosses: 1.5,
          iamLosses: 0, // Panel estándar sin IAM ASHRAE
        };
        const sinBIPV = calculateAnnualProduction(monthlyPOAData, panelEstandar, lossesEstandar, shadingFactors);
        
        // Capacidades para Yield
        const kwpConBIPV = (panelPower * panelQuantity) / 1000;
        const kwpSinBIPV = (panelEstandar.powerRating * panelEstandar.quantity) / 1000;
        const yieldConBIPV = kwpConBIPV > 0 ? conBIPV.totalACEnergy / kwpConBIPV : 0;
        const yieldSinBIPV = kwpSinBIPV > 0 ? sinBIPV.totalACEnergy / kwpSinBIPV : 0;
        
        // Deltas
        const deltaAC = conBIPV.totalACEnergy - sinBIPV.totalACEnergy;
        const deltaACpct = sinBIPV.totalACEnergy > 0 ? (deltaAC / sinBIPV.totalACEnergy) * 100 : 0;
        const deltaYield = yieldConBIPV - yieldSinBIPV;
        const deltaYieldPct = yieldSinBIPV > 0 ? (deltaYield / yieldSinBIPV) * 100 : 0;
        const deltaPR = conBIPV.performanceRatio - sinBIPV.performanceRatio;
        
        // Desglose de factores BIPV
        // iamPromedio es factor de retención (0.81 = 81% retenido, pérdida = 19%)
        const iamLoss = (1 - bipvData.iamPromedio) * 100;
        // soilingPromedio es la PÉRDIDA fraccional directa (0.038 = 3.8% de pérdida)
        const soilingLoss = bipvData.soilingPromedio * 100;
        // factorTermicoPromedio es factor multiplicador (0.95 = 5% pérdida)
        const thermalLoss = (1 - bipvData.factorTermicoPromedio) * 100;
        
        // Datos mensuales para gráfico
        const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        const chartData = conBIPV.monthlyData.map((m, i) => ({
          mes: monthNames[i],
          'Con BIPV': m.energyProduced,
          [`Baseline (${baselinePanel ? baselinePanel.id : 'Gen.'})`]: sinBIPV.monthlyData[i]?.energyProduced ?? 0,
          'BIPV (IAM+Soiling)': bipvData.produccionMensualKwh[i] ?? 0,
        }));
        const baselineBarKey = `Baseline (${baselinePanel ? baselinePanel.id : 'Gen.'})`;
        
        return (
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-start justify-between mb-1">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <Target size={16} className="text-teal-600" />
                Impacto de la Tecnología BIPV — Comparación con Baseline
              </h4>
              {/* Selector de panel baseline */}
              <div className="flex items-center gap-2">
                <label className="text-[10px] text-gray-500 whitespace-nowrap">Panel de referencia:</label>
                <select
                  className="text-xs border border-gray-300 rounded px-2 py-1 bg-white max-w-[200px] focus:ring-1 focus:ring-teal-400 focus:border-teal-400"
                  value={baselinePanelId || '__generic__'}
                  onChange={(e) => setBaselinePanelId(e.target.value === '__generic__' ? null : e.target.value)}
                >
                  <option value="__generic__">Genérico (400W, 20%, NOCT 45°C)</option>
                  {DEFAULT_PANEL_TECHNOLOGIES.filter(p => p.id !== bipvData.panelId).map(p => (
                    <option key={p.id} value={p.id}>
                      {p.id} · {p.name} ({p.pmax}W, {p.efficiencySTC}%)
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <p className="text-xs text-gray-500 mb-4">
              Cuantificación del impacto de usar <strong>{bipvData.technology}</strong> ({bipvData.generation}) vs <strong>{baselineName}</strong> en la misma área de {bipvData.areaM2.toFixed(1)} m² ({panelEstandar.quantity} paneles baseline)
            </p>
            
            {/* Tarjetas KPI comparativas */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-5">
              <div className="rounded-lg border border-teal-200 bg-teal-50 p-3 text-center">
                <p className="text-[9px] font-semibold text-teal-700 uppercase">Producción AC (BIPV)</p>
                <p className="text-lg font-bold text-teal-800">{conBIPV.totalACEnergy.toFixed(0)}</p>
                <p className="text-[9px] text-gray-500">kWh/año</p>
              </div>
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-center">
                <p className="text-[9px] font-semibold text-gray-600 uppercase">Producción AC (Estándar)</p>
                <p className="text-lg font-bold text-gray-700">{sinBIPV.totalACEnergy.toFixed(0)}</p>
                <p className="text-[9px] text-gray-500">kWh/año</p>
              </div>
              <div className={`rounded-lg border p-3 text-center ${deltaAC >= 0 ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                <p className="text-[9px] font-semibold text-gray-600 uppercase">Δ Producción</p>
                <p className={`text-lg font-bold ${deltaAC >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {deltaAC >= 0 ? '+' : ''}{deltaAC.toFixed(0)}
                </p>
                <p className={`text-[9px] font-bold ${deltaACpct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {deltaACpct >= 0 ? '+' : ''}{deltaACpct.toFixed(1)}%
                </p>
              </div>
              <div className="rounded-lg border border-violet-200 bg-violet-50 p-3 text-center">
                <p className="text-[9px] font-semibold text-violet-700 uppercase">Yield BIPV</p>
                <p className="text-lg font-bold text-violet-800">{yieldConBIPV.toFixed(0)}</p>
                <p className="text-[9px] text-gray-500">kWh/kWp</p>
              </div>
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-center">
                <p className="text-[9px] font-semibold text-gray-600 uppercase">Yield Estándar</p>
                <p className="text-lg font-bold text-gray-700">{yieldSinBIPV.toFixed(0)}</p>
                <p className="text-[9px] text-gray-500">kWh/kWp</p>
              </div>
              <div className={`rounded-lg border p-3 text-center ${deltaYield >= 0 ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                <p className="text-[9px] font-semibold text-gray-600 uppercase">Δ Yield</p>
                <p className={`text-lg font-bold ${deltaYield >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {deltaYield >= 0 ? '+' : ''}{deltaYield.toFixed(0)}
                </p>
                <p className={`text-[9px] font-bold ${deltaYieldPct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {deltaYieldPct >= 0 ? '+' : ''}{deltaYieldPct.toFixed(1)}%
                </p>
              </div>
            </div>
            
            {/* Tabla de desglose de pérdidas BIPV */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
              <div>
                <h5 className="text-xs font-semibold text-gray-700 mb-2">Desglose de Factores BIPV</h5>
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border border-gray-200 px-2 py-1 text-left">Factor</th>
                      <th className="border border-gray-200 px-2 py-1 text-center">Valor</th>
                      <th className="border border-gray-200 px-2 py-1 text-center">Pérdida</th>
                      <th className="border border-gray-200 px-2 py-1 text-center">Impacto</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-gray-200 px-2 py-1">IAM (Incidence Angle Modifier)</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono">{(bipvData.iamPromedio * 100).toFixed(1)}%</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono text-red-600">-{iamLoss.toFixed(1)}%</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono">{(conBIPV.totalACEnergy * iamLoss / 100).toFixed(0)} kWh</td>
                    </tr>
                    <tr className="bg-gray-50">
                      <td className="border border-gray-200 px-2 py-1">Soiling (Suciedad)</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono">{(bipvData.soilingPromedio * 100).toFixed(1)}%</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono text-red-600">-{soilingLoss.toFixed(1)}%</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono">{(conBIPV.totalACEnergy * soilingLoss / 100).toFixed(0)} kWh</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-200 px-2 py-1">Factor Térmico (k_bipv={bipvData.kBipv})</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono">{(bipvData.factorTermicoPromedio * 100).toFixed(1)}%</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono text-red-600">-{thermalLoss.toFixed(1)}%</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono">{(conBIPV.totalACEnergy * thermalLoss / 100).toFixed(0)} kWh</td>
                    </tr>
                    <tr className="bg-gray-50">
                      <td className="border border-gray-200 px-2 py-1">Transparencia (τ)</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono">{(bipvData.transparencia * 100).toFixed(0)}%</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono text-orange-600">-{(bipvData.transparencia * 100).toFixed(0)}%</td>
                      <td className="border border-gray-200 px-2 py-1 text-center text-[10px] text-gray-500">Reduce área activa</td>
                    </tr>
                    <tr className="bg-teal-50 font-semibold">
                      <td className="border border-gray-200 px-2 py-1">Eficiencia Ajustada Final</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono text-teal-700">{(bipvData.eficienciaAjustada * 100).toFixed(1)}%</td>
                      <td className="border border-gray-200 px-2 py-1 text-center" colSpan={2}>
                        <span className="text-[10px] text-gray-500">vs {panelEstandar.efficiency.toFixed(0)}% estándar</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <div>
                <h5 className="text-xs font-semibold text-gray-700 mb-2">Comparación de Métricas</h5>
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border border-gray-200 px-2 py-1 text-left">Métrica</th>
                      <th className="border border-gray-200 px-2 py-1 text-center">Con BIPV</th>
                      <th className="border border-gray-200 px-2 py-1 text-center">Estándar</th>
                      <th className="border border-gray-200 px-2 py-1 text-center">Δ</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-gray-200 px-2 py-1">Producción AC (kWh/año)</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono font-bold text-teal-700">{conBIPV.totalACEnergy.toFixed(0)}</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono">{sinBIPV.totalACEnergy.toFixed(0)}</td>
                      <td className={`border border-gray-200 px-2 py-1 text-center font-mono font-bold ${deltaAC >= 0 ? 'text-green-600' : 'text-red-600'}`}>{deltaAC >= 0 ? '+' : ''}{deltaAC.toFixed(0)}</td>
                    </tr>
                    <tr className="bg-gray-50">
                      <td className="border border-gray-200 px-2 py-1">Yield (kWh/kWp/año)</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono font-bold text-violet-700">{yieldConBIPV.toFixed(1)}</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono">{yieldSinBIPV.toFixed(1)}</td>
                      <td className={`border border-gray-200 px-2 py-1 text-center font-mono font-bold ${deltaYield >= 0 ? 'text-green-600' : 'text-red-600'}`}>{deltaYield >= 0 ? '+' : ''}{deltaYield.toFixed(1)}</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-200 px-2 py-1">PR (%)</td>
                      <td className={`border border-gray-200 px-2 py-1 text-center font-mono font-bold ${conBIPV.performanceRatio > 100 ? 'text-red-700 bg-red-50' : 'text-teal-700'}`}>
                        {conBIPV.performanceRatio.toFixed(1)}
                        {conBIPV.performanceRatio > 100 && <span className="text-[9px] block text-red-600">⚠️ Anormal</span>}
                      </td>
                      <td className={`border border-gray-200 px-2 py-1 text-center font-mono ${sinBIPV.performanceRatio > 100 ? 'text-red-700 bg-red-50' : ''}`}>
                        {sinBIPV.performanceRatio.toFixed(1)}
                        {sinBIPV.performanceRatio > 100 && <span className="text-[9px] block text-red-600">⚠️ Anormal</span>}
                      </td>
                      <td className={`border border-gray-200 px-2 py-1 text-center font-mono font-bold ${deltaPR >= 0 ? 'text-green-600' : 'text-red-600'}`}>{deltaPR >= 0 ? '+' : ''}{deltaPR.toFixed(1)}</td>
                    </tr>
                    {(conBIPV.performanceRatio > 100 || sinBIPV.performanceRatio > 100) && (
                    <tr>
                      <td colSpan={4} className="border border-gray-200 px-2 py-1.5 bg-red-50">
                        <p className="text-[9px] text-red-700 flex items-center gap-1">
                          <span className="font-bold">⚠️ PR &gt; 100%:</span> Verifique que la irradiancia POA corresponda a la orientación real (tilt/azimut) y que la capacidad nominal (kWp) sea correcta.
                        </p>
                      </td>
                    </tr>
                    )}
                    <tr className="bg-gray-50">
                      <td className="border border-gray-200 px-2 py-1">Capacidad Instalada (kWp)</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono font-bold text-teal-700">{kwpConBIPV.toFixed(2)}</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono">{kwpSinBIPV.toFixed(2)}</td>
                      <td className={`border border-gray-200 px-2 py-1 text-center font-mono font-bold ${kwpConBIPV - kwpSinBIPV >= 0 ? 'text-green-600' : 'text-red-600'}`}>{kwpConBIPV - kwpSinBIPV >= 0 ? '+' : ''}{(kwpConBIPV - kwpSinBIPV).toFixed(2)}</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-200 px-2 py-1">Factor de Capacidad (%)</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono font-bold text-teal-700">{conBIPV.capacityFactor.toFixed(1)}</td>
                      <td className="border border-gray-200 px-2 py-1 text-center font-mono">{sinBIPV.capacityFactor.toFixed(1)}</td>
                      <td className={`border border-gray-200 px-2 py-1 text-center font-mono font-bold ${conBIPV.capacityFactor - sinBIPV.capacityFactor >= 0 ? 'text-green-600' : 'text-red-600'}`}>{conBIPV.capacityFactor - sinBIPV.capacityFactor >= 0 ? '+' : ''}{(conBIPV.capacityFactor - sinBIPV.capacityFactor).toFixed(1)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            {/* Gráfico de barras mensual comparativo */}
            <h5 className="text-xs font-semibold text-gray-700 mb-2">Producción Mensual: Con BIPV vs Estándar vs IAM+Soiling</h5>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="mes" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} label={{ value: 'kWh', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }} />
                <Tooltip contentStyle={{ fontSize: 10, borderRadius: 8, border: '1px solid #e2e8f0' }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Bar dataKey="Con BIPV" fill="#0d9488" radius={[3, 3, 0, 0]} />
                <Bar dataKey={baselineBarKey} fill="#9ca3af" radius={[3, 3, 0, 0]} />
                <Bar dataKey="BIPV (IAM+Soiling)" fill="#06b6d4" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <p className="text-[9px] text-gray-400 mt-1 text-center">
              "Con BIPV" = Simulador con panel {bipvData.panelId || bipvData.technology} aplicado | "Baseline" = {baselineName} | "BIPV (IAM+Soiling)" = Motor IAM+Soiling directo
            </p>
          </div>
        );
      })()}

      {/* Integration Summary Banner */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-indigo-900 mb-2 flex items-center gap-2">
          <TrendingUp size={16} />
          Integración del Simulador
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div className={`flex items-center gap-2 p-2 rounded ${(use3DShading && facadeAnalysis3D) ? 'bg-purple-100 text-purple-800' : hasShadingData ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
            <Shield size={14} />
            <span>
              <strong>Sombreado:</strong> {(use3DShading && facadeAnalysis3D)
                ? `Modelo 3D: ${facadeAnalysis3D.facadeName} (FS=${(facadeAnalysis3D.annualFS * 100).toFixed(1)}%, Pérdida=${facadeAnalysis3D.annualShadingLoss.toFixed(1)}%)`
                : hasShadingData
                ? `Activo (FS prom. ${(avgShadingFactor * 100).toFixed(1)}%)`
                : 'Sin datos (FS=100%). Importa modelo 3D o ingresa puntos en Calculadora.'}
            </span>
          </div>
          <div className={`flex items-center gap-2 p-2 rounded ${fieldMeasurementsEnabled ? 'bg-teal-100 text-teal-800' : 'bg-green-100 text-green-800'}`}>
            <Sun size={14} />
            <span>
              {fieldMeasurementsEnabled
                ? <><strong>Campo:</strong> GHI={fieldGHI} W/m², T_amb={fieldTempAmbient}°C, T_cell={fieldCellTemp?.toFixed(1)}°C</>
                : <><strong>Meteorología:</strong> {weatherData.location.city || 'EPW'} (POA: {Math.round(poaData.reduce((a, d) => a + d.totalPOA, 0) / 12)} W/m² prom.)</>}
            </span>
          </div>
          <div className={`flex items-center gap-2 p-2 rounded ${optimizerResult ? 'bg-cyan-100 text-cyan-800' : 'bg-yellow-100 text-yellow-800'}`}>
            <Compass size={14} />
            <span>
              {optimizerResult
                ? <><strong>Optimizador:</strong> Tilt={optimizerResult.optimalTilt}°, Az={optimizerResult.optimalAzimuth}° ({optimizerResult.gainPercent > 0 ? '+' : ''}{optimizerResult.gainPercent}%)</>
                : <><strong>Orientación:</strong> Manual (Tilt={poaConfig?.tilt ?? installTilt}°, Az={poaConfig?.azimuth ?? installAzimuth}°). Usa el Optimizador.</>}
            </span>
          </div>
          <div className="flex items-center gap-2 p-2 rounded bg-green-100 text-green-800">
            <Thermometer size={14} />
            <span>
              <strong>Panel:</strong> {selectedTech.name.substring(0, 30)} ({panelPower}W, η={panelEfficiency}%)
            </span>
          </div>
        </div>
      </div>

      {/* ===== SELECTOR DE FACHADA DEL MODELO 3D ===== */}
      {modelFacades.length > 0 && onFacadeSelectFromSimulator && (
        <div className="bg-gradient-to-r from-purple-50 to-fuchsia-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <h3 className="text-sm font-semibold text-purple-900 flex items-center gap-2">
              <Building2 size={16} className="text-purple-600" />
              Selector de Superficie BIPV — Modelo 3D ({modelFacades.length} superficies)
            </h3>
            <label className="flex items-center gap-2 text-xs text-purple-700 font-semibold cursor-pointer">
              <input
                type="checkbox"
                checked={use3DShading}
                onChange={(e) => setUse3DShading(e.target.checked)}
                className="rounded border-purple-400 text-purple-600 focus:ring-purple-400 accent-purple-600"
              />
              Usar sombreado y fachada del modelo 3D
            </label>
          </div>
          {use3DShading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {modelFacades.map((facade, idx) => {
                const isActive = facadeAnalysis3D?.facadeIdx === idx;
                return (
                  <button
                    key={idx}
                    onClick={() => onFacadeSelectFromSimulator(idx)}
                    className={`flex items-center gap-2 p-2.5 rounded-lg border text-left transition-all text-xs ${
                      isActive
                        ? 'bg-purple-100 border-purple-400 ring-2 ring-purple-300 shadow-sm'
                        : 'bg-white/80 border-gray-200 hover:bg-purple-50 hover:border-purple-300'
                    }`}
                  >
                    <div
                      className="w-3.5 h-3.5 rounded-full flex-shrink-0 border border-gray-300"
                      style={{ backgroundColor: facade.color }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-gray-800 truncate">
                        {facade.name}
                        {isActive && <span className="ml-1 text-purple-600">✓</span>}
                      </div>
                      <div className="text-[10px] text-gray-500">
                        Az: {facade.azimuthNormal.toFixed(0)}° | Incl: {facade.tilt.toFixed(0)}° | {facade.area.toFixed(1)} m²
                      </div>
                      {isActive && facadeAnalysis3D && (
                        <div className="text-[10px] text-purple-700 font-medium mt-0.5">
                          FS={( facadeAnalysis3D.annualFS * 100).toFixed(1)}% | Pérdida={facadeAnalysis3D.annualShadingLoss.toFixed(1)}%
                        </div>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <p className="text-[10px] text-amber-600 font-medium">
              ⚠️ Se está aplicando la orientación manual del panel/POA y los factores de sombreado de la Calculadora.
            </p>
          )}
          {use3DShading && (
            <p className="text-[10px] text-purple-600 mt-2">
              Haz clic en una superficie para recalcular la producción BIPV desde esa perspectiva. Los FS mensuales se actualizan automáticamente.
            </p>
          )}
        </div>
      )}

      {/* ===== TABLA COMPARATIVA MULTI-FACHADA ===== */}
      {modelFacades.length > 0 && (
        <MultiFacadeComparison
          modelFacades={modelFacades}
          modelObstacles3D={modelObstacles3D}
          modelNorthOffset={modelNorthOffset}
          weatherData={weatherData}
          panelSpecs={panelSpecs}
          systemLosses={systemLosses}
          onFacadeSelect={onFacadeSelectFromSimulator}
          activeFacadeIdx={facadeAnalysis3D?.facadeIdx ?? null}
        />
      )}

      {/* ===== POA CONFIG & COMPONENTS BANNER ===== */}
      <div className="bg-gradient-to-r from-violet-50 to-purple-50 border border-violet-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-violet-900 mb-3 flex items-center gap-2">
          <Sun size={16} className="text-violet-600" />
          Configuración POA (Plano del Arreglo) — Modelo {poaConfig?.usePerez ? 'Perez (Anisotrópico)' : 'Liu-Jordan (Isotrópico)'}
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
          <div className="bg-white/70 rounded p-2">
            <label className="text-[10px] text-gray-500 block">Inclinación (°)</label>
            <p className="text-sm font-bold text-violet-800">{poaConfig?.tilt ?? installTilt}°</p>
            <p className="text-[9px] text-gray-400">Sincronizado con instalación</p>
          </div>
          <div className="bg-white/70 rounded p-2">
            <label className="text-[10px] text-gray-500 block">Azimut (°)</label>
            <p className="text-sm font-bold text-violet-800">{poaConfig?.azimuth ?? installAzimuth}°</p>
            <p className="text-[9px] text-gray-400">0°=Sur, 90°=Oeste</p>
          </div>
          <div className="bg-white/70 rounded p-2">
            <label className="text-[10px] text-gray-500 block">Albedo</label>
            <p className="text-sm font-bold text-violet-800">{poaConfig?.albedo ?? 0.2}</p>
            <p className="text-[9px] text-gray-400">Reflectancia del suelo</p>
          </div>
          <div className="bg-white/70 rounded p-2">
            <label className="text-[10px] text-gray-500 block">Fuente de datos</label>
            <p className="text-sm font-bold text-violet-800">
              {poaConfig?.source === 'prospector' ? 'Prospector PVGIS' : poaConfig?.source === 'field' ? 'Campo' : 'EPW Horario'}
            </p>
            <p className="text-[9px] text-gray-400">
              {poaConfig?.source === 'epw_hourly' ? 'Cálculo horario real' : poaConfig?.source === 'prospector' ? 'GHI sintético' : 'Medición directa'}
            </p>
          </div>
        </div>

        {/* Desglose de componentes POA mensual */}
        <div className="mt-2">
          <p className="text-[10px] text-violet-700 font-medium mb-1">Desglose Componentes POA (W/m² promedio mensual)</p>
          <div className="overflow-x-auto">
            <table className="w-full text-[10px] border-collapse">
              <thead>
                <tr className="bg-violet-100">
                  <th className="px-1 py-0.5 text-left text-violet-800">Mes</th>
                  <th className="px-1 py-0.5 text-right text-orange-700">Directa</th>
                  <th className="px-1 py-0.5 text-right text-blue-700">Difusa</th>
                  <th className="px-1 py-0.5 text-right text-green-700">Reflejada</th>
                  <th className="px-1 py-0.5 text-right text-violet-800 font-bold">Total POA</th>
                  <th className="px-1 py-0.5 text-right text-red-600">T. Amb</th>
                  <th className="px-1 py-0.5 text-right text-cyan-700">Viento</th>
                </tr>
              </thead>
              <tbody>
                {poaData.map((d, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-white/50' : 'bg-violet-50/30'}>
                    <td className="px-1 py-0.5 font-medium">{d.month}</td>
                    <td className="px-1 py-0.5 text-right text-orange-700">{d.directPOA}</td>
                    <td className="px-1 py-0.5 text-right text-blue-700">{d.diffusePOA}</td>
                    <td className="px-1 py-0.5 text-right text-green-700">{d.reflectedPOA}</td>
                    <td className="px-1 py-0.5 text-right font-bold text-violet-800">{d.totalPOA}</td>
                    <td className="px-1 py-0.5 text-right text-red-600">{d.avgTemp}°C</td>
                    <td className="px-1 py-0.5 text-right text-cyan-700">{d.avgWindSpeed} m/s</td>
                  </tr>
                ))}
                <tr className="bg-violet-100 font-bold">
                  <td className="px-1 py-0.5">Promedio</td>
                  <td className="px-1 py-0.5 text-right text-orange-700">{Math.round(poaData.reduce((a, d) => a + d.directPOA, 0) / 12)}</td>
                  <td className="px-1 py-0.5 text-right text-blue-700">{Math.round(poaData.reduce((a, d) => a + d.diffusePOA, 0) / 12)}</td>
                  <td className="px-1 py-0.5 text-right text-green-700">{Math.round(poaData.reduce((a, d) => a + d.reflectedPOA, 0) / 12)}</td>
                  <td className="px-1 py-0.5 text-right text-violet-800">{Math.round(poaData.reduce((a, d) => a + d.totalPOA, 0) / 12)}</td>
                  <td className="px-1 py-0.5 text-right text-red-600">{(poaData.reduce((a, d) => a + d.avgTemp, 0) / 12).toFixed(1)}°C</td>
                  <td className="px-1 py-0.5 text-right text-cyan-700">{(poaData.reduce((a, d) => a + d.avgWindSpeed, 0) / 12).toFixed(1)} m/s</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-[9px] text-gray-400 mt-1">
            * POA calculado con modelo {poaConfig?.usePerez ? 'Perez (anisotrópico, incluye circunsolar y horizonte)' : 'Liu-Jordan (isotrópico)'} usando ángulos solares horarios reales del EPW.
            Viento real del EPW enfría paneles (factor Sandia). T_cell usa NOCT y eficiencia real del panel seleccionado.
          </p>
        </div>
      </div>

      {/* ===== FIELD MEASUREMENTS SECTION ===== */}
      <div className="bg-gradient-to-r from-teal-50 to-cyan-50 border-2 border-teal-300 rounded-lg overflow-hidden">
        <button
          onClick={() => {
            if (!fieldMeasurementsEnabled) {
              setFieldMeasurementsEnabled(true);
              setFieldMeasurementsExpanded(true);
            } else {
              setFieldMeasurementsExpanded(!fieldMeasurementsExpanded);
            }
          }}
          className="w-full flex items-center justify-between p-4 hover:bg-teal-100/50 transition-colors"
        >
          <h3 className="text-sm font-semibold text-teal-900 flex items-center gap-2">
            <Pencil size={16} className="text-teal-600" />
            Mediciones de Campo (Valores Reales BIPV)
          </h3>
          <div className="flex items-center gap-3">
            {fieldMeasurementsEnabled && (
              <span className="text-xs text-teal-700 bg-teal-200 px-2 py-0.5 rounded font-medium">
                Activo: GHI={fieldGHI} W/m², T_amb={fieldTempAmbient}°C
              </span>
            )}
            <label className="flex items-center gap-2 text-xs cursor-pointer" onClick={(e) => e.stopPropagation()}>
              <input
                type="checkbox"
                checked={fieldMeasurementsEnabled}
                onChange={(e) => {
                  setFieldMeasurementsEnabled(e.target.checked);
                  if (e.target.checked) setFieldMeasurementsExpanded(true);
                }}
                className="accent-teal-600"
              />
              <span className="text-teal-700 font-medium">Usar datos de campo</span>
            </label>
            <span className={`text-xs transition-transform ${fieldMeasurementsExpanded && fieldMeasurementsEnabled ? 'rotate-180' : ''}`}>▼</span>
          </div>
        </button>

        {fieldMeasurementsEnabled && fieldMeasurementsExpanded && (
          <div className="px-4 pb-4 space-y-4">
            {/* Coordenadas EPW de referencia */}
            <div className="flex items-center gap-2 text-xs bg-white/70 rounded p-2 border border-teal-100">
              <MapPin size={14} className="text-teal-600" />
              <span className="text-gray-600">
                <strong>Coordenadas EPW:</strong> {weatherData.location.latitude.toFixed(4)}°, {weatherData.location.longitude.toFixed(4)}°
                {weatherData.location.city && ` — ${weatherData.location.city}`}
                {weatherData.location.state && `, ${weatherData.location.state}`}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Left: Input Fields */}
              <div className="space-y-3">
                {/* GHI Field */}
                <div className="bg-white rounded-lg p-3 border border-teal-100">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    <Sun size={12} className="inline mr-1 text-amber-500" />
                    GHI - Irradiancia Global Horizontal (W/m²)
                  </label>
                  <input
                    type="number"
                    value={fieldGHI}
                    onChange={(e) => setFieldGHI(Math.max(0, Math.min(1500, parseFloat(e.target.value) || 0)))}
                    className="w-full border border-teal-200 rounded px-3 py-2 text-lg font-mono font-bold text-teal-900 focus:ring-2 focus:ring-teal-400 focus:border-teal-400"
                    min={0}
                    max={1500}
                    step={10}
                  />
                  <div className="flex gap-1 mt-2">
                    {[200, 400, 600, 800, 1000, 1200].map(v => (
                      <button
                        key={v}
                        onClick={() => setFieldGHI(v)}
                        className={`px-2 py-0.5 text-[10px] rounded border transition-colors ${
                          fieldGHI === v ? 'bg-teal-600 text-white border-teal-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-teal-50'
                        }`}
                      >
                        {v}
                      </button>
                    ))}
                  </div>
                  <p className="text-[10px] text-gray-400 mt-1">Medida con piranómetro o solarimetro en campo</p>
                </div>

                {/* T_amb Field */}
                <div className="bg-white rounded-lg p-3 border border-teal-100">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    <Thermometer size={12} className="inline mr-1 text-blue-500" />
                    Temperatura Ambiente en Campo (°C)
                  </label>
                  <input
                    type="number"
                    value={fieldTempAmbient}
                    onChange={(e) => setFieldTempAmbient(parseFloat(e.target.value) || 0)}
                    className="w-full border border-teal-200 rounded px-3 py-2 text-lg font-mono font-bold text-teal-900 focus:ring-2 focus:ring-teal-400 focus:border-teal-400"
                    min={-10}
                    max={60}
                    step={0.5}
                  />
                  <p className="text-[10px] text-gray-400 mt-1">Medida con termómetro a la sombra, cerca del panel</p>
                </div>

                {/* T_cell Field (optional) */}
                <div className="bg-white rounded-lg p-3 border border-teal-100">
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-medium text-gray-700">
                      <Thermometer size={12} className="inline mr-1 text-red-500" />
                      Temperatura de Celda en Campo (°C)
                    </label>
                    <label className="flex items-center gap-1 text-[10px] cursor-pointer">
                      <input
                        type="checkbox"
                        checked={useManualCellTemp}
                        onChange={(e) => {
                          setUseManualCellTemp(e.target.checked);
                          if (e.target.checked && fieldTempCell === null) {
                            // Pre-llenar con T_cell calculada
                            setFieldTempCell(Math.round(mulcueCellTemp(fieldTempAmbient, noct, fieldGHI) * 10) / 10);
                          }
                        }}
                        className="accent-red-500"
                      />
                      <span className="text-gray-600">Ingresar manualmente</span>
                    </label>
                  </div>
                  {useManualCellTemp ? (
                    <input
                      type="number"
                      value={fieldTempCell ?? ''}
                      onChange={(e) => setFieldTempCell(parseFloat(e.target.value) || 0)}
                      className="w-full border border-red-200 rounded px-3 py-2 text-lg font-mono font-bold text-red-900 focus:ring-2 focus:ring-red-400 focus:border-red-400"
                      min={-10}
                      max={100}
                      step={0.5}
                    />
                  ) : (
                    <div className="bg-gray-50 rounded px-3 py-2 text-lg font-mono font-bold text-gray-600">
                      {fieldCellTemp !== null ? `${fieldCellTemp.toFixed(1)}°C` : '—'}
                      <span className="text-[10px] font-normal text-gray-400 ml-2">(calculada con NOCT={noct}°C)</span>
                    </div>
                  )}
                  <p className="text-[10px] text-gray-400 mt-1">
                    {useManualCellTemp
                      ? 'Medida con termopar o cámara termográfica en la parte posterior del panel'
                      : `Auto-calculada: T_cell = T_amb + (NOCT-20) × (G/800) = ${fieldTempAmbient} + (${noct}-20) × (${fieldGHI}/800)`}
                  </p>
                </div>

                {/* Label field */}
                <div className="bg-white rounded-lg p-3 border border-teal-100">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    <Clock size={12} className="inline mr-1 text-teal-500" />
                    Etiqueta / Nota (opcional)
                  </label>
                  <input
                    type="text"
                    value={fieldLabel}
                    onChange={(e) => setFieldLabel(e.target.value)}
                    placeholder="Ej: mañana nublado, mediodía despejado..."
                    className="w-full border border-teal-200 rounded px-3 py-2 text-sm text-teal-900 focus:ring-2 focus:ring-teal-400 focus:border-teal-400"
                    maxLength={60}
                  />
                </div>

                {/* Save measurement button */}
                <button
                  onClick={() => {
                    if (fieldCellTemp === null || fieldPExp === null || fieldPR === null || fieldTempLoss === null) return;
                    measurementHistory.addRecord({
                      label: fieldLabel || `Medición ${measurementHistory.count + 1}`,
                      ghi: fieldGHI,
                      tempAmbient: fieldTempAmbient,
                      tempCell: fieldCellTemp,
                      tempCellManual: useManualCellTemp,
                      pExp: fieldPExp,
                      pExpTotal: (fieldPExp * panelQuantity) / 1000,
                      prMulcue: fieldPR.prCorrected,
                      tempLoss: fieldTempLoss,
                      panelName: selectedTech.name,
                      panelPower: panelPower,
                      panelQuantity: panelQuantity,
                      noct: noct,
                      tempCoeff: selectedTech.tempCoeffPmax,
                      latitude: weatherData.location.latitude,
                      longitude: weatherData.location.longitude,
                      cityName: weatherData.location.city || 'Desconocida',
                    });
                    setFieldLabel('');
                  }}
                  disabled={fieldCellTemp === null || fieldPExp === null}
                  className="w-full py-2.5 rounded-lg text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 shadow-sm"
                >
                  <Save size={14} />
                  Guardar Medición ({measurementHistory.count} guardadas)
                </button>

                {/* Reset button */}
                <button
                  onClick={() => {
                    setFieldMeasurementsEnabled(false);
                    setUseManualCellTemp(false);
                    setFieldTempCell(null);
                    setFieldLabel('');
                  }}
                  className="w-full py-2 rounded-lg text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
                >
                  <RotateCw size={12} />
                  Desactivar mediciones de campo (volver a datos EPW)
                </button>
              </div>

              {/* Right: Calculated Results */}
              <div className="space-y-3">
                {/* P_exp Card */}
                <div className="bg-teal-600 text-white rounded-lg p-4">
                  <p className="text-xs opacity-80 mb-1">P_exp (Mulcue-Llanos) por módulo</p>
                  <p className="text-3xl font-mono font-bold">
                    {fieldPExp !== null ? fieldPExp.toFixed(1) : '—'} <span className="text-sm font-normal">W</span>
                  </p>
                  <p className="text-xs opacity-80 mt-1">
                    P_nom STC = {panelPower}W | Δ = {fieldPExp !== null ? ((fieldPExp - panelPower) / panelPower * 100).toFixed(1) : '—'}%
                  </p>
                  <p className="text-[10px] opacity-70 mt-2">
                    P_exp = P_nom × [1 + γ(T_c − 21)] × (G/1000)
                  </p>
                </div>

                {/* Derived metrics grid */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-white rounded-lg p-3 border border-teal-100 text-center">
                    <p className="text-[10px] text-gray-500">T. Celda</p>
                    <p className="text-lg font-mono font-bold text-red-700">
                      {fieldCellTemp !== null ? fieldCellTemp.toFixed(1) : '—'}°C
                    </p>
                    <p className="text-[10px] text-gray-400">{useManualCellTemp ? 'medida' : 'NOCT'}</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-teal-100 text-center">
                    <p className="text-[10px] text-gray-500">Pérdida por T°</p>
                    <p className="text-lg font-mono font-bold text-orange-700">
                      {fieldTempLoss !== null ? ((1 - fieldTempLoss) * 100).toFixed(1) : '—'}%
                    </p>
                    <p className="text-[10px] text-gray-400">vs STC 25°C</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-teal-100 text-center">
                    <p className="text-[10px] text-gray-500">PR Mulcue-Llanos</p>
                    <p className="text-lg font-mono font-bold text-blue-700">
                      {fieldPR !== null ? (fieldPR.prCorrected * 100).toFixed(1) : '—'}%
                    </p>
                    <p className="text-[10px] text-gray-400">{fieldPR?.interpretation || ''}</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-teal-100 text-center">
                    <p className="text-[10px] text-gray-500">P_exp Total</p>
                    <p className="text-lg font-mono font-bold text-teal-700">
                      {fieldPExp !== null ? ((fieldPExp * panelQuantity) / 1000).toFixed(2) : '—'}
                    </p>
                    <p className="text-[10px] text-gray-400">kWp ({panelQuantity} módulos)</p>
                  </div>
                </div>

                {/* Info box */}
                <div className="bg-amber-50 rounded-lg p-3 border border-amber-200">
                  <div className="flex items-start gap-2">
                    <AlertTriangle size={14} className="text-amber-600 mt-0.5 flex-shrink-0" />
                    <div className="text-[10px] text-amber-800 space-y-1">
                      <p><strong>Modo Campo Activo:</strong> Los cálculos de producción usan GHI={fieldGHI} W/m² y T_amb={fieldTempAmbient}°C como valores constantes para todos los meses.</p>
                      <p>Los <strong>factores de sombreado (FS)</strong> de la Calculadora se siguen aplicando normalmente.</p>
                      <p>Las <strong>ecuaciones BIPV</strong> (P_exp, PR, pérdidas del sistema) se calculan con los valores de campo.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ===== ALERTA DE RENDIMIENTO ===== */}
            {fieldPerformanceAlert && (
              <div className="border-t border-teal-200 pt-4">
                <PerformanceAlertPanel alert={fieldPerformanceAlert} />
              </div>
            )}

            {/* ===== HISTORIAL DE MEDICIONES ===== */}
            <div className="border-t border-teal-200 pt-4">
              <FieldMeasurementHistory
                records={measurementHistory.records}
                onRemove={measurementHistory.removeRecord}
                onClearAll={measurementHistory.clearAll}
                onLoadRecord={(record) => {
                  setFieldGHI(record.ghi);
                  setFieldTempAmbient(record.tempAmbient);
                  setUseManualCellTemp(record.tempCellManual);
                  if (record.tempCellManual) {
                    setFieldTempCell(record.tempCell);
                  } else {
                    setFieldTempCell(null);
                  }
                  setFieldLabel(record.label);
                }}
                onExportCSV={measurementHistory.exportCSV}
              />
            </div>
          </div>
        )}
      </div>

      {/* Panel Technology Selector */}
      <PanelTechSelector
        selectedTech={selectedTech}
        onSelectTech={handleSelectTech}
        yearsFromInstall={yearsFromInstall}
        onYearsChange={setYearsFromInstall}
        selectedRegion={activeRegion}
        onRegionChange={(r) => setRegionOverride(r)}
        detectedRegionInfo={detectedRegion}
        savedPanels={savedPanelsTech}
        onSavePanel={handleSavePanelPersist}
        onDeletePanel={handleDeletePanelPersist}
      />

      {/* ===== AREA CALCULATOR SECTION ===== */}
      <div className="bg-gradient-to-r from-violet-50 to-purple-50 border border-violet-200 rounded-lg overflow-hidden">
        <button
          onClick={() => setAreaCalcExpanded(!areaCalcExpanded)}
          className="w-full flex items-center justify-between p-4 hover:bg-violet-100/50 transition-colors"
        >
          <h3 className="text-sm font-semibold text-violet-900 flex items-center gap-2">
            <LayoutGrid size={16} />
            Calculadora de Área y Número de Paneles
          </h3>
          <div className="flex items-center gap-3">
            <span className="text-xs text-violet-600 bg-violet-100 px-2 py-0.5 rounded">
              {areaCalcResult.totalPanels} paneles = {areaCalcResult.totalPowerKWp.toFixed(1)} kWp
            </span>
            <span className={`text-xs transition-transform ${areaCalcExpanded ? 'rotate-180' : ''}`}>▼</span>
          </div>
        </button>

        <div style={{ display: areaCalcExpanded ? 'block' : 'none' }}>
          <div className="px-4 pb-4 space-y-4">
            {/* Input Mode Toggle */}
            <div className="flex items-center gap-4 text-xs">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={!useRectangular}
                  onChange={() => setUseRectangular(false)}
                  className="accent-violet-600"
                />
                <span className="text-gray-700">Área total (m²)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={useRectangular}
                  onChange={() => setUseRectangular(true)}
                  className="accent-violet-600"
                />
                <span className="text-gray-700">Dimensiones rectangulares (ancho × largo)</span>
              </label>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Left: Input Parameters */}
              <div className="space-y-3">
                {/* Area Input */}
                <div style={{ display: useRectangular ? 'none' : 'block' }}>
                  <div className="bg-white rounded-lg p-3 border border-violet-100">
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      <Maximize2 size={12} className="inline mr-1" />
                      Área disponible (m²)
                    </label>
                    <input
                      type="number"
                      value={availableArea}
                      onChange={(e) => setAvailableArea(Math.max(0, parseFloat(e.target.value) || 0))}
                      className="w-full border border-violet-200 rounded px-3 py-2 text-lg font-mono font-bold text-violet-900 focus:ring-2 focus:ring-violet-400 focus:border-violet-400"
                      min={0}
                      step={1}
                    />
                    <div className="flex gap-1 mt-2">
                      {[25, 50, 100, 200, 500, 1000].map(v => (
                        <button
                          key={v}
                          onClick={() => setAvailableArea(v)}
                          className={`px-2 py-0.5 text-[10px] rounded border transition-colors ${
                            availableArea === v ? 'bg-violet-600 text-white border-violet-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-violet-50'
                          }`}
                        >
                          {v}m²
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Rectangular Input */}
                <div style={{ display: useRectangular ? 'block' : 'none' }}>
                  <div className="bg-white rounded-lg p-3 border border-violet-100">
                    <label className="block text-xs font-medium text-gray-700 mb-2">
                      <Maximize2 size={12} className="inline mr-1" />
                      Dimensiones del área disponible
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[10px] text-gray-500 mb-1">Ancho (m)</label>
                        <input
                          type="number"
                          value={availableWidth}
                          onChange={(e) => setAvailableWidth(Math.max(0, parseFloat(e.target.value) || 0))}
                          className="w-full border border-violet-200 rounded px-2 py-1.5 text-sm font-mono font-bold text-violet-900 focus:ring-2 focus:ring-violet-400"
                          min={0}
                          step={0.1}
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] text-gray-500 mb-1">Largo (m)</label>
                        <input
                          type="number"
                          value={availableLength}
                          onChange={(e) => setAvailableLength(Math.max(0, parseFloat(e.target.value) || 0))}
                          className="w-full border border-violet-200 rounded px-2 py-1.5 text-sm font-mono font-bold text-violet-900 focus:ring-2 focus:ring-violet-400"
                          min={0}
                          step={0.1}
                        />
                      </div>
                    </div>
                    <p className="text-[10px] text-gray-400 mt-1">
                      Área total: {(availableWidth * availableLength).toFixed(1)} m²
                    </p>
                  </div>
                </div>

                {/* Orientation */}
                <div className="bg-white rounded-lg p-3 border border-violet-100">
                  <label className="block text-xs font-medium text-gray-700 mb-2">
                    <RotateCcw size={12} className="inline mr-1" />
                    Orientación del panel
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPanelOrientation('landscape')}
                      className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded border text-xs transition-colors ${
                        panelOrientation === 'landscape'
                          ? 'bg-violet-600 text-white border-violet-600'
                          : 'bg-white text-gray-600 border-gray-200 hover:bg-violet-50'
                      }`}
                    >
                      <span className="inline-block w-6 h-4 border-2 border-current rounded-sm"></span>
                      Horizontal
                    </button>
                    <button
                      onClick={() => setPanelOrientation('portrait')}
                      className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded border text-xs transition-colors ${
                        panelOrientation === 'portrait'
                          ? 'bg-violet-600 text-white border-violet-600'
                          : 'bg-white text-gray-600 border-gray-200 hover:bg-violet-50'
                      }`}
                    >
                      <span className="inline-block w-4 h-6 border-2 border-current rounded-sm"></span>
                      Vertical
                    </button>
                  </div>
                  <p className="text-[10px] text-gray-400 mt-1">
                    Panel: {(areaCalcResult.panelW * 1000).toFixed(0)} × {(areaCalcResult.panelH * 1000).toFixed(0)} mm
                    ({panelOrientation === 'landscape' ? 'largo × ancho' : 'ancho × largo'})
                  </p>
                </div>

                {/* Spacing Factor */}
                <div className="bg-white rounded-lg p-3 border border-violet-100">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Factor de separación: ×{spacingFactor.toFixed(2)}
                  </label>
                  <Slider
                    value={[spacingFactor]}
                    onValueChange={(v) => setSpacingFactor(v[0])}
                    min={1.0}
                    max={2.0}
                    step={0.05}
                  />
                  <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                    <span>×1.0 (sin separación)</span>
                    <span>×1.5 (50% extra)</span>
                    <span>×2.0 (doble)</span>
                  </div>
                  <p className="text-[10px] text-gray-500 mt-1">
                    Espacio efectivo por panel: {areaCalcResult.effectiveW.toFixed(2)}m × {areaCalcResult.effectiveH.toFixed(2)}m = {areaCalcResult.singlePanelAreaWithSpacing.toFixed(2)} m²
                  </p>
                </div>
              </div>

              {/* Right: Results */}
              <div className="space-y-3">
                {/* Main Result */}
                <div className="bg-violet-600 text-white rounded-lg p-4">
                  <p className="text-xs opacity-80 mb-1">Paneles que caben en el área</p>
                  <p className="text-4xl font-mono font-bold">{areaCalcResult.totalPanels}</p>
                  <p className="text-sm opacity-90 mt-1">paneles {selectedTech.hiitioId || selectedTech.id}</p>
                  {useRectangular && (
                    <p className="text-xs opacity-80 mt-1">
                      Distribución: {areaCalcResult.panelsInRow} columnas × {areaCalcResult.panelsInCol} filas
                    </p>
                  )}
                </div>

                {/* Detail Metrics */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-white rounded-lg p-3 border border-violet-100 text-center">
                    <p className="text-[10px] text-gray-500">Potencia Total</p>
                    <p className="text-lg font-mono font-bold text-violet-700">{areaCalcResult.totalPowerKWp.toFixed(1)}</p>
                    <p className="text-[10px] text-gray-500">kWp</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-violet-100 text-center">
                    <p className="text-[10px] text-gray-500">Cobertura</p>
                    <p className="text-lg font-mono font-bold text-violet-700">{areaCalcResult.coverageRatio.toFixed(1)}</p>
                    <p className="text-[10px] text-gray-500">% del área</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-violet-100 text-center">
                    <p className="text-[10px] text-gray-500">Área Paneles</p>
                    <p className="text-lg font-mono font-bold text-violet-700">{areaCalcResult.totalPanelArea.toFixed(1)}</p>
                    <p className="text-[10px] text-gray-500">m² netos</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-violet-100 text-center">
                    <p className="text-[10px] text-gray-500">Área Ocupada</p>
                    <p className="text-lg font-mono font-bold text-violet-700">{areaCalcResult.totalOccupiedArea.toFixed(1)}</p>
                    <p className="text-[10px] text-gray-500">m² con separación</p>
                  </div>
                </div>

                {/* Panel Layout Visualization (mini grid) */}
                <div className="bg-white rounded-lg p-3 border border-violet-100">
                  <p className="text-[10px] text-gray-500 mb-2">Vista previa de distribución</p>
                  <div className="flex flex-wrap gap-[1px] max-h-24 overflow-hidden">
                    {Array.from({ length: Math.min(areaCalcResult.totalPanels, 120) }).map((_, i) => (
                      <div
                        key={i}
                        className="bg-violet-400 rounded-[1px]"
                        style={{
                          width: panelOrientation === 'landscape' ? '8px' : '5px',
                          height: panelOrientation === 'landscape' ? '5px' : '8px',
                        }}
                      />
                    ))}
                    {areaCalcResult.totalPanels > 120 && (
                      <span className="text-[9px] text-gray-400 ml-1">+{areaCalcResult.totalPanels - 120} más</span>
                    )}
                  </div>
                </div>

                {/* Apply Button */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-xs cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoSyncQuantity}
                      onChange={(e) => {
                        setAutoSyncQuantity(e.target.checked);
                        if (e.target.checked) setPanelQuantity(areaCalcResult.totalPanels);
                      }}
                      className="accent-violet-600"
                    />
                    <span className="text-gray-600">Sincronizar automáticamente con el simulador</span>
                  </label>
                  <button
                    onClick={applyAreaCalculation}
                    className={`w-full py-2.5 rounded-lg font-semibold text-sm transition-all ${
                      panelQuantity === areaCalcResult.totalPanels
                        ? 'bg-green-100 text-green-700 border border-green-300'
                        : 'bg-violet-600 text-white hover:bg-violet-700 shadow-lg shadow-violet-200'
                    }`}
                  >
                    {autoSyncQuantity && panelQuantity === areaCalcResult.totalPanels
                      ? `\u2713 Sincronizado: ${areaCalcResult.totalPanels} paneles`
                      : panelQuantity === areaCalcResult.totalPanels
                        ? `\u2713 Aplicado: ${areaCalcResult.totalPanels} paneles en simulador`
                        : `Aplicar ${areaCalcResult.totalPanels} paneles al simulador`}
                  </button>
                </div>
              </div>
            </div>

            {/* Summary Table */}
            <div className="bg-white rounded-lg border border-violet-100 overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-violet-50">
                    <th className="text-left px-3 py-2 text-violet-700">Parámetro</th>
                    <th className="text-right px-3 py-2 text-violet-700">Valor</th>
                    <th className="text-left px-3 py-2 text-violet-700">Parámetro</th>
                    <th className="text-right px-3 py-2 text-violet-700">Valor</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-violet-50">
                    <td className="px-3 py-1.5 text-gray-600">Panel seleccionado</td>
                    <td className="px-3 py-1.5 text-right font-mono text-gray-900">{selectedTech.hiitioId || selectedTech.id}</td>
                    <td className="px-3 py-1.5 text-gray-600">Potencia por panel</td>
                    <td className="px-3 py-1.5 text-right font-mono text-gray-900">{selectedTech.pmax}W</td>
                  </tr>
                  <tr className="border-t border-violet-50">
                    <td className="px-3 py-1.5 text-gray-600">Dimensiones panel</td>
                    <td className="px-3 py-1.5 text-right font-mono text-gray-900">{selectedTech.lengthMm}×{selectedTech.widthMm}mm</td>
                    <td className="px-3 py-1.5 text-gray-600">Área por panel</td>
                    <td className="px-3 py-1.5 text-right font-mono text-gray-900">{areaCalcResult.singlePanelAreaNet.toFixed(3)} m²</td>
                  </tr>
                  <tr className="border-t border-violet-50">
                    <td className="px-3 py-1.5 text-gray-600">Área disponible</td>
                    <td className="px-3 py-1.5 text-right font-mono text-gray-900">{areaCalcResult.effectiveAreaUsed.toFixed(1)} m²</td>
                    <td className="px-3 py-1.5 text-gray-600">Orientación</td>
                    <td className="px-3 py-1.5 text-right font-mono text-gray-900">{panelOrientation === 'landscape' ? 'Horizontal' : 'Vertical'}</td>
                  </tr>
                  <tr className="border-t border-violet-50">
                    <td className="px-3 py-1.5 text-gray-600">Factor separación</td>
                    <td className="px-3 py-1.5 text-right font-mono text-gray-900">×{spacingFactor.toFixed(2)}</td>
                    <td className="px-3 py-1.5 text-gray-600">Espacio por panel</td>
                    <td className="px-3 py-1.5 text-right font-mono text-gray-900">{areaCalcResult.singlePanelAreaWithSpacing.toFixed(3)} m²</td>
                  </tr>
                  <tr className="border-t border-violet-100 bg-violet-50 font-semibold">
                    <td className="px-3 py-2 text-violet-800">Total paneles</td>
                    <td className="px-3 py-2 text-right font-mono text-violet-900">{areaCalcResult.totalPanels}</td>
                    <td className="px-3 py-2 text-violet-800">Potencia total</td>
                    <td className="px-3 py-2 text-right font-mono text-violet-900">{areaCalcResult.totalPowerKWp.toFixed(2)} kWp</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Installation Configuration */}
      <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Building2 size={20} className="text-blue-600" />
            Configuración de Instalación
          </h3>
          <button
            onClick={() => setInstallConfigExpanded(!installConfigExpanded)}
            className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            {installConfigExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {installConfigExpanded ? 'Colapsar' : 'Expandir'}
          </button>
        </div>

        {/* Selected config summary - always visible */}
        <div className="flex items-center gap-3 mb-3 bg-white rounded-lg p-3 border border-blue-100">
          <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
            {INSTALL_ICONS[selectedInstallation.id]}
          </div>
          <div className="flex-1">
            <p className="font-semibold text-gray-900 text-sm">{selectedInstallation.icon} {selectedInstallation.name}</p>
            <p className="text-xs text-gray-500">{selectedInstallation.description.substring(0, 80)}...</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">Inclinación</p>
            <p className="font-mono font-bold text-blue-700">{installTilt}°</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">Azimut</p>
            <p className="font-mono font-bold text-blue-700">{installAzimuth}°</p>
          </div>
        </div>

        <div style={{ display: installConfigExpanded ? 'block' : 'none' }}>
          {/* Installation type grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 mb-4">
            {INSTALLATION_CONFIGS.map(config => (
              <button
                key={config.id}
                onClick={() => applyInstallationConfig(config)}
                className={`relative p-3 rounded-lg border-2 transition-all text-left ${
                  selectedInstallation.id === config.id
                    ? 'border-blue-500 bg-blue-50 shadow-md shadow-blue-100'
                    : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/50'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{config.icon}</span>
                  {selectedInstallation.id === config.id && (
                    <span className="absolute top-1 right-1 w-2 h-2 bg-blue-500 rounded-full" />
                  )}
                </div>
                <p className="text-xs font-semibold text-gray-900 leading-tight">{config.name}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">{config.defaultTilt}° inclinación</p>
              </button>
            ))}
          </div>

          {/* BIPV Imported badge */}
          {selectedInstallation.id === 'bipv_imported' && bipvData && (
            <div className="mb-4 bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-300 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <span className="text-lg">🔬</span>
                <div>
                  <p className="text-sm font-bold text-purple-900">Ángulos definidos por Modelo 3D (Optimizador BIPV)</p>
                  <p className="text-xs text-purple-700">
                    Inclinación: <strong>{installTilt}°</strong> | Azimut: <strong>{installAzimuth}°</strong> | 
                    Superficie: <strong>{bipvData.surfaceName || 'N/A'}</strong>
                  </p>
                  <p className="text-[10px] text-purple-500 mt-0.5">
                    ⚠️ Los ángulos están bloqueados. Para cambiarlos, usa "← Volver al BIPV" y selecciona otra superficie.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Tilt and Azimuth controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className={`bg-white rounded-lg p-4 border ${selectedInstallation.id === 'bipv_imported' ? 'border-purple-200 opacity-75' : 'border-blue-100'}`}>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Inclinación: {installTilt}°
                <span className="text-xs text-gray-400 ml-2">
                  {selectedInstallation.id === 'bipv_imported' 
                    ? '(🔒 Definido por modelo 3D)' 
                    : `(Rango: ${selectedInstallation.tiltRange[0]}° - ${selectedInstallation.tiltRange[1]}°)`}
                </span>
              </label>
              <Slider
                value={[installTilt]}
                onValueChange={(v) => setInstallTilt(v[0])}
                min={selectedInstallation.tiltRange[0]}
                max={selectedInstallation.tiltRange[1]}
                step={1}
                disabled={selectedInstallation.id === 'bipv_imported'}
              />
              <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                <span>{selectedInstallation.tiltRange[0]}°</span>
                <span>{selectedInstallation.tiltRange[1]}°</span>
              </div>
            </div>

            <div className={`bg-white rounded-lg p-4 border ${selectedInstallation.id === 'bipv_imported' ? 'border-purple-200 opacity-75' : 'border-blue-100'}`}>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Azimut: {installAzimuth}°
                {selectedInstallation.id === 'bipv_imported' ? (
                  <span className="text-xs text-purple-600 ml-2">(🔒 Definido por modelo 3D)</span>
                ) : selectedInstallation.azimuthLocked ? (
                  <span className="text-xs text-amber-600 ml-2">(Definido por orientación de fachada)</span>
                ) : null}
              </label>
              <Slider
                value={[installAzimuth]}
                onValueChange={(v) => setInstallAzimuth(v[0])}
                min={0}
                max={360}
                step={5}
                disabled={selectedInstallation.azimuthLocked || selectedInstallation.id === 'bipv_imported'}
              />
              <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                <span>0° (N)</span>
                <span>90° (E)</span>
                <span>180° (S)</span>
                <span>270° (O)</span>
                <span>360° (N)</span>
              </div>
            </div>
          </div>

          {/* Configuration details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Applied losses */}
            <div className="bg-white rounded-lg p-4 border border-blue-100">
              <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <Info size={14} className="text-blue-500" />
                Pérdidas Aplicadas
              </h4>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-500">Suciedad:</span>
                  <span className="font-mono text-gray-700">{selectedInstallation.losses.soiling}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Desajuste:</span>
                  <span className="font-mono text-gray-700">{selectedInstallation.losses.mismatch}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Cable DC:</span>
                  <span className="font-mono text-gray-700">{selectedInstallation.losses.dcWiring}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Cable AC:</span>
                  <span className="font-mono text-gray-700">{selectedInstallation.losses.acWiring}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Inversor:</span>
                  <span className="font-mono text-gray-700">{selectedInstallation.losses.inverterEfficiency}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Disponibilidad:</span>
                  <span className="font-mono text-gray-700">{selectedInstallation.losses.availabilityLosses}%</span>
                </div>
              </div>
            </div>

            {/* Applied costs & notes */}
            <div className="bg-white rounded-lg p-4 border border-blue-100">
              <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <DollarSign size={14} className="text-emerald-500" />
                Costos y Notas
              </h4>
              <div className="space-y-1 text-xs mb-3">
                <div className="flex justify-between">
                  <span className="text-gray-500">Estructura/panel:</span>
                  <span className="font-mono text-emerald-700 font-semibold">${selectedInstallation.structureCostPerPanel}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Mano obra/panel:</span>
                  <span className="font-mono text-emerald-700 font-semibold">${selectedInstallation.laborCostPerPanel}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Separación rec.:</span>
                  <span className="font-mono text-gray-700">×{selectedInstallation.recommendedSpacing}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">PVGIS montaje:</span>
                  <span className="font-mono text-gray-700">{selectedInstallation.pvgisMountingPlace === 'free' ? 'Rack abierto' : 'Integrado'}</span>
                </div>
              </div>
              <div className="border-t pt-2">
                {selectedInstallation.notes.slice(0, 2).map((note, i) => (
                  <p key={i} className="text-[10px] text-gray-500 leading-tight mb-1">• {note}</p>
                ))}
              </div>
            </div>
          </div>

          {/* Production factor estimate */}
          {weatherData && (
            <div className="mt-3 bg-blue-50 rounded-lg p-3 border border-blue-100">
              <div className="flex items-center gap-3">
                <Sun size={16} className="text-amber-500" />
                <div className="flex-1">
                  <p className="text-xs text-gray-600">
                    <strong>Factor de producción estimado</strong> para {installTilt}° de inclinación en latitud {weatherData.location.latitude.toFixed(1)}°:
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{ width: `${estimateProductionFactor(installTilt, weatherData.location.latitude) * 100}%` }}
                      />
                    </div>
                    <span className="font-mono font-bold text-blue-700 text-sm">
                      {(estimateProductionFactor(installTilt, weatherData.location.latitude) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-[10px] text-gray-400 mt-1">
                    Respecto a inclinación óptima ({Math.abs(weatherData.location.latitude).toFixed(0)}°). Fachadas verticales (90°) típicamente producen 40-60% del óptimo.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Shading Factors Display */}
      <div style={{ display: (hasShadingData || (use3DShading && facadeAnalysis3D)) ? 'block' : 'none' }}>
        <div className={`${(use3DShading && facadeAnalysis3D) ? 'bg-purple-50 border-purple-200' : 'bg-amber-50 border-amber-200'} border rounded-lg p-4`}>
          <h4 className={`font-semibold ${(use3DShading && facadeAnalysis3D) ? 'text-purple-900' : 'text-amber-900'} mb-2 text-sm flex items-center gap-2`}>
            <Shield size={14} />
            {(use3DShading && facadeAnalysis3D)
              ? `Factores de Sombreado — Modelo 3D: ${facadeAnalysis3D.facadeName} (Az ${facadeAnalysis3D.azimuth.toFixed(0)}°, Incl ${facadeAnalysis3D.tilt.toFixed(0)}°, ${facadeAnalysis3D.area.toFixed(1)} m²)`
              : 'Factores de Sombreado Aplicados (desde Calculadora)'}
          </h4>
          {(use3DShading && facadeAnalysis3D) && (
            <p className="text-xs text-purple-700 mb-2">
              FS anual: <strong>{(facadeAnalysis3D.annualFS * 100).toFixed(1)}%</strong> | 
              Pérdida por sombra: <strong>{facadeAnalysis3D.annualShadingLoss.toFixed(1)}%</strong> | 
              Horas sol efectivas: <strong>{facadeAnalysis3D.monthlyData.reduce((a, m) => a + m.effectiveSunHours, 0).toFixed(0)}h</strong> de {facadeAnalysis3D.monthlyData.reduce((a, m) => a + m.totalSunHours, 0).toFixed(0)}h disponibles
            </p>
          )}
          {(!use3DShading && hasShadingData) && (
            <p className="text-xs text-amber-700 mb-2">
              FS anual promedio: <strong>{(avgShadingFactor * 100).toFixed(1)}%</strong> | 
              Pérdida promedio de sombreado: <strong>{((1 - avgShadingFactor) * 100).toFixed(1)}%</strong>
            </p>
          )}
          <div className="grid grid-cols-6 md:grid-cols-12 gap-1">
            {MONTHS.map((m, i) => (
              <div key={m} className="text-center">
                <p className="text-[10px] text-gray-500">{m}</p>
                <p className={`text-xs font-mono font-bold ${activeShadingFactors[i] < 0.9 ? 'text-red-600' : activeShadingFactors[i] < 1.0 ? 'text-amber-600' : 'text-green-600'}`}>
                  {(activeShadingFactors[i] * 100).toFixed(0)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Zap size={20} className="text-green-600" />
          Simulador de Producción Energética
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* Panel Specifications */}
          <div className="bg-white rounded-lg p-4 border border-green-100">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold text-gray-900">Especificaciones del Panel</h4>
              <button
                onClick={() => setUseCustomSpecs(!useCustomSpecs)}
                className={`px-2 py-0.5 text-[10px] rounded border transition-colors ${
                  useCustomSpecs ? 'bg-purple-100 border-purple-300 text-purple-700' : 'bg-gray-50 border-gray-200 text-gray-500 hover:bg-gray-100'
                }`}
              >
                {useCustomSpecs ? 'Manual' : 'Personalizar'}
              </button>
            </div>
            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-gray-600 mb-1">Potencia: {panelPower}W</label>
                <Slider
                  value={[panelPower]}
                  onValueChange={(v) => { setCustomPower(v[0]); setUseCustomSpecs(true); }}
                  min={30} max={700} step={5}
                  disabled={!useCustomSpecs}
                />
              </div>
              <div>
                <label className="block text-gray-600 mb-1">Eficiencia: {panelEfficiency}%</label>
                <Slider
                  value={[panelEfficiency]}
                  onValueChange={(v) => { setCustomEfficiency(v[0]); setUseCustomSpecs(true); }}
                  min={5} max={25} step={0.1}
                  disabled={!useCustomSpecs}
                />
              </div>
              <div>
                <label className="block text-gray-600 mb-1">Área: {panelArea.toFixed(2)}m²</label>
                <Slider
                  value={[panelArea]}
                  onValueChange={(v) => { setCustomArea(v[0]); setUseCustomSpecs(true); }}
                  min={0.1} max={4} step={0.01}
                  disabled={!useCustomSpecs}
                />
              </div>
              <div>
                <label className="block text-gray-600 mb-1">Cantidad: {panelQuantity}</label>
                <Slider value={[panelQuantity]} onValueChange={(v) => { setPanelQuantity(v[0]); setAutoSyncQuantity(false); }} min={1} max={500} step={1} />
              </div>
              <div>
                <label className="block text-gray-600 mb-1">Coef. Temp: {(tempCoefficient * 100).toFixed(2)}%/°C</label>
                <Slider
                  value={[tempCoefficient]}
                  onValueChange={(v) => { setCustomTempCoeff(v[0]); setUseCustomSpecs(true); }}
                  min={-0.006} max={-0.001} step={0.0001}
                  disabled={!useCustomSpecs}
                />
              </div>
              <div>
                <label className="block text-gray-600 mb-1">NOCT: {noct}°C</label>
                <Slider
                  value={[noct]}
                  onValueChange={(v) => { setCustomNoct(v[0]); setUseCustomSpecs(true); }}
                  min={38} max={55} step={1}
                  disabled={!useCustomSpecs}
                />
              </div>
            </div>
            <div className="mt-3 pt-2 border-t text-xs text-gray-400">
              {useCustomSpecs
                ? 'Valores personalizados activos'
                : `Valores del panel ${selectedTech.hiitioId || selectedTech.id}`}
            </div>
          </div>

          {/* System Losses */}
          <div className="bg-white rounded-lg p-4 border border-green-100">
            <h4 className="font-semibold text-gray-900 mb-4">Pérdidas del Sistema</h4>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span>Cableado DC (%):</span>
                <input type="number" value={dcWiring} onChange={(e) => setDcWiring(parseFloat(e.target.value) || 0)} className="w-14 border rounded px-1 py-0.5" step="0.5" />
              </div>
              <div className="flex justify-between items-center">
                <span>Efic. Inversor (%):</span>
                <input type="number" value={inverterEfficiency} onChange={(e) => setInverterEfficiency(parseFloat(e.target.value) || 0)} className="w-14 border rounded px-1 py-0.5" step="0.5" />
              </div>
              <div className="flex justify-between items-center">
                <span>Cableado AC (%):</span>
                <input type="number" value={acWiring} onChange={(e) => setAcWiring(parseFloat(e.target.value) || 0)} className="w-14 border rounded px-1 py-0.5" step="0.5" />
              </div>
              <div className="flex justify-between items-center">
                <span>Transformador (%):</span>
                <input type="number" value={transformerLosses} onChange={(e) => setTransformerLosses(parseFloat(e.target.value) || 0)} className="w-14 border rounded px-1 py-0.5" step="0.5" />
              </div>
              <div className="flex justify-between items-center">
                <span>Desajuste (%):</span>
                <input type="number" value={mismatchLosses} onChange={(e) => setMismatchLosses(parseFloat(e.target.value) || 0)} className="w-14 border rounded px-1 py-0.5" step="0.5" />
              </div>
              <div className="flex justify-between items-center">
                <span className="flex items-center gap-1">
                  Suciedad (%):
                  {soilingMensualData && <span className="text-[9px] text-teal-600 font-semibold">(mensual)</span>}
                </span>
                <input type="number" value={soilingLosses} onChange={(e) => setSoilingLosses(parseFloat(e.target.value) || 0)} className="w-14 border rounded px-1 py-0.5" step="0.5" />
              </div>
              {soilingMensualData && (
                <div className="mt-1 px-2 py-1 bg-teal-50 border border-teal-200 rounded text-[10px] text-teal-700">
                  <span className="font-semibold">Soiling mensual variable activo</span> — 12 valores estacionales aplicados (rango: {Math.min(...soilingMensualData).toFixed(1)}% – {Math.max(...soilingMensualData).toFixed(1)}%)
                </div>
              )}
              <div className="flex justify-between items-center">
                <span>Disponibilidad (%):</span>
                <input type="number" value={availabilityLosses} onChange={(e) => setAvailabilityLosses(parseFloat(e.target.value) || 0)} className="w-14 border rounded px-1 py-0.5" step="0.5" />
              </div>
              <div className="flex justify-between items-center">
                <span className="flex items-center gap-1">
                  IAM ASHRAE (%):
                  <span className="text-xs text-gray-400" title="Incidence Angle Modifier - Pérdida angular por reflexión en el vidrio. Se importa automáticamente desde IAM+Soiling BIPV.">&#9432;</span>
                </span>
                <input type="number" value={iamLosses} onChange={(e) => setIamLosses(parseFloat(e.target.value) || 0)} className="w-14 border rounded px-1 py-0.5" step="0.5" min="0" max="50" />
              </div>
              {iamMensualData && (
                <div className="mt-1 px-2 py-1 bg-violet-50 border border-violet-200 rounded text-[10px] text-violet-700">
                  <span className="font-semibold">IAM mensual variable activo</span> — 12 valores de pérdida estacional aplicados (rango: {Math.min(...iamMensualData).toFixed(1)}% – {Math.max(...iamMensualData).toFixed(1)}%)
                </div>
              )}
              <div className="pt-2 border-t mt-2">
                <div className="flex justify-between items-center font-semibold text-amber-700">
                  <span>Sombreado (auto):</span>
                  <span>{((1 - avgShadingFactor) * 100).toFixed(1)}%</span>
                </div>
                <p className="text-[10px] text-gray-400 mt-1">Calculado desde la pestaña Calculadora</p>
              </div>
            </div>
          </div>

          {/* Financial Parameters - Cost Breakdown Table */}
          <div className="bg-white rounded-lg p-4 border border-green-100">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <Calculator size={16} className="text-emerald-600" />
                Presupuesto del Sistema BIPV
              </h4>
              <button
                onClick={() => setCostTableExpanded(!costTableExpanded)}
                className="text-xs text-emerald-600 hover:text-emerald-800 flex items-center gap-1"
              >
                {costTableExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {costTableExpanded ? 'Colapsar' : 'Expandir tabla'}
              </button>
            </div>

            {/* Summary always visible */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="bg-emerald-50 rounded p-2 text-center">
                <p className="text-xs text-gray-500">Costo Total</p>
                <p className="text-lg font-bold text-emerald-700">${systemCost.toLocaleString(undefined, {maximumFractionDigits: 0})}</p>
              </div>
              <div className="bg-blue-50 rounded p-2 text-center">
                <p className="text-xs text-gray-500">USD/Wp</p>
                <p className="text-lg font-bold text-blue-700">
                  {panelQuantity > 0 && panelPower > 0
                    ? (systemCost / (panelQuantity * panelPower)).toFixed(2)
                    : '—'}
                </p>
              </div>
            </div>

            {/* Expandable cost table */}
            <div style={{ display: costTableExpanded ? 'block' : 'none' }}>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-xs w-[180px]">Concepto</TableHead>
                      <TableHead className="text-xs text-right w-[90px]">Costo Unit.</TableHead>
                      <TableHead className="text-xs text-right w-[70px]">Cant.</TableHead>
                      <TableHead className="text-xs w-[50px]">Ud.</TableHead>
                      <TableHead className="text-xs text-right w-[100px]">Subtotal</TableHead>
                      <TableHead className="text-xs w-[30px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {costItems.map((item) => (
                      <TableRow key={item.id} className={item.id === 'panels' ? 'bg-amber-50/50' : ''}>
                        <TableCell className="py-1">
                          <Input
                            value={item.description}
                            onChange={(e) => updateCostItem(item.id, 'description', e.target.value)}
                            className="h-7 text-xs border-0 bg-transparent px-1 focus-visible:ring-1"
                          />
                        </TableCell>
                        <TableCell className="py-1 text-right">
                          <Input
                            type="number"
                            value={item.unitCost}
                            onChange={(e) => updateCostItem(item.id, 'unitCost', parseFloat(e.target.value) || 0)}
                            className="h-7 text-xs text-right border-0 bg-transparent px-1 focus-visible:ring-1 w-[80px] ml-auto"
                            step={item.unit === 'Wp' ? 0.01 : 1}
                          />
                        </TableCell>
                        <TableCell className="py-1 text-right">
                          {item.isAutoCalc ? (
                            <span className="text-xs text-gray-500 font-mono">{item.quantity.toLocaleString()}</span>
                          ) : (
                            <Input
                              type="number"
                              value={item.quantity}
                              onChange={(e) => updateCostItem(item.id, 'quantity', parseFloat(e.target.value) || 0)}
                              className="h-7 text-xs text-right border-0 bg-transparent px-1 focus-visible:ring-1 w-[60px] ml-auto"
                            />
                          )}
                        </TableCell>
                        <TableCell className="py-1 text-xs text-gray-400">{item.unit}</TableCell>
                        <TableCell className="py-1 text-right font-mono text-xs font-semibold">
                          ${(item.unitCost * item.quantity).toLocaleString(undefined, {maximumFractionDigits: 0})}
                        </TableCell>
                        <TableCell className="py-1">
                          {item.id !== 'panels' && (
                            <button
                              onClick={() => removeCostItem(item.id)}
                              className="text-gray-300 hover:text-red-500 transition-colors"
                              title="Eliminar"
                            >
                              <Trash2 size={12} />
                            </button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                  <TableFooter>
                    <TableRow className="bg-emerald-50">
                      <TableCell colSpan={4} className="text-xs font-bold text-gray-700">TOTAL SISTEMA</TableCell>
                      <TableCell className="text-right font-mono text-sm font-bold text-emerald-700">
                        ${systemCost.toLocaleString(undefined, {maximumFractionDigits: 0})}
                      </TableCell>
                      <TableCell></TableCell>
                    </TableRow>
                  </TableFooter>
                </Table>
              </div>

              <button
                onClick={addCostItem}
                className="mt-2 w-full flex items-center justify-center gap-1 text-xs text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50 rounded py-1.5 transition-colors border border-dashed border-emerald-200"
              >
                <Plus size={12} /> Agregar ítem
              </button>

              {/* Cost distribution */}
              <div className="mt-3 space-y-1">
                {costItems.filter(i => i.unitCost * i.quantity > 0).map(item => {
                  const subtotal = item.unitCost * item.quantity;
                  const pct = systemCost > 0 ? (subtotal / systemCost) * 100 : 0;
                  return (
                    <div key={item.id} className="flex items-center gap-2 text-xs">
                      <span className="w-[120px] truncate text-gray-600">{item.description}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-2">
                        <div
                          className="bg-emerald-500 h-2 rounded-full transition-all"
                          style={{ width: `${Math.min(pct, 100)}%` }}
                        />
                      </div>
                      <span className="w-[40px] text-right font-mono text-gray-500">{pct.toFixed(0)}%</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Tarifa y Mantenimiento */}
            <div className="mt-3 pt-3 border-t space-y-3 text-sm">
              <div>
                <label className="block text-gray-600 mb-1">Tarifa Eléctrica: ${electricityRate.toFixed(2)}/kWh</label>
                <Slider value={[electricityRate]} onValueChange={(v) => setElectricityRate(v[0])} min={0.05} max={0.8} step={0.01} />
              </div>
              <div>
                <label className="block text-gray-600 mb-1">Mant. Anual: {maintenanceCostPercent.toFixed(1)}% = ${maintenanceCost.toLocaleString(undefined, {maximumFractionDigits: 0})}/año</label>
                <Slider value={[maintenanceCostPercent]} onValueChange={(v) => setMaintenanceCostPercent(v[0])} min={0} max={5} step={0.1} />
              </div>
            </div>

            <div className="mt-3 pt-3 border-t">
              <p className="text-xs text-gray-500">Potencia instalada:</p>
              <p className="text-lg font-bold text-gray-900">{((panelPower * panelQuantity) / 1000).toFixed(2)} kWp</p>
              {yearsFromInstall > 0 && (
                <p className="text-xs text-amber-600 mt-1">
                  Degradación {yearsFromInstall} años: -{(selectedTech.degradationAnnual * yearsFromInstall).toFixed(1)}%
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Key Metrics - IEC 61724 */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-blue-50 rounded p-3 border border-blue-200">
            <p className="text-xs text-gray-600 mb-1">Producción DC Anual</p>
            <p className="text-2xl font-mono font-bold text-blue-700">{Math.round(production.totalDCEnergy)}</p>
            <p className="text-xs text-gray-500">kWh/año DC</p>
          </div>
          <div className="bg-green-50 rounded p-3 border border-green-200">
            <p className="text-xs text-gray-600 mb-1">Producción AC Anual</p>
            <p className="text-2xl font-mono font-bold text-green-700">{Math.round(production.totalACEnergy)}</p>
            <p className="text-xs text-gray-500">kWh/año AC</p>
            {pvgisData && (
              <div className="mt-1 pt-1 border-t border-green-200">
                <p className="text-[10px] text-emerald-700 font-medium">PVGIS: {pvgisData.annualProductionCorrected.toFixed(0)} kWh/año AC</p>
                <p className="text-[10px] text-gray-500">
                  Δ = {(((production.totalACEnergy - pvgisData.annualProductionCorrected) / pvgisData.annualProductionCorrected) * 100).toFixed(1)}%
                </p>
              </div>
            )}
            {pvwattsData && (
              <div className="mt-1 pt-1 border-t border-indigo-200">
                <p className="text-[10px] text-indigo-700 font-medium">PVWatts: {pvwattsData.annualAC_kWh.toFixed(0)} kWh/año AC</p>
                <p className="text-[10px] text-gray-500">
                  Δ = {(((production.totalACEnergy - pvwattsData.annualAC_kWh) / pvwattsData.annualAC_kWh) * 100).toFixed(1)}%
                </p>
              </div>
            )}
            {bipvData && (() => {
              // Comparación normalizada por Yield DC (kWh/kWp) para ser justa
              // independientemente de la capacidad configurada en cada motor
              const bipvCapKWp = bipvData.potenciaPicoW / 1000;
              const simCapKWp = (panelPower * panelQuantity) / 1000;
              const bipvYieldDC = bipvCapKWp > 0 ? bipvData.energiaAnualKwh / bipvCapKWp : 0;
              const simYieldDC = simCapKWp > 0 ? production.totalDCEnergy / simCapKWp : 0;
              const delta = bipvYieldDC > 0 ? ((simYieldDC - bipvYieldDC) / bipvYieldDC) * 100 : 0;
              const absDelta = Math.abs(delta);
              const color = absDelta < 10 ? 'text-green-700' : absDelta < 25 ? 'text-amber-700' : 'text-red-700';
              const bgColor = absDelta < 10 ? 'bg-green-50' : absDelta < 25 ? 'bg-amber-50' : 'bg-red-50';
              const icon = absDelta < 10 ? '✅' : absDelta < 25 ? '⚠️' : '❌';
              return (
                <div className={`mt-1 pt-1 border-t border-teal-200 ${bgColor} rounded px-1`}>
                  <p className="text-[10px] text-teal-700 font-medium">{icon} IAM+Soiling: {bipvYieldDC.toFixed(0)} kWh/kWp DC</p>
                  <p className="text-[10px] text-gray-500">Sim: {simYieldDC.toFixed(0)} kWh/kWp DC</p>
                  <p className={`text-[10px] font-semibold ${color}`}>
                    Δ Yield = {delta > 0 ? '+' : ''}{delta.toFixed(1)}% {absDelta < 10 ? '(coherente)' : absDelta < 25 ? '(revisar)' : '(divergente)'}
                  </p>
                </div>
              );
            })()}
          </div>
          <div className="bg-yellow-50 rounded p-3 border border-yellow-200">
            <p className="text-xs text-gray-600 mb-1">Specific Yield</p>
            <p className="text-2xl font-mono font-bold text-yellow-700">{production.specificYield.toFixed(0)}</p>
            <p className="text-xs text-gray-500">kWh/kWp/año</p>
          </div>
          <div className={`rounded p-3 border relative group ${production.performanceRatio > 100 ? 'bg-red-50 border-red-400 ring-2 ring-red-300' : 'bg-purple-50 border-purple-200'}`}>
            <p className="text-xs text-gray-600 mb-1 flex items-center gap-1">
              PR IEC 61724
              <span className="inline-block w-3.5 h-3.5 rounded-full bg-gray-300 text-[9px] text-white text-center leading-[14px] cursor-help" title="Performance Ratio = Yf / Yr\nYf (Final Yield) = E_AC / P_nom\nYr (Reference Yield) = H_POA / G_ref (1000 W/m²)\n\nValor esperado: 70-90%\nPR > 100% indica error en datos de entrada">?</span>
            </p>
            <p className={`text-2xl font-mono font-bold ${production.performanceRatio > 100 ? 'text-red-700' : 'text-purple-700'}`}>{production.performanceRatio.toFixed(1)}%</p>
            <p className="text-xs text-gray-500">Yf/Yr = {production.iec61724.finalYield.toFixed(0)}/{production.iec61724.referenceYield.toFixed(0)}</p>
            {/* Tooltip expandido al hover */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-gray-900 text-white text-[10px] rounded-lg p-3 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 shadow-xl">
              <p className="font-bold mb-1">Performance Ratio (PR)</p>
              <p className="mb-1">PR = Yf / Yr</p>
              <p>Yf = E_AC / P_nom = {production.totalACEnergy.toFixed(0)} / {(production.iec61724.finalYield > 0 ? production.totalACEnergy / production.iec61724.finalYield : 1).toFixed(1)} kWp = <strong>{production.iec61724.finalYield.toFixed(1)} h</strong></p>
              <p>Yr = H_POA / G_ref = <strong>{production.iec61724.referenceYield.toFixed(1)} h</strong></p>
              <p className="mt-1 border-t border-gray-700 pt-1">PR = {production.iec61724.finalYield.toFixed(1)} / {production.iec61724.referenceYield.toFixed(1)} = <strong>{(production.performanceRatio).toFixed(1)}%</strong></p>
              <p className="mt-1 text-gray-400">Rango típico: 70–90%</p>
            </div>
            {/* Alerta PR > 100% */}
            {production.performanceRatio > 100 && (
              <div className="mt-2 pt-2 border-t border-red-300">
                <p className="text-[10px] text-red-700 font-bold flex items-center gap-1">
                  ⚠️ PR &gt;100% — Físicamente imposible
                </p>
                <p className="text-[9px] text-red-600 mt-0.5">Posibles causas: irradiancia POA subestimada, capacidad nominal incorrecta, o datos de entrada inconsistentes.</p>
                <button
                  onClick={() => setShowPRDiagnostic(!showPRDiagnostic)}
                  className="mt-1.5 px-2 py-0.5 text-[9px] font-bold bg-red-700 text-white rounded hover:bg-red-800 transition-colors"
                >
                  {showPRDiagnostic ? '✕ Cerrar diagnóstico' : '🔍 Diagnosticar PR'}
                </button>
              </div>
            )}
            {/* Panel de diagnóstico PR expandido */}
            {showPRDiagnostic && production.performanceRatio > 100 && (() => {
              const tilt = poaConfig?.tilt ?? installTilt;
              const azimuth = poaConfig?.azimuth ?? installAzimuth;
              const lat = weatherData.location.latitude;
              const pNomKw = (panelPower * panelQuantity) / 1000;
              const eAC = production.totalACEnergy;
              const yf = production.iec61724.finalYield;
              const yr = production.iec61724.referenceYield;
              // H_POA anual real usada (kWh/m²)
              const hPoaReal = production.monthlyData.reduce((s, m, i) => {
                const days = [31,28,31,30,31,30,31,31,30,31,30,31][i];
                return s + (m.rawPOA * days * 24) / 1000;
              }, 0);
              // H_POA esperada para la latitud (estimación simplificada)
              // GHI típico Colombia: 1400-2000 kWh/m²/año, factor de transposición ~1.1-1.4
              const ghi_tipico = lat >= 0 && lat <= 12 ? 1700 : 1500; // kWh/m²/año Colombia
              const factorTransp = 1 + 0.01 * Math.min(tilt, 30); // aprox
              const hPoaEsperada = ghi_tipico * factorTransp / 1000; // en kWh/m²... NO
              // Mejor: usar el POA promedio mensual real × 12 meses × 30 días × 24h
              const avgPOA_Wm2 = poaData.reduce((s, d) => s + d.totalPOA, 0) / poaData.length;
              // PR esperado para un sistema bien diseñado: 75-85%
              const prExpected = 0.80;
              // E_AC esperada con PR=80%
              const eACEsperada = prExpected * pNomKw * (hPoaReal); // kWh
              // Diagnóstico: ¿cuál es el problema principal?
              const issues: { param: string; real: string; esperado: string; impacto: string; accion: string }[] = [];
              
              // 1. Verificar si H_POA es anormalmente baja
              const hPoaAnualEsperada = avgPOA_Wm2 > 50 ? avgPOA_Wm2 * 365 * 24 / 1000 : 1800;
              if (hPoaReal < 500) {
                issues.push({
                  param: 'H_POA (Irradiancia POA anual)',
                  real: `${hPoaReal.toFixed(0)} kWh/m²`,
                  esperado: `1400–2000 kWh/m² (Colombia)`,
                  impacto: `Yr muy bajo → PR inflado artificialmente`,
                  accion: 'Verifique que los datos EPW correspondan a la ubicación real. El POA mensual promedio debería ser 120-200 W/m² en Colombia.'
                });
              }
              
              // 2. Verificar si P_nom es coherente con el área y la eficiencia
              const areaTotal = panelArea * panelQuantity;
              const pNomEsperadaKw = (areaTotal * (panelEfficiency / 100) * 1000) / 1000;
              const ratioPnom = pNomKw / pNomEsperadaKw;
              if (ratioPnom < 0.5 || ratioPnom > 2.0) {
                issues.push({
                  param: 'P_nom (Capacidad nominal)',
                  real: `${pNomKw.toFixed(2)} kWp (${panelQuantity} × ${panelPower}W)`,
                  esperado: `~${pNomEsperadaKw.toFixed(2)} kWp (${areaTotal.toFixed(1)}m² × η=${panelEfficiency}%)`,
                  impacto: `Desbalance entre potencia declarada y área/eficiencia`,
                  accion: 'Verifique que la potencia del panel, cantidad y área sean consistentes. Si usa paneles BIPV semitransparentes, la potencia efectiva es menor que un panel opaco del mismo tamaño.'
                });
              }
              
              // 3. Verificar si E_AC es excesiva para el sistema
              const cfReal = eAC / (pNomKw * 8760);
              if (cfReal > 0.30) {
                issues.push({
                  param: 'E_AC (Producción AC)',
                  real: `${eAC.toFixed(0)} kWh/año (CF=${(cfReal*100).toFixed(1)}%)`,
                  esperado: `CF típico: 15-25% (Colombia)`,
                  impacto: `Producción excesiva para la capacidad instalada`,
                  accion: 'Verifique que las pérdidas del sistema (soiling, inversor, cableado) estén correctamente configuradas. Un CF > 30% es inusual.'
                });
              }
              
              // 4. Verificar orientación
              const optimalTilt = Math.abs(lat);
              if (Math.abs(tilt - optimalTilt) > 30) {
                issues.push({
                  param: 'Orientación (Tilt/Azimut)',
                  real: `Tilt=${tilt}°, Azimut=${azimuth}°`,
                  esperado: `Tilt óptimo ≈ ${optimalTilt.toFixed(0)}° para lat=${lat.toFixed(1)}°`,
                  impacto: `Orientación muy diferente al óptimo puede reducir H_POA real`,
                  accion: 'Si el tilt difiere mucho del óptimo, la H_POA calculada podría no corresponder a la producción real. Verifique que tilt y azimut reflejen la superficie real.'
                });
              }

              // 5. Verificar pérdidas totales
              const totalLosses = soilingLosses + (100 - inverterEfficiency) + dcWiring + acWiring + mismatchLosses;
              if (totalLosses < 5) {
                issues.push({
                  param: 'Pérdidas del sistema',
                  real: `Total: ${totalLosses.toFixed(1)}% (Soiling=${soilingLosses}%, Inv=${(100-inverterEfficiency).toFixed(1)}%)`,
                  esperado: `10-20% pérdidas totales típicas`,
                  impacto: `Pérdidas muy bajas inflan la producción AC`,
                  accion: 'Revise que soiling, eficiencia del inversor y pérdidas de cableado sean realistas. Valores mínimos recomendados: Soiling ≥2%, Inversor ≤96%, DC wiring ≥1%.'
                });
              }

              if (issues.length === 0) {
                issues.push({
                  param: 'Causa no identificada',
                  real: `PR = ${production.performanceRatio.toFixed(1)}%`,
                  esperado: '70-90%',
                  impacto: 'Posible inconsistencia entre fuentes de datos',
                  accion: 'Verifique que los datos EPW, la configuración POA y los parámetros del panel provengan de la misma ubicación y orientación.'
                });
              }

              return (
                <div className="mt-2 bg-red-50 border border-red-200 rounded-lg p-3 text-[10px] max-h-64 overflow-y-auto">
                  <p className="font-bold text-red-800 mb-2 text-[11px]">🔍 Diagnóstico PR — Análisis de parámetros</p>
                  <div className="grid grid-cols-2 gap-1 mb-2 text-[9px] bg-white rounded p-1.5">
                    <span className="text-gray-600">Yf (Final Yield):</span><span className="font-mono font-bold">{yf.toFixed(1)} h</span>
                    <span className="text-gray-600">Yr (Reference Yield):</span><span className="font-mono font-bold">{yr.toFixed(1)} h</span>
                    <span className="text-gray-600">H_POA anual:</span><span className="font-mono font-bold">{hPoaReal.toFixed(0)} kWh/m²</span>
                    <span className="text-gray-600">P_nom:</span><span className="font-mono font-bold">{pNomKw.toFixed(2)} kWp</span>
                    <span className="text-gray-600">E_AC:</span><span className="font-mono font-bold">{eAC.toFixed(0)} kWh/año</span>
                    <span className="text-gray-600">Tilt/Az:</span><span className="font-mono font-bold">{tilt}° / {azimuth}°</span>
                  </div>
                  <table className="w-full border-collapse text-[9px]">
                    <thead>
                      <tr className="bg-red-100">
                        <th className="border border-red-200 px-1 py-0.5 text-left">Parámetro</th>
                        <th className="border border-red-200 px-1 py-0.5 text-left">Valor actual</th>
                        <th className="border border-red-200 px-1 py-0.5 text-left">Esperado</th>
                        <th className="border border-red-200 px-1 py-0.5 text-left">Acción</th>
                      </tr>
                    </thead>
                    <tbody>
                      {issues.map((issue, i) => (
                        <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-red-50'}>
                          <td className="border border-red-200 px-1 py-0.5 font-bold text-red-800">{issue.param}</td>
                          <td className="border border-red-200 px-1 py-0.5 font-mono">{issue.real}</td>
                          <td className="border border-red-200 px-1 py-0.5 font-mono text-green-700">{issue.esperado}</td>
                          <td className="border border-red-200 px-1 py-0.5 text-gray-700">{issue.accion}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="mt-2 text-[9px] text-gray-600 italic">💡 Corrija el parámetro con mayor impacto primero. Si PR sigue anormal, verifique la coherencia entre fuentes de datos (EPW, PVGIS, PVWatts).</p>
                </div>
              );
            })()}
            {prospectorData && (
              <div className="mt-2 pt-2 border-t border-purple-200">
                <p className="text-[10px] text-amber-700 font-medium">PR Mulcue-Llanos ({prospectorData.source === 'heatmap_pvwatts' ? 'PVWatts' : 'PVGIS'}): {(prospectorData.prCorrected * 100).toFixed(1)}%</p>
                <p className="text-[10px] text-gray-500">
                  Δ = {(production.performanceRatio - prospectorData.prCorrected * 100).toFixed(1)} pp
                </p>
              </div>
            )}
          </div>
          <div className="bg-indigo-50 rounded p-3 border border-indigo-200">
            <p className="text-xs text-gray-600 mb-1">PR Corregido T°</p>
            <p className="text-2xl font-mono font-bold text-indigo-700">{production.prTemperatureCorrected.toFixed(1)}%</p>
            <p className="text-xs text-gray-500">IEC 61724-1:2021</p>
          </div>
          <div className="bg-orange-50 rounded p-3 border border-orange-200">
            <p className="text-xs text-gray-600 mb-1">Capacity Factor</p>
            <p className="text-2xl font-mono font-bold text-orange-700">{production.capacityFactor.toFixed(1)}%</p>
            <p className="text-xs text-gray-500">Desempeño anual</p>
          </div>
        </div>

        {/* IEC 61724 Yields & Losses Breakdown */}
        <div className="bg-gradient-to-r from-slate-50 to-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
          <div className="flex items-center gap-2 mb-3">
            <Calculator className="w-4 h-4 text-gray-600" />
            <h5 className="text-sm font-semibold text-gray-800">Métricas IEC 61724-1 — Desglose de Yields</h5>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-center">
            <div className="bg-white rounded-lg p-2 border border-gray-100">
              <p className="text-[10px] text-gray-500 font-medium">Yr (Reference)</p>
              <p className="text-lg font-mono font-bold text-gray-800">{production.iec61724.referenceYield.toFixed(0)}</p>
              <p className="text-[10px] text-gray-400">h equiv.</p>
            </div>
            <div className="bg-white rounded-lg p-2 border border-gray-100">
              <p className="text-[10px] text-gray-500 font-medium">Ya (Array)</p>
              <p className="text-lg font-mono font-bold text-amber-700">{production.iec61724.arrayYield.toFixed(0)}</p>
              <p className="text-[10px] text-gray-400">kWh/kWp</p>
            </div>
            <div className="bg-white rounded-lg p-2 border border-gray-100">
              <p className="text-[10px] text-gray-500 font-medium">Yf (Final)</p>
              <p className="text-lg font-mono font-bold text-green-700">{production.iec61724.finalYield.toFixed(0)}</p>
              <p className="text-[10px] text-gray-400">kWh/kWp</p>
            </div>
            <div className="bg-white rounded-lg p-2 border border-red-100">
              <p className="text-[10px] text-gray-500 font-medium">Lc (Capture)</p>
              <p className="text-lg font-mono font-bold text-red-600">{production.iec61724.captureLosses.toFixed(0)}</p>
              <p className="text-[10px] text-gray-400">h (T°, sombra)</p>
            </div>
            <div className="bg-white rounded-lg p-2 border border-red-100">
              <p className="text-[10px] text-gray-500 font-medium">Ls (System)</p>
              <p className="text-lg font-mono font-bold text-red-500">{production.iec61724.systemLosses.toFixed(0)}</p>
              <p className="text-[10px] text-gray-400">h (inv, cable)</p>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
            <div className="bg-white rounded-lg p-2 border border-gray-100">
              <p className="text-[10px] text-gray-500">BOS Efficiency</p>
              <p className="text-sm font-mono font-bold text-gray-700">{(production.iec61724.bosEfficiency * 100).toFixed(1)}%</p>
              <p className="text-[10px] text-gray-400">E_AC / E_DC</p>
            </div>
            <div className="bg-white rounded-lg p-2 border border-gray-100">
              <p className="text-[10px] text-gray-500">Pérdidas Totales</p>
              <p className="text-sm font-mono font-bold text-red-600">{production.losses.total.toFixed(1)}%</p>
              <p className="text-[10px] text-gray-400">1 - PR</p>
            </div>
            <div className="bg-white rounded-lg p-2 border border-gray-100">
              <p className="text-[10px] text-gray-500">E_DC Total</p>
              <p className="text-sm font-mono font-bold text-blue-700">{Math.round(production.totalDCEnergy)}</p>
              <p className="text-[10px] text-gray-400">kWh/año DC</p>
            </div>
            <div className="bg-white rounded-lg p-2 border border-gray-100">
              <p className="text-[10px] text-gray-500">E_AC Total</p>
              <p className="text-sm font-mono font-bold text-green-700">{Math.round(production.totalACEnergy)}</p>
              <p className="text-[10px] text-gray-400">kWh/año AC</p>
            </div>
          </div>
          <p className="text-[10px] text-gray-400 mt-2 italic">PR = Yf/Yr según IEC 61724-1:2017. PR_T corregido por temperatura según IEC 61724-1:2021 Ed.2. Yr = H_POA/G_ref (1000 W/m²).</p>
        </div>

        {/* ===== DESGLOSE DE CAPTURE LOSSES (IEC 61724) ===== */}
        <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg p-4 mt-4">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-red-600" />
            <h5 className="text-sm font-semibold text-red-800">Desglose de Capture Losses (Lc) — IEC 61724-1</h5>
            <span className="text-[10px] bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
              Lc Total: {production.iec61724.captureLosses.toFixed(0)} h equiv.
            </span>
          </div>
          <p className="text-[10px] text-gray-600 mb-3 italic">
            Las Capture Losses (Lc = Yr − Ya) representan la energía perdida en el array DC antes del inversor. Se descomponen en 5 categorías según IEC 61724-1.
          </p>
          {/* Barras horizontales proporcionales */}
          <div className="space-y-2">
            {[
              { label: 'Temperatura (Lc_temp)', value: production.iec61724.captureLossesBreakdown.temperature, color: 'bg-red-500', pct: production.losses.temperature },
              { label: 'Sombreado (Lc_sombra)', value: production.iec61724.captureLossesBreakdown.shading, color: 'bg-gray-600', pct: production.losses.shading },
              { label: 'Suciedad (Lc_suciedad)', value: production.iec61724.captureLossesBreakdown.soiling, color: 'bg-amber-500', pct: production.losses.soiling },
              { label: 'Mismatch (Lc_mismatch)', value: production.iec61724.captureLossesBreakdown.mismatch, color: 'bg-purple-500', pct: production.losses.mismatch },
              { label: 'Cableado DC (Lc_dc)', value: production.iec61724.captureLossesBreakdown.dcWiring, color: 'bg-blue-500', pct: production.losses.dcWiring },
              { label: 'IAM (Lc_iam)', value: production.iec61724.captureLossesBreakdown.iam, color: 'bg-teal-500', pct: production.losses.iam },
            ].filter(item => item.value > 0.1).map((item) => {
              const maxVal = Math.max(
                production.iec61724.captureLossesBreakdown.temperature,
                production.iec61724.captureLossesBreakdown.shading,
                production.iec61724.captureLossesBreakdown.soiling,
                production.iec61724.captureLossesBreakdown.mismatch,
                production.iec61724.captureLossesBreakdown.dcWiring,
                production.iec61724.captureLossesBreakdown.iam,
                1
              );
              const barWidth = Math.max(2, (item.value / maxVal) * 100);
              return (
                <div key={item.label} className="flex items-center gap-2">
                  <div className="w-36 text-[10px] text-gray-700 font-medium truncate">{item.label}</div>
                  <div className="flex-1 bg-gray-100 rounded-full h-4 relative overflow-hidden">
                    <div
                      className={`${item.color} h-full rounded-full transition-all duration-500`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                  <div className="w-20 text-right">
                    <span className="text-xs font-mono font-bold text-gray-800">{item.value.toFixed(1)}</span>
                    <span className="text-[9px] text-gray-500 ml-1">h</span>
                  </div>
                  <div className="w-14 text-right">
                    <span className="text-[10px] font-mono text-gray-500">{item.pct.toFixed(1)}%</span>
                  </div>
                </div>
              );
            })}
            {/* Barra total */}
            <div className="flex items-center gap-2 pt-1 mt-1 border-t border-red-200">
              <div className="w-36 text-[10px] text-red-800 font-bold">Σ Capture Losses</div>
              <div className="flex-1 bg-red-100 rounded-full h-4 relative overflow-hidden">
                <div className="bg-red-600 h-full rounded-full" style={{ width: '100%' }} />
              </div>
              <div className="w-20 text-right">
                <span className="text-xs font-mono font-bold text-red-700">{production.iec61724.captureLossesBreakdown.total.toFixed(1)}</span>
                <span className="text-[9px] text-red-500 ml-1">h</span>
              </div>
              <div className="w-14 text-right">
                <span className="text-[10px] font-mono text-red-600">
                  {(production.iec61724.captureLossesBreakdown.total / (production.iec61724.referenceYield || 1) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
          <div className="mt-3 pt-2 border-t border-red-200 grid grid-cols-3 gap-2 text-center">
            <div className="bg-white/70 rounded p-1.5">
              <p className="text-[9px] text-gray-500">Yr (Referencia)</p>
              <p className="text-sm font-mono font-bold text-gray-700">{production.iec61724.referenceYield.toFixed(0)} h</p>
            </div>
            <div className="bg-white/70 rounded p-1.5">
              <p className="text-[9px] text-gray-500">Ya (Array)</p>
              <p className="text-sm font-mono font-bold text-amber-700">{production.iec61724.arrayYield.toFixed(0)} h</p>
            </div>
            <div className="bg-white/70 rounded p-1.5">
              <p className="text-[9px] text-gray-500">Lc / Yr</p>
              <p className="text-sm font-mono font-bold text-red-700">{((production.iec61724.captureLosses / (production.iec61724.referenceYield || 1)) * 100).toFixed(1)}%</p>
            </div>
          </div>
          <p className="text-[9px] text-gray-500 mt-2 italic">
            Lc_tipo = Yr × (pérdida_tipo% / 100). La suma ΣLc puede diferir ligeramente de Lc total por interacción entre pérdidas.
          </p>
        </div>

        {/* ===== PR_T HORARIO IEC 61724-1:2021 ===== */}
        {(hourlyPR_T_PVWatts || hourlyPR_T_PVGIS) && (
          <div className="bg-gradient-to-r from-cyan-50 to-teal-50 border border-cyan-300 rounded-lg p-4 mt-4">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-4 h-4 text-cyan-700" />
              <h5 className="text-sm font-semibold text-cyan-900">PR_T Horario — IEC 61724-1:2021 Ed.2 (Paso a Paso Temporal)</h5>
              <span className="text-[10px] bg-cyan-100 text-cyan-700 px-2 py-0.5 rounded-full font-medium">
                {hourlyPR_T_PVWatts && hourlyPR_T_PVGIS ? 'PVWatts + PVGIS' : hourlyPR_T_PVWatts ? 'PVWatts' : 'PVGIS'}
              </span>
            </div>
            <p className="text-[10px] text-gray-600 mb-3 italic">
              PR_T = Σ(E_AC_h) / Σ((G_POA_h/G_ref) × P_nom × (1 + γ × (T_cell_h − 25°C))). Calculado hora a hora con datos TMY ({hourlyPR_T_PVWatts?.totalRecords || hourlyPR_T_PVGIS?.totalRecords || 0} registros). Umbral: G_POA ≥ 50 W/m² (IEC 61724).
            </p>

            {/* Comparación Anual: Mensual vs Horario */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div className="bg-white rounded-lg p-3 border border-gray-200 text-center">
                <p className="text-[10px] text-gray-500 mb-1">PR_T Mensual</p>
                <p className="text-xl font-mono font-bold text-indigo-700">{production.prTemperatureCorrected.toFixed(1)}%</p>
                <p className="text-[9px] text-gray-400">Promedios mensuales</p>
              </div>
              {hourlyPR_T_PVWatts && (
                <div className="bg-white rounded-lg p-3 border border-cyan-200 text-center">
                  <p className="text-[10px] text-cyan-700 mb-1 font-medium">PR_T Horario (PVWatts)</p>
                  <p className="text-xl font-mono font-bold text-cyan-800">{(hourlyPR_T_PVWatts.annualPR_T * 100).toFixed(1)}%</p>
                  <p className="text-[9px] text-gray-400">{hourlyPR_T_PVWatts.sunHours} h sol | T̄_cell: {hourlyPR_T_PVWatts.avgCellTempWeighted.toFixed(1)}°C</p>
                </div>
              )}
              {hourlyPR_T_PVGIS && (
                <div className="bg-white rounded-lg p-3 border border-emerald-200 text-center">
                  <p className="text-[10px] text-emerald-700 mb-1 font-medium">PR_T Horario (PVGIS)</p>
                  <p className="text-xl font-mono font-bold text-emerald-800">{(hourlyPR_T_PVGIS.annualPR_T * 100).toFixed(1)}%</p>
                  <p className="text-[9px] text-gray-400">{hourlyPR_T_PVGIS.sunHours} h sol | T̄_cell: {hourlyPR_T_PVGIS.avgCellTempWeighted.toFixed(1)}°C</p>
                </div>
              )}
              <div className="bg-white rounded-lg p-3 border border-gray-200 text-center">
                <p className="text-[10px] text-gray-500 mb-1">Δ PR_T (Horario vs Mensual)</p>
                {hourlyPR_T_PVWatts && (
                  <p className={`text-sm font-mono font-bold ${(hourlyPR_T_PVWatts.annualPR_T * 100 - production.prTemperatureCorrected) >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    PVWatts: {(hourlyPR_T_PVWatts.annualPR_T * 100 - production.prTemperatureCorrected) >= 0 ? '+' : ''}{(hourlyPR_T_PVWatts.annualPR_T * 100 - production.prTemperatureCorrected).toFixed(2)} pp
                  </p>
                )}
                {hourlyPR_T_PVGIS && (
                  <p className={`text-sm font-mono font-bold ${(hourlyPR_T_PVGIS.annualPR_T * 100 - production.prTemperatureCorrected) >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    PVGIS: {(hourlyPR_T_PVGIS.annualPR_T * 100 - production.prTemperatureCorrected) >= 0 ? '+' : ''}{(hourlyPR_T_PVGIS.annualPR_T * 100 - production.prTemperatureCorrected).toFixed(2)} pp
                  </p>
                )}
                <p className="text-[9px] text-gray-400">pp = puntos porcentuales</p>
              </div>
            </div>

            {/* Gráfico Mensual PR vs PR_T */}
            <div className="bg-white rounded-lg p-3 border border-gray-200">
              <p className="text-[10px] text-gray-600 font-medium mb-2">PR y PR_T Mensual (Horario vs Simulador)</p>
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={Array.from({ length: 12 }, (_, i) => {
                  const monthNames = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
                  const simMonthly = production.monthlyData[i];
                  const simPR = simMonthly ? (simMonthly.energyProduced / (simMonthly.referenceEnergy || 1)) * 100 : 0;
                  const pvwM = hourlyPR_T_PVWatts?.monthly[i];
                  const pvgM = hourlyPR_T_PVGIS?.monthly[i];
                  return {
                    name: monthNames[i],
                    pr_sim: Math.round(simPR * 10) / 10,
                    pr_t_pvwatts: pvwM ? Math.round(pvwM.pr_t * 1000) / 10 : undefined,
                    pr_pvwatts: pvwM ? Math.round(pvwM.pr * 1000) / 10 : undefined,
                    pr_t_pvgis: pvgM ? Math.round(pvgM.pr_t * 1000) / 10 : undefined,
                    pr_pvgis: pvgM ? Math.round(pvgM.pr * 1000) / 10 : undefined,
                    tcell_pvwatts: pvwM ? Math.round(pvwM.avgTcell * 10) / 10 : undefined,
                    tcell_pvgis: pvgM ? Math.round(pvgM.avgTcell * 10) / 10 : undefined,
                  };
                })}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis yAxisId="pr" domain={[50, 100]} tick={{ fontSize: 10 }} label={{ value: 'PR (%)', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }} />
                  <YAxis yAxisId="temp" orientation="right" domain={[15, 55]} tick={{ fontSize: 10 }} label={{ value: 'T_cell (°C)', angle: 90, position: 'insideRight', style: { fontSize: 10 } }} />
                  <Tooltip contentStyle={{ fontSize: 11 }} />
                  <Legend wrapperStyle={{ fontSize: 10 }} />
                  <Bar yAxisId="pr" dataKey="pr_sim" name="PR Simulador" fill="#a78bfa" opacity={0.4} />
                  {hourlyPR_T_PVWatts && <Line yAxisId="pr" type="monotone" dataKey="pr_t_pvwatts" name="PR_T PVWatts (horario)" stroke="#06b6d4" strokeWidth={2.5} dot={{ r: 3 }} />}
                  {hourlyPR_T_PVWatts && <Line yAxisId="pr" type="monotone" dataKey="pr_pvwatts" name="PR PVWatts (horario)" stroke="#0891b2" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />}
                  {hourlyPR_T_PVGIS && <Line yAxisId="pr" type="monotone" dataKey="pr_t_pvgis" name="PR_T PVGIS (horario)" stroke="#10b981" strokeWidth={2.5} dot={{ r: 3 }} />}
                  {hourlyPR_T_PVGIS && <Line yAxisId="pr" type="monotone" dataKey="pr_pvgis" name="PR PVGIS (horario)" stroke="#059669" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />}
                  {hourlyPR_T_PVWatts && <Line yAxisId="temp" type="monotone" dataKey="tcell_pvwatts" name="T_cell PVWatts" stroke="#f97316" strokeWidth={1} strokeDasharray="3 3" dot={false} />}
                  {hourlyPR_T_PVGIS && <Line yAxisId="temp" type="monotone" dataKey="tcell_pvgis" name="T_cell PVGIS" stroke="#ef4444" strokeWidth={1} strokeDasharray="3 3" dot={false} />}
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Tabla mensual detallada */}
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-[10px] border-collapse">
                <thead>
                  <tr className="bg-cyan-100/50">
                    <th className="border border-cyan-200 px-2 py-1 text-left">Mes</th>
                    <th className="border border-cyan-200 px-2 py-1 text-center">PR Sim (%)</th>
                    {hourlyPR_T_PVWatts && <th className="border border-cyan-200 px-2 py-1 text-center">PR_T PVWatts (%)</th>}
                    {hourlyPR_T_PVWatts && <th className="border border-cyan-200 px-2 py-1 text-center">PR PVWatts (%)</th>}
                    {hourlyPR_T_PVGIS && <th className="border border-cyan-200 px-2 py-1 text-center">PR_T PVGIS (%)</th>}
                    {hourlyPR_T_PVGIS && <th className="border border-cyan-200 px-2 py-1 text-center">PR PVGIS (%)</th>}
                    {hourlyPR_T_PVWatts && <th className="border border-cyan-200 px-2 py-1 text-center">T̄_cell PVW (°C)</th>}
                    {hourlyPR_T_PVGIS && <th className="border border-cyan-200 px-2 py-1 text-center">T̄_cell PVG (°C)</th>}
                    {hourlyPR_T_PVWatts && <th className="border border-cyan-200 px-2 py-1 text-center">POA PVW (kWh/m²)</th>}
                    {hourlyPR_T_PVGIS && <th className="border border-cyan-200 px-2 py-1 text-center">POA PVG (kWh/m²)</th>}
                    {hourlyPR_T_PVWatts && <th className="border border-cyan-200 px-2 py-1 text-center">h Sol PVW</th>}
                  </tr>
                </thead>
                <tbody>
                  {Array.from({ length: 12 }, (_, i) => {
                    const monthNames = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
                    const simMonthly = production.monthlyData[i];
                    const simPR = simMonthly ? (simMonthly.energyProduced / (simMonthly.referenceEnergy || 1)) * 100 : 0;
                    const pvwM = hourlyPR_T_PVWatts?.monthly[i];
                    const pvgM = hourlyPR_T_PVGIS?.monthly[i];
                    return (
                      <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-cyan-50/30'}>
                        <td className="border border-cyan-200 px-2 py-1 font-medium">{monthNames[i]}</td>
                        <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{simPR.toFixed(1)}</td>
                        {hourlyPR_T_PVWatts && <td className="border border-cyan-200 px-2 py-1 text-center font-mono text-cyan-700 font-bold">{pvwM ? (pvwM.pr_t * 100).toFixed(1) : '—'}</td>}
                        {hourlyPR_T_PVWatts && <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{pvwM ? (pvwM.pr * 100).toFixed(1) : '—'}</td>}
                        {hourlyPR_T_PVGIS && <td className="border border-cyan-200 px-2 py-1 text-center font-mono text-emerald-700 font-bold">{pvgM ? (pvgM.pr_t * 100).toFixed(1) : '—'}</td>}
                        {hourlyPR_T_PVGIS && <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{pvgM ? (pvgM.pr * 100).toFixed(1) : '—'}</td>}
                        {hourlyPR_T_PVWatts && <td className="border border-cyan-200 px-2 py-1 text-center font-mono text-orange-600">{pvwM ? pvwM.avgTcell.toFixed(1) : '—'}</td>}
                        {hourlyPR_T_PVGIS && <td className="border border-cyan-200 px-2 py-1 text-center font-mono text-red-600">{pvgM ? pvgM.avgTcell.toFixed(1) : '—'}</td>}
                        {hourlyPR_T_PVWatts && <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{pvwM ? pvwM.totalPOA_kWhm2.toFixed(1) : '—'}</td>}
                        {hourlyPR_T_PVGIS && <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{pvgM ? pvgM.totalPOA_kWhm2.toFixed(1) : '—'}</td>}
                        {hourlyPR_T_PVWatts && <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{pvwM ? pvwM.hoursWithSun : '—'}</td>}
                      </tr>
                    );
                  })}
                  {/* Fila totales/anuales */}
                  <tr className="bg-cyan-100/70 font-bold">
                    <td className="border border-cyan-200 px-2 py-1">ANUAL</td>
                    <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{production.performanceRatio.toFixed(1)}</td>
                    {hourlyPR_T_PVWatts && <td className="border border-cyan-200 px-2 py-1 text-center font-mono text-cyan-800">{(hourlyPR_T_PVWatts.annualPR_T * 100).toFixed(1)}</td>}
                    {hourlyPR_T_PVWatts && <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{(hourlyPR_T_PVWatts.annualPR * 100).toFixed(1)}</td>}
                    {hourlyPR_T_PVGIS && <td className="border border-cyan-200 px-2 py-1 text-center font-mono text-emerald-800">{(hourlyPR_T_PVGIS.annualPR_T * 100).toFixed(1)}</td>}
                    {hourlyPR_T_PVGIS && <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{(hourlyPR_T_PVGIS.annualPR * 100).toFixed(1)}</td>}
                    {hourlyPR_T_PVWatts && <td className="border border-cyan-200 px-2 py-1 text-center font-mono text-orange-700">{hourlyPR_T_PVWatts.avgCellTempWeighted.toFixed(1)}</td>}
                    {hourlyPR_T_PVGIS && <td className="border border-cyan-200 px-2 py-1 text-center font-mono text-red-700">{hourlyPR_T_PVGIS.avgCellTempWeighted.toFixed(1)}</td>}
                    {hourlyPR_T_PVWatts && <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{hourlyPR_T_PVWatts.monthly.reduce((s, m) => s + m.totalPOA_kWhm2, 0).toFixed(0)}</td>}
                    {hourlyPR_T_PVGIS && <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{hourlyPR_T_PVGIS.monthly.reduce((s, m) => s + m.totalPOA_kWhm2, 0).toFixed(0)}</td>}
                    {hourlyPR_T_PVWatts && <td className="border border-cyan-200 px-2 py-1 text-center font-mono">{hourlyPR_T_PVWatts.sunHours}</td>}
                  </tr>
                </tbody>
              </table>
            </div>

            <p className="text-[9px] text-gray-500 mt-2 italic">
              PR_T según IEC 61724-1:2021 Ed.2 §6.4. γ = {(panelSpecs.temperatureCoefficient * 100).toFixed(2)}%/°C. Umbral POA ≥ 50 W/m². 
              {hourlyPR_T_PVWatts && ` PVWatts: ${hourlyPR_T_PVWatts.totalRecords} registros, ${hourlyPR_T_PVWatts.sunHours} h sol.`}
              {hourlyPR_T_PVGIS && ` PVGIS: ${hourlyPR_T_PVGIS.totalRecords} registros, ${hourlyPR_T_PVGIS.sunHours} h sol.`}
            </p>
          </div>
        )}

        {/* ===== ENERGY PERFORMANCE INDEX (EPI) - IEC 61724-1:2021 ===== */}
        {epi !== null && pvwattsData && (
          <div className={`border rounded-lg p-4 mt-4 ${
            epi >= 1.0 ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300' :
            epi >= 0.9 ? 'bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-300' :
            'bg-gradient-to-r from-red-50 to-rose-50 border-red-300'
          }`}>
            <div className="flex items-center gap-2 mb-3">
              <Satellite className="w-4 h-4 text-indigo-600" />
              <h5 className="text-sm font-semibold text-gray-800">Energy Performance Index (EPI) — IEC 61724-1:2021</h5>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                epi >= 1.0 ? 'bg-green-200 text-green-800' :
                epi >= 0.9 ? 'bg-yellow-200 text-yellow-800' :
                'bg-red-200 text-red-800'
              }`}>
                {epi >= 1.0 ? '✅ Óptimo' : epi >= 0.9 ? '⚠️ Aceptable' : '❌ Bajo'}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* EPI Principal */}
              <div className="flex flex-col items-center justify-center bg-white/80 rounded-lg p-4 border border-gray-200">
                <p className="text-[10px] text-gray-500 mb-1">EPI = E_AC / E_benchmark</p>
                <p className={`text-4xl font-mono font-black ${
                  epi >= 1.0 ? 'text-green-700' : epi >= 0.9 ? 'text-yellow-700' : 'text-red-700'
                }`}>
                  {epi.toFixed(3)}
                </p>
                <p className="text-[10px] text-gray-500 mt-1">
                  {epi >= 1.0 ? 'Producción superior al benchmark' :
                   epi >= 0.9 ? 'Producción dentro del rango esperado' :
                   'Producción inferior al esperado'}
                </p>
              </div>
              {/* Comparación */}
              <div className="bg-white/80 rounded-lg p-3 border border-gray-200">
                <p className="text-[10px] text-gray-500 font-medium mb-2">Comparación de Producción AC</p>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] text-gray-600">Simulador (E_AC)</span>
                    <span className="text-sm font-mono font-bold text-blue-700">{Math.round(production.totalACEnergy)} kWh</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] text-gray-600">PVWatts NREL (Benchmark)</span>
                    <span className="text-sm font-mono font-bold text-indigo-700">{Math.round(pvwattsData.annualAC_kWh)} kWh</span>
                  </div>
                  <div className="flex justify-between items-center pt-1 border-t border-gray-200">
                    <span className="text-[10px] text-gray-600">Diferencia</span>
                    <span className={`text-sm font-mono font-bold ${
                      production.totalACEnergy >= pvwattsData.annualAC_kWh ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {production.totalACEnergy >= pvwattsData.annualAC_kWh ? '+' : ''}
                      {Math.round(production.totalACEnergy - pvwattsData.annualAC_kWh)} kWh
                      ({((epi - 1) * 100).toFixed(1)}%)
                    </span>
                  </div>
                </div>
              </div>
              {/* Interpretación */}
              <div className="bg-white/80 rounded-lg p-3 border border-gray-200">
                <p className="text-[10px] text-gray-500 font-medium mb-2">Interpretación IEC 61724</p>
                <div className="text-[10px] text-gray-600 space-y-1">
                  <p>• <strong>EPI ≥ 1.0:</strong> Sistema supera el benchmark satelital. Condiciones locales favorables o modelo conservador.</p>
                  <p>• <strong>0.9 ≤ EPI &lt; 1.0:</strong> Rango aceptable. Diferencias por pérdidas locales no modeladas en PVWatts.</p>
                  <p>• <strong>EPI &lt; 0.9:</strong> Investigar pérdidas excesivas (sombra, suciedad, degradación, fallas).</p>
                  <p className="mt-2 text-gray-500 italic">Benchmark: PVWatts v8 NREL (TMY NSRDB, tilt={pvwattsData.tilt}°, azimuth={pvwattsData.azimuth}°, losses={pvwattsData.losses}%)</p>
                </div>
              </div>
            </div>
            <p className="text-[9px] text-gray-500 mt-2 italic">
              EPI según IEC 61724-1:2021 Ed.2 §7.3. Benchmark satelital: NREL PVWatts v8 con datos TMY del NSRDB. Coord: {pvwattsData.latitude.toFixed(4)}°, {pvwattsData.longitude.toFixed(4)}°.
            </p>
          </div>
        )}
      </div>

      {/* ===== TABLA COMPARATIVA — VALIDACIÓN CRUZADA ===== */}
      {crossValidation && (
        <CrossValidationTable
          comparison={crossValidation}
          onResimultateBIPV={onResimultateBIPV}
          isResimulating={isResimulatingBIPV}
        />
      )}

      {/* ===== GRÁFICO MENSUAL DE YIELD (kWh/kWp) ===== */}
      {crossValidation && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 mb-1">Yield Mensual — Rendimiento Específico (kWh/kWp)</h4>
          <p className="text-xs text-gray-500 mb-4">Comparación de rendimiento específico por mes según IEC 61724 entre todas las fuentes disponibles</p>

          {/* KPI Yield Anual Total */}
          {(() => {
            const sources: { label: string; value: number | null; color: string; bgColor: string; borderColor: string }[] = [
              { label: 'Simulador', value: crossValidation.annualSimulator.yield_kwh_kwp, color: 'text-violet-700', bgColor: 'bg-violet-50', borderColor: 'border-violet-200' },
              ...(crossValidation.hasPVWatts ? [{ label: 'PVWatts', value: crossValidation.annualPVWatts.yield_kwh_kwp, color: 'text-cyan-700', bgColor: 'bg-cyan-50', borderColor: 'border-cyan-200' }] : []),
              ...(crossValidation.hasPVGIS ? [{ label: 'PVGIS', value: crossValidation.annualPVGIS.yield_kwh_kwp, color: 'text-emerald-700', bgColor: 'bg-emerald-50', borderColor: 'border-emerald-200' }] : []),
              ...(crossValidation.hasBIPV ? [{ label: 'IAM+Soiling', value: crossValidation.annualBIPV.yield_kwh_kwp, color: 'text-teal-700', bgColor: 'bg-teal-50', borderColor: 'border-teal-200' }] : []),
            ];
            const validValues = sources.filter(s => s.value !== null && s.value > 0).map(s => s.value as number);
            const mean = validValues.length > 0 ? validValues.reduce((a, b) => a + b, 0) / validValues.length : 0;
            return (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
                {sources.map(src => {
                  const deltaVsMean = src.value && mean > 0 ? ((src.value - mean) / mean) * 100 : null;
                  const deltaColor = deltaVsMean === null ? '' : Math.abs(deltaVsMean) < 5 ? 'text-green-600' : Math.abs(deltaVsMean) < 15 ? 'text-yellow-600' : 'text-red-600';
                  return (
                    <div key={src.label} className={`rounded-lg border ${src.borderColor} ${src.bgColor} p-3 text-center`}>
                      <p className={`text-[10px] font-semibold ${src.color} uppercase tracking-wide mb-1`}>{src.label}</p>
                      <p className={`text-xl font-bold ${src.color}`}>
                        {src.value !== null ? src.value.toFixed(0) : '—'}
                      </p>
                      <p className="text-[10px] text-gray-500 mb-1">kWh/kWp/año</p>
                      {deltaVsMean !== null && (
                        <p className={`text-[10px] font-bold ${deltaColor}`}>
                          {deltaVsMean >= 0 ? '+' : ''}{deltaVsMean.toFixed(1)}% vs media
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })()}
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={crossValidation.rows.map(r => ({
                mes: r.monthName,
                Simulador: r.simulator.yield_kwh_kwp,
                ...(crossValidation.hasPVWatts ? { PVWatts: r.pvwatts.yield_kwh_kwp } : {}),
                ...(crossValidation.hasPVGIS ? { PVGIS: r.pvgis.yield_kwh_kwp } : {}),
                ...(crossValidation.hasBIPV ? { 'IAM+Soiling': r.bipv.yield_kwh_kwp } : {}),
              }))}
              margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="mes" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} label={{ value: 'kWh/kWp', angle: -90, position: 'insideLeft', style: { fontSize: 11 } }} />
              <Tooltip
                contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e2e8f0' }}
                formatter={(value: number) => [value !== null ? value.toFixed(1) : '—', '']}
                labelFormatter={(label) => `Mes: ${label}`}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="Simulador" fill="#7c3aed" radius={[3, 3, 0, 0]} />
              {crossValidation.hasPVWatts && <Bar dataKey="PVWatts" fill="#06b6d4" radius={[3, 3, 0, 0]} />}
              {crossValidation.hasPVGIS && <Bar dataKey="PVGIS" fill="#10b981" radius={[3, 3, 0, 0]} />}
              {crossValidation.hasBIPV && <Bar dataKey="IAM+Soiling" fill="#14b8a6" radius={[3, 3, 0, 0]} />}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ===== ALERTA DE DESVIACIÓN EXCESIVA S-BIPV ===== */}
      {crossValidation && crossValidation.hasBIPV && (
        <BIPVDeviationAlert
          comparison={crossValidation}
          onResyncParams={bipvData ? () => {
            setIsResyncingParams(true);
            // Re-aplicar el bridge BIPV con la lógica corregida
            setBipvApplied(false);
            // El useEffect del bridge se re-ejecutará automáticamente
            setTimeout(() => {
              setBipvApplied(false);
              setIsResyncingParams(false);
            }, 500);
          } : undefined}
          isResyncing={isResyncingParams}
        />
      )}

      {/* Production Chart - DC vs AC con PVGIS */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-semibold text-gray-900 mb-4">Producción Mensual de Energía (DC y AC)</h4>
        <ResponsiveContainer width="100%" height={350}>
          <ComposedChart data={production.monthlyData.map((d: any, idx: number) => ({
            ...d,
            energyDC: d.dcEnergy,
            energyAC: d.energyProduced,
            pvgisAC: pvgisData?.monthlyData?.[idx]?.productionCorrectedAC_kWh ?? null,
            pvwattsAC: pvwattsData?.monthlyData?.[idx]?.ac_kWh ?? null,
            bipvAC: bipvData?.produccionMensualKwh?.[idx] ?? null,
            shadingPct: shadingFactors[idx] * 100,
          }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="month" stroke="#6B7280" />
            <YAxis yAxisId="left" stroke="#6B7280" label={{ value: 'Energía (kWh/mes)', angle: -90, position: 'insideLeft' }} />
            <YAxis yAxisId="right" orientation="right" stroke="#F59E0B" label={{ value: 'FS (%)', angle: 90, position: 'insideRight' }} domain={[0, 100]} />
            <Tooltip contentStyle={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: '8px' }} />
            <Legend />
            <Bar yAxisId="left" dataKey="energyDC" fill="#3B82F6" name="Producción DC (kWh/mes)" radius={[4, 4, 0, 0]} opacity={0.4} />
            <Bar yAxisId="left" dataKey="energyAC" fill="#10B981" name="Producción AC (kWh/mes)" radius={[4, 4, 0, 0]} />
            {pvgisData && pvgisData.monthlyData && (
              <Line yAxisId="left" type="monotone" dataKey="pvgisAC" stroke="#8B5CF6" strokeWidth={2.5} strokeDasharray="6 3" name="PVGIS AC (kWh/mes)" dot={{ r: 3 }} connectNulls />
            )}
            {pvwattsData && pvwattsData.monthlyData && (
              <Line yAxisId="left" type="monotone" dataKey="pvwattsAC" stroke="#6366F1" strokeWidth={2.5} strokeDasharray="4 4" name="PVWatts AC (kWh/mes)" dot={{ r: 3, fill: '#6366F1' }} connectNulls />
            )}
            {bipvData && bipvData.produccionMensualKwh && (
              <Line yAxisId="left" type="monotone" dataKey="bipvAC" stroke="#14B8A6" strokeWidth={2.5} strokeDasharray="8 3" name="IAM+Soiling BIPV (kWh/mes)" dot={{ r: 4, fill: '#14B8A6', stroke: '#0D9488', strokeWidth: 1 }} connectNulls />
            )}
            <Line yAxisId="right" type="monotone" dataKey="shadingPct" stroke="#F59E0B" strokeWidth={2} strokeDasharray="5 5" name="Factor Sombreado (%)" dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
        <div className="flex flex-wrap gap-4 mt-2 text-xs text-gray-500">
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-500 rounded opacity-40"></span> DC = antes de inversor</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-500 rounded"></span> AC = después de inversor</span>
          {pvgisData && <span className="flex items-center gap-1"><span className="w-3 h-1 bg-purple-500 rounded"></span> PVGIS = satelital corregido</span>}
          {pvwattsData && <span className="flex items-center gap-1"><span className="w-3 h-1 bg-indigo-500 rounded"></span> PVWatts = NREL TMY</span>}
          {bipvData && <span className="flex items-center gap-1"><span className="w-3 h-1 bg-teal-500 rounded"></span> IAM+Soiling = modelo BIPV</span>}
        </div>
      </div>

      {/* DC vs AC Power - Energía mensual */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-semibold text-gray-900 mb-4">Energía DC vs AC Mensual (kWh/mes)</h4>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={production.monthlyData.map((d: any) => ({
            ...d,
            dcEnergy_kWh: d.dcEnergy, // kWh/mes DC (ya calculado en el motor)
            acEnergy_kWh: d.energyProduced, // kWh/mes AC
            losses_kWh: d.dcEnergy - d.energyProduced, // Pérdidas BOS = DC - AC (siempre ≥ 0)
          }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="month" stroke="#6B7280" />
            <YAxis stroke="#6B7280" label={{ value: 'Energía (kWh/mes)', angle: -90, position: 'insideLeft' }} />
            <Tooltip contentStyle={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: '8px' }} formatter={(value: any, name: string) => [`${typeof value === 'number' ? value.toFixed(1) : value} kWh/mes`, name]} />
            <Legend />
            <Line type="monotone" dataKey="dcEnergy_kWh" stroke="#3B82F6" strokeWidth={2.5} name="Energía DC (kWh/mes)" dot={{ r: 3 }} />
            <Line type="monotone" dataKey="acEnergy_kWh" stroke="#10B981" strokeWidth={2.5} name="Energía AC (kWh/mes)" dot={{ r: 3 }} />
            <Line type="monotone" dataKey="losses_kWh" stroke="#EF4444" strokeWidth={1.5} strokeDasharray="4 4" name="Pérdidas BOS (kWh/mes)" dot={false} />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-xs text-gray-500 mt-2">DC = potencia generada por los paneles. AC = potencia entregada a la red (después de inversor y pérdidas). Pérdidas BOS = diferencia DC - AC.</p>
      </div>

      {/* Losses Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 mb-4">Desglose de Pérdidas</h4>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={lossesData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {lossesData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: any) => `${typeof value === 'number' ? value.toFixed(1) : value}%`} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 mb-4">Temperatura de Célula Mensual</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={production.monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="month" stroke="#6B7280" />
              <YAxis stroke="#6B7280" label={{ value: 'Temperatura (°C)', angle: -90, position: 'insideLeft' }} />
              <Tooltip contentStyle={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: '8px' }} />
              <Legend />
              <Line type="monotone" dataKey="cellTemperature" stroke="#EF4444" strokeWidth={2} name="T° Célula" />
              <Line type="monotone" dataKey="avgTemp" stroke="#3B82F6" strokeWidth={2} name="T° Ambiente" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Financial Analysis */}
      <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <DollarSign size={20} className="text-emerald-600" />
          Análisis Financiero
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded p-4 border border-emerald-100">
            <p className="text-sm text-gray-600 mb-1">Ingreso Anual</p>
            <p className="text-2xl font-mono font-bold text-emerald-700">${financials.annualRevenue.toLocaleString(undefined, {maximumFractionDigits: 0})}</p>
            <p className="text-xs text-gray-500">por energía generada</p>
          </div>

          <div className="bg-white rounded p-4 border border-emerald-100">
            <p className="text-sm text-gray-600 mb-1">Payback Period</p>
            <p className="text-2xl font-mono font-bold text-emerald-700">{financials.paybackPeriod.toFixed(1)}</p>
            <p className="text-xs text-gray-500">años</p>
          </div>

          <div className="bg-white rounded p-4 border border-emerald-100">
            <p className="text-sm text-gray-600 mb-1">ROI 10 Años</p>
            <p className="text-2xl font-mono font-bold text-emerald-700">{financials.roi10Years.toFixed(0)}%</p>
            <p className="text-xs text-gray-500">retorno</p>
          </div>

          <div className="bg-white rounded p-4 border border-emerald-100">
            <p className="text-sm text-gray-600 mb-1">ROI 25 Años</p>
            <p className="text-2xl font-mono font-bold text-emerald-700">{financials.roi25Years.toFixed(0)}%</p>
            <p className="text-xs text-gray-500">retorno</p>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-900">
        <p><strong>Nota:</strong> Este simulador integra tres fuentes de datos: (1) <strong>Sombreado</strong> desde la pestaña Calculadora (factores FS mensuales), (2) <strong>Meteorología</strong> del archivo EPW cargado (irradiancia POA, temperatura), y (3) <strong>Especificaciones del panel</strong> del catálogo HIITIO/genérico seleccionado. La <strong>Calculadora de Área</strong> determina automáticamente cuántos paneles caben según las dimensiones reales del panel y el factor de separación configurado.</p>
      </div>
    </div>
  );
}
