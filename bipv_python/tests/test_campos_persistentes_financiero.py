"""Campos de Financiero que no se pierden al cambiar de página (27-sep-2026).

Caso real: «Tarifa de excedentes» en 800 volvía a 1.200 al ir a 🏠 Proyecto a
guardar y al cargar el proyecto.
"""
import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGINA = Path(__file__).resolve().parents[1] / "pages" / "7_💰_Financiero.py"


def _app():
    import streamlit as st
    from calculos.campos_persistentes import campo_persistente
    if st.session_state.get("pagina", "fin") == "fin":
        campo_persistente(st.session_state, st.number_input, "Tarifa exc",
                          "tarifa_excedentes_cop_kWh", 1200.0,
                          min_value=0.0, max_value=5000.0, step=10.0)
        campo_persistente(st.session_state, st.slider, "WACC", "fin_tasa_desc_pct", 10.0,
                          min_value=5.0, max_value=20.0, step=0.5)
    else:
        st.write("otra página")


def test_el_valor_sobrevive_al_cambio_de_pagina():
    at = AppTest.from_function(_app)
    at.run()
    at.number_input[0].set_value(800.0).run()
    at.slider[0].set_value(12.0).run()
    at.session_state["pagina"] = "proyecto"
    at.run()
    assert at.session_state["tarifa_excedentes_cop_kWh"] == 800.0      # se guardaría así
    at.session_state["pagina"] = "fin"
    at.run()
    assert at.number_input[0].value == 800.0
    assert at.slider[0].value == 12.0


def test_cargar_un_proyecto_actualiza_el_campo():
    at = AppTest.from_function(_app)
    at.run()
    at.session_state["tarifa_excedentes_cop_kWh"] = 750.0    # lo que escribe «Cargar proyecto»
    at.run()
    assert at.number_input[0].value == 750.0
    at.number_input[0].set_value(700.0).run()                # y luego se puede editar
    at.number_input[0].set_value(650.0).run()
    assert at.session_state["tarifa_excedentes_cop_kWh"] == 650.0


def test_valor_fuera_de_rango_se_recorta():
    from calculos.campos_persistentes import valor_inicial
    assert valor_inicial({"x": 99.0}, "x", 10.0, 5.0, 20.0) == 20.0
    assert valor_inicial({"x": "no"}, "x", 25, 10, 30) == 25
    assert valor_inicial({}, "x", 25, 10, 30) == 25


CAMPOS = {
    "tarifa_excedentes_cop_kWh": "Tarifa de excedentes exportados",
    "fin_costo_estructura_usd_kw": "Estructura, cableado, protecciones",
    "fin_costo_instalacion_pct": "Ingeniería + instalación",
    "fin_imprevistos_pct": "Imprevistos y contingencia",
    "fin_esc_tarifa_pct": "Escalación anual tarifa",
    "fin_esc_opex_pct": "Escalación anual O&M",
    "fin_opex_pct_capex": "O&M anual (%CAPEX)",
    "fin_tasa_desc_pct": "Tasa de descuento WACC",
    "fin_n_anos": "Horizonte de análisis",
    "fin_tasa_renta_pct": "Tasa impuesto de renta",
}


def test_pagina_usa_campos_persistentes():
    src = PAGINA.read_text(encoding="utf-8")
    assert 'key="tarifa_excedentes_cop_kWh"' not in src
    for clave, etiqueta in CAMPOS.items():
        assert f'"{clave}"' in src, clave
        # la etiqueta aparece solo dentro de campo_persistente(...)
        for m in re.finditer(re.escape(etiqueta), src):
            previo = src[max(0, m.start() - 160):m.start()]
            if "st.slider(" in previo[-40:] or "st.number_input(" in previo[-40:]:
                raise AssertionError(f"{etiqueta} sigue como campo sin persistencia")


def test_los_datos_se_guardan_con_el_proyecto():
    from calculos import proyectos_manager as pm
    for clave in CAMPOS:
        assert clave not in pm._CLAVES_EXCLUIR
        assert not clave.startswith(pm._PREFIJOS_TEMP)
    # la clave temporal del campo no se guarda (se reconstruye desde el dato)
    assert "_w_tarifa_excedentes_cop_kWh".startswith(pm._PREFIJOS_TEMP)
