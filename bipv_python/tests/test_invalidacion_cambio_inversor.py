# -*- coding: utf-8 -*-
"""Contrato de estado al adoptar una configuración de inversor."""

import pandas as pd

from calculos.invalidacion import (
    ESTADO_MOTOR_OPTICO,
    KEYS_DERIVADOS_INVERSOR,
    KEYS_DERIVADOS_POA,
    invalidar_por_cambio_inversor,
)
from calculos.mismatch_bypass import exigir_poa_sin_termico


ESTADO_MOTOR_OPTICO_ESPERADO = {
    "motor_optico_ok",
    "motor_optico_result_df",
    "motor_optico_summary",
    "poa_efectiva_df",
    "poa_sin_termico_df",
    "poa_efectiva_anual_kWh_m2",
    "motor_optico_b0",
    "motor_optico_tau",
    "motor_optico_k_bipv",
    "motor_optico_noct",
    "motor_optico_coef_temp",
    "motor_optico_f_iam_dif",
    "motor_optico_k_soil_vert",
    "motor_optico_soiling_custom",
    "motor_optico_soiling_config",
}


def test_conjuntos_de_invalidation_son_completos_y_disjuntos():
    assert set(ESTADO_MOTOR_OPTICO) == ESTADO_MOTOR_OPTICO_ESPERADO
    assert set(ESTADO_MOTOR_OPTICO) <= set(KEYS_DERIVADOS_POA)
    assert not set(ESTADO_MOTOR_OPTICO) & set(KEYS_DERIVADOS_INVERSOR)
    assert set(KEYS_DERIVADOS_INVERSOR) == (
        set(KEYS_DERIVADOS_POA) - set(ESTADO_MOTOR_OPTICO)
    )


def test_cambio_inversor_conserva_optica_e_invalida_downstream():
    valores_opticos = {clave: object() for clave in ESTADO_MOTOR_OPTICO}
    estado = {
        **valores_opticos,
        **{clave: object() for clave in KEYS_DERIVADOS_INVERSOR},
        "tmy_df": object(),
        "poa_df": object(),
        "nombre_proyecto": "Proyecto conservado",
    }

    tmy = estado["tmy_df"]
    poa_base = estado["poa_df"]
    eliminadas = invalidar_por_cambio_inversor(estado)

    assert set(eliminadas) == set(KEYS_DERIVADOS_INVERSOR)
    for clave, valor in valores_opticos.items():
        assert estado[clave] is valor
    assert estado["tmy_df"] is tmy
    assert estado["poa_df"] is poa_base
    assert estado["nombre_proyecto"] == "Proyecto conservado"
    assert not set(KEYS_DERIVADOS_INVERSOR) & set(estado)


def test_cambio_inversor_es_idempotente_y_acepta_estado_parcial():
    poa_sin_termico = object()
    estado = {
        "motor_optico_ok": True,
        "poa_sin_termico_df": poa_sin_termico,
        "produccion_ok": True,
    }

    assert invalidar_por_cambio_inversor(estado) == ["produccion_ok"]
    assert invalidar_por_cambio_inversor(estado) == []
    assert estado == {
        "motor_optico_ok": True,
        "poa_sin_termico_df": poa_sin_termico,
    }


def test_produccion_sigue_seleccionando_poa_sin_termico_tras_cambio_inversor():
    poa_sin_termico = pd.DataFrame({"poa_global": [250.0, 500.0, 750.0]})
    estado = {
        "motor_optico_ok": True,
        "poa_sin_termico_df": poa_sin_termico,
        "poa_efectiva_df": pd.DataFrame({"poa_global": [225.0, 450.0, 675.0]}),
        "motor_optico_k_bipv": 1.3,
        "produccion_ok": True,
        "res_produccion": {"E_ac_anual_kWh": 1234.0},
        "financiero_ok": True,
    }

    invalidar_por_cambio_inversor(estado)
    poa_seleccionada, claves_invalidadas = exigir_poa_sin_termico(estado)

    assert poa_seleccionada is poa_sin_termico
    assert claves_invalidadas == []
    assert estado["motor_optico_ok"] is True
    assert "produccion_ok" not in estado
    assert "res_produccion" not in estado
    assert "financiero_ok" not in estado