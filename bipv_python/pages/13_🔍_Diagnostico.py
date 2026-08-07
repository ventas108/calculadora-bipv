"""Página 13 — Diagnóstico de sistema solar instalado (BIPV y Convencional)."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import date, datetime

from datos.ciudades_colombia import CIUDADES, LISTA_CIUDADES
from calculos.diagnostico_historico import (
    cargar_historico,
    guardar_registro,
    eliminar_registro,
)

st.set_page_config(
    page_title="Diagnóstico — Sistema Instalado",
    page_icon="🔍",
    layout="wide",
)

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página

st.title("🔍 Diagnóstico de Sistema Solar Instalado")
st.caption(
    "Auditoría técnica: compara la producción real medida contra el modelo teórico PVGIS. "
    "Aplica tanto a sistemas BIPV (fachadas/cubierta integrados) como convencionales."
)

# ── Constantes de referencia ──────────────────────────────────────────────────
PR_REF = {
    "BIPV":          {"min": 0.65, "max": 0.75, "nominal": 0.70},
    "Convencional":  {"min": 0.75, "max": 0.80, "nominal": 0.775},
}
DEGRADACION_NOMINAL_PCT = 0.50   # %/año — valor típico garantías Tier-1
DEGRADACION_ALERTA_PCT  = 0.70   # %/año — umbral inspección
DEGRADACION_CRITICA_PCT = 1.20   # %/año — umbral mantenimiento urgente

VIDA_UTIL_AÑOS = 25
OM_PCT_CAPEX   = 0.01            # 1 % del CAPEX anual (default O&M)

# ── Fuente GHI: session_state → ciudades_colombia.py ─────────────────────────
ciudad_proyecto = (
    st.session_state.get("tmy_ciudad")
    or st.session_state.get("ciudad", "Bogotá")
)
ghi_sesion = st.session_state.get("ghi_anual_kWh_m2", 0.0)          # del Recurso Solar
recurso_ok = st.session_state.get("recurso_solar_ok", False)


def _ghi_ciudad(ciudad: str) -> float:
    """GHI anual en kWh/m² desde catálogo de ciudades (fallback)."""
    datos = CIUDADES.get(ciudad, CIUDADES.get("Bogotá", {}))
    return datos.get("GHI_kWh_m2_dia", 4.5) * 365


def _t_amb(ciudad: str) -> float:
    datos = CIUDADES.get(ciudad, CIUDADES.get("Bogotá", {}))
    return datos.get("T_amb_media", 18.0)


# ═══════════════════════════════════════════════════════════════════════════════
# PANEL LATERAL — entradas
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ Parámetros del sistema instalado")

    tipo_sistema = st.radio(
        "Tipo de sistema",
        options=["BIPV", "Convencional"],
        index=0,
        help="BIPV: integrado en fachada/cubierta (PR referencia 0.65–0.75). "
             "Convencional: módulos sobre estructura (PR referencia 0.75–0.80).",
    )

    potencia_kWp = st.number_input(
        "Potencia instalada (kWp)",
        min_value=0.1,
        max_value=10_000.0,
        value=10.0,
        step=0.5,
        format="%.1f",
    )

    fecha_instalacion = st.date_input(
        "Fecha de instalación",
        value=date(date.today().year - 3, 1, 1),
        min_value=date(2000, 1, 1),
        max_value=date.today(),
    )

    st.divider()
    st.subheader("📊 Producción real medida")
    st.caption("Ingresa los datos de tu medidor o inversor (hasta 12 meses).")

    num_meses = st.slider("Meses de datos disponibles", 1, 12, 12)

    meses_labels = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
    ]

    prod_mensual = []
    with st.expander("Editar producción mensual (kWh)", expanded=True):
        cols = st.columns(2)
        for i in range(num_meses):
            with cols[i % 2]:
                val = st.number_input(
                    f"{meses_labels[i]}",
                    min_value=0.0,
                    max_value=500_000.0,
                    value=round(potencia_kWp * 120, 1),
                    step=10.0,
                    key=f"prod_mes_{i}",
                    label_visibility="visible",
                )
                prod_mensual.append(val)

    st.divider()
    st.subheader("🏢 Consumo del edificio")
    consumo_mensual_kwh = st.number_input(
        "Consumo promedio mensual (kWh/mes)",
        min_value=0.0,
        max_value=500_000.0,
        value=round(potencia_kWp * 160, 1),
        step=10.0,
        help="Promedio mensual del recibo de energía del período analizado.",
    )

    st.divider()
    st.subheader("💰 Datos económicos (opcional)")
    capex_cop = st.number_input(
        "Inversión total (COP $)",
        min_value=0.0,
        value=potencia_kWp * 8_000_000,
        step=500_000.0,
        format="%.0f",
        help="Costo total del sistema instalado. Necesario para calcular LCOE real.",
    )
    tarifa_cop_kwh = st.number_input(
        "Tarifa eléctrica (COP/kWh)",
        min_value=50.0,
        max_value=2_000.0,
        value=float(
            CIUDADES.get(ciudad_proyecto, CIUDADES.get("Bogotá", {})).get(
                "tarifa_comercial_cop_kwh", 700.0
            )
        ),
        step=10.0,
    )

    st.divider()
    st.subheader("🌞 Recurso solar")
    # Ciudad: usa la del proyecto si está disponible; de lo contrario, el usuario elige
    if recurso_ok and ghi_sesion > 0:
        ciudad_diag = ciudad_proyecto
        ghi_anual   = ghi_sesion
        st.success(
            f"✅ GHI desde Recurso Solar: **{ghi_anual:,.0f} kWh/m²/año** — {ciudad_diag}"
        )
    else:
        st.info("ℹ️ Recurso Solar no calculado. Selecciona ciudad manualmente.")
        ciudad_diag = st.selectbox(
            "Ciudad de referencia",
            LISTA_CIUDADES,
            index=LISTA_CIUDADES.index(ciudad_proyecto)
            if ciudad_proyecto in LISTA_CIUDADES
            else 0,
        )
        ghi_anual = _ghi_ciudad(ciudad_diag)
        st.caption(f"GHI catálogo: **{ghi_anual:,.0f} kWh/m²/año**")

# ═══════════════════════════════════════════════════════════════════════════════
# CÁLCULOS
# ═══════════════════════════════════════════════════════════════════════════════
prod_total_kwh  = sum(prod_mensual)                         # kWh en el período
prod_anual_kwh  = prod_total_kwh * (12 / num_meses)         # extrapolación anual

# Años de operación
años_operacion = max(
    0.5,
    (date.today() - fecha_instalacion).days / 365.25,
)

# ── PR real ───────────────────────────────────────────────────────────────────
# PR = E_ac / (GHI_plano * kWp) — el GHI está en kWh/m²/año
pr_real = prod_anual_kwh / (ghi_anual * potencia_kWp) if ghi_anual > 0 else 0.0

# ── Yield específico (kWh/kWp/año) ───────────────────────────────────────────
yield_especifico = prod_anual_kwh / potencia_kWp if potencia_kWp > 0 else 0.0

# ── PR referencia para el tipo de sistema ────────────────────────────────────
pr_ref_nom = PR_REF[tipo_sistema]["nominal"]
pr_ref_min = PR_REF[tipo_sistema]["min"]
pr_ref_max = PR_REF[tipo_sistema]["max"]

# ── Performance Index (%) ────────────────────────────────────────────────────
pi_pct = (pr_real / pr_ref_nom * 100) if pr_ref_nom > 0 else 0.0

# ── Degradación anual estimada ────────────────────────────────────────────────
# PR_real = PR_inicial * (1 - deg/100)^años  →  deg = (1 - (PR_real/PR_inicial)^(1/años)) * 100
pr_inicial = pr_ref_nom   # asumimos que el sistema arrancó con PR nominal
if años_operacion > 0.5 and pr_real < pr_inicial:
    deg_pct_año = (1 - (pr_real / pr_inicial) ** (1 / años_operacion)) * 100
else:
    deg_pct_año = 0.0
deg_pct_año = max(0.0, min(deg_pct_año, 10.0))  # clamp razonable

# ── % Autoconsumo ─────────────────────────────────────────────────────────────
consumo_anual_kwh = consumo_mensual_kwh * 12
autoconsumo_kwh   = min(prod_anual_kwh, consumo_anual_kwh)
pct_autoconsumo   = (autoconsumo_kwh / consumo_anual_kwh * 100) if consumo_anual_kwh > 0 else 0.0

# ── LCOE real (COP/kWh) ──────────────────────────────────────────────────────
if capex_cop > 0 and prod_anual_kwh > 0:
    om_anual_cop    = capex_cop * OM_PCT_CAPEX
    energia_total   = sum(
        prod_anual_kwh * ((1 - deg_pct_año / 100) ** yr)
        for yr in range(VIDA_UTIL_AÑOS)
    )
    costo_total_cop = capex_cop + om_anual_cop * VIDA_UTIL_AÑOS
    lcoe_cop_kwh    = costo_total_cop / energia_total if energia_total > 0 else 0.0
else:
    lcoe_cop_kwh    = 0.0
    energia_total   = 0.0

# ── Semáforo ──────────────────────────────────────────────────────────────────
def _semaforo(pi: float, deg: float) -> tuple[str, str, str]:
    """Devuelve (emoji, estado, recomendación)."""
    if pi >= 90 and deg <= DEGRADACION_ALERTA_PCT:
        return (
            "🟢",
            "Sistema en buen estado",
            "No se requiere acción inmediata. Continúe con revisiones anuales de rutina.",
        )
    elif pi >= 75 and deg <= DEGRADACION_CRITICA_PCT:
        return (
            "🟡",
            "Inspección recomendada",
            "Algunos indicadores están por debajo de lo esperado. Se recomienda revisión "
            "de conexiones, limpieza de módulos y verificación del inversor en los próximos 30 días.",
        )
    else:
        return (
            "🔴",
            "Mantenimiento urgente",
            "El sistema presenta un rendimiento significativamente inferior al esperado. "
            "Se recomienda inspección técnica inmediata: verificar módulos, cableado DC/AC, "
            "inversor, estructura y posibles sombras adicionales.",
        )


semaforo_emoji, semaforo_estado, semaforo_rec = _semaforo(pi_pct, deg_pct_año)

# ═══════════════════════════════════════════════════════════════════════════════
# RESULTADO: SEMÁFORO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
col_sem, col_info = st.columns([1, 3])
with col_sem:
    st.markdown(
        f"""
        <div style="
            background: {'#e8f5e9' if '🟢' in semaforo_emoji else '#fffde7' if '🟡' in semaforo_emoji else '#ffebee'};
            border-radius: 16px; padding: 32px; text-align: center;
            border: 2px solid {'#66bb6a' if '🟢' in semaforo_emoji else '#ffd54f' if '🟡' in semaforo_emoji else '#ef5350'};
        ">
            <div style="font-size: 72px; line-height: 1.1;">{semaforo_emoji}</div>
            <div style="font-size: 18px; font-weight: 700; margin-top: 12px;">{semaforo_estado}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_info:
    st.subheader(f"Diagnóstico — {tipo_sistema} · {potencia_kWp:.1f} kWp · {ciudad_diag}")
    st.info(f"**Recomendación:** {semaforo_rec}")

    # Mini métricas rápidas en columnas
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("PR real", f"{pr_real:.3f}", help="Performance Ratio real medido")
    m2.metric("Yield", f"{yield_especifico:,.0f}", "kWh/kWp/año")
    m3.metric(
        "Índice de desempeño",
        f"{pi_pct:.1f} %",
        delta=f"{pi_pct - 100:.1f} % vs nominal",
        delta_color="normal",
    )
    m4.metric(
        "Degradación",
        f"{deg_pct_año:.2f} %/año",
        delta=f"ref. ≤ {DEGRADACION_NOMINAL_PCT:.2f} %/año",
        delta_color="inverse",
    )
    m5.metric("Autoconsumo", f"{pct_autoconsumo:.1f} %")
    if lcoe_cop_kwh > 0:
        m6.metric(
            "LCOE real",
            f"${lcoe_cop_kwh:,.0f}/kWh",
            delta=f"tarifa: ${tarifa_cop_kwh:,.0f}",
            delta_color="off",
        )
    else:
        m6.metric("LCOE real", "—", help="Ingresa la inversión total para calcular")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# DETALLE EN TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_kpis, tab_produccion, tab_degradacion, tab_financiero, tab_referencia = st.tabs(
    ["📋 KPIs técnicos", "📊 Producción mensual", "📉 Degradación", "💰 Financiero", "📖 Referencias"]
)

# ── Tab 1: KPIs técnicos ──────────────────────────────────────────────────────
with tab_kpis:
    st.subheader("Indicadores técnicos detallados")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Rendimiento vs referencia")
        df_kpis = pd.DataFrame(
            {
                "Indicador": [
                    "PR real medido",
                    f"PR referencia {tipo_sistema} (mín)",
                    f"PR referencia {tipo_sistema} (nom)",
                    f"PR referencia {tipo_sistema} (máx)",
                    "Índice de desempeño (PI)",
                    "Yield específico",
                    "Producción anual estimada",
                    "Años en operación",
                ],
                "Valor": [
                    f"{pr_real:.4f}",
                    f"{pr_ref_min:.2f}",
                    f"{pr_ref_nom:.3f}",
                    f"{pr_ref_max:.2f}",
                    f"{pi_pct:.1f} %",
                    f"{yield_especifico:,.0f} kWh/kWp/año",
                    f"{prod_anual_kwh:,.0f} kWh/año",
                    f"{años_operacion:.1f} años",
                ],
                "Estado": [
                    "🟢" if pr_real >= pr_ref_min else ("🟡" if pr_real >= pr_ref_min * 0.9 else "🔴"),
                    "—", "—", "—",
                    "🟢" if pi_pct >= 90 else ("🟡" if pi_pct >= 75 else "🔴"),
                    "🟢" if yield_especifico >= 1000 else "🟡",
                    "🟢",
                    "🟢",
                ],
            }
        )
        st.dataframe(df_kpis, use_container_width=True, hide_index=True)

    with c2:
        st.markdown("#### Balance energético")
        df_balance = pd.DataFrame(
            {
                "Concepto": [
                    "Producción anual (estimada)",
                    "Consumo anual (estimado)",
                    "Autoconsumo directo",
                    "Excedente a red",
                    "Energía de red requerida",
                    "% Autoconsumo",
                    "% Cobertura del consumo",
                ],
                "Valor": [
                    f"{prod_anual_kwh:,.0f} kWh/año",
                    f"{consumo_anual_kwh:,.0f} kWh/año",
                    f"{autoconsumo_kwh:,.0f} kWh/año",
                    f"{max(0, prod_anual_kwh - consumo_anual_kwh):,.0f} kWh/año",
                    f"{max(0, consumo_anual_kwh - prod_anual_kwh):,.0f} kWh/año",
                    f"{pct_autoconsumo:.1f} %",
                    f"{min(100, prod_anual_kwh / consumo_anual_kwh * 100) if consumo_anual_kwh > 0 else 0:.1f} %",
                ],
            }
        )
        st.dataframe(df_balance, use_container_width=True, hide_index=True)

    # Gauge PR
    st.markdown("#### Gauge — Performance Ratio real vs referencia")
    pr_min_gauge = 0.40
    pr_max_gauge = 1.00
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=pr_real,
            delta={"reference": pr_ref_nom, "valueformat": ".3f"},
            number={"valueformat": ".3f"},
            title={"text": f"PR real — referencia {tipo_sistema}: {pr_ref_nom:.3f}"},
            gauge={
                "axis": {"range": [pr_min_gauge, pr_max_gauge], "tickformat": ".2f"},
                "bar": {"color": "#1565C0"},
                "steps": [
                    {"range": [pr_min_gauge, pr_ref_min], "color": "#ffcdd2"},
                    {"range": [pr_ref_min, pr_ref_max], "color": "#c8e6c9"},
                    {"range": [pr_ref_max, pr_max_gauge], "color": "#e3f2fd"},
                ],
                "threshold": {
                    "line": {"color": "#e53935", "width": 3},
                    "thickness": 0.75,
                    "value": pr_ref_min,
                },
            },
        )
    )
    fig_gauge.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

# ── Tab 2: Producción mensual ─────────────────────────────────────────────────
with tab_produccion:
    st.subheader("Producción mensual real vs estimación teórica")

    # Estimación teórica mensual: distribuir GHI anual proporcionalmente a días del mes
    dias_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    prod_teorica_mensual = [
        ghi_anual * (dias_mes[i] / 365) * potencia_kWp * pr_ref_nom
        for i in range(12)
    ]

    df_prod = pd.DataFrame(
        {
            "Mes": meses_labels[:num_meses],
            "Real (kWh)": prod_mensual,
            "Teórico PVGIS (kWh)": [prod_teorica_mensual[i] for i in range(num_meses)],
        }
    )
    df_prod["Diferencia (%)"] = (
        (df_prod["Real (kWh)"] - df_prod["Teórico PVGIS (kWh)"])
        / df_prod["Teórico PVGIS (kWh)"]
        * 100
    ).round(1)

    fig_bar = go.Figure()
    fig_bar.add_trace(
        go.Bar(
            name="Real medido",
            x=df_prod["Mes"],
            y=df_prod["Real (kWh)"],
            marker_color="#1565C0",
            text=df_prod["Real (kWh)"].apply(lambda v: f"{v:,.0f}"),
            textposition="outside",
        )
    )
    fig_bar.add_trace(
        go.Bar(
            name="Teórico PVGIS",
            x=df_prod["Mes"],
            y=df_prod["Teórico PVGIS (kWh)"],
            marker_color="#90CAF9",
            text=[f"{v:,.0f}" for v in df_prod["Teórico PVGIS (kWh)"]],
            textposition="outside",
        )
    )
    fig_bar.update_layout(
        barmode="group",
        title="Producción mensual: real vs teórico",
        xaxis_title="Mes",
        yaxis_title="Energía (kWh)",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", y=1.12),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Diferencia %
    colors_diff = [
        "#ef5350" if v < -15 else ("#ffd54f" if v < -5 else "#66bb6a")
        for v in df_prod["Diferencia (%)"]
    ]
    fig_diff = go.Figure(
        go.Bar(
            x=df_prod["Mes"],
            y=df_prod["Diferencia (%)"],
            marker_color=colors_diff,
            text=df_prod["Diferencia (%)"].apply(lambda v: f"{v:+.1f}%"),
            textposition="outside",
        )
    )
    fig_diff.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_diff.add_hline(y=-10, line_dash="dot", line_color="#ffd54f",
                       annotation_text="-10 % umbral inspección")
    fig_diff.add_hline(y=-20, line_dash="dot", line_color="#ef5350",
                       annotation_text="-20 % umbral urgente")
    fig_diff.update_layout(
        title="Desviación real vs teórico (%)",
        xaxis_title="Mes",
        yaxis_title="Desviación (%)",
        height=320,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig_diff, use_container_width=True)

    st.dataframe(
        df_prod.style.format(
            {"Real (kWh)": "{:,.0f}", "Teórico PVGIS (kWh)": "{:,.0f}", "Diferencia (%)": "{:+.1f}%"}
        ),
        use_container_width=True,
        hide_index=True,
    )

# ── Tab 3: Degradación ────────────────────────────────────────────────────────
with tab_degradacion:
    st.subheader("Análisis de degradación estimada")

    col_d1, col_d2 = st.columns([2, 1])
    with col_d1:
        # Curva de degradación proyectada
        años_vec = np.arange(0, VIDA_UTIL_AÑOS + 1)
        pr_proyectado = pr_real * ((1 - deg_pct_año / 100) ** años_vec)
        pr_garantia   = pr_ref_nom * ((1 - DEGRADACION_NOMINAL_PCT / 100) ** años_vec)

        fig_deg = go.Figure()
        fig_deg.add_trace(
            go.Scatter(
                x=años_vec,
                y=pr_proyectado,
                name=f"PR proyectado ({deg_pct_año:.2f} %/año)",
                mode="lines",
                line=dict(color="#1565C0", width=2),
            )
        )
        fig_deg.add_trace(
            go.Scatter(
                x=años_vec,
                y=pr_garantia,
                name=f"PR típico garantía ({DEGRADACION_NOMINAL_PCT:.2f} %/año)",
                mode="lines",
                line=dict(color="#43A047", width=2, dash="dash"),
            )
        )
        fig_deg.add_hline(
            y=pr_ref_min,
            line_dash="dot",
            line_color="#ef5350",
            annotation_text=f"PR mín referencia {tipo_sistema}: {pr_ref_min}",
        )
        # Punto actual
        fig_deg.add_trace(
            go.Scatter(
                x=[años_operacion],
                y=[pr_real],
                name="Punto actual",
                mode="markers",
                marker=dict(color="#e53935", size=12, symbol="circle"),
            )
        )
        fig_deg.update_layout(
            title="Proyección del PR a 25 años",
            xaxis_title="Años desde instalación",
            yaxis_title="Performance Ratio",
            height=380,
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(orientation="h", y=1.15),
        )
        st.plotly_chart(fig_deg, use_container_width=True)

    with col_d2:
        st.markdown("#### Resumen degradación")
        st.metric("Degradación estimada", f"{deg_pct_año:.2f} %/año")
        st.metric("PR inicial nominal", f"{pr_ref_nom:.3f}")
        st.metric("PR actual medido", f"{pr_real:.3f}")
        st.metric("Caída de PR", f"{(pr_ref_nom - pr_real):.4f} ({(pr_ref_nom - pr_real)/pr_ref_nom*100:.1f} %)")
        st.metric("Años en operación", f"{años_operacion:.1f} años")

        st.markdown("---")
        st.markdown("**Umbrales de referencia:**")
        st.markdown(f"- 🟢 ≤ {DEGRADACION_NOMINAL_PCT:.2f} %/año (normal)")
        st.markdown(f"- 🟡 {DEGRADACION_NOMINAL_PCT:.2f}–{DEGRADACION_ALERTA_PCT:.2f} %/año (inspección)")
        st.markdown(f"- 🔴 > {DEGRADACION_CRITICA_PCT:.2f} %/año (urgente)")

        if deg_pct_año <= DEGRADACION_NOMINAL_PCT:
            st.success("✅ Degradación dentro del rango normal")
        elif deg_pct_año <= DEGRADACION_ALERTA_PCT:
            st.warning("⚠️ Degradación ligeramente elevada")
        elif deg_pct_año <= DEGRADACION_CRITICA_PCT:
            st.error("🔴 Degradación superior al umbral de inspección")
        else:
            st.error("🚨 Degradación crítica — inspección urgente")

        # Año proyectado en que PR cae bajo mínimo
        if deg_pct_año > 0:
            if pr_real > pr_ref_min:
                años_hasta_limite = np.log(pr_ref_min / pr_real) / np.log(1 - deg_pct_año / 100)
                st.metric(
                    "Años hasta PR mínimo",
                    f"{años_hasta_limite:.1f} años" if años_hasta_limite > 0 else "Ya superado",
                )

# ── Tab 4: Financiero ─────────────────────────────────────────────────────────
with tab_financiero:
    st.subheader("Indicadores financieros del sistema instalado")

    if capex_cop <= 0:
        st.warning("⚠️ Ingresa la inversión total en el panel lateral para calcular indicadores financieros.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)
        ahorro_anual_cop = autoconsumo_kwh * tarifa_cop_kwh
        with col_f1:
            st.metric("CAPEX", f"${capex_cop:,.0f} COP")
            st.metric("O&M anual estimado", f"${capex_cop * OM_PCT_CAPEX:,.0f} COP/año")
            st.metric("LCOE real", f"${lcoe_cop_kwh:,.0f} COP/kWh" if lcoe_cop_kwh > 0 else "—")
        with col_f2:
            st.metric("Ahorro anual estimado", f"${ahorro_anual_cop:,.0f} COP/año")
            payback = capex_cop / ahorro_anual_cop if ahorro_anual_cop > 0 else 0
            st.metric("Payback simple", f"{payback:.1f} años" if payback > 0 else "—")
            st.metric("Tarifa eléctrica", f"${tarifa_cop_kwh:,.0f} COP/kWh")
        with col_f3:
            st.metric("Producción vida útil (25 a)", f"{energia_total:,.0f} kWh")
            ingreso_total = energia_total * tarifa_cop_kwh
            roi = (ingreso_total - capex_cop) / capex_cop * 100
            st.metric("ROI simple 25 años", f"{roi:.1f} %")
            st.metric("LCOE vs tarifa",
                      "✅ Competitivo" if lcoe_cop_kwh < tarifa_cop_kwh else "⚠️ Revisar",
                      delta=f"${tarifa_cop_kwh - lcoe_cop_kwh:,.0f} diferencia" if lcoe_cop_kwh > 0 else None)

        # Flujo de caja proyectado
        st.markdown("#### Flujo de caja proyectado (25 años)")
        flujo_acumulado = -capex_cop
        flujos = []
        for yr in range(1, VIDA_UTIL_AÑOS + 1):
            prod_yr  = prod_anual_kwh * ((1 - deg_pct_año / 100) ** yr)
            ahorro_yr = min(prod_yr, consumo_anual_kwh) * tarifa_cop_kwh
            om_yr     = capex_cop * OM_PCT_CAPEX
            neto_yr   = ahorro_yr - om_yr
            flujo_acumulado += neto_yr
            flujos.append({"Año": yr, "Ahorro": ahorro_yr, "O&M": -om_yr, "Neto acumulado": flujo_acumulado})

        df_flujo = pd.DataFrame(flujos)

        fig_flujo = go.Figure()
        fig_flujo.add_trace(
            go.Bar(name="Ahorro", x=df_flujo["Año"], y=df_flujo["Ahorro"],
                   marker_color="#43A047")
        )
        fig_flujo.add_trace(
            go.Bar(name="O&M", x=df_flujo["Año"], y=df_flujo["O&M"],
                   marker_color="#ef5350")
        )
        fig_flujo.add_trace(
            go.Scatter(name="Acumulado", x=df_flujo["Año"], y=df_flujo["Neto acumulado"],
                       mode="lines+markers", yaxis="y2",
                       line=dict(color="#1565C0", width=2))
        )
        fig_flujo.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_flujo.update_layout(
            barmode="relative",
            xaxis_title="Año",
            yaxis_title="COP / año",
            yaxis2=dict(title="Acumulado (COP)", overlaying="y", side="right"),
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", y=1.12),
        )
        st.plotly_chart(fig_flujo, use_container_width=True)

# ── Tab 5: Referencias ────────────────────────────────────────────────────────
with tab_referencia:
    st.subheader("Marco de referencia técnico")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("#### Performance Ratio por tecnología")
        df_pr_ref = pd.DataFrame(
            {
                "Tecnología": ["BIPV (fachada integrada)", "Convencional (techo/suelo)", "CPV concentrador"],
                "PR mínimo": [0.65, 0.75, 0.80],
                "PR nominal": [0.70, 0.775, 0.85],
                "PR máximo": [0.75, 0.80, 0.90],
                "Fuente": ["IEC 61724-1", "IEC 61724-1", "IEC 62670"],
            }
        )
        st.dataframe(df_pr_ref, use_container_width=True, hide_index=True)

        st.markdown("#### Criterios del semáforo")
        df_sem = pd.DataFrame(
            {
                "Estado": ["🟢 OK", "🟡 Inspección recomendada", "🔴 Mantenimiento urgente"],
                "PI (%)": ["≥ 90 %", "75 – 90 %", "< 75 %"],
                "Degradación (%/año)": [f"≤ {DEGRADACION_ALERTA_PCT:.2f}", f"{DEGRADACION_ALERTA_PCT:.2f}–{DEGRADACION_CRITICA_PCT:.2f}", f"> {DEGRADACION_CRITICA_PCT:.2f}"],
            }
        )
        st.dataframe(df_sem, use_container_width=True, hide_index=True)

    with col_r2:
        st.markdown("#### Definiciones")
        st.markdown(
            f"""
| KPI | Fórmula |
|-----|---------|
| **PR real** | E_ac_real / (GHI_anual × kWp_instalado) |
| **Yield específico** | E_ac_real / kWp_instalado [kWh/kWp/año] |
| **Índice de desempeño (PI)** | PR_real / PR_referencia × 100 % |
| **Degradación** | (1 − (PR_real / PR_ini)^(1/años)) × 100 %/año |
| **% Autoconsumo** | min(E_prod, E_consumo) / E_consumo × 100 % |
| **LCOE real** | (CAPEX + O&M×{VIDA_UTIL_AÑOS} años) / E_vida_útil |

**Nota:** GHI usado → {"sesión Recurso Solar (" + str(int(ghi_sesion)) + " kWh/m²/año)" if recurso_ok and ghi_sesion > 0 else "catálogo ciudades (" + str(int(ghi_anual)) + " kWh/m²/año)"}

**Normas de referencia:**
- IEC 61724-1:2017 — Monitoring of PV systems
- IEC 61724-3:2016 — Energy evaluation method
- RETIE 2013 (Colombia) — Reglamento Técnico de Instalaciones Eléctricas
"""
        )

# ═══════════════════════════════════════════════════════════════════════════════
# HISTÓRICO DE DIAGNÓSTICOS (#98) — ¿el sistema mejora o empeora con el tiempo?
# ═══════════════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("📈 Histórico de diagnósticos")

_nombre_proy_hist = st.session_state.get("nombre_proyecto") or "Diagnóstico general"
st.caption(
    f"Cada diagnóstico guardado queda asociado al proyecto **{_nombre_proy_hist}** "
    "y permite ver si el sistema mejora o empeora entre visitas."
)

_historico = cargar_historico(_nombre_proy_hist)

col_hg1, col_hg2 = st.columns([1, 3])
with col_hg1:
    if st.button("💾 Guardar este diagnóstico en el histórico", type="secondary",
                 use_container_width=True):
        _registro = {
            "fecha":              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tipo_sistema":       tipo_sistema,
            "potencia_kWp":       round(potencia_kWp, 2),
            "ciudad":             ciudad_diag,
            "ghi_anual_kWh_m2":   round(ghi_anual, 1),
            "num_meses":          int(num_meses),
            "prod_anual_kWh":     round(prod_anual_kwh, 0),
            "yield_kWh_kWp":      round(yield_especifico, 0),
            "pr_real":            round(pr_real, 4),
            "pr_ref_nominal":     pr_ref_nom,
            "pi_pct":             round(pi_pct, 1),
            "deg_pct_año":        round(deg_pct_año, 2),
            "pct_autoconsumo":    round(pct_autoconsumo, 1),
            "lcoe_cop_kwh":       round(lcoe_cop_kwh, 1),
            "semaforo":           semaforo_emoji,
            "estado":             semaforo_estado,
            "años_operacion":     round(años_operacion, 1),
        }
        _ok_hist, _historico = guardar_registro(_nombre_proy_hist, _registro)
        if _ok_hist:
            st.success("✅ Diagnóstico guardado en el histórico.")
        else:
            st.warning(
                "⚠️ No se pudo escribir el histórico a disco (revisa permisos/espacio "
                "del servidor en `datos/diagnosticos/`). El registro se muestra abajo "
                "pero se perderá al recargar."
            )

if not _historico:
    st.info(
        "ℹ️ Aún no hay diagnósticos guardados para este proyecto. Pulsa "
        "**💾 Guardar este diagnóstico** cada vez que audites el sistema (por ejemplo, "
        "cada 6–12 meses) para construir la tendencia."
    )
else:
    # ── Comparación contra el diagnóstico anterior ────────────────────────────
    if len(_historico) >= 2:
        _prev, _ult = _historico[-2], _historico[-1]
        _d_pi  = _ult.get("pi_pct", 0) - _prev.get("pi_pct", 0)
        _d_pr  = _ult.get("pr_real", 0) - _prev.get("pr_real", 0)
        _d_deg = _ult.get("deg_pct_año", 0) - _prev.get("deg_pct_año", 0)
        _tendencia = "mejoró" if _d_pi > 1 else ("empeoró" if _d_pi < -1 else "se mantiene estable")
        _icono = "🟢" if _d_pi > 1 else ("🔴" if _d_pi < -1 else "🟡")
        st.markdown(
            f"{_icono} Entre **{_prev.get('fecha','?')}** y **{_ult.get('fecha','?')}** "
            f"el sistema **{_tendencia}**: PI {_d_pi:+.1f} puntos · "
            f"PR {_d_pr:+.3f} · degradación estimada {_d_deg:+.2f} %/año."
        )

    _df_hist = pd.DataFrame(_historico)

    # ── Gráfica de tendencia PR / PI ──────────────────────────────────────────
    if len(_historico) >= 2 and "fecha" in _df_hist.columns:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(
            x=_df_hist["fecha"], y=_df_hist["pi_pct"],
            mode="lines+markers", name="PI (%)", line=dict(color="#1976d2", width=3),
        ))
        fig_hist.add_trace(go.Scatter(
            x=_df_hist["fecha"], y=_df_hist["pr_real"] * 100,
            mode="lines+markers", name="PR real (×100)",
            line=dict(color="#43a047", width=2, dash="dot"),
        ))
        fig_hist.add_hline(y=90, line_dash="dash", line_color="#43a047",
                           annotation_text="PI 90% (🟢)")
        fig_hist.add_hline(y=75, line_dash="dash", line_color="#fbc02d",
                           annotation_text="PI 75% (🟡)")
        fig_hist.update_layout(
            height=340, margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title="%", xaxis_title="Fecha del diagnóstico",
            legend=dict(orientation="h", y=1.12),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # ── Tabla del histórico ───────────────────────────────────────────────────
    _cols_tabla = [c for c in [
        "fecha", "semaforo", "estado", "pi_pct", "pr_real", "deg_pct_año",
        "yield_kWh_kWp", "prod_anual_kWh", "pct_autoconsumo", "potencia_kWp",
        "num_meses",
    ] if c in _df_hist.columns]
    st.dataframe(
        _df_hist[_cols_tabla].rename(columns={
            "fecha": "Fecha", "semaforo": "", "estado": "Estado",
            "pi_pct": "PI (%)", "pr_real": "PR real", "deg_pct_año": "Deg (%/año)",
            "yield_kWh_kWp": "Yield (kWh/kWp)", "prod_anual_kWh": "E_ac anual (kWh)",
            "pct_autoconsumo": "Autoconsumo (%)", "potencia_kWp": "kWp",
            "num_meses": "Meses de datos",
        }),
        use_container_width=True, hide_index=True,
    )

    with st.expander("🗑️ Eliminar un registro del histórico"):
        _opciones = [
            f"{i+1}. {r.get('fecha','?')} — {r.get('semaforo','')} PI {r.get('pi_pct','?')}%"
            for i, r in enumerate(_historico)
        ]
        _sel_borrar = st.selectbox("Registro a eliminar", _opciones, key="diag_hist_borrar")
        if st.button("Eliminar registro seleccionado", key="diag_hist_borrar_btn"):
            _idx = _opciones.index(_sel_borrar)
            _ok_borrar, _ = eliminar_registro(_nombre_proy_hist, _idx)
            if not _ok_borrar:
                st.warning(
                    "⚠️ No se pudo reescribir el histórico a disco (permisos/espacio "
                    "en `datos/diagnosticos/`). El registro NO se eliminó."
                )
            else:
                st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"🔍 Diagnóstico generado con datos de {num_meses} mes(es) · "
    f"GHI: {ghi_anual:,.0f} kWh/m²/año ({ciudad_diag}) · "
    f"Fecha instalación: {fecha_instalacion.strftime('%b %Y')} · "
    f"{años_operacion:.1f} años en operación"
)
