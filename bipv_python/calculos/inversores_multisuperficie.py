"""Validacion pura de inversores y asignaciones multi-superficie."""
from __future__ import annotations
from collections.abc import Mapping
from typing import Any


def derivar_tipo_inversor(n_superficies_asignadas: int) -> str:
    if n_superficies_asignadas <= 0:
        raise ValueError("Un inversor sin superficies asignadas no tiene tipo derivable.")
    return "dedicado" if n_superficies_asignadas == 1 else "compartido"


def validar_inversores_y_asignaciones(superficies: list[Mapping[str, Any]], inversores: list[Mapping[str, Any]]) -> dict:
    errores: list[str] = []
    ids: set[str] = set()
    for inversor in inversores:
        inv_id = str(inversor.get("inversor_id", "")).strip()
        if not inv_id:
            errores.append("Un inversor no tiene 'inversor_id'.")
        elif inv_id in ids:
            errores.append(f"inversor_id duplicado: '{inv_id}'.")
        ids.add(inv_id)
        eta = inversor.get("eta_inversor")
        if eta is None:
            errores.append(f"El inversor '{inv_id}' no tiene eta_inversor.")
        else:
            try:
                if not 0 < float(eta) <= 1:
                    errores.append(f"El inversor '{inv_id}' tiene eta_inversor fuera de (0, 1].")
            except (TypeError, ValueError):
                errores.append(f"El inversor '{inv_id}' tiene eta_inversor no numerica.")
    # Spec 03/diseno-electrico-multisuperficie (fase A2): la asignación es por
    # grupo de strings; una superficie antigua se lee como un grupo G1.
    from calculos.diseno_electrico_multisup import grupos_de_superficie

    activas = [s for s in superficies if s.get("activa", True)]
    asignaciones = {inv_id: [] for inv_id in ids if inv_id}
    for superficie in activas:
        nombre = superficie.get("nombre", "<sin nombre>")
        grupos = grupos_de_superficie(superficie)
        if not grupos:
            errores.append(f"La superficie '{nombre}' no tiene inversor asignado.")
            for campo in ("n_serie", "n_paralelo"):
                errores.append(f"La superficie '{nombre}' tiene {campo} invalido.")
            continue
        varios = len(grupos) > 1
        for grupo in grupos:
            unidad = f"{nombre} · {grupo.get('gid', 'G?')}" if varios else nombre
            sujeto = f"La superficie '{nombre}' ({grupo.get('gid', 'G?')})" if varios else f"La superficie '{nombre}'"
            inv_id = str(grupo.get("inversor_id") or "").strip()
            if not inv_id:
                errores.append(f"{sujeto} no tiene inversor asignado.")
            elif inv_id not in ids:
                errores.append(f"{sujeto} referencia el inversor '{inv_id}', que no existe.")
            else:
                asignaciones[inv_id].append(unidad)
            for campo in ("n_serie", "n_paralelo"):
                try:
                    if int(grupo.get(campo)) <= 0:
                        raise ValueError
                except (TypeError, ValueError):
                    errores.append(f"{sujeto} tiene {campo} invalido.")
    tipos = {}
    for inv_id, nombres in asignaciones.items():
        if not nombres:
            errores.append(f"El inversor '{inv_id}' no tiene ninguna superficie asignada.")
        else:
            tipos[inv_id] = derivar_tipo_inversor(len(nombres))
    return {"ok": not errores, "errores": errores, "tipos_derivados": tipos, "asignaciones": asignaciones}


def aplicar_tipos_derivados(inversores: list[Mapping[str, Any]], tipos_derivados: Mapping[str, str]) -> list[dict]:
    return [{**dict(inv), "tipo": tipos_derivados.get(str(inv.get("inversor_id")), inv.get("tipo"))} for inv in inversores]
