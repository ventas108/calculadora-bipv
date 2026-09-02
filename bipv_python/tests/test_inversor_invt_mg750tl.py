# -*- coding: utf-8 -*-
"""
Ancla real: el inversor INVT MG750TL (2-sep-2026) debe estar disponible en el
catálogo real de la app, con los valores reales verificados contra 2 fuentes
(ficha oficial INVT 2020.07 V1.0 + pantalla real de PVsyst 8.1.5 usada en la
validación del motor CdTe). Ver datos/agregar_inversor_invt_mg750tl.py y
DIAGNOSTICO_JRC_HULD_PRIMARIO_CDTE.md / DIAGNOSTICO_RECOMBINACION_CDTE.md
(el mismo inversor de esas corridas reales).
"""
from datos.catalogo_inversores_excel import cargar_catalogo_inversores


def test_mg750tl_esta_en_el_catalogo_real():
    cat = cargar_catalogo_inversores()
    assert "MG750TL" in cat, (
        "MG750TL no está en inversores_catalogo.xlsx -- "
        "correr datos/agregar_inversor_invt_mg750tl.py"
    )


def test_mg750tl_valores_reales_verificados():
    cat = cargar_catalogo_inversores()
    inv = cat["MG750TL"]

    # Coinciden EXACTO en la ficha oficial INVT y la pantalla real de PVsyst.
    assert inv["Vdc_max"] == 400.0
    assert inv["P_ac_nom_W"] == 750.0
    assert inv["P_ac_nom_kW"] == 0.75

    # Ventana MPPT: la de la pantalla real de PVsyst (la corrida validada),
    # no la más amplia de la ficha oficial 2020 (50-400V) -- ver docstring
    # de agregar_inversor_invt_mg750tl.py.
    assert inv["Vmppt_min"] == 60.0
    assert inv["Vmppt_max"] == 350.0

    # Real, de la ficha oficial ("Max. DC input power").
    assert inv["P_dc_max_W"] == 900.0

    assert inv["n_trackers"] == 1.0
    assert inv["es_hibrido"] is False
    assert inv["marca"] == "INVT Solar Technology"
