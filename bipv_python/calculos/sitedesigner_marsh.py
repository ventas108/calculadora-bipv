# -*- coding: utf-8 -*-
"""
sitedesigner_marsh.py — Lector de escenas de Site Designer (Andrew Marsh)
=========================================================================
Fase 5: fuente externa de sombreado.

El JSON exportado por Site Designer (drajmarsh.bitbucket.io) NO trae
porcentajes de sombra: trae la ESCENA — ubicación (lat/lon/tz/elevación/
northOffset) y los obstáculos como cajas alineadas a los ejes
(``Blocks: [{min:[x,y,z], max:[x,y,z]}]``) en MILÍMETROS.

Este módulo solo traduce esa escena a una malla ``trimesh`` idéntica a la
que produce el flujo SketchUp (``sombras_3d.cargar_malla``). El motor
solar oficial sigue siendo ``sombras_3d.calcular_fs_horario`` — aquí no
hay física nueva, solo lectura de formato.

Convenciones (las mismas de SketchUp / sombras_3d):
  X = Este, Y = Norte, Z = arriba, en METROS.
  ``northOffset`` del archivo = giro horario (visto desde arriba) que hay
  que aplicar al modelo para alinear Y con el norte real — la misma
  convención de ``rotacion_norte_deg`` en ``cargar_malla``.

Regla de unidades (acordada — no adivinar):
  Site Designer trabaja en milímetros → ``ESCALA_MM_A_M = 0.001`` SIEMPRE,
  sin selector. Un bloque max=[.., .., 10000] son 10 m de alto.
"""
from __future__ import annotations

import json

import numpy as np

try:
    import trimesh
    TRIMESH_OK = True
except Exception:  # pragma: no cover
    trimesh = None
    TRIMESH_OK = False

ESCALA_MM_A_M = 0.001   # Site Designer exporta en milímetros — fijo, no configurable
DIM_MAX_ESCENA_M = 5000.0  # una escena >5 km casi seguro es un archivo mal interpretado
MAX_BLOQUES = 5000      # 5000 cajas × 12 caras = 60k triángulos, muy por debajo
                        # del MAX_TRIANGULOS (300k) del ray-casting


class ErrorSiteDesigner(ValueError):
    """Error de lectura/validación de un archivo de Site Designer."""


def _requerir(cond: bool, msg: str) -> None:
    if not cond:
        raise ErrorSiteDesigner(msg)


def cargar_escena_sitedesigner(contenido):
    """
    Lee un JSON de Site Designer y devuelve ``(malla, meta)``.

    contenido: bytes o str con el JSON exportado.

    malla: ``trimesh.Trimesh`` en metros, con el norte ya corregido según
      ``Location.northOffset``, y con identidad de obstáculo por cara
      (``_bipv_obstacle_id_by_face`` / ``_bipv_obstacle_name_by_face``),
      lista para ``sombras_3d.calcular_fs_horario``.

    meta: dict con ``lat``, ``lon``, ``timezone``, ``elevacion_m``,
      ``north_offset_deg``, ``n_bloques`` y ``dim_m`` (x, y, z de la
      caja envolvente en metros) — para validar contra la sesión y para
      trazabilidad ("fuente: externa_marsh").

    Lanza ``ErrorSiteDesigner`` con mensaje claro si el archivo no es un
    JSON de Site Designer válido. Nunca corrige en silencio.
    """
    if not TRIMESH_OK:
        raise ImportError("trimesh no está instalado (pip install trimesh)")

    if isinstance(contenido, (bytes, bytearray)):
        try:
            contenido = contenido.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            raise ErrorSiteDesigner(f"El archivo no es texto UTF-8: {e}") from e
    try:
        data = json.loads(contenido)
    except json.JSONDecodeError as e:
        raise ErrorSiteDesigner(f"El archivo no es JSON válido: {e}") from e

    _requerir(isinstance(data, dict), "El JSON no tiene la estructura esperada (objeto raíz).")

    loc = data.get("Location")
    _requerir(isinstance(loc, dict), "Falta la sección 'Location' — ¿seguro que es un export de Site Designer?")
    try:
        lat = float(loc["latitude"])
        lon = float(loc["longitude"])
    except (KeyError, TypeError, ValueError):
        raise ErrorSiteDesigner("'Location' no trae latitude/longitude numéricos.")
    _requerir(-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0,
              f"Latitud/longitud fuera de rango: {lat}, {lon}.")
    # northOffset es parte de la física (orientación de las sombras): si falta
    # o no es un número finito se RECHAZA — nunca se asume 0 en silencio.
    _requerir("northOffset" in loc,
              "'Location' no trae 'northOffset'. La orientación del norte es parte "
              "del cálculo — re-exporta desde Site Designer sin editar el JSON.")
    try:
        north_offset = float(loc["northOffset"])
    except (TypeError, ValueError):
        raise ErrorSiteDesigner(
            f"'northOffset' no es numérico: {loc['northOffset']!r}.")
    _requerir(np.isfinite(north_offset) and -360.0 <= north_offset <= 360.0,
              f"'northOffset' fuera de rango o no finito: {north_offset!r}.")

    bloques = data.get("Blocks")
    _requerir(isinstance(bloques, list) and len(bloques) > 0,
              "El archivo no contiene 'Blocks' (obstáculos). En Site Designer dibuja "
              "los edificios/obstáculos y vuelve a exportar.")
    _requerir(len(bloques) <= MAX_BLOQUES,
              f"El archivo trae {len(bloques):,} bloques (máx. {MAX_BLOQUES:,}). "
              "Deja solo los volúmenes que producen sombra sobre los puntos.")

    mallas, ids, nombres = [], [], []
    for i, b in enumerate(bloques, start=1):
        _requerir(isinstance(b, dict) and "min" in b and "max" in b,
                  f"El bloque #{i} no tiene 'min'/'max'.")
        vmin = np.asarray(b["min"], dtype=float)
        vmax = np.asarray(b["max"], dtype=float)
        _requerir(vmin.shape == (3,) and vmax.shape == (3,),
                  f"El bloque #{i} no tiene coordenadas x,y,z completas.")
        _requerir(np.isfinite(vmin).all() and np.isfinite(vmax).all(),
                  f"El bloque #{i} tiene coordenadas no numéricas.")
        # mm → m ANTES de cualquier comparación de tamaño (regla fija de unidades)
        vmin_m, vmax_m = vmin * ESCALA_MM_A_M, vmax * ESCALA_MM_A_M
        _requerir((vmax_m > vmin_m).all(),
                  f"El bloque #{i} tiene max ≤ min en algún eje — bloque degenerado "
                  f"(min={vmin.tolist()}, max={vmax.tolist()} mm). Corrígelo en Site Designer.")
        caja = trimesh.creation.box(bounds=np.vstack([vmin_m, vmax_m]))
        mallas.append(caja)
        obstacle_id = f"bloque-{i}"
        ids.extend([obstacle_id] * int(caja.faces.shape[0]))
        nombres.extend([f"Bloque {i}"] * int(caja.faces.shape[0]))

    malla = trimesh.util.concatenate(mallas) if len(mallas) > 1 else mallas[0]

    if north_offset:
        # misma convención que sombras_3d.cargar_malla: giro horario visto
        # desde arriba = giro -θ alrededor de Z
        ang = -np.deg2rad(north_offset)
        malla.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 0, 1]))

    dims = (malla.bounds[1] - malla.bounds[0]).astype(float)
    _requerir(float(dims.max()) <= DIM_MAX_ESCENA_M,
              f"La escena mide {dims.max():,.0f} m — no parece un export en milímetros "
              "de Site Designer. Revisa el archivo antes de continuar.")

    malla._bipv_obstacle_id_by_face = np.asarray(ids, dtype=object)
    malla._bipv_obstacle_name_by_face = np.asarray(nombres, dtype=object)

    meta = {
        "fuente": "externa_marsh",
        "lat": lat,
        "lon": lon,
        "timezone": loc.get("timezone"),
        "elevacion_m": loc.get("elevation"),
        "north_offset_deg": north_offset,
        "n_bloques": len(bloques),
        "dim_m": {"x": round(float(dims[0]), 2), "y": round(float(dims[1]), 2),
                  "z": round(float(dims[2]), 2)},
    }
    return malla, meta


def verificar_ubicacion(meta: dict, lat_sesion: float, lon_sesion: float,
                        tolerancia_deg: float = 0.1) -> list[str]:
    """
    Compara la ubicación del archivo con la de la sesión activa.
    Devuelve lista de avisos (vacía si todo coincide). No bloquea: quien
    decide es la página, con el aviso a la vista.
    """
    avisos: list[str] = []
    d_lat = abs(float(meta["lat"]) - float(lat_sesion))
    d_lon = abs(float(meta["lon"]) - float(lon_sesion))
    if d_lat > tolerancia_deg or d_lon > tolerancia_deg:
        avisos.append(
            f"La ubicación del archivo Site Designer ({meta['lat']:.3f}, {meta['lon']:.3f}) "
            f"NO coincide con la del proyecto ({lat_sesion:.3f}, {lon_sesion:.3f}). "
            "¿Es la escena de otro proyecto?"
        )
    return avisos
