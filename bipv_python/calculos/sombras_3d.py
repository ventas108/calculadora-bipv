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
import re

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

    Retorna un ``trimesh.Trimesh`` único (escenas se aplanan). Además conserva
    metadata opcional por cara:

    ``_bipv_obstacle_id_by_face`` y ``_bipv_obstacle_name_by_face``.

    ``force="mesh"`` (usado anteriormente) elimina la identidad de objetos de
    OBJ/GLB/DAE al aplanar la escena. Se carga primero como escena para
    conservarla cuando el formato la trae; el ray-casting sigue usando una
    única malla y por tanto no cambia la física ni ``FS_geometrico``.
    """
    if not TRIMESH_OK:
        raise ImportError("trimesh no está instalado (pip install trimesh)")

    if isinstance(archivo, (bytes, bytearray)):
        cargado = trimesh.load(io.BytesIO(archivo), file_type=tipo, force="scene")
    else:
        cargado = trimesh.load(archivo, force="scene")

    piezas: list[tuple[object, str | None]] = []
    if isinstance(cargado, trimesh.Scene):
        # dump() aplica las transformaciones de cada nodo y conserva el nombre
        # del nodo en metadata; no dependemos de que el loader exponga el
        # nombre como atributo del objeto geométrico.
        for pieza in cargado.dump(concatenate=False):
            nombre = pieza.metadata.get("name") if hasattr(pieza, "metadata") else None
            piezas.append((pieza, str(nombre).strip() if nombre else None))
    else:
        piezas.append((cargado, None))

    piezas = [
        (pieza, nombre)
        for pieza, nombre in piezas
        if getattr(pieza, "vertices", np.empty((0, 3))).shape[0]
        and getattr(pieza, "faces", np.empty((0, 3))).shape[0]
    ]
    if not piezas:
        raise ValueError("El modelo no contiene geometría (¿exportaste solo aristas?)")

    # Cada pieza con nombre conserva una identidad de obstáculo. Cuando el
    # formato solo entrega triángulos anónimos se usa un id sintético estable
    # por cara; no se fabrica un nombre humano para esa geometría.
    mallas = [pieza for pieza, _ in piezas]
    nombres = [nombre for _, nombre in piezas]
    obj = trimesh.util.concatenate(mallas)
    ids: list[str] = []
    nombres_por_cara: list[str | None] = []
    desplazamiento = 0
    usados: dict[str, int] = {}
    for pieza, nombre in piezas:
        n_caras = int(pieza.faces.shape[0])
        if nombre:
            base = _id_obstaculo(nombre)
            usados[base] = usados.get(base, 0) + 1
            obstacle_id = base if usados[base] == 1 else f"{base}-{usados[base]}"
            ids.extend([obstacle_id] * n_caras)
            nombres_por_cara.extend([nombre] * n_caras)
        else:
            ids.extend(
                f"triangle-{desplazamiento + i + 1:06d}"
                for i in range(n_caras)
            )
            nombres_por_cara.extend([None] * n_caras)
        desplazamiento += n_caras

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
    # Atributos privados para no alterar la API de trimesh ni los consumidores
    # existentes que esperan directamente un Trimesh.
    obj._bipv_obstacle_id_by_face = np.asarray(ids, dtype=object)
    obj._bipv_obstacle_name_by_face = np.asarray(nombres_por_cara, dtype=object)
    return obj


MAX_TRIANGULOS = 300_000     # más allá, el ray-casting puro-Python se vuelve inviable
MAX_RAYOS = 6_000_000        # presupuesto puntos × horas con sol


def _id_obstaculo(nombre: str) -> str:
    """Genera un identificador estable y legible para un objeto importado."""
    normalizado = re.sub(r"[^a-z0-9]+", "-", nombre.strip().lower()).strip("-")
    return f"obj-{normalizado or 'sin-nombre'}"


def _metadata_caras(malla) -> tuple[np.ndarray, np.ndarray]:
    """Devuelve ids/nombres por cara, con fallback sintético estable."""
    n_caras = int(malla.faces.shape[0])
    ids = getattr(malla, "_bipv_obstacle_id_by_face", None)
    names = getattr(malla, "_bipv_obstacle_name_by_face", None)
    if ids is None or len(ids) != n_caras:
        ids = np.asarray(
            [f"triangle-{i + 1:06d}" for i in range(n_caras)],
            dtype=object,
        )
    else:
        ids = np.asarray(ids, dtype=object)
    if names is None or len(names) != n_caras:
        names = np.asarray([None] * n_caras, dtype=object)
    else:
        names = np.asarray(names, dtype=object)
    return ids, names


def _primeras_intersecciones(
    malla,
    origenes: np.ndarray,
    direcciones: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Obtiene hit, triángulo y distancia mínima por rayo.

    ``intersects_any`` solo informa booleanos. Aquí se conservan todas las
    intersecciones disponibles y se elige la más cercana, que es la causalidad
    geométrica correcta cuando hay obstáculos alineados.
    """
    n_rayos = len(origenes)
    hit = np.zeros(n_rayos, dtype=bool)
    tri_primero = np.full(n_rayos, -1, dtype=np.int64)
    distancia = np.full(n_rayos, np.nan, dtype=float)
    try:
        locations, index_ray, index_tri = malla.ray.intersects_location(
            ray_origins=origenes,
            ray_directions=direcciones,
            multiple_hits=True,
        )
        if len(index_ray):
            distancias = np.linalg.norm(
                np.asarray(locations) - origenes[np.asarray(index_ray)],
                axis=1,
            )
            # Orden estable: distancia y luego índice de triángulo.
            orden = np.lexsort((
                np.asarray(index_tri, dtype=np.int64),
                distancias,
                np.asarray(index_ray, dtype=np.int64),
            ))
            for pos in orden:
                rayo = int(index_ray[pos])
                d = float(distancias[pos])
                if not hit[rayo] or d < distancia[rayo]:
                    hit[rayo] = True
                    tri_primero[rayo] = int(index_tri[pos])
                    distancia[rayo] = d
        return hit, tri_primero, distancia
    except Exception:
        # Mantener el cálculo solar operativo en instalaciones de trimesh que
        # no tienen el backend de intersección detallada. En ese caso no se
        # inventa distancia ni identidad, pero FS conserva exactamente su
        # comportamiento anterior.
        hit = np.asarray(
            malla.ray.intersects_any(
                ray_origins=origenes,
                ray_directions=direcciones,
            ),
            dtype=bool,
        )
        return hit, tri_primero, distancia


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
      FS_geometrico, FS, Fachada, Fila, Punto y pesos espaciales opcionales.
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
        hits, tri_primero, distancias = _primeras_intersecciones(
            malla, origenes, dirs
        )
        fs_geo = np.where(hits, fs_choque, 0.0)
        ids_caras, nombres_caras = _metadata_caras(malla)
        obstacle_ids = [
            str(ids_caras[tri]) if 0 <= tri < len(ids_caras) else None
            for tri in tri_primero
        ]
        obstacle_names = [
            (
                str(nombres_caras[tri])
                if 0 <= tri < len(nombres_caras)
                and nombres_caras[tri] is not None
                else None
            )
            for tri in tri_primero
        ]
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
            "Fila": pt.get("fila") or pt.get("nombre") or "P1",
            "Punto": pt.get("nombre") or "P1",
            "N módulos": pt.get("n_modulos", 0.0),
            "Área activa (m²)": pt.get("area_activa_m2", 0.0),
            "Potencia instalada (kW)": pt.get("potencia_instalada_kw", 0.0),
            "obstacle_id": obstacle_ids,
            "obstacle_name": obstacle_names,
            "first_hit_distance_m": np.round(distancias, 6),
        }))
    return pd.concat(filas, ignore_index=True)


def resumen_fs(df_fs: pd.DataFrame) -> dict:
    """Estadísticas para la UI."""
    col_fs = "FS_geometrico" if "FS_geometrico" in df_fs.columns else "FS"
    horas_sombra = df_fs[df_fs[col_fs] > 0]
    return {
        "puntos": int(df_fs["Punto"].nunique()),
        "horas_evaluadas": int(len(df_fs) / max(1, df_fs["Punto"].nunique())),
        "registros_con_sombra": int(len(horas_sombra)),
        "pct_horas_con_sombra": round(100.0 * len(horas_sombra) / max(1, len(df_fs)), 1),
        "fs_medio_con_sombra": round(float(horas_sombra[col_fs].mean()), 3) if len(horas_sombra) else 0.0,
    }


def exportar_csv_fs(df_fs: pd.DataFrame) -> bytes:
    """
    CSV en el formato que consume la Página 5 (cargar_csv_fs):
    columnas con FS_geometrico (prioritaria en el parser: sombra física pura,
    las nubes NO deben activar bypass) + Fachada. Convención 0=sin sombra,
    1=sombra total — la nativa del modelo bypass, sin riesgo de FS invertido.
    """
    cols = [
        "Mes", "Dia", "Hora", "Altura Solar (deg)", "Acimut Solar (deg)",
        "FS_geometrico", "FS", "Fachada", "Fila", "Punto",
        "N módulos", "Área activa (m²)", "Potencia instalada (kW)",
    ]
    salida = df_fs.copy()
    # Compatibilidad con resultados generados antes del contrato espacial.
    defaults = {
        "Fila": salida["Punto"] if "Punto" in salida.columns else "P1",
        "N módulos": 1.0,
        "Área activa (m²)": 0.0,
        "Potencia instalada (kW)": 0.0,
    }
    for columna, valor in defaults.items():
        if columna not in salida.columns:
            salida[columna] = valor
    # Metadata de obstáculo solo se exporta cuando existe. Así los CSV
    # históricos no reciben nombres artificiales ni cambian de semántica.
    for columna in ("obstacle_id", "obstacle_name", "first_hit_distance_m"):
        if columna in salida.columns:
            cols.append(columna)
    return salida[cols].to_csv(index=False).encode("utf-8-sig")
