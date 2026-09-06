# -*- coding: utf-8 -*-
"""
Fix real (6-sep-2026, encontrado auditando calculos/produccion.py): el
Reference Yield (Y_r) y el Performance Ratio (PR) deben referenciarse a la
POA BRUTA real del sitio (IEC 61724), no a `poa_base` -- que con Motor
Óptico activo ya viene post-IAM+soiling (`poa_sin_termico_df`), "adelgazando"
el denominador y mostrando un PR más alto que el estándar exige.

Nuevo parámetro opcional `poa_bruta_kWh_m2` en simular_produccion_anual() y
simular_produccion_iv() -- None (default) conserva el comportamiento
histórico exacto (retrocompatible); si se pasa, Y_r lo usa directo.
"""
import numpy as np
import pandas as pd
import pytest

from calculos.produccion import simular_produccion_anual
from calculos.produccion_iv import simular_produccion_iv
from datos.tecnologias_bipv import ASP_ST1_T40


def _tmy_poa_sintetico(poa_wm2: float):
    """Un año sintético con la MISMA irradiancia constante en cada hora de
    sol (12h/día, 365 días) -- deliberadamente simple para que la suma
    anual de POA sea una cuenta fácil de verificar a mano."""
    index = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    horas_sol = (index.hour >= 6) & (index.hour < 18)
    poa = np.where(horas_sol, poa_wm2, 0.0)
    tmy = pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=index)
    poa_df = pd.DataFrame({"poa_global": poa}, index=index)
    return tmy, poa_df


@pytest.mark.parametrize("funcion, kwargs_extra", [
    (simular_produccion_anual, {}),
    (simular_produccion_iv, {}),
])
def test_sin_poa_bruta_kwh_m2_es_retrocompatible_exacto(funcion, kwargs_extra):
    tmy, poa_df = _tmy_poa_sintetico(500.0)
    res = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=1,
        eta_inversor=0.975, factor_pr_mismatch=1.0, **kwargs_extra,
    )
    assert res["Y_r_es_bruta_real"] is False
    # Comportamiento histórico: Y_r = suma(poa_base)/1000, redondeado.
    assert res["Y_r"] == round(float(poa_df["poa_global"].sum()) / 1000.0, 0)


@pytest.mark.parametrize("funcion, kwargs_extra", [
    (simular_produccion_anual, {}),
    (simular_produccion_iv, {}),
])
def test_con_poa_bruta_kwh_m2_yr_usa_la_bruta_real_no_poa_base(funcion, kwargs_extra):
    # poa_base simula el escenario con Motor Óptico activo: YA viene reducida
    # (post-IAM+soiling) frente a la bruta real del sitio -- deben diferir
    # para que el test detecte si el fix realmente cambia el denominador.
    tmy, poa_base_reducida = _tmy_poa_sintetico(450.0)   # "post-IAM+soiling"
    poa_bruta_real_kWh_m2 = 500.0 * 12 * 365 / 1000.0    # la bruta real, sin reducir

    res = funcion(
        tmy=tmy, poa_base=poa_base_reducida, panel=ASP_ST1_T40, N_paneles=1,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        poa_bruta_kWh_m2=poa_bruta_real_kWh_m2, **kwargs_extra,
    )
    assert res["Y_r_es_bruta_real"] is True
    assert res["Y_r"] == pytest.approx(poa_bruta_real_kWh_m2, abs=0.5)
    # El fallback (sum de poa_base, la reducida) NO debe ser lo que se usó --
    # confirma que el fix realmente ignora poa_base para este cálculo.
    yr_fallback_viejo = round(float(poa_base_reducida["poa_global"].sum()) / 1000.0, 0)
    assert res["Y_r"] != yr_fallback_viejo
    # PR debe ser MENOR que si (incorrectamente) se hubiera usado la reducida
    # como referencia -- una referencia más grande (bruta real) da un PR más
    # bajo y correcto, nunca inflado.
    pr_con_fallback_viejo = res["Y_f"] / yr_fallback_viejo if yr_fallback_viejo else 0.0
    assert res["PR"] < pr_con_fallback_viejo
