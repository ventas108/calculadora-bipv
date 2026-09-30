# -*- coding: utf-8 -*-
"""⚡ Eléctrico por bloques de una granja (🌾 Granja FV, fase 5).

Spec ``07-informes/granja-electrico-bloques`` (30-sep-2026).

Parte del campo de ``granja_fv.calcular_campo`` y de los datos eléctricos
de 📐 Dimensionamiento (módulos en serie, reparto de strings por inversor):

1. **Strings por fila:** los módulos de cada fila se recorren de izquierda a
   derecha, columna por columna de la mesa; cada ``N_serie`` módulos forman
   un string. Si una fila no es múltiplo de ``N_serie``, el string que
   sobra sigue en la fila siguiente (se avisa: cable extra entre filas).
2. **Bloques:** los strings, en orden, llenan los inversores según el
   reparto (por ejemplo 6 + 5): cada inversor recibe filas vecinas.
3. **Cables:** el inversor va en la cabecera (a la izquierda del campo) o en
   el centro de su bloque, a la altura media de sus filas. Largo DC de un
   string (ida, un conductor) = (recorrido en L desde el extremo más cercano
   del string hasta el inversor + medio largo del string, porque el otro
   polo vuelve por la fila + bajada desde la mesa) × (1 + holgura). El AC va
   de cada inversor al punto de conexión, en L, más 2 m de bajadas.
4. **Caída de tensión** (cobre a 45 °C, IEC 60228):
   DC ``ΔV% = 2·L·ρ·I_mp ÷ (S·V_mp_string)``;
   AC trifásico ``ΔV% = √3·L·ρ·I ÷ (S·V_línea)`` con ``I = P_ac ÷ (√3·V)``.
   Referencia NTC 2050 (sección 210-19, nota): 3 % por circuito.

Los tramos DC salen uno por string (``n_paneles = N_serie``): así
``diagrama_unifilar.calcular_perdida_ohmica`` suma la pérdida exacta de cada
string con su propia longitud.

Módulo puro: sin Streamlit.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from calculos.diagrama_unifilar import _resistividad_cobre

T_DISENO_C = 45.0
LIMITE_CAIDA_PCT = 3.0
HOLGURA_DEFECTO = 0.10
BAJADA_AC_M = 2.0
SEPARACION_INVERSOR_M = 1.0
ESQUINAS = {
    "frente_izquierda": "Esquina de adelante a la izquierda",
    "frente_derecha": "Esquina de adelante a la derecha",
    "atras_izquierda": "Esquina de atrás a la izquierda",
    "atras_derecha": "Esquina de atrás a la derecha",
}
UBICACIONES_INVERSOR = {
    "cabecera": "Cabecera de las filas (a la izquierda del campo)",
    "centro": "Centro de su bloque",
}


def _modulos_por_fila(campo: Mapping[str, Any]) -> dict[int, list[float]]:
    """Posición x (m) del centro de cada módulo, fila por fila, de izquierda a derecha."""
    mp = max(int(round(campo["ancho_mesa_m"] / max(campo["d_pend"], 1e-9) + 0.01)), 1)
    paso = float(campo["d_fila"]) + 0.02
    filas: dict[int, list[float]] = {}
    for m in sorted(campo["mesas"], key=lambda m: (m["fila"], m["x0"])):
        xs = filas.setdefault(int(m["fila"]), [])
        for k in range(int(m["modulos"])):
            xs.append(m["x0"] + (k // mp) * paso + campo["d_fila"] / 2.0)
    return filas


def _y_fila(campo: Mapping[str, Any], fila: int) -> float:
    m = next(m for m in campo["mesas"] if m["fila"] == fila)
    return (m["y0"] + m["y1"]) / 2.0


def armar_strings(campo: Mapping[str, Any], n_serie: int) -> dict:
    """Strings de ``n_serie`` módulos recorriendo las filas en orden."""
    n_serie = int(n_serie)
    filas = _modulos_por_fila(campo)
    strings, actual = [], []
    for f in sorted(filas):
        for x in filas[f]:
            actual.append((f, x))
            if len(actual) == n_serie:
                strings.append(actual)
                actual = []
    sobrantes = len(actual)
    salida = []
    for i, mods in enumerate(strings):
        filas_s = sorted({f for f, _ in mods})
        xs = [x for _, x in mods]
        y = sum(_y_fila(campo, f) for f, _ in mods) / len(mods)
        salida.append({"id": i + 1, "filas": filas_s, "x_min": min(xs), "x_max": max(xs),
                       "y": y, "cruza_filas": len(filas_s) > 1,
                       "largo_m": (max(xs) - min(xs)) + float(campo["d_fila"])})
    por_fila = {}
    for s in salida:
        for f in s["filas"]:
            por_fila[f] = por_fila.get(f, 0) + 1
    return {"strings": salida, "sobrantes": sobrantes, "por_fila": por_fila,
            "cruzan": sum(1 for s in salida if s["cruza_filas"])}


def _reparto_valido(reparto: Sequence[int] | None, n_strings: int) -> list[int]:
    rep = [int(r) for r in (reparto or []) if int(r) > 0]
    if sum(rep) == n_strings and rep:
        return rep
    n_inv = max(len(rep), 1)
    base, extra = divmod(n_strings, n_inv)
    return [base + (1 if i < extra else 0) for i in range(n_inv)]


def _punto_conexion(campo: Mapping[str, Any], esquina: str) -> tuple[float, float]:
    W, L = float(campo["ancho_terreno_m"]), float(campo["largo_terreno_m"])
    return {"frente_izquierda": (0.0, 0.0), "frente_derecha": (W, 0.0),
            "atras_izquierda": (0.0, L), "atras_derecha": (W, L)}.get(esquina, (0.0, 0.0))


def disenar_bloques(campo: Mapping[str, Any], panel: Mapping[str, Any], n_serie: int,
                    reparto: Sequence[int] | None, p_ac_inversor_w: float, *,
                    ubicacion_inversor: str = "cabecera", punto_conexion: str = "frente_izquierda",
                    calibre_dc_mm2: float = 6.0, calibre_ac_mm2: float = 70.0,
                    tension_ac_v: float = 400.0, holgura: float = HOLGURA_DEFECTO) -> dict:
    """Strings por fila, bloques por inversor, largo de cables y caída de tensión."""
    arm = armar_strings(campo, n_serie)
    strings = arm["strings"]
    rep = _reparto_valido(reparto, len(strings))
    rho = _resistividad_cobre(T_DISENO_C)
    imp = float(panel.get("Imp_stc") or 0.0)
    vmp_string = float(panel.get("Vmp_stc") or 0.0) * int(n_serie)
    bajada = float(campo["altura_centro_m"])
    x_poi, y_poi = _punto_conexion(campo, punto_conexion)

    bloques, i0 = [], 0
    for k, n in enumerate(rep):
        grupo = strings[i0:i0 + n]
        i0 += n
        if not grupo:
            continue
        ys = [s["y"] for s in grupo]
        x_inv = (min(s["x_min"] for s in grupo) - SEPARACION_INVERSOR_M if ubicacion_inversor == "cabecera"
                 else (min(s["x_min"] for s in grupo) + max(s["x_max"] for s in grupo)) / 2.0)
        y_inv = (min(ys) + max(ys)) / 2.0
        for s in grupo:
            extremo = min(abs(s["x_min"] - x_inv), abs(s["x_max"] - x_inv)) \
                if not (s["x_min"] <= x_inv <= s["x_max"]) else 0.0
            ida = extremo + abs(s["y"] - y_inv) + s["largo_m"] / 2.0 + bajada
            s["inversor"] = k + 1
            s["longitud_dc_m"] = round(ida * (1.0 + holgura), 1)
            s["caida_dc_pct"] = round(200.0 * s["longitud_dc_m"] * rho * imp
                                      / (float(calibre_dc_mm2) * vmp_string), 3) if vmp_string > 0 else None
        l_ac = round((abs(x_inv - x_poi) + abs(y_inv - y_poi) + BAJADA_AC_M) * (1.0 + holgura), 1)
        i_ac = float(p_ac_inversor_w) / (math.sqrt(3.0) * float(tension_ac_v)) if tension_ac_v else 0.0
        caida_ac = (100.0 * math.sqrt(3.0) * l_ac * rho * i_ac / (float(calibre_ac_mm2) * float(tension_ac_v))
                    if tension_ac_v else None)
        bloques.append({
            "inversor": k + 1, "strings": len(grupo), "modulos": len(grupo) * int(n_serie),
            "filas": sorted({f for s in grupo for f in s["filas"]}),
            "x_inversor": round(x_inv, 2), "y_inversor": round(y_inv, 2),
            "longitud_ac_m": l_ac, "corriente_ac_a": round(i_ac, 1),
            "caida_ac_pct": round(caida_ac, 3) if caida_ac is not None else None,
            "dc_media_m": round(sum(s["longitud_dc_m"] for s in grupo) / len(grupo), 1),
            "dc_max_m": max(s["longitud_dc_m"] for s in grupo),
        })

    caidas_dc = [s["caida_dc_pct"] for s in strings if s.get("caida_dc_pct") is not None]
    # Resistencia DC efectiva vista desde el total (Σ fracción² · R_string, la
    # misma de calcular_perdida_ohmica) y pérdida a STC con I_mp en cada string.
    r_strings = [2.0 * s["longitud_dc_m"] * rho / float(calibre_dc_mm2) for s in strings]
    n_s = len(strings)
    r_ef = sum(r / n_s ** 2 for r in r_strings) if n_s else 0.0
    p_stc = n_s * vmp_string * imp
    perdida_stc = 100.0 * sum(imp ** 2 * r for r in r_strings) / p_stc if p_stc > 0 else None
    caidas_ac = [b["caida_ac_pct"] for b in bloques if b["caida_ac_pct"] is not None]
    return {
        "n_serie": int(n_serie), "n_strings": len(strings), "sobrantes": arm["sobrantes"],
        "strings_por_fila": arm["por_fila"], "strings_cruzan_filas": arm["cruzan"],
        "reparto": rep, "bloques": bloques,
        "strings": [{**{k: s[k] for k in ("id", "filas", "inversor", "longitud_dc_m", "caida_dc_pct",
                                            "cruza_filas")},
                     "x_min": round(s["x_min"], 2), "x_max": round(s["x_max"], 2), "y": round(s["y"], 2)}
                    for s in strings],
        "punto_conexion_xy": [round(x_poi, 2), round(y_poi, 2)],
        "calibre_dc_mm2": float(calibre_dc_mm2), "calibre_ac_mm2": float(calibre_ac_mm2),
        "tension_ac_v": float(tension_ac_v), "holgura": float(holgura),
        "ubicacion_inversor": ubicacion_inversor, "punto_conexion": punto_conexion,
        "caida_dc_max_pct": round(max(caidas_dc), 3) if caidas_dc else None,
        "resistencia_dc_efectiva_mohm": round(1000.0 * r_ef, 2),
        "perdida_dc_stc_pct": round(perdida_stc, 3) if perdida_stc is not None else None,
        "caida_ac_max_pct": round(max(caidas_ac), 3) if caidas_ac else None,
        "dc_total_m": round(2.0 * sum(s["longitud_dc_m"] for s in strings), 1),
        "ac_total_m": round(3.0 * sum(b["longitud_ac_m"] for b in bloques), 1),
        "ac_media_m": round(sum(b["longitud_ac_m"] for b in bloques) / len(bloques), 1) if bloques else 0.0,
    }


def avisos_bloques(diseno: Mapping[str, Any], modulos_proyecto: int) -> list[dict]:
    """Comprobaciones ``{id, nivel, texto}`` del diseño eléctrico por bloques."""
    out = []
    n = int(diseno["n_strings"]) * int(diseno["n_serie"])
    if diseno["sobrantes"] or n != int(modulos_proyecto):
        out.append({"id": "strings_completos", "nivel": "🔴", "texto":
                    f"Los módulos del campo no forman strings completos de {diseno['n_serie']}: "
                    f"{diseno['n_strings']} strings = {n} módulos y sobran {diseno['sobrantes']}. "
                    "Ajusta los módulos del proyecto o los módulos en serie en 📐 Dimensionamiento."})
    else:
        out.append({"id": "strings_completos", "nivel": "🟢", "texto":
                    f"{diseno['n_strings']} strings de {diseno['n_serie']} módulos = {n} módulos, "
                    f"repartidos {' + '.join(str(r) for r in diseno['reparto'])} entre "
                    f"{len(diseno['bloques'])} inversor(es)."})
    if diseno["strings_cruzan_filas"]:
        out.append({"id": "cruzan_filas", "nivel": "🟠", "texto":
                    f"{diseno['strings_cruzan_filas']} string(s) empiezan en una fila y terminan en la "
                    "siguiente: se necesita cable extra entre filas. Si puedes, usa un número de módulos "
                    "por fila que sea múltiplo de los módulos en serie."})
    for clave, nombre in (("caida_dc_max_pct", "DC (string más lejano)"), ("caida_ac_max_pct", "AC (inversor más lejano)")):
        v = diseno.get(clave)
        if v is None:
            continue
        ok = v <= LIMITE_CAIDA_PCT
        out.append({"id": clave, "nivel": "🟢" if ok else "🟠", "texto":
                    f"Caída de tensión {nombre}: {v:.2f} % " + (
                        f"≤ {LIMITE_CAIDA_PCT:.0f} % (NTC 2050)." if ok else
                        f"> {LIMITE_CAIDA_PCT:.0f} % (NTC 2050): sube el calibre o acerca el inversor.")})
    return out


def tramos_para_unifilar(diseno: Mapping[str, Any]) -> list[dict]:
    """Un tramo DC por string para ``calcular_perdida_ohmica`` (pérdida exacta por string)."""
    return [{"nombre": f"String {s['id']} (INV-{s['inversor']})", "n_paneles": int(diseno["n_serie"]),
             "longitud_m": float(s["longitud_dc_m"]), "calibre_mm2": float(diseno["calibre_dc_mm2"])}
            for s in diseno["strings"]]


CONFIG_DEFECTO: dict[str, Any] = {
    "ubicacion_inversor": "cabecera", "punto_conexion": "frente_izquierda",
    "calibre_dc_mm2": 6.0, "calibre_ac_mm2": 70.0, "tension_ac_v": 400.0, "holgura": HOLGURA_DEFECTO,
}


def diseno_desde_estado(estado: Mapping[str, Any]) -> dict | None:
    """Diseño por bloques recalculado con los datos guardados del proyecto.

    Lo usan 🌾 Granja FV, ⚡ Diagrama Unifilar y 📋 Ficha RETIE: nunca un
    resultado viejo. ``None`` si el proyecto no tiene campo de granja
    (``granja_fv``), panel, módulos en serie o el campo tiene errores.
    """
    from calculos.granja_fv import calcular_campo, dimensiones_modulo, geometria_desde_estado, modulos_del_proyecto

    panel = dict(estado.get("panel_dict") or {})
    n_serie = int(estado.get("N_serie") or 0)
    if not estado.get("granja_fv") or not panel or n_serie <= 0:
        return None
    dims = dimensiones_modulo(panel)
    proy = modulos_del_proyecto(estado)
    campo = calcular_campo(geometria_desde_estado(estado, dims), dims, proy["n"],
                           float(panel.get("Pmax_stc") or 0.0))
    if campo["errores"] or not campo["mesas"]:
        return None
    cfg = {**CONFIG_DEFECTO, **dict(estado.get("granja_electrico_cfg") or {})}
    inv = dict(estado.get("inversor_dict_dim") or {})
    p_ac = float(inv.get("P_ac_nom_W") or (inv.get("ficha") or {}).get("P_ac_nom_W") or 0.0)
    d = disenar_bloques(campo, panel, n_serie, estado.get("reparto_strings_inversores"), p_ac,
                        ubicacion_inversor=cfg["ubicacion_inversor"], punto_conexion=cfg["punto_conexion"],
                        calibre_dc_mm2=float(cfg["calibre_dc_mm2"]), calibre_ac_mm2=float(cfg["calibre_ac_mm2"]),
                        tension_ac_v=float(cfg["tension_ac_v"]), holgura=float(cfg["holgura"]))
    d["modulos_proyecto"] = proy["n"]
    d["modulos_colocados"] = campo["modulos_colocados"]
    return d


def checks_retie(diseno: Mapping[str, Any]) -> list[dict]:
    """Avisos del diseño por bloques en el formato de la 📋 Ficha RETIE."""
    nivel = {"🟢": "OK", "🟠": "PENDIENTE", "🔴": "ERROR"}
    titulos = {"strings_completos": "Granja: strings y bloques por inversor",
               "cruzan_filas": "Granja: strings que cruzan filas",
               "caida_dc_max_pct": "Granja: caída de tensión DC",
               "caida_ac_max_pct": "Granja: caída de tensión AC"}
    return [{"nivel": nivel.get(a["nivel"], "PENDIENTE"), "titulo": titulos.get(a["id"], a["id"]),
             "detalle": a["texto"]}
            for a in avisos_bloques(diseno, int(diseno.get("modulos_proyecto") or 0))]
