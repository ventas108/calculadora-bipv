"""No nombrar el software de simulación de referencia en lo que ve el usuario.

Regla del usuario («por cuestiones legales», 30-ago-2026; reafirmada el
29-sep-2026, Spec ``08-interfaz/sin-nombre-referencia``): la app, el manual
del 🧭 Asistente y sus respuestas dicen «la referencia estándar internacional».
El catálogo de paneles trae ese nombre en más de 3.000 notas y fuentes; se
filtra al leerlo en vez de reescribir el Excel del servidor.
"""
from __future__ import annotations

import re

REFERENCIA = "la referencia estándar internacional"

_NOMBRE = r"[Pp][Vv][Ss][Yy][Ss][Tt](?![Ee][Mm])"   # «pvsystem» (pvlib) no es el nombre
_VERSION = r"(?:[ _-]?[Vv]?\d+(?:[.,]\d+)*)?"
_REGLAS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(rf"\b{_NOMBRE}[ _-]?[Vv]6\b"), f"modelo de un diodo v6 de {REFERENCIA}"),
    (re.compile(rf"\bestilo\s+{_NOMBRE}{_VERSION}\b"), f"estilo de {REFERENCIA}"),
    (re.compile(rf"\bbase\s+{_NOMBRE}{_VERSION}\b"), f"base de datos de {REFERENCIA}"),
    (re.compile(rf"\bmódulo\s+{_NOMBRE}{_VERSION}\b"), f"módulo de {REFERENCIA}"),
    (re.compile(rf"\bdel?\s+{_NOMBRE}{_VERSION}\b"), f"de {REFERENCIA}"),
    (re.compile(rf"\bal\s+{_NOMBRE}{_VERSION}\b"), f"a {REFERENCIA}"),
    (re.compile(rf"\bel\s+{_NOMBRE}{_VERSION}\b"), REFERENCIA),
    (re.compile(rf"\b{_NOMBRE}{_VERSION}\b"), REFERENCIA),
)
# Mayúscula al comienzo de texto, de oración, de línea o de viñeta.
_INICIO = re.compile(
    r"(^|[.!?]\s+|\n[ \t]*(?:[-*•]|\d+\.)?[ \t]*|\*\*|[«\"(]|:\s+|—\s+)(la referencia estándar internacional)"
)
_DOBLE = re.compile(r"\b(la|de la|a la)\s+(la referencia estándar internacional)")


def _mayuscula(m: re.Match) -> str:
    prefijo = m.group(1)
    if prefijo in ("«", '"', "(") or prefijo.startswith("—") or prefijo.startswith(":"):
        return m.group(0)
    return prefijo + "L" + m.group(2)[1:]


# Nombres de archivos y funciones que llevan el nombre (p. ej. un módulo
# interno o una función de pvlib): se describen sin nombrarlo.
_IDENTIFICADOR = re.compile(rf"`?[\w./:-]*{_NOMBRE}[\w./:-]*(?:\([^)]*\))?`?")


def _identificador(m: re.Match) -> str:
    token = m.group(0).strip("`")
    if "(" in token or "::" in token:
        return "una función interna"
    if token.lower().endswith(".md"):
        return "un documento interno de diagnóstico"
    if token.lower().endswith(".py"):
        return "un módulo interno"
    return "una función interna"


def anonimizar_referencia(texto, *, identificadores: bool = True):
    """Reemplaza el nombre del software de referencia. No-texto → igual."""
    if not isinstance(texto, str) or not re.search(_NOMBRE, texto):
        return texto
    salida = texto
    for patron, reemplazo in _REGLAS:
        salida = patron.sub(reemplazo, salida)
    if identificadores:
        salida = _IDENTIFICADOR.sub(_identificador, salida)
    salida = _DOBLE.sub(lambda m: m.group(1).rsplit(" ", 1)[0] + " " + m.group(2)
                        if m.group(1) != "la" else m.group(2), salida)
    return _INICIO.sub(_mayuscula, salida)


def menciona_referencia(texto) -> bool:
    return isinstance(texto, str) and re.search(_NOMBRE, texto) is not None
