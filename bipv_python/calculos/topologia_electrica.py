"""Topología eléctrica del sistema multi-superficie (inversor → MPPT → strings).

Spec ``07-informes/unifilar-retie-multisuperficie`` (28-sep-2026). Antes
📋 Ficha RETIE validaba el panel y el inversor de 📐 Dimensionamiento (un solo
panel, un solo tipo de string) y ⚡ Diagrama Unifilar pedía a mano los módulos
de cada superficie, aunque 🗺️ Vista 3D ya tenía los grupos de strings de cada
superficie con su inversor y su MPPT. En el proyecto del cliente (fachada
ASP 8 × 14 en el MPPT 1 con caja combinadora y techo SPR 4 × 1 en el MPPT 2 de
un SG5.0RT) las dos páginas describían otro sistema.

Este módulo arma UNA topología que leen las dos páginas. Es puro: no conoce
Streamlit ni dibuja. Las comprobaciones eléctricas NO se repiten aquí: la caja
combinadora y la corriente de cada MPPT salen del diagnóstico de
``diseno_electrico_multisup.validar_diseno_electrico``.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# Claves de datos del proyecto (se guardan con el proyecto): opciones del
# sistema que comparten ⚡ Diagrama Unifilar y 📋 Ficha RETIE.
CLAVE_OPTIMIZADORES = "sistema_optimizadores"
CLAVE_BATERIA_INVERSOR = "bateria_inversor_id"


def _num(valor: Any) -> float | None:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if numero == numero and numero > 0 else None


def _p_ac_kw(inversor: Mapping[str, Any]) -> float | None:
    p_w = _num(inversor.get("P_ac_nom_W")) or _num((inversor.get("ficha") or {}).get("P_ac_nom_W"))
    return p_w / 1000.0 if p_w else None


def construir_topologia(
    superficies: list[Mapping[str, Any]],
    inversores: list[Mapping[str, Any]],
    paneles: Mapping[str, Mapping[str, Any]],
    diagnostico: Mapping[str, Any],
    *,
    optimizadores: bool = False,
    bateria: Mapping[str, Any] | None = None,
) -> dict:
    """Topología del sistema (ver ``diseno.md`` de la Spec). No muta las entradas.

    ``paneles[nombre_superficie]`` es ``{"panel", "nombre"}``; ``diagnostico``
    es la salida de ``validar_diseno_electrico`` para esas mismas entradas.
    ``bateria``: ``{nombre, cantidad, capacidad_kWh_unidad, inversor_id}`` o
    ``None``.
    """
    from calculos.diseno_electrico_multisup import grupos_de_superficie

    invs = {str(i.get("inversor_id")): i for i in inversores if i.get("inversor_id")}
    mppt_diag = {(m["inversor_id"], m["mppt"]): m for m in diagnostico.get("mppt", [])}
    # Spec 07/unifilar-retie-bifacial-cruce: factor BNPI de cada grupo (del
    # diagnóstico) y strings que cruzan a otra superficie (Spec 05/string-
    # cruza-superficies).
    factor_diag = {(g.get("superficie"), g.get("gid")): float(g.get("factor_bifacial") or 1.0)
                   for g in diagnostico.get("grupos", [])}
    por_uid = {str(s.get("uid")): s.get("nombre") for s in superficies}

    ramas: dict[tuple[str, int], list[dict]] = {}
    sin_asignar: list[str] = []
    por_superficie: dict[str, dict] = {}
    for sup in superficies:
        if not sup.get("activa", True):
            continue
        nombre = sup.get("nombre", "?")
        info = paneles.get(nombre)
        pmax = _num((info or {}).get("panel", {}).get("Pmax_stc"))
        for g in grupos_de_superficie(sup):
            etiqueta = f"{nombre} · {g.get('gid', 'G?')}"
            inv_id = str(g.get("inversor_id") or "").strip()
            try:
                n_s, n_p, mppt = int(g.get("n_serie")), int(g.get("n_paralelo")), int(g.get("mppt"))
            except (TypeError, ValueError):
                sin_asignar.append(etiqueta)
                continue
            if inv_id not in invs or info is None or min(n_s, n_p, mppt) < 1:
                sin_asignar.append(etiqueta)
                continue
            modulos = n_s * n_p
            p_kwp = modulos * pmax / 1000.0 if pmax else None
            isc_frontal = _num(info["panel"].get("Isc_stc"))
            factor_bif = factor_diag.get((nombre, g.get("gid", "G?")), 1.0)
            cruce = g.get("cruce") if isinstance(g.get("cruce"), Mapping) else None
            cruce_texto = None
            if cruce and cruce.get("uid") is not None:
                cruce_texto = (f"{cruce.get('modulos')} de {n_s} módulos en "
                               f"«{por_uid.get(str(cruce['uid']), '?')}»")
            ramas.setdefault((inv_id, mppt), []).append({
                "superficie": nombre, "gid": g.get("gid", "G?"), "panel": info.get("nombre"),
                "n_serie": n_s, "n_paralelo": n_p, "modulos": modulos, "p_dc_kWp": p_kwp,
                # Isc de diseño del módulo: en BNPI si es bifacial (conductores y fusibles).
                "isc_stc_A": isc_frontal * factor_bif if isc_frontal else None,
                "isc_frontal_A": isc_frontal, "factor_bifacial": factor_bif,
                "cruce_texto": cruce_texto,
            })
            s = por_superficie.setdefault(nombre, {"nombre": nombre, "tipo": sup.get("tipo") or "",
                                                   "paneles": [], "modulos": 0, "p_dc_kWp": 0.0})
            if info.get("nombre") not in s["paneles"]:
                s["paneles"].append(info.get("nombre"))
            s["modulos"] += modulos
            s["p_dc_kWp"] += p_kwp or 0.0

    salida_invs = []
    for inv_id, inv in invs.items():
        claves = sorted(k for k in ramas if k[0] == inv_id)
        if not claves:
            continue
        ramas_inv = []
        for clave in claves:
            diag = mppt_diag.get(clave, {})
            grupos = ramas[clave]
            ramas_inv.append({
                "mppt": clave[1], "grupos": grupos,
                "strings": sum(g["n_paralelo"] for g in grupos),
                "caja_combinadora": bool(diag.get("caja_combinadora")),
                "isc_diseno_A": diag.get("isc_total"),
            })
        salida_invs.append({
            "inversor_id": inv_id, "nombre": inv.get("nombre") or "",
            "ficha": dict(inv.get("ficha") or {}),
            "p_ac_kW": _p_ac_kw(inv),
            "p_dc_kWp": sum(g["p_dc_kWp"] or 0.0 for r in ramas_inv for g in r["grupos"]),
            "ramas": ramas_inv, "bateria": False,
        })

    bateria_out = None
    if bateria and salida_invs:
        pedido = str(bateria.get("inversor_id") or "")
        ids = [i["inversor_id"] for i in salida_invs]
        destino = pedido if pedido in ids else ids[0]
        cantidad = int(bateria.get("cantidad") or 0)
        cap = _num(bateria.get("capacidad_kWh_unidad"))
        bateria_out = {
            "nombre": bateria.get("nombre") or "", "cantidad": cantidad,
            "capacidad_kWh_unidad": cap,
            "capacidad_total_kWh": round(cap * cantidad, 2) if cap and cantidad else None,
            "inversor_id": destino, "inversor_reasignado": destino != pedido,
        }
        for i in salida_invs:
            i["bateria"] = i["inversor_id"] == destino

    # Módulos donde están físicamente (un string que cruza pone parte de sus
    # módulos en otra superficie); "modulos" sigue siendo el eléctrico.
    from calculos.cruce_superficies import modulos_fisicos_por_superficie
    fisicos = modulos_fisicos_por_superficie(list(superficies))
    for nombre_s, datos_s in por_superficie.items():
        datos_s["modulos_fisicos"] = fisicos.get(nombre_s, datos_s["modulos"])

    p_ac = [i["p_ac_kW"] for i in salida_invs]
    return {
        "inversores": salida_invs,
        "superficies": list(por_superficie.values()),
        "optimizadores": bool(optimizadores),
        "bateria": bateria_out,
        "sin_asignar": sin_asignar,
        "n_modulos": sum(s["modulos"] for s in por_superficie.values()),
        "p_dc_kWp": sum(i["p_dc_kWp"] for i in salida_invs),
        "p_ac_kW": sum(p_ac) if p_ac and all(p is not None for p in p_ac) else None,
    }


def bateria_desde_estado(estado: Mapping[str, Any]) -> dict | None:
    """Batería de 🔋 Baterías y Balance para la topología, o ``None``."""
    if not estado.get("bateria_ok"):
        return None
    dim = estado.get("bateria_dim") or {}
    datos = estado.get("bateria_dict") or {}
    cantidad = int(dim.get("N_baterias") or 0)
    if cantidad < 1:
        return None
    return {
        "nombre": estado.get("bateria_nombre") or "", "cantidad": cantidad,
        "capacidad_kWh_unidad": dim.get("cap_unitaria_kWh") or datos.get("capacidad_kWh"),
        "inversor_id": estado.get(CLAVE_BATERIA_INVERSOR),
    }


def topologia_desde_estado(estado: Mapping[str, Any], *, incluir_bateria: bool = True) -> dict | None:
    """Topología del sistema multi-superficie de la sesión, o ``None`` si no
    hay multi-superficie activo con grupos de strings. Incluye el
    ``diagnostico`` eléctrico con el que se armó."""
    if not estado.get("multisup_activo"):
        return None
    from calculos.diseno_electrico_multisup import (
        grupos_de_superficie,
        paneles_superficies_estado,
        temperaturas_diseno,
        validar_diseno_electrico,
    )
    superficies = list(estado.get("superficies_bipv") or [])
    if not any(grupos_de_superficie(s) for s in superficies if s.get("activa", True)):
        return None
    inversores = list(estado.get("multisup_inversores") or [])
    paneles = paneles_superficies_estado(estado, superficies)
    from calculos.diseno_electrico_multisup import _bifacial_estado
    diagnostico = validar_diseno_electrico(superficies, inversores, paneles, temperaturas_diseno(estado),
                                           bifacial=_bifacial_estado(estado))
    topo = construir_topologia(
        superficies, inversores, paneles, diagnostico,
        optimizadores=bool(estado.get(CLAVE_OPTIMIZADORES)),
        bateria=bateria_desde_estado(estado) if incluir_bateria else None,
    )
    topo["diagnostico"] = diagnostico
    return topo
