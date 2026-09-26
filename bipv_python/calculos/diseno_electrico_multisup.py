"""Diseño eléctrico multi-superficie: inversores con ficha y grupos de strings.

Spec ``03-dimensionamiento/diseno-electrico-multisuperficie`` (fase A1):

- cada superficie tiene uno o más grupos de strings
  ``{gid, topologia, inversor_id, mppt, n_serie, n_paralelo}``;
- cada inversor tiene ``clase``, ``origen_ficha`` (proyecto, catálogo o
  manual), ``nombre``, ``ficha``, ``eta_inversor`` y ``P_ac_nom_W``;
- ``validar_diseno_electrico`` revisa grupo, MPPT, inversor y superficie con
  las mismas funciones y temperaturas de 📐 Dimensionamiento, y devuelve cada
  comprobación con su valor, límite, fórmula y fuente.

Este módulo es puro: no conoce Streamlit ni cambia ninguna energía. La Spec B
agregará las topologías ``microinversor`` y ``optimizador`` sobre la misma
estructura.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from calculos.dimensionamiento import (
    calcular_vmp_string,
    calcular_voc_string,
    evaluar_compatibilidad_string,
    evaluar_relacion_dc_ac,
)

TOPOLOGIAS_CONOCIDAS = ("string", "microinversor", "optimizador")
TOPOLOGIAS_SOPORTADAS = ("string",)
CLASES_SOPORTADAS = ("string",)
ORIGENES_FICHA = ("proyecto", "catalogo", "manual")
FS_ISC = 1.25
COBERTURA_MINIMA = 0.80
TEMPS_POR_DEFECTO = {"T_frio": -5.0, "T_real": 36.35, "T_extremo": 41.94}
_CLAVES_TEMPS = (("T_frio", "T_min_diseno"), ("T_real", "T_cel_realista"),
                 ("T_extremo", "T_cel_extremo"))
_ORDEN_ESTADO = {"verde": 0, "amarillo": 1, "rojo": 2}


# ── Números ──────────────────────────────────────────────────────────────────
def _positivo(valor: Any) -> float | None:
    if isinstance(valor, bool):
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if math.isfinite(numero) and numero > 0 else None


def _entero_positivo(valor: Any) -> int | None:
    numero = _positivo(valor)
    if numero is None or not float(numero).is_integer():
        return None
    return int(numero)


def _peor(*estados: str) -> str:
    return max(estados, key=lambda e: _ORDEN_ESTADO[e], default="verde")


# ── Modelo ───────────────────────────────────────────────────────────────────
def normalizar_ficha_inversor(raw: Mapping[str, Any] | None) -> dict:
    """Ficha con el contrato de esta Spec, venga del Excel o del catálogo interno."""
    raw = dict(raw or {})
    vmppt_min = _positivo(raw.get("Vmppt_min"))
    ficha = {
        "Vdc_max": _positivo(raw.get("Vdc_max")),
        "Vmppt_min": vmppt_min,
        "Vmppt_activo_min": _positivo(raw.get("Vmppt_activo_min") or raw.get("V_mppt_activo")) or vmppt_min,
        "Vmppt_max": _positivo(raw.get("Vmppt_max")),
        "I_max_tracker": _positivo(raw.get("I_max_tracker")),
        "Isc_max_tracker": _positivo(raw.get("Isc_max_tracker")),
        "N_mppt": _entero_positivo(raw.get("N_mppt") or raw.get("n_trackers")),
        "n_strings_tracker": _entero_positivo(raw.get("n_strings_tracker") or raw.get("N_strings_nativo")),
        "P_ac_nom_W": _positivo(raw.get("P_ac_nom_W")) or (
            _positivo(raw.get("P_ac_nom_kW")) and _positivo(raw.get("P_ac_nom_kW")) * 1000.0),
        "eficiencia_max": _positivo(raw.get("eficiencia_max")),
    }
    return {k: v for k, v in ficha.items() if v is not None}


def inversor_normalizado(inversor: Mapping[str, Any]) -> dict:
    """Inversor con los campos de esta Spec; uno antiguo se lee como manual."""
    inv = dict(inversor)
    inv.setdefault("clase", "string")
    if inv.get("origen_ficha") not in ORIGENES_FICHA:
        inv["origen_ficha"] = "manual"
    inv.setdefault("nombre", "")
    inv["ficha"] = normalizar_ficha_inversor(inv.get("ficha"))
    return inv


def grupos_de_superficie(superficie: Mapping[str, Any]) -> list[dict]:
    """Grupos de strings de la superficie (migra los campos antiguos a G1)."""
    grupos = superficie.get("grupos")
    if isinstance(grupos, list) and grupos:
        return [dict(g) for g in grupos]
    if any(superficie.get(c) is not None for c in ("inversor_id", "n_serie", "n_paralelo")):
        return [{
            "gid": "G1", "topologia": "string",
            "inversor_id": superficie.get("inversor_id"), "mppt": 1,
            "n_serie": superficie.get("n_serie"), "n_paralelo": superficie.get("n_paralelo"),
        }]
    return []


def campos_legacy_desde_grupos(grupos: list[Mapping[str, Any]]) -> dict:
    """``inversor_id``/``n_serie``/``n_paralelo`` de superficie que siguen
    leyendo el modo físico, el bypass y el MPPT hasta la fase A2 (espejo del
    grupo único; vacíos si hay varios grupos o ninguno)."""
    if len(grupos) == 1:
        g = grupos[0]
        return {"inversor_id": g.get("inversor_id"), "n_serie": g.get("n_serie"),
                "n_paralelo": g.get("n_paralelo")}
    return {"inversor_id": None, "n_serie": None, "n_paralelo": None}


def temperaturas_diseno(session_state: Mapping[str, Any]) -> dict:
    """Temperaturas de 📐 Dimensionamiento; si falta alguna, las de siempre
    con ``origen = "por_defecto"`` (la validación lo avisa)."""
    temps, origen = {}, "proyecto"
    for clave, clave_ss in _CLAVES_TEMPS:
        try:
            temps[clave] = float(session_state[clave_ss])
        except (KeyError, TypeError, ValueError):
            temps[clave] = TEMPS_POR_DEFECTO[clave]
            origen = "por_defecto"
    temps["origen"] = origen
    return temps


# ── Rango de N serie ─────────────────────────────────────────────────────────
def _limites_tension(ficha: Mapping[str, Any]) -> tuple[float, float, float] | None:
    vdc = _positivo(ficha.get("Vdc_max"))
    vmin = _positivo(ficha.get("Vmppt_activo_min") or ficha.get("Vmppt_min"))
    vmax = _positivo(ficha.get("Vmppt_max"))
    return (vdc, vmin, vmax) if vdc and vmin and vmax else None


def rango_n_serie(panel: Mapping[str, Any], ficha: Mapping[str, Any],
                  temps: Mapping[str, Any]) -> tuple[int, int] | None:
    """(N mín, N máx) que cumplen las condiciones de tensión de
    ``evaluar_compatibilidad_string``: Voc en frío ≤ Vdc máx. y Vmp real y
    extremo dentro de [MPPT mín. activo, MPPT máx.]. ``None`` si la ficha no
    trae las tensiones o ningún N cabe."""
    limites = _limites_tension(ficha)
    try:
        voc, vmp, beta = float(panel["Voc_stc"]), float(panel["Vmp_stc"]), float(panel["Tk_beta"])
    except (KeyError, TypeError, ValueError):
        return None
    if limites is None:
        return None
    vdc, vmin, vmax = limites
    validos = []
    for n in range(1, 200):
        voc_frio = calcular_voc_string(n, voc, beta, float(temps["T_frio"]))
        if voc_frio > vdc:
            break
        vmp_real = calcular_vmp_string(n, vmp, beta, float(temps["T_real"]))
        vmp_ext = calcular_vmp_string(n, vmp, beta, float(temps["T_extremo"]))
        if vmin <= min(vmp_real, vmp_ext) and max(vmp_real, vmp_ext) <= vmax:
            validos.append(n)
    return (min(validos), max(validos)) if validos else None


# ── Validación ───────────────────────────────────────────────────────────────
def _check(nombre, valor, limite, unidad, formula, fuente, estado) -> dict:
    return {"nombre": nombre, "valor": valor, "limite": limite, "unidad": unidad,
            "formula": formula, "fuente": fuente, "estado": estado}


def _fuente_ficha(inv: Mapping[str, Any]) -> str:
    origen = inv.get("origen_ficha")
    if origen == "proyecto":
        return f"ficha del inversor del proyecto ({inv.get('nombre') or 'sin nombre'})"
    if origen == "catalogo":
        return f"ficha del catálogo ({inv.get('nombre') or 'sin nombre'})"
    return "inversor manual (sin ficha)"


def _orientacion(sup: Mapping[str, Any]) -> tuple[float, float]:
    return (round(float(sup.get("tilt_deg", 0.0)), 1), round(float(sup.get("azimuth_deg", 0.0)), 1))


def validar_diseno_electrico(
    superficies: list[Mapping[str, Any]],
    inversores: list[Mapping[str, Any]],
    paneles: Mapping[str, Mapping[str, Any]],
    temps: Mapping[str, Any],
) -> dict:
    """Diagnóstico del diseño eléctrico (ver ``diseno.md`` de la Spec).

    ``paneles[nombre_superficie]`` es ``{"panel", "nombre"}`` (como
    ``panel_superficie.eficiencias_superficies``). No muta las entradas.
    """
    invs = {str(i.get("inversor_id")): inversor_normalizado(i) for i in inversores
            if i.get("inversor_id")}
    bloqueos: list[str] = []
    avisos: list[str] = []
    t_txt = (f"T mín {temps['T_frio']:g} °C, T celda {temps['T_real']:g}/"
             f"{temps['T_extremo']:g} °C ({'proyecto' if temps.get('origen') == 'proyecto' else 'por defecto'})")
    if temps.get("origen") != "proyecto":
        avisos.append(
            "Se usan temperaturas de diseño por defecto (−5 °C / 36,35 °C / 41,94 °C): "
            "define las del proyecto en 📐 Dimensionamiento."
        )

    activas = [s for s in superficies if s.get("activa", True)]
    # (inversor, mppt) → grupos
    por_mppt: dict[tuple[str, int], list[dict]] = {}
    salida_grupos, salida_sups = [], []

    for sup in activas:
        nombre = sup.get("nombre", "?")
        grupos = grupos_de_superficie(sup)
        info_panel = paneles.get(nombre)
        panel = dict(info_panel["panel"]) if info_panel else None
        checks_sup = []
        if not grupos:
            bloqueos.append(f"«{nombre}»: sin diseño eléctrico (agrega un inversor y sus strings).")
            checks_sup.append(_check("Diseño eléctrico definido", 0, 1, "grupos",
                                     "grupos de strings de la superficie", "🔌 Inversores por superficie", "rojo"))
        modulos = 0
        for g in grupos:
            gid = g.get("gid", "G?")
            etiqueta = f"«{nombre} · {gid}»"
            checks, estado = [], "verde"

            def falla(texto, nombre_check):
                nonlocal estado
                bloqueos.append(f"{etiqueta}: {texto}")
                checks.append(_check(nombre_check, None, None, "", texto, "grupo", "rojo"))
                estado = "rojo"

            topologia = g.get("topologia") or "string"
            if topologia not in TOPOLOGIAS_SOPORTADAS:
                falla(f"topología «{topologia}» no soportada todavía (llega con la Spec B).", "Topología")
            inv_id = str(g.get("inversor_id") or "").strip()
            inv = invs.get(inv_id)
            if not inv_id:
                falla("sin inversor asignado.", "Inversor")
            elif inv is None:
                falla(f"el inversor «{inv_id}» no existe.", "Inversor")
            n_serie = _entero_positivo(g.get("n_serie"))
            n_par = _entero_positivo(g.get("n_paralelo"))
            mppt = _entero_positivo(g.get("mppt"))
            if n_serie is None:
                falla("N serie inválido (entero ≥ 1).", "N serie")
            if n_par is None:
                falla("N paralelo inválido (entero ≥ 1).", "N paralelo")
            if mppt is None:
                falla("MPPT inválido (entero ≥ 1).", "MPPT")
            if panel is None:
                falla("la superficie no tiene panel utilizable.", "Panel")
            if n_serie and n_par:
                modulos += n_serie * n_par
            rango = rango_n_serie(panel, inv["ficha"], temps) if (panel and inv) else None
            registro = {
                "uid": sup.get("uid"), "gid": gid, "superficie": nombre,
                "panel": info_panel.get("nombre") if info_panel else None,
                "inversor_id": inv_id or None, "mppt": mppt, "n_serie": n_serie,
                "n_paralelo": n_par, "rango_n_serie": rango, "checks": checks,
                "estado": estado, "_orientacion": _orientacion(sup), "_panel": panel,
            }
            salida_grupos.append(registro)
            if inv is not None and mppt:
                por_mppt.setdefault((inv_id, mppt), []).append(registro)

        # Cobertura del área
        area = _positivo(sup.get("area_m2")) or 0.0
        area_mod = None
        if panel:
            from calculos.panel_superficie import area_modulo
            area_mod = area_modulo(panel)
        area_inst = modulos * area_mod if area_mod else None
        cobertura = (area_inst / area * 100.0) if (area_inst is not None and area) else None
        if cobertura is not None:
            est = "rojo" if cobertura > 100.0 + 1e-9 else ("amarillo" if cobertura < COBERTURA_MINIMA * 100 else "verde")
            checks_sup.append(_check(
                "Módulos caben en el área", round(area_inst, 2), round(area, 2), "m²",
                f"módulos ({modulos}) × área del módulo ({area_mod:g} m²) ≤ área de la superficie",
                "grupos y ficha del panel", est))
            if est == "rojo":
                bloqueos.append(f"«{nombre}»: {modulos} módulos ocupan {area_inst:.1f} m² y la superficie tiene {area:.1f} m².")
            elif est == "amarillo":
                avisos.append(f"«{nombre}»: los módulos cubren el {cobertura:.0f} % del área.")
        salida_sups.append({
            "uid": sup.get("uid"), "superficie": nombre, "modulos": modulos,
            "area_instalada_m2": round(area_inst, 3) if area_inst is not None else None,
            "area_m2": area, "cobertura_pct": round(cobertura, 2) if cobertura is not None else None,
            "checks": checks_sup,
            "estado": _peor(*(c["estado"] for c in checks_sup)),
        })

    # Por MPPT (y compatibilidad del string de cada grupo con su MPPT)
    salida_mppt = []
    for (inv_id, mppt), grupos in sorted(por_mppt.items()):
        inv = invs[inv_id]
        ficha = inv["ficha"]
        fuente = _fuente_ficha(inv)
        checks = []
        paneles_mppt = {g["panel"] for g in grupos}
        orient = {g["_orientacion"] for g in grupos}
        strings = sum(g["n_paralelo"] or 0 for g in grupos)
        etiqueta = f"«{inv_id} · MPPT {mppt}»"
        if len(paneles_mppt) > 1:
            bloqueos.append(f"{etiqueta}: paneles distintos en el mismo MPPT ({', '.join(sorted(map(str, paneles_mppt)))}).")
            checks.append(_check("Un solo panel por MPPT", len(paneles_mppt), 1, "paneles",
                                 "referencias de panel en el MPPT", "grupos", "rojo"))
        # Strings en paralelo en un MPPT trabajan al MISMO voltaje: todos deben
        # tener el mismo número de módulos en serie (25-sep-2026, antes de A3).
        largos = {}
        for g in grupos:
            if isinstance(g["n_serie"], int) and not isinstance(g["n_serie"], bool) and g["n_serie"] >= 1:
                largos.setdefault(g["n_serie"], []).append(f"{g['superficie']} · {g['gid']}")
        if largos:
            valores = " y ".join(str(n) for n in sorted(largos))
            if len(largos) > 1:
                detalle = ", ".join(f"{nombre}: {n} módulos"
                                    for n in sorted(largos, reverse=True) for nombre in largos[n])
                bloqueos.append(
                    f"{etiqueta}: strings de distinto largo en el mismo MPPT ({detalle}). Los "
                    "strings que comparten un MPPT quedan en paralelo y trabajan al mismo voltaje; "
                    "con distinto número de módulos cada uno necesita un voltaje diferente, así "
                    "que el más corto o el más largo produce mucho menos y puede circular "
                    "corriente de uno al otro. Solución: pon el mismo N serie en todos los grupos "
                    "de este MPPT, o conéctalos en MPPT distintos."
                )
            checks.append(_check("Mismo N serie en el MPPT", valores, "un solo valor", "módulos",
                                 "todos los strings de un MPPT con el mismo N serie", "grupos",
                                 "rojo" if len(largos) > 1 else "verde"))
        if len(orient) > 1:
            avisos.append(f"{etiqueta}: orientaciones distintas en el mismo MPPT; la sección 6 cuantifica la pérdida.")
            checks.append(_check("Una orientación por MPPT", len(orient), 1, "orientaciones",
                                 "tilt/azimuth distintos en el MPPT", "grupos", "amarillo"))
        isc_total = sum(float(g["_panel"]["Isc_stc"]) * (g["n_paralelo"] or 0) * FS_ISC
                        for g in grupos if g["_panel"])
        isc_max = _positivo(ficha.get("Isc_max_tracker") or ficha.get("I_max_tracker"))
        # Entradas del MPPT: límite de CONEXIÓN (cuántos pares de cables caben
        # en el inversor). El límite FÍSICO es la corriente: si cabe, los
        # strings se unen antes del inversor con una caja combinadora
        # (fase A2, aprobada el 25-sep-2026).
        n_ent = ficha.get("n_strings_tracker")
        caja = False
        if not n_ent:
            est_s = "amarillo"
            avisos.append(f"{etiqueta}: la ficha no dice cuántos strings admite cada MPPT; "
                          "revisa la hoja de datos del inversor.")
        elif strings <= n_ent:
            est_s = "verde"
        elif isc_max and isc_total <= isc_max:
            est_s, caja = "amarillo", True
            avisos.append(
                f"{etiqueta}: {strings} strings y el MPPT tiene {n_ent} entrada(s). Caben por "
                f"corriente ({isc_total:.1f} A de {isc_max:.1f} A), así que se pueden unir antes "
                "del inversor con una caja combinadora o conectores en Y. Inclúyela en el diseño "
                "y en el presupuesto; con más de 2 strings en paralelo, normalmente cada string "
                "lleva su fusible."
            )
        else:
            est_s = "rojo"
            detalle = (f"{isc_total:.1f} A > límite {isc_max:.1f} A" if isc_max
                       else "la ficha no trae la corriente máxima del MPPT")
            bloqueos.append(
                f"{etiqueta}: {strings} strings y el MPPT tiene {n_ent} entrada(s); ni con caja "
                f"combinadora caben ({detalle}). Reparte los strings en otro MPPT u otro inversor."
            )
        checks.append(_check(
            "Strings ≤ entradas del MPPT", strings, n_ent, "strings",
            "Σ N paralelo de los grupos del MPPT ≤ entradas por MPPT (si no, caja combinadora "
            "cuando la corriente cabe)", fuente, est_s))
        if isc_max:
            est_i = "rojo" if isc_total > isc_max else ("amarillo" if isc_total > isc_max * 0.925 else "verde")
        else:
            est_i = "amarillo"
        checks.append(_check(
            "Isc del MPPT ≤ límite del tracker", round(isc_total, 2), isc_max, "A",
            f"Σ Isc × N paralelo × {FS_ISC}", fuente, est_i))
        if est_i == "rojo":
            bloqueos.append(f"{etiqueta}: Isc {isc_total:.1f} A > límite {isc_max:.1f} A.")
        elif est_i == "amarillo" and isc_max:
            avisos.append(f"{etiqueta}: la corriente ({isc_total:.1f} A) queda a menos de 7,5 % "
                          f"del límite del MPPT ({isc_max:.1f} A).")
        elif est_i == "amarillo":
            avisos.append(f"{etiqueta}: la ficha no trae la corriente máxima del MPPT; no se "
                          "puede verificar la corriente.")

        # Compatibilidad del string de cada grupo con este MPPT
        for g in grupos:
            if g["_panel"] is None or g["n_serie"] is None:
                continue
            compat = evaluar_compatibilidad_string(
                panel=g["_panel"], inversor=ficha, N_serie=g["n_serie"],
                T_frio=float(temps["T_frio"]), T_real=float(temps["T_real"]),
                T_extremo=float(temps["T_extremo"]), N_strings_tracker=max(1, strings),
                FS_isc=FS_ISC,
            )
            if not compat.get("evaluable"):
                g["checks"].append(_check(
                    "Compatibilidad del string", None, None, "",
                    "no validado: " + "; ".join(compat.get("mensajes", [])), fuente, "amarillo"))
                g["estado"] = _peor(g["estado"], "amarillo")
                avisos.append(f"«{g['superficie']} · {g['gid']}»: no validado ({fuente}).")
                continue
            vdc = ficha.get("Vdc_max")
            vmin = ficha.get("Vmppt_activo_min") or ficha.get("Vmppt_min")
            vmax = ficha.get("Vmppt_max")
            estado_c = "rojo" if not compat["compatible"] else ("amarillo" if compat.get("alerta_margen") else "verde")
            g["checks"].extend([
                _check("Voc en frío ≤ Vdc máximo", round(compat["Voc_frio"], 1), vdc, "V",
                       f"N × Voc × (1 + β·(T mín − 25)); {t_txt}", fuente,
                       "rojo" if compat["Voc_frio"] > vdc else "verde"),
                _check("Vmp real dentro del MPPT", round(compat["Vmp_real"], 1), f"{vmin:g}–{vmax:g}", "V",
                       f"N × Vmp × (1 + β·(T celda − 25)); {t_txt}", fuente,
                       "rojo" if not vmin <= compat["Vmp_real"] <= vmax else "verde"),
                _check("Vmp extremo dentro del MPPT", round(compat["Vmp_extremo"], 1), f"{vmin:g}–{vmax:g}", "V",
                       f"N × Vmp × (1 + β·(T celda extrema − 25)); {t_txt}", fuente,
                       "rojo" if not vmin <= compat["Vmp_extremo"] <= vmax else "verde"),
            ])
            g["estado"] = _peor(g["estado"], estado_c)
            for mensaje in compat.get("mensajes", []):
                bloqueos.append(f"«{g['superficie']} · {g['gid']}»: {mensaje}.")
            if estado_c == "amarillo":
                avisos.append(f"«{g['superficie']} · {g['gid']}»: pasa con poco margen (< 7,5 %).")

        estado_m = _peor(*(c["estado"] for c in checks))
        salida_mppt.append({
            "inversor_id": inv_id, "mppt": mppt,
            "grupos": [f"{g['superficie']} · {g['gid']}" for g in grupos],
            "paneles": sorted(map(str, paneles_mppt)), "orientaciones": sorted(orient),
            "strings": strings, "caja_combinadora": caja, "isc_total": round(isc_total, 4), "checks": checks,
            "estado": estado_m,
        })

    # Por inversor
    salida_invs = []
    for inv_id, inv in invs.items():
        ficha = inv["ficha"]
        fuente = _fuente_ficha(inv)
        checks = []
        grupos_inv = [g for g in salida_grupos if g["inversor_id"] == inv_id]
        etiqueta = f"«{inv_id}»"
        if inv.get("clase") not in CLASES_SOPORTADAS:
            bloqueos.append(f"{etiqueta}: clase «{inv.get('clase')}» no soportada todavía (llega con la Spec B).")
            checks.append(_check("Clase de inversor", inv.get("clase"), "string", "", "clase soportada", "inversor", "rojo"))
        eta = _positivo(inv.get("eta_inversor"))
        if eta is None or eta > 1:
            bloqueos.append(f"{etiqueta}: falta la eficiencia (0–1).")
            checks.append(_check("Eficiencia", inv.get("eta_inversor"), "0–1", "", "η del inversor", "inversor", "rojo"))
        if not grupos_inv:
            avisos.append(f"{etiqueta}: sin grupos asignados.")
            checks.append(_check("Grupos asignados", 0, 1, "grupos", "grupos con este inversor", "grupos", "amarillo"))
        mppts = sorted({g["mppt"] for g in grupos_inv if g["mppt"]})
        n_mppt = ficha.get("N_mppt")
        if n_mppt:
            fuera = [m for m in mppts if m > n_mppt]
            est_m = "rojo" if fuera or len(mppts) > n_mppt else "verde"
            if est_m == "rojo":
                bloqueos.append(f"{etiqueta}: usa el MPPT {', '.join(map(str, fuera or mppts))} y tiene {n_mppt}.")
        else:
            est_m = "amarillo"
            if grupos_inv:
                avisos.append(f"{etiqueta}: la ficha no dice cuántos MPPT tiene; no se puede "
                              "verificar la asignación.")
        checks.append(_check("MPPT usados ≤ MPPT del inversor", len(mppts), n_mppt, "MPPT",
                             "MPPT distintos asignados", fuente, est_m))
        p_dc_kw = sum(
            float(g["_panel"].get("Pmax_stc", 0.0)) * (g["n_serie"] or 0) * (g["n_paralelo"] or 0)
            for g in grupos_inv if g["_panel"]) / 1000.0
        p_ac = _positivo(inv.get("P_ac_nom_W")) or ficha.get("P_ac_nom_W")
        rel = evaluar_relacion_dc_ac(p_dc_kw, p_ac) if grupos_inv else {"evaluable": False}
        # La relación DC/AC mide si el inversor está bien aprovechado; nunca
        # es un diseño imposible, así que como mucho es 🟡 (fase A2). Sin
        # grupos no hay nada que comparar.
        if grupos_inv and rel.get("evaluable"):
            ratio = rel["ratio"]
            est_r = "verde" if rel.get("estado") == "optimo" else "amarillo"
            checks.append(_check("Relación DC/AC", round(ratio, 3), "1,00–1,35 (orientativo)", "",
                                 "Σ Pmax × módulos del inversor ÷ P AC nominal", fuente, est_r))
            if ratio < 1.0:
                avisos.append(
                    f"{etiqueta}: el inversor es más grande que los paneles conectados "
                    f"(DC/AC {ratio:.2f}: {p_dc_kw:.2f} kW de paneles para {p_ac / 1000:.1f} kW de "
                    "inversor). Funciona bien, pero se desaprovecha parte del inversor y cuesta más "
                    "de lo necesario. Lo usual es entre 1,00 y 1,35: agrega módulos o elige un "
                    "inversor más pequeño."
                )
            elif est_r == "amarillo":
                avisos.append(
                    f"{etiqueta}: hay más potencia de paneles que de inversor (DC/AC {ratio:.2f}). "
                    "En las horas de más sol el inversor limita su salida (recorte o «clipping») "
                    "y se pierde algo de energía; el modo físico calcula cuánto. Hasta 1,35 suele "
                    "ser una buena decisión económica; más arriba conviene revisarlo."
                )
        elif grupos_inv:
            checks.append(_check("Relación DC/AC", None, None, "", "sin P AC nominal", fuente, "amarillo"))
            avisos.append(f"{etiqueta}: sin potencia AC nominal no se puede calcular la relación DC/AC.")
        salida_invs.append({
            "inversor_id": inv_id, "origen_ficha": inv.get("origen_ficha"),
            "nombre": inv.get("nombre"), "mppt_usados": len(mppts),
            "mppt_disponibles": n_mppt, "P_dc_stc_kW": round(p_dc_kw, 3),
            "cajas_combinadoras": sum(
                1 for m in salida_mppt if m["inversor_id"] == inv_id and m["caja_combinadora"]
            ),
            "relacion_dc_ac": rel, "checks": checks,
            "estado": _peor(*(c["estado"] for c in checks)),
        })

    for g in salida_grupos:
        g.pop("_orientacion", None)
        g.pop("_panel", None)
    _asegurar_mensajes(salida_grupos, salida_mppt, salida_invs, salida_sups, bloqueos, avisos)
    estados = ([g["estado"] for g in salida_grupos] + [m["estado"] for m in salida_mppt]
               + [i["estado"] for i in salida_invs] + [s["estado"] for s in salida_sups]
               + (["amarillo"] if temps.get("origen") != "proyecto" else []))
    return {
        "grupos": salida_grupos, "mppt": salida_mppt, "inversores": salida_invs,
        "superficies": salida_sups, "estado_global": _peor(*estados) if estados else "verde",
        "bloqueos": list(dict.fromkeys(bloqueos)), "avisos": list(dict.fromkeys(avisos)),
        "temperaturas": dict(temps),
    }


# ── Coherencia entre tabla y mensajes ────────────────────────────────────────
def _etiquetas(nivel: str, item: Mapping[str, Any]) -> str:
    if nivel == "grupo":
        return f"«{item['superficie']} · {item['gid']}»"
    if nivel == "mppt":
        return f"«{item['inversor_id']} · MPPT {item['mppt']}»"
    if nivel == "inversor":
        return f"«{item['inversor_id']}»"
    return f"«{item['superficie']}»"


def _asegurar_mensajes(grupos, mppt, invs, sups, bloqueos: list, avisos: list) -> None:
    """Cada 🔴 de la tabla tiene su mensaje rojo y cada 🟡 su mensaje amarillo
    (fase A2: antes una relación DC/AC salía 🔴 en la tabla y 🟡 en la lista)."""
    for nivel, items in (("grupo", grupos), ("mppt", mppt), ("inversor", invs), ("superficie", sups)):
        for item in items:
            etiqueta = _etiquetas(nivel, item)
            for c in item["checks"]:
                if c["estado"] == "rojo" and not any(b.startswith(etiqueta) for b in bloqueos):
                    bloqueos.append(f"{etiqueta}: {c['nombre']} ({c['formula']}).")
                elif c["estado"] == "amarillo" and not any(a.startswith(etiqueta) for a in avisos):
                    avisos.append(f"{etiqueta}: {c['nombre']} — {c['formula']}.")


# ── Resumen, estado de sesión y área instalada ───────────────────────────────
ICONO_ESTADO = {"verde": "🟢", "amarillo": "🟡", "rojo": "🔴"}


def resumen_estado_electrico(diagnostico: Mapping[str, Any]) -> dict:
    """``{"estado", "n_bloqueos", "n_avisos", "texto"}`` para el banner y la
    publicación (``multisup_estado_electrico``)."""
    estado = diagnostico["estado_global"]
    n_b, n_a = len(diagnostico["bloqueos"]), len(diagnostico["avisos"])
    if estado == "rojo":
        texto = (f"🔴 diseño eléctrico con fallas ({n_b}): hay strings, MPPT o inversores "
                 "eléctricamente imposibles; revísalos en ⚡ Diseño eléctrico.")
    elif estado == "amarillo":
        texto = (f"🟡 diseño eléctrico no verificado del todo ({n_a} aviso(s)): funciona, pero "
                 "revisa los avisos en ⚡ Diseño eléctrico.")
    else:
        texto = "🟢 diseño eléctrico verificado."
    return {"estado": estado, "n_bloqueos": n_b, "n_avisos": n_a, "texto": texto}


def paneles_superficies_estado(session_state: Mapping[str, Any],
                               superficies: list[Mapping[str, Any]] | None = None) -> dict:
    """``{nombre: {"panel", "nombre"}}`` de cada superficie activa con panel.

    Para el diseño eléctrico basta la ficha eléctrica del panel; no hace falta
    que traiga área (eso solo lo exige la eficiencia de la energía
    simplificada)."""
    from calculos.panel_superficie import PanelSuperficieError, panel_de_superficie

    salida = {}
    for sup in (superficies if superficies is not None
                else list(session_state.get("superficies_bipv") or [])):
        if not sup.get("activa", True):
            continue
        try:
            datos = panel_de_superficie(sup, session_state.get("panel_dict"),
                                        session_state.get("panel_nombre_dim"))
        except PanelSuperficieError:
            continue
        salida[sup["nombre"]] = {"panel": datos["panel"], "nombre": datos["nombre"]}
    return salida


def diagnostico_electrico_estado(session_state: Mapping[str, Any]) -> dict:
    """``validar_diseno_electrico`` con el estado de la sesión."""
    paneles = paneles_superficies_estado(session_state)
    return validar_diseno_electrico(
        list(session_state.get("superficies_bipv") or []),
        list(session_state.get("multisup_inversores") or []),
        paneles, temperaturas_diseno(session_state),
    )


def modulos_de_superficie(superficie: Mapping[str, Any]) -> int:
    """Σ N serie × N paralelo de los grupos válidos de la superficie."""
    total = 0
    for g in grupos_de_superficie(superficie):
        n_s, n_p = _entero_positivo(g.get("n_serie")), _entero_positivo(g.get("n_paralelo"))
        if n_s and n_p:
            total += n_s * n_p
    return total


def area_energia_superficie(superficie: Mapping[str, Any],
                            panel: Mapping[str, Any] | None) -> dict:
    """Área con la que se calcula la energía simplificada de la superficie.

    Con grupos de strings: área instalada = módulos × área del módulo (sin
    pasar del área de la superficie), la misma base del modo físico. Sin
    grupos: el área de la superficie, marcada como estimación.
    """
    area_sup = _positivo(superficie.get("area_m2")) or 0.0
    modulos = modulos_de_superficie(superficie)
    area_mod = None
    if panel:
        from calculos.panel_superficie import area_modulo
        area_mod = area_modulo(panel)
    if modulos and area_mod:
        instalada = modulos * area_mod
        return {"area_m2": round(min(instalada, area_sup), 4), "area_superficie_m2": area_sup,
                "area_instalada_m2": round(instalada, 4), "modulos": modulos,
                "origen": "instalada" if instalada <= area_sup + 1e-9 else "instalada_recortada"}
    return {"area_m2": area_sup, "area_superficie_m2": area_sup, "area_instalada_m2": None,
            "modulos": modulos, "origen": "superficie"}


def superficies_para_energia(superficies: list[Mapping[str, Any]],
                             paneles: Mapping[str, Mapping[str, Any]]) -> list[dict]:
    """Copias de las superficies con ``area_m2`` = área de energía y los campos
    ``area_superficie_m2`` y ``area_origen``. No muta la entrada."""
    salida = []
    for sup in superficies:
        info = paneles.get(sup.get("nombre"))
        area = area_energia_superficie(sup, info["panel"] if info else None)
        salida.append({**dict(sup), "area_m2": area["area_m2"],
                       "area_superficie_m2": area["area_superficie_m2"],
                       "area_origen": area["origen"], "modulos": area["modulos"]})
    return salida


# ── Invalidación por cambio del diseño eléctrico ─────────────────────────────
CLAVE_FIRMA_ELECTRICA = "_multisup_firma_electrica"
_CAMPOS_INVERSOR_FIRMA = ("clase", "origen_ficha", "nombre", "ficha", "eta_inversor", "P_ac_nom_W")


def firma_diseno_electrico(superficies: list[Mapping[str, Any]],
                           inversores: list[Mapping[str, Any]]) -> dict[str, str]:
    """Huella por ``uid`` de los grupos de cada superficie activa y de los
    inversores que usan."""
    from calculos.produccion_vigencia import fingerprint_mapping

    invs = {str(i.get("inversor_id")): i for i in inversores}
    salida = {}
    for sup in superficies:
        if not sup.get("activa", True):
            continue
        grupos = grupos_de_superficie(sup)
        usados = sorted({str(g.get("inversor_id")) for g in grupos if g.get("inversor_id")})
        salida[str(sup.get("uid", sup.get("nombre")))] = fingerprint_mapping({
            "grupos": grupos,
            "inversores": {i: {k: invs.get(i, {}).get(k) for k in _CAMPOS_INVERSOR_FIRMA}
                           for i in usados},
        })
    return salida


def invalidar_por_cambio_electrico(session_state) -> list[str]:
    """Retira la energía publicada y los resultados de bypass, MPPT y físico si
    cambió el diseño eléctrico de alguna superficie que ya existía. Agregar,
    quitar, desactivar o renombrar superficies no cuenta. La POA y la sombra
    no dependen del diseño eléctrico y se conservan."""
    from calculos.panel_superficie import KEYS_RESULTADOS_PANEL
    from calculos.publicacion_multisuperficie import (
        registrar_motivo_retiro, retirar_energia_multisuperficie,
    )

    actual = firma_diseno_electrico(
        list(session_state.get("superficies_bipv") or []),
        list(session_state.get("multisup_inversores") or []),
    )
    anterior = session_state.get(CLAVE_FIRMA_ELECTRICA)
    session_state[CLAVE_FIRMA_ELECTRICA] = actual
    if not isinstance(anterior, Mapping):
        return []
    cambiados = {uid for uid in anterior.keys() & actual.keys() if anterior[uid] != actual[uid]}
    if not cambiados:
        return []
    retiradas = retirar_energia_multisuperficie(session_state)
    registrar_motivo_retiro(session_state, retiradas, "cambió el diseño eléctrico", cambiados)
    for clave in KEYS_RESULTADOS_PANEL:
        if clave in session_state:
            session_state.pop(clave, None)
            retiradas.append(clave)
    return retiradas
