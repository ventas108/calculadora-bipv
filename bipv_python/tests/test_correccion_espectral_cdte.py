# -*- coding: utf-8 -*-
"""
Corrección espectral CdTe (6-sep-2026, pedido explícito del usuario tras la
auditoría del motor de producción) — modelo First Solar
(pvlib.spectrum.spectral_factor_firstsolar, coeficientes 'cdte'), el mismo
enfoque que usa PVsyst para esta tecnología.

Cubre:
  1. calcular_factor_espectral_cdte(): fallback retrocompatible sin columna
     RH, rango físico del factor, cero efecto de noche, y un cálculo
     independiente (NO reutiliza el código del módulo) para una hora
     puntual, cruzando el resultado contra pvlib llamado a mano.
  2. simular_produccion_anual(): retrocompatibilidad exacta sin el
     parámetro nuevo, aplicación solo a paneles CdTe (nunca a otras
     tecnologías aunque se pase el factor), y dirección física correcta
     (factor<1 reduce E_dc, factor>1 la aumenta).
"""
import numpy as np
import pandas as pd
import pvlib
import pytest

from calculos.correccion_espectral import calcular_factor_espectral_cdte
from calculos.produccion import simular_produccion_anual
from calculos.produccion_iv import simular_produccion_iv
from datos.tecnologias_bipv import ASP_ST1_T40

LAT, LON, ALT_M = 7.884, -76.635, 30.0   # Urabá, ya usado en otros tests del repo


def _tmy_sintetico(con_rh: bool = True):
    idx = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    loc = pvlib.location.Location(latitude=LAT, longitude=LON, altitude=ALT_M, tz="UTC")
    cs = loc.get_clearsky(idx, model="ineichen")
    datos = {
        "G_h": cs["ghi"].values, "Gb_n": cs["dni"].values, "Gd_h": cs["dhi"].values,
        "T2m": 27.0, "WS10m": 2.0, "SP": 100_500.0,
    }
    if con_rh:
        datos["RH"] = 85.0
    return pd.DataFrame(datos, index=idx)


# ---------------------------------------------------------------------------
# calcular_factor_espectral_cdte()
# ---------------------------------------------------------------------------


def test_sin_columna_rh_no_falla_y_no_aplica_correccion():
    tmy = _tmy_sintetico(con_rh=False)
    serie = calcular_factor_espectral_cdte(tmy, LAT, LON, ALT_M)
    assert (serie == 1.0).all()
    assert serie.attrs["aplicado"] is False
    assert "RH" in serie.attrs["motivo"]


def test_con_rh_el_factor_queda_en_rango_fisico_razonable():
    tmy = _tmy_sintetico()
    serie = calcular_factor_espectral_cdte(tmy, LAT, LON, ALT_M)
    assert serie.attrs["aplicado"] is True
    # Rango del modelo First Solar en condiciones reales -- ver docstring del
    # módulo (~0.89-1.05 típico); el clip defensivo es más ancho (0.5-1.5).
    assert serie.between(0.5, 1.5).all()
    assert not serie.isna().any()


def test_de_noche_el_factor_es_exactamente_1_0():
    tmy = _tmy_sintetico()
    loc = pvlib.location.Location(latitude=LAT, longitude=LON, altitude=ALT_M, tz="UTC")
    solpos = loc.get_solarposition(tmy.index)
    serie = calcular_factor_espectral_cdte(tmy, LAT, LON, ALT_M)
    mask_noche = solpos["apparent_elevation"].to_numpy() <= 0.0
    assert (serie.to_numpy()[mask_noche] == 1.0).all()


def test_cruce_independiente_contra_pvlib_llamado_a_mano_una_hora():
    # Cálculo COMPLETO por fuera del módulo (no se reutiliza ninguna función
    # de correccion_espectral.py) para una hora puntual con sol, verificando
    # que el módulo no tenga un error de transcripción de la fórmula.
    tmy = _tmy_sintetico()
    hora = tmy.index[12 * 30 + 12]   # mediodía UTC de un día cualquiera con sol
    loc = pvlib.location.Location(latitude=LAT, longitude=LON, altitude=ALT_M, tz="UTC")
    solpos_h = loc.get_solarposition(pd.DatetimeIndex([hora]))

    pw_manual = pvlib.atmosphere.gueymard94_pw(
        np.array([27.0]), np.array([85.0])
    )
    am_rel_manual = pvlib.atmosphere.get_relative_airmass(solpos_h["apparent_zenith"])
    am_abs_manual = pvlib.atmosphere.get_absolute_airmass(am_rel_manual, np.array([100_500.0]))
    esperado = pvlib.spectrum.spectral_factor_firstsolar(
        pw_manual, am_abs_manual.to_numpy(), module_type="cdte",
    )[0]

    serie = calcular_factor_espectral_cdte(tmy, LAT, LON, ALT_M)
    assert serie.loc[hora] == pytest.approx(esperado, rel=1e-9)


# ---------------------------------------------------------------------------
# simular_produccion_anual() -- integración
# ---------------------------------------------------------------------------


def test_sin_factor_espectral_es_retrocompatible_exacto():
    tmy = _tmy_sintetico()
    poa_df = pd.DataFrame({"poa_global": tmy["G_h"] * 1.1}, index=tmy.index)  # POA sintética
    res_sin_param = simular_produccion_anual(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
    )
    res_con_none = simular_produccion_anual(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0, factor_espectral=None,
    )
    assert res_sin_param["factor_espectral_aplicado"] is False
    assert res_sin_param["factor_espectral_promedio"] is None
    assert res_sin_param["E_dc_anual_kWh"] == res_con_none["E_dc_anual_kWh"]


def test_factor_menor_a_1_reduce_e_dc_en_panel_cdte():
    tmy = _tmy_sintetico()
    poa_df = pd.DataFrame({"poa_global": tmy["G_h"] * 1.1}, index=tmy.index)
    factor_reductor = pd.Series(0.9, index=tmy.index)   # -10% constante, sencillo de razonar

    assert ASP_ST1_T40["tecnologia"] == "CdTe"   # panel real ya usado en Teusaquillo

    res_base = simular_produccion_anual(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
    )
    res_corregido = simular_produccion_anual(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0, factor_espectral=factor_reductor,
    )
    assert res_corregido["factor_espectral_aplicado"] is True
    assert res_corregido["factor_espectral_promedio"] == pytest.approx(0.9, abs=1e-6)
    assert res_corregido["E_dc_anual_kWh"] < res_base["E_dc_anual_kWh"]
    # H_ef (irradiancia efectiva reportada) NO debe cambiar -- el efecto
    # espectral no es un cambio de irradiancia física, solo del cálculo
    # eléctrico (ver docstring de "factor_espectral" en produccion.py).
    assert res_corregido["H_ef_kWh_m2"] == res_base["H_ef_kWh_m2"]


def test_factor_espectral_se_ignora_en_panel_no_cdte():
    # Copia de ASP_ST1_T40 pero declarado Crystalline -- el factor 'cdte' NO
    # debe aplicarse a otra tecnología aunque el caller lo pase por error.
    # "Mono-Si" (no "Mono PERC" genérico) porque el SDM completo exige uno
    # de los 4 valores exactos de CONSTANTES_TECNOLOGIA -- este panel ya
    # tiene ficha SDM completa (hereda de ASP_ST1_T40), así que entra por
    # el camino SDM real, no el fallback lineal.
    panel_crystalline = dict(ASP_ST1_T40)
    panel_crystalline["tecnologia"] = "Mono-Si"

    tmy = _tmy_sintetico()
    poa_df = pd.DataFrame({"poa_global": tmy["G_h"] * 1.1}, index=tmy.index)
    factor_reductor = pd.Series(0.5, index=tmy.index)   # deliberadamente extremo

    res_sin = simular_produccion_anual(
        tmy=tmy, poa_base=poa_df, panel=panel_crystalline, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
    )
    res_con = simular_produccion_anual(
        tmy=tmy, poa_base=poa_df, panel=panel_crystalline, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0, factor_espectral=factor_reductor,
    )
    assert res_con["factor_espectral_aplicado"] is False
    assert res_con["factor_espectral_promedio"] is None
    assert res_con["E_dc_anual_kWh"] == res_sin["E_dc_anual_kWh"]


def test_factor_con_forma_distinta_se_ignora_sin_reventar():
    tmy = _tmy_sintetico()
    poa_df = pd.DataFrame({"poa_global": tmy["G_h"] * 1.1}, index=tmy.index)
    factor_mal_alineado = np.array([0.9, 0.9, 0.9])   # longitud incorrecta a propósito

    res = simular_produccion_anual(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0, factor_espectral=factor_mal_alineado,
    )
    assert res["factor_espectral_aplicado"] is False


def test_df_horario_incluye_columna_factor_espectral():
    tmy = _tmy_sintetico()
    poa_df = pd.DataFrame({"poa_global": tmy["G_h"] * 1.1}, index=tmy.index)
    factor = pd.Series(0.95, index=tmy.index)

    res = simular_produccion_anual(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0, factor_espectral=factor,
    )
    assert "factor_espectral" in res["df_horario"].columns
    horas_con_sol = res["df_horario"]["G_eff_Wm2"] > 5.0
    assert res["df_horario"].loc[horas_con_sol, "factor_espectral"].round(4).eq(0.95).all()


# ---------------------------------------------------------------------------
# simular_produccion_iv() (Motor IV) -- mismo fix, mismo motivo: este módulo
# usa el SDM completo para CdTe (no JRC/Huld como produccion.py) y habría
# divergido del motor base en paneles CdTe si se dejaba sin corregir.
# ---------------------------------------------------------------------------


def test_motor_iv_sin_factor_espectral_es_retrocompatible_exacto():
    tmy = _tmy_sintetico()
    poa_df = pd.DataFrame({"poa_global": tmy["G_h"] * 1.1}, index=tmy.index)
    res_sin_param = simular_produccion_iv(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
    )
    res_con_none = simular_produccion_iv(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0, factor_espectral=None,
    )
    assert res_sin_param["factor_espectral_aplicado"] is False
    assert res_sin_param["E_dc_anual_kWh"] == res_con_none["E_dc_anual_kWh"]


def test_motor_iv_factor_menor_a_1_reduce_e_dc_en_panel_cdte():
    tmy = _tmy_sintetico()
    poa_df = pd.DataFrame({"poa_global": tmy["G_h"] * 1.1}, index=tmy.index)
    factor_reductor = pd.Series(0.9, index=tmy.index)

    res_base = simular_produccion_iv(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0,
    )
    res_corregido = simular_produccion_iv(
        tmy=tmy, poa_base=poa_df, panel=ASP_ST1_T40, N_paneles=10,
        eta_inversor=0.975, factor_pr_mismatch=1.0, factor_espectral=factor_reductor,
    )
    assert res_corregido["factor_espectral_aplicado"] is True
    assert res_corregido["factor_espectral_promedio"] == pytest.approx(0.9, abs=1e-6)
    assert res_corregido["E_dc_anual_kWh"] < res_base["E_dc_anual_kWh"]
    assert res_corregido["H_ef_kWh_m2"] == res_base["H_ef_kWh_m2"]
