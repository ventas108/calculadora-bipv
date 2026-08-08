# -*- coding: utf-8 -*-
"""
sombras_3d.py — Sombras horarias desde modelos 3D de SketchUp (Opción A)
=========================================================================
Lógica pura (sin Streamlit):

1. Cargar una malla 3D exportada de SketchUp (OBJ / STL / DAE / PLY / GLB)
   con corrección de unidades y de rotación de norte.
2. Calcular la posición del sol hora a hora (pvlib) — idealmente sobre el
   MISMO índice del TMY del proyecto, para alineación perfecta con Producción.
3. Ray-casting: por cada punto de análisis y cada hora con sol, lanzar un
   rayo hacia el sol; si choca contra la malla → sombra (FS_geometrico = 1,
   atenuado por la transparencia opcional para árboles).
4. Exportar el CSV en el MISMO formato que la Calculadora de Sombreado 3D
   (Mes, Dia, Hora, FS_geometrico, FS, Fachada) → entra sin cambios a la
   Página 5 (Mismatch/Bypass) y de ahí a Producción y Financiero.

Convenciones geométricas (las de SketchUp):
  X = Este (eje rojo), Y = Norte (eje verde), Z = arriba (eje azul), en METROS.
  Si el norte del modelo no coincide con el eje verde, usar rotacion_norte_deg
  (ángulo horario que hay que girar el modelo para que Y apunte al norte real).
"""
from __future__ import annotations

import io

import numpy as np
import pandas as pd

try:
    import trimesh
    TRIMESH_OK = True
except Exception:  # pragma: no cover
    trimesh = None
    TRIMESH_OK = False

import pvlib

ALTURA_SOLAR_MIN_DEG = 1.0   # bajo esto el sol "no cuenta" (horizonte/ruido)
OFFSET_RAYO_M = 0.05         # separar el origen del rayo de la superficie propia


# ══════════════════════════════════════════════════════════════════════════════
# 1. Carga y normalización de la malla
# ══════════════════════════════════════════════════════════════════════════════
def cargar_malla(archivo, tipo: str, escala: float = 1.0,
                 rotacion_norte_deg: float = 0.0):
    """
    archivo: ruta (str) o bytes del modelo exportado de SketchUp.
    tipo: extensión sin punto ('obj', 'stl', 'dae', 'ply', 'glb').
    escala: factor a metros (1.0 si ya está en metros; 0.0254 si en pulgadas).
    rotacion_norte_deg: giro horario (visto desde arriba) para alinear el eje
      verde (Y) del modelo con el norte real.

    Retorna un trimesh.Trimesh único (escenas se aplanan).
    """
    if not TRIMESH_OK:
        raise ImportError("trimesh no está instalado (pip install trimesh)")

    if isinstance(archivo, (bytes, bytearray)):
        obj = trimesh.load(io.BytesIO(archivo), file_type=tipo, force="mesh")
    else:
        obj = trimesh.load(archivo, force="mesh")

    if isinstance(obj, trimesh.Scene):  # por si force="mesh" no aplanó
        obj = obj.to_mesh()
    if obj.vertices.shape[0] == 0 or obj.faces.shape[0] == 0:
        raise ValueError("El modelo no contiene geometría (¿exportaste solo aristas?)")
    if not np.isfinite(obj.vertices).all():
        obj.update_vertices(np.isfinite(obj.vertices).all(axis=1))
        if obj.faces.shape[0] == 0:
            raise ValueError("El modelo solo contiene geometría inválida (vértices no finitos)")
    if obj.faces.shape[0] > MAX_TRIANGULOS:
        raise ValueError(
            f"El modelo tiene {obj.faces.shape[0]:,} triángulos (máx. {MAX_TRIANGULOS:,}). "
            "Simplifícalo en SketchUp: borra mobiliario/detalle, deja solo los volúmenes "
            "que producen sombra."
        )

    if escala and escala != 1.0:
        obj.apply_scale(float(escala))
    if rotacion_norte_deg:
        # giro horario visto desde arriba = giro -θ alrededor de Z
        ang = -np.deg2rad(float(rotacion_norte_deg))
        obj.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 0, 1]))
    return obj


MAX_TRIANGULOS = 300_000     # más allá, el ray-casting puro-Python se vuelve inviable
MAX_RAYOS = 6_000_000        # presupuesto puntos × horas con sol


def estimar_rayos(n_puntos: int, n_horas_sol: int = 4400) -> int:
    return int(n_puntos) * int(n_horas_sol)


def validar_puntos(malla, puntos: list[dict], offset: float = OFFSET_RAYO_M) -> list[str]:
    """
    Devuelve lista de advertencias/errores por punto:
    - punto DENTRO de un sólido cerrado (reportaría sombra total falsa),
    - punto pegado (< offset×2) a la malla (el rayo puede nacer dentro del obstáculo).
    """
    avisos = []
    coords = np.array([[float(p["x"]), float(p["y"]), float(p["z"])] for p in puntos])
    if not np.isfinite(coords).all():
        return ["Hay coordenadas no numéricas en los puntos."]
    try:
        if malla.is_watertight:
            dentro = malla.contains(coords)
            for p, d in zip(puntos, dentro):
                if d:
                    avisos.append(
                        f"El punto «{p.get('nombre', '?')}» está DENTRO del modelo — "
                        "daría sombra total falsa. Revisa sus coordenadas."
                    )
        cercania = trimesh.proximity.signed_distance(malla, coords)
        for p, dist in zip(puntos, np.abs(cercania)):
            if np.isfinite(dist) and dist < offset * 2:
                avisos.append(
                    f"El punto «{p.get('nombre', '?')}» está a {dist*100:.0f} cm de la malla — "
                    "muy pegado al obstáculo, el resultado puede ser ambiguo."
                )
    except Exception:
        pass  # validación best-effort: nunca debe tumbar el cálculo
    return avisos


def resumen_malla(malla) -> dict:
    """Datos de sanidad para mostrar en la UI antes de calcular."""
    bb = malla.bounds
    return {
        "n_triangulos": int(malla.faces.shape[0]),
        "n_vertices": int(malla.vertices.shape[0]),
        "dim_x_m": round(float(bb[1][0] - bb[0][0]), 2),
        "dim_y_m": round(float(bb[1][1] - bb[0][1]), 2),
        "dim_z_m": round(float(bb[1][2] - bb[0][2]), 2),
        "z_min": round(float(bb[0][2]), 2),
        "z_max": round(float(bb[1][2]), 2),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. Posición solar — alineada con el TMY del proyecto
# ══════════════════════════════════════════════════════════════════════════════
def posiciones_solares(lat: float, lon: float,
                       indice_tmy: pd.DatetimeIndex | None = None,
                       tz: str = "America/Bogota") -> pd.DataFrame:
    """
    Retorna DataFrame indexado por hora con columnas:
      elevacion (deg), acimut (deg, desde el norte horario), mes, dia, hora.

    Si se pasa el índice del TMY del proyecto se usa TAL CUAL → las horas del
    CSV coinciden 1:1 con las horas que usa Producción (misma convención de
    'mes, dia, hora' que alinea la Página 5). Si no, se genera un año típico
    horario en hora local.
    """
    if indice_tmy is not None and len(indice_tmy) > 0:
        idx = pd.DatetimeIndex(indice_tmy)
        if idx.tz is None:
            idx = idx.tz_localize("UTC")
    else:
        idx = pd.date_range("2023-01-01 00:00", "2023-12-31 23:00",
                            freq="h", tz=tz)

    sol = pvlib.solarposition.get_solarposition(idx, lat, lon)
    df = pd.DataFrame({
        "elevacion": sol["apparent_elevation"].to_numpy(),
        "acimut": sol["azimuth"].to_numpy(),
    }, index=idx)
    df["mes"] = idx.month
    df["dia"] = idx.day
    df["hora"] = idx.hour
    return df


def vector_al_sol(elevacion_deg, acimut_deg) -> np.ndarray:
    """
    Dirección unitaria HACIA el sol en coordenadas del modelo:
    X=Este, Y=Norte, Z=arriba. Acimut medido desde el norte, horario
    (convención pvlib). Acepta escalares o arrays.
    """
    el = np.deg2rad(np.asarray(elevacion_deg, dtype=float))
    az = np.deg2rad(np.asarray(acimut_deg, dtype=float))
    return np.stack([
        np.sin(az) * np.cos(el),   # Este
        np.cos(az) * np.cos(el),   # Norte
        np.sin(el),                # arriba
    ], axis=-1)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Ray-casting horario
# ══════════════════════════════════════════════════════════════════════════════
def calcular_fs_horario(
    malla,
    puntos: list[dict],
    lat: float,
    lon: float,
    indice_tmy: pd.DatetimeIndex | None = None,
    transparencia: float = 0.0,
    altura_min_deg: float = ALTURA_SOLAR_MIN_DEG,
) -> pd.DataFrame:
    """
    puntos: lista de {"nombre": str, "fachada": str, "x": m, "y": m, "z": m}.
    transparencia: 0.0 = obstáculo sólido (edificio); 0.3–0.6 típico de árboles
      (fracción de luz que SÍ pasa cuando el rayo choca). FS = 1 - transparencia.

    Retorna DataFrame largo con columnas:
      Mes, Dia, Hora, Altura Solar (deg), Acimut Solar (deg),
      FS_geometrico, FS, Fachada, Punto
    Una fila por punto × hora con sol. Horas sin sol no se exportan
    (FS irrelevante: no hay irradiancia directa que recortar).
    """
    if not puntos:
        raise ValueError("Define al menos un punto de análisis")

    sol = posiciones_solares(lat, lon, indice_tmy)
    con_sol = sol[sol["elevacion"] > altura_min_deg]
    if con_sol.empty:
        raise ValueError("Ninguna hora con sol — revisa latitud/longitud")

    dirs = vector_al_sol(con_sol["elevacion"].to_numpy(),
                         con_sol["acimut"].to_numpy())          # (H, 3)
    n_h = dirs.shape[0]
    fs_choque = float(np.clip(1.0 - transparencia, 0.0, 1.0))

    filas = []
    for pt in puntos:
        origen = np.array([float(pt["x"]), float(pt["y"]), float(pt["z"])])
        origenes = np.repeat(origen[None, :], n_h, axis=0) + dirs * OFFSET_RAYO_M
        hits = malla.ray.intersects_any(ray_origins=origenes,
                                        ray_directions=dirs)     # (H,) bool
        fs_geo = np.where(hits, fs_choque, 0.0)
        filas.append(pd.DataFrame({
            "timestamp_utc": [
                pd.Timestamp(ts).tz_convert("UTC").isoformat().replace("+00:00", "Z")
                for ts in con_sol.index
            ],
            "Mes": con_sol["mes"].to_numpy(),
            "Dia": con_sol["dia"].to_numpy(),
            "Hora": con_sol["hora"].to_numpy(),
            "Altura Solar (deg)": np.round(con_sol["elevacion"].to_numpy(), 2),
            "Acimut Solar (deg)": np.round(con_sol["acimut"].to_numpy(), 2),
            "FS_geometrico": np.round(fs_geo, 4),
            "FS": np.round(fs_geo, 4),
            "Fachada": pt.get("fachada") or "Principal",
            "Punto": pt.get("nombre") or "P1",
        }))
    return pd.concat(filas, ignore_index=True)


def resumen_fs(df_fs: pd.DataFrame) -> dict:
    """Estadísticas para la UI."""
    horas_sombra = df_fs[df_fs["FS"] > 0]
    return {
        "puntos": int(df_fs["Punto"].nunique()),
        "horas_evaluadas": int(len(df_fs) / max(1, df_fs["Punto"].nunique())),
        "registros_con_sombra": int(len(horas_sombra)),
        "pct_horas_con_sombra": round(100.0 * len(horas_sombra) / max(1, len(df_fs)), 1),
        "fs_medio_con_sombra": round(float(horas_sombra["FS"].mean()), 3) if len(horas_sombra) else 0.0,
    }


def exportar_csv_fs(df_fs: pd.DataFrame) -> bytes:
    """
    CSV en el formato que consume la Página 5 (cargar_csv_fs):
    columnas con FS_geometrico (prioritaria en el parser: sombra física pura,
    las nubes NO deben activar bypass) + Fachada. Convención 0=sin sombra,
    1=sombra total — la nativa del modelo bypass, sin riesgo de FS invertido.
    """
    cols = ["Mes", "Dia", "Hora", "Altura Solar (deg)", "Acimut Solar (deg)",
            "FS_geometrico", "FS", "Fachada", "Punto"]
    return df_fs[cols].to_csv(index=False).encode("utf-8-sig")
