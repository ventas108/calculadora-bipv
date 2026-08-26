# -*- coding: utf-8 -*-
"""Compatibilidad AC (26-ago-2026): verifica calculos.comparador_inversores.
verificar_compatibilidad_ac() -- criterio que no existía en ningún lugar de
la app antes de esto (todo el motor solo chequeaba el lado DC: Vdc_max,
MPPT, Isc por tracker). Usa el Growatt-MAX-100KTL3-LV real del catálogo
(único con datos AC poblados hoy) más inversores sintéticos para cubrir las
ramas sin dato -- avisos, no errores.
"""
import pytest

from calculos.comparador_inversores import verificar_compatibilidad_ac
from datos.catalogo_inversores import INVERSORES

GROWATT_MAX_100 = INVERSORES["Growatt-MAX-100KTL3-LV"]


def test_apartado_2_inversores_400v_60hz_es_compatible_sin_capacidad_conexion():
    # Caso real del proyecto: 2× Growatt MAX 100KTL3 LV, red 400V/60Hz
    # (Colombia), sin capacidad de punto de conexión aún definida por el
    # cliente -- debe pasar, pero con aviso de que ese límite no se verificó.
    r = verificar_compatibilidad_ac(
        GROWATT_MAX_100, n_unidades=2, v_red_nominal_V=400.0, frecuencia_red_hz=60.0,
    )
    assert r["compatible"] is True
    assert r["errores"] == []
    assert any("Capacidad del punto de conexión" in a for a in r["avisos"])
    assert r["corriente_ac_total_A"] == pytest.approx(2 * 158.8, abs=0.05)
    assert r["potencia_ac_total_kVA"] == pytest.approx(220.0, abs=0.1)


def test_corriente_combinada_dentro_de_capacidad_de_conexion_es_compatible():
    r = verificar_compatibilidad_ac(
        GROWATT_MAX_100, n_unidades=2, v_red_nominal_V=400.0,
        capacidad_conexion_A=400.0,
    )
    assert r["compatible"] is True
    assert r["errores"] == []
    assert not any("Capacidad del punto de conexión" in a for a in r["avisos"])


def test_corriente_combinada_excede_capacidad_de_conexion_es_error():
    # 2 unidades = 317.6 A; un tablero de 300 A no alcanza.
    r = verificar_compatibilidad_ac(
        GROWATT_MAX_100, n_unidades=2, v_red_nominal_V=400.0,
        capacidad_conexion_A=300.0,
    )
    assert r["compatible"] is False
    assert any("supera la capacidad del punto de conexión" in e for e in r["errores"])


def test_tension_de_red_fuera_del_rango_ac_es_error():
    # El Growatt MAX 100KTL3 LV opera en [340, 440] V -- 208V (típico EEUU
    # residencial trifásico) queda fuera.
    r = verificar_compatibilidad_ac(GROWATT_MAX_100, n_unidades=1, v_red_nominal_V=208.0)
    assert r["compatible"] is False
    assert any("Tensión de red" in e for e in r["errores"])


def test_frecuencia_fuera_de_lo_soportado_es_error():
    r = verificar_compatibilidad_ac(
        GROWATT_MAX_100, n_unidades=1, v_red_nominal_V=400.0, frecuencia_red_hz=50.0,
    )
    # 50 Hz SÍ está soportado (frecuencia_hz = (50, 60)) -- no debe fallar.
    assert r["compatible"] is True
    r_incompatible = verificar_compatibilidad_ac(
        GROWATT_MAX_100, n_unidades=1, v_red_nominal_V=400.0, frecuencia_red_hz=45.0,
    )
    assert r_incompatible["compatible"] is False
    assert any("Frecuencia de red" in e for e in r_incompatible["errores"])


def test_inversor_sin_datos_ac_solo_avisa_no_bloquea():
    # La mayoría del catálogo hoy no tiene Vac_nom/I_ac_max_A/frecuencia_hz
    # -- ausencia de dato no es lo mismo que incompatibilidad.
    inversor_sin_ac = {"modelo": "SinDatosAC", "Vdc_max": 1500}
    r = verificar_compatibilidad_ac(inversor_sin_ac, n_unidades=2, v_red_nominal_V=400.0)
    assert r["compatible"] is True
    assert r["errores"] == []
    assert len(r["avisos"]) == 3  # tensión, frecuencia, corriente -- las 3 faltan
    assert r["corriente_ac_total_A"] is None
    assert r["potencia_ac_total_kVA"] is None


def test_tension_nominal_sin_rango_explicito_usa_tolerancia_por_defecto():
    # Un inversor que solo publica Vac_nom (sin Vac_min/Vac_max) acepta
    # +/-5% por defecto -- 380V está a -5% de 400V, justo en el borde.
    inversor_solo_nominal = {"modelo": "SoloNominal", "Vac_nom": 400}
    r_dentro = verificar_compatibilidad_ac(
        inversor_solo_nominal, n_unidades=1, v_red_nominal_V=380.0,
    )
    assert r_dentro["compatible"] is True

    r_fuera = verificar_compatibilidad_ac(
        inversor_solo_nominal, n_unidades=1, v_red_nominal_V=350.0,
    )
    assert r_fuera["compatible"] is False
