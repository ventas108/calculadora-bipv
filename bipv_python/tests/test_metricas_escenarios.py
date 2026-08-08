"""Regresión del contrato solar/eléctrico de la comparación de escenarios."""
import io
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos.metricas_escenarios import (  # noqa: E402
    metricas_electricas,
    metricas_recuperacion,
    metricas_solares,
)
from calculos.mismatch_bypass import cargar_csv_fs  # noqa: E402


def test_perdida_poa_no_se_convierte_en_perdida_ac():
    idx = pd.date_range("2024-01-01", periods=4, freq="h", tz="UTC")
    metricas = metricas_solares(
        poa_bruta_kWh_m2=1000.0,
        poa_efectiva_kWh_m2=800.0,
        fs_horario=pd.Series([0.0, 0.5, 0.0, 0.0], index=idx),
        tmy_index=idx,
        poa_horaria=pd.Series([1000.0, 1000.0, 0.0, 0.0], index=idx),
    )

    assert metricas["perdida_poa_solar_kWh_m2"] == 200.0
    assert metricas["horas_con_sombra"] == 1
    assert "AC" in metricas["nota_perdida_poa"]

    electricas = metricas_electricas(resultado_produccion=None)
    assert electricas["energia_ac_kWh"] is None
    assert electricas["perdida_electrica_total_kWh"] is None


def test_parser_conserva_fachada_punto_y_obstaculo():
    csv = (
        "Mes,Dia,Hora,FS_geometrico,Fachada,Punto,Obstaculo\n"
        "3,20,17,0.5,Sur,Fila 1,Edificio vecino\n"
    )
    df, _ = cargar_csv_fs(io.StringIO(csv))

    assert df.loc[0, "fachada"] == "Sur"
    assert df.loc[0, "punto"] == "Fila 1"
    assert df.loc[0, "obstaculo"] == "Edificio vecino"


def test_metricas_solares_identifican_grupos_y_mes_critico():
    idx = pd.date_range("2024-01-01", periods=4, freq="h", tz="UTC")
    df_fs = pd.DataFrame(
        {
            "mes": [1, 1, 1, 1],
            "dia": [1, 1, 1, 1],
            "hora": [0, 1, 2, 3],
            "FS_geometrico": [0.0, 1.0, 0.0, 0.0],
            "fachada": ["Sur"] * 4,
            "punto": ["Fila 1"] * 4,
            "obstaculo": ["Edificio vecino"] * 4,
        }
    )
    metricas = metricas_solares(
        poa_bruta_kWh_m2=4.0,
        fs_horario=pd.Series([0.0, 1.0, 0.0, 0.0], index=idx),
        tmy_index=idx,
        poa_horaria=pd.Series([1000.0] * 4, index=idx),
        df_fs=df_fs,
        modo_fs="exacto",
    )

    assert metricas["meses_criticos"] == ["Ene"]
    assert metricas["obstaculo_responsable"] == "Edificio vecino"
    assert metricas["por_fachada"][0]["poa_perdida_kWh_m2"] == 1.0
    assert metricas["por_fila_punto"][0]["grupo"] == "Fila 1"


def test_recuperacion_solo_usa_ac_y_se_limita_a_la_perdida():
    pendiente = metricas_recuperacion(
        e_ac_referencia_kWh=None,
        e_ac_actual_kWh=700.0,
        e_ac_optimizada_kWh=900.0,
    )
    assert pendiente["disponible"] is False

    recuperacion = metricas_recuperacion(
        e_ac_referencia_kWh=1000.0,
        e_ac_actual_kWh=700.0,
        e_ac_optimizada_kWh=1100.0,
    )
    assert recuperacion["energia_recuperable_kWh"] == 300.0
    assert recuperacion["energia_recuperada_kWh"] == 300.0
    assert recuperacion["porcentaje_recuperacion"] == 100.0