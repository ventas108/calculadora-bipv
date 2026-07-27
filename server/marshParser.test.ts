import { describe, it, expect } from 'vitest';

// We test the parser logic by importing from the client lib
// Since these are pure functions, they work in any JS environment
import {
  validateMarshJSON,
  parseMarshSiteDesigner,
  getMarshFileSummary,
  MarshSiteDesignerJSON,
} from '../client/src/lib/marshSiteDesigner';

// Sample Andrew Marsh Site Designer JSON (simplified from real export)
const sampleMarshJSON: MarshSiteDesignerJSON = {
  Location: {
    latitude: 6.3356,
    longitude: -75.5502,
    timezone: -5,
    northOffset: 0,
  },
  Blocks: [
    {
      // Solid block (obstacle) - a building
      min: [-52000, -29000, 0],
      max: [-38000, -27000, 27000],
      color: [0.865, 0.634, 0.907, 1],
      majorAxis: 0,
      fixedSize: 0,
      isSolid: true,
      group: 0,
    },
    {
      // Solid block (obstacle) - shorter structure
      min: [22000, 14000, 0],
      max: [43000, 19000, 9000],
      color: [0.171, 0.361, 0.385, 1],
      majorAxis: 0,
      fixedSize: 0,
      isSolid: true,
      group: 0,
    },
    {
      // Analysis grid (not an obstacle)
      min: [-80000, -60000, 0],
      max: [0, 0, 50],
      color: [0.864, 0.518, 0.480, 1],
      majorAxis: 3,
      fixedSize: 50,
      isSolid: false,
      group: 0,
      isGrid: true,
      isPlanar: true,
      hidden: false,
      width: 80000,
      height: 60000,
      depth: 5000,
      azimuth: 0,
      altitude: 90,
      plane: [0, 0, 1, -25],
      preferredCellSize: [2000, 2000, 2000],
      surfaceIncidence: true,
      clipToBlocks: true,
      closedU: false,
      inset: false,
    },
  ],
  Model: {
    units: 2, // mm
  },
};

describe('Andrew Marsh Site Designer Parser', () => {
  describe('validateMarshJSON', () => {
    it('should validate a correct Site Designer JSON', () => {
      expect(validateMarshJSON(sampleMarshJSON)).toBe(true);
    });

    it('should reject null/undefined', () => {
      expect(validateMarshJSON(null)).toBe(false);
      expect(validateMarshJSON(undefined)).toBe(false);
    });

    it('should reject objects without Location', () => {
      expect(validateMarshJSON({ Blocks: [], Model: { units: 2 } })).toBe(false);
    });

    it('should reject objects without Blocks array', () => {
      expect(
        validateMarshJSON({
          Location: { latitude: 0, longitude: 0, timezone: 0, northOffset: 0 },
          Model: { units: 2 },
        })
      ).toBe(false);
    });

    it('should reject objects without Model', () => {
      expect(
        validateMarshJSON({
          Location: { latitude: 0, longitude: 0, timezone: 0, northOffset: 0 },
          Blocks: [],
        })
      ).toBe(false);
    });

    it('should reject non-numeric latitude/longitude', () => {
      expect(
        validateMarshJSON({
          Location: { latitude: 'abc', longitude: 0, timezone: 0, northOffset: 0 },
          Blocks: [],
          Model: { units: 2 },
        })
      ).toBe(false);
    });
  });

  describe('getMarshFileSummary', () => {
    it('should return correct summary', () => {
      const summary = getMarshFileSummary(sampleMarshJSON);
      expect(summary.solidBlockCount).toBe(2);
      expect(summary.gridCount).toBe(1);
      expect(summary.units).toBe('milímetros');
      expect(summary.location).toContain('6.3356');
      expect(summary.location).toContain('-75.5502');
    });

    it('should handle unknown units', () => {
      const modified = { ...sampleMarshJSON, Model: { units: 99 } };
      const summary = getMarshFileSummary(modified);
      expect(summary.units).toBe('desconocido');
    });
  });

  describe('parseMarshSiteDesigner', () => {
    it('should parse solid blocks correctly', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      expect(result.solidBlocks.length).toBe(2);
    });

    it('should detect analysis grids', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      expect(result.analysisGrids.length).toBe(1);
    });

    it('should convert mm to meters correctly', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      expect(result.unitScale).toBe(0.001);

      // First block: min[-52000,-29000,0] max[-38000,-27000,27000] in mm
      // Should be min[-52,-29,0] max[-38,-27,27] in meters
      const block = result.solidBlocks[0];
      expect(block.min.x).toBe(-52);
      expect(block.min.y).toBe(-29);
      expect(block.min.z).toBe(0);
      expect(block.max.x).toBe(-38);
      expect(block.max.y).toBe(-27);
      expect(block.max.z).toBe(27);
    });

    it('should calculate block dimensions correctly', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      const block = result.solidBlocks[0];
      // 14m x 2m x 27m
      expect(block.dimensions.width).toBe(14);
      expect(block.dimensions.height).toBe(2);
      expect(block.dimensions.depth).toBe(27);
    });

    it('should use analysis grid center as observation point', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      // Grid: min[-80000,-60000,0] max[0,0,50] → center(-40,-30,0.025)m
      expect(result.observationPoint.x).toBeCloseTo(-40, 0);
      expect(result.observationPoint.y).toBeCloseTo(-30, 0);
      expect(result.observationPoint.z).toBeCloseTo(0.025, 2);
    });

    it('should generate obstacle polygons for each solid block', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      expect(result.obstacles.length).toBe(2);
    });

    it('should generate obstacles with at least 3 vertices', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      for (const obs of result.obstacles) {
        expect(obs.vertices.length).toBeGreaterThanOrEqual(3);
      }
    });

    it('should generate obstacles with valid azimuth range', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      for (const obs of result.obstacles) {
        for (const v of obs.vertices) {
          expect(v.azimuth).toBeGreaterThanOrEqual(-180);
          expect(v.azimuth).toBeLessThanOrEqual(180);
        }
      }
    });

    it('should generate obstacles with valid altitude range', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      for (const obs of result.obstacles) {
        for (const v of obs.vertices) {
          expect(v.altitude).toBeGreaterThanOrEqual(0);
          expect(v.altitude).toBeLessThanOrEqual(90);
        }
      }
    });

    it('should assign hex colors from block RGBA', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      // First block color: [0.865, 0.634, 0.907, 1] → approx #dda2e8
      expect(result.obstacles[0].color).toMatch(/^#[0-9a-f]{6}$/);
    });

    it('should name obstacles based on height', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      // First block is 27m tall → "Edificio alto"
      expect(result.obstacles[0].name).toContain('Edificio alto');
      // Second block is 9m tall → "Edificio"
      expect(result.obstacles[1].name).toContain('Edificio');
    });

    it('should set all obstacles as visible', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      for (const obs of result.obstacles) {
        expect(obs.visible).toBe(true);
      }
    });

    it('should handle custom observer point', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON, { x: 0, y: 0, z: 1500 });
      // Custom point in mm → converted to meters: (0, 0, 1.5)
      expect(result.observationPoint.x).toBe(0);
      expect(result.observationPoint.y).toBe(0);
      expect(result.observationPoint.z).toBe(1.5);
    });

    it('should handle file with no analysis grids', () => {
      const noGrid: MarshSiteDesignerJSON = {
        ...sampleMarshJSON,
        Blocks: sampleMarshJSON.Blocks.filter(b => !b.isGrid),
      };
      const result = parseMarshSiteDesigner(noGrid);
      expect(result.analysisGrids.length).toBe(0);
      // Should fallback to centroid of blocks
      expect(result.observationPoint).toBeDefined();
    });

    it('should preserve location data', () => {
      const result = parseMarshSiteDesigner(sampleMarshJSON);
      expect(result.location.latitude).toBe(6.3356);
      expect(result.location.longitude).toBe(-75.5502);
      expect(result.location.timezone).toBe(-5);
    });
  });
});
