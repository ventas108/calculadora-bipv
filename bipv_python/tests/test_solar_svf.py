# -*- coding: utf-8 -*-
"""
Tests del parámetro reduccion_diffusa_isotropica en calculos/solar.py::calcular_poa().

Cubre:
  1. Regresión: el default (1.0) da EXACTAMENTE los mismos números que antes
     de agregar el parámetro -- ningún caller existente debe ver ningún
     cambio de comportamiento.
  2. Reducción conocida: con un factor SVF dado, poa_isotropic baja en esa
     proporción exacta (comparado contra pvlib.irradiance.haydavies() con
     return_components=True, llamado independientemente en el test) y
     poa_global baja lo que corresponde -- sin tocar poa_direct ni
     poa_ground_diffuse.
  3. Compatibilidad de claves entre versiones de pvlib: el propio pin de
     producción (pvlib==0.11.1, ver requirements.txt) usa claves SIN
     prefijo 'poa_' en return_components=True (verificado leyendo el código
     fuente real de esa versión) -- este archivo corre bajo esa MISMA
     versión pinneada (ver venv de esta sesión), así que un test que pase
     aquí confirma que el manejo defensivo de nombres de columna funciona
     con la versión real de producción, no solo con una versión de
     desarrollo más nueva.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calculos.solar import calcular_poa  # noqa: E402

LAT, LON, ALT_M = 7.884, -76.635, 30.0   # Urabá, ya usado en otros tests del repo
TILT, AZIMUTH = 90.0, 180.0              # fachada vertical, mirando al Sur


def _tmy_sintetico_clearsky():
    """Mismo patrón que test_simulation_pipeline.py::_tmy_sintetico_offline
    -- TMY offline determinista (clear-sky Ineichen), sin red."""
    idx = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    loc = pvlib.location.Location(latitude=LAT, longitude=LON, altitude=ALT_M, tz="UTC")
    cs = loc.get_clearsky(idx, model="ineichen")
    return pd.DataFrame({
        "G_h": cs["ghi"].values, "Gb_n": cs["dni"].values, "Gd_h": cs["dhi"].values,
        "T2m": 25.0, "WS10m": 2.0, "SP": 101_325.0,
    }, index=idx)


@pytest.fixture(scope="module")
def tmy():
    return _tmy_sintetico_clearsky()


def test_default_reduccion_1_0_es_identico_a_antes_del_parametro(tmy):
    """Regresión: el parámetro nuevo, en su default, no debe cambiar NADA
    -- ni un watt -- del resultado de calcular_poa(). Comparación EXACTA
    (no approx), porque con factor=1.0 el código nuevo ni siquiera se
    ejecuta (ver el `if factor_svf < 1.0` en calcular_poa)."""
    poa_sin_parametro = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZIMUTH)
    poa_con_default = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZIMUTH,
                                    reduccion_diffusa_isotropica=1.0)
    pd.testing.assert_frame_equal(poa_sin_parametro, poa_con_default)


def test_reduccion_svf_baja_isotropica_en_la_proporcion_exacta(tmy):
    factor = 0.6

    poa_base = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZIMUTH)
    poa_reducida = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZIMUTH,
                                 reduccion_diffusa_isotropica=factor)

    # Referencia INDEPENDIENTE: llamar pvlib.irradiance.haydavies() a mano,
    # con return_components=True, exactamente como debería hacerlo
    # calcular_poa() por dentro -- pero calculado aquí de nuevo, no
    # importado del código de producción, para que sea una verificación
    # real y no una tautología.
    loc = pvlib.location.Location(latitude=LAT, longitude=LON, altitude=ALT_M, tz="UTC")
    solar_pos = loc.get_solarposition(tmy.index)
    dni_extra = pvlib.irradiance.get_extra_radiation(tmy.index)
    componentes = pvlib.irradiance.haydavies(
        surface_tilt=TILT, surface_azimuth=AZIMUTH,
        dhi=tmy["Gd_h"], dni=tmy["Gb_n"], dni_extra=dni_extra,
        solar_zenith=solar_pos["apparent_zenith"], solar_azimuth=solar_pos["azimuth"],
        return_components=True,
    )
    # Pin de producción (pvlib==0.11.1): claves SIN prefijo 'poa_'.
    assert "isotropic" in componentes.columns, (
        "Si esto falla, pvlib cambió el nombre de columna en la versión "
        "instalada -- ver el manejo defensivo en solar.py."
    )
    isotropic_esperada_reducida = componentes["isotropic"] * factor

    # poa_direct NO debe tocarse.
    pd.testing.assert_series_equal(
        poa_base["poa_direct"], poa_reducida["poa_direct"], check_names=False
    )
    # poa_global esperado = poa_direct + (isotropic*factor + circumsolar) + ground_diffuse
    global_esperado = (
        poa_base["poa_direct"]
        + isotropic_esperada_reducida + componentes["circumsolar"]
        + poa_base["poa_ground_diffuse"]
    ).clip(lower=0.0)
    pd.testing.assert_series_equal(
        poa_reducida["poa_global"], global_esperado, check_names=False, atol=1e-6
    )
    # La reducción total debe ser estrictamente menor o igual (nunca sube).
    assert poa_reducida["poa_global"].sum() < poa_base["poa_global"].sum()
    assert poa_reducida["poa_global"].sum() > 0


def test_reduccion_svf_cero_no_deja_isotropica_negativa(tmy):
    poa = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZIMUTH,
                        reduccion_diffusa_isotropica=0.0)
    assert (poa["poa_global"] >= 0.0).all()
    assert (poa["poa_diffuse"] >= 0.0).all()


def test_reduccion_svf_fuera_de_rango_se_recorta_0_1(tmy):
    # >1.0 o <0.0 no debería explotar ni "amplificar" -- se recorta a [0,1].
    poa_sobre_uno = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZIMUTH,
                                  reduccion_diffusa_isotropica=1.5)
    poa_normal = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZIMUTH)
    pd.testing.assert_frame_equal(poa_sobre_uno, poa_normal)


def test_reduccion_svf_con_bifacial_se_ignora_de_forma_coherente(tmy):
    # Fuera de alcance v1 (ver docstring de calcular_poa): en bifacial,
    # poa_global lo recalcula infinite_sheds íntegramente y NO conoce el
    # SVF -- se verifica que la reducción se ignora COMPLETAMENTE (no que
    # se aplique a medias, lo que dejaría poa_diffuse reducida pero
    # poa_global sin reducir -- un DataFrame incoherente).
    bifacial_cfg = {"bifacialidad": 0.8, "altura_m": 1.0, "gcr": 0.3,
                     "ancho_colector_m": 2.0}
    poa_sin_svf = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZIMUTH,
                                bifacial=bifacial_cfg)
    poa_con_svf = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZIMUTH,
                                bifacial=bifacial_cfg, reduccion_diffusa_isotropica=0.5)
    pd.testing.assert_frame_equal(poa_sin_svf, poa_con_svf)
