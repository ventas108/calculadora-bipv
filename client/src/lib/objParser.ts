/**
 * OBJ File Parser for Solar Shading Calculator
 *
 * Parses Wavefront OBJ files (the format used by Andrew Marsh Sun Path 3D
 * for shadow models) and converts 3D geometry into solar obstacle polygons
 * that can be overlaid on the sun path diagram.
 *
 * The conversion pipeline:
 * 1. Parse OBJ text to extract vertices, faces, and groups/objects
 * 2. Determine the observation point (center of bounding box at ground level, or custom)
 * 3. For each object/group, sample surface points from face vertices
 * 4. Project each point to angular coordinates (azimuth, altitude) from observer
 * 5. Compute convex hull of angular projections for the obstacle silhouette
 * 6. Convert to ObstaclePolygon format compatible with SunPathDiagram
 *
 * Supports:
 * - Vertex definitions (v x y z)
 * - Face definitions (f v1 v2 v3 ...) with optional texture/normal indices
 * - Object names (o name)
 * - Group names (g name)
 * - Comments (# ...)
 * - Negative vertex indices (relative to current vertex list)
 */

import { ObstaclePolygon } from '@/components/SunPathDiagram';

// ── Types ─────────────────────────────────────────────────────────────

export interface Vertex3D {
  x: number;
  y: number;
  z: number;
}

interface OBJFace {
  vertexIndices: number[]; // 0-based indices into the vertex array
}

interface OBJObject {
  name: string;
  faces: OBJFace[];
}

export interface OBJParseResult {
  vertices: Vertex3D[];
  objects: OBJObject[];
  totalFaces: number;
  boundingBox: {
    min: Vertex3D;
    max: Vertex3D;
    center: Vertex3D;
    dimensions: Vertex3D;
  };
}

interface AngularPoint {
  azimuth: number;  // degrees, 0=South, negative=East, positive=West (solar convention)
  altitude: number; // degrees above horizon
}

export interface OBJObstacleResult {
  parseResult: OBJParseResult;
  observationPoint: Vertex3D;
  obstacles: ObstaclePolygon[];
  northOffset: number;
}

// ── OBJ Text Parser ──────────────────────────────────────────────────

/**
 * Parse a Wavefront OBJ file text into vertices, faces, and objects/groups.
 */
export function parseOBJText(text: string): OBJParseResult {
  const vertices: Vertex3D[] = [];
  const objects: OBJObject[] = [];
  let currentObject: OBJObject = { name: 'default', faces: [] };
  let totalFaces = 0;

  const lines = text.split('\n');

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (line.length === 0 || line.startsWith('#')) continue;

    const parts = line.split(/\s+/);
    const keyword = parts[0];

    switch (keyword) {
      case 'v': {
        // Vertex: v x y z [w]
        const x = parseFloat(parts[1]) || 0;
        const y = parseFloat(parts[2]) || 0;
        const z = parseFloat(parts[3]) || 0;
        vertices.push({ x, y, z });
        break;
      }

      case 'o':
      case 'g': {
        // Object or Group name
        const name = parts.slice(1).join(' ') || `Object_${objects.length + 1}`;
        // Save current object if it has faces
        if (currentObject.faces.length > 0) {
          objects.push(currentObject);
        }
        currentObject = { name, faces: [] };
        break;
      }

      case 'f': {
        // Face: f v1 v2 v3 ... or f v1/vt1/vn1 v2/vt2/vn2 ...
        const vertexIndices: number[] = [];
        for (let i = 1; i < parts.length; i++) {
          const vertexPart = parts[i].split('/')[0]; // Take only vertex index
          let idx = parseInt(vertexPart);
          if (isNaN(idx)) continue;
          // OBJ indices are 1-based; negative means relative to end
          if (idx < 0) {
            idx = vertices.length + idx; // Convert negative to 0-based
          } else {
            idx = idx - 1; // Convert 1-based to 0-based
          }
          if (idx >= 0 && idx < vertices.length) {
            vertexIndices.push(idx);
          }
        }
        if (vertexIndices.length >= 3) {
          currentObject.faces.push({ vertexIndices });
          totalFaces++;
        }
        break;
      }

      // Ignore other keywords (vt, vn, mtllib, usemtl, s, etc.)
      default:
        break;
    }
  }

  // Don't forget the last object
  if (currentObject.faces.length > 0) {
    objects.push(currentObject);
  }

  // If no named objects were found, create one default with all faces
  if (objects.length === 0 && totalFaces > 0) {
    objects.push(currentObject);
  }

  // Compute bounding box
  const bbox = computeBoundingBox(vertices);

  return {
    vertices,
    objects,
    totalFaces,
    boundingBox: bbox,
  };
}

function computeBoundingBox(vertices: Vertex3D[]): {
  min: Vertex3D;
  max: Vertex3D;
  center: Vertex3D;
  dimensions: Vertex3D;
} {
  if (vertices.length === 0) {
    return {
      min: { x: 0, y: 0, z: 0 },
      max: { x: 0, y: 0, z: 0 },
      center: { x: 0, y: 0, z: 0 },
      dimensions: { x: 0, y: 0, z: 0 },
    };
  }

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

  return {
    min: { x: minX, y: minY, z: minZ },
    max: { x: maxX, y: maxY, z: maxZ },
    center: {
      x: (minX + maxX) / 2,
      y: (minY + maxY) / 2,
      z: (minZ + maxZ) / 2,
    },
    dimensions: {
      x: maxX - minX,
      y: maxY - minY,
      z: maxZ - minZ,
    },
  };
}

// ── 3D → Angular projection ──────────────────────────────────────────

/**
 * Project a 3D point to angular coordinates (azimuth, altitude) as seen
 * from an observation point. Uses the convention where Y-axis points North
 * by default, with an optional northOffset rotation.
 *
 * Azimuth convention matches SunPathDiagram:
 *   0° = South, negative = East, positive = West
 */
function projectToAngular(
  point: Vertex3D,
  observer: Vertex3D,
  northOffsetDeg: number = 0
): AngularPoint | null {
  const dx = point.x - observer.x;
  const dy = point.y - observer.y;
  const dz = point.z - observer.z;

  const horizontalDist = Math.sqrt(dx * dx + dy * dy);

  // If the point is essentially at the observer, skip it
  if (horizontalDist < 0.001 && Math.abs(dz) < 0.001) return null;

  // Altitude: angle above the horizon
  const altitude = Math.atan2(dz, horizontalDist) * 180 / Math.PI;

  // Skip points well below the horizon
  if (altitude < -2) return null;

  // Bearing from observer: atan2(dx, dy) gives angle from Y-axis (North)
  let bearing = Math.atan2(dx, dy) * 180 / Math.PI; // 0=N, 90=E, -90=W

  // Apply north offset rotation
  bearing += northOffsetDeg;

  // Convert from geographic bearing (0=N, CW) to solar azimuth (0=S, neg=E, pos=W)
  let solarAzimuth = bearing - 180;
  if (solarAzimuth > 180) solarAzimuth -= 360;
  if (solarAzimuth < -180) solarAzimuth += 360;

  return {
    azimuth: solarAzimuth,
    altitude: Math.max(0, altitude),
  };
}

// ── Convex Hull (Graham Scan in projected 2D space) ──────────────────

function angularToPlane(p: AngularPoint): { x: number; y: number } {
  const compassAz = (p.azimuth + 180) % 360;
  const r = (90 - p.altitude) / 90;
  const angleRad = (compassAz - 90) * Math.PI / 180;
  return {
    x: r * Math.cos(angleRad),
    y: r * Math.sin(angleRad),
  };
}

function planeToAngular(p: { x: number; y: number }): AngularPoint {
  const r = Math.sqrt(p.x * p.x + p.y * p.y);
  const altitude = Math.max(0, 90 - r * 90);
  const angleRad = Math.atan2(p.y, p.x);
  const compassAz = (angleRad * 180 / Math.PI + 90 + 360) % 360;
  let solarAz = compassAz - 180;
  if (solarAz > 180) solarAz -= 360;
  if (solarAz < -180) solarAz += 360;
  return { azimuth: solarAz, altitude };
}

function cross2D(
  O: { x: number; y: number },
  A: { x: number; y: number },
  B: { x: number; y: number }
): number {
  return (A.x - O.x) * (B.y - O.y) - (A.y - O.y) * (B.x - O.x);
}

function convexHull2D(points: Array<{ x: number; y: number }>): Array<{ x: number; y: number }> {
  if (points.length <= 3) return points;

  const sorted = [...points].sort((a, b) => a.x - b.x || a.y - b.y);

  const lower: Array<{ x: number; y: number }> = [];
  for (const p of sorted) {
    while (lower.length >= 2 && cross2D(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
      lower.pop();
    }
    lower.push(p);
  }

  const upper: Array<{ x: number; y: number }> = [];
  for (const p of sorted.reverse()) {
    while (upper.length >= 2 && cross2D(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) {
      upper.pop();
    }
    upper.push(p);
  }

  lower.pop();
  upper.pop();

  return [...lower, ...upper];
}

function angularConvexHull(points: AngularPoint[]): AngularPoint[] {
  if (points.length <= 2) return points;

  const projected = points.map(p => ({
    plane: angularToPlane(p),
    original: p,
  }));

  const hull2D = convexHull2D(projected.map(p => p.plane));

  return hull2D.map(hp => planeToAngular(hp));
}

// ── Face sampling ────────────────────────────────────────────────────

/**
 * Sample points from a face's vertices and edge midpoints for better
 * silhouette approximation.
 */
function sampleFacePoints(face: OBJFace, vertices: Vertex3D[]): Vertex3D[] {
  const points: Vertex3D[] = [];

  // Add all face vertices
  for (const idx of face.vertexIndices) {
    points.push(vertices[idx]);
  }

  // Add edge midpoints for faces with 3+ vertices
  if (face.vertexIndices.length >= 3) {
    for (let i = 0; i < face.vertexIndices.length; i++) {
      const v1 = vertices[face.vertexIndices[i]];
      const v2 = vertices[face.vertexIndices[(i + 1) % face.vertexIndices.length]];
      points.push({
        x: (v1.x + v2.x) / 2,
        y: (v1.y + v2.y) / 2,
        z: (v1.z + v2.z) / 2,
      });
    }

    // Add face centroid
    const cx = face.vertexIndices.reduce((s, idx) => s + vertices[idx].x, 0) / face.vertexIndices.length;
    const cy = face.vertexIndices.reduce((s, idx) => s + vertices[idx].y, 0) / face.vertexIndices.length;
    const cz = face.vertexIndices.reduce((s, idx) => s + vertices[idx].z, 0) / face.vertexIndices.length;
    points.push({ x: cx, y: cy, z: cz });
  }

  return points;
}

// ── Color palette for OBJ objects ────────────────────────────────────

const OBJ_COLORS = [
  '#6366f1', // indigo
  '#f59e0b', // amber
  '#10b981', // emerald
  '#ef4444', // red
  '#8b5cf6', // violet
  '#06b6d4', // cyan
  '#f97316', // orange
  '#ec4899', // pink
  '#14b8a6', // teal
  '#84cc16', // lime
  '#a855f7', // purple
  '#3b82f6', // blue
];

// ── Main conversion function ─────────────────────────────────────────

/**
 * Convert parsed OBJ data to solar obstacle polygons.
 *
 * @param parseResult The parsed OBJ file data
 * @param observerPoint Custom observation point. If not provided, uses
 *   the center of the bounding box at ground level (z=min + 1.5m)
 * @param northOffsetDeg Rotation of north from Y-axis in degrees (clockwise)
 * @param swapYZ Whether to swap Y and Z axes (common in some 3D tools where Y is up)
 * @param scaleFactor Scale factor to apply to all coordinates (e.g., 0.001 for mm→m)
 */
/**
 * Apply scale, optional Y/Z swap, and (when an anchor point is given)
 * reposition an obstacle's vertices so its footprint center + base sit at
 * `anchor + positionOffset` in the SAME real-world coordinate space as the
 * evaluated building.
 *
 * Why this is needed: the obstacle file (a tree, a neighboring building) is
 * modeled independently in SketchUp/Blender/etc. and almost never shares an
 * origin with the evaluated building's own file. Without this, the obstacle
 * renders wherever its own local (0,0,0) happens to be, unrelated to where it
 * actually sits relative to the building — the "aparece minimizado y en una
 * zona lejana" symptom, regardless of what coordinates the obstacle file uses.
 *
 * `anchor` must already be in real-world meters/orientation (e.g. the
 * building's mainObservationPoint) — it is NOT scaled/swapped, only the
 * obstacle's own vertices are.
 *
 * `buildingRotationDeg` must match the `rotationDeg` applied to the evaluated
 * building (ImportConfig.rotationDeg in buildingModelImporter.ts). Why: when
 * the two files come from the same original scene (e.g. a wall and the
 * facade it sits against, modeled together in SketchUp), their relative
 * position — expressed here via `positionOffset` — is only valid in that
 * scene's original orientation. If the building gets rotated to correct its
 * compass alignment but the obstacle isn't rotated the same amount, the
 * obstacle's shape and its offset keep pointing the old way while the
 * building spins underneath it — the obstacle silhouette then misses the
 * facade's field of view entirely ("0 obstáculos visibles" after rotating).
 * Rotating both the obstacle's own vertices and its offset vector by the
 * same angle keeps them rigidly attached through any building rotation.
 */
export function transformOBJVertices(
  rawVertices: Vertex3D[],
  scaleFactor: number = 1.0,
  swapYZ: boolean = false,
  anchor?: Vertex3D,
  positionOffset?: Vertex3D,
  buildingRotationDeg: number = 0
): Vertex3D[] {
  let vertices = rawVertices;
  if (scaleFactor !== 1.0 || swapYZ) {
    vertices = rawVertices.map(v => {
      const scaled = {
        x: v.x * scaleFactor,
        y: v.y * scaleFactor,
        z: v.z * scaleFactor,
      };
      if (swapYZ) {
        return { x: scaled.x, y: scaled.z, z: scaled.y };
      }
      return scaled;
    });
  }

  if (buildingRotationDeg !== 0) {
    vertices = vertices.map(v => rotateAroundVerticalAxis(v, buildingRotationDeg));
  }
  const rotatedOffset = positionOffset && buildingRotationDeg !== 0
    ? rotateAroundVerticalAxis(positionOffset, buildingRotationDeg)
    : positionOffset;

  if (anchor) {
    const bbox = computeBoundingBox(vertices);
    const target = {
      x: anchor.x + (rotatedOffset?.x ?? 0),
      y: anchor.y + (rotatedOffset?.y ?? 0),
      z: anchor.z + (rotatedOffset?.z ?? 0),
    };
    const shift = {
      x: target.x - bbox.center.x,
      y: target.y - bbox.center.y,
      z: target.z - bbox.min.z,
    };
    vertices = vertices.map(v => ({
      x: v.x + shift.x,
      y: v.y + shift.y,
      z: v.z + shift.z,
    }));
  } else if (rotatedOffset && (rotatedOffset.x !== 0 || rotatedOffset.y !== 0 || rotatedOffset.z !== 0)) {
    // Sin edificio importado todavía: no hay ancla real, se aplica el offset
    // como traslación simple (mejor que nada, pero sin marco de referencia real).
    vertices = vertices.map(v => ({
      x: v.x + rotatedOffset.x,
      y: v.y + rotatedOffset.y,
      z: v.z + rotatedOffset.z,
    }));
  }

  return vertices;
}

/**
 * Rotate a point/vector around the vertical (Z) axis, in the same sense
 * (degrees, clockwise) as `rotateAroundVertical` in buildingModelImporter.ts.
 * Kept as a separate copy (not imported) so objParser.ts has no dependency
 * on the building importer — same rationale as the duplicated convex-hull
 * helpers in buildingModelImporter.ts.
 */
function rotateAroundVerticalAxis(v: Vertex3D, degrees: number): Vertex3D {
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

export function convertOBJToObstacles(
  parseResult: OBJParseResult,
  observerPoint?: Vertex3D,
  northOffsetDeg: number = 0,
  swapYZ: boolean = false,
  scaleFactor: number = 1.0,
  positionOffset?: Vertex3D,
  buildingRotationDeg: number = 0
): OBJObstacleResult {
  // observerPoint, cuando se pasa, es el punto de evaluación REAL del
  // edificio (ya en metros/orientación reales) — se usa tanto para reubicar
  // el obstáculo (ancla) como para calcular su silueta angular vista desde ahí.
  // buildingRotationDeg debe ser el mismo ImportConfig.rotationDeg aplicado al
  // edificio evaluado, para que el obstáculo gire junto con él (ver docstring
  // de transformOBJVertices).
  const vertices = transformOBJVertices(parseResult.vertices, scaleFactor, swapYZ, observerPoint, positionOffset, buildingRotationDeg);

  // Recompute bounding box with transformed vertices
  const bbox = computeBoundingBox(vertices);

  // Determine observation point
  const observer: Vertex3D = observerPoint
    ? { x: observerPoint.x, y: observerPoint.y, z: observerPoint.z }
    : {
        x: bbox.center.x,
        y: bbox.center.y,
        z: bbox.min.z + 1.5, // 1.5m eye height above ground
      };

  const obstacles: ObstaclePolygon[] = [];

  for (let objIdx = 0; objIdx < parseResult.objects.length; objIdx++) {
    const obj = parseResult.objects[objIdx];

    // Collect all angular projections for this object
    const angularPoints: AngularPoint[] = [];

    for (const face of obj.faces) {
      const samplePoints = sampleFacePoints(face, vertices);
      for (const pt of samplePoints) {
        const angular = projectToAngular(pt, observer, northOffsetDeg);
        if (angular && angular.altitude >= 0) {
          angularPoints.push(angular);
        }
      }
    }

    // Need at least 3 points for a polygon
    if (angularPoints.length < 3) continue;

    // Deduplicate close points to improve hull quality
    const uniquePoints = deduplicateAngularPoints(angularPoints, 0.5);
    if (uniquePoints.length < 3) continue;

    // Compute convex hull for the silhouette
    const hull = angularConvexHull(uniquePoints);
    if (hull.length < 3) continue;

    // Compute object bounding box for naming
    const objVertexIndices = new Set<number>();
    for (const face of obj.faces) {
      for (const idx of face.vertexIndices) {
        objVertexIndices.add(idx);
      }
    }
    const objVertices = Array.from(objVertexIndices).map(idx => vertices[idx]);
    const objBbox = computeBoundingBox(objVertices);
    const height = objBbox.dimensions.z;

    const distToObserver = Math.sqrt(
      Math.pow(objBbox.center.x - observer.x, 2) +
      Math.pow(objBbox.center.y - observer.y, 2)
    );

    obstacles.push({
      id: `obj-${objIdx}-${Date.now()}`,
      name: `${obj.name} (${height.toFixed(1)}m, d=${distToObserver.toFixed(1)}m)`,
      color: OBJ_COLORS[objIdx % OBJ_COLORS.length],
      vertices: hull.map(p => ({
        azimuth: Math.round(p.azimuth * 100) / 100,
        altitude: Math.round(p.altitude * 100) / 100,
      })),
      visible: true,
    });
  }

  return {
    parseResult: {
      ...parseResult,
      vertices,
      boundingBox: bbox,
    },
    observationPoint: observer,
    obstacles,
    northOffset: northOffsetDeg,
  };
}

/**
 * Remove angular points that are very close to each other to improve
 * convex hull quality and reduce computation.
 */
function deduplicateAngularPoints(points: AngularPoint[], threshold: number): AngularPoint[] {
  const result: AngularPoint[] = [];
  for (const p of points) {
    let isDuplicate = false;
    for (const existing of result) {
      if (
        Math.abs(p.azimuth - existing.azimuth) < threshold &&
        Math.abs(p.altitude - existing.altitude) < threshold
      ) {
        isDuplicate = true;
        break;
      }
    }
    if (!isDuplicate) {
      result.push(p);
    }
  }
  return result;
}

/**
 * Validate that a string is a valid OBJ file by checking for vertex and face definitions.
 */
export function validateOBJText(text: string): boolean {
  const lines = text.split('\n');
  let hasVertices = false;
  let hasFaces = false;

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (line.startsWith('v ')) hasVertices = true;
    if (line.startsWith('f ')) hasFaces = true;
    if (hasVertices && hasFaces) return true;
  }

  return hasVertices && hasFaces;
}

/**
 * Get a quick summary of an OBJ file for display in the UI.
 */
export function getOBJSummary(result: OBJParseResult): {
  vertexCount: number;
  faceCount: number;
  objectCount: number;
  objectNames: string[];
  dimensions: string;
  boundingBox: string;
} {
  return {
    vertexCount: result.vertices.length,
    faceCount: result.totalFaces,
    objectCount: result.objects.length,
    objectNames: result.objects.map(o => o.name),
    dimensions: `${result.boundingBox.dimensions.x.toFixed(2)} × ${result.boundingBox.dimensions.y.toFixed(2)} × ${result.boundingBox.dimensions.z.toFixed(2)}`,
    boundingBox: `(${result.boundingBox.min.x.toFixed(2)}, ${result.boundingBox.min.y.toFixed(2)}, ${result.boundingBox.min.z.toFixed(2)}) → (${result.boundingBox.max.x.toFixed(2)}, ${result.boundingBox.max.y.toFixed(2)}, ${result.boundingBox.max.z.toFixed(2)})`,
  };
}
