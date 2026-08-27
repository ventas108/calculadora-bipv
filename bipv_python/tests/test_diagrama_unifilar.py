# -*- coding: utf-8 -*-
"""Tests de calculos/diagrama_unifilar.py -- Fase 1 (MVP)."""
import schemdraw

from calculos.diagrama_unifilar import (
    construir_config_unifilar,
    generar_diagrama_unifilar,
)


def test_config_calcula_derivados_correctos():
    cfg = construir_config_unifilar(
        panel={"Pmax_stc": 720.0},
        n_paneles=306,
        n_serie=18,
        inversor={"P_ac_nom_W": 100_000},
        n_inversores=2,
        tension_red_V=400,
    )
    assert cfg["generador"]["p_dc_kWp"] == 220.32
    assert cfg["generador"]["n_strings"] == 17
    assert cfg["generador"]["string_incompleto"] is False
    assert cfg["inversores"]["p_ac_total_kW"] == 200.0
    # Corriente AC estimada (1.25 x NEC, trifasico): 1.25*200000/(sqrt(3)*400)
    assert cfg["proteccion_ac_A"] == 360.8


def test_config_detecta_string_incompleto():
    cfg = construir_config_unifilar(panel={"Pmax_stc": 400.0}, n_paneles=25, n_serie=10)
    # 25 no es multiplo de 10 -- 2 strings completos + 5 modulos sueltos
    assert cfg["generador"]["string_incompleto"] is True
    assert cfg["generador"]["n_strings"] == 2


def test_config_no_revienta_con_datos_incompletos():
    # Sin panel, sin inversor -- caso de un proyecto recien creado. Los
    # derivados deben quedar en None, no lanzar excepcion (mismo criterio
    # que filtrar_inversores_compatibles: dato faltante != dato invalido).
    cfg = construir_config_unifilar(nombre_proyecto="Proyecto vacio")
    assert cfg["generador"]["p_dc_kWp"] is None
    assert cfg["inversores"]["p_ac_total_kW"] is None
    assert cfg["proteccion_ac_A"] is None


def test_proteccion_ac_manual_no_se_sobreescribe():
    cfg = construir_config_unifilar(
        panel={"Pmax_stc": 720.0}, n_paneles=306, n_serie=18,
        inversor={"P_ac_nom_W": 100_000}, n_inversores=2,
        tension_red_V=400, proteccion_ac_A=350.0,
    )
    assert cfg["proteccion_ac_A"] == 350.0


def test_genera_diagrama_un_inversor():
    cfg = construir_config_unifilar(
        nombre_proyecto="Fachada Test", panel_nombre="ASP-ST1-T40",
        panel={"Pmax_stc": 200.0}, n_paneles=40, n_serie=10,
        inversor_nombre="Growatt MIN 5000TL-X", inversor={"P_ac_nom_W": 5000},
        n_inversores=1, proteccion_dc_A=15, tension_red_V=220,
    )
    d = generar_diagrama_unifilar(cfg)
    assert isinstance(d, schemdraw.Drawing)


def test_genera_diagrama_multiples_inversores_uraba():
    # Caso real: proyecto Agrivoltaico Uraba (306 paneles, 17x18, 2x Growatt)
    cfg = construir_config_unifilar(
        nombre_proyecto="Agrivoltaico Uraba", cliente="Innovacion Quimica",
        tipo_instalacion="Granja fotovoltaica",
        panel_nombre="JA Solar JAM66D46-720/LB", panel={"Pmax_stc": 720.0},
        n_paneles=306, n_serie=18,
        inversor_nombre="Growatt MAX 100KTL3 LV",
        inversor={"P_ac_nom_W": 100_000}, n_inversores=2, tension_red_V=400,
    )
    d = generar_diagrama_unifilar(cfg)
    assert isinstance(d, schemdraw.Drawing)


def test_genera_diagrama_sin_datos_no_revienta():
    # Proyecto recien creado, sin nada configurado todavia -- el generador
    # debe producir un dibujo generico (con textos "Generador FV",
    # "Inversor", etc.) en vez de fallar.
    cfg = construir_config_unifilar()
    d = generar_diagrama_unifilar(cfg)
    assert isinstance(d, schemdraw.Drawing)
