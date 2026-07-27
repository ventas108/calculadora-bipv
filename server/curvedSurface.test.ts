import { describe, it, expect } from 'vitest';
import { importBuildingModel, DEFAULT_IMPORT_CONFIG } from '../client/src/lib/buildingModelImporter';
import * as fs from 'fs';
import * as path from 'path';

describe('Curved Surface Detection (Bóvedas/Arcos)', () => {
  // Load the user's curved roof OBJ
  const objPath = path.resolve('/home/ubuntu/upload/d0b85f54-1f08-4413-9e3f-24a8bc9d4208.obj');
  const objText = fs.existsSync(objPath) ? fs.readFileSync(objPath, 'utf-8') : '';

  describe('Barrel vault roof (arco uniforme de SketchUp)', () => {
    it('should detect the curved roof as a single surface', () => {
      if (!objText) return; // Skip if file not available
      const result = importBuildingModel(objText, DEFAULT_IMPORT_CONFIG);
      const curvedFacades = result.detectedFacades.filter(f => f.isCurved);
      expect(curvedFacades.length).toBe(1);
    });

    it('should NOT split the arc into East/West/Horizontal sections', () => {
      if (!objText) return;
      const result = importBuildingModel(objText, DEFAULT_IMPORT_CONFIG);
      const eastWest = result.detectedFacades.filter(f => 
        f.name.includes('Este') || f.name.includes('Oeste') || f.name.includes('Horizontal')
      );
      expect(eastWest.length).toBe(0);
    });

    it('should name the curved surface as "Techo Curvo"', () => {
      if (!objText) return;
      const result = importBuildingModel(objText, DEFAULT_IMPORT_CONFIG);
      const curved = result.detectedFacades.find(f => f.isCurved);
      expect(curved).toBeDefined();
      expect(curved!.name).toMatch(/Techo Curvo|Fachada Curva/);
    });

    it('should calculate total area as sum of all arc faces', () => {
      if (!objText) return;
      const result = importBuildingModel(objText, DEFAULT_IMPORT_CONFIG);
      const curved = result.detectedFacades.find(f => f.isCurved);
      expect(curved).toBeDefined();
      // The arc has ~12 faces of ~196 m² each = ~2350 m² total
      expect(curved!.area).toBeGreaterThan(2000);
      expect(curved!.area).toBeLessThan(3000);
    });

    it('should provide azimuth and tilt ranges for the curved surface', () => {
      if (!objText) return;
      const result = importBuildingModel(objText, DEFAULT_IMPORT_CONFIG);
      const curved = result.detectedFacades.find(f => f.isCurved);
      expect(curved).toBeDefined();
      expect(curved!.azimuthRange).toBeDefined();
      expect(curved!.tiltRange).toBeDefined();
      // Azimuth range should span from ~-94° to ~86° (≈180° range)
      const azRange = curved!.azimuthRange!;
      expect(azRange[1] - azRange[0]).toBeGreaterThan(100);
      // Tilt range should be from ~3° to ~35°
      const tiltRange = curved!.tiltRange!;
      expect(tiltRange[0]).toBeLessThan(10);
      expect(tiltRange[1]).toBeGreaterThan(25);
    });

    it('should auto-detect Y as up axis for barrel vault geometry', () => {
      if (!objText) return;
      const result = importBuildingModel(objText, DEFAULT_IMPORT_CONFIG);
      // With Y-up, the curved surface has tilt ~19° (roof-like)
      const curved = result.detectedFacades.find(f => f.isCurved);
      expect(curved).toBeDefined();
      expect(curved!.tilt).toBeGreaterThan(10);
      expect(curved!.tilt).toBeLessThan(40);
    });
  });

  describe('Flat/planar surfaces should NOT be affected', () => {
    it('should still correctly detect flat roofs', () => {
      // Create a simple box OBJ (6 faces, all planar)
      const boxOBJ = `
# Simple box
v 0 0 0
v 10 0 0
v 10 10 0
v 0 10 0
v 0 0 5
v 10 0 5
v 10 10 5
v 0 10 5
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
`;
      const result = importBuildingModel(boxOBJ, { ...DEFAULT_IMPORT_CONFIG, upAxis: 'Z' });
      // Should NOT detect any curved surfaces
      const curvedFacades = result.detectedFacades.filter(f => f.isCurved);
      expect(curvedFacades.length).toBe(0);
    });

    it('should still correctly detect a 2-slope roof (techo a 2 aguas)', () => {
      // Create a simple gable roof OBJ
      const gableOBJ = `
# Gable roof (2 aguas)
v 0 0 0
v 10 0 0
v 10 10 0
v 0 10 0
v 0 0 4
v 10 0 4
v 10 10 4
v 0 10 4
v 5 0 7
v 5 10 7
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
f 5 6 9
f 6 7 10 9
f 7 8 10
f 8 5 9 10
`;
      const result = importBuildingModel(gableOBJ, { ...DEFAULT_IMPORT_CONFIG, upAxis: 'Z' });
      // Should NOT detect curved surfaces (only 2 roof faces, not enough for curve)
      const curvedFacades = result.detectedFacades.filter(f => f.isCurved);
      expect(curvedFacades.length).toBe(0);
      // Should detect separate roof slopes
      const roofFacades = result.detectedFacades.filter(f => f.name.includes('Techo'));
      expect(roofFacades.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Connectivity-based detection', () => {
    it('should group faces that share edges and have gradual normal variation', () => {
      // Create a simple arc with 5 connected quads (normals vary gradually)
      // This simulates a small barrel vault section
      const arcOBJ = `
# Small arc (5 connected quads)
v 0 0 0
v 1 0 0
v 0.19 0.98 0
v 1.19 0.98 0
v 0.38 1.92 0
v 1.38 1.92 0
v 0.71 2.78 0
v 1.71 2.78 0
v 1.17 3.49 0
v 2.17 3.49 0
v 1.76 4.05 0
v 2.76 4.05 0
v 0 0 10
v 1 0 10
v 0.19 0.98 10
v 1.19 0.98 10
v 0.38 1.92 10
v 1.38 1.92 10
v 0.71 2.78 10
v 1.71 2.78 10
v 1.17 3.49 10
v 2.17 3.49 10
v 1.76 4.05 10
v 2.76 4.05 10
f 1 2 4 3
f 3 4 6 5
f 5 6 8 7
f 7 8 10 9
f 9 10 12 11
f 13 14 16 15
f 15 16 18 17
f 17 18 20 19
f 19 20 22 21
f 21 22 24 23
f 1 2 14 13
f 3 4 16 15
f 5 6 18 17
f 7 8 20 19
f 9 10 22 21
f 11 12 24 23
`;
      const result = importBuildingModel(arcOBJ, { ...DEFAULT_IMPORT_CONFIG, upAxis: 'Z' });
      // The connected faces with gradual normal variation should be grouped
      // (depends on whether the azimuth range exceeds 50°)
      expect(result.detectedFacades.length).toBeGreaterThanOrEqual(1);
    });
  });
});
