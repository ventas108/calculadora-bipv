"""Regresión del contrato solar/eléctrico de la comparación de escenarios."""
import io
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos.metricas_escenarios import (  # noqa: E402
    contrato_comparacion_escenarios,
    comparar_resultados_escenarios,
    metricas_electricas,
    metricas_recuperacion,
    metricas_solares,
)
from calculos.agregacion_fs import promedio_fs_por_claves, resolver_peso  # noqa: E402
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


def test_contrato_calcula_perdidas_con_la_referencia_y_protege_cero():
    contrato = contrato_comparacion_escenarios(
        e_referencia=1000.0,
        e_actual=800.0,
        e_optimizada=950.0,
        magnitud="E_AC_anual_kWh",
    )

    assert contrato["perdidas_pct"]["referencia"] == 0.0
    assert contrato["perdidas_pct"]["actual"] == 20.0
    assert contrato["perdidas_pct"]["optimizada"] == 5.0
    assert contrato["recuperacion_pct"] == 75.0
    assert contrato["recuperacion_etiqueta"] == "75.00%"

    cero = contrato_comparacion_escenarios(
        e_referencia=0.0,
        e_actual=0.0,
        e_optimizada=100.0,
    )
    assert cero["perdidas_pct"]["actual"] is None
    assert cero["recuperacion_estado"] == "no_aplica"
    assert cero["recuperacion_etiqueta"] == "No aplica"


def test_contrato_marca_no_aplica_si_no_hay_perdida_recuperable():
    contrato = contrato_comparacion_escenarios(
        e_referencia=900.0,
        e_actual=950.0,
        e_optimizada=1000.0,
    )

    assert contrato["energia_recuperable"] == 0.0
    assert contrato["recuperacion_pct"] is None
    assert contrato["recuperacion_etiqueta"] == "No aplica"


def test_comparador_acepta_alias_real_de_e_ac_y_no_mezcla_magnitudes():
    resultados = {
        "referencia": {"E_ac_anual_kWh": 1000.0, "poa_efectiva_anual_kWh_m2": 900.0},
        "actual": {"E_AC_anual_kWh": 800.0, "poa_efectiva_anual_kWh_m2": 700.0},
        "optimizada": {"E_ac_KWh": 950.0, "poa_efectiva_anual_kWh_m2": 850.0},
    }
    contrato = comparar_resultados_escenarios(resultados)

    assert contrato["escenarios_completos"] is True
    assert contrato["valores"] == {
        "referencia": 1000.0,
        "actual": 800.0,
        "optimizada": 950.0,
    }
    assert contrato["perdidas_etiqueta"]["actual"] == "20.00%"
    assert contrato["recuperacion_etiqueta"] == "75.00%"

    pendiente = comparar_resultados_escenarios(
        resultados,
        magnitud="POA efectiva",
        unidad="kWh/m²/año",
    )
    assert pendiente["escenarios_completos"] is True
    assert pendiente["es_magnitud_decision"] is False
    assert pendiente["valores"]["actual"] == 700.0


def test_poa_se_puede_comparar_como_diagnostico_sin_ser_magnitud_de_decision():
    contrato = contrato_comparacion_escenarios(
        e_referencia=1000.0,
        e_actual=700.0,
        e_optimizada=900.0,
        magnitud="POA efectiva",
        unidad="kWh/m²/año",
    )

    assert contrato["magnitud"] == "POA efectiva"
    assert contrato["es_magnitud_decision"] is False
    assert contrato["recuperacion_pct"] == round(200 / 300 * 100, 2)


def test_agregacion_auto_pondera_por_modulos_y_no_por_filas_iguales():
    df = pd.DataFrame(
        {
            "mes": [3, 3],
            "hora": [12, 12],
            "punto": ["Fila pequeña", "Fila grande"],
            "FS_geometrico": [1.0, 0.0],
            "n_modulos": [1, 3],
        }
    )

    agregado, auditoria = promedio_fs_por_claves(
        df, ["mes", "hora"], modo="auto"
    )

    assert agregado.loc[0, "FS_geometrico"] == 0.25
    assert auditoria["modo_aplicado"] == "modulos"
    assert auditoria["columna_peso"] == "n_modulos"


def test_agregacion_puede_seleccionar_area_o_potencia():
    df = pd.DataFrame(
        {
            "mes": [3, 3],
            "hora": [12, 12],
            "FS_geometrico": [1.0, 0.0],
            "area_activa_m2": [2.0, 6.0],
            "potencia_instalada_kW": [1.0, 9.0],
        }
    )

    por_area, aud_area = promedio_fs_por_claves(
        df, ["mes", "hora"], modo="area"
    )
    por_potencia, aud_potencia = promedio_fs_por_claves(
        df, ["mes", "hora"], modo="potencia"
    )

    assert por_area.loc[0, "FS_geometrico"] == 0.25
    assert aud_area["modo_aplicado"] == "area"
    assert por_potencia.loc[0, "FS_geometrico"] == 0.1
    assert aud_potencia["modo_aplicado"] == "potencia"


def test_agregacion_auto_fallback_a_simple_es_auditable():
    df = pd.DataFrame(
        {
            "mes": [3, 3],
            "hora": [12, 12],
            "FS_geometrico": [1.0, 0.0],
        }
    )

    agregado, auditoria = promedio_fs_por_claves(
        df, ["mes", "hora"], modo="auto"
    )

    assert agregado.loc[0, "FS_geometrico"] == 0.5
    assert auditoria["modo_aplicado"] == "simple"
    assert auditoria["advertencias"]


def test_agregacion_no_mezcla_pesos_incompletos_silenciosamente():
    df = pd.DataFrame(
        {
            "mes": [3, 3],
            "hora": [12, 12],
            "FS_geometrico": [1.0, 0.0],
            "n_modulos": [2, None],
        }
    )

    agregado, auditoria = promedio_fs_por_claves(
        df, ["mes", "hora"], modo="modulos"
    )

    assert agregado.loc[0, "FS_geometrico"] == 0.5
    assert auditoria["modo_aplicado"] == "simple"
    assert auditoria["n_pesos_validos"] == 1