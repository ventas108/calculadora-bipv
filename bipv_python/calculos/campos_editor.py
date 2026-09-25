"""Sincronización de los campos de los editores de Vista 3D con sus datos.

Los campos del editor no reciben ``value=``/``index=`` (en Streamlit la
identidad del widget incluye ese valor inicial y el campo se recreaba al
editar). Su estado se inicializa desde los datos y solo se resincroniza si el
dato cambió FUERA del campo (p. ej. al cargar un proyecto).
"""
from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any


def sincronizar_campo(estado: MutableMapping[str, Any], clave: str, valor_datos: Any) -> Any:
    """Valor del campo ``clave`` para esta ejecución.

    La referencia ``_ref_<clave>`` guarda el valor que el campo tenía al final
    de la ejecución anterior, que es el que la página guardó en los datos. Si
    los datos no coinciden con ella, cambiaron fuera del campo y el campo se
    actualiza; si coinciden, se respeta lo que el usuario escribió.

    Corregido 25-sep-2026: la referencia guardaba el dato de ENTRADA, así que
    un segundo cambio seguido del mismo campo se revertía (el tercero sí
    quedaba).
    """
    ref = f"_ref_{clave}"
    if clave not in estado or estado.get(ref) != valor_datos:
        estado[clave] = valor_datos
    estado[ref] = estado[clave]
    return estado[clave]
