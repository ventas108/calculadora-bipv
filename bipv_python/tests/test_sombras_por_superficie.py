"""Contrato de sombreado horario separado por superficie (recreado, ronda de
recuperación 2026-09-21, tras el borrado accidental de este archivo -- ver
references/recuperacion-multisuperficie-2026-09-21.md).

Verifica contra la API ACTUAL de calcular_fs_horario_por_superficie:
``(malla, puntos_por_superficie, lat, lon, tmy, geometria_por_superficie,
malla_horizonte, transparencia=0.0, n_modulos_serie_por_superficie=None)``
-- exige ``tmy`` como DataFrame con T2m real (no un DatetimeIndex suelto).
"""
import numpy as np
import pandas as pd
import pytest

trimesh = pytest.importorskip("trimesh")

import calculos.sombras_3d as sombras_3d
from calculos.produccion_vigencia import huella_horaria
from calculos.sombras_3d import calcular_fs_horario_por_superficie

_HORAS_ANIO = 8760


def _tmy_real(t2m_base: float = 20.0, periods: int = _HORAS_ANIO, tz: str = "UTC") -> pd.DataFrame:
    idx = pd.date_range("2023-01-01", periods=periods, freq="h", tz=tz)
    horas = idx.hour.to_numpy()
    t2m = t2m_base + 5.0 * np.sin((horas - 6) / 24.0 * 2 * np.pi)
    return pd.DataFrame({"T2m": t2m}, index=idx)


def _fake_calcular_fs_horario(malla, puntos, lat, lon, indice_tmy, transparencia):
    return pd.DataFrame({
        "timestamp_utc": [indice_tmy[10].tz_convert("UTC").isoformat().replace("+00:00", "Z")],
        "FS_geometrico": [0.5],
    })


def test_calcula_p_shade_y_firma_por_superficie(monkeypatch):
    tmy = _tmy_real()
    malla = trimesh.creation.box(extents=[4.0, 4.0, 8.0])
    puntos = {
        "Este": [{"nombre": "E1", "fachada": "Este", "x": -5.0, "y": 0.0, "z": 2.0}],
        "Oeste": [{"nombre": "O1", "fachada": "Oeste", "x": 5.0, "y": 0.0, "z": 2.0}],
    }
    geometria = {
        "Este": {"tilt_deg": 90.0, "azimuth_deg": 90.0},
        "Oeste": {"tilt_deg": 90.0, "azimuth_deg": 270.0},
    }
    monkeypatch.setattr(sombras_3d, "calcular_fs_horario", _fake_calcular_fs_horario)

    resultado = calcular_fs_horario_por_superficie(
        malla, puntos, 4.65, -74.08, tmy, geometria, malla_horizonte="box-test-v1",
    )

    assert set(resultado) == {"Este", "Oeste"}
    for nombre, datos in resultado.items():
        assert datos["p_shade"].shape == (8760,)
        assert np.isfinite(datos["p_shade"]).all()
        assert np.all((datos["p_shade"] >= 0) & (datos["p_shade"] <= 1))
        assert {"geometria", "puntos_analisis", "malla_horizonte", "tmy_fingerprint", "fuente"}.issubset(
            datos["firma_sombra"]
        )
        assert datos["firma_sombra"]["geometria"] == geometria[nombre]
        # El mock solo cubre 1 hora de las ~4000+ horas con sol reales en
        # este sitio -- estado "calculo_incompleto" es el resultado físico
        # correcto aquí, no un fallo (ver test_cobertura_sombra_por_superficie.py
        # para los 5 estados verificados uno por uno con cobertura controlada).
        assert datos["estado_sombra"] in (
            "calculado_completo", "sombra_cero_calculada", "calculo_incompleto",
        )
        assert datos["cobertura"]["horas_totales"] == 8760
        assert isinstance(datos["advertencias"], list)
    assert resultado["Este"]["firma_sombra"] != resultado["Oeste"]["firma_sombra"]


def test_tmy_debe_ser_dataframe_con_t2m_no_indice_suelto():
    idx_suelto = pd.date_range("2023-01-01", periods=_HORAS_ANIO, freq="h", tz="UTC")
    malla = trimesh.creation.box(extents=[4.0, 4.0, 8.0])
    puntos = {"A": [{"nombre": "P1", "fachada": "A", "x": 0.0, "y": -5.0, "z": 2.0}]}
    geometria = {"A": {"tilt_deg": 90.0, "azimuth_deg": 180.0}}
    with pytest.raises(ValueError, match="T2m"):
        calcular_fs_horario_por_superficie(
            malla, puntos, 4.65, -74.08, idx_suelto, geometria, malla_horizonte="box-test-v1",
        )


def test_cambiar_t2m_cambia_la_firma_tmy(monkeypatch):
    tmy_a, tmy_b = _tmy_real(t2m_base=20.0), _tmy_real(t2m_base=25.0)
    malla = trimesh.creation.box(extents=[4.0, 4.0, 8.0])
    puntos = {"A": [{"nombre": "P1", "fachada": "A", "x": 0.0, "y": -5.0, "z": 2.0}]}
    geometria = {"A": {"tilt_deg": 90.0, "azimuth_deg": 180.0}}
    monkeypatch.setattr(sombras_3d, "calcular_fs_horario", _fake_calcular_fs_horario)

    fp_a = calcular_fs_horario_por_superficie(
        malla, puntos, 4.65, -74.08, tmy_a, geometria, malla_horizonte="box-test-v1",
    )["A"]["firma_sombra"]["tmy_fingerprint"]
    fp_b = calcular_fs_horario_por_superficie(
        malla, puntos, 4.65, -74.08, tmy_b, geometria, malla_horizonte="box-test-v1",
    )["A"]["firma_sombra"]["tmy_fingerprint"]
    assert fp_a != fp_b


def test_nunca_se_usa_vector_de_ceros_para_simular_el_tmy(monkeypatch):
    tmy = _tmy_real()
    malla = trimesh.creation.box(extents=[4.0, 4.0, 8.0])
    puntos = {"A": [{"nombre": "P1", "fachada": "A", "x": 0.0, "y": -5.0, "z": 2.0}]}
    geometria = {"A": {"tilt_deg": 90.0, "azimuth_deg": 180.0}}
    monkeypatch.setattr(sombras_3d, "calcular_fs_horario", _fake_calcular_fs_horario)

    fp_real = calcular_fs_horario_por_superficie(
        malla, puntos, 4.65, -74.08, tmy, geometria, malla_horizonte="box-test-v1",
    )["A"]["firma_sombra"]["tmy_fingerprint"]
    fp_ceros = huella_horaria(tmy.index, np.zeros(len(tmy.index), dtype=float))
    assert fp_real != fp_ceros


def test_superficie_sin_puntos_bloquea():
    tmy = _tmy_real()
    malla = trimesh.creation.box(extents=[4.0, 4.0, 8.0])
    puntos = {"A": []}
    geometria = {"A": {"tilt_deg": 90.0, "azimuth_deg": 180.0}}
    with pytest.raises(ValueError, match="A.*puntos"):
        calcular_fs_horario_por_superficie(
            malla, puntos, 4.65, -74.08, tmy, geometria, malla_horizonte="box-test-v1",
        )
