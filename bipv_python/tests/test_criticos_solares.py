"""Pruebas del contrato de criticidad solar.

El contrato es diagnóstico: estas pruebas también verifican que la selección
de horas y meses no pueda convertirse accidentalmente en un filtro de energía.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from calculos.criticos_solares import calcular_horas_meses_criticos
from calculos.metricas_escenarios import metricas_solares


def _series_criticas() -> tuple[pd.Series, pd.Series]:
    idx = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
    # La primera hora tiene sombra total pero POA insuficiente: no es crítica.
    # La última tiene más horas de sombra acumuladas, pero pierde menos energía.
    poa = pd.Series([20.0, 100.0, 800.0, 200.0, 1000.0], index=idx)
    fs = pd.Series([1.0, 0.05, 0.5, 0.9, 0.1], index=idx)
    return poa, fs


def test_excluye_madrugada_y_umbral_no_superado() -> None:
    poa, fs = _series_criticas()
    resultado = calcular_horas_meses_criticos(poa, fs)

    timestamps = [fila["timestamp"] for fila in resultado["horas_criticas"]]
    assert poa.index[0].isoformat() not in timestamps
    # FS exactamente igual al umbral no cumple "superior a".
    assert poa.index[1].isoformat() not in timestamps
    assert resultado["horas_candidatas"] == 3


def test_mes_critico_se_ordena_por_energia_perdida_y_no_por_horas() -> None:
    idx = pd.DatetimeIndex(
        [
            "2024-01-01 10:00",
            "2024-01-01 11:00",
            "2024-02-01 10:00",
            "2024-02-01 11:00",
        ],
        tz="UTC",
    )
    poa = pd.Series([1000.0, 1000.0, 100.0, 100.0], index=idx)
    fs = pd.Series([0.2, 0.2, 1.0, 1.0], index=idx)

    resultado = calcular_horas_meses_criticos(
        poa,
        fs,
        configuracion={"top_n_meses": 2},
    )

    # Enero pierde 400 Wh/m² y febrero 200 Wh/m². El ranking usa energía,
    # no la cantidad de horas sombreadas.
    assert resultado["mes_critico"]["mes_nombre"] == "Ene"
    assert resultado["mes_critico"]["poa_perdida_kWh_m2"] == pytest.approx(0.4)


def test_metricas_exponen_criterio_sin_cambiar_perdida_solar() -> None:
    poa, fs = _series_criticas()
    metricas = metricas_solares(
        poa_bruta_kWh_m2=float(poa.sum() / 1000.0),
        fs_horario=fs,
        tmy_index=poa.index,
        poa_horaria=poa,
    )

    assert metricas["perdida_sombreado_poa_kWh_m2"] == pytest.approx(
        float((poa * fs).sum() / 1000.0)
    )
    assert metricas["configuracion_criticos"]["fs_minimo"] == 0.05
    assert "FS_geometrico > fs_minimo" in metricas["criterio_hora_critica"]


@pytest.mark.parametrize(
    "configuracion",
    [
        {"fs_minimo": 1.1},
        {"irradiancia_minima_wm2": -1},
        {"top_n_meses": 0},
        {"clave_inexistente": 1},
    ],
)
def test_configuracion_invalida_no_se_acepta_silenciosamente(configuracion) -> None:
    poa, fs = _series_criticas()
    with pytest.raises(ValueError):
        calcular_horas_meses_criticos(poa, fs, configuracion=configuracion)


def test_energia_horaria_no_se_filtra_por_criticidad() -> None:
    poa, fs = _series_criticas()
    p_ac = pd.Series(np.full(len(poa), 2.0), index=poa.index)
    resultado = calcular_horas_meses_criticos(poa, fs)

    # El diagnóstico puede seleccionar una parte de las horas, pero la
    # producción oficial seguiría sumando todas las horas del TMY.
    assert len(resultado["detalle_horario"]) == len(poa)
    assert p_ac.sum() == pytest.approx(10.0)


def test_no_completa_el_ranking_con_meses_sin_perdida() -> None:
    idx = pd.DatetimeIndex(
        ["2024-01-01 12:00", "2024-02-01 12:00"],
        tz="UTC",
    )
    resultado = calcular_horas_meses_criticos(
        pd.Series([1000.0, 1000.0], index=idx),
        pd.Series([0.5, 0.0], index=idx),
        configuracion={"top_n_meses": 3},
    )

    assert [m["mes_nombre"] for m in resultado["meses_criticos"]] == ["Ene"]