# -*- coding: utf-8 -*-
"""Deriva y VERIFICA numericamente (no a mano) el northOffset necesario para
que un bloque rectangular simple, con footprint cuadrado 17.2905 x 17.2905 m
(ancho medido de la fachada SE, Fig.4 tesis) y altura 36.4178 m (medida,
misma figura), quede orientado con sus dos caras adyacentes apuntando a los
azimuts reales de las fachadas SO=249 grados y SE=162 grados (convencion
pvlib), idealizando la esquina a 90 grados exactos (la diferencia real es
87 grados; se reparte el error 1.5 grados a cada lado, documentado)."""
import numpy as np
import trimesh

ANCHO_SE_M = 17.2905   # medido, Fig. 4 tesis
ANCHO_SO_M = 17.2905   # ASUMIDO = ancho SE (ver justificacion en el informe)
ALTO_M = 36.4178       # medido, Fig. 4 tesis

AZ_SE_REAL = 162.0
AZ_SO_REAL = 249.0
GAP_REAL = AZ_SO_REAL - AZ_SE_REAL
print(f"gap real SE->SO: {GAP_REAL} grados (idealizado a 90)")

# Reparto simetrico del error de idealizacion
error = 90.0 - GAP_REAL
AZ_SE_IDEAL = AZ_SE_REAL - error / 2.0
AZ_SO_IDEAL = AZ_SO_REAL + error / 2.0
print(f"AZ_SE_IDEAL={AZ_SE_IDEAL}, AZ_SO_IDEAL={AZ_SO_IDEAL}, gap={AZ_SO_IDEAL-AZ_SE_IDEAL}")

def azimut_de_normal(nx, ny):
    """pvlib: 0=N,90=E,180=S,270=O medido horario desde el norte."""
    az = np.degrees(np.arctan2(nx, ny)) % 360.0
    return az

# Construir bloque axis-aligned local: X en [0,ANCHO_SO], Y en [0,ANCHO_SE], Z en [0,ALTO]
# Antes de rotar, cara +Y (normal local (0,1,0)) = "cara SE local" (azimut local 0 = norte local)
# cara +X (normal local (1,0,0)) = "cara SO local" (azimut local 90)
box = trimesh.creation.box(bounds=[[0, 0, 0], [ANCHO_SO_M, ANCHO_SE_M, ALTO_M]])

def azimut_resultante_tras_rotacion(north_offset_deg):
    m = box.copy()
    ang = -np.deg2rad(north_offset_deg)  # misma convencion que sitedesigner_marsh.py
    m.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 0, 1]))
    # normal de la cara +Y local tras rotacion (buscar la cara cuya normal original era (0,1,0))
    normales = m.face_normals
    # normal original de cada cara del box sin rotar
    box_normales = box.face_normals
    idx_y = np.argmax(box_normales @ np.array([0, 1, 0]))
    idx_x = np.argmax(box_normales @ np.array([1, 0, 0]))
    n_se = normales[idx_y]
    n_so = normales[idx_x]
    az_se = azimut_de_normal(n_se[0], n_se[1])
    az_so = azimut_de_normal(n_so[0], n_so[1])
    return az_se, az_so

# El northOffset buscado: queremos que la cara +Y local (azimut local 0) termine en AZ_SE_IDEAL
candidato = AZ_SE_IDEAL
az_se, az_so = azimut_resultante_tras_rotacion(candidato)
print(f"\ncandidato northOffset={candidato:.4f}")
print(f"  cara SE resultante: az={az_se:.4f} (objetivo {AZ_SE_IDEAL:.4f})")
print(f"  cara SO resultante: az={az_so:.4f} (objetivo {AZ_SO_IDEAL:.4f})")

assert abs(((az_se - AZ_SE_IDEAL + 180) % 360) - 180) < 0.05, "cara SE no coincide"
assert abs(((az_so - AZ_SO_IDEAL + 180) % 360) - 180) < 0.05, "cara SO no coincide"
print("\nVERIFICADO: northOffset correcto, ambas caras coinciden con los azimuts idealizados.")

NORTH_OFFSET_FINAL = round(candidato, 4)
print(f"\nNORTH_OFFSET_FINAL = {NORTH_OFFSET_FINAL}")
print(f"Discrepancia vs valores reales medidos: SE {abs(AZ_SE_IDEAL-AZ_SE_REAL):.2f} deg, SO {abs(AZ_SO_IDEAL-AZ_SO_REAL):.2f} deg")
