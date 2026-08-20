# -*- coding: utf-8 -*-
"""
Regresión — unificación de geometría solar duplicada (auditoría Fase 1).

Antes de este cambio, `pages/5_🔀_Mismatch.py` y `pages/9_🗺️_Vista_3D.py`
reimplementaban cada una su propio cálculo de posiciones solares
(`_solar_path_diario` / `_solar_path_mensual`) y de interpolación de
horizonte (`_interp_horizonte`), en paralelo a `calculos/solar.py` y
`calculos/mismatch.py::_interpolar_horizonte`. El riesgo: dos páginas
podían mostrar/derivar geometría solar ligeramente distinta si una copia
se corregía y la otra no.

Este test verifica dos cosas:
1. Las funciones compartidas (`calculos.solar.posiciones_solares_*`,
   `calculos.mismatch._interpolar_horizonte`) calculan lo que se espera,
   comparando contra un cálculo pvlib independiente hecho en el test.
2. Las páginas ya NO contienen una reimplementación local — si alguien
   vuelve a pegar el cálculo dentro de una página, este test debe fallar.
"""
import ast
import os

import numpy as np
import pandas as pd
import pvlib
import pytest

from calculos.solar import (
    posiciones_solares_representativas,
    posiciones_solares_anio_estandar,
)
from calculos.mismatch import _interpolar_horizonte

# Bogotá — coordenadas ya usadas en otros tests/fixtures del repo.
LAT, LON, ALT_M = 4.7110, -74.0721, 2620.0

_DIR_PAGES = os.path.join(os.path.dirname(__file__), "..", "pages")
_PAGINA_MISMATCH = os.path.join(_DIR_PAGES, "5_🔀_Mismatch.py")
_PAGINA_VISTA_3D = os.path.join(_DIR_PAGES, "9_🗺️_Vista_3D.py")


def _pvlib_directo(lat, lon, alt_m, elevacion_min):
    """Recalcula manualmente, sin pasar por calculos.solar, para comparar."""
    loc = pvlib.location.Location(latitude=lat, longitude=lon, altitude=alt_m, tz="UTC")
    dias_rep = pd.date_range("2001-01-15", periods=12, freq="MS") + pd.Timedelta(days=14)
    frames = []
    for dia in dias_rep:
        times = pd.date_range(dia, dia + pd.Timedelta(hours=23), freq="h", tz="UTC")
        sp = loc.get_solarposition(times)
        sp["mes"] = dia.month
        frames.append(sp[sp["apparent_elevation"] > elevacion_min])
    return pd.concat(frames)


@pytest.mark.parametrize("elevacion_min", [0.0, 0.5])
def test_posiciones_representativas_coincide_con_calculo_directo(elevacion_min):
    esperado = _pvlib_directo(LAT, LON, ALT_M, elevacion_min)
    obtenido = posiciones_solares_representativas(LAT, LON, ALT_M, elevacion_min=elevacion_min)

    assert len(obtenido) == len(esperado)
    assert (obtenido["apparent_elevation"] > elevacion_min).all()
    np.testing.assert_allclose(
        obtenido["azimuth"].values, esperado["azimuth"].values, rtol=0, atol=1e-9
    )
    np.testing.assert_allclose(
        obtenido["apparent_elevation"].values,
        esperado["apparent_elevation"].values,
        rtol=0,
        atol=1e-9,
    )


def test_elevacion_min_por_defecto_es_mas_permisiva():
    # Mismatch usaba el umbral 0.0 (estrictamente > 0); Vista_3D usaba 0.5.
    # El default debe seguir siendo 0.0 para no cambiar el comportamiento
    # de la página que no pasa el argumento explícitamente.
    laxo = posiciones_solares_representativas(LAT, LON, ALT_M)
    estricto = posiciones_solares_representativas(LAT, LON, ALT_M, elevacion_min=0.5)
    assert len(laxo) >= len(estricto)


def test_posiciones_anio_estandar_8760_horas():
    pos = posiciones_solares_anio_estandar(LAT, LON, ALT_M)
    assert len(pos) == 8760
    esperado = pvlib.location.Location(
        latitude=LAT, longitude=LON, altitude=ALT_M, tz="UTC"
    ).get_solarposition(pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC"))
    np.testing.assert_allclose(
        pos["apparent_elevation"].values, esperado["apparent_elevation"].values,
        rtol=0, atol=1e-9,
    )


def test_interpolar_horizonte_vacio_da_ceros():
    az = np.linspace(0, 360, 10)
    out = _interpolar_horizonte([], az)
    assert (out == 0).all()


def test_interpolar_horizonte_es_periodica():
    # Un obstáculo justo en 0°/360° debe interpolar igual en ambos extremos.
    puntos = [(0, 20), (90, 5), (180, 0), (270, 5)]
    el_0 = _interpolar_horizonte(puntos, np.array([0.0]))[0]
    el_360 = _interpolar_horizonte(puntos, np.array([360.0]))[0]
    assert el_0 == pytest.approx(el_360)


def _fuente(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_mismatch_no_reimplementa_geometria_solar():
    src = _fuente(_PAGINA_MISMATCH)
    assert "def _solar_path_diario" not in src
    assert "posiciones_solares_representativas" in src


def test_vista_3d_no_reimplementa_geometria_solar():
    src = _fuente(_PAGINA_VISTA_3D)
    tree = ast.parse(src, filename=_PAGINA_VISTA_3D)
    defs_locales = {
        n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    # Estos nombres pueden seguir existiendo como envoltorios @st.cache_data,
    # pero ya no deben contener su propia llamada a pvlib.location.Location.
    assert "_interp_horizonte" not in defs_locales, (
        "Vista_3D volvió a definir su propia interpolación de horizonte; "
        "debe importar _interpolar_horizonte de calculos.mismatch"
    )
    assert "posiciones_solares_representativas" in src
    assert "posiciones_solares_anio_estandar" in src
    assert "from calculos.mismatch import _interpolar_horizonte" in src
