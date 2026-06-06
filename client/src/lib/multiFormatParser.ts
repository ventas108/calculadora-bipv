/**
 * Multi-Format 3D Parser
 * 
 * Converts various 3D file formats into the standard OBJParseResult format
 * used by the rest of the application (buildingModelImporter, ShadingCalculator).
 * 
 * Supported formats:
 * - DXF (AutoCAD): via dxf-parser library
 * - FBX (Blender, Revit, 3ds Max): via Three.js FBXLoader
 * - STL (Universal mesh format): ASCII and binary
 * - DAE/Collada (Blender, SketchUp, Rhino): via Three.js ColladaLoader
 * - VRML/WRL (Legacy 3D format): via Three.js VRMLLoader
 * - 3DS (3ds Max legacy): via Three.js TDSLoader
 * 
 * All parsers output OBJParseResult { vertices, objects, totalFaces, boundingBox }
 * which then feeds into the curved surface detection and facade clustering pipeline.
 * 
 * For DWG and XSI (proprietary formats without JS parsers):
 * - DWG: User must export as DXF from AutoCAD
 * - XSI: User must export as FBX or OBJ from Softimage
 */

import type { OBJParseResult } from './objParser';
import * as THREE from 'three';

// ── Interfaces ───────────────────────────────────────────────────────

interface Vertex3D {
  x: number;
  y: number;
  z: number;
}

interface ParsedFace {
  vertexIndices: number[];
}

interface ParsedObject {
  name: string;
  faces: ParsedFace[];
}

export type SupportedFormat = 'obj' | 'gltf' | 'glb' | 'dxf' | 'dwg' | 'fbx' | 'stl' | 'dae' | 'vrml' | 'wrl' | '3ds' | 'xsi';

export interface FormatInfo {
  extension: string;
  name: string;
  software: string[];
  supported: boolean;
  note?: string;
}

export const SUPPORTED_FORMATS: FormatInfo[] = [
  { extension: '.obj', name: 'Wavefront OBJ', software: ['SketchUp', 'Blender', 'Rhino', 'Revit', 'Sun Path 3D', 'AutoCAD'], supported: true },
  { extension: '.gltf', name: 'glTF 2.0', software: ['Blender', 'SketchUp', 'Rhino', 'Revit'], supported: true },
  { extension: '.glb', name: 'glTF Binary', software: ['Blender', 'SketchUp', 'Rhino', 'Revit'], supported: true },
  { extension: '.dxf', name: 'AutoCAD DXF', software: ['AutoCAD', 'Rhino', 'SketchUp', 'Revit'], supported: true },
  { extension: '.fbx', name: 'Autodesk FBX', software: ['Blender', 'Revit', '3ds Max', 'Maya', 'Rhino'], supported: true },
  { extension: '.stl', name: 'Stereolithography', software: ['Blender', 'Rhino', 'AutoCAD', 'SolidWorks', 'Revit'], supported: true },
  { extension: '.dae', name: 'Collada', software: ['Blender', 'SketchUp', 'Rhino', 'Revit'], supported: true },
  { extension: '.wrl', name: 'VRML', software: ['Rhino', 'Blender', '3ds Max'], supported: true },
  { extension: '.3ds', name: '3D Studio', software: ['3ds Max', 'Blender', 'Rhino'], supported: true },
  { extension: '.dwg', name: 'AutoCAD DWG', software: ['AutoCAD', 'Revit'], supported: false, note: 'Exporte como DXF desde AutoCAD (Archivo → Guardar como → DXF)' },
  { extension: '.xsi', name: 'Softimage XSI', software: ['Softimage'], supported: false, note: 'Exporte como FBX u OBJ desde Softimage' },
];

export function getAcceptedExtensions(): string {
  return SUPPORTED_FORMATS
    .filter(f => f.supported)
    .map(f => f.extension)
    .join(',');
}

export function detectFormat(fileName: string): SupportedFormat | null {
  const ext = fileName.toLowerCase().split('.').pop();
  if (!ext) return null;
  const map: Record<string, SupportedFormat> = {
    'obj': 'obj', 'gltf': 'gltf', 'glb': 'glb',
    'dxf': 'dxf', 'dwg': 'dwg', 'fbx': 'fbx',
    'stl': 'stl', 'dae': 'dae', 'vrml': 'vrml',
    'wrl': 'wrl', '3ds': '3ds', 'xsi': 'xsi',
  };
  return map[ext] || null;
}

export function isUnsupportedFormat(format: SupportedFormat): boolean {
  return format === 'dwg' || format === 'xsi';
}

export function getConversionAdvice(format: SupportedFormat): string {
  if (format === 'dwg') {
    return 'El formato DWG es propietario de Autodesk. Para importar su modelo:\n\n' +
      '1. Abra el archivo en AutoCAD\n' +
      '2. Vaya a Archivo → Guardar como\n' +
      '3. En "Tipo de archivo", seleccione "DXF (*.dxf)"\n' +
      '4. Guarde y cargue el archivo .dxf aquí\n\n' +
      'Alternativamente, puede exportar como OBJ o FBX si tiene plugins instalados.';
  }
  if (format === 'xsi') {
    return 'El formato XSI (dotXSI/Softimage) es un formato legacy. Para importar:\n\n' +
      '1. Abra el archivo en Softimage o un conversor compatible\n' +
      '2. Exporte como FBX (Archivo → Export → FBX)\n' +
      '3. O exporte como OBJ (Archivo → Export → OBJ)\n' +
      '4. Cargue el archivo exportado aquí';
  }
  return '';
}

// ── DXF Parser ───────────────────────────────────────────────────────

/**
 * Parse DXF file (AutoCAD Drawing Exchange Format).
 * Extracts 3D geometry from: 3DFACE, POLYFACE MESH, MESH, LINE, POLYLINE entities.
 * Works with exports from AutoCAD, Rhino, SketchUp, Revit.
 */
export function parseDXF(content: string): OBJParseResult {
  const vertices: Vertex3D[] = [];
  const objects: ParsedObject[] = [];
  let totalFaces = 0;

  // Manual DXF parsing for 3D geometry (more reliable for 3D solid models)
  const lines = content.split('\n').map(l => l.trim());
  
  // Parse entities section
  let inEntities = false;
  let currentEntityType = '';
  let currentLayer = 'default';
  const layerObjects = new Map<string, ParsedObject>();
  
  // Track 3DFACE entities (most common for solid 3D exports)
  const faceVertices: Vertex3D[] = [];
  let faceVertCount = 0;
  let readingVertex = false;
  let currentGroupCode = 0;
  
  // Temporary storage for current entity vertices
  let entityVerts: (Vertex3D | null)[] = [null, null, null, null];
  
  for (let i = 0; i < lines.length; i++) {
    const code = parseInt(lines[i]);
    const value = lines[i + 1] || '';
    
    if (code === 0 && value === 'SECTION') {
      const nextCode = parseInt(lines[i + 2] || '');
      const nextValue = lines[i + 3] || '';
      if (nextCode === 2 && nextValue === 'ENTITIES') {
        inEntities = true;
        i += 3;
        continue;
      }
    }
    
    if (code === 0 && value === 'ENDSEC') {
      if (inEntities) {
        // Flush last entity
        flushEntity();
        inEntities = false;
      }
    }
    
    if (!inEntities) { i++; continue; }
    
    if (code === 0) {
      // New entity - flush previous
      flushEntity();
      currentEntityType = value;
      entityVerts = [null, null, null, null];
      currentLayer = 'default';
    } else if (code === 8) {
      currentLayer = value;
    } else if (currentEntityType === '3DFACE') {
      // 3DFACE has 4 corner points (10-13, 20-23, 30-33)
      if (code >= 10 && code <= 13) {
        const idx = code - 10;
        if (!entityVerts[idx]) entityVerts[idx] = { x: 0, y: 0, z: 0 };
        entityVerts[idx]!.x = parseFloat(value);
      } else if (code >= 20 && code <= 23) {
        const idx = code - 20;
        if (!entityVerts[idx]) entityVerts[idx] = { x: 0, y: 0, z: 0 };
        entityVerts[idx]!.y = parseFloat(value);
      } else if (code >= 30 && code <= 33) {
        const idx = code - 30;
        if (!entityVerts[idx]) entityVerts[idx] = { x: 0, y: 0, z: 0 };
        entityVerts[idx]!.z = parseFloat(value);
      }
    } else if (currentEntityType === 'LINE') {
      // LINE has start (10,20,30) and end (11,21,31)
      if (code === 10) {
        if (!entityVerts[0]) entityVerts[0] = { x: 0, y: 0, z: 0 };
        entityVerts[0]!.x = parseFloat(value);
      } else if (code === 20) {
        if (!entityVerts[0]) entityVerts[0] = { x: 0, y: 0, z: 0 };
        entityVerts[0]!.y = parseFloat(value);
      } else if (code === 30) {
        if (!entityVerts[0]) entityVerts[0] = { x: 0, y: 0, z: 0 };
        entityVerts[0]!.z = parseFloat(value);
      } else if (code === 11) {
        if (!entityVerts[1]) entityVerts[1] = { x: 0, y: 0, z: 0 };
        entityVerts[1]!.x = parseFloat(value);
      } else if (code === 21) {
        if (!entityVerts[1]) entityVerts[1] = { x: 0, y: 0, z: 0 };
        entityVerts[1]!.y = parseFloat(value);
      } else if (code === 31) {
        if (!entityVerts[1]) entityVerts[1] = { x: 0, y: 0, z: 0 };
        entityVerts[1]!.z = parseFloat(value);
      }
    }
    
    i++; // Skip value line (we read pairs)
  }
  
  function flushEntity() {
    if (currentEntityType === '3DFACE') {
      const validVerts = entityVerts.filter((v): v is Vertex3D => v !== null);
      if (validVerts.length >= 3) {
        // Get or create layer object
        if (!layerObjects.has(currentLayer)) {
          layerObjects.set(currentLayer, { name: currentLayer, faces: [] });
        }
        const obj = layerObjects.get(currentLayer)!;
        
        // Add vertices and create face
        const startIdx = vertices.length;
        for (const v of validVerts) {
          vertices.push(v);
        }
        
        // Check if 4th vertex is same as 3rd (triangle encoded as quad)
        const indices: number[] = [];
        indices.push(startIdx, startIdx + 1, startIdx + 2);
        if (validVerts.length === 4) {
          const v3 = validVerts[2];
          const v4 = validVerts[3];
          const dist = Math.sqrt((v3.x-v4.x)**2 + (v3.y-v4.y)**2 + (v3.z-v4.z)**2);
          if (dist > 0.0001) {
            indices.push(startIdx + 3);
          }
        }
        
        obj.faces.push({ vertexIndices: indices });
        totalFaces++;
      }
    }
  }
  
  // Also try parsing with POLYLINE/VERTEX entities (polyface meshes)
  parseDXFPolyfaces(lines, vertices, layerObjects);
  
  // Convert layer map to objects array
  layerObjects.forEach((obj) => {
    if (obj.faces.length > 0) {
      objects.push(obj);
    }
  });
  
  // Recalculate totalFaces
  totalFaces = objects.reduce((sum, obj) => sum + obj.faces.length, 0);
  
  // Calculate bounding box
  const bbox = calculateBoundingBox(vertices);
  
  return { vertices, objects, totalFaces, boundingBox: bbox };
}

/**
 * Parse POLYLINE/VERTEX entities (polyface meshes in DXF)
 */
function parseDXFPolyfaces(
  lines: string[],
  vertices: Vertex3D[],
  layerObjects: Map<string, ParsedObject>
): void {
  let inPolyline = false;
  let isPolyface = false;
  let polyVertices: Vertex3D[] = [];
  let polyFaces: number[][] = [];
  let currentLayer = 'default';
  let currentVertex: Vertex3D = { x: 0, y: 0, z: 0 };
  let vertexFlags = 0;
  let faceIndices: number[] = [];
  
  for (let i = 0; i < lines.length - 1; i += 2) {
    const code = parseInt(lines[i]);
    const value = lines[i + 1] || '';
    
    if (code === 0 && value === 'POLYLINE') {
      inPolyline = true;
      isPolyface = false;
      polyVertices = [];
      polyFaces = [];
      currentLayer = 'default';
    } else if (code === 0 && value === 'SEQEND' && inPolyline) {
      // End of polyline - flush polyface
      if (isPolyface && polyVertices.length > 0 && polyFaces.length > 0) {
        if (!layerObjects.has(currentLayer)) {
          layerObjects.set(currentLayer, { name: currentLayer, faces: [] });
        }
        const obj = layerObjects.get(currentLayer)!;
        const startIdx = vertices.length;
        for (const v of polyVertices) {
          vertices.push(v);
        }
        for (const face of polyFaces) {
          const globalIndices = face.map(idx => startIdx + idx);
          obj.faces.push({ vertexIndices: globalIndices });
        }
      }
      inPolyline = false;
    } else if (inPolyline) {
      if (code === 70) {
        const flags = parseInt(value);
        if (!isPolyface && (flags & 64)) {
          isPolyface = true; // Polyface mesh flag
        }
        if (code === 70) vertexFlags = flags;
      } else if (code === 8) {
        currentLayer = value;
      } else if (code === 0 && value === 'VERTEX') {
        // Check if previous vertex was a face definition or vertex definition
        if (vertexFlags & 128) {
          // Face vertex - indices in 71-74
          if (faceIndices.length >= 3) {
            polyFaces.push([...faceIndices]);
          }
          faceIndices = [];
        }
        currentVertex = { x: 0, y: 0, z: 0 };
        vertexFlags = 0;
      } else if (code === 10) {
        currentVertex.x = parseFloat(value);
      } else if (code === 20) {
        currentVertex.y = parseFloat(value);
      } else if (code === 30) {
        currentVertex.z = parseFloat(value);
        if (!(vertexFlags & 128)) {
          polyVertices.push({ ...currentVertex });
        }
      } else if (code >= 71 && code <= 74) {
        const idx = Math.abs(parseInt(value)) - 1; // 1-based to 0-based
        if (idx >= 0) faceIndices.push(idx);
      }
    }
  }
}

// ── STL Parser ───────────────────────────────────────────────────────

/**
 * Parse STL file (Stereolithography format).
 * Supports both ASCII and binary formats.
 * Used by: Blender, Rhino, AutoCAD, SolidWorks, Revit, 3D printers.
 */
export function parseSTL(content: string | ArrayBuffer): OBJParseResult {
  if (typeof content === 'string') {
    return parseSTLAscii(content);
  }
  // Check if binary or ASCII
  const view = new DataView(content);
  // Binary STL: 80-byte header + 4-byte triangle count
  // ASCII STL starts with "solid"
  const header = new TextDecoder().decode(new Uint8Array(content, 0, Math.min(80, content.byteLength)));
  if (header.startsWith('solid') && content.byteLength > 84) {
    // Could be ASCII - check if the expected binary triangle count makes sense
    const expectedTriangles = view.getUint32(80, true);
    const expectedSize = 84 + expectedTriangles * 50;
    if (Math.abs(expectedSize - content.byteLength) > 100) {
      // Likely ASCII
      return parseSTLAscii(new TextDecoder().decode(new Uint8Array(content)));
    }
  }
  return parseSTLBinary(content);
}

function parseSTLAscii(content: string): OBJParseResult {
  const vertices: Vertex3D[] = [];
  const faces: ParsedFace[] = [];
  
  const lines = content.split('\n');
  let solidName = 'STL Model';
  const faceVerts: number[] = [];
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('solid ')) {
      solidName = trimmed.substring(6).trim() || 'STL Model';
    } else if (trimmed.startsWith('vertex ')) {
      const parts = trimmed.split(/\s+/);
      if (parts.length >= 4) {
        const v: Vertex3D = {
          x: parseFloat(parts[1]),
          y: parseFloat(parts[2]),
          z: parseFloat(parts[3]),
        };
        faceVerts.push(vertices.length);
        vertices.push(v);
      }
    } else if (trimmed === 'endfacet') {
      if (faceVerts.length >= 3) {
        faces.push({ vertexIndices: [...faceVerts] });
      }
      faceVerts.length = 0;
    }
  }
  
  const bbox = calculateBoundingBox(vertices);
  return {
    vertices,
    objects: [{ name: solidName, faces }],
    totalFaces: faces.length,
    boundingBox: bbox,
  };
}

function parseSTLBinary(buffer: ArrayBuffer): OBJParseResult {
  const view = new DataView(buffer);
  const vertices: Vertex3D[] = [];
  const faces: ParsedFace[] = [];
  
  // Skip 80-byte header
  const triangleCount = view.getUint32(80, true);
  let offset = 84;
  
  for (let i = 0; i < triangleCount && offset + 50 <= buffer.byteLength; i++) {
    // Skip normal (12 bytes)
    offset += 12;
    
    // Read 3 vertices (each 12 bytes = 3 floats)
    const startIdx = vertices.length;
    for (let v = 0; v < 3; v++) {
      vertices.push({
        x: view.getFloat32(offset, true),
        y: view.getFloat32(offset + 4, true),
        z: view.getFloat32(offset + 8, true),
      });
      offset += 12;
    }
    
    faces.push({ vertexIndices: [startIdx, startIdx + 1, startIdx + 2] });
    
    // Skip attribute byte count (2 bytes)
    offset += 2;
  }
  
  const bbox = calculateBoundingBox(vertices);
  return {
    vertices,
    objects: [{ name: 'STL Model', faces }],
    totalFaces: faces.length,
    boundingBox: bbox,
  };
}

// ── FBX Parser (via Three.js) ────────────────────────────────────────

/**
 * Parse FBX file using Three.js FBXLoader.
 * Works with FBX files from: Blender, Revit, 3ds Max, Maya, Rhino.
 * Requires FBX >= 7.0 (ASCII) or >= 6400 (Binary).
 */
export async function parseFBX(buffer: ArrayBuffer): Promise<OBJParseResult> {
  const { FBXLoader } = await import('three/examples/jsm/loaders/FBXLoader.js');
  
  const loader = new FBXLoader();
  const group = loader.parse(buffer, '');
  
  return extractGeometryFromThreeObject(group, 'FBX Model');
}

// ── DAE/Collada Parser (via Three.js) ────────────────────────────────

/**
 * Parse Collada/DAE file using Three.js ColladaLoader.
 * Works with exports from: Blender, SketchUp, Rhino, Revit.
 */
export async function parseDAE(content: string): Promise<OBJParseResult> {
  const { ColladaLoader } = await import('three/examples/jsm/loaders/ColladaLoader.js');
  
  const loader = new ColladaLoader();
  const collada = loader.parse(content, '');
  if (!collada || !collada.scene) {
    throw new Error('No se pudo parsear el archivo Collada/DAE. Verifique que el archivo es válido.');
  }
  
  return extractGeometryFromThreeObject(collada.scene, 'Collada Model');
}

// ── VRML Parser (via Three.js) ───────────────────────────────────────

/**
 * Parse VRML/WRL file using Three.js VRMLLoader.
 * Works with VRML 2.0 (VRML97) files from: Rhino, Blender, 3ds Max.
 */
export async function parseVRML(content: string): Promise<OBJParseResult> {
  const { VRMLLoader } = await import('three/examples/jsm/loaders/VRMLLoader.js');
  
  const loader = new VRMLLoader();
  const scene = loader.parse(content, '');
  
  return extractGeometryFromThreeObject(scene, 'VRML Model');
}

// ── 3DS Parser (via Three.js) ────────────────────────────────────────

/**
 * Parse 3DS file using Three.js TDSLoader.
 * Works with 3D Studio files from: 3ds Max, Blender, Rhino.
 */
export async function parse3DS(buffer: ArrayBuffer): Promise<OBJParseResult> {
  const { TDSLoader } = await import('three/examples/jsm/loaders/TDSLoader.js');
  
  const loader = new TDSLoader();
  const group = loader.parse(buffer, '');
  
  return extractGeometryFromThreeObject(group, '3DS Model');
}

// ── Three.js Geometry Extraction ─────────────────────────────────────

/**
 * Extract vertices and faces from a Three.js Object3D hierarchy.
 * Traverses all meshes in the scene graph and converts to OBJParseResult.
 */
function extractGeometryFromThreeObject(object: THREE.Object3D, defaultName: string): OBJParseResult {
  const vertices: Vertex3D[] = [];
  const objects: ParsedObject[] = [];
  let totalFaces = 0;
  
  object.updateMatrixWorld(true);
  
  object.traverse((child) => {
    if (!(child instanceof THREE.Mesh)) return;
    
    const mesh = child as THREE.Mesh;
    const geometry = mesh.geometry;
    if (!geometry) return;
    
    // Ensure geometry is BufferGeometry
    const bufferGeom = geometry as THREE.BufferGeometry;
    const posAttr = bufferGeom.getAttribute('position');
    if (!posAttr) return;
    
    const objName = mesh.name || defaultName;
    const faces: ParsedFace[] = [];
    const vertexOffset = vertices.length;
    
    // Apply world matrix to get absolute positions
    const worldMatrix = mesh.matrixWorld;
    const tempVec = new THREE.Vector3();
    
    // Extract vertices
    for (let i = 0; i < posAttr.count; i++) {
      tempVec.set(
        posAttr.getX(i),
        posAttr.getY(i),
        posAttr.getZ(i)
      );
      tempVec.applyMatrix4(worldMatrix);
      vertices.push({ x: tempVec.x, y: tempVec.y, z: tempVec.z });
    }
    
    // Extract faces (triangles)
    const index = bufferGeom.index;
    if (index) {
      // Indexed geometry
      for (let i = 0; i < index.count; i += 3) {
        faces.push({
          vertexIndices: [
            vertexOffset + index.getX(i),
            vertexOffset + index.getX(i + 1),
            vertexOffset + index.getX(i + 2),
          ],
        });
      }
    } else {
      // Non-indexed geometry (every 3 vertices form a triangle)
      for (let i = 0; i < posAttr.count; i += 3) {
        faces.push({
          vertexIndices: [
            vertexOffset + i,
            vertexOffset + i + 1,
            vertexOffset + i + 2,
          ],
        });
      }
    }
    
    if (faces.length > 0) {
      objects.push({ name: objName, faces });
      totalFaces += faces.length;
    }
  });
  
  // If no objects found, create empty result
  if (objects.length === 0) {
    objects.push({ name: defaultName, faces: [] });
  }
  
  const bbox = calculateBoundingBox(vertices);
  return { vertices, objects, totalFaces, boundingBox: bbox };
}

// ── Utility Functions ────────────────────────────────────────────────

function calculateBoundingBox(vertices: Vertex3D[]) {
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
    center: { x: (minX + maxX) / 2, y: (minY + maxY) / 2, z: (minZ + maxZ) / 2 },
    dimensions: { x: maxX - minX, y: maxY - minY, z: maxZ - minZ },
  };
}

// ── Main Parse Function ──────────────────────────────────────────────

/**
 * Parse any supported 3D file format and return OBJParseResult.
 * This is the main entry point for multi-format parsing.
 * 
 * @param fileName - Name of the file (used to detect format)
 * @param content - File content (string for text formats, ArrayBuffer for binary)
 * @returns OBJParseResult compatible with the rest of the application
 */
export async function parseMultiFormat(
  fileName: string,
  content: string | ArrayBuffer
): Promise<{ result: OBJParseResult; format: SupportedFormat; formatName: string }> {
  const format = detectFormat(fileName);
  
  if (!format) {
    throw new Error(`Formato no reconocido: ${fileName}. Formatos soportados: ${SUPPORTED_FORMATS.map(f => f.extension).join(', ')}`);
  }
  
  if (isUnsupportedFormat(format)) {
    throw new Error(getConversionAdvice(format));
  }
  
  let result: OBJParseResult;
  let formatName: string;
  
  switch (format) {
    case 'dxf':
      if (typeof content !== 'string') {
        content = new TextDecoder().decode(new Uint8Array(content as ArrayBuffer));
      }
      result = parseDXF(content as string);
      formatName = 'AutoCAD DXF';
      break;
      
    case 'fbx':
      if (typeof content === 'string') {
        throw new Error('El archivo FBX debe leerse como binario (ArrayBuffer)');
      }
      result = await parseFBX(content as ArrayBuffer);
      formatName = 'Autodesk FBX';
      break;
      
    case 'stl':
      result = parseSTL(content);
      formatName = 'STL (Stereolithography)';
      break;
      
    case 'dae':
      if (typeof content !== 'string') {
        content = new TextDecoder().decode(new Uint8Array(content as ArrayBuffer));
      }
      result = await parseDAE(content as string);
      formatName = 'Collada (DAE)';
      break;
      
    case 'vrml':
    case 'wrl':
      if (typeof content !== 'string') {
        content = new TextDecoder().decode(new Uint8Array(content as ArrayBuffer));
      }
      result = await parseVRML(content as string);
      formatName = 'VRML';
      break;
      
    case '3ds':
      if (typeof content === 'string') {
        throw new Error('El archivo 3DS debe leerse como binario (ArrayBuffer)');
      }
      result = await parse3DS(content as ArrayBuffer);
      formatName = '3D Studio (3DS)';
      break;
      
    default:
      throw new Error(`El formato ${format} debe procesarse con su parser dedicado (OBJ/glTF).`);
  }
  
  // Validate result
  if (result.totalFaces === 0) {
    throw new Error(
      `No se encontró geometría 3D en el archivo ${formatName}. ` +
      'Asegúrese de que el archivo contiene mallas 3D (no solo líneas 2D o curvas).'
    );
  }
  
  return { result, format, formatName };
}

/**
 * Get a human-readable summary of the parse result
 */
export function getParseResultSummary(result: OBJParseResult, formatName: string): string {
  const dims = result.boundingBox.dimensions;
  return [
    `Formato: ${formatName}`,
    `${result.vertices.length} vértices, ${result.totalFaces} caras`,
    `${result.objects.length} objeto(s)`,
    `Dimensiones: ${dims.x.toFixed(2)} × ${dims.y.toFixed(2)} × ${dims.z.toFixed(2)} m`,
  ].join('\n');
}
