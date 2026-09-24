"""Puntos 3D de análisis de sombra por superficie (Vista 3D).

Spec ``08-interfaz/puntos-3d-validacion``: ningún punto escrito por el
usuario se pierde sin aviso, los puntos geométricamente inválidos se detectan
antes de calcular y los puntos quedan asociados al ``uid`` de la superficie.

Formato por línea (metros; X = Este, Y = Norte verdadero, Z = altura):

- con ``;``  → campos separados por ``;``; la coma dentro de un campo es
  decimal (``8,5;0;2``);
- sin ``;``  → campos separados por ``,`` y decimal con punto (``8.5,0,2``).

Una línea que no dé exactamente 3 números finitos es un error con su número
de línea y su motivo; nunca se descarta en silencio.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


def _campos(linea: str) -> list[str]:
    if ";" in linea:
        return [c.strip().replace(",", ".") for c in linea.split(";")]
    return [c.strip() for c in linea.split(",")]


def parsear_puntos_3d(texto: str, nombre_superficie: str) -> tuple[list[dict], list[dict]]:
    """``(puntos, errores)`` del texto de puntos de una superficie.

    Cada punto: ``{"nombre", "fachada", "x", "y", "z"}`` (contrato del motor
    de sombra). Cada error: ``{"linea", "texto", "motivo"}``. Las líneas
    vacías se ignoran.
    """
    puntos: list[dict] = []
    errores: list[dict] = []
    for numero, cruda in enumerate((texto or "").splitlines(), start=1):
        linea = cruda.strip()
        if not linea:
            continue
        campos = _campos(linea)
        if len(campos) != 3:
            motivo = f"se esperaban 3 valores x,y,z y hay {len(campos)}"
            if ";" not in linea and len(campos) == 4:
                motivo += " (si usas coma decimal, separa los valores con «;»: 8,5;0;2)"
            errores.append({"linea": numero, "texto": linea, "motivo": motivo})
            continue
        valores = []
        for campo in campos:
            try:
                valor = float(campo)
            except ValueError:
                errores.append({"linea": numero, "texto": linea,
                                "motivo": f"valor no numérico: «{campo}»"})
                break
            if not math.isfinite(valor):
                errores.append({"linea": numero, "texto": linea,
                                "motivo": f"valor no finito: «{campo}»"})
                break
            valores.append(valor)
        else:
            x, y, z = valores
            puntos.append({
                "nombre": f"{nombre_superficie}-P{len(puntos) + 1}",
                "fachada": nombre_superficie, "x": x, "y": y, "z": z,
            })
    return puntos, errores


def previsualizar_puntos(malla: Any, puntos: list[dict]) -> list[str]:
    """Avisos de ``sombras_3d.validar_puntos`` (la misma función del motor)
    antes de calcular: punto dentro del volumen o a menos de 10 cm de la malla."""
    if malla is None or not puntos:
        return []
    from calculos.sombras_3d import validar_puntos

    return validar_puntos(malla, puntos)


def migrar_puntos_por_uid(
    puntos: Mapping[Any, list] | None, superficies: list[Mapping[str, Any]],
) -> tuple[dict[Any, list], list[str]]:
    """Reindexa por ``uid`` los puntos guardados por nombre (sesiones
    antiguas) o con el ``uid`` en texto (proyecto recargado desde JSON).

    Retorna ``(puntos_por_uid, avisos)``; los puntos de una superficie que ya
    no existe se descartan con aviso. No muta la entrada.
    """
    uids = {s.get("uid") for s in superficies}
    uid_por_nombre = {s.get("nombre"): s.get("uid") for s in superficies}
    uid_por_texto = {str(u): u for u in uids}
    salida: dict[Any, list] = {}
    avisos: list[str] = []
    for clave, lista in (puntos or {}).items():
        if clave in uids and not isinstance(clave, str):
            uid = clave
        elif clave in uid_por_nombre:
            uid = uid_por_nombre[clave]
        elif str(clave) in uid_por_texto:
            uid = uid_por_texto[str(clave)]
        else:
            avisos.append(
                f"Se descartaron los puntos de «{clave}»: esa superficie ya no existe."
            )
            continue
        salida.setdefault(uid, list(lista))
    return salida, avisos


def puntos_por_nombre(
    puntos_por_uid: Mapping[Any, list], superficies: list[Mapping[str, Any]],
) -> dict[str, list]:
    """Puntos de las superficies activas indexados por su nombre ACTUAL,
    como los recibe ``calcular_fs_horario_por_superficie``."""
    return {
        s["nombre"]: list(puntos_por_uid.get(s.get("uid"), []))
        for s in superficies if s.get("activa", True)
    }
