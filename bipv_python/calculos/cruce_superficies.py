# -*- coding: utf-8 -*-
"""Strings que cruzan dos superficies en 🗺️ Vista 3D.

Spec ``05-perdidas-y-temperatura/string-cruza-superficies`` (29-sep-2026).

Un grupo de strings de la superficie A puede declarar
``cruce = {"uid": <superficie B>, "modulos": k}``: en cada string del grupo,
k de sus N serie módulos están en B. Consecuencias:

- **Módulos donde están:** A cuenta (N − k) × N paralelo de ese grupo y B
  suma k × N paralelo (área y energía de cada superficie con sus módulos).
- **Pérdida en serie:** hora a hora con diodos de bypass
  (``calculos.mismatch.perdida_string_bypass``, Spec B) con la POA de las dos
  superficies. La pérdida anual del string (ponderada por energía) L se aplica
  a sus módulos en las dos superficies:
  f_cruce = 1 − Σ (L × módulos del string en la superficie) ÷ módulos de la superficie.
"""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd

from calculos.mismatch import perdida_string_bypass


def _entero(valor: Any) -> int | None:
    try:
        v = int(valor)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def _grupos(sup: Mapping[str, Any]) -> list[dict]:
    from calculos.diseno_electrico_multisup import grupos_de_superficie
    return grupos_de_superficie(sup)


def tiene_cruce(sup: Mapping[str, Any]) -> bool:
    """True si algún grupo de la superficie declara un cruce."""
    return any(isinstance(g.get("cruce"), Mapping) and g["cruce"].get("uid") for g in _grupos(sup))


def cruces_del_proyecto(superficies: list[Mapping[str, Any]]) -> list[dict]:
    """Cruces válidos de las superficies activas (los inválidos los reporta
    ``validar_cruces``)."""
    activas = [s for s in superficies if s.get("activa", True)]
    por_uid = {str(s.get("uid")): s for s in activas}
    salida = []
    for sup in activas:
        for g in _grupos(sup):
            c = g.get("cruce")
            if not isinstance(c, Mapping) or not c.get("uid"):
                continue
            destino = por_uid.get(str(c["uid"]))
            n_s, n_p, k = _entero(g.get("n_serie")), _entero(g.get("n_paralelo")), _entero(c.get("modulos"))
            if (destino is None or destino is sup or not n_s or not n_p or not k or k >= n_s):
                continue
            salida.append({
                "origen": sup["nombre"], "gid": str(g.get("gid", "G1")),
                "destino": destino["nombre"], "uid_destino": str(c["uid"]),
                "n_serie": n_s, "n_paralelo": n_p, "k": k,
            })
    return salida


def validar_cruces(superficies: list[Mapping[str, Any]],
                   paneles: Mapping[str, Mapping[str, Any]]) -> tuple[list[str], list[str]]:
    """(bloqueos 🔴, avisos 🟡) de los cruces declarados."""
    todas = {str(s.get("uid")): s for s in superficies}
    bloqueos, avisos = [], []
    for sup in superficies:
        if not sup.get("activa", True):
            continue
        for g in _grupos(sup):
            c = g.get("cruce")
            if not isinstance(c, Mapping) or not c.get("uid"):
                continue
            # Misma etiqueta que la tabla de ⚡ Diseño eléctrico (_etiquetas).
            etiqueta = f"«{sup['nombre']} · {g.get('gid', 'G1')}»"
            destino = todas.get(str(c["uid"]))
            if destino is None:
                bloqueos.append(f"{etiqueta}: el string cruza a una superficie que no existe.")
                continue
            if destino is sup or str(c["uid"]) == str(sup.get("uid")):
                bloqueos.append(f"{etiqueta}: el cruce apunta a la misma superficie.")
                continue
            if not destino.get("activa", True):
                bloqueos.append(f"{etiqueta}: el string cruza a «{destino['nombre']}», que no está activa.")
                continue
            n_s, k = _entero(g.get("n_serie")), c.get("modulos")
            if n_s:
                try:
                    k_int = int(k)
                except (TypeError, ValueError):
                    k_int = -1
                if not 1 <= k_int <= n_s - 1:
                    bloqueos.append(
                        f"{etiqueta}: los módulos en «{destino['nombre']}» deben estar entre 1 y "
                        f"{n_s - 1} (el string tiene {n_s} en serie)."
                    )
                    continue
            p_o = (paneles.get(sup["nombre"]) or {}).get("nombre")
            p_d = (paneles.get(destino["nombre"]) or {}).get("nombre")
            if p_o and p_d and p_o != p_d:
                bloqueos.append(
                    f"{etiqueta}: un string es de un solo panel; «{sup['nombre']}» usa {p_o} y "
                    f"«{destino['nombre']}» usa {p_d}. Usa el mismo panel en las dos superficies."
                )
                continue
            avisos.append(
                f"{etiqueta}: cada string cruza a «{destino['nombre']}» ({k} de {n_s} módulos). "
                "En serie, la corriente la marca la parte con menos luz o sus diodos la sacan: "
                "se resta esa pérdida hora a hora. Si puedes, conecta cada orientación a su propio MPPT."
            )
    return bloqueos, avisos


def modulos_fisicos_por_superficie(superficies: list[Mapping[str, Any]]) -> dict[str, int]:
    """Módulos de cada superficie activa contados donde están físicamente."""
    from calculos.diseno_electrico_multisup import modulos_de_superficie
    salida = {s["nombre"]: modulos_de_superficie(s) for s in superficies if s.get("activa", True)}
    for c in cruces_del_proyecto(superficies):
        movidos = c["k"] * c["n_paralelo"]
        salida[c["origen"]] -= movidos
        salida[c["destino"]] = salida.get(c["destino"], 0) + movidos
    return salida


def perdida_cruce(poa_origen: pd.DataFrame, poa_destino: pd.DataFrame, n_serie: int, k: int) -> dict:
    """Pérdida del string (N − k módulos en el origen, k en el destino)."""
    g_o = poa_origen["poa_global"].to_numpy(dtype=float)
    g_d = poa_destino["poa_global"].to_numpy(dtype=float)
    if len(g_o) != len(g_d):
        raise ValueError("Las POA de las dos superficies no tienen las mismas horas.")
    a = (n_serie - k) / n_serie
    ideal, string = perdida_string_bypass([g_o, g_d], [a, 1.0 - a])
    perdida = (1.0 - string.sum() / ideal.sum()) * 100.0 if ideal.sum() > 0 else 0.0
    with np.errstate(invalid="ignore", divide="ignore"):
        f_h = np.where(ideal > 0, string / np.maximum(ideal, 1e-12), 1.0)
    return {"perdida_pct": float(perdida), "factor_horario": np.clip(f_h, 0.0, 1.0)}


def factores_cruce(superficies: list[Mapping[str, Any]],
                   poas: Mapping[str, pd.DataFrame]) -> dict[str, dict]:
    """``{nombre: {"f_cruce", "detalle"}}`` para las superficies con módulos de
    strings que cruzan. Sin POA de alguna de las dos: sin factor y ``error``."""
    modulos = modulos_fisicos_por_superficie(superficies)
    salida: dict[str, dict] = {}
    for c in cruces_del_proyecto(superficies):
        p_o, p_d = poas.get(c["origen"]), poas.get(c["destino"])
        if p_o is None or p_d is None:
            for n in (c["origen"], c["destino"]):
                salida.setdefault(n, {"f_cruce": 1.0, "detalle": [], "perdida_mod": 0.0})["error"] = (
                    f"falta la POA de «{c['origen'] if p_o is None else c['destino']}» para el string "
                    f"que cruza ({c['origen']} {c['gid']})"
                )
            continue
        r = perdida_cruce(p_o, p_d, c["n_serie"], c["k"])
        L = r["perdida_pct"] / 100.0
        for n, mods in ((c["origen"], (c["n_serie"] - c["k"]) * c["n_paralelo"]),
                        (c["destino"], c["k"] * c["n_paralelo"])):
            d = salida.setdefault(n, {"f_cruce": 1.0, "detalle": [], "perdida_mod": 0.0})
            d["perdida_mod"] += L * mods
            d["detalle"].append({"string": f"{c['origen']} {c['gid']} ↔ {c['destino']}",
                                 "modulos": mods, "perdida_pct": r["perdida_pct"]})
    for n, d in salida.items():
        total = modulos.get(n, 0)
        d["f_cruce"] = 1.0 - d.pop("perdida_mod") / total if total > 0 else 1.0
    return salida
