# -*- coding: utf-8 -*-
"""🗺️ Vista 3D: borrar un inversor no debe dejar sin inversor a los demás
grupos (26-sep-2026, preparando un proyecto real).

Al eliminar INV-2, la lista del selector «Inversor» de cada grupo cambiaba
(de ["", "INV-1", "INV-2"] a ["", "INV-1"]); Streamlit recrea el widget con
la opción por defecto ("") y la página guardaba ese vacío en el diseño: los
grupos que estaban en INV-1 quedaban «sin inversor asignado» (🔴).
"""
import os

from calculos.campos_editor import clave_con_opciones

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_la_clave_cambia_si_cambian_las_opciones():
    a = clave_con_opciones("ms_sup_inv_1", ["", "INV-1", "INV-2"])
    b = clave_con_opciones("ms_sup_inv_1", ["", "INV-1"])
    assert a != b and a.startswith("ms_sup_inv_1") and b.startswith("ms_sup_inv_1")


def test_la_clave_es_estable_con_las_mismas_opciones():
    assert clave_con_opciones("k", ["", "INV-1"]) == clave_con_opciones("k", ["", "INV-1"])


def test_vista_3d_usa_la_clave_con_las_opciones_de_inversor():
    src = open(os.path.join(_ROOT, "pages", "9_🗺️_Vista_3D.py"), encoding="utf-8").read()
    assert 'clave_con_opciones(f"ms_sup_inv_{_suf}", _opciones_inv)' in src
