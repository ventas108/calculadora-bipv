# -*- coding: utf-8 -*-
"""Secciones de producción del 📄 Reporte PDF (Spec 07-informes/reporte-produccion-completo).

Datos que el reporte no mostraba y que el cliente necesita (30-sep-2026):
sistema eléctrico e inversores, diagrama de pérdidas de 📊 Producción,
datos bifaciales completos y todo 🌾 Granja FV (campo, sombra entre filas,
agrivoltaica, seguidor y eléctrico por bloques). Cada función devuelve filas
``(etiqueta, valor, unidad, nota)`` que la página convierte en tablas; nunca
calculan de nuevo la energía: leen lo que ya calcularon las páginas.

Módulo puro: sin Streamlit.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _f(valor: Any, dec: int = 1, fallback: str = "—") -> str:
    try:
        return f"{float(valor):,.{dec}f}"
    except (TypeError, ValueError):
        return fallback


def filas_sistema_electrico(estado: Mapping[str, Any], res: Mapping[str, Any] | None) -> list[tuple]:
    """Panel, módulos, strings, inversores, reparto, relación DC/AC y recorte."""
    res = res or {}
    panel = dict(estado.get("panel_dict") or {})
    inv = dict(estado.get("inversor_dict_dim") or {})
    n_mod = int(estado.get("N_paneles_final") or estado.get("N_paneles_granja") or 0)
    n_serie = int(estado.get("N_serie") or 0)
    p_stc = float(res.get("P_stc_kW") or estado.get("P_stc_kW_sistema") or 0.0)
    n_inv = int(estado.get("produccion_n_inversores") or estado.get("N_inv_total") or 0)
    p_ac_u = float(inv.get("P_ac_nom_W") or 0.0) / 1000.0
    p_ac_tot = float(estado.get("produccion_p_ac_total_w") or 0.0) / 1000.0 or (p_ac_u * n_inv)
    reparto = [int(x) for x in (estado.get("reparto_strings_inversores") or []) if int(x) > 0]
    filas = [
        ("Módulo fotovoltaico", str(estado.get("panel_nombre_final") or panel.get("nombre") or "—"), "",
         f"{_f(panel.get('Pmax_stc'), 0)} Wp por módulo"),
        ("Número de módulos", f"{n_mod:,}", "", "Los que simuló 📊 Producción"),
        ("Potencia pico DC", _f(p_stc, 2), "kWp", "Módulos × potencia STC"),
    ]
    if n_serie:
        filas.append(("Módulos en serie por string", str(n_serie), "",
                      f"{n_mod // n_serie if n_serie else 0} strings" if n_mod else ""))
    if n_inv:
        filas.append(("Inversores", f"{n_inv} × {estado.get('inversor_nombre_dim') or inv.get('nombre') or '—'}",
                      "", f"{_f(p_ac_u, 1)} kW AC cada uno"))
        filas.append(("Potencia AC total", _f(p_ac_tot, 1), "kW", ""))
    if reparto:
        filas.append(("Reparto de strings por inversor", " + ".join(str(r) for r in reparto), "strings", ""))
    if p_stc and p_ac_tot:
        filas.append(("Relación DC/AC", _f(p_stc / p_ac_tot, 2), "", "Potencia DC ÷ potencia AC total; típico 1,1–1,3"))
    if res.get("perdida_clipping_kWh") is not None:
        filas.append(("Recorte del inversor (clipping)", _f(res.get("perdida_clipping_kWh"), 0), "kWh/año",
                      f"{int(res.get('horas_con_clipping') or 0):,} horas al año sobre la potencia AC nominal"))
    return filas


def filas_perdidas(res: Mapping[str, Any] | None, poa_bruta_kwh_m2: float,
                   motor_optico_summary: Mapping[str, Any] | None) -> list[dict]:
    """Diagrama de pérdidas de 📊 Producción (la misma tabla de la página)."""
    if not res or not res.get("P_stc_kW") or not poa_bruta_kwh_m2:
        return []
    from calculos.produccion import perdidas_desglosadas

    df = perdidas_desglosadas(dict(res), float(poa_bruta_kwh_m2), dict(motor_optico_summary or {}))
    if df is None or df.empty:
        return []
    ref = float(df.iloc[0]["kWh"]) or 1.0
    filas = []
    for _, r in df.iterrows():
        delta = float(r.get("Δ kWh") or 0.0)
        filas.append({"etapa": str(r["Etapa"]).strip(), "kwh": float(r["kWh"]), "delta_kwh": delta,
                      "pct": 100.0 * delta / ref, "nota": str(r.get("Nota") or "")})
    return filas


def filas_bifacial(estado: Mapping[str, Any]) -> list[tuple]:
    """Datos bifaciales que faltaban: GCR, ancho de la mesa y factores de la cara trasera."""
    if not estado.get("bifacial_activo"):
        return []
    cfg = dict(estado.get("bifacial_cfg") or {})
    filas = []
    if cfg.get("gcr") is not None:
        filas.append(("GCR (cobertura del suelo)", _f(float(cfg["gcr"]) * 100, 1), "%", "Ancho de la mesa ÷ separación entre filas"))
    if cfg.get("ancho_colector_m") is not None:
        filas.append(("Ancho de la mesa en la pendiente", _f(cfg["ancho_colector_m"], 2), "m", ""))
    filas.append(("Sombra de la estructura en la cara trasera", _f(cfg.get("sombra_trasera_pct", 0.0), 1), "%", ""))
    filas.append(("Mismatch por luz trasera no uniforme", _f(cfg.get("mismatch_trasero_pct", 0.0), 1), "%", ""))
    return filas


def secciones_granja(estado: Mapping[str, Any]) -> dict:
    """Bloques de 🌾 Granja FV disponibles en el proyecto (vacío si no es granja)."""
    if str(estado.get("tipo_instalacion") or "") != "Granja fotovoltaica" or not estado.get("granja_fv"):
        return {}
    out: dict[str, Any] = {}
    r = dict(estado.get("granja_fv_resultado") or {})
    g = dict(estado.get("granja_fv") or {})
    if r:
        out["campo"] = [
            ("Módulos ubicados", f"{int(r.get('modulos_colocados') or 0):,} de {int(r.get('modulos_proyecto') or 0):,}", "", ""),
            ("Filas", str(r.get("filas_usadas", "—")), "", f"{int(g.get('modulos_pendiente') or 0)} módulos en la pendiente × "
                                                            f"{int(g.get('modulos_por_mesa') or 0)} a lo largo por mesa"),
            ("Terreno", f"{_f(g.get('ancho_terreno_m'), 0)} × {_f(g.get('largo_terreno_m'), 0)}", "m", ""),
            ("Separación entre filas (pitch)", _f(g.get("pitch_m"), 2), "m", ""),
            ("Ancho de la mesa en la pendiente", _f(r.get("ancho_mesa_m"), 3), "m", ""),
            ("GCR", _f(float(r.get("gcr") or 0) * 100, 1), "%", "Ancho de la mesa ÷ separación"),
            ("Ángulo límite de sombra", _f(r.get("angulo_limite_deg"), 1), "°", "Con el sol más bajo, una fila sombrea a la siguiente"),
            ("Corredor libre entre filas", _f(r.get("corredor_m"), 2), "m", ""),
            ("Altura libre / centro de la mesa", f"{_f(g.get('altura_libre_m'), 2)} / {_f(r.get('altura_centro_m'), 2)}", "m", ""),
            ("Suelo libre", _f(r.get("suelo_libre_pct"), 0), "%", "Terreno sin paneles encima"),
        ]
    energia = []
    geo = estado.get("poa_geometria_filas")
    energia.append(("Geometría del campo en la energía", "Sí" if geo else "No", "",
                    "La irradiancia incluye la sombra entre filas del campo" if geo
                    else "La energía no usa todavía la geometría del campo"))
    est = estado.get("granja_sombra_estimada")
    if est:
        energia.append(("Pérdida frontal por sombra entre filas", _f(est.get("perdida_frontal_pct"), 2), "%", ""))
    out["energia"] = energia
    luz = estado.get("granja_luz_suelo")
    if luz:
        out["agrivoltaica"] = [
            ("Luz media en el suelo", _f(luz.get("media_pct"), 0), "%", "Frente al terreno sin paneles"),
            ("Luz media anual en el suelo", _f(luz.get("media_kwh_m2"), 0), "kWh/m²",
             f"Sin paneles: {_f(luz.get('referencia_kwh_m2'), 0)} kWh/m²"),
            ("Bajo las mesas / entre filas", f"{_f(luz.get('bajo_mesa_pct'), 0)} / {_f(luz.get('entre_filas_pct'), 0)}", "%", ""),
            ("Homogeneidad de la luz", _f(luz.get("homogeneidad"), 2), "", "Punto más oscuro ÷ más iluminado"),
            ("Categoría agrivoltaica", "I (cultivo bajo los paneles)" if float(g.get("altura_libre_m") or 0) >= 2.10
             else "II (cultivo entre filas)", "", "DIN SPEC 91434: altura libre ≥ 2,10 m"),
        ]
    seg = estado.get("granja_seguidor")
    if seg:
        out["seguidor"] = [
            ("Luz frontal con estructura fija", _f(seg["fijo"]["poa_kwh_m2"], 0), "kWh/m²", ""),
            ("Seguidor de un eje con backtracking", _f(seg["backtracking"]["poa_kwh_m2"], 0), "kWh/m²",
             f"{seg['ganancia_backtracking_pct']:+.1f} % frente a la fija"),
            ("Seguidor sin backtracking", _f(seg["sin_backtracking"]["poa_kwh_m2"], 0), "kWh/m²",
             f"{seg['ganancia_sin_backtracking_pct']:+.1f} %; sombra eléctrica {seg['perdida_sombra_electrica_pct']:.1f} %"),
        ]
    try:
        from calculos.granja_electrico import diseno_desde_estado
        d = diseno_desde_estado(estado)
    except Exception:
        d = None
    if d:
        out["electrico"] = [
            ("Strings", f"{d['n_strings']} × {d['n_serie']} módulos", "",
             f"{d['strings_cruzan_filas']} cruzan de una fila a la siguiente"),
            ("Reparto por inversor", " + ".join(str(x) for x in d["reparto"]), "strings", ""),
            ("Cable DC / AC total", f"{_f(d['dc_total_m'], 0)} / {_f(d['ac_total_m'], 0)}", "m",
             f"Calibres {d['calibre_dc_mm2']:g} / {d['calibre_ac_mm2']:g} mm²"),
            ("Caída de tensión máxima DC / AC", f"{_f(d['caida_dc_max_pct'], 2)} / {_f(d['caida_ac_max_pct'], 2)}", "%",
             "Límite recomendado 3 % (NTC 2050)"),
            ("Pérdida DC a STC en cables", _f(d["perdida_dc_stc_pct"], 2), "%", f"Resistencia efectiva {d['resistencia_dc_efectiva_mohm']:.1f} mΩ"),
        ]
        out["bloques"] = [{"inversor": f"INV-{b['inversor']}", "strings": b["strings"], "modulos": b["modulos"],
                           "filas": ", ".join(str(f + 1) for f in b["filas"]), "dc_medio_m": b["dc_media_m"],
                           "ac_m": b["longitud_ac_m"], "caida_ac_pct": b["caida_ac_pct"]} for b in d["bloques"]]
    return out


# ── Spec 07-informes/reporte-granja-completo (1-oct-2026) ────────────────────
# El reporte usaba textos pensados solo para fachadas BIPV («Área de fachada»,
# «90° = fachada vertical», «al edificio», «Bogotá», «CdTe»…) en cualquier
# proyecto, mostraba «Factor Mismatch 100 %» aunque la simulación aplicara
# calidad del módulo y mismatch, y la altitud salía siempre «—».
_TIPOS_BIPV = ("Fachada BIPV", "Techo inclinado (BIPV)")


def etiquetas_tipo(tipo: str | None) -> dict:
    """Textos del reporte según el tipo de instalación de 🏠 Proyecto."""
    tipo = str(tipo or "")
    granja = tipo == "Granja fotovoltaica"
    fachada = tipo == "Fachada BIPV" or not tipo
    return {
        "granja": granja,
        "fachada": fachada,
        "area": ("Área del terreno", "Terreno disponible para la granja") if granja else
                (("Área de fachada", "Superficie total disponible para BIPV") if fachada else
                 ("Área disponible", "Superficie disponible para los paneles")),
        "orientacion": "Azimut hacia donde miran los paneles" if not fachada else "Azimut de la fachada",
        "inclinacion": "90° = fachada vertical típica" if fachada else "0° = horizontal · 90° = vertical",
        "panel": "Módulo BIPV" if (tipo in _TIPOS_BIPV or not tipo) else "Módulo fotovoltaico",
        "poa": ("POA bruta (fachada)", "Irradiación en el plano de la fachada sin correcciones") if fachada else
               ("POA bruta (plano de los paneles)", "Irradiación en el plano de los paneles sin correcciones"),
        "destino": "Energía AC neta entregada a la red" if granja else
                   ("Energía AC neta entregada al edificio" if fachada else "Energía AC neta entregada al edificio o a la red"),
        "iam": ("En fachadas verticales esta pérdida es la mayor de las tres porque los ángulos son siempre "
                "oblicuos." if fachada else
                "Es mayor en las primeras y últimas horas del día, cuando el sol llega muy inclinado."),
        "termico": ("En BIPV de fachada, la cámara trasera restringida eleva la temperatura" if fachada else
                    "Con estructura abierta y bien ventilada la celda se calienta menos"),
    }


def nota_poa(poa: Any, ghi: Any, fachada: bool) -> str:
    """Nota de la POA coherente con los números del proyecto."""
    base = ("POA (Plane Of Array): irradiación sobre el plano de los paneles. Esta es la energía disponible "
            "ANTES de descontar reflexión, suciedad y temperatura.")
    try:
        poa_f, ghi_f = float(poa), float(ghi)
    except (TypeError, ValueError):
        return base
    if poa_f >= ghi_f:
        return base + (" Aquí la POA es mayor que la irradiación horizontal (GHI): la inclinación hacia el sol "
                       "y, si el panel es bifacial, la luz de la cara trasera suman irradiación.")
    return base + (" Aquí la POA es menor que la irradiación horizontal (GHI)"
                   + (": en una fachada vertical los rayos llegan con mayor ángulo." if fachada
                      else ": la orientación o la inclinación capturan menos luz que un plano horizontal."))


def nota_pr(pr_pct: Any) -> str | None:
    """La explicación de PR > 100 % solo cuando el PR la necesita."""
    try:
        if float(pr_pct) <= 100.0:
            return None
    except (TypeError, ValueError):
        return None
    return ("Performance Ratio > 100 %: posible cuando los módulos trabajan muchas horas por debajo de 25 °C "
            "(climas fríos de alta altitud) y ganan eficiencia frente a las condiciones STC. IEC 61724 permite "
            "PR > 100 %: es un resultado físicamente correcto.")


def filas_mismatch(estado: Mapping[str, Any], res: Mapping[str, Any] | None) -> list[tuple]:
    """Pérdidas de 🔀 Mismatch que aplicó de verdad la simulación de 📊 Producción.

    Desde la Spec 05/calidad-y-mismatch la calidad del módulo y el mismatch se
    aplican en la simulación (``pct_*_aplicado``) y el factor escalar queda en
    1,0; el reporte mostraba entonces «Factor Mismatch aplicado 100 %», que
    contradecía su propio diagrama de pérdidas.
    """
    res = res or {}
    filas = []
    cal, fab = res.get("pct_calidad_modulo_aplicado"), res.get("pct_mismatch_fab_aplicado")
    if cal is not None:
        filas.append(("Calidad del módulo (aplicada)", _f(cal, 1), "%",
                      "Configurada en 🔀 Mismatch · negativo = ganancia por tolerancia positiva"))
    if fab is not None:
        filas.append(("Mismatch módulos y strings (aplicado)", _f(fab, 1), "%", "Configurado en 🔀 Mismatch"))
    f = estado.get("factor_mismatch_aplicado", estado.get("factor_global_mismatch", 1.0))
    try:
        f = float(f)
    except (TypeError, ValueError):
        f = 1.0
    if f < 0.9999 or not filas:
        filas.append(("Otras pérdidas de 🔀 Mismatch", _f((1.0 - f) * 100.0, 1), "%",
                      "Factor aplicado a la irradiancia (horizonte y desajustes de versiones anteriores)"))
    return filas


def altitud_proyecto(estado: Mapping[str, Any]) -> float | None:
    """Altitud del predio (🏠 Proyecto) o, si no, la de la ciudad de referencia."""
    for v in (estado.get("alt_proyecto"), estado.get("alt_m")):
        try:
            if v is not None and str(v).strip() not in ("", "—"):
                return float(v)
        except (TypeError, ValueError):
            pass
    try:
        from datos.ciudades_colombia import CIUDADES
        alt = CIUDADES.get(str(estado.get("ciudad") or ""), {}).get("alt_m")
        return float(alt) if alt is not None else None
    except Exception:
        return None


def aviso_soiling(mo_sum: Mapping[str, Any] | None, granja: bool) -> str | None:
    """Aviso cuando la suciedad quedó en 0 % (producción optimista)."""
    try:
        f_soil = float((mo_sum or {}).get("f_soil_prom", 1.0))
    except (TypeError, ValueError):
        return None
    if f_soil < 0.9995:
        return None
    return ("La pérdida por suciedad quedó en 0 %: la producción de este reporte supone paneles siempre limpios. "
            + ("En granjas en zona agrícola o con polvo de caminos lo usual es 2–3 % al año. "
               if granja else "Lo usual en Colombia es 1–3 % al año según la limpieza y la contaminación. ")
            + "Revísalo en 🔆 Motor Óptico (suciedad) y vuelve a simular 📊 Producción.")
