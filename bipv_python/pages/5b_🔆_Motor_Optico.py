"""
Página 5b — Motor Óptico BIPV
Cascada de correcciones reales: IAM · Soiling · Modelo Térmico Confinado
Auto-llenado desde el panel configurado en Proyecto.
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

# ── Prerequisitos ──────────────────────────────────────────────────────────────
if not st.session_state.get("recurso_solar_ok"):
    st.warning(
        "⚠️ Primero ejecuta ☀️ **Recurso Solar** para obtener el TMY y la POA del sitio."
    )
    st.stop()

tmy_df  = st.session_state.get("tmy_df")
poa_df  = st.session_state.get("poa_df")
if tmy_df is None or poa_df is None:
    st.error(
        "❌ Los datos del Recurso Solar no están disponibles en sesión. "
        "Ejecuta ☀️ **Recurso Solar** de nuevo y vuelve aquí."
    )
    st.stop()
poa_anual_bruta = st.session_state.get("poa_anual_kWh_m2", 0.0)
tilt    = st.session_state.get("tilt_fachada", 90)
azimuth = st.session_state.get("azimuth_fachada", 0)
orient_lbl = st.session_state.get("orientacion_label", "—")
ciudad  = st.session_state.get("tmy_ciudad", "—")
mismatch_ok  = st.session_state.get("mismatch_ok", False)
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
# AUTO-LLENADO desde el panel configurado en Proyecto
# ══════════════════════════════════════════════════════════════════════════════

# Mapa tecnología → opción b₀ del selectbox
_B0_POR_TECH = {
    "CdTe":    "Vidrio CdTe laminado (b₀=0.12)",
    "CIGS":    "Vidrio BIPV semi-transparente (b₀=0.10)",
    "Mono-Si": "Vidrio estándar templado (b₀=0.05)",
    "Poli-Si": "Vidrio estándar templado (b₀=0.05)",
    "HJT":     "Vidrio estándar templado (b₀=0.05)",
    "TopCon":  "Vidrio estándar templado (b₀=0.05)",
    "a-Si":    "Vidrio BIPV semi-transparente (b₀=0.10)",
}
_B0_DEFAULT_KEY = "Vidrio estándar templado (b₀=0.05)"

_panel_dict = st.session_state.get("panel_dict")
_panel_nombre_actual = (_panel_dict or {}).get("nombre", "")
_panel_ref_anterior  = st.session_state.get("mo_panel_ref", "")

_panel_detectado = bool(_panel_dict and _panel_nombre_actual)
_panel_cambio    = _panel_nombre_actual != _panel_ref_anterior

if _panel_detectado and _panel_cambio:
    # ── Inferir b₀ desde la tecnología del panel ───────────────────────────
    _tecno = _panel_dict.get("tecnologia", "")
    _b0_key = _B0_POR_TECH.get(_tecno, _B0_DEFAULT_KEY)
    st.session_state["mo_vidrio_sel"] = _b0_key

    # ── NOCT (°C) ──────────────────────────────────────────────────────────
    _noct_raw = _panel_dict.get("NOCT")
    if _noct_raw and 35.0 <= float(_noct_raw) <= 65.0:
        st.session_state["mo_noct"] = float(_noct_raw)
    else:
        st.session_state["mo_noct"] = 50.0   # BIPV sin datahoja → conservador

    # ── γ coeficiente temperatura (%/°C) ──────────────────────────────────
    # Usar `is None` para no tratar 0.0 como falsy
    _gamma_raw = _panel_dict.get("gamma_mp")
    if _gamma_raw is None:
        _gamma_raw = _panel_dict.get("beta_mp")
    if _gamma_raw and -0.70 <= float(_gamma_raw) <= -0.05:
        st.session_state["mo_coef_temp"] = float(_gamma_raw)
    else:
        st.session_state["mo_coef_temp"] = -0.45

    # ── Transparencia τ (%) — clampeada al máx del slider ─────────────────
    _tau_raw = _panel_dict.get("transparencia_pct", 0) or 0
    st.session_state["mo_transparencia"] = int(min(float(_tau_raw), 70))

    # Marcar panel como referencia para detectar futuros cambios
    st.session_state["mo_panel_ref"] = _panel_nombre_actual

# ── Banner informativo sobre auto-llenado ─────────────────────────────────────
if _panel_detectado:
    _tecno_disp = _panel_dict.get("tecnologia", "—")
    _noct_disp  = st.session_state.get("mo_noct", "—")
    _gamma_disp = st.session_state.get("mo_coef_temp", "—")
    _tau_disp   = st.session_state.get("mo_transparencia", "—")
    _b0_disp    = B0_POR_VIDRIO.get(st.session_state.get("mo_vidrio_sel", ""), "—")
    st.success(
        f"🔗 **Auto-llenado desde panel:** `{_panel_nombre_actual}` ({_tecno_disp})  ·  "
        f"b₀ = {_b0_disp}  ·  τ = {_tau_disp}%  ·  "
        f"NOCT = {_noct_disp}°C  ·  γ = {_gamma_disp} %/°C  "
        "— Puedes ajustar cualquier valor manualmente."
    )

    # ── Verificación #151: ¿el Isc/Pmax del panel realmente incluye τ? ─────
    # El modelo asume que la ficha ya descuenta la transparencia
    # (Isc_real = Isc_celda × (1−τ)); si no, la producción se sobreestima
    # en silencio. Chequeo por eficiencia implícita del área activa.
    from calculos.validacion_bipv import verificar_isc_transparencia
    _chk_tau = verificar_isc_transparencia(_panel_dict)
    if _chk_tau["estado"] == "sospechoso_alto":
        st.error(
            f"🚨 **τ sin efecto real en `{_panel_nombre_actual}`:** {_chk_tau['mensaje']}  \n"
            "Corrige el Pmax/Isc de la ficha (deben ser los del panel "
            "semitransparente real) o revisa el área y la τ declaradas antes "
            "de confiar en la energía calculada.",
            icon="🚨",
        )
    elif _chk_tau["estado"] == "sospechoso_bajo":
        st.warning(f"⚠️ **Revisión de τ en `{_panel_nombre_actual}`:** {_chk_tau['mensaje']}", icon="⚠️")
    elif _chk_tau["estado"] == "sin_datos" and (_panel_dict.get("transparencia_pct") or 0) > 0:
        st.caption(f"🧪 Coherencia τ vs ficha: no verificable — {_chk_tau['mensaje']}")
    elif _chk_tau["estado"] == "ok":
        st.caption(
            f"🧪 Coherencia τ vs ficha: η módulo {_chk_tau['eta_modulo_pct']:.1f}% → "
            f"η área activa {_chk_tau['eta_activa_pct']:.1f}% "
            f"(≤ {_chk_tau['eta_max_pct']:.1f}% plausible) — el Isc/Pmax ya incorporan τ. ✅"
        )
else:
    st.info(
        "ℹ️ No se detectó un panel configurado en 🏠 Proyecto. "
        "Configura los parámetros manualmente o regresa a Proyecto para seleccionar un panel."
    )

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — CONFIGURACIÓN DEL VIDRIO Y MONTAJE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚙️ 1. Parámetros del vidrio y montaje BIPV")

# ── Guía b₀ ───────────────────────────────────────────────────────────────────
with st.expander("📘 ¿Qué es b₀ y cómo elegirlo?", expanded=False):
    st.markdown("""
    ### Coeficiente de reflexión ASHRAE **b₀**

    Cuando la luz solar llega a una superficie de vidrio en ángulo oblicuo (no perpendicular),
    una fracción mayor se refleja en lugar de penetrar al semiconductor. El modelo **ASHRAE 93**
    cuantifica esta pérdida con la fórmula:

    > **f_IAM = 1 − b₀ × (1/cos AOI − 1)**

    donde AOI es el ángulo de incidencia. En fachadas verticales, AOI puede superar los 60° en
    las mañanas y tardes, haciendo que b₀ sea el parámetro óptico más crítico para BIPV.

    | Tipo de vidrio / tecnología | **b₀** | Pérdida IAM anual típica | Norma / fuente |
    |---|---|---|---|
    | Vidrio estándar templado (Si mono/poli, HJT, TopCon) | **0.05** | ~8-12% en fachada vertical | ASHRAE 93 / pvlib default |
    | Vidrio BIPV semi-transparente (CIGS, a-Si) | **0.10** | ~14-18% en fachada vertical | IEC 61853-2 / King et al. Sandia |
    | Vidrio CdTe laminado (ASP-ST1, First Solar) | **0.12** | ~16-20% en fachada vertical | IEA-PVPS T15 / Pern 1997 |
    | Personalizado | manual | — | Dato del fabricante |

    > 💡 **Regla práctica:** si el fabricante no indica b₀, usa el valor de la tecnología.
    > Un b₀ más alto no indica peor vidrio per se — refleja la naturaleza del material semiconductor laminado.
    """)

# ── Guía k_BIPV ───────────────────────────────────────────────────────────────
with st.expander("📘 ¿Qué es k_BIPV y cómo elegirlo?", expanded=False):
    st.markdown("""
    ### Factor de confinamiento térmico **k_BIPV**

    En un panel convencional montado con espacio libre, el viento enfría la celda por convección.
    En BIPV integrado en fachada, la cámara trasera está restringida o sellada, lo que eleva
    la temperatura de la celda y reduce la eficiencia (ya que γ < 0).

    El factor **k_BIPV** multiplica el término de calentamiento del modelo NOCT:

    > **T_celda = T_amb + G × [(NOCT − 20) / 800] × k_BIPV**

    | Tipo de instalación | **k_BIPV** | Temperatura adicional vs ventilado | Norma / fuente |
    |---|---|---|---|
    | Fachada ventilada — cámara de aire > 10 cm libre | **1.0** | 0°C adicional | IEA-PVPS T15 / EN ISO 15927-4 |
    | Fachada BIPV típica — cámara 2–5 cm (montaje habitual) | **1.3** | +8–12°C vs ventilado | IEA-PVPS T15 / Bloem 2008 |
    | Fachada sellada — sin cámara de aire, vidrio pegado | **1.5** | +15–20°C vs ventilado | ISO 15927-4 / Trinuruk 2009 |

    > ⚠️ **Importante para BIPV en Colombia:** la mayoría de las fachadas de vidrio arquitectónico
    > tienen cámara de 20–50 mm → usar **k = 1.3**. Solo usar k = 1.5 en fachadas tipo "curtain wall"
    > totalmente selladas sin cámara de ventilación.

    | Pérdida térmica adicional por k_BIPV (ejemplo: Bogotá, fachada norte) | |
    |---|---|
    | k = 1.0 (ventilado) | T_cel media ≈ 31°C → pérdida ~2.7% |
    | k = 1.3 (confinado típico) | T_cel media ≈ 37°C → pérdida ~5.4% |
    | k = 1.5 (sellado) | T_cel media ≈ 41°C → pérdida ~7.2% |
    """)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Óptica del vidrio**")
    vidrio_sel = st.selectbox(
        "Tipo de vidrio",
        options=list(B0_POR_VIDRIO.keys()),
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
        _origen_b0 = " (desde panel)" if _panel_detectado else ""
        st.metric("b₀ ASHRAE seleccionado", f"{b0:.3f}", help=f"Coeficiente ASHRAE inferido de la tecnología{_origen_b0}.")

    transparencia = st.slider(
        "Transparencia τ del vidrio (%)",
        min_value=0, max_value=70, step=5,
        key="mo_transparencia",
        help="Porcentaje de área transparente (sin celda activa). Tomado de la ficha del panel.",
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
    st.metric(
        "k_BIPV",
        f"{k_bipv:.1f}",
        help="Factor de confinamiento térmico. Ver tabla explicativa arriba (📘 k_BIPV).",
    )

    noct = st.number_input(
        "NOCT (°C)",
        min_value=35.0, max_value=65.0, step=1.0,
        key="mo_noct",
        help="Temperatura nominal de operación (G=800 W/m², T=20°C, v=1 m/s). Tomado de la ficha del panel.",
    )

with col3:
    st.markdown("**Coeficiente térmico**")
    coef_pct = st.number_input(
        "γ — Coef. temperatura (%/°C)",
        min_value=-0.70, max_value=-0.10, step=0.01,
        format="%.2f",
        key="mo_coef_temp",
        help="Negativo siempre. Tomado de la ficha del panel. Silicio cristalino ≈ −0.45, CdTe ≈ −0.21.",
    )
    coef_temp = coef_pct / 100.0  # convertir a decimal/°C
    st.metric("γ (decimal/°C)", f"{coef_temp:.4f}")

    st.markdown("**Soiling y auto-limpieza**")
    usar_soiling_custom = st.checkbox(
        "Usar factores de soiling personalizados",
        value=False, key="mo_soiling_custom",
    )
    _tilt_actual = st.session_state.get("tilt_fachada", 90)
    _es_vertical = _tilt_actual >= 75
    _k_vert_default = 0.65 if _es_vertical else 1.0
    k_soiling_vert = st.slider(
        "Factor auto-limpieza vertical",
        min_value=0.30, max_value=1.00, step=0.05,
        value=float(st.session_state.get("mo_k_soiling_vert", _k_vert_default)),
        format="%.2f",
        key="mo_k_soiling_vert",
        help=(
            "Fachadas verticales se ensucian ~35% menos que superficies inclinadas "
            "(lluvia los limpia con mayor eficacia). "
            "k=0.65 → 35% menos soiling. k=1.0 → sin ajuste."
        ),
    )
    if _es_vertical and k_soiling_vert < 0.9:
        st.caption(f"🧹 Auto-limpieza vertical activa (k={k_soiling_vert:.2f})")

    st.markdown("**IAM difusa**")
    f_iam_dif = st.slider(
        "Factor IAM difusa (f_iam_dif)",
        min_value=0.80, max_value=1.00, step=0.01,
        value=float(st.session_state.get("mo_f_iam_dif", 0.95)),
        format="%.2f",
        key="mo_f_iam_dif",
        help=(
            "Factor IAM para la componente difusa (llega de todos los ángulos). "
            "IEC 61853-3 recomienda 0.95 para vidrio plano. "
            "CdTe laminado o vidrio texturado: 0.90–0.93."
        ),
    )

# Soiling config
if usar_soiling_custom:
    st.markdown("##### Factores de soiling mensual (0–15 %)")
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
    with st.spinner("Aplicando cascada IAM (dir+dif) → Soiling → Térmico → Transparencia (8 760 h)…"):
        try:
            result_df, summary = cascada_optica(
                tmy_df=tmy_df,
                poa_df=poa_df,
                b0=b0,
                noct=noct,
                coef_temp=coef_temp,
                k_bipv=k_bipv,
                soiling_config=soiling_config,
                f_iam_dif=f_iam_dif,
                transparencia=transparencia,
                k_soiling_vert=k_soiling_vert,
            )
            # ── Guardar en session_state ──────────────────────────────────────
            poa_ef_df = poa_df.copy()
            # reindex garantiza alineación por índice (no posicional con .values)
            poa_ef_df["poa_global"] = result_df["poa_efectiva"].reindex(poa_ef_df.index).fillna(0.0)

            st.session_state["motor_optico_ok"]            = True
            st.session_state["motor_optico_result_df"]     = result_df
            st.session_state["motor_optico_summary"]       = summary
            st.session_state["poa_efectiva_df"]            = poa_ef_df
            st.session_state["poa_efectiva_anual_kWh_m2"] = summary["poa_efectiva_anual_kWh_m2"]
            st.session_state["motor_optico_b0"]            = b0
            st.session_state["motor_optico_tau"]           = transparencia
            st.session_state["motor_optico_k_bipv"]        = k_bipv
            st.session_state["motor_optico_noct"]          = noct
            st.session_state["motor_optico_coef_temp"]     = coef_temp
            st.session_state["motor_optico_f_iam_dif"]     = f_iam_dif
            st.session_state["motor_optico_k_soil_vert"]   = k_soiling_vert

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

summary   = st.session_state["motor_optico_summary"]
result_df = st.session_state["motor_optico_result_df"]

st.markdown("---")
st.subheader("📊 2. Resultados de la cascada óptico-térmica")

# ── 2A. Métricas de pérdidas ──────────────────────────────────────────────────
_bruta = summary["poa_bruta_anual_kWh_m2"]
cm1, cm2, cm3, cm4, cm5, cm6 = st.columns(6)
cm1.metric(
    "POA bruta",
    f"{_bruta:,.0f} kWh/m²/año",
    help="Irradiancia plano de array sin correcciones.",
)
def _pct(val, total):
    return f"−{val/total*100:.1f}%" if total > 0 else "—"

cm2.metric(
    "Pérdida IAM total",
    f"−{summary['perdida_iam_kWh_m2']:,.0f} kWh/m²/año",
    _pct(summary['perdida_iam_kWh_m2'], _bruta),
    delta_color="inverse",
    help=(
        "Reflexión sobre la componente directa (ASHRAE b₀) "
        f"+ difusa (f_iam_dif={summary.get('f_iam_dif', 0.95):.2f}, IEC 61853-3)."
    ),
)
cm3.metric(
    "Pérdida soiling",
    f"−{summary['perdida_soil_kWh_m2']:,.0f} kWh/m²/año",
    _pct(summary['perdida_soil_kWh_m2'], _bruta),
    delta_color="inverse",
    help=f"Suciedad estacional Colombia × k_vert={summary.get('k_soiling_vert', 1.0):.2f} (auto-limpieza fachada).",
)
cm4.metric(
    "Pérdida térmica",
    f"−{summary['perdida_term_kWh_m2']:,.0f} kWh/m²/año",
    _pct(summary['perdida_term_kWh_m2'], _bruta),
    delta_color="inverse",
    help=f"Caída de eficiencia por temperatura > 25°C (k_BIPV={summary['k_bipv']}).",
)
_tau_pct = summary.get("transparencia", 0.0) * 100
_tau_loss = summary.get("perdida_tau_kWh_m2_info", 0)
cm5.metric(
    "Transparencia τ (info)",
    f"−{_tau_loss:,.0f} kWh/m²/año",
    f"τ={_tau_pct:.0f}% — solo referencia",
    delta_color="inverse",
    help=(
        "Pérdida INFORMACIONAL. El modelo de producción usa SDM donde "
        "Isc_stc ya incluye τ (se calibró en el panel real). "
        "No se resta del POA que va a Producción para evitar doble conteo."
    ),
)
cm6.metric(
    "POA efectiva → Producción",
    f"{summary['poa_efectiva_anual_kWh_m2']:,.0f} kWh/m²/año",
    f"{summary['factor_global']*100:.1f}% de la bruta",
    delta_color="normal",
    help="Irradiancia efectiva tras IAM (dir+dif) + Soiling + Térmico. Es la que usa Producción.",
)

# ── 2B. Gráfica Waterfall ──────────────────────────────────────────────────────
st.markdown("#### 2.1. Cascada de pérdidas (kWh/m²/año)")

bruta  = summary["poa_bruta_anual_kWh_m2"]
p_iam  = summary["perdida_iam_kWh_m2"]
p_soil = summary["perdida_soil_kWh_m2"]
p_term = summary["perdida_term_kWh_m2"]
p_tau  = summary.get("perdida_tau_kWh_m2_info", 0.0)   # informacional
efect  = summary["poa_efectiva_anual_kWh_m2"]

# ── Cascada principal (4 pasos → lo que va a Producción) ──────────────────────
fig_wf = go.Figure(go.Waterfall(
    orientation="v",
    measure=["absolute", "relative", "relative", "relative", "total"],
    x=["POA bruta", "IAM\n(dir+dif)", "Soiling\n(suciedad)", "Térmico\n(BIPV)", "POA efectiva\n→ Producción"],
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
            f"<b>Cascada óptico-térmica BIPV</b>  "
            f"<sup>b₀={summary['b0']:.3f} · f_dif={summary.get('f_iam_dif', 0.95):.2f} · "
            f"k={summary['k_bipv']} · NOCT={summary['noct']}°C · "
            f"γ={summary['coef_temp']*100:.2f}%/°C</sup>"
        ),
        x=0.5, xanchor="center",
    ),
)
st.plotly_chart(fig_wf, use_container_width=True)

# ── Nota de transparencia (informacional separada) ────────────────────────────
_tau_pct_wf = summary.get("transparencia", 0.0) * 100
if _tau_pct_wf > 0:
    st.info(
        f"ℹ️ **Transparencia τ={_tau_pct_wf:.0f}% — referencia:**  "
        f"Pérdida potencial si Isc_stc fuera de celda pura: **{p_tau:,.0f} kWh/m²/año**. "
        "Esta pérdida NO se resta del POA porque el catálogo usa Isc_stc del panel real "
        "(donde τ ya redujo la corriente). Restarla daría doble conteo en el modelo SDM."
    )

# ── 2C. Comparación mensual ────────────────────────────────────────────────────
st.markdown("#### 2.2. Comparación mensual: POA bruta vs POA efectiva")

monthly  = summary["monthly"]
meses_es = monthly.index.tolist()

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    name="POA bruta",
    x=meses_es, y=monthly["poa_bruta"].round(1),
    marker_color="#85c1e9", opacity=0.85,
    text=monthly["poa_bruta"].round(0).astype(int),
    textposition="outside",
))
fig_bar.add_trace(go.Bar(
    name="POA efectiva (IAM dir+dif · Soiling · Térm · τ)",
    x=meses_es, y=monthly["poa_efectiva"].round(1),
    marker_color="#e67e22", opacity=0.90,
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
for col_s, lbl, color in [
    ("perdida_iam",  "IAM dir+dif (reflexión)", "#e74c3c"),
    ("perdida_soil", "Soiling (suciedad)",       "#f39c12"),
    ("perdida_term", "Térmica (BIPV)",           "#8e44ad"),
    ("perdida_tau",  "Transparencia (τ)",        "#95a5a6"),
]:
    fig_stack.add_trace(go.Bar(
        name=lbl,
        x=meses_es,
        y=monthly[col_s].round(2),
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

# ── 2E. Tabla resumen de factores ─────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 3. Factores promedio (horas con sol)")

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
tau_val  = st.session_state.get("motor_optico_tau", transparencia)
st.subheader(f"🪟 4. Impacto de la transparencia τ = {tau_val*100:.0f}%")

eta_factor = 1.0 - tau_val
efect_corr  = summary["poa_efectiva_anual_kWh_m2"] * eta_factor

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

delta_kWh   = summary["poa_bruta_anual_kWh_m2"] - summary["poa_efectiva_anual_kWh_m2"]
pct_impacto = (delta_kWh / summary["poa_bruta_anual_kWh_m2"] * 100
               if summary["poa_bruta_anual_kWh_m2"] > 0 else 0.0)

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
    f"como `poa_efectiva_df` con factor global **{summary['factor_global']*100:.1f}%**. "
    "📊 **Producción** la usa automáticamente en cuanto ejecutas esta cascada — "
    "no necesitas ajustar nada manualmente."
)
