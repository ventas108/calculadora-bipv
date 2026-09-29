# -*- coding: utf-8 -*-
"""Recorte (clipping) de cada inversor de 🗺️ Vista 3D en los modos simplificado y bypass.

Spec ``05-perdidas-y-temperatura/recorte-inversor-multisuperficie`` (29-sep-2026).
Antes solo el modo físico limitaba la salida de cada inversor a su potencia
AC nominal; el simplificado y el bypass publicaban POA × área × η × PR sin
ese límite.

Modelo, hora a hora:

- AC de una superficie en la hora t = E_s × perfil_s(t), con E_s = POA bruta ×
  módulos × Pmax × PR (la misma energía que publica el modo simplificado) y
  ``perfil_s`` la forma horaria de su AC (``cadena_superficie``: SDM o γ
  lineal), que suma 1.
- AC de un grupo = módulos del grupo en cada superficie × AC por módulo de esa
  superficie (un string que cruza aporta desde las dos).
- AC de un inversor = suma de sus grupos; recorte(t) = max(AC(t) − Pnom, 0).
- El recorte de cada hora se reparte entre las superficies según lo que
  aportó cada una en esa hora; el factor de la superficie es
  1 − recorte ÷ E_s.

Módulo puro: sin Streamlit.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np


def potencia_ac_inversor(inversor: Mapping[str, Any]) -> float | None:
    """Potencia AC nominal (W) del inversor o de su ficha; None si no la tiene."""
    for valor in (inversor.get("P_ac_nom_W"), (inversor.get("ficha") or {}).get("P_ac_nom_W")):
        try:
            v = float(valor)
        except (TypeError, ValueError):
            continue
        if v > 0:
            return v
    return None


def _modulos_por_inversor(superficies: list[Mapping[str, Any]], con_pac: set[str]) -> dict:
    """``{inversor_id: {superficie: módulos}}`` según dónde están los módulos."""
    por_uid = {s.get("uid"): s["nombre"] for s in superficies if s.get("uid")}
    salida: dict[str, dict[str, int]] = {}
    for s in superficies:
        for g in s.get("grupos") or []:
            inv = str(g.get("inversor_id"))
            if inv not in con_pac:
                continue
            ns, npar = int(g.get("n_serie") or 0), int(g.get("n_paralelo") or 0)
            if ns <= 0 or npar <= 0:
                continue
            cruce = g.get("cruce") or {}
            destino = por_uid.get(cruce.get("uid")) if cruce else None
            k = int(cruce.get("modulos") or 0) if destino and destino != s["nombre"] else 0
            k = min(max(k, 0), ns)
            d = salida.setdefault(inv, {})
            d[s["nombre"]] = d.get(s["nombre"], 0) + (ns - k) * npar
            if k:
                d[destino] = d.get(destino, 0) + k * npar
    return salida


def factores_recorte(superficies: list[Mapping[str, Any]], resultados: Mapping[str, Mapping[str, Any]],
                     paneles: Mapping[str, Mapping[str, Any]],
                     inversores: list[Mapping[str, Any]]) -> dict:
    """Recorte por superficie y por inversor.

    Devuelve ``{"superficies": {nombre: {f_recorte, recorte_kWh}},
    "inversores": [{inversor_id, nombre, P_ac_nom_W, e_sin_recorte_kWh,
    recorte_kWh, pct, horas, superficies}]}``. Un inversor sin potencia AC
    nominal no recorta; uno con alguna superficie sin cadena se omite.
    """
    pac = {str(i.get("inversor_id")): p for i in inversores or [] if (p := potencia_ac_inversor(i))}
    nombres = {str(i.get("inversor_id")): (i.get("nombre") or str(i.get("inversor_id")))
               for i in inversores or []}
    salida_sup: dict[str, dict] = {}
    salida_inv: list[dict] = []
    if not pac:
        return {"superficies": salida_sup, "inversores": salida_inv}
    modulos_sup = {s["nombre"]: int(s.get("modulos") or 0) for s in superficies}

    def _ac_por_modulo(nombre: str) -> tuple[np.ndarray, float] | None:
        r, info = resultados.get(nombre), paneles.get(nombre)
        mods = modulos_sup.get(nombre, 0)
        if r is None or info is None or mods <= 0 or r.get("perfil_ac") is None:
            return None
        e_sup = float(r["poa_bruta_kWh_m2"]) * mods * float(info["panel"]["Pmax_stc"]) / 1000.0 * float(r["pr"])
        perfil = np.asarray(r["perfil_ac"], dtype=float)
        return perfil * (e_sup / mods), e_sup

    perdida_sup: dict[str, float] = {}
    energia_sup: dict[str, float] = {}
    for inv, partes in _modulos_por_inversor(superficies, set(pac)).items():
        curvas = {}
        for nombre, mods in partes.items():
            ac = _ac_por_modulo(nombre)
            if ac is None:
                curvas = None
                break
            curvas[nombre] = ac[0] * mods
            energia_sup[nombre] = ac[1]
        if not curvas:
            continue
        total = np.sum(list(curvas.values()), axis=0)
        recorte = np.maximum(total - pac[inv] / 1000.0, 0.0)
        with np.errstate(divide="ignore", invalid="ignore"):
            parte = {n: np.where(total > 0, c / total, 0.0) for n, c in curvas.items()}
        por_sup = {n: float((recorte * p).sum()) for n, p in parte.items()}
        for n, v in por_sup.items():
            perdida_sup[n] = perdida_sup.get(n, 0.0) + v
        e_sin = float(total.sum())
        rec = float(recorte.sum())
        salida_inv.append({
            "inversor_id": inv, "nombre": nombres.get(inv, inv), "P_ac_nom_W": pac[inv],
            "e_sin_recorte_kWh": e_sin, "recorte_kWh": rec,
            "pct": rec / e_sin * 100.0 if e_sin > 0 else 0.0,
            "horas": int(np.sum(recorte > 1e-9)), "superficies": por_sup,
        })
    for n, perdida in perdida_sup.items():
        e = energia_sup.get(n, 0.0)
        salida_sup[n] = {"recorte_kWh": perdida, "f_recorte": 1.0 - perdida / e if e > 0 else 1.0}
    return {"superficies": salida_sup, "inversores": salida_inv}


def tabla_recorte(resumen: list[Mapping[str, Any]]) -> list[dict]:
    """Filas «✂️ Recorte por inversor» para la pantalla."""
    return [{
        "Inversor": r["nombre"],
        "Potencia AC (kW)": f"{r['P_ac_nom_W'] / 1000:,.1f}",
        "AC sin recorte (kWh/año)": f"{r['e_sin_recorte_kWh']:,.0f}",
        "Recorte (kWh/año)": f"{r['recorte_kWh']:,.0f}",
        "Recorte (%)": f"{r['pct']:.2f} %",
        "Horas con recorte": r["horas"],
    } for r in resumen]
