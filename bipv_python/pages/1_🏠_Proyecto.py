"""Página 1 — Configuración del proyecto."""
import streamlit as st
from datos.ciudades_colombia import CIUDADES, LISTA_CIUDADES

st.set_page_config(page_title="Proyecto — BIPV", page_icon="🏠", layout="wide")
st.title("🏠 Datos del Proyecto")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Identificación")
    nombre = st.text_input("Nombre del proyecto",
                           value=st.session_state.get("nombre_proyecto", "Proyecto BIPV"))
    ciudad = st.selectbox("Ciudad", LISTA_CIUDADES,
                          index=LISTA_CIUDADES.index(st.session_state.get("ciudad", "Bogotá")))
    area   = st.number_input("Área de fachada disponible (m²)",
                              min_value=10.0, max_value=5000.0,
                              value=float(st.session_state.get("area_fachada_m2", 97.34)),
                              step=1.0)

with col2:
    st.subheader("Datos del sitio")
    if ciudad in CIUDADES:
        c = CIUDADES[ciudad]
        st.info(
            f"**Latitud:** {c['lat']}°  |  **Longitud:** {c['lon']}°  |  "
            f"**Altitud:** {c['alt_m']} m\n\n"
            f"**GHI:** {c['GHI_kWh_m2_dia']} kWh/m²·día  |  **HSP:** {c['HSP']} h/día\n\n"
            f"**T_amb media:** {c['T_amb_media']}°C  |  "
            f"**T_mín diseño:** {c['T_min_diseno']}°C\n\n"
            f"**Región:** {c['region']}  |  **Zona CREG:** {c['CREG_zona']}"
        )

if st.button("💾 Guardar configuración", type="primary"):
    st.session_state["nombre_proyecto"] = nombre
    st.session_state["ciudad"]          = ciudad
    st.session_state["area_fachada_m2"] = area
    if ciudad in CIUDADES:
        c = CIUDADES[ciudad]
        st.session_state["T_min_diseno"]   = c["T_min_diseno"]
        st.session_state["T_cel_realista"] = c["T_cel_realista"]
        st.session_state["T_cel_extremo"]  = c["T_cel_extremo"]
    st.success("✅ Configuración guardada. Continúa en ☀️ Recurso Solar.")
