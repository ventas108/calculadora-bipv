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

    # ── Diseño cambiado después de simular ─────────────────────────────────
    if e_ac > 0:
        cambios = cambios_de_diseno(estado.get("produccion_resumen_diseno"), resumen_diseno(estado))
        if cambios:
            problemas.append({
                "nivel": "error", "titulo": "El diseño cambió después de simular ⚡ Producción",
                "detalle": "; ".join(cambios) + ". La energía del informe es la del diseño anterior.",
                "accion": "Vuelve a ejecutar 📊 Producción (y luego 🌿 Impacto CO₂ y 💰 Financiero).",
            })

    # ── Cables: Producción con el % manual habiendo cables calculados ───────
    # Spec 07-informes/reporte-cables-titulo-co2. La cadena multi-superficie
    # aplica sus propios cables.
    res = estado.get("res_produccion")
    granja_cables = (estado.get("tipo_instalacion") == "Granja fotovoltaica"
                     and bool(estado.get("granja_electrico_cfg")))
    unifilar = bool(estado.get("perdida_ohmica_unifilar"))
    if (e_ac > 0 and isinstance(res, Mapping) and res and not estado.get("multisup_activo")
            and (granja_cables or unifilar) and res.get("perdida_ohmica_dc_modo") != "calculado"):
        origen = "🌾 Granja FV" if granja_cables else "⚡ Diagrama Unifilar"
        problemas.append({
            "nivel": "error", "titulo": "📊 Producción no usó los cables calculados",
            "detalle": (f"Producción aplicó el % manual de 🔀 Mismatch para los cables "
                        f"(DC {_num(estado.get('pct_cableado_dc')):.1f} %, AC {_num(estado.get('pct_cableado_ac')):.1f} %), "
                        f"pero {origen} ya calculó los cables reales. El informe mostraría las dos cifras."),
            "accion": ("Abre ⚡ Diagrama Unifilar" + (" con «🌾 Usar los cables de 🌾 Granja FV» marcada" if granja_cables else "")
                       + " y vuelve a ejecutar 📊 Producción (y luego 🌿 Impacto CO₂ y 💰 Financiero)."),
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


# ── Diseño vigente al simular ⚡ Producción ──────────────────────────────────
# Producción guarda este resumen al simular; el Reporte lo compara con el
# actual. Si el diseñador cambió el panel, la inclinación, el Motor Óptico o
# las pérdidas después de simular, la energía del informe ya no es la de este
# diseño. (clave, etiqueta, unidad)
_CAMPOS_DISENO = (
    ("panel", "Panel", ""),
    ("inversor", "Inversor", ""),
    ("N_paneles", "Número de módulos", ""),
    ("N_serie", "Módulos en serie", ""),
    ("ciudad", "Ciudad / clima", ""),
    ("tilt", "Inclinación", "°"),
    ("azimuth", "Orientación (azimut)", "°"),
    ("poa_anual", "POA anual", " kWh/m²"),
    ("motor_optico", "Motor Óptico", ""),
    ("noct", "NOCT del Motor Óptico", " °C"),
    ("k_bipv", "Montaje k_BIPV", ""),
    ("pct_mismatch_fab", "Mismatch de fabricación", " %"),
    ("pct_calidad_modulo", "Calidad del módulo", " %"),
    ("pct_cableado_dc", "Cableado DC", " %"),
    ("pct_cableado_ac", "Cableado AC", " %"),
)


def _poa_anual(df) -> float | None:
    try:
        return round(float(df["poa_global"].sum()) / 1000.0, 0)
    except Exception:
        return None


def _redondeo(valor: Any, dec: int = 3):
    if valor is None or isinstance(valor, (str, bool)):
        return valor
    v = _num(valor)
    return round(v, dec)


def resumen_diseno(estado: Mapping[str, Any]) -> dict:
    """Datos de diseño que determinan la energía de 📊 Producción."""
    mo = bool(estado.get("motor_optico_ok"))
    return {
        "panel": str(estado.get("panel_nombre_dim") or estado.get("panel_nombre_final") or "") or None,
        "inversor": str(estado.get("inversor_nombre_dim") or "") or None,
        "N_paneles": int(_num(estado.get("N_paneles_final"))) or None,
        "N_serie": int(_num(estado.get("N_serie"))) or None,
        "ciudad": str(estado.get("tmy_ciudad") or "") or None,
        "tilt": _redondeo(estado.get("tilt_fachada"), 1),
        "azimuth": _redondeo(estado.get("azimuth_fachada"), 1),
        "poa_anual": _poa_anual(estado.get("poa_df")),
        "motor_optico": "activo" if mo else "inactivo",
        "noct": _redondeo(estado.get("motor_optico_noct"), 1) if mo else None,
        "k_bipv": _redondeo(estado.get("motor_optico_k_bipv"), 2) if mo else None,
        "pct_mismatch_fab": _redondeo(estado.get("pct_mismatch_fab"), 2),
        "pct_calidad_modulo": _redondeo(estado.get("pct_calidad_modulo"), 2),
        "pct_cableado_dc": _redondeo(estado.get("pct_cableado_dc"), 2),
        "pct_cableado_ac": _redondeo(estado.get("pct_cableado_ac"), 2),
    }


def cambios_de_diseno(al_simular: Mapping[str, Any] | None, actual: Mapping[str, Any]) -> list[str]:
    """Textos «Etiqueta: antes → ahora» de lo que cambió desde la simulación."""
    if not al_simular:
        return []
    cambios = []
    for clave, etiqueta, unidad in _CAMPOS_DISENO:
        a, b = al_simular.get(clave), actual.get(clave)
        if a is None or b is None or a == b:
            continue
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) <= 1e-6 * max(1, abs(a)):
            continue
        cambios.append(f"{etiqueta}: {a}{unidad} al simular → {b}{unidad} ahora")
    return cambios
