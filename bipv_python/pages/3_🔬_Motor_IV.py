"""Página 3 — Motor I-V (SDM De Soto 2006).

Auto-activación: si el panel seleccionado en Dimensionamiento tiene ficha
suficiente (Voc, Isc, Vmp, Imp, N_s/NsA), el motor carga y ejecuta
automáticamente sin que el usuario tenga que hacer nada.
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go

from calculos.modelo_iv import (
    resolver_curva_iv,
    validar_sdm_vs_ficha,
    tiene_sdm_completo,
    estimar_sdm_desde_ficha,
)
from calculos.temperatura import temperatura_celda_noct
from datos.tecnologias_bipv import ASP_ST1_T40, MODULOS_BIPV

st.set_page_config(page_title="Motor IV — BIPV", page_icon="🔬", layout="wide")
st.title("🔬 Motor I-V — Modelo De Soto 2006")
st.caption("Equivalente Python de SimuladorIV_CdTe_v2 + Mod_ModeloDiodo (VBA auditado)")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. DETECCIÓN AUTOMÁTICA DEL PANEL DESDE DIMENSIONAMIENTO
# ═══════════════════════════════════════════════════════════════════════════════

_panel_ss       = st.session_state.get("panel_dict")
_panel_nom_ss   = st.session_state.get("panel_nombre_dim", "")

_modo_auto      = False   # True si se usa el panel del Dimensionamiento
_panel_activo   = None    # dict que se usará en el motor
_estimado       = False   # True si se usaron parámetros estimados
_metodo_est     = ""

if _panel_ss and _panel_nom_ss:
    if tiene_sdm_completo(_panel_ss):
        # ── Ficha SDM calibrada (ej. ASP-ST1-T40 de MODULOS_BIPV) ─────────────
        _modo_auto   = True
        _panel_activo = _panel_ss
        _estimado    = False
        st.success(
            f"⚡ **Auto-activado** — Panel detectado en Dimensionamiento: "
            f"**{_panel_nom_ss}** · parámetros SDM calibrados."
        )
    else:
        # ── Ficha básica (catálogo Excel) → estimar SDM ────────────────────────
        _sdm_est = estimar_sdm_desde_ficha(_panel_ss)
        if _sdm_est is not None:
            _modo_auto    = True
            _panel_activo = _sdm_est
            _estimado     = True
            _metodo_est   = _sdm_est.get("_metodo", "estimado")
            st.warning(
                f"🟡 **Auto-activado con estimación** — Panel: **{_panel_nom_ss}** "
                f"(catálogo Excel). Parámetros SDM estimados por **{_metodo_est}** "
                f"desde ficha técnica. Resultados orientativos — valida con datos calibrados."
            )
        else:
            st.info(
                f"ℹ️ Panel **{_panel_nom_ss}** no tiene datos suficientes para el Motor IV "
                f"(faltan Voc, Isc, Vmp o Imp). Selecciona manualmente un panel con ficha completa."
            )

# ── Selector manual como alternativa / fallback ────────────────────────────────
st.markdown("---")
with st.expander(
    "🔧 Seleccionar panel manualmente" if _modo_auto else "🔬 Seleccionar panel",
    expanded=not _modo_auto,
):
    _panel_manual_nom = st.selectbox(
        "Panel del catálogo interno (SDM calibrado)",
        list(MODULOS_BIPV.keys()),
        index=list(MODULOS_BIPV.keys()).index("ASP-ST1-T40"),
        key="motor_iv_panel_manual",
    )
    if st.button("▶️ Usar este panel", key="btn_panel_manual"):
        _panel_activo = MODULOS_BIPV[_panel_manual_nom]
        _modo_auto    = True
        _estimado     = False
        _panel_nom_ss = _panel_manual_nom
        st.success(f"✅ Panel manual cargado: **{_panel_manual_nom}**")

# Si aún no hay panel activo, usar el default
if _panel_activo is None:
    _panel_activo = ASP_ST1_T40
    _panel_nom_ss = "ASP-ST1-T40"
    _estimado     = False

# ═══════════════════════════════════════════════════════════════════════════════
# 2. CONDICIONES DE SIMULACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("⚙️ Condiciones de simulación")

col1, col2 = st.columns([1, 2])

with col1:
    G     = st.slider("Irradiancia G (W/m²)", 50, 1200, 1000, step=25, key="iv_G")
    T_amb = st.slider("T_ambiente (°C)", 0, 40, 20, key="iv_Tamb")
    NOCT  = st.slider(
        "NOCT (°C)",
        35, 55,
        int(_panel_activo.get("NOCT") or 45),
        key="iv_NOCT",
    )
    T_cel = float(temperatura_celda_noct(G, T_amb, NOCT))
    st.metric("T_celda calculada", f"{T_cel:.1f} °C")

    st.markdown("---")
    st.subheader("Parámetros SDM @ STC")
    if _estimado:
        st.caption("⚠️ Estimados — no calibrados")
    _prec = 3 if _estimado else 2
    st.code(
        f"Iph  = {_panel_activo['I_L_ref']:.{_prec}f} A\n"
        f"I0   = {_panel_activo['I_o_ref']:.2e} A\n"
        f"Rs   = {_panel_activo['R_s']:.{_prec}f} Ω\n"
        f"Rsh  = {_panel_activo['R_sh_ref']:.1f} Ω\n"
        f"nNsVt= {_panel_activo['a_ref']:.4f} V\n"
        f"Tec  = {_panel_activo.get('tecnologia','—')}"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 3. CURVA I-V (AUTO-RUN)
# ═══════════════════════════════════════════════════════════════════════════════

with col2:
    res = resolver_curva_iv(G, T_cel, _panel_activo, n_puntos=150)

    if res["V"] is not None:
        fig = go.Figure()
        V_arr = np.array(res["V"])
        I_arr = np.array(res["I"])
        P_arr = V_arr * I_arr

        fig.add_trace(go.Scatter(
            x=V_arr, y=I_arr, name="I-V",
            line=dict(color="#1F497D", width=2.5),
        ))
        fig.add_trace(go.Scatter(
            x=V_arr, y=P_arr, name="P-V",
            yaxis="y2", line=dict(color="#E07B00", width=2, dash="dash"),
        ))
        fig.add_vline(x=res["Vmp"], line_dash="dot", line_color="green",
                      annotation_text=f"Vmp={res['Vmp']:.1f}V")
        fig.add_vline(x=res["Voc"], line_dash="dot", line_color="red",
                      annotation_text=f"Voc={res['Voc']:.1f}V")
        fig.update_layout(
            title=(
                f"{_panel_nom_ss} — G={G} W/m², T_cel={T_cel:.1f}°C"
                + (" (estimado)" if _estimado else "")
            ),
            xaxis_title="Tensión (V)",
            yaxis_title="Corriente (A)",
            yaxis2=dict(title="Potencia (W)", overlaying="y", side="right"),
            height=400,
            legend=dict(x=0.02, y=0.98),
        )
        st.plotly_chart(fig, use_container_width=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Voc",  f"{res['Voc']:.2f} V")
    m2.metric("Isc",  f"{res['Isc']:.4f} A")
    m3.metric("Vmp",  f"{res['Vmp']:.2f} V")
    m4.metric("Pmax", f"{res['Pmax']:.2f} W")
    m5.metric("FF",   f"{res['FF']*100:.2f} %")

    # Comparación vs ficha cuando hay datos de referencia
    if _panel_activo.get("Pmax_stc") and _panel_activo.get("Voc_stc"):
        _err_p = abs(res["Pmax"] - _panel_activo["Pmax_stc"]) / _panel_activo["Pmax_stc"] * 100
        _err_v = abs(res["Voc"]  - _panel_activo["Voc_stc"])  / _panel_activo["Voc_stc"]  * 100
        _icono = "✅" if max(_err_p, _err_v) < 5 else "⚠️"
        st.caption(
            f"{_icono} vs ficha STC — "
            f"Pmax: {res['Pmax']:.1f} W vs {_panel_activo['Pmax_stc']:.1f} W "
            f"(err {_err_p:.1f}%) | "
            f"Voc: {res['Voc']:.1f} V vs {_panel_activo['Voc_stc']:.1f} V "
            f"(err {_err_v:.1f}%)"
        )

# ═══════════════════════════════════════════════════════════════════════════════
# 4. VALIDACIÓN FORMAL (solo paneles con SDM calibrado)
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("✅ Validación SDM vs Ficha Técnica")

if _estimado:
    st.info(
        "ℹ️ La validación formal requiere parámetros SDM calibrados. "
        "Este panel usa estimación — los errores pueden superar el 5 %. "
        "Para validar exactamente, agrega los parámetros calibrados al catálogo Excel."
    )
else:
    if st.button("Ejecutar validación (G=1000 W/m², T=25°C)", key="btn_validar"):
        val = validar_sdm_vs_ficha(_panel_activo)
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

# ═══════════════════════════════════════════════════════════════════════════════
# 5. CURVA FF vs IRRADIANCIA
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("📈 Curva FF vs Irradiancia (validación VBA)")
if st.button("Generar curva FF vs G (T=25°C isotérmico)", key="btn_ff_g"):
    Gs_plot  = list(range(50, 1050, 25))
    FFs_plot = [
        resolver_curva_iv(G_i, 25.0, _panel_activo, n_puntos=0)["FF"] * 100
        for G_i in Gs_plot
    ]
    fig2 = go.Figure(go.Scatter(
        x=Gs_plot, y=FFs_plot,
        mode="lines+markers", line=dict(color="#1F497D"),
        name=_panel_nom_ss,
    ))
    if not _estimado:
        # Puntos de referencia del VBA (solo válidos para ASP-ST1-T40 CdTe)
        vba_G  = [100, 200, 400, 600, 800, 1000]
        vba_FF = [69.75, 76.28, 74.51, 72.87, 71.55, 64.92]
        fig2.add_trace(go.Scatter(
            x=vba_G, y=vba_FF, mode="markers",
            name="VBA (referencia CdTe)",
            marker=dict(color="red", size=10, symbol="x"),
        ))
    fig2.update_layout(
        title="FF vs G — De Soto 2006" + (" (estimado)" if _estimado else " + Rsh exp CdTe"),
        xaxis_title="G (W/m²)", yaxis_title="FF (%)", height=350,
    )
    st.plotly_chart(fig2, use_container_width=True)
    if not _estimado:
        st.caption(
            "Los puntos rojos ✕ son los valores del VBA. "
            "Las líneas azules son el resultado de Python."
        )
