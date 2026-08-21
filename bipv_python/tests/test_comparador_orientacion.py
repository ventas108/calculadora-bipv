# -*- coding: utf-8 -*-
"""Validación de calculos/comparador_orientacion.py (Página 4d) con datos
reales -- catálogo real de paneles/inversores, TMY sintético offline (mismo
patrón que test_comparador_paneles.py / test_simulation_pipeline.py).
"""
import pandas as pd
import pytest

from datos.catalogo_inversores import INVERSORES
from datos.tecnologias_bipv import ASP_ST1_T40
from simulation.schemas import BIPVConfiguration
from calculos.comparador_orientacion import (
    comparar_orientacion,
    formatear_comparacion_orientacion,
    malla_tilt_azimuth,
)
from tests.test_simulation_pipeline import _tmy_sintetico_offline, LAT, LON, ALT_M

GROWATT = INVERSORES["Growatt-MID15KTL3-X"]


def _cfg_base():
    return BIPVConfiguration(
        lat=LAT, lon=LON, alt_m=ALT_M, tilt=90.0, azimuth=180.0, area_m2=100.0,
        panel=ASP_ST1_T40, inversor=GROWATT, N_serie=8, N_strings_tracker=8,
    )


# ── malla_tilt_azimuth() ──────────────────────────────────────────────────

def test_malla_genera_los_valores_esperados():
    tilt_valores, azimuth_valores = malla_tilt_azimuth(
        tilt_min=0, tilt_max=90, tilt_paso=15, azimuth_min=0, azimuth_max=360, azimuth_paso=30,
    )
    assert tilt_valores == [0, 15, 30, 45, 60, 75, 90]
    # 0°=360°=Norte -- el barrido completo no debe duplicar el punto de cierre.
    assert 360 not in azimuth_valores
    assert azimuth_valores[0] == 0
    assert len(azimuth_valores) == 12   # 0,30,...,330


def test_malla_paso_invalido_lanza_error():
    with pytest.raises(ValueError):
        malla_tilt_azimuth(tilt_paso=0)


def test_malla_inserta_el_valor_actual_si_no_esta_en_la_grilla():
    # tilt=90/azimuth=180 (fachada típica) SÍ caen en la malla por defecto --
    # se fuerza un caso donde NO caen, para probar la inserción real.
    tilt_valores, azimuth_valores = malla_tilt_azimuth(
        tilt_min=0, tilt_max=90, tilt_paso=15, azimuth_min=0, azimuth_max=360, azimuth_paso=30,
        tilt_actual=22.0, azimuth_actual=187.0,
    )
    assert 22.0 in tilt_valores
    assert 187.0 in azimuth_valores
    # y sigue ordenada
    assert tilt_valores == sorted(tilt_valores)
    assert azimuth_valores == sorted(azimuth_valores)


def test_malla_no_duplica_el_valor_actual_si_ya_esta():
    tilt_valores, _ = malla_tilt_azimuth(
        tilt_min=0, tilt_max=90, tilt_paso=15, tilt_actual=90.0,
    )
    assert tilt_valores.count(90.0) == 1


# ── comparar_orientacion() ────────────────────────────────────────────────

def test_comparar_orientacion_no_crashea_y_tiene_las_columnas_esperadas():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    tilt_valores, azimuth_valores = malla_tilt_azimuth(
        tilt_min=60, tilt_max=90, tilt_paso=30, azimuth_min=150, azimuth_max=210, azimuth_paso=30,
    )
    df = comparar_orientacion(_cfg_base(), tmy, tilt_valores, azimuth_valores)
    assert not df.empty
    assert len(df) == len(tilt_valores) * len(azimuth_valores)
    for col in ("Tilt (°)", "Azimuth (°)", "Actual", "N° módulos", "P_dc (kWp)", "E_ac (kWh/año)", "PR"):
        assert col in df.columns
    assert (df["E_ac (kWh/año)"] > 0).all()
    assert (df["PR"] > 0).all() and (df["PR"] < 1.5).all()


def test_comparar_orientacion_ordena_por_energia_descendente():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    tilt_valores, azimuth_valores = malla_tilt_azimuth(
        tilt_min=0, tilt_max=90, tilt_paso=30, azimuth_min=90, azimuth_max=270, azimuth_paso=90,
    )
    df = comparar_orientacion(_cfg_base(), tmy, tilt_valores, azimuth_valores)
    energia = df["E_ac (kWh/año)"].tolist()
    assert energia == sorted(energia, reverse=True)


def test_comparar_orientacion_marca_la_fila_actual():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    cfg = _cfg_base()   # tilt=90, azimuth=180
    tilt_valores, azimuth_valores = malla_tilt_azimuth(
        tilt_min=60, tilt_max=90, tilt_paso=30, azimuth_min=150, azimuth_max=210, azimuth_paso=30,
        tilt_actual=cfg.tilt, azimuth_actual=cfg.azimuth,
    )
    df = comparar_orientacion(cfg, tmy, tilt_valores, azimuth_valores)
    marcadas = df[df["Actual"]]
    assert len(marcadas) == 1
    assert marcadas.iloc[0]["Tilt (°)"] == 90.0
    assert marcadas.iloc[0]["Azimuth (°)"] == 180.0


def test_comparar_orientacion_no_corre_financiero_no_hay_columnas_de_capex():
    # Diferencia de fondo con comparador_paneles: el hardware no cambia, no
    # hay CAPEX/VPN/TIR/LCOE que calcular aquí.
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    tilt_valores, azimuth_valores = malla_tilt_azimuth(
        tilt_min=90, tilt_max=90, tilt_paso=15, azimuth_min=180, azimuth_max=180, azimuth_paso=30,
    )
    df = comparar_orientacion(_cfg_base(), tmy, tilt_valores, azimuth_valores)
    for col in ("CAPEX (USD)", "VPN (USD)", "TIR (%)", "LCOE (USD/kWh)"):
        assert col not in df.columns


def test_comparar_orientacion_lista_vacia_devuelve_dataframe_vacio():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    df = comparar_orientacion(_cfg_base(), tmy, [], [])
    assert df.empty


# ── formatear_comparacion_orientacion() -- contexto para agentes/analista_produccion.py

def test_formatear_comparacion_declara_el_tipo_de_instalacion():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    tilt_valores, azimuth_valores = malla_tilt_azimuth(
        tilt_min=90, tilt_max=90, tilt_paso=15, azimuth_min=180, azimuth_max=180, azimuth_paso=30,
    )
    df = comparar_orientacion(_cfg_base(), tmy, tilt_valores, azimuth_valores)
    texto = formatear_comparacion_orientacion(df, "Granja FV campo")
    assert "Tipo de instalación: Granja FV campo" in texto


def test_formatear_comparacion_aclara_que_el_hardware_no_cambia():
    # El SYSTEM_PROMPT del agente menciona "compatibilidad eléctrica" como
    # criterio -- aquí no aplica, y el contexto debe decirlo explícitamente
    # para que el agente no invente esa comparación.
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    tilt_valores, azimuth_valores = malla_tilt_azimuth(
        tilt_min=90, tilt_max=90, tilt_paso=15, azimuth_min=180, azimuth_max=180, azimuth_paso=30,
    )
    df = comparar_orientacion(_cfg_base(), tmy, tilt_valores, azimuth_valores)
    texto = formatear_comparacion_orientacion(df, "BIPV fachada/pérgola")
    assert "hardware NO cambia" in texto


def test_formatear_comparacion_cita_los_numeros_reales_del_dataframe():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    tilt_valores, azimuth_valores = malla_tilt_azimuth(
        tilt_min=60, tilt_max=90, tilt_paso=30, azimuth_min=150, azimuth_max=210, azimuth_paso=30,
    )
    df = comparar_orientacion(_cfg_base(), tmy, tilt_valores, azimuth_valores)
    fila = df.iloc[0]
    texto = formatear_comparacion_orientacion(df, "BIPV fachada/pérgola")
    assert f"{fila['E_ac (kWh/año)']:,.0f}" in texto
    assert f"{fila['PR']:.3f}" in texto


def test_formatear_comparacion_marca_la_orientacion_actual():
    tmy = _tmy_sintetico_offline(LAT, LON, ALT_M)
    cfg = _cfg_base()
    tilt_valores, azimuth_valores = malla_tilt_azimuth(
        tilt_min=60, tilt_max=90, tilt_paso=30, azimuth_min=150, azimuth_max=210, azimuth_paso=30,
        tilt_actual=cfg.tilt, azimuth_actual=cfg.azimuth,
    )
    df = comparar_orientacion(cfg, tmy, tilt_valores, azimuth_valores)
    texto = formatear_comparacion_orientacion(df, "BIPV fachada/pérgola")
    assert "orientación actual del proyecto" in texto


def test_formatear_comparacion_dataframe_vacio_no_crashea():
    texto = formatear_comparacion_orientacion(pd.DataFrame(), "Granja FV campo")
    assert "Granja FV campo" in texto
    assert "No hay ninguna combinación" in texto
