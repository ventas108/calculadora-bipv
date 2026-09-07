# -*- coding: utf-8 -*-
"""
Integración de la pérdida óhmica de cableado + mismatch de fabricación en
las páginas Streamlit (7-sep-2026): 5 Mismatch (sliders + evitar doble
conteo), 6 Producción (pasa los parámetros al motor, con vigencia del
cálculo del Diagrama Unifilar), 20 Diagrama Unifilar (inputs de longitud/
calibre + persistencia), y calculos/invalidacion.py.

Mismo patrón AST/substring que el resto de tests de páginas de este repo
(ver test_pvwatts_persistencia_pagina.py) -- las páginas de Streamlit
requieren sesión/login para ejecutarse de verdad.
"""
import ast
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAG_MISMATCH = os.path.join(_ROOT, "pages", "5_🔀_Mismatch.py")
_PAG_PRODUCCION = os.path.join(_ROOT, "pages", "6_📊_Produccion.py")
_PAG_UNIFILAR = os.path.join(_ROOT, "pages", "20_⚡_Diagrama_Unifilar.py")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_paginas_tienen_sintaxis_valida():
    ast.parse(_leer(_PAG_MISMATCH))
    ast.parse(_leer(_PAG_PRODUCCION))
    ast.parse(_leer(_PAG_UNIFILAR))


# ── Página 5 — Mismatch ──────────────────────────────────────────────────────
def test_mismatch_tiene_slider_de_cableado_ac_nuevo():
    src = _leer(_PAG_MISMATCH)
    assert "pct_cableado_ac" in src
    assert 'st.session_state["pct_cableado_dc"]' in src


def test_mismatch_excluye_mismatch_fab_y_cableado_de_la_cascada_global():
    # cascada_perdidas() (que arma factor_global_mismatch, aplicado como
    # reductor de irradiancia en Producción) debe recibir 0.0 para estos 2
    # factores -- si no, Producción los contaría dos veces (una vez aquí,
    # otra vez como parámetro explícito del motor).
    src = _leer(_PAG_MISMATCH)
    idx = src.index("cascada = cascada_perdidas(")
    bloque = src[idx:idx + 400]
    assert "pct_mismatch_fab       = 0.0" in bloque
    assert "pct_cableado           = 0.0" in bloque


# ── Página 6 — Producción ────────────────────────────────────────────────────
def test_produccion_pasa_mismatch_fab_y_cableado_al_motor():
    src = _leer(_PAG_PRODUCCION)
    for _clave in (
        "pct_mismatch_fab   = st.session_state.get",
        "resistencia_dc_ohm = _resistencia_dc_ohm",
        "pct_cableado_dc    = st.session_state.get",
        "resistencia_ac_ohm = _resistencia_ac_ohm",
        "pct_cableado_ac    = st.session_state.get",
        "N_serie            = _n_serie_cfg",
    ):
        assert _clave in src, f"falta '{_clave}' en _sim_kwargs de Producción"


def test_produccion_valida_vigencia_del_calculo_unifilar_antes_de_usarlo():
    # No debe aplicar un cálculo de otro panel/inversor/N_serie/N_paneles
    # como si fuera el vigente para este proyecto -- N_paneles importa
    # porque la resistencia DC efectiva se calibró contra ese total
    # (fraccion_paneles), un cambio posterior lo invalida (auditoría 7-sep-2026).
    src = _leer(_PAG_PRODUCCION)
    idx = src.index("_unif_vigente = bool(")
    bloque = src[idx:idx + 900]
    assert 'panel_nombre") == panel_nombre' in bloque
    assert 'inversor_nombre") == inversor_nombre' in bloque
    assert 'n_serie") == _n_serie_cfg' in bloque
    assert 'n_paneles_total") == N_paneles' in bloque


# ── Página 20 — Diagrama Unifilar ────────────────────────────────────────────
def test_unifilar_importa_calcular_perdida_ohmica():
    src = _leer(_PAG_UNIFILAR)
    assert "calcular_perdida_ohmica" in src
    assert "CALIBRES_COMERCIALES_MM2" in src


def test_unifilar_persiste_el_resultado_en_session_state():
    src = _leer(_PAG_UNIFILAR)
    assert 'st.session_state["perdida_ohmica_unifilar"] = {' in src
    idx = src.index('st.session_state["perdida_ohmica_unifilar"] = {')
    bloque = src[idx:idx + 900]
    for _clave in ("resistencia_dc_ohm", "resistencia_ac_ohm", "tension_red_V",
                    "panel_nombre", "inversor_nombre", "n_serie", "n_paneles_total"):
        assert f'"{_clave}"' in bloque


def test_unifilar_limpia_el_resultado_si_el_usuario_vacia_los_campos():
    src = _leer(_PAG_UNIFILAR)
    assert 'del st.session_state["perdida_ohmica_unifilar"]' in src


def test_unifilar_soporta_un_tramo_por_superficie():
    src = _leer(_PAG_UNIFILAR)
    assert "tramos_dc_val" in src
    assert "if superficies_val:" in src


# ── calculos/invalidacion.py ─────────────────────────────────────────────────
def test_perdida_ohmica_unifilar_esta_en_la_lista_de_invalidacion():
    ruta = os.path.join(_ROOT, "calculos", "invalidacion.py")
    src = _leer(ruta)
    idx = src.index("KEYS_DERIVADOS_POA = (")
    bloque = src[idx:idx + 2000]
    assert '"perdida_ohmica_unifilar"' in bloque
