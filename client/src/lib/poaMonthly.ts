/**
 * Agregación mensual de POA (Plane of Array) desde datos EPW horarios.
 *
 * Única fuente compartida entre `Home.tsx` (contrato consumido por
 * EnergyProductionSimulator/ReportGenerator) y `POAAnalyzer.tsx` (vista
 * "Análisis POA") -- ver CodeSpecs/02-recurso-solar/react/diseno.md.
 *
 * Deliberadamente fuera de esta función: la ruta Prospector/PVGIS (estimación
 * rápida desde un único punto de GHI anual), IAM/soiling y PR_T -- esas rutas
 * siguen su propio cálculo en sus componentes correspondientes.
 */
import { EPWData } from './epwParser';
import { calculateHourlyPOA } from './liuJordanModel';

export const POA_MONTH_LABELS = [
  'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic',
];

export interface MonthlyPOAData {
  month: string;
  directPOA: number;
  diffusePOA: number;
  reflectedPOA: number;
  totalPOA: number;
  avgTemp: number;
  avgWindSpeed: number;
}

/**
 * Calcula el POA horario real (Liu-Jordan o Perez) para cada hora del EPW y
 * agrega promedios mensuales.
 *
 * Solo las horas con irradiancia (GHI u DNI > 0) contribuyen a las
 * componentes solares (directa/difusa/reflejada/total); las horas sin
 * irradiancia se excluyen de esa suma pero SIGUEN contando en el
 * denominador (todas las horas del mes) y en el promedio de
 * temperatura/viento -- mismo comportamiento que ya tenía `Home.tsx`.
 *
 * @param weatherData EPW ya cargado y validado (ver `solarRigor.ts`).
 * @param tiltDeg Inclinación de la superficie, en grados.
 * @param azimuthDeg Azimut de la superficie, en grados (0 = Sur).
 * @param albedo Reflectancia del suelo, fracción 0-1.
 * @param usePerezModel `true` usa el modelo Perez; `false` usa Liu-Jordan.
 */
export function calculateMonthlyPOA(
  weatherData: EPWData,
  tiltDeg: number,
  azimuthDeg: number,
  albedo: number,
  usePerezModel: boolean,
): MonthlyPOAData[] {
  const lat = weatherData.location.latitude;
  const lon = weatherData.location.longitude;
  const stdMeridian = weatherData.location.timezone * 15; // zona horaria -> meridiano estándar
  const tiltRad = (tiltDeg * Math.PI) / 180;
  const azimuthRad = (azimuthDeg * Math.PI) / 180;

  return POA_MONTH_LABELS.map((month, monthIdx) => {
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

    let sumDirect = 0, sumDiffuse = 0, sumReflected = 0, sumTotal = 0;
    let sumTemp = 0, sumWind = 0;

    for (const w of monthData) {
      // Solo calcular POA para horas con irradiancia > 0
      if (w.globalHorizontalIrradiance > 0 || w.directNormalIrradiance > 0) {
        // EPW conserva el día calendario exacto; no aproximar el mes.
        const dayOfYear = Math.floor(
          (Date.UTC(2023, w.month - 1, w.day || 15) - Date.UTC(2023, 0, 0)) / 86400000,
        );
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
          albedo,
          usePerezModel,
        );
        sumDirect += hourlyPOA.directPOA;
        sumDiffuse += hourlyPOA.diffusePOA;
        sumReflected += hourlyPOA.reflectedPOA;
        sumTotal += hourlyPOA.totalPOA;
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
}
