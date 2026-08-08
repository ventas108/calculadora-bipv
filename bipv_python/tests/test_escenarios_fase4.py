import pytest
import pandas as pd

from calculos.escenarios_fase4 import (
    SCENARIO_SCHEMA_VERSION,
    capturar_base_comparacion,
    comparar_bases,
    construir_definicion_escenarios,
    validar_base_comparacion,
    validar_definicion_escenarios,
)


def test_bogota_define_tres_escenarios_y_reconciliacion():
    definicion = construir_definicion_escenarios(
        nombre_proyecto="Proyecto BIPV Bogotá Teusaquillo",
        fuente_horizonte=True,
        fuente_sketchup=True,
        tipo_optimizacion="paneles",
        panel_nombre="ASP-ST1-T40",
        inversor_nombre="ECO HIBRID SNA US 6K",
    )

    validar_definicion_escenarios(definicion)
    assert definicion["schema_version"] == SCENARIO_SCHEMA_VERSION
    assert definicion["escenarios"]["referencia"]["estado"] == "definido"
    assert (
        definicion["escenarios"]["actual"]["estado"]
        == "definido_reconciliacion_pendiente"
    )
    assert definicion["escenarios"]["optimizada"]["estado"] == "pendiente_parametros"
    assert definicion["politica_fuentes_actual"]["no_sumar_dos_veces"] is True


def test_no_permite_situacion_actual_sin_fuente():
    with pytest.raises(ValueError, match="al menos una fuente"):
        construir_definicion_escenarios(
            nombre_proyecto="Bogotá",
            fuente_horizonte=False,
            fuente_sketchup=False,
        )


def test_rechaza_doble_fuente_sin_politica_de_reconciliacion():
    definicion = construir_definicion_escenarios(
        nombre_proyecto="Bogotá",
        fuente_horizonte=True,
        fuente_sketchup=True,
    )
    definicion["politica_fuentes_actual"]["no_sumar_dos_veces"] = False
    with pytest.raises(ValueError, match="doble conteo"):
        validar_definicion_escenarios(definicion)


def _estado_base():
    idx = pd.date_range("2023-01-01", periods=8760, freq="h", tz="UTC")
    tmy = pd.DataFrame(
        {
            "T2m": [20.0] * 8760,
            "GHI": [500.0] * 8760,
        },
        index=idx,
    )
    poa = pd.DataFrame({"poa_global": [450.0] * 8760}, index=idx)
    return {
        "_solar_lat_guardada": 4.65,
        "_solar_lon_guardada": -74.08,
        "_solar_alt_guardada": 2600.0,
        "tmy_ciudad": "Bogotá",
        "tmy_df": tmy,
        "poa_df": poa,
        "azimuth_fachada": 180.0,
        "tilt_fachada": 90.0,
        "sk_puntos_df": pd.DataFrame(
            [
                {
                    "Punto": "Fila 1",
                    "Fachada": "Sur",
                    "x (m)": 0.0,
                    "y (m)": 0.0,
                    "z (m)": 4.0,
                }
            ]
        ),
        "panel_nombre_dim": "ASP-ST1-T40",
        "panel_dict": {"nombre": "ASP-ST1-T40", "Pmax_stc": 60.0},
        "inversor_nombre_dim": "Inversor Bogotá",
        "inversor_dict_dim": {"Vdc_max": 600.0, "eta": 0.975},
        "N_paneles_dim": 12,
        "N_serie": 6,
        "N_str_tr": 1,
        "eta_inversor": 0.975,
        "motor_optico_ok": True,
        "motor_optico_b0": 0.12,
        "motor_optico_tau": 0.25,
        "motor_optico_k_bipv": 1.3,
        "motor_optico_noct": 45.0,
        "motor_optico_coef_temp": -0.0021,
        "motor_optico_f_iam_dif": 0.95,
        "motor_optico_k_soil_vert": 0.65,
        "mo_soiling_custom": False,
    }


def test_base_unica_completa_se_puede_validar():
    base = capturar_base_comparacion(_estado_base())

    assert base["lista_para_comparar"] is True
    assert base["faltantes"] == []
    validar_base_comparacion(base)


def test_base_incompleta_no_se_puede_validar():
    state = _estado_base()
    state.pop("motor_optico_k_bipv")
    base = capturar_base_comparacion(state)

    assert base["lista_para_comparar"] is False
    with pytest.raises(ValueError, match="incompleta"):
        validar_base_comparacion(base)


def test_cambio_de_tmy_rompe_la_base_unica():
    base_a = capturar_base_comparacion(_estado_base())
    state_b = _estado_base()
    state_b["tmy_df"] = state_b["tmy_df"].copy()
    state_b["tmy_df"].iloc[0, 0] = 21.0
    base_b = capturar_base_comparacion(state_b)

    with pytest.raises(ValueError, match="tmy|TMY"):
        comparar_bases(base_a, base_b)