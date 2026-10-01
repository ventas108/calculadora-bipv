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


def sincronizar_con_fuente(estado: MutableMapping[str, Any], clave: str,
                           valor_fuente: Any, respaldo: Any) -> Any:
    """Valor de un campo que sigue a una fuente externa (p. ej. el catálogo)
    sin pisar lo que escribió el usuario.

    El campo toma ``valor_fuente`` la primera vez y cada vez que la fuente
    CAMBIA; mientras no cambie, se respeta lo que el usuario escribió. Sin
    valor en la fuente se usa ``respaldo``. A diferencia de
    ``sincronizar_campo``, aquí el campo no se guarda de vuelta en la fuente
    (💰 Financiero no escribe el catálogo), 26-sep-2026.
    """
    ref = f"_fuente_{clave}"
    if clave not in estado or (ref in estado and estado[ref] != valor_fuente
                               and valor_fuente is not None):
        estado[clave] = valor_fuente if valor_fuente is not None else respaldo
    estado[ref] = valor_fuente
    return estado[clave]


def clave_con_opciones(base: str, opciones) -> str:
    """Clave de un selector que cambia cuando cambian sus opciones.

    Si la lista de opciones de un ``selectbox`` cambia (p. ej. se borra un
    inversor), Streamlit lo recrea con la opción por defecto aunque la clave
    tenga un valor válido. Con una clave distinta por lista de opciones, el
    campo nuevo se inicializa desde los datos (``sincronizar_campo``) y
    conserva la selección (26-sep-2026).
    """
    import zlib

    firma = zlib.crc32("\x1f".join(map(str, opciones)).encode("utf-8"))
    return f"{base}__{firma:08x}"


def campo_ligado(estado: MutableMapping[str, Any], widget, etiqueta: str, clave: str, defecto: Any,
                 **kwargs: Any) -> Any:
    """Widget ``_w_<clave>`` ligado al dato persistente ``clave`` (30-sep-2026).

    Streamlit borra la clave de un widget al abrir otra página o recargar. Si
    el dato y el widget comparten clave, al volver el campo arranca en su
    valor por defecto o en su mínimo (caso real: NOCT 35 °C y γ −0,70 %/°C en
    🔆 Motor Óptico). Aquí el dato vive en ``clave`` (se guarda con el
    proyecto) y el widget en ``_w_<clave>``; ``sincronizar_campo`` los une.
    Sin dato se usa ``defecto``; un dato fuera de rango se recorta y una
    opción que ya no existe vuelve a ``defecto``.
    """
    valor = estado.get(clave, defecto)
    if valor is None:
        valor = defecto
    if "min_value" in kwargs and valor is not None:
        valor = max(type(defecto)(valor), type(defecto)(kwargs["min_value"]))
    if "max_value" in kwargs and valor is not None:
        valor = min(type(defecto)(valor), type(defecto)(kwargs["max_value"]))
    if "options" in kwargs and valor not in list(kwargs["options"]):
        valor = defecto
    w = f"_w_{clave}"
    sincronizar_campo(estado, w, valor)
    resultado = widget(etiqueta, key=w, **kwargs)
    estado[clave] = resultado
    return resultado
