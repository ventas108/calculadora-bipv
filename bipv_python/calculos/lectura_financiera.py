"""Lecturas de 💰 Financiero para explicar el resultado al cliente.

Prueba del proyecto cliente (27-sep-2026, 8,36 kWp, tarifa 1.200 COP/kWh):

- La tabla de sensibilidad decía «Umbral mínimo 600 COP/kWh», pero la fila
  de 650 ya tenía VPN negativo: la búsqueda solo probaba precios de 50 a 600
  COP/kWh y, si el umbral era mayor, se quedaba en 600. El real era ~677.
- El LCOE (1.564 COP/kWh) se comparaba con la tarifa del año 1 (1.200) y
  parecía que el proyecto no se pagaba, aunque el VPN era positivo: la tarifa
  sube cada año y los excedentes tienen su propia tarifa. La comparación
  correcta es con el valor nivelado de la energía, descontado igual que el LCOE.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any


def umbral_vpn_cero(vpn_de: Callable[[float], float | None], lo: float = 50.0,
                    hi: float = 600.0, max_hi: float = 100_000.0,
                    iteraciones: int = 40) -> float | None:
    """Precio (COP/kWh) al que el VPN pasa por cero, o ``None`` si no lo alcanza.

    Si en ``hi`` el VPN todavía es negativo, amplía el rango (duplicando) hasta
    ``max_hi`` antes de buscar. Si ya es positivo en ``lo``, devuelve ``lo``.
    """
    def positivo(t: float) -> bool:
        v = vpn_de(t)
        return v is not None and v > 0

    if positivo(lo):
        return lo
    while not positivo(hi):
        if hi >= max_hi:
            return None
        lo, hi = hi, min(hi * 2, max_hi)
    for _ in range(iteraciones):
        medio = (lo + hi) / 2
        if positivo(medio):
            hi = medio
        else:
            lo = medio
    return (lo + hi) / 2


def valor_nivelado_energia(flujos: Iterable[Mapping[str, Any]], tasa_descuento: float,
                           tipo_cambio: float) -> dict | None:
    """Valor promedio descontado de cada kWh (lo que se ahorra o cobra), como el LCOE.

    Σ ingreso_t/(1+r)^t ÷ Σ producción_t/(1+r)^t. Incluye la escalación de la
    tarifa y los excedentes a su tarifa. Si el LCOE es menor, el proyecto se
    paga a la tasa de descuento (VPN sin Ley 1715 > 0).
    """
    ingreso = produccion = 0.0
    for f in flujos:
        t = int(f.get("año") or 0)
        if t <= 0:
            continue
        factor = (1 + tasa_descuento) ** t
        ingreso += float(f.get("ingreso_energia_usd") or 0.0) / factor
        produccion += float(f.get("produccion_kWh") or 0.0) / factor
    if produccion <= 0:
        return None
    usd = ingreso / produccion
    return {"usd_kWh": usd, "cop_kWh": usd * tipo_cambio}


# Separación vertical entre etiquetas (fracción de la altura de la gráfica):
# una fila de texto a 440 px de alto.
_PASO_ETIQUETA = 0.08


def etiquetas_payback(lineas: Iterable[tuple[str, float | None, str]]) -> list[dict]:
    """Posición de las etiquetas de payback de la gráfica de flujo acumulado.

    Antes cada etiqueta se ponía junto a su línea vertical («top right», «top
    left»…) y, con paybacks cercanos (6,7 y 10,0 años en el proyecto cliente),
    los textos se encimaban. Aquí se ordenan por año y cada una baja una fila,
    todas a la derecha de su línea: nunca comparten altura.

    ``lineas``: ``(texto, año, color)``; se omiten las que no tienen payback.
    Devuelve ``{texto, x, y, color}`` con ``y`` en fracción de la gráfica.
    """
    validas = sorted(((t, float(x), c) for t, x, c in lineas if x), key=lambda l: l[1])
    return [{"texto": t, "x": x, "y": 0.98 - i * _PASO_ETIQUETA, "color": c}
            for i, (t, x, c) in enumerate(validas)]


def rotulo_modulos(sistema: Mapping[str, Any] | None, n_modulos: int, panel_nombre: str) -> str:
    """Módulos del proyecto para el mensaje final de 💰 Financiero.

    Con el sistema multi-superficie publicado (``multisup_sistema``) se nombra
    cada panel con su cantidad: antes decía «116 módulos ASP-ST1-T40» (el panel
    de 📐 Dimensionamiento) para 112 ASP-ST1-T40 + 4 SPR-E20-327.
    """
    por_panel = [p for p in ((sistema or {}).get("por_panel") or []) if p.get("modulos")]
    if len(por_panel) > 1:
        return " + ".join(f"{int(p['modulos'])} {p['panel']}" for p in por_panel)
    if len(por_panel) == 1:
        return f"{int(por_panel[0]['modulos'])} módulos {por_panel[0]['panel']}"
    return f"{int(n_modulos)} módulos {panel_nombre or '—'}"


def mensaje_resumen_financiero(ciudad: str, rotulo: str, capex_neto_usd: float, tipo_cambio: float,
                               metricas: Mapping[str, Any], vne_cop_kWh: float | None, *,
                               vpn_positivo: bool) -> str:
    """Mensaje final de 💰 Financiero.

    Antes era una sola expresión `"…" f"TIR…" if tir else "TIR N/A" f"VPN…" + …`:
    el `if/else` abarcaba todo, así que con TIR el mensaje terminaba en
    «TIR: 16.8% |» sin VPN, Payback ni LCOE (28-sep-2026). Ahora cada parte se
    arma por separado. El «$» va escapado (``\\$``): Streamlit toma el texto
    entre dos «$» como fórmula LaTeX y deformaba el mensaje (28-sep-2026).
    """
    tir = metricas.get("tir_pct")
    payback = metricas.get("payback_simple")
    lcoe = metricas["lcoe_cop_kWh"]
    partes = [
        f"{'✅' if vpn_positivo else '⚠️'} **{ciudad}** — {rotulo}",
        f"CAPEX neto: **USD {capex_neto_usd:,.0f}** (\\$ {capex_neto_usd * tipo_cambio / 1e6:.2f} M COP)",
        f"TIR: **{tir:.1f}%**" if tir else "TIR: **N/A**",
        f"VPN: **USD {metricas['vpn_usd']:,.0f}** (\\$ {metricas['vpn_usd'] * tipo_cambio / 1e6:.1f} M COP)",
        f"Payback: **{payback:.1f} años**" if payback else "Payback: **> horizonte**",
        f"LCOE: **{lcoe:.0f} COP/kWh**" + (
            f" ({'<' if lcoe < vne_cop_kWh else '>'} valor nivelado de la energía "
            f"{vne_cop_kWh:.0f} COP/kWh)" if vne_cop_kWh else ""),
    ]
    return " | ".join(partes)
