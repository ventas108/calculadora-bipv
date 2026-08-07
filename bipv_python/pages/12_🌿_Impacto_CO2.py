"""
Página 12 — Huella de Carbono Evitada · BIPV Colombia

Estándares aplicados:
  • GHG Protocol Corporate Standard — Scope 2 · Location-based method
  • ISO 14064-1:2018 — Cuantificación y reporte de GEI
  • UNFCCC CDM — Metodología AMS-I.D (pequeña escala renovable)
  • IPCC AR6 WG III — factores de emisión por tecnología (kgCO₂eq/kWh)
  • Ley 1931/2018 — Gestión del Cambio Climático Colombia
  • NDC Colombia 2030 — Meta 51% reducción emisiones
  • XM / UPME — Factor de emisión SIN Colombia (promedio y marginal)
  • IDEAM — Equivalencia árboles nativos colombianos
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import datetime

from datos.ciudades_colombia import FACTOR_CO2_COLOMBIA_KG_KWH

st.set_page_config(page_title="Huella CO₂ — BIPV", page_icon="🌿", layout="wide")

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página
st.title("🌿 Huella de Carbono Evitada")
st.caption(
    "GHG Protocol Scope 2 · ISO 14064-1 · CDM AMS-I.D · "
    "Factor SIN Colombia XM/UPME · Ley 1931/2018 · NDC Colombia 2030"
)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES — ESTÁNDARES INTERNACIONALES Y COLOMBIANOS
# ─────────────────────────────────────────────────────────────────────────────

# ── Factores de emisión SIN Colombia ─────────────────────────────────────────
# Fuente: XM S.A. E.S.P. — Operador del SIN · UPME Resolución 520/2019
FACTOR_PROMEDIO_KG_KWH  = FACTOR_CO2_COLOMBIA_KG_KWH        # 0.126 kg/kWh — GHG Protocol location-based
FACTOR_MARGINAL_KG_KWH  = 0.300          # kg/kWh — Factor marginal combinado (CDM AMS-I.D)
                                          # OM ≈ 0.25, BM ≈ 0.35 → CM = (OM+BM)/2 ≈ 0.30
                                          # Fuente: UNFCCC CDM Tool 07 — Combined margin

# ── Equivalencias de impacto — Colombia ──────────────────────────────────────
# Árbol nativo adulto: absorción media 22 kgCO₂/año (IDEAM 2010 — "Vegetación Bosque Húmedo")
KG_CO2_ARBOL_ANUAL       = 22.0          # kg CO₂/árbol/año — IDEAM

# Hogar colombiano promedio — consumo eléctrico UPME 2022
KWH_HOGAR_ANUAL          = 1_560.0       # kWh/año (130 kWh/mes residencial estrato 3-4)

# Vehículo promedio Colombia — gasolina corriente
KG_CO2_KM_VEHICULO       = 0.162         # kgCO₂/km — IDEAM FECOC 2022 (auto gasolina)

# Vuelo doméstico — ICAO Carbon Emissions Calculator 2023
KG_CO2_VUELO_BOG_MDE     = 89.0          # kg CO₂/pasajero/vuelo ida (BOG–MDE ≈ 0.089 tCO₂)

# Barril de petróleo colombiano — combustión completa
KG_CO2_BARRIL_PETROLEO   = 431.7         # kgCO₂/barril (EPA AP-42 · API gravedad 31°)

# Cilindro GLP Colombia (40 lb = 18.14 kg)
KG_CO2_CILINDRO_GLP      = 55.6          # kgCO₂/cilindro 40 lb (IPCC 2006 Vol. 2 cap. 1)

# ── Intensidades carbono por tecnología — IPCC AR6 WG III Tabla A.III.2 ──────
INTENSIDAD_IPCC = {
    "Carbón (subcrítico)":     820,
    "Carbón (ultrasupercrítico)": 670,
    "Gas natural ciclo abierto":  490,
    "Gas natural ciclo combinado": 410,
    "Fuel oil / Diesel":       650,
    "Solar PV suelo (c-Si)":    24,
    "Solar BIPV fachada":       30,     # +25% vs PV suelo por vidrio laminado y soporte
    "Eólica terrestre":         7,
    "Hidroeléctrica":           24,
    "Nuclear":                  12,
    "Geotérmica":               38,
    "Biomasa":                  230,    # promedio, varía mucho
}

# ── Colores semáforo  ─────────────────────────────────────────────────────────
COLOR_VERDE   = "#2E7D32"
COLOR_AMBAR   = "#F57F17"
COLOR_ROJO    = "#C62828"
COLOR_AZUL    = "#1565C0"

# ─────────────────────────────────────────────────────────────────────────────
# PREREQUISITO — Producción anual
# ─────────────────────────────────────────────────────────────────────────────
# Prioridad E_ac: multi-superficie > bypass > base (claves exclusivas)
_e_ac_base     = st.session_state.get("E_ac_anual_kWh", 0.0)
_e_ac_bypass   = st.session_state.get("E_ac_anual_kWh_bypass", 0.0)
_e_ac_multisup = st.session_state.get("E_ac_anual_kWh_multisup", 0.0)
_bypass_ok     = st.session_state.get("bypass_ok", False)
_multisup_ok   = st.session_state.get("multisup_activo", False)
_area_ms       = st.session_state.get("area_total_multisup", 0.0)

if _multisup_ok and _e_ac_multisup > 0:
    e_ac = _e_ac_multisup
elif _bypass_ok and _e_ac_bypass > 0:
    e_ac = _e_ac_bypass
else:
    e_ac = _e_ac_base

p_stc   = st.session_state.get("P_stc_kW_sistema", 0.0)
n_pan   = st.session_state.get("N_paneles_final", 0)
ciudad  = st.session_state.get("tmy_ciudad", "—")
n_anos  = 25     # vida útil estándar BIPV — IEC 61730

if e_ac > 0:
    _sufijo = (
        f" | 🏗️ Sistema multi-superficie ({_area_ms:.1f} m²)" if (_multisup_ok and _e_ac_multisup > 0)
        else " | ⚡ Corrección bypass aplicada"                 if (_bypass_ok and _e_ac_bypass > 0)
        else ""
    )
    st.success(
        f"✅ Producción: **{e_ac:,.0f} kWh/año** | "
        f"Sistema: **{p_stc:.2f} kWp** ({n_pan} módulos) | Ciudad: **{ciudad}**"
        + _sufijo
    )
else:
    st.warning(
        "⚠️ Ejecuta 📊 Producción primero para obtener E_ac. "
        "Puedes ingresar la energía manualmente para explorar el cálculo."
    )
    e_ac  = st.number_input("Energía AC anual (kWh/año)", 100.0, 2e6, 50_000.0, 1000.0)
    p_stc = st.number_input("Potencia instalada (kWp)", 0.1, 5000.0, 40.0, 0.5)

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 0 — GESTIÓN DEL FACTOR SIN (TAREA #42)
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("🔧 Gestión del factor de emisión SIN Colombia — actualización anual", expanded=False):
    st.markdown("""
    **¿Por qué es crítico mantener este factor actualizado?**
    XM S.A. E.S.P. (operador del SIN) y la UPME publican el factor de emisión oficial
    cada año. Si el factor que usa la calculadora tiene más de 2 años de antigüedad,
    sus cálculos de CO₂ evitado y el valor de bonos de carbono estarán desactualizados —
    lo que puede invalidar un reporte ante el RETC o ante un auditor VCS.
    """)

    _factor_guardado = float(st.session_state.get("co2_factor_sin_custom", FACTOR_CO2_COLOMBIA_KG_KWH))
    _fecha_guardada  = st.session_state.get("co2_factor_fecha", "UPME Resolución 520/2019 (año 2022)")

    # Calcular antigüedad
    _anio_factor = 2022
    try:
        _anio_factor = int(_fecha_guardada.split("año")[-1].strip().split(")")[0].strip())
    except Exception:
        pass
    _anios_antiguo = datetime.datetime.now().year - _anio_factor
    _alerta_color  = "🔴" if _anios_antiguo >= 2 else ("🟡" if _anios_antiguo >= 1 else "🟢")

    st.info(
        f"{_alerta_color} **Factor activo:** {_factor_guardado:.4f} kg CO₂/kWh  "
        f"({_factor_guardado*1000:.1f} gCO₂/kWh) · "
        f"Fuente: **{_fecha_guardada}** · "
        f"Antigüedad: **{_anios_antiguo} año(s)**"
        + ("  ⚠️ — **Recomendado actualizar** — consulta XM o UPME." if _anios_antiguo >= 2 else "")
    )

    col_f1, col_f2 = st.columns([2, 3])
    with col_f1:
        nuevo_factor = st.number_input(
            "Nuevo factor SIN (kg CO₂/kWh)",
            min_value=0.05, max_value=1.0,
            value=_factor_guardado, step=0.001, format="%.4f",
            help=(
                "Fuente oficial: XM S.A. E.S.P. → www.xm.com.co → "
                "'Factor de Emisión de CO₂ del SIN'. "
                "También en UPME → 'Informe de Gestión de la Demanda'. "
                "Rango histórico Colombia: 0.100–0.185 kg/kWh (varía con hidrología). "
                "Año seco (El Niño) → mayor factor (más térmicas). "
                "Año húmedo → menor factor (más hidro)."
            ),
        )
    with col_f2:
        nueva_fecha = st.text_input(
            "Fuente y año del dato",
            value=_fecha_guardada,
            placeholder="Ej: XM S.A. E.S.P. Informe 2025 (año 2024)",
            help="Escribe la referencia exacta para trazabilidad en reportes ISO 14064 y RETC.",
        )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Guardar factor actualizado", use_container_width=True):
            st.session_state["co2_factor_sin_custom"] = nuevo_factor
            st.session_state["co2_factor_fecha"]      = nueva_fecha
            st.success(
                f"✅ Factor actualizado: **{nuevo_factor:.4f} kg CO₂/kWh** · "
                f"Fuente: {nueva_fecha}. "
                f"Recalcula la página para aplicarlo."
            )
    with col_btn2:
        if st.button("↩️ Restaurar valor oficial UPME 2022", use_container_width=True):
            st.session_state["co2_factor_sin_custom"] = FACTOR_CO2_COLOMBIA_KG_KWH
            st.session_state["co2_factor_fecha"]      = "UPME Resolución 520/2019 (año 2022)"
            st.info("Factor restaurado al valor oficial UPME 2022: 0.126 kg CO₂/kWh.")

    st.markdown("""
    **📌 Guía rápida para obtener el factor actualizado:**
    1. Ve a [www.xm.com.co](https://www.xm.com.co) → *Informes* → *Factor de Emisión del SIN*
    2. O consulta la UPME → *Publicaciones* → *Informe de Gestión Energética Nacional*
    3. El valor reportado es el **factor de emisión promedio anual** del SIN (gCO₂/kWh)
    4. Divídelo entre 1000 para convertirlo a kg CO₂/kWh e ingrésalo arriba
    5. El **factor marginal (CDM)** requiere el Margen Operativo y de Construcción de XM
    """)

# Leer factor activo (custom o default)
FACTOR_CO2_COLOMBIA_KG_KWH = float(
    st.session_state.get("co2_factor_sin_custom", FACTOR_CO2_COLOMBIA_KG_KWH)
)

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — SELECTOR DE METODOLOGÍA
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📐 1. Metodología y factor de emisión")

col_m1, col_m2 = st.columns([3, 2])

with col_m1:
    metodologia = st.radio(
        "Selecciona la metodología de referencia:",
        options=[
            "📊 GHG Protocol Scope 2 — Factor promedio SIN (0.126 kg/kWh)",
            "🏦 CDM / Bonos de Carbono — Factor marginal combinado (0.300 kg/kWh)",
        ],
        index=0,
        help=(
            "**GHG Protocol:** usa el factor promedio de la red (location-based). "
            "Es el método oficial para inventarios de GEI corporativos en Colombia "
            "(Ley 1931/2018, RETC, NAMA). Factor SIN: **0.126 kg CO₂/kWh** "
            "(fuente: XM S.A. E.S.P. / UPME).\n\n"
            "**CDM / Bonos:** usa el factor marginal combinado = (Margen Operativo + Margen de Construcción) / 2. "
            "Es el método UNFCCC para cuantificar reducciones certificadas de emisiones (CERs). "
            "Margen operativo ≈ 0.25 · Margen construcción ≈ 0.35 → CM ≈ 0.300 kg CO₂/kWh "
            "(Herramienta 07 UNFCCC CDM, 2023). Produce más bonos de carbono."
        ),
    )

factor_activo = (
    FACTOR_PROMEDIO_KG_KWH if "promedio" in metodologia.lower() else FACTOR_MARGINAL_KG_KWH
)

with col_m2:
    tasa_deg_co2 = st.slider(
        "Degradación módulos (%/año)",
        min_value=0.2, max_value=1.5, value=0.5, step=0.1,
        help="Igual que en Financiero. Afecta la producción acumulada en 25 años.",
    )
    precio_bono_usd = st.slider(
        "Precio bono de carbono (USD/tCO₂)",
        min_value=1.0, max_value=60.0, value=12.0, step=1.0,
        help=(
            "Mercado voluntario VCS/Gold Standard Colombia: USD 8–20/tCO₂ (2024). "
            "Mercado regulado (Sistema de Comercio de Emisiones propuesto): USD 10–25/tCO₂. "
            "Mercado europeo EU ETS referencia: USD 50–80/tCO₂."
        ),
    )
    tipo_cambio = float(st.session_state.get("tipo_cambio", 3400.0))

# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULOS PRINCIPALES
# ─────────────────────────────────────────────────────────────────────────────

# Producción año a año con degradación
anos_array  = np.arange(1, n_anos + 1)
e_ac_anual  = e_ac * (1 - tasa_deg_co2 / 100) ** (anos_array - 1)   # kWh/año cada año
e_ac_total  = e_ac_anual.sum()     # kWh acumulados en vida útil

# CO₂ evitado (factor activo)
co2_anual_kg      = e_ac * factor_activo                     # kg/año — año 1
co2_anual_t       = co2_anual_kg / 1000                      # tCO₂/año — año 1
co2_total_t       = (e_ac_anual * factor_activo / 1000).sum()  # tCO₂ acumulado 25 años

# CO₂ con ambos factores (para comparar)
co2_total_prom_t  = (e_ac_anual * FACTOR_PROMEDIO_KG_KWH  / 1000).sum()
co2_total_marg_t  = (e_ac_anual * FACTOR_MARGINAL_KG_KWH  / 1000).sum()

# Valor en bonos de carbono
valor_bonos_usd   = co2_total_t * precio_bono_usd
valor_bonos_cop   = valor_bonos_usd * tipo_cambio

# Intensidad del sistema
intensidad_sistema = factor_activo * 1000  # gCO₂/kWh (para comparar con IPCC)

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2 — BANNER DE 4 MÉTRICAS GRANDES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🎯 2. Emisiones evitadas — resumen ejecutivo")

col_b1, col_b2, col_b3, col_b4 = st.columns(4)
col_b1.metric(
    "CO₂ evitado · Año 1",
    f"{co2_anual_t:.2f} tCO₂/año",
    delta=f"{co2_anual_kg:,.0f} kg CO₂",
    delta_color="off",
    help="Toneladas de CO₂ equivalente evitadas en el primer año de operación."
)
col_b2.metric(
    f"CO₂ evitado · {n_anos} años",
    f"{co2_total_t:,.1f} tCO₂",
    delta=f"Factor: {factor_activo*1000:.0f} gCO₂/kWh",
    delta_color="off",
    help=f"Total acumulado en vida útil de {n_anos} años con degradación {tasa_deg_co2}%/año."
)
col_b3.metric(
    "Valor en bonos de carbono",
    f"USD {valor_bonos_usd:,.0f}",
    delta=f"$ {valor_bonos_cop/1e6:.2f} M COP",
    delta_color="off",
    help=f"A USD {precio_bono_usd}/tCO₂. Ajusta el slider para simular escenarios de precio."
)
col_b4.metric(
    "Intensidad BIPV fachada",
    f"30 gCO₂/kWh",
    delta=f"vs {int(intensidad_sistema)} gCO₂/kWh SIN Colombia",
    delta_color="off",
    help="Huella del ciclo de vida del sistema BIPV (IPCC AR6 WG III). "
         "Incluye fabricación, transporte e instalación del módulo BIPV laminado."
)

# ── Comparativo ambos factores en info ────────────────────────────────────────
if factor_activo == FACTOR_PROMEDIO_KG_KWH:
    st.info(
        f"📊 **Metodología activa: GHG Protocol Scope 2 (factor promedio SIN)** — "
        f"0.126 kg CO₂/kWh · {co2_total_prom_t:,.1f} tCO₂ en {n_anos} años. "
        f"Con factor marginal (CDM) serían **{co2_total_marg_t:,.1f} tCO₂** "
        f"(+{(co2_total_marg_t/co2_total_prom_t-1)*100:.0f}% más — relevante para bonos de carbono)."
    )
else:
    st.info(
        f"🏦 **Metodología activa: CDM / Factor marginal combinado** — "
        f"0.300 kg CO₂/kWh · {co2_total_marg_t:,.1f} tCO₂ en {n_anos} años. "
        f"Con factor promedio SIN (GHG Protocol) serían **{co2_total_prom_t:,.1f} tCO₂** "
        f"(para inventario corporativo Ley 1931)."
    )

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — EQUIVALENCIAS DE IMPACTO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🌍 3. Equivalencias de impacto (vida útil del proyecto)")

st.caption(
    f"Basado en **{co2_total_t:,.1f} tCO₂** evitadas en {n_anos} años · "
    f"Factor activo: {factor_activo*1000:.0f} gCO₂/kWh"
)

# Calcular equivalencias
arboles        = co2_total_t * 1000 / KG_CO2_ARBOL_ANUAL / n_anos   # árboles permanentes equivalentes
hogares        = e_ac_total / KWH_HOGAR_ANUAL                         # hogares abastecidos
km_vehiculo    = co2_total_t * 1000 / KG_CO2_KM_VEHICULO / 1000       # miles de km
vuelos_bogmde  = co2_total_t * 1000 / KG_CO2_VUELO_BOG_MDE
barriles       = co2_total_t * 1000 / KG_CO2_BARRIL_PETROLEO
cilindros_glp  = co2_total_t * 1000 / KG_CO2_CILINDRO_GLP

eq_data = [
    {
        "Equivalencia": "🌳 Árboles nativos colombianos",
        "Valor": f"{arboles:,.0f} árboles",
        "Detalle": f"plantados permanentemente durante {n_anos} años",
        "Fuente": "IDEAM — absorción media 22 kgCO₂/árbol/año (Bosque Húmedo Tropical)",
        "_num": arboles,
    },
    {
        "Equivalencia": "🏠 Hogares colombianos abastecidos",
        "Valor": f"{hogares:,.1f} hogares × 1 año",
        "Detalle": f"o {hogares/n_anos:.1f} hogares abastecidos durante {n_anos} años",
        "Fuente": "UPME 2022 — consumo residencial promedio 130 kWh/mes",
        "_num": hogares,
    },
    {
        "Equivalencia": "🚗 Km en vehículo a gasolina",
        "Valor": f"{km_vehiculo:,.0f} mil km no recorridos",
        "Detalle": f"≈ {km_vehiculo*1000/20_000:.0f} años de un auto promedio (20.000 km/año)",
        "Fuente": "IDEAM FECOC 2022 — 0.162 kgCO₂/km (gasolina corriente)",
        "_num": km_vehiculo,
    },
    {
        "Equivalencia": "✈️ Vuelos Bogotá–Medellín (ida)",
        "Valor": f"{vuelos_bogmde:,.0f} vuelos evitados",
        "Detalle": f"≈ {vuelos_bogmde/365:.1f} años de vuelos diarios Avianca/LATAM",
        "Fuente": "ICAO Carbon Emissions Calculator 2023 — 89 kgCO₂/pasajero BOG–MDE",
        "_num": vuelos_bogmde,
    },
    {
        "Equivalencia": "🛢️ Barriles de petróleo colombiano",
        "Valor": f"{barriles:,.0f} barriles no quemados",
        "Detalle": f"≈ USD {barriles*80/1000:,.0f} k en crudo (a USD 80/barril referencia)",
        "Fuente": "EPA AP-42 · 431.7 kgCO₂/barril (API 31°)",
        "_num": barriles,
    },
    {
        "Equivalencia": "🔵 Cilindros GLP (40 lb)",
        "Valor": f"{cilindros_glp:,.0f} cilindros no consumidos",
        "Detalle": f"≈ {cilindros_glp/12:.0f} hogares × {n_anos} años (1 cil/mes promedio)",
        "Fuente": "IPCC 2006 Vol. 2 · 55.6 kgCO₂/cilindro 40 lb",
        "_num": cilindros_glp,
    },
]

# Tabla de equivalencias
df_eq = pd.DataFrame([{
    "Equivalencia": r["Equivalencia"],
    "Resultado": r["Valor"],
    "Interpretación": r["Detalle"],
    "Fuente": r["Fuente"],
} for r in eq_data])
st.dataframe(df_eq, use_container_width=True, hide_index=True)

# ── Gráfica de barras horizontales — impacto visual ──────────────────────────
with st.expander("📊 Ver gráfica de equivalencias", expanded=True):
    nombres  = [r["Equivalencia"].split(" ", 1)[1] for r in eq_data]
    valores  = [r["_num"] for r in eq_data]
    # Normalizar a % del mayor para hacer las barras comparables
    v_max    = max(valores)
    pcts     = [v / v_max * 100 for v in valores]
    labels   = [r["Valor"] for r in eq_data]
    colores  = [COLOR_VERDE, COLOR_AZUL, COLOR_AMBAR, COLOR_ROJO, "#6A1B9A", "#00695C"]

    fig_eq = go.Figure(go.Bar(
        x=pcts,
        y=nombres,
        orientation="h",
        marker_color=colores,
        text=labels,
        textposition="outside",
        textfont=dict(size=12),
        hovertemplate="%{y}<br>%{text}<extra></extra>",
    ))
    fig_eq.update_layout(
        title=f"Impacto ambiental equivalente — {co2_total_t:,.1f} tCO₂ evitadas en {n_anos} años",
        xaxis=dict(title="Escala relativa (%)", showgrid=True, gridcolor="#F0F0F0"),
        yaxis=dict(tickfont=dict(size=12)),
        height=380,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(r=160),
        showlegend=False,
    )
    st.plotly_chart(fig_eq, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 — EVOLUCIÓN ANUAL CO₂ EVITADO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📈 4. Evolución anual de emisiones evitadas")

co2_prom_anual = e_ac_anual * FACTOR_PROMEDIO_KG_KWH / 1000   # tCO₂/año — factor promedio
co2_marg_anual = e_ac_anual * FACTOR_MARGINAL_KG_KWH / 1000   # tCO₂/año — factor marginal
co2_prom_acum  = np.cumsum(co2_prom_anual)
co2_marg_acum  = np.cumsum(co2_marg_anual)

fig_co2 = go.Figure()

# Banda entre factor promedio y marginal
fig_co2.add_trace(go.Scatter(
    x=anos_array, y=co2_marg_acum,
    name="Factor marginal CDM (0.300 kg/kWh)",
    line=dict(color="#1565C0", width=1.5, dash="dot"),
    mode="lines",
    fill=None,
))
fig_co2.add_trace(go.Scatter(
    x=anos_array, y=co2_prom_acum,
    name="Factor promedio SIN (0.126 kg/kWh)",
    line=dict(color=COLOR_VERDE, width=2.5),
    fill="tonexty",
    fillcolor="rgba(21,101,192,0.10)",
    mode="lines",
))

fig_co2.update_layout(
    xaxis_title="Año",
    yaxis_title="CO₂ acumulado evitado (tCO₂)",
    height=400,
    legend=dict(orientation="h", y=-0.22),
    plot_bgcolor="white",
    paper_bgcolor="white",
    hovermode="x unified",
)
st.plotly_chart(fig_co2, use_container_width=True)
st.caption(
    "🔵 Banda azul = rango de incertidumbre metodológica entre el "
    "factor promedio SIN (GHG Protocol) y el factor marginal combinado (CDM/bonos de carbono). "
    "El proyecto produce entre ambas curvas dependiendo del método de reporte."
)

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5 — INTENSIDAD VS OTRAS TECNOLOGÍAS (IPCC AR6)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("⚡ 5. Intensidad de carbono vs otras tecnologías — IPCC AR6 WG III")

df_ipcc = pd.DataFrame(
    list(INTENSIDAD_IPCC.items()),
    columns=["Tecnología", "gCO₂eq/kWh"]
).sort_values("gCO₂eq/kWh", ascending=True)

colores_ipcc = []
for _, row in df_ipcc.iterrows():
    if row["gCO₂eq/kWh"] <= 50:
        colores_ipcc.append("#2E7D32")   # verde — renovables / nuclear
    elif row["gCO₂eq/kWh"] <= 300:
        colores_ipcc.append("#F57F17")   # ámbar — gas
    else:
        colores_ipcc.append("#C62828")   # rojo — carbón / diesel

fig_ipcc = go.Figure(go.Bar(
    x=df_ipcc["gCO₂eq/kWh"],
    y=df_ipcc["Tecnología"],
    orientation="h",
    marker_color=colores_ipcc,
    text=[f"{v} gCO₂/kWh" for v in df_ipcc["gCO₂eq/kWh"]],
    textposition="outside",
    hovertemplate="%{y}: %{x} gCO₂eq/kWh<extra></extra>",
))

# Destacar BIPV
fig_ipcc.add_vline(
    x=FACTOR_PROMEDIO_KG_KWH * 1000,
    line_color="#1565C0", line_dash="dash",
    annotation_text=f"Factor SIN Colombia: {FACTOR_PROMEDIO_KG_KWH*1000:.0f} g/kWh",
    annotation_position="top right",
    annotation_font_color="#1565C0",
)

fig_ipcc.update_layout(
    title="Ciclo de vida completo (fabricación + operación + desmantelamiento)",
    xaxis_title="gCO₂eq/kWh",
    height=420,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(r=20),
    showlegend=False,
)
st.plotly_chart(fig_ipcc, use_container_width=True)
st.caption(
    "Fuente: IPCC AR6 WG III (2022) Tabla A.III.2 — Análisis de ciclo de vida (ACV). "
    "BIPV fachada incluye fabricación del módulo laminado de vidrio, estructura de muro cortina "
    "y transporte. La línea azul muestra el factor promedio del SIN Colombia como referencia."
)

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 6 — MERCADO DE CARBONO COLOMBIA
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("💵 6. Mercado de carbono — Colombia y estándares voluntarios")

col_mc1, col_mc2 = st.columns([3, 2])

with col_mc1:
    st.markdown(f"""
| Mercado | Factor aplicable | Precio referencia | Valor proyecto ({n_anos} años) |
|---|---|---|---|
| **GHG Protocol / RETC** | 0.126 kg/kWh (SIN promedio) | — (inventario, no transaccional) | **{co2_total_prom_t:,.1f} tCO₂ declaradas** |
| **Mercado voluntario VCS** | 0.300 kg/kWh (CDM marginal) | USD 8–20/tCO₂ | **USD {co2_total_marg_t*12:,.0f}** (a USD 12/t) |
| **Mercado voluntario Gold Standard** | 0.300 kg/kWh | USD 15–30/tCO₂ | **USD {co2_total_marg_t*18:,.0f}** (a USD 18/t) |
| **Impuesto carbono Colombia** | Emisiones directas (*) | COP 25.000/tCO₂ (2024) | **$ {co2_total_prom_t*25_000/1e6:.1f} M COP** ahorro |
| **NAMA Sector Energía Colombia** | 0.126 kg/kWh | No transaccional | Reporte NDC obligatorio |
| **Precio usuario (seleccionado)** | {factor_activo:.3f} kg/kWh | **USD {precio_bono_usd:.0f}/tCO₂** | **USD {valor_bonos_usd:,.0f}  ·  $ {valor_bonos_cop/1e6:.2f} M COP** |
    """)
    st.caption(
        "(*) El impuesto al carbono de Colombia (Ley 1819/2016, Art. 221) aplica a "
        "combustibles fósiles directamente quemados, NO a la electricidad de la red. "
        "Para proyectos BIPV el beneficio es indirecto: se evita el consumo de una red "
        "que sí tiene emisiones."
    )

with col_mc2:
    # Mini-simulador precio bono
    st.markdown("**Simulador de valor en bonos de carbono**")
    precios = [5, 8, 10, 12, 15, 18, 20, 25, 30, 40, 50, 60]
    valores_sim = [co2_total_marg_t * p for p in precios]
    fig_sim = go.Figure(go.Scatter(
        x=precios, y=valores_sim,
        mode="lines+markers",
        line=dict(color=COLOR_VERDE, width=2),
        marker=dict(size=6),
        hovertemplate="USD %{x}/tCO₂ → USD %{y:,.0f}<extra></extra>",
    ))
    fig_sim.add_vline(
        x=precio_bono_usd,
        line_color=COLOR_AMBAR, line_dash="dash",
        annotation_text=f"${precio_bono_usd:.0f}/t → USD {valor_bonos_usd:,.0f}",
        annotation_position="top left",
        annotation_font_size=10,
    )
    fig_sim.update_layout(
        xaxis_title="Precio bono (USD/tCO₂)",
        yaxis_title="Valor total bonos (USD)",
        height=280,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=0, r=10, t=10, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig_sim, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 7 — MARCO REGULATORIO COLOMBIA
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📜 7. Marco regulatorio colombiano e internacional", expanded=False):
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("""
**🇨🇴 Colombia**

| Norma | Relevancia para este proyecto |
|---|---|
| **Ley 1931/2018** | Gestión del cambio climático — obliga a entidades a reportar y reducir GEI |
| **NDC Colombia 2030** | Meta de reducir 51% emisiones GEI (actualizada 2020) — sector energía es clave |
| **Ley 1715/2014** | Beneficios fiscales a FNCE — vinculado a reducción CO₂ |
| **Ley 1819/2016** | Impuesto al carbono combustibles fósiles (COP 25.000/tCO₂ en 2024) |
| **RETC** | Registro de Emisiones y Transferencias de Contaminantes — reporte obligatorio empresas |
| **REDD+ Colombia** | Marco para reducción de emisiones por deforestación — complementario |
| **UPME Resolución 520/2019** | Factor de emisión SIN = 0.126 kgCO₂/kWh oficial para cálculos |
        """)
    with col_r2:
        st.markdown("""
**🌐 Internacional**

| Estándar | Aplicación |
|---|---|
| **GHG Protocol Corporate Standard** | Scope 2 · Location-based method · Inventarios corporativos |
| **ISO 14064-1:2018** | Cuantificación y reporte de GEI a nivel organizacional |
| **ISO 14067:2018** | Huella de carbono de productos (ACV módulo BIPV) |
| **UNFCCC CDM — AMS-I.D** | Metodología pequeña escala renovable < 15 MW |
| **UNFCCC Tool 07** | Cálculo factor de emisión de red eléctrica (OM + BM) |
| **IPCC AR6 WG III** | Intensidades de ciclo de vida por tecnología generación |
| **VCS (Verra)** | Verified Carbon Standard — bonos voluntarios reconocidos |
| **Gold Standard** | Bonos voluntarios + co-beneficios ODS |
        """)

    st.markdown("""
---
**📌 Nota sobre el factor SIN Colombia (0.126 kgCO₂/kWh)**

Colombia tiene uno de los factores de emisión de red **más bajos de América Latina** gracias a 
su matriz eléctrica dominada por hidroeléctricas (~65–70%). Esto tiene dos implicaciones opuestas:

1. ✅ **Para el inventario corporativo (GHG Protocol / Ley 1931):** el factor bajo refleja la realidad — 
   desplazar kWh de la red colombiana evita *menos* CO₂ que en matrices más carbonizadas.

2. 💡 **Para los bonos de carbono (CDM / VCS):** el factor **marginal** (0.30 kg/kWh) es más relevante 
   porque captura la tecnología **marginal** que entra o sale del despacho energético. En épocas de 
   sequía (fenómeno El Niño) la marginal es gas o diesel, no hidro. Por eso el CM ≈ 0.30 kg/kWh.

3. 🌦️ **Riesgo climático:** con el cambio climático, el factor del SIN Colombia tenderá a **aumentar** 
   en el futuro (más períodos secos, más uso de térmicas). Los proyectos BIPV que se instalen hoy 
   serán cada vez más valiosos en términos de carbono evitado.
    """)

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 8 — CONTRIBUCIÓN AL NDC COLOMBIA 2030
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🇨🇴 8. Contribución al NDC Colombia 2030")

# Meta NDC: reducir ~169 Mt CO₂eq en 2030 (51% vs escenario tendencial)
# Sector energía: ~35% de las emisiones = ~59 Mt a reducir del sector energía
META_NDC_TOTAL_MT   = 169.0    # Mt CO₂eq total Colombia 2030
META_SECTOR_MT      = 59.0     # Mt CO₂eq sector energía (≈35% del total)
EMIS_NAL_MT_AÑO     = 258.0    # Mt CO₂eq/año Colombia (IDEAM BUR4 2023)

pct_ndc_total   = co2_total_t / (META_NDC_TOTAL_MT * 1e6) * 100
pct_ndc_sector  = co2_total_t / (META_SECTOR_MT   * 1e6) * 100
pct_emis_nac    = co2_anual_t / (EMIS_NAL_MT_AÑO  * 1e6) * 100

col_ndc1, col_ndc2, col_ndc3 = st.columns(3)
col_ndc1.metric(
    "% de la meta NDC total (169 MtCO₂)",
    f"{pct_ndc_total:.4f}%",
    delta=f"{co2_total_t:,.1f} / {META_NDC_TOTAL_MT*1e6:,.0f} tCO₂",
    delta_color="off",
    help="Meta NDC Colombia 2030: reducir 169 Mt CO₂eq respecto al escenario tendencial."
)
col_ndc2.metric(
    "% de la meta sector energía (59 Mt)",
    f"{pct_ndc_sector:.4f}%",
    delta=f"{co2_total_t:,.1f} / {META_SECTOR_MT*1e6:,.0f} tCO₂",
    delta_color="off",
    help="El sector energía debe reducir ~59 MtCO₂eq para cumplir el NDC."
)
col_ndc3.metric(
    "% emisiones nacionales (año 1)",
    f"{pct_emis_nac:.6f}%",
    delta=f"{co2_anual_t:.2f} / {EMIS_NAL_MT_AÑO*1e6:,.0f} tCO₂ anuales",
    delta_color="off",
    help="Colombia emite ~258 Mt CO₂eq/año (IDEAM BUR4 2023, año base 2018)."
)

st.info(
    f"💡 **Escalamiento:** si se replicara este proyecto en **{1/pct_ndc_total*100:.0f} edificios** similares "
    f"en Colombia, se cubriría el 100% de la meta NDC del sector energía. "
    f"Si se instalaran **{META_SECTOR_MT*1e6/co2_total_t:,.0f} sistemas** idénticos, "
    f"se compensaría toda la meta NDC del sector energía en {n_anos} años."
)

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 9 — RASTREO CO₂ REAL VS PROYECTADO (TAREA #43)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📡 9. Seguimiento CO₂ real vs proyectado — operación del sistema")
st.caption(
    "Cuando el inversor lleva meses en operación, ingresa la producción mensual real "
    "para ver cuánto CO₂ evitaste realmente vs lo que el modelo proyectó. "
    "Este dato es obligatorio para reportes GHG Protocol, auditorías VCS y RETC."
)

# Producción mensual proyectada desde simulación
_meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

# Si hay producción simulada por mes, la usamos; si no, distribución uniforme
_prod_mensual_sim = st.session_state.get("produccion_mensual_kWh", None)
if _prod_mensual_sim is not None and len(_prod_mensual_sim) == 12:
    _proy_mes = list(_prod_mensual_sim)
else:
    _proy_mes = [e_ac / 12.0] * 12

with st.expander("📥 Ingresar producción real del inversor (mes a mes)", expanded=False):
    st.markdown(
        "**¿Por qué llevar este registro?** Cada kWh real validado por el inversor tiene mayor "
        "credibilidad ante un auditor VCS o un banco que los kWh simulados. Con estos datos "
        "puedes generar un reporte mensual de CO₂ evitado con trazabilidad completa."
    )

    _anio_actual = datetime.datetime.now().year
    anio_seguim = st.selectbox(
        "Año de operación",
        options=list(range(_anio_actual - 2, _anio_actual + 3)),
        index=2,
        key="co2_anio_seguim",
    )

    # Tabla editable de 12 meses
    _defaults = {m: 0.0 for m in _meses}
    _saved    = st.session_state.get("co2_kwh_real_dict", _defaults)

    cols_mes = st.columns(4)
    kwh_real_dict = {}
    for i, mes in enumerate(_meses):
        with cols_mes[i % 4]:
            kwh_real_dict[mes] = st.number_input(
                f"{mes} (kWh)",
                min_value=0.0, max_value=float(e_ac),
                value=float(_saved.get(mes, 0.0)),
                step=10.0,
                key=f"co2_real_{mes}",
            )
    st.session_state["co2_kwh_real_dict"] = kwh_real_dict

# Calcular métricas reales
kwh_real_list  = [kwh_real_dict.get(m, 0.0) for m in _meses]
kwh_real_total = sum(kwh_real_list)
meses_con_dato = sum(1 for v in kwh_real_list if v > 0)

if meses_con_dato > 0:
    # CO₂ real vs proyectado por mes
    co2_real_mes  = [v * factor_activo / 1000 for v in kwh_real_list]      # tCO₂/mes real
    co2_proy_mes  = [v * factor_activo / 1000 for v in _proy_mes]          # tCO₂/mes proyectado
    co2_real_acum = sum(co2_real_mes[:meses_con_dato])
    co2_proy_acum = sum(co2_proy_mes[:meses_con_dato])
    cumpl_pct     = (co2_real_acum / co2_proy_acum * 100) if co2_proy_acum > 0 else 0
    delta_co2     = co2_real_acum - co2_proy_acum
    kwh_real_anual_proy = kwh_real_total / meses_con_dato * 12 if meses_con_dato > 0 else 0

    # Métricas resumen
    cr1, cr2, cr3, cr4 = st.columns(4)
    cr1.metric(
        f"CO₂ real ({meses_con_dato} mes{'es' if meses_con_dato>1 else ''})",
        f"{co2_real_acum:.3f} tCO₂",
        delta=f"{kwh_real_total:,.0f} kWh reales",
        delta_color="off",
    )
    cr2.metric(
        "CO₂ proyectado (mismo período)",
        f"{co2_proy_acum:.3f} tCO₂",
        delta=f"{sum(_proy_mes[:meses_con_dato]):,.0f} kWh proyectados",
        delta_color="off",
    )
    _delta_label = f"+{delta_co2:.3f} t por encima" if delta_co2 >= 0 else f"{delta_co2:.3f} t por debajo"
    cr3.metric(
        "Cumplimiento vs proyectado",
        f"{cumpl_pct:.1f}%",
        delta=_delta_label,
        delta_color="normal" if delta_co2 >= 0 else "inverse",
        help="≥ 90% = excelente · 75–89% = aceptable · < 75% = revisar sombreado u O&M",
    )
    pr_real_pct = (kwh_real_total / (e_ac * meses_con_dato / 12) * 100) if e_ac > 0 else 0
    cr4.metric(
        "PR real vs PR simulado",
        f"{pr_real_pct:.1f}%",
        delta="✅ Dentro del rango" if 85 <= pr_real_pct <= 110 else "⚠️ Verificar sistema",
        delta_color="normal" if 85 <= pr_real_pct <= 110 else "inverse",
        help="Performance Ratio real respecto al proyectado. Rango saludable: 85–110%.",
    )

    # Interpretación persuasiva
    if cumpl_pct >= 95:
        st.success(
            f"🏆 **Rendimiento sobresaliente** — El sistema está superando las expectativas "
            f"({cumpl_pct:.1f}% del CO₂ proyectado en {meses_con_dato} mes{'es' if meses_con_dato>1 else ''}). "
            f"Estos datos son ideales para un **reporte GHG Protocol auditado** o para solicitar "
            f"**créditos VCS** con solidez técnica demostrada."
        )
    elif cumpl_pct >= 80:
        st.info(
            f"✅ **Rendimiento satisfactorio** — {cumpl_pct:.1f}% de cumplimiento. "
            f"El sistema opera dentro del rango normal. "
            f"Una pequeña diferencia puede deberse a días nublados no capturados en el TMY. "
            f"Continúa el registro mensual para consolidar la trazabilidad ante auditores."
        )
    elif meses_con_dato >= 1:
        st.warning(
            f"⚠️ **Cumplimiento bajo ({cumpl_pct:.1f}%)** — El sistema está produciendo "
            f"considerablemente menos CO₂ evitado del proyectado. Posibles causas: "
            f"sombreado no modelado, suciedad acumulada en módulos, falla de inversor "
            f"o consumo parasítico. Revisa la página 🔀 Mismatch y el O&M registrado."
        )

    # Gráfica barras agrupadas: real vs proyectado
    _meses_con = [_meses[i] for i in range(12) if kwh_real_list[i] > 0 or _proy_mes[i] > 0]
    _co2_r     = [co2_real_mes[i]*1000 for i in range(12) if kwh_real_list[i] > 0 or _proy_mes[i] > 0]
    _co2_p     = [co2_proy_mes[i]*1000 for i in range(12) if kwh_real_list[i] > 0 or _proy_mes[i] > 0]

    fig_real = go.Figure()
    fig_real.add_trace(go.Bar(
        name="Proyectado (simulación)", x=_meses_con, y=_co2_p,
        marker_color="#90CAF9", opacity=0.8,
        hovertemplate="%{x}: %{y:.1f} kgCO₂<extra>Proyectado</extra>",
    ))
    fig_real.add_trace(go.Bar(
        name="Real (inversor)", x=_meses_con, y=_co2_r,
        marker_color=COLOR_VERDE,
        hovertemplate="%{x}: %{y:.1f} kgCO₂<extra>Real</extra>",
    ))
    fig_real.add_hline(
        y=sum(_co2_p)/len(_co2_p) if _co2_p else 0,
        line_dash="dot", line_color="#1565C0",
        annotation_text="Promedio proyectado",
        annotation_position="top right",
    )
    fig_real.update_layout(
        barmode="group",
        title=f"CO₂ evitado real vs proyectado — {anio_seguim}  ({factor_activo*1000:.0f} gCO₂/kWh)",
        xaxis_title="Mes",
        yaxis_title="kgCO₂ evitado",
        height=360,
        legend=dict(orientation="h", y=-0.22),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
    )
    st.plotly_chart(fig_real, use_container_width=True)

    # Tabla exportable
    with st.expander("📋 Tabla mensual detallada — exportable para auditoría"):
        df_real = pd.DataFrame({
            "Mes":                 _meses,
            "kWh proyectado":      [round(v, 1) for v in _proy_mes],
            "kWh real (inversor)": [round(v, 1) for v in kwh_real_list],
            "kgCO₂ proyectado":    [round(v*factor_activo, 2) for v in _proy_mes],
            "kgCO₂ real":          [round(v*factor_activo, 2) for v in kwh_real_list],
            "Cumplimiento (%)":    [
                round(kwh_real_list[i]/(_proy_mes[i] or 1)*100, 1) if _proy_mes[i] > 0 else 0
                for i in range(12)
            ],
        })
        st.dataframe(
            df_real.style.format({
                "kWh proyectado": "{:,.1f}",
                "kWh real (inversor)": "{:,.1f}",
                "kgCO₂ proyectado": "{:.2f}",
                "kgCO₂ real": "{:.2f}",
                "Cumplimiento (%)": "{:.1f}%",
            }).background_gradient(subset=["Cumplimiento (%)"], cmap="RdYlGn", vmin=50, vmax=110),
            use_container_width=True, hide_index=True,
        )
        st.caption(
            f"Factor de emisión activo: {factor_activo:.4f} kg CO₂/kWh · "
            f"Fuente: {st.session_state.get('co2_factor_fecha','UPME 2022')} · "
            f"Metodología: {co2_metodologia} · "
            f"Referencia: UNFCCC CDM AMS-I.D / GHG Protocol Scope 2 Location-based."
        )

    # Guardar resultados reales en session_state
    st.session_state["co2_real_ok"]          = True
    st.session_state["co2_real_acum_t"]      = co2_real_acum
    st.session_state["co2_cumplimiento_pct"] = cumpl_pct
else:
    st.info(
        "📌 **Aún no hay datos reales ingresados.** Cuando el sistema lleve al menos un mes "
        "de operación, ingresa los kWh del inversor en el panel superior para activar "
        "el seguimiento de CO₂ real. Este registro transforma tus estimaciones en "
        "evidencia verificable para reportes corporativos y bonos de carbono."
    )
    st.session_state["co2_real_ok"] = False

# ─────────────────────────────────────────────────────────────────────────────
# GUARDAR EN SESSION STATE PARA REPORTE PDF
# ─────────────────────────────────────────────────────────────────────────────
st.session_state["co2_factor_kg_kwh"]      = factor_activo
st.session_state["co2_factor_fecha"]       = st.session_state.get("co2_factor_fecha", "UPME Resolución 520/2019 (año 2022)")
st.session_state["co2_metodologia"]        = "GHG Protocol" if "promedio" in metodologia.lower() else "CDM Marginal"
st.session_state["co2_anual_t"]            = co2_anual_t
st.session_state["co2_total_t"]            = co2_total_t
st.session_state["co2_total_prom_t"]       = co2_total_prom_t
st.session_state["co2_total_marg_t"]       = co2_total_marg_t
st.session_state["co2_arboles_equiv"]      = arboles
st.session_state["co2_hogares_equiv"]      = hogares
st.session_state["co2_km_vehiculo_equiv"]  = km_vehiculo
st.session_state["co2_valor_bonos_usd"]    = valor_bonos_usd
st.session_state["co2_precio_bono_usd"]    = precio_bono_usd
st.session_state["impacto_co2_ok"]         = True
