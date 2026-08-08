"""Regresión determinista del contrato del motor oficial de sombreado."""
import json
import io
import os
import sys

import numpy as np
import pandas as pd
import pytest
import trimesh

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos.contrato_sombreado import (  # noqa: E402
    CONTRACT_VERSION,
    resultado_a_contrato,
    validar_resultado,
    validar_solicitud,
)
from calculos.mismatch_bypass import cargar_csv_fs, simular_bypass_horario  # noqa: E402
from calculos.sombras_3d import posiciones_solares  # noqa: E402
from calculos.sombras_3d import calcular_fs_horario, vector_al_sol  # noqa: E402
from datos.tecnologias_bipv import ASP_ST1_T40  # noqa: E402


ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _fixture():
    with open(
        os.path.join(ROOT, "docs", "fixtures", "sombreado-referencia.json"),
        encoding="utf-8",
    ) as fh:
        return json.load(fh)


def test_pvlib_reproduce_la_referencia_solar():
    fixture = _fixture()
    timestamps = pd.DatetimeIndex(
        [case["timestamp_utc"] for case in fixture["solar_position_cases"]]
    )
    solar = posiciones_solares(
        fixture["location"]["latitude"],
        fixture["location"]["longitude"],
        timestamps,
    )

    for index, case in enumerate(fixture["solar_position_cases"]):
        assert abs(
            solar.iloc[index]["elevacion"] - case["expected_altitude_deg"]
        ) < case["tolerance_deg"]
        assert abs(
            solar.iloc[index]["acimut"] - case["expected_azimuth_deg"]
        ) < case["tolerance_deg"]


def test_solicitud_requiere_timestamps_utc_y_puntos_unicos():
    base = {
        "contract_version": CONTRACT_VERSION,
        "location": {
            "latitude": 6.25,
            "longitude": -75.56,
            "timezone": -5,
            "elevation_m": 1495,
        },
        "timestamps_utc": ["2024-03-20T17:00:00Z"],
        "points": [{
            "id": "P1",
            "facade": "Sur",
            "x_m": 0,
            "y_m": 0,
            "z_m": 2,
        }],
    }
    validar_solicitud(base)
    with pytest.raises(ValueError, match="zona horaria"):
        validar_solicitud({**base, "timestamps_utc": ["2024-03-20T12:00:00"]})
    with pytest.raises(ValueError, match="repetido"):
        validar_solicitud({
            **base,
            "points": [base["points"][0], base["points"][0]],
        })


def test_resultado_solo_expone_fs_geometrico_como_fs_oficial():
    frame = pd.DataFrame([{
        "timestamp_utc": "2024-03-20T17:00:00Z",
        "Mes": 3,
        "Dia": 20,
        "Hora": 17,
        "Altura Solar (deg)": 83.53,
        "Acimut Solar (deg)": 158.45,
        "FS_geometrico": 1.0,
        "Fachada": "Sur",
        "Punto": "P1",
    }])
    payload = resultado_a_contrato(frame)
    validar_resultado(payload)
    assert payload["contract_version"] == CONTRACT_VERSION
    assert payload["engine"] == "python"
    assert payload["results"][0]["fs"] == 1.0
    assert payload["results"][0]["fs_climatico"] is None
    assert payload["results"][0]["fs_combinado"] is None

    invalid = {
        **payload,
        "results": [{**payload["results"][0], "fs_climatico": 0.5}],
    }
    with pytest.raises(ValueError, match="no permite"):
        validar_resultado(invalid)


def test_mismatch_rechaza_fs_combinado_o_climatico_sin_fs_geometrico():
    csv = (
        "Mes,Dia,Hora,FS_climatico,FS\n"
        "3,20,17,0.8,0.8\n"
    )
    with pytest.raises(ValueError, match="FS_geometrico"):
        cargar_csv_fs(io.StringIO(csv))


def test_parser_y_alineacion_ignoran_fs_combinado_cuando_hay_nubosidad():
    """La nube alta nunca se convierte en p_shade para bypass."""
    csv = (
        "Mes,Dia,Hora,FS_geometrico,FS_climatico,FS\n"
        "3,20,17,0.0,0.9,0.9\n"
        "3,20,18,0.4,0.8,0.8\n"
    )
    df, meta = cargar_csv_fs(io.StringIO(csv))

    assert meta["tipo"] == "geometrico"
    assert df["FS_geometrico"].tolist() == [0.0, 0.4]
    # Alias legacy también debe ser físico, no el FS combinado del archivo.
    assert df["FS"].tolist() == [0.0, 0.4]

    tmy_index = pd.date_range("2024-03-20 17:00", periods=2, freq="h")
    p_shade = __import__("calculos.mismatch_bypass", fromlist=["alinear_fs_con_tmy"]).alinear_fs_con_tmy(
        df, tmy_index, modo="exacto"
    )
    np.testing.assert_allclose(p_shade.values, [0.0, 0.4])


def test_alineacion_bypass_pondera_por_modulos():
    """La serie que entra al bypass respeta el tamaño de cada punto."""
    from calculos.mismatch_bypass import alinear_fs_con_tmy

    df = pd.DataFrame(
        {
            "mes": [3, 3],
            "dia": [20, 20],
            "hora": [17, 17],
            "FS_geometrico": [1.0, 0.0],
            "punto": ["Fila pequeña", "Fila grande"],
            "n_modulos": [1, 3],
        }
    )
    idx = pd.date_range("2024-03-20 17:00", periods=1, freq="h")

    p_shade = alinear_fs_con_tmy(
        df, idx, modo="exacto", modo_agregacion="auto"
    )

    assert p_shade.iloc[0] == pytest.approx(0.25)
    assert p_shade.attrs["agregacion_fs"]["modo_aplicado"] == "modulos"


def test_clima_alto_con_geometria_cero_no_reduce_produccion_ni_activa_bypass():
    """FS_climatico no entra al motor de bypass ni reduce su referencia."""
    irradiancia = np.array([800.0, 900.0, 700.0])
    temperatura = np.full(3, 25.0)
    fs_climatico = np.full(3, 0.9)  # diagnóstico solamente; no es p_shade
    fs_geometrico = np.zeros(3)

    resultado = simular_bypass_horario(
        G_eff=irradiancia,
        T_amb=temperatura,
        p_shade=fs_geometrico,
        N_series=8,
        N_parallel=1,
        panel=ASP_ST1_T40,
    )

    assert np.all(fs_climatico > 0.8)
    assert resultado["horas_sombra"] == 0
    assert resultado["horas_bypass"] == 0
    assert resultado["kwh_bypass_anual"] == 0.0
    np.testing.assert_allclose(
        resultado["P_dc_kW"],
        resultado["P_dc_uniforme_kW"],
        rtol=0,
        atol=1e-12,
    )


def test_ray_casting_real_produce_sombra_geometrica_determinista():
    """Un obstáculo colocado sobre el vector solar debe producir FS=1."""
    timestamp = pd.DatetimeIndex(["2024-03-20T17:00:00Z"])
    solar = posiciones_solares(6.25, -75.56, timestamp)
    direction = vector_al_sol(
        solar.iloc[0]["elevacion"],
        solar.iloc[0]["acimut"],
    )

    # El centro del cubo queda sobre el rayo que parte del punto P1.
    obstacle = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    obstacle.apply_translation(direction * 3.0)
    rows = calcular_fs_horario(
        obstacle,
        [{"nombre": "P1", "fachada": "Sur", "x": 0.0, "y": 0.0, "z": 0.0}],
        6.25,
        -75.56,
        timestamp,
    )

    assert len(rows) == 1
    assert rows.iloc[0]["FS_geometrico"] == 1.0
    assert rows.iloc[0]["FS"] == rows.iloc[0]["FS_geometrico"]