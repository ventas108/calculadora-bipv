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
