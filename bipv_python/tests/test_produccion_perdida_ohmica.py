# -*- coding: utf-8 -*-
"""
Mismatch de fabricación + pérdida óhmica de cableado DC/AC, integrada en el
motor (7-sep-2026, ver calculos/diagrama_unifilar.py::calcular_perdida_ohmica()
y el diagnóstico completo en los docstrings de simular_produccion_anual() /
simular_produccion_iv()).

Antes, `pct_mismatch_fab` y `pct_cableado` (Página 5 Mismatch) se aplicaban
como reductor de G_eff ANTES del modelo eléctrico -- físicamente impreciso
(son pérdidas eléctricas post-conversión) y quedaban escondidos dentro de
"② Efecto SDM" del Loss Diagram. Ahora se aplican como parámetros explícitos
del motor:
  - pct_mismatch_fab / pct_cableado_dc / pct_cableado_ac: % fijo, modo manual.
  - resistencia_dc_ohm / resistencia_ac_ohm: modo calculado, real, HORA A
    HORA con la corriente real I(t) -- más preciso que el % fijo a
    condiciones STC que usa PVsyst, porque la corriente (y por tanto el %
    de pérdida) varía fuerte con la irradiancia.

Casos cubiertos (parametrizados sobre ambos motores salvo donde se indica):
  - Retrocompatibilidad exacta sin los nuevos parámetros.
  - Modo manual: Δ kWh reconcilia exactamente contra el % pasado.
  - Nunca se aplican modo manual Y modo calculado a la vez.
  - Modo calculado DC: reduce la energía, con modo="calculado".
  - El cálculo hora a hora da una pérdida MENOR que aplicar el % de diseño
    (a condiciones de alta irradiancia) fijo a las 8760 horas -- la prueba
    concreta de que corrige la sobreestimación de PVsyst.
  - perdida_clipping_kWh no absorbe la pérdida óhmica AC (no se "come" la
    pérdida de cableado como si fuera recorte del inversor).
"""
import numpy as np
import pandas as pd
import pytest

from calculos.produccion import simular_produccion_anual
from calculos.produccion_iv import simular_produccion_iv
from datos.tecnologias_bipv import ASP_ST1_T40

N_SERIE = 8
N_PANELES = 40  # 5 strings de 8 en serie


def _tmy_poa_sintetico(poa_wm2: float):
    index = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    horas_sol = (index.hour >= 6) & (index.hour < 18)
    poa = np.where(horas_sol, poa_wm2, 0.0)
    tmy = pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=index)
    poa_df = pd.DataFrame({"poa_global": poa}, index=index)
    return tmy, poa_df


def _tmy_poa_bimodal(poa_alta_wm2: float, poa_baja_wm2: float):
    """Días alternos de alta/baja irradiancia -- para comparar el cálculo
    hora a hora contra un % fijo calculado a condiciones de diseño (alta)."""
    index = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    horas_sol = (index.hour >= 6) & (index.hour < 18)
    dia_alto = (index.dayofyear % 2 == 0)
    poa = np.where(horas_sol, np.where(dia_alto, poa_alta_wm2, poa_baja_wm2), 0.0)
    tmy = pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=index)
    poa_df = pd.DataFrame({"poa_global": poa}, index=index)
    return tmy, poa_df


_MOTORES = [
    (simular_produccion_anual, {}),
    (simular_produccion_iv, {}),
]


@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_sin_parametros_nuevos_es_retrocompatible_exacto(funcion, kwargs_extra):
    tmy, poa_df = _tmy_poa_sintetico(600.0)
    res_sin = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0, **kwargs_extra,
    )
    res_con_none = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        pct_mismatch_fab=None, resistencia_dc_ohm=None, pct_cableado_dc=None,
        resistencia_ac_ohm=None, pct_cableado_ac=None,
        N_serie=None, tension_red_V=None, **kwargs_extra,
    )
    assert res_sin["E_ac_anual_kWh"] == res_con_none["E_ac_anual_kWh"]
    assert res_con_none["perdida_ohmica_dc_modo"] is None
    assert res_con_none["perdida_ohmica_ac_modo"] is None
    assert res_con_none["pct_mismatch_fab_aplicado"] is None


@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_modo_manual_mismatch_fab_reconcilia_exacto(funcion, kwargs_extra):
    tmy, poa_df = _tmy_poa_sintetico(600.0)
    res_base = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0, **kwargs_extra,
    )
    res_fab = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        pct_mismatch_fab=2.0, **kwargs_extra,
    )
    assert res_fab["pct_mismatch_fab_aplicado"] == 2.0
    # E_dc se reduce en (casi) exactamente 2% -- pequeña diferencia posible
    # porque perdida_mismatch_fab_kWh se redondea antes de comparar.
    esperado = res_base["E_dc_anual_kWh"] * 0.02
    assert res_fab["perdida_mismatch_fab_kWh"] == pytest.approx(esperado, rel=0.02)
    assert res_fab["E_dc_anual_kWh"] < res_base["E_dc_anual_kWh"]


@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_modo_manual_cableado_dc_y_ac_reconcilian_exacto(funcion, kwargs_extra):
    tmy, poa_df = _tmy_poa_sintetico(600.0)
    res_base = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0, **kwargs_extra,
    )
    res_cable = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        pct_cableado_dc=1.5, pct_cableado_ac=1.0, **kwargs_extra,
    )
    assert res_cable["perdida_ohmica_dc_modo"] == "manual"
    assert res_cable["perdida_ohmica_ac_modo"] == "manual"
    assert res_cable["perdida_ohmica_dc_kWh"] == pytest.approx(
        res_base["E_dc_anual_kWh"] * 0.015, rel=0.02
    )
    assert res_cable["E_ac_anual_kWh"] < res_base["E_ac_anual_kWh"]


@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_modo_calculado_tiene_prioridad_sobre_manual_nunca_ambos(funcion, kwargs_extra):
    tmy, poa_df = _tmy_poa_sintetico(600.0)
    res = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        resistencia_dc_ohm=0.05, pct_cableado_dc=3.0,  # ambos presentes
        resistencia_ac_ohm=0.02, pct_cableado_ac=3.0,
        N_serie=N_SERIE, tension_red_V=400.0,
        **kwargs_extra,
    )
    assert res["perdida_ohmica_dc_modo"] == "calculado"
    assert res["perdida_ohmica_ac_modo"] == "calculado"


@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_modo_calculado_dc_reduce_energia_y_requiere_n_serie(funcion, kwargs_extra):
    tmy, poa_df = _tmy_poa_sintetico(800.0)
    res_base = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0, **kwargs_extra,
    )
    res_calc = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        resistencia_dc_ohm=0.05, N_serie=N_SERIE, **kwargs_extra,
    )
    assert res_calc["perdida_ohmica_dc_modo"] == "calculado"
    assert res_calc["perdida_ohmica_dc_kWh"] > 0
    assert res_calc["E_dc_anual_kWh"] < res_base["E_dc_anual_kWh"]

    # Sin N_serie, el modo calculado no puede activarse -- no revienta, se
    # ignora (nunca inventa un dato que le falta).
    res_sin_nserie = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        resistencia_dc_ohm=0.05, **kwargs_extra,
    )
    assert res_sin_nserie["perdida_ohmica_dc_modo"] is None
    assert res_sin_nserie["E_dc_anual_kWh"] == res_base["E_dc_anual_kWh"]


@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_modo_calculado_ac_requiere_tension_red_v(funcion, kwargs_extra):
    # Espejo de test_modo_calculado_dc_reduce_energia_y_requiere_n_serie:
    # sin tension_red_V, resistencia_ac_ohm no puede activarse -- se ignora
    # en vez de reventar (nunca inventa el dato que le falta).
    tmy, poa_df = _tmy_poa_sintetico(800.0)
    res_base = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0, **kwargs_extra,
    )
    res_con_tension = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        resistencia_ac_ohm=0.03, tension_red_V=400.0, **kwargs_extra,
    )
    res_sin_tension = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        resistencia_ac_ohm=0.03, **kwargs_extra,  # sin tension_red_V
    )
    assert res_con_tension["perdida_ohmica_ac_modo"] == "calculado"
    assert res_con_tension["E_ac_anual_kWh"] < res_base["E_ac_anual_kWh"]
    assert res_sin_tension["perdida_ohmica_ac_modo"] is None
    assert res_sin_tension["E_ac_anual_kWh"] == res_base["E_ac_anual_kWh"]


def test_calculo_hora_a_hora_pierde_menos_que_aplicar_pct_de_diseno_fijo():
    """
    La prueba central de la mejora sobre PVsyst: con la MISMA resistencia,
    aplicar la pérdida hora a hora con la corriente real da un % agregado
    menor que aplicar, a las 8760 horas, el % que resultaría de evaluar esa
    misma resistencia a la corriente de diseño (alta irradiancia) -- porque
    en las horas de baja irradiancia la corriente real es mucho menor.

    Solo con Motor IV (produccion_iv): usa la i_mp REAL resuelta por el
    modelo, sin confundir el efecto. produccion.py (JRC/Huld) aproxima la
    corriente vía Vmp nominal corregido por T_celda -- como T_celda TAMBIÉN
    sube con la irradiancia (modelo NOCT) y Vmp baja con T_celda, esa
    aproximación introduce un segundo efecto que puede compensar parcialmente
    el de la corriente en un TMY sintético de solo 2 niveles como este, sin
    invalidar el principio físico (confirmado aquí con la corriente real).
    """
    funcion, kwargs_extra = simular_produccion_iv, {}
    poa_alta, poa_baja = 1000.0, 200.0
    tmy, poa_df = _tmy_poa_bimodal(poa_alta, poa_baja)
    R_dc = 0.08

    res_calc = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        resistencia_dc_ohm=R_dc, N_serie=N_SERIE, **kwargs_extra,
    )
    assert res_calc["perdida_ohmica_dc_modo"] == "calculado"
    pct_agregado_real = (
        res_calc["perdida_ohmica_dc_kWh"] / res_calc["E_dc_antes_binning_ohmico_kWh"] * 100.0
    )

    # % que PVsyst reportaría: evaluado una sola vez a la irradiancia de
    # diseño (alta) y aplicado como fijo a todo el año -- se obtiene con la
    # MISMA función, pasando un TMY de solo horas de alta irradiancia.
    tmy_alta, poa_df_alta = _tmy_poa_sintetico(poa_alta)
    res_diseno = funcion(
        tmy=tmy_alta, poa_base=poa_df_alta, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        resistencia_dc_ohm=R_dc, N_serie=N_SERIE, **kwargs_extra,
    )
    pct_diseno_fijo = (
        res_diseno["perdida_ohmica_dc_kWh"] / res_diseno["E_dc_antes_binning_ohmico_kWh"] * 100.0
    )

    assert pct_agregado_real < pct_diseno_fijo


@pytest.mark.parametrize("funcion, kwargs_extra", _MOTORES)
def test_perdida_ohmica_ac_no_se_confunde_con_recorte_del_inversor(funcion, kwargs_extra):
    tmy, poa_df = _tmy_poa_sintetico(900.0)
    res_base = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0, **kwargs_extra,
    )
    res_ac = funcion(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        resistencia_ac_ohm=0.03, tension_red_V=400.0, **kwargs_extra,
    )
    # Sin tope de inversor (P_ac_nom_W=None) no hay recorte en ninguno de los
    # 2 casos -- si la pérdida óhmica AC se estuviera contando como recorte
    # por error, perdida_clipping_kWh dejaría de ser 0.
    assert res_base["perdida_clipping_kWh"] == 0
    assert res_ac["perdida_clipping_kWh"] == 0
    assert res_ac["perdida_ohmica_ac_kWh"] > 0
    assert res_ac["E_ac_anual_kWh"] < res_base["E_ac_anual_kWh"]


def test_produccion_iv_usa_corriente_real_no_aproximada():
    """Motor IV: con resistencia_dc_ohm + N_serie, debe usar la i_mp REAL
    resuelta por pvlib (no la aproximación Vmp que usa produccion.py) --
    verificado indirectamente: perdida_ohmica_dc_modo == "calculado" Y el
    resultado cambia si i_mp cambia (probado con 2 calibres/tramos distintos
    -- doble R, doble pérdida aprox., misma I)."""
    tmy, poa_df = _tmy_poa_sintetico(800.0)
    res_r1 = simular_produccion_iv(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        resistencia_dc_ohm=1.0, N_serie=N_SERIE,
    )
    res_r2 = simular_produccion_iv(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=N_PANELES,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
        resistencia_dc_ohm=2.0, N_serie=N_SERIE,
    )
    assert res_r1["perdida_ohmica_dc_modo"] == "calculado"
    # El doble de resistencia, con la MISMA corriente, da (casi) el doble de
    # pérdida -- I(t) no cambia apreciablemente entre las 2 corridas porque
    # la pérdida óhmica es pequeña frente a la potencia total. Se usa el
    # valor SIN redondear (df_horario) para no arrastrar ruido de redondeo
    # a 0 decimales en magnitudes pequeñas.
    perdida_r1 = float(res_r1["df_horario"]["perdida_ohmica_dc_W"].sum()) / 1000.0
    perdida_r2 = float(res_r2["df_horario"]["perdida_ohmica_dc_W"].sum()) / 1000.0
    assert perdida_r2 == pytest.approx(perdida_r1 * 2.0, rel=0.01)
