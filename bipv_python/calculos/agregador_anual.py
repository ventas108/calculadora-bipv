"""
Agregación oficial del resultado horario Python para un año TMY completo.

Este módulo es deliberadamente independiente de las páginas Streamlit y de
Producción. Su responsabilidad es convertir un resultado horario ya calculado
en un contrato anual auditable, sin reconstruir energía desde promedios
mensuales ni mezclar fechas críticas con el año completo.

Unidades esperadas:
  - ``poa_global``: irradiancia horaria en W/m².
  - columnas de energía/potencia: valores por hora; por ejemplo ``P_ac_kW``
    representa kWh al sumar 8760 registros de una hora.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
import pandas as pd


HORAS_ANUALES_TMY = 8760


def _validar_indice_horario(
    df: pd.DataFrame,
    *,
    nombre: str,
) -> None:
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(f"{nombre} requiere un DatetimeIndex")
    if df.index.has_duplicates:
        raise ValueError(f"{nombre} contiene timestamps duplicados")
    if len(df) != HORAS_ANUALES_TMY:
        raise ValueError(
            f"{nombre} debe tener cobertura completa de {HORAS_ANUALES_TMY} horas; "
            f"recibidas: {len(df)}"
        )
    if not df.index.is_monotonic_increasing:
        raise ValueError(f"{nombre} debe estar ordenado cronológicamente")

    diferencias = df.index.to_series().diff().dropna()
    if not diferencias.eq(pd.Timedelta(hours=1)).all():
        raise ValueError(
            f"{nombre} debe tener una frecuencia horaria continua de 1 hora"
        )

    primero = df.index[0]
    ultimo = df.index[-1]
    inicio_tmy = pd.Timestamp(
        year=int(primero.year),
        month=1,
        day=1,
        tz=primero.tz,
    )
    fin_tmy = pd.Timestamp(
        year=int(primero.year),
        month=12,
        day=31,
        hour=23,
        tz=primero.tz,
    )
    if primero != inicio_tmy or ultimo != fin_tmy or primero.year != ultimo.year:
        raise ValueError(
            f"{nombre} debe cubrir exactamente el año TMY no bisiesto "
            "(01-ene 00:00 a 31-dic 23:00)"
        )


def _validar_columna_numerica(
    df: pd.DataFrame,
    columna: str,
    *,
    nombre: str,
    no_negativa: bool = False,
) -> pd.Series:
    if columna not in df.columns:
        raise ValueError(f"{nombre} no contiene la columna requerida '{columna}'")

    serie = pd.to_numeric(df[columna], errors="coerce")
    valores = serie.to_numpy(dtype=float)
    if not np.isfinite(valores).all():
        raise ValueError(f"{nombre}.{columna} contiene valores no finitos")
    if no_negativa and (valores < 0).any():
        raise ValueError(f"{nombre}.{columna} no puede contener valores negativos")
    return serie.astype(float)


def validar_cobertura_anual_8760(
    resultado_horario: pd.DataFrame,
    poa_horaria: pd.DataFrame,
    *,
    poa_col: str = "poa_global",
) -> None:
    """
    Valida que resultado y POA representen el mismo año horario completo.

    La validación es estricta a propósito: una intersección de índices que
    descarte horas silenciosamente no es válida para el agregador oficial.
    """
    if not isinstance(resultado_horario, pd.DataFrame):
        raise ValueError("resultado_horario debe ser un DataFrame")
    if not isinstance(poa_horaria, pd.DataFrame):
        raise ValueError("poa_horaria debe ser un DataFrame")

    _validar_indice_horario(
        resultado_horario,
        nombre="resultado_horario",
    )
    _validar_indice_horario(
        poa_horaria,
        nombre="poa_horaria",
    )

    if not resultado_horario.index.equals(poa_horaria.index):
        raise ValueError(
            "resultado_horario y poa_horaria deben tener exactamente el mismo "
            "índice horario; no se permite una intersección parcial"
        )

    _validar_columna_numerica(
        poa_horaria,
        poa_col,
        nombre="poa_horaria",
        no_negativa=True,
    )


def validar_entradas_horarias_8760(
    tmy: pd.DataFrame,
    poa_base: pd.DataFrame,
    *,
    poa_col: str = "poa_global",
) -> None:
    """
    Valida las entradas físicas antes de ejecutar Producción.

    A diferencia de una intersección de índices, esta función falla si una
    fuente está truncada, desplazada o contiene un hueco horario. ``tmy`` debe
    contener ``T2m`` y ``poa_base`` debe contener la POA usada por el motor.
    """
    if not isinstance(tmy, pd.DataFrame):
        raise ValueError("tmy debe ser un DataFrame")
    if not isinstance(poa_base, pd.DataFrame):
        raise ValueError("poa_base debe ser un DataFrame")

    _validar_indice_horario(tmy, nombre="tmy")
    _validar_indice_horario(poa_base, nombre="poa_base")

    if not tmy.index.equals(poa_base.index):
        raise ValueError(
            "tmy y poa_base deben tener exactamente el mismo índice horario; "
            "no se permite una intersección parcial"
        )

    _validar_columna_numerica(tmy, "T2m", nombre="tmy")
    _validar_columna_numerica(
        poa_base,
        poa_col,
        nombre="poa_base",
        no_negativa=True,
    )


def agregar_anual_8760_poa(
    resultado_horario: pd.DataFrame,
    poa_horaria: pd.DataFrame,
    *,
    columnas_energia: Iterable[str] = ("P_ac_kW",),
    metricas_ponderadas_poa: Iterable[str] = (),
    poa_col: str = "poa_global",
    critical_dates: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Agrega el resultado horario Python al contrato anual oficial.

    ``columnas_energia`` se suman directamente hora a hora. No se multiplican
    promedios mensuales por días ni se rellena cobertura faltante.

    ``metricas_ponderadas_poa`` se reportan como:

        sum(métrica × POA) / sum(POA)

    Esto es útil para factores horarios como FS geométrico o factores de
    rendimiento, donde una media simple daría el mismo peso a la noche que a
    las horas con irradiancia útil.

    ``critical_dates`` es únicamente diagnóstico y se devuelve separado. Nunca
    participa en ``annual_8760``.
    """
    columnas_energia = tuple(dict.fromkeys(columnas_energia))
    metricas_ponderadas_poa = tuple(dict.fromkeys(metricas_ponderadas_poa))
    if not columnas_energia and not metricas_ponderadas_poa:
        raise ValueError("Debe solicitar al menos una métrica horaria")

    validar_cobertura_anual_8760(
        resultado_horario,
        poa_horaria,
        poa_col=poa_col,
    )

    poa = _validar_columna_numerica(
        poa_horaria,
        poa_col,
        nombre="poa_horaria",
        no_negativa=True,
    )
    poa_total_kwh_m2 = float(poa.sum()) / 1000.0
    if poa_total_kwh_m2 <= 0:
        raise ValueError("La POA anual debe ser mayor que cero para ponderar")

    energia = {}
    for columna in columnas_energia:
        serie = _validar_columna_numerica(
            resultado_horario,
            columna,
            nombre="resultado_horario",
            no_negativa=True,
        )
        energia[columna] = float(serie.sum())

    ponderadas = {}
    for columna in metricas_ponderadas_poa:
        serie = _validar_columna_numerica(
            resultado_horario,
            columna,
            nombre="resultado_horario",
        )
        ponderadas[columna] = float((serie * poa).sum() / poa.sum())

    annual_8760 = {
        "horas": HORAS_ANUALES_TMY,
        "cobertura_completa": True,
        "inicio": resultado_horario.index[0].isoformat(),
        "fin": resultado_horario.index[-1].isoformat(),
        "anio_tmy": int(resultado_horario.index[0].year),
        "zona_horaria": (
            str(resultado_horario.index.tz)
            if resultado_horario.index.tz is not None
            else "naive"
        ),
        "poa_col": poa_col,
        "poa_total_kWh_m2": poa_total_kwh_m2,
        "energia": energia,
        "metricas_ponderadas_poa": ponderadas,
    }

    return {
        "annual_8760": annual_8760,
        "critical_dates": dict(critical_dates) if critical_dates is not None else None,
    }
