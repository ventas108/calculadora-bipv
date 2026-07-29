"""
Página 5b — Motor Óptico BIPV
Cascada de correcciones reales: IAM · Soiling · Modelo Térmico Confinado
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from calculos.motor_optico import (
    cascada_optica,
    B0_POR_VIDRIO,
    K_BIPV_POR_MONTAJE,
    SOILING_COLOMBIA,
)

st.set_page_config(page_title="Motor Óptico — BIPV", page_icon="🔆", layout="wide")
st.title("🔆 Motor Óptico BIPV")
st.caption(
    "Reflexión geométrica ASHRAE (IAM) · Suciedad estacional Colombia · "
    "Temperatura de celda confinada · Corrección por transparencia del vidrio"
)

# ── Prerequisitos ─────────────────────────────────────────────────────────────
if not st.session_state.get("recurso_solar_ok"):
    st.warning(
        "⚠️ Primero ejecuta ☀️ **Recurso Solar** para obtener el TMY y la POA del sitio."
    )
    st.stop()

tmy_df  = st.session_state["tmy_df"]
poa_df  = st.session_state["poa_df"]
poa_anual_bruta = st.session_state.get("poa_anual_kWh_m2", 0.0)
tilt    = st.session_state.get("tilt_fachada", 90)
azimuth = st.session_state.get("azimuth_fachada", 0)
orient_lbl = st.session_state.get("orientacion_label", "—")
ciudad  = st.session_state.get("tmy_ciudad", "—")
mismatch_ok = st.session_state.get("mismatch_ok", False)
factor_sombra = st.session_state.get("factor_sombra_anual", None)

st.info(
    f"📍 **{ciudad}** · Fachada **{orient_lbl} / {tilt}°** · "
    f"POA bruta: **{poa_anual_bruta:,.0f} kWh/m²/año**"
)

if mismatch_ok and factor_sombra is not None:
    st.success(
        f"✅ Mismatch disponible — factor de sombra: **{factor_sombra*100:.1f}%** "
        "(ya descontado en POA base)"
    )

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — CONFIGURACIÓN DEL VIDRIO Y MONTAJE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚙️ 1. Parámetros del vidrio y montaje BIPV")

with st.expander("ℹ️ Guía de parámetros", expanded=False):
    st.markdown("""
    | Parámetro | Significado físico | Valor típico |
    |-----------|-------------------|--------------|
    | **b₀ ASHRAE** | Reflexión del vidrio a ángulos oblicuos. Mayor b₀ = más pérdida por IAM en fachadas verticales | 0.05 vidrio estándar · 0.10 BIPV semi-trans |
    | **Transparencia τ** | Fracción de área sin semiconductor (luz que pasa sin generar energía) | 0.10-0.60 según diseño |
    | **k_BIPV** | Factor de confinamiento térmico. Mayor k = celda más caliente = menos eficiencia | 1.0 ventilado · 1.3 fachada · 1.5 sellado |
    | **NOCT** | Temperatura de operación nominal en condiciones estándar (G=800, T=20°C, v=1 m/s) | 45°C estándar · 50°C BIPV sin ventilar |
    | **γ (coef. temp.)** | Caída de eficiencia por grado sobre 25°C. Negativo siempre | −0.45 %/°C Si · −0.25 %/°C CdTe |
    """)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Óptica del vidrio**")
    vidrio_sel = st.selectbox(
        "Tipo de vidrio",
        options=list(B0_POR_VIDRIO.keys()),
        index=0,
        key="mo_vidrio_sel",
    )
    if vidrio_sel == "Personalizado":
        b0 = st.number_input(
            "b₀ ASHRAE personalizado",
            min_value=0.01, max_value=0.25, value=0.05, step=0.01,
            format="%.3f", key="mo_b0_custom",
        )
    else:
        b0 = B0_POR_VIDRIO[vidrio_sel]
        st.metric("b₀ ASHRAE seleccionado", f"{b0:.3f}")

    transparencia = st.slider(
        "Transparencia τ del vidrio (%)",
        min_value=0, max_value=70, value=40, step=5,
        key="mo_transparencia",
        help="Porcentaje de área transparente (sin celda activa).",
    ) / 100.0

with col2:
    st.markdown("**Montaje y temperatura**")
    montaje_sel = st.selectbox(
        "Tipo de montaje",
        options=list(K_BIPV_POR_MONTAJE.keys()),
        index=1,
        key="mo_montaje",
    )
    k_bipv = K_BIPV_POR_MONTAJE[montaje_sel]
    st.metric("k_BIPV", f"{k_bipv:.1f}")

    noct = st.number_input(
        "NOCT (°C)",
        min_value=35.0, max_value=65.0, value=50.0, step=1.0,
        key="mo_noct",
        help="Temperatura nominal de operación. Usa 45°C para paneles estándar, 50°C para BIPV.",
    )

with col3:
    st.markdown("**Coeficiente térmico**")
    coef_pct = st.number_input(
        "γ — Coef. temperatura (%/°C)",
        min_value=-0.70, max_value=-0.10, value=-0.45, step=0.01,
        format="%.2f",
        key="mo_coef_temp",
        help="Negativo siempre. Silicio cristalino ≈ -0.45, CdTe ≈ -0.25.",
    )
    coef_temp = coef_pct / 100.0  # convertir a decimal/°C
    st.metric("γ (decimal/°C)", f"{coef_temp:.4f}")

    st.markdown("**Soiling**")
    usar_soiling_custom = st.checkbox(
        "Usar factores de soiling personalizados",
        value=False, key="mo_soiling_custom",
    )

# Soiling config
if usar_soiling_custom:
    st.markdown("##### Factores de soiling mensual (0-15 %)")
    meses_es = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    soil_vals = []
    cols_soil = st.columns(6)
    for i, mes in enumerate(meses_es):
        with cols_soil[i % 6]:
            v = st.number_input(
                mes, min_value=0.0, max_value=15.0,
                value=round(SOILING_COLOMBIA.get(i+1, 0.04)*100, 1),
                step=0.5, format="%.1f", key=f"mo_soil_{i}",
            )
            soil_vals.append(v / 100.0)
    soiling_config = {i+1: soil_vals[i] for i in range(12)}
else:
    soiling_config = None

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — CÁLCULO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
run_btn = st.button(
    "🚀 Calcular cascada óptica",
    type="primary",
    use_container_width=True,
    key="mo_run",
)

if run_btn:
    with st.spinner("Aplicando cascada IAM → Soiling → Térmico (8 760 horas)…"):
        try:
            result_df, summary = cascada_optica(
                tmy_df=tmy_df,
                poa_df=poa_df,
                b0=b0,
                noct=noct,
                coef_temp=coef_temp,
                k_bipv=k_bipv,
                soiling_config=soiling_config,
            )
            # ── Guardar en session_state ──────────────────────────────────────
            # poa_efectiva_df tiene la misma estructura que poa_df
            # con poa_global = POA después de las 3 correcciones óptico-térmicas
            poa_ef_df = poa_df.copy()
            poa_ef_df["poa_global"] = result_df["poa_efectiva"].values

            st.session_state["motor_optico_ok"]             = True
            st.session_state["motor_optico_result_df"]      = result_df
            st.session_state["motor_optico_summary"]        = summary
            st.session_state["poa_efectiva_df"]             = poa_ef_df
            st.session_state["poa_efectiva_anual_kWh_m2"]  = summary["poa_efectiva_anual_kWh_m2"]
            st.session_state["motor_optico_b0"]             = b0
            st.session_state["motor_optico_tau"]            = transparencia
            st.session_state["motor_optico_k_bipv"]         = k_bipv
            st.session_state["motor_optico_noct"]           = noct
            st.session_state["motor_optico_coef_temp"]      = coef_temp

            st.success(
                f"✅ Cascada calculada. "
                f"POA efectiva: **{summary['poa_efectiva_anual_kWh_m2']:,.0f} kWh/m²/año** "
                f"(factor global: **{summary['factor_global']*100:.1f}%** de la POA bruta)"
            )
        except Exception as e:
            st.error(f"❌ Error en el cálculo: {e}")
            st.exception(e)
            st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — RESULTADOS (solo si se calculó)
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.get("motor_optico_ok"):
    st.info("ℹ️ Configura los parámetros arriba y haz clic en **Calcular cascada óptica**.")
    st.stop()

summary = st.session_state["motor_optico_summary"]
result_df = st.session_state["motor_optico_result_df"]

st.markdown("---")
st.subheader("📊 2. Resultados de la cascada óptico-térmica")

# ── 2A. Métricas de pérdidas ─────────────────────────────────────────────────
cm1, cm2, cm3, cm4, cm5 = st.columns(5)
cm1.metric(
    "POA bruta",
    f"{summary['poa_bruta_anual_kWh_m2']:,.0f} kWh/m²/año",
    help="Irradiancia plano de array sin correcciones.",
)
cm2.metric(
    "Pérdida IAM (reflexión)",
    f"−{summary['perdida_iam_kWh_m2']:,.0f} kWh/m²/año",
    f"−{summary['perdida_iam_kWh_m2']/summary['poa_bruta_anual_kWh_m2']*100:.1f}%",
    delta_color="inverse",
    help="Energía perdida por reflexión geométrica del vidrio según ángulo de incidencia.",
)
cm3.metric(
    "Pérdida soiling",
    f"−{summary['perdida_soil_kWh_m2']:,.0f} kWh/m²/año",
    f"−{summary['perdida_soil_kWh_m2']/summary['poa_bruta_anual_kWh_m2']*100:.1f}%",
    delta_color="inverse",
    help="Pérdida por suciedad estacional (polvo, smog). Incluye autolavado por lluvia.",
)
cm4.metric(
    "Pérdida térmica",
    f"−{summary['perdida_term_kWh_m2']:,.0f} kWh/m²/año",
    f"−{summary['perdida_term_kWh_m2']/summary['poa_bruta_anual_kWh_m2']*100:.1f}%",
    delta_color="inverse",
    help=f"Caída de eficiencia por temperatura de celda > 25°C (k_BIPV={summary['k_bipv']}).",
)
cm5.metric(
    "POA efectiva neta",
    f"{summary['poa_efectiva_anual_kWh_m2']:,.0f} kWh/m²/año",
    f"{summary['factor_global']*100:.1f}% de la bruta",
    delta_color="normal",
    help="Irradiancia efectiva aprovechable después de las 3 correcciones.",
)

# ── 2B. Gráfica Waterfall ─────────────────────────────────────────────────────
st.markdown("#### 2.1. Cascada de pérdidas (kWh/m²/año)")

bruta = summary["poa_bruta_anual_kWh_m2"]
p_iam  = summary["perdida_iam_kWh_m2"]
p_soil = summary["perdida_soil_kWh_m2"]
p_term = summary["perdida_term_kWh_m2"]
efect  = summary["poa_efectiva_anual_kWh_m2"]

fig_wf = go.Figure(go.Waterfall(
    orientation="v",
    measure=["absolute", "relative", "relative", "relative", "total"],
    x=["POA bruta", "IAM\n(reflexión)", "Soiling\n(suciedad)", "Térmico\n(temperatura)", "POA efectiva"],
    y=[bruta, -p_iam, -p_soil, -p_term, 0],
    text=[
        f"{bruta:,.0f}",
        f"−{p_iam:,.0f}",
        f"−{p_soil:,.0f}",
        f"−{p_term:,.1f}",
        f"{efect:,.0f}",
    ],
    textposition="outside",
    decreasing=dict(marker=dict(color="#e74c3c")),
    increasing=dict(marker=dict(color="#27ae60")),
    totals=dict(marker=dict(color="#2980b9")),
    connector=dict(line=dict(color="gray", width=1, dash="dot")),
))
fig_wf.update_layout(
    height=380,
    yaxis_title="kWh/m²/año",
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False,
    title=dict(
        text=(
            f"<b>Cascada óptico-térmica</b>  "
            f"<sup>b₀={summary['b0']:.3f} · k={summary['k_bipv']} · "
            f"NOCT={summary['noct']}°C · γ={summary['coef_temp']*100:.2f}%/°C</sup>"
        ),
        x=0.5, xanchor="center",
    ),
)
st.plotly_chart(fig_wf, use_container_width=True)

# ── 2C. Comparación mensual ───────────────────────────────────────────────────
st.markdown("#### 2.2. Comparación mensual: POA bruta vs POA efectiva")

monthly = summary["monthly"]
meses_es = monthly.index.tolist()

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    name="POA bruta",
    x=meses_es, y=monthly["poa_bruta"].round(1),
    marker_color="#85c1e9",
    opacity=0.85,
    text=monthly["poa_bruta"].round(0).astype(int),
    textposition="outside",
))
fig_bar.add_trace(go.Bar(
    name="POA efectiva (IAM+Soil+Térm)",
    x=meses_es, y=monthly["poa_efectiva"].round(1),
    marker_color="#e67e22",
    opacity=0.90,
    text=monthly["poa_efectiva"].round(0).astype(int),
    textposition="outside",
))
fig_bar.update_layout(
    barmode="group",
    height=370,
    xaxis_title="Mes",
    yaxis_title="kWh/m²/mes",
    legend=dict(orientation="h", y=-0.2),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
st.plotly_chart(fig_bar, use_container_width=True)

# ── 2D. Desglose pérdidas mensuales (apiladas) ────────────────────────────────
st.markdown("#### 2.3. Desglose de pérdidas por mes")

fig_stack = go.Figure()
for col, lbl, color in [
    ("perdida_iam",  "IAM (reflexión)",   "#e74c3c"),
    ("perdida_soil", "Soiling (suciedad)","#f39c12"),
    ("perdida_term", "Térmica",           "#8e44ad"),
]:
    fig_stack.add_trace(go.Bar(
        name=lbl,
        x=meses_es,
        y=monthly[col].round(2),
        marker_color=color,
        opacity=0.85,
    ))
fig_stack.update_layout(
    barmode="stack",
    height=320,
    xaxis_title="Mes",
    yaxis_title="Pérdida (kWh/m²/mes)",
    legend=dict(orientation="h", y=-0.25),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
st.plotly_chart(fig_stack, use_container_width=True)

# ── 2E. Tabla resumen de factores ────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 3. Factores promedio (horas con sol)")

MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
fcf = st.columns(3)
with fcf[0]:
    st.metric(
        "Factor IAM promedio",
        f"{summary['f_iam_prom']:.4f}",
        f"Pérdida: {(1-summary['f_iam_prom'])*100:.1f}%",
        delta_color="inverse",
        help="Promedio de f_IAM en horas con irradiancia directa > 10 W/m².",
    )
with fcf[1]:
    st.metric(
        "Factor Soiling promedio",
        f"{summary['f_soil_prom']:.4f}",
        f"Pérdida: {(1-summary['f_soil_prom'])*100:.1f}%",
        delta_color="inverse",
        help="Fracción media de POA retenida tras descontar suciedad.",
    )
with fcf[2]:
    st.metric(
        "Factor Térmico promedio",
        f"{summary['f_term_prom']:.4f}",
        f"Pérdida: {(1-summary['f_term_prom'])*100:.1f}%",
        delta_color="inverse",
        help=f"Degradación media de eficiencia por temperatura de celda con k_BIPV={summary['k_bipv']}.",
    )

# ── 2F. Impacto de la transparencia (informativo) ─────────────────────────────
st.markdown("---")
st.subheader(f"🪟 4. Impacto de la transparencia τ = {transparencia*100:.0f}%")

tau_val = st.session_state.get("motor_optico_tau", transparencia)
eta_factor = 1.0 - tau_val
efect_corr = summary["poa_efectiva_anual_kWh_m2"] * eta_factor

ci1, ci2, ci3 = st.columns(3)
ci1.metric(
    "POA efectiva óptico-térmica",
    f"{summary['poa_efectiva_anual_kWh_m2']:,.0f} kWh/m²/año",
    help="Irradiancia después de IAM + Soiling + Térmico.",
)
ci2.metric(
    "Factor de área activa (1−τ)",
    f"{eta_factor*100:.0f}%",
    help="Fracción del área con material semiconductor activo.",
)
ci3.metric(
    "POA aprovechable por la celda",
    f"{efect_corr:,.0f} kWh/m²/año",
    f"−{(1-eta_factor)*100:.0f}% por transparencia",
    delta_color="inverse",
    help="Energía que entra al semiconductor. Multiplica por η_STC para obtener energía eléctrica.",
)

st.caption(
    "ℹ️ La corrección por transparencia se aplica aquí de forma informativa. "
    "En 📐 Dimensionamiento, la eficiencia STC del panel ya incorpora τ "
    "según la especificación del fabricante."
)

# ── 2G. Comparativa con y sin motor óptico ────────────────────────────────────
st.markdown("---")
st.subheader("⚖️ 5. Impacto en el proyecto: con y sin correcciones ópticas")

delta_kWh = summary["poa_bruta_anual_kWh_m2"] - summary["poa_efectiva_anual_kWh_m2"]
pct_impacto = delta_kWh / summary["poa_bruta_anual_kWh_m2"] * 100

cmp1, cmp2, cmp3 = st.columns(3)
cmp1.metric(
    "Sin Motor Óptico (POA bruta)",
    f"{summary['poa_bruta_anual_kWh_m2']:,.0f} kWh/m²/año",
    "Estimación optimista — la actual calculadora",
)
cmp2.metric(
    "Con Motor Óptico (POA efectiva)",
    f"{summary['poa_efectiva_anual_kWh_m2']:,.0f} kWh/m²/año",
    f"−{pct_impacto:.1f}% vs estimación optimista",
    delta_color="inverse",
)
cmp3.metric(
    "Energía sobreestimada sin correcciones",
    f"{delta_kWh:,.0f} kWh/m²/año",
    "Diferencia a considerar en el análisis financiero",
    delta_color="inverse",
)

if pct_impacto > 15:
    st.warning(
        f"⚠️ La sobreestimación es **{pct_impacto:.1f}%** — significativa para una fachada vertical. "
        "El IAM domina las pérdidas en fachadas con ángulos de incidencia altos."
    )
elif pct_impacto > 8:
    st.info(
        f"ℹ️ La sobreestimación es **{pct_impacto:.1f}%** — moderada. "
        "El Motor Óptico mejora la precisión del análisis financiero."
    )
else:
    st.success(
        f"✅ La sobreestimación es **{pct_impacto:.1f}%** — baja para este sistema. "
        "La orientación y tipo de vidrio son favorables."
    )

# ── Nota final sobre integración downstream ───────────────────────────────────
st.markdown("---")
st.caption(
    "📌 **Integración con otras páginas:** La POA efectiva calculada aquí se guarda en sesión "
    "como `poa_efectiva_df`. En una próxima actualización, 📐 Dimensionamiento y 📊 Producción "
    "podrán usarla automáticamente. Por ahora, usa el **factor global** "
    f"(**{summary['factor_global']*100:.1f}%**) para ajustar manualmente las estimaciones de energía."
)
