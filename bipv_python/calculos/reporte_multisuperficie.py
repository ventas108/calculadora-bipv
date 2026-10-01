# -*- coding: utf-8 -*-
"""Secciones multi-superficie (🗺️ Vista 3D) del 📄 Reporte PDF.

Spec ``07-informes/reporte-multisuperficie`` (1-oct-2026). Con energía
multi-superficie publicada, esa es la energía del proyecto (la usan 💰
Financiero, 🔋 Baterías y 🌿 CO₂); el reporte debe mostrarla como la energía
del proyecto y explicar de dónde sale: superficies, paneles, inversores,
cadena de pérdidas, strings que cruzan, método y estado eléctrico.

Solo lee lo PUBLICADO (``multisup_*``, ``superficies_bipv``,
``multisup_inversores``); nunca recalcula energía. Módulo puro: sin Streamlit.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _f(valor: Any, dec: int = 1, fallback: str = "—") -> str:
    try:
        return f"{float(valor):,.{dec}f}"
    except (TypeError, ValueError):
        return fallback


def activo(estado: Mapping[str, Any]) -> bool:
    """Hay energía multi-superficie publicada: es la energía del proyecto."""
    return bool(estado.get("multisup_activo")) and float(estado.get("E_ac_anual_kWh_multisup") or 0) > 0 \
        and bool(estado.get("multisup_desglose"))


def _superficies(estado: Mapping[str, Any]) -> dict:
    return {s.get("nombre"): s for s in (estado.get("superficies_bipv") or []) if s.get("activa", True)}


def _paneles(estado: Mapping[str, Any]) -> dict:
    try:
        from calculos.diseno_electrico_multisup import paneles_superficies_estado
        return paneles_superficies_estado(estado, list(_superficies(estado).values()))
    except Exception:
        return {}


def _modulos_fisicos(estado: Mapping[str, Any]) -> dict:
    try:
        from calculos.cruce_superficies import modulos_fisicos_por_superficie
        return modulos_fisicos_por_superficie(list(_superficies(estado).values()))
    except Exception:
        return {}


def resumen(estado: Mapping[str, Any]) -> list[tuple]:
    """Energía del proyecto, potencia, rendimiento, método y estado eléctrico."""
    from calculos.publicacion_multisuperficie import ETIQUETA_ORIGEN, origen_vigente

    e = float(estado.get("E_ac_anual_kWh_multisup") or 0.0)
    sis = dict(estado.get("multisup_sistema") or {})
    kwp = float(sis.get("P_dc_stc_kW") or 0.0)
    area = float(estado.get("area_total_multisup") or 0.0)
    filas = [
        ("Energía AC anual del proyecto", _f(e, 0), "kWh/año", "Energía multi-superficie publicada en 🗺️ Vista 3D"),
        ("Superficies activas", str(len(estado.get("multisup_desglose") or [])), "", f"Área total {_f(area, 1)} m²"),
    ]
    if kwp > 0:
        filas += [("Potencia pico DC", _f(kwp, 2), "kWp", f"{int(sis.get('n_modulos') or 0):,} módulos"),
                  ("Rendimiento específico", _f(e / kwp, 0), "kWh/kWp·año", "Energía ÷ potencia pico")]
    if area > 0:
        filas.append(("Densidad energética", _f(e / area, 0), "kWh/m²·año", ""))
    origen = origen_vigente(estado)
    if origen:
        filas.append(("Método de cálculo", ETIQUETA_ORIGEN.get(origen, origen), "", ""))
    perd_bus = estado.get("multisup_perdida_bus_kWh")
    if perd_bus:
        filas.append(("Recorte de inversores compartidos", _f(perd_bus, 0), "kWh/año", "Modelo físico"))
    est = estado.get("multisup_estado_electrico") or {}
    if est.get("texto"):
        filas.append(("Diseño eléctrico", str(est["texto"]), "", ""))
    return filas


def tabla_superficies(estado: Mapping[str, Any]) -> list[dict]:
    """Por superficie: orientación, panel, módulos, kWp, área, POA, energía, kWh/kWp y PR."""
    sups, paneles, modulos = _superficies(estado), _paneles(estado), _modulos_fisicos(estado)
    prs = dict((estado.get("multisup_cadena_perdidas") or {}).get("pr") or {})
    filas = []
    for d in estado.get("multisup_desglose") or []:
        nombre = d.get("nombre")
        s = sups.get(nombre, {})
        info = paneles.get(nombre) or {}
        pmax = float((info.get("panel") or {}).get("Pmax_stc") or 0.0)
        n = int(modulos.get(nombre) or 0)
        kwp = n * pmax / 1000.0 if n and pmax else None
        e = float(d.get("e_ac_kWh") or 0.0)
        filas.append({
            "nombre": nombre, "tipo": d.get("tipo") or s.get("tipo") or "—",
            "inclinacion": s.get("tilt_deg"), "azimut": s.get("azimuth_deg"),
            "panel": info.get("nombre") or "—", "modulos": n or None, "kwp": kwp,
            "area_m2": float(d.get("area_m2") or 0.0), "poa_kwh_m2": float(d.get("poa_kWh_m2") or 0.0),
            "e_ac_kwh": e, "yield_kwh_kwp": (e / kwp) if kwp else None, "pr": prs.get(nombre),
        })
    return filas


def filas_por_panel(estado: Mapping[str, Any]) -> list[tuple]:
    """Módulos y potencia por modelo de panel."""
    return [(str(p.get("panel")), f"{int(p.get('modulos') or 0):,} módulos", "",
             f"{_f(p.get('P_dc_stc_kW'), 2)} kWp")
            for p in (estado.get("multisup_sistema") or {}).get("por_panel") or []]


def tabla_inversores(estado: Mapping[str, Any]) -> list[dict]:
    """Cada inversor: potencia AC, superficies y strings que alimenta, módulos, kWp y DC/AC."""
    from calculos.diseno_electrico_multisup import grupos_de_superficie
    from calculos.topologia_electrica import _p_ac_kw

    paneles = _paneles(estado)
    invs = {str(i.get("inversor_id")): i for i in (estado.get("multisup_inversores") or []) if i.get("inversor_id")}
    agg: dict[str, dict] = {k: {"superficies": [], "strings": 0, "modulos": 0, "kwp": 0.0} for k in invs}
    for nombre, s in _superficies(estado).items():
        pmax = float(((paneles.get(nombre) or {}).get("panel") or {}).get("Pmax_stc") or 0.0)
        for g in grupos_de_superficie(s):
            inv_id = str(g.get("inversor_id") or "")
            try:
                n_s, n_p = int(g.get("n_serie") or 0), int(g.get("n_paralelo") or 0)
            except (TypeError, ValueError):
                continue
            if inv_id not in agg or n_s <= 0 or n_p <= 0:
                continue
            a = agg[inv_id]
            if nombre not in a["superficies"]:
                a["superficies"].append(nombre)
            a["strings"] += n_p
            a["modulos"] += n_s * n_p
            a["kwp"] += n_s * n_p * pmax / 1000.0
    filas = []
    for inv_id, inv in invs.items():
        a = agg[inv_id]
        p_ac = _p_ac_kw(inv)
        filas.append({"inversor": inv_id, "modelo": inv.get("nombre") or "—", "p_ac_kw": p_ac,
                      "superficies": ", ".join(a["superficies"]) or "—", "strings": a["strings"],
                      "modulos": a["modulos"], "kwp": a["kwp"],
                      "dc_ac": (a["kwp"] / p_ac) if p_ac and a["kwp"] else None})
    return filas


def cadena_por_superficie(estado: Mapping[str, Any]) -> list[dict]:
    """Pérdidas de cada superficie publicadas por 🗺️ Vista 3D (vacío si se publicó antes de esta Spec)."""
    reg = estado.get("multisup_cadena_perdidas") or {}
    return [dict(f) for f in (reg.get("desglose") or [])]


def cruces(estado: Mapping[str, Any]) -> list[dict]:
    try:
        from calculos.cruce_superficies import cruces_del_proyecto
        return cruces_del_proyecto(list(_superficies(estado).values()))
    except Exception:
        return []


def mensual(estado: Mapping[str, Any]) -> list[float]:
    m = (estado.get("multisup_sistema") or {}).get("mensual_kWh") or []
    return [float(v) for v in m] if len(m) == 12 else []
