# -*- coding: utf-8 -*-
"""Revisión de la ficha de un inversor del catálogo y margen de tensión DC.

Spec ``07-informes/reporte-granja-completo`` (1-oct-2026). Caso real: el
catálogo traía el Growatt MAX 100KTL3 LV con 1.500 V DC y MPPT hasta 1.300 V,
pero su ficha oficial dice 1.100 V y 180–1.000 V. Con esos datos la app daba
🟢 a 28 módulos en serie (Voc en frío 1.386 V). Estas reglas no reemplazan la
ficha del fabricante: marcan datos que no pueden ser ciertos a la vez para que
el diseñador los revise antes de dimensionar. Módulo puro: sin Streamlit.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

# Inversores «LV» de string (salida 230/400 V): 1.100 V DC como máximo.
VDC_MAX_LV = 1100.0
# Margen del Voc en frío: el mismo 7,5 % del optimizador de 📐 Dimensionamiento
# (UMBRAL_ALERTA_PCT); se repite aquí para no importar ese módulo.
MARGEN_ALERTA_PCT = 7.5
_PATRON_LV = re.compile(r"(?<![A-Za-z])LV(?![A-Za-z])")


def _num(valor: Any) -> float | None:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    return v if v == v and v > 0 else None


def alertas_ficha_inversor(inv: Mapping[str, Any] | None) -> list[dict]:
    """Datos de la ficha que se contradicen: ``[{id, nivel, texto}]`` (vacío si todo cuadra)."""
    if not inv:
        return []
    nombre = str(inv.get("nombre") or "")
    vdc = _num(inv.get("Vdc_max"))
    v_min = _num(inv.get("Vmppt_min"))
    v_max = _num(inv.get("Vmppt_max"))
    v_act = _num(inv.get("Vmppt_activo_min") or inv.get("V_mppt_activo"))
    i_op = _num(inv.get("I_max_tracker"))
    i_sc = _num(inv.get("Isc_max_tracker"))
    out: list[dict] = []
    if vdc and v_max and v_max > vdc:
        out.append({"id": "mppt_sobre_vdc", "nivel": "🔴", "texto":
                    f"El rango MPPT llega a {v_max:,.0f} V y la tensión DC máxima es {vdc:,.0f} V: el MPPT "
                    "no puede superar la tensión máxima. Revisa la ficha del inversor."})
    if v_max and ((v_min and v_min >= v_max) or (v_act and v_act >= v_max)):
        out.append({"id": "mppt_invertido", "nivel": "🔴", "texto":
                    f"El mínimo del rango MPPT ({max(v_min or 0, v_act or 0):,.0f} V) no es menor que el "
                    f"máximo ({v_max:,.0f} V). Revisa la ficha del inversor."})
    if i_op and i_sc and i_sc < i_op:
        out.append({"id": "isc_menor", "nivel": "🟠", "texto":
                    f"La corriente de cortocircuito máxima por MPPT ({i_sc:g} A) es menor que la de "
                    f"operación ({i_op:g} A); en las fichas siempre es igual o mayor. Revisa la ficha."})
    if vdc and vdc > VDC_MAX_LV and _PATRON_LV.search(nombre):
        out.append({"id": "lv_1500", "nivel": "🟠", "texto":
                    f"«{nombre}» es un inversor LV (salida 230/400 V) y el catálogo dice {vdc:,.0f} V DC. "
                    f"Los inversores LV de string trabajan hasta {VDC_MAX_LV:,.0f} V DC: confirma la tensión "
                    "máxima y el rango MPPT con la ficha oficial antes de dimensionar."})
    return out


def margen_voc(voc_frio: Any, inv: Mapping[str, Any] | None) -> dict | None:
    """Margen del Voc en frío del string frente a la tensión DC máxima del inversor."""
    voc = _num(voc_frio)
    vdc = _num((inv or {}).get("Vdc_max"))
    if not voc or not vdc:
        return None
    margen = vdc - voc
    return {"voc_v": voc, "vdc_max_v": vdc, "margen_v": margen, "margen_pct": 100.0 * margen / vdc,
            "nivel": "🔴" if margen < 0 else ("🟠" if 100.0 * margen / vdc < MARGEN_ALERTA_PCT else "🟢")}
