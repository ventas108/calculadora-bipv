"""Regresiones del agregador anual oficial, aún aislado de Producción."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from calculos.agregador_anual import agregar_anual_8760_poa
from calculos.produccion_iv import simular_produccion_iv
from datos.tecnologias_bipv import ASP_ST1_T40


def _serie_anual() -> tuple[pd.DataFrame, pd.DataFrame]:
    index = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    poa = np.zeros(8760, dtype=float)
    poa[0] = 1000.0
    poa[1] = 100.0
    resultado = pd.DataFrame(
        {
            "P_ac_kW": np.full(8760, 1.0),
            "FS_geometrico": np.array([0.5, 1.0] + [0.0] * 8758),
        },
        index=index,
    )
    return resultado, pd.DataFrame({"poa_global": poa}, index=index)


def test_agrega_8760_suma_energia_y_pondera_por_poa() -> None:
    resultado, poa = _serie_anual()

    agregado = agregar_anual_8760_poa(
        resultado,
        poa,
        columnas_energia=("P_ac_kW",),
        metricas_ponderadas_poa=("FS_geometrico",),
    )

    anual = agregado["annual_8760"]
    assert anual["horas"] == 8760
    assert anual["cobertura_completa"] is True
    assert anual["energia"]["P_ac_kW"] == pytest.approx(8760.0)
    assert anual["poa_total_kWh_m2"] == pytest.approx(1.1)
    # (0.5×1000 + 1.0×100) / (1000 + 100) = 6/11
    assert anual["metricas_ponderadas_poa"]["FS_geometrico"] == pytest.approx(6 / 11)


def test_rechaza_hueco_de_cobertura_en_vez_de_intersectar_silenciosamente() -> None:
    resultado, poa = _serie_anual()
    resultado = resultado.drop(resultado.index[100])
    poa = poa.drop(poa.index[100])

    with pytest.raises(ValueError, match="8760"):
        agregar_anual_8760_poa(resultado, poa)


def test_rechaza_indices_desalineados_aunque_ambos_tengan_8760_horas() -> None:
    resultado, poa = _serie_anual()
    poa.index = poa.index + pd.Timedelta(hours=1)

    with pytest.raises(ValueError, match="exactamente el mismo|año TMY"):
        agregar_anual_8760_poa(resultado, poa)


def test_rechaza_ventana_continua_que_no_es_el_ano_tmy_completo() -> None:
    resultado, poa = _serie_anual()
    nuevo_indice = pd.date_range("2001-01-02", periods=8760, freq="h", tz="UTC")
    resultado.index = nuevo_indice
    poa.index = nuevo_indice

    with pytest.raises(ValueError, match="año TMY"):
        agregar_anual_8760_poa(resultado, poa)


def test_agrega_resultado_real_del_motor_iv_sin_reconstruirlo_por_mes() -> None:
    resultado, poa = _serie_anual()
    tmy = pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=resultado.index)
    res_iv = simular_produccion_iv(
        tmy=tmy,
        poa_base=poa,
        panel=ASP_ST1_T40,
        N_paneles=1,
        eta_inversor=0.975,
        factor_pr_mismatch=1.0,
    )

    agregado = agregar_anual_8760_poa(
        res_iv["df_horario"],
        poa,
        columnas_energia=("P_ac_kW",),
    )

    assert agregado["annual_8760"]["horas"] == 8760
    assert agregado["annual_8760"]["energia"]["P_ac_kW"] == pytest.approx(
        res_iv["df_horario"]["P_ac_kW"].sum()
    )


def test_critical_dates_queda_separado_y_no_cambia_el_anual() -> None:
    resultado, poa = _serie_anual()
    critical_dates = {"modo": "critical_dates", "dias": ["21-03", "21-06"]}

    agregado = agregar_anual_8760_poa(
        resultado,
        poa,
        critical_dates=critical_dates,
    )

    assert agregado["critical_dates"] == critical_dates
    assert agregado["annual_8760"]["energia"]["P_ac_kW"] == pytest.approx(8760.0)
