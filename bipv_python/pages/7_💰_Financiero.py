"""Página 7 — Análisis financiero BIPV — Ley 1715 de 2014 (Colombia)."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from calculos.financiero import (
    calcular_beneficios_ley_1715,
    calcular_flujo_caja,
    calcular_metricas,
    comparativo_ley_1715,
)

st.set_page_config(page_title="Financiero — BIPV", page_icon="💰", layout="wide")
st.title("💰 Análisis Financiero — Ley 1715 de 2014")
st.caption(
    "Art. 11 Deducción renta · Art. 12 Exclusión IVA · Art. 14 Depreciación acelerada "
    "· TIR · VPN · Payback · LCOE"
)

# ── Prerequisitos ─────────────────────────────────────────────────────────────
prod_ok = st.session_state.get("produccion_ok", False)
e_ac    = st.session_state.get("E_ac_anual_kWh", 0.0)
p_stc   = st.session_state.get("P_stc_kW_sistema", 0.0)
n_pan   = st.session_state.get("N_paneles_final", 64)
ciudad  = st.session_state.get("tmy_ciudad", "Bogotá")

if prod_ok and e_ac > 0:
    st.success(
        f"✅ Producción cargada — **{e_ac:,.0f} kWh/año** | "
        f"Sistema: **{p_stc:.2f} kWp** ({n_pan} módulos) | Ciudad: **{ciudad}**"
    )
else:
    st.warning("⚠️ Primero ejecuta 📊 Producción para calcular la energía anual del sistema.")
    e_ac = st.number_input(
        "Ingresa la energía AC anual manualmente (kWh/año)",
        min_value=100.0, max_value=1e6, value=3391.0, step=100.0,
    )
    p_stc = st.number_input("Potencia instalada (kWp)", min_value=0.1, value=4.03, step=0.1)
    n_pan = st.number_input("Número de módulos", min_value=1, value=64, step=1)


# TRM disponible desde el inicio (se actualiza en Sección 2)
tipo_cambio = float(st.session_state.get("tipo_cambio", 3400.0))

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — CAPEX
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🏗️ 1. Inversión (CAPEX)")

col_cx1, col_cx2 = st.columns(2)

with col_cx1:
    st.markdown("**Costos del sistema**")
    costo_modulo_usd = st.number_input(
        "Costo módulos BIPV (USD/módulo)",
        min_value=10.0, max_value=500.0,
        value=65.0, step=5.0,
        help="ASP-ST1-T40 SolTech ~ USD 60–80 / módulo (precio mercado Colombia 2024)",
    )
    costo_inversor_usd_kw = st.number_input(
        "Costo inversor (USD/kWp)",
        min_value=50.0, max_value=400.0,
        value=120.0, step=10.0,
        help="Growatt MID15KTL3-X ~ USD 100–150/kWp en Colombia 2024",
    )
    costo_estructura_usd_kw = st.number_input(
        "Estructura, cableado, protecciones (USD/kWp)",
        min_value=50.0, max_value=500.0,
        value=200.0, step=25.0,
        help="BIPV de fachada requiere subestructura especializada. Típico: USD 150–300/kWp",
    )
    costo_instalacion_pct = st.number_input(
        "Ingeniería + instalación + puesta en marcha (%CAPEX equipos)",
        min_value=5.0, max_value=40.0,
        value=18.0, step=1.0,
        help="Para Colombia: 15–25% del costo de equipos",
    )
    imprevistos_pct = st.number_input(
        "Imprevistos y contingencia (%)",
        min_value=0.0, max_value=20.0,
        value=5.0, step=1.0,
    )

with col_cx2:
    # Cálculo automático de CAPEX
    capex_modulos     = n_pan * costo_modulo_usd
    capex_inversor    = p_stc * costo_inversor_usd_kw
    capex_estructura  = p_stc * costo_estructura_usd_kw
    capex_equipos     = capex_modulos + capex_inversor + capex_estructura
    capex_instalacion = capex_equipos * costo_instalacion_pct / 100
    capex_sub_total   = capex_equipos + capex_instalacion
    capex_imprev      = capex_sub_total * imprevistos_pct / 100
    capex_total       = capex_sub_total + capex_imprev
    fraccion_equipos  = capex_equipos / capex_total if capex_total > 0 else 0.65

    st.markdown("**Desglose CAPEX**")
    items_capex = {
        "Módulos BIPV":        capex_modulos,
        "Inversor":            capex_inversor,
        "Estructura/cables":   capex_estructura,
        "Ingeniería/instal.":  capex_instalacion,
        "Imprevistos":         capex_imprev,
    }
    df_capex = pd.DataFrame.from_dict(
        items_capex, orient="index", columns=["USD"]
    )
    df_capex["COP (M)"] = (df_capex["USD"] * tipo_cambio / 1e6).round(1)
    st.dataframe(df_capex.style.format({"USD": "{:,.0f}", "COP (M)": "{:.1f}"}),
                 use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("CAPEX total",    f"USD {capex_total:,.0f}",
              delta=f"$ {capex_total*tipo_cambio/1e6:.1f} M COP", delta_color="off")
    c2.metric("Costo por Wp",   f"USD {capex_total/p_stc/1000:.2f}/Wp" if p_stc > 0 else "—",
              delta=f"$ {capex_total*tipo_cambio/p_stc/1000:,.0f} COP/Wp" if p_stc > 0 else None,
              delta_color="off")
    c3.metric("Costo módulo",   f"USD {capex_total/n_pan:,.0f}/módulo" if n_pan > 0 else "—",
              delta=f"$ {capex_total*tipo_cambio/n_pan:,.0f} COP/módulo" if n_pan > 0 else None,
              delta_color="off")

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — TARIFA Y PARÁMETROS OPERATIVOS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚡ 2. Tarifa eléctrica y parámetros operativos")

col_t1, col_t2, col_t3 = st.columns(3)

with col_t1:
    tarifa_cop = st.number_input(
        "Tarifa electricidad (COP/kWh)",
        min_value=100.0, max_value=2000.0,
        value=650.0, step=25.0,
        help="Tarifa comercial/industrial Bogotá 2024: ~550–750 COP/kWh. "
             "Residencial estrato 4-6: ~600–850 COP/kWh",
    )
    tipo_cambio = st.number_input(
        "Tipo de cambio (COP/USD)",
        min_value=3000.0, max_value=6000.0,
        value=float(st.session_state.get("tipo_cambio", 3400.0)),
        step=50.0,
        help="TRM actual (jul 2026): ~3.400 COP/USD. Ajusta según la tasa del día.",
    )
    st.session_state["tipo_cambio"] = tipo_cambio

with col_t2:
    esc_tarifa = st.slider(
        "Escalación anual tarifa (%)",
        min_value=0.0, max_value=15.0, value=5.0, step=0.5,
        help="Colombia: inflación energética histórica ~5–8%/año. "
             "Escenario base: 5%.",
    )
    tasa_deg = st.slider(
        "Degradación módulos CdTe (%/año)",
        min_value=0.2, max_value=1.5, value=0.5, step=0.1,
        help="CdTe SolTech: 0.5%/año (mejor que c-Si ~0.7%). "
             "Fuente: Jordan & Kurtz 2013.",
    )

with col_t3:
    opex_pct = st.slider(
        "O&M anual (%CAPEX)",
        min_value=0.5, max_value=3.0, value=1.0, step=0.25,
        help="BIPV fachada: 0.5–1.5%/año. Incluye limpieza, revisión y seguros.",
    )
    tasa_desc = st.slider(
        "Tasa de descuento WACC (%)",
        min_value=5.0, max_value=20.0, value=10.0, step=0.5,
        help="WACC Colombia: 9–14% para proyectos de energía renovable. Base: 10%.",
    )
    n_anos = st.slider(
        "Horizonte de análisis (años)",
        min_value=10, max_value=30, value=25, step=5,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL DE CONVERSIÓN USD → COP (en tiempo real)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
with st.expander("💱 Conversor de cifras USD → COP (TRM del día)", expanded=True):
    st.caption(f"Usando TRM: **{tipo_cambio:,.0f} COP/USD** — ajusta la tasa en la sección anterior para actualizar.")

    col_cv1, col_cv2, col_cv3, col_cv4 = st.columns(4)
    col_cv1.metric("CAPEX bruto",
                   f"${capex_total*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {capex_total:,.0f}", delta_color="off")
    col_cv2.metric("Módulos BIPV",
                   f"${capex_modulos*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {capex_modulos:,.0f}", delta_color="off")
    col_cv3.metric("Inversor",
                   f"${capex_inversor*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {capex_inversor:,.0f}", delta_color="off")
    col_cv4.metric("Estructura + Instalación",
                   f"${(capex_estructura+capex_instalacion)*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {(capex_estructura+capex_instalacion):,.0f}", delta_color="off")

    st.markdown("---")
    col_cv5, col_cv6, col_cv7, col_cv8 = st.columns(4)
    ben_lv = calcular_beneficios_ley_1715(
        capex_usd       = capex_total,
        fraccion_equipo = capex_equipos / capex_total if capex_total > 0 else 0.65,
        tasa_renta      = 0.35,
        tipo_cambio     = tipo_cambio,
    )
    col_cv5.metric("Beneficios Ley 1715",
                   f"${ben_lv['total_usd']*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {ben_lv['total_usd']:,.0f}", delta_color="off")
    col_cv6.metric("CAPEX neto (con Ley 1715)",
                   f"${ben_lv['capex_neto_usd']*tipo_cambio/1e6:.2f} M COP",
                   delta=f"USD {ben_lv['capex_neto_usd']:,.0f}", delta_color="off")
    col_cv7.metric("Ahorro energía año 1",
                   f"${e_ac * (tarifa_cop/1e6):.2f} M COP/año",
                   delta=f"USD {e_ac * tarifa_cop / tipo_cambio:,.0f}/año", delta_color="off")
    col_cv8.metric("Tarifa referencia",
                   f"{tarifa_cop:,.0f} COP/kWh",
                   delta=f"USD {tarifa_cop/tipo_cambio:.4f}/kWh", delta_color="off")

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — BENEFICIOS LEY 1715
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📜 3. Beneficios Ley 1715 de 2014")

col_l1, col_l2 = st.columns([1, 1])

with col_l1:
    tasa_renta = st.number_input(
        "Tasa impuesto de renta corporativo (%)",
        min_value=15.0, max_value=40.0,
        value=35.0, step=1.0,
        help="Colombia 2024: tasa general corporativa 35% (Ley 2277 de 2022)",
    )
    st.markdown("""
    **Artículos aplicables:**
    - **Art. 11** — Deducción especial renta: 50% del CAPEX deducible de la base gravable
    - **Art. 12** — Exclusión IVA: no se paga IVA (19%) sobre equipos SRFNC calificados
    - **Art. 14** — Depreciación acelerada: hasta 5 años (vs 10 años estándar)

    > ⚠️ Requiere certificación UPME previa al inicio del proyecto.
    > Aplicable a personas jurídicas obligadas a llevar contabilidad.
    """)

with col_l2:
    ben = calcular_beneficios_ley_1715(
        capex_usd        = capex_total,
        fraccion_equipo  = fraccion_equipos,
        tasa_renta       = tasa_renta / 100,
        tipo_cambio      = tipo_cambio,
        tasa_descuento   = tasa_desc / 100,
    )

    b1, b2, b3, b4 = st.columns(2), st.columns(2), None, None
    bb1, bb2 = st.columns(2)
    bbb1, bbb2 = st.columns(2)

    bb1.metric("Art. 11 — Deducción renta",
               f"USD {ben['ahorro_renta_usd']:,.0f}",
               delta=f"$ {ben['ahorro_renta_usd']*tipo_cambio/1e6:.2f} M COP",
               delta_color="off",
               help="50% × CAPEX × tasa_renta")
    bb2.metric("Art. 12 — Ahorro IVA",
               f"USD {ben['ahorro_iva_usd']:,.0f}",
               delta=f"$ {ben['ahorro_iva_usd']*tipo_cambio/1e6:.2f} M COP",
               delta_color="off",
               help="19% × CAPEX_equipos")
    bbb1.metric("Art. 14 — Dep. acelerada",
                f"USD {ben['ahorro_dep_vpn_usd']:,.0f}",
                delta=f"$ {ben['ahorro_dep_vpn_usd']*tipo_cambio/1e6:.2f} M COP",
                delta_color="off",
                help="VPN del ahorro por diferencial de depreciación 5 vs 10 años")
    bbb2.metric("💚 Total beneficios",
                f"USD {ben['total_usd']:,.0f}",
                delta=f"$ {ben['total_usd']*tipo_cambio/1e6:.2f} M COP  ·  -{ben['pct_capex']:.1f}% CAPEX",
                delta_color="off")

    st.info(
        f"**CAPEX bruto:** USD {capex_total:,.0f}  ($ {capex_total*tipo_cambio/1e6:.2f} M COP) → "
        f"**CAPEX neto (con Ley 1715):** USD {ben['capex_neto_usd']:,.0f}  "
        f"($ {ben['capex_neto_usd']*tipo_cambio/1e6:.2f} M COP)  "
        f"— {ben['pct_capex']:.1f}% de reducción efectiva"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — ANÁLISIS FINANCIERO
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📈 4. Análisis financiero")

btn_fin = st.button(
    "📊 Calcular TIR, VPN, Payback y LCOE", type="primary", use_container_width=True
)

if btn_fin or st.session_state.get("financiero_ok"):

    if btn_fin:
        comp = comparativo_ley_1715(
            capex_usd         = capex_total,
            e_ac_kWh_anual    = e_ac,
            tarifa_cop_kWh    = tarifa_cop,
            tipo_cambio       = tipo_cambio,
            tasa_descuento    = tasa_desc / 100,
            tasa_escalacion   = esc_tarifa,
            tasa_degradacion  = tasa_deg,
            opex_pct          = opex_pct,
            n_anos            = n_anos,
            beneficios_1715   = ben,
        )
        st.session_state["comp_financiero"] = comp
        st.session_state["financiero_ok"]   = True
    else:
        comp = st.session_state.get("comp_financiero", {})
        if not comp:
            st.warning("Presiona el botón para calcular.")
            st.stop()

    m_sin = comp["sin"]["metricas"]
    m_con = comp["con"]["metricas"]

    # ── Tabla comparativa SIN / CON Ley 1715 ─────────────────────────────────
    st.subheader("⚖️ Comparativo sin / con Ley 1715")

    df_comp = pd.DataFrame({
        "Métrica": [
            "CAPEX efectivo",
            "CAPEX efectivo (COP)",
            "TIR (%)",
            "VPN a " + str(int(tasa_desc)) + "% (USD)",
            "VPN a " + str(int(tasa_desc)) + "% (COP)",
            "Payback simple (años)",
            "Payback descontado (años)",
            "LCOE (USD/kWh)",
            "LCOE (COP/kWh)",
        ],
        "Sin Ley 1715": [
            f"USD {capex_total:,.0f}",
            f"$ {capex_total*tipo_cambio/1e6:.2f} M",
            f"{m_sin['tir_pct']:.1f}%" if m_sin['tir_pct'] else "N/A",
            f"USD {m_sin['vpn_usd']:,.0f}",
            f"$ {m_sin['vpn_cop_millon']:.1f} M",
            f"{m_sin['payback_simple']:.1f} años" if m_sin['payback_simple'] else "> horizonte",
            f"{m_sin['payback_desc']:.1f} años" if m_sin['payback_desc'] else "> horizonte",
            f"{m_sin['lcoe_usd_kWh']:.4f}",
            f"{m_sin['lcoe_cop_kWh']:.0f}",
        ],
        "Con Ley 1715": [
            f"USD {ben['capex_neto_usd']:,.0f}",
            f"$ {ben['capex_neto_usd']*tipo_cambio/1e6:.2f} M",
            f"{m_con['tir_pct']:.1f}%" if m_con['tir_pct'] else "N/A",
            f"USD {m_con['vpn_usd']:,.0f}",
            f"$ {m_con['vpn_cop_millon']:.1f} M",
            f"{m_con['payback_simple']:.1f} años" if m_con['payback_simple'] else "> horizonte",
            f"{m_con['payback_desc']:.1f} años" if m_con['payback_desc'] else "> horizonte",
            f"{m_con['lcoe_usd_kWh']:.4f}",
            f"{m_con['lcoe_cop_kWh']:.0f}",
        ],
    })

    def _color_comp(row):
        """Verde para Con Ley 1715 si mejora el indicador."""
        return ["", "", "background-color: #E8F5E9; font-weight: bold"]

    st.dataframe(df_comp.style.apply(_color_comp, axis=1), use_container_width=True, hide_index=True)

    # ── Métricas clave ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    tir_delta = ((m_con['tir_pct'] or 0) - (m_sin['tir_pct'] or 0))
    c1.metric("TIR con Ley 1715",     f"{m_con['tir_pct']:.1f}%" if m_con['tir_pct'] else "—",
              delta=f"+{tir_delta:.1f}pp vs sin Ley 1715")
    c2.metric("VPN con Ley 1715",
              f"USD {m_con['vpn_usd']:,.0f}  |  $ {m_con['vpn_usd']*tipo_cambio/1e6:.1f} M COP",
              delta="✅ Positivo" if m_con['vpn_positivo'] else "❌ Negativo",
              delta_color="normal" if m_con['vpn_positivo'] else "inverse")
    c3.metric("Payback con Ley 1715", f"{m_con['payback_simple']:.1f} años" if m_con['payback_simple'] else "—")
    c4.metric("LCOE",                 f"{m_con['lcoe_cop_kWh']:.0f} COP/kWh  ·  USD {m_con['lcoe_usd_kWh']:.4f}",
              delta=f"Tarifa: {tarifa_cop:.0f} COP/kWh",
              delta_color="off")

    # ── Gráfica flujo de caja acumulado ──────────────────────────────────────
    st.subheader("💵 Flujo de caja acumulado (USD)")

    fc_sin = comp["sin"]["flujos"]
    fc_con = comp["con"]["flujos"]
    anos   = [f["año"] for f in fc_sin]

    fig_fc = go.Figure()
    fig_fc.add_trace(go.Scatter(
        x=anos, y=[f["flujo_acum_usd"] for f in fc_sin],
        name="Sin Ley 1715",
        line=dict(color="#EF5350", width=2, dash="dash"),
        mode="lines",
    ))
    fig_fc.add_trace(go.Scatter(
        x=anos, y=[f["flujo_acum_usd"] for f in fc_con],
        name="Con Ley 1715",
        line=dict(color="#2E7D32", width=2.5),
        fill="tonexty",
        fillcolor="rgba(46,125,50,0.08)",
        mode="lines",
    ))
    fig_fc.add_hline(y=0, line_color="gray", line_dash="dot", line_width=1)

    # Marcar payback
    if m_con.get("payback_simple"):
        fig_fc.add_vline(
            x=m_con["payback_simple"],
            line_color="#2E7D32", line_dash="dot",
            annotation_text=f"Payback: {m_con['payback_simple']:.1f} años",
            annotation_position="top right",
        )
    if m_sin.get("payback_simple"):
        fig_fc.add_vline(
            x=m_sin["payback_simple"],
            line_color="#EF5350", line_dash="dot",
            annotation_text=f"Payback sin: {m_sin['payback_simple']:.1f} años",
            annotation_position="bottom right",
        )

    fig_fc.update_layout(
        xaxis_title="Año",
        yaxis_title="Flujo acumulado (USD)",
        height=420,
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
    )
    st.plotly_chart(fig_fc, use_container_width=True)

    # ── Gráfica ingresos anuales vs OPEX ──────────────────────────────────────
    with st.expander("📊 Ver ingresos anuales vs O&M"):
        fig_ing = go.Figure()
        fig_ing.add_trace(go.Bar(
            name="Ingreso energía",
            x=anos[1:], y=[f["ingreso_energia_usd"] for f in fc_con[1:]],
            marker_color="#66BB6A",
        ))
        fig_ing.add_trace(go.Bar(
            name="O&M (OPEX)",
            x=anos[1:], y=[-f["opex_usd"] for f in fc_con[1:]],
            marker_color="#EF9A9A",
        ))
        fig_ing.update_layout(
            barmode="relative",
            xaxis_title="Año",
            yaxis_title="USD",
            height=340,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_ing, use_container_width=True)

    # ── Tabla de beneficios Ley 1715 ─────────────────────────────────────────
    with st.expander("📜 Detalle Ley 1715 — base de cálculo"):
        st.markdown(f"""
| Beneficio | Base | Cálculo | USD | COP |
|---|---|---|---|---|
| **Art. 11** Deducción renta | 50% × CAPEX × tasa_renta | 0.50 × {capex_total:,.0f} × {tasa_renta/100:.2f} | **{ben['ahorro_renta_usd']:,.0f}** | **$ {ben['ahorro_renta_usd']*tipo_cambio/1e6:.2f} M** |
| **Art. 12** Exclusión IVA | 19% × CAPEX_equipos | 0.19 × {capex_total*fraccion_equipos:,.0f} | **{ben['ahorro_iva_usd']:,.0f}** | **$ {ben['ahorro_iva_usd']*tipo_cambio/1e6:.2f} M** |
| **Art. 14** Dep. acelerada | VPN diferencial 5yr vs 10yr | — | **{ben['ahorro_dep_vpn_usd']:,.0f}** | **$ {ben['ahorro_dep_vpn_usd']*tipo_cambio/1e6:.2f} M** |
| **Total Ley 1715** | — | — | **{ben['total_usd']:,.0f}** | **$ {ben['total_usd']*tipo_cambio/1e6:.2f} M** |
| **CAPEX neto** | CAPEX − Ley 1715 | {capex_total:,.0f} − {ben['total_usd']:,.0f} | **{ben['capex_neto_usd']:,.0f}** | **$ {ben['capex_neto_usd']*tipo_cambio/1e6:.2f} M** |
        """)
        st.caption(
            "⚠️ Los beneficios Art. 11 y 14 requieren declaración de renta con utilidades suficientes. "
            "Art. 12 aplica desde la compra de equipos. Requiere certificación UPME previa."
        )

    # ── Tabla flujo de caja completo ─────────────────────────────────────────
    with st.expander("📋 Ver tabla de flujo de caja anual"):
        df_fc = pd.DataFrame(fc_con)
        df_fc.columns = ["Año", "Producción (kWh)", "Ingreso energía (USD)",
                          "O&M (USD)", "Flujo (USD)", "Flujo acum. (USD)"]
        df_fc["Ingreso (M COP)"]    = (df_fc["Ingreso energía (USD)"] * tipo_cambio / 1e6).round(3)
        df_fc["Flujo acum. (M COP)"] = (df_fc["Flujo acum. (USD)"] * tipo_cambio / 1e6).round(3)
        st.dataframe(
            df_fc.style.format({
                "Producción (kWh)":      "{:,.0f}",
                "Ingreso energía (USD)":  "{:,.0f}",
                "O&M (USD)":             "{:,.0f}",
                "Flujo (USD)":           "{:+,.0f}",
                "Flujo acum. (USD)":     "{:+,.0f}",
                "Ingreso (M COP)":       "{:.3f}",
                "Flujo acum. (M COP)":   "{:+.3f}",
            }).background_gradient(subset=["Flujo acum. (USD)"], cmap="RdYlGn"),
            use_container_width=True,
        )

    # ── Mensaje final ─────────────────────────────────────────────────────────
    color_vpn = "✅" if m_con["vpn_positivo"] else "⚠️"
    st.success(
        f"{color_vpn} **{ciudad}** — {n_pan} módulos ASP-ST1-T40 | "
        f"CAPEX neto: **USD {ben['capex_neto_usd']:,.0f}** ($ {ben['capex_neto_usd']*tipo_cambio/1e6:.2f} M COP) | "
        f"TIR: **{m_con['tir_pct']:.1f}%** | "
        f"VPN: **USD {m_con['vpn_usd']:,.0f}** ($ {m_con['vpn_usd']*tipo_cambio/1e6:.1f} M COP) | "
        f"Payback: **{m_con['payback_simple']:.1f} años** | "
        f"LCOE: **{m_con['lcoe_cop_kWh']:.0f} COP/kWh** "
        f"({'<' if m_con['lcoe_cop_kWh'] < tarifa_cop else '>'} tarifa {tarifa_cop:.0f} COP/kWh)"
    )

    # Guardar para Reporte
    st.session_state["capex_total_usd"]     = capex_total
    st.session_state["ben_1715"]            = ben
    st.session_state["metricas_financiero"] = m_con
    st.session_state["tarifa_cop_kWh"]      = tarifa_cop
    st.session_state["financiero_ok"]       = True
