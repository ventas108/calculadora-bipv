"""Tabla editable del catálogo de inversores (🔌 Catálogo Inversores PDF › ✏️).

Antes la página comparaba filas con ``getattr(fila, "Vdc_max_V")`` sobre
``itertuples()``, pero pandas renombra a ``_1``, ``_2``… las columnas con
espacios o paréntesis: «💾 Guardar cambios» fallaba con AttributeError y no
se podía corregir ningún inversor (26-sep-2026).
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

# clave del catálogo → (etiqueta de la tabla, columna del Excel)
COLUMNAS_EDICION = {
    "nombre":            ("Modelo",               "Modelo"),
    "Vdc_max":           ("Vdc máx (V)",          "Tension DC Maxima (V)"),
    "Vmppt_min":         ("MPPT mín (V)",         "Rango MPPT Min (V)"),
    "Vmppt_max":         ("MPPT máx (V)",         "Rango MPPT Max (V)"),
    "V_mppt_activo":     ("MPPT activo mín (V)",  "Tension Minima MPPT Activo (V)"),
    "V_arranque":        ("V arranque (V)",       "Tension Arranque (V)"),
    "n_trackers":        ("N Trackers",           "N Trackers"),
    "n_strings_tracker": ("Strings/Tracker",      "N Strings/Tracker"),
    "I_max_tracker":     ("I máx tracker (A)",    "Corriente Maxima Tracker (A)"),
    "Isc_max_tracker":   ("Isc máx tracker (A)",  "Corriente Cortocircuito Max Tracker (A)"),
    "P_ac_nom_kW":       ("P AC nominal (kW)",    "Potencia AC nominal (kW)"),
    "P_dc_max_W":        ("P FV máx (W)",         "Potencia FV Max Recomendada (W)"),
    "costo_usd":         ("Costo (USD)",          "Costo Inversor"),
}


def tabla_edicion(inversores: list[dict]) -> pd.DataFrame:
    return pd.DataFrame([
        {etiqueta: inv.get(clave) for clave, (etiqueta, _) in COLUMNAS_EDICION.items()}
        for inv in inversores
    ])


def _igual(a: Any, b: Any) -> bool:
    vacio_a = a is None or (isinstance(a, float) and math.isnan(a))
    vacio_b = b is None or (isinstance(b, float) and math.isnan(b))
    if vacio_a or vacio_b:
        return vacio_a and vacio_b
    return a == b


def parches_edicion(original: pd.DataFrame, editada: pd.DataFrame) -> list[tuple[str, dict]]:
    """``[(modelo original, {columna Excel: valor nuevo})]`` de las filas cambiadas."""
    parches = []
    for i in range(len(original)):
        fila_o, fila_e = original.iloc[i], editada.iloc[i]
        parche = {}
        for etiqueta, columna_excel in COLUMNAS_EDICION.values():
            nuevo = fila_e[etiqueta]
            if not _igual(fila_o[etiqueta], nuevo):
                parche[columna_excel] = None if (isinstance(nuevo, float) and math.isnan(nuevo)) else nuevo
        if parche:
            parches.append((str(fila_o["Modelo"]), parche))
    return parches
