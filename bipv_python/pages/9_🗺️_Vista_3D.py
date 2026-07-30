"""Página 9 — Vista 3D del sitio: mapa geolocalizado y modelo volumétrico BIPV."""
import math
import streamlit as st
import plotly.graph_objects as go

from datos.ciudades_colombia import CIUDADES

# ── Funciones auxiliares nivel módulo (cacheables con st.cache_data) ──────────

@st.cache_data(show_spinner=False)
def _solar_path_mensual(lat: float, lon: float, alt_m: float):
    """Posiciones solares horarias para 12 días representativos (uno por mes)."""
    import pvlib, pandas as pd
    loc    = pvlib.location.Location(lat, lon, altitude=alt_m, tz="UTC")
    dias   = pd.date_range("2001-01-15", periods=12, freq="MS") + pd.Timedelta(days=14)
    frames = []
    for dia in dias:
        times = pd.date_range(dia, dia + pd.Timedelta(hours=23), freq="h", tz="UTC")
        sp    = loc.get_solarposition(times)
        sp["mes"] = dia.month
        frames.append(sp[sp["apparent_elevation"] > 0.5])
    return pd.concat(frames) if frames else pd.DataFrame()


@st.cache_data(show_spinner=False)
def _solar_anual_std(lat: float, lon: float, alt_m: float):
    """Posiciones solares para año estándar 8760 h UTC (sin datos TMY)."""
    import pvlib, pandas as pd
    loc   = pvlib.location.Location(lat, lon, altitude=alt_m, tz="UTC")
    times = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
    return loc.get_solarposition(times)


def _interp_horizonte(puntos_az_el: list, az_array) -> "np.ndarray":
    """Interpola la elevación del horizonte (0-360°, periódico)."""
    import numpy as np
    if not puntos_az_el:
        return np.zeros(len(az_array))
    datos = sorted(puntos_az_el, key=lambda p: p[0])
    azs   = np.array([p[0] for p in datos])
    els   = np.array([p[1] for p in datos])
    azs_e = np.concatenate([[azs[-1] - 360], azs, [azs[0] + 360]])
    els_e = np.concatenate([[els[-1]], els, [els[0]]])
    return np.interp(np.asarray(az_array, dtype=float), azs_e, els_e)

st.set_page_config(page_title="Vista 3D — BIPV", page_icon="🗺️", layout="wide")
st.title("🗺️ Vista 3D del Sitio")
st.caption(
    "Mapa geolocalizado del edificio · Modelo volumétrico 3D con paneles BIPV · "
    "Fase 3 — Módulo B-5A/B"
)

# ── Verificar pydeck disponible ───────────────────────────────────────────────
try:
    import pydeck as pdk
    _pydeck_ok = True
except ImportError:
    _pydeck_ok = False

# ── Guard: ciudad requerida ───────────────────────────────────────────────────
ciudad = st.session_state.get("ciudad")
if not ciudad or ciudad not in CIUDADES:
    st.warning(
        "⚠️ Primero configura el proyecto en **🏠 Proyecto** y selecciona la ciudad."
    )
    try:
        st.page_link("pages/1_🏠_Proyecto.py", label="Ir a Datos del Proyecto →", icon="🏠")
    except Exception:
        pass
    st.stop()

c     = CIUDADES[ciudad]

# Coordenadas: predio exacto tiene prioridad sobre centro de ciudad
lat   = float(st.session_state.get("lat_proyecto", c["lat"]))
lon   = float(st.session_state.get("lon_proyecto", c["lon"]))
alt_m = int(st.session_state.get("alt_proyecto",   c["alt_m"]))

_coord_personalizada = (
    abs(lat - c["lat"]) > 0.0001 or abs(lon - c["lon"]) > 0.0001
)

# ── Panel de estado ───────────────────────────────────────────────────────────
recurso_ok   = st.session_state.get("recurso_solar_ok", False)
azimuth      = float(st.session_state.get("azimuth_fachada", 180))
tilt         = float(st.session_state.get("tilt_fachada", 90))
area_m2      = float(st.session_state.get("area_fachada_m2", 50.0))
nombre_proy  = st.session_state.get("nombre_proyecto", "Proyecto BIPV")
orient_label = st.session_state.get("orientacion_label", f"Azimuth {azimuth:.0f}°")

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
col_s1.metric("Ciudad",      ciudad)
_coord_label = f"{lat:.5f}°N, {lon:.5f}°E" if _coord_personalizada else f"{lat}°N, {lon}°E"
col_s2.metric("Coordenadas", _coord_label)
col_s3.metric("Orientación",  orient_label)
col_s4.metric("Recurso Solar", "✅ Calculado" if recurso_ok else "⚠️ Pendiente")

if not recurso_ok:
    st.info(
        "ℹ️ Las visualizaciones ya están disponibles. "
        "Calcula el **Recurso Solar** en ☀️ para obtener datos de irradiancia exactos."
    )

st.divider()

# ── Parámetros del edificio — compartidos entre tabs ─────────────────────────
st.subheader("🏗️ Geometría del edificio")
st.caption(
    "Parámetros visuales. **No afectan cálculos de producción ni análisis financiero.**"
)

_ancho_default = max(3.0, round(math.sqrt(area_m2), 1))
col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    ancho_m = st.number_input(
        "Ancho de fachada (m)", min_value=2.0, max_value=500.0,
        value=float(st.session_state.get("edificio_ancho_m", _ancho_default)),
        step=0.5,
        help="Longitud horizontal de la fachada. Sugerido: √(área_fachada).",
    )
with col_b:
    profundidad_m = st.number_input(
        "Profundidad del edificio (m)", min_value=2.0, max_value=200.0,
        value=float(st.session_state.get("edificio_profundidad_m", 12.0)),
        step=0.5,
    )
with col_c:
    n_pisos = st.number_input(
        "Número de pisos", min_value=1, max_value=60,
        value=int(st.session_state.get("n_pisos", 3)), step=1,
    )
with col_d:
    altura_m = st.number_input(
        "Altura total (m)", min_value=3.0, max_value=300.0,
        value=float(st.session_state.get("edificio_altura_m", float(n_pisos) * 3.0)),
        step=0.5, help="~3 m por piso.",
    )

st.session_state["edificio_ancho_m"]       = ancho_m
st.session_state["edificio_profundidad_m"] = profundidad_m
st.session_state["edificio_altura_m"]      = altura_m
st.session_state["n_pisos"]                = n_pisos

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# TABS: Mapa del Sitio (B-5A) | Modelo 3D (B-5B) | Diagrama Solar (B-5C)
# ══════════════════════════════════════════════════════════════════════════════
tab_mapa, tab_modelo, tab_solar = st.tabs([
    "🗺️ Mapa del Sitio",
    "🏗️ Modelo 3D con Paneles",
    "🌞 Diagrama Solar",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — MAPA PYDECK (B-5A)
# ─────────────────────────────────────────────────────────────────────────────
with tab_mapa:

    if not _pydeck_ok:
        st.error(
            "❌ La librería **pydeck** no está instalada. "
            "Ejecuta: `pip install pydeck` y reinicia la aplicación."
        )
        st.info("`requirements.txt` ya incluye `pydeck>=0.8.0`.")
    else:
        def _escala_geo(lat_c: float):
            lat_m = 1.0 / 111_320.0
            lon_m = 1.0 / (111_320.0 * math.cos(math.radians(lat_c)))
            return lat_m, lon_m

        def poligono_edificio(lat_c, lon_c, ancho, profund, az_deg):
            lat_m, lon_m = _escala_geo(lat_c)
            az  = math.radians(az_deg)
            nx, ny = math.sin(az), math.cos(az)
            wx, wy = math.cos(az), -math.sin(az)
            hw, hd = ancho / 2.0, profund / 2.0
            corners = [
                (lat_c + ( ny*hd + wy*hw) * lat_m, lon_c + ( nx*hd + wx*hw) * lon_m),
                (lat_c + ( ny*hd - wy*hw) * lat_m, lon_c + ( nx*hd - wx*hw) * lon_m),
                (lat_c + (-ny*hd - wy*hw) * lat_m, lon_c + (-nx*hd - wx*hw) * lon_m),
                (lat_c + (-ny*hd + wy*hw) * lat_m, lon_c + (-nx*hd + wx*hw) * lon_m),
            ]
            return [[p[1], p[0]] for p in corners]

        def lineas_fachada(lat_c, lon_c, ancho, profund, az_deg):
            lat_m, lon_m = _escala_geo(lat_c)
            az  = math.radians(az_deg)
            nx, ny = math.sin(az), math.cos(az)
            wx, wy = math.cos(az), -math.sin(az)
            hw, hd = ancho / 2.0, profund / 2.0
            p1_lon = lon_c + ( nx*hd + wx*hw) * lon_m
            p1_lat = lat_c + ( ny*hd + wy*hw) * lat_m
            p2_lon = lon_c + ( nx*hd - wx*hw) * lon_m
            p2_lat = lat_c + ( ny*hd - wy*hw) * lat_m
            fc_lon = (p1_lon + p2_lon) / 2
            fc_lat = (p1_lat + p2_lat) / 2
            dist   = ancho * 0.6
            return (
                {"start": [p1_lon, p1_lat], "end": [p2_lon, p2_lat]},
                {"start": [fc_lon, fc_lat],
                 "end":   [fc_lon + nx * dist * lon_m,
                            fc_lat + ny * dist * lat_m]},
            )

        polygon        = poligono_edificio(lat, lon, ancho_m, profundidad_m, azimuth)
        ln_fach, ln_fl = lineas_fachada(lat, lon, ancho_m, profundidad_m, azimuth)

        datos_ed   = [{"polygon": polygon, "elevation": altura_m,
                       "name": nombre_proy, "pisos": n_pisos,
                       "planta_m2": round(ancho_m * profundidad_m), "ciudad": ciudad}]
        datos_fa   = [ln_fach]
        datos_fl   = [ln_fl]
        datos_pt   = [{"lon": lon, "lat": lat, "name": nombre_proy}]

        col_mapa, col_ctrl = st.columns([4, 1])

        with col_ctrl:
            st.markdown("#### 🎛️ Vista")
            pitch_val    = st.slider("Inclinación 3D (°)", 0, 60, 45, step=5)
            bearing_auto = st.checkbox("Alinear con fachada", value=True)
            bearing_val  = azimuth if bearing_auto else 0.0
            estilo       = st.radio("Estilo", ["Calles", "Claro", "Oscuro"], index=0)
            st.markdown("---")
            st.markdown("##### Capas")
            show_fachada = st.checkbox("Fachada activa", value=True)
            show_flecha  = st.checkbox("Vector orientación", value=True)
            show_punto   = st.checkbox("Centroide", value=True)
            st.markdown("---")
            st.markdown("##### Leyenda")
            st.markdown("🟦 Edificio (3D)  \n🟠 Fachada  \n🔴 Orientación  \n🟡 Centroide")
            st.caption(f"Az: {azimuth:.0f}° · Tilt: {tilt:.0f}°")

        MAP_STYLES = {
            "Calles": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
            "Claro":  "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            "Oscuro": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        }

        layer_ed = pdk.Layer("PolygonLayer", data=datos_ed, get_polygon="polygon",
                             get_elevation="elevation", elevation_scale=1, extruded=True,
                             wireframe=True, get_fill_color=[30, 90, 180, 150],
                             get_line_color=[50, 120, 220, 255], line_width_min_pixels=1,
                             pickable=True, auto_highlight=True)
        layer_fa = pdk.Layer("LineLayer", data=datos_fa,
                             get_source_position="start", get_target_position="end",
                             get_color=[255, 140, 0, 255], get_width=5,
                             width_min_pixels=4, pickable=False)
        layer_fl = pdk.Layer("LineLayer", data=datos_fl,
                             get_source_position="start", get_target_position="end",
                             get_color=[220, 50, 20, 255], get_width=3,
                             width_min_pixels=3, pickable=False)
        layer_pt = pdk.Layer("ScatterplotLayer", data=datos_pt,
                             get_position=["lon", "lat"],
                             get_radius=max(3.0, ancho_m * 0.12),
                             radius_min_pixels=5, radius_max_pixels=30,
                             get_fill_color=[255, 200, 0, 220],
                             get_line_color=[200, 100, 0, 255], stroked=True,
                             line_width_min_pixels=2, pickable=True)

        capas = [layer_ed]
        if show_fachada: capas.append(layer_fa)
        if show_flecha:  capas.append(layer_fl)
        if show_punto:   capas.append(layer_pt)

        deck = pdk.Deck(
            layers=capas,
            initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=17,
                                             pitch=pitch_val, bearing=bearing_val),
            map_style=MAP_STYLES[estilo],
            tooltip={
                "html": "<b>🏗️ {name}</b><br>Ciudad: {ciudad}<br>Pisos: {pisos}<br>Planta: {planta_m2} m²",
                "style": {"backgroundColor": "rgba(10,30,80,0.92)", "color": "white",
                          "fontSize": "13px", "padding": "10px 12px", "borderRadius": "6px"},
            },
        )

        with col_mapa:
            st.pydeck_chart(deck, use_container_width=True)

        # Métricas
        st.divider()
        fach_total = ancho_m * altura_m
        cob_fach   = min(area_m2 / fach_total * 100, 100.0) if fach_total > 0 else 0.0
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.metric("Planta",          f"{ancho_m * profundidad_m:.0f} m²")
        mc2.metric("Altura total",    f"{altura_m:.1f} m  ({n_pisos} pisos)")
        mc3.metric("Fachada total",   f"{fach_total:.0f} m²")
        mc4.metric("Área con paneles",f"{area_m2:.1f} m²")
        mc5.metric("Cobertura fachada", f"{cob_fach:.0f}%")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — MODELO 3D PLOTLY (B-5B)
# ─────────────────────────────────────────────────────────────────────────────
with tab_modelo:

    # ── Datos de irradiancia POA ──────────────────────────────────────────────
    poa_df     = st.session_state.get("poa_df")
    poa_anual  = float(st.session_state.get("poa_anual_kWh_m2",
                       c["GHI_kWh_m2_dia"] * 365 * 0.7))

    MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    if poa_df is not None:
        poa_mensual_kwh = (
            poa_df.groupby(poa_df.index.month)["poa_global"].sum() / 1000.0
        )
        poa_mensual = [float(poa_mensual_kwh.get(m, poa_anual / 12))
                       for m in range(1, 13)]
    else:
        # Estimación sinusoidal desde GHI de referencia
        ghi_dia = c["GHI_kWh_m2_dia"]
        # Colombia es tropical: variación estacional pequeña
        # Factor POA fachada ≈ 0.6–0.8 × GHI según orientación
        factor_poa = 0.70
        poa_base   = ghi_dia * factor_poa
        # Pequeña variación estacional (~±15%)
        poa_mensual = [
            poa_base * (1 + 0.15 * math.cos(math.radians((m - 7) * 30))) * 30
            for m in range(1, 13)
        ]

    # ── Datos del sistema fotovoltaico ────────────────────────────────────────
    N_paneles = int(st.session_state.get("N_paneles_final",
                    st.session_state.get("N_paneles_dim", 0)))

    # Estimación desde área si no hay datos de producción
    if N_paneles == 0:
        _area_panel_est = 0.72  # m² típico panel CdTe BIPV
        N_paneles = max(1, int(area_m2 / _area_panel_est))

    panel_dict = st.session_state.get("panel_dict")
    area_panel = 0.72   # m² default (CdTe BIPV típico)
    pmax_panel = 60.0   # W default

    if panel_dict and panel_dict.get("area_m2"):
        area_panel = float(panel_dict["area_m2"])
        pmax_panel = float(panel_dict.get("Pmax_stc", 60))
    elif st.session_state.get("N_paneles_final") and area_m2 > 0:
        area_panel = area_m2 / N_paneles

    P_instalada_kWp = round(N_paneles * pmax_panel / 1000.0, 2)

    # Dimensiones del panel (aspect ratio 0.56: ancho/alto BIPV típico)
    _asp = 0.56
    pw   = max(0.2, math.sqrt(area_panel * _asp))    # panel width  (m)
    ph   = max(0.3, math.sqrt(area_panel / _asp))    # panel height (m)
    gap  = 0.04                                        # gap entre paneles (m)

    # ── Controles del modelo 3D ───────────────────────────────────────────────
    col_ctrl3d, col_fig3d = st.columns([1, 4])

    with col_ctrl3d:
        st.markdown("#### 🎛️ Modelo")

        mes_idx = st.slider(
            "Mes seleccionado",
            min_value=0, max_value=11,
            value=5,   # Junio por defecto
            format="%d",
            help="0 = Enero … 11 = Diciembre",
        )
        mes_nombre = MESES_ES[mes_idx]
        poa_mes    = poa_mensual[mes_idx]

        st.caption(f"**{mes_nombre}:** {poa_mes:.0f} kWh/m²")

        vista  = st.radio("Vista", ["Fachada", "Perspectiva", "Planta"], index=1)
        opac_ed = st.slider("Opacidad edificio", 0.1, 1.0, 0.4, 0.1)
        show_sun = st.checkbox("Mostrar rayo solar", value=True)
        show_all_months = st.checkbox("Comparar todos los meses",
                                      help="Muestra la barra de POA anual en el gráfico")

        st.markdown("---")
        st.markdown("##### Leyenda")
        st.markdown("🟦 Edificio  \n🟧 Fachada activa  \n🟨 Paneles BIPV  \n🌞 Rayo solar")
        poa_min_m = min(poa_mensual)
        poa_max_m = max(poa_mensual)
        st.caption(f"POA min: {poa_min_m:.0f}  \nPOA max: {poa_max_m:.0f}  \nkWh/m²/mes")

    # ── Funciones de geometría 3D ─────────────────────────────────────────────

    def _color_poa(val, vmin, vmax):
        """Mapea POA [vmin, vmax] → color 'rgb(r,g,b)' en escala cálida."""
        t = max(0.0, min(1.0, (val - vmin) / max(1.0, vmax - vmin)))
        # Blue(0.1) → Yellow(0.5) → Red(1.0)
        if t < 0.5:
            s  = t * 2          # 0→1
            r  = int(50  + 205 * s)
            g  = int(50  + 205 * s)
            b  = int(200 - 180 * s)
        else:
            s  = (t - 0.5) * 2  # 0→1
            r  = 255
            g  = int(255 - 230 * s)
            b  = int(20  - 20  * s)
        return f'rgb({r},{g},{b})'

    def building_box_traces(w, d, h, opacity):
        """Mesh3d del box del edificio (5 caras: frente, atrás, izq, der, techo)."""
        # Vértices
        x8 = [-w/2,  w/2,  w/2, -w/2, -w/2,  w/2,  w/2, -w/2]
        y8 = [   0,    0,    d,    d,    0,    0,    d,    d]
        z8 = [   0,    0,    0,    0,    h,    h,    h,    h]
        # Caras como triángulos (i,j,k)
        # Frente (Y=0): 0,1,5 / 0,5,4
        # Atrás  (Y=d): 3,2,6 / 3,6,7
        # Izq (X=-w/2): 3,0,4 / 3,4,7
        # Der (X=+w/2): 1,2,6 / 1,6,5
        # Techo (Z=h):  4,5,6 / 4,6,7
        fi = [0, 0, 3, 3, 3, 3, 1, 1, 4, 4]
        fj = [1, 5, 2, 6, 0, 4, 2, 6, 5, 6]
        fk = [5, 4, 6, 7, 4, 7, 6, 5, 6, 7]
        face_colors = [
            'rgb(100,130,200)', 'rgb(100,130,200)',   # frente
            'rgb(80, 100,160)', 'rgb(80, 100,160)',   # atrás
            'rgb(90, 115,180)', 'rgb(90, 115,180)',   # izq
            'rgb(90, 115,180)', 'rgb(90, 115,180)',   # der
            'rgb(60,  70,120)', 'rgb(60,  70,120)',   # techo
        ]
        mesh = go.Mesh3d(
            x=x8, y=y8, z=z8,
            i=fi, j=fj, k=fk,
            facecolor=face_colors,
            opacity=opacity,
            flatshading=True,
            showscale=False,
            name="Edificio",
            hoverinfo="name",
        )
        # Aristas (wireframe)
        edges_x, edges_y, edges_z = [], [], []
        edge_pairs = [
            (0,1),(1,2),(2,3),(3,0),  # base
            (4,5),(5,6),(6,7),(7,4),  # techo
            (0,4),(1,5),(2,6),(3,7),  # pilares
        ]
        for a, b in edge_pairs:
            edges_x += [x8[a], x8[b], None]
            edges_y += [y8[a], y8[b], None]
            edges_z += [z8[a], z8[b], None]
        wire = go.Scatter3d(
            x=edges_x, y=edges_y, z=edges_z,
            mode='lines',
            line=dict(color='rgb(40,80,180)', width=2),
            hoverinfo='none',
            showlegend=False,
            name="Aristas",
        )
        return mesh, wire

    def panel_grid_traces(w, h, pw, ph, gap, poa_val, poa_min, poa_max, n_pan_target):
        """
        Genera un Mesh3d con la cuadrícula de paneles en la fachada (Y=-0.01).
        Colorea todos los paneles con el POA del mes seleccionado.
        """
        n_cols = max(1, int(w / (pw + gap)))
        n_rows = max(1, int(h / (ph + gap)))

        # Ajustar dimensiones para que llenen la fachada uniformemente
        actual_pw = max(0.1, (w - gap * (n_cols - 1)) / n_cols)
        actual_ph = max(0.1, (h - gap * (n_rows - 1)) / n_rows)

        color = _color_poa(poa_val, poa_min, poa_max)

        all_x, all_y, all_z = [], [], []
        all_i, all_j, all_k = [], [], []
        face_colors = []
        vert = 0

        for row in range(n_rows):
            for col in range(n_cols):
                x0 = -w/2 + col * (actual_pw + gap)
                x1 = x0 + actual_pw
                z0 = row * (actual_ph + gap)
                z1 = z0 + actual_ph
                yp = -0.01   # ligeramente por delante de la fachada

                # 4 vértices del panel
                all_x += [x0, x1, x1, x0]
                all_y += [yp, yp, yp, yp]
                all_z += [z0, z0, z1, z1]

                # 2 triángulos
                all_i += [vert,   vert]
                all_j += [vert+1, vert+2]
                all_k += [vert+2, vert+3]
                face_colors += [color, color]
                vert += 4

        n_shown = n_rows * n_cols

        panels_mesh = go.Mesh3d(
            x=all_x, y=all_y, z=all_z,
            i=all_i, j=all_j, k=all_k,
            facecolor=face_colors,
            opacity=0.95,
            flatshading=True,
            showscale=False,
            name=f"Paneles BIPV ({n_shown} unid.)",
            hovertemplate=(
                f"<b>Paneles BIPV</b><br>"
                f"POA {mes_nombre}: {poa_val:.0f} kWh/m²<br>"
                f"Paneles visualizados: {n_shown}<br>"
                f"<extra></extra>"
            ),
        )

        # Marco dorado alrededor de la fachada activa
        frame_x = [-w/2, w/2, w/2, -w/2, -w/2]
        frame_y = [-0.02]*5
        frame_z = [0,    0,   h,    h,    0   ]
        frame_line = go.Scatter3d(
            x=frame_x, y=frame_y, z=frame_z,
            mode='lines',
            line=dict(color='rgb(255,165,0)', width=4),
            showlegend=False,
            hoverinfo='none',
            name="Marco fachada",
        )
        return panels_mesh, frame_line, n_shown, n_rows, n_cols

    def sun_ray_trace(az_fachada, az_solar, el_solar, ancho, altura):
        """
        Genera un Scatter3d mostrando el rayo de sol entrante al modelo.
        Coordenadas locales: X = ancho fachada, Y = profundidad, Z = altura
        """
        az_f = math.radians(az_fachada)
        az_s = math.radians(az_solar)
        el   = math.radians(el_solar)

        # Vector sol en (Este, Norte, Arriba)
        se  = math.sin(az_s) * math.cos(el)
        sn  = math.cos(az_s) * math.cos(el)
        su  = math.sin(el)

        # Transformar a coords locales del edificio
        # X_local = E * cos(az_f) - N * sin(az_f)
        # Y_local = E * sin(az_f) + N * cos(az_f)
        sx_loc = se * math.cos(az_f) - sn * math.sin(az_f)
        sy_loc = se * math.sin(az_f) + sn * math.cos(az_f)
        sz_loc = su

        # Longitud del rayo = 1.2 × ancho
        L = max(ancho, altura) * 1.2

        # Centro de la fachada
        cx, cy, cz = 0.0, 0.0, altura / 2.0

        # Punto de inicio del rayo (posición del sol relativa al edificio)
        sx = cx + L * sx_loc
        sy = cy + L * sy_loc
        sz = cz + L * sz_loc

        # El sol está "detrás" de la fachada si sy_loc < 0 (Y_local < 0)
        # La fachada mira hacia Y < 0, así que sol_visible si sy_loc < 0
        sol_visible = sy_loc <= 0  # sol delante de la fachada

        if not sol_visible:
            return None, False

        # Rayo principal (línea amarilla)
        ray = go.Scatter3d(
            x=[sx, cx], y=[sy, cy], z=[sz, cz],
            mode='lines+markers',
            line=dict(color='rgb(255,220,0)', width=5),
            marker=dict(
                symbol='circle',   # único símbolo válido para todos los puntos
                size=[14, 6],
                color=['rgb(255,220,0)', 'rgb(255,120,0)'],
            ),
            name=f"☀️ Sol {mes_nombre} (mediodía)",
            hovertemplate=(
                f"<b>Rayo solar — {mes_nombre}</b><br>"
                f"Elevación: {el_solar:.1f}°<br>"
                f"Azimuth solar: {az_solar:.1f}°<br>"
                f"<extra></extra>"
            ),
        )
        return ray, True

    def colorbar_trace(poa_mensual, mes_idx, meses_es):
        """Scatter3d invisible solo para mostrar la barra de color de POA anual."""
        dummy = go.Scatter3d(
            x=[None]*12, y=[None]*12, z=[None]*12,
            mode='markers',
            marker=dict(
                color=poa_mensual,
                colorscale='YlOrRd',
                cmin=min(poa_mensual),
                cmax=max(poa_mensual),
                colorbar=dict(
                    title="POA<br>(kWh/m²<br>/mes)",
                    thickness=14,
                    len=0.6,
                    x=1.02,
                    tickvals=poa_mensual,
                    ticktext=meses_es,
                    tickfont=dict(size=10),
                ),
                showscale=True,
            ),
            showlegend=False,
            hoverinfo='none',
        )
        return dummy

    # ── Calcular posición solar para el mes ───────────────────────────────────
    az_solar_mes, el_solar_mes = 0.0, 30.0   # defaults

    try:
        import pvlib
        import pandas as pd
        mes_num = mes_idx + 1
        times   = pd.DatetimeIndex([f"2019-{mes_num:02d}-15 12:00:00"], tz="UTC")
        loc_pv  = pvlib.location.Location(lat, lon, tz="UTC", altitude=alt_m)
        sp      = loc_pv.get_solarposition(times)
        az_solar_mes = float(sp["azimuth"].iloc[0])
        el_solar_mes = float(sp["elevation"].iloc[0])
    except Exception:
        # Aproximación para Colombia (tropical)
        az_solar_mes = 180.0 if lat >= 0 else 0.0   # sol al sur en hemisferio norte
        el_solar_mes = 70.0 - abs(lat)               # ~60-70° en Colombia

    # ── Construir figura ──────────────────────────────────────────────────────
    poa_min_m = min(poa_mensual)
    poa_max_m = max(poa_mensual)
    poa_mes   = poa_mensual[mes_idx]

    mesh_ed, wire_ed = building_box_traces(ancho_m, profundidad_m, altura_m, opac_ed)
    mesh_pan, frame_pan, n_shown, n_rows, n_cols = panel_grid_traces(
        ancho_m, altura_m, pw, ph, gap, poa_mes, poa_min_m, poa_max_m, N_paneles
    )

    traces = [mesh_ed, wire_ed, mesh_pan, frame_pan]

    if show_sun:
        ray_tr, sol_vis = sun_ray_trace(azimuth, az_solar_mes, el_solar_mes,
                                         ancho_m, altura_m)
        if ray_tr is not None:
            traces.append(ray_tr)

    if show_all_months:
        traces.append(colorbar_trace(poa_mensual, mes_idx, MESES_ES))

    # Configurar cámara según vista seleccionada
    cam_presets = {
        "Fachada":     dict(x=0, y=-3, z=0.5),
        "Perspectiva": dict(x=1.5, y=-2, z=1.0),
        "Planta":      dict(x=0, y=0, z=3),
    }
    eye = cam_presets.get(vista, cam_presets["Perspectiva"])
    max_dim = max(ancho_m, profundidad_m, altura_m)
    eye_scaled = dict(x=eye["x"] * max_dim / 10,
                      y=eye["y"] * max_dim / 10,
                      z=eye["z"] * max_dim / 10)

    layout_3d = go.Layout(
        scene=dict(
            xaxis=dict(title="← Ancho fachada (m) →", showgrid=True,
                       zeroline=False, gridcolor='rgba(150,150,150,0.3)'),
            yaxis=dict(title="Profundidad (m)", showgrid=True,
                       zeroline=False, gridcolor='rgba(150,150,150,0.3)'),
            zaxis=dict(title="Altura (m)", showgrid=True,
                       zeroline=False, gridcolor='rgba(150,150,150,0.3)'),
            bgcolor='rgb(10, 15, 35)',
            camera=dict(eye=eye_scaled, up=dict(x=0, y=0, z=1)),
            aspectmode='data',
        ),
        paper_bgcolor='rgb(15, 20, 45)',
        plot_bgcolor='rgb(10, 15, 35)',
        font=dict(color='white', size=12),
        title=dict(
            text=(f"<b>Modelo 3D — {nombre_proy}</b><br>"
                  f"<sub>{ciudad} · {orient_label} · "
                  f"POA {mes_nombre}: <b>{poa_mes:.0f} kWh/m²</b></sub>"),
            x=0.5, xanchor='center', font=dict(size=14, color='white'),
        ),
        legend=dict(
            x=0.01, y=0.99, bgcolor='rgba(20,30,70,0.8)',
            bordercolor='rgba(100,130,200,0.5)', borderwidth=1,
            font=dict(color='white', size=11),
        ),
        margin=dict(l=0, r=60, t=80, b=0),
        height=540,
    )

    fig_3d = go.Figure(data=traces, layout=layout_3d)

    with col_fig3d:
        st.plotly_chart(fig_3d, use_container_width=True)

    # ── Métricas del modelo ───────────────────────────────────────────────────
    st.divider()
    _cob_m2 = min(area_m2, ancho_m * altura_m)

    _nota_paneles = "" if n_shown == N_paneles else f" (diseño: {N_paneles})"
    mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
    mc1.metric("Paneles visualizados",
               f"{n_shown}{_nota_paneles}",
               help="Calculado desde las dimensiones del edificio y del panel. "
                    "Puede diferir del número final del sistema por huecos o recortes.")
    mc2.metric("Potencia visualizada", f"{round(n_shown * pmax_panel / 1000, 2):.2f} kWp")
    mc3.metric("Filas × Columnas",   f"{n_rows} × {n_cols}")
    mc4.metric("Potencia instalada", f"{P_instalada_kWp:.2f} kWp")
    mc5.metric(f"POA {mes_nombre}",  f"{poa_mes:.0f} kWh/m²")
    mc6.metric("POA anual",          f"{sum(poa_mensual):.0f} kWh/m²")

    # ── Gráfica de barras POA mensual ─────────────────────────────────────────
    with st.expander("📊 Ver irradiancia POA mensual en la fachada"):
        colors_bar = [_color_poa(v, poa_min_m, poa_max_m) for v in poa_mensual]
        colors_bar[mes_idx] = 'rgb(255,255,100)'  # resaltar mes seleccionado

        fig_bar = go.Figure(go.Bar(
            x=MESES_ES,
            y=poa_mensual,
            marker_color=colors_bar,
            text=[f"{v:.0f}" for v in poa_mensual],
            textposition="outside",
            name="POA mensual",
        ))
        fig_bar.add_hline(
            y=sum(poa_mensual) / 12,
            line_dash="dash", line_color="white",
            annotation_text=f"Promedio: {sum(poa_mensual)/12:.0f} kWh/m²",
            annotation_position="top right",
        )
        fig_bar.update_layout(
            xaxis_title="Mes",
            yaxis_title="POA (kWh/m²/mes)",
            height=320,
            plot_bgcolor="rgb(15,20,45)",
            paper_bgcolor="rgb(15,20,45)",
            font=dict(color="white"),
            yaxis=dict(gridcolor="rgba(150,150,150,0.2)"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        src = "POA calculado desde TMY PVGIS" if poa_df is not None else \
              "POA estimado desde GHI de referencia IDEAM (ejecuta ☀️ Recurso Solar para datos reales)"
        st.caption(f"📌 Fuente: {src}")

    # (tab_modelo cerrada)



# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — B-5C: SUPERFICIES BIPV MÚLTIPLES
# Fachadas · Techos · Pérgolas · Marquesinas — multi-orientación
# ─────────────────────────────────────────────────────────────────────────────
with tab_solar:

    try:
        import pvlib as _pv
        import pandas as _pd
        import numpy as _np
        from calculos.multi_superficie import (
            TIPOS_SUPERFICIE, MESES_ES as _MESES_ES,
            superficie_nueva, superficies_por_defecto,
            calcular_poa_todas,
            poa_mensual_superficie, poa_anual_superficie,
            produccion_superficie,
            mapear_fachadas_csv, fs_mensual_por_superficie,
            color_tipo, color_poa_normalizado, color_fs,
        )
        _b5c_ok = True
    except Exception as _e5c:
        st.error(f"❌ Error cargando módulo multi-superficie: {_e5c}")
        _b5c_ok = False

    if _b5c_ok:

        stab_sup, stab_viz, stab_prod, stab_sol = st.tabs([
            "⚙️ Superficies BIPV",
            "🎨 Vista 3D Multi-Superficie",
            "📊 Producción por Superficie",
            "🌞 Trayectoria Solar",
        ])

        # Inicializar superficies en session_state
        if "superficies_bipv" not in st.session_state:
            st.session_state["superficies_bipv"] = superficies_por_defecto(
                azimuth_principal=float(st.session_state.get("azimuth_fachada", 180)),
                area_fachada=float(st.session_state.get("area_fachada_m2", 50.0)),
            )

        # ════════════════════════════════════════════════════════════════════
        # SUB-TAB 1 — GESTOR DE SUPERFICIES
        # ════════════════════════════════════════════════════════════════════
        with stab_sup:
            st.subheader("⚙️ Definir superficies BIPV del proyecto")
            st.caption(
                "Agrega fachadas, techos, pérgolas y marquesinas. "
                "Cada superficie tiene su propia orientación y área activa."
            )

            # Botones de alta rápida
            st.markdown("##### ➕ Agregar superficie")
            _btn_cols = st.columns(4)
            for _col_b, _tipo_b in zip(_btn_cols, ["Fachada", "Techo", "Pérgola", "Marquesina"]):
                _meta_b = TIPOS_SUPERFICIE[_tipo_b]
                if _col_b.button(
                    f"{_meta_b['icon']} {_tipo_b}",
                    key=f"add_sup_{_tipo_b}",
                    use_container_width=True,
                ):
                    _ex = st.session_state["superficies_bipv"]
                    _n  = sum(1 for s in _ex if s["tipo"] == _tipo_b) + 1
                    _ex.append(
                        superficie_nueva(
                            f"{_tipo_b} {_n}", _tipo_b,
                            area_m2=float(st.session_state.get("area_fachada_m2", 20.0)),
                        )
                    )
                    st.session_state["superficies_bipv"] = _ex
                    st.rerun()

            st.divider()
            st.markdown("##### 📋 Superficies configuradas")

            _sups_list       = st.session_state["superficies_bipv"]
            _sups_actualizado = []
            _idx_eliminar     = None

            for _i, _sup in enumerate(_sups_list):
                _meta_t = TIPOS_SUPERFICIE.get(_sup["tipo"], TIPOS_SUPERFICIE["Fachada"])
                with st.expander(
                    f"{_meta_t['icon']} **{_sup['nombre']}** — {_sup['tipo']} · "
                    f"Tilt {_sup['tilt_deg']:.0f}° · Az {_sup['azimuth_deg']:.0f}° · "
                    f"{_sup['area_m2']:.1f} m²",
                    expanded=(len(_sups_list) == 1),
                ):
                    _c1, _c2, _c3, _c4, _c5 = st.columns([2, 1, 1, 1, 1])
                    _c_del = st.columns([6, 1])[1]

                    _nom_e  = _c1.text_input("Nombre",  value=_sup["nombre"],  key=f"snom_{_i}")
                    _tipo_e = _c2.selectbox(
                        "Tipo", list(TIPOS_SUPERFICIE.keys()),
                        index=list(TIPOS_SUPERFICIE.keys()).index(
                            _sup["tipo"] if _sup["tipo"] in TIPOS_SUPERFICIE else "Fachada"
                        ),
                        key=f"stipo_{_i}",
                    )
                    _meta_e = TIPOS_SUPERFICIE[_tipo_e]
                    _tilt_e = _c3.number_input(
                        "Tilt (°)",
                        min_value=float(_meta_e["tilt_min"]),
                        max_value=float(_meta_e["tilt_max"]),
                        value=float(max(_meta_e["tilt_min"],
                                        min(_meta_e["tilt_max"], _sup["tilt_deg"]))),
                        step=5.0, key=f"stilt_{_i}",
                        help=_meta_e["descripcion"],
                    )
                    _az_e   = _c4.number_input(
                        "Azimuth (°)", 0.0, 360.0,
                        value=float(_sup["azimuth_deg"]),
                        step=5.0, key=f"saz_{_i}",
                        help="0=Norte · 90=Este · 180=Sur · 270=Oeste",
                    )
                    _area_e = _c5.number_input(
                        "Área (m²)", 1.0, 5000.0,
                        value=float(_sup["area_m2"]),
                        step=1.0, key=f"sarea_{_i}",
                    )
                    _act_e  = _c1.checkbox(
                        "Activa", value=bool(_sup.get("activa", True)), key=f"sact_{_i}"
                    )
                    if _c_del.button("🗑️", key=f"sdel_{_i}", help="Eliminar"):
                        _idx_eliminar = _i

                    _sups_actualizado.append({
                        "nombre":      _nom_e,
                        "tipo":        _tipo_e,
                        "tilt_deg":    _tilt_e,
                        "azimuth_deg": _az_e,
                        "area_m2":     _area_e,
                        "activa":      _act_e,
                    })

            if _idx_eliminar is not None:
                _sups_actualizado.pop(_idx_eliminar)
            st.session_state["superficies_bipv"] = _sups_actualizado

            # Calcular POA para todas
            st.divider()
            _tmy_sup = st.session_state.get("tmy_df")
            _cb1, _cb2 = st.columns([2, 3])
            _btn_poa = _cb1.button(
                "⚡ Calcular POA para todas las superficies",
                type="primary", disabled=(_tmy_sup is None),
                key="btn_calc_poa_all",
            )
            if _tmy_sup is None:
                _cb2.info("ℹ️ Primero calcula el Recurso Solar en ☀️.")

            if _btn_poa and _tmy_sup is not None:
                _sups_act = [s for s in _sups_actualizado if s.get("activa", True)]
                with st.spinner(f"Calculando POA para {len(_sups_act)} superficies..."):
                    _poa_m = calcular_poa_todas(_sups_act, _tmy_sup, lat, lon, alt_m)
                    st.session_state["poa_superficies"]    = _poa_m
                    st.session_state["poa_superficies_ok"] = True
                st.success(f"✅ POA calculada para {len(_poa_m)} superficie(s).")

            # Resumen POA
            _poa_ss = st.session_state.get("poa_superficies", {})
            if _poa_ss:
                st.markdown("##### 📊 Resumen POA por superficie")
                _eta_g = float(st.session_state.get("eta_panel", 0.16))
                _pr_g  = float(st.session_state.get("pr_sistema", 0.78))
                _rows_r, _tot_r = [], 0.0
                for _s in _sups_actualizado:
                    if not _s.get("activa", True):
                        continue
                    _pd_s  = _poa_ss.get(_s["nombre"])
                    _pa_s  = poa_anual_superficie(_pd_s) if _pd_s is not None else 0.0
                    _pr_s  = produccion_superficie(_pd_s, _s["area_m2"], _eta_g, _pr_g)
                    _mt_s  = TIPOS_SUPERFICIE.get(_s["tipo"], {})
                    _tot_r += _pr_s["e_ac_anual_kWh"]
                    _rows_r.append({
                        "Superficie":       f"{_mt_s.get('icon','')} {_s['nombre']}",
                        "Tipo":             _s["tipo"],
                        "Tilt/Az":          f"{_s['tilt_deg']:.0f}°/{_s['azimuth_deg']:.0f}°",
                        "Área (m²)":        f"{_s['area_m2']:.1f}",
                        "POA (kWh/m²/año)": f"{_pa_s:.0f}",
                        "E_ac (kWh/año)":   f"{_pr_s['e_ac_anual_kWh']:,.0f}",
                    })
                if _rows_r:
                    st.dataframe(_pd.DataFrame(_rows_r), use_container_width=True, hide_index=True)
                    st.metric("⚡ Producción total del sistema", f"{_tot_r:,.0f} kWh/año")
                    st.caption(f"η={_eta_g*100:.0f}% · PR={_pr_g*100:.0f}%")


        # ════════════════════════════════════════════════════════════════════
        # SUB-TAB 2 — VISTA 3D MULTI-SUPERFICIE
        # ════════════════════════════════════════════════════════════════════
        with stab_viz:
            st.subheader("🎨 Modelo 3D — todas las superficies BIPV")
            st.caption(
                "Color: POA mensual (azul→rojo) o FS del CSV (verde→rojo). "
                "Incluye fachadas, techos, pérgolas y marquesinas."
            )

            _sups_viz   = [s for s in st.session_state.get("superficies_bipv", []) if s.get("activa", True)]
            _poa_viz    = st.session_state.get("poa_superficies", {})
            _df_fs_viz  = st.session_state.get("df_fs_raw")
            _csv_viz_ok = st.session_state.get("csv_fs_ok", False)

            if not _sups_viz:
                st.info("ℹ️ Define al menos una superficie activa en ⚙️ Superficies BIPV.")
            else:
                _ctrl_col, _fig_col = st.columns([1, 4])

                with _ctrl_col:
                    st.markdown("#### 🎛️ Vista")
                    _mes_viz = st.slider("Mes", 1, 12, 6, key="viz3d_mes")
                    st.caption(f"**{_MESES_ES[_mes_viz - 1]}**")
                    _modo_c = st.radio(
                        "Colorear por", ["POA mensual", "FS del CSV"], key="viz3d_color"
                    )
                    if _modo_c == "FS del CSV" and not _csv_viz_ok:
                        st.warning("Sin CSV — usando POA.")
                        _modo_c = "POA mensual"
                    _vista_3d = st.radio("Vista", ["Perspectiva","Fachada","Planta","Lateral"], key="viz3d_vista")
                    _opac_v   = st.slider("Opacidad edificio", 0.1, 0.8, 0.3, 0.1, key="viz3d_op")
                    _grid_v   = st.checkbox("Cuadrícula paneles", True,  key="viz3d_grid")
                    _lbl_v    = st.checkbox("Etiquetas",           True,  key="viz3d_lbl")
                    st.markdown("---")
                    st.markdown("##### Leyenda")
                    for _sl in _sups_viz:
                        _ic_l = TIPOS_SUPERFICIE.get(_sl["tipo"], {}).get("icon", "")
                        _co_l = color_tipo(_sl["tipo"])
                        st.markdown(
                            f'<span style="color:{_co_l};font-size:18px">■</span> '
                            f'{_ic_l} {_sl["nombre"]}',
                            unsafe_allow_html=True,
                        )

                # Helpers geometría
                def _face_from_az_v(sz, bz):
                    r = (sz - bz + 360) % 360
                    if r < 45 or r >= 315: return "front"
                    elif r < 135: return "left"
                    elif r < 225: return "back"
                    return "right"

                def _fachada_v(face, w, d, h, area):
                    if face in ("front", "back"):
                        fw = min(w, _np.sqrt(max(1.0, area * w / max(1.0, h))))
                        fh = min(h, area / max(0.1, fw))
                        cx, cz = 0.0, h/2.0
                        oy = -0.04 if face == "front" else 0.04
                        yf = (0.0 if face == "front" else d) + oy
                        return [cx-fw/2, cx+fw/2, cx+fw/2, cx-fw/2], [yf]*4, [cz-fh/2, cz-fh/2, cz+fh/2, cz+fh/2], fw, fh
                    else:
                        fd = min(d, _np.sqrt(max(1.0, area * d / max(1.0, h))))
                        fh = min(h, area / max(0.1, fd))
                        cy, cz = d/2.0, h/2.0
                        ox = -0.04 if face == "left" else 0.04
                        xf = (-w/2 if face == "left" else w/2) + ox
                        return [xf]*4, [cy-fd/2, cy+fd/2, cy+fd/2, cy-fd/2], [cz-fh/2, cz-fh/2, cz+fh/2, cz+fh/2], fd, fh

                def _techo_v(w, d, h, area, tilt):
                    frac = min(1.0, area / max(1.0, w * d))
                    fw = min(w, w * _np.sqrt(frac)); fd = min(d, area / max(0.1, fw))
                    cx, cy, z0 = 0.0, d/2.0, h + 0.06
                    dz = fd * _np.tan(_np.radians(max(0, tilt)))
                    return [cx-fw/2, cx+fw/2, cx+fw/2, cx-fw/2], [cy-fd/2, cy-fd/2, cy+fd/2, cy+fd/2], [z0, z0, z0+dz, z0+dz], fw, fd

                def _pergola_v(face, w, d, h, area):
                    proj = min(6.0, _np.sqrt(max(1.0, area)))
                    pw_p = min(area / max(0.5, proj), w if face in ("front","back") else d)
                    zp   = max(3.0, h * 0.55)
                    cx   = 0.0
                    if face == "front":
                        xs = [cx-pw_p/2, cx+pw_p/2, cx+pw_p/2, cx-pw_p/2]; ys = [-0.1]*2 + [-0.1-proj]*2; zs = [zp]*4
                    elif face == "back":
                        xs = [cx-pw_p/2, cx+pw_p/2, cx+pw_p/2, cx-pw_p/2]; ys = [d+0.1]*2 + [d+0.1+proj]*2; zs = [zp]*4
                    elif face == "left":
                        xs = [-w/2-0.1]*2 + [-w/2-0.1-proj]*2; ys = [d/2-pw_p/2, d/2+pw_p/2, d/2+pw_p/2, d/2-pw_p/2]; zs = [zp]*4
                    else:
                        xs = [w/2+0.1]*2 + [w/2+0.1+proj]*2; ys = [d/2-pw_p/2, d/2+pw_p/2, d/2+pw_p/2, d/2-pw_p/2]; zs = [zp]*4
                    posts = [([xs[i], xs[i]], [ys[i], ys[i]], [0.0, zp]) for i in range(4)]
                    return xs, ys, zs, pw_p, proj, posts

                def _marquesina_v(face, w, d, h, area, tilt):
                    proj = min(4.0, area / max(0.3, min(w,h)*0.5))
                    mw   = min(area / max(0.3, proj), w if face in ("front","back") else d)
                    zb   = h * 0.60; dz = proj * _np.tan(_np.radians(max(1, tilt)))
                    cx   = 0.0
                    if face == "front":
                        return [cx-mw/2, cx+mw/2, cx+mw/2, cx-mw/2], [-0.05]*2+[-0.05-proj]*2, [zb, zb, zb-dz, zb-dz], mw, proj
                    elif face == "back":
                        return [cx-mw/2, cx+mw/2, cx+mw/2, cx-mw/2], [d+0.05]*2+[d+0.05+proj]*2, [zb, zb, zb-dz, zb-dz], mw, proj
                    elif face == "left":
                        return [-w/2-0.05]*2+[-w/2-0.05-proj]*2, [d/2-mw/2, d/2+mw/2, d/2+mw/2, d/2-mw/2], [zb, zb, zb-dz, zb-dz], mw, proj
                    else:
                        return [w/2+0.05]*2+[w/2+0.05+proj]*2, [d/2-mw/2, d/2+mw/2, d/2+mw/2, d/2-mw/2], [zb, zb, zb-dz, zb-dz], mw, proj

                def _quad(xs, ys, zs, col, op, nm, hov):
                    return go.Mesh3d(
                        x=xs, y=ys, z=zs,
                        i=[0, 0], j=[1, 2], k=[2, 3],
                        color=col, opacity=op, flatshading=True,
                        showscale=False, name=nm,
                        hovertext=hov,
                        hovertemplate="%{hovertext}<extra></extra>",
                    )

                def _grid(xs, ys, zs, fw, fh, pw=0.60, ph=1.20):
                    v0=_np.array([xs[0],ys[0],zs[0]],dtype=float)
                    v1=_np.array([xs[1],ys[1],zs[1]],dtype=float)
                    v3=_np.array([xs[3],ys[3],zs[3]],dtype=float)
                    sw=max(1,int(fw/max(pw,0.01))); sh=max(1,int(fh/max(ph,0.01)))
                    lx,ly,lz=[],[],[]
                    for i in range(sw+1):
                        t=i/max(sw,1); pb=v0+t*(v1-v0); pt=v3+t*(v1-v0)
                        lx+=[pb[0],pt[0],None]; ly+=[pb[1],pt[1],None]; lz+=[pb[2],pt[2],None]
                    for j in range(sh+1):
                        t=j/max(sh,1); pl=v0+t*(v3-v0); pr_v=v1+t*(v3-v0)
                        lx+=[pl[0],pr_v[0],None]; ly+=[pl[1],pr_v[1],None]; lz+=[pl[2],pr_v[2],None]
                    return go.Scatter3d(x=lx,y=ly,z=lz,mode="lines",
                                        line=dict(color="rgba(0,0,0,0.28)",width=1),
                                        showlegend=False,hoverinfo="skip")

                # Calcular colores
                _baz_v = float(st.session_state.get("azimuth_fachada", 180))
                _wv, _dv, _hv = ancho_m, profundidad_m, altura_m
                _sup_cols: dict = {}; _sup_hovs: dict = {}; _vals_v: list = []

                for _sv in _sups_viz:
                    _nv = _sv["nombre"]
                    _pdf_v = _poa_viz.get(_nv)
                    if _modo_c == "POA mensual":
                        _pm_v = poa_mensual_superficie(_pdf_v) if _pdf_v else None
                        _val_v = _pm_v[_mes_viz-1] if _pm_v else (
                            float(st.session_state.get("GHI_kWh_m2_dia", 5.0))
                            * (0.5 + 0.5 * _np.cos(_np.radians(float(_sv["tilt_deg"])))) * 30.0
                        )
                        _pa_v = poa_anual_superficie(_pdf_v) if _pdf_v else 0.0
                        _sup_hovs[_nv] = (
                            f"<b>{_nv}</b><br>Tipo: {_sv['tipo']}<br>"
                            f"Tilt {_sv['tilt_deg']:.0f}° · Az {_sv['azimuth_deg']:.0f}°<br>"
                            f"Área: {_sv['area_m2']:.1f} m²<br>"
                            f"POA {_MESES_ES[_mes_viz-1]}: <b>{_val_v:.0f} kWh/m²</b><br>"
                            f"POA anual: {_pa_v:.0f} kWh/m²"
                        )
                    else:
                        _mf_v = mapear_fachadas_csv(_df_fs_viz, _sups_viz)
                        _fs_v = fs_mensual_por_superficie(_df_fs_viz, _mf_v.get(_nv))
                        _val_v = _fs_v[_mes_viz-1]
                        _sup_hovs[_nv] = (
                            f"<b>{_nv}</b><br>Tipo: {_sv['tipo']}<br>"
                            f"Tilt {_sv['tilt_deg']:.0f}° · Az {_sv['azimuth_deg']:.0f}°<br>"
                            f"Área: {_sv['area_m2']:.1f} m²<br>"
                            f"FS {_MESES_ES[_mes_viz-1]}: <b>{_val_v:.3f}</b> "
                            f"({'🔴bypass' if _val_v>0.35 else '🟠parcial' if _val_v>0.10 else '🟢libre'})"
                        )
                    _vals_v.append(_val_v); _sup_cols[_nv] = _val_v

                _vmin_v = min(_vals_v) if _vals_v else 0.0
                _vmax_v = max(_vals_v) if _vals_v else 1.0
                if abs(_vmax_v - _vmin_v) < 0.5: _vmax_v = _vmin_v + max(1.0, _vmin_v * 0.1)
                for _nv in _sup_cols:
                    _fv_c = float(_sup_cols[_nv])
                    _sup_cols[_nv] = (color_fs(_fv_c) if _modo_c == "FS del CSV"
                                      else color_poa_normalizado(_fv_c, _vmin_v, _vmax_v))

                # Figura
                _fig3d = go.Figure()
                # Edificio
                _x8b=[-_wv/2,_wv/2,_wv/2,-_wv/2,-_wv/2,_wv/2,_wv/2,-_wv/2]
                _y8b=[0,0,_dv,_dv,0,0,_dv,_dv]; _z8b=[0,0,0,0,_hv,_hv,_hv,_hv]
                _fcb=["rgb(90,120,180)"]*2+["rgb(70,95,150)"]*2+["rgb(80,105,165)"]*4+["rgb(55,65,110)"]*2
                _fig3d.add_trace(go.Mesh3d(
                    x=_x8b,y=_y8b,z=_z8b,
                    i=[0,0,3,3,3,3,1,1,4,4],j=[1,5,2,6,0,4,2,6,5,6],k=[5,4,6,7,4,7,6,5,6,7],
                    facecolor=_fcb,opacity=_opac_v,flatshading=True,showscale=False,name="Edificio",
                    hovertemplate=f"<b>Edificio</b><br>W:{_wv:.1f}m D:{_dv:.1f}m H:{_hv:.1f}m<extra></extra>",
                ))

                _pw_v, _ph_v = 0.60, 1.20
                for _sv in _sups_viz:
                    _nv = _sv["nombre"]; _tv = _sv["tipo"]
                    _cv = _sup_cols.get(_nv, color_tipo(_tv))
                    _hv_t = _sup_hovs.get(_nv, _nv)
                    _fv_v = _face_from_az_v(float(_sv["azimuth_deg"]), _baz_v)

                    if _tv == "Fachada":
                        _xs_v,_ys_v,_zs_v,_fw_v,_fh_v = _fachada_v(_fv_v,_wv,_dv,_hv,float(_sv["area_m2"]))
                        _fig3d.add_trace(_quad(_xs_v,_ys_v,_zs_v,_cv,0.90,_nv,_hv_t))
                        if _grid_v: _fig3d.add_trace(_grid(_xs_v,_ys_v,_zs_v,_fw_v,_fh_v,_pw_v,_ph_v))
                    elif _tv == "Techo":
                        _xs_v,_ys_v,_zs_v,_fw_v,_fh_v = _techo_v(_wv,_dv,_hv,float(_sv["area_m2"]),float(_sv["tilt_deg"]))
                        _fig3d.add_trace(_quad(_xs_v,_ys_v,_zs_v,_cv,0.90,_nv,_hv_t))
                        if _grid_v: _fig3d.add_trace(_grid(_xs_v,_ys_v,_zs_v,_fw_v,_fh_v,_pw_v,_pw_v))
                    elif _tv == "Pérgola":
                        _xs_v,_ys_v,_zs_v,_fw_v,_fh_v,_posts_v = _pergola_v(_fv_v,_wv,_dv,_hv,float(_sv["area_m2"]))
                        _fig3d.add_trace(_quad(_xs_v,_ys_v,_zs_v,_cv,0.90,_nv,_hv_t))
                        if _grid_v: _fig3d.add_trace(_grid(_xs_v,_ys_v,_zs_v,_fw_v,_fh_v,_pw_v,_pw_v))
                        for _px_p,_py_p,_pz_p in _posts_v:
                            _fig3d.add_trace(go.Scatter3d(x=_px_p,y=_py_p,z=_pz_p,mode="lines",
                                                           line=dict(color="rgb(100,80,60)",width=4),
                                                           showlegend=False,hoverinfo="skip"))
                    elif _tv == "Marquesina":
                        _xs_v,_ys_v,_zs_v,_fw_v,_fh_v = _marquesina_v(_fv_v,_wv,_dv,_hv,float(_sv["area_m2"]),float(_sv["tilt_deg"]))
                        _fig3d.add_trace(_quad(_xs_v,_ys_v,_zs_v,_cv,0.90,_nv,_hv_t))
                        if _grid_v: _fig3d.add_trace(_grid(_xs_v,_ys_v,_zs_v,_fw_v,_fh_v,_pw_v,_ph_v))

                    if _lbl_v:
                        _fig3d.add_trace(go.Scatter3d(
                            x=[float(_np.mean(_xs_v))],y=[float(_np.mean(_ys_v))],
                            z=[float(_np.mean(_zs_v))+max(0.4,_hv*0.04)],
                            mode="text",
                            text=[f"{TIPOS_SUPERFICIE.get(_tv,{}).get('icon','')} {_nv}"],
                            textfont=dict(size=10,color=_cv),
                            showlegend=False,hoverinfo="skip",
                        ))

                _CAMS = {
                    "Perspectiva": dict(eye=dict(x=1.5,y=-1.8,z=1.2)),
                    "Fachada":     dict(eye=dict(x=0.0,y=-2.5,z=0.5)),
                    "Planta":      dict(eye=dict(x=0.0,y=0.0, z=3.0)),
                    "Lateral":     dict(eye=dict(x=2.5,y=0.5, z=0.8)),
                }
                _fig3d.update_layout(
                    height=580,
                    scene=dict(
                        xaxis=dict(title="Ancho (m)", showgrid=True, gridcolor="rgba(200,200,200,0.4)"),
                        yaxis=dict(title="Profundidad (m)", showgrid=True, gridcolor="rgba(200,200,200,0.4)"),
                        zaxis=dict(title="Altura (m)", showgrid=True, gridcolor="rgba(200,200,200,0.4)"),
                        bgcolor="rgba(240,248,255,0.6)",
                        camera=_CAMS.get(_vista_3d, _CAMS["Perspectiva"]),
                        aspectmode="data",
                    ),
                    margin=dict(l=0,r=0,t=44,b=0),
                    paper_bgcolor="white",showlegend=False,
                    title=dict(
                        text=(f"<b>Sistema BIPV Multi-Superficie — {nombre_proy}</b>  "
                              f"<sup>{len(_sups_viz)} sup. activa(s) · "
                              f"{_MESES_ES[_mes_viz-1]} · {_modo_c}</sup>"),
                        x=0.5,xanchor="center",
                    ),
                )
                with _fig_col:
                    st.plotly_chart(_fig3d, use_container_width=True)

                st.divider()
                if _modo_c == "POA mensual":
                    _bc1,_bc2,_bc3 = st.columns(3)
                    _bc1.metric(f"POA mín — {_MESES_ES[_mes_viz-1]}", f"{_vmin_v:.0f} kWh/m²")
                    _bc2.metric(f"POA máx — {_MESES_ES[_mes_viz-1]}", f"{_vmax_v:.0f} kWh/m²")
                    _bc3.info("🔵 Azul=bajo · 🟡 Amarillo=medio · 🔴 Rojo=alto")
                else:
                    st.info("🟢 Libre (FS<10%) · 🟠 Parcial (10-35%) · 🔴 Bypass (>35%)")

                # Tabla del mes
                _rows_mv = []
                for _sv in _sups_viz:
                    _nv = _sv["nombre"]
                    _pdf_vm = _poa_viz.get(_nv)
                    _pm_vm  = poa_mensual_superficie(_pdf_vm) if _pdf_vm else [0.0]*12
                    _pv_vm  = _pm_vm[_mes_viz-1]
                    _e_vm   = _pv_vm * _sv["area_m2"] * float(st.session_state.get("eta_panel",0.16)) * float(st.session_state.get("pr_sistema",0.78))
                    _row_mv = {
                        "Superficie": f"{TIPOS_SUPERFICIE.get(_sv['tipo'],{}).get('icon','')} {_nv}",
                        "Tipo": _sv["tipo"],
                        f"POA {_MESES_ES[_mes_viz-1]} (kWh/m²)": f"{_pv_vm:.1f}",
                        f"E_ac {_MESES_ES[_mes_viz-1]} (kWh)": f"{_e_vm:.1f}",
                    }
                    if _csv_viz_ok and _df_fs_viz is not None:
                        _mf_vm = mapear_fachadas_csv(_df_fs_viz, _sups_viz)
                        _fs_vm = fs_mensual_por_superficie(_df_fs_viz, _mf_vm.get(_nv))
                        _fvv   = _fs_vm[_mes_viz-1]
                        _row_mv[f"FS {_MESES_ES[_mes_viz-1]}"] = f"{_fvv:.3f}"
                        _row_mv["Estado"] = ("🟢 Libre" if _fvv<0.10 else "🟠 Parcial" if _fvv<0.35 else "🔴 Bypass")
                    _rows_mv.append(_row_mv)
                if _rows_mv:
                    st.markdown(f"**Valores del mes — {_MESES_ES[_mes_viz-1]}**")
                    st.dataframe(_pd.DataFrame(_rows_mv), use_container_width=True, hide_index=True)


        # ════════════════════════════════════════════════════════════════════
        # SUB-TAB 3 — PRODUCCIÓN POR SUPERFICIE
        # ════════════════════════════════════════════════════════════════════
        with stab_prod:
            st.subheader("📊 Producción mensual por superficie")
            st.caption("Requiere POA calculada en ⚙️ Superficies BIPV.")

            _sups_p  = [s for s in st.session_state.get("superficies_bipv", []) if s.get("activa", True)]
            _poa_p   = st.session_state.get("poa_superficies", {})
            _df_fsp  = st.session_state.get("df_fs_raw")
            _csv_p   = st.session_state.get("csv_fs_ok", False)
            _eta_p   = float(st.session_state.get("eta_panel", 0.16))
            _pr_p    = float(st.session_state.get("pr_sistema", 0.78))

            if not _poa_p:
                st.info("ℹ️ Primero calcula la POA en ⚙️ Superficies BIPV.")
            else:
                # 1. Barras apiladas
                st.markdown("#### 1. Producción mensual (barras apiladas)")
                _fig_stk = go.Figure()
                _tot_m = [0.0]*12
                for _sp in _sups_p:
                    _pdf_p = _poa_p.get(_sp["nombre"])
                    if not _pdf_p or _pdf_p.empty: continue
                    _prod_p = produccion_superficie(_pdf_p, _sp["area_m2"], _eta_p, _pr_p)
                    for _mi in range(12): _tot_m[_mi] += _prod_p["e_ac_mensual"][_mi]
                    _fig_stk.add_trace(go.Bar(
                        name=f"{TIPOS_SUPERFICIE.get(_sp['tipo'],{}).get('icon','')} {_sp['nombre']}",
                        x=_MESES_ES, y=_prod_p["e_ac_mensual"],
                        marker_color=color_tipo(_sp["tipo"]),
                        hovertemplate=f"<b>{_sp['nombre']}</b><br>%{{x}}: <b>%{{y:.1f}} kWh</b><extra></extra>",
                    ))
                _fig_stk.add_trace(go.Scatter(
                    name="▲ Total", x=_MESES_ES, y=_tot_m,
                    mode="lines+markers", line=dict(color="black", width=2.5, dash="dot"),
                    marker=dict(size=7),
                    hovertemplate="<b>Total</b> %{x}: <b>%{y:.1f} kWh</b><extra></extra>",
                ))
                _fig_stk.update_layout(
                    barmode="stack", height=420,
                    xaxis_title="Mes", yaxis_title="Energía AC (kWh)",
                    legend=dict(orientation="h", y=-0.28, font_size=10),
                    plot_bgcolor="white", paper_bgcolor="white",
                    title=dict(text="<b>Producción mensual por superficie BIPV</b>", x=0.5, xanchor="center"),
                )
                st.plotly_chart(_fig_stk, use_container_width=True)

                # 2. POA anual horizontal
                st.divider()
                st.markdown("#### 2. Recurso solar anual por orientación")
                _pa_list, _et_list, _co_list = [], [], []
                for _sp in _sups_p:
                    _pdf_p = _poa_p.get(_sp["nombre"])
                    _pa_v2 = poa_anual_superficie(_pdf_p) if _pdf_p else 0.0
                    _pa_list.append(_pa_v2)
                    _et_list.append(
                        f"{TIPOS_SUPERFICIE.get(_sp['tipo'],{}).get('icon','')} "
                        f"{_sp['nombre']} ({_sp['tilt_deg']:.0f}°/Az{_sp['azimuth_deg']:.0f}°)"
                    )
                    _co_list.append(color_tipo(_sp["tipo"]))
                _fig_poa = go.Figure(go.Bar(
                    x=_pa_list, y=_et_list, orientation="h",
                    marker_color=_co_list,
                    text=[f"{v:.0f}" for v in _pa_list], textposition="auto",
                    hovertemplate="POA: <b>%{x:.0f} kWh/m²/año</b><extra></extra>",
                ))
                _fig_poa.update_layout(
                    height=max(280, 80+60*len(_sups_p)), xaxis_title="POA anual (kWh/m²/año)",
                    plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
                    title=dict(text="<b>Recurso solar por orientación</b>", x=0.5, xanchor="center"),
                )
                st.plotly_chart(_fig_poa, use_container_width=True)

                # 3. Tabla resumen anual
                st.divider()
                st.markdown("#### 3. Resumen anual del sistema")
                _rows_a, _tot_ar, _tot_ea = [], 0.0, 0.0
                for _sp in _sups_p:
                    _pdf_p = _poa_p.get(_sp["nombre"])
                    _pa_a  = poa_anual_superficie(_pdf_p) if _pdf_p else 0.0
                    _pr_a  = produccion_superficie(_pdf_p, _sp["area_m2"], _eta_p, _pr_p)
                    _tot_ar += _sp["area_m2"]; _tot_ea += _pr_a["e_ac_anual_kWh"]
                    _fs_str = "—"
                    if _csv_p and _df_fsp is not None:
                        _mf_a = mapear_fachadas_csv(_df_fsp, _sups_p)
                        _fs_a = fs_mensual_por_superficie(_df_fsp, _mf_a.get(_sp["nombre"]))
                        _fs_str = f"{float(_np.mean(_fs_a)):.3f}"
                    _rows_a.append({
                        "Superficie": f"{TIPOS_SUPERFICIE.get(_sp['tipo'],{}).get('icon','')} {_sp['nombre']}",
                        "Tipo": _sp["tipo"],
                        "Tilt/Az": f"{_sp['tilt_deg']:.0f}°/{_sp['azimuth_deg']:.0f}°",
                        "Área (m²)": f"{_sp['area_m2']:.1f}",
                        "POA (kWh/m²/año)": f"{_pa_a:.0f}",
                        "E_ac (kWh/año)": f"{_pr_a['e_ac_anual_kWh']:,.0f}",
                        "% total": "—", "FS medio": _fs_str,
                    })
                for _r in _rows_a:
                    _ev = float(_r["E_ac (kWh/año)"].replace(",",""))
                    _r["% total"] = f"{_ev/max(1.0,_tot_ea)*100:.1f}%"
                st.dataframe(_pd.DataFrame(_rows_a), use_container_width=True, hide_index=True)
                _sa1,_sa2,_sa3,_sa4 = st.columns(4)
                _sa1.metric("Superficies activas", str(len(_sups_p)))
                _sa2.metric("Área total (m²)", f"{_tot_ar:.1f}")
                _sa3.metric("E_ac total (kWh/año)", f"{_tot_ea:,.0f}")
                _sa4.metric("Densidad", f"{_tot_ea/max(1,_tot_ar):.0f} kWh/m²·año")
                st.session_state["multi_sup_e_ac_total_kWh"] = round(_tot_ea, 1)
                st.session_state["multi_sup_area_total_m2"]  = round(_tot_ar, 2)
                st.session_state["multi_sup_ok"]             = True

                # 4. FS por superficie desde CSV
                if _csv_p and _df_fsp is not None:
                    st.divider()
                    st.markdown("#### 4. Factor de sombreado por superficie (CSV)")
                    _fach_csv = (sorted(_df_fsp["fachada"].dropna().unique().tolist())
                                 if "fachada" in _df_fsp.columns else [])
                    if not _fach_csv:
                        st.caption("El CSV no tiene columna 'Fachada' — FS uniforme para todas.")
                        _fs_u = _df_fsp.groupby("mes")["FS"].mean()
                        _fig_fsu = go.Figure(go.Bar(
                            x=_MESES_ES, y=[float(_fs_u.get(m,0)) for m in range(1,13)],
                            marker_color="orange", name="FS uniforme",
                        ))
                        _fig_fsu.update_layout(
                            height=300, yaxis_title="FS promedio mensual", yaxis_range=[0,1],
                            plot_bgcolor="white", paper_bgcolor="white",
                        )
                        st.plotly_chart(_fig_fsu, use_container_width=True)
                    else:
                        st.caption(f"Fachadas en CSV: **{', '.join(_fach_csv)}** — asigna cada superficie.")
                        _col_m, _col_g = st.columns([1, 2])
                        _opc_csv = ["— No asignar —"] + _fach_csv
                        _map_m = {}
                        for _sp in _sups_p:
                            _nm_bx = _sp["nombre"]
                            _am    = mapear_fachadas_csv(_df_fsp, _sups_p).get(_nm_bx)
                            _idx_d = _opc_csv.index(_am) if _am in _opc_csv else 0
                            _sel_v = _col_m.selectbox(
                                f"{TIPOS_SUPERFICIE.get(_sp['tipo'],{}).get('icon','')} {_nm_bx}",
                                _opc_csv, index=_idx_d, key=f"map_csv_{_nm_bx}",
                            )
                            _map_m[_nm_bx] = None if _sel_v == "— No asignar —" else _sel_v
                        _fig_fsm = go.Figure()
                        for _sp in _sups_p:
                            _fs_bx = fs_mensual_por_superficie(_df_fsp, _map_m.get(_sp["nombre"]))
                            _fig_fsm.add_trace(go.Scatter(
                                x=_MESES_ES, y=_fs_bx, mode="lines+markers",
                                name=f"{TIPOS_SUPERFICIE.get(_sp['tipo'],{}).get('icon','')} {_sp['nombre']}",
                                line=dict(color=color_tipo(_sp["tipo"])),
                                hovertemplate=f"<b>{_sp['nombre']}</b><br>%{{x}}: FS=<b>%{{y:.3f}}</b><extra></extra>",
                            ))
                        _fig_fsm.update_layout(
                            height=340,
                            yaxis=dict(title="Factor Sombreado (FS)", range=[0,1]),
                            xaxis_title="Mes", plot_bgcolor="white", paper_bgcolor="white",
                            legend=dict(orientation="h", y=-0.30),
                            title=dict(text="<b>FS mensual por superficie</b>", x=0.5, xanchor="center"),
                        )
                        with _col_g:
                            st.plotly_chart(_fig_fsm, use_container_width=True)

        # ════════════════════════════════════════════════════════════════════
        # SUB-TAB 4 — TRAYECTORIA SOLAR (contenido original conservado)
        # ════════════════════════════════════════════════════════════════════
        with stab_sol:
            st.subheader("\U0001f31e Diagrama de trayectoria solar y análisis de sombras")
            st.caption(
                "Trayectoria del sol por mes · Perfil de horizonte · "
                "Horas productivas vs sombreadas — B-5C"
            )

            _tmy_s      = st.session_state.get("tmy_df")
            _poa_s      = st.session_state.get("poa_df")
            _mm_ok_s    = bool(st.session_state.get("mismatch_ok", False))
            _sm_ok_s    = bool(st.session_state.get("sombra_ok", False))
            _fs_anual_s = st.session_state.get("factor_sombra_anual", None)
            _hz_df_s    = st.session_state.get("horizonte_df")

            _cs1,_cs2,_cs3,_cs4 = st.columns(4)
            _cs1.metric("Recurso Solar",  "\u2705 OK" if recurso_ok  else "\u26a0\ufe0f Pendiente")
            _cs2.metric("Mismatch",       "\u2705 OK" if _mm_ok_s    else "\u26a0\ufe0f No calculado")
            _cs3.metric("Sombreado",      "\u2705 OK" if _sm_ok_s    else "\u2139\ufe0f Sin obstáculos")
            _cs4.metric("TMY disponible", "\u2705 OK" if _tmy_s is not None else "\u26a0\ufe0f Estimado")

            if not recurso_ok:
                st.info("\u2139\ufe0f El diagrama solar no necesita TMY, pero el heatmap mejora con ☀️ Recurso Solar.")

            _pts_hz = []
            if _hz_df_s is not None:
                for _, _rh in _hz_df_s.dropna().iterrows():
                    try:
                        _az_h = float(_rh.get("Azimuth (°)", 0))
                        _el_h = float(_rh.get("Elevación obstáculo (°)", 0))
                        if _el_h > 0: _pts_hz.append((_az_h, _el_h))
                    except (ValueError, TypeError): pass
            _hay_hz = len(_pts_hz) > 0

            _MESES_SOL = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
            _COLS_SOL  = ["#e6194b","#f58231","#ffe119","#bfef45","#3cb44b","#42d4f4",
                          "#4363d8","#911eb4","#f032e6","#a9a9a9","#9A6324","#800000"]

            with st.spinner("Calculando trayectoria solar..."):
                try:    _sp_m = _solar_path_mensual(lat, lon, alt_m)
                except Exception as _er_s: st.error(f"Error: {_er_s}"); _sp_m = _pd.DataFrame()

            with st.spinner("Calculando posiciones anuales..."):
                try:
                    if _tmy_s is not None:
                        _loc_s = _pv.location.Location(lat, lon, altitude=alt_m, tz="UTC")
                        _sp_a  = _loc_s.get_solarposition(_tmy_s.index)
                    else:
                        _sp_a  = _solar_anual_std(lat, lon, alt_m)
                    _sp_a_ok = True
                except Exception as _er2:
                    st.warning(f"No se pudo calcular posición anual: {_er2}")
                    _sp_a = _pd.DataFrame(); _sp_a_ok = False

            st.divider()
            st.subheader("\U0001f31e 1. Trayectoria solar — Azimuth vs Elevación")

            _fig_sp = go.Figure()
            _fig_sp.add_hrect(y0=0,y1=90,fillcolor="rgba(173,216,230,0.15)",line_width=0,layer="below")

            _az_lin = _np.linspace(0, 360, 721)
            if _hay_hz:
                _el_hz = _interp_horizonte(_pts_hz, _az_lin)
                _fig_sp.add_trace(go.Scatter(
                    x=_np.concatenate([_az_lin,[360,0]]),
                    y=_np.concatenate([_el_hz,[_el_hz[-1],0]]),
                    fill="tozeroy", fillcolor="rgba(120,60,20,0.35)",
                    mode="lines", line=dict(color="saddlebrown",width=2.5),
                    name="\U0001f3d9\ufe0f Horizonte obstáculos",
                ))
            else:
                _fig_sp.add_trace(go.Scatter(
                    x=[0,360],y=[0,0],mode="lines",
                    line=dict(color="saddlebrown",width=1.5,dash="dot"),
                    name="Horizonte libre",opacity=0.6,
                ))

            if not _sp_m.empty:
                for _mn, _grp in _sp_m.groupby("mes"):
                    if not len(_grp): continue
                    _fig_sp.add_trace(go.Scatter(
                        x=_grp["azimuth"],y=_grp["apparent_elevation"],
                        mode="lines",name=_MESES_SOL[_mn-1],
                        line=dict(color=_COLS_SOL[_mn-1],width=2),opacity=0.85,
                        hovertemplate=f"<b>{_MESES_SOL[_mn-1]}</b><br>Az:%{{x:.1f}}° El:%{{y:.1f}}°<extra></extra>",
                    ))

            # Línea vertical para cada superficie activa
            _sups_sl = [s for s in st.session_state.get("superficies_bipv",[]) if s.get("activa",True)]
            for _sl in _sups_sl:
                _fig_sp.add_vline(
                    x=float(_sl["azimuth_deg"]),
                    line_dash="dash",
                    line_color=color_tipo(_sl["tipo"]),
                    line_width=1.5,
                    annotation_text=(
                        f"{TIPOS_SUPERFICIE.get(_sl['tipo'],{}).get('icon','')} "
                        f"{_sl['nombre']} ({_sl['azimuth_deg']:.0f}°)"
                    ),
                    annotation_position="top right",
                    annotation_font=dict(color=color_tipo(_sl["tipo"]),size=10),
                )

            _esp_sol = {
                6:  ("Solsticio Jun",  "#FFD700"),
                12: ("Solsticio Dic",  "#87CEEB"),
                3:  ("Equinoccio Mar", "#90EE90"),
                9:  ("Equinoccio Sep", "#FFA07A"),
            }
            if not _sp_m.empty:
                for _me,(lbl,col) in _esp_sol.items():
                    _ge = _sp_m[_sp_m["mes"]==_me]
                    if not len(_ge): continue
                    _fm = _ge.loc[_ge["apparent_elevation"].idxmax()]
                    _fig_sp.add_trace(go.Scatter(
                        x=[_fm["azimuth"]],y=[_fm["apparent_elevation"]],
                        mode="markers+text",
                        marker=dict(size=10,color=col,symbol="star",line=dict(color="white",width=1)),
                        text=[lbl],textposition="top right",textfont=dict(size=9,color=col),
                        showlegend=False,
                        hovertemplate=f"<b>{lbl}</b><br>Az:%{{x:.1f}}° El:%{{y:.1f}}°<extra></extra>",
                    ))

            _fig_sp.update_layout(
                height=460,
                xaxis=dict(
                    title="Azimuth solar (°) — 0=Norte · 90=Este · 180=Sur · 270=Oeste",
                    tickvals=[0,45,90,135,180,225,270,315,360],
                    ticktext=["N(0°)","NE","E(90°)","SE","S(180°)","SO","O(270°)","NO","N(360°)"],
                    range=[0,360],
                ),
                yaxis=dict(title="Elevación solar (°)",range=[0,90]),
                legend=dict(orientation="h",y=-0.30,x=0,font_size=10,bgcolor="rgba(255,255,255,0.7)"),
                plot_bgcolor="white",paper_bgcolor="white",margin=dict(b=130),
                title=dict(
                    text=(f"<b>Trayectoria solar — {ciudad}</b>  "
                          f"<sup>{lat:.2f}°N, {abs(lon):.2f}°W · {alt_m} m</sup>"),
                    x=0.5,xanchor="center",
                ),
            )
            st.plotly_chart(_fig_sp, use_container_width=True)
            if _hay_hz:
                st.caption(f"\U0001f4cc Horizonte: {len(_pts_hz)} puntos cargados desde \U0001f500 Mismatch.")

            # Heatmap horas productivas
            st.divider()
            st.subheader("\u23f0 2. Horas productivas vs sombreadas (24 h × 12 meses)")

            _sups_hm = [s for s in st.session_state.get("superficies_bipv",[]) if s.get("activa",True)]
            if len(_sups_hm) > 1:
                _nom_hm = st.selectbox(
                    "Superficie para heatmap",
                    [s["nombre"] for s in _sups_hm], key="hm_sup_sel",
                )
                _sup_hm = next((s for s in _sups_hm if s["nombre"]==_nom_hm), _sups_hm[0])
            else:
                _sup_hm = _sups_hm[0] if _sups_hm else {"azimuth_deg":azimuth,"tilt_deg":tilt,"nombre":"Fachada","tipo":"Fachada"}

            _tilt_hm = float(_sup_hm.get("tilt_deg", tilt))
            _az_hm   = float(_sup_hm.get("azimuth_deg", azimuth))

            if _sp_a_ok and not _sp_a.empty:
                import pvlib as _pv_hm
                _spw = _sp_a.copy()
                _spw["hora"] = _spw.index.hour; _spw["mes"] = _spw.index.month
                _spw["aoi"]  = _pv_hm.irradiance.aoi(
                    surface_tilt=_tilt_hm, surface_azimuth=_az_hm,
                    solar_zenith=_spw["apparent_zenith"], solar_azimuth=_spw["azimuth"],
                )
                _spw["el_hz"] = _interp_horizonte(_pts_hz, _spw["azimuth"].values)
                _es_dia  = _spw["apparent_elevation"] > 0.5
                _sombr   = _es_dia & (_spw["apparent_elevation"] <= _spw["el_hz"])
                _detras  = _es_dia & (~_sombr) & (_spw["aoi"] >= 90.0)
                _prod_hm = _es_dia & (~_sombr) & (~_detras)

                _poa_hm_df = (
                    st.session_state.get("poa_superficies", {}).get(_sup_hm.get("nombre", ""))
                    or _poa_s
                )
                if _poa_hm_df is not None and len(_poa_hm_df) == len(_spw):
                    _spw["poa_eff"] = _poa_hm_df["poa_global"].values * _prod_hm.astype(float)
                else:
                    _spw["poa_eff"] = _prod_hm.astype(float) * 300.0

                _hm_p = (
                    _spw.groupby(["hora","mes"])["poa_eff"].mean()
                    .unstack().reindex(index=range(24), columns=range(1,13), fill_value=0.0)
                )
                _fig_hm = go.Figure(go.Heatmap(
                    z=_hm_p.values, x=_MESES_SOL,
                    y=[f"{h:02d}:00" for h in range(24)],
                    colorscale="YlOrRd",
                    colorbar=dict(title="POA (W/m²)<br>horas prod.", thickness=14, len=0.8),
                    zmin=0,
                    hovertemplate="<b>%{y} — %{x}</b><br>POA: <b>%{z:.0f} W/m²</b><extra></extra>",
                ))
                _fig_hm.update_layout(
                    height=440, xaxis_title="Mes", yaxis_title="Hora del día (UTC)",
                    plot_bgcolor="white", paper_bgcolor="white",
                    title=dict(
                        text=(
                            f"<b>Horas productivas — "
                            f"{TIPOS_SUPERFICIE.get(_sup_hm.get('tipo','Fachada'),{}).get('icon','')} "
                            f"{_sup_hm.get('nombre','—')} / {_tilt_hm:.0f}°</b>"
                        ),
                        x=0.5, xanchor="center",
                    ),
                )
                st.plotly_chart(_fig_hm, use_container_width=True)

                st.divider()
                st.subheader("\U0001f4ca 3. Métricas de sombras")
                _n_d  = int(_es_dia.sum()); _n_pr = int(_prod_hm.sum())
                _n_so = int(_sombr.sum());  _n_de = int(_detras.sum())
                _p_pr = (_n_pr / _n_d * 100) if _n_d > 0 else 0.0
                _p_so = (_n_so / _n_d * 100) if _n_d > 0 else 0.0

                _sm1,_sm2,_sm3,_sm4 = st.columns(4)
                _sm1.metric("Horas productivas", f"{_n_pr:,} h/año", f"{_p_pr:.1f}%")
                _sm2.metric("Horas sombreadas",  f"{_n_so:,} h/año", f"-{_p_so:.1f}%", delta_color="inverse")
                _sm3.metric("Sin vista fachada",  f"{_n_de:,} h/año")
                _sm4.metric("Nocturnas",          f"{8760-_n_d:,} h/año")

                st.markdown("---")
                if _fs_anual_s is not None:
                    _p_mm = _fs_anual_s * 100; _dp = _p_so - _p_mm
                    _sc1,_sc2,_sc3 = st.columns(3)
                    _sc1.metric("% horas sombreadas (sun path)", f"{_p_so:.1f}%")
                    _sc2.metric("% pérdida energética (Mismatch)", f"{_p_mm:.1f}%")
                    _sc3.metric("Diferencia", f"{abs(_dp):.1f} pp", delta_color="off")
                    if   abs(_dp) < 3:   st.success(f"\u2705 Diferencia {abs(_dp):.1f} pp — consistencia alta.")
                    elif abs(_dp) < 6:   st.warning(f"\u26a0\ufe0f Diferencia {abs(_dp):.1f} pp — revisar horizonte o TMY.")
                    else:                st.error(  f"\u274c Diferencia {abs(_dp):.1f} pp — revisar configuración.")
                else:
                    st.info("\u2139\ufe0f Ejecuta la cascada de pérdidas en \U0001f500 Mismatch para comparar.")

                with st.expander("\u2139\ufe0f ¿Por qué difieren sun path y Mismatch?"):
                    st.markdown(
                        "| Criterio | Sun path | Mismatch |\n"
                        "|---|---|---|\n"
                        "| **Qué mide** | Fracción de **horas** con sombra | Fracción de **energía POA** perdida |\n"
                        "| **Datos** | Posición astronómica + horizonte | TMY 8760 h + horizonte |\n"
                        "| **Ponderación** | Cada hora vale igual | Ponderada por POA |\n"
                        "| **Diferencia típica** | < 2 pp | n/a |"
                    )
            else:
                st.info("\u26a0\ufe0f No se pudo calcular posición solar anual. Verifica pvlib.")

            st.divider()
            st.caption(
                f"\U0001f4cc pvlib {_pv.__version__} — algoritmo Enoch/Spencer.  "
                "Horizonte: " + ("configurado en \U0001f500 Mismatch" if _hay_hz else "no configurado") + ".  "
                "POA: " + ("TMY PVGIS real" if _tmy_s is not None else "estimado (ejecuta ☀️ Recurso Solar)") + "."
            )
