/**
 * facadeShadingAnalysis.ts
 * 
 * Calcula los factores de sombreado (FS) mensuales para una fachada específica
 * del modelo 3D importado, considerando los obstáculos del entorno.
 * 
 * Este módulo conecta el análisis geométrico del modelo 3D con el Simulador de Energía,
 * proporcionando los 12 valores mensuales de FS que alimentan el cálculo BIPV.
 */

import { DetectedFacade, Vertex3D, recalculateForFacade } from '@/lib/buildingModelImporter';
import { EPWData, getWeatherForDateTime } from '@/lib/epwParser';
import { calculateSolarPosition } from '@/lib/solarPosition';
import { ObstaclePolygon } from '@/components/SunPathDiagram';

export interface MonthlyFacadeAnalysis {
  month: number; // 1-12
  monthName: string;
  fsAverage: number; // Factor de sombreado promedio del mes (0-1, 1=sin sombra)
  totalSunHours: number; // Horas de sol totales en el mes
  effectiveSunHours: number; // Horas de sol sin sombra
  shadedHours: number; // Horas con sombra
  poaMonthly: number; // kWh/m²/mes con sombreado
  poaNoShading: number; // kWh/m²/mes sin sombreado
  shadingLoss: number; // % de pérdida por sombreado en el mes
}

export interface FacadeFullAnalysis {
  facadeName: string;
  facadeIdx: number;
  azimuth: number;
  tilt: number;
  area: number;
  monthlyData: MonthlyFacadeAnalysis[];
  annualFS: number; // FS promedio anual ponderado por irradiancia
  annualPOA: number; // kWh/m²/año con sombreado
  annualPOANoShading: number; // kWh/m²/año sin sombreado
  annualShadingLoss: number; // % pérdida anual
  monthlyShadingFactors: number[]; // Array de 12 valores para el Simulador
}

const MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
const DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

/**
 * Verifica si un punto solar (azimut, altitud) está dentro de algún polígono de obstáculo
 * usando el algoritmo de ray-casting en coordenadas estereográficas del diagrama solar.
 */
function checkPointInObstacles(azimuth: number, altitude: number, obstacles: ObstaclePolygon[]): boolean {
  for (const obs of obstacles) {
    if (!obs.visible || obs.vertices.length < 3) continue;

    // Convertir punto solar a coordenadas SVG estereográficas
    const compassAz = (azimuth + 180) % 360;
    const r = 250 * (90 - altitude) / 90;
    const angleRad = (compassAz - 90) * Math.PI / 180;
    const px = 300 + r * Math.cos(angleRad);
    const py = 300 + r * Math.sin(angleRad);

    // Convertir vértices del obstáculo a SVG
    const svgPoly = obs.vertices.map(v => {
      const cAz = (v.azimuth + 180) % 360;
      const rV = 250 * (90 - v.altitude) / 90;
      const aRad = (cAz - 90) * Math.PI / 180;
      return { x: 300 + rV * Math.cos(aRad), y: 300 + rV * Math.sin(aRad) };
    });

    // Ray casting algorithm
    let inside = false;
    for (let i = 0, j = svgPoly.length - 1; i < svgPoly.length; j = i++) {
      const xi = svgPoly[i].x, yi = svgPoly[i].y;
      const xj = svgPoly[j].x, yj = svgPoly[j].y;
      if (((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) {
        inside = !inside;
      }
    }
    if (inside) return true;
  }
  return false;
}

/**
 * Calcula los factores de sombreado mensuales para una fachada específica.
 * 
 * Método: Para cada mes, se muestrean múltiples días representativos (1, 8, 15, 22)
 * y todas las horas con sol (5-20h). Para cada hora, se calcula:
 * 1. La posición solar exacta
 * 2. Si el punto solar está dentro de algún obstáculo (sombreado geométrico)
 * 3. La irradiancia POA con y sin sombreado
 * 
 * El FS mensual se calcula como la relación POA_con_sombra / POA_sin_sombra,
 * ponderado por la irradiancia real de cada hora (del archivo EPW).
 */
export function calculateMonthlyShadingFactorsForFacade(
  facade: DetectedFacade,
  weatherData: EPWData,
  obstacleVertices3D: Vertex3D[][],
  northOffset: number,
): FacadeFullAnalysis {
  const { latitude, longitude, timezone } = weatherData.location;
  const albedo = 0.2;

  // Recalcular obstáculos desde la perspectiva de esta fachada
  const facadeObstacles = recalculateForFacade(facade, obstacleVertices3D, northOffset);

  const monthlyData: MonthlyFacadeAnalysis[] = [];
  let annualPOA = 0;
  let annualPOANoShading = 0;

  for (let month = 1; month <= 12; month++) {
    const daysInMonth = DAYS_IN_MONTH[month - 1];
    // Muestrear 4 días representativos por mes para mayor precisión
    const sampleDays = [1, 8, 15, 22];
    
    let monthPOA = 0;
    let monthPOANoShading = 0;
    let totalSunHours = 0;
    let effectiveSunHours = 0;
    let shadedHours = 0;

    for (const day of sampleDays) {
      for (let hour = 5; hour <= 20; hour++) {
        // Muestrear cada media hora para mayor resolución
        for (const halfHour of [0, 0.5]) {
          const h = hour + halfHour;
          const solarPos = calculateSolarPosition(latitude, longitude, timezone, month, day, h);
          if (solarPos.altitude <= 0) continue;

          const weather = getWeatherForDateTime(weatherData, month, day, hour);
          if (!weather) continue;

          const GHI = weather.globalHorizontalIrradiance;
          const DNI = weather.directNormalIrradiance;
          const DHI = weather.diffuseHorizontalIrradiance;
          if (GHI <= 0 && DNI <= 0) continue;

          // Calcular POA sobre la superficie inclinada (Liu-Jordan)
          const tiltRad = facade.tilt * Math.PI / 180;
          const altRad = solarPos.altitude * Math.PI / 180;
          const solarAzRad = solarPos.azimuth * Math.PI / 180;
          const surfAzRad = facade.azimuthNormal * Math.PI / 180;

          // Ángulo de incidencia (cos θi)
          const cosIncidence = Math.sin(altRad) * Math.cos(tiltRad) +
            Math.cos(altRad) * Math.sin(tiltRad) * Math.cos(solarAzRad - surfAzRad);

          // Componentes de irradiancia sobre la superficie
          const directPOA = Math.max(0, DNI * cosIncidence);
          const diffusePOA = DHI * (1 + Math.cos(tiltRad)) / 2;
          const reflectedPOA = GHI * albedo * (1 - Math.cos(tiltRad)) / 2;
          const poaTotal = directPOA + diffusePOA + reflectedPOA;

          if (poaTotal <= 0) continue;

          // Contabilizar horas de sol (cada muestra = 0.5h)
          totalSunHours += 0.5;

          // POA sin sombreado
          monthPOANoShading += poaTotal * 0.5; // Wh/m² (media hora)

          // Verificar sombreado geométrico
          const isShaded = facadeObstacles.length > 0 && 
            checkPointInObstacles(solarPos.azimuth, solarPos.altitude, facadeObstacles);

          if (isShaded) {
            // Cuando hay sombra, solo llega la componente difusa + reflejada (no la directa)
            const poaShaded = diffusePOA + reflectedPOA;
            monthPOA += poaShaded * 0.5;
            shadedHours += 0.5;
          } else {
            monthPOA += poaTotal * 0.5;
            effectiveSunHours += 0.5;
          }
        }
      }
    }

    // Escalar de los 4 días muestreados al mes completo
    const scaleFactor = daysInMonth / sampleDays.length;
    const monthPOAScaled = (monthPOA * scaleFactor) / 1000; // Wh → kWh/m²
    const monthPOANoShadingScaled = (monthPOANoShading * scaleFactor) / 1000;

    // FS mensual = POA_con_sombra / POA_sin_sombra
    const fsMonth = monthPOANoShadingScaled > 0
      ? Math.min(1.0, monthPOAScaled / monthPOANoShadingScaled)
      : 1.0;

    const shadingLoss = monthPOANoShadingScaled > 0
      ? ((monthPOANoShadingScaled - monthPOAScaled) / monthPOANoShadingScaled) * 100
      : 0;

    // Escalar horas al mes completo
    const sunHoursMonthly = (totalSunHours * scaleFactor);
    const effectiveSunHoursMonthly = (effectiveSunHours * scaleFactor);
    const shadedHoursMonthly = (shadedHours * scaleFactor);

    monthlyData.push({
      month,
      monthName: MONTH_NAMES[month - 1],
      fsAverage: fsMonth,
      totalSunHours: sunHoursMonthly,
      effectiveSunHours: effectiveSunHoursMonthly,
      shadedHours: shadedHoursMonthly,
      poaMonthly: monthPOAScaled,
      poaNoShading: monthPOANoShadingScaled,
      shadingLoss,
    });

    annualPOA += monthPOAScaled;
    annualPOANoShading += monthPOANoShadingScaled;
  }

  // FS anual ponderado por irradiancia
  const annualFS = annualPOANoShading > 0
    ? Math.min(1.0, annualPOA / annualPOANoShading)
    : 1.0;

  const annualShadingLoss = annualPOANoShading > 0
    ? ((annualPOANoShading - annualPOA) / annualPOANoShading) * 100
    : 0;

  // Array de 12 valores para el Simulador de Energía
  const monthlyShadingFactors = monthlyData.map(m => m.fsAverage);

  return {
    facadeName: facade.name,
    facadeIdx: 0,
    azimuth: facade.azimuthNormal,
    tilt: facade.tilt,
    area: facade.area,
    monthlyData,
    annualFS,
    annualPOA,
    annualPOANoShading,
    annualShadingLoss,
    monthlyShadingFactors,
  };
}

/**
 * Calcula los FS mensuales para todas las fachadas del modelo.
 * Devuelve un mapa de índice de fachada → análisis completo.
 */
export function calculateAllFacadesShadingFactors(
  facades: DetectedFacade[],
  weatherData: EPWData,
  obstacleVertices3D: Vertex3D[][],
  northOffset: number,
): FacadeFullAnalysis[] {
  return facades.map((facade, idx) => {
    const analysis = calculateMonthlyShadingFactorsForFacade(
      facade, weatherData, obstacleVertices3D, northOffset
    );
    return { ...analysis, facadeIdx: idx };
  });
}
