# -*- coding: utf-8 -*-
"""Formatos de presentación de 📊 Producción (29-sep-2026).

Solo presentación: ninguna función de este archivo cambia un kWh.
"""

# Formato de cada columna de `res["df_mensual"]` (los dos motores devuelven
# las mismas columnas). Una columna nueva sin formato aquí la detecta
# tests/test_produccion_presentacion.py.
FORMATO_TABLA_MENSUAL = {
    "E_dc (kWh)":             "{:,.0f}",
    "E_ac (kWh)":             "{:,.0f}",
    "Pérdida T° (kWh)":       "{:,.0f}",
    "Recorte inversor (kWh)": "{:,.0f}",
    "Producción (kWh/kWp)":   "{:.1f}",
}


def gamma_ficha(panel: dict) -> float | None:
    """γ de potencia de la ficha (%/°C), o None si la ficha no lo trae."""
    g = panel.get("Tk_gamma")
    return float(g) if g not in (None, "") else None


def texto_gamma(tk_gamma_pct) -> str:
    """Coeficiente de potencia γ (%/°C) para mostrar; «—» si la ficha no lo trae."""
    if tk_gamma_pct is None:
        return "—"
    return f"{float(tk_gamma_pct):.4g}"
