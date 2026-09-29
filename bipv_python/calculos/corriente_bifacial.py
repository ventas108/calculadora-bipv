# -*- coding: utf-8 -*-
"""Corriente de diseño DC de paneles bifaciales (Isc en BNPI).

Spec ``07-informes/unifilar-retie-bifacial-cruce`` (29-sep-2026).

Con panel bifacial, IEC 62548-1 pide dimensionar conductores, fusibles y el
límite de corriente del MPPT con la corriente en la irradiancia de placa
bifacial (BNPI, IEC TS 60904-1-2: 1000 W/m² al frente + 135 W/m² atrás):

    Isc_BNPI = Isc × (1 + φ × 135 / 1000)

JAM66D46-720/LB (φ = 0.80): 18.59 A × 1.108 = 20.60 A por string.

φ efectivo (mismo criterio que 🔆 Motor Óptico / 🗺️ Vista 3D):
- modelo bifacial activo → bifacialidad × factor de vista trasera (fachada
  adosada → 0);
- modelo apagado pero panel bifacial en el catálogo → bifacialidad del panel
  (lado seguro: en obra la cara trasera recibe luz igual);
- panel monofacial → 0.
Solo cambia la corriente: Voc y Vmp del string no dependen de esto.
"""
from __future__ import annotations

from typing import Any, Mapping

BNPI_TRASERA_W_M2 = 135.0
_BNPI_FRONTAL_W_M2 = 1000.0


def factor_isc_bifacial(phi: float | None) -> float:
    """1 + φ × 0.135, con φ recortado a 0–1."""
    try:
        p = float(phi or 0.0)
    except (TypeError, ValueError):
        p = 0.0
    p = min(max(p, 0.0), 1.0)
    return 1.0 + p * BNPI_TRASERA_W_M2 / _BNPI_FRONTAL_W_M2


def _phi_panel(panel: Mapping[str, Any] | None) -> float:
    try:
        pct = float((panel or {}).get("bifacialidad_pct") or 0.0)
    except (TypeError, ValueError):
        pct = 0.0
    return min(max(pct / 100.0, 0.0), 1.0)


def _phi_cfg(cfg: Mapping[str, Any] | None) -> float:
    cfg = cfg or {}
    try:
        bif = float(cfg.get("bifacialidad", 0.0) or 0.0)
        vista = float(cfg.get("factor_vista_trasera", 1.0))
    except (TypeError, ValueError):
        return 0.0
    return min(max(bif * vista, 0.0), 1.0)


def phi_proyecto(estado: Mapping[str, Any], panel: Mapping[str, Any] | None) -> tuple[float, str]:
    """``(φ, origen)`` del proyecto de superficie única."""
    cfg = estado.get("bifacial_cfg") or None
    if estado.get("bifacial_activo") and cfg:
        return _phi_cfg(cfg), "modelo"
    phi = _phi_panel(panel)
    return (phi, "panel") if phi > 0 else (0.0, "monofacial")


def phi_superficie(superficie: Mapping[str, Any], estado: Mapping[str, Any],
                   panel: Mapping[str, Any] | None) -> tuple[float, str]:
    """``(φ, origen)`` de una superficie de 🗺️ Vista 3D (con su montaje)."""
    from calculos.multi_superficie import config_bifacial_superficie, parametros_poa_estado

    _, cfg, usar = parametros_poa_estado(estado)
    if usar:
        return _phi_cfg(config_bifacial_superficie(dict(superficie), cfg, True)), "modelo"
    phi = _phi_panel(panel)
    return (phi, "panel") if phi > 0 else (0.0, "monofacial")


def panel_para_corriente(panel: Mapping[str, Any], phi: float | None) -> dict:
    """Copia del panel con ``Isc_stc`` en BNPI (para conductores, fusibles y
    límite de corriente del MPPT). No muta el original."""
    salida = dict(panel)
    factor = factor_isc_bifacial(phi)
    isc = salida.get("Isc_stc")
    salida["Isc_stc_frontal"] = isc
    salida["factor_bifacial"] = factor
    if isc is not None:
        try:
            salida["Isc_stc"] = float(isc) * factor
        except (TypeError, ValueError):
            pass
    return salida


def texto_origen(origen: str, phi: float) -> str:
    """Explicación corta para la pantalla."""
    if origen == "modelo":
        return f"bifacialidad efectiva {phi:.2f} del modelo bifacial (☀️ Recurso Solar / 🗺️ Vista 3D)"
    if origen == "panel":
        return (f"bifacialidad {phi:.2f} de la ficha del panel: el modelo bifacial está apagado, "
                "pero en obra la cara trasera recibe luz (lado seguro)")
    return "panel monofacial"
