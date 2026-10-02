# -*- coding: utf-8 -*-
"""Revisión de coherencia antes de generar el 📄 Reporte.

Spec ``07-informes/coherencia-reporte`` (2-oct-2026). El reporte junta datos
de varias páginas y cada una guarda su último cálculo. Si el diseñador cambia
algo y no vuelve a ejecutar una página, el informe mezcla momentos distintos.
Caso real (Granja Apartadó 3): «3 inversores» con «reparto 7+7+7+7», sin
Producción, y CO₂ de 6,3 t/año calculado con los 50.000 kWh de ejemplo de
🌿 Impacto CO₂ cuando la granja produce ~604 MWh.

Devuelve una lista de problemas ``{nivel, titulo, detalle, accion}`` con
nivel «error» (el informe tendría datos contradictorios) o «aviso».
Módulo puro: sin Streamlit.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

TOLERANCIA_ENERGIA = 0.02     # 2 %: redondeos y factores de un mismo cálculo


def _num(valor: Any) -> float:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return 0.0
    return v if v == v else 0.0


def energia_vigente(estado: Mapping[str, Any]) -> float:
    """E_ac anual de 📊 Producción con la misma prioridad que 🌿 Impacto CO₂ y
    💰 Financiero: multi-superficie > bypass > base."""
    e_ms = _num(estado.get("E_ac_anual_kWh_multisup"))
    e_bp = _num(estado.get("E_ac_anual_kWh_bypass"))
    if estado.get("multisup_activo") and e_ms > 0:
        return e_ms
    if estado.get("bypass_ok") and e_bp > 0:
        return e_bp
    return _num(estado.get("E_ac_anual_kWh"))


def _distinta(a: float, b: float) -> bool:
    return b > 0 and abs(a - b) / b > TOLERANCIA_ENERGIA


def revisar_coherencia_reporte(estado: Mapping[str, Any]) -> list[dict]:
    problemas: list[dict] = []
    e_ac = energia_vigente(estado)

    # ── Producción ──────────────────────────────────────────────────────────
    if e_ac <= 0:
        problemas.append({
            "nivel": "error", "titulo": "Falta ⚡ Producción",
            "detalle": "No hay energía anual simulada en esta sesión: el informe saldría sin producción "
                       "y CO₂ / Financiero usarían valores de ejemplo.",
            "accion": "Ejecuta 📊 Producción antes de generar el reporte.",
        })

    # ── Inversores ──────────────────────────────────────────────────────────
    n_prod = int(_num(estado.get("produccion_n_inversores")))
    reparto = [int(_num(x)) for x in (estado.get("reparto_strings_inversores") or []) if _num(x) > 0]
    n_rep = len(reparto)
    n_fij = int(_num(estado.get("N_inversores_proyecto")))
    if n_prod and n_rep and n_prod != n_rep:
        problemas.append({
            "nivel": "error", "titulo": "Cantidad de inversores distinta entre páginas",
            "detalle": (f"📊 Producción se simuló con {n_prod} inversores, pero 📐 Dimensionamiento reparte "
                        f"los strings en {n_rep} ({' + '.join(map(str, reparto))}). El informe mostraría ambos."),
            "accion": "Vuelve a ejecutar 📊 Producción con el diseño actual de 📐 Dimensionamiento.",
        })
    elif n_prod and n_fij and n_prod != n_fij:
        problemas.append({
            "nivel": "error", "titulo": "Cantidad de inversores distinta entre páginas",
            "detalle": (f"En 📐 Dimensionamiento fijaste {n_fij} inversores, pero 📊 Producción se simuló "
                        f"con {n_prod}."),
            "accion": "Vuelve a ejecutar 📊 Producción.",
        })

    # ── 🌿 Impacto CO₂ ──────────────────────────────────────────────────────
    co2_t = _num(estado.get("co2_anual_t"))
    if co2_t > 0 and e_ac > 0:
        e_co2 = _num(estado.get("co2_e_ac_kWh"))
        factor = _num(estado.get("co2_factor_kg_kwh"))
        if e_co2 <= 0 and factor > 0:
            e_co2 = co2_t * 1000.0 / factor          # páginas anteriores no guardaban la energía
        if estado.get("co2_e_ac_manual") or (e_co2 > 0 and _distinta(e_co2, e_ac)):
            problemas.append({
                "nivel": "error", "titulo": "🌿 Impacto CO₂ con otra energía",
                "detalle": (f"El CO₂ ({co2_t:,.1f} t/año) se calculó con {e_co2:,.0f} kWh/año"
                            + (" escritos a mano" if estado.get("co2_e_ac_manual") else "")
                            + f"; 📊 Producción da {e_ac:,.0f} kWh/año."),
                "accion": "Abre 🌿 Impacto CO₂ después de 📊 Producción para recalcularlo.",
            })

    # ── 💰 Financiero ──────────────────────────────────────────────────────
    e_fin = _num(estado.get("fin_e_ac_kWh"))
    if e_ac > 0 and (estado.get("fin_e_ac_manual") or (e_fin > 0 and _distinta(e_fin, e_ac))):
        problemas.append({
            "nivel": "error", "titulo": "💰 Financiero con otra energía",
            "detalle": (f"El análisis financiero usó {e_fin:,.0f} kWh/año"
                        + (" escritos a mano" if estado.get("fin_e_ac_manual") else "")
                        + f"; 📊 Producción da {e_ac:,.0f} kWh/año."),
            "accion": "Abre 💰 Financiero después de 📊 Producción para recalcularlo.",
        })
    return problemas
