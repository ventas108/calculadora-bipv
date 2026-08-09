# -*- coding: utf-8 -*-
"""
Comparativo SketchUp vs Site Designer — Fase 5
==============================================
Confirma que las dos rutas de sombreado dan sombras COMPARABLES sobre el
mismo caso real: la misma caja de obstáculo construida (a) como JSON de
Site Designer (min/max en mm) y (b) como OBJ en metros del flujo SketchUp
deben producir un FS_geometrico idéntico hora a hora.

No se usa TMY real (no hay red): ``calcular_fs_horario`` corre con su índice
horario típico por defecto.
"""
import numpy as np
import pandas as pd

from calculos.sitedesigner_marsh import cargar_escena_sitedesigner
from calculos.sombras_3d import cargar_malla, calcular_fs_horario


# ── Caso real: Bogotá, edificio vecino alto al este/norte del punto ──────────
LAT_BOGOTA = 4.702
LON_BOGOTA = -74.147

# Caja del obstáculo en mm (convención Site Designer) — vecino alto al este/
# norte del punto de fachada. min/max en milímetros.
MIN_MM = [2000, 500, 0]
MAX_MM = [8000, 12000, 30000]

# El mismo volumen en METROS (mm → m) para construir el OBJ de SketchUp.
MIN_M = np.array(MIN_MM, dtype=float) * 0.001
MAX_M = np.array(MAX_MM, dtype=float) * 0.001

# Punto de fachada Norte, a z=1.5 m, al oeste/sur del obstáculo.
PUNTOS = [{
    "nombre": "P1", "fachada": "Norte", "fila": "Fila 1",
    "n_modulos": 1, "area_activa_m2": 0.0, "potencia_instalada_kw": 0.0,
    "x": 0.0, "y": 0.0, "z": 1.5,
}]


def _obj_caja_bytes(vmin, vmax):
    """
    Genera el OBJ (bytes) de una caja alineada a los ejes con 8 vértices y
    12 triángulos, en metros. Coordenadas idénticas a las que produce
    Site Designer tras mm→m, para que ambas rutas partan del mismo volumen.
    """
    x0, y0, z0 = float(vmin[0]), float(vmin[1]), float(vmin[2])
    x1, y1, z1 = float(vmax[0]), float(vmax[1]), float(vmax[2])
    vertices = [
        (x0, y0, z0),  # 1
        (x1, y0, z0),  # 2
        (x1, y1, z0),  # 3
        (x0, y1, z0),  # 4
        (x0, y0, z1),  # 5
        (x1, y0, z1),  # 6
        (x1, y1, z1),  # 7
        (x0, y1, z1),  # 8
    ]
    # 12 triángulos (2 por cara × 6 caras), índices OBJ 1-based.
    caras = [
        (1, 2, 3), (1, 3, 4),   # z = z0 (abajo)
        (5, 7, 6), (5, 8, 7),   # z = z1 (arriba)
        (1, 6, 2), (1, 5, 6),   # y = y0
        (4, 3, 7), (4, 7, 8),   # y = y1
        (1, 4, 8), (1, 8, 5),   # x = x0
        (2, 6, 7), (2, 7, 3),   # x = x1
    ]
    lineas = [f"v {vx:.6f} {vy:.6f} {vz:.6f}" for vx, vy, vz in vertices]
    lineas += [f"f {a} {b} {c}" for a, b, c in caras]
    return ("\n".join(lineas) + "\n").encode("utf-8")


def _merge_fs(df_sd, df_obj):
    """Une ambos resultados por Mes/Dia/Hora/Punto para comparar FS 1:1."""
    claves = ["Mes", "Dia", "Hora", "Punto"]
    a = df_sd[claves + ["FS_geometrico"]].rename(columns={"FS_geometrico": "fs_sd"})
    b = df_obj[claves + ["FS_geometrico"]].rename(columns={"FS_geometrico": "fs_obj"})
    fusion = a.merge(b, on=claves, how="outer")
    return fusion


def test_misma_caja_sketchup_vs_sitedesigner_fs_identico():
    """(a) JSON Site Designer y (b) OBJ en metros del MISMO volumen → FS igual."""
    escena = (
        '{"Location": {"latitude": %s, "longitude": %s, "timezone": -5, '
        '"northOffset": 0, "elevation": 2548.4}, '
        '"Blocks": [{"min": %s, "max": %s}]}'
    ) % (LAT_BOGOTA, LON_BOGOTA, MIN_MM, MAX_MM)

    malla_sd, meta = cargar_escena_sitedesigner(escena)
    malla_obj = cargar_malla(_obj_caja_bytes(MIN_M, MAX_M), "obj", escala=1.0)

    df_sd = calcular_fs_horario(malla_sd, PUNTOS, LAT_BOGOTA, LON_BOGOTA)
    df_obj = calcular_fs_horario(malla_obj, PUNTOS, LAT_BOGOTA, LON_BOGOTA)

    fusion = _merge_fs(df_sd, df_obj)
    # Ninguna hora debe quedar sin par (misma malla física, mismas horas con sol).
    assert fusion["fs_sd"].notna().all()
    assert fusion["fs_obj"].notna().all()
    # El obstáculo debe generar sombra en alguna hora (caso no trivial).
    assert fusion["fs_sd"].max() == 1.0
    # FS idéntico hora a hora por ambas rutas.
    assert (fusion["fs_sd"].to_numpy() == fusion["fs_obj"].to_numpy()).all()


def test_north_offset_7_sketchup_vs_sitedesigner_fs_identico():
    """northOffset=7 (JSON) == rotacion_norte_deg=7.0 (OBJ) → FS igual hora a hora."""
    escena = (
        '{"Location": {"latitude": %s, "longitude": %s, "timezone": -5, '
        '"northOffset": 7, "elevation": 2548.4}, '
        '"Blocks": [{"min": %s, "max": %s}]}'
    ) % (LAT_BOGOTA, LON_BOGOTA, MIN_MM, MAX_MM)

    malla_sd, _ = cargar_escena_sitedesigner(escena)
    malla_obj = cargar_malla(
        _obj_caja_bytes(MIN_M, MAX_M), "obj", escala=1.0, rotacion_norte_deg=7.0
    )

    df_sd = calcular_fs_horario(malla_sd, PUNTOS, LAT_BOGOTA, LON_BOGOTA)
    df_obj = calcular_fs_horario(malla_obj, PUNTOS, LAT_BOGOTA, LON_BOGOTA)

    fusion = _merge_fs(df_sd, df_obj)
    assert fusion["fs_sd"].notna().all()
    assert fusion["fs_obj"].notna().all()
    assert (fusion["fs_sd"].to_numpy() == fusion["fs_obj"].to_numpy()).all()
