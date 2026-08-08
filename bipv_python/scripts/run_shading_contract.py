"""CLI interno para ejecutar el contrato oficial de sombreado.

Lee una solicitud JSON por stdin y escribe el resultado JSON por stdout.
No contiene una física paralela: delega en ``sombras_3d.calcular_fs_horario``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Permite ejecutar el script directamente desde la raíz del repositorio y
# mantiene la misma resolución de imports que usa el proxy Express.
PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

import numpy as np
import pandas as pd
import trimesh

from calculos.contrato_sombreado import resultado_a_contrato, validar_solicitud
from calculos.sombras_3d import calcular_fs_horario


def _run(request: dict) -> dict:
    validar_solicitud(request)
    triangles = request.get("triangles")
    if not isinstance(triangles, list) or not triangles:
        raise ValueError("triangles debe ser una lista no vacía para ejecutar el motor")
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    for triangle in triangles:
        start = len(vertices)
        vertices.extend([triangle["a"], triangle["b"], triangle["c"]])
        faces.append([start, start + 1, start + 2])

    mesh = trimesh.Trimesh(
        vertices=np.asarray(vertices, dtype=float),
        faces=np.asarray(faces, dtype=np.int64),
        process=False,
    )
    if mesh.is_empty:
        raise ValueError("La malla no contiene triángulos válidos")
    mesh._bipv_obstacle_id_by_face = np.asarray(
        [
            str(t.get("obstacle_id"))
            if t.get("obstacle_id") is not None
            else f"triangle-{i + 1:06d}"
            for i, t in enumerate(triangles)
        ],
        dtype=object,
    )
    mesh._bipv_obstacle_name_by_face = np.asarray(
        [t.get("obstacle_name") for t in triangles],
        dtype=object,
    )

    timestamps = pd.DatetimeIndex(request["timestamps_utc"])
    points = [
        {
            "nombre": point["id"],
            "fachada": point["facade"],
            "x": point["x_m"],
            "y": point["y_m"],
            "z": point["z_m"],
        }
        for point in request["points"]
    ]
    rows = calcular_fs_horario(
        mesh,
        points,
        request["location"]["latitude"],
        request["location"]["longitude"],
        timestamps,
        transparencia=request.get("transparency", 0.0),
    )
    return resultado_a_contrato(rows)


def main() -> None:
    try:
        request = json.load(sys.stdin)
        print(json.dumps(_run(request), ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()