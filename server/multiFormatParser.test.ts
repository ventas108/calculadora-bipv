/**
 * Tests for multiFormatParser.ts
 * Verifies DXF, STL parsing and format detection utilities.
 */
import { describe, it, expect } from 'vitest';

// We test the pure functions that don't require Three.js (which needs a DOM)
// DXF and STL parsers are pure JS and can be tested directly.
// FBX, DAE, VRML, 3DS use Three.js loaders which require browser environment.

// Import the source directly for testing
import {
  detectFormat,
  isUnsupportedFormat,
  getConversionAdvice,
  getAcceptedExtensions,
  SUPPORTED_FORMATS,
  parseDXF,
  parseSTL,
} from '../client/src/lib/multiFormatParser';

describe('Format Detection', () => {
  it('detects OBJ format', () => {
    expect(detectFormat('model.obj')).toBe('obj');
    expect(detectFormat('Model.OBJ')).toBe('obj');
  });

  it('detects DXF format', () => {
    expect(detectFormat('building.dxf')).toBe('dxf');
    expect(detectFormat('TECHO.DXF')).toBe('dxf');
  });

  it('detects FBX format', () => {
    expect(detectFormat('model.fbx')).toBe('fbx');
  });

  it('detects STL format', () => {
    expect(detectFormat('part.stl')).toBe('stl');
  });

  it('detects DAE/Collada format', () => {
    expect(detectFormat('scene.dae')).toBe('dae');
  });

  it('detects VRML formats', () => {
    expect(detectFormat('model.wrl')).toBe('wrl');
    expect(detectFormat('scene.vrml')).toBe('vrml');
  });

  it('detects 3DS format', () => {
    expect(detectFormat('model.3ds')).toBe('3ds');
  });

  it('detects DWG format', () => {
    expect(detectFormat('drawing.dwg')).toBe('dwg');
  });

  it('detects XSI format', () => {
    expect(detectFormat('scene.xsi')).toBe('xsi');
  });

  it('returns null for unknown formats', () => {
    expect(detectFormat('file.txt')).toBeNull();
    expect(detectFormat('image.png')).toBeNull();
    expect(detectFormat('noextension')).toBeNull();
  });
});

describe('Unsupported Format Detection', () => {
  it('marks DWG as unsupported', () => {
    expect(isUnsupportedFormat('dwg')).toBe(true);
  });

  it('marks XSI as unsupported', () => {
    expect(isUnsupportedFormat('xsi')).toBe(true);
  });

  it('marks DXF as supported', () => {
    expect(isUnsupportedFormat('dxf')).toBe(false);
  });

  it('marks FBX as supported', () => {
    expect(isUnsupportedFormat('fbx')).toBe(false);
  });

  it('provides conversion advice for DWG', () => {
    const advice = getConversionAdvice('dwg');
    expect(advice).toContain('DXF');
    expect(advice).toContain('AutoCAD');
  });

  it('provides conversion advice for XSI', () => {
    const advice = getConversionAdvice('xsi');
    expect(advice).toContain('FBX');
    expect(advice).toContain('OBJ');
  });
});

describe('Accepted Extensions', () => {
  it('includes all supported formats', () => {
    const extensions = getAcceptedExtensions();
    expect(extensions).toContain('.obj');
    expect(extensions).toContain('.gltf');
    expect(extensions).toContain('.glb');
    expect(extensions).toContain('.dxf');
    expect(extensions).toContain('.fbx');
    expect(extensions).toContain('.stl');
    expect(extensions).toContain('.dae');
    expect(extensions).toContain('.wrl');
    expect(extensions).toContain('.3ds');
  });

  it('excludes unsupported formats', () => {
    const extensions = getAcceptedExtensions();
    expect(extensions).not.toContain('.dwg');
    expect(extensions).not.toContain('.xsi');
  });
});

describe('SUPPORTED_FORMATS metadata', () => {
  it('has correct count of formats', () => {
    expect(SUPPORTED_FORMATS.length).toBe(11);
  });

  it('DWG has conversion note', () => {
    const dwg = SUPPORTED_FORMATS.find(f => f.extension === '.dwg');
    expect(dwg).toBeDefined();
    expect(dwg!.supported).toBe(false);
    expect(dwg!.note).toContain('DXF');
  });

  it('DXF lists AutoCAD as software', () => {
    const dxf = SUPPORTED_FORMATS.find(f => f.extension === '.dxf');
    expect(dxf).toBeDefined();
    expect(dxf!.supported).toBe(true);
    expect(dxf!.software).toContain('AutoCAD');
  });
});

describe('DXF Parser', () => {
  it('parses a simple 3DFACE entity', () => {
    const dxfContent = `0
SECTION
2
ENTITIES
0
3DFACE
8
Layer1
10
0.0
20
0.0
30
0.0
11
10.0
21
0.0
31
0.0
12
10.0
22
10.0
32
0.0
13
0.0
23
10.0
33
0.0
0
ENDSEC
0
EOF
`;
    const result = parseDXF(dxfContent);
    expect(result.totalFaces).toBe(1);
    expect(result.objects.length).toBe(1);
    expect(result.objects[0].name).toBe('Layer1');
    expect(result.vertices.length).toBe(4);
    // Check bounding box
    expect(result.boundingBox.min.x).toBe(0);
    expect(result.boundingBox.max.x).toBe(10);
    expect(result.boundingBox.dimensions.x).toBe(10);
    expect(result.boundingBox.dimensions.y).toBe(10);
    expect(result.boundingBox.dimensions.z).toBe(0);
  });

  it('parses multiple 3DFACE entities on different layers', () => {
    const dxfContent = `0
SECTION
2
ENTITIES
0
3DFACE
8
Roof
10
0.0
20
0.0
30
5.0
11
10.0
21
0.0
31
5.0
12
5.0
22
5.0
32
8.0
13
5.0
23
5.0
33
8.0
0
3DFACE
8
Wall
10
0.0
20
0.0
30
0.0
11
10.0
21
0.0
31
0.0
12
10.0
22
0.0
32
5.0
13
0.0
23
0.0
33
5.0
0
ENDSEC
0
EOF
`;
    const result = parseDXF(dxfContent);
    expect(result.totalFaces).toBe(2);
    expect(result.objects.length).toBe(2);
    
    const roofObj = result.objects.find(o => o.name === 'Roof');
    const wallObj = result.objects.find(o => o.name === 'Wall');
    expect(roofObj).toBeDefined();
    expect(wallObj).toBeDefined();
    expect(roofObj!.faces.length).toBe(1);
    expect(wallObj!.faces.length).toBe(1);
  });

  it('handles triangular 3DFACE (3rd and 4th vertex same)', () => {
    const dxfContent = `0
SECTION
2
ENTITIES
0
3DFACE
8
default
10
0.0
20
0.0
30
0.0
11
5.0
21
0.0
31
0.0
12
2.5
22
4.0
32
0.0
13
2.5
23
4.0
33
0.0
0
ENDSEC
0
EOF
`;
    const result = parseDXF(dxfContent);
    expect(result.totalFaces).toBe(1);
    // Should be a triangle (3 indices) since 3rd and 4th vertex are the same
    expect(result.objects[0].faces[0].vertexIndices.length).toBe(3);
  });

  it('returns empty result for DXF with no 3D entities', () => {
    const dxfContent = `0
SECTION
2
HEADER
0
ENDSEC
0
SECTION
2
ENTITIES
0
LINE
8
default
10
0.0
20
0.0
11
10.0
21
10.0
0
ENDSEC
0
EOF
`;
    const result = parseDXF(dxfContent);
    // LINE entities don't produce faces
    expect(result.totalFaces).toBe(0);
  });

  it('parses a curved roof approximation (multiple 3DFACEs)', () => {
    // Simulate a curved surface as multiple triangular facets
    const faces: string[] = [];
    const numSegments = 12;
    const radius = 5;
    
    for (let i = 0; i < numSegments; i++) {
      const angle1 = (i / numSegments) * Math.PI;
      const angle2 = ((i + 1) / numSegments) * Math.PI;
      
      const x1 = radius * Math.cos(angle1);
      const z1 = radius * Math.sin(angle1);
      const x2 = radius * Math.cos(angle2);
      const z2 = radius * Math.sin(angle2);
      
      faces.push(`0
3DFACE
8
CurvedRoof
10
${x1.toFixed(4)}
20
0.0
30
${z1.toFixed(4)}
11
${x2.toFixed(4)}
21
0.0
31
${z2.toFixed(4)}
12
${x2.toFixed(4)}
22
10.0
32
${z2.toFixed(4)}
13
${x1.toFixed(4)}
23
10.0
33
${z1.toFixed(4)}`);
    }
    
    const dxfContent = `0
SECTION
2
ENTITIES
${faces.join('\n')}
0
ENDSEC
0
EOF
`;
    const result = parseDXF(dxfContent);
    expect(result.totalFaces).toBe(numSegments);
    expect(result.objects[0].name).toBe('CurvedRoof');
    expect(result.vertices.length).toBe(numSegments * 4);
  });
});

describe('STL Parser (ASCII)', () => {
  it('parses a simple ASCII STL triangle', () => {
    const stlContent = `solid SimpleTriangle
  facet normal 0 0 1
    outer loop
      vertex 0 0 0
      vertex 10 0 0
      vertex 5 10 0
    endloop
  endfacet
endsolid SimpleTriangle
`;
    const result = parseSTL(stlContent);
    expect(result.totalFaces).toBe(1);
    expect(result.vertices.length).toBe(3);
    expect(result.objects[0].name).toBe('SimpleTriangle');
    expect(result.boundingBox.dimensions.x).toBe(10);
    expect(result.boundingBox.dimensions.y).toBe(10);
    expect(result.boundingBox.dimensions.z).toBe(0);
  });

  it('parses multiple triangles (a quad as 2 triangles)', () => {
    const stlContent = `solid Quad
  facet normal 0 0 1
    outer loop
      vertex 0 0 0
      vertex 10 0 0
      vertex 10 10 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 0 0 0
      vertex 10 10 0
      vertex 0 10 0
    endloop
  endfacet
endsolid Quad
`;
    const result = parseSTL(stlContent);
    expect(result.totalFaces).toBe(2);
    expect(result.vertices.length).toBe(6);
  });

  it('parses a 3D box (12 triangles)', () => {
    // A box has 6 faces, each face = 2 triangles = 12 total
    const stlContent = `solid Box
  facet normal 0 0 -1
    outer loop
      vertex 0 0 0
      vertex 1 0 0
      vertex 1 1 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 0 0 0
      vertex 1 1 0
      vertex 0 1 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 0 0 1
      vertex 1 1 1
      vertex 1 0 1
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 0 0 1
      vertex 0 1 1
      vertex 1 1 1
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 0 0 0
      vertex 1 0 1
      vertex 1 0 0
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 0 0 0
      vertex 0 0 1
      vertex 1 0 1
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 0 1 0
      vertex 1 1 0
      vertex 1 1 1
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 0 1 0
      vertex 1 1 1
      vertex 0 1 1
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 0 0 0
      vertex 0 1 0
      vertex 0 1 1
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 0 0 0
      vertex 0 1 1
      vertex 0 0 1
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 1 0 0
      vertex 1 0 1
      vertex 1 1 1
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 1 0 0
      vertex 1 1 1
      vertex 1 1 0
    endloop
  endfacet
endsolid Box
`;
    const result = parseSTL(stlContent);
    expect(result.totalFaces).toBe(12);
    expect(result.vertices.length).toBe(36); // 12 triangles × 3 vertices
    expect(result.boundingBox.dimensions.x).toBeCloseTo(1);
    expect(result.boundingBox.dimensions.y).toBeCloseTo(1);
    expect(result.boundingBox.dimensions.z).toBeCloseTo(1);
  });
});

describe('STL Parser (Binary)', () => {
  it('parses a binary STL with 1 triangle', () => {
    // Create a minimal binary STL
    // 80 bytes header + 4 bytes triangle count + 50 bytes per triangle
    const buffer = new ArrayBuffer(84 + 50);
    const view = new DataView(buffer);
    
    // Header (80 bytes) - leave as zeros
    // Triangle count
    view.setUint32(80, 1, true);
    
    // Triangle data (50 bytes):
    // Normal (12 bytes)
    view.setFloat32(84, 0, true);  // nx
    view.setFloat32(88, 0, true);  // ny
    view.setFloat32(92, 1, true);  // nz
    
    // Vertex 1 (12 bytes)
    view.setFloat32(96, 0, true);   // x
    view.setFloat32(100, 0, true);  // y
    view.setFloat32(104, 0, true);  // z
    
    // Vertex 2 (12 bytes)
    view.setFloat32(108, 10, true); // x
    view.setFloat32(112, 0, true);  // y
    view.setFloat32(116, 0, true);  // z
    
    // Vertex 3 (12 bytes)
    view.setFloat32(120, 5, true);  // x
    view.setFloat32(124, 10, true); // y
    view.setFloat32(128, 0, true);  // z
    
    // Attribute byte count (2 bytes)
    view.setUint16(132, 0, true);
    
    const result = parseSTL(buffer);
    expect(result.totalFaces).toBe(1);
    expect(result.vertices.length).toBe(3);
    expect(result.vertices[0]).toEqual({ x: 0, y: 0, z: 0 });
    expect(result.vertices[1]).toEqual({ x: 10, y: 0, z: 0 });
    expect(result.vertices[2]).toEqual({ x: 5, y: 10, z: 0 });
  });

  it('parses a binary STL with multiple triangles', () => {
    const numTriangles = 4;
    const buffer = new ArrayBuffer(84 + numTriangles * 50);
    const view = new DataView(buffer);
    
    view.setUint32(80, numTriangles, true);
    
    for (let i = 0; i < numTriangles; i++) {
      const offset = 84 + i * 50;
      // Normal
      view.setFloat32(offset, 0, true);
      view.setFloat32(offset + 4, 0, true);
      view.setFloat32(offset + 8, 1, true);
      // Vertices
      view.setFloat32(offset + 12, i, true);
      view.setFloat32(offset + 16, 0, true);
      view.setFloat32(offset + 20, 0, true);
      view.setFloat32(offset + 24, i + 1, true);
      view.setFloat32(offset + 28, 0, true);
      view.setFloat32(offset + 32, 0, true);
      view.setFloat32(offset + 36, i + 0.5, true);
      view.setFloat32(offset + 40, 1, true);
      view.setFloat32(offset + 44, 0, true);
      // Attribute
      view.setUint16(offset + 48, 0, true);
    }
    
    const result = parseSTL(buffer);
    expect(result.totalFaces).toBe(numTriangles);
    expect(result.vertices.length).toBe(numTriangles * 3);
  });
});
