"""Potencia AC nominal de los inversores del catálogo.

La potencia AC nominal («Rated AC output power») sale SOLO de la ficha del
fabricante. Antes el catálogo la estimaba como 96 % de la «Potencia FV máx.
recomendada»; con el Growatt MID15KTL3-X eso daba 21.600 W en vez de
15.000 W y la relación DC/AC salía 0,79 🟡 en vez de 1,13 🟢 (26-sep-2026).
Sin el dato, las comprobaciones que lo necesitan quedan «no evaluables» y
la app explica dónde completarlo.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

# Un cargador off-grid puro no entrega potencia a la red: no se le exige.
ARQUITECTURAS_SIN_P_AC = ("Cargador off-grid puro",)

MENSAJE_SIN_POTENCIA_AC = (
    "La ficha de este inversor no tiene la potencia AC nominal en el catálogo, así que no se "
    "calcula la relación DC/AC (la app ya no la estima: daba valores falsos). Complétala en "
    "🔌 Catálogo Inversores PDF › ✏️ Editar / Eliminar, columna «P AC nominal (kW)», con el "
    "dato «Rated AC output power» de la ficha, y vuelve a elegir la ficha del inversor."
)


def potencia_ac_w(p_ac_kw: Any) -> float | None:
    """Potencia AC nominal en W desde el dato de la ficha en kW; ``None`` si falta."""
    try:
        valor = float(p_ac_kw)
    except (TypeError, ValueError):
        return None
    return valor * 1000.0 if math.isfinite(valor) and valor > 0 else None


def potencia_ac_requerida(arquitectura: str | None) -> bool:
    return (arquitectura or "") not in ARQUITECTURAS_SIN_P_AC


def error_potencia_ac(arquitectura: str | None, p_ac_kw: Any) -> str | None:
    """Mensaje para no guardar un inversor sin potencia AC, o ``None`` si está bien."""
    if not potencia_ac_requerida(arquitectura) or potencia_ac_w(p_ac_kw) is not None:
        return None
    return (
        "La **Potencia AC nominal (kW)** es obligatoria: búscala en la ficha como «Rated AC "
        "output power» o «Potencia nominal CA». Sin ella la relación DC/AC no se puede "
        "calcular (no uses la potencia FV máxima: es otro dato)."
    )


def inversores_sin_potencia_ac(catalogo: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Nombres de los inversores del catálogo que no tienen potencia AC de ficha."""
    return [
        str(inv.get("nombre") or clave)
        for clave, inv in catalogo.items()
        if potencia_ac_w((inv.get("P_ac_nom_W") or 0) / 1000.0) is None
    ]
