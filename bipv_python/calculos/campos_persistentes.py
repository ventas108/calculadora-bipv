"""Campos de 💰 Financiero que sobreviven al cambio de página y se guardan.

Streamlit borra el valor de un campo con ``key`` cuando se abre otra página, y
un campo sin ``key`` vuelve a su ``value=`` fijo en cada visita. Así, la
«Tarifa de excedentes» volvía a la tarifa de compra (1.200 en vez de 800) al
ir a 🏠 Proyecto a guardar, y WACC, escalaciones, horizonte, costos, O&M e
impuesto de renta volvían a sus valores por defecto; ninguno se guardaba con
el proyecto (27-sep-2026).

El valor vive en una clave de datos normal (se guarda con el proyecto) y el
campo usa una clave temporal ``_w_<clave>`` que se vuelve a llenar desde el
dato cuando falta o cuando el dato cambió fuera del campo (al cargar un
proyecto), igual que la tarifa de compra.
"""
from __future__ import annotations

from collections.abc import Callable, MutableMapping
from typing import Any

from calculos.campos_editor import sincronizar_campo


def clave_widget(clave: str) -> str:
    return f"_w_{clave}"


def valor_inicial(estado: MutableMapping[str, Any], clave: str, defecto: float,
                  minimo: float, maximo: float) -> float:
    """Dato guardado (o ``defecto``) con el tipo de ``defecto`` y dentro del rango."""
    try:
        valor = type(defecto)(estado.get(clave, defecto))
    except (TypeError, ValueError):
        valor = defecto
    return min(max(valor, type(defecto)(minimo)), type(defecto)(maximo))


def campo_persistente(estado: MutableMapping[str, Any], widget: Callable[..., Any],
                      etiqueta: str, clave: str, defecto: float, *,
                      min_value: float, max_value: float, **kwargs: Any) -> Any:
    """Dibuja ``widget`` (``st.slider``/``st.number_input``) ligado al dato ``clave``."""
    w = clave_widget(clave)
    sincronizar_campo(estado, w, valor_inicial(estado, clave, defecto, min_value, max_value))
    valor = widget(etiqueta, min_value=min_value, max_value=max_value, key=w, **kwargs)
    estado[clave] = valor
    return valor
