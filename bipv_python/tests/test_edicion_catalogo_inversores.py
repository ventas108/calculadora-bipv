# -*- coding: utf-8 -*-
"""«💾 Guardar cambios» de la tabla del catálogo de inversores (26-sep-2026).

Antes se leía cada fila con ``getattr(fila, "Vdc_max_V")`` sobre
``itertuples()``; pandas renombra esas columnas a ``_1``, ``_2``… y guardar
fallaba con AttributeError.
"""
import math

from calculos.edicion_catalogo_inversores import parches_edicion, tabla_edicion

_GROWATT = {"nombre": "Growatt MID15KTL3-X", "Vdc_max": 1100.0, "Vmppt_min": 140.0,
            "Vmppt_max": 1000.0, "V_mppt_activo": 293.0, "V_arranque": None,
            "n_trackers": 2.0, "n_strings_tracker": 8.0, "I_max_tracker": 27.5,
            "Isc_max_tracker": 33.5, "P_ac_nom_kW": 15.0, "P_dc_max_W": 22500.0,
            "costo_usd": None}
_OTRO = {"nombre": "MID 15KTL3-X", "Vdc_max": 1100.0, "P_ac_nom_kW": None}


def test_sin_cambios_no_hay_parches_aunque_haya_celdas_vacias():
    df = tabla_edicion([_GROWATT, _OTRO])
    assert parches_edicion(df, df.copy()) == []


def test_corregir_el_growatt_con_la_ficha_oficial():
    orig = tabla_edicion([_GROWATT, _OTRO])
    ed = orig.copy()
    ed.loc[0, ["MPPT mín (V)", "MPPT activo mín (V)", "V arranque (V)", "Strings/Tracker",
               "I máx tracker (A)", "Isc máx tracker (A)"]] = [200.0, 200.0, 250.0, 2.0, 27.0, 33.8]
    parches = parches_edicion(orig, ed)
    assert parches == [("Growatt MID15KTL3-X", {
        "Rango MPPT Min (V)": 200.0, "Tension Minima MPPT Activo (V)": 200.0,
        "Tension Arranque (V)": 250.0, "N Strings/Tracker": 2.0,
        "Corriente Maxima Tracker (A)": 27.0, "Corriente Cortocircuito Max Tracker (A)": 33.8,
    })]


def test_completar_la_potencia_ac_de_un_inversor_antiguo():
    orig = tabla_edicion([_GROWATT, _OTRO])
    ed = orig.copy()
    ed.loc[1, "P AC nominal (kW)"] = 15.0
    assert parches_edicion(orig, ed) == [("MID 15KTL3-X", {"Potencia AC nominal (kW)": 15.0})]


def test_borrar_un_valor_lo_deja_vacio_y_no_nan():
    orig = tabla_edicion([_GROWATT])
    ed = orig.copy()
    ed.loc[0, "Costo (USD)"] = 900.0
    ed2 = ed.copy()
    ed2.loc[0, "Costo (USD)"] = float("nan")
    (_, parche), = parches_edicion(ed, ed2)
    assert parche == {"Costo Inversor": None}
    assert not any(isinstance(v, float) and math.isnan(v) for v in parche.values())
