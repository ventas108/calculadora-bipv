/**
 * Tests for gltfParser.ts
 * 
 * Tests the glTF/GLB parser including:
 * - GLB binary format parsing
 * - glTF JSON with embedded base64 buffers
 * - Node hierarchy and transformations
 * - Material extraction
 * - Validation
 * - Conversion to OBJParseResult format
 */

import { describe, it, expect } from 'vitest';
import { parseGLTF, validateGLTF, isGLB, getGLTFSummary, GLTFParseResult } from '../client/src/lib/gltfParser';

// ─── Helper: Create a minimal glTF JSON with embedded buffer ─────────────────

function createMinimalGLTF(): string {
  // A single triangle: vertices at (0,0,0), (1,0,0), (0,1,0)
  // Buffer contains: 3 floats for positions (9 floats = 36 bytes) + 3 uint16 indices (6 bytes) = 42 bytes
  // We need to pad to 4-byte alignment: 44 bytes total
  
  const positions = new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0]);
  const indices = new Uint16Array([0, 1, 2]);
  
  // Combine into a single buffer
  const totalBytes = positions.byteLength + indices.byteLength;
  const buffer = new ArrayBuffer(totalBytes);
  const posView = new Float32Array(buffer, 0, 9);
  const idxView = new Uint16Array(buffer, 36, 3);
  posView.set(positions);
  idxView.set(indices);
  
  // Convert to base64
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = btoa(binary);
  
  const gltf = {
    asset: { version: "2.0", generator: "Test" },
    scene: 0,
    scenes: [{ nodes: [0] }],
    nodes: [{ mesh: 0, name: "Triangle" }],
    meshes: [{
      name: "TriangleMesh",
      primitives: [{
        attributes: { POSITION: 0 },
        indices: 1,
        material: 0,
      }],
    }],
    accessors: [
      { bufferView: 0, componentType: 5126, count: 3, type: "VEC3", max: [1, 1, 0], min: [0, 0, 0] },
      { bufferView: 1, componentType: 5123, count: 3, type: "SCALAR" },
    ],
    bufferViews: [
      { buffer: 0, byteOffset: 0, byteLength: 36 },
      { buffer: 0, byteOffset: 36, byteLength: 6 },
    ],
    buffers: [{ uri: `data:application/octet-stream;base64,${base64}`, byteLength: totalBytes }],
    materials: [{
      name: "RedMaterial",
      pbrMetallicRoughness: {
        baseColorFactor: [1.0, 0.0, 0.0, 1.0],
        metallicFactor: 0.0,
        roughnessFactor: 1.0,
      },
    }],
  };
  
  return JSON.stringify(gltf);
}

// Create a glTF with a cube (8 vertices, 12 triangles)
function createCubeGLTF(): string {
  // Cube vertices: 8 corners of a unit cube centered at origin
  const positions = new Float32Array([
    -0.5, -0.5, -0.5,  // 0
     0.5, -0.5, -0.5,  // 1
     0.5,  0.5, -0.5,  // 2
    -0.5,  0.5, -0.5,  // 3
    -0.5, -0.5,  0.5,  // 4
     0.5, -0.5,  0.5,  // 5
     0.5,  0.5,  0.5,  // 6
    -0.5,  0.5,  0.5,  // 7
  ]);
  
  // 12 triangles (2 per face, 6 faces)
  const indices = new Uint16Array([
    0, 1, 2, 0, 2, 3, // front
    4, 6, 5, 4, 7, 6, // back
    0, 4, 5, 0, 5, 1, // bottom
    2, 6, 7, 2, 7, 3, // top
    0, 3, 7, 0, 7, 4, // left
    1, 5, 6, 1, 6, 2, // right
  ]);
  
  const posBytes = positions.byteLength; // 96
  const idxBytes = indices.byteLength;   // 72
  const totalBytes = posBytes + idxBytes; // 168
  
  const buffer = new ArrayBuffer(totalBytes);
  new Float32Array(buffer, 0, positions.length).set(positions);
  new Uint16Array(buffer, posBytes, indices.length).set(indices);
  
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = btoa(binary);
  
  const gltf = {
    asset: { version: "2.0", generator: "TestCube" },
    scene: 0,
    scenes: [{ nodes: [0] }],
    nodes: [{ mesh: 0, name: "Cube" }],
    meshes: [{
      name: "CubeMesh",
      primitives: [{
        attributes: { POSITION: 0 },
        indices: 1,
        material: 0,
      }],
    }],
    accessors: [
      { bufferView: 0, componentType: 5126, count: 8, type: "VEC3", max: [0.5, 0.5, 0.5], min: [-0.5, -0.5, -0.5] },
      { bufferView: 1, componentType: 5123, count: 36, type: "SCALAR" },
    ],
    bufferViews: [
      { buffer: 0, byteOffset: 0, byteLength: posBytes },
      { buffer: 0, byteOffset: posBytes, byteLength: idxBytes },
    ],
    buffers: [{ uri: `data:application/octet-stream;base64,${base64}`, byteLength: totalBytes }],
    materials: [{
      name: "BlueMaterial",
      pbrMetallicRoughness: {
        baseColorFactor: [0.0, 0.0, 1.0, 1.0],
      },
    }],
  };
  
  return JSON.stringify(gltf);
}

// Create a glTF with node hierarchy (parent with translation, child with mesh)
function createHierarchyGLTF(): string {
  // Single triangle at origin, but parent node translates by (10, 0, 0)
  const positions = new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0]);
  const indices = new Uint16Array([0, 1, 2]);
  
  const totalBytes = positions.byteLength + indices.byteLength;
  const buffer = new ArrayBuffer(totalBytes);
  new Float32Array(buffer, 0, 9).set(positions);
  new Uint16Array(buffer, 36, 3).set(indices);
  
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = btoa(binary);
  
  const gltf = {
    asset: { version: "2.0", generator: "TestHierarchy" },
    scene: 0,
    scenes: [{ nodes: [0] }],
    nodes: [
      { name: "Parent", translation: [10, 0, 0], children: [1] },
      { name: "Child", mesh: 0, scale: [2, 2, 2] },
    ],
    meshes: [{
      name: "TriangleMesh",
      primitives: [{
        attributes: { POSITION: 0 },
        indices: 1,
      }],
    }],
    accessors: [
      { bufferView: 0, componentType: 5126, count: 3, type: "VEC3" },
      { bufferView: 1, componentType: 5123, count: 3, type: "SCALAR" },
    ],
    bufferViews: [
      { buffer: 0, byteOffset: 0, byteLength: 36 },
      { buffer: 0, byteOffset: 36, byteLength: 6 },
    ],
    buffers: [{ uri: `data:application/octet-stream;base64,${base64}`, byteLength: totalBytes }],
  };
  
  return JSON.stringify(gltf);
}

// Create a minimal GLB binary
function createMinimalGLB(): ArrayBuffer {
  const gltfJson = JSON.stringify({
    asset: { version: "2.0", generator: "TestGLB" },
    scene: 0,
    scenes: [{ nodes: [0] }],
    nodes: [{ mesh: 0, name: "Triangle" }],
    meshes: [{
      name: "TriangleMesh",
      primitives: [{
        attributes: { POSITION: 0 },
        indices: 1,
      }],
    }],
    accessors: [
      { bufferView: 0, componentType: 5126, count: 3, type: "VEC3" },
      { bufferView: 1, componentType: 5123, count: 3, type: "SCALAR" },
    ],
    bufferViews: [
      { buffer: 0, byteOffset: 0, byteLength: 36 },
      { buffer: 0, byteOffset: 36, byteLength: 6 },
    ],
    buffers: [{ byteLength: 44 }],
  });
  
  // Pad JSON to 4-byte alignment
  const jsonEncoder = new TextEncoder();
  let jsonBytes = jsonEncoder.encode(gltfJson);
  const jsonPadding = (4 - (jsonBytes.length % 4)) % 4;
  const paddedJsonBytes = new Uint8Array(jsonBytes.length + jsonPadding);
  paddedJsonBytes.set(jsonBytes);
  for (let i = jsonBytes.length; i < paddedJsonBytes.length; i++) {
    paddedJsonBytes[i] = 0x20; // space padding for JSON
  }
  
  // Binary buffer: 3 vertices (36 bytes) + 3 indices (6 bytes) + 2 bytes padding = 44 bytes
  const binLength = 44;
  const binBuffer = new ArrayBuffer(binLength);
  const posView = new Float32Array(binBuffer, 0, 9);
  posView.set([0, 0, 0, 1, 0, 0, 0, 1, 0]);
  const idxView = new Uint16Array(binBuffer, 36, 3);
  idxView.set([0, 1, 2]);
  
  // GLB structure: header (12) + JSON chunk (8 + paddedJson) + BIN chunk (8 + bin)
  const totalLength = 12 + 8 + paddedJsonBytes.length + 8 + binLength;
  const glb = new ArrayBuffer(totalLength);
  const view = new DataView(glb);
  
  // Header
  view.setUint32(0, 0x46546C67, true); // magic "glTF"
  view.setUint32(4, 2, true);          // version
  view.setUint32(8, totalLength, true); // total length
  
  // JSON chunk
  let offset = 12;
  view.setUint32(offset, paddedJsonBytes.length, true); // chunk length
  view.setUint32(offset + 4, 0x4E4F534A, true);        // chunk type "JSON"
  offset += 8;
  new Uint8Array(glb, offset, paddedJsonBytes.length).set(paddedJsonBytes);
  offset += paddedJsonBytes.length;
  
  // BIN chunk
  view.setUint32(offset, binLength, true);       // chunk length
  view.setUint32(offset + 4, 0x004E4942, true); // chunk type "BIN\0"
  offset += 8;
  new Uint8Array(glb, offset, binLength).set(new Uint8Array(binBuffer));
  
  return glb;
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('gltfParser', () => {
  describe('validateGLTF', () => {
    it('should validate a correct glTF JSON string', () => {
      const gltf = createMinimalGLTF();
      expect(validateGLTF(gltf)).toBeNull();
    });

    it('should reject invalid JSON', () => {
      const result = validateGLTF('not json at all');
      expect(result).not.toBeNull();
      expect(result).toContain('Error al validar');
    });

    it('should reject JSON without asset.version', () => {
      const result = validateGLTF(JSON.stringify({ foo: 'bar' }));
      expect(result).not.toBeNull();
      expect(result).toContain('asset.version');
    });

    it('should reject glTF version 1', () => {
      const result = validateGLTF(JSON.stringify({ asset: { version: '1.0' } }));
      expect(result).not.toBeNull();
      expect(result).toContain('no soportada');
    });

    it('should validate a correct GLB ArrayBuffer', () => {
      const glb = createMinimalGLB();
      expect(validateGLTF(glb)).toBeNull();
    });

    it('should reject a too-small ArrayBuffer', () => {
      const result = validateGLTF(new ArrayBuffer(4));
      expect(result).not.toBeNull();
      expect(result).toContain('demasiado peque');
    });

    it('should reject an ArrayBuffer with wrong magic', () => {
      const buf = new ArrayBuffer(12);
      const view = new DataView(buf);
      view.setUint32(0, 0x12345678, true);
      const result = validateGLTF(buf);
      expect(result).not.toBeNull();
      expect(result).toContain('firma GLB');
    });
  });

  describe('isGLB', () => {
    it('should detect GLB magic number', () => {
      const glb = createMinimalGLB();
      expect(isGLB(glb)).toBe(true);
    });

    it('should return false for non-GLB buffer', () => {
      const buf = new ArrayBuffer(12);
      expect(isGLB(buf)).toBe(false);
    });

    it('should return false for too-small buffer', () => {
      const buf = new ArrayBuffer(2);
      expect(isGLB(buf)).toBe(false);
    });
  });

  describe('parseGLTF - glTF JSON', () => {
    it('should parse a minimal triangle glTF', () => {
      const gltf = createMinimalGLTF();
      const result = parseGLTF(gltf);

      expect(result.asset.version).toBe('2.0');
      expect(result.asset.generator).toBe('Test');
      expect(result.meshCount).toBe(1);
      expect(result.nodeCount).toBe(1);
      expect(result.objResult.totalFaces).toBe(1);
      expect(result.objResult.vertices.length).toBe(3);
      expect(result.objResult.objects.length).toBe(1);
      expect(result.objResult.objects[0].name).toBe('TriangleMesh');
    });

    it('should extract material info', () => {
      const gltf = createMinimalGLTF();
      const result = parseGLTF(gltf);

      expect(result.materials.length).toBe(1);
      expect(result.materials[0]).not.toBeNull();
      expect(result.materials[0]!.name).toBe('RedMaterial');
      expect(result.materials[0]!.baseColor).toEqual([1.0, 0.0, 0.0, 1.0]);
    });

    it('should compute correct bounding box for triangle', () => {
      const gltf = createMinimalGLTF();
      const result = parseGLTF(gltf);
      const bb = result.objResult.boundingBox;

      expect(bb.min.x).toBeCloseTo(0);
      expect(bb.min.y).toBeCloseTo(0);
      expect(bb.min.z).toBeCloseTo(0);
      expect(bb.max.x).toBeCloseTo(1);
      expect(bb.max.y).toBeCloseTo(1);
      expect(bb.max.z).toBeCloseTo(0);
    });

    it('should parse a cube with 12 triangles', () => {
      const gltf = createCubeGLTF();
      const result = parseGLTF(gltf);

      expect(result.objResult.totalFaces).toBe(12);
      expect(result.objResult.vertices.length).toBe(36); // 12 triangles * 3 vertices
      expect(result.objResult.objects.length).toBe(1);
      expect(result.materials[0]!.name).toBe('BlueMaterial');
      expect(result.materials[0]!.baseColor).toEqual([0.0, 0.0, 1.0, 1.0]);
    });

    it('should compute correct bounding box for cube', () => {
      const gltf = createCubeGLTF();
      const result = parseGLTF(gltf);
      const bb = result.objResult.boundingBox;

      expect(bb.min.x).toBeCloseTo(-0.5);
      expect(bb.min.y).toBeCloseTo(-0.5);
      expect(bb.min.z).toBeCloseTo(-0.5);
      expect(bb.max.x).toBeCloseTo(0.5);
      expect(bb.max.y).toBeCloseTo(0.5);
      expect(bb.max.z).toBeCloseTo(0.5);
      expect(bb.dimensions.x).toBeCloseTo(1);
      expect(bb.dimensions.y).toBeCloseTo(1);
      expect(bb.dimensions.z).toBeCloseTo(1);
    });

    it('should apply node hierarchy transformations', () => {
      const gltf = createHierarchyGLTF();
      const result = parseGLTF(gltf);

      // Parent translates by (10, 0, 0), child scales by 2
      // Original vertices: (0,0,0), (1,0,0), (0,1,0)
      // After scale: (0,0,0), (2,0,0), (0,2,0)
      // After translation: (10,0,0), (12,0,0), (10,2,0)
      const verts = result.objResult.vertices;
      expect(verts.length).toBe(3);

      // Sort by x then y for deterministic comparison
      const sorted = [...verts].sort((a, b) => a.x - b.x || a.y - b.y);
      expect(sorted[0].x).toBeCloseTo(10);
      expect(sorted[0].y).toBeCloseTo(0);
      expect(sorted[1].x).toBeCloseTo(10);
      expect(sorted[1].y).toBeCloseTo(2);
      expect(sorted[2].x).toBeCloseTo(12);
      expect(sorted[2].y).toBeCloseTo(0);
    });

    it('should handle null materials gracefully', () => {
      // glTF without materials section
      const positions = new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0]);
      const indices = new Uint16Array([0, 1, 2]);
      const totalBytes = positions.byteLength + indices.byteLength;
      const buffer = new ArrayBuffer(totalBytes);
      new Float32Array(buffer, 0, 9).set(positions);
      new Uint16Array(buffer, 36, 3).set(indices);
      const bytes = new Uint8Array(buffer);
      let binary = '';
      for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
      const base64 = btoa(binary);

      const gltf = JSON.stringify({
        asset: { version: "2.0", generator: "NoMat" },
        scene: 0,
        scenes: [{ nodes: [0] }],
        nodes: [{ mesh: 0 }],
        meshes: [{ primitives: [{ attributes: { POSITION: 0 }, indices: 1 }] }],
        accessors: [
          { bufferView: 0, componentType: 5126, count: 3, type: "VEC3" },
          { bufferView: 1, componentType: 5123, count: 3, type: "SCALAR" },
        ],
        bufferViews: [
          { buffer: 0, byteOffset: 0, byteLength: 36 },
          { buffer: 0, byteOffset: 36, byteLength: 6 },
        ],
        buffers: [{ uri: `data:application/octet-stream;base64,${base64}`, byteLength: totalBytes }],
      });

      const result = parseGLTF(gltf);
      expect(result.materials[0]).toBeNull();
      expect(result.objResult.totalFaces).toBe(1);
    });
  });

  describe('parseGLTF - GLB binary', () => {
    it('should parse a minimal GLB file', () => {
      const glb = createMinimalGLB();
      const result = parseGLTF(glb);

      expect(result.asset.version).toBe('2.0');
      expect(result.asset.generator).toBe('TestGLB');
      expect(result.objResult.totalFaces).toBe(1);
      expect(result.objResult.vertices.length).toBe(3);
    });

    it('should produce correct vertex positions from GLB', () => {
      const glb = createMinimalGLB();
      const result = parseGLTF(glb);
      const verts = result.objResult.vertices;

      expect(verts[0]).toEqual({ x: 0, y: 0, z: 0 });
      expect(verts[1]).toEqual({ x: 1, y: 0, z: 0 });
      expect(verts[2]).toEqual({ x: 0, y: 1, z: 0 });
    });
  });

  describe('getGLTFSummary', () => {
    it('should produce a readable summary', () => {
      const gltf = createMinimalGLTF();
      const result = parseGLTF(gltf);
      const summary = getGLTFSummary(result);

      expect(summary).toContain('glTF v2.0');
      expect(summary).toContain('Test');
      expect(summary).toContain('1 mesh');
      expect(summary).toContain('3 vértices');
      expect(summary).toContain('1 triángulo');
      expect(summary).toContain('RedMaterial');
    });

    it('should show dimensions for cube', () => {
      const gltf = createCubeGLTF();
      const result = parseGLTF(gltf);
      const summary = getGLTFSummary(result);

      expect(summary).toContain('1.00');
      expect(summary).toContain('Dimensiones');
    });
  });

  describe('OBJParseResult compatibility', () => {
    it('should produce face vertexIndices that reference valid vertices', () => {
      const gltf = createCubeGLTF();
      const result = parseGLTF(gltf);
      const { vertices, objects } = result.objResult;

      for (const obj of objects) {
        for (const face of obj.faces) {
          for (const idx of face.vertexIndices) {
            expect(idx).toBeGreaterThanOrEqual(0);
            expect(idx).toBeLessThan(vertices.length);
          }
        }
      }
    });

    it('should produce triangulated faces (3 vertices each)', () => {
      const gltf = createCubeGLTF();
      const result = parseGLTF(gltf);

      for (const obj of result.objResult.objects) {
        for (const face of obj.faces) {
          expect(face.vertexIndices.length).toBe(3);
        }
      }
    });
  });

  describe('Edge cases', () => {
    it('should handle empty scene gracefully', () => {
      const gltf = JSON.stringify({
        asset: { version: "2.0", generator: "Empty" },
        scene: 0,
        scenes: [{ nodes: [] }],
        nodes: [],
        meshes: [],
      });

      const result = parseGLTF(gltf);
      expect(result.objResult.totalFaces).toBe(0);
      expect(result.objResult.vertices.length).toBe(0);
      expect(result.objResult.objects.length).toBe(0);
    });

    it('should handle non-indexed geometry', () => {
      // Triangle without indices (non-indexed)
      const positions = new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0]);
      const totalBytes = positions.byteLength;
      const buffer = new ArrayBuffer(totalBytes);
      new Float32Array(buffer, 0, 9).set(positions);
      const bytes = new Uint8Array(buffer);
      let binary = '';
      for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
      const base64 = btoa(binary);

      const gltf = JSON.stringify({
        asset: { version: "2.0", generator: "NonIndexed" },
        scene: 0,
        scenes: [{ nodes: [0] }],
        nodes: [{ mesh: 0 }],
        meshes: [{ primitives: [{ attributes: { POSITION: 0 } }] }],
        accessors: [
          { bufferView: 0, componentType: 5126, count: 3, type: "VEC3" },
        ],
        bufferViews: [
          { buffer: 0, byteOffset: 0, byteLength: 36 },
        ],
        buffers: [{ uri: `data:application/octet-stream;base64,${base64}`, byteLength: totalBytes }],
      });

      const result = parseGLTF(gltf);
      expect(result.objResult.totalFaces).toBe(1);
      expect(result.objResult.vertices.length).toBe(3);
    });

    it('should throw for external buffer URIs', () => {
      const gltf = JSON.stringify({
        asset: { version: "2.0" },
        scene: 0,
        scenes: [{ nodes: [0] }],
        nodes: [{ mesh: 0 }],
        meshes: [{ primitives: [{ attributes: { POSITION: 0 } }] }],
        accessors: [{ bufferView: 0, componentType: 5126, count: 3, type: "VEC3" }],
        bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: 36 }],
        buffers: [{ uri: "external.bin", byteLength: 36 }],
      });

      expect(() => parseGLTF(gltf)).toThrow('External buffer files are not supported');
    });
  });
});
