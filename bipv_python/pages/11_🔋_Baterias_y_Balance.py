"""
Página 11 — Baterías y Balance Energético
B-6: Dimensionado eléctrico strings + baterías
B-7: Balance energético mensual + Clasificación A+/A/B/C/D
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from datos.catalogo_baterias_excel import (
    cargar_catalogo_baterias,
    obtener_bateria,
    lista_baterias,
)
from calculos.baterias_balance import (
    dimensionar_bateria,
    balance_mensual,
    metricas_balance,
    clasificar_energia,
    distribuir_consumo_anual,
    tabla_clasificaciones,
    PERFILES_TIPICOS,
    MESES,
)

st.set_page_config(
    page_title="Baterías y Balance — BIPV",
    page_icon="🔋",
    layout="wide",
)
st.title("🔋 Baterías y Balance Energético")
st.caption(
    "B-6: Dimensionado de baterías · "
    "B-7: Balance mensual producción vs consumo · "
    "Clasificación energética A+/A/B/C/D"
)

# ── Pre-requisitos ────────────────────────────────────────────────────────────
prod_ok   = st.session_state.get("produccion_ok", False)
df_m_prod = st.session_state.get("df_mensual_produccion", None)

# Usar E_ac corregida por bypass si está disponible (#37)
_e_ac_base_bat   = float(st.session_state.get("E_ac_anual_kWh", 0.0))
_e_ac_bypass_bat = float(st.session_state.get("E_ac_anual_kWh_bypass", 0.0))
_bypass_ok_bat   = st.session_state.get("bypass_ok", False)
_kwh_bp_bat      = float(st.session_state.get("kwh_bypass_anual", 0.0))

e_ac_anual = _e_ac_bypass_bat if (_bypass_ok_bat and _e_ac_bypass_bat > 0) else _e_ac_base_bat

if not prod_ok or df_m_prod is None or e_ac_anual <= 0:
    st.warning(
        "⚠️ **Producción no calculada.** "
        "Complete primero la Página 6 — Producción Anual para obtener los datos mensuales "
        "que necesita esta página."
    )
    st.info(
        "💡 Puede continuar configurando baterías, pero el balance energético "
        "requiere los resultados de producción."
    )

# Banner bypass (#37)
if prod_ok and _bypass_ok_bat and _e_ac_bypass_bat > 0:
    st.info(
        f"⚡ **Corrección bypass activa:** "
        f"E_ac base = {_e_ac_base_bat:,.0f} kWh/año → "
        f"pérdida bypass = {_kwh_bp_bat:,.0f} kWh/año → "
        f"**E_ac usada en el balance = {e_ac_anual:,.0f} kWh/año** "
        f"({(_e_ac_base_bat - e_ac_anual) / _e_ac_base_bat * 100:.1f}% menos). "
        "La autogeneración y el dimensionamiento de la batería se calculan con la producción real."
    )
elif prod_ok and e_ac_anual > 0:
    st.caption(
        "💡 Ejecuta el modelo Bypass Diodes en Página 5 para usar la E_ac corregida "
        "por sombra parcial en este balance energético."
    )

# ══════════════════════════════════════════════════════════════════════════════
# B-6 — Dimensionado de baterías
# ══════════════════════════════════════════════════════════════════════════════
st.header("⚡ B-6 — Dimensionado de Baterías")

cat_bat = cargar_catalogo_baterias()
tiene_catalogo = len(cat_bat) > 0

col_b1, col_b2 = st.columns([1, 1])

with col_b1:
    st.subheader("Selección de batería")

    if not tiene_catalogo:
        st.error(
            "🔴 **Catálogo de baterías no encontrado.** "
            "Agregue una hoja `Catalogo_Baterias` en el archivo "
            "`inversores_catalogo.xlsx` del servidor."
        )
        with st.expander("📋 Columnas esperadas en la hoja Catalogo_Baterias"):
            st.markdown("""
| Columna | Descripción | Ejemplo |
|---|---|---|
| Modelo | Nombre del modelo | BYD Battery-Box HVM |
| Datos completos (Si/No) | Si / No | Si |
| Capacidad (kWh) | Capacidad nominal | 11.04 |
| Potencia Continua (kW) | Potencia de carga/descarga | 5.0 |
| Voltaje Nominal (V) | Tensión del bus DC | 48 |
| DoD Máximo (%) | Profundidad de descarga máxima | 90 |
| Ciclos de Vida | Ciclos garantizados a DoD nominal | 4000 |
| Eficiencia RTE (%) | Rendimiento round-trip | 96 |
| Tecnología | Química | LFP |
| Costo (USD) | Precio unitario sin IVA | 4200 |
| Garantía (años) | Años de garantía | 10 |
            """)
        usa_bateria = False
    else:
        lista = lista_baterias()
        bat_sel = st.selectbox("Batería del catálogo", lista, key="bat_nombre_sel")
        bat = obtener_bateria(bat_sel)

        # Indicador completitud
        if bat.get("datos_completos"):
            st.success("🟢 Ficha completa")
        else:
            _falt = [k for k in ["capacidad_kWh", "potencia_kW", "dod_pct", "ciclos_vida"]
                     if not bat.get(k)]
            st.warning(f"🟡 Datos incompletos — faltan: {', '.join(_falt)}" if _falt
                       else "🟡 Ficha marcada como incompleta en catálogo")

        # Ficha técnica
        with st.expander("📋 Ficha técnica del modelo seleccionado"):
            ficha = {
                "Capacidad (kWh)":      bat.get("capacidad_kWh", "—"),
                "Potencia (kW)":        bat.get("potencia_kW", "—"),
                "Voltaje nominal (V)":  bat.get("voltaje_V", "—"),
                "DoD máximo (%)":       bat.get("dod_pct", "—"),
                "Ciclos de vida":       bat.get("ciclos_vida", "—"),
                "Eficiencia RTE (%)":   bat.get("eta_rte_pct", "—"),
                "Tecnología":           bat.get("tipo", "—"),
                "Costo unitario (USD)": f"${bat.get('costo_usd', 0):,.0f}" if bat.get("costo_usd") else "—",
                "Garantía (años)":      bat.get("garantia_anos", "—"),
            }
            st.table(pd.DataFrame(ficha.items(), columns=["Parámetro", "Valor"]))

        usa_bateria = st.checkbox("✅ Incluir batería en el balance energético", value=True)

with col_b2:
    st.subheader("Parámetros de diseño")

    # Consumo diario — tomarlo de session_state o calcular desde anual
    consumo_diario_default = round(e_ac_anual / 365, 1) if e_ac_anual > 0 else 30.0
    E_consumo_diario = st.number_input(
        "Consumo diario del edificio (kWh/día)",
        min_value=1.0,
        max_value=5000.0,
        value=float(st.session_state.get("consumo_diario_kWh", consumo_diario_default)),
        step=1.0,
        help="Promedio diario. Si tiene la factura mensual, divida por 30.",
        key="consumo_diario_kWh",
    )

    autonomia_h = st.slider(
        "Autonomía deseada (horas sin sol / red)",
        min_value=1,
        max_value=48,
        value=int(st.session_state.get("autonomia_baterias_h", 4)),
        step=1,
        key="autonomia_baterias_h",
        help="Horas que la batería debe cubrir sin producción solar ni red. "
             "Valor típico: 4–8 h (respaldo nocturno). "
             "24 h = autonomía completa 1 día.",
    )

if tiene_catalogo and st.button("▶️ Dimensionar batería", type="primary"):
    if not bat.get("capacidad_kWh"):
        st.error("❌ La batería seleccionada no tiene capacidad definida en el catálogo.")
    else:
        dim = dimensionar_bateria(bat, E_consumo_diario, autonomia_h)
        if "error" in dim:
            st.error(f"❌ {dim['error']}")
        else:
            st.session_state["bateria_dim"] = dim
            st.session_state["bateria_nombre"] = bat_sel
            st.session_state["bateria_dict"] = bat
            st.session_state["bateria_ok"] = True

# Mostrar resultado del dimensionamiento
dim_res = st.session_state.get("bateria_dim")
if dim_res and not dim_res.get("error"):
    st.success(f"✅ Dimensionamiento calculado — {st.session_state.get('bateria_nombre','')}")
    bat_nom = st.session_state.get("bateria_nombre", "—")

    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("Unidades requeridas", dim_res["N_baterias"])
    col_r2.metric("Capacidad instalada", f"{dim_res['C_instalada_kWh']:.1f} kWh")
    col_r3.metric("Capacidad útil (DoD+η)", f"{dim_res['C_util_kWh']:.1f} kWh")
    col_r4.metric("Vida estimada", f"{dim_res['vida_estimada_anos']} años")

    col_r5, col_r6, col_r7, col_r8 = st.columns(4)
    col_r5.metric("DoD real de operación", f"{dim_res['dod_real_pct']:.1f}%",
                  delta=f"Máx: {dim_res['dod_max_pct']}%", delta_color="off")
    col_r6.metric("Eficiencia RTE", f"{dim_res['eta_rte_pct']:.0f}%")
    col_r7.metric("Ciclos garantizados", f"{dim_res['ciclos_vida']:,}")
    if dim_res.get("costo_total_usd"):
        col_r8.metric("Costo total baterías",
                      f"USD {dim_res['costo_total_usd']:,.0f}",
                      delta=f"USD {dim_res['costo_unitario_usd']:,.0f}/unid", delta_color="off")
    else:
        col_r8.metric("Costo total baterías", "No disponible")

    for adv in dim_res.get("advertencias", []):
        st.warning(f"⚠️ {adv}")

    with st.expander("📐 Tabla de dimensionamiento detallada"):
        tabla_dim = {
            "Parámetro":  [
                "Modelo seleccionado", "Capacidad unitaria (kWh)", "Número de unidades",
                "Capacidad instalada total (kWh)", "Capacidad útil aprovechable (kWh)",
                "DoD real de operación (%)", "DoD máximo del fabricante (%)",
                "Eficiencia round-trip (%)", "Ciclos de vida garantizados",
                "Vida estimada de operación (años)", "Costo total baterías (USD)"
            ],
            "Valor": [
                bat_nom,
                dim_res["cap_unitaria_kWh"],
                dim_res["N_baterias"],
                dim_res["C_instalada_kWh"],
                dim_res["C_util_kWh"],
                f"{dim_res['dod_real_pct']:.1f}%",
                f"{dim_res['dod_max_pct']:.0f}%",
                f"{dim_res['eta_rte_pct']:.0f}%",
                f"{dim_res['ciclos_vida']:,}",
                dim_res["vida_estimada_anos"],
                f"USD {dim_res['costo_total_usd']:,.0f}" if dim_res.get("costo_total_usd") else "—",
            ],
        }
        st.table(pd.DataFrame(tabla_dim))

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# B-7 — Balance energético mensual + Clasificación
# ══════════════════════════════════════════════════════════════════════════════
st.header("📊 B-7 — Balance Energético Mensual y Clasificación")

# ── Sección consumo ──────────────────────────────────────────────────────────
st.subheader("1️⃣ Perfil de consumo del edificio")

modo_consumo = st.radio(
    "¿Cómo desea ingresar el consumo?",
    ["Consumo anual + perfil típico", "Ingresar 12 valores mensuales manualmente"],
    horizontal=True,
    key="modo_consumo_b7",
)

if modo_consumo == "Consumo anual + perfil típico":
    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        consumo_anual_input = st.number_input(
            "Consumo anual total (kWh/año)",
            min_value=100.0,
            max_value=10_000_000.0,
            value=float(st.session_state.get("consumo_anual_edificio_kWh",
                        max(e_ac_anual * 1.2, 10000.0))),
            step=500.0,
            key="consumo_anual_edificio_kWh",
            help="Puede obtenerlo sumando 12 meses de facturas de energía.",
        )
    with col_c2:
        perfil_sel = st.selectbox(
            "Perfil de distribución mensual",
            list(PERFILES_TIPICOS.keys()),
            key="perfil_consumo_tipico",
            help="Distribución estacional del consumo. 'Uniforme' si no sabe.",
        )
    consumo_mensual_list = distribuir_consumo_anual(consumo_anual_input, perfil_sel)

else:
    st.info("Ingrese el consumo de cada mes (kWh). Puede basarse en facturas históricas.")
    cols_mes = st.columns(6)
    consumo_mensual_list = []
    defaults_mens = st.session_state.get(
        "consumo_mensual_manual",
        [round(max(e_ac_anual * 1.2, 10000) / 12, 0)] * 12
    )
    for i, mes in enumerate(MESES):
        col = cols_mes[i % 6]
        val = col.number_input(
            mes, min_value=0.0, max_value=500_000.0,
            value=float(defaults_mens[i]),
            step=100.0, key=f"cons_mes_{i}"
        )
        consumo_mensual_list.append(val)
    st.session_state["consumo_mensual_manual"] = consumo_mensual_list

# Vista previa del consumo
with st.expander("👁️ Vista previa del perfil de consumo"):
    df_cons_prev = pd.DataFrame({
        "Mes": MESES,
        "Consumo (kWh)": [round(v, 0) for v in consumo_mensual_list],
    })
    fig_cons = px.bar(df_cons_prev, x="Mes", y="Consumo (kWh)",
                      title="Perfil de consumo mensual",
                      color_discrete_sequence=["#3498db"])
    fig_cons.update_layout(height=280, margin=dict(t=40, b=20))
    st.plotly_chart(fig_cons, use_container_width=True)
    st.caption(f"Total anual: **{sum(consumo_mensual_list):,.0f} kWh/año**")

# ── Calcular balance ─────────────────────────────────────────────────────────
st.subheader("2️⃣ Calcular balance")

if st.button("▶️ Calcular balance energético mensual", type="primary",
             disabled=(df_m_prod is None)):
    if df_m_prod is None:
        st.error("❌ No hay datos de producción mensual. Complete primero la Página 6.")
    else:
        _bat_dim_activo = (st.session_state.get("bateria_dim")
                           if (usa_bateria if tiene_catalogo else False)
                              and st.session_state.get("bateria_ok")
                           else None)
        try:
            df_bal = balance_mensual(df_m_prod, consumo_mensual_list, _bat_dim_activo)
            metr   = metricas_balance(df_bal)
            clase  = clasificar_energia(metr["fraccion_solar_pct"])

            st.session_state["balance_mensual_df"]       = df_bal
            st.session_state["balance_metricas"]         = metr
            st.session_state["clasificacion_energetica"] = clase
            st.session_state["fraccion_solar_pct"]       = metr["fraccion_solar_pct"]
            st.session_state["consumo_anual_edificio_kWh_calc"] = metr["E_consumo_anual_kWh"]
            st.session_state["balance_ok"]               = True
            st.success("✅ Balance calculado correctamente")
        except Exception as e:
            st.error(f"❌ Error en el cálculo: {e}")

# ── Mostrar resultados ───────────────────────────────────────────────────────
df_bal  = st.session_state.get("balance_mensual_df")
metr    = st.session_state.get("balance_metricas")
clase   = st.session_state.get("clasificacion_energetica")

if df_bal is not None and metr and clase:

    # ── Clasificación energética ────────────────────────────────────────────
    st.divider()
    st.subheader("3️⃣ Clasificación energética del edificio")

    col_cl1, col_cl2 = st.columns([1, 2])
    with col_cl1:
        color = clase["color_hex"]
        clase_letra = clase["clase"]
        frac = clase["fraccion_solar_pct"]
        st.markdown(
            f"""
            <div style="
                background:{color}22;
                border: 3px solid {color};
                border-radius: 16px;
                padding: 24px;
                text-align: center;
            ">
                <div style="font-size:64px; font-weight:900; color:{color};">
                    {clase_letra}
                </div>
                <div style="font-size:18px; font-weight:600; color:{color}; margin-top:4px;">
                    {clase['emoji']} {clase['descripcion']}
                </div>
                <div style="font-size:28px; font-weight:700; margin-top:12px;">
                    {frac:.1f}%
                </div>
                <div style="font-size:13px; color:#666;">
                    fracción solar (% consumo cubierto)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_cl2:
        st.markdown("**Tabla de clasificaciones energéticas**")
        df_clases = tabla_clasificaciones()
        # Resaltar la fila activa
        def _highlight_row(row):
            if row["Clase"].endswith(clase_letra) or clase_letra in row["Clase"]:
                return [f"background-color:{color}33; font-weight:bold"] * len(row)
            return [""] * len(row)
        st.dataframe(df_clases.style.apply(_highlight_row, axis=1),
                     use_container_width=True, hide_index=True)

    # ── KPIs anuales ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("4️⃣ Indicadores anuales del balance")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Producción solar",
              f"{metr['E_solar_anual_kWh']:,.0f} kWh/año")
    k2.metric("Consumo edificio",
              f"{metr['E_consumo_anual_kWh']:,.0f} kWh/año")
    k3.metric("Autoconsumo solar",
              f"{metr['E_autoconsumo_anual_kWh']:,.0f} kWh/año",
              delta=f"{metr['fraccion_solar_pct']:.1f}% del consumo")
    k4.metric("Excedente exportado",
              f"{metr['E_exportacion_anual_kWh']:,.0f} kWh/año",
              delta=f"{metr['tasa_autoconsumo_pct']:.1f}% autoc. solar")
    k5.metric("Déficit residual",
              f"{metr['E_deficit_anual_kWh']:,.0f} kWh/año",
              delta=f"Ratio solar/consumo: {metr['ratio_solar_consumo']:.2f}x",
              delta_color="off")

    if metr.get("E_bateria_total_kWh", 0) > 0:
        st.info(
            f"🔋 **Contribución batería:** {metr['E_bateria_total_kWh']:,.0f} kWh/año "
            f"(energía descargada que cubre consumo nocturno/déficit)"
        )

    # ── Gráfico de balance mensual ───────────────────────────────────────────
    st.divider()
    st.subheader("5️⃣ Balance mensual — Producción vs Consumo")

    fig = go.Figure()

    # Barras apiladas del autoconsumo
    fig.add_trace(go.Bar(
        name="Autoconsumo directo (solar→edificio)",
        x=df_bal["mes"], y=df_bal["autoconsumo_directo_kWh"],
        marker_color="#27ae60",
        hovertemplate="%{y:,.0f} kWh<extra>Autoconsumo directo</extra>",
    ))
    if df_bal["E_bateria_descargada_kWh"].sum() > 0:
        fig.add_trace(go.Bar(
            name="Batería → edificio",
            x=df_bal["mes"], y=df_bal["E_bateria_descargada_kWh"],
            marker_color="#2ecc71",
            hovertemplate="%{y:,.0f} kWh<extra>Batería → edificio</extra>",
        ))
    fig.add_trace(go.Bar(
        name="Déficit (de la red)",
        x=df_bal["mes"], y=df_bal["deficit_neto_kWh"],
        marker_color="#e74c3c",
        hovertemplate="%{y:,.0f} kWh<extra>Déficit (red)</extra>",
    ))
    fig.add_trace(go.Bar(
        name="Excedente exportado",
        x=df_bal["mes"], y=df_bal["exportacion_kWh"],
        marker_color="#f39c12", opacity=0.7,
        hovertemplate="%{y:,.0f} kWh<extra>Excedente exportado</extra>",
    ))

    # Línea de consumo total
    fig.add_trace(go.Scatter(
        name="Consumo edificio",
        x=df_bal["mes"], y=df_bal["E_consumo_kWh"],
        mode="lines+markers",
        line=dict(color="#2c3e50", width=2.5, dash="dot"),
        marker=dict(size=7),
        hovertemplate="%{y:,.0f} kWh<extra>Consumo</extra>",
    ))

    # Línea de producción solar
    fig.add_trace(go.Scatter(
        name="Producción solar (E_ac)",
        x=df_bal["mes"], y=df_bal["E_solar_kWh"],
        mode="lines+markers",
        line=dict(color="#e67e22", width=2.5),
        marker=dict(size=7, symbol="diamond"),
        hovertemplate="%{y:,.0f} kWh<extra>Producción solar</extra>",
    ))

    fig.update_layout(
        barmode="stack",
        title="Balance energético mensual — Autoconsumo · Déficit · Excedente",
        xaxis_title="Mes",
        yaxis_title="Energía (kWh)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=480,
        margin=dict(t=80, b=40),
        plot_bgcolor="white",
    )
    fig.update_xaxes(gridcolor="#f0f0f0")
    fig.update_yaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig, use_container_width=True)

    # ── Gráfico fracción solar mensual ──────────────────────────────────────
    fig2 = go.Figure()

    colores_bar = []
    for v in df_bal["fraccion_solar_pct"]:
        if v >= 90:   colores_bar.append("#2ecc71")
        elif v >= 75: colores_bar.append("#27ae60")
        elif v >= 50: colores_bar.append("#f39c12")
        elif v >= 25: colores_bar.append("#e67e22")
        else:         colores_bar.append("#e74c3c")

    fig2.add_trace(go.Bar(
        x=df_bal["mes"],
        y=df_bal["fraccion_solar_pct"],
        marker_color=colores_bar,
        text=[f"{v:.0f}%" for v in df_bal["fraccion_solar_pct"]],
        textposition="outside",
        name="Fracción solar mensual",
        hovertemplate="%{y:.1f}%<extra>Fracción solar</extra>",
    ))

    # Líneas de clasificación
    for umbral, clase_l, _, color_l, _ in [
        (90, "A+", "", "#2ecc71", ""),
        (75, "A",  "", "#27ae60", ""),
        (50, "B",  "", "#f39c12", ""),
        (25, "C",  "", "#e67e22", ""),
    ]:
        fig2.add_hline(
            y=umbral, line_dash="dash", line_color=color_l, line_width=1.5,
            annotation_text=f" {clase_l} ({umbral}%)",
            annotation_position="right",
        )

    fig2.update_layout(
        title="Fracción solar mensual — % del consumo cubierto por solar",
        xaxis_title="Mes",
        yaxis_title="Fracción solar (%)",
        yaxis=dict(range=[0, 115]),
        height=380,
        plot_bgcolor="white",
        margin=dict(t=60, b=40),
    )
    fig2.update_xaxes(gridcolor="#f0f0f0")
    fig2.update_yaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig2, use_container_width=True)

    # ── Tabla detallada ──────────────────────────────────────────────────────
    with st.expander("📋 Tabla detallada del balance mensual"):
        df_show = df_bal[[
            "mes", "E_solar_kWh", "E_consumo_kWh",
            "autoconsumo_directo_kWh", "E_bateria_descargada_kWh",
            "autoconsumo_total_kWh", "deficit_neto_kWh",
            "exportacion_kWh", "fraccion_solar_pct",
        ]].copy()
        df_show.columns = [
            "Mes", "Solar (kWh)", "Consumo (kWh)",
            "Autoconsumo directo", "Batería→edificio",
            "Autoconsumo total", "Déficit (red)", "Exportado", "Fracción solar (%)",
        ]
        # Fila de totales
        totales = {
            "Mes": "TOTAL",
            "Solar (kWh)": df_show["Solar (kWh)"].sum(),
            "Consumo (kWh)": df_show["Consumo (kWh)"].sum(),
            "Autoconsumo directo": df_show["Autoconsumo directo"].sum(),
            "Batería→edificio": df_show["Batería→edificio"].sum(),
            "Autoconsumo total": df_show["Autoconsumo total"].sum(),
            "Déficit (red)": df_show["Déficit (red)"].sum(),
            "Exportado": df_show["Exportado"].sum(),
            "Fracción solar (%)": round(metr["fraccion_solar_pct"], 1),
        }
        df_show = pd.concat([df_show, pd.DataFrame([totales])], ignore_index=True)
        st.dataframe(df_show.style.format({
            "Solar (kWh)": "{:,.0f}",
            "Consumo (kWh)": "{:,.0f}",
            "Autoconsumo directo": "{:,.0f}",
            "Batería→edificio": "{:,.0f}",
            "Autoconsumo total": "{:,.0f}",
            "Déficit (red)": "{:,.0f}",
            "Exportado": "{:,.0f}",
            "Fracción solar (%)": "{:.1f}%",
        }), use_container_width=True, hide_index=True)

    # ── Flujo de ahorro estimado ─────────────────────────────────────────────
    tarifa = float(st.session_state.get("tarifa_cop_kWh", 650.0))
    if tarifa > 0 and metr["E_autoconsumo_anual_kWh"] > 0:
        ahorro_anual_cop = metr["E_autoconsumo_anual_kWh"] * tarifa
        tipo_cambio = float(st.session_state.get("tipo_cambio", 4100.0))
        ahorro_anual_usd = ahorro_anual_cop / tipo_cambio
        st.divider()
        st.subheader("6️⃣ Estimación de ahorro en factura")
        col_a1, col_a2, col_a3 = st.columns(3)
        col_a1.metric("Autoconsumo anual",
                      f"{metr['E_autoconsumo_anual_kWh']:,.0f} kWh")
        col_a2.metric("Ahorro anual estimado",
                      f"COP {ahorro_anual_cop / 1e6:,.1f}M",
                      delta=f"USD {ahorro_anual_usd:,.0f}")
        col_a3.metric("Ahorro mensual promedio",
                      f"COP {ahorro_anual_cop / 12 / 1e3:,.0f}K/mes")
        st.caption(
            f"Cálculo: {metr['E_autoconsumo_anual_kWh']:,.0f} kWh × "
            f"{tarifa:,.0f} COP/kWh = {ahorro_anual_cop/1e6:.2f} M COP/año. "
            "Tarifa y TRM tomadas de la página Financiero."
        )

    # ── Guardar en session_state para Financiero y Reporte ──────────────────
    st.session_state["balance_ok"]               = True
    st.session_state["fraccion_solar_pct"]       = metr["fraccion_solar_pct"]
    st.session_state["clasificacion_energetica"] = clase
    st.session_state["balance_metricas"]         = metr

    # Nota de integración con Financiero
    with st.expander("🔗 Integración con otras páginas"):
        st.markdown("""
| Página | Dato que recibe de esta página |
|---|---|
| **7 — Financiero** | `fraccion_solar_pct`, `E_autoconsumo_anual_kWh` para calcular LCOE con storage |
| **8 — Presupuesto** | `bateria_dim` → N baterías × costo unitario se suman al CAPEX |
| **10 — Reporte PDF** | Clase energética A+/A/B/C/D, tabla de balance, KPIs de autoconsumo |

Los valores se propagan automáticamente vía `session_state` cuando calcule en esta página primero.
        """)

else:
    if prod_ok and df_m_prod is not None:
        st.info("👆 Configure el perfil de consumo y haga clic en **Calcular balance energético mensual**")
