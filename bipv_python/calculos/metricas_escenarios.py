"""Métricas separadas para auditoría solar y eléctrica de escenarios.

Regla principal:
    una pérdida de POA se reporta como pérdida solar y no se convierte
    automáticamente en kWh AC. La recuperación solo se calcula comparando
    resultados eléctricos de escenarios con la misma base.
"""
from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

import numpy as np
import pandas as pd

from calculos.agregacion_fs import promedio_fs_por_claves, resolver_peso
from calculos.criticos_solares import (
    calcular_horas_meses_criticos,
    normalizar_configuracion_criticos,
)


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
    modo_agregacion: str = "auto",
    identidad_col: str | None = None,
) -> pd.DataFrame:
    columnas = _periodo_fs(grupo, modo)
    if identidad_col and identidad_col in grupo.columns:
        # Un punto puede aparecer en varios días críticos. Primero se reduce
        # por punto y hora para que la cantidad de registros no cambie su peso.
        fs_punto = (
            grupo.groupby(columnas + [identidad_col], dropna=False)
            .agg(FS_geometrico=("FS_geometrico", "mean"))
            .reset_index()
        )
        columnas_peso = [
            columna
            for columna in (
                "n_modulos",
                "area_activa_m2",
                "potencia_instalada_kw",
            )
            if columna in grupo.columns
        ]
        if columnas_peso:
            pesos = grupo[[identidad_col] + columnas_peso].drop_duplicates(
                subset=[identidad_col]
            )
            fs_punto = fs_punto.merge(pesos, on=identidad_col, how="left")
        fs, auditoria = promedio_fs_por_claves(
            fs_punto, columnas, modo=modo_agregacion
        )
    else:
        fs, auditoria = promedio_fs_por_claves(
            grupo, columnas, modo=modo_agregacion
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
    unido.attrs["agregacion_fs"] = auditoria
    return unido


def _agregar_grupos(
    df_fs: pd.DataFrame | None,
    tmy_index: pd.DatetimeIndex | None,
    poa: pd.Series | None,
    *,
    modo: str,
    columna: str,
    modo_agregacion: str = "auto",
    identidad_col: str | None = None,
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
        alineado = _alinear_fs_grupo(
            grupo,
            tmy_index,
            poa,
            modo=modo,
            modo_agregacion=modo_agregacion,
            identidad_col=identidad_col,
        )
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
                "agregacion": (
                    alineado.attrs.get("agregacion_fs", {}).get(
                        "etiqueta", modo_agregacion
                    )
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
    modo_agregacion_fs: str = "auto",
    configuracion_criticos: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Construye el grupo de métricas solares sin inferir energía AC.

    ``horas_criticas`` y ``meses_criticos`` son diagnóstico independiente:
    nunca filtran ni modifican la serie usada para producción.
    """
    poa_bruta = _float_or_none(poa_bruta_kWh_m2)
    poa_efectiva = _float_or_none(poa_efectiva_kWh_m2)
    config_criticos = normalizar_configuracion_criticos(configuracion_criticos)
    fs = _serie_numerica(
        fs_horario,
        tmy_index if tmy_index is not None else pd.RangeIndex(0),
    )

    if fs is not None and poa_horaria is not None:
        poa = pd.to_numeric(poa_horaria, errors="coerce").fillna(0.0)
        perdida_solar = float((poa.clip(lower=0) * fs).sum() / 1000.0)
        horas_sombra = int((fs > 0).sum())
        criticos = calcular_horas_meses_criticos(
            poa,
            fs,
            configuracion=config_criticos,
        )
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
        meses_criticos = [
            item["mes_nombre"] for item in criticos["meses_criticos"]
        ]
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
        criticos = {
            "configuracion": config_criticos,
            "criterio_hora": (
                "POA >= irradiancia_minima_wm2 y "
                "FS_geometrico > fs_minimo"
            ),
            "criterio_mes": (
                "orden descendente por suma mensual de "
                "poa_perdida_kWh_m2"
            ),
            "horas_sombreadas": horas_sombra,
            "horas_candidatas": 0,
            "horas_criticas": [],
            "meses_criticos": [],
            "mes_critico": None,
        }

    perdida_poa_total = (
        max(poa_bruta - poa_efectiva, 0.0)
        if poa_bruta is not None and poa_efectiva is not None
        else None
    )
    obstaculo_responsable = (
        _agregar_grupos(
            df_fs,
            tmy_index,
            poa_horaria,
            modo=modo_fs,
            columna="obstaculo",
            modo_agregacion=modo_agregacion_fs,
            identidad_col="punto",
        )
    )
    por_fachada = _agregar_grupos(
        df_fs,
        tmy_index,
        poa_horaria,
        modo=modo_fs,
        columna="fachada",
        modo_agregacion=modo_agregacion_fs,
        identidad_col="punto",
    )
    por_fila = _agregar_grupos(
        df_fs,
        tmy_index,
        poa_horaria,
        modo=modo_fs,
        columna="fila",
        modo_agregacion=modo_agregacion_fs,
        identidad_col="punto",
    ) if isinstance(df_fs, pd.DataFrame) and "fila" in df_fs.columns else []
    por_punto = _agregar_grupos(
        df_fs,
        tmy_index,
        poa_horaria,
        modo=modo_fs,
        columna="punto",
        modo_agregacion=modo_agregacion_fs,
    )
    agregacion_auditoria: dict[str, Any] = {
        "modo_solicitado": modo_agregacion_fs,
        "modo_aplicado": "simple",
        "columna_peso": None,
        "etiqueta": "promedio simple por punto",
        "advertencias": [],
    }
    if isinstance(df_fs, pd.DataFrame) and not df_fs.empty:
        _, agregacion_auditoria = resolver_peso(df_fs, modo_agregacion_fs)
    return {
        "poa_bruta_kWh_m2": poa_bruta,
        "poa_efectiva_kWh_m2": poa_efectiva,
        "poa_efectiva_fuente": poa_efectiva_fuente,
        "perdida_poa_solar_kWh_m2": (
            round(perdida_poa_total, 2) if perdida_poa_total is not None else None
        ),
        "perdida_sombreado_poa_kWh_m2": (
            round(perdida_solar, 6) if perdida_solar is not None else None
        ),
        "fs_geometrico_ponderado_pct": round(fs_ponderado_pct, 2),
        "horas_con_sombra": horas_sombra,
        "meses_criticos": meses_criticos,
        "horas_criticas": criticos["horas_criticas"],
        "horas_criticas_n": len(criticos["horas_criticas"]),
        "horas_candidatas_criticas": criticos["horas_candidatas"],
        "meses_criticos_detalle": criticos["meses_criticos"],
        "mes_critico": criticos["mes_critico"],
        "configuracion_criticos": criticos["configuracion"],
        "criterio_hora_critica": criticos["criterio_hora"],
        "criterio_mes_critico": criticos["criterio_mes"],
        "por_fachada": por_fachada,
        "por_fila": por_fila,
        "por_punto": por_punto,
        "por_fila_punto": por_punto or por_fila,
        "agregacion_fs": modo_agregacion_fs,
        "agregacion_fs_auditoria": agregacion_auditoria,
        "nota_agregacion_fs": (
            "La agregación usa el tamaño representado por cada punto. "
            "Si no hay pesos válidos, se informa el fallback a promedio simple."
        ),
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


def contrato_comparacion_escenarios(
    *,
    e_referencia: float | None,
    e_actual: float | None,
    e_optimizada: float | None,
    magnitud: str = "E_AC_anual_kWh",
    unidad: str = "kWh/año",
) -> dict[str, Any]:
    """Aplica el contrato común de pérdidas y recuperación de escenarios.

    ``magnitud`` identifica la misma magnitud usada por los tres escenarios.
    Para la decisión de diseño debe ser ``E_AC_anual_kWh``; ``POA efectiva``
    puede pasarse explícitamente como diagnóstico solar.

    Pérdida del escenario:
        ((E_referencia - E_escenario) / E_referencia) × 100

    Recuperación:
        ((E_optimizada - E_actual) /
         (E_referencia - E_actual)) × 100

    Cuando la referencia es cero o no existe pérdida recuperable, el porcentaje
    no se inventa: se devuelve como ``None`` y con etiqueta ``No aplica``.
    """
    valores = {
        "referencia": _float_or_none(e_referencia),
        "actual": _float_or_none(e_actual),
        "optimizada": _float_or_none(e_optimizada),
    }
    referencia = valores["referencia"]
    perdidas_pct: dict[str, float | None] = {
        "referencia": 0.0 if referencia is not None else None,
        "actual": None,
        "optimizada": None,
    }
    motivo_perdidas = None
    if referencia is None:
        motivo_perdidas = "Se requiere E_referencia para calcular pérdidas."
    elif referencia == 0:
        motivo_perdidas = (
            "E_referencia = 0; las pérdidas porcentuales no aplican."
        )
    else:
        for escenario in ("actual", "optimizada"):
            valor = valores[escenario]
            if valor is not None:
                perdidas_pct[escenario] = round(
                    (referencia - valor) / referencia * 100.0,
                    2,
                )

    actual = valores["actual"]
    optimizada = valores["optimizada"]
    perdida_recuperable = (
        referencia - actual
        if referencia is not None and actual is not None
        else None
    )
    recuperacion_pct: float | None = None
    recuperacion_estado = "pendiente"
    motivo_recuperacion = (
        "Se requieren E_referencia, E_actual y E_optimizada."
    )
    if perdida_recuperable is not None and perdida_recuperable <= 0:
        recuperacion_estado = "no_aplica"
        motivo_recuperacion = (
            "E_referencia - E_actual <= 0; no existe pérdida recuperable."
        )
    elif (
        perdida_recuperable is not None
        and optimizada is not None
        and perdida_recuperable > 0
    ):
        recuperacion_pct = round(
            float(
                np.clip(
                    (optimizada - actual) / perdida_recuperable * 100.0,
                    0.0,
                    100.0,
                )
            ),
            2,
        )
        recuperacion_estado = "calculada"
        motivo_recuperacion = "Comparación con la misma magnitud en los tres escenarios."

    return {
        "magnitud": magnitud,
        "unidad": unidad,
        "es_magnitud_decision": magnitud == "E_AC_anual_kWh",
        "valores": valores,
        "perdidas_pct": perdidas_pct,
        "perdidas_etiqueta": {
            escenario: (
                "No aplica"
                if porcentaje is None
                else f"{porcentaje:.2f}%"
            )
            for escenario, porcentaje in perdidas_pct.items()
        },
        "motivo_perdidas": motivo_perdidas,
        "energia_recuperable": (
            round(max(perdida_recuperable, 0.0), 2)
            if perdida_recuperable is not None
            else None
        ),
        "recuperacion_pct": recuperacion_pct,
        "recuperacion_estado": recuperacion_estado,
        "recuperacion_etiqueta": (
            "No aplica" if recuperacion_estado == "no_aplica"
            else f"{recuperacion_pct:.2f}%" if recuperacion_pct is not None
            else "Pendiente"
        ),
        "motivo_recuperacion": motivo_recuperacion,
        "formula_perdida": (
            "((E_referencia - E_escenario) / E_referencia) × 100"
        ),
        "formula_recuperacion": (
            "((E_optimizada - E_actual) / "
            "(E_referencia - E_actual)) × 100; límite 0–100%"
        ),
    }


def _clave_normalizada(clave: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(clave).lower())


def _extraer_magnitud_resultado(
    resultado: Mapping[str, Any] | None,
    magnitud: str,
) -> float | None:
    """Lee resultados de escenarios tolerando aliases históricos."""
    if not isinstance(resultado, Mapping):
        return None
    normalizadas = {
        _clave_normalizada(clave): valor
        for clave, valor in resultado.items()
    }
    if magnitud == "E_AC_anual_kWh":
        aliases = (
            "eacanualkwh",
            "eackwh",
            "eac",
            "energiaacanualkwh",
        )
    elif magnitud == "POA efectiva":
        aliases = (
            "poaefectivaanualkwhm2",
            "poaefectivakwhm2",
            "poaefectiva",
        )
    else:
        aliases = (_clave_normalizada(magnitud),)
    for alias in aliases:
        if alias in normalizadas:
            valor = _float_or_none(normalizadas[alias])
            if valor is not None:
                return valor
    return None


def comparar_resultados_escenarios(
    resultados: Mapping[str, Mapping[str, Any]] | None,
    *,
    magnitud: str = "E_AC_anual_kWh",
    unidad: str = "kWh/año",
) -> dict[str, Any]:
    """Aplica el contrato a resultados etiquetados por escenario.

    La misma ``magnitud`` se extrae para referencia, actual y optimizada.
    Si falta cualquiera de los tres resultados, el contrato queda pendiente y
    no se sustituye silenciosamente por POA u otra métrica.
    """
    resultados = resultados if isinstance(resultados, Mapping) else {}
    valores = {
        escenario: _extraer_magnitud_resultado(
            resultados.get(escenario),
            magnitud,
        )
        for escenario in ("referencia", "actual", "optimizada")
    }
    contrato = contrato_comparacion_escenarios(
        e_referencia=valores["referencia"],
        e_actual=valores["actual"],
        e_optimizada=valores["optimizada"],
        magnitud=magnitud,
        unidad=unidad,
    )
    contrato["escenarios_completos"] = all(
        valor is not None for valor in valores.values()
    )
    if not contrato["escenarios_completos"]:
        contrato["recuperacion_estado"] = "pendiente"
        contrato["recuperacion_etiqueta"] = "Pendiente"
        contrato["motivo_recuperacion"] = (
            f"Faltan resultados {magnitud} en uno o más escenarios."
        )
    return contrato


def metricas_recuperacion(
    *,
    e_ac_referencia_kWh: float | None,
    e_ac_actual_kWh: float | None,
    e_ac_optimizada_kWh: float | None,
) -> dict[str, Any]:
    """Compatibilidad: aplica el contrato usando E_AC como magnitud de decisión."""
    contrato = contrato_comparacion_escenarios(
        e_referencia=e_ac_referencia_kWh,
        e_actual=e_ac_actual_kWh,
        e_optimizada=e_ac_optimizada_kWh,
        magnitud="E_AC_anual_kWh",
        unidad="kWh/año",
    )
    recuperable = contrato["energia_recuperable"]
    porcentaje = contrato["recuperacion_pct"]
    recuperada = (
        min(
            max(
                (_float_or_none(e_ac_optimizada_kWh) or 0.0)
                - (_float_or_none(e_ac_actual_kWh) or 0.0),
                0.0,
            ),
            recuperable,
        )
        if recuperable is not None
        else None
    )
    return {
        **contrato,
        "disponible": contrato["recuperacion_estado"] == "calculada",
        "energia_recuperable_kWh": recuperable,
        "energia_recuperada_kWh": (
            round(recuperada, 2) if recuperada is not None else None
        ),
        "porcentaje_recuperacion": porcentaje,
        "motivo": contrato["motivo_recuperacion"],
    }