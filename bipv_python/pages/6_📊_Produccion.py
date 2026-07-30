"""Página 6 — Producción anual BIPV (IEC 61724)."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from calculos.produccion import simular_produccion_anual, perdidas_desglosadas
from datos.tecnologias_bipv import MODULOS_BIPV
from datos.catalogo_inversores import INVERSORES

st.set_page_config(page_title="Producción — BIPV", page_icon="📊", layout="wide")
st.title("📊 Producción Anual — IEC 61724")
st.caption(
    "Simulación hora a hora · Motor SDM De Soto 2006 · "
    "Temperatura NOCT · Métricas IEC 61724"
)

# ── Prerequisitos ─────────────────────────────────────────────────────────────
if not st.session_state.get("recurso_solar_ok"):
    st.warning("⚠️ Primero ejecuta ☀️ Recurso Solar para obtener el TMY del sitio.")
    st.stop()

tmy             = st.session_state["tmy_df"]
ciudad          = st.session_state.get("tmy_ciudad", "—")
poa_bruta_anual = st.session_state.get("poa_anual_kWh_m2", 0.0)

# ── Selección de POA base: Motor Óptico tiene prioridad sobre Mismatch ────────
_motor_ok       = st.session_state.get("motor_optico_ok", False)
_mo_summary     = st.session_state.get("motor_optico_summary", {})
_mismatch_ok    = st.session_state.get("mismatch_ok", False)

# Factor de pérdidas de la página Mismatch (default 1.0 si no se ejecutó)
factor_pr = st.session_state.get("factor_global_mismatch", 1.0)
poa_ef    = st.session_state.get("poa_efectiva_kWh_m2", poa_bruta_anual)

if _motor_ok:
    # Motor Óptico disponible — usar POA corregida hora a hora (IAM + Soiling + Térmico)
    poa_base          = st.session_state["poa_efectiva_df"]
    poa_base_label    = "POA efectiva — Motor Óptico"
    poa_display_anual = st.session_state.get("poa_efectiva_anual_kWh_m2", poa_bruta_anual)
    _factor_global_mo = _mo_summary.get("factor_global", 1.0)
    st.success(
        f"🔆 **Motor Óptico activo** — POA corregida: **{poa_display_anual:,.0f} kWh/m²/año** "
        f"(factor global **{_factor_global_mo*100:.1f}%** = IAM + Soiling + Térmico). "
        "La simulación usa la irradiancia real hora a hora, no un factor promedio."
    )
    if _mismatch_ok:
        st.info(
            f"🔀 Mismatch también disponible (factor {factor_pr*100:.1f}%) — "
            "se aplica además de las correcciones ópticas del Motor Óptico."
        )
else:
    poa_base          = st.session_state["poa_df"]
    poa_base_label    = "POA bruta"
    poa_display_anual = poa_bruta_anual
    if _mismatch_ok:
        st.success(
            f"✅ Cascada Mismatch cargada — POA efectiva: **{poa_ef:.0f} kWh/m²/año** | "
            f"Factor PR parcial: **{factor_pr*100:.1f}%**"
        )
    else:
        st.info(
            "ℹ️ No se detecta resultado de 🔀 Mismatch ni de 🔆 Motor Óptico — "
            f"se usará POA bruta ({poa_bruta_anual:.0f} kWh/m²/año). "
            "Puedes continuar o ejecutar primero el Motor Óptico para mayor precisión."
        )

with st.expander("ℹ️ ¿Qué POA se usa en la simulación?", expanded=False):
    st.markdown(f"""
    | Fuente de POA | Estado | Valor anual |
    |---|---|---|
    | POA bruta (PVGIS/TMY) | siempre disponible | {poa_bruta_anual:,.0f} kWh/m²/año |
    | Motor Óptico (IAM + Soiling + Térmico) | {"✅ activo" if _motor_ok else "⬜ no ejecutado"} | {st.session_state.get("poa_efectiva_anual_kWh_m2", "—"):{",.0f" if _motor_ok else ""}} {"kWh/m²/año" if _motor_ok else ""} |
    | Factor Mismatch | {"✅ {:.1f}%".format(factor_pr*100) if _mismatch_ok else "⬜ no ejecutado"} | — |

    **Prioridad:** Motor Óptico > Mismatch > POA bruta.
    El Motor Óptico corrige la irradiancia **hora a hora** (más preciso que un factor anual).
    El factor Mismatch se aplica como pérdida adicional encima de la POA ya corregida.

    🟢 **POA actualmente en uso:** `{poa_base_label}` — {poa_display_anual:,.0f} kWh/m²/año
    """)

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — CONFIGURACIÓN DEL SISTEMA
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚙️ Configuración del sistema")

col_c1, col_c2, col_c3 = st.columns(3)

with col_c1:
    panel_nombre = st.selectbox(
        "Panel fotovoltaico",
        list(MODULOS_BIPV.keys()),
        index=list(MODULOS_BIPV.keys()).index("ASP-ST1-T40"),
    )
    panel = MODULOS_BIPV[panel_nombre]

    # Mostrar ficha rápida
    st.caption(
        f"Pmax STC: {panel.get('Pmax_stc','—')} W · "
        f"Área: {panel['area_m2']} m² · "
        f"NOCT: {panel.get('NOCT',45)}°C"
    )

with col_c2:
    # Tomar N_paneles de Dimensionamiento si existe
    n_default = st.session_state.get("N_paneles_dim", 0)
    p_default = st.session_state.get("P_dc_stc_kW_dim", 0.0)

    N_paneles = st.number_input(
        "Número de módulos (N_paneles)",
        min_value=1, max_value=5000,
        value=int(n_default) if n_default > 0 else 64,
        step=1,
        help="Resultado de la página 📐 Dimensionamiento, o ingresar manualmente.",
    )

    area_ocup = N_paneles * panel["area_m2"]
    P_stc_kW  = round(panel.get("Pmax_stc", 60) * N_paneles / 1000, 3)
    st.metric("Potencia instalada", f"{P_stc_kW:.2f} kWp")
    st.metric("Área módulos",       f"{area_ocup:.1f} m²")

with col_c3:
    inversor_nombre = st.selectbox("Inversor", list(INVERSORES.keys()))
    eta_inv = st.slider(
        "Eficiencia del inversor (%)",
        min_value=90.0, max_value=99.0,
        value=97.5, step=0.5,
        help="Growatt MID15KTL3-X: 97.6% típico. Valor CEC weighted efficiency.",
    )
    eta_inv_frac = eta_inv / 100.0
    st.caption(f"Pérdida inversor: **{100-eta_inv:.1f}%** de E_dc")

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — SIMULACIÓN
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")

btn_sim = st.button(
    "▶️ Simular producción anual hora a hora (SDM De Soto 2006)",
    type="primary",
    use_container_width=True,
)

if btn_sim or st.session_state.get("produccion_ok"):

    if btn_sim:
        with st.spinner(
            f"Simulando 8.760 horas para {N_paneles} módulos {panel_nombre} en {ciudad}..."
        ):
            res = simular_produccion_anual(
                tmy               = tmy,
                poa_base          = poa_base,
                panel             = panel,
                N_paneles         = N_paneles,
                eta_inversor      = eta_inv_frac,
                factor_pr_mismatch= factor_pr,
                P_dc_stc_kW       = P_stc_kW,
            )
        st.session_state["res_produccion"]    = res
        st.session_state["produccion_ok"]     = True
        st.session_state["N_paneles_dim"]     = N_paneles
        st.session_state["P_dc_stc_kW_dim"]   = P_stc_kW
        st.session_state["E_ac_anual_kWh"]    = res["E_ac_anual_kWh"]
        st.session_state["PR_sistema"]        = res["PR"]
    else:
        res = st.session_state.get("res_produccion", {})

    if not res:
        st.stop()

    # ── Nota sobre correcciones aplicadas ────────────────────────────────────
    st.markdown("---")
    if _motor_ok:
        _b0   = _mo_summary.get("b0", "—")
        _k    = _mo_summary.get("k_bipv", "—")
        _noct = _mo_summary.get("noct", "—")
        _gam  = _mo_summary.get("coef_temp", 0) * 100
        _fiam  = _mo_summary.get("f_iam_prom",  1.0)
        _fsoil = _mo_summary.get("f_soil_prom", 1.0)
        _fterm = _mo_summary.get("f_term_prom", 1.0)
        st.info(
            f"🔆 **Correcciones óptico-térmicas aplicadas** (Motor Óptico):\n\n"
            f"• **IAM reflexión** (b₀={_b0:.3f}): factor promedio {_fiam:.3f} "
            f"→ pérdida {(1-_fiam)*100:.1f}%\n\n"
            f"• **Soiling estacional Colombia**: factor promedio {_fsoil:.3f} "
            f"→ pérdida {(1-_fsoil)*100:.1f}%\n\n"
            f"• **Térmico confinado** (k={_k}, NOCT={_noct}°C, γ={_gam:.2f}%/°C): "
            f"factor promedio {_fterm:.3f} → pérdida {(1-_fterm)*100:.1f}%\n\n"
            f"**Factor global aplicado: {_factor_global_mo*100:.1f}%** de la POA bruta "
            f"({poa_bruta_anual:,.0f} → {poa_display_anual:,.0f} kWh/m²/año)."
        )

    # ── Métricas IEC 61724 ────────────────────────────────────────────────────
    st.subheader("📈 Métricas IEC 61724")

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("E_ac anual",       f"{res['E_ac_anual_kWh']:,.0f} kWh",
              help="Energía AC entregada a la red o al edificio")
    m2.metric("E_dc anual",       f"{res['E_dc_anual_kWh']:,.0f} kWh",
              help="Energía DC generada por los módulos")
    m3.metric("Y_f (Final yield)", f"{res['Y_f']:,.0f} kWh/kWp",
              help="Producción normalizada — equivalente a horas a plena carga AC")
    m4.metric("Y_r (Ref. yield)",  f"{res['Y_r']:,.0f} h",
              help="POA efectiva / 1 kW/m² — horas sol pico equivalentes")
    m5.metric("PR (Perf. Ratio)",  f"{res['PR']*100:.1f}%",
              help="Performance Ratio IEC 61724 = Y_f / Y_r. Bueno: >75%")
    m6.metric("Factor de Planta",  f"{res['CF_pct']:.1f}%",
              help="Capacity Factor = E_ac / (P_STC × 8760 h)")

    # ── Gráfica mensual ───────────────────────────────────────────────────────
    st.subheader("📅 Producción mensual")

    df_m = res["df_mensual"]

    fig_mes = go.Figure()
    fig_mes.add_trace(go.Bar(
        name="E_ac (kWh)",
        x=df_m.index,
        y=df_m["E_ac (kWh)"],
        marker_color="#2E7D32",
        opacity=0.88,
    ))
    fig_mes.add_trace(go.Bar(
        name="E_dc (kWh)",
        x=df_m.index,
        y=df_m["E_dc (kWh)"],
        marker_color="#66BB6A",
        opacity=0.6,
    ))
    fig_mes.add_trace(go.Bar(
        name="Pérdida T° (kWh)",
        x=df_m.index,
        y=df_m["Pérdida T° (kWh)"],
        marker_color="#EF5350",
        opacity=0.7,
    ))
    fig_mes.update_layout(
        barmode="group",
        xaxis_title="Mes",
        yaxis_title="Energía (kWh)",
        height=380,
        legend=dict(orientation="h", y=-0.25),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(b=80),
    )
    st.plotly_chart(fig_mes, use_container_width=True)

    # ── Gráfica kWh/kWp mensual (normalizada) ────────────────────────────────
    with st.expander("📊 Ver producción normalizada (kWh/kWp por mes)"):
        fig_norm = go.Figure(go.Bar(
            x=df_m.index,
            y=df_m["Producción (kWh/kWp)"].round(1),
            marker_color="#1565C0",
            text=df_m["Producción (kWh/kWp)"].round(1),
            textposition="outside",
        ))
        fig_norm.update_layout(
            yaxis_title="kWh/kWp",
            height=320,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_norm, use_container_width=True)

    # ── Heatmap perfil de potencia ────────────────────────────────────────────
    st.subheader("🌡️ Perfil de potencia DC — promedio diario (kW)")

    df_h = res["df_horario"].copy()
    df_h["hora"] = df_h.index.hour
    df_h["mes"]  = df_h.index.month

    pivot_p = df_h.groupby(["hora", "mes"])["P_dc_kW"].mean().unstack()
    meses_es = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    pivot_p.columns = meses_es

    fig_hm = go.Figure(go.Heatmap(
        z=pivot_p.values,
        x=pivot_p.columns,
        y=[f"{h:02d}:00" for h in pivot_p.index],
        colorscale="Greens",
        colorbar=dict(title="kW"),
        zmin=0,
    ))
    fig_hm.update_layout(
        xaxis_title="Mes",
        yaxis_title="Hora del día (UTC)",
        height=400,
        plot_bgcolor="white",
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    # ── Nota PR > 100% ────────────────────────────────────────────────────────
    if res["PR"] > 1.0:
        st.info(
            f"ℹ️ **PR = {res['PR']*100:.1f}% > 100%** — resultado correcto para "
            f"**{ciudad}** (altitud {st.session_state.get('alt_m', '≈2600')} m, "
            f"T_amb media {st.session_state.get('t_media_anual', 13.9):.1f}°C). "
            "En climas fríos de alta altitud, los módulos CdTe operan por debajo de 25°C "
            "durante muchas horas, ganando eficiencia respecto a STC. "
            "El PR > 100% indica **sobre-rendimiento real** (no es un error de cálculo). "
            "IEC 61724 permite PR > 100% cuando las condiciones reales superan las STC."
        )

    # ── Desglose de pérdidas / ganancias ─────────────────────────────────────
    st.subheader("📉 Balance energético del sistema")

    e_ref    = round(poa_bruta_anual * P_stc_kW, 0)
    e_dc     = res["E_dc_anual_kWh"]
    p_temp   = res["perdida_temp_kWh"]
    p_inv    = res["perdida_inv_kWh"]
    delta_sdm = e_dc - e_ref   # positivo = ganancia

    etapas_bal  = ["Ganancia T° CdTe" if delta_sdm >= 0 else "Pérdida óptica+T°",
                   "Pérdida T° (horas calientes)",
                   "Pérdida inversor"]
    vals_bal    = [delta_sdm, -p_temp, -p_inv]
    colores_bal = [
        "#2E7D32" if delta_sdm >= 0 else "#EF5350",
        "#FF7043",
        "#FFA726",
    ]
    pct_ref = [round(abs(v) / e_ref * 100, 1) if e_ref > 0 else 0 for v in vals_bal]

    fig_loss = go.Figure(go.Bar(
        x=vals_bal,
        y=etapas_bal,
        orientation="h",
        marker_color=colores_bal,
        text=[f"{v:+,.0f} kWh ({p}%)" for v, p in zip(vals_bal, pct_ref)],
        textposition="outside",
    ))
    fig_loss.add_vline(x=0, line_color="gray", line_width=1)
    fig_loss.update_layout(
        xaxis_title="Δ Energía respecto a E_ref (kWh/año)",
        height=260,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=200, r=180),
    )
    st.plotly_chart(fig_loss, use_container_width=True)
    st.caption(
        f"E ref (P_STC × POA): **{e_ref:,.0f} kWh** | "
        f"E_dc: **{e_dc:,.0f} kWh** | "
        f"E_ac: **{res['E_ac_anual_kWh']:,.0f} kWh**"
    )

    # Tabla desglose
    with st.expander("📋 Ver tabla detallada de balance IEC 61724"):
        df_loss = perdidas_desglosadas(res, poa_bruta_anual)
        if not df_loss.empty:
            st.dataframe(
                df_loss.style.format({
                    "kWh":        "{:,.0f}",
                    "Δ kWh":      "{:+,.0f}",
                    "% de E_ref": "{:.2f}%",
                }),
                use_container_width=True,
            )

    # ── Tabla mensual completa ────────────────────────────────────────────────
    with st.expander("📋 Ver tabla de producción mensual completa"):
        st.dataframe(
            df_m.style.format({
                "E_dc (kWh)":            "{:,.0f}",
                "E_ac (kWh)":            "{:,.0f}",
                "Pérdida T° (kWh)":      "{:,.0f}",
                "Producción (kWh/kWp)":  "{:.1f}",
            }).background_gradient(subset=["E_ac (kWh)"], cmap="Greens"),
            use_container_width=True,
        )

    # ── Resumen final ─────────────────────────────────────────────────────────
    st.success(
        f"✅ Simulación completada para **{ciudad}** | "
        f"Sistema: **{P_stc_kW:.2f} kWp** ({N_paneles} módulos {panel_nombre}) | "
        f"**E_ac = {res['E_ac_anual_kWh']:,.0f} kWh/año** | "
        f"PR = **{res['PR']*100:.1f}%** | "
        f"Y_f = **{res['Y_f']:,.0f} kWh/kWp** | "
        f"Continúa en 💰 Financiero para el análisis Ley 1715."
    )

    # Guardar para Financiero
    st.session_state["E_ac_anual_kWh"]      = res["E_ac_anual_kWh"]
    st.session_state["E_dc_anual_kWh"]      = res["E_dc_anual_kWh"]
    st.session_state["PR_sistema"]          = res["PR"]
    st.session_state["Y_f_kWh_kWp"]        = res["Y_f"]
    st.session_state["P_stc_kW_sistema"]   = P_stc_kW
    st.session_state["N_paneles_final"]     = N_paneles
    st.session_state["panel_nombre_final"]  = panel_nombre
    st.session_state["eta_inversor"]        = eta_inv_frac
    st.session_state["df_mensual_produccion"] = df_m   # para Página 11 Balance
    st.session_state["produccion_ok"]       = True

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN — DIAGNÓSTICO IEC 61724: PR CONVENCIONAL Y PR CORREGIDO POR T°
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🔍 Diagnóstico BIPV: PR convencional · PR corregido · Pérdidas T°")
    with st.expander("ℹ️ ¿Qué mide cada PR?", expanded=False):
        st.markdown("""
| Indicador | Fórmula | Qué muestra |
|---|---|---|
| **PR convencional** | E_real ÷ (P_STC × HSP) | PR estándar IEC 61724 — incluye **todas** las pérdidas (temperatura + eléctricas + ópticas) |
| **% Pérdidas T°** | (1 − factor_T) × 100 | Cuánto pierde el sistema **solo por calor** = γ × (T_cell − 25°C) |
| **PR corregido T°** | PR_conv ÷ factor_T | PR sin efecto temperatura — revela las **pérdidas reales** (suciedad, sombras, degradación, cableado) |

*factor_T = 1 + γ × (T_cell_media − 25°C)   ·   γ = coeficiente de temperatura de Pmax del panel*

**Regla de diagnóstico:**
- Si PR_corr ≈ PR_conv → temperatura no es el problema principal; buscar fallas mecánicas/eléctricas
- Si PR_corr >> PR_conv → temperatura está consumiendo una fracción importante de la producción (común en BIPV fachada)
- Si PR_corr < 0.85 → existen pérdidas no térmicas significativas (suciedad, sombras, degradación, strings)
        """)

    # ── Pre-cómputos desde la simulación ─────────────────────────────────────
    _poa_hsp = poa_base.copy()
    _poa_hsp["_mes"] = _poa_hsp.index.month
    _hsp_mes = _poa_hsp.groupby("_mes")["poa_global"].sum() / 1000.0   # kWh/m² = HSP

    # T_cell media mensual desde df_horario (ya calculado por la simulación)
    _df_h_diag = res["df_horario"].copy()
    _df_h_diag["_mes"] = _df_h_diag.index.month
    # Solo horas con irradiancia > 10 W/m² para promediar T_cell operativa real
    _df_h_diag_sol = _df_h_diag[_df_h_diag["G_eff_Wm2"] > 10]
    _t_cell_mes = _df_h_diag_sol.groupby("_mes")["T_cel_C"].mean()

    # E_ac_STC mensual = (E_dc + pérdida_T) × eta_inv  → producción si T_cell = 25°C siempre
    # = "Producción a irradiancia real pero temperatura constante 25°C"
    _e_dc_mes      = df_m["E_dc (kWh)"]
    _perdida_t_mes = df_m["Pérdida T° (kWh)"]
    _e_ac_stc_mes  = (_e_dc_mes + _perdida_t_mes) * eta_inv_frac  # kWh, T=25°C

    # Coeficiente de temperatura de Pmax del panel (%/°C → fracción/°C)
    gamma_pct = panel.get("Tk_gamma", -0.45)          # %/°C  (negativo)
    gamma_frac = gamma_pct / 100.0                     # fracción/°C

    meses_etiq = ["Ene","Feb","Mar","Abr","May","Jun",
                  "Jul","Ago","Sep","Oct","Nov","Dic"]

    # ── Info del coeficiente de temperatura ──────────────────────────────────
    st.info(
        f"Panel seleccionado: **{panel_nombre}** · "
        f"γ (Tk_gamma) = **{gamma_pct:+.3f} %/°C** · "
        f"NOCT = **{panel.get('NOCT', 45):.0f}°C**  |  "
        f"A mayor temperatura → mayor pérdida de potencia (monocristalino típico: −0.35 a −0.45 %/°C)"
    )

    # ── Tabla de ingreso de datos reales ─────────────────────────────────────
    st.markdown("#### 📥 Producción real del inversor (kWh/mes)")
    st.caption("Tomar de: display del inversor · app de monitoreo · factura EPM · medidor bidireccional")

    _prev = st.session_state.get("diag_real_kwh", {})
    cols_inp = st.columns(6)
    kwh_real = {}
    for i, mes in enumerate(meses_etiq):
        col = cols_inp[i % 6]
        kwh_real[mes] = col.number_input(
            mes,
            min_value=0.0, max_value=500_000.0,
            value=float(_prev.get(mes, 0.0)),
            step=10.0, format="%.1f",
            key=f"diag_real_{mes}",
            help=f"kWh AC reales medidos por el inversor en {mes}",
        )
    st.session_state["diag_real_kwh"] = kwh_real
    meses_con_dato = [m for m in meses_etiq if kwh_real[m] > 0]

    if not meses_con_dato:
        st.info(
            "💡 Ingresa los kWh reales de al menos un mes para activar el diagnóstico. "
            "Con dos o más meses obtienes la tendencia de degradación y las pérdidas por temperatura."
        )
    else:
        # ── Calcular comparativa completa ─────────────────────────────────────
        filas = []
        for i, mes in enumerate(meses_etiq):
            num_mes      = i + 1
            e_sim_arr    = df_m.loc[df_m.index == mes, "E_ac (kWh)"].values
            e_sim_val    = float(e_sim_arr[0]) if len(e_sim_arr) > 0 else 0.0
            e_stc_arr    = _e_ac_stc_mes[_e_ac_stc_mes.index == mes].values
            e_stc_val    = float(e_stc_arr[0]) if len(e_stc_arr) > 0 else e_sim_val
            hsp_val      = float(_hsp_mes.get(num_mes, 0.0))
            t_cell_val   = float(_t_cell_mes.get(num_mes, 25.0))
            e_real       = kwh_real[mes]

            # Factor temperatura mensual: < 1 cuando T_cell > 25°C (pérdida)
            factor_T     = 1.0 + gamma_frac * (t_cell_val - 25.0)
            perdida_T_pct= (1.0 - factor_T) * 100.0   # % de producción perdida por calor

            # PR simulado esperado (referencia)
            pr_esp = (e_sim_val / (P_stc_kW * hsp_val)) if (P_stc_kW > 0 and hsp_val > 0) else 0.0
            # PR convencional real = E_real / (P_STC × HSP)  — incluye pérdidas temperatura
            pr_conv = (e_real / (P_stc_kW * hsp_val)) if (e_real > 0 and P_stc_kW > 0 and hsp_val > 0) else None
            # PR corregido por temperatura = PR_conv / factor_T  — elimina efecto térmico
            pr_corr = (pr_conv / factor_T) if (pr_conv is not None and factor_T > 0.5) else None

            if pr_conv is not None:
                ratio_conv = pr_conv / pr_esp if pr_esp > 0 else 0.0
                # Semáforo sobre PR_corregido (pérdidas NO térmicas)
                if pr_corr is not None:
                    if pr_corr >= 0.90:
                        sem_corr = "🟢"; est_corr = "Bueno"
                    elif pr_corr >= 0.80:
                        sem_corr = "🟡"; est_corr = "Revisar"
                    else:
                        sem_corr = "🔴"; est_corr = "Problema"
                else:
                    sem_corr = "⬜"; est_corr = "—"
                delta_kwh  = e_real - e_sim_val
                delta_pct  = (delta_kwh / e_sim_val * 100) if e_sim_val > 0 else 0.0
            else:
                ratio_conv = None; delta_kwh = None; delta_pct = None
                sem_corr = "⬜"; est_corr = "Sin dato"

            filas.append({
                "Mes":              mes,
                "HSP (h)":          round(hsp_val, 1),
                "T_cell (°C)":      round(t_cell_val, 1),
                "factor_T":         round(factor_T, 4),
                "% Pérd. T°":       round(perdida_T_pct, 1),
                "E_STC_sim (kWh)":  round(e_stc_val, 0),     # "producción baja irradiancia"
                "E_sim (kWh)":      round(e_sim_val, 0),      # simulada con temperatura real
                "E_real (kWh)":     round(e_real, 0) if e_real > 0 else "—",
                "PR_esp (%)":       round(pr_esp * 100, 1)   if pr_esp > 0      else "—",
                "PR_conv (%)":      round(pr_conv * 100, 1)  if pr_conv is not None else "—",
                "PR_corr_T (%)":    round(pr_corr * 100, 1)  if pr_corr is not None else "—",
                "Δ kWh":            round(delta_kwh, 0)       if delta_kwh is not None else "—",
                "Δ %":              round(delta_pct, 1)        if delta_pct is not None else "—",
                "Estado":           f"{sem_corr} {est_corr}",
            })

        df_diag = pd.DataFrame(filas)

        # Filtrar filas con datos reales para gráficas
        filas_r     = [f for f in filas if f["E_real (kWh)"] != "—"]
        meses_g     = [f["Mes"]             for f in filas_r]
        pr_esp_g    = [f["PR_esp (%)"]      for f in filas_r]
        pr_conv_g   = [f["PR_conv (%)"]     for f in filas_r]
        pr_corr_g   = [f["PR_corr_T (%)"]   for f in filas_r]
        perdida_t_g = [f["% Pérd. T°"]      for f in filas_r]
        t_cell_g    = [f["T_cell (°C)"]     for f in filas_r]
        e_stc_g     = [f["E_STC_sim (kWh)"] for f in filas_r]
        e_sim_g     = [f["E_sim (kWh)"]     for f in filas_r]
        e_real_g    = [f["E_real (kWh)"]    for f in filas_r]

        # ── TABS de gráficas ──────────────────────────────────────────────────
        tab1, tab2, tab3 = st.tabs([
            "📊 PR convencional vs PR corregido T°",
            "🌡️ Pérdidas por temperatura",
            "📅 kWh: STC vs simulado vs real",
        ])

        with tab1:
            st.caption(
                "**Azul**: PR esperado (simulado con temperatura real) · "
                "**Naranja**: PR convencional real (E_real/P_STC/HSP, incluye pérdidas T°) · "
                "**Verde/Rojo**: PR corregido (sin efecto temperatura) → pérdidas reales no térmicas"
            )
            fig_pr = go.Figure()
            fig_pr.add_trace(go.Bar(
                name="PR esperado (sim)",
                x=meses_g, y=pr_esp_g,
                marker_color="#1565C0", opacity=0.60,
            ))
            fig_pr.add_trace(go.Bar(
                name="PR convencional real",
                x=meses_g, y=pr_conv_g,
                marker_color="#E65100", opacity=0.80,
                text=[f"{v:.1f}%" for v in pr_conv_g],
                textposition="outside",
            ))
            fig_pr.add_trace(go.Bar(
                name="PR corregido T° (real no-térmico)",
                x=meses_g, y=pr_corr_g,
                marker_color=[
                    "#2E7D32" if v >= 90 else
                    "#F9A825" if v >= 80 else
                    "#C62828"
                    for v in pr_corr_g
                ],
                opacity=0.90,
                text=[f"{v:.1f}%" for v in pr_corr_g],
                textposition="inside",
            ))
            fig_pr.add_hline(
                y=85, line_dash="dot", line_color="#C62828",
                annotation_text="Umbral PR_corr 85%", annotation_position="top left",
            )
            fig_pr.update_layout(
                barmode="group", yaxis_title="Performance Ratio (%)",
                height=400, plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", y=-0.28), margin=dict(b=90),
                yaxis=dict(range=[0, max(max(pr_corr_g + [0]), max(pr_esp_g + [0])) * 1.18]),
            )
            st.plotly_chart(fig_pr, use_container_width=True)

        with tab2:
            st.caption(
                "Barras rojas: % de producción perdida por temperatura cada mes. "
                "Línea: T_cell media operativa del panel. "
                "Para BIPV en fachada confinada, T_cell puede llegar a 50–65°C → pérdidas del 10–18%."
            )
            fig_t = go.Figure()
            fig_t.add_trace(go.Bar(
                name="% Pérdida por T° (respecto a STC)",
                x=meses_g, y=perdida_t_g,
                marker_color=[
                    "#C62828" if v > 10 else
                    "#F9A825" if v > 6  else
                    "#43A047"
                    for v in perdida_t_g
                ],
                opacity=0.85,
                text=[f"{v:.1f}%" for v in perdida_t_g],
                textposition="outside",
                yaxis="y1",
            ))
            fig_t.add_trace(go.Scatter(
                name="T_cell media operativa (°C)",
                x=meses_g, y=t_cell_g,
                mode="lines+markers+text",
                text=[f"{v:.0f}°C" for v in t_cell_g],
                textposition="top center",
                line=dict(color="#1565C0", width=2),
                marker=dict(size=7),
                yaxis="y2",
            ))
            fig_t.update_layout(
                yaxis=dict(title="Pérdida T° (%)", range=[0, max(perdida_t_g) * 1.4]),
                yaxis2=dict(title="T_cell (°C)", overlaying="y", side="right",
                            range=[0, max(t_cell_g) * 1.3]),
                height=380, plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", y=-0.28), margin=dict(b=90),
            )
            st.plotly_chart(fig_t, use_container_width=True)

        with tab3:
            st.caption(
                "**Gris**: E_ac_STC — producción si T_cell = 25°C siempre (baja irradiancia, T constante). "
                "**Azul**: E_ac simulada con temperatura real. "
                "**Verde**: E_real del inversor. "
                "La brecha Gris−Azul = pérdidas por temperatura. La brecha Azul−Verde = otras pérdidas reales."
            )
            fig_kwh = go.Figure()
            fig_kwh.add_trace(go.Bar(
                name="E_STC (T=25°C, sin pérd. temp.)",
                x=meses_g, y=e_stc_g,
                marker_color="#9E9E9E", opacity=0.70,
            ))
            fig_kwh.add_trace(go.Bar(
                name="E_sim (temperatura real)",
                x=meses_g, y=e_sim_g,
                marker_color="#1565C0", opacity=0.75,
            ))
            fig_kwh.add_trace(go.Bar(
                name="E_real (inversor)",
                x=meses_g, y=e_real_g,
                marker_color="#2E7D32", opacity=0.88,
                text=[f"{v:,.0f}" for v in e_real_g],
                textposition="outside",
            ))
            fig_kwh.update_layout(
                barmode="group", yaxis_title="Energía (kWh)",
                height=400, plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", y=-0.28), margin=dict(b=90),
            )
            st.plotly_chart(fig_kwh, use_container_width=True)

        # ── Tabla completa ────────────────────────────────────────────────────
        st.markdown("#### 📋 Tabla completa de diagnóstico mes a mes")
        cols_show = ["Mes","HSP (h)","T_cell (°C)","% Pérd. T°",
                     "E_STC_sim (kWh)","E_sim (kWh)","E_real (kWh)",
                     "PR_esp (%)","PR_conv (%)","PR_corr_T (%)","Δ kWh","Estado"]
        st.dataframe(df_diag[cols_show], use_container_width=True, hide_index=True)

        # ── Diagnóstico automático ────────────────────────────────────────────
        meses_rojo     = [f["Mes"] for f in filas_r if f["Estado"].startswith("🔴")]
        meses_amarillo = [f["Mes"] for f in filas_r if f["Estado"].startswith("🟡")]
        meses_verde    = [f["Mes"] for f in filas_r if f["Estado"].startswith("🟢")]

        total_real = sum(kwh_real[m] for m in meses_etiq if kwh_real[m] > 0)
        total_sim  = sum(
            float(df_m.loc[df_m.index == m, "E_ac (kWh)"].values[0])
            for m in meses_con_dato if len(df_m.loc[df_m.index == m]) > 0
        )
        total_stc  = sum(
            float(_e_ac_stc_mes[_e_ac_stc_mes.index == m].values[0])
            for m in meses_con_dato if len(_e_ac_stc_mes[_e_ac_stc_mes.index == m]) > 0
        )
        perdida_t_kwh_total = max(0.0, total_stc - total_sim)
        tarifa_ref  = st.session_state.get("tarifa_kwh", 650)
        perdida_cop = max(0.0, (total_sim - total_real) * tarifa_ref)

        # PR globales acumulados (meses con dato)
        _hsp_total_diag = sum(float(_hsp_mes.get(meses_etiq.index(m)+1, 0.0)) for m in meses_con_dato)
        _factor_T_pond  = (1.0 + gamma_frac * (
            np.mean([float(_t_cell_mes.get(meses_etiq.index(m)+1, 25.0)) for m in meses_con_dato]) - 25.0
        )) if meses_con_dato else 1.0
        pr_conv_global  = (total_real / (P_stc_kW * _hsp_total_diag)) if (_hsp_total_diag > 0 and P_stc_kW > 0) else 0.0
        pr_corr_global  = (pr_conv_global / _factor_T_pond) if _factor_T_pond > 0.5 else 0.0
        perdida_t_pct_global = (1.0 - _factor_T_pond) * 100.0

        st.markdown("#### 🩺 Diagnóstico automático")

        # Métricas resumen
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("PR convencional global", f"{pr_conv_global*100:.1f}%",
                   help="E_real / (P_STC × HSP) — incluye pérdidas temperatura")
        mc2.metric("PR corregido T° global", f"{pr_corr_global*100:.1f}%",
                   help="Pérdidas NO térmicas: suciedad, sombras, degradación, cableado")
        mc3.metric("% Pérd. temperatura (prom.)", f"{perdida_t_pct_global:.1f}%",
                   help=f"γ × (T_cell_media − 25°C) · γ = {gamma_pct:+.3f}%/°C")
        mc4.metric("Pérdida T° acumulada", f"{perdida_t_kwh_total:,.0f} kWh",
                   help="kWh perdidos solo por temperatura en los meses ingresados")

        # Alertas
        if meses_rojo:
            st.error(
                f"🔴 **PR_corregido < 80% en: {', '.join(meses_rojo)}** — "
                "Existen pérdidas NO térmicas significativas. "
                "Causas probables: suciedad severa, sombras, degradación de paneles, "
                "falla en strings o conector MC4 quemado. Inspección de campo urgente."
            )
        if meses_amarillo:
            st.warning(
                f"🟡 **PR_corregido 80–90% en: {', '.join(meses_amarillo)}** — "
                "Pérdidas no térmicas moderadas. "
                "Verificar limpieza, sombreado parcial y revisar strings individuales."
            )
        if meses_verde and not meses_rojo and not meses_amarillo:
            st.success(
                f"🟢 **Sistema en buen estado** en todos los meses con dato ({', '.join(meses_verde)}). "
                f"PR_corregido ≥ 90% — las pérdidas observadas son principalmente por temperatura, "
                f"que es normal en BIPV (γ = {gamma_pct:+.3f}%/°C)."
            )
        if total_sim > 0:
            delta_total     = total_real - total_sim
            delta_pct_total = delta_total / total_sim * 100
            st.info(
                f"📊 **Resumen ({len(meses_con_dato)} meses):** "
                f"E_real = **{total_real:,.0f} kWh** · "
                f"E_sim = **{total_sim:,.0f} kWh** · "
                f"E_STC (T=25°C) = **{total_stc:,.0f} kWh** | "
                f"Diferencia real vs sim = **{delta_total:+,.0f} kWh ({delta_pct_total:+.1f}%)** · "
                f"Pérdida temperatura acumulada ≈ **{perdida_t_kwh_total:,.0f} kWh** "
                f"({perdida_t_kwh_total/total_stc*100:.1f}% de E_STC)"
                + (f" · Pérdida no-térmica ≈ **${perdida_cop:,.0f} COP**" if perdida_cop > 0 else "")
            )

        # ── Guardar para Reporte PDF ──────────────────────────────────────────
        st.session_state["df_diagnostico_real"]  = df_diag
        st.session_state["diag_meses_rojo"]      = meses_rojo
        st.session_state["diag_meses_amarillo"]  = meses_amarillo
        st.session_state["diag_total_real_kwh"]  = total_real
        st.session_state["diag_total_sim_kwh"]   = total_sim
        st.session_state["diag_total_stc_kwh"]   = total_stc
        st.session_state["diag_pr_conv_global"]  = pr_conv_global
        st.session_state["diag_pr_corr_global"]  = pr_corr_global
        st.session_state["diag_perdida_t_pct"]   = perdida_t_pct_global
        st.session_state["diag_perdida_t_kwh"]   = perdida_t_kwh_total
        st.session_state["diag_gamma_pct"]       = gamma_pct
