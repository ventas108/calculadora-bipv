#!/usr/bin/env python3
"""Reconstrucción angular de FS_geometrico para East2 (fachada este, azimut 82.65°).

*** ADVERTENCIA ***
Este script NO usa el DSM, la malla 3D ni los puntos de análisis reales de
East2 (que no existen en este proyecto, ver references/east2-validacion-informe.md).
En su lugar usa la Tabla 4 del artículo de referencia (DOI
10.3390/buildings16091668), que publica el factor de sombreado
acimut-a-elevación calculado por PVsyst a partir de un DSM real para el array
East2 (rejilla discreta de 19 acimutes x 10 elevaciones = 190 valores,
transcrita en references/east2-mascara-angular.json), interpolada
bilinealmente y convertida en una serie horaria de FS_geometrico. Es una
RECONSTRUCCIÓN a partir de una rejilla discreta publicada, NO el DSM/malla
continua original, y NO es válida para homologación oficial de la
Calculadora BIPV.

Reutiliza `posiciones_solares` y `ALTURA_SOLAR_MIN_DEG` de
bipv_python/calculos/sombras_3d.py (motor oficial) SOLO para calcular la
posición solar horaria con la misma convención de mes/día/hora/azimut que usa
el proyecto — no se modifica ni se reimplementa esa lógica. La interpolación
bilineal sobre la tabla publicada es propia de esta reconstrucción y no forma
parte del motor oficial.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from bipv_python.calculos.sombras_3d import posiciones_solares, ALTURA_SOLAR_MIN_DEG  # noqa: E402

REFERENCES_DIR = Path(__file__).resolve().parent
MASCARA_PATH = REFERENCES_DIR / "east2-mascara-angular.json"
SALIDA_CSV = REFERENCES_DIR / "east2-fs-angular-reconstruido.csv"

LATITUD = 40.45
LONGITUD = -3.74
ZONA_HORARIA = "Europe/Madrid"
FACHADA = "East2"
AZIMUT_ARRAY_DEG = 82.65
INCLINACION_DEG = 90.0
PUNTO = "P1-reconstruido"
FILA = "Fila 1"


def cargar_rejilla(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    data = json.loads(path.read_text())
    elevaciones = np.array(data["rejilla_elevacion_deg"], dtype=float)
    acimutes = np.array(data["rejilla_acimut_brujula_deg"], dtype=float)
    tabla = data["tabla_factor_por_elevacion"]
    grid = np.array([tabla[str(int(e))] for e in elevaciones], dtype=float)  # (n_elev, n_az)
    return elevaciones, acimutes, grid


def interpolar_bilineal(elev_q: np.ndarray, az_q: np.ndarray,
                         elevaciones: np.ndarray, acimutes: np.ndarray,
                         grid: np.ndarray) -> np.ndarray:
    """Interpolación bilineal sobre la rejilla publicada (Tabla 4).

    az_q se envuelve a [0, 360). elev_q se recorta a [0, 90] (fuera de ese
    rango no hay datos publicados y no debería ocurrir para horas con sol).
    """
    az_q = np.mod(az_q, 360.0)
    elev_q = np.clip(elev_q, elevaciones.min(), elevaciones.max())

    i_e = np.clip(np.searchsorted(elevaciones, elev_q, side="right") - 1, 0, len(elevaciones) - 2)
    i_a = np.clip(np.searchsorted(acimutes, az_q, side="right") - 1, 0, len(acimutes) - 2)

    e0, e1 = elevaciones[i_e], elevaciones[i_e + 1]
    a0, a1 = acimutes[i_a], acimutes[i_a + 1]
    te = np.where(e1 > e0, (elev_q - e0) / (e1 - e0), 0.0)
    ta = np.where(a1 > a0, (az_q - a0) / (a1 - a0), 0.0)

    f00 = grid[i_e, i_a]
    f10 = grid[i_e + 1, i_a]
    f01 = grid[i_e, i_a + 1]
    f11 = grid[i_e + 1, i_a + 1]

    return (f00 * (1 - te) * (1 - ta) + f10 * te * (1 - ta)
            + f01 * (1 - te) * ta + f11 * te * ta)


def main() -> None:
    elevaciones, acimutes, grid = cargar_rejilla(MASCARA_PATH)

    sol = posiciones_solares(LATITUD, LONGITUD, tz=ZONA_HORARIA)
    con_sol = sol[sol["elevacion"] > ALTURA_SOLAR_MIN_DEG].copy()

    fs_geometrico = interpolar_bilineal(
        con_sol["elevacion"].to_numpy(), con_sol["acimut"].to_numpy(),
        elevaciones, acimutes, grid,
    )
    fs_geometrico = np.clip(fs_geometrico, 0.0, 1.0)

    salida = pd.DataFrame({
        "Mes": con_sol["mes"].to_numpy(),
        "Dia": con_sol["dia"].to_numpy(),
        "Hora": con_sol["hora"].to_numpy(),
        "FS_geometrico": np.round(fs_geometrico, 4),
        "Fachada": FACHADA,
        "Punto": PUNTO,
        "Fila": FILA,
    })

    salida.to_csv(SALIDA_CSV, index=False)

    print(f"Filas escritas: {len(salida)}")
    print(f"FS_geometrico min={salida['FS_geometrico'].min()} max={salida['FS_geometrico'].max()}")
    fuera_rango = salida[(salida["FS_geometrico"] < 0) | (salida["FS_geometrico"] > 1)]
    print(f"Filas fuera de [0,1]: {len(fuera_rango)}")
    print(f"Horas con FS_geometrico > 0: {int((salida['FS_geometrico'] > 0).sum())} de {len(salida)}")
    print(f"Horas con FS_geometrico == 1 (sombra total): {int((salida['FS_geometrico'] >= 0.999).sum())}")
    print("ADVERTENCIA: reconstruccion a partir de la Tabla 4 del articulo (rejilla discreta "
          "interpolada), NO es el DSM/malla 3D original. Ver east2-validacion-informe.md")


if __name__ == "__main__":
    main()
