"""Indicadores de 💰 Financiero que separan autoconsumo y excedentes.

El flujo de caja ya valoraba los excedentes a su propia tarifa (Res. CREG
174/2021), pero dos indicadores de la página valoraban toda la energía a la
tarifa de compra (27-sep-2026, proyecto cliente Bogotá, excedentes a
800 COP/kWh):

- «Ahorro energía año 1» mostraba 6.155 kWh × 1.200 = 7,39 M COP en vez de
  autoconsumo × tarifa + excedentes × tarifa de excedentes.
- «Impacto de la batería» comparaba contra un escenario «sin batería» con
  toda la energía a 1.200 COP: sin batería alguna salía TIR 18,0 % contra
  17,2 %, y «Energía adicional −826 kWh/año» eran en realidad los excedentes.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _num(valor: Any) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return 0.0
    return numero if numero == numero else 0.0      # NaN → 0


def ahorro_anual_cop(energia_kWh: float, frac_exportada: float,
                     tarifa_cop: float, tarifa_excedentes_cop: float) -> dict:
    """Valor del año 1: autoconsumo a la tarifa de compra y excedentes a la suya.

    Es el mismo reparto que usa ``calcular_flujo_caja`` para el año 1 (sin
    degradación ni escalación).
    """
    energia = max(_num(energia_kWh), 0.0)
    frac = min(max(_num(frac_exportada), 0.0), 1.0)
    exportada = energia * frac
    autoconsumo = energia - exportada
    ahorro = autoconsumo * _num(tarifa_cop)
    ingreso = exportada * _num(tarifa_excedentes_cop)
    return {
        "autoconsumo_kWh": autoconsumo,
        "exportada_kWh": exportada,
        "ahorro_autoconsumo_cop": ahorro,
        "ingreso_excedentes_cop": ingreso,
        "total_cop": ahorro + ingreso,
    }


def hay_bateria(capex_bateria_usd: float, metricas_balance: Mapping[str, Any] | None) -> bool:
    """``True`` si el balance incluye una batería (costo o energía descargada)."""
    descargada = _num((metricas_balance or {}).get("E_bateria_total_kWh"))
    return _num(capex_bateria_usd) > 0 or descargada > 0


def escenario_sin_bateria(metricas_balance: Mapping[str, Any] | None) -> dict | None:
    """Energía y fracción exportada del mismo sistema solar sin batería.

    En el balance (mensual u horario) la producción se reparte en autoconsumo
    directo + excedente; la batería solo desplaza excedente a autoconsumo. Sin
    batería: autoconsumo directo = autoconsumo total − descarga de la batería,
    y todo lo demás se exporta. ``None`` si el balance no trae la producción.
    """
    m = metricas_balance or {}
    solar = _num(m.get("E_solar_anual_kWh"))
    if solar <= 0:
        return None
    directo = min(max(_num(m.get("E_autoconsumo_anual_kWh")) - _num(m.get("E_bateria_total_kWh")), 0.0), solar)
    exportada = solar - directo
    return {
        "energia_kWh": solar,
        "autoconsumo_kWh": directo,
        "exportada_kWh": exportada,
        "frac_exportada": exportada / solar,
    }
