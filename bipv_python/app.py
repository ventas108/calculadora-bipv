"""
Calculadora BIPV — SolTech Energy LaTam / Colombia
Streamlit app principal.
"""
import streamlit as st

st.set_page_config(
    page_title="Calculadora BIPV Colombia",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inicialización de session_state global ─────────────────────────────────
defaults = {
    # Proyecto
    "ciudad":          "Bogotá",
    "nombre_proyecto": "Proyecto BIPV",
    "area_fachada_m2": 97.34,

    # Panel
    "panel_nombre":    "ASP-ST1-T40",

    # Inversor
    "inversor_nombre": "Growatt-MID15KTL3-X",

    # String sizing
    "N_serie":          8,
    "N_strings_tracker": 8,
    "T_min_diseno":    -5.0,
    "T_cel_realista":  36.35,
    "T_cel_extremo":   41.94,

    # Producción
    "energia_anual_kWh": None,
    "simulacion_ok":     False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Página principal ───────────────────────────────────────────────────────
st.title("☀️ Calculadora BIPV — Colombia")
st.markdown(
    "**Panel:** ASP-ST1-T40 (SolTech Energy LaTam, CdTe)  •  "
    "**Inversor:** Growatt MID15KTL3-X  •  "
    "**Motor físico:** De Soto 2006 + pvlib"
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🏙️ Ciudad", st.session_state["ciudad"])

with col2:
    st.metric("📐 Área fachada", f"{st.session_state['area_fachada_m2']} m²")

with col3:
    energia = st.session_state.get("energia_anual_kWh")
    st.metric("⚡ Energía anual",
              f"{energia:,.0f} kWh/año" if energia else "—  (pendiente simulación)")

st.markdown("---")
st.markdown(
    "### Navegación\n"
    "Usa el menú lateral para acceder a cada módulo:\n\n"
    "| Página | Función |\n"
    "|--------|--------|\n"
    "| 🏠 Proyecto | Configuración básica del proyecto |\n"
    "| ☀️ Recurso Solar | TMY + PVGIS + irradiancia POA |\n"
    "| 🔬 Motor IV | Curva I-V + validación SDM vs ficha |\n"
    "| 📐 Dimensionamiento | String sizing con semáforo OK/ALERTA/FALLA |\n"
    "| ⚡ Mismatch | Análisis de mismatch MPPT |\n"
    "| 📊 Producción | Simulación IEC 61724 hora a hora |\n"
    "| 💰 Financiero | VPN, TIR, Ley 1715/2014 Colombia |\n"
)

st.markdown("---")
st.caption(
    "Calculadora BIPV v1.0 — Motor SDM validado contra XLSM auditado (De Soto 2006). "
    "FF_max CdTe = 76.28% @ G=200 W/m² ✓"
)
