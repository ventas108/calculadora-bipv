/**
 * Simulador de Vidrios Fotovoltaicos BIPV
 * 
 * Componente que integra:
 * - Selección de tecnología de vidrio (1G/2G/3G)
 * - Niveles de transparencia
 * - Modelo IAM ASHRAE (reflexión geométrica)
 * - Soiling estacional (suciedad/contaminación)
 * - Modelo térmico confinado BIPV
 * - Modelo de transposición Perez (anisótropo) o Isotrópico (Liu-Jordan)
 * - Simulación comparativa multi-tecnología × multi-transparencia
 * - Persistencia de simulaciones con resultados horarios
 * - Historial y comparador de escenarios guardados
 * - Exportación CSV de resultados horarios
 */

import { useState, useMemo, useCallback } from 'react';
import { useCustomPanels, CustomPanelLocal } from '@/hooks/useCustomPanels';
import PanelTechSelector from '@/components/PanelTechSelector';
import PDFPanelImporter from '@/components/PDFPanelImporter';
import { DEFAULT_PANEL_TECHNOLOGIES, PanelTechnology } from '@/lib/panelTechnologies';
import { BIPVToEnergyData } from '@/lib/bipvToEnergyBridge';
import BIPVROIOptimizer from '@/components/BIPVROIOptimizer';
import { useAuth } from '@/_core/hooks/useAuth';
import { trpc } from '@/lib/trpc';
import {
  calculateIAM_ASHRAE,
  calculateAOI,
  calculateSoiling,
  calculateThermalBIPV,
  calculateAdjustedEfficiency,
  calculateBIPVPower,
  calculatePassiveLighting,
  calculatePOATransposition,
  applyIAM,
  evaluateObstacleShading,
  runBIPVSimulation,
  DEFAULT_SOILING_CONFIG,
  type BIPVSimulationSummary,
  type BIPVSimulationConfig,
  type BIPVHourlyResult,
  type WeatherHourData,
  type SoilingConfig,
  type BIPVGlassTechnology,
  type TranspositionModel,
} from '@/lib/iamSoilingEngine';
import {
  BIPV_GLASS_CATALOG,
  TRANSPARENCY_LEVELS,
  SOILING_PRESETS,
  THERMAL_MOUNTING_TYPES,
  type TransparencyLevel,
} from '@/lib/bipvGlassCatalog';
import { calculateSolarPosition } from '@/lib/solarPosition';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import {
  runROIScenario,
  calculateBIPVSHGC,
  DEFAULT_BIPV_COSTS,
  DEFAULT_ENERGY_PARAMS,
  DEFAULT_INCENTIVES_COLOMBIA,
  DEFAULT_HVAC_PARAMS,
  type ROIScenarioResult,
} from '@/lib/bipvROIOptimizer';

/** Tipo de superficie arquitectónica BIPV */
export type BIPVSurfaceType = 'fachada' | 'ventana' | 'pergola' | 'marquesina' | 'pasamano' | 'techo' | 'lucernario' | 'muro_cortina';

/** Superficie arquitectónica para simulación BIPV multi-superficie */
export interface ArchitecturalSurface {
  id: string;
  name: string;
  type: BIPVSurfaceType;
  tilt: number;          // Inclinación en grados (0=horizontal, 90=vertical)
  azimuth: number;       // Azimut en grados (0=Sur)
  area: number;          // Área en m²
  mountingType: string;  // ID del tipo de montaje térmico
  enabled: boolean;      // Incluir en simulación
  fromModel?: boolean;   // Proviene del modelo 3D
  facadeIdx?: number;    // Índice de la fachada en el modelo 3D
}

/** Configuraciones por defecto de superficies arquitectónicas */
const SURFACE_TYPE_DEFAULTS: Record<BIPVSurfaceType, { tilt: number; mountingType: string; label: string; icon: string }> = {
  fachada: { tilt: 90, mountingType: 'fachada_confinada', label: 'Fachada', icon: '🏢' },
  ventana: { tilt: 90, mountingType: 'fachada_confinada', label: 'Ventana', icon: '🪟' },
  pergola: { tilt: 10, mountingType: 'pergola_ventilada', label: 'Pérgola', icon: '☕' },
  marquesina: { tilt: 15, mountingType: 'pergola_ventilada', label: 'Marquesina', icon: '🏪' },
  pasamano: { tilt: 60, mountingType: 'fachada_confinada', label: 'Pasamano/Baranda', icon: '🪧' },
  techo: { tilt: 5, mountingType: 'cubierta_integrada', label: 'Techo/Cubierta', icon: '🏠' },
  lucernario: { tilt: 30, mountingType: 'pergola_ventilada', label: 'Lucernario/Skylight', icon: '🔳' },
  muro_cortina: { tilt: 90, mountingType: 'fachada_confinada', label: 'Muro Cortina', icon: '🏛️' },
};

interface BIPVGlassSimulatorProps {
  /** Callback para enviar resultados al Simulador de Energía */
  onSendToEnergySimulator?: (data: BIPVToEnergyData) => void;
  /** Datos EPW parseados */
  weatherData?: Array<{
    month: number;
    day: number;
    hour: number;
    ghi: number;
    dni: number;
    dhi: number;
    temperature: number;
    windSpeed?: number;
    precipitableWater?: number;
  }>;
  /** Latitud del sitio */
  latitude: number;
  /** Longitud del sitio */
  longitude: number;
  /** Zona horaria (offset UTC) */
  timezone: number;
  /** Fachadas del modelo 3D importado */
  facades?: Array<{
    name: string;
    azimuthNormal: number;
    tilt: number;
    area?: number;
  }>;
  /** Obstáculos del diagrama solar (formato simplificado angular) */
  obstacles?: Array<{
    azimutInicio: number;
    azimutFin: number;
    alturaAngular: number;
  }>;
  /** Obstáculos poligonales del diagrama solar (polígonos SVG con vértices azimut/altitud) */
  obstaclePolygons?: Array<{
    id: string;
    name: string;
    vertices: Array<{ azimuth: number; altitude: number }>;
    visible: boolean;
  }>;
  /** Vértices 3D de obstáculos del modelo importado */
  obstacleVertices3D?: Array<Array<{ x: number; y: number; z: number }>>;
  /** North offset del modelo 3D */
  modelNorthOffset?: number;
  /** Análisis de sombreado 3D por fachada (factores mensuales) */
  facadeAnalysis3D?: {
    facadeName: string;
    facadeIdx: number;
    azimuth: number;
    tilt: number;
    area: number;
    monthlyShadingFactors: number[];
    annualFS: number;
    annualShadingLoss: number;
  } | null;
  /** Factores de sombreado mensuales (manuales o de fachada) */
  shadingFactors?: number[];
  /** Indica si hay datos de irradiación cargados (EPW/PVGIS/PVWatts) para validar orden de importación */
  hasIrradianceData?: boolean;
}

// ─── Mapeo de CustomPanelLocal a BIPVGlassTechnology ──────────────────────────
function customPanelToBIPVGlass(p: CustomPanelLocal): BIPVGlassTechnology {
  return {
    id: `custom_${p.localId}`,
    name: p.name,
    generation: '3G' as const,
    generationLabel: 'Panel Personalizado',
    eficienciaBase: p.efficiency / 100,  // % → 0-1
    coefTemperatura: p.tempCoeff / 100,  // %/°C → fracción/°C
    noct: p.noct,
    b0Ashrae: 0.05,  // Default ASHRAE para vidrio estándar
    description: `Panel personalizado: ${p.name} (${p.powerRating}W, ${p.efficiency}% STC)`,
  };
}

// ─── Mapeo de PanelTechnology a BIPVGlassTechnology ──────────────────────────
function panelTechToBIPVGlass(p: PanelTechnology): BIPVGlassTechnology {
  const isCdTe = p.pvgisTechchoice === 'CdTe';
  const gen: '1G' | '2G' | '3G' = isCdTe ? '2G' : '3G';
  return {
    id: `panel_${p.id}`,
    name: p.name,
    generation: gen,
    generationLabel: isCdTe ? '2ª Generación / CdTe' : '3ª Generación / Personalizado',
    eficienciaBase: p.efficiencySTC / 100,  // % → 0-1
    coefTemperatura: p.tempCoeffPmax / 100,  // %/°C → fracción/°C
    noct: p.noct,
    b0Ashrae: isCdTe ? 0.045 : 0.05,
    description: `${p.description} (${p.pmax}W)`,
  };
}

export default function BIPVGlassSimulator({
  weatherData,
  latitude,
  longitude,
  timezone,
  facades,
  obstacles = [],
  obstaclePolygons = [],
  obstacleVertices3D,
  modelNorthOffset = 0,
  facadeAnalysis3D,
  shadingFactors,
  onSendToEnergySimulator,
  hasIrradianceData = false,
}: BIPVGlassSimulatorProps) {
  // ─── Auth ──────────────────────────────────────────────────────────────
  const { user, isAuthenticated } = useAuth();

  // ─── Paneles Personalizados Persistentes ────────────────────────────────
  const { panels: savedPanelsRaw, savePanel, deletePanel, isSyncing: panelsSyncing } = useCustomPanels();

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

  // Convertir paneles guardados a BIPVGlassTechnology para la simulación
  const customBIPVTechs = useMemo<BIPVGlassTechnology[]>(() => {
    return savedPanelsRaw.map(customPanelToBIPVGlass);
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
  }, [savePanel]);

  const handleDeletePanelPersist = useCallback((panelId: string) => {
    const localId = panelId.replace('saved_', '');
    deletePanel(localId);
  }, [deletePanel]);

  // Panel seleccionado para agregar a la simulación BIPV
  const [selectedCustomPanel, setSelectedCustomPanel] = useState<PanelTechnology>(DEFAULT_PANEL_TECHNOLOGIES[0]);
  const [customPanelYears, setCustomPanelYears] = useState(0);

  // ─── Estado ─────────────────────────────────────────────────────────────
  const [selectedTechs, setSelectedTechs] = useState<string[]>(
    BIPV_GLASS_CATALOG.map(t => t.id)
  );
  const [selectedTransparencies, setSelectedTransparencies] = useState<number[]>([0.10, 0.20, 0.40]);
  const [soilingPresetId, setSoilingPresetId] = useState('tropical_urbano');
  const [mountingTypeId, setMountingTypeId] = useState('fachada_confinada');
  const [customArea, setCustomArea] = useState<number>(120);
  const [customTilt, setCustomTilt] = useState<number>(90);
  const [customAzimuth, setCustomAzimuth] = useState<number>(180);
  const [useFacadeFromModel, setUseFacadeFromModel] = useState(false);
  const [selectedFacadeIdx, setSelectedFacadeIdx] = useState(0);
  // Multi-superficie arquitectónica
  const [architecturalSurfaces, setArchitecturalSurfaces] = useState<ArchitecturalSurface[]>([]);
  const [useMultiSurface, setUseMultiSurface] = useState(false);
  const [applyShadingFactors, setApplyShadingFactors] = useState(true);
  const [isSimulating, setIsSimulating] = useState(false);
  const [results, setResults] = useState<BIPVSimulationSummary[] | null>(null);
  const [activeTab, setActiveTab] = useState<'config' | 'results' | 'losses' | 'history' | 'comparison'>('config');
  const [transpositionModel, setTranspositionModel] = useState<TranspositionModel>('isotropic');
  const [generateHourly, setGenerateHourly] = useState(false);

  // ─── Auto-optimizador ──────────────────────────────────────────────────
  const [autoOptRunning, setAutoOptRunning] = useState(false);
  const [autoOptResults, setAutoOptResults] = useState<Array<{
    rank: number;
    techName: string;
    techId: string;
    transparency: number;
    surfaceName: string;
    surfaceIdx: number;
    tilt: number;
    azimuth: number;
    area: number;
    kwhYear: number;
    kwhM2: number;
    produccionMensualKwh: number[];
    iamPromedio: number;
    soilingPromedio: number;
    factorTermicoPromedio: number;
    iamMensual?: number[];
    soilingMensual?: number[];
    roi25: number;
    payback: number;
    npv25: number;
    lcoe: number;
    irr: number;
    isViable: boolean;
  }> | null>(null);
  const [autoOptExpanded, setAutoOptExpanded] = useState(false);
  // Filtro: paneles seleccionados para evaluar (por índice en el ranking)
  const [selectedRankingItems, setSelectedRankingItems] = useState<Set<number>>(new Set());
  const [showOnlySelected, setShowOnlySelected] = useState(false);

  // ─── Guardar Simulación ─────────────────────────────────────────────────
  const [saveName, setSaveName] = useState('');
  const [saveNotes, setSaveNotes] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [selectedResultIdx, setSelectedResultIdx] = useState(0);

  // ─── Historial ──────────────────────────────────────────────────────────
  const [compareIds, setCompareIds] = useState<number[]>([]);

  // ─── tRPC queries ───────────────────────────────────────────────────────
  const historyQuery = trpc.bipvSimulations.list.useQuery(undefined, {
    enabled: isAuthenticated,
  });
  const compareQuery = trpc.bipvSimulations.compare.useQuery(
    { ids: compareIds },
    { enabled: compareIds.length >= 2 }
  );
  const saveWithHourlyMutation = trpc.bipvSimulations.saveWithHourly.useMutation();
  const deleteMutation = trpc.bipvSimulations.delete.useMutation();

  // ─── Derivados ──────────────────────────────────────────────────────────
  const soilingPreset = useMemo(
    () => SOILING_PRESETS.find(p => p.id === soilingPresetId) || SOILING_PRESETS[0],
    [soilingPresetId]
  );
  const mountingType = useMemo(
    () => THERMAL_MOUNTING_TYPES.find(m => m.id === mountingTypeId) || THERMAL_MOUNTING_TYPES[2],
    [mountingTypeId]
  );

  // ─── Convertir polígonos de obstáculos a formato angular simplificado ────
  const effectiveObstacles = useMemo(() => {
    if (obstacles.length > 0) return obstacles;
    // Convertir ObstaclePolygon[] a formato angular simplificado
    if (obstaclePolygons.length > 0) {
      return obstaclePolygons
        .filter(p => p.visible && p.vertices.length >= 2)
        .map(poly => {
          const azimuths = poly.vertices.map(v => ((v.azimuth % 360) + 360) % 360);
          const altitudes = poly.vertices.map(v => v.altitude);
          return {
            azimutInicio: Math.min(...azimuths),
            azimutFin: Math.max(...azimuths),
            alturaAngular: Math.max(...altitudes),
          };
        });
    }
    return [];
  }, [obstacles, obstaclePolygons]);

  // ─── Factores de sombreado mensuales desde análisis 3D o manual ────────────────────
  const is3DActive = !!(useFacadeFromModel && facadeAnalysis3D);

  const { hasManualShading, annualManualLoss } = useMemo(() => {
    const hasShading = !!(shadingFactors && shadingFactors.some(f => f < 1.0));
    const annualLoss = hasShading ? (1 - shadingFactors!.reduce((a, b) => a + b, 0) / 12) * 100 : 0;
    return { hasManualShading: hasShading, annualManualLoss: annualLoss };
  }, [shadingFactors]);

  const monthlyShadingFactors3D = useMemo<number[]>(() => {
    if (applyShadingFactors) {
      if (useFacadeFromModel && facadeAnalysis3D) {
        return facadeAnalysis3D.monthlyShadingFactors;
      }
      if (shadingFactors) {
        return shadingFactors;
      }
    }
    return Array(12).fill(1.0); // Sin sombreado
  }, [useFacadeFromModel, facadeAnalysis3D, shadingFactors, applyShadingFactors]);

  const facadeParams = useMemo(() => {
    if (useFacadeFromModel && facades && facades[selectedFacadeIdx]) {
      const f = facades[selectedFacadeIdx];
      return { tilt: f.tilt || 90, azimuth: f.azimuthNormal || 180, area: f.area || customArea, name: f.name || `Superficie ${selectedFacadeIdx + 1}` };
    }
    return { tilt: customTilt, azimuth: customAzimuth, area: customArea, name: 'Manual' };
  }, [useFacadeFromModel, facades, selectedFacadeIdx, customTilt, customAzimuth, customArea]);

  // ─── Simulación ────────────────────────────────────────────────────────
  const runSimulation = useCallback(() => {
    if (!weatherData || weatherData.length === 0) return;

    setIsSimulating(true);
    setActiveTab('results');

    setTimeout(() => {
      // Combinar catálogo base + paneles personalizados + paneles del selector PanelTech
      const panelTechMapped = selectedCustomPanel ? [panelTechToBIPVGlass(selectedCustomPanel)] : [];
      const allAvailableTechs = [...BIPV_GLASS_CATALOG, ...customBIPVTechs, ...panelTechMapped];
      const technologies = allAvailableTechs.filter(t => selectedTechs.includes(t.id));
      const allResults: BIPVSimulationSummary[] = [];

      const mappedWeather: WeatherHourData[] = weatherData.map(w => ({
        month: w.month,
        day: w.day,
        hour: w.hour,
        ghi: w.ghi,
        dni: w.dni,
        dhi: w.dhi,
        tempAir: w.temperature,
        windSpeed: w.windSpeed || 1,
        precipitableWater: w.precipitableWater,
      }));

      // === MODO MULTI-SUPERFICIE ===
      if (useMultiSurface && architecturalSurfaces.filter(s => s.enabled).length > 0) {
        const enabledSurfaces = architecturalSurfaces.filter(s => s.enabled);
        for (const surface of enabledSurfaces) {
          const surfMounting = THERMAL_MOUNTING_TYPES.find(m => m.id === surface.mountingType) || mountingType;
          for (const tech of technologies) {
            for (const tau of selectedTransparencies) {
              const config: BIPVSimulationConfig = {
                technology: { ...tech, name: `${tech.name} [${surface.name}]` },
                transparencia: tau,
                areaM2: surface.area,
                inclinacionFachada: surface.tilt,
                azimutFachada: surface.azimuth,
                soiling: soilingPreset.config,
                kBipv: surfMounting.kBipv,
                transpositionModel,
                generateHourlyResults: generateHourly,
              };
              const summary = runBIPVSimulation(
                mappedWeather,
                latitude, longitude, timezone,
                config, effectiveObstacles,
                monthlyShadingFactors3D
              );
              allResults.push(summary);
            }
          }
        }
      } else {
        // === MODO SUPERFICIE ÚNICA (original) ===
        for (const tech of technologies) {
          for (const tau of selectedTransparencies) {
            const config: BIPVSimulationConfig = {
              technology: tech,
              transparencia: tau,
              areaM2: facadeParams.area,
              inclinacionFachada: facadeParams.tilt,
              azimutFachada: facadeParams.azimuth,
              soiling: soilingPreset.config,
              kBipv: mountingType.kBipv,
              transpositionModel,
              generateHourlyResults: generateHourly,
            };
            const summary = runBIPVSimulation(
              mappedWeather,
              latitude, longitude, timezone,
              config, effectiveObstacles,
              monthlyShadingFactors3D
            );
            allResults.push(summary);
          }
        }
      }

      setResults(allResults);
      setSelectedResultIdx(0);
      setIsSimulating(false);
    }, 50);
  }, [weatherData, latitude, longitude, timezone, selectedTechs, selectedTransparencies, soilingPreset, mountingType, facadeParams, effectiveObstacles, monthlyShadingFactors3D, transpositionModel, generateHourly, customBIPVTechs, useMultiSurface, architecturalSurfaces]);

  // ─── Auto-optimizador: Todas las combinaciones ─────────────────────────
  const runAutoOptimizer = useCallback(() => {
    if (!weatherData || weatherData.length === 0 || !facades || facades.length < 1) return;
    setAutoOptRunning(true);
    setAutoOptResults(null);

    setTimeout(() => {
      const allTechs = [...BIPV_GLASS_CATALOG, ...customBIPVTechs];
      const allTransparencies = TRANSPARENCY_LEVELS.map(t => t.value);
      const surfaces = facades;

      const mappedW: WeatherHourData[] = weatherData.map(w => ({
        month: w.month, day: w.day, hour: w.hour,
        ghi: w.ghi, dni: w.dni, dhi: w.dhi,
        tempAir: w.temperature, windSpeed: w.windSpeed || 1,
        precipitableWater: w.precipitableWater,
      }));

      const combinations: Array<{
        techName: string; techId: string; transparency: number;
        surfaceName: string; surfaceIdx: number;
        tilt: number; azimuth: number; area: number;
        kwhYear: number; kwhM2: number;
        produccionMensualKwh: number[];
        iamPromedio: number; soilingPromedio: number; factorTermicoPromedio: number;
        iamMensual?: number[]; soilingMensual?: number[];
        roi25: number; payback: number; npv25: number; lcoe: number; irr: number; isViable: boolean;
      }> = [];

      for (let si = 0; si < surfaces.length; si++) {
        const surf = surfaces[si];
        const surfArea = surf.area || 30;
        const surfTilt = surf.tilt || 90;
        const surfAzimuth = surf.azimuthNormal || 180;

        for (const tech of allTechs) {
          for (const tau of allTransparencies) {
            // 1. Simular producción energética
            const config: BIPVSimulationConfig = {
              technology: tech,
              transparencia: tau,
              areaM2: surfArea,
              inclinacionFachada: surfTilt,
              azimutFachada: surfAzimuth,
              soiling: soilingPreset.config,
              kBipv: mountingType.kBipv,
              transpositionModel,
              generateHourlyResults: false,
            };
            const summary = runBIPVSimulation(
              mappedW, latitude, longitude, timezone,
              config, effectiveObstacles, monthlyShadingFactors3D
            );

            // 2. Calcular ROI financiero
            const annualPOA = summary.energiaAnualKwhM2 / (summary.eficienciaAjustada || 0.10);
            const bipvSHGC = calculateBIPVSHGC(tau);
            const hvacParams = {
              conventionalSHGC: DEFAULT_HVAC_PARAMS.conventionalSHGC || 0.65,
              bipvSHGC,
              area: surfArea,
              annualPOA: annualPOA > 0 ? annualPOA : 800,
              coolingCOP: DEFAULT_HVAC_PARAMS.coolingCOP || 3.2,
              electricityRate: DEFAULT_ENERGY_PARAMS.electricityBuyRate,
              coolingMonths: DEFAULT_HVAC_PARAMS.coolingMonths || 12,
            };

            const roiResult = runROIScenario(
              `${tech.name} × τ${(tau * 100).toFixed(0)}% × ${surf.name}`,
              '',
              '',
              surfTilt >= 60 ? 'fachada' : 'techo',
              summary.energiaAnualKwh,
              summary.energiaAnualKwhM2,
              surfArea,
              surfTilt,
              surfAzimuth,
              tau,
              DEFAULT_BIPV_COSTS,
              DEFAULT_ENERGY_PARAMS,
              hvacParams,
              DEFAULT_INCENTIVES_COLOMBIA
            );

            combinations.push({
              techName: tech.name,
              techId: tech.id,
              transparency: tau,
              surfaceName: surf.name,
              surfaceIdx: si,
              tilt: surfTilt,
              azimuth: surfAzimuth,
              area: surfArea,
              kwhYear: summary.energiaAnualKwh,
              kwhM2: summary.energiaAnualKwhM2,
              produccionMensualKwh: summary.produccionMensualKwh,
              iamPromedio: summary.iamPromedio,
              soilingPromedio: summary.soilingPromedio,
              factorTermicoPromedio: summary.factorTermicoPromedio,
              iamMensual: summary.iamMensual,
              soilingMensual: summary.soilingMensual,
              roi25: roiResult.roi25Years,
              payback: roiResult.paybackYears,
              npv25: roiResult.npv25Years,
              lcoe: roiResult.lcoe,
              irr: roiResult.irr,
              isViable: roiResult.isViable,
            });
          }
        }
      }

      // Ordenar por ROI 25 años (mayor es mejor)
      combinations.sort((a, b) => b.roi25 - a.roi25);
      const ranked = combinations.map((c, i) => ({ ...c, rank: i + 1 }));
      setAutoOptResults(ranked);
      setAutoOptRunning(false);
      setAutoOptExpanded(true);
    }, 100);
  }, [weatherData, facades, latitude, longitude, timezone, soilingPreset, mountingType, transpositionModel, effectiveObstacles, monthlyShadingFactors3D, customBIPVTechs]);

  // ─── Enviar al Simulador de Energía ───────────────────────────────────────
  const handleSendToEnergy = useCallback(() => {
    if (!results || results.length === 0 || !onSendToEnergySimulator) return;
    const r = results[selectedResultIdx];
    if (!r) return;

    // Buscar la tecnología para obtener coeficientes
    const allTechs = [...BIPV_GLASS_CATALOG, ...customBIPVTechs];
    const tech = allTechs.find(t => t.name === r.technology);

    const bridgeData: BIPVToEnergyData = {
      produccionMensualKwh: r.produccionMensualKwh,
      eficienciaAjustada: r.eficienciaAjustada,
      potenciaPicoW: r.potenciaPicoW,
      tilt: facadeParams.tilt,
      azimuth: facadeParams.azimuth,
      areaM2: facadeParams.area,
      transparencia: r.transparencia,
      technology: r.technology,
      generation: r.generation,
      iamPromedio: r.iamPromedio,
      soilingPromedio: r.soilingPromedio,
      factorTermicoPromedio: r.factorTermicoPromedio,
      energiaAnualKwh: r.energiaAnualKwh,
      energiaAnualKwhM2: r.energiaAnualKwhM2,
      transpositionModel: r.transpositionModel || 'isotropic',
      coefTemperatura: tech ? tech.coefTemperatura * 100 : -0.29,  // 0-1 → %/°C
      noct: tech?.noct ?? 46,
      kBipv: mountingType.kBipv,
      // Nombre de la superficie del modelo 3D
      surfaceName: facadeParams.name || undefined,
      // Sincronizar panel del catálogo con el Simulador de Energía
      panelId: selectedCustomPanel.id,
      panelPmax: selectedCustomPanel.pmax,
      panelEfficiencySTC: selectedCustomPanel.efficiencySTC,
      panelLengthMm: selectedCustomPanel.lengthMm,
      panelWidthMm: selectedCustomPanel.widthMm,
      // IAM y Soiling mensuales variables (12 valores)
      iamMensual: r.iamMensual,
      soilingMensual: r.soilingMensual,
    };

    onSendToEnergySimulator(bridgeData);
  }, [results, selectedResultIdx, facadeParams, mountingType, customBIPVTechs, selectedCustomPanel, onSendToEnergySimulator]);

  // ─── Guardar Simulación ─────────────────────────────────────────────────
  const handleSave = useCallback(async () => {
    if (!results || results.length === 0 || !saveName.trim()) return;
    const r = results[selectedResultIdx];
    if (!r) return;

    setIsSaving(true);
    setSaveSuccess(null);

    try {
      // Preparar datos horarios por mes
      const hourlyData: Array<{ month: number; hourlyData: unknown; monthlySummary: unknown }> = [];
      if (r.hourlyResults && r.hourlyResults.length > 0) {
        for (let m = 1; m <= 12; m++) {
          const monthHours = r.hourlyResults.filter(h => h.month === m);
          if (monthHours.length > 0) {
            hourlyData.push({
              month: m,
              hourlyData: monthHours,
              monthlySummary: {
                energiaKwh: monthHours.reduce((s, h) => s + h.potenciaDcW, 0) / 1000,
                iluminacionKwh: monthHours.reduce((s, h) => s + h.potenciaIluminacionPasivaW, 0) / 1000,
                horasSol: monthHours.length,
                iamPromedio: monthHours.reduce((s, h) => s + h.fIamAshrae, 0) / monthHours.length,
                soilingPromedio: monthHours.reduce((s, h) => s + h.soilingReal, 0) / monthHours.length,
                tCellPromedio: monthHours.reduce((s, h) => s + h.tCell, 0) / monthHours.length,
              },
            });
          }
        }
      }

      await saveWithHourlyMutation.mutateAsync({
        simulation: {
          name: saveName.trim(),
          technology: r.technology,
          generation: r.generation,
          transparencia: r.transparencia,
          eficienciaAjustada: r.eficienciaAjustada,
          areaM2: facadeParams.area,
          inclinacionFachada: facadeParams.tilt,
          azimutFachada: facadeParams.azimuth,
          kBipv: mountingType.kBipv,
          transpositionModel: r.transpositionModel || 'isotropic',
          latitude,
          longitude,
          energiaAnualKwh: r.energiaAnualKwh,
          energiaAnualKwhM2: r.energiaAnualKwhM2,
          potenciaPicoW: r.potenciaPicoW,
          iluminacionPasivaAnualKwh: r.iluminacionPasivaAnualKwh,
          irradianciaReflejadaAnualKwhM2: r.irradianciaReflejadaAnualKwhM2,
          perdidasSoilingAnualKwhM2: r.perdidasSoilingAnualKwhM2,
          perdidasTermicasAnualKwhM2: r.perdidasTermicasAnualKwhM2,
          iamPromedio: r.iamPromedio,
          soilingPromedio: r.soilingPromedio,
          factorTermicoPromedio: r.factorTermicoPromedio,
          factorSombraPromedio: r.factorSombraPromedio,
          horasSimuladas: r.horasSimuladas,
          produccionMensualKwh: JSON.stringify(r.produccionMensualKwh),
          iluminacionMensualKwh: JSON.stringify(r.iluminacionMensualKwh),
          soilingConfig: JSON.stringify(soilingPreset.config),
          notes: saveNotes.trim() || undefined,
        },
        hourlyData,
      });

      setSaveSuccess(`Simulación "${saveName}" guardada correctamente`);
      setSaveName('');
      setSaveNotes('');
      historyQuery.refetch();
    } catch (err: any) {
      setSaveSuccess(`Error: ${err.message || 'No se pudo guardar'}`);
    } finally {
      setIsSaving(false);
    }
  }, [results, selectedResultIdx, saveName, saveNotes, facadeParams, mountingType, latitude, longitude, soilingPreset]);

  // ─── Exportar CSV ───────────────────────────────────────────────────────
  const exportCSV = useCallback(() => {
    if (!results || results.length === 0) return;
    const r = results[selectedResultIdx];
    if (!r || !r.hourlyResults || r.hourlyResults.length === 0) {
      // Exportar resumen mensual si no hay hourly
      const headers = 'Mes,Produccion_kWh,Iluminacion_kWh';
      const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
      const rows = r.produccionMensualKwh.map((kwh, i) => `${months[i]},${kwh.toFixed(2)},${r.iluminacionMensualKwh[i].toFixed(2)}`);
      const csv = [headers, ...rows].join('\n');
      downloadCSV(csv, `bipv_mensual_${r.technology.replace(/\s/g,'_')}_tau${(r.transparencia*100).toFixed(0)}.csv`);
      return;
    }

    // Exportar datos horarios completos
    const headers = 'Timestamp,Mes,Hora,Elevacion_Solar,Azimut_Solar,DNI_Original,DNI_ConSombra,GHI,DHI,POA_Directa,POA_Difusa,POA_Total,POA_Optica,Factor_Sombra,IAM_ASHRAE,Soiling,Factor_Termico,T_Amb,T_Cell,Potencia_DC_W,Iluminacion_W,AOI_deg';
    const rows = r.hourlyResults.map(h =>
      `${h.month}/${h.hour},${h.month},${h.hour},${h.elevacionSolar.toFixed(1)},${h.azimutSolar.toFixed(1)},${h.dniOriginal.toFixed(1)},${h.dniConSombra.toFixed(1)},${h.ghi.toFixed(1)},${h.dhi.toFixed(1)},${h.poaDirecta.toFixed(1)},${h.poaDifusa.toFixed(1)},${h.poaTotal.toFixed(1)},${h.poaTotalOptica.toFixed(1)},${h.factorSombraSF.toFixed(3)},${h.fIamAshrae.toFixed(4)},${h.soilingReal.toFixed(4)},${h.factorTermico.toFixed(4)},${h.tAmb.toFixed(1)},${h.tCell.toFixed(1)},${h.potenciaDcW.toFixed(2)},${h.potenciaIluminacionPasivaW.toFixed(2)},${h.aoiDeg.toFixed(1)}`
    );
    const csv = [headers, ...rows].join('\n');
    downloadCSV(csv, `bipv_horario_${r.technology.replace(/\s/g,'_')}_tau${(r.transparencia*100).toFixed(0)}.csv`);
  }, [results, selectedResultIdx]);

  const downloadCSV = (csv: string, filename: string) => {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ─── Eliminar simulación ────────────────────────────────────────────────
  const handleDelete = useCallback(async (id: number) => {
    if (!confirm('¿Eliminar esta simulación?')) return;
    await deleteMutation.mutateAsync({ id });
    historyQuery.refetch();
  }, []);

  // ─── Toggle comparar ───────────────────────────────────────────────────
  const toggleCompare = (id: number) => {
    setCompareIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id].slice(0, 5)
    );
  };

  // ─── Render ─────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-5 shadow-lg">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="text-2xl">🔬</span>
          Simulador BIPV — IAM + Soiling + Modelo Térmico
        </h3>
        <p className="text-sm text-indigo-100 mt-1">
          Análisis comparativo de vidrios fotovoltaicos 1G/2G/3G con reflexión geométrica ASHRAE, suciedad estacional, modelo térmico confinado y transposición Perez.
        </p>
      </div>

      {/* Banner de Estado de Integración */}
      <div className="bg-white border-2 border-indigo-100 rounded-xl p-4 shadow-sm">
        <h4 className="text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Estado de Integración con Calculadora</h4>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium ${
            weatherData && weatherData.length > 0 ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-gray-50 text-gray-400 border border-gray-200'
          }`}>
            <span>{weatherData && weatherData.length > 0 ? '✅' : '⚪'}</span>
            EPW ({weatherData ? `${weatherData.length} h` : 'No'})
          </div>
          <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium ${
            facades && facades.length > 0 ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-gray-50 text-gray-400 border border-gray-200'
          }`}>
            <span>{facades && facades.length > 0 ? '✅' : '⚪'}</span>
            Modelo 3D ({facades ? facades.length : 0} fachadas)
          </div>
          <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium ${
            effectiveObstacles.length > 0 ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-gray-50 text-gray-400 border border-gray-200'
          }`}>
            <span>{effectiveObstacles.length > 0 ? '✅' : '⚪'}</span>
            Obstáculos ({effectiveObstacles.length})
          </div>
          <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium ${
            (is3DActive || hasManualShading) ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-gray-50 text-gray-400 border border-gray-200'
          }`}>
            <span>{(is3DActive || hasManualShading) ? '✅' : '⚪'}</span>
            Sombreado {is3DActive ? `3D (${(facadeAnalysis3D.annualShadingLoss).toFixed(0)}%)` : hasManualShading ? `Manual (${annualManualLoss.toFixed(0)}%)` : '(No)'}
          </div>
          <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium ${
            latitude !== 6.25 ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
          }`}>
            <span>{latitude !== 6.25 ? '✅' : '⚠️'}</span>
            Ubicación ({latitude.toFixed(2)}°, {longitude.toFixed(2)}°)
          </div>
        </div>
        {!weatherData && (
          <p className="text-xs text-amber-600 mt-2 font-medium">
            ⚠️ Cargue un archivo EPW en la Calculadora o seleccione una ciudad para habilitar la simulación con datos climáticos reales.
          </p>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 border border-gray-200 rounded-xl p-1.5 overflow-x-auto shadow-sm">
        {(['config', 'results', 'losses', 'history', 'comparison'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2.5 px-3 rounded-lg text-sm font-semibold transition-all whitespace-nowrap ${
              activeTab === tab
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-gray-600 hover:text-indigo-700 hover:bg-indigo-50'
            }`}
          >
            {tab === 'config' ? '⚙️ Config' : tab === 'results' ? '📊 Resultados' : tab === 'losses' ? '📉 Pérdidas' : tab === 'history' ? '💾 Historial' : '📈 Comparar'}
          </button>
        ))}
      </div>

      {/* Tab: Configuración */}
      {activeTab === 'config' && (
        <div className="space-y-4">
          {/* Modelo de Transposición */}
          <div className="bg-white border-2 border-indigo-100 rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-bold text-gray-800 mb-3">Modelo de Transposición Solar</h4>
            <div className="grid grid-cols-2 gap-3">
              <label className={`flex flex-col p-3 rounded-xl border-2 cursor-pointer transition-all ${
                transpositionModel === 'isotropic' ? 'border-emerald-500 bg-emerald-50' : 'border-gray-200 hover:border-gray-300 bg-gray-50'
              }`}>
                <div className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="transModel"
                    checked={transpositionModel === 'isotropic'}
                    onChange={() => setTranspositionModel('isotropic')}
                    className="text-emerald-600"
                  />
                  <span className="text-sm font-semibold text-gray-800">Isotrópico (Liu-Jordan)</span>
                </div>
                <p className="text-xs text-gray-600 mt-1 ml-5">Difusa uniforme desde todo el cielo. Más simple, conservador.</p>
              </label>
              <label className={`flex flex-col p-3 rounded-xl border-2 cursor-pointer transition-all ${
                transpositionModel === 'perez' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300 bg-gray-50'
              }`}>
                <div className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="transModel"
                    checked={transpositionModel === 'perez'}
                    onChange={() => setTranspositionModel('perez')}
                    className="text-blue-600"
                  />
                  <span className="text-sm font-semibold text-gray-800">Perez (Anisótropo)</span>
                </div>
                <p className="text-xs text-gray-600 mt-1 ml-5">Circunsolar + horizonte + isótropo. Más preciso para fachadas.</p>
              </label>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <input
                type="checkbox"
                id="generateHourly"
                checked={generateHourly}
                onChange={(e) => setGenerateHourly(e.target.checked)}
                className="rounded border-gray-400 text-indigo-600"
              />
              <label htmlFor="generateHourly" className="text-xs text-gray-700">
                Generar resultados horarios detallados (permite exportar CSV y guardar con datos completos)
              </label>
            </div>
          </div>

          {/* Tecnologías */}
          <div className="bg-white border-2 border-purple-100 rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-bold text-gray-800 mb-3">Tecnologías de Vidrio BIPV</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {BIPV_GLASS_CATALOG.map(tech => (
                <label
                  key={tech.id}
                  className={`flex flex-col p-3 rounded-xl border-2 cursor-pointer transition-all ${
                    selectedTechs.includes(tech.id)
                      ? 'border-purple-500 bg-purple-50 shadow-sm'
                      : 'border-gray-200 bg-gray-50 hover:border-purple-300'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <input
                      type="checkbox"
                      checked={selectedTechs.includes(tech.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedTechs([...selectedTechs, tech.id]);
                        } else {
                          setSelectedTechs(selectedTechs.filter(id => id !== tech.id));
                        }
                      }}
                      className="rounded border-gray-400 text-purple-600"
                    />
                    <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                      tech.generation === '1G' ? 'bg-emerald-100 text-emerald-700' :
                      tech.generation === '2G' ? 'bg-blue-100 text-blue-700' :
                      'bg-orange-100 text-orange-700'
                    }`}>
                      {tech.generation}
                    </span>
                    <span className="text-sm font-semibold text-gray-800">{tech.name}</span>
                  </div>
                  <div className="text-xs text-gray-600 space-y-0.5">
                    <div>η = {(tech.eficienciaBase * 100).toFixed(0)}% | b₀ = {tech.b0Ashrae}</div>
                    <div>γ = {(tech.coefTemperatura * 100).toFixed(2)}%/°C | NOCT = {tech.noct}°C</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Paneles Personalizados / HIITIO / EINNOVA */}
          {customBIPVTechs.length > 0 && (
            <div className="bg-white border-2 border-teal-100 rounded-xl p-5 shadow-sm">
              <h4 className="text-sm font-bold text-gray-800 mb-3">Paneles Personalizados / Otras Marcas</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {customBIPVTechs.map(tech => (
                  <label
                    key={tech.id}
                    className={`flex flex-col p-3 rounded-xl border-2 cursor-pointer transition-all ${
                      selectedTechs.includes(tech.id)
                        ? 'border-teal-500 bg-teal-50 shadow-sm'
                        : 'border-gray-200 bg-gray-50 hover:border-teal-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <input
                        type="checkbox"
                        checked={selectedTechs.includes(tech.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedTechs([...selectedTechs, tech.id]);
                          } else {
                            setSelectedTechs(selectedTechs.filter(id => id !== tech.id));
                          }
                        }}
                        className="rounded border-gray-400 text-teal-600"
                      />
                      <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-teal-100 text-teal-700">
                        Custom
                      </span>
                      <span className="text-sm font-semibold text-gray-800 truncate">{tech.name}</span>
                    </div>
                    <div className="text-xs text-gray-600 space-y-0.5">
                      <div>η = {(tech.eficienciaBase * 100).toFixed(1)}% | b₀ = {tech.b0Ashrae}</div>
                      <div>γ = {(tech.coefTemperatura * 100).toFixed(2)}%/°C | NOCT = {tech.noct}°C</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Agregar Panel Personalizado */}
          <div className="bg-white border-2 border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
            <h4 className="text-sm font-bold text-gray-800 mb-3">Agregar Panel de Otra Marca / Referencia</h4>
            <p className="text-xs text-gray-600 mb-3">Seleccione un panel del catálogo HIITIO/EINNOVA, importe una ficha técnica PDF, o cree uno personalizado para incluirlo en la simulación IAM+Soiling.</p>
            <PDFPanelImporter
              onApplyParams={(partial) => {
                // Crear un PanelTechnology a partir de los datos extraídos del PDF
                const newPanel: PanelTechnology = {
                  ...selectedCustomPanel,
                  ...partial,
                  id: `pdf_${Date.now()}`,
                  isCustom: true,
                  brand: 'custom' as any,
                  category: 'custom' as any,
                  color: '#8B5CF6',
                  hiitioId: '',
                  priceUSD: 0,
                  pricePerWp: 0,
                };
                setSelectedCustomPanel(newPanel);
                // Auto-agregar a la simulación
                const bipvTech = panelTechToBIPVGlass(newPanel);
                if (!selectedTechs.includes(bipvTech.id)) {
                  setSelectedTechs([...selectedTechs, bipvTech.id]);
                }
              }}
            />
            <PanelTechSelector
              selectedTech={selectedCustomPanel}
              onSelectTech={(tech) => {
                setSelectedCustomPanel(tech);
                // Auto-agregar a la simulación como BIPVGlassTechnology
                const bipvTech = panelTechToBIPVGlass(tech);
                if (!selectedTechs.includes(bipvTech.id)) {
                  setSelectedTechs([...selectedTechs, bipvTech.id]);
                }
              }}
              yearsFromInstall={customPanelYears}
              onYearsChange={setCustomPanelYears}
              savedPanels={savedPanelsTech}
              onSavePanel={handleSavePanelPersist}
              onDeletePanel={handleDeletePanelPersist}
            />
          </div>

          {/* Transparencia */}
          <div className="bg-white border-2 border-cyan-100 rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-bold text-gray-800 mb-3">Niveles de Transparencia</h4>
            <div className="flex flex-wrap gap-2">
              {TRANSPARENCY_LEVELS.map(level => (
                <label
                  key={level.value}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full border-2 cursor-pointer text-sm font-medium transition-all ${
                    selectedTransparencies.includes(level.value)
                      ? 'border-cyan-500 bg-cyan-50 text-cyan-700 shadow-sm'
                      : 'border-gray-200 text-gray-600 hover:border-cyan-300 bg-gray-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedTransparencies.includes(level.value)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTransparencies([...selectedTransparencies, level.value].sort());
                      } else {
                        setSelectedTransparencies(selectedTransparencies.filter(v => v !== level.value));
                      }
                    }}
                    className="hidden"
                  />
                  <span>τ = {level.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Geometría de Fachada */}
          <div className="bg-white border-2 border-amber-100 rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-bold text-gray-800 mb-3">Geometría de Fachada</h4>
            {facades && facades.length > 0 && (
              <div className="mb-3">
                <label className="flex items-center gap-2 text-sm text-gray-700 mb-2 font-medium">
                  <input
                    type="checkbox"
                    checked={useFacadeFromModel}
                    onChange={(e) => setUseFacadeFromModel(e.target.checked)}
                    className="rounded border-gray-400 text-amber-600"
                  />
                  Usar fachada del modelo 3D importado
                </label>
                {useFacadeFromModel && (
                  <select
                    value={selectedFacadeIdx}
                    onChange={(e) => setSelectedFacadeIdx(Number(e.target.value))}
                    className="w-full bg-gray-50 border-2 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 font-medium"
                  >
                    {facades.map((f, i) => (
                      <option key={i} value={i}>
                        {f.name} (Az: {f.azimuthNormal?.toFixed(0)}°, Tilt: {f.tilt?.toFixed(0)}°)
                      </option>
                    ))}
                  </select>
                )}
              </div>
            )}

            {!useFacadeFromModel && (
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-gray-600">Inclinación (°)</label>
                  <input type="number" value={customTilt} onChange={(e) => setCustomTilt(Number(e.target.value))}
                    className="w-full bg-gray-50 border-2 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 font-medium" min={0} max={90} />
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-600">Azimut (°)</label>
                  <input type="number" value={customAzimuth} onChange={(e) => setCustomAzimuth(Number(e.target.value))}
                    className="w-full bg-gray-50 border-2 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 font-medium" min={0} max={360} />
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-600">Área (m²)</label>
                  <input type="number" value={customArea} onChange={(e) => setCustomArea(Number(e.target.value))}
                    className="w-full bg-gray-50 border-2 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 font-medium" min={1} />
                </div>
              </div>
            )}

            {useFacadeFromModel && (
              <div className="mt-2 grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-gray-600">Área (m²)</label>
                  <input type="number" value={customArea} onChange={(e) => setCustomArea(Number(e.target.value))}
                    className="w-full bg-gray-50 border-2 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 font-medium" min={1} />
                </div>
              </div>
            )}
          </div>

          {/* Multi-Superficie Arquitectónica */}
          <div className="bg-white border-2 border-cyan-100 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                <span className="text-lg">🏗️</span> Superficies Arquitectónicas BIPV
              </h4>
              <label className="flex items-center gap-2 text-xs text-gray-600">
                <input
                  type="checkbox"
                  checked={useMultiSurface}
                  onChange={(e) => setUseMultiSurface(e.target.checked)}
                  className="rounded border-gray-400 text-cyan-600"
                />
                Simulación multi-superficie
              </label>
            </div>

            {useMultiSurface && (
              <div className="space-y-3">
                {/* Botón agregar superficie */}
                <div className="flex flex-wrap gap-2">
                  {(Object.entries(SURFACE_TYPE_DEFAULTS) as [BIPVSurfaceType, typeof SURFACE_TYPE_DEFAULTS[BIPVSurfaceType]][]).map(([type, def]) => (
                    <button
                      key={type}
                      onClick={() => {
                        const newSurface: ArchitecturalSurface = {
                          id: `${type}_${Date.now()}`,
                          name: `${def.label} ${architecturalSurfaces.filter(s => s.type === type).length + 1}`,
                          type,
                          tilt: def.tilt,
                          azimuth: customAzimuth,
                          area: type === 'ventana' ? 4 : type === 'pasamano' ? 8 : type === 'pergola' ? 25 : type === 'marquesina' ? 15 : 30,
                          mountingType: def.mountingType,
                          enabled: true,
                        };
                        setArchitecturalSurfaces([...architecturalSurfaces, newSurface]);
                      }}
                      className="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-cyan-200 bg-cyan-50 text-cyan-700 hover:bg-cyan-100 transition-colors"
                    >
                      {def.icon} {def.label}
                    </button>
                  ))}
                </div>

                {/* Auto-importar fachadas del modelo 3D */}
                {facades && facades.length > 0 && architecturalSurfaces.filter(s => s.fromModel).length === 0 && (
                  <button
                    onClick={() => {
                      const imported = facades.map((f, i) => ({
                        id: `model_${i}_${Date.now()}`,
                        name: f.name,
                        type: (f.tilt < 30 ? 'techo' : 'fachada') as BIPVSurfaceType,
                        tilt: f.tilt,
                        azimuth: f.azimuthNormal,
                        area: f.area || 30,
                        mountingType: f.tilt < 30 ? 'cubierta_integrada' : 'fachada_confinada',
                        enabled: true,
                        fromModel: true,
                        facadeIdx: i,
                      }));
                      setArchitecturalSurfaces([...architecturalSurfaces, ...imported]);
                    }}
                    className="w-full py-2 text-xs font-bold rounded-lg border-2 border-dashed border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100 transition-colors"
                  >
                    🏢 Importar {facades.length} fachadas/techos del modelo 3D
                  </button>
                )}

                {/* Lista de superficies */}
                {architecturalSurfaces.length > 0 && (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {architecturalSurfaces.map((surf, idx) => (
                      <div key={surf.id} className={`flex items-center gap-2 p-2.5 rounded-lg border-2 transition-all ${
                        surf.enabled ? 'border-cyan-200 bg-cyan-50/50' : 'border-gray-200 bg-gray-50 opacity-60'
                      }`}>
                        <input
                          type="checkbox"
                          checked={surf.enabled}
                          onChange={(e) => {
                            const updated = [...architecturalSurfaces];
                            updated[idx] = { ...surf, enabled: e.target.checked };
                            setArchitecturalSurfaces(updated);
                          }}
                          className="rounded border-gray-400 text-cyan-600"
                        />
                        <span className="text-sm">{SURFACE_TYPE_DEFAULTS[surf.type]?.icon}</span>
                        <input
                          value={surf.name}
                          onChange={(e) => {
                            const updated = [...architecturalSurfaces];
                            updated[idx] = { ...surf, name: e.target.value };
                            setArchitecturalSurfaces(updated);
                          }}
                          className="flex-1 text-xs font-medium bg-transparent border-none outline-none text-gray-800"
                        />
                        <div className="flex items-center gap-1 text-[10px] text-gray-500">
                          <span>Tilt:{surf.tilt}°</span>
                          <span>Az:{surf.azimuth}°</span>
                          <span>{surf.area}m²</span>
                        </div>
                        <select
                          value={surf.mountingType}
                          onChange={(e) => {
                            const updated = [...architecturalSurfaces];
                            updated[idx] = { ...surf, mountingType: e.target.value };
                            setArchitecturalSurfaces(updated);
                          }}
                          className="text-[10px] bg-gray-100 border border-gray-200 rounded px-1 py-0.5"
                        >
                          {THERMAL_MOUNTING_TYPES.map(mt => (
                            <option key={mt.id} value={mt.id}>{mt.name}</option>
                          ))}
                        </select>
                        <button
                          onClick={() => setArchitecturalSurfaces(architecturalSurfaces.filter((_, i) => i !== idx))}
                          className="text-red-400 hover:text-red-600 text-sm font-bold"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {architecturalSurfaces.length > 0 && (
                  <div className="text-xs text-gray-500 bg-gray-50 rounded-lg p-2">
                    Total: {architecturalSurfaces.filter(s => s.enabled).length} superficies activas —
                    Área combinada: {architecturalSurfaces.filter(s => s.enabled).reduce((sum, s) => sum + s.area, 0).toFixed(1)} m²
                  </div>
                )}
              </div>
            )}

            {!useMultiSurface && (
              <p className="text-xs text-gray-500 italic">Active para simular múltiples superficies (ventanas, pérgolas, marquesinas, pasamanos, techos) simultáneamente.</p>
            )}
          </div>

          {/* Sombreado 3D o Manual */}
          {(is3DActive || hasManualShading) && (
            <div className="bg-white border-2 border-orange-100 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🌤️</span>
                  <div>
                    <h4 className="text-sm font-bold text-gray-800">
                      Sombreado {is3DActive ? '3D' : 'Manual'} Aplicado
                    </h4>
                    <p className="text-xs text-gray-600">
                      {is3DActive ? (
                        <>Fachada: <strong>{facadeAnalysis3D.facadeName}</strong> — Pérdida anual: <strong className="text-orange-600">{(facadeAnalysis3D.annualShadingLoss).toFixed(1)}%</strong> — FS medio: {facadeAnalysis3D.annualFS.toFixed(3)}</>
                      ) : (
                        <>Pérdida anual: <strong className="text-orange-600">{annualManualLoss.toFixed(1)}%</strong> — FS medio: {(shadingFactors!.reduce((a, b) => a + b, 0) / 12).toFixed(3)}</>
                      )}
                    </p>
                  </div>
                </div>
                <label className="flex items-center gap-2 text-xs text-gray-600">
                  <input
                    type="checkbox"
                    checked={applyShadingFactors}
                    onChange={(e) => setApplyShadingFactors(e.target.checked)}
                    className="rounded border-gray-400 text-orange-600"
                  />
                  Aplicar
                </label>
              </div>
              {applyShadingFactors && (
                <div className="mt-2 grid grid-cols-12 gap-1">
                  {['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'].map((m, i) => {
                    const factor = is3DActive ? facadeAnalysis3D.monthlyShadingFactors[i] : shadingFactors![i];
                    return (
                      <div key={i} className="text-center">
                        <div className="text-[9px] text-gray-500">{m}</div>
                        <div className={`text-[10px] font-bold ${
                          factor < 0.8 ? 'text-red-600' :
                          factor < 0.95 ? 'text-orange-600' : 'text-green-600'
                        }`}>
                          {(factor * 100).toFixed(0)}%
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Soiling y Montaje */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white border-2 border-yellow-100 rounded-xl p-5 shadow-sm">
              <h4 className="text-sm font-bold text-gray-800 mb-3">Perfil de Suciedad (Soiling)</h4>
              <select value={soilingPresetId} onChange={(e) => setSoilingPresetId(e.target.value)}
                className="w-full bg-gray-50 border-2 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 font-medium mb-2">
                {SOILING_PRESETS.map(preset => (
                  <option key={preset.id} value={preset.id}>{preset.name}</option>
                ))}
              </select>
              <p className="text-xs text-gray-600">{soilingPreset.description}</p>
            </div>

            <div className="bg-white border-2 border-red-100 rounded-xl p-5 shadow-sm">
              <h4 className="text-sm font-bold text-gray-800 mb-3">Montaje Térmico</h4>
              <select value={mountingTypeId} onChange={(e) => setMountingTypeId(e.target.value)}
                className="w-full bg-gray-50 border-2 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 font-medium mb-2">
                {THERMAL_MOUNTING_TYPES.map(mt => (
                  <option key={mt.id} value={mt.id}>{mt.name} (k={mt.kBipv})</option>
                ))}
              </select>
              <p className="text-xs text-gray-600">{mountingType.description}</p>
            </div>
          </div>

          {/* Botón de simulación */}
          <button
            onClick={runSimulation}
            disabled={isSimulating || !weatherData || weatherData.length === 0 || selectedTechs.length === 0 || selectedTransparencies.length === 0}
            className="w-full py-3.5 rounded-xl font-bold text-white text-base transition-all disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-lg hover:shadow-xl"
          >
            {isSimulating ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                Simulando ({transpositionModel === 'perez' ? 'Perez' : 'Isotrópico'})...
              </span>
            ) : (
              `🚀 Simular (${selectedTechs.length} × ${selectedTransparencies.length} = ${selectedTechs.length * selectedTransparencies.length}) — ${transpositionModel === 'perez' ? 'Perez' : 'Isotrópico'}`
            )}
          </button>

          {!weatherData || weatherData.length === 0 ? (
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-2 text-center font-medium">⚠️ Se requieren datos EPW cargados para ejecutar la simulación.</p>
          ) : null}
        </div>
      )}

      {/* Tab: Resultados */}
      {activeTab === 'results' && (
        <div className="space-y-4">
          {isSimulating && (
            <div className="text-center py-8 text-gray-600">
              <svg className="animate-spin h-8 w-8 mx-auto mb-3 text-indigo-600" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              Procesando simulación multivariable...
            </div>
          )}

          {!isSimulating && results && results.length > 0 && (
            <>
              {/* Tabla de resultados */}
              <div className="bg-white border-2 border-gray-200 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-bold text-gray-800">Resumen de Resultados ({transpositionModel === 'perez' ? 'Perez' : 'Isotrópico'})</h4>
                  <div className="flex gap-2">
                    {onSendToEnergySimulator && (
                      <div className="relative group">
                        <button onClick={handleSendToEnergy} className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition-colors shadow-sm ${hasIrradianceData ? 'bg-blue-600 hover:bg-blue-500 text-white' : 'bg-blue-600/70 hover:bg-blue-500 text-white'}`}>
                          ⚡ Enviar al Simulador de Energía {!hasIrradianceData && '⚠️'}
                        </button>
                        {!hasIrradianceData && (
                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-2 bg-amber-50 border border-amber-300 rounded-lg text-[10px] text-amber-800 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-lg">
                            ⚠️ Primero importe datos de irradiación (Heatmap PVGIS o PVWatts) antes de enviar al Simulador.
                          </div>
                        )}
                      </div>
                    )}
                    <button onClick={exportCSV} className="text-xs px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold transition-colors shadow-sm">
                      📥 Exportar CSV
                    </button>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-gray-600 font-semibold border-b-2 border-gray-200">
                        <th className="text-left py-2.5 px-2">Tecnología</th>
                        <th className="text-center py-2.5 px-1">τ</th>
                        <th className="text-center py-2.5 px-1">η_adj</th>
                        <th className="text-right py-2.5 px-1">kWh/año</th>
                        <th className="text-right py-2.5 px-1">kWh/m²</th>
                        <th className="text-right py-2.5 px-1">Pico W</th>
                        <th className="text-right py-2.5 px-1">Luz kWh</th>
                        <th className="text-center py-2.5 px-1">IAM̄</th>
                        <th className="text-center py-2.5 px-1">Soil̄</th>
                        <th className="text-center py-2.5 px-1">F_th̄</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.map((r, i) => (
                        <tr key={i} onClick={() => setSelectedResultIdx(i)}
                          className={`border-b border-gray-100 cursor-pointer transition-colors ${
                            selectedResultIdx === i ? 'bg-indigo-50' : 'hover:bg-gray-50'
                          }`}>
                          <td className="py-2 px-2 text-gray-800 font-medium">{r.technology}</td>
                          <td className="text-center text-cyan-700 font-semibold">{(r.transparencia * 100).toFixed(0)}%</td>
                          <td className="text-center text-emerald-700 font-semibold">{(r.eficienciaAjustada * 100).toFixed(1)}%</td>
                          <td className="text-right text-amber-700 font-bold">{r.energiaAnualKwh.toFixed(1)}</td>
                          <td className="text-right text-amber-600">{r.energiaAnualKwhM2.toFixed(2)}</td>
                          <td className="text-right text-orange-600">{r.potenciaPicoW.toFixed(0)}</td>
                          <td className="text-right text-blue-600">{r.iluminacionPasivaAnualKwh.toFixed(1)}</td>
                          <td className="text-center text-gray-700">{r.iamPromedio.toFixed(3)}</td>
                          <td className="text-center text-red-600 font-medium">{(r.soilingPromedio * 100).toFixed(1)}%</td>
                          <td className="text-center text-gray-700">{r.factorTermicoPromedio.toFixed(3)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-gray-500 mt-2 font-medium">Clic en una fila para seleccionarla y guardar/exportar.</p>
              </div>

              {/* Guardar simulación */}
              {isAuthenticated && (
                <div className="bg-indigo-50 border-2 border-indigo-200 rounded-xl p-5">
                  <h4 className="text-sm font-bold text-indigo-800 mb-3">💾 Guardar Simulación Seleccionada</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input
                      type="text"
                      value={saveName}
                      onChange={(e) => setSaveName(e.target.value)}
                      placeholder="Nombre del escenario..."
                      className="bg-white border-2 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 font-medium"
                    />
                    <input
                      type="text"
                      value={saveNotes}
                      onChange={(e) => setSaveNotes(e.target.value)}
                      placeholder="Notas (opcional)..."
                      className="bg-white border-2 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800"
                    />
                    <button
                      onClick={handleSave}
                      disabled={isSaving || !saveName.trim()}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm rounded-lg font-bold transition-colors shadow-sm"
                    >
                      {isSaving ? 'Guardando...' : '💾 Guardar'}
                    </button>
                  </div>
                  {saveSuccess && (
                    <p className={`text-xs mt-2 font-medium ${saveSuccess.startsWith('Error') ? 'text-red-600' : 'text-emerald-600'}`}>
                      {saveSuccess}
                    </p>
                  )}
                  <p className="text-xs text-indigo-600 mt-1 font-medium">
                    Guardando: {results[selectedResultIdx]?.technology} (τ={((results[selectedResultIdx]?.transparencia || 0) * 100).toFixed(0)}%)
                    {generateHourly ? ' — con datos horarios' : ' — solo resumen mensual'}
                  </p>
                </div>
              )}

              {/* Gráfico mensual */}
              <div className="bg-white border-2 border-gray-200 rounded-xl p-5 shadow-sm">
                <h4 className="text-sm font-bold text-gray-800 mb-3">
                  Producción Mensual — {results[selectedResultIdx]?.technology} (τ={((results[selectedResultIdx]?.transparencia || 0) * 100).toFixed(0)}%)
                </h4>
                <div className="grid grid-cols-12 gap-1">
                  {(() => {
                    const r = results[selectedResultIdx] || results[0];
                    const maxMonth = Math.max(...r.produccionMensualKwh);
                    const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
                    return r.produccionMensualKwh.map((kwh, i) => (
                      <div key={i} className="flex flex-col items-center">
                        <div className="w-full bg-gray-100 rounded-t relative" style={{ height: '80px' }}>
                          <div className="absolute bottom-0 w-full bg-gradient-to-t from-indigo-600 to-purple-400 rounded-t"
                            style={{ height: maxMonth > 0 ? `${(kwh / maxMonth) * 100}%` : '0%' }} />
                        </div>
                        <div className="text-[9px] text-gray-600 font-semibold mt-1">{months[i]}</div>
                        <div className="text-[9px] text-gray-800 font-bold">{kwh.toFixed(0)}</div>
                      </div>
                    ));
                  })()}
                </div>
              </div>
            </>
          )}

          {!isSimulating && (!results || results.length === 0) && (
            <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-xl border border-gray-200">
              <p className="font-medium">No hay resultados. Ejecute la simulación desde la pestaña de Configuración.</p>
            </div>
          )}
        </div>
      )}

      {/* Tab: Pérdidas Detalladas */}
      {activeTab === 'losses' && results && results.length > 0 && (
        <div className="space-y-4">
          <div className="bg-white border-2 border-red-100 rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-bold text-gray-800 mb-3">Desglose de Pérdidas Ópticas y Térmicas</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-600 font-semibold border-b-2 border-gray-200">
                    <th className="text-left py-2.5 px-2">Tecnología</th>
                    <th className="text-center py-2.5 px-1">τ</th>
                    <th className="text-right py-2.5 px-1">Pérd. IAM (kWh/m²)</th>
                    <th className="text-right py-2.5 px-1">Pérd. Soiling (kWh/m²)</th>
                    <th className="text-right py-2.5 px-1">Pérd. Térmica (kWh/m²)</th>
                    <th className="text-right py-2.5 px-1">Total Pérdidas (kWh/m²)</th>
                    <th className="text-right py-2.5 px-1">Producción Neta (kWh/m²)</th>
                    <th className="text-center py-2.5 px-1">% Pérdida Total</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => {
                    const totalLoss = r.irradianciaReflejadaAnualKwhM2 + r.perdidasSoilingAnualKwhM2 + r.perdidasTermicasAnualKwhM2;
                    const grossProd = r.energiaAnualKwhM2 + totalLoss;
                    const pctLoss = grossProd > 0 ? (totalLoss / grossProd) * 100 : 0;
                    return (
                      <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-2 px-2 text-gray-800 font-medium">{r.technology}</td>
                        <td className="text-center text-cyan-700 font-semibold">{(r.transparencia * 100).toFixed(0)}%</td>
                        <td className="text-right text-red-600 font-medium">{r.irradianciaReflejadaAnualKwhM2.toFixed(2)}</td>
                        <td className="text-right text-amber-600 font-medium">{r.perdidasSoilingAnualKwhM2.toFixed(2)}</td>
                        <td className="text-right text-orange-600 font-medium">{r.perdidasTermicasAnualKwhM2.toFixed(2)}</td>
                        <td className="text-right text-red-700 font-bold">{totalLoss.toFixed(2)}</td>
                        <td className="text-right text-emerald-600 font-bold">{r.energiaAnualKwhM2.toFixed(2)}</td>
                        <td className="text-center text-red-600 font-bold">{pctLoss.toFixed(1)}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Barras de pérdida visual */}
          <div className="bg-white border-2 border-gray-200 rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-bold text-gray-800 mb-3">Distribución de Pérdidas (Mejor Resultado)</h4>
            {(() => {
              const best = results.reduce((b, r) => r.energiaAnualKwh > b.energiaAnualKwh ? r : b);
              const totalLoss = best.irradianciaReflejadaAnualKwhM2 + best.perdidasSoilingAnualKwhM2 + best.perdidasTermicasAnualKwhM2;
              const items = [
                { label: 'Reflexión IAM', value: best.irradianciaReflejadaAnualKwhM2, color: 'bg-red-500' },
                { label: 'Suciedad (Soiling)', value: best.perdidasSoilingAnualKwhM2, color: 'bg-yellow-500' },
                { label: 'Temperatura', value: best.perdidasTermicasAnualKwhM2, color: 'bg-orange-500' },
              ];
              return (
                <div className="space-y-3">
                  {items.map((item, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-xs text-gray-700 font-semibold w-32 shrink-0">{item.label}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-5 relative">
                        <div className={`absolute inset-y-0 left-0 ${item.color} rounded-full`}
                          style={{ width: totalLoss > 0 ? `${(item.value / totalLoss) * 100}%` : '0%' }} />
                      </div>
                      <span className="text-xs text-gray-800 font-bold w-28 text-right">{item.value.toFixed(2)} kWh/m²</span>
                      <span className="text-xs text-gray-600 font-semibold w-12 text-right">
                        {totalLoss > 0 ? `${((item.value / totalLoss) * 100).toFixed(0)}%` : '0%'}
                      </span>
                    </div>
                  ))}
                  <div className="mt-3 pt-3 border-t-2 border-gray-200 flex items-center gap-3">
                    <span className="text-xs text-gray-800 w-32 shrink-0 font-bold">Producción Neta</span>
                    <div className="flex-1 bg-gray-100 rounded-full h-5 relative">
                      <div className="absolute inset-y-0 left-0 bg-emerald-500 rounded-full"
                        style={{ width: `${(best.energiaAnualKwhM2 / (best.energiaAnualKwhM2 + totalLoss)) * 100}%` }} />
                    </div>
                    <span className="text-xs text-emerald-700 w-28 text-right font-bold">{best.energiaAnualKwhM2.toFixed(2)} kWh/m²</span>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {activeTab === 'losses' && (!results || results.length === 0) && (
        <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-xl border border-gray-200">
          <p className="font-medium">Ejecute la simulación primero para ver el desglose de pérdidas.</p>
        </div>
      )}

      {/* Tab: Historial */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          {!isAuthenticated && (
            <div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-4 text-center">
              <p className="text-sm text-amber-800 font-medium">Inicie sesión para ver y guardar simulaciones.</p>
            </div>
          )}

          {isAuthenticated && historyQuery.isLoading && (
            <div className="text-center py-8 text-gray-600 font-medium">Cargando historial...</div>
          )}

          {isAuthenticated && historyQuery.data && historyQuery.data.length === 0 && (
            <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-xl border border-gray-200">
              <p className="font-medium">No hay simulaciones guardadas. Ejecute una simulación y guárdela desde la pestaña Resultados.</p>
            </div>
          )}

          {isAuthenticated && historyQuery.data && historyQuery.data.length > 0 && (
            <>
              <div className="bg-white border-2 border-indigo-100 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-bold text-gray-800">Simulaciones Guardadas ({historyQuery.data.length})</h4>
                  {compareIds.length >= 2 && (
                    <button onClick={() => setActiveTab('comparison')}
                      className="text-xs px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-semibold transition-colors shadow-sm">
                      📈 Comparar ({compareIds.length})
                    </button>
                  )}
                </div>
                <div className="space-y-2">
                  {historyQuery.data.map((sim: any) => (
                    <div key={sim.id} className={`flex items-center gap-3 p-3 rounded-xl border-2 transition-all ${
                      compareIds.includes(sim.id) ? 'border-indigo-400 bg-indigo-50 shadow-sm' : 'border-gray-200 bg-gray-50 hover:border-indigo-200'
                    }`}>
                      <input
                        type="checkbox"
                        checked={compareIds.includes(sim.id)}
                        onChange={() => toggleCompare(sim.id)}
                        className="rounded border-gray-400 text-indigo-600"
                        title="Seleccionar para comparar"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-semibold text-gray-800 truncate">{sim.name}</div>
                        <div className="text-xs text-gray-600">
                          {sim.technology} | τ={(sim.transparencia * 100).toFixed(0)}% | {sim.transpositionModel || 'isotropic'}
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-sm font-bold text-amber-700">{sim.energiaAnualKwh?.toFixed(1)} kWh/año</div>
                        <div className="text-xs text-gray-600">{sim.energiaAnualKwhM2?.toFixed(2)} kWh/m²</div>
                      </div>
                      <button onClick={() => handleDelete(sim.id)}
                        className="text-xs px-2 py-1.5 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors">
                        🗑️
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Tab: Comparar Escenarios */}
      {activeTab === 'comparison' && (
        <div className="space-y-4">
          {compareIds.length < 2 && !results && (
            <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-xl border border-gray-200">
              <p className="font-medium">Seleccione al menos 2 simulaciones del Historial para comparar, o ejecute una simulación.</p>
            </div>
          )}

          {/* Comparación de simulaciones guardadas */}
          {compareIds.length >= 2 && compareQuery.data && compareQuery.data.length >= 2 && (
            <div className="bg-white border-2 border-purple-100 rounded-xl p-5 shadow-sm">
              <h4 className="text-sm font-bold text-gray-800 mb-3">Comparación de Escenarios Guardados</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-gray-600 font-semibold border-b-2 border-gray-200">
                      <th className="text-left py-2.5 px-2">Nombre</th>
                      <th className="text-left py-2.5 px-1">Tecnología</th>
                      <th className="text-center py-2.5 px-1">τ</th>
                      <th className="text-center py-2.5 px-1">Modelo</th>
                      <th className="text-right py-2.5 px-1">kWh/año</th>
                      <th className="text-right py-2.5 px-1">kWh/m²</th>
                      <th className="text-right py-2.5 px-1">Luz kWh</th>
                      <th className="text-center py-2.5 px-1">IAM̄</th>
                      <th className="text-center py-2.5 px-1">Soil̄</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compareQuery.data.map((sim: any) => (
                      <tr key={sim.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-2 px-2 text-gray-800 font-semibold">{sim.name}</td>
                        <td className="py-2 px-1 text-gray-700">{sim.technology}</td>
                        <td className="text-center text-cyan-700 font-semibold">{(sim.transparencia * 100).toFixed(0)}%</td>
                        <td className="text-center text-gray-600">{sim.transpositionModel || 'iso'}</td>
                        <td className="text-right text-amber-700 font-bold">{sim.energiaAnualKwh?.toFixed(1)}</td>
                        <td className="text-right text-amber-600">{sim.energiaAnualKwhM2?.toFixed(2)}</td>
                        <td className="text-right text-blue-600">{sim.iluminacionPasivaAnualKwh?.toFixed(1)}</td>
                        <td className="text-center text-gray-700">{sim.iamPromedio?.toFixed(3)}</td>
                        <td className="text-center text-red-600 font-medium">{((sim.soilingPromedio || 0) * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {/* Diferencia porcentual */}
              {compareQuery.data.length === 2 && (
                <div className="mt-3 p-3 bg-purple-50 border border-purple-200 rounded-xl">
                  <h5 className="text-xs font-bold text-purple-800 mb-2">Diferencia entre escenarios</h5>
                  {(() => {
                    const [a, b] = compareQuery.data as any[];
                    const diffKwh = b.energiaAnualKwh - a.energiaAnualKwh;
                    const diffPct = a.energiaAnualKwh > 0 ? (diffKwh / a.energiaAnualKwh) * 100 : 0;
                    return (
                      <div className="grid grid-cols-3 gap-3 text-xs">
                        <div>
                          <span className="text-gray-600 font-medium">Δ Energía:</span>
                          <span className={`ml-1 font-bold ${diffKwh >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>
                            {diffKwh >= 0 ? '+' : ''}{diffKwh.toFixed(1)} kWh ({diffPct >= 0 ? '+' : ''}{diffPct.toFixed(1)}%)
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600 font-medium">Δ Luz:</span>
                          <span className="ml-1 text-blue-700 font-bold">
                            {((b.iluminacionPasivaAnualKwh || 0) - (a.iluminacionPasivaAnualKwh || 0)).toFixed(1)} kWh
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600 font-medium">Δ IAM:</span>
                          <span className="ml-1 text-gray-800 font-bold">
                            {(((b.iamPromedio || 0) - (a.iamPromedio || 0)) * 100).toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          )}

          {/* Comparativa de resultados actuales por generación */}
          {results && results.length > 0 && (
            <div className="bg-white border-2 border-gray-200 rounded-xl p-5 shadow-sm">
              <h4 className="text-sm font-bold text-gray-800 mb-3">Comparativa por Generación (Simulación Actual)</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {['1G', '2G', '3G'].map(gen => {
                  const genResults = results.filter(r => r.generation.startsWith(gen === '1G' ? '1ª' : gen === '2G' ? '2ª' : '3ª'));
                  if (genResults.length === 0) return null;
                  const best = genResults.reduce((b, r) => r.energiaAnualKwh > b.energiaAnualKwh ? r : b);
                  return (
                    <div key={gen} className={`p-4 rounded-xl border-2 ${
                      gen === '1G' ? 'border-emerald-200 bg-emerald-50' :
                      gen === '2G' ? 'border-blue-200 bg-blue-50' :
                      'border-orange-200 bg-orange-50'
                    }`}>
                      <div className="text-xs font-bold text-gray-800 mb-2">{gen} — {best.technology}</div>
                      <div className="space-y-1.5 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-600 font-medium">Producción:</span>
                          <span className="text-amber-700 font-bold">{best.energiaAnualKwh.toFixed(1)} kWh</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 font-medium">Transparencia:</span>
                          <span className="text-cyan-700 font-semibold">{(best.transparencia * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 font-medium">Pérd. IAM:</span>
                          <span className="text-red-600 font-semibold">{best.irradianciaReflejadaAnualKwhM2.toFixed(2)} kWh/m²</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 font-medium">Pérd. Soiling:</span>
                          <span className="text-amber-600 font-semibold">{best.perdidasSoilingAnualKwhM2.toFixed(2)} kWh/m²</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 font-medium">Luz pasiva:</span>
                          <span className="text-blue-600 font-semibold">{best.iluminacionPasivaAnualKwh.toFixed(0)} kWh</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Optimizador ROI */}
          {results && results.length > 0 && (
            <BIPVROIOptimizer
              results={results}
              area={facadeParams.area}
              tilt={facadeParams.tilt}
              azimuth={facadeParams.azimuth}
              latitude={latitude}
            />
          )}

          {/* Optimizar Orientación BIPV — Ranking de superficies del modelo 3D */}
          {results && results.length > 0 && facades && facades.length > 1 && weatherData && (
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-bold text-indigo-900 flex items-center gap-2">
                  🧭 Optimizar Orientación BIPV
                  <span className="text-xs font-normal text-indigo-600 bg-indigo-100 px-2 py-0.5 rounded-full">
                    {facades.length} superficies
                  </span>
                </h4>
              </div>
              <p className="text-xs text-indigo-700 mb-3">
                Compara la producción BIPV estimada en cada superficie del modelo 3D para identificar la orientación óptima.
                La mejor superficie se puede enviar directamente al Simulador de Energía para cálculos detallados.
              </p>
              {(() => {
                // Ranking rápido de superficies usando la mejor tecnología del resultado actual
                const bestResult = results[selectedResultIdx] || results[0];
                const tech = [...BIPV_GLASS_CATALOG, ...customBIPVTechs].find(t => t.name === bestResult.technology);
                if (!tech) return null;

                const mappedW: WeatherHourData[] = weatherData.map(w => ({
                  month: w.month, day: w.day, hour: w.hour,
                  ghi: w.ghi, dni: w.dni, dhi: w.dhi,
                  tempAir: w.temperature, windSpeed: w.windSpeed || 1,
                  precipitableWater: w.precipitableWater,
                }));

                const surfaceRanking = facades.map((f, idx) => {
                  const config: BIPVSimulationConfig = {
                    technology: tech,
                    transparencia: bestResult.transparencia,
                    areaM2: f.area || 30,
                    inclinacionFachada: f.tilt || 90,
                    azimutFachada: f.azimuthNormal || 180,
                    soiling: soilingPreset.config,
                    kBipv: mountingType.kBipv,
                    transpositionModel,
                    generateHourlyResults: false,
                  };
                  const summary = runBIPVSimulation(
                    mappedW, latitude, longitude, timezone,
                    config, effectiveObstacles,
                    monthlyShadingFactors3D
                  );
                  return { idx, name: f.name, tilt: f.tilt, azimuth: f.azimuthNormal, area: f.area, kwh: summary.energiaAnualKwh, kwhM2: summary.energiaAnualKwhM2, summary };
                }).sort((a, b) => b.kwhM2 - a.kwhM2);

                const best = surfaceRanking[0];
                const maxKwh = best.kwh;

                return (
                  <div className="space-y-2">
                    {surfaceRanking.map((s, rank) => (
                      <div key={s.idx} className={`flex items-center gap-2 p-2 rounded-lg border transition-all ${rank === 0 ? 'bg-green-50 border-green-300 ring-1 ring-green-200' : 'bg-white border-gray-200'}`}>
                        <span className="w-6 text-center font-bold text-sm">
                          {rank === 0 ? '🥇' : rank === 1 ? '🥈' : rank === 2 ? '🥉' : `#${rank + 1}`}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-gray-800 truncate">{s.name}</span>
                            <span className="text-[10px] text-gray-500">Tilt:{s.tilt?.toFixed(0)}° Az:{s.azimuth?.toFixed(0)}° {s.area?.toFixed(0)}m²</span>
                          </div>
                          <div className="flex items-center gap-2 mt-0.5">
                            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div className="h-full bg-indigo-500 rounded-full transition-all" style={{ width: `${maxKwh > 0 ? (s.kwh / maxKwh) * 100 : 0}%` }} />
                            </div>
                            <span className="text-[10px] font-bold text-indigo-700 whitespace-nowrap">{s.kwh.toFixed(0)} kWh/año</span>
                            <span className="text-[10px] text-gray-500 whitespace-nowrap">({s.kwhM2.toFixed(1)} kWh/m²)</span>
                          </div>
                        </div>
                        {rank === 0 && onSendToEnergySimulator && (
                          <button
                            onClick={() => {
                              const bridgeData: BIPVToEnergyData = {
                                produccionMensualKwh: s.summary.produccionMensualKwh,
                                eficienciaAjustada: s.summary.eficienciaAjustada,
                                potenciaPicoW: s.summary.potenciaPicoW,
                                tilt: s.tilt || 90,
                                azimuth: s.azimuth || 180,
                                areaM2: s.area || 30,
                                transparencia: s.summary.transparencia,
                                technology: s.summary.technology,
                                generation: s.summary.generation,
                                iamPromedio: s.summary.iamPromedio,
                                soilingPromedio: s.summary.soilingPromedio,
                                factorTermicoPromedio: s.summary.factorTermicoPromedio,
                                energiaAnualKwh: s.summary.energiaAnualKwh,
                                energiaAnualKwhM2: s.summary.energiaAnualKwhM2,
                                transpositionModel: s.summary.transpositionModel || 'isotropic',
                                coefTemperatura: tech.coefTemperatura * 100,
                                noct: tech.noct,
                                kBipv: mountingType.kBipv,
                                surfaceName: s.name || `Superficie ${rank + 1}`,
                                // Sincronizar panel del catálogo con el Simulador de Energía
                                panelId: selectedCustomPanel.id,
                                panelPmax: selectedCustomPanel.pmax,
                                panelEfficiencySTC: selectedCustomPanel.efficiencySTC,
                                panelLengthMm: selectedCustomPanel.lengthMm,
                                panelWidthMm: selectedCustomPanel.widthMm,
                                iamMensual: s.summary.iamMensual,
                                soilingMensual: s.summary.soilingMensual,
                              };
                              onSendToEnergySimulator(bridgeData);
                            }}
                            className="text-[10px] px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold transition-colors shadow-sm whitespace-nowrap"
                          >
                            ⚡ Enviar al Simulador
                          </button>
                        )}
                      </div>
                    ))}
                    <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-xs text-green-800 font-medium">
                        ✅ <strong>Superficie óptima:</strong> {best.name} — {best.kwh.toFixed(0)} kWh/año ({best.kwhM2.toFixed(1)} kWh/m²/año)
                        {surfaceRanking.length > 1 && ` — ${((best.kwhM2 / (surfaceRanking[surfaceRanking.length - 1].kwhM2 || 1) - 1) * 100).toFixed(0)}% más productiva que ${surfaceRanking[surfaceRanking.length - 1].name}`}
                      </p>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* AUTO-OPTIMIZADOR: Todas las combinaciones tecnología × transparencia × superficie */}
          {results && results.length > 0 && facades && facades.length >= 1 && weatherData && (
            <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-bold text-amber-900 flex items-center gap-2">
                  🚀 Auto-optimizador ROI Global
                  <span className="text-xs font-normal text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
                    {facades.length} sup × {BIPV_GLASS_CATALOG.length + customBIPVTechs.length} techs × {TRANSPARENCY_LEVELS.length} τ
                  </span>
                </h4>
                <button
                  onClick={runAutoOptimizer}
                  disabled={autoOptRunning}
                  className="text-xs px-4 py-2 bg-amber-600 hover:bg-amber-500 disabled:bg-amber-300 text-white rounded-lg font-semibold transition-colors shadow-sm"
                >
                  {autoOptRunning ? '⏳ Calculando...' : '⚡ Ejecutar Auto-optimización'}
                </button>
              </div>
              <p className="text-xs text-amber-700 mb-3">
                Prueba <strong>todas</strong> las combinaciones posibles de tecnología BIPV × nivel de transparencia × superficie del modelo 3D,
                calcula el ROI financiero de cada una (incluyendo ahorro HVAC e incentivos Ley 1715), y muestra la configuración óptima.
              </p>

              {autoOptRunning && (
                <div className="flex items-center gap-2 p-3 bg-amber-100 rounded-lg">
                  <div className="animate-spin w-4 h-4 border-2 border-amber-600 border-t-transparent rounded-full" />
                  <span className="text-xs text-amber-800 font-medium">
                    Simulando {facades.length * (BIPV_GLASS_CATALOG.length + customBIPVTechs.length) * TRANSPARENCY_LEVELS.length} combinaciones...
                  </span>
                </div>
              )}

              {autoOptResults && autoOptResults.length > 0 && (
                <div className="space-y-3">
                  {/* GANADOR */}
                  <div className="bg-green-50 border-2 border-green-300 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">🏆</span>
                      <span className="text-sm font-bold text-green-900">Configuración Óptima (Mejor ROI 25 años)</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="bg-white rounded-lg p-2 text-center">
                        <div className="text-[10px] text-gray-500 uppercase">Tecnología</div>
                        <div className="text-xs font-bold text-gray-800 truncate">{autoOptResults[0].techName}</div>
                      </div>
                      <div className="bg-white rounded-lg p-2 text-center">
                        <div className="text-[10px] text-gray-500 uppercase">Transparencia</div>
                        <div className="text-xs font-bold text-cyan-700">τ = {(autoOptResults[0].transparency * 100).toFixed(0)}%</div>
                      </div>
                      <div className="bg-white rounded-lg p-2 text-center">
                        <div className="text-[10px] text-gray-500 uppercase">Superficie</div>
                        <div className="text-xs font-bold text-indigo-700 truncate">{autoOptResults[0].surfaceName}</div>
                      </div>
                      <div className="bg-white rounded-lg p-2 text-center">
                        <div className="text-[10px] text-gray-500 uppercase">ROI 25 años</div>
                        <div className={`text-sm font-bold ${autoOptResults[0].roi25 > 0 ? 'text-green-700' : 'text-red-600'}`}>{autoOptResults[0].roi25.toFixed(0)}%</div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mt-2">
                      <div className="text-center">
                        <div className="text-[9px] text-gray-400">Producción</div>
                        <div className="text-[11px] font-semibold text-amber-700">{autoOptResults[0].kwhYear.toFixed(0)} kWh/a</div>
                      </div>
                      <div className="text-center">
                        <div className="text-[9px] text-gray-400">kWh/m²</div>
                        <div className="text-[11px] font-semibold text-amber-700">{autoOptResults[0].kwhM2.toFixed(1)}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-[9px] text-gray-400">Payback</div>
                        <div className="text-[11px] font-semibold text-blue-700">{autoOptResults[0].payback.toFixed(1)} años</div>
                      </div>
                      <div className="text-center">
                        <div className="text-[9px] text-gray-400">VAN 25a</div>
                        <div className="text-[11px] font-semibold text-green-700">${autoOptResults[0].npv25.toLocaleString(undefined, {maximumFractionDigits: 0})}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-[9px] text-gray-400">TIR</div>
                        <div className="text-[11px] font-semibold text-purple-700">{autoOptResults[0].irr.toFixed(1)}%</div>
                      </div>
                    </div>
                    {onSendToEnergySimulator && (
                      <button
                        onClick={() => {
                          const best = autoOptResults[0];
                          const tech = [...BIPV_GLASS_CATALOG, ...customBIPVTechs].find(t => t.id === best.techId);
                          if (!tech) return;
                          const bridgeData: BIPVToEnergyData = {
                            produccionMensualKwh: best.produccionMensualKwh,
                            eficienciaAjustada: tech.eficienciaBase * (1 - best.transparency),
                            potenciaPicoW: tech.eficienciaBase * (1 - best.transparency) * best.area * 1000,
                            tilt: best.tilt,
                            azimuth: best.azimuth,
                            areaM2: best.area,
                            transparencia: best.transparency,
                            technology: tech.name,
                            generation: tech.generation,
                            iamPromedio: best.iamPromedio,
                            soilingPromedio: best.soilingPromedio,
                            factorTermicoPromedio: best.factorTermicoPromedio,
                            energiaAnualKwh: best.kwhYear,
                            energiaAnualKwhM2: best.kwhM2,
                            transpositionModel,
                            coefTemperatura: tech.coefTemperatura * 100,
                            noct: tech.noct,
                            kBipv: mountingType.kBipv,
                            surfaceName: best.surfaceName || `Superficie Óptima`,
                            panelId: selectedCustomPanel.id,
                            panelPmax: selectedCustomPanel.pmax,
                            panelEfficiencySTC: selectedCustomPanel.efficiencySTC,
                            panelLengthMm: selectedCustomPanel.lengthMm,
                            panelWidthMm: selectedCustomPanel.widthMm,
                            iamMensual: best.iamMensual,
                            soilingMensual: best.soilingMensual,
                          };
                          onSendToEnergySimulator(bridgeData);
                        }}
                        className="mt-3 w-full text-xs px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg font-semibold transition-colors shadow-sm"
                      >
                        ⚡ Aplicar configuración óptima y enviar al Simulador de Energía
                      </button>
                    )}
                  </div>

                  {/* Tabla expandible con todas las combinaciones */}
                  <button
                    onClick={() => setAutoOptExpanded(!autoOptExpanded)}
                    className="text-xs text-amber-700 hover:text-amber-900 font-medium flex items-center gap-1"
                  >
                    {autoOptExpanded ? '▼' : '▶'} Ver ranking completo ({autoOptResults.length} combinaciones)
                  </button>

                  {autoOptExpanded && (
                    <div>
                      {/* Controles de filtro */}
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <label className="flex items-center gap-1.5 text-[10px] text-gray-600 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={showOnlySelected}
                            onChange={(e) => setShowOnlySelected(e.target.checked)}
                            className="w-3 h-3 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
                          />
                          <span className="font-medium">Solo seleccionados ({selectedRankingItems.size})</span>
                        </label>
                        {selectedRankingItems.size > 0 && (
                          <>
                            <span className="text-[9px] text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full font-semibold">
                              🏆 Óptimo entre seleccionados: {(() => {
                                const filtered = autoOptResults.filter((_, i) => selectedRankingItems.has(i));
                                return filtered.length > 0 ? `${filtered[0].techName} (τ=${(filtered[0].transparency * 100).toFixed(0)}%)` : 'N/A';
                              })()}
                            </span>
                            <button
                              onClick={() => { setSelectedRankingItems(new Set()); setShowOnlySelected(false); }}
                              className="text-[9px] text-red-600 hover:text-red-800 font-medium"
                            >
                              ✕ Limpiar selección
                            </button>
                          </>
                        )}
                      </div>

                      {/* Indicador del óptimo entre seleccionados */}
                      {selectedRankingItems.size >= 2 && (() => {
                        const filtered = autoOptResults.filter((_, i) => selectedRankingItems.has(i));
                        if (filtered.length < 2) return null;
                        const best = filtered[0];
                        return (
                          <div className="bg-violet-50 border border-violet-300 rounded-lg p-3 mb-2">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm">🎯</span>
                              <span className="text-[11px] font-bold text-violet-900">Óptimo entre {filtered.length} seleccionados</span>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-[10px]">
                              <div className="bg-white rounded p-1.5 text-center">
                                <div className="text-gray-500">Tecnología</div>
                                <div className="font-bold text-violet-800 truncate">{best.techName}</div>
                              </div>
                              <div className="bg-white rounded p-1.5 text-center">
                                <div className="text-gray-500">τ</div>
                                <div className="font-bold text-cyan-700">{(best.transparency * 100).toFixed(0)}%</div>
                              </div>
                              <div className="bg-white rounded p-1.5 text-center">
                                <div className="text-gray-500">kWh/año</div>
                                <div className="font-bold text-amber-700">{best.kwhYear.toFixed(0)}</div>
                              </div>
                              <div className="bg-white rounded p-1.5 text-center">
                                <div className="text-gray-500">ROI 25a</div>
                                <div className={`font-bold ${best.roi25 > 0 ? 'text-green-700' : 'text-red-600'}`}>{best.roi25.toFixed(0)}%</div>
                              </div>
                              <div className="bg-white rounded p-1.5 text-center">
                                <div className="text-gray-500">LCOE</div>
                                <div className="font-bold text-blue-700">${best.lcoe.toFixed(3)}</div>
                              </div>
                            </div>

                            {/* Botón Aplicar óptimo seleccionado al Simulador */}
                            {onSendToEnergySimulator && (
                              <button
                                onClick={() => {
                                  const tech = [...BIPV_GLASS_CATALOG, ...customBIPVTechs].find(t => t.id === best.techId);
                                  if (!tech) return;
                                  const bridgeData: BIPVToEnergyData = {
                                    produccionMensualKwh: best.produccionMensualKwh,
                                    eficienciaAjustada: tech.eficienciaBase * (1 - best.transparency),
                                    potenciaPicoW: tech.eficienciaBase * (1 - best.transparency) * best.area * 1000,
                                    tilt: best.tilt,
                                    azimuth: best.azimuth,
                                    areaM2: best.area,
                                    transparencia: best.transparency,
                                    technology: tech.name,
                                    generation: tech.generation,
                                    iamPromedio: best.iamPromedio,
                                    soilingPromedio: best.soilingPromedio,
                                    factorTermicoPromedio: best.factorTermicoPromedio,
                                    energiaAnualKwh: best.kwhYear,
                                    energiaAnualKwhM2: best.kwhM2,
                                    transpositionModel,
                                    coefTemperatura: tech.coefTemperatura * 100,
                                    noct: tech.noct,
                                    kBipv: mountingType.kBipv,
                                    surfaceName: best.surfaceName || `Superficie Óptima (Seleccionado)`,
                                    panelId: selectedCustomPanel.id,
                                    panelPmax: selectedCustomPanel.pmax,
                                    panelEfficiencySTC: selectedCustomPanel.efficiencySTC,
                                    panelLengthMm: selectedCustomPanel.lengthMm,
                                    panelWidthMm: selectedCustomPanel.widthMm,
                                    iamMensual: best.iamMensual,
                                    soilingMensual: best.soilingMensual,
                                  };
                                  onSendToEnergySimulator(bridgeData);
                                }}
                                className="mt-2 w-full text-xs px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg font-semibold transition-colors shadow-sm"
                              >
                                🎯 Aplicar óptimo seleccionado al Simulador de Energía
                              </button>
                            )}

                            {/* Gráfico Radar comparativo entre seleccionados */}
                            {(() => {
                              const RADAR_COLORS = ['#7c3aed', '#0d9488', '#d97706', '#dc2626', '#2563eb', '#059669'];
                              // Normalizar valores al rango 0-100 para comparación visual
                              const maxKwh = Math.max(...filtered.map(r => r.kwhYear));
                              const maxRoi = Math.max(...filtered.map(r => Math.abs(r.roi25)));
                              const maxPayback = Math.max(...filtered.map(r => r.payback < 99 ? r.payback : 0));
                              const maxLcoe = Math.max(...filtered.map(r => r.lcoe));
                              const maxKwhM2 = Math.max(...filtered.map(r => r.kwhM2));

                              // Score compuesto de Viabilidad Financiera: VAN (40%) + TIR (30%) + Payback invertido (30%)
                              const maxNpv = Math.max(...filtered.map(r => Math.max(0, r.npv25)));
                              const maxIrr = Math.max(...filtered.map(r => Math.max(0, r.irr)));
                              const computeFinancialScore = (r: typeof filtered[0]) => {
                                const vanScore = maxNpv > 0 ? (Math.max(0, r.npv25) / maxNpv) * 100 : 0;
                                const tirScore = maxIrr > 0 ? (Math.max(0, r.irr) / maxIrr) * 100 : 0;
                                const paybackScore = maxPayback > 0 ? ((maxPayback - (r.payback < 99 ? r.payback : maxPayback)) / maxPayback) * 100 : 0;
                                return vanScore * 0.4 + tirScore * 0.3 + paybackScore * 0.3;
                              };

                              const radarData = [
                                {
                                  metric: 'kWh/año',
                                  ...Object.fromEntries(filtered.map((r, idx) => [`p${idx}`, maxKwh > 0 ? (r.kwhYear / maxKwh) * 100 : 0]))
                                },
                                {
                                  metric: 'ROI 25a',
                                  ...Object.fromEntries(filtered.map((r, idx) => [`p${idx}`, maxRoi > 0 ? (Math.max(0, r.roi25) / maxRoi) * 100 : 0]))
                                },
                                {
                                  metric: 'Payback',
                                  // Invertido: menor payback = mejor = mayor score
                                  ...Object.fromEntries(filtered.map((r, idx) => [`p${idx}`, maxPayback > 0 ? ((maxPayback - (r.payback < 99 ? r.payback : maxPayback)) / maxPayback) * 100 : 0]))
                                },
                                {
                                  metric: 'LCOE',
                                  // Invertido: menor LCOE = mejor = mayor score
                                  ...Object.fromEntries(filtered.map((r, idx) => [`p${idx}`, maxLcoe > 0 ? ((maxLcoe - r.lcoe) / maxLcoe) * 100 : 0]))
                                },
                                {
                                  metric: 'kWh/m²',
                                  ...Object.fromEntries(filtered.map((r, idx) => [`p${idx}`, maxKwhM2 > 0 ? (r.kwhM2 / maxKwhM2) * 100 : 0]))
                                },
                                {
                                  metric: 'Viab. Financiera',
                                  // Score compuesto: VAN 40% + TIR 30% + Payback⁻¹ 30%
                                  ...Object.fromEntries(filtered.map((r, idx) => [`p${idx}`, computeFinancialScore(r)]))
                                },
                              ];

                              return (
                                <div className="mt-3">
                                  <div className="text-[10px] font-semibold text-violet-700 mb-1">Comparación Radar — Paneles Seleccionados</div>
                                  <ResponsiveContainer width="100%" height={220}>
                                    <RadarChart data={radarData} outerRadius="70%">
                                      <PolarGrid stroke="#e5e7eb" />
                                      <PolarAngleAxis dataKey="metric" tick={{ fontSize: 9, fill: '#6b7280' }} />
                                      <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 8 }} axisLine={false} />
                                      {filtered.slice(0, 6).map((r, idx) => (
                                        <Radar
                                          key={idx}
                                          name={`${r.techName} (τ=${(r.transparency * 100).toFixed(0)}%)`}
                                          dataKey={`p${idx}`}
                                          stroke={RADAR_COLORS[idx % RADAR_COLORS.length]}
                                          fill={RADAR_COLORS[idx % RADAR_COLORS.length]}
                                          fillOpacity={0.15}
                                          strokeWidth={1.5}
                                        />
                                      ))}
                                      <Legend wrapperStyle={{ fontSize: 9 }} />
                                      <Tooltip contentStyle={{ fontSize: 9, borderRadius: 8 }} formatter={(value: number) => `${value.toFixed(0)}%`} />
                                    </RadarChart>
                                  </ResponsiveContainer>
                                  <p className="text-[8px] text-gray-400 text-center mt-0.5">Valores normalizados 0-100%. Payback y LCOE invertidos (mayor = mejor). Viab. Financiera = VAN(40%) + TIR(30%) + Payback⁻¹(30%).</p>
                                </div>
                              );
                            })()}
                          </div>
                        );
                      })()}

                      <div className="max-h-80 overflow-y-auto border border-amber-200 rounded-lg">
                        <table className="w-full text-[10px]">
                          <thead className="bg-amber-100 sticky top-0">
                            <tr>
                              <th className="px-1 py-1 text-center w-6">
                                <input
                                  type="checkbox"
                                  className="w-3 h-3 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
                                  checked={autoOptResults.slice(0, 50).every((_, i) => selectedRankingItems.has(i))}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      const newSet = new Set(selectedRankingItems);
                                      autoOptResults.slice(0, 50).forEach((_, i) => newSet.add(i));
                                      setSelectedRankingItems(newSet);
                                    } else {
                                      setSelectedRankingItems(new Set());
                                    }
                                  }}
                                />
                              </th>
                              <th className="px-2 py-1 text-left">#</th>
                              <th className="px-2 py-1 text-left">Tecnología</th>
                              <th className="px-2 py-1 text-center">τ</th>
                              <th className="px-2 py-1 text-left">Superficie</th>
                              <th className="px-2 py-1 text-right">kWh/a</th>
                              <th className="px-2 py-1 text-right">ROI 25a</th>
                              <th className="px-2 py-1 text-right">Payback</th>
                              <th className="px-2 py-1 text-right">LCOE</th>
                              <th className="px-2 py-1 text-center">Viable</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(showOnlySelected
                              ? autoOptResults.map((r, i) => ({ r, i })).filter(({ i }) => selectedRankingItems.has(i))
                              : autoOptResults.slice(0, 50).map((r, i) => ({ r, i }))
                            ).map(({ r, i }) => (
                              <tr key={i} className={`border-t border-amber-100 ${selectedRankingItems.has(i) ? 'bg-violet-50 ring-1 ring-inset ring-violet-200' : i === 0 ? 'bg-green-50 font-bold' : i % 2 === 0 ? 'bg-white' : 'bg-amber-50/30'}`}>
                                <td className="px-1 py-1 text-center">
                                  <input
                                    type="checkbox"
                                    className="w-3 h-3 rounded border-gray-300 text-violet-600 focus:ring-violet-500"
                                    checked={selectedRankingItems.has(i)}
                                    onChange={(e) => {
                                      const newSet = new Set(selectedRankingItems);
                                      if (e.target.checked) newSet.add(i);
                                      else newSet.delete(i);
                                      setSelectedRankingItems(newSet);
                                    }}
                                  />
                                </td>
                                <td className="px-2 py-1">{i === 0 ? '🏆' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`}</td>
                                <td className="px-2 py-1 truncate max-w-[100px]">{r.techName}</td>
                                <td className="px-2 py-1 text-center">{(r.transparency * 100).toFixed(0)}%</td>
                                <td className="px-2 py-1 truncate max-w-[80px]">{r.surfaceName}</td>
                                <td className="px-2 py-1 text-right">{r.kwhYear.toFixed(0)}</td>
                                <td className={`px-2 py-1 text-right font-semibold ${r.roi25 > 0 ? 'text-green-700' : 'text-red-600'}`}>{r.roi25.toFixed(0)}%</td>
                                <td className="px-2 py-1 text-right">{r.payback < 99 ? `${r.payback.toFixed(1)}a` : 'N/A'}</td>
                                <td className="px-2 py-1 text-right">${r.lcoe.toFixed(3)}</td>
                                <td className="px-2 py-1 text-center">{r.isViable ? '✅' : '❌'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {!showOnlySelected && autoOptResults.length > 50 && (
                          <div className="text-center text-[10px] text-amber-600 py-1 bg-amber-50">
                            Mostrando top 50 de {autoOptResults.length} combinaciones
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Trade-off */}
          {results && results.length > 0 && (
            <div className="bg-white border-2 border-gray-200 rounded-xl p-5 shadow-sm">
              <h4 className="text-sm font-bold text-gray-800 mb-3">Trade-off: Generación vs Iluminación</h4>
              <div className="space-y-2">
                {results.map((r, i) => {
                  const maxEnergy = Math.max(...results.map(x => x.energiaAnualKwh));
                  const maxLight = Math.max(...results.map(x => x.iluminacionPasivaAnualKwh));
                  return (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <span className="w-24 shrink-0 text-gray-800 font-medium truncate">{r.technology}</span>
                      <span className="w-10 shrink-0 text-cyan-700 font-semibold">τ={( r.transparencia * 100).toFixed(0)}%</span>
                      <div className="flex-1 flex gap-0.5">
                        <div className="bg-amber-500 h-3 rounded-l"
                          style={{ width: maxEnergy > 0 ? `${(r.energiaAnualKwh / maxEnergy) * 50}%` : '0%' }}
                          title={`Generación: ${r.energiaAnualKwh.toFixed(0)} kWh`} />
                        <div className="bg-blue-500 h-3 rounded-r"
                          style={{ width: maxLight > 0 ? `${(r.iluminacionPasivaAnualKwh / maxLight) * 50}%` : '0%' }}
                          title={`Iluminación: ${r.iluminacionPasivaAnualKwh.toFixed(0)} kWh`} />
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="flex gap-4 mt-3 text-xs text-gray-600 font-medium">
                <span className="flex items-center gap-1"><span className="w-3 h-2.5 bg-amber-500 rounded inline-block" /> Generación</span>
                <span className="flex items-center gap-1"><span className="w-3 h-2.5 bg-blue-500 rounded inline-block" /> Iluminación</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
