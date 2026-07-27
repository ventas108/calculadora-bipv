/**
 * Integration test: DXF curved roof detection
 * 
 * Generates a realistic DXF file representing a barrel vault roof (bóveda de cañón)
 * similar to what AutoCAD/Revit would export, then verifies that:
 * 1. The DXF parser correctly extracts all 3DFACE entities
 * 2. The building model importer detects it as a single curved surface
 * 3. The curved surface has correct aggregate properties
 */
import { describe, it, expect } from 'vitest';
import { parseDXF } from '../client/src/lib/multiFormatParser';
import { importBuildingModel, DEFAULT_IMPORT_CONFIG } from '../client/src/lib/buildingModelImporter';

/**
 * Generate a DXF file representing a barrel vault (bóveda de cañón)
 * The vault spans from -5m to +5m in X, 0 to 20m in Y (length),
 * with the arc going from 0° to 180° in the XZ plane.
 */
function generateBarrelVaultDXF(numSegments: number = 16): string {
  const radius = 5; // 5m radius
  const length = 20; // 20m long
  const lines: string[] = [];
  
  // DXF header
  lines.push('0', 'SECTION', '2', 'HEADER', '0', 'ENDSEC');
  
  // Entities section
  lines.push('0', 'SECTION', '2', 'ENTITIES');
  
  for (let i = 0; i < numSegments; i++) {
    const angle1 = (i / numSegments) * Math.PI;
    const angle2 = ((i + 1) / numSegments) * Math.PI;
    
    const x1 = radius * Math.cos(angle1);
    const z1 = radius * Math.sin(angle1);
    const x2 = radius * Math.cos(angle2);
    const z2 = radius * Math.sin(angle2);
    
    // Front face (Y=0)
    lines.push('0', '3DFACE');
    lines.push('8', 'BarrelVault');
    // Vertex 1 (10, 20, 30)
    lines.push('10', x1.toFixed(6));
    lines.push('20', '0.000000');
    lines.push('30', z1.toFixed(6));
    // Vertex 2 (11, 21, 31)
    lines.push('11', x2.toFixed(6));
    lines.push('21', '0.000000');
    lines.push('31', z2.toFixed(6));
    // Vertex 3 (12, 22, 32)
    lines.push('12', x2.toFixed(6));
    lines.push('22', length.toFixed(6));
    lines.push('32', z2.toFixed(6));
    // Vertex 4 (13, 23, 33)
    lines.push('13', x1.toFixed(6));
    lines.push('23', length.toFixed(6));
    lines.push('33', z1.toFixed(6));
  }
  
  lines.push('0', 'ENDSEC');
  lines.push('0', 'EOF');
  
  return lines.join('\n');
}

/**
 * Generate a DXF file representing a dome (cúpula hemisférica)
 * Similar to what Rhino or Revit would export for a dome structure.
 */
function generateDomeDXF(latSegments: number = 8, lonSegments: number = 12): string {
  const radius = 5;
  const lines: string[] = [];
  
  lines.push('0', 'SECTION', '2', 'HEADER', '0', 'ENDSEC');
  lines.push('0', 'SECTION', '2', 'ENTITIES');
  
  for (let lat = 0; lat < latSegments; lat++) {
    const theta1 = (lat / latSegments) * (Math.PI / 2);
    const theta2 = ((lat + 1) / latSegments) * (Math.PI / 2);
    
    for (let lon = 0; lon < lonSegments; lon++) {
      const phi1 = (lon / lonSegments) * 2 * Math.PI;
      const phi2 = ((lon + 1) / lonSegments) * 2 * Math.PI;
      
      // Four corners of the quad on the sphere
      const v1 = {
        x: radius * Math.cos(theta1) * Math.cos(phi1),
        y: radius * Math.cos(theta1) * Math.sin(phi1),
        z: radius * Math.sin(theta1),
      };
      const v2 = {
        x: radius * Math.cos(theta1) * Math.cos(phi2),
        y: radius * Math.cos(theta1) * Math.sin(phi2),
        z: radius * Math.sin(theta1),
      };
      const v3 = {
        x: radius * Math.cos(theta2) * Math.cos(phi2),
        y: radius * Math.cos(theta2) * Math.sin(phi2),
        z: radius * Math.sin(theta2),
      };
      const v4 = {
        x: radius * Math.cos(theta2) * Math.cos(phi1),
        y: radius * Math.cos(theta2) * Math.sin(phi1),
        z: radius * Math.sin(theta2),
      };
      
      lines.push('0', '3DFACE');
      lines.push('8', 'Dome');
      lines.push('10', v1.x.toFixed(6), '20', v1.y.toFixed(6), '30', v1.z.toFixed(6));
      lines.push('11', v2.x.toFixed(6), '21', v2.y.toFixed(6), '31', v2.z.toFixed(6));
      lines.push('12', v3.x.toFixed(6), '22', v3.y.toFixed(6), '32', v3.z.toFixed(6));
      lines.push('13', v4.x.toFixed(6), '23', v4.y.toFixed(6), '33', v4.z.toFixed(6));
    }
  }
  
  lines.push('0', 'ENDSEC');
  lines.push('0', 'EOF');
  
  return lines.join('\n');
}

describe('DXF Barrel Vault (Bóveda de Cañón)', () => {
  const dxfContent = generateBarrelVaultDXF(16);
  
  it('DXF parser extracts all 16 quad faces', () => {
    const result = parseDXF(dxfContent);
    expect(result.totalFaces).toBe(16);
    expect(result.objects.length).toBe(1);
    expect(result.objects[0].name).toBe('BarrelVault');
  });
  
  it('bounding box matches expected vault dimensions', () => {
    const result = parseDXF(dxfContent);
    // X: -5 to +5 (diameter 10m)
    expect(result.boundingBox.dimensions.x).toBeCloseTo(10, 0);
    // Y: 0 to 20 (length 20m)
    expect(result.boundingBox.dimensions.y).toBeCloseTo(20, 0);
    // Z: 0 to 5 (radius, top of vault)
    expect(result.boundingBox.dimensions.z).toBeCloseTo(5, 0);
  });
  
  it('building model importer detects as curved surface', () => {
    const result = parseDXF(dxfContent);
    const config = { ...DEFAULT_IMPORT_CONFIG, upAxis: 'Z' as const };
    const model = importBuildingModel(result, config);
    
    // Should detect at least one curved surface
    const curvedFacades = model.detectedFacades.filter(f => f.isCurved);
    expect(curvedFacades.length).toBeGreaterThan(0);
    
    // The curved surface should contain most of the faces
    const totalCurvedFaces = curvedFacades.reduce((sum, f) => sum + (f.faceCount || 0), 0);
    expect(totalCurvedFaces).toBeGreaterThanOrEqual(12); // At least 12 of 16 faces
  });
  
  it('curved surface has reasonable tilt range', () => {
    const result = parseDXF(dxfContent);
    const config = { ...DEFAULT_IMPORT_CONFIG, upAxis: 'Z' as const };
    const model = importBuildingModel(result, config);
    
    const curvedFacade = model.detectedFacades.find(f => f.isCurved);
    expect(curvedFacade).toBeDefined();
    
    if (curvedFacade) {
      // A barrel vault has tilts ranging from near-vertical (sides) to near-horizontal (top)
      expect(curvedFacade.tiltRange).toBeDefined();
      if (curvedFacade.tiltRange) {
        expect(curvedFacade.tiltRange[1] - curvedFacade.tiltRange[0]).toBeGreaterThan(30);
      }
    }
  });
  
  it('curved surface name contains "Curvo" or "Cúpula" or "Bóveda"', () => {
    const result = parseDXF(dxfContent);
    const config = { ...DEFAULT_IMPORT_CONFIG, upAxis: 'Z' as const };
    const model = importBuildingModel(result, config);
    
    const curvedFacade = model.detectedFacades.find(f => f.isCurved);
    expect(curvedFacade).toBeDefined();
    if (curvedFacade) {
      expect(curvedFacade.name).toMatch(/Curv|Cúpula|Bóveda/i);
    }
  });
});

describe('DXF Dome (Cúpula Hemisférica)', () => {
  const dxfContent = generateDomeDXF(6, 10);
  
  it('DXF parser extracts all dome faces', () => {
    const result = parseDXF(dxfContent);
    // 6 latitude × 10 longitude = 60 faces
    expect(result.totalFaces).toBe(60);
    expect(result.objects[0].name).toBe('Dome');
  });
  
  it('building model importer detects dome as curved surface', () => {
    const result = parseDXF(dxfContent);
    const config = { ...DEFAULT_IMPORT_CONFIG, upAxis: 'Z' as const };
    const model = importBuildingModel(result, config);
    
    const curvedFacades = model.detectedFacades.filter(f => f.isCurved);
    expect(curvedFacades.length).toBeGreaterThan(0);
    
    // Dome should be detected as curved with wide azimuth range
    const mainCurved = curvedFacades.reduce((a, b) => a.area > b.area ? a : b);
    expect(mainCurved.azimuthRange).toBeDefined();
    if (mainCurved.azimuthRange) {
      // A dome spans nearly 360° of azimuth
      const range = mainCurved.azimuthRange[1] - mainCurved.azimuthRange[0];
      expect(range).toBeGreaterThan(90);
    }
  });
});

describe('DXF with mixed flat and curved surfaces', () => {
  it('correctly separates flat walls from curved roof', () => {
    // Generate a building with flat walls and a barrel vault roof
    const lines: string[] = [];
    lines.push('0', 'SECTION', '2', 'HEADER', '0', 'ENDSEC');
    lines.push('0', 'SECTION', '2', 'ENTITIES');
    
    // Flat floor (Z=0)
    lines.push('0', '3DFACE', '8', 'Floor');
    lines.push('10', '-5', '20', '0', '30', '0');
    lines.push('11', '5', '21', '0', '31', '0');
    lines.push('12', '5', '22', '20', '32', '0');
    lines.push('13', '-5', '23', '20', '33', '0');
    
    // Curved roof (barrel vault, 8 segments)
    const radius = 5;
    const numSeg = 8;
    for (let i = 0; i < numSeg; i++) {
      const a1 = (i / numSeg) * Math.PI;
      const a2 = ((i + 1) / numSeg) * Math.PI;
      const x1 = radius * Math.cos(a1);
      const z1 = radius * Math.sin(a1);
      const x2 = radius * Math.cos(a2);
      const z2 = radius * Math.sin(a2);
      
      lines.push('0', '3DFACE', '8', 'Roof');
      lines.push('10', x1.toFixed(4), '20', '0', '30', z1.toFixed(4));
      lines.push('11', x2.toFixed(4), '21', '0', '31', z2.toFixed(4));
      lines.push('12', x2.toFixed(4), '22', '20', '32', z2.toFixed(4));
      lines.push('13', x1.toFixed(4), '23', '20', '33', z1.toFixed(4));
    }
    
    lines.push('0', 'ENDSEC', '0', 'EOF');
    
    const dxfContent = lines.join('\n');
    const result = parseDXF(dxfContent);
    
    // Total: 1 floor + 8 roof segments = 9 faces
    expect(result.totalFaces).toBe(9);
    expect(result.objects.length).toBe(2); // Floor and Roof layers
    
    // Import and check detection
    const config = { ...DEFAULT_IMPORT_CONFIG, upAxis: 'Z' as const };
    const model = importBuildingModel(result, config);
    
    // Should have curved facade(s)
    const curvedFacades = model.detectedFacades.filter(f => f.isCurved);
    expect(curvedFacades.length).toBeGreaterThan(0);
    
    // The vault should be curved with multiple faces
    const vaultFacade = curvedFacades[0];
    expect(vaultFacade).toBeDefined();
    expect(vaultFacade.faceCount).toBeGreaterThanOrEqual(6); // Most of the 8 vault segments
  });
});
