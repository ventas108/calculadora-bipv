# -*- coding: utf-8 -*-
"""
P_ac_sin_recorte_kW -- coherencia del comparador de inversores.

Hallazgo (auditoría de coherencia de comparadores, 19-sep-2026): la serie
horaria P_ac_kW que publica Producción YA tiene aplicado el recorte (Pnom)
del inversor ACTUALMENTE seleccionado. pages/4b_⚖️_Comparador_Inversores.py
la reutilizaba como si fuera "sin límite" y volvía a aplicar clipping por
candidato -- imposible recuperar la energía que el inversor original había
recortado, y la comparación quedaba sesgada contra cualquier candidato de
mayor potencia AC.

Fix: calculos/produccion.py y calculos/produccion_iv.py publican además
"P_ac_sin_recorte_kW" en df_horario -- la misma serie física (pérdidas de
temperatura, mismatch, óhmica DC y eficiencia del inversor incluidas) pero
SIN el límite P_ac_nom_W. El comparador debe usar exclusivamente esa serie.

Este archivo cubre el motor (produccion.py / produccion_iv.py) + el reclip
por candidato con calculos.comparador_inversores.energia_con_clipping() /
comparar_configuraciones() -- exactamente lo que hace la página. La
cobertura de la página en sí (qué columna lee, qué hace si falta) está en
tests/test_pagina_comparador_inversores.py.
"""
import numpy as np
import pandas as pd
import pytest

from calculos.produccion import simular_produccion_anual
from calculos.produccion_iv import simular_produccion_iv
from calculos.comparador_inversores import energia_con_clipping, comparar_configuraciones
from datos.tecnologias_bipv import ASP_ST1_T40

N_PANELES = 40  # ver _tmy_poa_sintetico: pico P_ac sin recorte ≈ 1.88 kW

_MOTORES = [
    (simular_produccion_anual, {}),
    (simular_produccion_iv, {}),
]


def _tmy_poa_sintetico(poa_wm2: float = 800.0):
    index = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    horas_sol = (index.hour >= 6) & (index.hour < 18)
    poa = np.where(horas_sol, poa_wm2, 0.0)
    tmy = pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=index)
    poa_df = pd.DataFrame({"poa_global": poa}, index=index)
    return tmy, poa_df


def _simular(funcion, kwargs_extra, **overrides):
    tmy, poa_df = _tmy_poa_sintetico()
    kwargs = dict(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
    )
    kwargs.update(kwargs_extra)
    kwargs.update(overrides)
    return funcion(**kwargs)


# ══════════════════════════════════════════════════════════════════════════
# 1. La columna existe, con la longitud correcta, en ambos motores
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_p_ac_sin_recorte_kw_existe_con_8760_valores(funcion, kwargs_extra):
    res = _simular(funcion, kwargs_extra, P_ac_nom_W=1200.0)
    df = res["df_horario"]
    assert "P_ac_sin_recorte_kW" in df.columns
    assert len(df["P_ac_sin_recorte_kW"]) == 8760
    assert len(df["P_ac_sin_recorte_kW"]) == len(df["P_ac_kW"])


# ══════════════════════════════════════════════════════════════════════════
# 2. Sin recorte activo, P_ac_sin_recorte_kW == P_ac_kW exactamente
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_sin_p_ac_nom_w_las_dos_series_coinciden(funcion, kwargs_extra):
    res = _simular(funcion, kwargs_extra)  # P_ac_nom_W=None -- sin recorte
    df = res["df_horario"]
    np.testing.assert_array_equal(
        df["P_ac_sin_recorte_kW"].to_numpy(), df["P_ac_kW"].to_numpy()
    )


# ══════════════════════════════════════════════════════════════════════════
# 3. Con recorte activo: P_ac_kW sigue topada (comportamiento actual
#    intacto); P_ac_sin_recorte_kW NO tiene el límite aplicado.
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_p_ac_kw_mantiene_su_comportamiento_de_clipping_actual(funcion, kwargs_extra):
    cap_w = 1200.0
    res = _simular(funcion, kwargs_extra, P_ac_nom_W=cap_w)
    df = res["df_horario"]
    assert df["P_ac_kW"].max() * 1000.0 <= cap_w + 1e-6
    assert res["perdida_clipping_kWh"] > 0
    assert res["horas_con_clipping"] > 0


@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_p_ac_sin_recorte_kw_supera_el_limite_en_horas_de_clipping(funcion, kwargs_extra):
    cap_w = 1200.0
    res = _simular(funcion, kwargs_extra, P_ac_nom_W=cap_w)
    df = res["df_horario"]
    horas_clip = df["clipping_kW"] > 1e-6
    assert horas_clip.any(), "el escenario sintético debe producir clipping real"
    # En esas horas, la serie sin recorte SÍ supera el límite del inversor
    # original -- es justo la energía que P_ac_kW perdió por el recorte.
    assert (df.loc[horas_clip, "P_ac_sin_recorte_kW"] * 1000.0 > cap_w + 1e-6).all()
    # E_ac_sin_recorte_kWh (agregado anual ya existente) reconcilia con la
    # suma horaria de la nueva columna.
    assert res["E_ac_sin_recorte_kWh"] == pytest.approx(
        df["P_ac_sin_recorte_kW"].sum(), abs=1.0
    )


# ══════════════════════════════════════════════════════════════════════════
# 4. El comparador reclippeando P_ac_sin_recorte_kW: candidato mayor
#    recupera energía recortada; candidato menor recorta más.
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_candidato_con_mayor_potencia_recupera_energia_recortada(funcion, kwargs_extra):
    cap_original_w = 1200.0
    res = _simular(funcion, kwargs_extra, P_ac_nom_W=cap_original_w)
    p_ac_sin_recorte_w = res["df_horario"]["P_ac_sin_recorte_kW"].to_numpy() * 1000.0

    e_ac_original_kwh = res["E_ac_anual_kWh"]  # oficial, YA recortada a cap_original_w
    assert res["perdida_clipping_kWh"] > 0  # precondición: sí hubo recorte que recuperar

    # Candidato de mayor potencia AC (2500 W > pico ≈ 1883 W) -- nunca recorta.
    cap_mayor_w = 2500.0
    e_ac_mayor, clip_mayor = energia_con_clipping(p_ac_sin_recorte_w, cap_mayor_w)
    assert clip_mayor == 0.0
    assert e_ac_mayor > e_ac_original_kwh, (
        "un inversor candidato de mayor potencia AC debe recuperar energía "
        "que el inversor original recortó -- objetivo central de este fix"
    )
    # Recupera EXACTAMENTE la energía sin recorte (ninguna pérdida adicional
    # de por medio -- la bug original nunca hubiera podido acercarse a esto).
    # abs=1.0: E_ac_sin_recorte_kWh viene redondeada a entero en el dict de
    # resultado; e_ac_mayor viene de energia_con_clipping() redondeada a 1
    # decimal -- ambas son la MISMA suma, solo con distinto redondeo.
    assert e_ac_mayor == pytest.approx(res["E_ac_sin_recorte_kWh"], abs=1.0)


@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_candidato_con_menor_potencia_aplica_clipping_adicional(funcion, kwargs_extra):
    cap_original_w = 1200.0
    res = _simular(funcion, kwargs_extra, P_ac_nom_W=cap_original_w)
    p_ac_sin_recorte_w = res["df_horario"]["P_ac_sin_recorte_kW"].to_numpy() * 1000.0
    e_ac_original_kwh = res["E_ac_anual_kWh"]

    cap_menor_w = 900.0  # < cap_original_w
    e_ac_menor, clip_menor = energia_con_clipping(p_ac_sin_recorte_w, cap_menor_w)
    assert clip_menor > 0.0
    assert e_ac_menor < e_ac_original_kwh, (
        "un candidato de menor potencia AC debe recortar MÁS que el inversor "
        "original, no reusar el recorte ya aplicado"
    )
    # Coherencia física: nunca por encima de lo que ese tope permite.
    assert e_ac_menor <= cap_menor_w / 1000.0 * 8760


# ══════════════════════════════════════════════════════════════════════════
# 5. Caso multiinversor: el reclip contra un candidato de N unidades
#    recupera/recorta igual que con una unidad equivalente -- mismo camino
#    que pages/4b usa vía comparar_configuraciones() (p_cap = p_ac_unidad_W
#    × n_unidades).
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_caso_multiinversor_candidato_de_mas_unidades_recupera_energia(funcion, kwargs_extra):
    # Original: 2 inversores de 600 W c/u = 1200 W total -- recorta.
    n_original, p_unidad_original_w = 2, 600.0
    res = _simular(funcion, kwargs_extra, P_ac_nom_W=n_original * p_unidad_original_w)
    assert res["perdida_clipping_kWh"] > 0
    p_ac_sin_recorte_w = res["df_horario"]["P_ac_sin_recorte_kW"].to_numpy() * 1000.0
    p_dc_stc_kW = res["P_stc_kW"]

    # Candidato: 2 inversores de 1500 W c/u = 3000 W total -- no recorta.
    df_cmp = comparar_configuraciones(
        p_ac_sin_recorte_w,
        [{"nombre": "Candidato-multi", "p_ac_unidad_W": 1500.0, "n_unidades": 2,
          "costo_unidad_usd": 0.0}],
        p_dc_stc_kW,
        capex_sin_inversores_usd=0.0, tarifa_cop_kwh=950.0, tipo_cambio=4000.0,
    )
    fila = df_cmp.iloc[0]
    assert fila["Clipping (%)"] == 0.0
    assert fila["E_ac (kWh/año)"] > res["E_ac_anual_kWh"]
    assert fila["AC total (kW)"] == pytest.approx(3.0)


# ══════════════════════════════════════════════════════════════════════════
# 6. Resultado "antiguo" (legacy) sin P_ac_sin_recorte_kW -- a nivel de
#    motor esto solo puede pasar con un dict armado a mano (simulando un
#    res_produccion persistido/cacheado de ANTES de este fix); la
#    responsabilidad de rechazarlo es de la página (ver
#    tests/test_pagina_comparador_inversores.py), pero aquí se deja
#    constancia explícita de que el motor SIEMPRE publica la columna --
#    nunca hay que fallar por None/ausencia con el motor actual.
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_el_motor_actual_siempre_publica_la_columna_nueva(funcion, kwargs_extra):
    res = _simular(funcion, kwargs_extra, P_ac_nom_W=1200.0)
    assert "P_ac_sin_recorte_kW" in res["df_horario"].columns
    assert res["df_horario"]["P_ac_sin_recorte_kW"].notna().all()
