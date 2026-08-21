# -*- coding: utf-8 -*-
"""Validación de calculos/comparador_paneles.py (Página 4c) con datos reales
-- catálogo real de paneles/inversores, TMY sintético offline (mismo patrón
que test_simulation_pipeline.py). No usa datos inventados: si el catálogo
cambia, estos tests deben reflejarlo, no al revés.
"""
from datos.catalogo_inversores import INVERSORES
from datos.tecnologias_bipv import ASP_ST1_T40
from simulation.schemas import BIPVConfiguration
from calculos.comparador_paneles import (
    comparar_paneles,
    formatear_comparacion_paneles,
    paneles_excluidos_por_ficha_incompleta,
)
from tests.test_simulation_pipeline import _tmy_sintetico_offline, LAT, LON, ALT_M

GROWATT = INVERSORES["Growatt-MID15KTL3-X"]


def _cfg_base():
    return BIPVConfiguration(
        lat=LAT, lon=LON, alt_m=ALT_M, tilt=90.0, azimuth=180.0, area_m2=100.0,
        panel=ASP_ST1_T40, inversor=GROWATT, N_serie=8, N_strings_tracker=8,
    )


def test_paneles_excluidos_por_ficha_incompleta_refleja_el_catalogo_real():
    excluidos = paneles_excluidos_por_ficha_incompleta()
    assert "ASP-ST1-T40" not in excluidos
    assert "ASP-ST1-T10" in excluidos   # ficha incompleta conocida (Pmax_stc=None)


def test_comparar_paneles_no_crashea_y_devuelve_solo_simulables():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    df = comparar_paneles(
        _cfg_base(), tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    assert not df.empty
    assert set(df["Panel"]) == {"ASP-ST1-T40"}   # el único simulable hoy
    assert "ASP-ST1-T10" not in df["Panel"].tolist()


def test_comparar_paneles_columnas_esperadas_y_valores_positivos():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    df = comparar_paneles(
        _cfg_base(), tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    fila = df.iloc[0]
    assert fila["N° módulos"] > 0
    assert fila["P_dc (kWp)"] > 0
    assert fila["E_ac (kWh/año)"] > 0
    assert 0.0 < fila["PR"] < 1.5
    assert fila["CAPEX (USD)"] > 0
    assert fila["Compatible"] == "✅"   # N_serie=8 con Growatt ya validado contra el XLSM


def test_comparar_paneles_ordena_por_lcoe_ascendente():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    df = comparar_paneles(
        _cfg_base(), tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    lcoe = df["LCOE (USD/kWh)"].tolist()
    assert lcoe == sorted(lcoe)


def test_comparar_paneles_marca_incompatibilidad_electrica_real():
    # N_serie=40 (fuera de la ventana MPPT del Growatt para este panel) debe
    # marcar el candidato como incompatible -- sin inventar el criterio,
    # reusa optimization.constraints.evaluar_compatibilidad_electrica().
    import dataclasses
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    cfg = dataclasses.replace(_cfg_base(), N_serie=40)
    df = comparar_paneles(
        cfg, tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    assert df.iloc[0]["Compatible"] == "❌"


# ── formatear_comparacion_paneles() -- contexto para agentes/analista_produccion.py

def test_formatear_comparacion_declara_el_tipo_de_instalacion():
    # Mismo principio que corrigió el sesgo de fachada en los otros agentes:
    # el tipo de instalación va como dato explícito, no algo que el LLM deba
    # adivinar del nombre genérico "BIPV" de la plataforma.
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    df = comparar_paneles(
        _cfg_base(), tmy, "Granja FV campo",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    texto = formatear_comparacion_paneles(df, "Granja FV campo")
    assert "Tipo de instalación: Granja FV campo" in texto


def test_formatear_comparacion_cita_los_numeros_reales_del_dataframe():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    df = comparar_paneles(
        _cfg_base(), tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    fila = df.iloc[0]
    texto = formatear_comparacion_paneles(df, "BIPV fachada/pérgola")
    assert fila["Panel"] in texto
    assert f"{fila['E_ac (kWh/año)']:,.0f}" in texto
    assert f"{fila['PR']:.3f}" in texto


def test_formatear_comparacion_incluye_motivo_de_incompatibilidad():
    # El agente necesita saber POR QUÉ un candidato se descartó, no solo
    # que salga marcado ❌, para no recomendarlo sin explicación.
    import dataclasses
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    cfg = dataclasses.replace(_cfg_base(), N_serie=40)
    df = comparar_paneles(
        cfg, tmy, "BIPV fachada/pérgola",
        tarifa_cop_kWh=750.0, tipo_cambio=4000.0,
    )
    texto = formatear_comparacion_paneles(df, "BIPV fachada/pérgola")
    assert "❌" in texto
    assert df.iloc[0]["_motivo_electrico"] in texto


def test_formatear_comparacion_dataframe_vacio_no_crashea():
    import pandas as pd
    texto = formatear_comparacion_paneles(pd.DataFrame(), "Granja FV campo")
    assert "Granja FV campo" in texto
    assert "No hay ningún panel simulable" in texto
