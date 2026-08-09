# -*- coding: utf-8 -*-
"""#232: combinación FS 3D + horizonte — máximo hora a hora, sin doble conteo."""
import numpy as np
import pandas as pd
import pytest

from calculos.mismatch_bypass import combinar_fs_con_horizonte


def _series(n=24):
    idx = pd.date_range("2023-01-01", periods=n, freq="h", tz="UTC")
    return idx


def test_maximo_no_suma():
    idx = _series()
    fs3d = pd.Series(0.4, index=idx)
    mask = pd.Series([True] * 6 + [False] * 18, index=idx)
    comb, info = combinar_fs_con_horizonte(fs3d, mask)
    # horas con horizonte: sombra total (1.0), no 1.4
    assert (comb.iloc[:6] == 1.0).all()
    assert (comb.iloc[6:] == 0.4).all()
    assert info["horas_horizonte"] == 6
    assert info["horas_solo_horizonte"] == 6


def test_horizonte_dominante_vs_obstaculo_dominante():
    idx = _series()
    fs3d = pd.Series([1.0] * 12 + [0.0] * 12, index=idx)
    mask = pd.Series([False] * 6 + [True] * 12 + [False] * 6, index=idx)
    comb, info = combinar_fs_con_horizonte(fs3d, mask)
    assert (comb.iloc[:12] == 1.0).all()      # obstáculo domina la mañana
    assert (comb.iloc[12:18] == 1.0).all()    # horizonte domina la tarde
    assert (comb.iloc[18:] == 0.0).all()
    # solo-horizonte: horas donde FS 3D < 1 y horizonte = 1 → 12:00-18:00
    assert info["horas_solo_horizonte"] == 6


def test_sin_horizonte_no_cambia_nada():
    idx = _series()
    fs3d = pd.Series(np.linspace(0, 1, 24), index=idx)
    mask = pd.Series(False, index=idx)
    comb, info = combinar_fs_con_horizonte(fs3d, mask)
    assert (comb.values == fs3d.values).all()
    assert info["horas_horizonte"] == 0


def test_rechaza_calendarios_distintos():
    fs3d = pd.Series(0.5, index=_series(24))
    mask = pd.Series(True, index=_series(23))
    with pytest.raises(ValueError, match="recalcula"):
        combinar_fs_con_horizonte(fs3d, mask)
    mask2 = pd.Series(True, index=pd.date_range("2024-06-01", periods=24, freq="h", tz="UTC"))
    with pytest.raises(ValueError, match="no coinciden"):
        combinar_fs_con_horizonte(fs3d, mask2)


def test_resultado_en_rango():
    idx = _series()
    fs3d = pd.Series(np.random.RandomState(0).rand(24), index=idx)
    mask = pd.Series(np.random.RandomState(1).rand(24) > 0.5, index=idx)
    comb, _ = combinar_fs_con_horizonte(fs3d, mask)
    assert comb.between(0, 1).all()
    assert (comb.values >= fs3d.values).all()  # nunca reduce la sombra
