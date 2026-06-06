/**
 * glTF/GLB Parser for Solar Shading Calculator
 *
 * Parses glTF 2.0 (.gltf) and GLB (.glb) files exported from Blender, SketchUp,
 * Rhino, Revit, and other 3D software. Converts the geometry into the same
 * OBJParseResult format used by the rest of the application, enabling seamless
 * integration with facade detection, obstacle projection, and the 3D viewer.
 *
 * Supports:
 * - GLB binary container (magic 0x46546C67 = "glTF")
 * - glTF JSON with embedded base64 buffers
 * - Multiple meshes, nodes, and scenes
 * - Node hierarchy with nested transformations (translation, rotation, scale, matrix)
 * - Indexed and non-indexed geometry
 * - Triangle primitives (mode 4, default)
 * - Triangle strip (mode 5) and triangle fan (mode 6)
 * - Material name and base color extraction
 *
 * Does NOT support (by design, for a shading calculator):
 * - External .bin buffer files (must be embedded or GLB)
 * - Morph targets / animations
 * - Skinning / joints
 * - Extensions (KHR_draco_mesh_compression, etc.)
 */

import { OBJParseResult } from './objParser';

// ─── glTF 2.0 Type Definitions (subset) ─────────────────────────────────────

interface GLTFAsset {
  version: string;
  generator?: string;
  minVersion?: string;
}

interface GLTFBuffer {
  uri?: string;
  byteLength: number;
}

interface GLTFBufferView {
  buffer: number;
  byteOffset?: number;
  byteLength: number;
  byteStride?: number;
  target?: number;
}

interface GLTFAccessor {
  bufferView?: number;
  byteOffset?: number;
  componentType: number;
  count: number;
  type: string;
  max?: number[];
  min?: number[];
  normalized?: boolean;
}

interface GLTFPrimitive {
  attributes: Record<string, number>;
  indices?: number;
  material?: number;
  mode?: number; // 0=POINTS, 1=LINES, 4=TRIANGLES (default), 5=TRIANGLE_STRIP, 6=TRIANGLE_FAN
}

interface GLTFMesh {
  name?: string;
  primitives: GLTFPrimitive[];
}

interface GLTFNode {
  name?: string;
  mesh?: number;
  children?: number[];
  translation?: [number, number, number];
  rotation?: [number, number, number, number]; // quaternion [x, y, z, w]
  scale?: [number, number, number];
  matrix?: number[]; // 4x4 column-major
}

interface GLTFScene {
  name?: string;
  nodes?: number[];
}

interface GLTFMaterialPBR {
  baseColorFactor?: [number, number, number, number];
  baseColorTexture?: { index: number };
  metallicFactor?: number;
  roughnessFactor?: number;
}

interface GLTFMaterial {
  name?: string;
  pbrMetallicRoughness?: GLTFMaterialPBR;
  doubleSided?: boolean;
}

interface GLTFDocument {
  asset: GLTFAsset;
  scene?: number;
  scenes?: GLTFScene[];
  nodes?: GLTFNode[];
  meshes?: GLTFMesh[];
  accessors?: GLTFAccessor[];
  bufferViews?: GLTFBufferView[];
  buffers?: GLTFBuffer[];
  materials?: GLTFMaterial[];
}

// ─── Material Info (exported for viewer) ─────────────────────────────────────

export interface GLTFMaterialInfo {
  name: string;
  baseColor: [number, number, number, number]; // RGBA 0-1
}

export interface GLTFParseResult {
  /** Standard OBJParseResult for compatibility with existing pipeline */
  objResult: OBJParseResult;
  /** Material info per object (same order as objResult.objects) */
  materials: (GLTFMaterialInfo | null)[];
  /** glTF asset metadata */
  asset: { version: string; generator: string };
  /** Total number of meshes in the file */
  meshCount: number;
  /** Total number of nodes in the scene */
  nodeCount: number;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const GLB_MAGIC = 0x46546C67; // "glTF" in little-endian
const GLB_VERSION_2 = 2;
const CHUNK_TYPE_JSON = 0x4E4F534A; // "JSON"
const CHUNK_TYPE_BIN = 0x004E4942;  // "BIN\0"

// Component type sizes
const COMPONENT_TYPE_SIZES: Record<number, number> = {
  5120: 1, // BYTE
  5121: 1, // UNSIGNED_BYTE
  5122: 2, // SHORT
  5123: 2, // UNSIGNED_SHORT
  5125: 4, // UNSIGNED_INT
  5126: 4, // FLOAT
};

// Type element counts
const TYPE_ELEMENT_COUNTS: Record<string, number> = {
  SCALAR: 1,
  VEC2: 2,
  VEC3: 3,
  VEC4: 4,
  MAT2: 4,
  MAT3: 9,
  MAT4: 16,
};

// ─── Matrix / Quaternion Utilities ───────────────────────────────────────────

type Vec3 = [number, number, number];
type Vec4 = [number, number, number, number];
type Mat4 = number[]; // 16 elements, column-major

function mat4Identity(): Mat4 {
  return [
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1,
  ];
}

function mat4FromTRS(t: Vec3, r: Vec4, s: Vec3): Mat4 {
  // Quaternion to rotation matrix
  const [qx, qy, qz, qw] = r;
  const x2 = qx + qx, y2 = qy + qy, z2 = qz + qz;
  const xx = qx * x2, xy = qx * y2, xz = qx * z2;
  const yy = qy * y2, yz = qy * z2, zz = qz * z2;
  const wx = qw * x2, wy = qw * y2, wz = qw * z2;

  return [
    (1 - (yy + zz)) * s[0], (xy + wz) * s[0], (xz - wy) * s[0], 0,
    (xy - wz) * s[1], (1 - (xx + zz)) * s[1], (yz + wx) * s[1], 0,
    (xz + wy) * s[2], (yz - wx) * s[2], (1 - (xx + yy)) * s[2], 0,
    t[0], t[1], t[2], 1,
  ];
}

function mat4Multiply(a: Mat4, b: Mat4): Mat4 {
  const out: Mat4 = new Array(16).fill(0);
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) {
      for (let k = 0; k < 4; k++) {
        out[j * 4 + i] += a[k * 4 + i] * b[j * 4 + k];
      }
    }
  }
  return out;
}

function transformPoint(m: Mat4, p: Vec3): Vec3 {
  const x = m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12];
  const y = m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13];
  const z = m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14];
  return [x, y, z];
}

// ─── Buffer Access ───────────────────────────────────────────────────────────

function getAccessorData(
  doc: GLTFDocument,
  accessorIndex: number,
  buffers: ArrayBuffer[]
): Float32Array | Uint16Array | Uint32Array | Int8Array | Uint8Array | Int16Array {
  const accessor = doc.accessors![accessorIndex];
  const bufferView = doc.bufferViews![accessor.bufferView ?? 0];
  const buffer = buffers[bufferView.buffer];

  const byteOffset = (bufferView.byteOffset ?? 0) + (accessor.byteOffset ?? 0);
  const elementCount = TYPE_ELEMENT_COUNTS[accessor.type] ?? 1;
  const totalElements = accessor.count * elementCount;

  switch (accessor.componentType) {
    case 5126: // FLOAT
      return new Float32Array(buffer, byteOffset, totalElements);
    case 5123: // UNSIGNED_SHORT
      return new Uint16Array(buffer, byteOffset, totalElements);
    case 5125: // UNSIGNED_INT
      return new Uint32Array(buffer, byteOffset, totalElements);
    case 5122: // SHORT
      return new Int16Array(buffer, byteOffset, totalElements);
    case 5121: // UNSIGNED_BYTE
      return new Uint8Array(buffer, byteOffset, totalElements);
    case 5120: // BYTE
      return new Int8Array(buffer, byteOffset, totalElements);
    default:
      throw new Error(`Unsupported component type: ${accessor.componentType}`);
  }
}

// ─── GLB Parser ──────────────────────────────────────────────────────────────

function parseGLB(arrayBuffer: ArrayBuffer): { json: GLTFDocument; binBuffer: ArrayBuffer | null } {
  const view = new DataView(arrayBuffer);

  // Header: magic (4) + version (4) + length (4)
  const magic = view.getUint32(0, true);
  if (magic !== GLB_MAGIC) {
    throw new Error('Invalid GLB file: wrong magic number');
  }

  const version = view.getUint32(4, true);
  if (version !== GLB_VERSION_2) {
    throw new Error(`Unsupported GLB version: ${version}. Only version 2 is supported.`);
  }

  let offset = 12; // Skip header
  let jsonDoc: GLTFDocument | null = null;
  let binBuffer: ArrayBuffer | null = null;

  // Read chunks
  while (offset < arrayBuffer.byteLength) {
    const chunkLength = view.getUint32(offset, true);
    const chunkType = view.getUint32(offset + 4, true);
    offset += 8;

    if (chunkType === CHUNK_TYPE_JSON) {
      const jsonBytes = new Uint8Array(arrayBuffer, offset, chunkLength);
      const jsonStr = new TextDecoder().decode(jsonBytes);
      jsonDoc = JSON.parse(jsonStr) as GLTFDocument;
    } else if (chunkType === CHUNK_TYPE_BIN) {
      // Create a properly aligned copy of the binary chunk
      binBuffer = arrayBuffer.slice(offset, offset + chunkLength);
    }

    offset += chunkLength;
  }

  if (!jsonDoc) {
    throw new Error('GLB file does not contain a JSON chunk');
  }

  return { json: jsonDoc, binBuffer };
}

// ─── glTF JSON Parser ────────────────────────────────────────────────────────

function parseGLTFJSON(jsonStr: string): { json: GLTFDocument; buffers: ArrayBuffer[] } {
  const doc = JSON.parse(jsonStr) as GLTFDocument;
  const buffers: ArrayBuffer[] = [];

  // Resolve embedded base64 buffers
  if (doc.buffers) {
    for (const buf of doc.buffers) {
      if (buf.uri) {
        if (buf.uri.startsWith('data:')) {
          // Base64 data URI
          const base64 = buf.uri.split(',')[1];
          const binaryStr = atob(base64);
          const bytes = new Uint8Array(binaryStr.length);
          for (let i = 0; i < binaryStr.length; i++) {
            bytes[i] = binaryStr.charCodeAt(i);
          }
          buffers.push(bytes.buffer);
        } else {
          throw new Error(
            `External buffer files are not supported. Please use GLB format or embed buffers as base64 data URIs. URI: ${buf.uri}`
          );
        }
      } else {
        // Buffer without URI should only appear in GLB (handled separately)
        buffers.push(new ArrayBuffer(buf.byteLength));
      }
    }
  }

  return { json: doc, buffers };
}

// ─── Node Transform Traversal ────────────────────────────────────────────────

interface MeshInstance {
  meshIndex: number;
  worldMatrix: Mat4;
  nodeName: string;
}

function collectMeshInstances(doc: GLTFDocument): MeshInstance[] {
  const instances: MeshInstance[] = [];
  const nodes = doc.nodes ?? [];

  function traverseNode(nodeIndex: number, parentMatrix: Mat4) {
    const node = nodes[nodeIndex];
    if (!node) return;

    // Compute local transform
    let localMatrix: Mat4;
    if (node.matrix) {
      localMatrix = node.matrix;
    } else {
      const t: Vec3 = node.translation ?? [0, 0, 0];
      const r: Vec4 = node.rotation ?? [0, 0, 0, 1];
      const s: Vec3 = node.scale ?? [1, 1, 1];
      localMatrix = mat4FromTRS(t, r, s);
    }

    const worldMatrix = mat4Multiply(parentMatrix, localMatrix);

    // If this node has a mesh, record it
    if (node.mesh !== undefined) {
      instances.push({
        meshIndex: node.mesh,
        worldMatrix,
        nodeName: node.name ?? `Node_${nodeIndex}`,
      });
    }

    // Traverse children
    if (node.children) {
      for (const childIdx of node.children) {
        traverseNode(childIdx, worldMatrix);
      }
    }
  }

  // Start from the default scene or scene 0
  const sceneIndex = doc.scene ?? 0;
  const scene = doc.scenes?.[sceneIndex];
  if (scene?.nodes) {
    for (const rootNodeIdx of scene.nodes) {
      traverseNode(rootNodeIdx, mat4Identity());
    }
  } else if (nodes.length > 0) {
    // Fallback: traverse all root nodes
    const childNodes = new Set<number>();
    for (const node of nodes) {
      if (node.children) {
        for (const c of node.children) childNodes.add(c);
      }
    }
    for (let i = 0; i < nodes.length; i++) {
      if (!childNodes.has(i)) {
        traverseNode(i, mat4Identity());
      }
    }
  }

  return instances;
}

// ─── Primitive to Triangles ──────────────────────────────────────────────────

interface Triangle {
  v0: Vec3;
  v1: Vec3;
  v2: Vec3;
}

function extractTriangles(
  doc: GLTFDocument,
  primitive: GLTFPrimitive,
  buffers: ArrayBuffer[],
  worldMatrix: Mat4
): Triangle[] {
  const posAccessorIdx = primitive.attributes.POSITION;
  if (posAccessorIdx === undefined) return [];

  const posData = getAccessorData(doc, posAccessorIdx, buffers) as Float32Array;
  const posCount = doc.accessors![posAccessorIdx].count;

  // Transform all positions to world space
  const worldPositions: Vec3[] = [];
  for (let i = 0; i < posCount; i++) {
    const local: Vec3 = [posData[i * 3], posData[i * 3 + 1], posData[i * 3 + 2]];
    worldPositions.push(transformPoint(worldMatrix, local));
  }

  const mode = primitive.mode ?? 4; // Default: TRIANGLES
  const triangles: Triangle[] = [];

  if (primitive.indices !== undefined) {
    // Indexed geometry
    const indexData = getAccessorData(doc, primitive.indices, buffers);

    if (mode === 4) {
      // TRIANGLES
      for (let i = 0; i + 2 < indexData.length; i += 3) {
        triangles.push({
          v0: worldPositions[indexData[i]],
          v1: worldPositions[indexData[i + 1]],
          v2: worldPositions[indexData[i + 2]],
        });
      }
    } else if (mode === 5) {
      // TRIANGLE_STRIP
      for (let i = 0; i + 2 < indexData.length; i++) {
        if (i % 2 === 0) {
          triangles.push({
            v0: worldPositions[indexData[i]],
            v1: worldPositions[indexData[i + 1]],
            v2: worldPositions[indexData[i + 2]],
          });
        } else {
          triangles.push({
            v0: worldPositions[indexData[i + 1]],
            v1: worldPositions[indexData[i]],
            v2: worldPositions[indexData[i + 2]],
          });
        }
      }
    } else if (mode === 6) {
      // TRIANGLE_FAN
      for (let i = 1; i + 1 < indexData.length; i++) {
        triangles.push({
          v0: worldPositions[indexData[0]],
          v1: worldPositions[indexData[i]],
          v2: worldPositions[indexData[i + 1]],
        });
      }
    }
  } else {
    // Non-indexed geometry
    if (mode === 4) {
      for (let i = 0; i + 2 < posCount; i += 3) {
        triangles.push({
          v0: worldPositions[i],
          v1: worldPositions[i + 1],
          v2: worldPositions[i + 2],
        });
      }
    } else if (mode === 5) {
      for (let i = 0; i + 2 < posCount; i++) {
        if (i % 2 === 0) {
          triangles.push({ v0: worldPositions[i], v1: worldPositions[i + 1], v2: worldPositions[i + 2] });
        } else {
          triangles.push({ v0: worldPositions[i + 1], v1: worldPositions[i], v2: worldPositions[i + 2] });
        }
      }
    } else if (mode === 6) {
      for (let i = 1; i + 1 < posCount; i++) {
        triangles.push({ v0: worldPositions[0], v1: worldPositions[i], v2: worldPositions[i + 1] });
      }
    }
  }

  return triangles;
}

// ─── Main Parse Function ─────────────────────────────────────────────────────

/**
 * Validate if the input is a valid glTF/GLB file.
 * Returns an error message if invalid, or null if valid.
 */
export function validateGLTF(input: ArrayBuffer | string): string | null {
  try {
    if (input instanceof ArrayBuffer) {
      // Check GLB magic
      if (input.byteLength < 12) return 'El archivo es demasiado pequeño para ser un GLB válido';
      const view = new DataView(input);
      const magic = view.getUint32(0, true);
      if (magic !== GLB_MAGIC) {
        return 'El archivo no tiene la firma GLB correcta (0x46546C67)';
      }
      const version = view.getUint32(4, true);
      if (version !== 2) {
        return `Versión GLB no soportada: ${version}. Solo se soporta la versión 2.`;
      }
    } else {
      // Try parsing as JSON
      const parsed = JSON.parse(input);
      if (!parsed.asset || !parsed.asset.version) {
        return 'El archivo JSON no contiene la propiedad "asset.version" requerida por glTF';
      }
      if (!parsed.asset.version.startsWith('2')) {
        return `Versión glTF no soportada: ${parsed.asset.version}. Solo se soporta la versión 2.x`;
      }
    }
    return null;
  } catch (e: any) {
    return `Error al validar el archivo: ${e.message}`;
  }
}

/**
 * Detect if an ArrayBuffer is a GLB file (binary glTF).
 */
export function isGLB(buffer: ArrayBuffer): boolean {
  if (buffer.byteLength < 4) return false;
  const view = new DataView(buffer);
  return view.getUint32(0, true) === GLB_MAGIC;
}

/**
 * Parse a glTF (.gltf JSON string) or GLB (.glb ArrayBuffer) file
 * and convert it to the standard OBJParseResult format used by the application.
 */
export function parseGLTF(input: ArrayBuffer | string): GLTFParseResult {
  let doc: GLTFDocument;
  let buffers: ArrayBuffer[];

  if (input instanceof ArrayBuffer) {
    // GLB binary format
    const { json, binBuffer } = parseGLB(input);
    doc = json;
    buffers = binBuffer ? [binBuffer] : [];

    // Also resolve any additional embedded buffers beyond the binary chunk
    if (doc.buffers && doc.buffers.length > 1) {
      for (let i = 1; i < doc.buffers.length; i++) {
        const buf = doc.buffers[i];
        if (buf.uri && buf.uri.startsWith('data:')) {
          const base64 = buf.uri.split(',')[1];
          const binaryStr = atob(base64);
          const bytes = new Uint8Array(binaryStr.length);
          for (let j = 0; j < binaryStr.length; j++) {
            bytes[j] = binaryStr.charCodeAt(j);
          }
          buffers.push(bytes.buffer);
        }
      }
    }
  } else {
    // glTF JSON format
    const parsed = parseGLTFJSON(input);
    doc = parsed.json;
    buffers = parsed.buffers;
  }

  // Collect all mesh instances with their world transforms
  const meshInstances = collectMeshInstances(doc);

  // Convert each mesh instance into an OBJ-compatible object
  const allVertices: { x: number; y: number; z: number }[] = [];
  const objects: { name: string; faces: { vertexIndices: number[] }[] }[] = [];
  const materials: (GLTFMaterialInfo | null)[] = [];

  let totalFaces = 0;

  for (const instance of meshInstances) {
    const mesh = doc.meshes![instance.meshIndex];
    const objectName = mesh.name || instance.nodeName || `Mesh_${instance.meshIndex}`;

    const objectFaces: { vertexIndices: number[] }[] = [];
    let primaryMaterial: GLTFMaterialInfo | null = null;

    for (const primitive of mesh.primitives) {
      // Extract material info from the first primitive that has one
      if (!primaryMaterial && primitive.material !== undefined && doc.materials) {
        const mat = doc.materials[primitive.material];
        const pbr = mat.pbrMetallicRoughness;
        primaryMaterial = {
          name: mat.name ?? `Material_${primitive.material}`,
          baseColor: pbr?.baseColorFactor ?? [0.8, 0.8, 0.8, 1.0],
        };
      }

      const triangles = extractTriangles(doc, primitive, buffers, instance.worldMatrix);

      for (const tri of triangles) {
        const baseIdx = allVertices.length;
        allVertices.push({ x: tri.v0[0], y: tri.v0[1], z: tri.v0[2] });
        allVertices.push({ x: tri.v1[0], y: tri.v1[1], z: tri.v1[2] });
        allVertices.push({ x: tri.v2[0], y: tri.v2[1], z: tri.v2[2] });
        objectFaces.push({ vertexIndices: [baseIdx, baseIdx + 1, baseIdx + 2] });
        totalFaces++;
      }
    }

    if (objectFaces.length > 0) {
      objects.push({ name: objectName, faces: objectFaces });
      materials.push(primaryMaterial);
    }
  }

  // Compute bounding box
  let minX = Infinity, minY = Infinity, minZ = Infinity;
  let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;

  for (const v of allVertices) {
    if (v.x < minX) minX = v.x;
    if (v.y < minY) minY = v.y;
    if (v.z < minZ) minZ = v.z;
    if (v.x > maxX) maxX = v.x;
    if (v.y > maxY) maxY = v.y;
    if (v.z > maxZ) maxZ = v.z;
  }

  // Handle empty geometry
  if (allVertices.length === 0) {
    minX = minY = minZ = maxX = maxY = maxZ = 0;
  }

  const objResult: OBJParseResult = {
    vertices: allVertices,
    objects,
    totalFaces,
    boundingBox: {
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
    },
  };

  return {
    objResult,
    materials,
    asset: {
      version: doc.asset.version,
      generator: doc.asset.generator ?? 'Unknown',
    },
    meshCount: doc.meshes?.length ?? 0,
    nodeCount: doc.nodes?.length ?? 0,
  };
}

/**
 * Get a human-readable summary of a parsed glTF file.
 */
export function getGLTFSummary(result: GLTFParseResult): string {
  const { objResult, asset, meshCount, nodeCount, materials } = result;
  const lines: string[] = [
    `glTF v${asset.version} (${asset.generator})`,
    `${meshCount} mesh(es), ${nodeCount} nodo(s)`,
    `${objResult.vertices.length} vértices, ${objResult.totalFaces} triángulos`,
    `${objResult.objects.length} objeto(s)`,
  ];

  const dims = objResult.boundingBox.dimensions;
  lines.push(`Dimensiones: ${dims.x.toFixed(2)} × ${dims.y.toFixed(2)} × ${dims.z.toFixed(2)}`);

  const namedMaterials = materials.filter(m => m !== null);
  if (namedMaterials.length > 0) {
    lines.push(`Materiales: ${namedMaterials.map(m => m!.name).join(', ')}`);
  }

  return lines.join('\n');
}
