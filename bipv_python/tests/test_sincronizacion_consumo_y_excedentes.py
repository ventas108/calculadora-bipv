# -*- coding: utf-8 -*-
"""Validación de la sincronización de consumo (🏠 Proyecto ↔ 🔋 Baterías) y
la tarifa diferenciada de excedentes (💰 Financiero), 2026-08-21.

Hallazgo del usuario: el consumo declarado en 🏠 Proyecto (modo "Conozco mi
consumo/factura", session_state["consumo_kwh_mes"]) nunca llegaba al motor
financiero real -- ni directamente, ni a través de 🔋 Baterías y Balance
(que tenía su PROPIO consumo, siempre estimado desde la producción, nunca
desde la factura real). Además, el motor financiero no distinguía energía
autoconsumida de excedente exportado -- todo se valoraba a una sola tarifa,
y el excedente quedaba excluido del ingreso por completo cuando había un
balance de baterías activo.

Streamlit no está instalado en este entorno de desarrollo -- se audita el
código fuente vía regex, mismo patrón que los demás tests de páginas.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG_BATERIAS = os.path.join(_ROOT, "pages", "11_🔋_Baterias_y_Balance.py")
_PAG_FINANCIERO = os.path.join(_ROOT, "pages", "7_💰_Financiero.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# ── 🔋 Baterías y Balance: consumo sincronizado con la factura real ─────────

def test_b6_consumo_diario_prioriza_la_factura_real():
    src = _leer(_PAG_BATERIAS)
    assert '_consumo_mes_factura_b6 = float(st.session_state.get("consumo_kwh_mes", 0.0))' in src
    idx_factura = src.index("_consumo_mes_factura_b6")
    idx_widget = src.index('key="consumo_diario_kWh"')
    assert idx_factura < idx_widget


def test_b7_consumo_anual_prioriza_la_factura_real():
    src = _leer(_PAG_BATERIAS)
    assert '_consumo_mes_factura_b7 = float(st.session_state.get("consumo_kwh_mes", 0.0))' in src
    assert "_consumo_anual_default_b7" in src
    # Ya no debe quedar ningún fallback antiguo (solo producción×1.2) suelto
    # -- todos los usos deben pasar por la variable compartida.
    assert src.count("max(e_ac_anual * 1.2, 10000.0)") == 1  # solo la definición fuente


def test_b7_todos_los_modos_de_consumo_usan_el_default_compartido():
    # Los 3 modos de entrada (anual+perfil, horaria, 12 valores manuales)
    # deben derivar del mismo _consumo_anual_default_b7 -- no 3 estimaciones
    # independientes y potencialmente distintas entre sí.
    src = _leer(_PAG_BATERIAS)
    assert src.count("_consumo_anual_default_b7") >= 6


# ── 💰 Financiero: excedente exportado ya no se excluye del ingreso ─────────

def test_e_financiero_incluye_la_exportacion_no_solo_autoconsumo():
    src = _leer(_PAG_FINANCIERO)
    assert '_e_exportacion    = float(_balance_metricas.get("E_exportacion_anual_kWh", 0.0))' in src
    assert "e_financiero = (_e_autoconsumo + _e_exportacion) if _balance_activo else e_ac" in src


def test_frac_exportada_se_calcula_y_se_pasa_a_ambos_escenarios():
    src = _leer(_PAG_FINANCIERO)
    assert "frac_exportada = (_e_exportacion / e_financiero)" in src
    # Debe pasarse tanto al escenario P50 como al P90.
    ocurrencias = src.count("frac_exportada    = frac_exportada,")
    assert ocurrencias == 2, f"esperaba 2 llamadas (P50 y P90) con frac_exportada, encontré {ocurrencias}"


def test_tarifa_excedentes_widget_existe_y_tiene_ayuda_sobre_creg_174():
    src = _leer(_PAG_FINANCIERO)
    assert 'key="tarifa_excedentes_cop_kWh"' in src
    assert "CREG 174" in src
    # Su default debe ser la tarifa de compra (sin descuento inventado) hasta
    # que el usuario la ajuste -- nunca un porcentaje de descuento supuesto.
    assert 'value=float(st.session_state.get("tarifa_excedentes_cop_kWh", tarifa_cop))' in src


def test_tarifa_excedentes_se_pasa_a_ambos_escenarios():
    src = _leer(_PAG_FINANCIERO)
    ocurrencias = src.count("tarifa_excedentes_cop_kWh = tarifa_excedentes_cop,")
    assert ocurrencias == 2
