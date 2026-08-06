"""
Calculadora BIPV — Innovación Química / Colombia
Streamlit app principal.
"""
import streamlit as st

st.set_page_config(
    page_title="Calculadora BIPV Colombia",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)
from utils.ui import bloquear_traduccion
bloquear_traduccion()

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

# ── Subtítulo dinámico — solo muestra panel/inversor si fueron configurados ───
# Si el usuario no ha corrido Motor IV ni Dimensionamiento en esta sesión,
# los valores son los defaults y no corresponden al proyecto real.
_PANEL_DEFAULT    = "ASP-ST1-T40"
_INVERSOR_DEFAULT = "Growatt-MID15KTL3-X"
_panel_home    = st.session_state.get("panel_nombre",    _PANEL_DEFAULT)
_inversor_home = st.session_state.get("inversor_nombre", _INVERSOR_DEFAULT)
_sistema_conf  = st.session_state.get("simulacion_ok", False) or \
                 st.session_state.get("produccion_ok",  False) or \
                 bool(st.session_state.get("N_serie") and
                      st.session_state.get("panel_nombre") != _PANEL_DEFAULT)

if _sistema_conf:
    st.markdown(
        f"**Panel:** {_panel_home}  •  "
        f"**Inversor:** {_inversor_home}  •  "
        "**Motor físico:** De Soto 2006 + pvlib"
    )
else:
    _tipo_sub = st.session_state.get("tipo_instalacion", "")
    _tipo_str = f" · {_tipo_sub}" if _tipo_sub else ""
    st.markdown(
        f"**Motor físico:** De Soto 2006 + pvlib{_tipo_str}  •  "
        "Configura el proyecto y ejecuta los módulos para ver el resumen aquí."
    )

col1, col2, col3 = st.columns(3)

with col1:
    # Prioridad de ubicación: municipio geocodificado > nombre proyecto > ciudad ref.
    _ciudad_home    = st.session_state.get("ciudad", "—")
    _municipio_home = st.session_state.get("municipio_predio", "").strip()
    _nombre_home    = st.session_state.get("nombre_proyecto", "").strip()
    _default_nom    = "Proyecto BIPV"

    if _municipio_home:
        _ubicacion_label = "📍 Ubicación del predio"
        _ubicacion_val   = _municipio_home
        _ubicacion_delta = f"Ref. TMY: {_ciudad_home}"
    elif _nombre_home and _nombre_home != _default_nom:
        _ubicacion_label = "📍 Proyecto"
        _ubicacion_val   = _nombre_home
        _ubicacion_delta = f"Ref. climática: {_ciudad_home}"
    else:
        _ubicacion_label = "🌡️ Ref. climática TMY"
        _ubicacion_val   = _ciudad_home
        _ubicacion_delta = "Ingresa coords del predio en Proyecto"

    st.metric(_ubicacion_label, _ubicacion_val,
              delta=_ubicacion_delta, delta_color="off")

with col2:
    _tipo_inst = st.session_state.get("tipo_instalacion", "Fachada BIPV")
    st.metric("📐 Área instalación", f"{st.session_state['area_fachada_m2']} m²",
              delta=_tipo_inst, delta_color="off")

with col3:
    energia = st.session_state.get("energia_anual_kWh")
    st.metric("⚡ Energía anual",
              f"{energia:,.0f} kWh/año" if energia else "—  (pendiente simulación)")

st.markdown("---")
st.markdown(
    "### Navegación\n"
    "Utilice el menú lateral para acceder a cada módulo:\n\n"
    "| Página | Función |\n"
    "|--------|--------|\n"
    "| 🏠 Proyecto | Ciudad de referencia climática, coordenadas del predio, tipo de instalación |\n"
    "| ☀️ Recurso Solar | Datos TMY desde PVGIS + irradiancia POA hora a hora |\n"
    "| 🔬 Motor IV | Curva I-V, modelo De Soto 2006, validación SDM vs ficha |\n"
    "| 📐 Dimensionamiento | String sizing con semáforo OK / ALERTA / FALLA |\n"
    "| 🔆 Motor Óptico | Factor óptico por sombra, suciedad y reflectividad |\n"
    "| ⚡ Desajuste | Análisis de mismatch MPPT por sombra parcial |\n"
    "| 📊 Producción | Simulación energética IEC 61724 hora a hora |\n"
    "| 💰 Financiero | VPN, TIR, Payback, LCOE — Ley 1715/2014 Colombia |\n"
    "| 💼 Presupuesto | CAPEX detallado por ítem + OPEX + estimación rápida paramétrica |\n"
    "| 🗺️ Vista 3D | Modelo 3D del sistema con sombreado |\n"
    "| 📄 Informe en PDF | Reporte técnico descargable con todos los resultados |\n"
    "| 🔋 Baterías y Balance | Dimensionamiento de almacenamiento y balance de energía |\n"
    "| 🌿 Impacto CO₂ | Huella de carbono evitada y equivalencias ambientales |\n"
    "| 💱 TRM en tiempo real | Tasa de cambio oficial del Banco de la República — actualización automática por hora |\n"
    "| 🔄 TRM sincronizada | Cambiar la TRM en Presupuesto la actualiza automáticamente en Financiero y viceversa |\n"
)
st.markdown("---")
st.caption(
    "Calculadora BIPV v1.0 — Motor SDM validado contra XLSM auditado (De Soto 2006). "
    "FF_max CdTe = 76.28% @ G=200 W/m² ✓"
)
