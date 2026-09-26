"""Precios vigentes de los catálogos para 💰 Financiero y 💼 Presupuesto.

Financiero y Presupuesto usaban copias de precios tomadas antes (al abrir
📐 Dimensionamiento, al publicar en Vista 3D o al pulsar «Dimensionar
batería»): un precio cambiado después en el catálogo no llegaba, sin aviso
(26-sep-2026). Estas funciones buscan el precio vigente; si el catálogo no
lo trae, devuelven ``None`` y la página lo dice en vez de inventarlo.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


def _positivo(valor: Any) -> float | None:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if math.isfinite(numero) and numero > 0 else None


def nombre_catalogo_inversor(inversor: Mapping[str, Any], nombre_proyecto: str | None) -> str | None:
    """Nombre en el catálogo de un inversor de ``multisup_inversores``."""
    origen = inversor.get("origen_ficha")
    if origen == "catalogo":
        return inversor.get("nombre") or None
    if origen == "proyecto":
        return nombre_proyecto or inversor.get("nombre") or None
    return None          # manual: no hay ficha de catálogo


def costo_actual_inversor(inversor: Mapping[str, Any], catalogo: Mapping[str, Any],
                          nombre_proyecto: str | None) -> float | None:
    """Precio USD/unidad vigente del inversor, o ``None`` si el catálogo no lo trae."""
    nombre = nombre_catalogo_inversor(inversor, nombre_proyecto)
    ficha = (catalogo or {}).get(nombre) if nombre else None
    return _positivo((ficha or {}).get("costo_usd"))


def potencia_ac_kw_inversor(ficha: Mapping[str, Any]) -> float | None:
    """Potencia AC nominal en kW; ``None`` si falta (nunca la potencia FV máxima)."""
    p_w = _positivo(ficha.get("P_ac_nom_W"))
    if p_w is not None:
        return p_w / 1000.0
    return _positivo(ficha.get("P_ac_nom_kW"))


def capex_baterias_vigente(bateria_dim: Mapping[str, Any] | None,
                           costo_catalogo_usd: Any) -> dict:
    """Costo del banco con el precio vigente del catálogo.

    ``cambio`` indica que el precio del catálogo ya no es el que se usó al
    dimensionar (la página lo avisa). Sin precio en el catálogo se conserva el
    del dimensionamiento.
    """
    dim = bateria_dim or {}
    n = int(dim.get("N_baterias") or 0)
    anterior = _positivo(dim.get("costo_unitario_usd"))
    vigente = _positivo(costo_catalogo_usd)
    unitario = vigente if vigente is not None else anterior
    if n <= 0 or unitario is None:
        total = _positivo(dim.get("costo_total_usd")) or 0.0
    else:
        total = n * unitario
    return {
        "N_baterias": n,
        "costo_unitario_usd": unitario,
        "costo_unitario_anterior": anterior,
        "costo_total_usd": float(total),
        "cambio": vigente is not None and anterior is not None and abs(vigente - anterior) > 1e-9,
    }
