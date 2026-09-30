# -*- coding: utf-8 -*-
"""NOCT y γ de 🔆 Motor Óptico frente a la ficha del panel.

Spec ``05-perdidas-y-temperatura/motor-optico-ficha-termica`` (30-sep-2026).
El auto-llenado del Motor Óptico corre solo cuando cambia el panel; al abrir
un proyecto guardado se restauran sus valores viejos aunque no coincidan con
la ficha. 📊 Producción usa el NOCT del Motor Óptico para la temperatura de
celda (el γ lo toma del modelo del panel), así que un NOCT distinto cambia la
energía en silencio.

Módulo puro: sin Streamlit.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

TOL_NOCT_C = 0.5
TOL_GAMMA_PCT = 0.005


def _num(valor: Any) -> float | None:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    return v if v != 0 else None


def ficha_termica(panel: Mapping[str, Any] | None) -> dict:
    """NOCT (°C) y γ (%/°C) de la ficha; γ con la prioridad de ``modelo_iv``."""
    panel = panel or {}
    gamma = None
    for clave in ("Tk_gamma", "gamma_mp", "beta_mp"):
        gamma = _num(panel.get(clave))
        if gamma is not None:
            break
    return {"noct": _num(panel.get("NOCT")), "gamma_pct": gamma}


def diferencias_ficha(noct_motor: float | None, gamma_motor_pct: float | None,
                      panel: Mapping[str, Any] | None) -> list[dict]:
    """Campos del Motor Óptico que no coinciden con la ficha del panel.

    Cada elemento: ``{campo, motor, ficha, afecta_energia}``. El NOCT sí
    cambia la energía de Producción; el γ solo el térmico informativo del
    Motor Óptico.
    """
    ficha = ficha_termica(panel)
    salida = []
    if ficha["noct"] is not None and noct_motor is not None \
            and abs(float(noct_motor) - ficha["noct"]) > TOL_NOCT_C:
        salida.append({"campo": "NOCT", "motor": float(noct_motor), "ficha": ficha["noct"],
                       "afecta_energia": True})
    if ficha["gamma_pct"] is not None and gamma_motor_pct is not None \
            and abs(float(gamma_motor_pct) - ficha["gamma_pct"]) > TOL_GAMMA_PCT:
        salida.append({"campo": "γ", "motor": float(gamma_motor_pct), "ficha": ficha["gamma_pct"],
                       "afecta_energia": False})
    return salida


def texto_aviso_ficha(diferencias: list[Mapping[str, Any]], panel_nombre: str, *,
                      k_bipv: float = 1.0) -> str:
    """Aviso 🟠 en palabras simples, con el efecto en la temperatura de celda."""
    if not diferencias:
        return ""
    partes = []
    for d in diferencias:
        if d["campo"] == "NOCT":
            dt = (d["motor"] - d["ficha"]) / 800.0 * 1000.0 * float(k_bipv)
            sentido = "más fría" if dt < 0 else "más caliente"
            partes.append(
                f"**NOCT {d['motor']:g} °C** (la ficha dice **{d['ficha']:g} °C**): con 1000 W/m² "
                f"la celda sale {abs(dt):.1f} °C {sentido} y 📊 Producción calcula "
                + ("más" if dt < 0 else "menos") + " energía de la real"
            )
        else:
            partes.append(
                f"**γ {d['motor']:g} %/°C** (la ficha dice **{d['ficha']:g} %/°C**): cambia la "
                "pérdida térmica que muestra el Motor Óptico (la energía usa el γ del panel)"
            )
    return (f"🟠 Los datos térmicos del Motor Óptico no coinciden con la ficha de "
            f"**{panel_nombre}**: " + "; ".join(partes) + ". Suele pasar al abrir un proyecto "
            "guardado con valores viejos. Presiona **«Usar los de la ficha»** en 🔆 Motor Óptico "
            "y vuelve a calcular la cascada, salvo que tengas un dato medido distinto.")
