"""Contrato auditable para horas y meses solares críticos.

Este módulo es diagnóstico. No modifica, filtra ni redistribuye la serie
horaria que usa Producción para calcular E_dc/E_ac.

Convenciones:
    - ``FS_geometrico``: 0 = sin sombra, 1 = sombra total.
    - ``poa_Wm2``: irradiancia POA antes de aplicar la pérdida geométrica.
    - ``poa_perdida_kWh_m2``: ``poa_Wm2 × FS_geometrico / 1000`` por hora.

Una hora crítica debe tener simultáneamente irradiancia significativa y una
pérdida geométrica superior al umbral. Los meses se ordenan por la suma de
energía solar perdida, no por la cantidad de horas sombreadas.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd


CONFIG_CRITICOS_POR_DEFECTO: dict[str, float | int] = {
    "irradiancia_minima_wm2": 100.0,
    "fs_minimo": 0.05,
    "top_n_horas": 10,
    "top_n_meses": 3,
}

MESES_ES = {
    1: "Ene",
    2: "Feb",
    3: "Mar",
    4: "Abr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dic",
}


def normalizar_configuracion_criticos(
    configuracion: Mapping[str, Any] | None = None,
) -> dict[str, float | int]:
    """Devuelve una configuración completa, validada y serializable.

    Se aceptan solo los cuatro parámetros del contrato para evitar que una
    clave mal escrita cambie el diagnóstico silenciosamente.
    """
    configuracion = configuracion or {}
    desconocidas = set(configuracion) - set(CONFIG_CRITICOS_POR_DEFECTO)
    if desconocidas:
        raise ValueError(
            "Configuración de críticos desconocida: "
            + ", ".join(sorted(map(str, desconocidas)))
        )

    resultado: dict[str, float | int] = dict(CONFIG_CRITICOS_POR_DEFECTO)
    try:
        resultado["irradiancia_minima_wm2"] = float(
            configuracion.get(
                "irradiancia_minima_wm2",
                CONFIG_CRITICOS_POR_DEFECTO["irradiancia_minima_wm2"],
            )
        )
        resultado["fs_minimo"] = float(
            configuracion.get(
                "fs_minimo",
                CONFIG_CRITICOS_POR_DEFECTO["fs_minimo"],
            )
        )
        resultado["top_n_horas"] = int(
            configuracion.get(
                "top_n_horas",
                CONFIG_CRITICOS_POR_DEFECTO["top_n_horas"],
            )
        )
        resultado["top_n_meses"] = int(
            configuracion.get(
                "top_n_meses",
                CONFIG_CRITICOS_POR_DEFECTO["top_n_meses"],
            )
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Configuración de críticos no numérica") from exc

    if not np.isfinite(resultado["irradiancia_minima_wm2"]):
        raise ValueError("irradiancia_minima_wm2 debe ser finita")
    if resultado["irradiancia_minima_wm2"] < 0:
        raise ValueError("irradiancia_minima_wm2 no puede ser negativa")
    if not np.isfinite(resultado["fs_minimo"]):
        raise ValueError("fs_minimo debe ser finito")
    if not 0.0 <= resultado["fs_minimo"] <= 1.0:
        raise ValueError("fs_minimo debe estar entre 0 y 1")
    if resultado["top_n_horas"] < 1:
        raise ValueError("top_n_horas debe ser mayor que cero")
    if resultado["top_n_meses"] < 1 or resultado["top_n_meses"] > 12:
        raise ValueError("top_n_meses debe estar entre 1 y 12")
    return resultado


def calcular_horas_meses_criticos(
    poa_horaria: pd.Series,
    fs_horario: pd.Series,
    *,
    configuracion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Calcula el diagnóstico horario y mensual de criticidad.

    El resultado conserva todas las horas en ``detalle_horario``. La selección
    de ``horas_criticas`` solo sirve para presentar el top configurado y usa
    primero los filtros físicos, luego ordena por pérdida solar descendente.
    """
    config = normalizar_configuracion_criticos(configuracion)
    if not isinstance(poa_horaria, pd.Series) or not isinstance(fs_horario, pd.Series):
        raise ValueError("poa_horaria y fs_horario deben ser Series")
    if not isinstance(poa_horaria.index, pd.DatetimeIndex):
        raise ValueError("poa_horaria requiere un DatetimeIndex")
    if not poa_horaria.index.equals(fs_horario.index):
        raise ValueError("POA y FS deben tener exactamente el mismo índice")

    poa = pd.to_numeric(poa_horaria, errors="coerce")
    fs = pd.to_numeric(fs_horario, errors="coerce")
    if not np.isfinite(poa.to_numpy(dtype=float)).all():
        raise ValueError("poa_horaria contiene valores no finitos")
    if not np.isfinite(fs.to_numpy(dtype=float)).all():
        raise ValueError("fs_horario contiene valores no finitos")
    if (poa < 0).any():
        raise ValueError("poa_horaria no puede contener valores negativos")
    if ((fs < 0) | (fs > 1)).any():
        raise ValueError("fs_horario debe estar entre 0 y 1")

    detalle = pd.DataFrame(
        {
            "timestamp": poa.index,
            "poa_Wm2": poa.to_numpy(dtype=float),
            "FS_geometrico": fs.to_numpy(dtype=float),
        }
    )
    detalle["poa_perdida_kWh_m2"] = (
        detalle["poa_Wm2"] * detalle["FS_geometrico"] / 1000.0
    )
    detalle["mes"] = detalle["timestamp"].dt.month
    detalle["mes_nombre"] = detalle["mes"].map(MESES_ES)
    detalle["irradiancia_significativa"] = (
        detalle["poa_Wm2"] >= config["irradiancia_minima_wm2"]
    )
    detalle["perdida_supera_umbral"] = (
        detalle["FS_geometrico"] > config["fs_minimo"]
    )
    detalle["hora_critica"] = (
        detalle["irradiancia_significativa"]
        & detalle["perdida_supera_umbral"]
    )

    horas_candidatas = detalle[detalle["hora_critica"]].copy()
    horas_candidatas = horas_candidatas.sort_values(
        ["poa_perdida_kWh_m2", "timestamp"],
        ascending=[False, True],
        kind="mergesort",
    )
    horas_top = horas_candidatas.head(int(config["top_n_horas"]))

    mensual = (
        detalle.groupby(["mes", "mes_nombre"], as_index=False)
        .agg(
            poa_perdida_kWh_m2=("poa_perdida_kWh_m2", "sum"),
            horas_con_sombra=("FS_geometrico", lambda serie: int((serie > 0).sum())),
            horas_criticas=("hora_critica", "sum"),
            fs_geometrico_medio=("FS_geometrico", "mean"),
        )
        .sort_values(
            ["poa_perdida_kWh_m2", "mes"],
            ascending=[False, True],
            kind="mergesort",
        )
    )
    # Un mes sin pérdida no es crítico aunque se soliciten más meses que
    # meses afectados. Esto evita completar el ranking con falsos críticos.
    meses_con_perdida = mensual[
        mensual["poa_perdida_kWh_m2"] > 0
    ]
    meses_top = meses_con_perdida.head(int(config["top_n_meses"]))

    def _fila_hora(fila: pd.Series) -> dict[str, Any]:
        return {
            "timestamp": fila["timestamp"].isoformat(),
            "mes": int(fila["mes"]),
            "mes_nombre": str(fila["mes_nombre"]),
            "hora": int(fila["timestamp"].hour),
            "poa_Wm2": round(float(fila["poa_Wm2"]), 3),
            "FS_geometrico": round(float(fila["FS_geometrico"]), 6),
            "poa_perdida_kWh_m2": round(
                float(fila["poa_perdida_kWh_m2"]), 6
            ),
        }

    def _fila_mes(fila: pd.Series) -> dict[str, Any]:
        return {
            "mes": int(fila["mes"]),
            "mes_nombre": str(fila["mes_nombre"]),
            "poa_perdida_kWh_m2": round(
                float(fila["poa_perdida_kWh_m2"]), 6
            ),
            "horas_con_sombra": int(fila["horas_con_sombra"]),
            "horas_criticas": int(fila["horas_criticas"]),
            "fs_geometrico_medio": round(
                float(fila["fs_geometrico_medio"]), 6
            ),
        }

    return {
        "configuracion": config,
        "criterio_hora": (
            "POA >= irradiancia_minima_wm2 y "
            "FS_geometrico > fs_minimo"
        ),
        "criterio_mes": (
            "orden descendente por suma mensual de "
            "poa_perdida_kWh_m2"
        ),
        "horas_sombreadas": int((detalle["FS_geometrico"] > 0).sum()),
        "horas_candidatas": int(len(horas_candidatas)),
        "horas_criticas": [_fila_hora(fila) for _, fila in horas_top.iterrows()],
        "meses_criticos": [_fila_mes(fila) for _, fila in meses_top.iterrows()],
        "mes_critico": (
            _fila_mes(meses_top.iloc[0]) if not meses_top.empty else None
        ),
        "detalle_horario": detalle,
        "tabla_mensual": mensual.reset_index(drop=True),
    }