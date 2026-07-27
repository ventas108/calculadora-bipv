/**
 * ModelViewer3D Component
 * 
 * Visor 3D interactivo usando Three.js (via @react-three/fiber + @react-three/drei)
 * para previsualizar el modelo del edificio importado junto con los obstáculos de sombra.
 * 
 * Features:
 * - Renderizado del edificio con fachadas coloreadas por orientación
 * - Renderizado de obstáculos semi-transparentes
 * - Controles orbitales funcionales (rotación, zoom, pan)
 * - Botones de control: Rotar, Zoom In/Out, Reset, Fullscreen
 * - Ejes X, Y, Z con etiquetas y colores estándar
 * - Selección visual de fachadas (clic + hover)
 * - Indicador de orientación (brújula N/S/E/O)
 * - Panel de información de fachada seleccionada
 */

import { useRef, useState, useMemo, useCallback, useEffect, Suspense } from 'react';
import { Canvas, useFrame, useThree, ThreeEvent } from '@react-three/fiber';
import { OrbitControls, Text, Grid, Html, Line } from '@react-three/drei';
import * as THREE from 'three';
import { EvaluationModel, DetectedFacade, Vertex3D } from '@/lib/buildingModelImporter';
import { Compass, RotateCcw, ZoomIn, ZoomOut, Maximize2, Minimize2, RotateCw, Move, Info, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';

// ─── Types ───────────────────────────────────────────────────────────────────

interface ModelViewer3DProps {
  /** Modelo del edificio importado */
  model: EvaluationModel;
  /** Vértices 3D de los obstáculos del entorno */
  obstacleVertices3D?: Vertex3D[][];
  /** Fachada actualmente seleccionada (índice) */
  selectedFacadeIdx: number | null;
  /** Callback al seleccionar una fachada */
  onFacadeSelect?: (idx: number | null) => void;
  /** North offset en grados */
  northOffset?: number;
  /** Altura del componente */
  height?: number;
}

// ─── Color Utilities ─────────────────────────────────────────────────────────

const FACADE_COLORS: string[] = [
  '#3B82F6', // blue
  '#EF4444', // red
  '#10B981', // green
  '#F59E0B', // amber
  '#8B5CF6', // violet
  '#EC4899', // pink
  '#06B6D4', // cyan
  '#F97316', // orange
];

const OBSTACLE_COLOR = '#94A3B8'; // slate-400
const OBSTACLE_OPACITY = 0.35;
const SELECTED_EMISSIVE = '#FFD700';
const HOVER_EMISSIVE = '#87CEEB';

// ─── Building Mesh Component ─────────────────────────────────────────────────

interface BuildingMeshProps {
  model: EvaluationModel;
  selectedFacadeIdx: number | null;
  hoveredFacadeIdx: number | null;
  onFacadeClick: (idx: number) => void;
  onFacadeHover: (idx: number | null) => void;
  northOffset?: number;
}

function BuildingMesh({ model, selectedFacadeIdx, hoveredFacadeIdx, onFacadeClick, onFacadeHover, northOffset = 0 }: BuildingMeshProps) {
  const { parseResult, transformedVertices, detectedFacades, centroid } = model;
  
  const faceMeshes = useMemo(() => {
    const meshes: Array<{
      geometry: THREE.BufferGeometry;
      color: string;
      facadeIdx: number;
      isVertical: boolean;
    }> = [];

    // Usar vértices transformados (con remapeo de ejes aplicado) para coherencia con fachadas
    const vertices = transformedVertices || parseResult.vertices;
    
    for (const obj of parseResult.objects) {
      for (const face of obj.faces) {
        const faceVerts = face.vertexIndices.map(idx => vertices[idx]);
        if (faceVerts.length < 3) continue;

        const v0 = faceVerts[0];
        const v1 = faceVerts[1];
        const v2 = faceVerts[2];
        const e1 = new THREE.Vector3(v1.x - v0.x, v1.y - v0.y, v1.z - v0.z);
        const e2 = new THREE.Vector3(v2.x - v0.x, v2.y - v0.y, v2.z - v0.z);
        let normal = new THREE.Vector3().crossVectors(e1, e2).normalize();

        const faceCenter = new THREE.Vector3(
          faceVerts.reduce((s, v) => s + v.x, 0) / faceVerts.length,
          faceVerts.reduce((s, v) => s + v.y, 0) / faceVerts.length,
          faceVerts.reduce((s, v) => s + v.z, 0) / faceVerts.length,
        );
        const toCentroid = new THREE.Vector3(centroid.x - faceCenter.x, centroid.y - faceCenter.y, centroid.z - faceCenter.z);
        if (normal.dot(toCentroid) > 0) {
          normal.negate();
        }

        // Clasificar la cara según su inclinación (coherente con buildingModelImporter)
        const faceTilt = Math.acos(Math.abs(normal.z)) * 180 / Math.PI;
        const isVerticalFace = faceTilt > 75; // Muro vertical
        const isFlatRoof = normal.z > 0 && faceTilt < 15; // Techo plano
        const isSlopedRoof = normal.z > 0 && faceTilt >= 15 && faceTilt <= 75; // Techo inclinado (agua)
        const isSurface = isVerticalFace || isFlatRoof || isSlopedRoof;

        // Calcular azimut solar de la cara (aplicando northOffset igual que buildingModelImporter)
        const bearing = (Math.atan2(normal.x, normal.y) * 180 / Math.PI) + northOffset;
        let solarAzimuth = bearing - 180;
        if (solarAzimuth > 180) solarAzimuth -= 360;
        if (solarAzimuth < -180) solarAzimuth += 360;

        let facadeIdx = -1;
        if (isVerticalFace) {
          // Buscar la fachada vertical más cercana por azimut
          for (let i = 0; i < detectedFacades.length; i++) {
            if (detectedFacades[i].tilt <= 75) continue; // Solo fachadas verticales
            let azDiff = Math.abs(solarAzimuth - detectedFacades[i].azimuthNormal);
            if (azDiff > 180) azDiff = 360 - azDiff;
            if (azDiff < 30) {
              facadeIdx = i;
              break;
            }
          }
        } else if (isFlatRoof) {
          // Buscar el techo plano más cercano
          for (let i = 0; i < detectedFacades.length; i++) {
            if (detectedFacades[i].tilt < 15) {
              facadeIdx = i;
              break;
            }
          }
        } else if (isSlopedRoof) {
          // Buscar el techo inclinado más cercano por azimut Y tilt
          let bestMatch = -1;
          let bestScore = Infinity;
          for (let i = 0; i < detectedFacades.length; i++) {
            const df = detectedFacades[i];
            if (df.tilt < 15 || df.tilt > 75) continue; // Solo techos inclinados
            let azDiff = Math.abs(solarAzimuth - df.azimuthNormal);
            if (azDiff > 180) azDiff = 360 - azDiff;
            const tiltDiff = Math.abs(faceTilt - df.tilt);
            const score = azDiff + tiltDiff * 0.5; // Ponderar azimut más que tilt
            if (azDiff < 30 && tiltDiff < 25 && score < bestScore) {
              bestScore = score;
              bestMatch = i;
            }
          }
          facadeIdx = bestMatch;
        }

        const geometry = new THREE.BufferGeometry();
        const positions: number[] = [];
        const normals: number[] = [];

        for (let i = 1; i < faceVerts.length - 1; i++) {
          positions.push(faceVerts[0].x, faceVerts[0].y, faceVerts[0].z);
          positions.push(faceVerts[i].x, faceVerts[i].y, faceVerts[i].z);
          positions.push(faceVerts[i + 1].x, faceVerts[i + 1].y, faceVerts[i + 1].z);
          normals.push(normal.x, normal.y, normal.z);
          normals.push(normal.x, normal.y, normal.z);
          normals.push(normal.x, normal.y, normal.z);
        }

        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));

        const color = facadeIdx >= 0
          ? detectedFacades[facadeIdx].color || FACADE_COLORS[facadeIdx % FACADE_COLORS.length]
          : '#E2E8F0';

        meshes.push({ geometry, color, facadeIdx, isVertical: isSurface });
      }
    }

    return meshes;
  }, [parseResult, transformedVertices, detectedFacades, centroid, northOffset]);

  return (
    <group>
      {faceMeshes.map((mesh, i) => {
        const isSelected = mesh.facadeIdx >= 0 && mesh.facadeIdx === selectedFacadeIdx;
        const isHovered = mesh.facadeIdx >= 0 && mesh.facadeIdx === hoveredFacadeIdx;
        
        return (
          <mesh
            key={i}
            geometry={mesh.geometry}
            onClick={(e: ThreeEvent<MouseEvent>) => {
              e.stopPropagation();
              if (mesh.facadeIdx >= 0) onFacadeClick(mesh.facadeIdx);
            }}
            onPointerOver={(e: ThreeEvent<PointerEvent>) => {
              e.stopPropagation();
              if (mesh.facadeIdx >= 0) onFacadeHover(mesh.facadeIdx);
            }}
            onPointerOut={() => {
              if (mesh.facadeIdx >= 0) onFacadeHover(null);
            }}
          >
            <meshStandardMaterial
              color={mesh.color}
              emissive={isSelected ? SELECTED_EMISSIVE : isHovered ? HOVER_EMISSIVE : '#000000'}
              emissiveIntensity={isSelected ? 0.4 : isHovered ? 0.2 : 0}
              side={THREE.DoubleSide}
              transparent={mesh.facadeIdx < 0}
              opacity={mesh.facadeIdx >= 0 ? 1.0 : 0.5}
            />
          </mesh>
        );
      })}
    </group>
  );
}

// ─── Obstacle Meshes ─────────────────────────────────────────────────────────

interface ObstacleMeshesProps {
  obstacleVertices3D: Vertex3D[][];
}

function ObstacleMeshes({ obstacleVertices3D }: ObstacleMeshesProps) {
  const meshes = useMemo(() => {
    return obstacleVertices3D.map((vertices, idx) => {
      if (vertices.length < 3) return null;

      const geometry = new THREE.BufferGeometry();
      const positions: number[] = [];
      const normals: number[] = [];

      for (let i = 1; i < vertices.length - 1; i++) {
        positions.push(vertices[0].x, vertices[0].y, vertices[0].z);
        positions.push(vertices[i].x, vertices[i].y, vertices[i].z);
        positions.push(vertices[i + 1].x, vertices[i + 1].y, vertices[i + 1].z);

        const v0 = new THREE.Vector3(vertices[0].x, vertices[0].y, vertices[0].z);
        const v1 = new THREE.Vector3(vertices[i].x, vertices[i].y, vertices[i].z);
        const v2 = new THREE.Vector3(vertices[i + 1].x, vertices[i + 1].y, vertices[i + 1].z);
        const e1n = new THREE.Vector3().subVectors(v1, v0);
        const e2n = new THREE.Vector3().subVectors(v2, v0);
        const normal = new THREE.Vector3().crossVectors(e1n, e2n).normalize();
        normals.push(normal.x, normal.y, normal.z);
        normals.push(normal.x, normal.y, normal.z);
        normals.push(normal.x, normal.y, normal.z);
      }

      if (positions.length === 0) return null;

      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));

      return { geometry, key: idx };
    }).filter(Boolean) as Array<{ geometry: THREE.BufferGeometry; key: number }>;
  }, [obstacleVertices3D]);

  return (
    <group>
      {meshes.map(({ geometry, key }) => (
        <mesh key={key} geometry={geometry}>
          <meshStandardMaterial
            color={OBSTACLE_COLOR}
            transparent
            opacity={OBSTACLE_OPACITY}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}
    </group>
  );
}

// ─── XYZ Axis Helper ────────────────────────────────────────────────────────

interface AxisHelperProps {
  position: [number, number, number];
  size: number;
}

function AxisHelper({ position, size }: AxisHelperProps) {
  const axisLength = size;
  const coneSize = size * 0.08;

  return (
    <group position={position}>
      {/* X Axis - Red */}
      <Line
        points={[[0, 0, 0], [axisLength, 0, 0]]}
        color="#EF4444"
        lineWidth={3}
      />
      <mesh position={[axisLength + coneSize, 0, 0]} rotation={[0, 0, -Math.PI / 2]}>
        <coneGeometry args={[coneSize, coneSize * 2.5, 8]} />
        <meshBasicMaterial color="#EF4444" />
      </mesh>
      <Text
        position={[axisLength + coneSize * 4, 0, 0]}
        fontSize={size * 0.18}
        color="#EF4444"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
      >
        X
      </Text>

      {/* Y Axis - Green */}
      <Line
        points={[[0, 0, 0], [0, axisLength, 0]]}
        color="#22C55E"
        lineWidth={3}
      />
      <mesh position={[0, axisLength + coneSize, 0]}>
        <coneGeometry args={[coneSize, coneSize * 2.5, 8]} />
        <meshBasicMaterial color="#22C55E" />
      </mesh>
      <Text
        position={[0, axisLength + coneSize * 4, 0]}
        fontSize={size * 0.18}
        color="#22C55E"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
      >
        Y (N)
      </Text>

      {/* Z Axis - Blue */}
      <Line
        points={[[0, 0, 0], [0, 0, axisLength]]}
        color="#3B82F6"
        lineWidth={3}
      />
      <mesh position={[0, 0, axisLength + coneSize]} rotation={[Math.PI / 2, 0, 0]}>
        <coneGeometry args={[coneSize, coneSize * 2.5, 8]} />
        <meshBasicMaterial color="#3B82F6" />
      </mesh>
      <Text
        position={[0, 0, axisLength + coneSize * 4]}
        fontSize={size * 0.18}
        color="#3B82F6"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
      >
        Z (↑)
      </Text>

      {/* Origin sphere */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[coneSize * 0.6, 12, 12]} />
        <meshBasicMaterial color="#6B7280" />
      </mesh>
    </group>
  );
}

// ─── Compass Rose ────────────────────────────────────────────────────────────

interface CompassRoseProps {
  northOffset: number;
  position: [number, number, number];
}

function CompassRose({ northOffset, position }: CompassRoseProps) {
  const groupRef = useRef<THREE.Group>(null);
  const rotation = (-northOffset * Math.PI) / 180;

  return (
    <group ref={groupRef} position={position} rotation={[0, 0, rotation]}>
      {/* North arrow */}
      <Line
        points={[[0, 0, 0], [0, 2, 0]]}
        color="#EF4444"
        lineWidth={3}
      />
      <Text
        position={[0, 2.5, 0]}
        fontSize={0.6}
        color="#EF4444"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
      >
        N
      </Text>
      {/* South */}
      <Line
        points={[[0, 0, 0], [0, -1.5, 0]]}
        color="#64748B"
        lineWidth={1.5}
      />
      <Text
        position={[0, -2, 0]}
        fontSize={0.4}
        color="#64748B"
        anchorX="center"
        anchorY="middle"
      >
        S
      </Text>
      {/* East */}
      <Line
        points={[[0, 0, 0], [1.5, 0, 0]]}
        color="#64748B"
        lineWidth={1.5}
      />
      <Text
        position={[2, 0, 0]}
        fontSize={0.4}
        color="#64748B"
        anchorX="center"
        anchorY="middle"
      >
        E
      </Text>
      {/* West */}
      <Line
        points={[[0, 0, 0], [-1.5, 0, 0]]}
        color="#64748B"
        lineWidth={1.5}
      />
      <Text
        position={[-2, 0, 0]}
        fontSize={0.4}
        color="#64748B"
        anchorX="center"
        anchorY="middle"
      >
        O
      </Text>
    </group>
  );
}

// ─── Evaluation Point Markers ────────────────────────────────────────────────

interface EvalPointMarkersProps {
  facades: DetectedFacade[];
  selectedIdx: number | null;
}

function EvalPointMarkers({ facades, selectedIdx }: EvalPointMarkersProps) {
  return (
    <group>
      {facades.map((facade, idx) => (
        <group key={idx} position={[facade.evaluationPoint.x, facade.evaluationPoint.y, facade.evaluationPoint.z]}>
          <mesh>
            <sphereGeometry args={[0.15, 16, 16]} />
            <meshStandardMaterial
              color={facade.color}
              emissive={idx === selectedIdx ? SELECTED_EMISSIVE : '#000000'}
              emissiveIntensity={idx === selectedIdx ? 0.6 : 0}
            />
          </mesh>
          {idx === selectedIdx && (
            <Html distanceFactor={10} center>
              <div className="bg-white/90 backdrop-blur-sm border border-violet-300 rounded px-2 py-1 text-[10px] whitespace-nowrap shadow-lg pointer-events-none">
                <span className="font-semibold text-violet-800">{facade.name}</span>
                <span className="text-gray-500 ml-1">Az: {facade.azimuthNormal.toFixed(0)}°</span>
              </div>
            </Html>
          )}
        </group>
      ))}
    </group>
  );
}

// ─── Normal Arrows ───────────────────────────────────────────────────────────

interface NormalArrowsProps {
  facades: DetectedFacade[];
  selectedIdx: number | null;
}

function NormalArrows({ facades, selectedIdx }: NormalArrowsProps) {
  return (
    <group>
      {facades.map((facade, idx) => {
        if (idx !== selectedIdx && selectedIdx !== null) return null;
        
        const normalRad = (facade.azimuthNormal + 180) * Math.PI / 180;
        const arrowLength = 2;
        const start: [number, number, number] = [facade.center.x, facade.center.y, facade.center.z];
        const end: [number, number, number] = [
          facade.center.x + Math.sin(normalRad) * arrowLength,
          facade.center.y + Math.cos(normalRad) * arrowLength,
          facade.center.z,
        ];
        
        return (
          <Line
            key={idx}
            points={[start, end]}
            color={facade.color}
            lineWidth={2.5}
            dashed
            dashSize={0.3}
            gapSize={0.15}
          />
        );
      })}
    </group>
  );
}

// ─── Camera Controller (for external button controls) ───────────────────────

interface CameraControllerProps {
  controlsRef: React.RefObject<any>;
  model: EvaluationModel;
  autoRotate: boolean;
}

function CameraController({ controlsRef, model, autoRotate }: CameraControllerProps) {
  const { camera } = useThree();

  useFrame(() => {
    if (controlsRef.current && autoRotate) {
      const azimuthAngle = controlsRef.current.getAzimuthalAngle();
      controlsRef.current.setAzimuthalAngle(azimuthAngle + 0.005);
      controlsRef.current.update();
    }
  });

  return null;
}

// ─── Scene Setup ─────────────────────────────────────────────────────────────

interface SceneProps {
  model: EvaluationModel;
  obstacleVertices3D?: Vertex3D[][];
  selectedFacadeIdx: number | null;
  onFacadeSelect: (idx: number | null) => void;
  northOffset: number;
  controlsRef: React.RefObject<any>;
  autoRotate: boolean;
}

function Scene({ model, obstacleVertices3D, selectedFacadeIdx, onFacadeSelect, northOffset, controlsRef, autoRotate }: SceneProps) {
  const [hoveredFacadeIdx, setHoveredFacadeIdx] = useState<number | null>(null);

  const sceneBounds = useMemo(() => {
    const maxDim = Math.max(model.dimensions.x, model.dimensions.y, model.dimensions.z);
    return maxDim * 1.5;
  }, [model.dimensions]);

  const axisSize = useMemo(() => {
    const maxDim = Math.max(model.dimensions.x, model.dimensions.y, model.dimensions.z);
    return Math.max(maxDim * 0.4, 2);
  }, [model.dimensions]);

  const handleFacadeClick = useCallback((idx: number) => {
    onFacadeSelect(idx === selectedFacadeIdx ? null : idx);
  }, [onFacadeSelect, selectedFacadeIdx]);

  const { gl } = useThree();
  useFrame(() => {
    gl.domElement.style.cursor = hoveredFacadeIdx !== null ? 'pointer' : 'grab';
  });

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 15]} intensity={0.8} castShadow />
      <directionalLight position={[-5, -5, 10]} intensity={0.3} />
      <hemisphereLight args={['#87CEEB', '#F0E68C', 0.3]} />

      {/* Ground Grid */}
      <Grid
        args={[50, 50]}
        position={[model.centroid.x, model.centroid.y, 0]}
        cellSize={1}
        cellThickness={0.5}
        cellColor="#CBD5E1"
        sectionSize={5}
        sectionThickness={1}
        sectionColor="#94A3B8"
        fadeDistance={30}
        fadeStrength={1}
        followCamera={false}
      />

      {/* XYZ Axis Helper - positioned at origin relative to model */}
      <AxisHelper
        position={[
          model.centroid.x - model.dimensions.x * 0.7,
          model.centroid.y - model.dimensions.y * 0.7,
          0,
        ]}
        size={axisSize}
      />

      {/* Building Model */}
      <BuildingMesh
        model={model}
        selectedFacadeIdx={selectedFacadeIdx}
        hoveredFacadeIdx={hoveredFacadeIdx}
        onFacadeClick={handleFacadeClick}
        onFacadeHover={setHoveredFacadeIdx}
        northOffset={northOffset}
      />

      {/* Obstacles */}
      {obstacleVertices3D && obstacleVertices3D.length > 0 && (
        <ObstacleMeshes obstacleVertices3D={obstacleVertices3D} />
      )}

      {/* Evaluation Points */}
      <EvalPointMarkers facades={model.detectedFacades} selectedIdx={selectedFacadeIdx} />

      {/* Normal Arrows */}
      <NormalArrows facades={model.detectedFacades} selectedIdx={selectedFacadeIdx} />

      {/* Compass */}
      <CompassRose northOffset={northOffset} position={[model.centroid.x + sceneBounds, model.centroid.y + sceneBounds, 0.01]} />

      {/* Camera Controller for auto-rotate */}
      <CameraController controlsRef={controlsRef} model={model} autoRotate={autoRotate} />

      {/* Camera Controls - OrbitControls with ref for external manipulation */}
      <OrbitControls
        ref={controlsRef}
        makeDefault
        target={[model.centroid.x, model.centroid.y, model.centroid.z]}
        minDistance={1}
        maxDistance={200}
        maxPolarAngle={Math.PI * 0.9}
        enableDamping
        dampingFactor={0.12}
        rotateSpeed={0.8}
        zoomSpeed={1.2}
        panSpeed={0.8}
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        mouseButtons={{
          LEFT: THREE.MOUSE.ROTATE,
          MIDDLE: THREE.MOUSE.DOLLY,
          RIGHT: THREE.MOUSE.PAN,
        }}
        touches={{
          ONE: THREE.TOUCH.ROTATE,
          TWO: THREE.TOUCH.DOLLY_PAN,
        }}
      />
    </>
  );
}

// ─── Info Panel ──────────────────────────────────────────────────────────────

interface InfoPanelProps {
  facade: DetectedFacade | null;
  model: EvaluationModel;
}

function InfoPanel({ facade, model }: InfoPanelProps) {
  if (!facade) {
    return (
      <div className="absolute bottom-3 left-3 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-lg px-3 py-2 shadow-md pointer-events-none">
        <p className="text-[10px] text-gray-500 flex items-center gap-1">
          <Info size={10} />
          Clic en una fachada para ver detalles
        </p>
      </div>
    );
  }

  return (
    <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur-sm border border-violet-200 rounded-lg px-4 py-3 shadow-lg max-w-[280px] pointer-events-none">
      <div className="flex items-center gap-2 mb-2">
        <span
          className="w-3 h-3 rounded-sm border border-gray-300"
          style={{ backgroundColor: facade.color }}
        />
        <h4 className="text-xs font-bold text-gray-900">{facade.name}</h4>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
        <div className="col-span-2">
          <span className="text-gray-500">Tipo:</span>
          <span className="ml-1 font-semibold text-violet-700">
            {facade.tilt < 15 ? '🏠 Techo Plano' : facade.tilt <= 75 ? '△ Techo Inclinado (Agua)' : '🧱 Muro/Fachada'}
          </span>
        </div>
        <div>
          <span className="text-gray-500">Azimut Normal:</span>
          <span className="ml-1 font-mono font-semibold">{facade.azimuthNormal.toFixed(1)}°</span>
        </div>
        <div>
          <span className="text-gray-500">Inclinación:</span>
          <span className="ml-1 font-mono font-semibold">{facade.tilt.toFixed(1)}°</span>
        </div>
        <div>
          <span className="text-gray-500">Área:</span>
          <span className="ml-1 font-mono font-semibold">{facade.area.toFixed(1)} m²</span>
        </div>
        <div>
          <span className="text-gray-500">Centro:</span>
          <span className="ml-1 font-mono font-semibold text-[9px]">
            ({facade.center.x.toFixed(1)}, {facade.center.y.toFixed(1)}, {facade.center.z.toFixed(1)})
          </span>
        </div>
      </div>
      <div className="mt-2 pt-2 border-t border-gray-100 text-[10px] text-gray-500">
        Punto de evaluación: ({facade.evaluationPoint.x.toFixed(1)}, {facade.evaluationPoint.y.toFixed(1)}, {facade.evaluationPoint.z.toFixed(1)})
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function ModelViewer3D({
  model,
  obstacleVertices3D,
  selectedFacadeIdx,
  onFacadeSelect,
  northOffset = 0,
  height = 400,
}: ModelViewer3DProps) {
  const [internalSelectedIdx, setInternalSelectedIdx] = useState<number | null>(selectedFacadeIdx);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [autoRotate, setAutoRotate] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<any>(null);

  const currentSelectedIdx = selectedFacadeIdx ?? internalSelectedIdx;
  const handleFacadeSelect = useCallback((idx: number | null) => {
    setInternalSelectedIdx(idx);
    onFacadeSelect?.(idx);
  }, [onFacadeSelect]);

  const selectedFacade = currentSelectedIdx !== null
    ? model.detectedFacades[currentSelectedIdx] ?? null
    : null;

  // Calculate camera position based on model size
  const cameraPosition = useMemo((): [number, number, number] => {
    const maxDim = Math.max(model.dimensions.x, model.dimensions.y, model.dimensions.z);
    const distance = maxDim * 2.5;
    return [
      model.centroid.x + distance * 0.7,
      model.centroid.y - distance * 0.7,
      model.centroid.z + distance * 0.5,
    ];
  }, [model]);

  // ─── Control Handlers ───────────────────────────────────────────────────────

  const handleZoomIn = useCallback(() => {
    if (controlsRef.current) {
      const controls = controlsRef.current;
      const currentDistance = controls.getDistance();
      const newDistance = Math.max(currentDistance * 0.7, controls.minDistance);
      // Dolly in by adjusting camera position
      const direction = new THREE.Vector3();
      controls.object.getWorldDirection(direction);
      controls.object.position.addScaledVector(direction, currentDistance - newDistance);
      controls.update();
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (controlsRef.current) {
      const controls = controlsRef.current;
      const currentDistance = controls.getDistance();
      const newDistance = Math.min(currentDistance * 1.4, controls.maxDistance);
      const direction = new THREE.Vector3();
      controls.object.getWorldDirection(direction);
      controls.object.position.addScaledVector(direction, currentDistance - newDistance);
      controls.update();
    }
  }, []);

  const handleResetView = useCallback(() => {
    if (controlsRef.current) {
      const controls = controlsRef.current;
      const maxDim = Math.max(model.dimensions.x, model.dimensions.y, model.dimensions.z);
      const distance = maxDim * 2.5;
      controls.object.position.set(
        model.centroid.x + distance * 0.7,
        model.centroid.y - distance * 0.7,
        model.centroid.z + distance * 0.5,
      );
      controls.target.set(model.centroid.x, model.centroid.y, model.centroid.z);
      controls.update();
    }
    setAutoRotate(false);
  }, [model]);

  const handleToggleAutoRotate = useCallback(() => {
    setAutoRotate(prev => !prev);
  }, []);

  const handleFullscreen = useCallback(() => {
    if (!containerRef.current) return;
    
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch((err) => {
        console.warn('Fullscreen not available:', err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      }).catch(() => {});
    }
  }, []);

  // Listen for fullscreen change events
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative rounded-xl overflow-hidden border border-violet-200 bg-gradient-to-b from-sky-100 to-sky-50"
      style={{ height: isFullscreen ? '100vh' : height }}
    >
      {/* Legend - pointer-events-none to not block canvas */}
      <div className="absolute top-3 left-3 z-10 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-lg px-3 py-2 shadow-sm pointer-events-none">
        <p className="text-[10px] font-semibold text-gray-700 mb-1">Leyenda</p>
        <div className="space-y-0.5">
          {model.detectedFacades.map((f, i) => (
            <div key={i} className="flex items-center gap-1.5 text-[9px]">
              <span className="w-2.5 h-2.5 rounded-sm border border-gray-300" style={{ backgroundColor: f.color }} />
              <span className="text-gray-600">{f.name} ({f.tilt < 15 ? `${f.tilt.toFixed(0)}°` : `${f.azimuthNormal.toFixed(0)}°`})</span>
            </div>
          ))}
          {obstacleVertices3D && obstacleVertices3D.length > 0 && (
            <div className="flex items-center gap-1.5 text-[9px]">
              <span className="w-2.5 h-2.5 rounded-sm border border-gray-300" style={{ backgroundColor: OBSTACLE_COLOR, opacity: 0.5 }} />
              <span className="text-gray-600">Obstáculos ({obstacleVertices3D.length})</span>
            </div>
          )}
        </div>
      </div>

      {/* Axis Legend - pointer-events-none */}
      <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-lg px-3 py-1.5 shadow-sm pointer-events-none">
        <div className="flex items-center gap-3 text-[9px] font-medium">
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-red-500 inline-block rounded" />
            <span className="text-red-600">X</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-green-500 inline-block rounded" />
            <span className="text-green-600">Y (Norte)</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-blue-500 inline-block rounded" />
            <span className="text-blue-600">Z (Arriba)</span>
          </span>
        </div>
      </div>

      {/* Functional Control Buttons - these DO need pointer-events */}
      <div className="absolute top-3 right-3 z-10 flex flex-col gap-1">
        {/* Rotate toggle */}
        <Button
          variant="outline"
          size="sm"
          className={`h-7 w-7 p-0 bg-white/90 backdrop-blur-sm border-gray-300 shadow-sm hover:bg-violet-50 ${autoRotate ? 'bg-violet-100 border-violet-400' : ''}`}
          onClick={handleToggleAutoRotate}
          title="Auto-rotar"
        >
          <RotateCw size={13} className={autoRotate ? 'text-violet-600' : 'text-gray-600'} />
        </Button>

        {/* Zoom In */}
        <Button
          variant="outline"
          size="sm"
          className="h-7 w-7 p-0 bg-white/90 backdrop-blur-sm border-gray-300 shadow-sm hover:bg-violet-50"
          onClick={handleZoomIn}
          title="Zoom In"
        >
          <ZoomIn size={13} className="text-gray-600" />
        </Button>

        {/* Zoom Out */}
        <Button
          variant="outline"
          size="sm"
          className="h-7 w-7 p-0 bg-white/90 backdrop-blur-sm border-gray-300 shadow-sm hover:bg-violet-50"
          onClick={handleZoomOut}
          title="Zoom Out"
        >
          <ZoomOut size={13} className="text-gray-600" />
        </Button>

        {/* Reset View */}
        <Button
          variant="outline"
          size="sm"
          className="h-7 w-7 p-0 bg-white/90 backdrop-blur-sm border-gray-300 shadow-sm hover:bg-violet-50"
          onClick={handleResetView}
          title="Resetear vista"
        >
          <Home size={13} className="text-gray-600" />
        </Button>

        {/* Fullscreen */}
        <Button
          variant="outline"
          size="sm"
          className="h-7 w-7 p-0 bg-white/90 backdrop-blur-sm border-gray-300 shadow-sm hover:bg-violet-50"
          onClick={handleFullscreen}
          title={isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa'}
        >
          {isFullscreen
            ? <Minimize2 size={13} className="text-gray-600" />
            : <Maximize2 size={13} className="text-gray-600" />
          }
        </Button>
      </div>

      {/* Mouse interaction hints - bottom right, pointer-events-none */}
      <div className="absolute bottom-3 right-3 z-10 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-lg px-2.5 py-1.5 shadow-sm pointer-events-none">
        <div className="flex flex-col gap-0.5 text-[8px] text-gray-500">
          <span>🖱️ Izq: Rotar | Der: Pan</span>
          <span>🔲 Scroll: Zoom | Doble-clic: Centrar</span>
        </div>
      </div>

      {/* Three.js Canvas */}
      <Canvas
        camera={{
          position: cameraPosition,
          fov: 50,
          near: 0.01,
          far: 2000,
          up: [0, 0, 1],
        }}
        shadows
        gl={{ antialias: true, alpha: true, preserveDrawingBuffer: true }}
        onPointerMissed={() => handleFacadeSelect(null)}
        style={{ touchAction: 'none' }}
      >
        <Suspense fallback={null}>
          <Scene
            model={model}
            obstacleVertices3D={obstacleVertices3D}
            selectedFacadeIdx={currentSelectedIdx}
            onFacadeSelect={handleFacadeSelect}
            northOffset={northOffset}
            controlsRef={controlsRef}
            autoRotate={autoRotate}
          />
        </Suspense>
      </Canvas>

      {/* Info Panel */}
      <InfoPanel facade={selectedFacade} model={model} />
    </div>
  );
}
