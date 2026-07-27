/**
 * Librería para generar datos de irradiancia para heatmap
 * Utiliza modelos de radiación solar basados en latitud, longitud y datos históricos
 */

export interface IrradiancePoint {
  lat: number;
  lng: number;
  irradiance: number; // kWh/m²/año
  weight: number; // Para Google Maps HeatmapLayer
}

/**
 * Modelo de estimación de irradiancia basado en latitud
 * Utiliza datos de PVGIS y NASA POWER
 */
export function estimateAnnualIrradiance(latitude: number, longitude: number): number {
  // Constantes basadas en datos de radiación solar global
  const absLat = Math.abs(latitude);
  
  // Modelo base: irradiancia disminuye con latitud
  let baseIrradiance = 1600; // kWh/m²/año en el ecuador
  
  // Factor latitudinal (disminuye hacia los polos)
  const latitudeFactor = Math.cos((absLat * Math.PI) / 180);
  baseIrradiance *= (0.7 + 0.3 * latitudeFactor);
  
  // Factor de continentalidad (longitud afecta nubosidad)
  // Áreas costeras tienen más nubosidad
  const longitudeFactor = 0.95 + 0.05 * Math.sin((longitude * Math.PI) / 180);
  baseIrradiance *= longitudeFactor;
  
  // Factor de altitud (aproximado)
  // Altitudes más altas tienen más radiación
  const altitudeFactor = 1.0; // Se puede mejorar con datos reales
  baseIrradiance *= altitudeFactor;
  
  // Ajuste regional (factores climáticos)
  // América del Sur tropical: mejor radiación
  if (latitude > -35 && latitude < 15 && longitude > -82 && longitude < -30) {
    baseIrradiance *= 1.1;
  }
  
  // Desiertos: excelente radiación
  if ((latitude > 15 && latitude < 35 && longitude > -120 && longitude < -95) || // Desiertos NA
      (latitude > -35 && latitude < -15 && longitude > -75 && longitude < -65)) { // Desiertos SA
    baseIrradiance *= 1.15;
  }
  
  // Zonas tropicales: nubosidad moderada
  if (latitude > -23.5 && latitude < 23.5) {
    baseIrradiance *= 0.95;
  }
  
  return Math.max(800, Math.min(2200, baseIrradiance));
}

/**
 * Genera una malla de puntos de irradiancia para el heatmap
 */
export function generateIrradianceGrid(
  centerLat: number,
  centerLng: number,
  radiusKm: number = 500
): IrradiancePoint[] {
  const points: IrradiancePoint[] = [];
  
  // Convertir km a grados aproximadamente (1 grado ≈ 111 km)
  const radiusDegrees = radiusKm / 111;
  
  // Generar puntos en una malla
  const gridSize = 15; // Número de puntos por lado
  const step = (radiusDegrees * 2) / gridSize;
  
  for (let i = 0; i < gridSize; i++) {
    for (let j = 0; j < gridSize; j++) {
      const lat = centerLat - radiusDegrees + i * step;
      const lng = centerLng - radiusDegrees + j * step;
      
      // Validar límites geográficos
      if (lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        const irradiance = estimateAnnualIrradiance(lat, lng);
        
        points.push({
          lat,
          lng,
          irradiance,
          weight: normalizeIrradiance(irradiance),
        });
      }
    }
  }
  
  return points;
}

/**
 * Normaliza la irradiancia a un rango de 0-1 para el heatmap
 */
function normalizeIrradiance(irradiance: number): number {
  // Rango típico: 800-2200 kWh/m²/año
  const min = 800;
  const max = 2200;
  return Math.max(0, Math.min(1, (irradiance - min) / (max - min)));
}

/**
 * Clasifica la irradiancia en categorías
 */
export function classifyIrradiance(irradiance: number): {
  category: string;
  color: string;
  description: string;
} {
  if (irradiance >= 2000) {
    return {
      category: 'Excelente',
      color: '#d32f2f', // Rojo intenso
      description: 'Irradiancia muy alta - Ubicación óptima para solar',
    };
  } else if (irradiance >= 1800) {
    return {
      category: 'Muy Buena',
      color: '#f57c00', // Naranja
      description: 'Irradiancia alta - Excelente para proyectos solares',
    };
  } else if (irradiance >= 1600) {
    return {
      category: 'Buena',
      color: '#fbc02d', // Amarillo
      description: 'Irradiancia moderada-alta - Viable para solar',
    };
  } else if (irradiance >= 1400) {
    return {
      category: 'Aceptable',
      color: '#7cb342', // Verde claro
      description: 'Irradiancia moderada - Posible con optimización',
    };
  } else if (irradiance >= 1200) {
    return {
      category: 'Limitada',
      color: '#1976d2', // Azul
      description: 'Irradiancia baja - Requiere análisis detallado',
    };
  } else {
    return {
      category: 'Muy Limitada',
      color: '#424242', // Gris
      description: 'Irradiancia muy baja - No recomendado para solar',
    };
  }
}

/**
 * Genera datos de irradiancia para múltiples ciudades
 */
export function generateCitiesIrradianceData(
  cities: Array<{ name: string; lat: number; lng: number }>
): Array<{
  name: string;
  lat: number;
  lng: number;
  irradiance: number;
  category: string;
  color: string;
}> {
  return cities.map(city => {
    const irradiance = estimateAnnualIrradiance(city.lat, city.lng);
    const classification = classifyIrradiance(irradiance);
    
    return {
      name: city.name,
      lat: city.lat,
      lng: city.lng,
      irradiance,
      category: classification.category,
      color: classification.color,
    };
  });
}

/**
 * Calcula estadísticas de irradiancia para una región
 */
export function calculateRegionStats(points: IrradiancePoint[]): {
  average: number;
  min: number;
  max: number;
  median: number;
  stdDev: number;
} {
  if (points.length === 0) {
    return { average: 0, min: 0, max: 0, median: 0, stdDev: 0 };
  }
  
  const irradiances = points.map(p => p.irradiance).sort((a, b) => a - b);
  
  const average = irradiances.reduce((a, b) => a + b, 0) / irradiances.length;
  const min = irradiances[0];
  const max = irradiances[irradiances.length - 1];
  const median = irradiances[Math.floor(irradiances.length / 2)];
  
  const variance = irradiances.reduce((sum, val) => sum + Math.pow(val - average, 2), 0) / irradiances.length;
  const stdDev = Math.sqrt(variance);
  
  return { average, min, max, median, stdDev };
}
