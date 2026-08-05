"""Página 2 — Recurso Solar: TMY desde PVGIS + POA para sistemas solares."""
import os
import pickle
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# ── Caché de disco para TMY+POA — sobrevive reinicios de PM2 ─────────────────
_SOLAR_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "datos", "solar_cache")

def _cache_path(lat, lon, tilt, azimuth, alt_m, albedo=0.20):
    os.makedirs(_SOLAR_CACHE_DIR, exist_ok=True)
    # El sufijo de albedo solo aparece si difiere del default histórico (0.20),
    # para no invalidar los cachés existentes en el servidor.
    _alb = "" if abs(float(albedo) - 0.20) < 1e-9 else f"_alb{float(albedo):.2f}"
    return os.path.join(
        _SOLAR_CACHE_DIR,
        f"solar_{lat:.4f}_{lon:.4f}_t{tilt}_a{int(azimuth)}_h{alt_m}{_alb}.pkl",
    )

def _leer_cache(lat, lon, tilt, azimuth, alt_m, albedo=0.20):
    try:
        p = _cache_path(lat, lon, tilt, azimuth, alt_m, albedo)
        if os.path.exists(p):
            with open(p, "rb") as f:
                return pickle.load(f)
    except Exception:
        pass
    return None

def _guardar_cache(lat, lon, tilt, azimuth, alt_m, tmy, poa, albedo=0.20):
    try:
        with open(_cache_path(lat, lon, tilt, azimuth, alt_m, albedo), "wb") as f:
            pickle.dump({"tmy": tmy, "poa": poa}, f, protocol=4)
    except Exception:
        pass

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
from utils.ui import bloquear_traduccion
bloquear_traduccion()
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
    # Prioridad: municipio geocodificado > nombre del proyecto > coordenadas
    _nombre_proy    = st.session_state.get("nombre_proyecto", "").strip()
    _municipio_rs   = st.session_state.get("municipio_predio", "").strip()
    _default_nombre = "Proyecto BIPV"
    if _municipio_rs:
        _label_sitio = _municipio_rs
    elif _nombre_proy and _nombre_proy != _default_nombre:
        _label_sitio = _nombre_proy
    else:
        _label_sitio = f"{lat:.4f}°N, {abs(lon):.4f}°O"
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
        min_value=0.05, max_value=0.50,
        value=float(st.session_state.get("albedo_suelo", 0.20)), step=0.05,
        help="0.20 = suelo urbano típico. 0.30 = concreto. 0.05 = asfalto. "
             "Afecta la componente reflejada del POA frontal y, si activas el "
             "modelo bifacial, la luz que capta la cara trasera.",
    )

# ── Simulación bifacial (pvlib infinite_sheds) ────────────────────────────────
_panel_bif   = st.session_state.get("panel_dict") or {}
_bif_catalogo = float(_panel_bif.get("bifacialidad_pct") or 0)
_texto_panel  = (str(_panel_bif.get("tecnologia", "")) + " " +
                 str(_panel_bif.get("notas", ""))).lower()
_panel_es_bif = _bif_catalogo > 0 or "bifacial" in _texto_panel

with st.expander("🔄 Simulación bifacial (ganancia de la cara trasera)",
                 expanded=_panel_es_bif or st.session_state.get("bifacial_activo", False)):
    if _panel_es_bif:
        st.info(
            f"🔎 El panel del proyecto (`{_panel_bif.get('nombre', '—')}`) es **bifacial**"
            + (f" con bifacialidad {_bif_catalogo:.0f}% según el catálogo."
               if _bif_catalogo > 0 else
               " según su ficha, pero el catálogo no trae el % de bifacialidad — usa 70% como valor típico o consulta el datasheet."),
            icon="🔄",
        )
    elif _panel_bif:
        st.caption(f"El panel del proyecto (`{_panel_bif.get('nombre', '—')}`) no registra "
                   "bifacialidad en el catálogo. Puedes activar el modelo igualmente si sabes que es bifacial.")

    bifacial_on = st.checkbox(
        "Activar modelo bifacial — pvlib `infinite_sheds` (estándar de la industria)",
        value=bool(st.session_state.get("bifacial_activo", _panel_es_bif)),
        help="Suma a la POA la irradiancia que capta la cara trasera "
             "(reflejo del suelo + difusa), ponderada por la bifacialidad del panel. "
             "poa_global = POA frontal + bifacialidad × POA trasera.",
    )

    bifacial_cfg = None
    if bifacial_on:
        cb1, cb2, cb3, cb4 = st.columns(4)
        _bif_def = st.session_state.get("bifacial_cfg", {})
        bif_pct = cb1.number_input(
            "Bifacialidad (%)", min_value=5.0, max_value=100.0,
            value=float(_bif_def.get("bifacialidad", (_bif_catalogo or 70.0) / 100) * 100),
            step=5.0,
            help="Relación entre la respuesta de la cara trasera y la frontal. "
                 "TOPCon/HJT: 75–90%. PERC: 65–75%. Viene de la ficha del panel.",
        )
        altura_m = cb2.number_input(
            "Altura sobre el suelo (m)", min_value=0.1, max_value=30.0,
            value=float(_bif_def.get("altura_m", 1.0)), step=0.1,
            help="Altura del centro del panel sobre el suelo. Más altura = la cara "
                 "trasera 've' más suelo reflejante = más ganancia.",
        )
        # ── #154 — Fachadas verticales: la trasera puede estar sellada al muro ─
        # Con tilt >= 80 se ofrece un selector de montaje. "Adosada al muro"
        # anula prácticamente la trasera (factor_vista_trasera=0, albedo 0.05 y
        # slider deshabilitado) para evitar ganancias bifaciales irreales;
        # "ventilada" mantiene el comportamiento normal.
        _es_fachada = tilt >= 80
        factor_vista_trasera = 1.0
        _albedo_rear_forzado = None
        if _es_fachada:
            _montaje = st.radio(
                "🏢 Montaje de la fachada vertical (tilt ≥ 80°)",
                ["Adosada al muro (sellada)",
                 "Separación ventilada con superficie reflejante"],
                index=0,
                horizontal=True,
                help="Adosada: la cara trasera queda contra el muro y no capta luz "
                     "reflejada — la ganancia bifacial real es nula. Ventilada: hay "
                     "cámara de aire con una superficie reflejante detrás del panel.",
            )
            if _montaje.startswith("Adosada"):
                factor_vista_trasera = 0.0
                _albedo_rear_forzado = 0.05

        _rear_disabled = _albedo_rear_forzado is not None
        albedo_rear = cb3.slider(
            "Albedo trasero", min_value=0.05, max_value=0.80,
            value=(_albedo_rear_forzado if _rear_disabled
                   else float(_bif_def.get("albedo_trasero", albedo))),
            step=0.05,
            disabled=_rear_disabled,
            help="Reflectividad de la superficie DETRÁS del array. Grava blanca: 0.5. "
                 "Concreto: 0.30. Pasto: 0.20. Membrana blanca de techo: 0.6–0.8.",
        )
        if _rear_disabled:
            cb3.caption("🔒 Fijado en 0.05 y sin efecto: con la fachada adosada al muro "
                        "la cara trasera está sellada y no aporta ganancia bifacial.")
        # ── #168 — GCR sincronizado con el factor de ocupación del Proyecto ──
        # El GCR (ancho colector ÷ pitch) y el factor de ocupación representan
        # la misma fracción de suelo cubierta por paneles. Si el usuario definió
        # un factor en 🏠 Proyecto, ese valor inicializa el slider.
        _f_ocup_rs = float(st.session_state.get("factor_ocupacion_pct", 0.0) or 0.0)
        if _bif_def.get("gcr") is not None:
            _gcr_ini = float(_bif_def["gcr"])
        elif _f_ocup_rs > 0:
            _gcr_ini = round((_f_ocup_rs / 100.0) / 0.05) * 0.05
        else:
            _gcr_ini = 0.25
        _gcr_ini = min(max(_gcr_ini, 0.10), 0.90)
        gcr = cb4.slider(
            "GCR (cobertura del suelo)", min_value=0.10, max_value=0.90,
            value=_gcr_ini, step=0.05,
            help="Ancho del panel ÷ separación entre filas. Fila única o aislada: 0.20–0.30. "
                 "Filas juntas (menos luz trasera): 0.5+. "
                 "🌱 Agrivoltaica: usa el mismo valor que el factor de ocupación de 🏠 Proyecto.",
        )
        if _f_ocup_rs > 0 and abs(gcr * 100.0 - _f_ocup_rs) > 15.0:
            st.warning(
                f"⚠️ **GCR y factor de ocupación inconsistentes:** el GCR es "
                f"**{gcr:.2f}** ({gcr*100:.0f}% del suelo cubierto) pero en 🏠 Proyecto "
                f"definiste un factor de ocupación de **{_f_ocup_rs:.0f}%**. Ambos "
                f"representan la fracción de terreno con paneles — el sombreado entre "
                f"filas y el conteo de paneles usarán supuestos distintos. "
                f"Sugerido: GCR ≈ **{min(max(_f_ocup_rs/100.0, 0.10), 0.90):.2f}**.",
                icon="🌱",
            )
        bifacial_cfg = {
            "bifacialidad":          bif_pct / 100.0,
            "altura_m":              altura_m,
            "albedo_trasero":        albedo_rear,
            "gcr":                   gcr,
            "factor_vista_trasera":  factor_vista_trasera,
        }
        if _es_fachada:
            st.warning(
                "⚠️ **Fachada vertical:** la cara trasera queda contra el muro y casi no "
                "recibe luz. Con montaje **adosado** la ganancia bifacial se anula "
                "automáticamente (albedo trasero 0.05, sin aporte trasero). Elige "
                "**separación ventilada** solo si existe una cámara de aire con superficie "
                "reflejante detrás del panel.",
                icon="🏢",
            )

st.markdown("---")

# ── #64 — Invalidar recurso solar si las coordenadas cambiaron ───────────────
# Compara las coords actuales del proyecto con las que se usaron para calcular
# el recurso solar almacenado. Si difieren, limpia los resultados y avisa.
_SOLAR_SS_KEYS = (
    "recurso_solar_ok", "tmy_df", "poa_df", "tmy_ciudad",
    "tilt_fachada", "tilt_default", "azimuth_fachada", "orientacion_label",
    "poa_anual_kWh_m2", "ghi_anual_kWh_m2", "t_media_anual",
    "zona_geo_coords", "poa_efectiva_df", "ganancia_bifacial_pct",
)
_s_lat = st.session_state.get("_solar_lat_guardada")
_s_lon = st.session_state.get("_solar_lon_guardada")
_s_alt = st.session_state.get("_solar_alt_guardada")
if st.session_state.get("recurso_solar_ok") and _s_lat is not None:
    _drift = (
        abs(lat - float(_s_lat)) > 0.0001 or
        abs(lon - float(_s_lon)) > 0.0001 or
        abs(alt_m - int(_s_alt))  > 10
    )
    if _drift:
        for _k in _SOLAR_SS_KEYS:
            st.session_state.pop(_k, None)
        for _k in ("_solar_lat_guardada", "_solar_lon_guardada", "_solar_alt_guardada"):
            st.session_state.pop(_k, None)
        st.warning(
            f"⚠️ **Recurso solar invalidado** — las coordenadas del proyecto cambiaron.  \n"
            f"Recurso calculado para: **{float(_s_lat):.5f}°**, **{float(_s_lon):.5f}°**, "
            f"**{int(_s_alt)} m**  \n"
            f"Coordenadas actuales: **{lat:.5f}°**, **{lon:.5f}°**, **{alt_m} m**  \n"
            "Presiona **🌐 Descargar TMY de PVGIS** para recalcular con las coordenadas actuales."
        )

# ── Auto-restaurar desde caché de disco (sobrevive reinicios de PM2) ─────────
# Si los parámetros actuales coinciden con un caché en disco y la sesión aún no
# tiene datos, restaurar silenciosamente para evitar la descarga de PVGIS.
if not st.session_state.get("recurso_solar_ok"):
    _auto_cached = _leer_cache(lat, lon, tilt, azimuth, alt_m, albedo)
    if _auto_cached is not None:
        _tmy_r = _auto_cached["tmy"]
        _poa_r = _auto_cached["poa"]
        # El caché guarda la POA monofacial — si el modelo bifacial está activo,
        # recalcular localmente la ganancia trasera (sin ir a PVGIS).
        if bifacial_cfg:
            _poa_r = calcular_poa(_tmy_r, lat, lon, alt_m, tilt, azimuth,
                                  albedo=albedo, bifacial=bifacial_cfg)
        _poa_anual_r = _poa_r["poa_global"].sum() / 1000.0
        _ghi_anual_r = _tmy_r["G_h"].sum() / 1000.0
        _t_media_r   = _tmy_r["T2m"].mean()
        def _zona_por_coords_rs(la, lo):
            if 4.5 <= la <= 8.5 and lo <= -76.0:              return "Urabá / Chocó (tropical)"
            if la > 8.5 or (la > 7.5 and lo > -76.0):         return "Barranquilla / Costa"
            if lo > -74.0:                                     return "Llanos Orientales"
            if la < 4.5 and lo < -74.0:                        return "Cali / Valle"
            if la < 5.5 and lo > -74.5:                        return "Bogotá / Sabana"
            return "Medellín / Antioquia"
        st.session_state.update({
            "tmy_df":              _tmy_r,
            "poa_df":              _poa_r,
            "tmy_ciudad":          ciudad,
            "tilt_fachada":        tilt,
            "tilt_default":        tilt,
            "azimuth_fachada":     azimuth,
            "orientacion_label":   orientacion_label,
            "poa_anual_kWh_m2":    round(_poa_anual_r, 1),
            "ghi_anual_kWh_m2":    round(_ghi_anual_r, 1),
            "t_media_anual":       round(_t_media_r, 1),
            "zona_geo_coords":     _zona_por_coords_rs(lat, lon),
            "recurso_solar_ok":    True,
            # ── #64 — Guardar coords para detectar cambios futuros ───────────
            "_solar_lat_guardada": lat,
            "_solar_lon_guardada": lon,
            "_solar_alt_guardada": alt_m,
        })
        st.info(
            f"📂 **Recurso solar restaurado desde caché local** — "
            f"POA: **{_poa_anual_r:,.0f} kWh/m²/año** · "
            f"GHI: **{_ghi_anual_r:,.0f} kWh/m²/año** · "
            f"{icono_tipo} {orientacion_label} / {tilt}°  \n"
            f"*(Sin descarga de PVGIS. Usa 🔄 **Limpiar caché** si necesitas datos frescos.)*"
        )
        st.rerun()

# ── Función cacheada para PVGIS (RAM, 24 h) ──────────────────────────────────
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
    # También borrar caché de disco para este predio/orientación — TODAS las
    # variantes de albedo (sufijo _albXX), no solo la del default 0.20.
    try:
        import glob as _glob
        _base = _cache_path(lat, lon, tilt, azimuth, alt_m)     # sin sufijo
        for _p in _glob.glob(_base.replace(".pkl", "*.pkl")):
            os.remove(_p)
    except Exception:
        pass
    st.session_state["recurso_solar_ok"] = False
    # ── #64 — Limpiar coords guardadas para que la próxima ejecución las reescriba
    for _k in ("_solar_lat_guardada", "_solar_lon_guardada", "_solar_alt_guardada"):
        st.session_state.pop(_k, None)
    st.success("✅ Caché limpiada — presiona **Descargar TMY** para obtener datos frescos.")

if _descarga_btn:

    _sitio_label = (
        f"predio en {ciudad} ({lat:.5f}°, {lon:.5f}°)"
        if _coord_personalizada else f"{ciudad} ({lat}°, {lon}°)"
    )
    # Intentar caché de disco antes de ir a PVGIS
    _disco = _leer_cache(lat, lon, tilt, azimuth, alt_m, albedo)
    if _disco is not None:
        tmy = _disco["tmy"]
        poa = _disco["poa"]
        st.info("📂 Datos recuperados de caché local — sin conexión a PVGIS.")
    else:
        with st.spinner(f"Conectando a PVGIS para {_sitio_label}..."):
            try:
                tmy = cargar_tmy(lat, lon)
            except Exception as e:
                st.error(f"❌ Error conectando a PVGIS: {e}")
                st.info("Verifica la conexión a internet del servidor. PVGIS requiere acceso a re.jrc.ec.europa.eu")
                st.stop()

        with st.spinner(f"Calculando irradiancia POA para {icono_tipo} {tipo_instalacion} ({tilt}°)..."):
            poa = calcular_poa(tmy, lat, lon, alt_m, tilt, azimuth, albedo=albedo)
            # El caché de disco guarda SIEMPRE la POA monofacial; la ganancia
            # bifacial se recalcula localmente (es barata y depende de la config).
            _guardar_cache(lat, lon, tilt, azimuth, alt_m, tmy, poa, albedo)

    # ── Modelo bifacial: recalcular POA con ganancia trasera ─────────────────
    poa_anual_mono = poa["poa_global"].sum() / 1000.0
    if bifacial_cfg:
        with st.spinner("🔄 Calculando ganancia bifacial (pvlib infinite_sheds)..."):
            poa = calcular_poa(tmy, lat, lon, alt_m, tilt, azimuth,
                               albedo=albedo, bifacial=bifacial_cfg)
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

    ganancia_bif_pct = 0.0
    if bifacial_cfg and "poa_front" in poa.columns:
        _front_anual = poa["poa_front"].sum() / 1000.0
        _rear_aporte = poa_anual - _front_anual   # = bifacialidad × POA trasera
        if _front_anual > 0:
            ganancia_bif_pct = _rear_aporte / _front_anual * 100.0
        st.success(
            f"🔄 **Ganancia bifacial: +{ganancia_bif_pct:.1f}%** — "
            f"POA frontal: {_front_anual:,.0f} kWh/m²/año → POA bifacial total: "
            f"{poa_anual:,.0f} kWh/m²/año "
            f"(bifacialidad {bifacial_cfg['bifacialidad']*100:.0f}% · "
            f"altura {bifacial_cfg['altura_m']:.1f} m · "
            f"albedo trasero {bifacial_cfg['albedo_trasero']:.2f}). "
            "Esta POA alimenta el Motor Óptico, Producción, Financiero y el Reporte.",
            icon="🔄",
        )

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
    # Detectar zona geográfica desde coordenadas del proyecto (referencia directa para Presupuesto)
    def _zona_por_coords(la, lo):
        if 4.5 <= la <= 8.5 and lo <= -76.0:              return "Urabá / Chocó (tropical)"
        if la > 8.5 or (la > 7.5 and lo > -76.0):         return "Barranquilla / Costa"
        if lo > -74.0:                                     return "Llanos Orientales"
        if la < 4.5 and lo < -74.0:                        return "Cali / Valle"
        if la < 5.5 and lo > -74.5:                        return "Bogotá / Sabana"
        return "Medellín / Antioquia"
    st.session_state["zona_geo_coords"]    = _zona_por_coords(lat, lon)

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
    # ── Bifacial: persistir configuración y ganancia ─────────────────────────
    st.session_state["albedo_suelo"]          = albedo
    st.session_state["bifacial_activo"]       = bool(bifacial_cfg)
    st.session_state["bifacial_cfg"]          = bifacial_cfg or {}
    st.session_state["ganancia_bifacial_pct"] = round(ganancia_bif_pct, 2)
    # ── #64 — Guardar coords usadas para detectar drift futuro ───────────────
    st.session_state["_solar_lat_guardada"] = lat
    st.session_state["_solar_lon_guardada"] = lon
    st.session_state["_solar_alt_guardada"] = alt_m

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
