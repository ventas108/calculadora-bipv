/**
 * Auto-detección de región climática colombiana por coordenadas geográficas.
 *
 * Colombia se divide en 6 regiones naturales:
 * - Caribe: costa norte, tierras bajas < 200 m, lat > ~8° generalmente
 * - Andina: cordilleras, altiplanos, valles interandinos, elevaciones > 500 m
 * - Pacífica: costa occidental, selva húmeda tropical
 * - Orinoquía: llanos orientales, sabanas
 * - Amazonía: selva amazónica sur-oriental
 * - Insular: San Andrés y Providencia
 *
 * La clasificación usa polígonos simplificados basados en límites geográficos
 * reconocidos por el IDEAM y el IGAC.
 */

import type { RegionalCompatibility } from './panelTechnologies';

export type ColombianRegionKey = keyof Omit<RegionalCompatibility, 'notes'>;

export interface RegionDetectionResult {
  region: ColombianRegionKey;
  label: string;
  confidence: 'alta' | 'media' | 'baja';
  isInColombia: boolean;
  nearestCities: string;
}

/** Punto geográfico [lat, lon] */
type Point = [number, number];

/** Polígono simplificado como lista de puntos */
type Polygon = Point[];

/**
 * Algoritmo ray-casting para determinar si un punto está dentro de un polígono.
 */
function pointInPolygon(point: Point, polygon: Polygon): boolean {
  const [y, x] = point; // lat, lon
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [yi, xi] = polygon[i];
    const [yj, xj] = polygon[j];
    if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
      inside = !inside;
    }
  }
  return inside;
}

/**
 * Polígonos simplificados de las regiones colombianas.
 * Basados en límites geográficos del IGAC.
 * Formato: [latitud, longitud]
 */
const REGION_POLYGONS: { key: ColombianRegionKey; label: string; cities: string; polygon: Polygon }[] = [
  {
    key: 'insular',
    label: 'Insular',
    cities: 'San Andrés, Providencia',
    polygon: [
      [14.0, -82.0], [14.0, -81.0], [12.0, -81.0], [12.0, -82.0],
    ],
  },
  {
    key: 'caribe',
    label: 'Caribe',
    cities: 'Barranquilla, Cartagena, Santa Marta, Valledupar, Montería, Sincelejo, Riohacha',
    polygon: [
      // Costa norte de Colombia - tierras bajas
      [12.6, -77.0], [12.6, -71.0], [11.0, -71.8], [10.0, -72.8],
      [9.5, -73.5], [8.5, -73.5], [8.0, -74.0], [7.5, -74.8],
      [7.8, -75.5], [8.0, -76.0], [8.5, -76.5], [8.8, -76.8],
      [9.5, -76.5], [9.3, -76.0], [9.5, -75.5], [10.5, -75.5],
      [11.0, -75.0], [12.0, -75.5], [12.5, -77.0],
    ],
  },
  {
    key: 'pacifica',
    label: 'Pacífica',
    cities: 'Quibdó, Buenaventura, Tumaco',
    polygon: [
      // Costa pacífica occidental
      [8.8, -76.8], [8.5, -76.5], [8.0, -76.0], [7.8, -76.5],
      [7.5, -77.0], [7.0, -77.5], [6.5, -77.5], [6.0, -77.5],
      [5.5, -77.5], [5.0, -77.5], [4.5, -77.5], [4.0, -77.8],
      [3.5, -78.0], [3.0, -78.2], [2.5, -78.5], [2.0, -78.8],
      [1.5, -79.0], [1.4, -78.5], [1.5, -78.0], [2.0, -77.5],
      [2.5, -77.0], [3.0, -76.8], [3.5, -76.5], [4.0, -76.5],
      [4.5, -76.5], [5.0, -76.5], [5.5, -76.5], [6.0, -76.3],
      [6.5, -76.5], [7.0, -76.5], [7.5, -76.5], [8.0, -76.5],
      [8.5, -76.8],
    ],
  },
  {
    key: 'amazonia',
    label: 'Amazonía',
    cities: 'Leticia, Florencia, Mocoa, Puerto Asís',
    polygon: [
      // Selva amazónica sur-oriental
      [2.5, -76.0], [2.0, -76.0], [1.5, -76.5], [1.0, -76.5],
      [0.5, -76.0], [0.0, -75.5], [-0.5, -75.0], [-1.0, -74.5],
      [-1.5, -73.5], [-2.0, -72.5], [-2.5, -71.5], [-3.0, -70.5],
      [-4.2, -70.0], [-4.2, -69.5], [-2.0, -69.5], [-1.0, -70.0],
      [0.0, -70.0], [1.0, -70.0], [2.0, -70.0], [2.5, -70.5],
      [3.0, -71.0], [3.5, -71.5], [3.5, -72.0], [3.0, -73.0],
      [2.5, -74.0], [2.0, -74.5], [2.0, -75.0], [2.5, -75.5],
    ],
  },
  {
    key: 'orinoquia',
    label: 'Orinoquía',
    cities: 'Villavicencio, Yopal, Arauca',
    polygon: [
      // Llanos orientales
      [7.5, -72.5], [7.0, -71.0], [6.5, -67.5], [6.0, -67.5],
      [5.0, -68.0], [4.0, -68.0], [3.5, -69.0], [3.0, -70.0],
      [2.5, -70.5], [2.0, -70.0], [2.5, -71.5], [3.0, -72.0],
      [3.5, -72.5], [4.0, -73.0], [4.5, -73.5], [5.0, -73.5],
      [5.5, -73.0], [6.0, -72.5], [6.5, -72.5], [7.0, -72.5],
    ],
  },
  {
    key: 'andina',
    label: 'Andina',
    cities: 'Bogotá, Medellín, Cali, Bucaramanga, Pereira, Manizales, Tunja, Ibagué',
    polygon: [
      // Cordilleras y valles interandinos (polígono central)
      [8.0, -76.0], [7.8, -75.5], [7.5, -74.8], [7.5, -73.5],
      [7.5, -72.5], [7.0, -72.5], [6.5, -72.5], [6.0, -72.5],
      [5.5, -73.0], [5.0, -73.5], [4.5, -73.5], [4.0, -73.0],
      [3.5, -72.5], [3.0, -73.0], [2.5, -74.0], [2.0, -75.0],
      [2.0, -76.0], [2.5, -76.0], [3.0, -76.5], [3.5, -76.5],
      [4.0, -76.5], [4.5, -76.5], [5.0, -76.5], [5.5, -76.5],
      [6.0, -76.3], [6.5, -76.5], [7.0, -76.5], [7.5, -76.5],
    ],
  },
];

/**
 * Detecta la región climática colombiana basada en coordenadas geográficas.
 * Primero verifica si las coordenadas están dentro de Colombia,
 * luego usa polígonos para clasificar la región.
 * Si no se encuentra en ningún polígono, usa la distancia al centroide más cercano.
 */
export function detectColombianRegion(latitude: number, longitude: number): RegionDetectionResult {
  // Verificar si está dentro del bounding box de Colombia (aprox)
  const isInColombiaBBox = latitude >= -4.3 && latitude <= 13.5 && longitude >= -82.0 && longitude <= -66.8;

  if (!isInColombiaBBox) {
    // Fuera de Colombia - intentar asignar la región más cercana por distancia
    return findNearestRegion(latitude, longitude, false);
  }

  // Verificar cada polígono de región
  for (const regionDef of REGION_POLYGONS) {
    if (pointInPolygon([latitude, longitude], regionDef.polygon)) {
      return {
        region: regionDef.key,
        label: regionDef.label,
        confidence: 'alta',
        isInColombia: true,
        nearestCities: regionDef.cities,
      };
    }
  }

  // Si no cayó en ningún polígono (zonas fronterizas), buscar la más cercana
  return findNearestRegion(latitude, longitude, true);
}

/** Centroides aproximados de cada región para fallback por distancia */
const REGION_CENTROIDS: { key: ColombianRegionKey; label: string; cities: string; lat: number; lon: number }[] = [
  { key: 'caribe', label: 'Caribe', cities: 'Barranquilla, Cartagena, Santa Marta', lat: 10.4, lon: -75.5 },
  { key: 'andina', label: 'Andina', cities: 'Bogotá, Medellín, Cali, Bucaramanga', lat: 5.5, lon: -74.5 },
  { key: 'pacifica', label: 'Pacífica', cities: 'Quibdó, Buenaventura, Tumaco', lat: 4.5, lon: -77.0 },
  { key: 'orinoquia', label: 'Orinoquía', cities: 'Villavicencio, Yopal, Arauca', lat: 5.0, lon: -71.0 },
  { key: 'amazonia', label: 'Amazonía', cities: 'Leticia, Florencia, Mocoa', lat: 0.5, lon: -73.0 },
  { key: 'insular', label: 'Insular', cities: 'San Andrés, Providencia', lat: 12.5, lon: -81.7 },
];

function findNearestRegion(lat: number, lon: number, isInColombia: boolean): RegionDetectionResult {
  let minDist = Infinity;
  let nearest = REGION_CENTROIDS[1]; // default: Andina

  for (const centroid of REGION_CENTROIDS) {
    const dist = Math.sqrt(Math.pow(lat - centroid.lat, 2) + Math.pow(lon - centroid.lon, 2));
    if (dist < minDist) {
      minDist = dist;
      nearest = centroid;
    }
  }

  return {
    region: nearest.key,
    label: nearest.label,
    confidence: isInColombia ? 'media' : 'baja',
    isInColombia,
    nearestCities: nearest.cities,
  };
}

/** Todas las regiones disponibles para selector manual */
export const COLOMBIAN_REGION_OPTIONS: { key: ColombianRegionKey; label: string; cities: string }[] = [
  { key: 'caribe', label: 'Caribe', cities: 'Barranquilla, Cartagena, Santa Marta, Valledupar, Montería, Sincelejo, Riohacha' },
  { key: 'andina', label: 'Andina', cities: 'Bogotá, Medellín, Cali, Bucaramanga, Pereira, Manizales, Tunja, Ibagué' },
  { key: 'pacifica', label: 'Pacífica', cities: 'Quibdó, Buenaventura, Tumaco' },
  { key: 'orinoquia', label: 'Orinoquía', cities: 'Villavicencio, Yopal, Arauca' },
  { key: 'amazonia', label: 'Amazonía', cities: 'Leticia, Florencia, Mocoa, Puerto Asís' },
  { key: 'insular', label: 'Insular', cities: 'San Andrés, Providencia' },
];
