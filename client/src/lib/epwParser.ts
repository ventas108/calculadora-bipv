/**
 * Parser para archivos EPW (Energy Plus Weather)
 * Extrae datos meteorológicos horarios para análisis solar
 */

export interface LocationInfo {
  city: string;
  state: string;
  country: string;
  latitude: number;
  longitude: number;
  timezone: number;
  elevation: number;
}

export interface WeatherData {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  temperature: number; // °C
  dewPoint: number; // °C
  relativeHumidity: number; // %
  atmosphericPressure: number; // Pa
  directNormalIrradiance: number; // Wh/m²
  diffuseHorizontalIrradiance: number; // Wh/m²
  globalHorizontalIrradiance: number; // Wh/m²
  windSpeed: number; // m/s
  cloudCover: number; // 0-10
}

export interface EPWData {
  location: LocationInfo;
  weatherData: WeatherData[];
}

export const parseEPW = (content: string): EPWData => {
  const lines = content.trim().split('\n');
  
  if (lines.length < 3) {
    throw new Error('Archivo EPW inválido: menos de 3 líneas');
  }

  // Parsear encabezado de ubicación
  const locationLine = lines[0].split(',');
  const location: LocationInfo = {
    city: locationLine[1] || 'Unknown',
    state: locationLine[2] || '',
    country: locationLine[3] || '',
    latitude: parseFloat(locationLine[6]) || 0,
    longitude: parseFloat(locationLine[7]) || 0,
    timezone: parseFloat(locationLine[8]) || 0,
    elevation: parseFloat(locationLine[9]) || 0,
  };

  // Parsear datos meteorológicos
  // El formato EPW estándar tiene 8 líneas de encabezado:
  // 0: LOCATION, 1: DESIGN CONDITIONS, 2: TYPICAL/EXTREME PERIODS,
  // 3: GROUND TEMPERATURES, 4: HOLIDAYS/DAYLIGHT SAVINGS,
  // 5: COMMENTS 1, 6: COMMENTS 2, 7: DATA PERIODS
  // Los datos horarios empiezan en la línea 8.
  const weatherData: WeatherData[] = [];

  // Detectar dónde empiezan los datos: buscar la primera línea que empiece con un año numérico (4 dígitos)
  let dataStartIdx = 8; // Default: línea 8 (formato estándar)
  for (let i = 1; i < Math.min(lines.length, 15); i++) {
    const firstField = lines[i].split(',')[0].trim();
    if (/^\d{4}$/.test(firstField)) {
      dataStartIdx = i;
      break;
    }
  }

  for (let i = dataStartIdx; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const parts = line.split(',');
    
    // Verificar que la línea tiene suficientes campos y empieza con un año válido
    if (parts.length < 22) continue;
    const year = parseInt(parts[0]);
    if (isNaN(year) || year < 1900 || year > 2100) continue;
    
    // Estructura EPW (EnergyPlus Weather Format):
    // 0: Year, 1: Month, 2: Day, 3: Hour, 4: Minute, 5: Data Source/Uncertainty
    // 6: Dry Bulb Temperature (°C)
    // 7: Dew Point Temperature (°C)
    // 8: Relative Humidity (%)
    // 9: Atmospheric Station Pressure (Pa)
    // 10: Extraterrestrial Horizontal Radiation (Wh/m²)
    // 11: Extraterrestrial Direct Normal Radiation (Wh/m²)
    // 12: Horizontal Infrared Radiation Intensity from Sky (Wh/m²)
    // 13: Global Horizontal Radiation (Wh/m²)
    // 14: Direct Normal Radiation (Wh/m²)
    // 15: Diffuse Horizontal Radiation (Wh/m²)
    // 21: Wind Speed (m/s)
    // 22: Total Sky Cover (tenths)

    try {
      const data: WeatherData = {
        year: year,
        month: parseInt(parts[1]) || 1,
        day: parseInt(parts[2]) || 1,
        hour: parseInt(parts[3]) || 0,
        minute: parseInt(parts[4]) || 0,
        temperature: parseFloat(parts[6]) || 0,
        dewPoint: parseFloat(parts[7]) || 0,
        relativeHumidity: parseFloat(parts[8]) || 0,
        atmosphericPressure: parseFloat(parts[9]) || 101325,
        globalHorizontalIrradiance: parseFloat(parts[13]) || 0,
        directNormalIrradiance: parseFloat(parts[14]) || 0,
        diffuseHorizontalIrradiance: parseFloat(parts[15]) || 0,
        windSpeed: parseFloat(parts[21]) || 0,
        cloudCover: parseFloat(parts[22]) || 0,
      };

      weatherData.push(data);
    } catch (error) {
      console.warn(`Error parsing EPW line ${i}:`, error);
    }
  }

  return { location, weatherData };
};

/**
 * Obtener datos meteorológicos para una fecha y hora específica
 */
export const getWeatherForDateTime = (
  epwData: EPWData,
  month: number,
  day: number,
  hour: number
): WeatherData | null => {
  return (
    epwData.weatherData.find(
      w => w.month === month && w.day === day && w.hour === hour
    ) || null
  );
};

/**
 * Calcular promedio de temperatura para un mes
 */
export const getMonthlyAverageTemperature = (
  epwData: EPWData,
  month: number
): number => {
  const monthData = epwData.weatherData.filter(w => w.month === month);
  if (monthData.length === 0) return 0;
  const sum = monthData.reduce((acc, w) => acc + w.temperature, 0);
  return sum / monthData.length;
};

/**
 * Calcular irradiancia global promedio para un mes
 */
export const getMonthlyAverageIrradiance = (
  epwData: EPWData,
  month: number
): number => {
  const monthData = epwData.weatherData.filter(w => w.month === month);
  if (monthData.length === 0) return 0;
  const sum = monthData.reduce((acc, w) => acc + w.globalHorizontalIrradiance, 0);
  return sum / monthData.length;
};

/**
 * Obtener datos de irradiancia directa y difusa para cálculo de sombreado
 */
export const getIrradianceComponents = (
  epwData: EPWData,
  month: number,
  day: number,
  hour: number
): { direct: number; diffuse: number; global: number } => {
  const weather = getWeatherForDateTime(epwData, month, day, hour);
  
  if (!weather) {
    return { direct: 0, diffuse: 0, global: 0 };
  }

  return {
    direct: weather.directNormalIrradiance,
    diffuse: weather.diffuseHorizontalIrradiance,
    global: weather.globalHorizontalIrradiance,
  };
};

/**
 * Calcular factor de corrección de sombreado basado en condiciones meteorológicas
 * Considera nubosidad y humedad
 */
export const getWeatherCorrectionFactor = (
  epwData: EPWData,
  month: number,
  day: number,
  hour: number
): number => {
  const weather = getWeatherForDateTime(epwData, month, day, hour);
  
  if (!weather) {
    return 1.0;
  }

  // Factor de nubosidad (0-10 escala EPW)
  const cloudCoverageFactor = 1 - (weather.cloudCover / 10) * 0.3; // Máximo 30% de reducción

  // Factor de humedad (afecta difusión)
  const humidityFactor = 1 - (weather.relativeHumidity / 100) * 0.1; // Máximo 10% de reducción

  return Math.max(0.5, cloudCoverageFactor * humidityFactor);
};

/**
 * Generar resumen mensual de datos meteorológicos
 */
export const getMonthlyWeatherSummary = (
  epwData: EPWData,
  month: number
): {
  avgTemp: number;
  maxTemp: number;
  minTemp: number;
  avgHumidity: number;
  avgIrradiance: number;
  avgWindSpeed: number;
  avgCloudCover: number;
} => {
  const monthData = epwData.weatherData.filter(w => w.month === month);
  
  if (monthData.length === 0) {
    return {
      avgTemp: 0,
      maxTemp: 0,
      minTemp: 0,
      avgHumidity: 0,
      avgIrradiance: 0,
      avgWindSpeed: 0,
      avgCloudCover: 0,
    };
  }

  return {
    avgTemp: monthData.reduce((a, w) => a + w.temperature, 0) / monthData.length,
    maxTemp: Math.max(...monthData.map(w => w.temperature)),
    minTemp: Math.min(...monthData.map(w => w.temperature)),
    avgHumidity: monthData.reduce((a, w) => a + w.relativeHumidity, 0) / monthData.length,
    avgIrradiance: monthData.reduce((a, w) => a + w.globalHorizontalIrradiance, 0) / monthData.length,
    avgWindSpeed: monthData.reduce((a, w) => a + w.windSpeed, 0) / monthData.length,
    avgCloudCover: monthData.reduce((a, w) => a + w.cloudCover, 0) / monthData.length,
  };
};
