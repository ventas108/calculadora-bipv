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

tmy      = st.session_state["tmy_df"]
poa_base = st.session_state["poa_df"]
ciudad   = st.session_state.get("tmy_ciudad", "—")
poa_bruta_anual = st.session_state.get("poa_anual_kWh_m2", 0.0)

# Factor de pérdidas de la página Mismatch (default 1.0 si no se ejecutó)
factor_pr = st.session_state.get("factor_global_mismatch", 1.0)
poa_ef    = st.session_state.get("poa_efectiva_kWh_m2", poa_bruta_anual)

if st.session_state.get("mismatch_ok"):
    st.success(
        f"✅ Cascada Mismatch cargada — POA efectiva: **{poa_ef:.0f} kWh/m²/año** | "
        f"Factor PR parcial: **{factor_pr*100:.1f}%**"
    )
else:
    st.info(
        "ℹ️ No se detecta resultado de 🔀 Mismatch — se usará POA bruta sin pérdidas "
        f"({poa_bruta_anual:.0f} kWh/m²/año). Puedes seguir adelante."
    )

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

    # ── Métricas IEC 61724 ────────────────────────────────────────────────────
    st.markdown("---")
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

    # ── Desglose de pérdidas ──────────────────────────────────────────────────
    st.subheader("📉 Desglose de pérdidas del sistema")

    poa_ref_kWh_m2 = poa_bruta_anual  # POA bruta de Recurso Solar

    # Construir Sankey simplificado con barras horizontales
    p_optica    = round((poa_bruta_anual - poa_ef) * P_stc_kW, 0)
    p_temp      = res["perdida_temp_kWh"]
    p_inv       = res["perdida_inv_kWh"]
    e_ref       = round(poa_bruta_anual * P_stc_kW, 0)
    e_ac        = res["E_ac_anual_kWh"]

    etapas_loss = ["Óptica/mismatch", "Temperatura celda", "Inversor"]
    vals_loss   = [p_optica, p_temp, p_inv]
    pcts_loss   = [round(v / e_ref * 100, 1) if e_ref > 0 else 0 for v in vals_loss]

    fig_loss = go.Figure(go.Bar(
        x=vals_loss,
        y=etapas_loss,
        orientation="h",
        marker_color=["#EF5350", "#FF7043", "#FFA726"],
        text=[f"{v:,.0f} kWh ({p}%)" for v, p in zip(vals_loss, pcts_loss)],
        textposition="outside",
    ))
    fig_loss.update_layout(
        xaxis_title="Pérdida (kWh/año)",
        height=260,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=160, r=160),
    )
    st.plotly_chart(fig_loss, use_container_width=True)

    # Tabla desglose
    with st.expander("📋 Ver tabla detallada de pérdidas IEC 61724"):
        df_loss = perdidas_desglosadas(res, poa_bruta_anual)
        if not df_loss.empty:
            st.dataframe(
                df_loss.style.format({
                    "kWh": "{:,.0f}",
                    "Pérdida (kWh)": "{:,.0f}",
                    "% de E_ref": "{:.2f}%",
                }).background_gradient(subset=["Pérdida (kWh)"], cmap="Reds", low=0, high=1),
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
    st.session_state["produccion_ok"]       = True
