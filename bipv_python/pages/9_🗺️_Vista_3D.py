"""Página 9 — Vista 3D del sitio: mapa geolocalizado del edificio con pydeck."""
import math
import streamlit as st

from datos.ciudades_colombia import CIUDADES

st.set_page_config(page_title="Vista 3D — BIPV", page_icon="🗺️", layout="wide")
st.title("🗺️ Vista 3D del Sitio")
st.caption(
    "Visualización geolocalizada del edificio y la orientación de la fachada BIPV "
    "sobre mapa interactivo · Módulo Fase 3 — Paso B-5A"
)

# ── Verificar pydeck disponible ───────────────────────────────────────────────
try:
    import pydeck as pdk
    _pydeck_ok = True
except ImportError:
    _pydeck_ok = False

if not _pydeck_ok:
    st.error(
        "❌ La librería **pydeck** no está instalada en este entorno. "
        "Ejecuta en el servidor: `pip install pydeck` y reinicia la aplicación."
    )
    st.info(
        "El archivo `requirements.txt` ya incluye `pydeck>=0.8.0`. "
        "Si la aplicación se reinició recientemente, puede que aún no se haya instalado."
    )
    st.stop()

# ── Guard: ciudad requerida ───────────────────────────────────────────────────
ciudad = st.session_state.get("ciudad")
if not ciudad or ciudad not in CIUDADES:
    st.warning(
        "⚠️ Primero configura el proyecto en **🏠 Proyecto** y selecciona la ciudad. "
        "La visualización 3D necesita las coordenadas del sitio."
    )
    st.page_link("pages/1_🏠_Proyecto.py", label="Ir a Datos del Proyecto →", icon="🏠")
    st.stop()

c    = CIUDADES[ciudad]
lat  = c["lat"]
lon  = c["lon"]
alt_m = c["alt_m"]

# ── Panel de estado ───────────────────────────────────────────────────────────
recurso_ok   = st.session_state.get("recurso_solar_ok", False)
azimuth      = float(st.session_state.get("azimuth_fachada", 180))
tilt         = float(st.session_state.get("tilt_fachada", 90))
area_m2      = float(st.session_state.get("area_fachada_m2", 50.0))
nombre_proy  = st.session_state.get("nombre_proyecto", "Proyecto BIPV")
orient_label = st.session_state.get("orientacion_label", f"Azimuth {azimuth:.0f}°")

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
col_s1.metric("Ciudad",           ciudad)
col_s2.metric("Coordenadas",      f"{lat}°N, {lon}°W")
col_s3.metric("Orientación",      orient_label)
col_s4.metric(
    "Recurso Solar",
    "✅ Calculado" if recurso_ok else "⚠️ Pendiente",
)

if not recurso_ok:
    st.info(
        "ℹ️ El mapa ya está disponible. Calcula el **Recurso Solar** en ☀️ Recurso Solar "
        "para disponer del azimuth y tilt exactos de la fachada en la visualización."
    )

st.divider()

# ── Parámetros del edificio ───────────────────────────────────────────────────
st.subheader("🏗️ Geometría del edificio")
st.caption(
    "Estos parámetros definen el modelo visual del edificio. "
    "**No afectan ningún cálculo de producción ni el análisis financiero.**"
)

# Valor por defecto para el ancho: raíz cuadrada del área de fachada
_ancho_default = max(3.0, round(math.sqrt(area_m2), 1))

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    ancho_m = st.number_input(
        "Ancho de fachada (m)",
        min_value=2.0, max_value=500.0,
        value=float(st.session_state.get("edificio_ancho_m", _ancho_default)),
        step=0.5,
        help="Longitud horizontal de la fachada con paneles. "
             "Valor sugerido: √(área_fachada). Ajustar según plano real.",
    )

with col_b:
    profundidad_m = st.number_input(
        "Profundidad del edificio (m)",
        min_value=2.0, max_value=200.0,
        value=float(st.session_state.get("edificio_profundidad_m", 12.0)),
        step=0.5,
        help="Dimensión del edificio perpendicular a la fachada activa.",
    )

with col_c:
    n_pisos = st.number_input(
        "Número de pisos",
        min_value=1, max_value=60,
        value=int(st.session_state.get("n_pisos", 3)),
        step=1,
    )

with col_d:
    _altura_default = float(st.session_state.get("edificio_altura_m", float(n_pisos) * 3.0))
    altura_m = st.number_input(
        "Altura total (m)",
        min_value=3.0, max_value=300.0,
        value=_altura_default,
        step=0.5,
        help="Altura total del edificio. Referencia: ~3 m por piso.",
    )

# Guardar en session_state — solo variables propias de esta página
st.session_state["edificio_ancho_m"]       = ancho_m
st.session_state["edificio_profundidad_m"] = profundidad_m
st.session_state["edificio_altura_m"]      = altura_m
st.session_state["n_pisos"]                = n_pisos

# ── Funciones geométricas ─────────────────────────────────────────────────────

def _escala_geo(lat_c: float):
    """Retorna (metros_por_grado_lat, metros_por_grado_lon)."""
    lat_m = 1.0 / 111_320.0
    lon_m = 1.0 / (111_320.0 * math.cos(math.radians(lat_c)))
    return lat_m, lon_m


def poligono_edificio(lat_c, lon_c, ancho, profund, az_deg):
    """
    Calcula los 4 vértices del polígono de planta del edificio.
    La fachada activa mira en la dirección az_deg.
    Retorna lista de [lon, lat] en formato GeoJSON (para pydeck).
    """
    lat_m, lon_m = _escala_geo(lat_c)
    az  = math.radians(az_deg)

    # Normal de la fachada (vector que apunta hacia fuera)
    nx, ny = math.sin(az), math.cos(az)
    # Vector a lo largo del ancho (perpendicular)
    wx, wy = math.cos(az), -math.sin(az)

    hw = ancho   / 2.0
    hd = profund / 2.0

    corners_latlon = [
        (lat_c + ( ny*hd + wy*hw) * lat_m,  lon_c + ( nx*hd + wx*hw) * lon_m),
        (lat_c + ( ny*hd - wy*hw) * lat_m,  lon_c + ( nx*hd - wx*hw) * lon_m),
        (lat_c + (-ny*hd - wy*hw) * lat_m,  lon_c + (-nx*hd - wx*hw) * lon_m),
        (lat_c + (-ny*hd + wy*hw) * lat_m,  lon_c + (-nx*hd + wx*hw) * lon_m),
    ]
    # pydeck PolygonLayer espera [lon, lat]
    return [[p[1], p[0]] for p in corners_latlon]


def lineas_fachada(lat_c, lon_c, ancho, profund, az_deg):
    """
    Calcula:
    - La línea de la fachada activa (naranja)
    - El vector de orientación que sale del centro de la fachada (rojo)
    Retorna dos listas: [lon_start, lat_start], [lon_end, lat_end] para cada segmento.
    """
    lat_m, lon_m = _escala_geo(lat_c)
    az  = math.radians(az_deg)

    nx, ny = math.sin(az), math.cos(az)
    wx, wy = math.cos(az), -math.sin(az)

    hw = ancho   / 2.0
    hd = profund / 2.0

    # Extremos de la fachada (borde frontal del edificio)
    p1_lon = lon_c + ( nx*hd + wx*hw) * lon_m
    p1_lat = lat_c + ( ny*hd + wy*hw) * lat_m
    p2_lon = lon_c + ( nx*hd - wx*hw) * lon_m
    p2_lat = lat_c + ( ny*hd - wy*hw) * lat_m

    # Centro de la fachada
    fc_lon = (p1_lon + p2_lon) / 2
    fc_lat = (p1_lat + p2_lat) / 2

    # Flecha de orientación (longitud = 60 % del ancho)
    dist_flecha = ancho * 0.6
    arr_lon = fc_lon + nx * dist_flecha * lon_m
    arr_lat = fc_lat + ny * dist_flecha * lat_m

    # Formato de filas para LineLayer: [{start: [...], end: [...]}]
    linea_fachada = {
        "start": [p1_lon, p1_lat],
        "end":   [p2_lon, p2_lat],
        "tipo":  "fachada",
    }
    linea_flecha = {
        "start": [fc_lon, fc_lat],
        "end":   [arr_lon, arr_lat],
        "tipo":  "orientacion",
    }
    return linea_fachada, linea_flecha


# ── Calcular geometría ────────────────────────────────────────────────────────
polygon   = poligono_edificio(lat, lon, ancho_m, profundidad_m, azimuth)
ln_fach, ln_flecha = lineas_fachada(lat, lon, ancho_m, profundidad_m, azimuth)

datos_edificio = [{
    "polygon":   polygon,
    "elevation": altura_m,
    "name":      nombre_proy,
    "pisos":     n_pisos,
    "planta_m2": round(ancho_m * profundidad_m),
    "ciudad":    ciudad,
}]

datos_fachada  = [ln_fach]
datos_flecha   = [ln_flecha]
datos_punto    = [{"lon": lon, "lat": lat, "name": nombre_proy}]

# ── Controles de visualización ────────────────────────────────────────────────
st.subheader("🗺️ Mapa interactivo 3D")

col_mapa, col_ctrl = st.columns([4, 1])

with col_ctrl:
    st.markdown("#### 🎛️ Vista")
    pitch_val = st.slider("Inclinación 3D (°)", 0, 60, 45, step=5,
                          help="0° = vista cenital · 60° = perspectiva máxima")

    bearing_auto = st.checkbox("Alinear norte con fachada", value=True,
                               help="Rota el mapa para que la fachada mire al frente")
    bearing_val  = azimuth if bearing_auto else 0.0

    estilo = st.radio(
        "Estilo",
        ["Calles", "Claro", "Oscuro"],
        index=0,
    )

    st.markdown("---")
    st.markdown("##### Capas")
    show_fachada = st.checkbox("Fachada activa", value=True)
    show_flecha  = st.checkbox("Vector orientación", value=True)
    show_punto   = st.checkbox("Centroide", value=True)

    st.markdown("---")
    st.markdown("##### Leyenda")
    st.markdown("🟦 Edificio (extruido)")
    st.markdown("🟠 Fachada con paneles")
    st.markdown("🔴 Orientación fachada")
    st.markdown("🟡 Centroide del sitio")
    st.markdown("---")
    st.caption(f"**Azimuth:** {azimuth:.0f}°")
    st.caption(f"**Tilt:** {tilt:.0f}°")
    st.caption(f"**Área paneles:** {area_m2:.1f} m²")

MAP_STYLES = {
    "Calles": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
    "Claro":  "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Oscuro": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
}

# ── Capas pydeck ──────────────────────────────────────────────────────────────
layer_edificio = pdk.Layer(
    "PolygonLayer",
    data=datos_edificio,
    get_polygon="polygon",
    get_elevation="elevation",
    elevation_scale=1,
    extruded=True,
    wireframe=True,
    get_fill_color=[30, 90, 180, 150],
    get_line_color=[50, 120, 220, 255],
    line_width_min_pixels=1,
    pickable=True,
    auto_highlight=True,
    highlight_color=[80, 160, 255, 200],
)

layer_fachada = pdk.Layer(
    "LineLayer",
    data=datos_fachada,
    get_source_position="start",
    get_target_position="end",
    get_color=[255, 140, 0, 255],
    get_width=5,
    width_min_pixels=4,
    pickable=False,
)

layer_flecha = pdk.Layer(
    "LineLayer",
    data=datos_flecha,
    get_source_position="start",
    get_target_position="end",
    get_color=[220, 50, 20, 255],
    get_width=3,
    width_min_pixels=3,
    pickable=False,
)

layer_punto = pdk.Layer(
    "ScatterplotLayer",
    data=datos_punto,
    get_position=["lon", "lat"],
    get_radius=max(3.0, ancho_m * 0.12),
    radius_min_pixels=5,
    radius_max_pixels=30,
    get_fill_color=[255, 200, 0, 220],
    get_line_color=[200, 100, 0, 255],
    stroked=True,
    line_width_min_pixels=2,
    pickable=True,
)

capas = [layer_edificio]
if show_fachada:
    capas.append(layer_fachada)
if show_flecha:
    capas.append(layer_flecha)
if show_punto:
    capas.append(layer_punto)

view_state = pdk.ViewState(
    latitude=lat,
    longitude=lon,
    zoom=17,
    pitch=pitch_val,
    bearing=bearing_val,
)

deck = pdk.Deck(
    layers=capas,
    initial_view_state=view_state,
    map_style=MAP_STYLES[estilo],
    tooltip={
        "html": (
            "<b>🏗️ {name}</b><br/>"
            "Ciudad: {ciudad}<br/>"
            "Pisos: {pisos}<br/>"
            "Planta: {planta_m2} m²<br/>"
        ),
        "style": {
            "backgroundColor": "rgba(10, 30, 80, 0.92)",
            "color": "white",
            "fontSize": "13px",
            "padding": "10px 12px",
            "borderRadius": "6px",
        },
    },
)

with col_mapa:
    st.pydeck_chart(deck, use_container_width=True, height=520)

# ── Resumen de geometría ──────────────────────────────────────────────────────
st.divider()
st.subheader("📐 Resumen del modelo")

planta_m2_total   = ancho_m * profundidad_m
fachada_total_m2  = ancho_m * altura_m
cobertura_fach    = min(area_m2 / fachada_total_m2 * 100, 100.0) if fachada_total_m2 > 0 else 0.0

mc1, mc2, mc3, mc4, mc5 = st.columns(5)
mc1.metric("Planta del edificio",   f"{planta_m2_total:.0f} m²")
mc2.metric("Altura total",          f"{altura_m:.1f} m  ({n_pisos} pisos)")
mc3.metric("Área de fachada total", f"{fachada_total_m2:.0f} m²")
mc4.metric("Área con paneles",      f"{area_m2:.1f} m²")
mc5.metric("Cobertura de fachada",  f"{cobertura_fach:.0f}%",
           help="Porcentaje de la fachada total cubierto con paneles BIPV")

# ── Info sobre próximos módulos ───────────────────────────────────────────────
st.divider()
with st.expander("ℹ️ Próximas secciones de este módulo 3D"):
    st.markdown("""
    **Lo que se agregará en las siguientes etapas de la Fase 3:**

    | Módulo | Descripción |
    |--------|-------------|
    | **B-5B: Modelo 3D del edificio** | Vista volumétrica con paneles individuales en la fachada, coloreados por irradiancia mensual POA |
    | **B-5C: Diagrama solar y sombras** | Trayectoria solar anual (sun path) superpuesta sobre el perfil de horizonte de la página Mismatch. Heatmap de horas productivas vs sombreadas (24h × 12 meses) |

    > Estos módulos se añadirán como pestañas adicionales en esta misma página
    > y usarán los datos ya calculados en Recurso Solar, Dimensionamiento y Mismatch.
    > **No requieren recalcular nada** — solo visualizan lo que ya existe en el sistema.
    """)
