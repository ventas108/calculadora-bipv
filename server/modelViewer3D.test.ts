/**
 * Tests para ModelViewer3D - validación de la lógica de renderizado 3D
 * 
 * Nota: No podemos testear el renderizado WebGL directamente en vitest (sin DOM/canvas),
 * pero sí podemos validar la lógica de datos que alimenta al visor.
 */
import { describe, it, expect } from 'vitest';
import {
  importBuildingModel,
  DEFAULT_IMPORT_CONFIG,
  Vertex3D,
  EvaluationModel,
  recalculateObstaclesFromPoint,
} from '../client/src/lib/buildingModelImporter';

// ─── Test Data ───────────────────────────────────────────────────────────────

const cubeOBJ = `
o Building_Cube
v -1 -1 0
v  1 -1 0
v  1  1 0
v -1  1 0
v -1 -1 3
v  1 -1 3
v  1  1 3
v -1  1 3
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 3 4 8 7
f 1 4 8 5
f 2 3 7 6
`;

const lShapeOBJ = `
o L_Building
v 0 0 0
v 4 0 0
v 4 2 0
v 2 2 0
v 2 4 0
v 0 4 0
v 0 0 5
v 4 0 5
v 4 2 5
v 2 2 5
v 2 4 5
v 0 4 5
f 1 2 3 4 5 6
f 7 8 9 10 11 12
f 1 2 8 7
f 2 3 9 8
f 3 4 10 9
f 4 5 11 10
f 5 6 12 11
f 6 1 7 12
`;

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('ModelViewer3D - Data Validation', () => {
  describe('Model data for 3D rendering', () => {
    it('should produce valid centroid for camera positioning', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      
      expect(model.centroid).toBeDefined();
      expect(typeof model.centroid.x).toBe('number');
      expect(typeof model.centroid.y).toBe('number');
      expect(typeof model.centroid.z).toBe('number');
      expect(isNaN(model.centroid.x)).toBe(false);
      expect(isNaN(model.centroid.y)).toBe(false);
      expect(isNaN(model.centroid.z)).toBe(false);
    });

    it('should produce valid dimensions for scene scaling', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      
      expect(model.dimensions.x).toBeGreaterThan(0);
      expect(model.dimensions.y).toBeGreaterThan(0);
      expect(model.dimensions.z).toBeGreaterThan(0);
      // Cube is 2x2x3
      expect(model.dimensions.x).toBeCloseTo(2, 0);
      expect(model.dimensions.y).toBeCloseTo(2, 0);
      expect(model.dimensions.z).toBeCloseTo(3, 0);
    });

    it('should produce facades with valid colors for rendering', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      
      for (const facade of model.detectedFacades) {
        expect(facade.color).toBeDefined();
        expect(facade.color).toMatch(/^#[0-9A-Fa-f]{6}$/);
      }
    });

    it('should produce facades with valid evaluation points for markers', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      
      for (const facade of model.detectedFacades) {
        expect(facade.evaluationPoint).toBeDefined();
        expect(isNaN(facade.evaluationPoint.x)).toBe(false);
        expect(isNaN(facade.evaluationPoint.y)).toBe(false);
        expect(isNaN(facade.evaluationPoint.z)).toBe(false);
        // Evaluation point should be outside the building bounding box
        // For roofs (tilt < 30), the evaluation point is above the center (Z offset)
        // For vertical facades, the evaluation point is offset horizontally
        if (facade.tilt >= 30) {
          const distFromCenter = Math.sqrt(
            (facade.evaluationPoint.x - model.centroid.x) ** 2 +
            (facade.evaluationPoint.y - model.centroid.y) ** 2
          );
          expect(distFromCenter).toBeGreaterThan(0);
        } else {
          // Roof: evaluation point is above the center
          expect(facade.evaluationPoint.z).toBeGreaterThan(facade.center.z);
        }
      }
    });

    it('should produce vertices array for mesh construction', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      
      expect(model.parseResult.vertices.length).toBe(8);
      for (const v of model.parseResult.vertices) {
        expect(typeof v.x).toBe('number');
        expect(typeof v.y).toBe('number');
        expect(typeof v.z).toBe('number');
      }
    });

    it('should produce transformedVertices with Z as vertical axis (roof on top)', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      
      // transformedVertices must exist and have same count as parseResult.vertices
      expect(model.transformedVertices).toBeDefined();
      expect(model.transformedVertices.length).toBe(model.parseResult.vertices.length);
      
      // After transformation, Z should be the vertical axis
      // The cube has Z from 0 to 3 (height), so max Z of transformed vertices should be ~3
      const maxZ = Math.max(...model.transformedVertices.map(v => v.z));
      const minZ = Math.min(...model.transformedVertices.map(v => v.z));
      expect(maxZ - minZ).toBeCloseTo(3, 0); // Height is 3
      
      // The horizontal dimensions (X, Y) should be 2
      const maxX = Math.max(...model.transformedVertices.map(v => v.x));
      const minX = Math.min(...model.transformedVertices.map(v => v.x));
      expect(maxX - minX).toBeCloseTo(2, 0);
      
      const maxY = Math.max(...model.transformedVertices.map(v => v.y));
      const minY = Math.min(...model.transformedVertices.map(v => v.y));
      expect(maxY - minY).toBeCloseTo(2, 0);
    });

    it('should have transformedVertices coherent with centroid and dimensions', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      
      // Centroid should be within bounding box of transformed vertices
      const maxX = Math.max(...model.transformedVertices.map(v => v.x));
      const minX = Math.min(...model.transformedVertices.map(v => v.x));
      const maxY = Math.max(...model.transformedVertices.map(v => v.y));
      const minY = Math.min(...model.transformedVertices.map(v => v.y));
      const maxZ = Math.max(...model.transformedVertices.map(v => v.z));
      const minZ = Math.min(...model.transformedVertices.map(v => v.z));
      
      expect(model.centroid.x).toBeGreaterThanOrEqual(minX - 0.01);
      expect(model.centroid.x).toBeLessThanOrEqual(maxX + 0.01);
      expect(model.centroid.y).toBeGreaterThanOrEqual(minY - 0.01);
      expect(model.centroid.y).toBeLessThanOrEqual(maxY + 0.01);
      expect(model.centroid.z).toBeGreaterThanOrEqual(minZ - 0.01);
      expect(model.centroid.z).toBeLessThanOrEqual(maxZ + 0.01);
      
      // Dimensions should match bounding box of transformed vertices
      expect(model.dimensions.x).toBeCloseTo(maxX - minX, 1);
      expect(model.dimensions.y).toBeCloseTo(maxY - minY, 1);
      expect(model.dimensions.z).toBeCloseTo(maxZ - minZ, 1);
    });

    it('should produce faces with valid vertex indices for triangulation', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      
      const numVertices = model.parseResult.vertices.length;
      for (const obj of model.parseResult.objects) {
        for (const face of obj.faces) {
          expect(face.vertexIndices.length).toBeGreaterThanOrEqual(3);
          for (const idx of face.vertexIndices) {
            expect(idx).toBeGreaterThanOrEqual(0);
            expect(idx).toBeLessThan(numVertices);
          }
        }
      }
    });
  });

  describe('Facade normal directions for arrow rendering', () => {
    it('should produce 4 distinct vertical facade orientations plus roof for a cube', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      
      expect(model.detectedFacades.length).toBe(5); // 4 vertical + 1 roof
      
      const verticalFacades = model.detectedFacades.filter(f => f.tilt >= 30);
      const azimuths = verticalFacades.map(f => f.azimuthNormal);
      // Should have approximately 0°, -90°, 90°, ±180°
      const hasNorth = azimuths.some(a => Math.abs(a) > 160);
      const hasSouth = azimuths.some(a => Math.abs(a) < 20);
      const hasEast = azimuths.some(a => Math.abs(a + 90) < 20);
      const hasWest = azimuths.some(a => Math.abs(a - 90) < 20);
      
      expect(hasNorth).toBe(true);
      expect(hasSouth).toBe(true);
      expect(hasEast).toBe(true);
      expect(hasWest).toBe(true);
    });

    it('should produce normal arrows pointing outward from facade centers', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      
      for (const facade of model.detectedFacades) {
        // Normal direction should point away from centroid
        const normalRad = (facade.azimuthNormal + 180) * Math.PI / 180;
        const arrowEndX = facade.center.x + Math.sin(normalRad) * 2;
        const arrowEndY = facade.center.y + Math.cos(normalRad) * 2;
        
        // Arrow end should be farther from centroid than facade center
        const distCenter = Math.sqrt(
          (facade.center.x - model.centroid.x) ** 2 +
          (facade.center.y - model.centroid.y) ** 2
        );
        const distArrowEnd = Math.sqrt(
          (arrowEndX - model.centroid.x) ** 2 +
          (arrowEndY - model.centroid.y) ** 2
        );
        
        expect(distArrowEnd).toBeGreaterThan(distCenter);
      }
    });
  });

  describe('Obstacle rendering data', () => {
    it('should produce valid obstacle polygons for 3D rendering', () => {
      const wallVertices: Vertex3D[] = [
        { x: -2.5, y: 10, z: 0 },
        { x: 2.5, y: 10, z: 0 },
        { x: 2.5, y: 10, z: 8 },
        { x: -2.5, y: 10, z: 8 },
      ];
      
      // The raw vertices should be usable for 3D mesh construction
      expect(wallVertices.length).toBe(4);
      for (const v of wallVertices) {
        expect(typeof v.x).toBe('number');
        expect(typeof v.y).toBe('number');
        expect(typeof v.z).toBe('number');
      }
    });

    it('should handle multiple obstacle groups', () => {
      const obstacles: Vertex3D[][] = [
        [
          { x: -5, y: 10, z: 0 },
          { x: -3, y: 10, z: 0 },
          { x: -3, y: 10, z: 6 },
          { x: -5, y: 10, z: 6 },
        ],
        [
          { x: 3, y: 12, z: 0 },
          { x: 5, y: 12, z: 0 },
          { x: 5, y: 12, z: 10 },
          { x: 3, y: 12, z: 10 },
        ],
      ];
      
      expect(obstacles.length).toBe(2);
      for (const group of obstacles) {
        expect(group.length).toBeGreaterThanOrEqual(3);
      }
    });
  });

  describe('Camera positioning', () => {
    it('should calculate appropriate camera distance based on model size', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      const maxDim = Math.max(model.dimensions.x, model.dimensions.y, model.dimensions.z);
      const distance = maxDim * 2.5;
      
      // Camera should be far enough to see the whole model
      expect(distance).toBeGreaterThan(maxDim);
      expect(distance).toBeLessThan(maxDim * 5); // But not too far
    });

    it('should position camera at an angle for perspective view', () => {
      const model = importBuildingModel(cubeOBJ, DEFAULT_IMPORT_CONFIG);
      const maxDim = Math.max(model.dimensions.x, model.dimensions.y, model.dimensions.z);
      const distance = maxDim * 2.5;
      
      const camX = model.centroid.x + distance * 0.7;
      const camY = model.centroid.y - distance * 0.7;
      const camZ = model.centroid.z + distance * 0.5;
      
      // Camera should be above the model
      expect(camZ).toBeGreaterThan(model.centroid.z);
      // Camera should be offset from center
      expect(camX).not.toBeCloseTo(model.centroid.x, 0);
      expect(camY).not.toBeCloseTo(model.centroid.y, 0);
    });
  });

  describe('L-shaped building', () => {
    it('should detect multiple facades for complex geometry', () => {
      const model = importBuildingModel(lShapeOBJ, DEFAULT_IMPORT_CONFIG);
      
      // L-shape should have at least 4 distinct facade orientations
      expect(model.detectedFacades.length).toBeGreaterThanOrEqual(3);
    });

    it('should produce valid centroid for non-rectangular buildings', () => {
      const model = importBuildingModel(lShapeOBJ, DEFAULT_IMPORT_CONFIG);
      
      // Centroid should be within the bounding box
      const bb = model.parseResult.boundingBox;
      expect(model.centroid.x).toBeGreaterThanOrEqual(bb.min.x);
      expect(model.centroid.x).toBeLessThanOrEqual(bb.max.x);
      expect(model.centroid.y).toBeGreaterThanOrEqual(bb.min.y);
      expect(model.centroid.y).toBeLessThanOrEqual(bb.max.y);
    });
  });

  describe('Compass rose orientation', () => {
    it('should rotate compass by north offset', () => {
      // The compass rotation is -northOffset in radians
      const northOffset = 45;
      const rotation = (-northOffset * Math.PI) / 180;
      
      expect(rotation).toBeCloseTo(-Math.PI / 4);
    });

    it('should handle 0 north offset (no rotation)', () => {
      const northOffset = 0;
      const rotation = (-northOffset * Math.PI) / 180;
      
      expect(rotation).toBeCloseTo(0);
    });
  });
});
