import { useState, useMemo, useCallback, useEffect } from 'react';
import { toast } from 'sonner';
import ShadingCalculator from '@/components/ShadingCalculator';
import TemplateManager from '@/components/TemplateManager';
import WeatherDataManager from '@/components/WeatherDataManager';
import SolarRadiationChart from '@/components/SolarRadiationChart';
import OrientationOptimizer, { OptimizerResult } from '@/components/OrientationOptimizer';
import POAAnalyzer from '@/components/POAAnalyzer';
import EnergyProductionSimulator from '@/components/EnergyProductionSimulator';
import CityWeatherLibrary from '@/components/CityWeatherLibrary';
import CityMapExplorer from '@/components/CityMapExplorer';
import ReportGenerator from '@/components/ReportGenerator';
import IrradianceHeatmap from '@/components/IrradianceHeatmap';
import PVWattsSatellite, { PVWattsToSimulatorData } from '@/components/PVWattsSatellite';
import PVGISAnalyzer, { PVGISToSimulatorData } from '@/components/PVGISAnalyzer';
import BIPVDiagnostic from '@/components/BIPVDiagnostic';
import BIPVGlassSimulator from '@/components/BIPVGlassSimulator';
import { BIPVToEnergyData } from '@/lib/bipvToEnergyBridge';
import { EPWData, getWeatherCorrectionFactor } from '@/lib/epwParser';
import { runBIPVSimulation, type WeatherHourData, type BIPVSimulationConfig } from '@/lib/iamSoilingEngine';
import { BIPV_GLASS_CATALOG } from '@/lib/bipvGlassCatalog';
import { calculateHourlyPOA } from '@/lib/liuJordanModel';
import { ProspectorToSimulatorData } from '@/components/SolarProspector';
import { FacadeFullAnalysis, calculateMonthlyShadingFactorsForFacade } from '@/lib/facadeShadingAnalysis';
import { normalizeMonthToAbbr } from '@/lib/monthHelper';

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

interface CityWeatherData {
  id: string;
  cityName: string;
  country: string;
  latitude: number;
  longitude: number;
  elevation: number;
  uploadDate: string;
  epwData: EPWData;
}

export default function Home() {
  const [view, setView] = useState<'calculator' | 'templates' | 'weather' | 'radiation' | 'optimizer' | 'cities' | 'poa' | 'energy' | 'map' | 'report' | 'heatmap' | 'pvgis' | 'pvwatts' | 'bipv' | 'bipvglass'>('calculator');
  const [templateData, setTemplateData] = useState<string[][] | null>(null);
  const [weatherData, setWeatherData] = useState<EPWData | null>(null);
  const [selectedCity, setSelectedCity] = useState<CityWeatherData | null>(null);
  const [shadingPoints, setShadingPoints] = useState<any[]>([]);

  // Calcular factores de sombreado mensuales promedio de manera reactiva (con o sin meteorología)
  const monthlyShadingFactors = useMemo(() => {
    const monthlyFactors = Array(12).fill(1.0);
    const monthCounts = Array(12).fill(0);
    const monthSums = Array(12).fill(0);
    const MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    
    shadingPoints.forEach(p => {
      const normalizedMonth = normalizeMonthToAbbr(p.month);
      const idx = MONTH_NAMES.indexOf(normalizedMonth);
      if (idx >= 0) {
        let finalFS = p.fs;
        if (weatherData) {
          const monthNum = idx + 1;
          const correction = getWeatherCorrectionFactor(weatherData, monthNum, p.day, p.hour);
          finalFS = p.fs * correction;
        }
        monthSums[idx] += finalFS;
        monthCounts[idx]++;
      }
    });
    for (let i = 0; i < 12; i++) {
      if (monthCounts[i] > 0) {
        monthlyFactors[i] = monthSums[i] / monthCounts[i];
      }
    }
    console.log('Integración Calculadora - Puntos:', shadingPoints.length, 'Factores mensuales:', monthlyFactors);
    return monthlyFactors;
  }, [shadingPoints, weatherData]);

  // Análisis 3D de fachada activa (prioridad sobre puntos manuales)
  const [facadeAnalysis3D, setFacadeAnalysis3D] = useState<FacadeFullAnalysis | null>(null);
  // Lista de fachadas del modelo 3D para el selector en el Simulador
  const [modelFacades, setModelFacades] = useState<import('@/lib/buildingModelImporter').DetectedFacade[]>([]);
  const [modelObstacles3D, setModelObstacles3D] = useState<import('@/lib/buildingModelImporter').Vertex3D[][] | undefined>(undefined);
  const [modelNorthOffset, setModelNorthOffset] = useState(0);
  const [externalFacadeIdx, setExternalFacadeIdx] = useState<number | null>(null);
  // Track if PVGISAnalyzer has ever been shown (lazy mount, then keep alive)
  const [pvgisEverShown, setPvgisEverShown] = useState(false);
  const [heatmapEverShown, setHeatmapEverShown] = useState(false);
  const [pvwattsEverShown, setPvwattsEverShown] = useState(false);
  // === PARÁMETROS POA COMPARTIDOS (sincronizados entre Análisis POA y Simulador) ===
  const [poaTilt, setPoaTilt] = useState<number | null>(null); // null = usar latitud
  const [poaAzimuth, setPoaAzimuth] = useState(0); // 0 = Sur
  const [poaAlbedo, setPoaAlbedo] = useState(0.2);
  const [poaUsePerez, setPoaUsePerez] = useState(false);
  // Datos del Optimizador de Orientación
  const [optimizerResult, setOptimizerResult] = useState<OptimizerResult | null>(null);
  // Restricciones de instalación compartidas (del Simulador al Optimizador)
  const [installTiltRange, setInstallTiltRange] = useState<[number, number]>([0, 60]);
  const [installAzimuthLocked, setInstallAzimuthLocked] = useState(false);
  const [installTypeName, setInstallTypeName] = useState('Cubierta Inclinada');
  // Datos del Prospector Solar para pre-llenar el Simulador
  const [prospectorData, setProspectorData] = useState<ProspectorToSimulatorData | null>(null);
  // Datos del PVGIS Real para comparar en el Simulador
  const [pvgisData, setPvgisData] = useState<PVGISToSimulatorData | null>(null);
  // Datos de PVWatts Satelital para comparar en el Simulador
  const [pvwattsData, setPvwattsData] = useState<PVWattsToSimulatorData | null>(null);
  // Datos del simulador BIPV IAM+Soiling para pre-llenar el Simulador de Energía
  const [bipvToEnergyData, setBipvToEnergyData] = useState<BIPVToEnergyData | null>(null);
  const [energyData, setEnergyData] = useState<any>({
    panelPower: 400,
    panelEfficiency: 0.20,
    panelArea: 2.0,
    panelQuantity: 1,
    tilt: 15,
    azimuth: 0,
    annualProduction: 0,
    capacityFactor: 0,
    performanceRatio: 0,
    systemLosses: 0.15,
    paybackPeriod: 0,
    roi10Year: 0,
    roi25Year: 0,
  });
  // Parámetros financieros del Simulador (editables por el usuario)
  const [financialParams, setFinancialParams] = useState({ electricityRate: 0.15, systemCost: 0, costPerWp: 4500 });

  // Sincronizar inclinación y azimut del BIPV con los ángulos activos de POA
  useEffect(() => {
    if (poaTilt !== null) {
      setBipvToEnergyData(prev => prev ? { ...prev, tilt: poaTilt } : null);
    }
  }, [poaTilt]);

  useEffect(() => {
    setBipvToEnergyData(prev => prev ? { ...prev, azimuth: poaAzimuth } : null);
  }, [poaAzimuth]);

  const handleSelectCity = (city: CityWeatherData) => {
    setSelectedCity(city);
    setWeatherData(city.epwData);
    setView('calculator');
  };

  const handleLoadTemplate = (data: string[][]) => {
    setTemplateData(data);
    setView('calculator');
  };

  // Callback para recibir factores de sombreado de la calculadora
  const handleShadingPointsChange = useCallback((points: Array<{month: string; day: number; hour: number; solarHeight: number; solarAzimuth: number; obstacle: string; shadedArea: number; fs: number}>) => {
    setShadingPoints(points);
  }, []);

  // Mark PVGISAnalyzer as ever-shown when navigating to it
  const handleSetView = (newView: typeof view) => {
    if (newView === 'pvgis') {
      setPvgisEverShown(true);
    }
    if (newView === 'heatmap') {
      setHeatmapEverShown(true);
    }
    if (newView === 'pvwatts') {
      setPvwattsEverShown(true);
    }
    setView(newView);
  };

  // Callback del Prospector Solar: genera POA sintético y cambia a vista Simulador
  const handleProspectorToSimulator = useCallback((data: ProspectorToSimulatorData) => {
    setProspectorData(data);
    // Si no hay weatherData cargado, crear uno sintético determinista mínimo
    if (!weatherData) {
      // Distribución mensual típica tropical (fracciones del GHI anual por mes)
      const monthlyFractions = [0.085, 0.082, 0.088, 0.083, 0.080, 0.078, 0.080, 0.083, 0.082, 0.083, 0.080, 0.096];
      const syntheticEPW: EPWData = {
        location: {
          city: `PVGIS (${data.lat.toFixed(2)}, ${data.lng.toFixed(2)})`,
          state: data.regionLabel,
          country: 'COL',
          latitude: data.lat,
          longitude: data.lng,
          timezone: -5,
          elevation: 0,
        },
        weatherData: MONTHS.flatMap((_, monthIdx) => {
          // Generar 60 registros por mes (determinista, sin Math.random)
          const monthGHI_Wh = (data.ghiAnnualKwhM2 * monthlyFractions[monthIdx] * 1000); // Wh/m² para el mes
          const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][monthIdx];
          const dailyGHI_Wh = monthGHI_Wh / daysInMonth;
          // Temperatura con variación diurna determinista (±2°C)
          const tempVariation = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 1.5, 1.0, 0.5, 0.0];
          return Array.from({ length: 60 }, (__, h) => {
            const hourOfDay = (h % 24);
            const isSunHour = hourOfDay >= 6 && hourOfDay <= 18;
            const sunFraction = isSunHour ? Math.sin(Math.PI * (hourOfDay - 6) / 12) : 0;
            return {
              year: 2024,
              month: monthIdx + 1,
              day: Math.floor(h / 2) + 1,
              hour: hourOfDay + 1,
              minute: 0,
              temperature: data.ambientTemp + tempVariation[monthIdx],
              dewPoint: data.ambientTemp - 5,
              directNormalIrradiance: dailyGHI_Wh / 8 * sunFraction * 1.4,
              diffuseHorizontalIrradiance: dailyGHI_Wh / 12 * (isSunHour ? 0.35 : 0.02),
              globalHorizontalIrradiance: dailyGHI_Wh / 8 * sunFraction * 1.1,
              windSpeed: 2.5,
              relativeHumidity: 70,
              atmosphericPressure: 101325,
              cloudCover: 4,
            };
          });
        }),
      };
      setWeatherData(syntheticEPW);
    }
    handleSetView('energy');
  }, [weatherData, handleSetView]);

  // Callback de PVWatts Satelital: envía datos completos al Simulador
  const handlePVWattsToSimulator = useCallback((data: PVWattsToSimulatorData) => {
    setPvwattsData(data);
    // Si no hay weatherData cargado, crear uno sintético desde PVWatts
    if (!weatherData) {
      const syntheticEPW: EPWData = {
        location: {
          city: `PVWatts (${data.latitude.toFixed(2)}, ${data.longitude.toFixed(2)})`,
          state: data.stationCity || 'TMY',
          country: 'PVWatts/NREL',
          latitude: data.latitude,
          longitude: data.longitude,
          timezone: -5,
          elevation: 0,
        },
        weatherData: MONTHS.flatMap((_, monthIdx) => {
          const mData = data.monthlyData[monthIdx];
          const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][monthIdx];
          // Generar registros horarios realistas: 1 registro por hora × días del mes
          // POA mensual (kWh/m²) → distribuir en horas solares con perfil sinusoidal
          const totalHours = daysInMonth * 24;
          const records = [];
          // Energía diaria POA en Wh/m²
          const dailyPOA_Wh = (mData.poa_kWhm2 / daysInMonth) * 1000;
          // Integral del perfil sinusoidal en 12h solares: ∫sin(π*t/12)dt de 0 a 12 = 24/π ≈ 7.64
          const sinIntegral = 24 / Math.PI;
          // POA pico al mediodía para que la integral coincida con dailyPOA_Wh
          const peakPOA = dailyPOA_Wh / sinIntegral;
          for (let d = 0; d < daysInMonth; d++) {
            for (let h = 0; h < 24; h++) {
              const isSunHour = h >= 6 && h <= 18;
              const sunFraction = isSunHour ? Math.sin(Math.PI * (h - 6) / 12) : 0;
              const poaHour = peakPOA * sunFraction; // W/m² instantáneo esta hora
              records.push({
                year: 2024,
                month: monthIdx + 1,
                day: d + 1,
                hour: h + 1,
                minute: 0,
                temperature: mData.tamb_C + (isSunHour ? 2 : -2),
                dewPoint: mData.tamb_C - 5,
                directNormalIrradiance: poaHour * 0.65,
                diffuseHorizontalIrradiance: poaHour * 0.30,
                globalHorizontalIrradiance: poaHour * 0.85,
                windSpeed: mData.wspd_ms,
                relativeHumidity: 70,
                atmosphericPressure: 101325,
                cloudCover: 4,
              });
            }
          }
          return records;
        }),
      };
      setWeatherData(syntheticEPW);
    }
    handleSetView('energy');
  }, [weatherData, handleSetView]);

  // Callback del BIPVGlassSimulator: envía resultados IAM+Soiling al Simulador de Energía
  const handleBipvToSimulator = useCallback((data: BIPVToEnergyData) => {
    // Validación: verificar que hay datos de irradiación cargados (POA disponible)
    if (!weatherData && !prospectorData) {
      toast.error('⚠️ Orden de importación incorrecto', {
        description: 'Primero debe importar datos de irradiación desde Heatmap PVGIS, PVWatts Satelital o cargar un archivo EPW antes de enviar los datos IAM+Soiling al Simulador de Energía.',
        duration: 8000,
      });
      return;
    }
    setBipvToEnergyData(data);
    toast.success('✅ Datos IAM+Soiling enviados al Simulador', {
      description: 'Panel BIPV, IAM mensual y soiling mensual configurados correctamente.',
      duration: 4000,
    });
    handleSetView('energy');
  }, [handleSetView, weatherData, prospectorData]);

  // Callback de auto-corrección: re-simula BIPV con datos horarios reales
  const handleResimultateBIPV = useCallback(() => {
    if (!bipvToEnergyData || !weatherData) return;

    // Reconstruir WeatherHourData[] desde EPW
    const hourlyData: WeatherHourData[] = weatherData.weatherData.map(d => ({
      month: d.month,
      day: d.day,
      hour: d.hour,
      dni: d.directNormalIrradiance,
      ghi: d.globalHorizontalIrradiance,
      dhi: d.diffuseHorizontalIrradiance,
      tempAir: d.temperature,
      windSpeed: d.windSpeed,
    }));

    // Reconstruir BIPVGlassTechnology desde bipvData
    const techFromCatalog = BIPV_GLASS_CATALOG.find(t => t.name === bipvToEnergyData.technology);
    const technology = techFromCatalog || {
      id: 'resim_' + bipvToEnergyData.technology,
      name: bipvToEnergyData.technology,
      generation: bipvToEnergyData.generation as '1G' | '2G' | '3G',
      generationLabel: bipvToEnergyData.generation,
      eficienciaBase: bipvToEnergyData.eficienciaAjustada / (1 - bipvToEnergyData.transparencia * 0.5),
      coefTemperatura: bipvToEnergyData.coefTemperatura,
      noct: bipvToEnergyData.noct,
      b0Ashrae: 0.05,
      description: 'Reconstruido para re-simulación',
    };

    // Reconstruir SoilingConfig (usar soiling promedio como base mensual)
    const soilingBase = bipvToEnergyData.soilingPromedio;
    const monthlyFactors: Record<number, number> = {};
    for (let m = 1; m <= 12; m++) monthlyFactors[m] = soilingBase;

    const config: BIPVSimulationConfig = {
      technology,
      transparencia: bipvToEnergyData.transparencia,
      areaM2: bipvToEnergyData.areaM2,
      inclinacionFachada: bipvToEnergyData.tilt,
      azimutFachada: bipvToEnergyData.azimuth,
      soiling: {
        monthlyFactors,
        precipitableWaterThreshold: 25,
        autoWashReduction: 0.15,
      },
      kBipv: bipvToEnergyData.kBipv,
      transpositionModel: bipvToEnergyData.transpositionModel,
    };

    // Ejecutar simulación completa (síncrona, ~8760 iteraciones)
    const summary = runBIPVSimulation(
      hourlyData,
      weatherData.location.latitude,
      weatherData.location.longitude,
      weatherData.location.timezone,
      config
    );

    // Actualizar bipvToEnergyData con la producción mensual real
    setBipvToEnergyData(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        produccionMensualKwh: summary.produccionMensualKwh,
        energiaAnualKwh: summary.energiaAnualKwh,
        energiaAnualKwhM2: summary.energiaAnualKwhM2,
        iamPromedio: summary.iamPromedio,
        soilingPromedio: summary.soilingPromedio,
        factorTermicoPromedio: summary.factorTermicoPromedio,
      };
    });
  }, [bipvToEnergyData, weatherData]);

  // === CÁLCULO POA MEJORADO ===
  // Usa calculateHourlyPOA (Liu-Jordan/Perez real) con ángulos solares horarios
  // Sincronizado con parámetros del Análisis POA (tilt, azimut, albedo, modelo)
  // Incluye windSpeed real del EPW
  const effectiveTilt = poaTilt ?? Math.round(weatherData?.location.latitude ?? 5);

  const poaData = useMemo(() => {
    if (!weatherData) return [];

    // === OVERRIDE: Si hay datos del Prospector, generar POA desde GHI PVGIS ===
    if (prospectorData) {
      const monthlyFractions = [0.085, 0.082, 0.088, 0.083, 0.080, 0.078, 0.080, 0.083, 0.082, 0.083, 0.080, 0.096];
      const tempVariation = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 1.5, 1.0, 0.5, 0.0];
      const fi = prospectorData.fi;
      const ghiAnnualWh = prospectorData.ghiAnnualKwhM2 * 1000;

      return MONTHS.map((month, monthIdx) => {
        const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][monthIdx];
        const monthGHI_Wh = ghiAnnualWh * monthlyFractions[monthIdx];
        // Dividir por 24 para obtener el promedio horario real (incluyendo noche=0)
        // calculateAnnualProduction reconstruye la energía mensual como: avgPOA × días × 24
        const avgHourlyPOA_Wm2 = monthGHI_Wh / daysInMonth / 24;
        const totalPOA = Math.round(avgHourlyPOA_Wm2 * fi);
        const directPOA = Math.round(totalPOA * 0.70);
        const diffusePOA = Math.round(totalPOA * 0.25);
        const reflectedPOA = Math.round(totalPOA * 0.05);
        const avgTemp = Math.round((prospectorData.ambientTemp + tempVariation[monthIdx]) * 10) / 10;

        return { month, directPOA, diffusePOA, reflectedPOA, totalPOA, avgTemp, avgWindSpeed: 2.5 };
      });
    }

    // === RUTA MEJORADA: Cálculo POA horario real con Liu-Jordan/Perez ===
    const lat = weatherData.location.latitude;
    const lon = weatherData.location.longitude;
    const stdMeridian = weatherData.location.timezone * 15; // Convertir zona horaria a meridiano estándar
    const tiltRad = (effectiveTilt * Math.PI) / 180;
    const azimuthRad = (poaAzimuth * Math.PI) / 180;

    return MONTHS.map((month, monthIdx) => {
      const monthData = weatherData.weatherData.filter(w => w.month === monthIdx + 1);

      if (monthData.length === 0) {
        return {
          month,
          directPOA: 0,
          diffusePOA: 0,
          reflectedPOA: 0,
          totalPOA: 0,
          avgTemp: 0,
          avgWindSpeed: 1,
        };
      }

      // Calcular POA horario real para cada registro del mes
      let sumDirect = 0, sumDiffuse = 0, sumReflected = 0, sumTotal = 0;
      let sumTemp = 0, sumWind = 0;
      let validCount = 0;

      for (const w of monthData) {
        // Solo calcular para horas con irradiancia > 0
        if (w.globalHorizontalIrradiance > 0 || w.directNormalIrradiance > 0) {
          // Día del año aproximado
          const dayOfYear = Math.floor((monthIdx * 30.44) + (w.day || 15));
          const hourlyPOA = calculateHourlyPOA(
            lat, lon, stdMeridian,
            dayOfYear,
            w.hour - 1, // EPW usa 1-24, calculateHourlyPOA usa 0-23
            w.minute || 0,
            w.directNormalIrradiance,
            w.diffuseHorizontalIrradiance,
            w.globalHorizontalIrradiance,
            tiltRad,
            azimuthRad,
            poaAlbedo,
            poaUsePerez
          );
          sumDirect += hourlyPOA.directPOA;
          sumDiffuse += hourlyPOA.diffusePOA;
          sumReflected += hourlyPOA.reflectedPOA;
          sumTotal += hourlyPOA.totalPOA;
          validCount++;
        }
        sumTemp += w.temperature;
        sumWind += w.windSpeed;
      }

      // Dividir por TODAS las horas del mes (monthData.length) para obtener
      // el promedio horario real (incluyendo noche=0). Esto es consistente con
      // calculateAnnualProduction que multiplica avgPOA × daysInMonth × 24.
      const n = monthData.length || 1;
      const avgTemp = sumTemp / monthData.length;
      const avgWindSpeed = sumWind / monthData.length;

      return {
        month,
        directPOA: Math.round(sumDirect / n),
        diffusePOA: Math.round(sumDiffuse / n),
        reflectedPOA: Math.round(sumReflected / n),
        totalPOA: Math.round(sumTotal / n),
        avgTemp: Math.round(avgTemp * 10) / 10,
        avgWindSpeed: Math.round(avgWindSpeed * 10) / 10,
      };
    });
  }, [weatherData, prospectorData, effectiveTilt, poaAzimuth, poaAlbedo, poaUsePerez]);

  // Datos para el mapa
  const mapCities = useMemo(() => {
    if (!selectedCity) return [];
    return [{
      id: selectedCity.id,
      name: selectedCity.cityName,
      latitude: selectedCity.latitude,
      longitude: selectedCity.longitude,
      country: selectedCity.country,
      hasEPW: true,
    }];
  }, [selectedCity]);

  // Datos multi-fachada para el Reporte PDF
  const multiFacadeReportData = useMemo(() => {
    if (!modelFacades || modelFacades.length === 0 || !weatherData) return undefined;
    try {
      const lat = weatherData.location.latitude;
      const lon = weatherData.location.longitude;
      const tz = weatherData.location.timezone;
      const stdMeridian = tz * 15;

      const results = modelFacades.map((facade) => {
        const analysis = calculateMonthlyShadingFactorsForFacade(facade, weatherData, modelObstacles3D || [], modelNorthOffset);
        const facadeTilt = facade.tilt;
        const facadeAz = facade.azimuthNormal;
        const facadeTiltRad = (facadeTilt * Math.PI) / 180;
        const facadeAzRad = (facadeAz * Math.PI) / 180;
        let poaTotal = 0;

        // Calcular día del año para cada registro horario y acumular POA
        weatherData.weatherData.forEach(h => {
          if (h.globalHorizontalIrradiance <= 0 && h.directNormalIrradiance <= 0) return;
          // Calcular dayOfYear a partir de month/day
          const doy = Math.floor((Date.UTC(2023, h.month - 1, h.day) - Date.UTC(2023, 0, 0)) / 86400000);
          const poa = calculateHourlyPOA(
            lat, lon, stdMeridian,
            doy, h.hour, h.minute || 30,
            h.directNormalIrradiance || 0,
            h.diffuseHorizontalIrradiance || 0,
            h.globalHorizontalIrradiance || 0,
            facadeTiltRad, facadeAzRad, 0.2
          );
          poaTotal += (poa.totalPOA || 0) / 1000; // Wh/m² → kWh/m²
        });

        // Producción AC
        const panelPower = energyData.panelPower || 400;
        const panelQty = energyData.panelQuantity || 1;
        const systemLosses = energyData.systemLosses || 0.15;
        const capacity = panelPower * panelQty / 1000; // kWp
        const fsAnnual = analysis.annualFS;
        const prodAC = poaTotal * capacity * (1 - systemLosses) * fsAnnual;
        const specificYield = capacity > 0 ? prodAC / capacity : 0;
        const pr = poaTotal > 0 ? prodAC / (poaTotal * capacity) : 0;

        // ROI por fachada - usar parámetros del Simulador si disponibles
        // electricityRate del simulador está en USD/kWh, convertir a COP/kWh (TRM ~4200)
        const TRM_APPROX = 4200;
        const elecRateCOP = financialParams.electricityRate > 0 ? financialParams.electricityRate * TRM_APPROX : 850;
        const costPerWpCOP = financialParams.costPerWp > 0 ? financialParams.costPerWp * TRM_APPROX : 4500;
        const facadeSystemCost = capacity * 1000 * costPerWpCOP; // COP
        const facadeAnnualSavings = prodAC * elecRateCOP;
        const facadePayback = facadeAnnualSavings > 0 ? facadeSystemCost / facadeAnnualSavings : 99;
        const facadeROI25 = facadeSystemCost > 0 ? ((facadeAnnualSavings * 25 - facadeSystemCost) / facadeSystemCost) * 100 : 0;

        return {
          facadeName: facade.name,
          azimuth: facadeAz,
          tilt: facadeTilt,
          area: facade.area || 0,
          fsAnnual,
          poaAnnual: poaTotal,
          productionAC: prodAC,
          specificYield,
          performanceRatio: pr,
          rank: 0,
          annualSavingsCOP: facadeAnnualSavings,
          paybackYears: facadePayback,
          roi25Year: facadeROI25,
        };
      });
      // Ordenar por producción y asignar rank
      results.sort((a, b) => b.productionAC - a.productionAC);
      results.forEach((r, i) => r.rank = i + 1);
      const totalArea = results.reduce((s, r) => s + r.area, 0);
      const totalAC = results.reduce((s, r) => s + r.productionAC, 0);
      const avgFS = totalArea > 0 ? results.reduce((s, r) => s + r.fsAnnual * r.area, 0) / totalArea : 1;
      const avgPR = totalArea > 0 ? results.reduce((s, r) => s + r.performanceRatio * r.area, 0) / totalArea : 0;
      const TRM_APPROX = 4200;
      const elecRateCOP = financialParams.electricityRate > 0 ? financialParams.electricityRate * TRM_APPROX : 850;
      const costPerWpCOP = financialParams.costPerWp > 0 ? financialParams.costPerWp * TRM_APPROX : 4500;
      const totalCapacity = (energyData.panelPower || 400) * (energyData.panelQuantity || 1) / 1000;
      const totalSystemCost = totalCapacity * 1000 * costPerWpCOP;

      return {
        results,
        totalArea,
        totalProductionAC: totalAC,
        avgFS,
        avgPR,
        bestFacade: results[0]?.facadeName || '',
        panelInfo: `${energyData.panelPower}W x ${energyData.panelQuantity}`,
        systemCapacity: `${(energyData.panelPower * energyData.panelQuantity / 1000).toFixed(2)} kWp`,
        systemCostPerWp: costPerWpCOP,
        electricityRate: elecRateCOP,
        totalSystemCost,
      };
    } catch (e) {
      console.error('Error calculando multi-fachada para reporte:', e);
      return undefined;
    }
  }, [modelFacades, weatherData, modelObstacles3D, modelNorthOffset, energyData, financialParams]);

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-gray-200 bg-gray-50">
        <div className="container py-4">
          <div className="flex justify-between items-center flex-wrap gap-4">
            <h1 className="text-2xl font-bold text-gray-900">Solar Shading Calculator</h1>
            <nav className="flex gap-2 flex-wrap">
              <button
                onClick={() => handleSetView('calculator')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'calculator'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                Calculadora
              </button>
              <button
                onClick={() => handleSetView('templates')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'templates'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                Plantillas
              </button>
              <button
                onClick={() => handleSetView('cities')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'cities'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                Ciudades {selectedCity && '✓'}
              </button>
              <button
                onClick={() => handleSetView('map')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'map'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                Mapa
              </button>
              <button
                onClick={() => handleSetView('weather')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'weather'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                Datos Meteorológicos {weatherData && '✓'}
              </button>
              {/* === Pestañas satelitales: siempre visibles === */}
              <button
                onClick={() => handleSetView('heatmap')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'heatmap'
                    ? 'bg-orange-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                🔥 Heatmap PVGIS
              </button>
              <button
                onClick={() => handleSetView('pvgis')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'pvgis'
                    ? 'bg-green-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                🌐 PVGIS Analyzer
              </button>
              <button
                onClick={() => handleSetView('pvwatts')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'pvwatts'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                🛰️ PVWatts Satelital
              </button>
              <button
                onClick={() => handleSetView('bipv')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'bipv'
                    ? 'bg-amber-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                🔧 Diagnóstico BIPV
              </button>
              <button
                onClick={() => handleSetView('bipvglass')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'bipvglass'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                🔬 IAM + Soiling BIPV
              </button>
              {/* === Simulador: visible con EPW o datos satelitales === */}
              {(weatherData || pvwattsData || pvgisData) && (
                <button
                  onClick={() => handleSetView('energy')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    view === 'energy'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  Simulador Energía {(pvwattsData || pvgisData) && '✓'}
                </button>
              )}
              {/* === Pestañas que requieren EPW === */}
              {weatherData && (
                <>
                  <button
                    onClick={() => handleSetView('radiation')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      view === 'radiation'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Radiación Solar
                  </button>
                  <button
                    onClick={() => handleSetView('optimizer')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      view === 'optimizer'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Optimizador
                  </button>
                  <button
                    onClick={() => handleSetView('poa')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      view === 'poa'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Análisis POA
                  </button>
                  <button
                    onClick={() => handleSetView('report')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      view === 'report'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    📄 Generar Reporte
                  </button>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>

      <main className="container py-12">
        {view === 'calculator' && <ShadingCalculator initialPoints={shadingPoints} templateData={templateData} weatherData={weatherData} onPointsChange={handleShadingPointsChange} onWeatherDataOverride={setWeatherData} onFacadeAnalysis3D={setFacadeAnalysis3D} onModelDataReady={(data) => { setModelFacades(data.facades); setModelObstacles3D(data.obstacleVertices3D); setModelNorthOffset(data.northOffset); }} externalActiveFacadeIdx={externalFacadeIdx} />}
        {view === 'templates' && <TemplateManager onLoadTemplate={handleLoadTemplate} />}
        {view === 'cities' && <CityWeatherLibrary onSelectCity={handleSelectCity} selectedCityId={selectedCity?.id || null} />}
        {view === 'map' && <CityMapExplorer cities={mapCities} onSelectCity={(city) => {
          if (selectedCity) handleSelectCity(selectedCity);
        }} />}
        {view === 'weather' && <WeatherDataManager onWeatherDataLoaded={setWeatherData} weatherData={weatherData} />}
        {view === 'radiation' && weatherData && <SolarRadiationChart weatherData={weatherData} />}
        {view === 'optimizer' && weatherData && <OrientationOptimizer weatherData={weatherData} sharedTilt={effectiveTilt} sharedAzimuth={poaAzimuth} onConfigChange={(cfg) => { setPoaTilt(cfg.tilt); setPoaAzimuth(cfg.azimuth); }} tiltRange={installTiltRange} azimuthLocked={installAzimuthLocked} installationType={installTypeName} onSendToSimulator={(result) => { setOptimizerResult(result); setPoaTilt(result.optimalTilt); setPoaAzimuth(result.optimalAzimuth); handleSetView('energy'); }} />}
        {view === 'poa' && weatherData && <POAAnalyzer weatherData={weatherData} tiltAngle={effectiveTilt} surfaceAzimuth={poaAzimuth} sharedAlbedo={poaAlbedo} sharedUsePerez={poaUsePerez} onConfigChange={(cfg) => { if (cfg.tilt !== undefined) setPoaTilt(cfg.tilt); if (cfg.azimuth !== undefined) setPoaAzimuth(cfg.azimuth); if (cfg.albedo !== undefined) setPoaAlbedo(cfg.albedo); if (cfg.usePerez !== undefined) setPoaUsePerez(cfg.usePerez); }} />}
        {view === 'energy' && weatherData && poaData.length > 0 && <EnergyProductionSimulator weatherData={weatherData} poaData={poaData} shadingFactors={monthlyShadingFactors} facadeAnalysis3D={facadeAnalysis3D} prospectorData={prospectorData} onDiscardProspector={() => setProspectorData(null)} optimizerResult={optimizerResult} onDiscardOptimizer={() => setOptimizerResult(null)} pvgisData={pvgisData} onDiscardPvgis={() => setPvgisData(null)} pvwattsData={pvwattsData} onDiscardPvwatts={() => setPvwattsData(null)} onInstallConfigChange={(cfg) => { if (cfg.tiltRange) setInstallTiltRange(cfg.tiltRange); if (cfg.azimuthLocked !== undefined) setInstallAzimuthLocked(cfg.azimuthLocked); if (cfg.name) setInstallTypeName(cfg.name); }} poaConfig={{ tilt: effectiveTilt, azimuth: poaAzimuth, albedo: poaAlbedo, usePerez: poaUsePerez, source: optimizerResult ? 'optimizer' : prospectorData ? 'prospector' : 'epw_hourly' }} onPoaConfigChange={(cfg) => { if (cfg.tilt !== undefined) setPoaTilt(cfg.tilt); if (cfg.azimuth !== undefined) setPoaAzimuth(cfg.azimuth); if (cfg.albedo !== undefined) setPoaAlbedo(cfg.albedo); if (cfg.usePerez !== undefined) setPoaUsePerez(cfg.usePerez); }} modelFacades={modelFacades} modelObstacles3D={modelObstacles3D} modelNorthOffset={modelNorthOffset} onFacadeSelectFromSimulator={(idx) => { setExternalFacadeIdx(idx); if (modelFacades && modelFacades[idx] && weatherData) { const analysis = calculateMonthlyShadingFactorsForFacade(modelFacades[idx], weatherData, modelObstacles3D || [], modelNorthOffset); analysis.facadeIdx = idx; setFacadeAnalysis3D(analysis); /* Sincronizar POA con ángulos de la fachada seleccionada (ya en grados) */ setPoaTilt(Math.round(modelFacades[idx].tilt)); setPoaAzimuth(Math.round(modelFacades[idx].azimuthNormal)); } }} onFinancialParamsChange={setFinancialParams} onEnergyDataChange={setEnergyData} bipvData={bipvToEnergyData} onDiscardBipv={() => setBipvToEnergyData(null)} onReturnToBIPV={() => handleSetView('bipvglass')} onResimultateBIPV={handleResimultateBIPV} />}
        {view === 'report' && weatherData && (
          <ReportGenerator
            city={selectedCity?.cityName || weatherData.location.city || 'Sin definir'}
            country={selectedCity?.country || weatherData.location.country || 'Colombia'}
            latitude={selectedCity?.latitude || weatherData.location.latitude || 0}
            longitude={selectedCity?.longitude || weatherData.location.longitude || 0}
            elevation={selectedCity?.elevation || weatherData.location.elevation || 0}
            shadingPoints={shadingPoints}
            poaData={poaData}
            weatherData={weatherData}
            panelPower={energyData.panelPower}
            panelEfficiency={energyData.panelEfficiency}
            panelArea={energyData.panelArea}
            panelQuantity={energyData.panelQuantity}
            tilt={energyData.tilt}
            azimuth={energyData.azimuth}
            annualProduction={energyData.annualProduction}
            capacityFactor={energyData.capacityFactor}
            performanceRatio={energyData.performanceRatio}
            systemLosses={energyData.systemLosses}
            paybackPeriod={energyData.paybackPeriod}
            roi10Year={energyData.roi10Year}
            roi25Year={energyData.roi25Year}
            multiFacadeData={multiFacadeReportData}
            shadingLoss={energyData.shadingLoss}
            annualFS={energyData.annualFS}
            shadingSource={energyData.shadingSource}
            surfaceName={facadeAnalysis3D ? facadeAnalysis3D.facadeName : installTypeName}
            facadeAnalysis3D={facadeAnalysis3D ? {
              facadeName: facadeAnalysis3D.facadeName || 'Fachada',
              facadeIdx: facadeAnalysis3D.facadeIdx ?? 0,
              azimuth: facadeAnalysis3D.azimuth ?? 180,
              tilt: facadeAnalysis3D.tilt ?? 90,
              area: facadeAnalysis3D.area ?? 30,
              monthlyData: facadeAnalysis3D.monthlyData,
              monthlyShadingFactors: facadeAnalysis3D.monthlyShadingFactors,
              annualFS: facadeAnalysis3D.monthlyShadingFactors.reduce((a, b) => a + b, 0) / 12,
              annualShadingLoss: (1 - facadeAnalysis3D.monthlyShadingFactors.reduce((a, b) => a + b, 0) / 12) * 100,
            } : undefined}
          />
        )}
        {/* IrradianceHeatmap: once mounted, stays mounted (hidden via CSS) to prevent map/DOM errors */}
        {heatmapEverShown && (
          <div style={{ display: view === 'heatmap' ? 'block' : 'none' }}>
            <IrradianceHeatmap
              initialLat={selectedCity?.latitude || 6.25}
              initialLng={selectedCity?.longitude || -75.56}
              cityName={selectedCity?.cityName || 'Medellín'}
              onUseInSimulator={handleProspectorToSimulator}
              modelFacades={modelFacades}
            />
          </div>
        )}
        {/* PVWattsSatellite: once mounted, stays mounted (hidden via CSS) to prevent map/DOM errors */}
        {pvwattsEverShown && (
          <div style={{ display: view === 'pvwatts' ? 'block' : 'none' }}>
            <PVWattsSatellite
              initialLat={selectedCity?.latitude || 6.25}
              initialLng={selectedCity?.longitude || -75.56}
              cityName={selectedCity?.cityName || 'Medellín'}
              onUseInSimulator={handleProspectorToSimulator}
              onSendPVWattsToSimulator={handlePVWattsToSimulator}
              modelFacades={modelFacades}
            />
          </div>
        )}
        {/* PVGISAnalyzer: once mounted, stays mounted (hidden via CSS) to prevent insertBefore errors */}
        {pvgisEverShown && (
          <div style={{ display: view === 'pvgis' ? 'block' : 'none' }}>
            <PVGISAnalyzer
              initialLat={selectedCity?.latitude || 6.25}
              initialLng={selectedCity?.longitude || -75.56}
              cityName={selectedCity?.cityName || 'Medellín'}
              onSendToSimulator={(data) => {
                setPvgisData(data);
                handleSetView('energy');
              }}
              modelFacades={modelFacades}
            />
          </div>
        )}
        {view === 'bipv' && <BIPVDiagnostic />}
        {view === 'bipvglass' && (
          <BIPVGlassSimulator
            weatherData={weatherData ? weatherData.weatherData.map(w => ({
              month: w.month,
              day: w.day,
              hour: w.hour,
              ghi: w.globalHorizontalIrradiance,
              dni: w.directNormalIrradiance,
              dhi: w.diffuseHorizontalIrradiance,
              temperature: w.temperature,
              windSpeed: w.windSpeed,
            })) : undefined}
            latitude={selectedCity?.latitude || weatherData?.location.latitude || 6.25}
            longitude={selectedCity?.longitude || weatherData?.location.longitude || -75.56}
            timezone={weatherData?.location.timezone || -5}
            facades={modelFacades.length > 0 ? modelFacades.map(f => ({
              name: f.name,
              azimuthNormal: f.azimuthNormal,
              tilt: f.tilt,
              area: f.area,
            })) : undefined}
            facadeAnalysis3D={facadeAnalysis3D ? {
              facadeName: facadeAnalysis3D.facadeName || 'Fachada',
              facadeIdx: facadeAnalysis3D.facadeIdx ?? 0,
              azimuth: facadeAnalysis3D.azimuth ?? 180,
              tilt: facadeAnalysis3D.tilt ?? 90,
              area: facadeAnalysis3D.area ?? 30,
              monthlyShadingFactors: facadeAnalysis3D.monthlyShadingFactors,
              annualFS: facadeAnalysis3D.monthlyShadingFactors.reduce((a, b) => a + b, 0) / 12,
              annualShadingLoss: (1 - facadeAnalysis3D.monthlyShadingFactors.reduce((a, b) => a + b, 0) / 12) * 100,
            } : undefined}
            shadingFactors={monthlyShadingFactors}
            obstacleVertices3D={modelObstacles3D}
            onSendToEnergySimulator={handleBipvToSimulator}
            hasIrradianceData={!!(weatherData || prospectorData)}
          />
        )}
      </main>
    </div>
  );
}
