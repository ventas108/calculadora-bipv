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

c      = CIUDADES[ciudad]
lat    = c["lat"]
lon    = c["lon"]
alt_m  = c["alt_m"]

# ── Panel de estado ───────────────────────────────────────────────────────────
recurso_ok   = st.session_state.get("recurso_solar_ok", False)
azimuth      = float(st.session_state.get("azimuth_fachada", 180))
tilt         = float(st.session_state.get("tilt_fachada", 90))
area_m2      = float(st.session_state.get("area_fachada_m2", 50.0))
nombre_proy  = st.session_state.get("nombre_proyecto", "Proyecto BIPV")
orient_label = st.session_state.get("orientacion_label", f"Azimuth {azimuth:.0f}°")

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
col_s1.metric("Ciudad",       ciudad)
col_s2.metric("Coordenadas",  f"{lat}°N, {lon}°W")
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
            st.pydeck_chart(deck, use_container_width=True, height=500)

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
# TAB 3 — DIAGRAMA SOLAR Y SOMBRAS (B-5C)
# ─────────────────────────────────────────────────────────────────────────────
with tab_solar:

    # Dependencias internas
    try:
        import pvlib as _pv
        import pandas as _pd
        import numpy as _np
        _b5c_ok = True
    except ImportError as _e:
        st.error(f"❌ Dependencia faltante para el diagrama solar: {_e}")
        _b5c_ok = False

    if _b5c_ok:

        st.subheader("🌞 Diagrama de trayectoria solar y análisis de sombras")
        st.caption(
            "Trayectoria del sol por mes · Perfil de horizonte de Mismatch · "
            "Mapa de horas productivas vs sombreadas — Fase 3 · B-5C"
        )

        # ── Leer session_state (solo lectura) ────────────────────────────────
        tmy_df_b5c     = st.session_state.get("tmy_df")
        poa_df_b5c     = st.session_state.get("poa_df")
        mismatch_ok_b5c= bool(st.session_state.get("mismatch_ok", False))
        sombra_ok_b5c  = bool(st.session_state.get("sombra_ok", False))
        factor_sombra  = st.session_state.get("factor_sombra_anual", None)
        res_sombra_b5c = st.session_state.get("res_sombra", {})
        horizonte_df_b5c = st.session_state.get("horizonte_df")

        # Estado de dependencias
        cs1, cs2, cs3, cs4 = st.columns(4)
        cs1.metric("Recurso Solar",  "✅ OK" if recurso_ok else "⚠️ Pendiente")
        cs2.metric("Mismatch",       "✅ OK" if mismatch_ok_b5c else "⚠️ No calculado")
        cs3.metric("Sombreado",      "✅ OK" if sombra_ok_b5c else "ℹ️ Sin obstáculos")
        cs4.metric("TMY disponible", "✅ OK" if tmy_df_b5c is not None else "⚠️ Estimado")

        if not recurso_ok:
            st.info(
                "ℹ️ El diagrama solar se calcula con posiciones astronómicas (pvlib). "
                "**No necesita el TMY** para mostrarse, pero el heatmap de sombras mejora "
                "con los datos POA reales de ☀️ Recurso Solar."
            )

        # ── Extraer perfil de horizonte ───────────────────────────────────────
        puntos_hz = []
        if horizonte_df_b5c is not None:
            for _, row in horizonte_df_b5c.dropna().iterrows():
                try:
                    az_h = float(row.get("Azimuth (°)", 0))
                    el_h = float(row.get("Elevación obstáculo (°)", 0))
                    if el_h > 0:
                        puntos_hz.append((az_h, el_h))
                except (ValueError, TypeError):
                    pass

        hay_horizonte = len(puntos_hz) > 0

        # ── Paleta de colores por mes ─────────────────────────────────────────
        MESES_B5C   = ["Ene","Feb","Mar","Abr","May","Jun",
                       "Jul","Ago","Sep","Oct","Nov","Dic"]
        COLORS_MESES = [
            "#e6194b","#f58231","#ffe119","#bfef45","#3cb44b","#42d4f4",
            "#4363d8","#911eb4","#f032e6","#a9a9a9","#9A6324","#800000",
        ]

        # ── Calcular trayectoria solar mensual (cacheado) ─────────────────────
        with st.spinner("Calculando trayectoria solar..."):
            try:
                sp_meses = _solar_path_mensual(lat, lon, alt_m)
            except Exception as _er:
                st.error(f"Error calculando posición solar: {_er}")
                sp_meses = _pd.DataFrame()

        # ── Calcular posiciones anuales (8760 h) ──────────────────────────────
        with st.spinner("Calculando posiciones solares anuales..."):
            try:
                if tmy_df_b5c is not None:
                    loc_b5c = _pv.location.Location(lat, lon, altitude=alt_m, tz="UTC")
                    sp_anual = loc_b5c.get_solarposition(tmy_df_b5c.index)
                else:
                    sp_anual = _solar_anual_std(lat, lon, alt_m)
                _sp_ok = True
            except Exception as _er2:
                st.warning(f"No se pudo calcular posición solar anual: {_er2}")
                sp_anual = _pd.DataFrame()
                _sp_ok = False

        st.divider()

        # ══════════════════════════════════════════════════════════════════════
        # SECCIÓN 1: DIAGRAMA DE TRAYECTORIA SOLAR
        # ══════════════════════════════════════════════════════════════════════
        st.subheader("🌞 1. Trayectoria solar — Azimuth vs Elevación")

        fig_sp = go.Figure()

        # Zona azul de cielo (fondo)
        fig_sp.add_hrect(y0=0, y1=90,
                         fillcolor="rgba(173,216,230,0.15)",
                         line_width=0, layer="below")

        # Perfil de horizonte (zona sombreada, si hay obstáculos)
        az_lin = _np.linspace(0, 360, 721)
        if hay_horizonte:
            el_hz_lin = _interp_horizonte(puntos_hz, az_lin)
            fig_sp.add_trace(go.Scatter(
                x=_np.concatenate([az_lin, [360, 0]]),
                y=_np.concatenate([el_hz_lin, [el_hz_lin[-1], 0]]),
                fill="tozeroy",
                fillcolor="rgba(120,60,20,0.35)",
                mode="lines",
                line=dict(color="saddlebrown", width=2.5),
                name="🏙️ Horizonte obstáculos",
                showlegend=True,
            ))
        else:
            fig_sp.add_trace(go.Scatter(
                x=[0, 360], y=[0, 0],
                mode="lines",
                line=dict(color="saddlebrown", width=1.5, dash="dot"),
                name="Horizonte libre (sin obstáculos)",
                showlegend=True,
                opacity=0.6,
            ))

        # Trayectorias solares por mes
        if not sp_meses.empty:
            for mes_num, grp in sp_meses.groupby("mes"):
                if len(grp) == 0:
                    continue
                fig_sp.add_trace(go.Scatter(
                    x=grp["azimuth"],
                    y=grp["apparent_elevation"],
                    mode="lines",
                    name=MESES_B5C[mes_num - 1],
                    line=dict(color=COLORS_MESES[mes_num - 1], width=2),
                    opacity=0.85,
                    showlegend=True,
                    hovertemplate=(
                        f"<b>{MESES_B5C[mes_num-1]}</b><br>"
                        "Az: %{x:.1f}°<br>El: %{y:.1f}°<extra></extra>"
                    ),
                ))

        # Línea vertical: azimuth de la fachada
        fig_sp.add_vline(
            x=azimuth,
            line_dash="dash", line_color="orange", line_width=2,
            annotation_text=f"◀ Fachada: {azimuth:.0f}°",
            annotation_position="top right",
            annotation_font=dict(color="orange", size=12),
        )

        # Marcadores especiales: solsticios + equinoccios (horas al mediodía)
        especiales = {
            6:  ("Solsticio Jun", "#FFD700"),    # sol más alto aprox
            12: ("Solsticio Dic", "#87CEEB"),    # sol más bajo aprox
            3:  ("Equinoccio Mar", "#90EE90"),
            9:  ("Equinoccio Sep", "#FFA07A"),
        }
        if not sp_meses.empty:
            for mes_e, (lbl, col) in especiales.items():
                grp_e = sp_meses[sp_meses["mes"] == mes_e]
                if len(grp_e) == 0:
                    continue
                # Punto al mediodía local aprox (elevación máxima)
                fila_max = grp_e.loc[grp_e["apparent_elevation"].idxmax()]
                fig_sp.add_trace(go.Scatter(
                    x=[fila_max["azimuth"]],
                    y=[fila_max["apparent_elevation"]],
                    mode="markers+text",
                    marker=dict(size=10, color=col, symbol="star",
                                line=dict(color="white", width=1)),
                    text=[lbl],
                    textposition="top right",
                    textfont=dict(size=9, color=col),
                    showlegend=False,
                    hovertemplate=(
                        f"<b>{lbl}</b><br>Az: %{{x:.1f}}°<br>El: %{{y:.1f}}°"
                        "<extra></extra>"
                    ),
                ))

        fig_sp.update_layout(
            height=440,
            xaxis=dict(
                title="Azimuth solar (°) — 0=Norte, 90=Este, 180=Sur, 270=Oeste",
                tickvals=[0, 45, 90, 135, 180, 225, 270, 315, 360],
                ticktext=["N (0°)", "NE", "E (90°)", "SE",
                          "S (180°)", "SO", "O (270°)", "NO", "N (360°)"],
                range=[0, 360],
            ),
            yaxis=dict(title="Elevación solar (°)", range=[0, 90]),
            legend=dict(
                orientation="h", y=-0.30, x=0, font_size=10,
                bgcolor="rgba(255,255,255,0.7)",
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(b=120),
            title=dict(
                text=(f"<b>Trayectoria solar — {ciudad}</b>  "
                      f"<sup>{lat:.2f}°N, {abs(lon):.2f}°W · {alt_m} m</sup>"),
                x=0.5, xanchor="center",
            ),
        )
        st.plotly_chart(fig_sp, use_container_width=True)

        if hay_horizonte:
            n_obs = len(puntos_hz)
            max_el = max(p[1] for p in puntos_hz)
            st.caption(
                f"🏙️ Horizonte: **{n_obs} puntos** · Elevación máxima: **{max_el:.0f}°** · "
                "Zona marrón = porciones del cielo bloqueadas por obstáculos. "
                "Modifica los obstáculos en 🔀 Mismatch."
            )
        else:
            st.caption(
                "ℹ️ No hay obstáculos en el horizonte. "
                "Configura el perfil en 🔀 Mismatch → Sección 1."
            )

        # ══════════════════════════════════════════════════════════════════════
        # SECCIÓN 2: HEATMAP HORAS PRODUCTIVAS
        # ══════════════════════════════════════════════════════════════════════
        st.divider()
        st.subheader("⏰ 2. Horas productivas vs sombreadas (24h × 12 meses)")
        st.caption(
            "Verde/naranja = horas con sol directo sobre la fachada (AOI < 90° y sobre el horizonte). "
            "El valor es la irradiancia POA media (W/m²). "
            "Gris = noche o sol detrás de la fachada."
        )

        if _sp_ok and not sp_anual.empty:

            # Agregar hora y mes al DataFrame de posiciones solares
            sp_w = sp_anual.copy()
            sp_w["hora"] = sp_w.index.hour
            sp_w["mes"]  = sp_w.index.month

            # Calcular AOI (Ángulo de Incidencia) sobre la fachada
            try:
                sp_w["aoi"] = _pv.irradiance.aoi(
                    tilt, azimuth,
                    sp_w["apparent_zenith"],
                    sp_w["azimuth"]
                )
            except Exception:
                sp_w["aoi"] = 90.0  # fallback

            # Interpolar elevación del horizonte para cada azimuth solar
            sp_w["el_horiz"] = _interp_horizonte(
                puntos_hz, sp_w["azimuth"].values
            )

            # Clasificación vectorizada
            _es_dia    = sp_w["apparent_elevation"] > 0.5
            _sombreado = _es_dia & (sp_w["apparent_elevation"] <= sp_w["el_horiz"])
            _detras    = _es_dia & (~_sombreado) & (sp_w["aoi"] >= 90.0)
            _productivo = _es_dia & (~_sombreado) & (~_detras)

            # Valor para el heatmap: POA si productivo, 0 si no
            if poa_df_b5c is not None and len(poa_df_b5c) == len(sp_w):
                sp_w["poa_eff"] = poa_df_b5c["poa_global"].values * _productivo.astype(float)
            else:
                # Fallback: valor binario ×300 para tener escala visualizable
                sp_w["poa_eff"] = _productivo.astype(float) * 300.0

            # Agregar a heatmap 24 × 12
            hm_prod = (
                sp_w.groupby(["hora", "mes"])["poa_eff"]
                .mean()
                .unstack()
                .reindex(index=range(24), columns=range(1, 13), fill_value=0.0)
            )

            fig_hm = go.Figure(go.Heatmap(
                z=hm_prod.values,
                x=MESES_B5C,
                y=[f"{h:02d}:00" for h in range(24)],
                colorscale="YlOrRd",
                colorbar=dict(
                    title="POA (W/m²)<br>horas prod.",
                    thickness=14, len=0.8,
                ),
                zmin=0,
                hovertemplate=(
                    "<b>%{y} — %{x}</b><br>"
                    "POA media: <b>%{z:.0f} W/m²</b><br>"
                    "(0 = noche, sombra o sol detrás de fachada)"
                    "<extra></extra>"
                ),
            ))
            fig_hm.update_layout(
                height=440,
                xaxis_title="Mes",
                yaxis_title="Hora del día (UTC)",
                plot_bgcolor="white",
                paper_bgcolor="white",
                title=dict(
                    text=(f"<b>Horas productivas — fachada {orient_label} / {tilt:.0f}°</b>"),
                    x=0.5, xanchor="center",
                ),
            )
            st.plotly_chart(fig_hm, use_container_width=True)

            # ── Métricas ─────────────────────────────────────────────────────
            st.divider()
            st.subheader("📊 3. Métricas de sombras")

            n_total_dia = int(_es_dia.sum())
            n_prod      = int(_productivo.sum())
            n_sombra    = int(_sombreado.sum())
            n_detras_f  = int(_detras.sum())
            pct_prod    = (n_prod / n_total_dia * 100) if n_total_dia > 0 else 0.0
            pct_sombra  = (n_sombra / n_total_dia * 100) if n_total_dia > 0 else 0.0

            cm1, cm2, cm3, cm4 = st.columns(4)
            cm1.metric(
                "Horas productivas estimadas",
                f"{n_prod:,} h/año",
                f"{pct_prod:.1f}% de horas con sol",
                help="Horas con sol directo en la fachada (AOI < 90° y sobre horizonte).",
            )
            cm2.metric(
                "Horas sombreadas",
                f"{n_sombra:,} h/año",
                f"-{pct_sombra:.1f}%",
                delta_color="inverse",
                help="Horas donde la elevación solar queda por debajo del horizonte configurado.",
            )
            cm3.metric(
                "Horas sin vista de fachada",
                f"{n_detras_f:,} h/año",
                help="El sol está sobre el horizonte pero mira desde atrás de la fachada (AOI ≥ 90°).",
            )
            cm4.metric(
                "Horas nocturnas",
                f"{8760 - n_total_dia:,} h/año",
            )

            # Comparar con factor_sombra_anual de Mismatch
            st.markdown("---")
            if factor_sombra is not None:
                pct_perdida_mismatch = factor_sombra * 100
                delta_pct = pct_sombra - pct_perdida_mismatch

                col_comp1, col_comp2, col_comp3 = st.columns(3)
                col_comp1.metric(
                    "% horas sombreadas (sun path)",
                    f"{pct_sombra:.1f}%",
                    help="Porcentaje de horas diurnas con sombra de horizonte — calculado desde posición astronómica.",
                )
                col_comp2.metric(
                    "Factor de sombra energético (Mismatch)",
                    f"{pct_perdida_mismatch:.1f}%",
                    help="Pérdida energética ponderada por irradiancia — calculada en 🔀 Mismatch.",
                )
                col_comp3.metric(
                    "Diferencia de métodos",
                    f"{abs(delta_pct):.1f} pp",
                    delta=f"{'normal' if abs(delta_pct) < 3 else 'revisar'}",
                    delta_color="normal" if abs(delta_pct) < 3 else "inverse",
                    help="<2 pp es normal (tiempo vs energía). >3 pp sugiere revisar el horizonte.",
                )

                if abs(delta_pct) < 3:
                    st.success(
                        f"✅ Consistencia entre métodos: la diferencia es **{abs(delta_pct):.1f} pp** "
                        f"(< 3 pp es normal porque uno mide tiempo y el otro energía)."
                    )
                elif abs(delta_pct) < 6:
                    st.warning(
                        f"⚠️ Diferencia de **{abs(delta_pct):.1f} pp** entre sun path y Mismatch. "
                        "Puede deberse a diferencias en el perfil de horizonte o el TMY. "
                        "Verifica que el horizonte esté actualizado en 🔀 Mismatch."
                    )
                else:
                    st.error(
                        f"❌ Diferencia de **{abs(delta_pct):.1f} pp** — revisar configuración de horizonte. "
                        "El sun path usa posición astronómica pura; Mismatch usa el TMY completo."
                    )
            else:
                st.info(
                    "ℹ️ Ejecuta la **cascada de pérdidas** en 🔀 Mismatch para comparar el factor de "
                    "sombra energético con las horas productivas calculadas aquí."
                )

            # Nota aclaratoria sobre los dos métodos
            with st.expander("ℹ️ ¿Por qué pueden diferir el sun path y el factor de Mismatch?"):
                st.markdown("""
                | Criterio | Sun path (este diagrama) | Mismatch |
                |----------|--------------------------|----------|
                | **Qué mide** | Fracción de **horas diurnas** con sombra | Fracción de **energía POA** perdida |
                | **Datos base** | Posición astronómica + horizonte | TMY completo (8760 h) + horizonte |
                | **Ponderación** | Cada hora vale igual | Cada hora ponderada por su POA |
                | **Diferencia típica** | < 2 puntos porcentuales | — |

                > En Colombia, las horas de mayor POA suelen coincidir con las de menor sombreado
                > (sol alto), por lo que el factor energético de Mismatch suele ser **menor**
                > que el porcentaje temporal calculado aquí.
                """)

        else:
            st.info(
                "⚠️ No se pudo calcular la posición solar anual. "
                "Verifica que pvlib esté instalado y que el servidor tenga acceso a la red."
            )

        # ── Fuentes de datos ──────────────────────────────────────────────────
        st.divider()
        st.caption(
            "📌 **Fuentes:** "
            f"Posición solar: pvlib {_pv.__version__} — algoritmo Enoch/Spencer. "
            "Horizonte: " + ("configurado en 🔀 Mismatch" if hay_horizonte else
                             "no configurado — se asume horizonte libre") + ". "
            "POA: " + ("TMY PVGIS real" if poa_df_b5c is not None else
                       "estimado (ejecuta ☀️ Recurso Solar para datos reales)") + "."
        )
