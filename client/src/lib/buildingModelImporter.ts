/**
 * Building Model Importer
 * 
 * Importa un modelo 3D del edificio a evaluar (desde SketchUp, Blender, Sun Path 3D)
 * y recalcula los obstáculos de sombra existentes desde la perspectiva del modelo.
 * 
 * Conceptos clave:
 * - "Modelo a evaluar" = el edificio propio (sus fachadas reciben sol)
 * - "Obstáculos de sombra" = el entorno (edificios vecinos, árboles, montañas)
 * 
 * Flujo:
 * 1. Importar modelo 3D del edificio (OBJ)
 * 2. Detectar fachadas principales del modelo (superficies verticales con normales exteriores)
 * 3. Para cada punto de evaluación en las fachadas:
 *    a. Recalcular la proyección angular de los obstáculos del entorno
 *    b. Generar FacadeDefinition compatible con el cruce Máscara+EPW
 * 4. Actualizar automáticamente la tabla de Puntos de Análisis
 */

import { ObstaclePolygon } from '@/components/SunPathDiagram';
import { FacadeDefinition } from './shadingMaskCrossing';
import {
  OBJParseResult,
  OBJObstacleResult,
  parseOBJText,
  validateOBJText,
  convertOBJToObstacles,
} from './objParser';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface Vertex3D {
  x: number;
  y: number;
  z: number;
}

export interface DetectedFacade {
  /** Nombre descriptivo de la fachada */
  name: string;
  /** Azimut de la normal exterior (convención solar: 0=Sur, neg=Este, pos=Oeste) */
  azimuthNormal: number;
  /** Inclinación de la superficie (90° = vertical) */
  tilt: number;
  /** Punto central de la fachada en coordenadas 3D */
  center: Vertex3D;
  /** Área aproximada de la fachada en m² */
  area: number;
  /** Punto de evaluación (a 1.5m del centro de la fachada hacia el exterior) */
  evaluationPoint: Vertex3D;
  /** Color para visualización */
  color: string;
  /** Número de caras que componen esta fachada */
  faceCount: number;
  /** Indica si la superficie es curva (bóveda, arco, casquete) */
  isCurved?: boolean;
  /** Rango de azimuts que abarca la superficie curva [min, max] */
  azimuthRange?: [number, number];
  /** Rango de tilts que abarca la superficie curva [min, max] */
  tiltRange?: [number, number];
}

export interface EvaluationModel {
  /** Nombre del archivo importado */
  fileName: string;
  /** Resultado del parsing OBJ */
  parseResult: OBJParseResult;
  /** Vértices transformados (con remapeo de ejes + rotación + escala aplicados) */
  transformedVertices: Vertex3D[];
  /** Fachadas detectadas automáticamente */
  detectedFacades: DetectedFacade[];
  /** Centroide del modelo */
  centroid: Vertex3D;
  /** Dimensiones del modelo en metros */
  dimensions: Vertex3D;
  /** Punto de observación principal (centroide a nivel de suelo + 1.5m) */
  mainObservationPoint: Vertex3D;
  /** Obstáculos recalculados desde la perspectiva del modelo */
  recalculatedObstacles: ObstaclePolygon[];
  /** Fachadas en formato compatible con CrossingConfig */
  facadeDefinitions: FacadeDefinition[];
  /** Configuración aplicada */
  config: ImportConfig;
}

/** Eje que se interpreta como "arriba" (vertical/altura) */
export type UpAxis = 'Z' | 'Y' | 'X' | 'auto';

export interface ImportConfig {
  /** Factor de escala (ej: 0.001 para mm→m) */
  scaleFactor: number;
  /** Intercambiar ejes Y/Z (común en SketchUp) — legacy, reemplazado por upAxis */
  swapYZ: boolean;
  /** Eje que se interpreta como vertical (auto = auto-detectar) */
  upAxis: UpAxis;
  /** Rotación adicional alrededor del eje vertical en grados (0, 90, 180, 270) */
  rotationDeg: number;
  /** Rotación del norte respecto al eje Y (grados, sentido horario) */
  northOffset: number;
  /** Altura del punto de evaluación sobre el suelo (metros) */
  evaluationHeight: number;
  /** Distancia del punto de evaluación desde la fachada (metros) */
  evaluationOffset: number;
}

export const DEFAULT_IMPORT_CONFIG: ImportConfig = {
  scaleFactor: 1.0,
  swapYZ: false,
  upAxis: 'auto',
  rotationDeg: 0,
  northOffset: 0,
  evaluationHeight: 1.5,
  evaluationOffset: 0.5,
};

/**
 * Remapea un vértice para que el eje indicado sea Z (vertical).
 * Después de esta transformación, Z = arriba, Y = norte, X = este.
 */
function remapAxes(v: Vertex3D, upAxis: 'X' | 'Y' | 'Z'): Vertex3D {
  switch (upAxis) {
    case 'Z': return v; // Ya correcto
    case 'Y': return { x: v.x, y: -v.z, z: v.y }; // Y-up → Z-up
    case 'X': return { x: v.y, y: v.z, z: v.x }; // X-up → Z-up
  }
}

/**
 * Aplica rotación horizontal (alrededor del eje Z/vertical) en grados.
 */
function rotateAroundVertical(v: Vertex3D, degrees: number): Vertex3D {
  if (degrees === 0) return v;
  const rad = (degrees * Math.PI) / 180;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);
  return {
    x: v.x * cos - v.y * sin,
    y: v.x * sin + v.y * cos,
    z: v.z,
  };
}

/**
 * Auto-detecta cuál eje es "arriba" analizando la geometría del modelo.
 * Heurísticas:
 * 1. Prueba las 3 orientaciones (X-up, Y-up, Z-up)
 * 2. Para cada una, cuenta cuántas caras son "techo" (normal apuntando arriba)
 *    y cuántas son "fachada vertical" (normal horizontal)
 * 3. Elige la orientación que produce la distribución más realista de un edificio:
 *    - Debe tener al menos 1 techo (cara horizontal arriba)
 *    - Debe tener fachadas verticales
 *    - El eje vertical debe ser el de menor extensión relativa (edificios son más anchos que altos)
 */
export function autoDetectUpAxis(vertices: Vertex3D[], faces: { vertexIndices: number[] }[]): {
  bestAxis: 'X' | 'Y' | 'Z';
  confidence: 'high' | 'medium' | 'low';
  scores: Record<string, { roofFaces: number; verticalFaces: number; heightRatio: number; score: number }>;
} {
  const axes: Array<'X' | 'Y' | 'Z'> = ['X', 'Y', 'Z'];
  const scores: Record<string, { roofFaces: number; verticalFaces: number; heightRatio: number; score: number }> = {};

  for (const axis of axes) {
    // Remapear vértices
    const remapped = vertices.map(v => remapAxes(v, axis));

    // Calcular bounding box
    let minX = Infinity, minY = Infinity, minZ = Infinity;
    let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
    for (const v of remapped) {
      if (v.x < minX) minX = v.x;
      if (v.y < minY) minY = v.y;
      if (v.z < minZ) minZ = v.z;
      if (v.x > maxX) maxX = v.x;
      if (v.y > maxY) maxY = v.y;
      if (v.z > maxZ) maxZ = v.z;
    }
    const dx = maxX - minX || 0.001;
    const dy = maxY - minY || 0.001;
    const dz = maxZ - minZ || 0.001;

    // Ratio: altura vs promedio horizontal (edificios: altura < ancho)
    const horizontalAvg = (dx + dy) / 2;
    const heightRatio = dz / horizontalAvg; // < 1 para edificios típicos

    // Contar caras tipo techo y fachada (incluyendo techos inclinados)
    let roofFaces = 0;
    let verticalFaces = 0;
    for (const face of faces) {
      if (face.vertexIndices.length < 3) continue;
      const fv = face.vertexIndices.map(i => remapped[i]);
      if (!fv[0] || !fv[1] || !fv[2]) continue;
      const normal = calculateFaceNormal(fv);
      if (isRoofFace(normal) || isSlopedRoofFace(normal)) roofFaces++;
      if (isVerticalFace(normal)) verticalFaces++;
    }

    // Score: priorizar orientaciones con techos + fachadas + ratio realista
    let score = 0;
    score += roofFaces * 3; // Techos son la señal más fuerte
    score += verticalFaces * 1;
    // Penalizar solo ratios extremos (la heurística de ratio no es confiable para cubos simétricos)
    if (heightRatio > 2) score *= 0.3;
    else if (heightRatio > 1.5) score *= 0.6;
    else if (heightRatio < 0.1) {
      // Bóvedas/arcos de techo son muy planos (height << width) pero tienen muchos roof faces.
      // Si hay muchas caras de techo (>8), es probable que sea un techo curvo válido,
      // así que reducimos la penalización.
      if (roofFaces > 8) score *= 0.85; // Penalización leve para techos curvos planos
      else score *= 0.5; // Penalización normal para modelos realmente planos
    }
    // Bonus si hay tanto techos como fachadas
    if (roofFaces > 0 && verticalFaces > 0) score *= 1.5;

    scores[axis] = { roofFaces, verticalFaces, heightRatio, score };
  }

  // Elegir el mejor (en caso de empate, preferir Z > Y > X como convención más común)
  const axisPriority: Record<string, number> = { 'Z': 3, 'Y': 2, 'X': 1 };
  const sorted = [...axes].sort((a, b) => {
    const diff = scores[b].score - scores[a].score;
    if (Math.abs(diff) < 0.001) return axisPriority[b] - axisPriority[a]; // Tie-break: Z > Y > X
    return diff;
  });
  const best = sorted[0];
  const second = sorted[1];

  // Confianza
  let confidence: 'high' | 'medium' | 'low' = 'low';
  const bestScore = scores[best].score;
  const secondScore = scores[second].score;
  if (bestScore > 0 && bestScore > secondScore * 2) confidence = 'high';
  else if (bestScore > 0 && bestScore > secondScore * 1.3) confidence = 'medium';

  return { bestAxis: best, confidence, scores };
}

// ─── Face Normal Calculation ─────────────────────────────────────────────────

interface Face3D {
  vertices: Vertex3D[];
  normal: Vertex3D;
  center: Vertex3D;
  area: number;
}

/**
 * Calcula la normal de una cara poligonal usando el producto cruzado.
 */
function calculateFaceNormal(vertices: Vertex3D[]): Vertex3D {
  if (vertices.length < 3) return { x: 0, y: 0, z: 1 };

  // Usar los primeros 3 vértices para calcular la normal
  const v0 = vertices[0];
  const v1 = vertices[1];
  const v2 = vertices[2];

  // Vectores de arista
  const e1 = { x: v1.x - v0.x, y: v1.y - v0.y, z: v1.z - v0.z };
  const e2 = { x: v2.x - v0.x, y: v2.y - v0.y, z: v2.z - v0.z };

  // Producto cruzado
  const normal = {
    x: e1.y * e2.z - e1.z * e2.y,
    y: e1.z * e2.x - e1.x * e2.z,
    z: e1.x * e2.y - e1.y * e2.x,
  };

  // Normalizar
  const length = Math.sqrt(normal.x ** 2 + normal.y ** 2 + normal.z ** 2);
  if (length < 1e-10) return { x: 0, y: 0, z: 1 };

  return {
    x: normal.x / length,
    y: normal.y / length,
    z: normal.z / length,
  };
}

/**
 * Calcula el área de un polígono 3D usando la fórmula de Newell.
 */
function calculateFaceArea(vertices: Vertex3D[]): number {
  if (vertices.length < 3) return 0;

  let nx = 0, ny = 0, nz = 0;
  for (let i = 0; i < vertices.length; i++) {
    const j = (i + 1) % vertices.length;
    nx += (vertices[i].y - vertices[j].y) * (vertices[i].z + vertices[j].z);
    ny += (vertices[i].z - vertices[j].z) * (vertices[i].x + vertices[j].x);
    nz += (vertices[i].x - vertices[j].x) * (vertices[i].y + vertices[j].y);
  }

  return 0.5 * Math.sqrt(nx * nx + ny * ny + nz * nz);
}

/**
 * Calcula el centroide de un polígono 3D.
 */
function calculateFaceCenter(vertices: Vertex3D[]): Vertex3D {
  const n = vertices.length;
  if (n === 0) return { x: 0, y: 0, z: 0 };
  return {
    x: vertices.reduce((s, v) => s + v.x, 0) / n,
    y: vertices.reduce((s, v) => s + v.y, 0) / n,
    z: vertices.reduce((s, v) => s + v.z, 0) / n,
  };
}

// ─── Facade Detection ────────────────────────────────────────────────────────

const FACADE_COLORS = [
  '#dc2626', // red (Sur)
  '#2563eb', // blue (Norte)
  '#16a34a', // green (Este)
  '#d97706', // amber (Oeste)
  '#7c3aed', // violet
  '#0891b2', // cyan
  '#e11d48', // rose
  '#65a30d', // lime
];

/**
 * Convierte la normal de una cara (en coordenadas 3D) a azimut solar.
 * Asume que Y apunta al Norte (con northOffset aplicado).
 * 
 * Convención solar: 0° = Sur, negativo = Este, positivo = Oeste
 */
function normalToSolarAzimuth(normal: Vertex3D, northOffsetDeg: number = 0): number {
  // Bearing geográfico: atan2(x, y) da ángulo desde Y (Norte)
  let bearing = Math.atan2(normal.x, normal.y) * 180 / Math.PI;
  bearing += northOffsetDeg;

  // Convertir de bearing geográfico (0=N, CW) a azimut solar (0=S, neg=E, pos=W)
  let solarAzimuth = bearing - 180;
  if (solarAzimuth > 180) solarAzimuth -= 360;
  if (solarAzimuth < -180) solarAzimuth += 360;

  return solarAzimuth;
}

/**
 * Determina si una cara es "vertical" (fachada de muro).
 * Inclinación > 75° respecto a la horizontal (normal casi horizontal).
 */
function isVerticalFace(normal: Vertex3D): boolean {
  // tilt = ángulo entre la normal y el vector vertical (0,0,1)
  // Para una fachada vertical pura: normal horizontal → tilt = 90°
  const tilt = Math.acos(Math.abs(normal.z)) * 180 / Math.PI;
  return tilt > 75; // Más de 75° de inclinación = muro/fachada vertical
}

/**
 * Determina si una cara es "techo horizontal" (cubierta plana).
 * La normal apunta hacia arriba (+Z) con inclinación < 15° respecto a la horizontal.
 */
function isRoofFace(normal: Vertex3D): boolean {
  if (normal.z <= 0) return false; // Normal debe apuntar hacia arriba
  const tilt = Math.acos(Math.abs(normal.z)) * 180 / Math.PI;
  return tilt < 15; // Menos de 15° de inclinación = techo plano
}

/**
 * Determina si una cara es un "techo inclinado" (agua de techo).
 * La normal apunta hacia arriba (+Z) con inclinación entre 15° y 75°.
 * Esto captura las aguas de techos de 2, 3 y 4 aguas.
 */
function isSlopedRoofFace(normal: Vertex3D): boolean {
  if (normal.z <= 0) return false; // Normal debe apuntar hacia arriba
  const tilt = Math.acos(Math.abs(normal.z)) * 180 / Math.PI;
  return tilt >= 15 && tilt <= 75; // Entre 15° y 75° = techo inclinado (agua)
}

/**
 * Calcula la inclinación de la superficie desde la normal.
 * 0° = horizontal (techo), 90° = vertical (fachada)
 */
function normalToTilt(normal: Vertex3D): number {
  // El ángulo entre la normal y el vector vertical (0,0,1)
  // Para una fachada vertical, la normal es horizontal → ángulo con Z = 90°
  // tilt = ángulo entre la normal y el plano horizontal
  const horizontalComponent = Math.sqrt(normal.x ** 2 + normal.y ** 2);
  const tilt = Math.atan2(horizontalComponent, Math.abs(normal.z)) * 180 / Math.PI;
  return tilt;
}

/**
 * Agrupa caras con normales similares en fachadas.
 * Usa clustering por ángulo de azimut (±15°) y similar tilt (±10°).
 */
interface FacadeCluster {
  faces: Face3D[];
  avgAzimuth: number;
  avgTilt: number;
  totalArea: number;
  center: Vertex3D;
  /** Indica si el cluster es una superficie curva detectada por conectividad */
  isCurved?: boolean;
  /** Rango de azimuts [min, max] para superficies curvas */
  azimuthRange?: [number, number];
  /** Rango de tilts [min, max] para superficies curvas */
  tiltRange?: [number, number];
}

/**
 * Detecta superficies curvas continuas usando conectividad de malla (flood-fill).
 * 
 * Algoritmo:
 * 1. Construir grafo de adyacencia: dos caras son vecinas si comparten al menos una arista
 * 2. Flood-fill: agrupar caras conectadas donde vecinas adyacentes tienen normales
 *    que difieren < MAX_NEIGHBOR_ANGLE (variación gradual = curvatura)
 * 3. Si un grupo conectado tiene un rango de azimuts > CURVED_AZIMUTH_RANGE,
 *    se clasifica como superficie curva (bóveda/arco)
 * 
 * @returns Array de clusters curvos detectados (ya extraídos de la lista de caras)
 */
function detectCurvedSurfaces(
  faces: Face3D[],
  northOffsetDeg: number
): { curvedClusters: FacadeCluster[]; remainingFaces: Face3D[] } {
  if (faces.length < 3) return { curvedClusters: [], remainingFaces: faces };

  // Umbral: ángulo máximo entre normales de caras VECINAS para considerar curvatura gradual
  const MAX_NEIGHBOR_ANGLE = 45; // grados
  // Umbral: rango mínimo de azimuts para clasificar como superficie curva
  const CURVED_AZIMUTH_RANGE = 50; // grados (un arco típico abarca >60°)
  // Umbral mínimo de caras para considerar un grupo como superficie curva
  const MIN_CURVED_FACES = 3;

  // 1. Construir mapa de aristas → caras (para encontrar vecinos)
  // Una arista se define por dos vértices. Usamos coordenadas redondeadas como clave
  // ya que los índices de vértice no están disponibles en Face3D.
  const COORD_PRECISION = 4; // decimales para redondeo
  function vertexKey(v: Vertex3D): string {
    return `${v.x.toFixed(COORD_PRECISION)},${v.y.toFixed(COORD_PRECISION)},${v.z.toFixed(COORD_PRECISION)}`;
  }
  function edgeKey(v1: Vertex3D, v2: Vertex3D): string {
    const k1 = vertexKey(v1);
    const k2 = vertexKey(v2);
    return k1 < k2 ? `${k1}|${k2}` : `${k2}|${k1}`;
  }

  const edgeToFaces = new Map<string, number[]>();
  for (let i = 0; i < faces.length; i++) {
    const verts = faces[i].vertices;
    for (let j = 0; j < verts.length; j++) {
      const v1 = verts[j];
      const v2 = verts[(j + 1) % verts.length];
      const ek = edgeKey(v1, v2);
      if (!edgeToFaces.has(ek)) edgeToFaces.set(ek, []);
      edgeToFaces.get(ek)!.push(i);
    }
  }

  // 2. Construir grafo de adyacencia
  const adjacency: Set<number>[] = faces.map(() => new Set<number>());
  edgeToFaces.forEach((faceIndices) => {
    if (faceIndices.length >= 2) {
      for (let a = 0; a < faceIndices.length; a++) {
        for (let b = a + 1; b < faceIndices.length; b++) {
          adjacency[faceIndices[a]].add(faceIndices[b]);
          adjacency[faceIndices[b]].add(faceIndices[a]);
        }
      }
    }
  });

  // 3. Flood-fill: agrupar caras conectadas con variación gradual de normales
  const visited = new Set<number>();
  const connectedGroups: number[][] = [];

  for (let startIdx = 0; startIdx < faces.length; startIdx++) {
    if (visited.has(startIdx)) continue;
    
    const group: number[] = [];
    const queue: number[] = [startIdx];
    visited.add(startIdx);

    while (queue.length > 0) {
      const current = queue.shift()!;
      group.push(current);

      const neighbors = Array.from(adjacency[current]);
      for (let ni = 0; ni < neighbors.length; ni++) {
        const neighbor = neighbors[ni];
        if (visited.has(neighbor)) continue;

        // Verificar que la variación de normal entre vecinas es gradual
        const n1 = faces[current].normal;
        const n2 = faces[neighbor].normal;
        const dot = n1.x * n2.x + n1.y * n2.y + n1.z * n2.z;
        const clampedDot = Math.max(-1, Math.min(1, dot));
        const angleDeg = Math.acos(clampedDot) * 180 / Math.PI;

        if (angleDeg < MAX_NEIGHBOR_ANGLE) {
          visited.add(neighbor);
          queue.push(neighbor);
        }
      }
    }

    connectedGroups.push(group);
  }

  // 4. Evaluar cada grupo: si tiene rango de azimuts amplio → superficie curva
  const curvedClusters: FacadeCluster[] = [];
  const curvedFaceIndices = new Set<number>();

  for (const group of connectedGroups) {
    if (group.length < MIN_CURVED_FACES) continue;

    // Calcular rango de azimuts del grupo
    const azimuts = group.map(i => normalToSolarAzimuth(faces[i].normal, northOffsetDeg));
    
    // Para manejar el wrap-around de azimuts (ej: -170° y +170° están cerca),
    // calculamos el rango circular
    const sortedAz = [...azimuts].sort((a, b) => a - b);
    let maxGap = 0;
    for (let i = 1; i < sortedAz.length; i++) {
      maxGap = Math.max(maxGap, sortedAz[i] - sortedAz[i - 1]);
    }
    // Gap circular (entre el último y el primero + 360)
    const circularGap = (sortedAz[0] + 360) - sortedAz[sortedAz.length - 1];
    maxGap = Math.max(maxGap, circularGap);
    const azimuthRange = 360 - maxGap; // El rango real es 360° - el gap más grande

    if (azimuthRange >= CURVED_AZIMUTH_RANGE) {
      // ¡Es una superficie curva!
      const groupFaces = group.map(i => faces[i]);
      const totalArea = groupFaces.reduce((s, f) => s + f.area, 0);
      
      // Calcular azimut y tilt promedio ponderado por área
      // Para el azimut, usar promedio circular para evitar problemas con wrap-around
      let sinSum = 0, cosSum = 0;
      let tiltSum = 0;
      for (const idx of group) {
        const az = normalToSolarAzimuth(faces[idx].normal, northOffsetDeg);
        const tilt = normalToTilt(faces[idx].normal);
        const weight = faces[idx].area;
        sinSum += Math.sin(az * Math.PI / 180) * weight;
        cosSum += Math.cos(az * Math.PI / 180) * weight;
        tiltSum += tilt * weight;
      }
      const avgAzimuth = Math.atan2(sinSum, cosSum) * 180 / Math.PI;
      const avgTilt = tiltSum / totalArea;

      // Centro ponderado por área
      const center: Vertex3D = {
        x: groupFaces.reduce((s, f) => s + f.center.x * f.area, 0) / totalArea,
        y: groupFaces.reduce((s, f) => s + f.center.y * f.area, 0) / totalArea,
        z: groupFaces.reduce((s, f) => s + f.center.z * f.area, 0) / totalArea,
      };

      // Rango de tilts
      const tilts = group.map(i => normalToTilt(faces[i].normal));
      const minTilt = Math.min(...tilts);
      const maxTilt = Math.max(...tilts);

      curvedClusters.push({
        faces: groupFaces,
        avgAzimuth,
        avgTilt,
        totalArea,
        center,
        isCurved: true,
        azimuthRange: [sortedAz[0], sortedAz[sortedAz.length - 1]],
        tiltRange: [minTilt, maxTilt],
      });

      for (const idx of group) {
        curvedFaceIndices.add(idx);
      }
    }
  }

  // 5. Retornar clusters curvos y las caras restantes (no curvas)
  const remainingFaces = faces.filter((_, i) => !curvedFaceIndices.has(i));
  return { curvedClusters, remainingFaces };
}

function clusterFacesIntoFacades(
  faces: Face3D[],
  northOffsetDeg: number
): FacadeCluster[] {
  const clusters: FacadeCluster[] = [];
  // Tolerancias ajustadas para separar correctamente aguas de techo
  // (un techo a 2 aguas tiene aguas opuestas a 180°, pero un techo a 4 aguas
  //  tiene aguas a 90° de diferencia, por lo que 30° de tolerancia las separa bien)
  const AZIMUTH_TOLERANCE = 30; // ±30° para agrupar (suficiente para separar aguas a 90°)
  const TILT_TOLERANCE = 20;    // ±20° para agrupar (captura curvaturas 3D con triángulos similares)

  for (const face of faces) {
    const faceAzimuth = normalToSolarAzimuth(face.normal, northOffsetDeg);
    const faceTilt = normalToTilt(face.normal);

    // Buscar cluster existente compatible
    let matched = false;
    for (const cluster of clusters) {
      let azDiff = Math.abs(faceAzimuth - cluster.avgAzimuth);
      if (azDiff > 180) azDiff = 360 - azDiff;
      const tiltDiff = Math.abs(faceTilt - cluster.avgTilt);

      if (azDiff < AZIMUTH_TOLERANCE && tiltDiff < TILT_TOLERANCE) {
        cluster.faces.push(face);
        // Recalcular promedios ponderados por área
        const totalArea = cluster.totalArea + face.area;
        cluster.avgAzimuth = (cluster.avgAzimuth * cluster.totalArea + faceAzimuth * face.area) / totalArea;
        cluster.avgTilt = (cluster.avgTilt * cluster.totalArea + faceTilt * face.area) / totalArea;
        cluster.totalArea = totalArea;
        // Recalcular centro
        const n = cluster.faces.length;
        cluster.center = {
          x: cluster.faces.reduce((s, f) => s + f.center.x, 0) / n,
          y: cluster.faces.reduce((s, f) => s + f.center.y, 0) / n,
          z: cluster.faces.reduce((s, f) => s + f.center.z, 0) / n,
        };
        matched = true;
        break;
      }
    }

    if (!matched) {
      clusters.push({
        faces: [face],
        avgAzimuth: faceAzimuth,
        avgTilt: faceTilt,
        totalArea: face.area,
        center: { ...face.center },
      });
    }
  }

  return clusters;
}

/**
 * Nombra una fachada según su orientación e inclinación.
 * Distingue entre: muros verticales, techos planos y techos inclinados (aguas).
 */
function nameFacade(azimuth: number, tilt: number): string {
  // Techo plano (horizontal)
  if (tilt < 15) {
    if (tilt < 5) return 'Techo/Cubierta (Horizontal)';
    return 'Techo/Cubierta (Casi Horizontal)';
  }
  
  // Determinar la dirección cardinal
  const az = ((azimuth + 360) % 360);
  let direction = '';
  if (az >= 337.5 || az < 22.5) direction = 'Sur';
  else if (az >= 22.5 && az < 67.5) direction = 'Suroeste';
  else if (az >= 67.5 && az < 112.5) direction = 'Oeste';
  else if (az >= 112.5 && az < 157.5) direction = 'Noroeste';
  else if (az >= 157.5 && az < 202.5) direction = 'Norte';
  else if (az >= 202.5 && az < 247.5) direction = 'Noreste';
  else if (az >= 247.5 && az < 292.5) direction = 'Este';
  else direction = 'Sureste';
  
  // Techo inclinado (agua de techo): tilt entre 15° y 75°
  if (tilt >= 15 && tilt <= 75) {
    return `Techo Agua ${direction}`;
  }
  
  // Fachada vertical (muro): tilt > 75°
  return `Fachada ${direction}`;
}

// ─── Obstacle Recalculation ──────────────────────────────────────────────────

/**
 * Recalcula los obstáculos existentes (entorno) desde un nuevo punto de observación.
 * Esto es necesario cuando se importa un modelo 3D y se quiere ver las sombras
 * desde la perspectiva de una fachada específica del edificio.
 * 
 * @param existingObstaclesRaw Los datos 3D originales de los obstáculos (OBJ o Marsh)
 * @param newObserver El nuevo punto de observación (en la fachada del edificio)
 * @param northOffset Rotación del norte
 * @returns Obstáculos recalculados como polígonos angulares
 */
export function recalculateObstaclesFromPoint(
  obstacleVertices3D: Vertex3D[][],
  newObserver: Vertex3D,
  northOffset: number = 0
): ObstaclePolygon[] {
  const DEG2RAD = Math.PI / 180;
  const obstacles: ObstaclePolygon[] = [];

  for (let i = 0; i < obstacleVertices3D.length; i++) {
    const vertices = obstacleVertices3D[i];
    if (vertices.length < 3) continue;

    // Proyectar cada vértice a coordenadas angulares desde el nuevo observador
    const angularPoints: Array<{ azimuth: number; altitude: number }> = [];

    // First pass: compute all angular projections (including below horizon)
    const allProjections: Array<{ azimuth: number; altitude: number }> = [];
    let hasAboveHorizon = false;
    
    for (const pt of vertices) {
      const dx = pt.x - newObserver.x;
      const dy = pt.y - newObserver.y;
      const dz = pt.z - newObserver.z;

      const horizontalDist = Math.sqrt(dx * dx + dy * dy);
      if (horizontalDist < 0.001 && Math.abs(dz) < 0.001) continue;

      const altitude = Math.atan2(dz, horizontalDist) * 180 / Math.PI;
      
      // Skip points far below horizon (e.g. underground objects)
      if (altitude < -45) continue;

      let bearing = Math.atan2(dx, dy) * 180 / Math.PI;
      bearing += northOffset;

      let solarAzimuth = bearing - 180;
      if (solarAzimuth > 180) solarAzimuth -= 360;
      if (solarAzimuth < -180) solarAzimuth += 360;

      if (altitude > 0) hasAboveHorizon = true;
      
      allProjections.push({
        azimuth: solarAzimuth,
        altitude: altitude,
      });
    }
    
    // Only include obstacles that have at least one point above horizon
    if (!hasAboveHorizon) continue;
    
    // Clip altitudes to 0 (horizon) for the convex hull
    for (const p of allProjections) {
      angularPoints.push({
        azimuth: p.azimuth,
        altitude: Math.max(0, p.altitude),
      });
    }

    if (angularPoints.length < 3) continue;

    // Calcular convex hull en espacio angular proyectado
    const hull = angularConvexHull(angularPoints);
    if (hull.length < 3) continue;

    obstacles.push({
      id: `recalc-obs-${i}-${Date.now()}`,
      name: `Obstáculo ${i + 1}`,
      color: FACADE_COLORS[i % FACADE_COLORS.length],
      vertices: hull.map(p => ({
        azimuth: Math.round(p.azimuth * 100) / 100,
        altitude: Math.round(p.altitude * 100) / 100,
      })),
      visible: true,
    });
  }

  return obstacles;
}

// ─── Convex Hull (copied from objParser for independence) ────────────────────

function angularToPlane(p: { azimuth: number; altitude: number }): { x: number; y: number } {
  const compassAz = (p.azimuth + 180) % 360;
  const r = (90 - p.altitude) / 90;
  const angleRad = (compassAz - 90) * Math.PI / 180;
  return { x: r * Math.cos(angleRad), y: r * Math.sin(angleRad) };
}

function planeToAngular(p: { x: number; y: number }): { azimuth: number; altitude: number } {
  const r = Math.sqrt(p.x * p.x + p.y * p.y);
  const altitude = Math.max(0, 90 - r * 90);
  const angleRad = Math.atan2(p.y, p.x);
  const compassAz = (angleRad * 180 / Math.PI + 90 + 360) % 360;
  let solarAz = compassAz - 180;
  if (solarAz > 180) solarAz -= 360;
  if (solarAz < -180) solarAz += 360;
  return { azimuth: solarAz, altitude };
}

function cross2D(O: { x: number; y: number }, A: { x: number; y: number }, B: { x: number; y: number }): number {
  return (A.x - O.x) * (B.y - O.y) - (A.y - O.y) * (B.x - O.x);
}

function convexHull2D(points: Array<{ x: number; y: number }>): Array<{ x: number; y: number }> {
  if (points.length <= 3) return points;
  const sorted = [...points].sort((a, b) => a.x - b.x || a.y - b.y);
  const lower: Array<{ x: number; y: number }> = [];
  for (const p of sorted) {
    while (lower.length >= 2 && cross2D(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop();
    lower.push(p);
  }
  const upper: Array<{ x: number; y: number }> = [];
  for (const p of sorted.reverse()) {
    while (upper.length >= 2 && cross2D(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop();
    upper.push(p);
  }
  lower.pop();
  upper.pop();
  return [...lower, ...upper];
}

function angularConvexHull(points: Array<{ azimuth: number; altitude: number }>): Array<{ azimuth: number; altitude: number }> {
  if (points.length <= 2) return points;
  const projected = points.map(p => ({ plane: angularToPlane(p), original: p }));
  const hull2D = convexHull2D(projected.map(p => p.plane));
  return hull2D.map(hp => planeToAngular(hp));
}

// ─── Non-Planar Face Splitting ────────────────────────────────────────────────

/**
 * Detecta si un polígono con 4+ vértices es no-planar (cubre múltiples orientaciones,
 * como un quad que abarca dos aguas de un techo a dos aguas).
 * Si las sub-normales de los triángulos difieren significativamente (>25°),
 * divide el polígono en triángulos individuales como caras separadas.
 * Retorna un array vacío si es planar (usar cara original),
 * o múltiples Face3D si fue dividido.
 */
function splitNonPlanarFace(faceVerts: Vertex3D[], modelCentroid: Vertex3D): Face3D[] {
  // Triangular por fan desde vértice 0
  const triangles: { verts: Vertex3D[]; normal: Vertex3D; area: number }[] = [];
  
  for (let i = 1; i < faceVerts.length - 1; i++) {
    const triVerts = [faceVerts[0], faceVerts[i], faceVerts[i + 1]];
    const normal = calculateFaceNormal(triVerts);
    const area = calculateFaceArea(triVerts);
    if (area < 0.001) continue;
    triangles.push({ verts: triVerts, normal, area });
  }

  if (triangles.length <= 1) {
    return []; // No se puede dividir
  }

  // Verificar si las normales de los triángulos difieren significativamente
  let maxAngleDeg = 0;
  for (let i = 0; i < triangles.length; i++) {
    for (let j = i + 1; j < triangles.length; j++) {
      const n1 = triangles[i].normal;
      const n2 = triangles[j].normal;
      const dot = n1.x * n2.x + n1.y * n2.y + n1.z * n2.z;
      const clampedDot = Math.max(-1, Math.min(1, dot));
      const angleDeg = Math.acos(clampedDot) * 180 / Math.PI;
      if (angleDeg > maxAngleDeg) maxAngleDeg = angleDeg;
    }
  }

  // Si la diferencia máxima es <25°, el polígono es planar
  if (maxAngleDeg < 25) {
    return []; // Es planar, no dividir
  }

  // Dividir en triángulos individuales como caras separadas
  const result: Face3D[] = [];
  for (const tri of triangles) {
    let normal = tri.normal;
    const center = calculateFaceCenter(tri.verts);
    
    // Orientar normal hacia afuera
    const toCentroid = {
      x: modelCentroid.x - center.x,
      y: modelCentroid.y - center.y,
      z: modelCentroid.z - center.z,
    };
    const dot = normal.x * toCentroid.x + normal.y * toCentroid.y + normal.z * toCentroid.z;
    if (dot > 0) {
      normal = { x: -normal.x, y: -normal.y, z: -normal.z };
    }

    result.push({
      vertices: tri.verts,
      normal,
      center,
      area: tri.area,
    });
  }

  return result;
}

// ─── Main Import Function ────────────────────────────────────────────────────

/**
 * Importa un modelo 3D del edificio a evaluar y detecta sus fachadas.
 * 
 * @param input Contenido del archivo OBJ (string) o un OBJParseResult ya parseado (ej: desde glTF)
 * @param config Configuración de importación
 * @param existingObstacleVertices Vértices 3D de los obstáculos existentes (entorno)
 * @returns EvaluationModel con fachadas detectadas y obstáculos recalculados
 */
export function importBuildingModel(
  input: string | OBJParseResult,
  config: ImportConfig = DEFAULT_IMPORT_CONFIG,
  existingObstacleVertices?: Vertex3D[][]
): EvaluationModel {
  // 1. Parsear el OBJ (o usar el resultado ya parseado)
  const parseResult: OBJParseResult = typeof input === 'string' ? parseOBJText(input) : input;

  // 2. Aplicar transformaciones (escala, remapeo de ejes, rotación)
  // Determinar el eje vertical
  let effectiveUpAxis: 'X' | 'Y' | 'Z' = 'Z';
  if (config.upAxis === 'auto') {
    // Primero escalar los vértices para la auto-detección
    const scaledVerts = parseResult.vertices.map(v => ({
      x: v.x * config.scaleFactor,
      y: v.y * config.scaleFactor,
      z: v.z * config.scaleFactor,
    }));
    const allFaces = parseResult.objects.flatMap(o => o.faces);
    const detection = autoDetectUpAxis(scaledVerts, allFaces);
    effectiveUpAxis = detection.bestAxis;
    // Guardar la detección en el resultado para la UI
    (parseResult as any).__detectedUpAxis = detection.bestAxis;
    (parseResult as any).__detectionConfidence = detection.confidence;
    (parseResult as any).__detectionScores = detection.scores;
  } else {
    effectiveUpAxis = config.upAxis as 'X' | 'Y' | 'Z';
  }
  // Legacy: si swapYZ está activo y upAxis no fue configurado explícitamente
  if (config.swapYZ && config.upAxis === 'auto') {
    effectiveUpAxis = 'Y';
  }

  let vertices = parseResult.vertices.map(v => {
    let scaled = {
      x: v.x * config.scaleFactor,
      y: v.y * config.scaleFactor,
      z: v.z * config.scaleFactor,
    };
    // Remapear ejes para que Z sea vertical
    scaled = remapAxes(scaled, effectiveUpAxis);
    // Aplicar rotación horizontal
    if (config.rotationDeg !== 0) {
      scaled = rotateAroundVertical(scaled, config.rotationDeg);
    }
    return scaled;
  });

  // 3. Calcular bounding box y centroide
  let minX = Infinity, minY = Infinity, minZ = Infinity;
  let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
  for (const v of vertices) {
    if (v.x < minX) minX = v.x;
    if (v.y < minY) minY = v.y;
    if (v.z < minZ) minZ = v.z;
    if (v.x > maxX) maxX = v.x;
    if (v.y > maxY) maxY = v.y;
    if (v.z > maxZ) maxZ = v.z;
  }

  const centroid: Vertex3D = {
    x: (minX + maxX) / 2,
    y: (minY + maxY) / 2,
    z: (minZ + maxZ) / 2,
  };

  const dimensions: Vertex3D = {
    x: maxX - minX,
    y: maxY - minY,
    z: maxZ - minZ,
  };

  // 4. Extraer caras 3D con normales y áreas
  // PASO 4a: Deduplicar caras (eliminar back faces de SketchUp)
  // SketchUp exporta cada cara con su reverso (front + back face con mismos vértices en orden invertido).
  // Si no se filtran, el área se duplica. Detectamos duplicados por el conjunto de índices de vértices.
  const seenFaceKeys = new Set<string>();
  const dedupedFaces: Array<{ vertexIndices: number[]; objName: string }> = [];
  
  for (const obj of parseResult.objects) {
    for (const face of obj.faces) {
      if (face.vertexIndices.length < 3) continue;
      // Crear clave canónica: ordenar índices para que front y back face generen la misma clave
      const canonicalKey = [...face.vertexIndices].sort((a, b) => a - b).join(',');
      if (seenFaceKeys.has(canonicalKey)) {
        continue; // Cara duplicada (back face), omitir
      }
      seenFaceKeys.add(canonicalKey);
      dedupedFaces.push({ vertexIndices: face.vertexIndices, objName: obj.name });
    }
  }

  // PASO 4b: Procesar caras deduplicadas
  const faces3D: Face3D[] = [];
  for (const face of dedupedFaces) {
    const faceVerts = face.vertexIndices.map(idx => vertices[idx]);

    // Para polígonos con 4+ vértices, verificar si es no-planar
    // (puede cubrir dos aguas de techo diferentes)
    if (faceVerts.length >= 4) {
      const subFaces = splitNonPlanarFace(faceVerts, centroid);
      if (subFaces.length > 1) {
        // El polígono fue dividido en sub-caras con normales distintas
        for (const sf of subFaces) {
          faces3D.push(sf);
        }
        continue;
      }
    }

    let normal = calculateFaceNormal(faceVerts);
    const center = calculateFaceCenter(faceVerts);
    const area = calculateFaceArea(faceVerts);

    // Orientar la normal hacia afuera: si apunta hacia el centroide del modelo, invertirla
    const toCentroid = {
      x: centroid.x - center.x,
      y: centroid.y - center.y,
      z: centroid.z - center.z,
    };
    const dot = normal.x * toCentroid.x + normal.y * toCentroid.y + normal.z * toCentroid.z;
    if (dot > 0) {
      // Normal apunta hacia el centroide (inward), invertir
      normal = { x: -normal.x, y: -normal.y, z: -normal.z };
    }

    faces3D.push({ vertices: faceVerts, normal, center, area });
  }

  // PASO 4c: Deduplicar caras geométricamente paralelas (grosor de losa/teja en SketchUp)
  // SketchUp modela el grosor de techos/muros, creando dos caras paralelas (exterior + interior)
  // separadas por ~0.1-1.5m con la misma normal y área similar. Solo debemos contar la exterior.
  // Criterio: misma normal (ángulo < 5°), área similar (±15%), centros alineados en la dirección normal (< 2m).
  const THICKNESS_TOLERANCE = 2.0; // máximo grosor de losa/teja a deduplicar
  const AREA_RATIO_TOLERANCE = 0.15; // ±15% de diferencia de área
  const NORMAL_ANGLE_TOLERANCE = 5; // grados
  
  const deduplicatedFaces3D: Face3D[] = [];
  const usedIndices = new Set<number>();
  
  for (let i = 0; i < faces3D.length; i++) {
    if (usedIndices.has(i)) continue;
    const faceA = faces3D[i];
    
    // Solo deduplicar caras significativas (> 10 m²)
    if (faceA.area < 10) {
      deduplicatedFaces3D.push(faceA);
      continue;
    }
    
    let foundDuplicate = false;
    for (let j = i + 1; j < faces3D.length; j++) {
      if (usedIndices.has(j)) continue;
      const faceB = faces3D[j];
      
      // Verificar área similar
      const areaRatio = Math.abs(faceA.area - faceB.area) / Math.max(faceA.area, faceB.area);
      if (areaRatio > AREA_RATIO_TOLERANCE) continue;
      
      // Verificar normales paralelas (mismo sentido)
      const dotNormals = faceA.normal.x * faceB.normal.x + faceA.normal.y * faceB.normal.y + faceA.normal.z * faceB.normal.z;
      if (dotNormals < Math.cos(NORMAL_ANGLE_TOLERANCE * Math.PI / 180)) continue;
      
      // Verificar que los centros están alineados en la dirección de la normal (desplazamiento por grosor)
      const centerDiff = {
        x: faceB.center.x - faceA.center.x,
        y: faceB.center.y - faceA.center.y,
        z: faceB.center.z - faceA.center.z,
      };
      const centerDist = Math.sqrt(centerDiff.x ** 2 + centerDiff.y ** 2 + centerDiff.z ** 2);
      
      if (centerDist > THICKNESS_TOLERANCE) continue;
      
      // Verificar que el desplazamiento es principalmente en la dirección de la normal
      // (no dos caras paralelas pero lateralmente separadas)
      if (centerDist > 0.01) {
        const normalComponent = Math.abs(
          centerDiff.x * faceA.normal.x + centerDiff.y * faceA.normal.y + centerDiff.z * faceA.normal.z
        );
        const normalRatio = normalComponent / centerDist;
        if (normalRatio < 0.7) continue; // El desplazamiento no es en la dirección normal
      }
      
      // Es un duplicado geométrico (cara interior del grosor de losa)
      // Mantener la cara más exterior (la que está más lejos del centroide del modelo)
      const distA = Math.sqrt(
        (faceA.center.x - centroid.x) ** 2 +
        (faceA.center.y - centroid.y) ** 2 +
        (faceA.center.z - centroid.z) ** 2
      );
      const distB = Math.sqrt(
        (faceB.center.x - centroid.x) ** 2 +
        (faceB.center.y - centroid.y) ** 2 +
        (faceB.center.z - centroid.z) ** 2
      );
      
      if (distA >= distB) {
        usedIndices.add(j); // Descartar B (interior)
      } else {
        usedIndices.add(i); // Descartar A (interior)
        foundDuplicate = true;
        break;
      }
    }
    
    if (!foundDuplicate) {
      deduplicatedFaces3D.push(faceA);
    }
  }
  
  // Agregar las caras que no fueron marcadas como usadas y no se procesaron arriba
  for (let j = 0; j < faces3D.length; j++) {
    if (!usedIndices.has(j) && !deduplicatedFaces3D.includes(faces3D[j])) {
      deduplicatedFaces3D.push(faces3D[j]);
    }
  }

  // 5. NUEVO: Detectar superficies curvas por conectividad ANTES del clustering por orientación
  // Esto evita que bóvedas/arcos se dividan en múltiples secciones Este/Oeste/Horizontal
  const allSignificantFaces = deduplicatedFaces3D.filter(f => f.area > 0.01);
  const { curvedClusters, remainingFaces } = detectCurvedSurfaces(allSignificantFaces, config.northOffset);

  // 6. Filtrar caras restantes (no curvas) en verticales, techos planos y techos inclinados
  const verticalFaces = remainingFaces.filter(f => isVerticalFace(f.normal));
  const flatRoofFaces = remainingFaces.filter(f => isRoofFace(f.normal));
  const slopedRoofFaces = remainingFaces.filter(f => isSlopedRoofFace(f.normal));
  
  const verticalClusters = clusterFacesIntoFacades(verticalFaces, config.northOffset);
  const flatRoofClusters = clusterFacesIntoFacades(flatRoofFaces, config.northOffset);
  const slopedRoofClusters = clusterFacesIntoFacades(slopedRoofFaces, config.northOffset);
  
  // Combinar clusters curvos + verticales + techos planos + techos inclinados
  const allClusters = [...curvedClusters, ...verticalClusters, ...flatRoofClusters, ...slopedRoofClusters];

  // 7. Filtrar clusters pequeños (menos del 3% del área total de superficies)
  // Umbral reducido para no perder aguas de techo pequeñas en techos de 3/4 aguas
  // Los clusters curvos nunca se filtran (ya pasaron el umbral de MIN_CURVED_FACES)
  const totalFacadeArea = allClusters.reduce((s, c) => s + c.totalArea, 0);
  const significantClusters = allClusters
    .filter(c => c.isCurved || c.totalArea > totalFacadeArea * 0.03)
    .sort((a, b) => b.totalArea - a.totalArea);

  // 8. Generar DetectedFacade para cada cluster significativo
  const detectedFacades: DetectedFacade[] = significantClusters.map((cluster, idx) => {
    // Nombre especial para superficies curvas
    let uniqueName: string;
    if (cluster.isCurved) {
      // Determinar tipo de curvatura por el tilt promedio
      if (cluster.avgTilt < 30) {
        uniqueName = 'Techo Curvo (Cúpula)';
      } else if (cluster.avgTilt > 70) {
        uniqueName = 'Fachada Curva (Bóveda)';
      } else {
        uniqueName = 'Techo Curvo (Bóveda)';
      }
      // Si hay múltiples superficies curvas, añadir índice
      const curvedCount = significantClusters.filter((c, i) => i <= idx && c.isCurved).length;
      if (curvedCount > 1) {
        uniqueName = `${uniqueName} (${curvedCount})`;
      }
    } else {
      const name = nameFacade(cluster.avgAzimuth, cluster.avgTilt);
      uniqueName = significantClusters.filter((c, i) => i <= idx && !c.isCurved && nameFacade(c.avgAzimuth, c.avgTilt) === name).length > 1
        ? `${name} (${idx + 1})`
        : name;
    }

    // Calcular punto de evaluación según tipo de superficie:
    // - Techos planos (<15°): desde el centro, desplazado hacia arriba
    // - Techos inclinados (15-75°): desde el centro del agua, desplazado perpendicular a la pendiente
    // - Fachadas verticales (>75°): desde el centro, desplazado hacia afuera en la dirección de la normal
    let evalPoint: Vertex3D;
    
    if (cluster.avgTilt < 15) {
      // Techo plano: punto de evaluación sobre el centro
      evalPoint = {
        x: cluster.center.x,
        y: cluster.center.y,
        z: cluster.center.z + config.evaluationOffset,
      };
    } else if (cluster.avgTilt <= 75) {
      // Techo inclinado (agua): punto de evaluación sobre la superficie inclinada
      // Desplazar ligeramente en la dirección de la normal (perpendicular a la pendiente)
      const normalRad = (cluster.avgAzimuth + 180) * Math.PI / 180;
      const tiltRad = cluster.avgTilt * Math.PI / 180;
      evalPoint = {
        x: cluster.center.x + Math.sin(normalRad) * Math.sin(tiltRad) * config.evaluationOffset,
        y: cluster.center.y + Math.cos(normalRad) * Math.sin(tiltRad) * config.evaluationOffset,
        z: cluster.center.z + Math.cos(tiltRad) * config.evaluationOffset,
      };
    } else {
      // Fachada vertical: desplazar en la dirección de la normal horizontal
      const normalRad = (cluster.avgAzimuth + 180) * Math.PI / 180;
      evalPoint = {
        x: cluster.center.x + Math.sin(normalRad) * config.evaluationOffset,
        y: cluster.center.y + Math.cos(normalRad) * config.evaluationOffset,
        z: minZ + config.evaluationHeight,
      };
    }

    return {
      name: uniqueName,
      azimuthNormal: Math.round(cluster.avgAzimuth * 10) / 10,
      tilt: Math.round(cluster.avgTilt * 10) / 10,
      center: cluster.center,
      area: Math.round(cluster.totalArea * 100) / 100,
      evaluationPoint: evalPoint,
      color: FACADE_COLORS[idx % FACADE_COLORS.length],
      faceCount: cluster.faces.length,
      ...(cluster.isCurved ? {
        isCurved: true,
        azimuthRange: cluster.azimuthRange,
        tiltRange: cluster.tiltRange,
      } : {}),
    };
  });

  // 9. Punto de observación principal (centroide a nivel del suelo + altura de evaluación)
  const mainObservationPoint: Vertex3D = {
    x: centroid.x,
    y: centroid.y,
    z: minZ + config.evaluationHeight,
  };

  // 10. Recalcular obstáculos desde la perspectiva del modelo
  let recalculatedObstacles: ObstaclePolygon[] = [];
  if (existingObstacleVertices && existingObstacleVertices.length > 0) {
    recalculatedObstacles = recalculateObstaclesFromPoint(
      existingObstacleVertices,
      mainObservationPoint,
      config.northOffset
    );
  }

  // 11. Generar FacadeDefinition para CrossingConfig
  const facadeDefinitions: FacadeDefinition[] = detectedFacades.map(f => ({
    name: f.name,
    azimuthNormal: f.azimuthNormal,
    tilt: f.tilt,
  }));

  return {
    fileName: '',
    parseResult,
    transformedVertices: vertices,
    detectedFacades,
    centroid,
    dimensions,
    mainObservationPoint,
    recalculatedObstacles,
    facadeDefinitions,
    config,
  };
}

/**
 * Recalcula los obstáculos desde la perspectiva de una fachada específica.
 */
export function recalculateForFacade(
  facade: DetectedFacade,
  existingObstacleVertices: Vertex3D[][],
  northOffset: number = 0
): ObstaclePolygon[] {
  return recalculateObstaclesFromPoint(
    existingObstacleVertices,
    facade.evaluationPoint,
    northOffset
  );
}

/**
 * Extrae los vértices 3D de los obstáculos existentes para poder recalcularlos.
 * Esto requiere que los obstáculos hayan sido importados con datos 3D.
 * 
 * Si solo tenemos polígonos angulares (sin datos 3D), no podemos recalcular
 * desde otro punto. En ese caso, se usan los obstáculos tal cual.
 */
export function canRecalculateObstacles(obstacleSource: 'marsh' | 'obj' | 'drawn'): boolean {
  return obstacleSource === 'marsh' || obstacleSource === 'obj';
}

/**
 * Valida que un archivo OBJ es adecuado como modelo de edificio a evaluar.
 * Verifica que tenga geometría suficiente para detectar fachadas.
 */
export function validateBuildingModel(objText: string): {
  valid: boolean;
  message: string;
  vertexCount?: number;
  faceCount?: number;
} {
  if (!validateOBJText(objText)) {
    return { valid: false, message: 'El archivo no es un OBJ válido (debe contener vértices y caras)' };
  }

  const parsed = parseOBJText(objText);

  if (parsed.vertices.length < 4) {
    return { valid: false, message: 'El modelo necesita al menos 4 vértices para definir un volumen' };
  }

  if (parsed.totalFaces < 4) {
    return { valid: false, message: 'El modelo necesita al menos 4 caras para definir un volumen' };
  }

  return {
    valid: true,
    message: `Modelo válido: ${parsed.vertices.length} vértices, ${parsed.totalFaces} caras, ${parsed.objects.length} objeto(s)`,
    vertexCount: parsed.vertices.length,
    faceCount: parsed.totalFaces,
  };
}

/**
 * Genera un resumen del modelo importado para la UI.
 */
export function getModelSummary(model: EvaluationModel): {
  vertexCount: number;
  faceCount: number;
  objectCount: number;
  dimensions: string;
  facadeCount: number;
  facadeNames: string[];
  totalFacadeArea: number;
  centroid: string;
} {
  return {
    vertexCount: model.parseResult.vertices.length,
    faceCount: model.parseResult.totalFaces,
    objectCount: model.parseResult.objects.length,
    dimensions: `${model.dimensions.x.toFixed(1)} × ${model.dimensions.y.toFixed(1)} × ${model.dimensions.z.toFixed(1)} m`,
    facadeCount: model.detectedFacades.length,
    facadeNames: model.detectedFacades.map(f => f.name),
    totalFacadeArea: model.detectedFacades.reduce((s, f) => s + f.area, 0),
    centroid: `(${model.centroid.x.toFixed(1)}, ${model.centroid.y.toFixed(1)}, ${model.centroid.z.toFixed(1)})`,
  };
}
