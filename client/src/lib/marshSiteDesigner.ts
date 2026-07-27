/**
 * Andrew Marsh Site Designer JSON Parser
 *
 * Converts 3D block models exported from Andrew Marsh's Site Designer
 * (https://andrewmarsh.com/software/site-designer-web/) into solar obstacle
 * polygons that can be overlaid on the sun path diagram.
 *
 * The conversion pipeline:
 * 1. Parse the JSON and extract solid blocks (obstacles) and analysis grids (observation points)
 * 2. Determine the observation point from the analysis grid center
 * 3. For each solid block, compute the 8 corners of the axis-aligned bounding box
 * 4. Project each corner to angular coordinates (azimuth, altitude) as seen from the observer
 * 5. Compute the convex hull of the angular projections to get the obstacle silhouette
 * 6. Convert to ObstaclePolygon format compatible with the SunPathDiagram component
 */

import { ObstaclePolygon } from '@/components/SunPathDiagram';

// ── Andrew Marsh Site Designer JSON types ──────────────────────────────

export interface MarshLocation {
  latitude: number;
  longitude: number;
  timezone: number;
  northOffset: number; // degrees, clockwise rotation of north from Y-axis
}

export interface MarshBlock {
  min: [number, number, number]; // [x, y, z] in mm
  max: [number, number, number]; // [x, y, z] in mm
  color: [number, number, number, number]; // [r, g, b, a] 0-1
  majorAxis: number;
  fixedSize: number;
  isSolid: boolean;
  group: number;
  isGrid?: boolean;
  isPlanar?: boolean;
  hidden?: boolean;
  width?: number;
  height?: number;
  depth?: number;
  azimuth?: number;
  altitude?: number;
  plane?: [number, number, number, number];
  preferredCellSize?: [number, number, number];
  surfaceIncidence?: boolean;
  clipToBlocks?: boolean;
  closedU?: boolean;
  inset?: boolean;
  isGridVolume?: boolean;
}

export interface MarshModel {
  units: number; // 0=m, 1=cm, 2=mm, 3=ft, 4=in
}

export interface MarshSiteDesignerJSON {
  Location: MarshLocation;
  DateTime?: {
    clockTime: number;
    dayOfMonth: number;
    monthOfYear: number;
    year: number;
  };
  Grid?: Record<string, unknown>;
  SunPath?: Record<string, unknown>;
  Shading?: Record<string, unknown>;
  Blocks: MarshBlock[];
  Display?: Record<string, unknown>;
  Model: MarshModel;
  Animation?: Record<string, unknown>;
  Slider?: Record<string, unknown>;
}

// ── Parsed result ──────────────────────────────────────────────────────

export interface MarshParseResult {
  location: MarshLocation;
  solidBlocks: MarshSolidBlock[];
  analysisGrids: MarshAnalysisGrid[];
  observationPoint: { x: number; y: number; z: number }; // in meters
  unitScale: number; // multiplier to convert file units to meters
  obstacles: ObstaclePolygon[];
}

export interface MarshSolidBlock {
  index: number;
  min: { x: number; y: number; z: number }; // in meters
  max: { x: number; y: number; z: number }; // in meters
  color: string; // hex color
  dimensions: { width: number; height: number; depth: number }; // in meters
}

export interface MarshAnalysisGrid {
  index: number;
  center: { x: number; y: number; z: number }; // in meters
  width: number;
  height: number;
  azimuth: number;
  altitude: number;
}

// ── Unit conversion ────────────────────────────────────────────────────

function getUnitScale(units: number): number {
  switch (units) {
    case 0: return 1;       // meters
    case 1: return 0.01;    // cm → m
    case 2: return 0.001;   // mm → m
    case 3: return 0.3048;  // ft → m
    case 4: return 0.0254;  // in → m
    default: return 0.001;  // default mm
  }
}

// ── Color conversion ───────────────────────────────────────────────────

function rgbaToHex(r: number, g: number, b: number): string {
  const toHex = (v: number) => Math.round(v * 255).toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

// ── 3D → Angular projection ───────────────────────────────────────────

interface Point3D {
  x: number;
  y: number;
  z: number;
}

interface AngularPoint {
  azimuth: number;  // degrees, 0=South, negative=East, positive=West (solar convention)
  altitude: number; // degrees above horizon
}

/**
 * Project a 3D point to angular coordinates (azimuth, altitude) as seen
 * from an observation point. Uses the Andrew Marsh convention where Y-axis
 * points North by default, with an optional northOffset rotation.
 *
 * The azimuth convention used here matches the SunPathDiagram:
 *   0° = South, negative = East, positive = West
 */
function projectToAngular(
  point: Point3D,
  observer: Point3D,
  northOffsetDeg: number = 0
): AngularPoint | null {
  const dx = point.x - observer.x;
  const dy = point.y - observer.y;
  const dz = point.z - observer.z;

  const horizontalDist = Math.sqrt(dx * dx + dy * dy);

  // If the point is essentially at the observer, skip it
  if (horizontalDist < 0.01 && Math.abs(dz) < 0.01) return null;

  // Altitude: angle above the horizon
  const altitude = Math.atan2(dz, horizontalDist) * 180 / Math.PI;

  // Skip points below the horizon
  if (altitude < -2) return null;

  // Bearing from observer: atan2(dx, dy) gives angle from Y-axis (North)
  // In Marsh's coordinate system, Y-axis points North (with optional offset)
  let bearing = Math.atan2(dx, dy) * 180 / Math.PI; // 0=N, 90=E, -90=W

  // Apply north offset rotation
  bearing += northOffsetDeg;

  // Convert from geographic bearing (0=N, CW) to solar azimuth (0=S, neg=E, pos=W)
  // Geographic: 0=N, 90=E, 180=S, 270=W
  // Solar: 0=S, -90=E, +90=W, ±180=N
  let solarAzimuth = bearing - 180;
  if (solarAzimuth > 180) solarAzimuth -= 360;
  if (solarAzimuth < -180) solarAzimuth += 360;

  return {
    azimuth: solarAzimuth,
    altitude: Math.max(0, altitude), // Clamp to horizon
  };
}

/**
 * Get the 8 corners of an axis-aligned bounding box.
 */
function getBoxCorners(min: Point3D, max: Point3D): Point3D[] {
  return [
    { x: min.x, y: min.y, z: min.z },
    { x: max.x, y: min.y, z: min.z },
    { x: min.x, y: max.y, z: min.z },
    { x: max.x, y: max.y, z: min.z },
    { x: min.x, y: min.y, z: max.z },
    { x: max.x, y: min.y, z: max.z },
    { x: min.x, y: max.y, z: max.z },
    { x: max.x, y: max.y, z: max.z },
  ];
}

/**
 * Get additional edge midpoints for better silhouette approximation.
 * This helps when the observer is close to a large block, where the
 * convex hull of just 8 corners may not accurately represent the
 * angular silhouette.
 */
function getBoxEdgeMidpoints(min: Point3D, max: Point3D): Point3D[] {
  const mx = (min.x + max.x) / 2;
  const my = (min.y + max.y) / 2;
  const mz = (min.z + max.z) / 2;

  return [
    // Top face edge midpoints
    { x: mx, y: min.y, z: max.z },
    { x: mx, y: max.y, z: max.z },
    { x: min.x, y: my, z: max.z },
    { x: max.x, y: my, z: max.z },
    // Bottom face edge midpoints
    { x: mx, y: min.y, z: min.z },
    { x: mx, y: max.y, z: min.z },
    { x: min.x, y: my, z: min.z },
    { x: max.x, y: my, z: min.z },
    // Vertical edge midpoints
    { x: min.x, y: min.y, z: mz },
    { x: max.x, y: min.y, z: mz },
    { x: min.x, y: max.y, z: mz },
    { x: max.x, y: max.y, z: mz },
    // Face centers
    { x: mx, y: my, z: max.z }, // top
    { x: mx, y: my, z: min.z }, // bottom
    { x: mx, y: min.y, z: mz }, // front
    { x: mx, y: max.y, z: mz }, // back
    { x: min.x, y: my, z: mz }, // left
    { x: max.x, y: my, z: mz }, // right
  ];
}

// ── Convex Hull (Graham Scan in angular space) ─────────────────────────

/**
 * Compute the convex hull of a set of 2D points using the Graham Scan algorithm.
 * Points are in (azimuth, altitude) space, but we need to handle the azimuth
 * wrap-around carefully.
 *
 * We use a stereographic-like projection to map angular points to a 2D plane
 * before computing the convex hull, then convert back.
 */
function angularToPlane(p: AngularPoint): { x: number; y: number } {
  // Use the same projection as the SunPathDiagram for consistency
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
  let angleRad = Math.atan2(p.y, p.x);
  let compassAz = (angleRad * 180 / Math.PI + 90 + 360) % 360;
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

  // Sort by x, then by y
  const sorted = [...points].sort((a, b) => a.x - b.x || a.y - b.y);

  // Build lower hull
  const lower: Array<{ x: number; y: number }> = [];
  for (const p of sorted) {
    while (lower.length >= 2 && cross2D(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
      lower.pop();
    }
    lower.push(p);
  }

  // Build upper hull
  const upper: Array<{ x: number; y: number }> = [];
  for (const p of sorted.reverse()) {
    while (upper.length >= 2 && cross2D(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) {
      upper.pop();
    }
    upper.push(p);
  }

  // Remove last point of each half because it's repeated
  lower.pop();
  upper.pop();

  return [...lower, ...upper];
}

/**
 * Compute the convex hull of angular points, working in projected 2D space.
 */
function angularConvexHull(points: AngularPoint[]): AngularPoint[] {
  if (points.length <= 2) return points;

  // Project to 2D plane
  const projected = points.map(p => ({
    plane: angularToPlane(p),
    original: p,
  }));

  // Compute convex hull in 2D
  const hull2D = convexHull2D(projected.map(p => p.plane));

  // Map back to angular coordinates
  return hull2D.map(p => planeToAngular(p));
}

// ── Main parser ────────────────────────────────────────────────────────

/**
 * Validate that the input is a valid Andrew Marsh Site Designer JSON file.
 */
export function validateMarshJSON(data: unknown): data is MarshSiteDesignerJSON {
  if (!data || typeof data !== 'object') return false;
  const obj = data as Record<string, unknown>;

  // Must have Location with lat/lon
  if (!obj.Location || typeof obj.Location !== 'object') return false;
  const loc = obj.Location as Record<string, unknown>;
  if (typeof loc.latitude !== 'number' || typeof loc.longitude !== 'number') return false;

  // Must have Blocks array
  if (!Array.isArray(obj.Blocks)) return false;

  // Must have Model with units
  if (!obj.Model || typeof obj.Model !== 'object') return false;

  return true;
}

/**
 * Parse an Andrew Marsh Site Designer JSON file and convert solid blocks
 * to solar obstacle polygons.
 *
 * @param json The parsed JSON object from the Site Designer export
 * @param customObserverPoint Optional custom observation point (in file units).
 *   If not provided, the center of the first analysis grid is used.
 *   If no analysis grid exists, the centroid of all blocks at ground level is used.
 * @returns Parsed result with obstacles ready for the SunPathDiagram
 */
export function parseMarshSiteDesigner(
  json: MarshSiteDesignerJSON,
  customObserverPoint?: { x: number; y: number; z: number }
): MarshParseResult {
  const unitScale = getUnitScale(json.Model.units);
  const northOffset = json.Location.northOffset || 0;

  // ── Separate solid blocks from analysis grids ──────────────────────
  const solidBlocks: MarshSolidBlock[] = [];
  const analysisGrids: MarshAnalysisGrid[] = [];

  json.Blocks.forEach((block, index) => {
    if (block.isGrid) {
      // Analysis grid — potential observation point
      const cx = ((block.min[0] + block.max[0]) / 2) * unitScale;
      const cy = ((block.min[1] + block.max[1]) / 2) * unitScale;
      const cz = ((block.min[2] + block.max[2]) / 2) * unitScale;

      analysisGrids.push({
        index,
        center: { x: cx, y: cy, z: cz },
        width: (block.width || (block.max[0] - block.min[0])) * unitScale,
        height: (block.height || (block.max[1] - block.min[1])) * unitScale,
        azimuth: block.azimuth || 0,
        altitude: block.altitude || 90,
      });
    } else if (block.isSolid && !block.hidden) {
      // Solid block — obstacle
      const minM = {
        x: block.min[0] * unitScale,
        y: block.min[1] * unitScale,
        z: block.min[2] * unitScale,
      };
      const maxM = {
        x: block.max[0] * unitScale,
        y: block.max[1] * unitScale,
        z: block.max[2] * unitScale,
      };

      solidBlocks.push({
        index,
        min: minM,
        max: maxM,
        color: rgbaToHex(block.color[0], block.color[1], block.color[2]),
        dimensions: {
          width: Math.abs(maxM.x - minM.x),
          height: Math.abs(maxM.y - minM.y),
          depth: Math.abs(maxM.z - minM.z),
        },
      });
    }
  });

  // ── Determine observation point ────────────────────────────────────
  let observationPoint: Point3D;

  if (customObserverPoint) {
    observationPoint = {
      x: customObserverPoint.x * unitScale,
      y: customObserverPoint.y * unitScale,
      z: customObserverPoint.z * unitScale,
    };
  } else if (analysisGrids.length > 0) {
    // Use the center of the first (primary) analysis grid
    const grid = analysisGrids[0];
    observationPoint = { ...grid.center };
  } else {
    // Fallback: centroid of all solid blocks at ground level
    if (solidBlocks.length > 0) {
      const cx = solidBlocks.reduce((s, b) => s + (b.min.x + b.max.x) / 2, 0) / solidBlocks.length;
      const cy = solidBlocks.reduce((s, b) => s + (b.min.y + b.max.y) / 2, 0) / solidBlocks.length;
      observationPoint = { x: cx, y: cy, z: 1.5 }; // 1.5m eye height
    } else {
      observationPoint = { x: 0, y: 0, z: 1.5 };
    }
  }

  // ── Convert each solid block to an angular obstacle polygon ────────
  const obstacles: ObstaclePolygon[] = [];

  for (const block of solidBlocks) {
    // Get all sample points on the block surface
    const corners = getBoxCorners(block.min, block.max);
    const midpoints = getBoxEdgeMidpoints(block.min, block.max);
    const allPoints = [...corners, ...midpoints];

    // Project to angular coordinates
    const angularPoints: AngularPoint[] = [];
    for (const pt of allPoints) {
      const angular = projectToAngular(pt, observationPoint, northOffset);
      if (angular && angular.altitude >= 0) {
        angularPoints.push(angular);
      }
    }

    // Need at least 3 points for a polygon
    if (angularPoints.length < 3) continue;

    // Compute convex hull to get the silhouette
    const hull = angularConvexHull(angularPoints);
    if (hull.length < 3) continue;

    // Determine a descriptive name based on block dimensions
    const maxDim = Math.max(block.dimensions.width, block.dimensions.height, block.dimensions.depth);
    const blockHeight = block.dimensions.depth; // Z is vertical
    let blockType = 'Obstáculo';
    if (blockHeight > 20) blockType = 'Edificio alto';
    else if (blockHeight > 8) blockType = 'Edificio';
    else if (blockHeight > 3) blockType = 'Estructura';
    else blockType = 'Muro';

    const distToObserver = Math.sqrt(
      Math.pow((block.min.x + block.max.x) / 2 - observationPoint.x, 2) +
      Math.pow((block.min.y + block.max.y) / 2 - observationPoint.y, 2)
    );

    obstacles.push({
      id: `marsh-${block.index}-${Date.now()}`,
      name: `${blockType} ${block.index + 1} (${blockHeight.toFixed(0)}m, ${distToObserver.toFixed(0)}m)`,
      color: block.color,
      vertices: hull.map(p => ({
        azimuth: Math.round(p.azimuth * 100) / 100,
        altitude: Math.round(p.altitude * 100) / 100,
      })),
      visible: true,
    });
  }

  return {
    location: json.Location,
    solidBlocks,
    analysisGrids,
    observationPoint,
    unitScale,
    obstacles,
  };
}

/**
 * Quick summary of a Site Designer file for display in the UI.
 */
export function getMarshFileSummary(json: MarshSiteDesignerJSON): {
  location: string;
  solidBlockCount: number;
  gridCount: number;
  units: string;
} {
  const unitNames: Record<number, string> = {
    0: 'metros',
    1: 'centímetros',
    2: 'milímetros',
    3: 'pies',
    4: 'pulgadas',
  };

  let solidCount = 0;
  let gridCount = 0;
  for (const block of json.Blocks) {
    if (block.isGrid) gridCount++;
    else if (block.isSolid) solidCount++;
  }

  return {
    location: `${json.Location.latitude.toFixed(4)}°, ${json.Location.longitude.toFixed(4)}°`,
    solidBlockCount: solidCount,
    gridCount,
    units: unitNames[json.Model.units] || 'desconocido',
  };
}
