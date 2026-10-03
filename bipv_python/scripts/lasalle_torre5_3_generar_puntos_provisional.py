# -*- coding: utf-8 -*-
"""v2: parametrizado por ancho_so_m, para que cada escena de sensibilidad use
puntos correctos relativos a SU PROPIO footprint (el bug de v1 reutilizaba
los puntos de la escena central de 17.29m para las escenas de 12m/25m,
dejando puntos dentro o mal ubicados)."""
import json
import numpy as np
import trimesh

ANCHO_SE_M = 17.2905
ALTO_M = 36.4178
N_PISOS = 13
ALTO_PISO_M = ALTO_M / N_PISOS
OFFSET_PUNTO_M = 0.5
NORTH_OFFSET = 160.5
MODULOS_TOTAL_FACHADA = 70

ang = -np.deg2rad(NORTH_OFFSET)
R = trimesh.transformations.rotation_matrix(ang, [0, 0, 1])[:3, :3]

def rotar(x, y, z):
    v = R @ np.array([x, y, z])
    return float(v[0]), float(v[1]), float(v[2])

def generar(ancho_so_m):
    puntos_se, puntos_so = [], []
    for i in range(1, N_PISOS + 1):
        z = (i - 0.5) * ALTO_PISO_M
        x_se, y_se, z_se = rotar(ancho_so_m / 2.0, ANCHO_SE_M + OFFSET_PUNTO_M, z)
        puntos_se.append({
            "nombre": f"SE-piso{i:02d}", "fachada": "Sureste", "fila": i,
            "x": round(x_se, 4), "y": round(y_se, 4), "z": round(z_se, 4),
            "modulos_representados_aprox": round(MODULOS_TOTAL_FACHADA / N_PISOS, 2),
        })
        # Centro de la cara SO: a lo largo de Y (longitud ANCHO_SE_M), no ancho_so/2.
        x_so, y_so, z_so = rotar(ancho_so_m + OFFSET_PUNTO_M, ANCHO_SE_M / 2.0, z)
        puntos_so.append({
            "nombre": f"SO-piso{i:02d}", "fachada": "Suroeste", "fila": i,
            "x": round(x_so, 4), "y": round(y_so, 4), "z": round(z_so, 4),
            "modulos_representados_aprox": round(MODULOS_TOTAL_FACHADA / N_PISOS, 2),
        })
    return {"puntos_Fachada-Sureste": puntos_se, "puntos_Fachada-Suroeste": puntos_so}

from pathlib import Path
G = str(Path(__file__).resolve().parents[2] / "references" / "lasalle_torre5_geom")
for etiqueta, ancho_so in [("central", 17.2905), ("estrecha_12m", 12.0), ("ancha_25m", 25.0)]:
    out = generar(ancho_so)
    with open(f"{G}/puntos_analisis_{etiqueta}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(etiqueta, "SO piso1:", out["puntos_Fachada-Suroeste"][0])
