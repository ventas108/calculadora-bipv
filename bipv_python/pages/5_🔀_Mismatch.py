"""Página 5 — Mismatch y pérdidas de sombreado."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import pvlib

from calculos.mismatch import (
    calcular_sombreado_horizonte,
    calcular_mismatch_orientacion,
    cascada_perdidas,
    factor_global_perdidas,
)
from calculos.mismatch_bypass import (
    cargar_csv_fs,
    alinear_fs_con_tmy,
    simular_bypass_horario,
    estadisticas_fs,
)
from calculos.solar import calcular_poa, ORIENTACIONES
from datos.ciudades_colombia import CIUDADES
from datos.tecnologias_bipv import MODULOS_BIPV

st.set_page_config(page_title="Mismatch — BIPV", page_icon="🔀", layout="wide")
st.title("🔀 Mismatch y Pérdidas de Sombreado")
st.caption(
    "Sombreado de horizonte · Mismatch por orientación múltiple · "
    "Fabricación · Suciedad · Cableado DC"
)

# ── Prerequisitos ─────────────────────────────────────────────────────────────
if not st.session_state.get("recurso_solar_ok"):
    st.warning("⚠️ Primero ejecuta ☀️ Recurso Solar para obtener el TMY y la POA del sitio.")
    st.stop()

tmy       = st.session_state["tmy_df"]
poa_base  = st.session_state["poa_df"]
ciudad    = st.session_state.get("tmy_ciudad", "—")
c         = CIUDADES[ciudad]
lat, lon, alt_m = c["lat"], c["lon"], c["alt_m"]
poa_anual = st.session_state.get("poa_anual_kWh_m2", 0.0)
tilt_def  = st.session_state.get("tilt_fachada", 90)
az_def    = st.session_state.get("azimuth_fachada", 0)
or_label  = st.session_state.get("orientacion_label", "Norte (0°)")

st.info(
    f"📍 **{ciudad}** — POA fachada {or_label} / {tilt_def}°: "
    f"**{poa_anual:,.0f} kWh/m²/año**"
)

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — SOMBREADO DE HORIZONTE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🏙️ 1. Sombreado de horizonte")
st.markdown(
    """
Define el **perfil de obstrucciones** que rodean la fachada BIPV — edificios vecinos, árboles,
cornisas, etc. Para cada obstáculo ingresa:

- **Azimuth**: dirección desde la fachada hacia el obstáculo (0°=Norte, 90°=Este, 180°=Sur, 270°=Oeste)
- **Ángulo de elevación**: ángulo vertical del borde superior del obstáculo desde el nivel del array

> 💡 *Regla práctica*: `elevación ≈ arctan(altura_obstáculo / distancia_horizontal)`.
> Un edificio de 15 m a 30 m de distancia → elevación ≈ 26°.
"""
)

# ── Tabla editable de obstáculos ──────────────────────────────────────────────
col_tbl, col_ayuda = st.columns([2, 1])

with col_ayuda:
    st.markdown("**Ejemplos de elevación:**")
    ejemplos = pd.DataFrame({
        "Obstáculo":    ["Edificio 3 pisos (15m) a 10m", "Edificio 5 pisos (20m) a 30m",
                         "Árbol (8m) a 20m", "Cornisa (3m) a 5m"],
        "Elevación (°)": [56, 34, 22, 31],
    })
    st.dataframe(ejemplos, hide_index=True, use_container_width=True)
    st.caption("elevación = arctan(h/d) × 180/π")

with col_tbl:
    horizonte_default = pd.DataFrame({
        "Azimuth (°)": [0, 45, 90, 135, 180, 225, 270, 315],
        "Elevación obstáculo (°)": [0, 0, 0, 0, 0, 0, 0, 0],
    })

    if "horizonte_df" not in st.session_state:
        st.session_state["horizonte_df"] = horizonte_default.copy()

    horizonte_editado = st.data_editor(
        st.session_state["horizonte_df"],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Azimuth (°)": st.column_config.NumberColumn(
                "Azimuth (°)",
                min_value=0, max_value=359, step=1,
                help="0=Norte, 90=Este, 180=Sur, 270=Oeste",
            ),
            "Elevación obstáculo (°)": st.column_config.NumberColumn(
                "Elevación obstáculo (°)",
                min_value=0, max_value=85, step=1,
                help="Ángulo vertical del tope del obstáculo",
            ),
        },
        key="editor_horizonte",
    )
    st.session_state["horizonte_df"] = horizonte_editado

# ── Diagrama panorámico de trayectoria solar ──────────────────────────────────
st.subheader("🌞 Diagrama de trayectoria solar y horizonte")

@st.cache_data(show_spinner=False)
def _solar_path_diario(lat, lon, alt_m):
    """Posiciones solares horarias para cada mes (1 día representativo/mes)."""
    loc = pvlib.location.Location(latitude=lat, longitude=lon, altitude=alt_m, tz="UTC")
    dias_rep = pd.date_range("2001-01-15", periods=12, freq="MS") + pd.Timedelta(days=14)
    frames = []
    for dia in dias_rep:
        times = pd.date_range(dia, dia + pd.Timedelta(hours=23), freq="h", tz="UTC")
        sp    = loc.get_solarposition(times)
        sp["mes"] = dia.month
        frames.append(sp[sp["apparent_elevation"] > 0])
    return pd.concat(frames)

solar_path = _solar_path_diario(lat, lon, alt_m)

# Parsear horizonte editado
puntos_horizonte = []
for _, row in horizonte_editado.dropna().iterrows():
    az  = float(row["Azimuth (°)"])
    elv = float(row["Elevación obstáculo (°)"])
    if elv > 0:
        puntos_horizonte.append((az, elv))

nombres_meses = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                 7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
colores_meses = px.colors.qualitative.Set3[:12]

fig_sp = go.Figure()

# Trayectorias solares por mes
for mes, grp in solar_path.groupby("mes"):
    fig_sp.add_trace(go.Scatter(
        x=grp["azimuth"],
        y=grp["apparent_elevation"],
        mode="lines",
        name=nombres_meses[mes],
        line=dict(color=colores_meses[mes - 1], width=1.5),
        opacity=0.75,
        showlegend=True,
    ))

# Perfil de horizonte
az_linspace = np.linspace(0, 360, 721)
if puntos_horizonte:
    from calculos.mismatch import _interpolar_horizonte
    el_horizonte = _interpolar_horizonte(puntos_horizonte, az_linspace)
    fig_sp.add_trace(go.Scatter(
        x=np.concatenate([az_linspace, [360]]),
        y=np.concatenate([el_horizonte, [el_horizonte[0]]]),
        fill="tozeroy",
        fillcolor="rgba(139,90,43,0.30)",
        mode="lines",
        line=dict(color="saddlebrown", width=2),
        name="Horizonte obstáculos",
    ))
else:
    fig_sp.add_trace(go.Scatter(
        x=[0, 360], y=[0, 0],
        mode="lines",
        line=dict(color="saddlebrown", width=1.5, dash="dot"),
        name="Horizonte (sin obstáculos)",
    ))

fig_sp.update_layout(
    height=420,
    xaxis=dict(
        title="Azimuth (°) — 0=Norte, 90=Este, 180=Sur, 270=Oeste",
        tickvals=[0, 45, 90, 135, 180, 225, 270, 315, 360],
        ticktext=["N (0°)","NE","E (90°)","SE","S (180°)","SO","O (270°)","NO","N (360°)"],
        range=[0, 360],
    ),
    yaxis=dict(title="Elevación solar (°)", range=[0, 80]),
    legend=dict(orientation="h", y=-0.25, x=0, font_size=11),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(b=100),
)
st.plotly_chart(fig_sp, use_container_width=True)
st.caption(
    "Zona marrón = horizonte bloqueado por obstáculos. "
    "Las horas donde la trayectoria solar queda por debajo del horizonte son sombreadas."
)

# ── Botón calcular sombreado ──────────────────────────────────────────────────
btn_sombra = st.button(
    "🏙️ Calcular pérdidas por sombreado", type="primary", use_container_width=True
)

if btn_sombra or st.session_state.get("sombra_ok"):
    if btn_sombra:
        with st.spinner("Calculando sombreado horario sobre TMY completo..."):
            res_sombra = calcular_sombreado_horizonte(
                lat, lon, alt_m, tmy, poa_base, puntos_horizonte
            )
        st.session_state["res_sombra"]  = res_sombra
        st.session_state["sombra_ok"]   = True
        st.session_state["puntos_horiz"] = puntos_horizonte
    else:
        res_sombra       = st.session_state.get("res_sombra", {})
        puntos_horizonte = st.session_state.get("puntos_horiz", [])

    if res_sombra:
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("POA bruta",            f"{poa_anual:.0f} kWh/m²")
        sc2.metric("Pérdida sombreado",    f"{res_sombra['energia_perdida_kWh_m2']:.1f} kWh/m²",
                   delta=f"-{res_sombra['factor_sombra_anual']*100:.1f}%",
                   delta_color="inverse")
        sc3.metric("Horas sombreadas/año", f"{res_sombra['horas_sombreadas']} h")
        sc4.metric("Factor de sombreado",
                   f"{res_sombra['factor_sombra_anual']*100:.1f}%",
                   help="Fracción de la energía POA perdida por sombreado")

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — MISMATCH POR ORIENTACIÓN MÚLTIPLE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🧭 2. Mismatch por orientación múltiple")
st.markdown(
    "Si el sistema BIPV abarca **varias fachadas con distinto azimuth** y los módulos "
    "de orientaciones diferentes están conectados **en el mismo string**, se produce una "
    "pérdida por diferencia de corriente (mismatch). Define cada grupo de módulos:"
)

multi_orient = st.toggle(
    "Tengo módulos en fachadas con distintas orientaciones en el mismo string",
    value=st.session_state.get("multi_orient", False),
    key="toggle_multi_orient",
)
st.session_state["multi_orient"] = multi_orient

res_mismatch_or = None

if multi_orient:
    n_orientaciones = st.radio(
        "¿Cuántas orientaciones distintas?",
        [2, 3], horizontal=True,
        index=0,
    )

    configs = []
    cols_or = st.columns(n_orientaciones)
    fracciones_validas = True

    orientaciones_lista = list(ORIENTACIONES.keys())

    for i, col in enumerate(cols_or):
        with col:
            st.markdown(f"**Fachada {i+1}**")
            lbl = st.selectbox(
                f"Orientación {i+1}",
                orientaciones_lista,
                index=i % len(orientaciones_lista),
                key=f"or_label_{i}",
            )
            tlt = st.slider(
                f"Inclinación {i+1} (°)",
                0, 90, tilt_def, key=f"or_tilt_{i}",
            )
            frac = st.number_input(
                f"Fracción de módulos {i+1} (0–1)",
                min_value=0.01, max_value=1.0,
                value=round(1.0 / n_orientaciones, 2),
                step=0.05,
                key=f"or_frac_{i}",
            )
            configs.append({
                "label":   lbl,
                "azimuth": ORIENTACIONES[lbl],
                "tilt":    tlt,
                "fraccion": frac,
            })

    suma_fracs = sum(c["fraccion"] for c in configs)
    if abs(suma_fracs - 1.0) > 0.05:
        st.warning(f"⚠️ La suma de fracciones es {suma_fracs:.2f} — debería ser 1.00. Ajusta los valores.")
        fracciones_validas = False
    else:
        st.success(f"✅ Suma de fracciones: {suma_fracs:.2f}")

    if fracciones_validas:
        btn_mismatch_or = st.button(
            "🧭 Calcular mismatch de orientación", type="primary", use_container_width=True
        )
        if btn_mismatch_or or st.session_state.get("mismatch_or_ok"):
            if btn_mismatch_or:
                with st.spinner("Calculando POA por orientación y factor de mismatch..."):
                    res_mismatch_or = calcular_mismatch_orientacion(
                        tmy, lat, lon, alt_m, configs
                    )
                st.session_state["res_mismatch_or"] = res_mismatch_or
                st.session_state["mismatch_or_ok"]  = True
            else:
                res_mismatch_or = st.session_state.get("res_mismatch_or", {})

            if res_mismatch_or:
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("POA media ponderada",  f"{res_mismatch_or['energia_ideal_kWh_m2']:.0f} kWh/m²")
                mc2.metric("Pérdida mismatch or.", f"{res_mismatch_or['energia_perdida_kWh_m2']:.1f} kWh/m²",
                           delta=f"-{res_mismatch_or['factor_mismatch_pct']:.2f}%",
                           delta_color="inverse")
                mc3.metric("Factor mismatch",      f"{res_mismatch_or['factor_mismatch_pct']:.2f}%",
                           help="σ²/(2μ²) — PVsyst 1er orden")

                # Tabla POA por orientación
                df_poas = pd.DataFrame(res_mismatch_or["poas"])
                df_poas.columns = ["Fachada","Azimuth (°)","Inclinación (°)","Fracción","POA anual (kWh/m²)"]
                st.dataframe(df_poas.style.format({"Fracción": "{:.2f}", "POA anual (kWh/m²)": "{:.1f}"}),
                             use_container_width=True)
else:
    st.info("Sin mismatch de orientación — todos los módulos están en la misma fachada.")
    res_mismatch_or = {"factor_mismatch_pct": 0.0, "energia_perdida_kWh_m2": 0.0}
    st.session_state["res_mismatch_or"] = res_mismatch_or

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — PÉRDIDAS SIMPLES
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚙️ 3. Otras pérdidas del sistema")

col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    pct_mismatch_fab = st.slider(
        "🔩 Mismatch de fabricación (%)",
        min_value=0.0, max_value=3.0,
        value=st.session_state.get("pct_mismatch_fab", 1.0),
        step=0.1,
        help="Diferencias entre módulos del mismo lote. IEC 61215: 0.5–2%. Típico BIPV: 1.0–1.5%.",
    )
    st.caption("Tolerancias de ±3% en Pmax generan ~1% de pérdida")

with col_s2:
    pct_soiling = st.slider(
        "🌫️ Suciedad — Soiling (%)",
        min_value=0.0, max_value=6.0,
        value=st.session_state.get("pct_soiling", 2.0),
        step=0.5,
        help="Polvo y suciedad en el vidrio. Colombia urbana: 1.5–3%. Sin limpieza periódica: hasta 5%.",
    )
    st.caption("Reducir con limpieza cada 2–3 meses")

with col_s3:
    pct_cableado = st.slider(
        "🔌 Cableado DC (%)",
        min_value=0.0, max_value=4.0,
        value=st.session_state.get("pct_cableado", 1.5),
        step=0.5,
        help="Pérdidas óhmicas en cables DC. Buena práctica: <1.5%. Instalaciones largas: hasta 3%.",
    )
    st.caption("Minimizar con sección de cable adecuada")

# Guardar sliders en session_state
st.session_state["pct_mismatch_fab"] = pct_mismatch_fab
st.session_state["pct_soiling"]      = pct_soiling
st.session_state["pct_cableado"]     = pct_cableado

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — CASCADA DE PÉRDIDAS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📉 4. Cascada de pérdidas — POA bruta → POA efectiva")

# Recuperar factores calculados
sombra_ok     = st.session_state.get("sombra_ok", False)
mismatch_or_r = st.session_state.get("res_mismatch_or", {"factor_mismatch_pct": 0.0})
sombra_r      = st.session_state.get("res_sombra",      {"factor_sombra_anual": 0.0})

factor_sombra_anual   = sombra_r.get("factor_sombra_anual", 0.0)
factor_mismatch_or_pct = mismatch_or_r.get("factor_mismatch_pct", 0.0)

if not sombra_ok:
    st.info(
        "💡 Calcula el sombreado de horizonte (sección 1) para incluirlo en la cascada. "
        "Puedes ejecutar la cascada igualmente con factor_sombra = 0."
    )

btn_cascada = st.button(
    "📉 Calcular cascada completa de pérdidas", type="primary", use_container_width=True
)

if btn_cascada or st.session_state.get("cascada_ok"):
    cascada = cascada_perdidas(
        poa_bruta_kWh_m2       = poa_anual,
        factor_sombra          = factor_sombra_anual,
        factor_mismatch_orient = factor_mismatch_or_pct,
        pct_mismatch_fab       = pct_mismatch_fab,
        pct_soiling            = pct_soiling,
        pct_cableado           = pct_cableado,
    )
    fg = factor_global_perdidas(cascada)
    st.session_state["cascada_mismatch"] = cascada
    st.session_state["factor_global_mismatch"] = fg
    st.session_state["cascada_ok"] = True

    # ── Waterfall chart ──────────────────────────────────────────────────────
    etapas     = [r["etapa"]   for r in cascada]
    energias   = [r["energia"] for r in cascada]
    perdidas   = [r["perdida"] for r in cascada]

    # Plotly waterfall
    measures = []
    y_vals   = []
    for r in cascada:
        if r["etapa"] in ("POA bruta", "POA efectiva final"):
            measures.append("absolute")
            y_vals.append(r["energia"])
        else:
            measures.append("relative")
            y_vals.append(-r["perdida"])

    fig_wf = go.Figure(go.Waterfall(
        orientation  = "v",
        measure      = measures,
        x            = etapas,
        y            = y_vals,
        connector    = dict(line=dict(color="rgb(63,63,63)", dash="dot")),
        decreasing   = dict(marker_color="#E05252"),
        increasing   = dict(marker_color="#5B9BD5"),
        totals       = dict(marker_color="#2E7D32"),
        text         = [f"{abs(v):.1f}" for v in y_vals],
        textposition = "outside",
        hovertemplate = "<b>%{x}</b><br>kWh/m²: %{y:.1f}<extra></extra>",
    ))
    fig_wf.update_layout(
        yaxis_title  = "Irradiancia POA (kWh/m²/año)",
        height       = 450,
        plot_bgcolor = "white",
        paper_bgcolor= "white",
        showlegend   = False,
        margin       = dict(t=40),
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    # ── Métricas finales ──────────────────────────────────────────────────────
    poa_efectiva = next(r["energia"] for r in cascada if r["etapa"] == "POA efectiva final")
    perdida_total = poa_anual - poa_efectiva

    cm1, cm2, cm3, cm4 = st.columns(4)
    cm1.metric("POA bruta",        f"{poa_anual:.0f} kWh/m²")
    cm2.metric("POA efectiva",     f"{poa_efectiva:.0f} kWh/m²")
    cm3.metric("Pérdida total",    f"{perdida_total:.0f} kWh/m²",
               delta=f"-{perdida_total/poa_anual*100:.1f}%", delta_color="inverse")
    cm4.metric("Factor global PR",  f"{fg*100:.1f}%",
               help="Performance Ratio de pérdidas ópticas y eléctricas (sin temperatura)")

    # ── Tabla detalle ─────────────────────────────────────────────────────────
    with st.expander("📋 Ver tabla detallada de la cascada"):
        df_casc = pd.DataFrame(cascada)
        df_casc.columns = ["Etapa", "Energía (kWh/m²)", "Pérdida (kWh/m²)", "% sobre POA bruta"]
        st.dataframe(
            df_casc.style.format({
                "Energía (kWh/m²)":    "{:.2f}",
                "Pérdida (kWh/m²)":    "{:.2f}",
                "% sobre POA bruta": "{:.2f}%",
            }).background_gradient(subset=["Pérdida (kWh/m²)"], cmap="Reds", low=0, high=1),
            use_container_width=True,
        )

    st.success(
        f"✅ Cascada calculada para **{ciudad}** | "
        f"POA efectiva: **{poa_efectiva:.0f} kWh/m²/año** | "
        f"Factor global PR: **{fg*100:.1f}%** | "
        f"Continúa en 📊 Producción para calcular la energía generada."
    )

    # ── Guardar en session_state para Producción ──────────────────────────────
    st.session_state["poa_efectiva_kWh_m2"]       = round(poa_efectiva, 1)
    st.session_state["factor_global_mismatch"]    = fg
    st.session_state["factor_sombra_anual"]       = factor_sombra_anual
    st.session_state["factor_mismatch_or_pct"]    = factor_mismatch_or_pct
    st.session_state["mismatch_ok"]               = True

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — BYPASS DIODES · Pérdida eléctrica por sombra parcial
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚡ 5. Bypass Diodes — Pérdida eléctrica por sombra parcial")

with st.expander("ℹ️ ¿Qué son los bypass diodes y por qué importan en BIPV fachada?", expanded=False):
    st.markdown("""
Cuando una fracción de módulos en un **string** queda en sombra, su corriente cae
por debajo del punto de operación del resto. Los **bypass diodes** se activan y
cortocircuitan esos módulos → se pierde **toda su tensión V_mp**, no solo la
potencia proporcional a la irradiancia reducida.

| Método | Pérdida calculada | Error típico |
|---|---|---|
| Reducción escalar (método actual) | Irradiancia × factor | Subestima 3–8% en fachadas urbanas |
| **Modelo bypass diode** | Pérdida eléctrica real por string | Exacto para sombras parciales |

**Fuente de datos:** CSV exportado desde la Calculadora de Sombreado BIPV
(`bipv.innovacionquimica.com.co`) tras ejecutar **«Cruzar Máscara + EPW»**.
Cada «Punto de Análisis» del CSV = una fila de módulos en la fachada.
    """)

# ── Uploader CSV ─────────────────────────────────────────────────────────────
st.markdown("#### 📂 Cargar CSV de la Calculadora de Sombreado")
st.caption(
    "Exporta el CSV desde bipv.innovacionquimica.com.co → Puntos de Análisis → "
    "**Exportar CSV** (después de ejecutar «Cruzar Máscara + EPW»). "
    "Columnas requeridas: **Mes, Dia, Hora, FS**"
)

csv_file = st.file_uploader(
    "Archivo CSV con Factor de Sombreado horario",
    type=["csv"],
    key="uploader_csv_fs",
    help="CSV exportado por la Calculadora de Factor de Sombreado BIPV",
)

# Mantener CSV cargado entre reruns
if csv_file is not None:
    try:
        df_fs_raw, _meta_fs = cargar_csv_fs(csv_file)
        st.session_state["df_fs_raw"]  = df_fs_raw
        st.session_state["meta_fs"]    = _meta_fs
        st.session_state["csv_fs_ok"]  = True
    except Exception as e:
        st.error(f"❌ Error al leer el CSV: {e}")
        st.session_state["csv_fs_ok"] = False

csv_ok   = st.session_state.get("csv_fs_ok", False)
df_fs_raw = st.session_state.get("df_fs_raw", None)
meta_fs   = st.session_state.get("meta_fs", {})

if csv_ok and df_fs_raw is not None:
    # ── Banner fuente del FS ───────────────────────────────────────────────
    tipo_fs = meta_fs.get("tipo", "combinado")
    if tipo_fs == "geometrico":
        st.success(meta_fs.get("descripcion", ""))
    else:
        st.warning(meta_fs.get("descripcion", ""))
    for adv in meta_fs.get("advertencias", []):
        st.warning(f"⚠️ {adv}")

    # ── Estadísticas del CSV ──────────────────────────────────────────────
    try:
        stats = estadisticas_fs(df_fs_raw)
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Puntos de análisis", stats["n_puntos_analisis"],
                   help="Filas de módulos / posiciones en la fachada")
        sc2.metric("Timestamps en CSV",  f"{stats['n_timestamps']:,}",
                   help="Horas únicas con dato de FS")
        sc3.metric(
            f"{'FS_geom' if tipo_fs == 'geometrico' else 'FS'} medio",
            f"{stats['fs_medio']:.3f}",
            help="0 = sin sombra · 1 = sombra total — "
                 + ("solo obstáculos físicos" if tipo_fs == "geometrico" else "sombra geom. + nubes"),
        )
        sc4.metric("Horas con FS > 0",   f"{stats['horas_fs_gt0']} h",
                   help="Horas al año con algún grado de sombreado activo")

        # Gráfica FS medio por mes
        df_fs_mes = stats["df_mensual_fs"]
        fig_fs = go.Figure(go.Bar(
            x=df_fs_mes["Mes"],
            y=df_fs_mes["FS medio"],
            marker_color=[
                "#C62828" if v > 0.3 else
                "#F9A825" if v > 0.1 else
                "#43A047"
                for v in df_fs_mes["FS medio"]
            ],
            text=[f"{v:.3f}" for v in df_fs_mes["FS medio"]],
            textposition="outside",
        ))
        fig_fs.update_layout(
            title="Factor de Sombreado medio mensual (CSV importado)",
            yaxis=dict(title="FS medio [0–1]", range=[0, max(df_fs_mes["FS medio"].max() * 1.3, 0.1)]),
            xaxis_title="Mes",
            height=320,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_fs, use_container_width=True)

    except Exception as e:
        st.warning(f"No se pudo calcular estadísticas del CSV: {e}")

    st.markdown("---")

    # ── Configuración de strings ──────────────────────────────────────────
    st.markdown("#### ⚙️ Configuración de strings para el modelo bypass")

    _n_total = st.session_state.get("N_paneles_dim", 0)
    col_bp1, col_bp2, col_bp3 = st.columns(3)

    with col_bp1:
        panel_bp_nombre = st.selectbox(
            "Panel fotovoltaico",
            list(MODULOS_BIPV.keys()),
            index=list(MODULOS_BIPV.keys()).index("ASP-ST1-T40"),
            key="bypass_panel",
            help="Debe coincidir con el panel de Producción",
        )
        panel_bp = MODULOS_BIPV[panel_bp_nombre]

    with col_bp2:
        n_series_default = 8
        # Inferir N_series desde dimensionamiento si hay datos
        if _n_total > 0:
            # Módulos típicos en serie para tensión 300-600V con paneles ~80-100Voc
            Voc_stc = panel_bp.get("Voc_stc", 100.0)
            # Apuntar a ~400V DC → N_series ≈ 400 / Voc_stc
            n_series_default = max(4, min(20, int(round(400 / Voc_stc))))

        N_series_bp = st.number_input(
            "Módulos en serie por string (N_series)",
            min_value=2, max_value=30,
            value=n_series_default,
            step=1,
            key="bypass_n_series",
            help="Número de módulos conectados en serie en cada string",
        )

    with col_bp3:
        if _n_total > 0 and N_series_bp > 0:
            n_par_default = max(1, round(_n_total / N_series_bp))
        else:
            n_par_default = 4
        N_parallel_bp = st.number_input(
            "Strings en paralelo (N_parallel)",
            min_value=1, max_value=200,
            value=n_par_default,
            step=1,
            key="bypass_n_parallel",
            help="Número de strings en paralelo en el array",
        )
        st.caption(
            f"Total módulos: **{N_series_bp * N_parallel_bp}**"
            + (f" (dimensionamiento: {_n_total})" if _n_total > 0 else "")
        )

    # ── POA base para el cálculo ──────────────────────────────────────────
    _motor_ok = st.session_state.get("motor_optico_ok", False)
    _mismatch_factor = st.session_state.get("factor_global_mismatch", 1.0)
    if _motor_ok:
        poa_bp = st.session_state["poa_efectiva_df"]["poa_global"].values
        poa_src = "Motor Óptico (IAM + Soiling + Térmico)"
    else:
        poa_bp = st.session_state["poa_df"]["poa_global"].values * _mismatch_factor
        poa_src = f"POA bruta × factor mismatch ({_mismatch_factor*100:.1f}%)"

    T_amb_bp = tmy["T2m"].values
    st.caption(f"📡 POA de referencia: **{poa_src}**")

    # ── Botón de simulación ───────────────────────────────────────────────
    btn_bypass = st.button(
        "⚡ Calcular pérdida real por bypass diodes",
        type="primary",
        use_container_width=True,
        key="btn_bypass",
    )

    if btn_bypass or st.session_state.get("bypass_ok"):
        if btn_bypass:
            with st.spinner("Alineando FS con TMY y simulando bypass diodes hora a hora..."):
                try:
                    # Alinear FS con el TMY
                    tmy_idx  = st.session_state["tmy_df"].index
                    p_shade  = alinear_fs_con_tmy(df_fs_raw, tmy_idx)

                    # Simular bypass
                    res_bp = simular_bypass_horario(
                        G_eff      = poa_bp,
                        T_amb      = T_amb_bp,
                        p_shade    = p_shade.values,
                        N_series   = int(N_series_bp),
                        N_parallel = int(N_parallel_bp),
                        panel      = panel_bp,
                        NOCT       = float(panel_bp.get("NOCT", 45.0)),
                        umbral_shade = 0.05,
                    )
                    st.session_state["bypass_result"]     = res_bp
                    st.session_state["bypass_p_shade"]    = p_shade
                    st.session_state["bypass_n_series"]   = int(N_series_bp)
                    st.session_state["bypass_n_parallel"] = int(N_parallel_bp)
                    st.session_state["bypass_panel"]      = panel_bp_nombre
                    st.session_state["bypass_ok"]         = True
                except Exception as e:
                    st.error(f"❌ Error en simulación bypass: {e}")
                    st.session_state["bypass_ok"] = False

        res_bp = st.session_state.get("bypass_result", {})

        if res_bp:
            # ── Métricas resumen ───────────────────────────────────────────
            bp1, bp2, bp3, bp4 = st.columns(4)
            bp1.metric(
                "Pérdida DC por bypass",
                f"{res_bp['kwh_bypass_anual']:,.0f} kWh/año",
                delta=f"-{res_bp['pct_bypass_anual']:.2f}% de E_dc",
                delta_color="inverse",
                help="Energía DC adicional perdida por activación de bypass diodes",
            )
            bp2.metric(
                "Horas con bypass activo",
                f"{res_bp['horas_bypass']} h/año",
                help="Horas al año donde al menos un bypass diode se activa",
            )
            bp3.metric(
                "Horas con sombra (FS > 5%)",
                f"{res_bp['horas_sombra']} h/año",
                help="Horas con sombra activa en el CSV cargado",
            )
            bp4.metric(
                "E_dc con bypass",
                f"{res_bp['kwh_dc_uniforme'] - res_bp['kwh_bypass_anual']:,.0f} kWh/año",
                help="Producción DC real considerando bypass diodes",
            )

            # ── Gráfica mensual ────────────────────────────────────────────
            df_m_bp = res_bp["df_mensual_bypass"]

            fig_bp = go.Figure()
            fig_bp.add_trace(go.Bar(
                name="Producción DC con bypass (kWh)",
                x=df_m_bp.index,
                y=df_m_bp["E_dc con bypass (kWh)"].round(0),
                marker_color="#2E7D32",
                opacity=0.85,
            ))
            fig_bp.add_trace(go.Bar(
                name="Pérdida bypass diodes (kWh)",
                x=df_m_bp.index,
                y=df_m_bp["Pérdida bypass (kWh)"].round(0),
                marker_color="#C62828",
                opacity=0.80,
                text=df_m_bp["Pérdida bypass (kWh)"].apply(
                    lambda v: f"{v:,.0f}" if v > 1 else ""
                ),
                textposition="outside",
            ))
            fig_bp.update_layout(
                barmode="stack",
                title="Producción DC mensual con bypass diodes",
                yaxis_title="Energía (kWh)",
                xaxis_title="Mes",
                height=360,
                plot_bgcolor="white",
                paper_bgcolor="white",
                legend=dict(orientation="h", y=-0.25),
                margin=dict(b=80),
            )
            st.plotly_chart(fig_bp, use_container_width=True)

            # ── Horas de bypass por mes ────────────────────────────────────
            fig_h = go.Figure()
            fig_h.add_trace(go.Bar(
                name="Horas sombra activa",
                x=df_m_bp.index,
                y=df_m_bp["Horas con sombra"].round(0),
                marker_color="#BDBDBD",
                opacity=0.70,
            ))
            fig_h.add_trace(go.Bar(
                name="Horas bypass activo",
                x=df_m_bp.index,
                y=df_m_bp["Horas bypass activo"].round(0),
                marker_color="#E65100",
                opacity=0.85,
                text=df_m_bp["Horas bypass activo"].apply(
                    lambda v: f"{v:.0f}h" if v > 0 else ""
                ),
                textposition="outside",
            ))
            fig_h.update_layout(
                barmode="group",
                title="Horas de sombra vs horas con bypass diode activo",
                yaxis_title="Horas / mes",
                xaxis_title="Mes",
                height=300,
                plot_bgcolor="white",
                paper_bgcolor="white",
                legend=dict(orientation="h", y=-0.30),
                margin=dict(b=80),
            )
            st.plotly_chart(fig_h, use_container_width=True)

            # ── Tabla mensual detallada ────────────────────────────────────
            with st.expander("📋 Ver tabla mensual completa de bypass diodes"):
                df_show = df_m_bp.copy()
                df_show["FS medio mensual"] = df_show["FS medio mensual"].round(3)
                st.dataframe(
                    df_show.style.format({
                        "E_dc con bypass (kWh)":  "{:,.0f}",
                        "Pérdida bypass (kWh)":   "{:,.1f}",
                        "FS medio mensual":        "{:.3f}",
                        "Horas bypass activo":     "{:.0f}",
                        "Horas con sombra":        "{:.0f}",
                    }).background_gradient(subset=["Pérdida bypass (kWh)"], cmap="Reds"),
                    use_container_width=True,
                )

            # ── Diagnóstico automático ─────────────────────────────────────
            pct = res_bp["pct_bypass_anual"]
            if pct > 5.0:
                st.error(
                    f"🔴 **Pérdida por bypass diodes: {pct:.2f}%** — "
                    "Supera el 5% de la producción DC. La sombra parcial tiene un "
                    "impacto significativo. Considerar:\n"
                    "- Reorganizar strings para agrupar módulos con igual patrón de sombra\n"
                    "- Añadir optimizadores de módulo (SolarEdge, Tigo) en las filas críticas\n"
                    "- Verificar si el diseño de fachada puede reducir la sombra en horas pico"
                )
            elif pct > 2.0:
                st.warning(
                    f"🟡 **Pérdida por bypass diodes: {pct:.2f}%** — "
                    "Moderada (2–5%). Revisar si los strings más afectados pueden "
                    "separarse en ramas de MPPT independientes del inversor."
                )
            else:
                st.success(
                    f"🟢 **Pérdida por bypass diodes: {pct:.2f}%** — "
                    "Baja (<2%). Las sombras parciales tienen impacto eléctrico controlado. "
                    f"({res_bp['horas_bypass']} horas/año con bypass activo)"
                )

            _tipo_fs_res = meta_fs.get("tipo", "combinado")
            _col_fs_res  = meta_fs.get("col_original", "FS")
            _fs_badge    = (
                "🟩 FS geométrico (solo obstáculos físicos)"
                if _tipo_fs_res == "geometrico"
                else "🟨 FS combinado (geom + nubes) — puede sobreestimar bypass"
            )
            st.success(
                f"✅ Modelo bypass completado | "
                f"Pérdida adicional: **{res_bp['kwh_bypass_anual']:,.0f} kWh/año** "
                f"({res_bp['pct_bypass_anual']:.2f}% de E_dc) | "
                f"Bypass activo **{res_bp['horas_bypass']} h/año** · "
                f"Fuente FS: **{_col_fs_res}** — {_fs_badge}"
            )

elif not csv_ok:
    st.info(
        "💡 Carga el CSV exportado desde **bipv.innovacionquimica.com.co** "
        "(Calculadora de Factor de Sombreado → Puntos de Análisis → "
        "Cruzar Máscara + EPW → Exportar CSV) para calcular la pérdida "
        "real por bypass diodes con tu modelo 3D del edificio."
    )
