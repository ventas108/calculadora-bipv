# -*- coding: utf-8 -*-
"""💰 Financiero: el costo de cada panel sigue al catálogo (26-sep-2026).

Encontrado preparando el proyecto de un cliente: el usuario puso USD 150 al
SPR-E20-327 en 📋 Catálogo Paneles y Financiero seguía mostrando 140. El
costo salía de la copia del panel guardada en la superficie de Vista 3D, y
el campo (con clave fija por posición) conservaba su primer valor.
"""
import os

from calculos.campos_editor import sincronizar_con_fuente
from calculos.sistema_multisuperficie import costo_actual_panel

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_el_campo_toma_el_precio_del_catalogo_la_primera_vez():
    estado = {}
    assert sincronizar_con_fuente(estado, "c", 150.0, 65.0) == 150.0


def test_respeta_lo_que_escribe_el_usuario_mientras_el_catalogo_no_cambie():
    estado = {}
    sincronizar_con_fuente(estado, "c", 150.0, 65.0)
    estado["c"] = 155.0                      # el usuario negocia otro precio
    assert sincronizar_con_fuente(estado, "c", 150.0, 65.0) == 155.0


def test_un_cambio_en_el_catalogo_actualiza_el_campo():
    estado = {}
    sincronizar_con_fuente(estado, "c", None, 140.0)       # sin precio: respaldo
    assert estado["c"] == 140.0
    assert sincronizar_con_fuente(estado, "c", 150.0, 140.0) == 150.0   # el caso real
    estado["c"] = 148.0
    assert sincronizar_con_fuente(estado, "c", 160.0, 140.0) == 160.0


def test_costo_actual_prefiere_el_catalogo_vigente_sobre_la_copia_publicada():
    item = {"panel": "SPR-E20-327 (E20-327NE-WHT-D)", "costo_usd": None}
    excel = {"SPR-E20-327 (E20-327NE-WHT-D)": {"costo_usd": 150.0}}
    assert costo_actual_panel(item, excel, {}) == 150.0
    assert costo_actual_panel(item, {}, {"SPR-E20-327 (E20-327NE-WHT-D)": {"costo_usd": 90.0}}) == 90.0
    assert costo_actual_panel({"panel": "X", "costo_usd": 70.0}, {}, {}) == 70.0
    assert costo_actual_panel({"panel": "X", "costo_usd": None}, {"X": {"costo_usd": None}}, {}) is None


def test_financiero_usa_el_catalogo_vigente_y_una_clave_por_panel():
    src = open(os.path.join(_ROOT, "pages", "7_💰_Financiero.py"), encoding="utf-8").read()
    assert "costo_actual_panel(" in src and "sincronizar_con_fuente(" in src
    assert 'key=f"fin_costo_panel_ms_{_i_pp}"' not in src      # la posición no identifica al panel
