# -*- coding: utf-8 -*-
"""Límite del Voc en frío: el menor entre el inversor y el módulo.

Spec ``03-dimensionamiento/tension-maxima-modulo`` (1-oct-2026). La tensión
máxima de sistema del módulo (VSYS en la ficha, aislamiento IEC 61730) es un
límite propio: un string no puede superarla aunque el inversor aguante más.
Caso real: Teusaquillo, ASP-ST1-T40 (1.000 V) con un inversor de 1.100 V;
8 en serie daban 1.002 V a 0 °C y la app los aprobaba. Módulo puro.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

TEXTO_LIMITE = {
    "modulo": "tensión máxima del módulo",
    "inversor": "Vdc máximo del inversor",
}


def _positivo(valor: Any) -> float | None:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    return v if v == v and v > 0 else None


def v_sistema_modulo(panel: Mapping[str, Any] | None) -> float | None:
    """Tensión máxima de sistema del módulo (V) o ``None`` si la ficha no la trae."""
    return _positivo((panel or {}).get("V_sistema_max"))


def limite_voc(panel: Mapping[str, Any] | None, inversor: Mapping[str, Any] | None) -> dict:
    """``{limite_v, origen, vdc_inversor_v, v_sistema_modulo_v}``.

    ``origen`` = ``"modulo"`` solo si el módulo es estrictamente menor que el
    inversor (en empate manda el inversor, como antes); ``None`` sin datos.
    """
    vdc = _positivo((inversor or {}).get("Vdc_max"))
    vsys = v_sistema_modulo(panel)
    if vsys and (vdc is None or vsys < vdc):
        limite, origen = vsys, "modulo"
    elif vdc:
        limite, origen = vdc, "inversor"
    else:
        limite, origen = None, None
    return {"limite_v": limite, "origen": origen, "vdc_inversor_v": vdc, "v_sistema_modulo_v": vsys}
