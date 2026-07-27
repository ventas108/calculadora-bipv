"""Página 3 — Motor I-V (SDM De Soto 2006)."""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from calculos.modelo_iv import resolver_curva_iv, validar_sdm_vs_ficha
from calculos.temperatura import temperatura_celda_noct
from datos.tecnologias_bipv import ASP_ST1_T40, MODULOS_BIPV

st.set_page_config(page_title="Motor IV — BIPV", page_icon="🔬", layout="wide")
st.title("🔬 Motor I-V — Modelo De Soto 2006")
st.caption("Equivalente Python de SimuladorIV_CdTe_v2 + Mod_ModeloDiodo (VBA auditado)")

panel_nombre = st.selectbox("Panel", list(MODULOS_BIPV.keys()),
                             index=list(MODULOS_BIPV.keys()).index("ASP-ST1-T40"))
panel = MODULOS_BIPV[panel_nombre]

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Condiciones de simulación")
    G     = st.slider("Irradiancia G (W/m²)", 50, 1200, 1000, step=25)
    T_amb = st.slider("T_ambiente (°C)", 0, 40, 20)
    NOCT  = st.slider("NOCT (°C)", 35, 55, 45)

    T_cel = float(temperatura_celda_noct(G, T_amb, NOCT))
    st.metric("T_celda calculada", f"{T_cel:.1f} °C")

    st.markdown("---")
    st.subheader("Parámetros SDM @ STC")
    st.code(
        f"Iph = {panel['I_L_ref']} A\n"
        f"I0  = {panel['I_o_ref']:.2e} A\n"
        f"Rs  = {panel['R_s']} Ω\n"
        f"Rsh = {panel['R_sh_ref']} Ω (base)\n"
        f"NsA = {panel['a_ref']} (n×Ns)"
    )

with col2:
    res = resolver_curva_iv(G, T_cel, panel, n_puntos=150)

    if res["V"] is not None:
        fig = go.Figure()
        V_arr = np.array(res["V"])
        I_arr = np.array(res["I"])
        P_arr = V_arr * I_arr

        fig.add_trace(go.Scatter(x=V_arr, y=I_arr, name="I-V",
                                  line=dict(color="#1F497D", width=2.5)))
        fig.add_trace(go.Scatter(x=V_arr, y=P_arr, name="P-V",
                                  yaxis="y2", line=dict(color="#E07B00", width=2,
                                                         dash="dash")))
        fig.add_vline(x=res["Vmp"], line_dash="dot", line_color="green",
                       annotation_text=f"Vmp={res['Vmp']:.1f}V")
        fig.add_vline(x=res["Voc"], line_dash="dot", line_color="red",
                       annotation_text=f"Voc={res['Voc']:.1f}V")

        fig.update_layout(
            title=f"{panel_nombre} — G={G} W/m², T_cel={T_cel:.1f}°C",
            xaxis_title="Tensión (V)",
            yaxis_title="Corriente (A)",
            yaxis2=dict(title="Potencia (W)", overlaying="y", side="right"),
            height=400, legend=dict(x=0.02, y=0.98),
        )
        st.plotly_chart(fig, use_container_width=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Voc",  f"{res['Voc']:.2f} V")
    m2.metric("Isc",  f"{res['Isc']:.4f} A")
    m3.metric("Vmp",  f"{res['Vmp']:.2f} V")
    m4.metric("Pmax", f"{res['Pmax']:.2f} W")
    m5.metric("FF",   f"{res['FF']*100:.2f} %")

st.markdown("---")
st.subheader("✅ Validación SDM vs Ficha Técnica")
if st.button("Ejecutar validación (G=1000 W/m², T=25°C)"):
    val = validar_sdm_vs_ficha(panel)
    for param, datos in val.items():
        if param == "validacion_ok":
            continue
        icono = "✅" if datos["ok"] else "❌"
        st.write(
            f"{icono} **{param}**: calculado={datos['calculado']} | "
            f"ficha={datos['referencia']} | error={datos['error_pct']}%"
        )
    if val["validacion_ok"]:
        st.success("✅ SDM validado — error < 5% en todos los parámetros")
    else:
        st.error("❌ Revisar calibración SDM")

st.markdown("---")
st.subheader("📈 Curva FF vs Irradiancia (validación VBA)")
if st.button("Generar curva FF vs G (T=25°C isotérmico)"):
    Gs_plot  = list(range(50, 1050, 25))
    FFs_plot = [resolver_curva_iv(G, 25.0, panel, n_puntos=0)["FF"] * 100 for G in Gs_plot]
    fig2 = go.Figure(go.Scatter(x=Gs_plot, y=FFs_plot,
                                 mode="lines+markers", line=dict(color="#1F497D")))
    # Puntos de referencia del VBA
    vba_G  = [100, 200, 400, 600, 800, 1000]
    vba_FF = [69.75, 76.28, 74.51, 72.87, 71.55, 64.92]
    fig2.add_trace(go.Scatter(x=vba_G, y=vba_FF, mode="markers",
                               name="VBA (referencia)",
                               marker=dict(color="red", size=10, symbol="x")))
    fig2.update_layout(title="FF vs G — De Soto 2006 + Rsh exp CdTe",
                        xaxis_title="G (W/m²)", yaxis_title="FF (%)", height=350)
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Los puntos rojos ✕ son los valores calculados por el VBA. "
               "Las líneas azules son el resultado de Python.")
