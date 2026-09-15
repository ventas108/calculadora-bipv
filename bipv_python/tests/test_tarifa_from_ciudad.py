# -*- coding: utf-8 -*-
"""CodeSpecs/01-datos-proyecto — precedencia de tarifa_fuente en
set_tarifa_from_ciudad().

Contexto (propuesta.md): la función sobreescribía tarifa_cop_kwh sin
verificar si el usuario ya la había corregido a mano con su factura real,
perdiendo esa corrección de forma silenciosa al cambiar de ciudad. La
corrección: solo sobreescribir si tarifa_fuente actual es "catálogo" o
"valor por defecto"; si es manual ("Proyecto"/"Financiero"), conservar el
valor y dejar la referencia de la nueva ciudad en tarifa_sugerida_ciudad.

calculos/tarifa_utils.py importa `streamlit as st` a nivel de módulo y solo
usa `st.session_state` dentro de set_tarifa_from_ciudad() / init_tarifa()
(las funciones bajo prueba aquí no llaman a los widgets de UI) -- se inyecta
un stub mínimo con un dict como session_state, igual que
test_compatibilidad_bateria.py hace para datos/catalogo_baterias_excel.py.
"""
import sys
import types

import pytest


def _cargar_modulo_tarifa_utils(session_state: dict):
    if "streamlit" not in sys.modules:
        stub = types.ModuleType("streamlit")
        stub.session_state = session_state
        sys.modules["streamlit"] = stub
    else:
        sys.modules["streamlit"].session_state = session_state

    # Recargar para asegurar que el módulo vea el session_state de este test
    # (los tests de este archivo no comparten estado entre sí).
    sys.modules.pop("calculos.tarifa_utils", None)
    import calculos.tarifa_utils as mod
    return mod


CIUDADES = {
    "Bogotá":     {"operador": "Codensa", "tarifa_comercial_cop_kwh": 1200},
    "Medellín":   {"operador": "EPM",     "tarifa_comercial_cop_kwh": 900},
    "Sin Catalogo": {"operador": "N/A"},  # ciudad sin tarifa_comercial_cop_kwh
}


@pytest.fixture
def session_state():
    return {}


# ── Fuente manual se conserva al cambiar de ciudad ──────────────────────────

@pytest.mark.parametrize("fuente_manual", ["Proyecto", "Financiero"])
def test_fuente_manual_se_conserva_al_cambiar_de_ciudad(session_state, fuente_manual):
    mod = _cargar_modulo_tarifa_utils(session_state)
    session_state["tarifa_cop_kwh"] = 650.0
    session_state["tarifa_cop_kWh"] = 650.0
    session_state["tarifa_fuente"] = fuente_manual

    mod.set_tarifa_from_ciudad("Bogotá", CIUDADES)

    # El valor manual del usuario NO se pierde
    assert session_state["tarifa_cop_kwh"] == 650.0
    assert session_state["tarifa_cop_kWh"] == 650.0
    assert session_state["tarifa_fuente"] == fuente_manual
    # La UI puede avisar con el valor de referencia de la nueva ciudad
    assert session_state["tarifa_sugerida_ciudad"] == 1200.0


def test_fuente_manual_sin_catalogo_en_ciudad_nueva_no_deja_sugerencia_stale(session_state):
    mod = _cargar_modulo_tarifa_utils(session_state)
    session_state["tarifa_cop_kwh"] = 650.0
    session_state["tarifa_fuente"] = "Proyecto"
    session_state["tarifa_sugerida_ciudad"] = 999.0  # sugerencia vieja de otra ciudad

    mod.set_tarifa_from_ciudad("Sin Catalogo", CIUDADES)

    assert session_state["tarifa_cop_kwh"] == 650.0
    assert session_state["tarifa_fuente"] == "Proyecto"
    assert "tarifa_sugerida_ciudad" not in session_state


# ── Fuente catálogo (o valor por defecto) sí se actualiza ───────────────────

@pytest.mark.parametrize("fuente_no_manual", ["catálogo", "valor por defecto"])
def test_fuente_catalogo_o_default_se_actualiza_al_cambiar_de_ciudad(session_state, fuente_no_manual):
    mod = _cargar_modulo_tarifa_utils(session_state)
    session_state["tarifa_cop_kwh"] = 850.0
    session_state["tarifa_cop_kWh"] = 850.0
    session_state["tarifa_fuente"] = fuente_no_manual

    mod.set_tarifa_from_ciudad("Medellín", CIUDADES)

    assert session_state["tarifa_cop_kwh"] == 900.0
    assert session_state["tarifa_cop_kWh"] == 900.0
    assert session_state["tarifa_fuente"] == "catálogo"
    assert session_state["tarifa_ciudad_origen"] == "Medellín"
    assert session_state["tarifa_operador"] == "EPM"
    assert "tarifa_sugerida_ciudad" not in session_state


def test_primera_carga_sin_fuente_previa_se_trata_como_no_manual(session_state):
    # Sesión nueva: no hay tarifa_fuente todavía -- debe comportarse igual que
    # "valor por defecto" (no bloquear la precarga inicial por ciudad).
    mod = _cargar_modulo_tarifa_utils(session_state)

    mod.set_tarifa_from_ciudad("Bogotá", CIUDADES)

    assert session_state["tarifa_cop_kwh"] == 1200.0
    assert session_state["tarifa_fuente"] == "catálogo"
