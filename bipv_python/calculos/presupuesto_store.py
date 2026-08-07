# -*- coding: utf-8 -*-
"""
Persistencia de las tablas editables del Presupuesto (#114).

Las 4 secciones editables (Perfilería, Mano de Obra, Sistema FV,
Inversor/Eléctrico) viven en session_state y se pierden al recargar la página
o al abrir otra pestaña — el usuario puede perder una cotización completa.

Este módulo guarda cada sección editada (filas + fuente de precios) en
datos/presupuesto_guardado.json (gitignored: son datos del usuario) con
escritura atómica, y las restaura al inicializar la tabla.
"""
import json
import os

_DIR_DATOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")
RUTA_PRESUPUESTO = os.path.join(_DIR_DATOS, "presupuesto_guardado.json")

# Solo las secciones cuya plantilla es estable; 'catalogo' se regenera desde
# la selección de equipos y 'soft'/'opex' tienen su propia lógica dinámica.
SECCIONES_PERSISTIBLES = ("perfileria", "mano_obra", "sistema_fv", "inversor")


def _leer() -> dict:
    if not os.path.exists(RUTA_PRESUPUESTO):
        return {}
    try:
        with open(RUTA_PRESUPUESTO, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _escribir(data: dict) -> bool:
    try:
        os.makedirs(_DIR_DATOS, exist_ok=True)
        tmp = RUTA_PRESUPUESTO + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, RUTA_PRESUPUESTO)
        return True
    except OSError:
        return False


def guardar_seccion(key: str, filas: list, fuente: str = "") -> bool:
    """Guarda las filas (list[dict]) y la fuente de precios de una sección."""
    if key not in SECCIONES_PERSISTIBLES:
        return False
    data = _leer()
    data[key] = {"filas": filas, "fuente": fuente or ""}
    return _escribir(data)


def cargar_seccion(key: str):
    """Devuelve (filas, fuente) guardadas, o (None, "") si no hay nada."""
    if key not in SECCIONES_PERSISTIBLES:
        return None, ""
    sec = _leer().get(key)
    if not isinstance(sec, dict):
        return None, ""
    filas = sec.get("filas")
    if not isinstance(filas, list) or not filas:
        return None, ""
    return filas, str(sec.get("fuente", ""))


def borrar_seccion(key: str) -> None:
    """Elimina una sección guardada (botón 'Resetear' → vuelve a la plantilla)."""
    data = _leer()
    if key in data:
        del data[key]
        _escribir(data)
