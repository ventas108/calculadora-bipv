"""Contrato versionado para el motor oficial de sombreado BIPV.

Este módulo no calcula una segunda física solar. Adapta la salida del
ray-casting oficial de ``sombras_3d`` a un payload neutral que puede consumir
la interfaz React y que conserva la convención UTC de BIPV.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any

import pandas as pd

CONTRACT_VERSION = "bipv.shading.v1"
REQUIRED_RESULT_COLUMNS = {
    "timestamp_utc",
    "Mes",
    "Dia",
    "Hora",
    "Altura Solar (deg)",
    "Acimut Solar (deg)",
    "FS_geometrico",
    "Fachada",
    "Punto",
}
OPTIONAL_RESULT_COLUMNS = {
    "obstacle_id",
    "obstacle_name",
    "first_hit_distance_m",
}


def _finite(value: Any) -> bool:
    try:
        return isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _utc_timestamp(value: Any) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        raise ValueError("timestamp_utc debe incluir zona horaria")
    return ts.tz_convert("UTC").isoformat().replace("+00:00", "Z")


def validar_solicitud(request: dict[str, Any]) -> None:
    """Valida la frontera mínima antes de invocar un cálculo solar."""
    if request.get("contract_version") != CONTRACT_VERSION:
        raise ValueError(f"contract_version inválida: {request.get('contract_version')!r}")

    location = request.get("location")
    if not isinstance(location, dict):
        raise ValueError("Falta location en la solicitud")
    for key, minimum, maximum in (
        ("latitude", -90.0, 90.0),
        ("longitude", -180.0, 180.0),
        ("timezone", -14.0, 14.0),
        ("elevation_m", -500.0, 10000.0),
    ):
        value = location.get(key)
        if not _finite(value) or not minimum <= float(value) <= maximum:
            raise ValueError(f"location.{key} fuera de rango: {value!r}")

    timestamps = request.get("timestamps_utc")
    if not isinstance(timestamps, list) or not timestamps:
        raise ValueError("timestamps_utc debe ser una lista no vacía")
    for timestamp in timestamps:
        _utc_timestamp(timestamp)

    points = request.get("points")
    if not isinstance(points, list) or not points:
        raise ValueError("points debe ser una lista no vacía")
    ids: set[str] = set()
    for point in points:
        if not isinstance(point, dict):
            raise ValueError("Cada punto debe ser un objeto")
        point_id = point.get("id")
        if not isinstance(point_id, str) or not point_id or point_id in ids:
            raise ValueError(f"id de punto inválido o repetido: {point_id!r}")
        ids.add(point_id)
        if not isinstance(point.get("facade"), str) or not point["facade"]:
            raise ValueError(f"fachada inválida para {point_id!r}")
        for coordinate in ("x_m", "y_m", "z_m"):
            if not _finite(point.get(coordinate)):
                raise ValueError(f"{point_id}.{coordinate} no es numérico")

    triangles = request.get("triangles", [])
    if not isinstance(triangles, list):
        raise ValueError("triangles debe ser una lista")
    for triangle in triangles:
        if not isinstance(triangle, dict):
            raise ValueError("Cada triángulo debe ser un objeto")
        for vertex in ("a", "b", "c"):
            coordinates = triangle.get(vertex)
            if (
                not isinstance(coordinates, list)
                or len(coordinates) != 3
                or not all(_finite(value) for value in coordinates)
            ):
                raise ValueError(f"Vértice {vertex} inválido en triángulo")
        for key in ("obstacle_id", "obstacle_name"):
            if key in triangle and triangle[key] is not None and (
                not isinstance(triangle[key], str) or not triangle[key].strip()
            ):
                raise ValueError(f"{key} inválido en triángulo")
        if "first_hit_distance_m" in triangle and triangle["first_hit_distance_m"] is not None:
            if not _finite(triangle["first_hit_distance_m"]) or float(
                triangle["first_hit_distance_m"]
            ) < 0:
                raise ValueError("first_hit_distance_m inválido en triángulo")

    transparency = request.get("transparency", 0.0)
    if not _finite(transparency) or not 0.0 <= float(transparency) <= 1.0:
        raise ValueError("transparency fuera de rango")


def validar_resultado(payload: dict[str, Any]) -> None:
    """Rechaza resultados ambiguos antes de entregarlos a la interfaz."""
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise ValueError("Resultado con versión de contrato incorrecta")
    if payload.get("engine") != "python":
        raise ValueError("Solo Python puede producir el resultado oficial")
    if payload.get("authority") != "official_solar_engine":
        raise ValueError("El resultado no está marcado como autoridad oficial")
    conventions = payload.get("conventions", {})
    expected_conventions = {
        "timestamp": "UTC",
        "azimuth": "north_clockwise",
        "coordinates": "x_east_y_north_z_up_m",
        "fs_geometrico": "0_no_geometric_shadow_1_total_geometric_shadow",
    }
    if conventions != expected_conventions:
        raise ValueError("Convenciones solares incompletas o incompatibles")

    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("results debe ser una lista")
    for row in results:
        required = {
            "timestamp_utc", "month", "day", "hour_utc",
            "solar_altitude_deg", "solar_azimuth_deg", "point_id",
            "facade", "fs_geometrico", "fs_climatico", "fs_combinado", "fs",
        }
        if not required.issubset(row):
            raise ValueError("Fila de resultado incompleta")
        if row["fs_climatico"] is not None or row["fs_combinado"] is not None:
            raise ValueError(
                "El contrato diagnóstico no permite que clima o FS combinado "
                "activen mismatch/bypass"
            )
        fs_geo = float(row["fs_geometrico"])
        fs = float(row["fs"])
        if not 0.0 <= fs_geo <= 1.0 or abs(fs - fs_geo) > 1e-9:
            raise ValueError("FS_geometrico y fs deben coincidir en [0, 1]")
        _utc_timestamp(row["timestamp_utc"])
        if "obstacle_id" in row and row["obstacle_id"] is not None:
            if not isinstance(row["obstacle_id"], str) or not row["obstacle_id"]:
                raise ValueError("obstacle_id inválido")
        if "obstacle_name" in row and row["obstacle_name"] is not None:
            if not isinstance(row["obstacle_name"], str) or not row["obstacle_name"]:
                raise ValueError("obstacle_name inválido")
        if "first_hit_distance_m" in row and row["first_hit_distance_m"] is not None:
            if not _finite(row["first_hit_distance_m"]) or float(
                row["first_hit_distance_m"]
            ) < 0:
                raise ValueError("first_hit_distance_m inválido")


def resultado_a_contrato(df: pd.DataFrame) -> dict[str, Any]:
    """Convierte ``calcular_fs_horario`` al contrato oficial v1."""
    missing = REQUIRED_RESULT_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Salida de sombras_3d sin columnas: {sorted(missing)}")

    results: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        fs_geo = float(row["FS_geometrico"])
        if not 0.0 <= fs_geo <= 1.0:
            raise ValueError(f"FS_geometrico fuera de rango: {fs_geo}")
        results.append({
            "timestamp_utc": _utc_timestamp(row["timestamp_utc"]),
            "month": int(row["Mes"]),
            "day": int(row["Dia"]),
            "hour_utc": int(row["Hora"]),
            "solar_altitude_deg": float(row["Altura Solar (deg)"]),
            "solar_azimuth_deg": float(row["Acimut Solar (deg)"]),
            "point_id": str(row["Punto"]),
            "facade": str(row["Fachada"]),
            "fs_geometrico": fs_geo,
            "fs_climatico": None,
            "fs_combinado": None,
            "fs": fs_geo,
        })
        for column in OPTIONAL_RESULT_COLUMNS:
            if column in df.columns:
                value = row[column]
                if pd.isna(value):
                    value = None
                elif column == "first_hit_distance_m":
                    value = float(value)
                else:
                    value = str(value)
                results[-1][column] = value

    payload = {
        "contract_version": CONTRACT_VERSION,
        "engine": "python",
        "authority": "official_solar_engine",
        "conventions": {
            "timestamp": "UTC",
            "azimuth": "north_clockwise",
            "coordinates": "x_east_y_north_z_up_m",
            "fs_geometrico": "0_no_geometric_shadow_1_total_geometric_shadow",
        },
        "results": results,
    }
    validar_resultado(payload)
    return payload