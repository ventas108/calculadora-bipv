"""Distinción explícita de los 5 estados de sombra por superficie (recreado,
ronda de recuperación 2026-09-21). Ninguna de estas pruebas cambia el
contrato numérico de p_shade (sigue siendo 0.0 por defecto en horas sin fila
de ray-casting); verifican que esa situación queda SIEMPRE visible en
``estado_sombra``/``cobertura``/``advertencias``, nunca en silencio.
"""
import numpy as np
import pandas as pd
import pytest

trimesh = pytest.importorskip("trimesh")

import calculos.sombras_3d as sombras_3d
from calculos.sombras_3d import calcular_fs_horario_por_superficie


def _idx():
    return pd.date_range("2023-01-01", periods=8760, freq="h", tz="UTC")


def _tmy(idx=None):
    idx = _idx() if idx is None else idx
    horas = idx.hour.to_numpy()
    t2m = 20.0 + 5.0 * np.sin((horas - 6) / 24.0 * 2 * np.pi)
    return pd.DataFrame({"T2m": t2m}, index=idx)


def _geometria_y_puntos():
    puntos = {"Sur": [{"nombre": "S1", "fachada": "Sur", "x": 0.0, "y": -5.0, "z": 2.0}]}
    geometria = {"Sur": {"tilt_deg": 90.0, "azimuth_deg": 180.0}}
    return puntos, geometria


def _fake_sol(idx, horas_con_sol_idx, elevacion=50.0):
    elevacion_arr = np.full(len(idx), -10.0)
    elevacion_arr[horas_con_sol_idx] = elevacion
    return pd.DataFrame({"elevacion": elevacion_arr, "acimut": np.zeros(len(idx))}, index=idx)


def test_calculo_incompleto_si_faltan_horas_con_sol(monkeypatch):
    idx = _idx()
    tmy = _tmy(idx)
    puntos, geometria = _geometria_y_puntos()
    malla = trimesh.creation.box(extents=[4.0, 4.0, 8.0])
    monkeypatch.setattr(sombras_3d, "posiciones_solares", lambda lat, lon, indice_tmy: _fake_sol(idx, [0, 1, 2, 3, 4]))
    monkeypatch.setattr(
        sombras_3d, "calcular_fs_horario",
        lambda malla, puntos, lat, lon, indice_tmy, transparencia: pd.DataFrame({
            "timestamp_utc": [idx[i].isoformat().replace("+00:00", "Z") for i in (0, 1, 2)],
            "FS_geometrico": [0.3, 0.3, 0.3],
        }),
    )
    resultado = calcular_fs_horario_por_superficie(
        malla, puntos, 4.65, -74.08, tmy, geometria, malla_horizonte="box-test-v1",
    )
    datos = resultado["Sur"]
    assert datos["estado_sombra"] == sombras_3d.ESTADO_CALCULO_INCOMPLETO
    assert datos["estado_sombra"] not in sombras_3d.ESTADOS_SOMBRA_ACEPTABLES
    assert datos["cobertura"]["horas_con_sol_no_calculadas"] == 2
    assert any("no fueron calculadas" in a.lower() for a in datos["advertencias"])
    # Horas no calculadas siguen en 0.0 numéricamente -- el consumidor NUNCA
    # debe leer p_shade sin comprobar estado_sombra antes.
    assert datos["p_shade"][3] == 0.0 and datos["p_shade"][4] == 0.0


def test_calculado_completo_cuando_no_hay_huecos(monkeypatch):
    idx = _idx()
    tmy = _tmy(idx)
    puntos, geometria = _geometria_y_puntos()
    malla = trimesh.creation.box(extents=[4.0, 4.0, 8.0])
    monkeypatch.setattr(sombras_3d, "posiciones_solares", lambda lat, lon, indice_tmy: _fake_sol(idx, [0, 1]))
    monkeypatch.setattr(
        sombras_3d, "calcular_fs_horario",
        lambda malla, puntos, lat, lon, indice_tmy, transparencia: pd.DataFrame({
            "timestamp_utc": [idx[i].isoformat().replace("+00:00", "Z") for i in (0, 1)],
            "FS_geometrico": [0.4, 0.4],
        }),
    )
    resultado = calcular_fs_horario_por_superficie(
        malla, puntos, 4.65, -74.08, tmy, geometria, malla_horizonte="box-test-v1",
    )
    datos = resultado["Sur"]
    assert datos["estado_sombra"] == sombras_3d.ESTADO_CALCULADO_COMPLETO
    assert datos["estado_sombra"] in sombras_3d.ESTADOS_SOMBRA_ACEPTABLES
    assert datos["cobertura"]["horas_con_sol_no_calculadas"] == 0


def test_sombra_cero_calculada_cuando_todo_da_cero(monkeypatch):
    idx = _idx()
    tmy = _tmy(idx)
    puntos, geometria = _geometria_y_puntos()
    malla = trimesh.creation.box(extents=[4.0, 4.0, 8.0])
    monkeypatch.setattr(sombras_3d, "posiciones_solares", lambda lat, lon, indice_tmy: _fake_sol(idx, [0, 1]))
    monkeypatch.setattr(
        sombras_3d, "calcular_fs_horario",
        lambda malla, puntos, lat, lon, indice_tmy, transparencia: pd.DataFrame({
            "timestamp_utc": [idx[i].isoformat().replace("+00:00", "Z") for i in (0, 1)],
            "FS_geometrico": [0.0, 0.0],
        }),
    )
    resultado = calcular_fs_horario_por_superficie(
        malla, puntos, 4.65, -74.08, tmy, geometria, malla_horizonte="box-test-v1",
    )
    datos = resultado["Sur"]
    assert datos["estado_sombra"] == sombras_3d.ESTADO_SOMBRA_CERO_CALCULADA
    assert datos["estado_sombra"] in sombras_3d.ESTADOS_SOMBRA_ACEPTABLES


def test_resolucion_insuficiente_si_menos_puntos_que_n_serie(monkeypatch):
    idx = _idx()
    tmy = _tmy(idx)
    puntos, geometria = _geometria_y_puntos()  # 1 solo punto
    malla = trimesh.creation.box(extents=[4.0, 4.0, 8.0])
    monkeypatch.setattr(sombras_3d, "posiciones_solares", lambda lat, lon, indice_tmy: _fake_sol(idx, [0]))
    monkeypatch.setattr(
        sombras_3d, "calcular_fs_horario",
        lambda malla, puntos, lat, lon, indice_tmy, transparencia: pd.DataFrame({
            "timestamp_utc": [idx[0].isoformat().replace("+00:00", "Z")],
            "FS_geometrico": [0.5],
        }),
    )
    resultado = calcular_fs_horario_por_superficie(
        malla, puntos, 4.65, -74.08, tmy, geometria, malla_horizonte="box-test-v1",
        n_modulos_serie_por_superficie={"Sur": 7},
    )
    datos = resultado["Sur"]
    assert datos["estado_sombra"] == sombras_3d.ESTADO_RESOLUCION_INSUFICIENTE
    assert datos["estado_sombra"] not in sombras_3d.ESTADOS_SOMBRA_ACEPTABLES
    # El motor NUNCA bloquea por sí mismo -- sigue devolviendo p_shade usable;
    # el bloqueo real es responsabilidad del vinculador/adaptador.
    assert datos["p_shade"].shape == (8760,)


def test_error_geometrico_si_punto_dentro_del_obstaculo():
    idx = _idx()
    tmy = _tmy(idx)
    malla = trimesh.creation.box(extents=[4.0, 4.0, 8.0])
    assert malla.is_watertight
    puntos = {"Sur": [{"nombre": "S1", "fachada": "Sur", "x": 0.0, "y": 0.0, "z": 0.0}]}
    geometria = {"Sur": {"tilt_deg": 90.0, "azimuth_deg": 180.0}}
    resultado = calcular_fs_horario_por_superficie(
        malla, puntos, 4.65, -74.08, tmy, geometria, malla_horizonte="box-test-v1",
    )
    datos = resultado["Sur"]
    assert datos["estado_sombra"] == sombras_3d.ESTADO_ERROR_GEOMETRICO
    assert datos["estado_sombra"] not in sombras_3d.ESTADOS_SOMBRA_ACEPTABLES
