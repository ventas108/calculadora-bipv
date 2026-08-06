"""Página 6 — Producción anual BIPV (IEC 61724)."""
import streamlit as st

from calculos.auth import requerir_login
requerir_login()
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from calculos.produccion import simular_produccion_anual, perdidas_desglosadas, panel_tiene_sdm_completo
from calculos.produccion_iv import simular_produccion_iv, panel_apto_para_iv, preparar_para_iv
from datos.tecnologias_bipv import MODULOS_BIPV
from datos.catalogo_inversores import INVERSORES
from datos.catalogo_paneles_excel import cargar_catalogo_excel, obtener_panel_excel
from datos.catalogo_inversores_excel import cargar_catalogo_inversores

st.set_page_config(page_title="Producción — BIPV", page_icon="📊", layout="wide")
from utils.ui import bloquear_traduccion
bloquear_traduccion()
st.title("📊 Producción Anual — IEC 61724")
st.caption(
    "Simulación hora a hora · Motor SDM De Soto 2006 · "
    "Temperatura NOCT · Métricas IEC 61724"
)

# ── Prerequisitos ─────────────────────────────────────────────────────────────
if not st.session_state.get("recurso_solar_ok"):
    st.warning("⚠️ Primero ejecuta ☀️ Recurso Solar para obtener el TMY del sitio.")
    st.stop()

tmy             = st.session_state.get("tmy_df")
if tmy is None:
    st.error("❌ TMY no disponible en sesión. Ejecuta ☀️ **Recurso Solar** de nuevo.")
    st.stop()
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
    poa_base          = st.session_state.get("poa_efectiva_df") or st.session_state.get("poa_df")
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
    | Motor Óptico (IAM dir+dif · Soiling · Térmico BIPV) | {"✅ activo" if _motor_ok else "⬜ no ejecutado"} | {st.session_state.get("poa_efectiva_anual_kWh_m2", "—"):{",.0f" if _motor_ok else ""}} {"kWh/m²/año" if _motor_ok else ""} |
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
    _cat_excel  = cargar_catalogo_excel() or {}
    _lista_pan  = sorted(_cat_excel.keys()) if _cat_excel else list(MODULOS_BIPV.keys())
    _pan_default = st.session_state.get("panel_nombre_dim", "")
    _pan_idx     = _lista_pan.index(_pan_default) if _pan_default in _lista_pan else 0
    panel_nombre = st.selectbox("Panel fotovoltaico", _lista_pan, index=_pan_idx)
    panel = obtener_panel_excel(panel_nombre) if _cat_excel else MODULOS_BIPV.get(panel_nombre, {})

    # Mostrar ficha rápida
    _sdm_ok = panel_tiene_sdm_completo(panel)
    st.caption(
        f"Pmax STC: {panel.get('Pmax_stc','—')} W · "
        f"Área: {panel.get('area_m2','—')} m² · "
        f"NOCT: {panel.get('NOCT',45)}°C · "
        f"{'🟢 SDM De Soto completo' if _sdm_ok else '🟡 Modelo simplificado (±15%)'}"
    )
    if not _sdm_ok:
        _faltantes = [p for p in ("I_L_ref","I_o_ref","R_s","R_sh_ref","a_ref")
                      if panel.get(p) is None or panel.get(p) == 0.0]
        st.warning(
            f"⚠️ **{panel_nombre}** no tiene parámetros SDM completos "
            f"(`{'`, `'.join(_faltantes)}`).  \n"
            "La simulación usará el **modelo simplificado lineal** — incertidumbre ±10–20% "
            "respecto al SDM De Soto real, especialmente a irradiancias bajas y en clima frío.  \n"
            "Para mayor precisión: calibra el SDM en 🔬 **Motor IV** o sube la ficha completa "
            "en 📋 **Catálogo Paneles**.",
            icon="⚠️",
        )

with col_c2:
    # Prioridad: total granja > por inversor > default
    n_granja  = st.session_state.get("N_paneles_granja", 0)
    n_inv     = st.session_state.get("N_paneles_dim", 0)
    n_default = n_granja if n_granja > 0 else (n_inv if n_inv > 0 else 64)

    N_paneles = st.number_input(
        "Número de módulos (N_paneles)",
        min_value=1, max_value=50000,
        value=int(n_default),
        step=1,
        help="Se toma automáticamente del Proyecto completo en 📐 Dimensionamiento.",
    )

    area_ocup = N_paneles * (panel.get("area_m2") or 0)
    P_stc_kW  = round(panel.get("Pmax_stc", 60) * N_paneles / 1000, 3)
    st.metric("Potencia instalada", f"{P_stc_kW:.2f} kWp")
    st.metric("Área módulos",       f"{area_ocup:.1f} m²")

with col_c3:
    _cat_inv_p   = cargar_catalogo_inversores() or {}
    _lista_inv_p = sorted(_cat_inv_p.keys()) if _cat_inv_p else list(INVERSORES.keys())
    _inv_default = st.session_state.get("inversor_nombre_dim", "")
    _inv_idx_p   = _lista_inv_p.index(_inv_default) if _inv_default in _lista_inv_p else 0
    inversor_nombre = st.selectbox("Inversor", _lista_inv_p, index=_inv_idx_p)
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

# ── Modo Motor IV (opt-in) — #105: SDM calibrado O estimado desde ficha ──────
_panel_iv_prep, _sdm_origen = preparar_para_iv(panel)
_panel_apto_iv = _panel_iv_prep is not None
usar_iv = False
if _panel_apto_iv:
    _origen_txt = (
        "parámetros SDM **calibrados** del catálogo"
        if _sdm_origen == "calibrado"
        else "SDM **estimado desde la ficha** (Voc/Isc/Vmp/Imp + Ns, fit De Soto)"
    )
    usar_iv = st.toggle(
        "🔬 Usar curva IV real del panel (Motor IV)",
        value=st.session_state.get("produccion_usar_iv", False),
        key="produccion_usar_iv",
        help=(
            "Deriva la potencia Pmp(G, Tcell) de la curva I-V single-diode "
            "(De Soto 2006 + Rsh CdTe), en lugar del modelo lineal genérico. "
            f"Este panel usa {_origen_txt}. Modo opt-in: por defecto se usa el "
            "modelo base."
        ),
    )
    if usar_iv:
        st.caption(
            f"🟢 Modo **curva IV real** activo ({_origen_txt}) — se comparará contra "
            "el modelo base y la E_ac oficial (aguas abajo) usará el resultado del Motor IV."
        )
        if _sdm_origen == "estimado_ficha":
            st.caption(
                "ℹ️ Los parámetros SDM se estimaron a partir de los 4 puntos de la ficha; "
                "verifica en 🔬 **Motor IV** que la curva reproduce la ficha (error < 5%)."
            )
else:
    # #105: si el panel cambió a uno NO apto, limpiar el estado IV anterior —
    # sin esto quedaría el toggle en True y una comparación IV de OTRO panel.
    if st.session_state.get("produccion_usar_iv") or st.session_state.get("res_produccion_iv") is not None:
        st.session_state["produccion_usar_iv"] = False
        st.session_state["res_produccion_iv"]  = None
        st.session_state["produccion_modo_iv"] = False
    st.caption(
        "ℹ️ El modo **curva IV real (Motor IV)** no está disponible: este panel no tiene "
        "ni parámetros SDM calibrados ni ficha completa (Voc, Isc, Vmp, Imp y N_s) para "
        "estimarlos. Se usa el modelo base. Completa la ficha en 🔬 Motor IV o 📋 Catálogo Paneles."
    )

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
            _sim_kwargs = dict(
                tmy               = tmy,
                poa_base          = poa_base,
                panel             = panel,
                N_paneles         = N_paneles,
                eta_inversor      = eta_inv_frac,
                factor_pr_mismatch= factor_pr,
                P_dc_stc_kW       = P_stc_kW,
            )
            res_base = simular_produccion_anual(**_sim_kwargs)
            res_iv   = None
            if usar_iv and _panel_apto_iv:
                # #105: pasar el panel YA preparado (evita repetir el fit_desoto
                # y garantiza que se simula con el mismo SDM mostrado arriba).
                res_iv = simular_produccion_iv(**{**_sim_kwargs, "panel": _panel_iv_prep})

        # El modo IV es opt-in: si está activo y disponible, queda como oficial.
        res = res_iv if (usar_iv and res_iv is not None) else res_base

        st.session_state["res_produccion"]         = res
        st.session_state["res_produccion_base"]    = res_base
        st.session_state["res_produccion_iv"]      = res_iv
        st.session_state["produccion_modo_iv"]     = bool(usar_iv and res_iv is not None)
        st.session_state["produccion_ok"]          = True
        st.session_state["N_paneles_dim"]          = N_paneles
        st.session_state["P_dc_stc_kW_dim"]        = P_stc_kW
        # E_ac_anual_kWh = valor "base" oficial (multi-superficie > bypass > base
        # aguas abajo). Al elegir IV como oficial, la base pasa a ser la IV.
        st.session_state["E_ac_anual_kWh"]         = res["E_ac_anual_kWh"]
        st.session_state["PR_sistema"]             = res["PR"]
    else:
        res       = st.session_state.get("res_produccion", {})
        res_base  = st.session_state.get("res_produccion_base", res)
        res_iv    = st.session_state.get("res_produccion_iv", None)

    if not res:
        st.stop()

    # ── Comparación modelo IV vs modelo base (solo si IV está activo) ──────────
    if res_iv is not None and res_base:
        e_base = res_base["E_ac_anual_kWh"]
        e_iv   = res_iv["E_ac_anual_kWh"]
        dif_pct = (e_iv - e_base) / e_base * 100 if e_base > 0 else 0.0

        st.markdown("#### 🔬 Comparación: modelo base vs curva IV real")
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("E_ac — modelo base", f"{e_base:,.0f} kWh",
                   help="Modelo hora a hora estándar de la página (SDM/lineal)")
        cc2.metric("E_ac — curva IV real", f"{e_iv:,.0f} kWh",
                   help="Pmp(G,Tcell) derivada de la curva I-V single-diode de la ficha")
        cc3.metric("Diferencia", f"{dif_pct:+.1f}%",
                   delta=f"{e_iv - e_base:+,.0f} kWh")

        if abs(dif_pct) > 10.0:
            if res_iv.get("sdm_origen") == "estimado_ficha":
                st.error(
                    f"🔴 **La curva IV difiere {dif_pct:+.1f}% del modelo base (> ±10%).**  \n"
                    "El SDM de este panel fue **estimado desde la ficha** y aquí se compara "
                    "contra el modelo lineal: una divergencia así sugiere que la estimación "
                    "no reproduce bien la ficha (Voc/Isc/Vmp/Imp o N_s half-cut). Valida la "
                    "curva en 🔬 **Motor IV** antes de usar este resultado en Financiero."
                )
            else:
                st.error(
                    f"🔴 **La curva IV difiere {dif_pct:+.1f}% del modelo base (> ±10%).**  \n"
                    "Es una señal de **datos de ficha inconsistentes** (Voc/Isc/Vmp/Imp, "
                    "N_s half-cut, o parámetros SDM mal calibrados). Revisa la ficha en "
                    "🔬 **Motor IV** antes de usar este resultado en el análisis financiero."
                )
        else:
            st.success(
                f"🟢 Ambos modelos coinciden dentro de ±10% (diferencia {dif_pct:+.1f}%). "
                "**La E_ac oficial aguas abajo usa el modelo de curva IV real.**"
            )
    elif st.session_state.get("produccion_modo_iv") is False and _panel_apto_iv and not usar_iv:
        st.caption(
            "ℹ️ E_ac oficial = **modelo base**. Activa el toggle de curva IV real "
            "y vuelve a simular para comparar y usar el Motor IV como oficial."
        )

    # ── Aviso modelo simplificado (post-simulación) ───────────────────────────
    if res.get("uso_modelo_simplificado"):
        st.warning(
            "⚠️ **Simulación con modelo simplificado** — este panel no tiene parámetros SDM "
            "completos, por lo que se usó `Pmax = Pmax_stc × G/1000 × (1 + γ·ΔT)` en lugar "
            "del SDM De Soto 2006.  \n"
            "La incertidumbre en E_ac es **±10–20%**, mayor en horas de baja irradiancia "
            "y en climas fríos donde el SDM capta la ganancia real por temperatura.  \n"
            "Para resultados más precisos, completa los parámetros en 🔬 **Motor IV** "
            "o sube la ficha técnica en 📋 **Catálogo Paneles**.",
            icon="⚠️",
        )

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
              help=(
                  "**Performance Ratio IEC 61724**  \n"
                  "PR = Y_f / Y_r = E_ac / (P_stc × H_POA_bruta)  \n\n"
                  "Mide la eficiencia global del sistema frente a su potencial teórico "
                  "(irradiancia × potencia nominal).  \n\n"
                  "**Rangos típicos Colombia BIPV:**  \n"
                  "· Fachada vertical: 55–70 %  \n"
                  "· Techo inclinado optimizado: 70–80 %  \n"
                  "· PR > 100 %: normal en climas fríos (Bogotá, Manizales) — "
                  "los módulos CdTe ganan eficiencia por debajo de 25 °C"
              ))
    m6.metric("Factor de Planta",  f"{res['CF_pct']:.1f}%",
              help="Capacity Factor = E_ac / (P_STC × 8760 h)")

    # ── Alertas de rango PR IEC 61724 ─────────────────────────────────────────
    _pr_pct = res["PR"] * 100
    if _pr_pct < 50:
        st.error(
            f"🔴 **PR = {_pr_pct:.1f}% — MUY BAJO (< 50%).**  \n"
            "Posibles causas: inversor sobredimensionado, pérdidas de cableado altas, "
            "paneles degradados o datos de entrada inconsistentes.  \n"
            "Revisa la simulación antes de utilizarla en un análisis financiero."
        )
    elif _pr_pct < 60:
        st.warning(
            f"⚠️ **PR = {_pr_pct:.1f}% — por debajo del rango típico Colombia BIPV (60–75%).**  \n"
            "Para fachadas verticales con orientación desfavorable puede ser esperado. "
            "Verifica la orientación, inclinación y las pérdidas del sistema."
        )
    elif 90 < _pr_pct <= 100:
        st.warning(
            f"⚠️ **PR = {_pr_pct:.1f}% — alto (> 90%).**  \n"
            "Verifica que la potencia nominal del sistema y la POA de referencia sean correctas. "
            "PR > 90 % es inusual en zonas tropicales — si no estás en clima frío de altitud, revisa los datos."
        )
    # PR > 100%: ya se maneja abajo con contexto de sobre-rendimiento en climas fríos

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

    # ── Incluir pérdida bypass diodes si está disponible ─────────────────
    _bypass_ok  = st.session_state.get("bypass_ok", False)
    _res_bp     = st.session_state.get("bypass_result", {})
    kwh_bypass  = _res_bp.get("kwh_bypass_anual", 0.0) if _bypass_ok else 0.0
    kwh_bypass_ac = kwh_bypass * eta_inv_frac   # pérdida AC equivalente

    etapas_bal  = ["Ganancia T° CdTe" if delta_sdm >= 0 else "Pérdida óptica+T°",
                   "Pérdida T° (horas calientes)",
                   "Pérdida inversor"]
    vals_bal    = [delta_sdm, -p_temp, -p_inv]
    colores_bal = [
        "#2E7D32" if delta_sdm >= 0 else "#EF5350",
        "#FF7043",
        "#FFA726",
    ]

    if _bypass_ok and kwh_bypass > 0:
        etapas_bal.append("⚡ Bypass diodes (sombra parcial)")
        vals_bal.append(-kwh_bypass_ac)
        colores_bal.append("#C62828")

    pct_ref = [round(abs(v) / e_ref * 100, 1) if e_ref > 0 else 0 for v in vals_bal]

    chart_height = 260 + (40 if _bypass_ok and kwh_bypass > 0 else 0)
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
        height=chart_height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=200, r=180),
    )
    st.plotly_chart(fig_loss, use_container_width=True)

    if _bypass_ok and kwh_bypass > 0:
        e_ac_corr = res["E_ac_anual_kWh"] - kwh_bypass_ac
        pct_bp    = _res_bp.get("pct_bypass_anual", 0.0)
        st.info(
            f"⚡ **Bypass diodes incluidos** — "
            f"Pérdida adicional: **{kwh_bypass:,.0f} kWh DC · {kwh_bypass_ac:,.0f} kWh AC/año** "
            f"({pct_bp:.2f}% de E_dc) | "
            f"**E_ac corregida ≈ {e_ac_corr:,.0f} kWh/año** "
            f"(vs {res['E_ac_anual_kWh']:,.0f} sin bypass)"
        )
        # Actualizar E_ac con corrección bypass para páginas financieras
        st.session_state["E_ac_anual_kWh_bypass"] = round(e_ac_corr, 0)
        st.session_state["kwh_bypass_anual"]       = round(kwh_bypass, 1)

    st.caption(
        f"E ref (P_STC × POA): **{e_ref:,.0f} kWh** | "
        f"E_dc: **{e_dc:,.0f} kWh** | "
        f"E_ac: **{res['E_ac_anual_kWh']:,.0f} kWh**"
        + (f" | E_ac con bypass: **{res['E_ac_anual_kWh'] - kwh_bypass_ac:,.0f} kWh**"
           if _bypass_ok and kwh_bypass > 0 else "")
    )

    # ── Aporte de la cara trasera (modelo bifacial) ───────────────────────────
    if poa_base is not None and {"poa_front", "poa_rear"}.issubset(poa_base.columns):
        # Aporte EFECTIVO al global = poa_global − poa_front
        # (= bifacialidad × factor_vista_trasera × POA trasera bruta)
        _front_kwh_m2  = float(poa_base["poa_front"].sum()) / 1000.0
        _global_kwh_m2 = float(poa_base["poa_global"].sum()) / 1000.0
        _rear_ef_kwh_m2 = max(_global_kwh_m2 - _front_kwh_m2, 0.0)
        _rear_pct      = (_rear_ef_kwh_m2 / _global_kwh_m2 * 100.0) if _global_kwh_m2 > 0 else 0.0

        st.markdown("---")
        st.subheader("🔆 Aporte de la cara trasera (bifacial)")
        mb1, mb2, mb3 = st.columns(3)
        mb1.metric("Cara frontal (POA)", f"{_front_kwh_m2:,.0f} kWh/m²/año",
                   help="Irradiación sobre la cara frontal (pvlib infinite_sheds, con sombreado fila-fila)")
        mb2.metric("Aporte trasero efectivo", f"{_rear_ef_kwh_m2:,.0f} kWh/m²/año",
                   help="Irradiación trasera ya ponderada por la bifacialidad del panel "
                        "(y el factor de vista si es fachada adosada) — es lo que realmente suma a la POA global")
        mb3.metric("Aporte trasero", f"{_rear_pct:.1f}% de la POA global",
                   help="Fracción de la POA global usada en la simulación que proviene de la cara trasera")
        st.caption(
            "Modelo bifacial activo (pvlib infinite_sheds): la POA global usada en la simulación "
            "ya integra el aporte de la cara trasera, por lo que la **E_ac anual ya lo incluye**. "
            "No se debe sumar aparte."
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

---
**Referencia IEC 61724 — rangos Colombia BIPV:**

| Tipo de sistema | PR típico | Nota |
|---|---|---|
| Fachada vertical (Sur/Occidente) | 55–65 % | Ángulo de incidencia alto → menor captura |
| Fachada vertical (Norte/Oriente) | 60–70 % | Mejor orientación para Colombia |
| Techo inclinado 15–25° | 70–80 % | Óptimo para la latitud colombiana |
| Pérgola / sombreadero | 65–75 % | Depende de la inclinación |
| PR < 50 % | ⚠️ Revisar | Posible error de datos o pérdidas anómalas |
| PR > 90 % | ⚠️ Verificar | Inusual en zonas tropicales |
| PR > 100 % | ✅ Normal frío | Climas Andinos > 2 000 m (Bogotá, Manizales, Pasto) |

*Fuente: UPME / CREG, proyectos BIPV Colombia 2022–2025.*
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
    # Usar `is None` para no tratar 0.0 como falsy; fallback si clave existe con None
    _tk_raw = panel.get("Tk_gamma")
    gamma_pct  = float(_tk_raw) if _tk_raw is not None else -0.45   # %/°C (negativo)
    gamma_frac = gamma_pct / 100.0                                   # fracción/°C

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
        tarifa_ref  = float(st.session_state.get(
            "tarifa_cop_kwh",                         # clave canónica (Proyecto/Financiero)
            st.session_state.get("tarifa_cop_kWh",    # fallback legacy
            st.session_state.get("tarifa_kwh", 650))  # fallback original
        ))
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

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN — #28 TASA DE DEGRADACIÓN ANUAL DESDE HISTORIAL DE PR
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📉 Tasa de degradación anual del sistema")
st.caption(
    "Ingresa el **PR corregido por temperatura** de cada año operativo para detectar "
    "la degradación real de los módulos mediante regresión lineal. "
    "Requiere al menos **2 años** de datos."
)

n_anos_hist = st.number_input(
    "Número de años con datos",
    min_value=2, max_value=15, value=3, step=1,
    key="deg_n_anos_hist",
    help="Cada año → un valor de PR_corr_T promedio anual.",
)

# Tabla de entrada: año | PR_corr_T (%)
_hist_data = []
_deg_cols  = st.columns(min(int(n_anos_hist), 6))
for _i in range(int(n_anos_hist)):
    _col_i = _deg_cols[_i % len(_deg_cols)]
    _yr_v  = _col_i.number_input(
        f"Año {_i + 1}",
        min_value=2015, max_value=2040,
        value=int(st.session_state.get(f"deg_ano_{_i}", 2023 - int(n_anos_hist) + 1 + _i)),
        step=1, key=f"deg_ano_{_i}",
    )
    _pr_v  = _col_i.number_input(
        f"PR_corr_T {_yr_v} (%)",
        min_value=40.0, max_value=100.0,
        value=float(st.session_state.get(f"deg_pr_{_i}", 80.0)),
        step=0.5, format="%.1f",
        key=f"deg_pr_{_i}",
        help="PR corregido por temperatura de la tabla de diagnóstico. Promedio anual.",
    )
    _hist_data.append({"año": float(_yr_v), "pr": float(_pr_v)})

if len(_hist_data) >= 2:
    import numpy as _np_deg
    _años_arr = _np_deg.array([d["año"] for d in _hist_data])
    _prs_arr  = _np_deg.array([d["pr"]  for d in _hist_data])
    _slope, _intercept = _np_deg.polyfit(_años_arr, _prs_arr, 1)
    # Tasa relativa: % de pérdida por año respecto al PR del primer año
    _pr_inicial      = float(_prs_arr[0]) if _prs_arr[0] > 0 else 80.0
    _tasa_deg_calc   = max(0.0, -_slope / _pr_inicial * 100.0)
    _tasa_deg_abs_pp = -_slope  # puntos porcentuales por año

    # Guardar para Financiero
    st.session_state["tasa_degradacion_calculada"] = round(_tasa_deg_calc, 2)

    # Métricas
    _dm1, _dm2, _dm3 = st.columns(3)
    _dm1.metric(
        "Pendiente PR",
        f"{_slope:+.3f} pp/año",
        help="Cambio absoluto en PR por año (puntos porcentuales)",
    )
    _dm2.metric(
        "Tasa de degradación calculada",
        f"{_tasa_deg_calc:.2f}%/año",
        delta="→ disponible en 💰 Financiero",
        delta_color="off",
        help="Relativa al PR inicial. Se usa en el cálculo de TIR/VPN.",
    )
    _años_hasta_70 = (
        int((_pr_inicial - 70.0) / max(0.001, -_slope))
        if _slope < 0 else None
    )
    _dm3.metric(
        "Vida útil (PR > 70%)",
        f"{_años_hasta_70} años" if _años_hasta_70 is not None else "PR estable",
        help="Años hasta que el sistema alcance un PR_corr_T del 70%.",
    )

    # Gráfica de tendencia
    _x_fit = _np_deg.linspace(_años_arr.min(), _años_arr.max(), 80)
    _y_fit = _slope * _x_fit + _intercept
    _fig_deg = go.Figure()
    _fig_deg.add_trace(go.Scatter(
        x=_años_arr.tolist(), y=_prs_arr.tolist(),
        mode="markers", name="PR_corr_T real",
        marker=dict(size=12, color="#1565C0",
                    line=dict(width=2, color="white")),
        hovertemplate="Año %{x:.0f}: <b>%{y:.1f}%</b><extra></extra>",
    ))
    _fig_deg.add_trace(go.Scatter(
        x=_x_fit.tolist(), y=_y_fit.tolist(),
        mode="lines",
        name=f"Tendencia lineal ({_slope:+.3f} pp/año)",
        line=dict(color="#C62828", dash="dash", width=2.5),
    ))
    _fig_deg.update_layout(
        height=320,
        xaxis=dict(title="Año", tickformat="d"),
        yaxis=dict(
            title="PR corregido T° (%)",
            range=[max(50.0, float(_prs_arr.min()) - 5.0),
                   min(105.0, float(_prs_arr.max()) + 5.0)],
        ),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=-0.30),
        title=dict(
            text="<b>Tendencia de degradación del sistema BIPV</b>",
            x=0.5, xanchor="center",
        ),
        margin=dict(b=80),
    )
    st.plotly_chart(_fig_deg, use_container_width=True)

    if _slope < -0.001:
        st.info(
            f"📉 **Degradación detectada: {_tasa_deg_calc:.2f}%/año** "
            f"({_tasa_deg_abs_pp:+.3f} pp/año absolutos). "
            "La tasa calculada está disponible en 💰 Financiero — "
            "activa el interruptor 'Usar degradación del historial real'."
        )
    else:
        st.success(
            "✅ **No se detecta degradación significativa** — PR estable o en mejora. "
            "Posible causa: mejora en limpieza/mantenimiento entre años."
        )

    # ── Exportar reporte PDF ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📄 Exportar reporte")
    st.caption(
        "Genera un PDF técnico con los datos del proyecto, configuración del sistema, "
        "métricas IEC 61724 y (si ya ejecutaste 💰 Financiero) los indicadores financieros."
    )
    if st.button("📄 Exportar reporte PDF", use_container_width=True):
        try:
            from utils.generador_reporte import generar_pdf, nombre_archivo
            with st.spinner("Generando PDF..."):
                pdf_bytes = generar_pdf(dict(st.session_state))
            st.download_button(
                label="⬇️ Descargar reporte PDF",
                data=pdf_bytes,
                file_name=nombre_archivo(dict(st.session_state)),
                mime="application/pdf",
                use_container_width=True,
            )
        except ImportError as e:
            st.error(f"❌ fpdf2 no está instalado: {e}. Ejecuta `pip install fpdf2` en el servidor.")
        except Exception as e:
            st.error(f"❌ Error al generar el PDF: {e}")
