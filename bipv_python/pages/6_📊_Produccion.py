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
    # SECCIÓN — DIAGNÓSTICO: PRODUCCIÓN REAL DEL INVERSOR
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🔍 Diagnóstico: PR real vs PR esperado")
    st.caption(
        "Ingresa los kWh reales registrados por el inversor (o por la factura EPM) "
        "mes a mes para calcular el PR real y compararlo contra el PR simulado."
    )

    # ── HSP mensual desde POA base ────────────────────────────────────────────
    _poa_hsp = poa_base.copy()
    _poa_hsp["_mes"] = _poa_hsp.index.month
    _hsp_mes = _poa_hsp.groupby("_mes")["poa_global"].sum() / 1000.0  # kWh/m² → HSP

    meses_etiq = ["Ene","Feb","Mar","Abr","May","Jun",
                  "Jul","Ago","Sep","Oct","Nov","Dic"]

    # ── Tabla de ingreso de datos reales ─────────────────────────────────────
    st.markdown("#### 📥 Ingresar producción real del inversor (kWh/mes)")

    _prev = st.session_state.get("diag_real_kwh", {})

    cols_inp = st.columns(6)
    kwh_real = {}
    for i, mes in enumerate(meses_etiq):
        col = cols_inp[i % 6]
        kwh_real[mes] = col.number_input(
            mes,
            min_value=0.0,
            max_value=500_000.0,
            value=float(_prev.get(mes, 0.0)),
            step=10.0,
            format="%.1f",
            key=f"diag_real_{mes}",
            help=f"kWh AC reales medidos por el inversor en {mes}",
        )

    # Guardar valores ingresados
    st.session_state["diag_real_kwh"] = kwh_real

    meses_con_dato = [m for m in meses_etiq if kwh_real[m] > 0]

    if not meses_con_dato:
        st.info(
            "💡 Ingresa los kWh reales de al menos un mes para ver el diagnóstico. "
            "Puedes obtenerlos del display del inversor, su app de monitoreo o de la factura EPM."
        )
    else:
        # ── Calcular comparativa ──────────────────────────────────────────────
        filas = []
        for i, mes in enumerate(meses_etiq):
            num_mes   = i + 1
            e_sim     = df_m.loc[df_m.index == mes, "E_ac (kWh)"].values
            e_sim_val = float(e_sim[0]) if len(e_sim) > 0 else 0.0
            hsp_val   = float(_hsp_mes.get(num_mes, 0.0))
            e_real    = kwh_real[mes]

            # PR esperado del mes = E_sim / (P_stc × HSP_mes)
            pr_esp = (e_sim_val / (P_stc_kW * hsp_val)) if (P_stc_kW > 0 and hsp_val > 0) else 0.0
            # PR real del mes
            pr_real = (e_real / (P_stc_kW * hsp_val)) if (e_real > 0 and P_stc_kW > 0 and hsp_val > 0) else None

            if pr_real is not None:
                ratio = pr_real / pr_esp if pr_esp > 0 else 0.0
                if ratio >= 0.90:
                    semaforo = "🟢"
                    estado   = "Normal"
                elif ratio >= 0.80:
                    semaforo = "🟡"
                    estado   = "Revisar"
                else:
                    semaforo = "🔴"
                    estado   = "Problema"
                delta_kwh  = e_real - e_sim_val
                delta_pct  = (delta_kwh / e_sim_val * 100) if e_sim_val > 0 else 0.0
            else:
                semaforo = "⬜"; estado = "Sin dato"
                delta_kwh = None; delta_pct = None; ratio = None

            filas.append({
                "Mes":           mes,
                "HSP (h)":       round(hsp_val, 1),
                "E_sim (kWh)":   round(e_sim_val, 0),
                "E_real (kWh)":  round(e_real, 0) if e_real > 0 else "—",
                "PR_esp (%)":    round(pr_esp * 100, 1) if pr_esp > 0 else "—",
                "PR_real (%)":   round(pr_real * 100, 1) if pr_real is not None else "—",
                "Δ kWh":         round(delta_kwh, 0) if delta_kwh is not None else "—",
                "Δ %":           round(delta_pct, 1) if delta_pct is not None else "—",
                "Estado":        f"{semaforo} {estado}",
            })

        df_diag = pd.DataFrame(filas)

        # ── Gráfica PR real vs esperado ───────────────────────────────────────
        meses_grafica  = [f["Mes"] for f in filas if f["PR_real (%)"] != "—"]
        pr_esp_grafica = [f["PR_esp (%)"] for f in filas if f["PR_real (%)"] != "—"]
        pr_real_grafica= [f["PR_real (%)"] for f in filas if f["PR_real (%)"] != "—"]
        e_sim_graf     = [f["E_sim (kWh)"] for f in filas if f["E_real (kWh)"] != "—"]
        e_real_graf    = [f["E_real (kWh)"] for f in filas if f["E_real (kWh)"] != "—"]

        tab1, tab2 = st.tabs(["📊 PR real vs esperado", "📅 kWh real vs simulado"])

        with tab1:
            fig_pr = go.Figure()
            fig_pr.add_trace(go.Bar(
                name="PR esperado (simulado)",
                x=meses_grafica, y=pr_esp_grafica,
                marker_color="#1565C0", opacity=0.75,
            ))
            fig_pr.add_trace(go.Bar(
                name="PR real (inversor)",
                x=meses_grafica, y=pr_real_grafica,
                marker_color=[
                    "#2E7D32" if (r >= e * 0.90) else
                    "#F9A825" if (r >= e * 0.80) else
                    "#C62828"
                    for r, e in zip(pr_real_grafica, pr_esp_grafica)
                ],
                opacity=0.90,
                text=[f"{r:.1f}%" for r in pr_real_grafica],
                textposition="outside",
            ))
            fig_pr.add_hline(
                y=float(res["PR"]) * 100 * 0.90,
                line_dash="dash", line_color="#EF5350",
                annotation_text="Umbral 90% PR", annotation_position="top right",
            )
            fig_pr.update_layout(
                barmode="group", yaxis_title="Performance Ratio (%)",
                height=380, plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", y=-0.25), margin=dict(b=80),
                yaxis=dict(range=[0, max(max(pr_esp_grafica), max(pr_real_grafica)) * 1.15]),
            )
            st.plotly_chart(fig_pr, use_container_width=True)

        with tab2:
            fig_kwh = go.Figure()
            fig_kwh.add_trace(go.Bar(
                name="E_ac simulada (kWh)",
                x=meses_grafica, y=e_sim_graf,
                marker_color="#1565C0", opacity=0.70,
            ))
            fig_kwh.add_trace(go.Bar(
                name="E_ac real inversor (kWh)",
                x=meses_grafica, y=e_real_graf,
                marker_color="#2E7D32", opacity=0.85,
                text=[f"{v:,.0f}" for v in e_real_graf],
                textposition="outside",
            ))
            fig_kwh.update_layout(
                barmode="group", yaxis_title="Energía (kWh)",
                height=380, plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", y=-0.25), margin=dict(b=80),
            )
            st.plotly_chart(fig_kwh, use_container_width=True)

        # ── Tabla comparativa ─────────────────────────────────────────────────
        st.markdown("#### 📋 Tabla comparativa mes a mes")
        st.dataframe(df_diag, use_container_width=True, hide_index=True)

        # ── Diagnóstico automático ────────────────────────────────────────────
        meses_rojo    = [f["Mes"] for f in filas if f["Estado"].startswith("🔴")]
        meses_amarillo= [f["Mes"] for f in filas if f["Estado"].startswith("🟡")]
        meses_verde   = [f["Mes"] for f in filas if f["Estado"].startswith("🟢")]

        # Totales reales ingresados
        total_real = sum(kwh_real[m] for m in meses_etiq if kwh_real[m] > 0)
        total_sim  = sum(
            float(df_m.loc[df_m.index == m, "E_ac (kWh)"].values[0])
            for m in meses_con_dato
            if len(df_m.loc[df_m.index == m]) > 0
        )
        tarifa_ref = st.session_state.get("tarifa_kwh", 650)
        perdida_cop= max(0.0, (total_sim - total_real) * tarifa_ref)

        st.markdown("#### 🩺 Diagnóstico automático")

        if meses_rojo:
            st.error(
                f"🔴 **Problema detectado en: {', '.join(meses_rojo)}** — "
                f"PR real < 80% del esperado. "
                "Causas probables: paneles degradados, suciedad severa, sombras, "
                "falla en strings o en el inversor. Requiere inspección de campo urgente."
            )
        if meses_amarillo:
            st.warning(
                f"🟡 **Atención en: {', '.join(meses_amarillo)}** — "
                f"PR real entre 80% y 90% del esperado. "
                "Posible suciedad acumulada, sombreado parcial o degradación leve. "
                "Verificar limpieza y revisar strings individuales."
            )
        if meses_verde and not meses_rojo and not meses_amarillo:
            st.success(
                f"🟢 **Sistema operando correctamente** en todos los meses ingresados "
                f"({', '.join(meses_verde)}). PR real ≥ 90% del esperado."
            )
        if total_sim > 0:
            delta_total = total_real - total_sim
            delta_pct_total = delta_total / total_sim * 100
            st.info(
                f"📊 **Resumen acumulado ({len(meses_con_dato)} meses con dato):** "
                f"E_real = **{total_real:,.0f} kWh** | "
                f"E_simulada = **{total_sim:,.0f} kWh** | "
                f"Diferencia = **{delta_total:+,.0f} kWh ({delta_pct_total:+.1f}%)**"
                + (f" | Pérdida estimada ≈ **${perdida_cop:,.0f} COP**" if perdida_cop > 0 else "")
            )

        # Guardar para Reporte PDF
        st.session_state["df_diagnostico_real"] = df_diag
        st.session_state["diag_meses_rojo"]     = meses_rojo
        st.session_state["diag_meses_amarillo"] = meses_amarillo
        st.session_state["diag_total_real_kwh"] = total_real
        st.session_state["diag_total_sim_kwh"]  = total_sim
