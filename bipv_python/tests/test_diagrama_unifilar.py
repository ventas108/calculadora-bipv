# -*- coding: utf-8 -*-
"""Tests de calculos/diagrama_unifilar.py -- Fase 1 (MVP) + Fase 2 (batería)."""
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


# ══════════════════════════════════════════════════════════════════════════
# Fase 2 -- bateria
# ══════════════════════════════════════════════════════════════════════════
def test_config_sin_bateria_por_defecto():
    # n_baterias=0 (default) -- bateria inactiva, mismo comportamiento que
    # Fase 1 para proyectos sin bateria (sin regresion).
    cfg = construir_config_unifilar(panel={"Pmax_stc": 720.0}, n_paneles=306, n_serie=18)
    assert cfg["bateria"]["activa"] is False
    assert cfg["bateria"]["capacidad_total_kWh"] is None


def test_config_bateria_calcula_capacidad_total():
    cfg = construir_config_unifilar(
        bateria_nombre="Growatt ARK 10kWh",
        bateria={"capacidad_kWh": 10.0},
        n_baterias=2,
    )
    assert cfg["bateria"]["activa"] is True
    assert cfg["bateria"]["capacidad_total_kWh"] == 20.0
    assert cfg["bateria"]["cantidad"] == 2


def test_config_bateria_capacidad_manual_tiene_prioridad():
    cfg = construir_config_unifilar(
        bateria={"capacidad_kWh": 10.0},
        n_baterias=2,
        capacidad_kWh_unidad=15.0,  # valor manual, distinto al del catalogo
    )
    assert cfg["bateria"]["capacidad_total_kWh"] == 30.0


def test_diagrama_sin_bateria_no_dibuja_rama_extra():
    # Regresion: el diagrama de un proyecto SIN bateria debe generarse sin
    # error y sin necesitar ninguno de los parametros de bateria.
    cfg = construir_config_unifilar(
        panel={"Pmax_stc": 720.0}, n_paneles=306, n_serie=18,
        inversor={"P_ac_nom_W": 100_000}, n_inversores=2, tension_red_V=400,
    )
    assert cfg["bateria"]["activa"] is False
    d = generar_diagrama_unifilar(cfg)
    assert isinstance(d, schemdraw.Drawing)


def test_diagrama_con_bateria_hibrida():
    cfg = construir_config_unifilar(
        nombre_proyecto="Fachada BIPV con respaldo", cliente="Cliente Demo",
        panel_nombre="ASP-ST1-T40", panel={"Pmax_stc": 200.0},
        n_paneles=40, n_serie=10,
        inversor_nombre="Growatt SPH 10000TL3 BH-UP",
        inversor={"P_ac_nom_W": 10_000}, n_inversores=1, tension_red_V=220,
        bateria_nombre="Growatt ARK 10kWh", bateria={"capacidad_kWh": 10.0},
        n_baterias=2, proteccion_bat_A=63,
    )
    assert cfg["bateria"]["activa"] is True
    d = generar_diagrama_unifilar(cfg)
    assert isinstance(d, schemdraw.Drawing)
