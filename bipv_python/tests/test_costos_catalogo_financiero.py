# -*- coding: utf-8 -*-
"""💰 Financiero con los precios vigentes de los catálogos (26-sep-2026).

- Inversores en modo multi-superficie: el CAPEX de inversores era
  USD 120/kWp × kWp de paneles con el inversor de 📐 Dimensionamiento, sin
  mirar los inversores reales del diseño de 🗺️ Vista 3D (1 o 2, cuáles).
- Superficie única: el precio era una copia tomada al abrir Dimensionamiento
  y, sin potencia AC, se usaba la potencia FV máxima como si lo fuera.
- Baterías: el costo quedaba fijo al pulsar «Dimensionar batería»; un precio
  cambiado después en el catálogo no llegaba, sin aviso.
"""
import os

from calculos.costos_catalogo import (
    capex_baterias_vigente,
    costo_actual_inversor,
    potencia_ac_kw_inversor,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CAT = {"Growatt MID15KTL3-X": {"costo_usd": 1850.0}, "SG5.0RT": {"costo_usd": 900.0},
        "Sin precio": {"costo_usd": None}}


def test_inversor_del_catalogo_usa_el_precio_vigente():
    inv = {"inversor_id": "INV-2", "origen_ficha": "catalogo", "nombre": "Growatt MID15KTL3-X"}
    assert costo_actual_inversor(inv, _CAT, "SG5.0RT") == 1850.0


def test_inversor_del_proyecto_usa_el_precio_del_inversor_de_dimensionamiento():
    inv = {"inversor_id": "INV-1", "origen_ficha": "proyecto", "nombre": "SG5.0RT"}
    assert costo_actual_inversor(inv, _CAT, "SG5.0RT") == 900.0


def test_inversor_manual_o_sin_precio_no_inventa():
    assert costo_actual_inversor({"origen_ficha": "manual", "nombre": ""}, _CAT, "SG5.0RT") is None
    assert costo_actual_inversor({"origen_ficha": "catalogo", "nombre": "Sin precio"}, _CAT, None) is None
    assert costo_actual_inversor({"origen_ficha": "catalogo", "nombre": "No existe"}, _CAT, None) is None


def test_potencia_ac_sin_respaldo_de_la_potencia_fv_maxima():
    assert potencia_ac_kw_inversor({"P_ac_nom_W": 15000.0}) == 15.0
    assert potencia_ac_kw_inversor({"P_ac_nom_kW": 5.0}) == 5.0
    assert potencia_ac_kw_inversor({"P_dc_max_W": 22500.0}) is None


def test_baterias_con_el_precio_vigente_y_aviso_si_cambio():
    dim = {"N_baterias": 4, "costo_unitario_usd": 1000.0, "costo_total_usd": 4000.0}
    r = capex_baterias_vigente(dim, 1200.0)
    assert r["costo_total_usd"] == 4800.0 and r["cambio"] and r["costo_unitario_anterior"] == 1000.0
    r = capex_baterias_vigente(dim, 1000.0)
    assert r["costo_total_usd"] == 4000.0 and not r["cambio"]
    r = capex_baterias_vigente(dim, None)          # sin precio en el catálogo: el del dimensionamiento
    assert r["costo_total_usd"] == 4000.0 and not r["cambio"]
    assert capex_baterias_vigente({}, 1200.0)["costo_total_usd"] == 0.0


def test_financiero_usa_los_inversores_del_diseno_y_el_precio_vigente():
    src = open(os.path.join(_ROOT, "pages", "7_💰_Financiero.py"), encoding="utf-8").read()
    assert "costo_actual_inversor(" in src and 'fin_costo_inv_ms_{' in src
    assert "capex_baterias_vigente(" in src and "costo_actual_inversor" in src
    assert 'or _inversor_dim.get("P_dc_max_W")' not in src     # sin la estimación falsa


def test_presupuesto_usa_el_precio_vigente_de_la_bateria():
    src = open(os.path.join(_ROOT, "pages", "8_💼_Presupuesto.py"), encoding="utf-8").read()
    assert "capex_baterias_vigente(" in src and "costo_actual_inversor" in src
