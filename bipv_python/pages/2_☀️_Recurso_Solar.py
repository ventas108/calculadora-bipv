"""Página 2 — Recurso Solar: TMY desde PVGIS + POA para sistemas solares."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from datos.ciudades_colombia import CIUDADES
from calculos.solar import (
    obtener_tmy_pvgis,
    calcular_poa,
    resumen_mensual,
    heatmap_poa_horario,
    ORIENTACIONES,
)
from calculos.tz_utils import utc_offset_latam, tz_label

st.set_page_config(page_title="Recurso Solar — BIPV", page_icon="☀️", layout="wide")
st.title("☀️ Recurso Solar")
st.caption("Datos TMY (Typical Meteorological Year) desde PVGIS v5.2 — JRC European Commission")

# ── Leer ciudad y tipo de instalación desde session_state ────────────────────
ciudad = st.session_state.get("ciudad", "Bogotá")
if ciudad not in CIUDADES:
    st.warning("⚠️ Primero configura el proyecto en 🏠 Proyecto.")
    st.stop()

c = CIUDADES[ciudad]

# ── Tipo de instalación activo (para etiquetas y tilt default) ───────────────
tipo_instalacion = st.session_state.get("tipo_instalacion", "Fachada BIPV")
TIPOS_INFO = {
    "Fachada BIPV":              {"icono": "🏢", "tilt_def": 90,  "tilt_hint": "90° = vertical (fachada). BIPV integrado en vidrio."},
    "Techo inclinado (BIPV)":    {"icono": "🏠", "tilt_def": 25,  "tilt_hint": "15°–35° típico en Colombia. Ajusta al ángulo real de tu cubierta."},
    "Techo plano (con soporte)": {"icono": "🏭", "tilt_def": 15,  "tilt_hint": "10°–20° con estructura metálica. Permite autolimpieza."},
    "Pérgola / sombreadero":     {"icono": "⛱️", "tilt_def": 10,  "tilt_hint": "5°–15°. Casi horizontal para maximizar sombra."},
    "Marquesina / voladizo":     {"icono": "🏗️", "tilt_def": 20,  "tilt_hint": "15°–30°. Inclinación del voladizo estructural."},
    "Granja fotovoltaica":       {"icono": "☀️", "tilt_def": 20,  "tilt_hint": "15°–25° óptimo para Colombia (lat. 4°–8°N). Maximiza producción anual."},
}
tipo_cfg = TIPOS_INFO.get(tipo_instalacion, TIPOS_INFO["Fachada BIPV"])
icono_tipo = tipo_cfg["icono"]

# ── Coordenadas: predio exacto tiene prioridad sobre centro de ciudad ─────────
lat   = float(st.session_state.get("lat_proyecto", c["lat"]))
lon   = float(st.session_state.get("lon_proyecto", c["lon"]))
alt_m = int(st.session_state.get("alt_proyecto",   c["alt_m"]))

_coord_personalizada = (
    abs(lat - c["lat"]) > 0.0001 or abs(lon - c["lon"]) > 0.0001
)

# ── Panel de configuración ───────────────────────────────────────────────────
if _coord_personalizada:
    # Mostrar nombre del proyecto si existe, de lo contrario las coordenadas
    _nombre_proy = st.session_state.get("nombre_proyecto", "").strip()
    _label_sitio = _nombre_proy if _nombre_proy else f"{lat:.4f}°N, {abs(lon):.4f}°O"
    st.subheader(f"📍 Sitio: {_label_sitio}  ·  📌 Predio personalizado  ·  {icono_tipo} {tipo_instalacion}")
    st.success(
        f"✅ **Coordenadas exactas del predio:** "
        f"**{lat:.5f}°** lat, **{lon:.5f}°** lon, **{alt_m} m.s.n.m.**  \n"
        f"🌡️ *Ciudad de referencia climática TMY: **{ciudad}** "
        f"({c['lat']}°, {c['lon']}°) — seleccionada por similitud térmica y costera. "
        f"Los datos meteorológicos se descargan de PVGIS para las coordenadas exactas del predio, no para {ciudad}.*"
    )
else:
    st.subheader(f"📍 Sitio: {ciudad}  ·  {icono_tipo} {tipo_instalacion}")

col_info1, col_info2, col_info3, col_info4 = st.columns(4)
col_info1.metric("Latitud", f"{lat:.5f}°")
col_info2.metric("Longitud", f"{lon:.5f}°")
col_info3.metric("Altitud", f"{alt_m} m.s.n.m.")
col_info4.metric("GHI referencia", f"{c['GHI_kWh_m2_dia']} kWh/m²·día")

st.markdown("---")

# ── Orientación e inclinación del sistema ────────────────────────────────────
st.subheader(f"🧭 Orientación e inclinación — {icono_tipo} {tipo_instalacion}")

col_or1, col_or2, col_or3 = st.columns(3)

with col_or1:
    orientacion_label = st.selectbox(
        "Azimuth (dirección que mira el sistema)",
        list(ORIENTACIONES.keys()),
        index=list(ORIENTACIONES.keys()).index(
            st.session_state.get("orientacion_label", "Norte (0°)")
            if st.session_state.get("orientacion_label") in ORIENTACIONES
            else "Norte (0°)"
        ),
        help="En Colombia las orientaciones Norte y Oriente reciben buen recurso solar.",
    )
    azimuth = ORIENTACIONES[orientacion_label]

with col_or2:
    # Tilt default: session_state (guardado) > default del tipo > 90
    _tilt_guardado = st.session_state.get("tilt_default", tipo_cfg["tilt_def"])
    # Si el tilt guardado corresponde a otro tipo (ej. venía de fachada=90 y ahora es granja=20),
    # usar el default del tipo actual si el usuario aún no guardó con el nuevo tipo.
    _tilt_tipo_activo = int(st.session_state.get("tilt_default", tipo_cfg["tilt_def"]))

    tilt = st.slider(
        "Inclinación del plano (°)",
        min_value=0, max_value=90,
        value=_tilt_tipo_activo,
        help=tipo_cfg["tilt_hint"],
    )

with col_or3:
    albedo = st.slider(
        "Albedo del suelo",
        min_value=0.05, max_value=0.50, value=0.20, step=0.05,
        help="0.20 = suelo urbano típico. 0.30 = concreto. 0.05 = asfalto.",
    )

st.markdown("---")

# ── Función cacheada para PVGIS ──────────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def cargar_tmy(lat, lon):
    return obtener_tmy_pvgis(lat, lon)

# ── Botones de acción ────────────────────────────────────────────────────────
_btn_col1, _btn_col2 = st.columns([4, 1])
_descarga_btn = _btn_col1.button("🌐 Descargar TMY de PVGIS y calcular POA", type="primary", use_container_width=True)
_recalc_btn   = _btn_col2.button("🔄 Limpiar caché", use_container_width=True,
                                  help="Fuerza nueva descarga desde PVGIS, descartando datos anteriores.")
if _recalc_btn:
    cargar_tmy.clear()
    st.success("✅ Caché limpiada — presiona **Descargar TMY** para obtener datos frescos.")

if _descarga_btn:

    _sitio_label = (
        f"predio en {ciudad} ({lat:.5f}°, {lon:.5f}°)"
        if _coord_personalizada else f"{ciudad} ({lat}°, {lon}°)"
    )
    with st.spinner(f"Conectando a PVGIS para {_sitio_label}..."):
        try:
            tmy = cargar_tmy(lat, lon)
        except Exception as e:
            st.error(f"❌ Error conectando a PVGIS: {e}")
            st.info("Verifica la conexión a internet del servidor. PVGIS requiere acceso a re.jrc.ec.europa.eu")
            st.stop()

    with st.spinner(f"Calculando irradiancia POA para {icono_tipo} {tipo_instalacion} ({tilt}°)..."):
        poa = calcular_poa(tmy, lat, lon, alt_m, tilt, azimuth)
        monthly = resumen_mensual(tmy, poa)

    # ── Métricas anuales ─────────────────────────────────────────────────────
    ghi_anual  = tmy["G_h"].sum() / 1000.0
    poa_anual  = poa["poa_global"].sum() / 1000.0
    ratio_poa  = poa_anual / ghi_anual if ghi_anual > 0 else 0
    t_media    = tmy["T2m"].mean()

    st.markdown("---")
    st.subheader("📊 Resultados del recurso solar")

    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.metric("GHI anual", f"{ghi_anual:,.0f} kWh/m²", help="Irradiancia Global Horizontal")
    mc2.metric("POA anual", f"{poa_anual:,.0f} kWh/m²", help=f"Irradiancia en el plano del sistema ({tilt}°)")
    mc3.metric("Factor POA/GHI", f"{ratio_poa:.2f}",
               help="<1 es normal para fachadas verticales. ~1 en techos optimizados. >1 posible con tracking.")
    mc4.metric("T° media anual", f"{t_media:.1f} °C", help="Temperatura media ambiente del TMY")
    mc5.metric("HSP equivalentes", f"{poa_anual:.0f} h/año", help="Horas Sol Pico — energía base para cálculo")

    # ── Gráfica mensual ──────────────────────────────────────────────────────
    st.subheader("📅 Irradiancia mensual")

    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(
        name="GHI (kWh/m²)",
        x=monthly.index,
        y=monthly["GHI (kWh/m²)"],
        marker_color="#87CEEB",
        opacity=0.85,
    ))
    fig_monthly.add_trace(go.Bar(
        name=f"POA {icono_tipo} {tipo_instalacion} — {orientacion_label} / {tilt}° (kWh/m²)",
        x=monthly.index,
        y=monthly["POA (kWh/m²)"],
        marker_color="#FF8C00",
        opacity=0.85,
    ))
    fig_monthly.update_layout(
        barmode="group",
        xaxis_title="Mes",
        yaxis_title="Irradiancia (kWh/m²/mes)",
        height=380,
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

    # ── Heatmap POA horario ──────────────────────────────────────────────────
    st.subheader("🌡️ Mapa de calor — POA promedio por hora y mes (W/m²)")

    _tz_off  = st.session_state.get("utc_offset_local", utc_offset_latam(lat, lon))
    _tz_lbl  = tz_label(_tz_off)
    heatmap  = heatmap_poa_horario(poa, utc_offset=_tz_off)

    fig_heat = go.Figure(go.Heatmap(
        z=heatmap.values,
        x=heatmap.columns,
        y=[f"{h:02d}:00" for h in heatmap.index],
        colorscale="YlOrRd",
        colorbar=dict(title="W/m²"),
        zmin=0,
    ))
    fig_heat.update_layout(
        xaxis_title="Mes",
        yaxis_title=f"Hora local ({_tz_lbl})",
        height=400,
        plot_bgcolor="white",
    )
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption(f"🕐 Horas en hora local ({_tz_lbl}). Datos TMY en UTC convertidos para visualización.")

    # ── Tabla resumen mensual ────────────────────────────────────────────────
    with st.expander("📋 Ver tabla de irradiancia mensual"):
        monthly_display = monthly.copy()
        monthly_display["Ratio POA/GHI"] = (
            monthly_display["POA (kWh/m²)"] / monthly_display["GHI (kWh/m²)"]
        ).round(3)
        st.dataframe(monthly_display.style.format("{:.1f}"), use_container_width=True)

    # ── Guardar en session_state ─────────────────────────────────────────────
    st.session_state["tmy_df"]            = tmy
    st.session_state["poa_df"]            = poa
    st.session_state["tmy_ciudad"]        = ciudad
    st.session_state["tilt_fachada"]      = tilt
    st.session_state["tilt_default"]      = tilt   # persiste la selección del usuario
    st.session_state["azimuth_fachada"]   = azimuth
    st.session_state["orientacion_label"] = orientacion_label
    st.session_state["poa_anual_kWh_m2"]  = round(poa_anual, 1)
    st.session_state["ghi_anual_kWh_m2"]  = round(ghi_anual, 1)
    st.session_state["t_media_anual"]     = round(t_media, 1)
    st.session_state["recurso_solar_ok"]  = True

    st.success(
        f"✅ Recurso solar calculado para **{ciudad}**  |  "
        f"{icono_tipo} **{tipo_instalacion}** — {orientacion_label} / {tilt}°  |  "
        f"POA: **{poa_anual:,.0f} kWh/m²/año**  |  "
        f"GHI: **{ghi_anual:,.0f} kWh/m²/año**\n\n"
        f"Continúa en 📊 Producción para simular la energía generada."
    )

# ── Mostrar resultado previo si ya se calculó ────────────────────────────────
elif st.session_state.get("recurso_solar_ok") and st.session_state.get("tmy_ciudad") == ciudad:
    poa_prev  = st.session_state.get("poa_anual_kWh_m2", 0)
    ghi_prev  = st.session_state.get("ghi_anual_kWh_m2", 0)
    tilt_prev = st.session_state.get("tilt_fachada", tipo_cfg["tilt_def"])
    az_prev   = st.session_state.get("orientacion_label", "—")

    st.success(
        f"✅ TMY cargado para **{ciudad}**  |  "
        f"{icono_tipo} **{tipo_instalacion}** — {az_prev} / {tilt_prev}°  |  "
        f"POA: **{poa_prev:,.0f} kWh/m²/año**  |  "
        f"GHI: **{ghi_prev:,.0f} kWh/m²/año**"
    )
    st.info("Cambia la orientación o inclinación y presiona el botón para recalcular.")

else:
    st.info(
        f"👆 Presiona el botón para descargar el TMY de PVGIS y calcular la irradiancia "
        f"para tu {icono_tipo} **{tipo_instalacion}**."
    )
    st.markdown(f"""
    **¿Qué descarga PVGIS?**
    - **8.760 horas** de datos climáticos típicos (promedio 2005–2020)
    - Variables: GHI, DNI, DHI, temperatura, viento, presión
    - Fuente: satélite CM SAF + estaciones SYNOP
    - Gratis, sin API key, precisión ~±5% para Colombia

    **¿Qué calcula pvlib?**
    - Posición solar hora a hora para la latitud/longitud del proyecto
    - Irradiancia en el plano del sistema a **{tilt}°** de inclinación (modelo Hay-Davies)
    - Resultado: **POA (W/m²)** — entrada directa al motor de producción

    > {icono_tipo} **{tipo_instalacion}**: inclinación recomendada {tipo_cfg['tilt_hint']}
    """)
