# -*- coding: utf-8 -*-
"""
Persistencia de las tablas editables del Presupuesto (#114) — POR USUARIO.

Las 4 secciones editables (Perfilería, Mano de Obra, Sistema FV,
Inversor/Eléctrico) viven en session_state y se pierden al recargar la página
o al abrir otra pestaña — el usuario puede perder una cotización completa.

Cada usuario logueado guarda sus tablas en SU archivo privado dentro de
datos/persistencia/ (gitignored): las cotizaciones de un cliente jamás se
mezclan con las de otro en el mismo servidor.
"""
import json
import os

from calculos.persistencia_resultados import ruta_datos_usuario

# Solo las secciones cuya plantilla es estable; 'catalogo' se regenera desde
# la selección de equipos y 'soft'/'opex' tienen su propia lógica dinámica.
SECCIONES_PERSISTIBLES = ("perfileria", "mano_obra", "sistema_fv", "inversor")

# Esquema mínimo que una tabla restaurada debe traer para ser usable
COLUMNAS_REQUERIDAS = ("Descripcion", "Cantidad", "USD_un")
COLUMNAS_OPCIONALES = {"Activo": True, "Ref": "", "Unidad": ""}


def _ruta(usuario: str) -> str:
    return ruta_datos_usuario("presupuesto_guardado.json", usuario)


def _leer(usuario: str) -> dict:
    ruta = _ruta(usuario)
    if not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _escribir(usuario: str, data: dict) -> bool:
    try:
        ruta = _ruta(usuario)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        tmp = f"{ruta}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, ruta)
        return True
    except OSError:
        return False


def guardar_seccion(key: str, filas: list, usuario: str, fuente: str = "") -> bool:
    """Guarda las filas (list[dict]) y la fuente de precios de una sección."""
    if key not in SECCIONES_PERSISTIBLES or not usuario:
        return False
    data = _leer(usuario)
    data[key] = {"filas": filas, "fuente": fuente or ""}
    return _escribir(usuario, data)


def cargar_seccion(key: str, usuario: str):
    """Devuelve (filas_validadas, fuente) o (None, "") si no hay nada usable.

    Valida el esquema: exige las columnas requeridas y completa las opcionales
    con sus defaults. Una tabla de una versión vieja/corrupta se descarta y la
    página cae a la plantilla en vez de romper con KeyError.
    """
    if key not in SECCIONES_PERSISTIBLES or not usuario:
        return None, ""
    sec = _leer(usuario).get(key)
    if not isinstance(sec, dict):
        return None, ""
    filas = sec.get("filas")
    if not isinstance(filas, list) or not filas:
        return None, ""
    validadas = []
    for fila in filas:
        if not isinstance(fila, dict):
            return None, ""                       # estructura irreconocible
        if not all(c in fila for c in COLUMNAS_REQUERIDAS):
            return None, ""                       # esquema viejo → plantilla
        f = dict(fila)
        for c, defecto in COLUMNAS_OPCIONALES.items():
            f.setdefault(c, defecto)
        validadas.append(f)
    return validadas, str(sec.get("fuente", ""))


def borrar_seccion(key: str, usuario: str) -> None:
    """Elimina una sección guardada (botón 'Resetear' → vuelve a la plantilla)."""
    if not usuario:
        return
    data = _leer(usuario)
    if key in data:
        del data[key]
        _escribir(usuario, data)
