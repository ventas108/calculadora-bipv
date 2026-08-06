# -*- coding: utf-8 -*-
"""
comparador_inversores.py — Tarea #180
=====================================
Lógica pura (sin Streamlit) para:

1. Filtrar el catálogo de inversores COMPATIBLES con el panel y el string
   actual (Voc frío, ventana MPPT y corriente por entrada), incluyendo el
   modo "1 string por tracker" cuando la corriente del panel supera lo que
   admite un tracker con todos sus strings en paralelo.
2. Comparar configuraciones candidatas (modelo × n unidades) aplicando el
   límite AC real (clipping) sobre la serie horaria P_ac ya simulada.
3. Barrer el ratio DC/AC y encontrar el óptimo por LCOE.

Reutiliza los criterios de calculos/dimensionamiento.py (mismos umbrales)
y las funciones financieras de calculos/financiero.py — no duplica lógica
de flujo de caja.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from calculos.dimensionamiento import (
    calcular_voc_string,
    calcular_vmp_string,
)
from calculos.financiero import calcular_flujo_caja, calcular_metricas

FS_ISC_DEFECTO = 1.25  # mismo factor de seguridad NEC del dimensionamiento


# ══════════════════════════════════════════════════════════════════════════════
# 1. Filtro de compatibilidad de catálogo completo
# ══════════════════════════════════════════════════════════════════════════════
def filtrar_inversores_compatibles(
    panel: dict,
    inversores: dict,
    N_serie: int,
    T_frio: float = -5.0,
    T_real: float = 36.35,
    FS_isc: float = FS_ISC_DEFECTO,
) -> pd.DataFrame:
    """
    Evalúa TODOS los inversores del catálogo contra el string actual.

    Retorna DataFrame con una fila por inversor y columnas:
      modelo, compatible (bool), modo ("normal" | "1 string/tracker" | "—"),
      strings_max (int), P_ac_nom_kW, costo_usd, motivo (str si no compatible).

    Criterios (mismos de optimizar_n_serie):
      • Voc_frío del string ≤ Vdc_max
      • Vmp_real ≥ Vmppt_activo_min  y  Vmp_real ≤ Vmppt_max
      • Corriente: Isc_panel × FS × strings_por_tracker ≤ Isc_max_tracker.
        Si no pasa con los strings nominales del tracker pero SÍ con 1 solo
        string, el inversor queda compatible en modo "1 string/tracker"
        (capacidad = n_trackers strings).
    """
    filas = []
    voc = calcular_voc_string(N_serie, panel["Voc_stc"], panel["Tk_beta"], T_frio)
    vmp = calcular_vmp_string(N_serie, panel["Vmp_stc"], panel["Tk_gamma"], T_real)
    isc = float(panel["Isc_stc"]) * FS_isc

    for nombre, inv in sorted(inversores.items()):
        fila = {
            "modelo": nombre,
            "compatible": False,
            "modo": "—",
            "strings_max": 0,
            "P_ac_nom_kW": (inv.get("P_ac_nom_W") or 0) / 1000.0 or None,
            "costo_usd": inv.get("costo_usd"),
            "Voc_string_frio (V)": round(voc, 0),
            "Vmp_string (V)": round(vmp, 0),
            "motivo": "",
        }
        vdc_max = inv.get("Vdc_max") or 0
        vmppt_min = inv.get("Vmppt_activo_min") or inv.get("Vmppt_min") or 0
        vmppt_max = inv.get("Vmppt_max") or 0
        isc_lim = inv.get("Isc_max_tracker") or inv.get("I_max_tracker") or 0
        n_tr = int(inv.get("n_trackers") or inv.get("N_mppt") or 0)
        str_tr = int(inv.get("n_strings_tracker") or 1)

        if not (vdc_max and vmppt_max and isc_lim and n_tr):
            fila["motivo"] = "Ficha incompleta (tensiones/corrientes/trackers)"
            filas.append(fila)
            continue
        if voc > vdc_max:
            fila["motivo"] = f"Voc frío {voc:,.0f} V > máx. {vdc_max:,.0f} V"
            filas.append(fila)
            continue
        if vmp < vmppt_min:
            fila["motivo"] = f"Vmp {vmp:,.0f} V < MPPT mín. {vmppt_min:,.0f} V"
            filas.append(fila)
            continue
        if vmp > vmppt_max:
            fila["motivo"] = f"Vmp {vmp:,.0f} V > MPPT máx. {vmppt_max:,.0f} V"
            filas.append(fila)
            continue

        if isc * str_tr <= isc_lim:
            fila.update(compatible=True, modo="normal", strings_max=n_tr * str_tr)
        elif isc <= isc_lim:
            fila.update(compatible=True, modo="1 string/tracker", strings_max=n_tr)
        else:
            fila["motivo"] = (
                f"Isc×{FS_isc:.2f} = {isc:.1f} A > {isc_lim:.1f} A por tracker "
                "(ni con 1 string por entrada)"
            )
        filas.append(fila)

    df = pd.DataFrame(filas)
    return df.sort_values(
        ["compatible", "P_ac_nom_kW"], ascending=[False, False]
    ).reset_index(drop=True)


def unidades_necesarias(n_strings_total: int, strings_max_por_equipo: int) -> int:
    """Número de inversores para alojar todos los strings (entradas)."""
    if strings_max_por_equipo <= 0:
        return 0
    return math.ceil(n_strings_total / strings_max_por_equipo)


# ══════════════════════════════════════════════════════════════════════════════
# 2. Comparación de configuraciones con clipping AC real
# ══════════════════════════════════════════════════════════════════════════════
def energia_con_clipping(p_ac_W: np.ndarray, p_ac_max_W: float) -> tuple[float, float]:
    """
    Aplica el límite AC sobre la serie horaria P_ac (W, sin límite) y
    retorna (E_ac_kWh_anual, clipping_pct).
    """
    p = np.asarray(p_ac_W, dtype=float)
    p = np.nan_to_num(p, nan=0.0)
    e_sin = float(p.sum()) / 1000.0
    if p_ac_max_W is None or p_ac_max_W <= 0 or e_sin <= 0:
        return round(e_sin, 1), 0.0
    e_con = float(np.minimum(p, p_ac_max_W).sum()) / 1000.0
    clip = 100.0 * (1.0 - e_con / e_sin)
    return round(e_con, 1), round(clip, 2)


def comparar_configuraciones(
    p_ac_horaria_W,
    configs: list[dict],
    p_dc_stc_kW: float,
    capex_sin_inversores_usd: float,
    tarifa_cop_kwh: float,
    tipo_cambio: float,
    tasa_descuento: float = 0.10,
    tasa_escalacion_tarifa: float = 0.0,
    tasa_degradacion_pct: float = 0.4,
    opex_pct_capex: float = 1.5,
    n_anos: int = 25,
    beneficios_1715_usd: float = 0.0,
) -> pd.DataFrame:
    """
    Cada config: {"nombre", "p_ac_unidad_W", "n_unidades", "costo_unidad_usd"}.
    Retorna DataFrame comparativo con E_ac, clipping, CAPEX, TIR, VPN,
    payback y LCOE — usando calculos/financiero.py.
    """
    filas = []
    for cfg in configs:
        n_u = int(cfg["n_unidades"])
        p_cap = float(cfg["p_ac_unidad_W"]) * n_u
        e_ac, clip = energia_con_clipping(p_ac_horaria_W, p_cap)
        costo_inv = float(cfg.get("costo_unidad_usd") or 0.0) * n_u
        capex = capex_sin_inversores_usd + costo_inv

        flujos = calcular_flujo_caja(
            capex_usd=capex,
            beneficios_1715_usd=beneficios_1715_usd,
            e_ac_kWh_anual=e_ac,
            tarifa_cop_kWh=tarifa_cop_kwh,
            tipo_cambio=tipo_cambio,
            tasa_escalacion_tarifa=tasa_escalacion_tarifa,
            tasa_degradacion_pct=tasa_degradacion_pct,
            opex_pct_capex=opex_pct_capex,
            n_anos=n_anos,
        )
        met = calcular_metricas(flujos, tasa_descuento, capex, e_ac, tipo_cambio)
        ratio = (p_dc_stc_kW * 1000.0 / p_cap) if p_cap > 0 else float("nan")
        filas.append({
            "Configuración": f"{n_u} × {cfg['nombre']}",
            "AC total (kW)": round(p_cap / 1000.0, 1),
            "Ratio DC/AC": round(ratio, 2),
            "E_ac (kWh/año)": round(e_ac),
            "Clipping (%)": clip,
            "CAPEX (USD)": round(capex),
            "TIR (%)": met.get("tir_pct"),
            "VPN (USD)": round(met["vpn_usd"]) if met.get("vpn_usd") is not None else None,
            "Payback (años)": met.get("payback_simple"),
            "LCOE (USD/kWh)": met.get("lcoe_usd_kWh"),
            "LCOE (COP/kWh)": met.get("lcoe_cop_kWh"),
        })
    return pd.DataFrame(filas)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Barrido de ratio DC/AC
# ══════════════════════════════════════════════════════════════════════════════
def barrido_dc_ac(
    p_ac_horaria_W,
    p_dc_stc_kW: float,
    capex_sin_inversores_usd: float,
    costo_usd_por_kw_ac: float,
    tarifa_cop_kwh: float,
    tipo_cambio: float,
    ratios: list[float] | None = None,
    tasa_descuento: float = 0.10,
    tasa_escalacion_tarifa: float = 0.0,
    tasa_degradacion_pct: float = 0.4,
    opex_pct_capex: float = 1.5,
    n_anos: int = 25,
    beneficios_1715_usd: float = 0.0,
) -> pd.DataFrame:
    """
    Barre ratios DC/AC (capacidad AC = P_dc / ratio), estimando el costo del
    inversor como costo_usd_por_kw_ac × kW AC instalados.
    Marca el óptimo (LCOE mínimo) en la columna "óptimo".
    """
    if ratios is None:
        ratios = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0, 2.2]
    filas = []
    for r in ratios:
        ac_kw = p_dc_stc_kW / r
        e_ac, clip = energia_con_clipping(p_ac_horaria_W, ac_kw * 1000.0)
        capex = capex_sin_inversores_usd + costo_usd_por_kw_ac * ac_kw
        flujos = calcular_flujo_caja(
            capex_usd=capex,
            beneficios_1715_usd=beneficios_1715_usd,
            e_ac_kWh_anual=e_ac,
            tarifa_cop_kWh=tarifa_cop_kwh,
            tipo_cambio=tipo_cambio,
            tasa_escalacion_tarifa=tasa_escalacion_tarifa,
            tasa_degradacion_pct=tasa_degradacion_pct,
            opex_pct_capex=opex_pct_capex,
            n_anos=n_anos,
        )
        met = calcular_metricas(flujos, tasa_descuento, capex, e_ac, tipo_cambio)
        filas.append({
            "Ratio DC/AC": round(r, 2),
            "AC (kW)": round(ac_kw, 1),
            "E_ac (kWh/año)": round(e_ac),
            "Clipping (%)": clip,
            "CAPEX (USD)": round(capex),
            "TIR (%)": met.get("tir_pct"),
            "LCOE (USD/kWh)": met.get("lcoe_usd_kWh"),
        })
    df = pd.DataFrame(filas)
    lcoes = pd.to_numeric(df["LCOE (USD/kWh)"], errors="coerce")
    df["óptimo"] = ""
    if lcoes.notna().any():
        df.loc[lcoes.idxmin(), "óptimo"] = "⭐"
    return df
