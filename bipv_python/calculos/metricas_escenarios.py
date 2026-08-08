"""Métricas separadas para auditoría solar y eléctrica de escenarios.

Regla principal:
    una pérdida de POA se reporta como pérdida solar y no se convierte
    automáticamente en kWh AC. La recuperación solo se calcula comparando
    resultados eléctricos de escenarios con la misma base.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd


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


def _float_or_none(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if np.isfinite(value) else None


def _serie_numerica(value: Any, index: pd.Index) -> pd.Series | None:
    if value is None:
        return None
    if isinstance(value, pd.Series):
        serie = value.copy()
    else:
        try:
            serie = pd.Series(value, index=index)
        except (TypeError, ValueError):
            return None
    if len(serie) != len(index):
        return None
    serie.index = index
    return pd.to_numeric(serie, errors="coerce").fillna(0.0).clip(0.0, 1.0)


def _periodo_fs(df_fs: pd.DataFrame, modo: str) -> list[str]:
    return ["mes", "hora"] if modo == "mensual" else ["mes", "dia", "hora"]


def _alinear_fs_grupo(
    grupo: pd.DataFrame,
    tmy_index: pd.DatetimeIndex,
    poa: pd.Series,
    *,
    modo: str,
) -> pd.DataFrame:
    columnas = _periodo_fs(grupo, modo)
    fs = (
        grupo.groupby(columnas, dropna=False)["FS_geometrico"]
        .mean()
        .rename("FS_geometrico")
        .reset_index()
    )
    claves_tmy = pd.DataFrame(index=tmy_index)
    claves_tmy["mes"] = tmy_index.month
    claves_tmy["dia"] = tmy_index.day
    claves_tmy["hora"] = tmy_index.hour
    claves_tmy["poa_Wm2"] = np.asarray(poa.values, dtype=float)
    unido = claves_tmy.reset_index(names="timestamp_utc").merge(
        fs, on=columnas, how="left"
    )
    unido["FS_geometrico"] = unido["FS_geometrico"].fillna(0.0).clip(0.0, 1.0)
    unido["poa_perdida_kWh_m2"] = (
        unido["poa_Wm2"] * unido["FS_geometrico"] / 1000.0
    )
    return unido


def _agregar_grupos(
    df_fs: pd.DataFrame | None,
    tmy_index: pd.DatetimeIndex | None,
    poa: pd.Series | None,
    *,
    modo: str,
    columna: str,
) -> list[dict[str, Any]]:
    if (
        not isinstance(df_fs, pd.DataFrame)
        or df_fs.empty
        or columna not in df_fs.columns
        or tmy_index is None
        or poa is None
    ):
        return []
    resultado = []
    for etiqueta, grupo in df_fs.groupby(columna, dropna=False):
        alineado = _alinear_fs_grupo(grupo, tmy_index, poa, modo=modo)
        poa_total = float(alineado["poa_Wm2"].clip(lower=0).sum() / 1000.0)
        perdida = float(alineado["poa_perdida_kWh_m2"].sum())
        resultado.append(
            {
                "grupo": str(etiqueta),
                "poa_perdida_kWh_m2": round(perdida, 2),
                "fs_geometrico_ponderado_pct": round(
                    perdida / poa_total * 100.0 if poa_total > 0 else 0.0,
                    2,
                ),
                "horas_con_sombra": int(
                    (alineado["FS_geometrico"] > 0).sum()
                ),
            }
        )
    return sorted(
        resultado,
        key=lambda item: item["poa_perdida_kWh_m2"],
        reverse=True,
    )


def metricas_solares(
    *,
    poa_bruta_kWh_m2: float | None,
    poa_efectiva_kWh_m2: float | None = None,
    poa_efectiva_fuente: str | None = None,
    fs_horario: Any = None,
    tmy_index: pd.DatetimeIndex | None = None,
    poa_horaria: pd.Series | None = None,
    res_sombra: Mapping[str, Any] | None = None,
    df_fs: pd.DataFrame | None = None,
    modo_fs: str = "mensual",
) -> dict[str, Any]:
    """Construye el grupo de métricas solares sin inferir energía AC."""
    poa_bruta = _float_or_none(poa_bruta_kWh_m2)
    poa_efectiva = _float_or_none(poa_efectiva_kWh_m2)
    fs = _serie_numerica(
        fs_horario,
        tmy_index if tmy_index is not None else pd.RangeIndex(0),
    )

    if fs is not None and poa_horaria is not None:
        poa = pd.to_numeric(poa_horaria, errors="coerce").fillna(0.0)
        perdida_solar = float((poa.clip(lower=0) * fs).sum() / 1000.0)
        horas_sombra = int((fs > 0).sum())
        df_mes = pd.DataFrame(
            {
                "mes": tmy_index.month,
                "poa_perdida_kWh_m2": poa.clip(lower=0).values
                * fs.values
                / 1000.0,
                "fs": fs.values,
            }
        )
        mensual = (
            df_mes.groupby("mes")
            .agg(
                poa_perdida_kWh_m2=("poa_perdida_kWh_m2", "sum"),
                fs_geometrico_medio=("fs", "mean"),
            )
            .reset_index()
        )
        mensual["mes_nombre"] = mensual["mes"].map(MESES_ES)
        mensual["poa_perdida_kWh_m2"] = mensual["poa_perdida_kWh_m2"].round(2)
        meses_criticos = (
            mensual.sort_values("poa_perdida_kWh_m2", ascending=False)
            .head(3)["mes_nombre"]
            .tolist()
        )
        fs_ponderado_pct = (
            perdida_solar / (float(poa.clip(lower=0).sum()) / 1000.0) * 100.0
            if poa.clip(lower=0).sum() > 0
            else 0.0
        )
    else:
        perdida_solar = _float_or_none(
            (res_sombra or {}).get("energia_perdida_kWh_m2")
        )
        horas_sombra = int((res_sombra or {}).get("horas_sombreadas", 0) or 0)
        fs_ponderado_pct = (
            _float_or_none((res_sombra or {}).get("factor_sombra_anual")) or 0.0
        ) * 100.0
        mensual = pd.DataFrame()
        meses_criticos = []

    perdida_poa_total = (
        max(poa_bruta - poa_efectiva, 0.0)
        if poa_bruta is not None and poa_efectiva is not None
        else None
    )
    obstaculo_responsable = (
        _agregar_grupos(
            df_fs, tmy_index, poa_horaria, modo=modo_fs, columna="obstaculo"
        )
    )
    por_fachada = _agregar_grupos(
        df_fs, tmy_index, poa_horaria, modo=modo_fs, columna="fachada"
    )
    por_fila_punto = _agregar_grupos(
        df_fs, tmy_index, poa_horaria, modo=modo_fs, columna="punto"
    )
    return {
        "poa_bruta_kWh_m2": poa_bruta,
        "poa_efectiva_kWh_m2": poa_efectiva,
        "poa_efectiva_fuente": poa_efectiva_fuente,
        "perdida_poa_solar_kWh_m2": (
            round(perdida_poa_total, 2) if perdida_poa_total is not None else None
        ),
        "fs_geometrico_ponderado_pct": round(fs_ponderado_pct, 2),
        "horas_con_sombra": horas_sombra,
        "meses_criticos": meses_criticos,
        "por_fachada": por_fachada,
        "por_fila_punto": por_fila_punto,
        "por_obstaculo": obstaculo_responsable,
        "obstaculo_responsable": (
            obstaculo_responsable[0]["grupo"]
            if obstaculo_responsable
            else None
        ),
        "nota_perdida_poa": (
            "Pérdida solar de irradiancia POA; no es equivalente automáticamente "
            "a pérdida de kWh AC."
        ),
    }


def metricas_electricas(
    *,
    resultado_produccion: Mapping[str, Any] | None = None,
    bypass: Mapping[str, Any] | None = None,
    mismatch: Mapping[str, Any] | None = None,
    eta_inversor: float | None = None,
) -> dict[str, Any]:
    """Construye el grupo eléctrico del escenario actual."""
    resultado = resultado_produccion or {}
    e_dc = _float_or_none(resultado.get("E_dc_anual_kWh"))
    e_ac_modelo = _float_or_none(resultado.get("E_ac_anual_kWh"))
    bypass_dc = _float_or_none((bypass or {}).get("kwh_bypass_anual")) or 0.0
    eta = _float_or_none(eta_inversor) or 0.0
    bypass_ac = bypass_dc * eta if bypass_dc > 0 and eta > 0 else None
    e_ac_final = e_ac_modelo
    if bypass_ac is not None and e_ac_final is not None:
        e_ac_final = max(e_ac_final - bypass_ac, 0.0)
    perdida_inversor = _float_or_none(resultado.get("perdida_inv_kWh"))
    perdida_electrica = (
        (perdida_inversor or 0.0) + (bypass_ac or 0.0)
        if e_dc is not None
        else None
    )
    return {
        "energia_dc_kWh": e_dc,
        "energia_ac_kWh": e_ac_final,
        "energia_ac_modelo_sin_bypass_kWh": e_ac_modelo,
        "perdida_inversor_kWh": perdida_inversor,
        "perdida_bypass_dc_kWh": bypass_dc if bypass else None,
        "perdida_bypass_ac_kWh": bypass_ac,
        "perdida_electrica_total_kWh": (
            round(perdida_electrica, 2)
            if perdida_electrica is not None
            else None
        ),
        "impacto_bypass_pct_dc": _float_or_none(
            (bypass or {}).get("pct_bypass_anual")
        ),
        "impacto_mismatch_poa_pct": _float_or_none(
            (mismatch or {}).get("factor_mismatch_pct")
        ),
        "impacto_mismatch_poa_kWh_m2": _float_or_none(
            (mismatch or {}).get("energia_perdida_kWh_m2")
        ),
        "nota_mismatch": (
            "El mismatch mostrado es impacto de POA cuando no existe "
            "simulación eléctrica independiente."
        ),
    }


def metricas_recuperacion(
    *,
    e_ac_referencia_kWh: float | None,
    e_ac_actual_kWh: float | None,
    e_ac_optimizada_kWh: float | None,
) -> dict[str, Any]:
    """Calcula recuperación AC, limitada a 0–100 % y sin pérdida recuperable."""
    referencia = _float_or_none(e_ac_referencia_kWh)
    actual = _float_or_none(e_ac_actual_kWh)
    optimizada = _float_or_none(e_ac_optimizada_kWh)
    if referencia is None or actual is None or optimizada is None:
        return {
            "disponible": False,
            "energia_recuperable_kWh": None,
            "energia_recuperada_kWh": None,
            "porcentaje_recuperacion": None,
            "motivo": "Se requieren E_AC de referencia, actual y optimizada.",
        }
    recuperable = max(referencia - actual, 0.0)
    recuperada = min(max(optimizada - actual, 0.0), recuperable)
    porcentaje = (
        recuperada / recuperable * 100.0 if recuperable > 0 else 0.0
    )
    return {
        "disponible": True,
        "energia_recuperable_kWh": round(recuperable, 2),
        "energia_recuperada_kWh": round(recuperada, 2),
        "porcentaje_recuperacion": round(float(np.clip(porcentaje, 0.0, 100.0)), 2),
        "motivo": (
            "No hay pérdida AC recuperable entre referencia y situación actual."
            if recuperable == 0
            else "Comparación AC de escenarios con base común."
        ),
    }