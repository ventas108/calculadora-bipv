# -*- coding: utf-8 -*-
"""Validación de calculos/comparador_paneles.py (Página 4c) con datos reales
-- catálogo real de paneles/inversores, TMY sintético offline (mismo patrón
que test_simulation_pipeline.py). No usa datos inventados: si el catálogo
cambia, estos tests deben reflejarlo, no al revés.
"""
from datos.catalogo_inversores import INVERSORES
from datos.tecnologias_bipv import ASP_ST1_T40
from simulation.schemas import BIPVConfiguration
from calculos.comparador_paneles import comparar_paneles, paneles_excluidos_por_ficha_incompleta
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
