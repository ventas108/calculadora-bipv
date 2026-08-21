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


# Columnas financieras/técnicas de comparar_configuraciones() -- se usan para
# rellenar con None las filas de inversores incompatibles/sin datos, que no
# pasan por esa función (no hay unidades que calcular para ellos).
_COLS_FINANCIERAS = (
    "Configuración", "AC total (kW)", "Ratio DC/AC", "E_ac (kWh/año)",
    "Clipping (%)", "CAPEX (USD)", "TIR (%)", "VPN (USD)",
    "Payback (años)", "LCOE (USD/kWh)", "LCOE (COP/kWh)",
)


def comparar_todos_los_inversores_compatibles(
    df_compatibilidad: pd.DataFrame,
    n_strings_total: int,
    p_ac_horaria_W,
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
    Arma automáticamente las configuraciones para TODOS los inversores del
    catálogo marcados compatible=True en `df_compatibilidad` (salida de
    filtrar_inversores_compatibles()) -- a diferencia del flujo manual de 4b
    (el usuario elige 2-4 modelos a mano), esto cubre TODO el catálogo
    compatible de una sola vez. Barato de calcular: reusa la misma serie
    horaria p_ac_horaria_W ya simulada en 📊 Producción -- cada candidato
    solo aplica clipping/escala sobre esa serie, no vuelve a correr física.

    A diferencia de comparar_configuraciones() (que asume que ya le pasaron
    candidatos filtrados), esta función SÍ incluye los inversores marcados
    incompatibles en el resultado -- con "Compatible": "❌" y su motivo en
    "_motivo" -- mismo principio de transparencia que
    calculos.comparador_paneles.comparar_paneles(): un agente de IA necesita
    saber que un candidato existe y por qué se descartó, no que simplemente
    falte de la lista sin explicación.

    Devuelve un DataFrame ordenado por: compatibles primero (por LCOE
    ascendente entre ellos), incompatibles al final -- vacío si
    df_compatibilidad está vacío.
    """
    if df_compatibilidad.empty:
        return pd.DataFrame()

    configs = []
    filas_excluidas = []

    def _fila_excluida(modelo: str, motivo: str) -> dict:
        fila = {c: None for c in _COLS_FINANCIERAS}
        fila.update({"Modelo": modelo, "Compatible": "❌", "_motivo": motivo, "Configuración": modelo})
        return fila

    for _, row in df_compatibilidad.iterrows():
        if not row["compatible"]:
            filas_excluidas.append(_fila_excluida(row["modelo"], row["motivo"]))
            continue

        p_ac_u = (row["P_ac_nom_kW"] or 0) * 1000.0
        if p_ac_u <= 0:
            filas_excluidas.append(
                _fila_excluida(row["modelo"], "Sin potencia AC nominal (P_ac_nom_W) en el catálogo")
            )
            continue

        n_u = unidades_necesarias(n_strings_total, int(row["strings_max"]))
        if n_u <= 0:
            filas_excluidas.append(
                _fila_excluida(row["modelo"], "No se pudieron determinar las unidades necesarias")
            )
            continue

        nombre = row["modelo"] + (" (1 str/MPPT)" if row["modo"] == "1 string/tracker" else "")
        configs.append({
            "modelo": row["modelo"], "nombre": nombre,
            "p_ac_unidad_W": p_ac_u, "n_unidades": n_u,
            "costo_unidad_usd": row["costo_usd"] if row["costo_usd"] is not None else 0.0,
        })

    df_cmp = pd.DataFrame()
    if configs:
        df_cmp = comparar_configuraciones(
            p_ac_horaria_W,
            [{"nombre": c["nombre"], "p_ac_unidad_W": c["p_ac_unidad_W"],
              "n_unidades": c["n_unidades"], "costo_unidad_usd": c["costo_unidad_usd"]}
             for c in configs],
            p_dc_stc_kW,
            capex_sin_inversores_usd=capex_sin_inversores_usd,
            tarifa_cop_kwh=tarifa_cop_kwh, tipo_cambio=tipo_cambio,
            tasa_descuento=tasa_descuento, tasa_escalacion_tarifa=tasa_escalacion_tarifa,
            tasa_degradacion_pct=tasa_degradacion_pct, opex_pct_capex=opex_pct_capex,
            n_anos=n_anos, beneficios_1715_usd=beneficios_1715_usd,
        )
        df_cmp.insert(0, "Modelo", [c["modelo"] for c in configs])
        df_cmp["Compatible"] = "✅"
        df_cmp["_motivo"] = ""

    df_todo = pd.concat([df_cmp, pd.DataFrame(filas_excluidas)], ignore_index=True)
    if not df_todo.empty:
        df_todo["_orden_compat"] = df_todo["Compatible"].map({"✅": 0, "❌": 1})
        df_todo = (
            df_todo.sort_values(
                ["_orden_compat", "LCOE (USD/kWh)"], ascending=[True, True], na_position="last",
            )
            .drop(columns="_orden_compat")
            .reset_index(drop=True)
        )
    return df_todo


def formatear_comparacion_inversores(df: pd.DataFrame, tipo_instalacion: str) -> str:
    """Texto plano para agentes/analista_produccion.py -- mismo principio que
    formatear_comparacion_paneles(): nunca se le pasa el DataFrame crudo a un
    LLM, y el tipo de instalación se declara explícito.

    Aclara que el criterio técnico aquí es energía con clipping real (E_ac)
    y % de clipping (menos es mejor) -- NO Performance Ratio (PR), que no
    aplica a esta comparación (el panel/geometría no cambian, solo el
    inversor). Incluye los incompatibles CON su motivo, igual que
    formatear_comparacion_paneles().
    """
    if df.empty:
        return (
            f"Tipo de instalación: {tipo_instalacion}.\n\n"
            "No hay ningún inversor comparable en el catálogo."
        )

    lineas = [
        f"Tipo de instalación: {tipo_instalacion}.",
        "",
        "Esta comparación es de INVERSORES sobre el MISMO panel, string (N en serie) y "
        "geometría del proyecto -- el criterio técnico es energía anual con clipping AC real "
        "(E_ac) y el % de clipping (pérdida por recorte del inversor; menos es mejor). NO "
        "Performance Ratio (PR) -- no aplica aquí, el panel/geometría no cambian, solo el "
        "inversor.",
        "",
        "## Inversores comparados (compatibles primero, ordenados por LCOE ascendente; "
        "incompatibles al final con su motivo)",
        "",
    ]
    for _, r in df.iterrows():
        if r["Compatible"] == "❌":
            lineas.append(f"- **{r['Modelo']}** — Compatible: ❌ ({r['_motivo']})")
            continue
        irr = f"{r['TIR (%)']:.1f}%" if r["TIR (%)"] is not None else "None (sin solución real)"
        payback = f"{r['Payback (años)']:.1f} años" if r["Payback (años)"] is not None else "None"
        lcoe = f"{r['LCOE (USD/kWh)']:.4f} USD/kWh" if r["LCOE (USD/kWh)"] is not None else "None"
        lineas.append(
            f"- **{r['Configuración']}** — Compatible: ✅\n"
            f"  E_ac={r['E_ac (kWh/año)']:,.0f} kWh/año, clipping={r['Clipping (%)']:.2f}%, "
            f"AC total={r['AC total (kW)']:.1f} kW, ratio DC/AC={r['Ratio DC/AC']:.2f} | "
            f"CAPEX=USD {r['CAPEX (USD)']:,.0f}, VPN=USD {r['VPN (USD)']:,.0f}, "
            f"IRR={irr}, payback={payback}, LCOE={lcoe}"
        )
    return "\n".join(lineas)


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
