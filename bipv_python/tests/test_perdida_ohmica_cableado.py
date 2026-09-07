# -*- coding: utf-8 -*-
"""
Pérdida óhmica de cableado DC/AC (7-sep-2026) -- calculos/diagrama_unifilar.py::
calcular_perdida_ohmica(). Capa de cálculo eléctrico puro (sin Streamlit, sin
dibujo) que reemplaza el % fijo manual por una resistencia real (Ω) por tramo,
calculada de longitud + calibre reales del proyecto -- el motor de producción
(calculos/produccion.py, calculos/produccion_iv.py) aplica esa resistencia a
la corriente REAL hora a hora (I(t)²·R), no a condiciones STC fijas como hace
PVsyst. Ver test_produccion_perdida_ohmica.py para la integración hora a hora.

Casos cubiertos:
  - Un solo tramo DC (proyecto sin multi-superficie) -- resistencia y
    resistividad verificadas a mano.
  - Tramo AC -- verificado a mano.
  - Dos tramos DC de distinta longitud -- cada uno con su propia resistencia
    y su fracción de paneles correcta (no se combinan en una sola R).
  - Sin longitud/calibre -- resistencia_ohm queda en None (nunca se inventa).
  - Sin tramos_dc en absoluto -- lista de tramos vacía, nada revienta.
"""
import pytest

from calculos.diagrama_unifilar import (
    calcular_perdida_ohmica,
    RESISTIVIDAD_COBRE_OHM_MM2_M_20C,
    COEF_TEMP_COBRE_POR_C,
)

PANEL = {"Isc_stc": 10.0}
INVERSOR = {"P_ac_nom_W": 15_000.0}


def _rho(T_C: float) -> float:
    return RESISTIVIDAD_COBRE_OHM_MM2_M_20C * (1 + COEF_TEMP_COBRE_POR_C * (T_C - 20.0))


def test_un_tramo_dc_resistencia_correcta_a_mano():
    r = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
        tramos_dc=[{"nombre": "Techo", "longitud_m": 20.0, "calibre_mm2": 6.0, "n_paneles": 40}],
        T_diseno_C=45.0,
    )
    rho_esperada = _rho(45.0)
    r_dc_esperada = 2.0 * 20.0 * rho_esperada / 6.0
    assert r["tramos"][0]["resistencia_ohm"] == pytest.approx(r_dc_esperada)
    assert r["tramos"][0]["fraccion_paneles"] == 1.0
    assert r["resistividad_ohm_mm2_m"] == pytest.approx(rho_esperada, abs=1e-6)


def test_tramo_ac_resistencia_correcta_a_mano():
    r = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
        longitud_ac_m=15.0, calibre_ac_mm2=16.0,
        T_diseno_C=45.0,
    )
    rho_esperada = _rho(45.0)
    r_ac_esperada = 2.0 * 15.0 * rho_esperada / 16.0
    assert r["resistencia_ac_ohm"] == pytest.approx(r_ac_esperada)


def test_corriente_de_diseno_dc_reutiliza_dimensionamiento():
    r = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
    )
    # Isc_stc(10) * N_strings_tracker(2) * FS(1.25) = 25.0 -- misma fórmula
    # que evaluar_compatibilidad_string() en calculos/dimensionamiento.py.
    assert r["corriente_dc_diseno_A"] == pytest.approx(25.0)


def test_dos_tramos_dc_no_se_combinan_en_una_sola_resistencia():
    r = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
        tramos_dc=[
            {"nombre": "Fachada Sur", "longitud_m": 10.0, "calibre_mm2": 6.0, "n_paneles": 30},
            {"nombre": "Fachada Norte", "longitud_m": 40.0, "calibre_mm2": 6.0, "n_paneles": 10},
        ],
        T_diseno_C=45.0,
    )
    assert len(r["tramos"]) == 2
    rho_esperada = _rho(45.0)
    r_sur = next(t for t in r["tramos"] if t["nombre"] == "Fachada Sur")
    r_norte = next(t for t in r["tramos"] if t["nombre"] == "Fachada Norte")
    # Cada tramo tiene su PROPIA resistencia -- el de Norte, con 4x la
    # longitud del de Sur y mismo calibre, tiene 4x su resistencia.
    assert r_norte["resistencia_ohm"] == pytest.approx(r_sur["resistencia_ohm"] * 4.0)
    assert r_sur["resistencia_ohm"] == pytest.approx(2.0 * 10.0 * rho_esperada / 6.0)
    # Fracción de paneles: 30/(30+40) y 10/40 -- no un simple promedio.
    assert r_sur["fraccion_paneles"] == pytest.approx(30 / 40)
    assert r_norte["fraccion_paneles"] == pytest.approx(10 / 40)


def test_resistencia_dc_efectiva_es_suma_de_fraccion_cuadrado_por_r():
    r = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
        tramos_dc=[
            {"nombre": "Fachada Sur", "longitud_m": 10.0, "calibre_mm2": 6.0, "n_paneles": 30},
            {"nombre": "Fachada Norte", "longitud_m": 40.0, "calibre_mm2": 6.0, "n_paneles": 10},
        ],
        T_diseno_C=45.0,
    )
    r_sur = next(t for t in r["tramos"] if t["nombre"] == "Fachada Sur")
    r_norte = next(t for t in r["tramos"] if t["nombre"] == "Fachada Norte")
    esperado = (r_sur["fraccion_paneles"] ** 2) * r_sur["resistencia_ohm"] + \
               (r_norte["fraccion_paneles"] ** 2) * r_norte["resistencia_ohm"]
    assert r["resistencia_dc_efectiva_ohm"] == pytest.approx(esperado)
    # Verificación independiente: con un único tramo (fracción=1.0), la
    # resistencia efectiva debe ser EXACTAMENTE la resistencia de ese tramo
    # -- caso trivial que confirma que la fórmula no introduce un factor
    # espurio.
    r_uno = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
        tramos_dc=[{"nombre": "Techo", "longitud_m": 20.0, "calibre_mm2": 6.0, "n_paneles": 40}],
        T_diseno_C=45.0,
    )
    assert r_uno["resistencia_dc_efectiva_ohm"] == pytest.approx(r_uno["tramos"][0]["resistencia_ohm"])


def test_tramo_sin_longitud_o_calibre_queda_en_none_nunca_inventa():
    r = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
        tramos_dc=[{"nombre": "Techo", "n_paneles": 40}],  # sin longitud/calibre
    )
    assert r["tramos"][0]["resistencia_ohm"] is None
    assert r["resistencia_ac_ohm"] is None  # tampoco se dio longitud/calibre AC
    assert r["resistencia_dc_efectiva_ohm"] is None  # nunca inventa con un tramo incompleto


def test_sin_tramos_dc_no_revienta_y_devuelve_lista_vacia():
    r = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
    )
    assert r["tramos"] == []


def test_temperatura_de_diseno_mayor_aumenta_la_resistencia():
    r_frio = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
        tramos_dc=[{"nombre": "Techo", "longitud_m": 20.0, "calibre_mm2": 6.0, "n_paneles": 40}],
        T_diseno_C=20.0,
    )
    r_caliente = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
        tramos_dc=[{"nombre": "Techo", "longitud_m": 20.0, "calibre_mm2": 6.0, "n_paneles": 40}],
        T_diseno_C=60.0,
    )
    assert r_caliente["tramos"][0]["resistencia_ohm"] > r_frio["tramos"][0]["resistencia_ohm"]
    # A 20°C la resistividad debe ser exactamente la de catálogo IEC 60228 (sin corrección).
    assert r_frio["resistividad_ohm_mm2_m"] == pytest.approx(RESISTIVIDAD_COBRE_OHM_MM2_M_20C)
