"""Página 1 — Configuración del proyecto."""
import json
import os
import streamlit as st
from datetime import date
from datos.ciudades_colombia import CIUDADES, LISTA_CIUDADES, FECHA_VALIDACION_TARIFAS
from calculos.tz_utils import utc_offset_latam, tz_label
from calculos.tarifa_utils import init_tarifa, set_tarifa_from_ciudad, tarifa_widget
from calculos.invalidacion import KEYS_RECURSO_SOLAR, KEYS_DERIVADOS_POA
from calculos.proyectos_manager import (
    listar_proyectos, guardar_proyecto_actual,
    cargar_proyecto, eliminar_proyecto,
)


@st.cache_data(ttl=86400, show_spinner=False)
def _geocodificar_inverso(lat: float, lon: float) -> str:
    """Obtiene municipio/región desde coordenadas — Nominatim OSM, sin clave."""
    import urllib.request
    import urllib.parse
    try:
        params = urllib.parse.urlencode({
            "lat": lat, "lon": lon, "format": "json", "zoom": 10,
            "accept-language": "es",
        })
        url = f"https://nominatim.openstreetmap.org/reverse?{params}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BIPV-Calculadora/1.0 (calc.innovacionquimica.com.co)"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
        addr = data.get("address", {})
        municipio = (addr.get("municipality") or addr.get("city")
                     or addr.get("town") or addr.get("village")
                     or addr.get("county") or "")
        region    = addr.get("state_district") or addr.get("region") or ""
        estado    = addr.get("state") or ""
        partes    = [p for p in [municipio, region, estado] if p]
        return ", ".join(partes)
    except Exception:
        return ""

# ── Rutas de persistencia POR USUARIO (auditoría: sin archivos compartidos) ──
# Cada cuenta guarda su configuración en su propio archivo dentro de
# datos/persistencia/ — dos usuarios del mismo servidor nunca se ven ni se
# pisan el proyecto. Requiere login, por eso la carga va DESPUÉS de
# requerir_login() (más abajo).
_DIR_DATOS = os.path.join(os.path.dirname(__file__), "..", "datos")

from calculos.persistencia_resultados import ruta_datos_usuario

def _ruta_proyecto_usuario():
    return ruta_datos_usuario("proyecto_actual.json",
                              st.session_state.get("auth_email", ""))

def _ruta_consumo_usuario():
    return ruta_datos_usuario("consumo_cache.json",
                              st.session_state.get("auth_email", ""))

def _cargar_proyecto():
    """Lee el proyecto y el consumo guardados DEL USUARIO — vuelca en session_state."""
    for _ruta in (_ruta_proyecto_usuario(), _ruta_consumo_usuario()):
        if os.path.exists(_ruta):
            try:
                with open(_ruta, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                for k, v in saved.items():
                    st.session_state.setdefault(k, v)
            except Exception:
                pass

def _guardar_proyecto(datos: dict):
    """Persiste datos del proyecto en el JSON privado del usuario."""
    _ruta = _ruta_proyecto_usuario()
    os.makedirs(os.path.dirname(_ruta), exist_ok=True)
    _tmp = f"{_ruta}.{os.getpid()}.tmp"
    with open(_tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(_tmp, _ruta)

st.set_page_config(page_title="Proyecto — BIPV", page_icon="🏠", layout="wide")

from calculos.auth import requerir_login
requerir_login()

# ── Cargar al inicio de cada sesión (solo la primera vez, ya logueado) ──────
if "proyecto_cargado_desde_disco" not in st.session_state:
    _cargar_proyecto()
    st.session_state["proyecto_cargado_desde_disco"] = True

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página
st.title("🏠 Datos del Proyecto")

# ── 📁 Gestión de múltiples proyectos (tarea #63) ────────────────────────────
with st.expander("📁 Mis Proyectos — guardar / cambiar proyecto", expanded=False):
    _proyectos = listar_proyectos()
    _nombre_actual = st.session_state.get("nombre_proyecto", "Proyecto BIPV")

    # ── Guardar proyecto actual ───────────────────────────────────────────────
    st.markdown("**💾 Guardar proyecto actual**")
    _col_nombre, _col_btn = st.columns([3, 1])
    _nombre_guardar = _col_nombre.text_input(
        "Nombre del proyecto a guardar",
        value=_nombre_actual,
        key="_pm_nombre_guardar",
        label_visibility="collapsed",
        placeholder="Nombre del proyecto",
    )
    if _col_btn.button("💾 Guardar", key="_pm_btn_guardar", use_container_width=True):
        try:
            # Sincronizar nombre en session_state antes de guardar
            st.session_state["nombre_proyecto"] = _nombre_guardar
            _slug_guardado = guardar_proyecto_actual(_nombre_guardar)
            st.success(f"✅ Proyecto «{_nombre_guardar}» guardado correctamente.")
            st.rerun()
        except Exception as _e_pm:
            st.error(f"Error al guardar: {_e_pm}")

    st.divider()

    # ── Lista de proyectos guardados ──────────────────────────────────────────
    if not _proyectos:
        st.info(
            "No hay proyectos guardados todavía. "
            "Ingresa los datos del proyecto y pulsa **💾 Guardar** para crear el primero."
        )
    else:
        st.markdown(f"**📂 Proyectos guardados** ({len(_proyectos)})")
        for _p in _proyectos:
            _es_actual = (
                _p["nombre"].strip().lower() == _nombre_actual.strip().lower()
            )
            _fecha_corta = _p["guardado"][:16].replace("T", " ") if _p["guardado"] else "—"
            _e_ac_label  = (
                f"{_p['e_ac_kWh']:,.0f} kWh/año"
                if _p["e_ac_kWh"] > 0 else "sin E_ac"
            )
            _area_label  = f"{_p['area_m2']:.0f} m²" if _p["area_m2"] > 0 else "—"
            _tag = " 🔵 **(actual)**" if _es_actual else ""

            _pc1, _pc2, _pc3 = st.columns([4, 1, 1])
            _pc1.markdown(
                f"**{_p['nombre']}**{_tag}  \n"
                f"<span style='color:#888;font-size:0.85em'>"
                f"{_p['ciudad']} · {_area_label} · {_e_ac_label} · {_fecha_corta}"
                f"</span>",
                unsafe_allow_html=True,
            )
            if _pc2.button("📂 Cargar", key=f"_pm_cargar_{_p['slug']}", use_container_width=True):
                try:
                    _nombre_cargado = cargar_proyecto(_p["slug"])
                    st.session_state["_proyecto_recien_cargado"] = True
                    st.rerun()
                except Exception as _e_carga:
                    st.error(f"Error al cargar: {_e_carga}")
            if _pc3.button("🗑️", key=f"_pm_del_{_p['slug']}", help="Eliminar proyecto", use_container_width=True):
                eliminar_proyecto(_p["slug"])
                st.rerun()

    st.caption(
        "💡 Los resultados de simulación (Producción, Bypass, Motor IV) "
        "no se guardan — deberás volver a ejecutarlos tras cargar un proyecto. "
        "Los datos de entrada (ciudad, área, equipos, presupuesto) sí se preservan."
    )

# ── Banner de pasos pendientes tras cargar un proyecto (#124) ────────────────
if st.session_state.get("_proyecto_recien_cargado"):
    _pasos = []
    if not st.session_state.get("recurso_solar_ok"):
        _pasos.append("☀️ **Recurso Solar**")
    if not st.session_state.get("produccion_ok"):
        _pasos.append("📊 **Producción**")
    if not st.session_state.get("financiero_ok"):
        _pasos.append("💰 **Financiero**")

    if _pasos:
        _col_banner, _col_x = st.columns([10, 1])
        _col_banner.info(
            f"📂 **Proyecto cargado.** Para activar todos los módulos, "
            f"re-ejecuta en orden: {' → '.join(_pasos)}  \n"
            f"💡 Si las coordenadas no cambiaron, ☀️ Recurso Solar se revalida "
            f"solo al abrir la página (usa el caché de disco, sin descarga)."
        )
        if _col_x.button("✕", key="_pm_dismiss_banner", help="Descartar aviso"):
            st.session_state.pop("_proyecto_recien_cargado", None)
            st.rerun()
    else:
        # Todos los pasos están listos — limpiar flag
        st.session_state.pop("_proyecto_recien_cargado", None)

# ── Tipos de instalación con defaults técnicos ────────────────────────────────
TIPOS_INSTALACION = {
    #  icono  dens W/m²              PR              tilt °
    "Fachada BIPV":             {"icono": "🏢", "dens_min": 70,  "dens_max": 90,  "dens_def": 75,  "pr_def": 0.70, "pr_hint": "0.65–0.75", "tilt_def": 90},
    "Techo inclinado (BIPV)":   {"icono": "🏠", "dens_min": 100, "dens_max": 200, "dens_def": 150, "pr_def": 0.78, "pr_hint": "0.75–0.85", "tilt_def": 25},
    "Techo plano (con soporte)":{"icono": "🏭", "dens_min": 130, "dens_max": 200, "dens_def": 160, "pr_def": 0.80, "pr_hint": "0.75–0.85", "tilt_def": 15},
    "Pérgola / sombreadero":    {"icono": "⛱️", "dens_min": 80,  "dens_max": 130, "dens_def": 100, "pr_def": 0.73, "pr_hint": "0.68–0.78", "tilt_def": 10},
    "Marquesina / voladizo":    {"icono": "🏗️", "dens_min": 70,  "dens_max": 100, "dens_def": 80,  "pr_def": 0.70, "pr_hint": "0.65–0.75", "tilt_def": 20},
    "Granja fotovoltaica":      {"icono": "☀️", "dens_min": 150, "dens_max": 240, "dens_def": 190, "pr_def": 0.82, "pr_hint": "0.78–0.88", "tilt_def": 20},
}
LISTA_TIPOS = list(TIPOS_INSTALACION.keys())

# ── Selector de modo ─────────────────────────────────────────────────────────
modo = st.radio(
    "¿Cuál es tu punto de partida?",
    ["📐 Tengo un área disponible", "🔌 Conozco mi consumo / factura"],
    index=0 if st.session_state.get("modo_calculo", "area") == "area" else 1,
    horizontal=True,
)
modo_key = "consumo" if "consumo" in modo else "area"
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Identificación")
    nombre = st.text_input("Nombre del proyecto",
                           value=st.session_state.get("nombre_proyecto", "Proyecto BIPV"))

    # ── Detectar cambio de ciudad ANTES de mostrar el expander ───────────────
    ciudad_anterior = st.session_state.get("ciudad", "Bogotá")
    ciudad = st.selectbox(
        "Ciudad de referencia climática",
        LISTA_CIUDADES,
        index=LISTA_CIUDADES.index(ciudad_anterior),
        help=(
            "Selecciona la ciudad cuyo clima se asemeja más al sitio del proyecto. "
            "Si el predio está en una ubicación no listada (ej. Urabá, Catatumbo, "
            "Llanos Orientales), elige la ciudad más cercana en temperatura y régimen "
            "de lluvia. Las coordenadas exactas del predio se ingresan abajo — PVGIS "
            "descargará los datos TMY para esas coordenadas, no para el centro de "
            "esta ciudad."
        ),
    )

    # Si la ciudad cambió → pre-cargar coords Y tarifa de la nueva ciudad
    if ciudad != ciudad_anterior:
        c_nueva = CIUDADES.get(ciudad, {})
        st.session_state["ciudad"] = ciudad
        # Establecer coords nuevas ANTES de renderizar el expander (evita DOM error)
        st.session_state["_lat_custom_temp"] = c_nueva.get("lat", 4.711)
        st.session_state["_lon_custom_temp"] = c_nueva.get("lon", -74.072)
        st.session_state["_alt_custom_temp"] = c_nueva.get("alt_m", 0)
        # Pre-cargar tarifa del operador local de la nueva ciudad (con metadata de ciudad/operador)
        set_tarifa_from_ciudad(ciudad, CIUDADES)
        # Limpiar datos de proyecto + recurso solar (coords del sitio cambian)
        _KEYS_LIMPIAR_CIUDAD = (
            "lat_proyecto", "lon_proyecto", "alt_proyecto",
            "densidad_Wm2", "PR", "tilt_default",
            # ── #64 — Recurso solar para las coordenadas anteriores ──────────
            "recurso_solar_ok", "tmy_df", "poa_df", "tmy_ciudad",
            "tilt_fachada", "azimuth_fachada", "orientacion_label",
            "poa_anual_kWh_m2", "ghi_anual_kWh_m2", "t_media_anual",
            "zona_geo_coords", "poa_efectiva_df", "poa_sin_termico_df",
            "motor_optico_ok", "motor_optico_result_df", "motor_optico_summary",
            "poa_efectiva_anual_kWh_m2",
            "motor_optico_b0", "motor_optico_tau", "motor_optico_k_bipv",
            "motor_optico_noct", "motor_optico_coef_temp", "motor_optico_f_iam_dif",
            "motor_optico_k_soil_vert",
            "_solar_lat_guardada", "_solar_lon_guardada", "_solar_alt_guardada",
        )
        for _k in _KEYS_LIMPIAR_CIUDAD:
            st.session_state.pop(_k, None)
        # #89 — borrar también los resultados de Producción persistidos a disco:
        # si sobreviven, Financiero los "restauraría" con el sol de otra ciudad.
        from calculos.persistencia_resultados import limpiar_resultados_produccion
        limpiar_resultados_produccion(st.session_state.get("auth_email", ""))
        st.rerun()  # Re-render limpio para evitar DOM error al cambiar ciudad

    # ── Tipo de instalación — key= para que Streamlit maneje el estado ────────
    # Inicializar desde valor guardado si es la primera vez
    if "tipo_inst_key" not in st.session_state:
        _saved = st.session_state.get("tipo_instalacion", LISTA_TIPOS[0])
        st.session_state["tipo_inst_key"] = _saved if _saved in LISTA_TIPOS else LISTA_TIPOS[0]

    _tipo_prev = st.session_state["tipo_inst_key"]   # valor ANTES de este render

    tipo_instalacion = st.selectbox(
        "Tipo de instalación",
        LISTA_TIPOS,
        key="tipo_inst_key",   # Streamlit gestiona el estado — sin index=
        help="Define el contexto físico del sistema solar. Ajusta los rangos recomendados de densidad y PR.",
        format_func=lambda t: f"{TIPOS_INSTALACION[t]['icono']}  {t}",
    )
    cfg = TIPOS_INSTALACION[tipo_instalacion]
    st.session_state["tipo_instalacion"] = tipo_instalacion  # compatibilidad con Save

    # ── Banner de tipo — siempre coherente con el selectbox ──────────────────
    st.info(
        f"{cfg['icono']} **{tipo_instalacion}** — "
        f"Densidad: {cfg['dens_min']}–{cfg['dens_max']} W/m²  |  "
        f"PR: {cfg['pr_hint']}  |  "
        f"Inclinación sugerida: **{cfg['tilt_def']}°**"
    )

    # Si cambió el tipo → resetear densidad, PR y tilt a los defaults del nuevo tipo
    if tipo_instalacion != _tipo_prev:
        st.session_state.pop("densidad_Wm2", None)
        st.session_state.pop("PR", None)
        st.session_state.pop("tilt_default", None)

    area = st.number_input(
        "Área de instalación disponible (m²)",
        min_value=10.0, max_value=500_000.0,
        value=float(st.session_state.get("area_fachada_m2", 97.34)),
        step=1.0,
        help=f"{cfg['icono']} {tipo_instalacion} — ingresa la superficie total del predio o superficie."
    )

    # ── Factor de ocupación con paneles (#agrivoltaica) ──────────────────────
    # En granjas agrivoltaicas los paneles NO pueden cubrir el 100% del terreno:
    # el cultivo necesita luz directa. Típico agrivoltaica: 25–35%.
    # Clamp defensivo: un JSON corrupto fuera de [5, 100] rompería el widget
    _f_ocup_def = min(max(float(st.session_state.get("factor_ocupacion_pct", 100.0) or 100.0), 5.0), 100.0)
    factor_ocupacion = st.number_input(
        "Factor de ocupación con paneles (%)",
        min_value=5.0, max_value=100.0, value=_f_ocup_def, step=5.0,
        help=(
            "Porcentaje del área disponible que realmente se cubre con paneles. "
            "🌱 **Agrivoltaica** (cultivo bajo los paneles): usa 25–35% para que "
            "el cultivo reciba sol directo. "
            "☀️ Granja FV convencional: 40–60% (separación entre filas). "
            "🏠 Techo/fachada dedicados: 100%."
        ),
    )
    st.session_state["factor_ocupacion_pct"] = factor_ocupacion
    area_util = area * factor_ocupacion / 100.0
    st.session_state["area_util_m2"] = area_util
    if factor_ocupacion < 100.0:
        st.caption(
            f"🌱 Área efectiva de paneles: **{area_util:,.0f} m²** "
            f"({factor_ocupacion:.0f}% de {area:,.0f} m²) — "
            f"el {100 - factor_ocupacion:.0f}% restante queda libre para el cultivo."
        )

    # ── Inputs adicionales Modo Consumo ──────────────────────────────────────
    consumo_mes   = 0.0
    factura_cop   = 0.0
    cobertura_pct = int(st.session_state.get("cobertura_pct", 80))

    # ── Tarifa sincronizada con Financiero — patrón TRM ──────────────────────
    init_tarifa(ciudad, CIUDADES)   # no-op si ya fue inicializada
    tarifa_kwh = tarifa_widget("proy")

    # ── Aviso si las tarifas del catálogo llevan más de 6 meses sin actualizar ─
    try:
        _fv = date.fromisoformat(FECHA_VALIDACION_TARIFAS)
        _meses_sin_actualizar = (date.today() - _fv).days / 30.44
        if _meses_sin_actualizar > 6:
            st.warning(
                f"⚠️ **Tarifas del catálogo desactualizadas** — la última validación fue el "
                f"**{_fv.strftime('%d/%m/%Y')}** "
                f"({int(_meses_sin_actualizar)} meses). "
                f"Las tarifas de CREG/operadores pueden haber variado. "
                f"Confirma con la factura real del cliente o la circular CREG más reciente "
                f"y ajusta el valor arriba. "
                f"*(Para actualizar el catálogo: `bipv_python/datos/ciudades_colombia.py` → "
                f"campo `tarifa_comercial_cop_kwh` + actualizar `FECHA_VALIDACION_TARIFAS`.)*"
            )
    except Exception:
        pass

    if modo_key == "consumo":
        st.subheader("Consumo / Factura")
        # ── #94 — Recordar también el modo de entrada entre sesiones ─────────
        # (el valor guardado en consumo_cache.json ya llegó a session_state vía
        # _cargar_proyecto; sanear por si el archivo trae un valor inválido)
        if st.session_state.get("entrada_consumo") not in ("Factura COP", "Consumo kWh/mes"):
            st.session_state.pop("entrada_consumo", None)
        entrada = st.radio("Ingresar por:", ["Factura COP", "Consumo kWh/mes"],
                           horizontal=True, key="entrada_consumo")
        if entrada == "Factura COP":
            factura_cop = st.number_input("Factura mensual (COP)",
                                          min_value=0.0,
                                          value=float(st.session_state.get("factura_cop", 573755.0)),
                                          step=1000.0, format="%.0f")
            consumo_mes = factura_cop / tarifa_kwh if tarifa_kwh > 0 else 0.0
            st.info(f"Consumo estimado: **{consumo_mes:.1f} kWh/mes**")
        else:
            consumo_mes = st.number_input("Consumo mensual (kWh/mes)",
                                          min_value=0.0,
                                          value=float(st.session_state.get("consumo_kwh_mes", 565.0)),
                                          step=10.0)
            factura_cop = consumo_mes * tarifa_kwh
        cobertura_pct = st.slider("% Cobertura deseada", 10, 100,
                                  value=int(st.session_state.get("cobertura_pct", 80)),
                                  step=5, format="%d%%")

with col2:
    st.subheader("Datos del sitio")
    if ciudad in CIUDADES:
        c = CIUDADES[ciudad]

        # ── Coordenadas exactas del predio (opcional) ─────────────────────
        with st.expander("📍 Coordenadas exactas del predio (opcional — para mayor precisión)"):
            st.caption(
                "Por defecto se usan las coordenadas del centro de la ciudad. "
                "Si conoces las coordenadas GPS exactas del predio, ingrésalas aquí. "
                "PVGIS descargará el TMY para ese punto específico."
            )
            _lat_def = float(st.session_state.get("lat_proyecto", c["lat"]))
            _lon_def = float(st.session_state.get("lon_proyecto", c["lon"]))
            _alt_def = int(st.session_state.get("alt_proyecto",   c["alt_m"]))

            cx1, cx2, cx3 = st.columns(3)
            lat_custom = cx1.number_input(
                "Latitud (°N)", min_value=-5.0, max_value=15.0,
                value=_lat_def, step=0.00001, format="%.5f",
                help="Positivo = Norte del Ecuador. Colombia: 4° a 13°N aprox."
            )
            lon_custom = cx2.number_input(
                "Longitud (°E)", min_value=-82.0, max_value=-66.0,
                value=_lon_def, step=0.00001, format="%.5f",
                help="Colombia: entre -67° y -82°. Siempre negativo."
            )
            alt_custom = cx3.number_input(
                "Altitud (m.s.n.m.)", min_value=0, max_value=4500,
                value=_alt_def, step=10,
                help="Altitud del predio en metros sobre el nivel del mar."
            )

            _coords_personalizadas = (
                abs(lat_custom - c["lat"]) > 0.0001 or
                abs(lon_custom - c["lon"]) > 0.0001 or
                alt_custom != c["alt_m"]
            )
            if _coords_personalizadas:
                # ── Geocodificación inversa — municipio real del predio ───────
                with st.spinner("Detectando municipio…"):
                    _municipio = _geocodificar_inverso(lat_custom, lon_custom)
                if _municipio:
                    st.success(
                        f"✅ Coordenadas del predio: **{lat_custom:.5f}°**, "
                        f"**{lon_custom:.5f}°**, **{alt_custom} m.s.n.m.**  \n"
                        f"📍 **Municipio detectado: {_municipio}**  \n"
                        f"Se usarán estas coordenadas en Recurso Solar."
                    )
                    st.session_state["municipio_predio"] = _municipio
                else:
                    st.success(
                        f"✅ Coordenadas del predio: **{lat_custom:.5f}°**, "
                        f"**{lon_custom:.5f}°**, **{alt_custom} m.s.n.m.**  "
                        f"— Se usarán estas coordenadas en Recurso Solar."
                    )
                    st.session_state.pop("municipio_predio", None)
            else:
                st.info(
                    f"Usando coordenadas de referencia de {ciudad}: "
                    f"{c['lat']}°, {c['lon']}°. "
                    "Modifica los valores para usar las del predio específico."
                )
                st.session_state.pop("municipio_predio", None)

            st.session_state["_lat_custom_temp"] = lat_custom
            st.session_state["_lon_custom_temp"] = lon_custom
            st.session_state["_alt_custom_temp"] = alt_custom

        # ── Panel "Datos del sitio" — refleja ciudad + coordenadas activas ──
        _lat_activa = st.session_state.get("_lat_custom_temp", c["lat"])
        _lon_activa = st.session_state.get("_lon_custom_temp", c["lon"])
        _alt_activa = st.session_state.get("_alt_custom_temp", c["alt_m"])
        _coords_mod = (
            abs(_lat_activa - c["lat"]) > 0.0001 or
            abs(_lon_activa - c["lon"]) > 0.0001 or
            _alt_activa != c["alt_m"]
        )
        _coord_label = (
            f"**Latitud:** {_lat_activa:.5f}°  |  **Longitud:** {_lon_activa:.5f}°  |  "
            f"**Altitud:** {_alt_activa} m  ⚠️ *coordenadas del predio*"
            if _coords_mod else
            f"**Latitud:** {c['lat']}°  |  **Longitud:** {c['lon']}°  |  "
            f"**Altitud:** {c['alt_m']} m"
        )
        st.info(
            f"{_coord_label}\n\n"
            f"**GHI:** {c['GHI_kWh_m2_dia']} kWh/m²·día  |  **HSP:** {c['HSP']} h/día\n\n"
            f"**T_amb media:** {c['T_amb_media']}°C  |  "
            f"**T_mín diseño:** {c['T_min_diseno']}°C\n\n"
            f"**Región:** {c['region']}  |  **Zona CREG:** {c['CREG_zona']}"
        )
        _tz_off_p = utc_offset_latam(_lat_activa, _lon_activa)
        _tz_lbl_p = tz_label(_tz_off_p)
        st.caption(
            f"🕐 Zona horaria estimada para este sitio: **{_tz_lbl_p}** "
            f"— los heatmaps y diagramas solares se mostrarán en hora local. "
            f"Guarda el proyecto para aplicarla."
        )

        GHI_anual = c["GHI_kWh_m2_dia"] * 365

        # ── Densidad de potencia — desde panel seleccionado o entrada manual ─
        panel_ss = st.session_state.get("panel_dict")
        if panel_ss and panel_ss.get("area_m2") and panel_ss.get("Pmax_stc"):
            dens_Wm2 = panel_ss["Pmax_stc"] / panel_ss["area_m2"]
            st.caption(f"Panel activo: {panel_ss['nombre']} → {dens_Wm2:.0f} W/m²")
        else:
            dens_Wm2 = st.number_input(
                "Densidad de potencia del panel (W/m²)",
                min_value=30.0, max_value=300.0,
                value=float(st.session_state.get("densidad_Wm2", float(cfg["dens_def"]))),
                step=5.0,
                help=(
                    f"{cfg['icono']} {tipo_instalacion}: "
                    f"{cfg['dens_min']}–{cfg['dens_max']} W/m²  |  "
                    "CdTe BIPV fachada: 70–90 · Mono-Si techo/campo: 150–220 W/m²"
                )
            )

        # ── Alerta densidad fuera de rango (#48) ─────────────────────────────
        if not (panel_ss and panel_ss.get("area_m2")):   # solo cuando es entrada manual
            if dens_Wm2 < cfg["dens_min"]:
                st.warning(
                    f"⚠️ **Densidad baja** para {cfg['icono']} {tipo_instalacion}: "
                    f"ingresaste **{dens_Wm2:.0f} W/m²**, rango recomendado "
                    f"**{cfg['dens_min']}–{cfg['dens_max']} W/m²**. "
                    f"¿Usas un módulo de baja eficiencia o película delgada?"
                )
            elif dens_Wm2 > cfg["dens_max"]:
                st.warning(
                    f"⚠️ **Densidad alta** para {cfg['icono']} {tipo_instalacion}: "
                    f"ingresaste **{dens_Wm2:.0f} W/m²**, rango recomendado "
                    f"**{cfg['dens_min']}–{cfg['dens_max']} W/m²**. "
                    f"Verifica la ficha técnica del panel."
                )

        PR = st.number_input(
            "Performance Ratio (PR)",
            min_value=0.40, max_value=0.98,
            value=float(st.session_state.get("PR", cfg["pr_def"])),
            step=0.01,
            help=(
                f"{cfg['icono']} {tipo_instalacion}: {cfg['pr_hint']}  |  "
                "BIPV fachada: 0.65–0.75 · Techo conv.: 0.75–0.85 · Granja FV: 0.78–0.88"
            )
        )

        # ── Alerta PR fuera de rango (#48) ───────────────────────────────────
        _pr_min, _pr_max = (float(x) for x in cfg["pr_hint"].split("–"))
        if PR < _pr_min:
            st.warning(
                f"⚠️ **PR bajo** para {cfg['icono']} {tipo_instalacion}: "
                f"ingresaste **{PR:.2f}**, rango recomendado **{cfg['pr_hint']}**. "
                f"Un PR muy bajo sobreestima las pérdidas del sistema."
            )
        elif PR > _pr_max:
            st.warning(
                f"⚠️ **PR alto** para {cfg['icono']} {tipo_instalacion}: "
                f"ingresaste **{PR:.2f}**, rango recomendado **{cfg['pr_hint']}**. "
                f"Valores >0.85 son poco frecuentes sin monitoreo activo de pérdidas."
            )

        eta = dens_Wm2 / 1000.0

        st.divider()
        if modo_key == "area":
            E_anual = area_util * eta * GHI_anual * PR
            ahorro_mes = E_anual / 12.0 * tarifa_kwh
            st.subheader("📊 Estimación de producción")

            # % cobertura si existe consumo previo en session_state
            _consumo_prev = float(st.session_state.get("consumo_kwh_mes", 0.0))
            if _consumo_prev > 0:
                _cob_area = min(E_anual / (_consumo_prev * 12) * 100, 100)
                m1, m2, m3 = st.columns(3)
                m1.metric("Energía anual proyectada", f"{E_anual:,.0f} kWh/año")
                m2.metric("Ahorro estimado", f"${ahorro_mes:,.0f} COP/mes")
                m3.metric("Cobertura de consumo", f"{_cob_area:.0f}%",
                          help=f"Sobre un consumo previo de {_consumo_prev:.0f} kWh/mes")
            else:
                m1, m2 = st.columns(2)
                m1.metric("Energía anual proyectada", f"{E_anual:,.0f} kWh/año")
                m2.metric("Ahorro estimado", f"${ahorro_mes:,.0f} COP/mes")
                st.caption(
                    "💡 Para ver el **% de cobertura** cambia al modo Consumo o "
                    "guarda un proyecto con consumo conocido."
                )
            st.session_state["energia_anual_estimada"] = E_anual

        else:
            E_objetivo  = consumo_mes * (cobertura_pct / 100.0) * 12.0
            denominador = eta * GHI_anual * PR
            area_nec    = E_objetivo / denominador if denominador > 0 else 0.0
            E_con_area  = area_util * eta * GHI_anual * PR
            cob_real    = min(E_con_area / (consumo_mes * 12) * 100, 100) if consumo_mes > 0 else 0.0

            # N paneles estimados — usar panel activo si está disponible
            _panel_area = panel_ss.get("area_m2") if panel_ss else None
            _panel_pmax = panel_ss.get("Pmax_stc") if panel_ss else None
            if _panel_area and _panel_area > 0 and area_nec > 0:
                import math
                _n_est = math.ceil(area_nec / _panel_area)
                _n_label = f"{_n_est} paneles"
                _n_help = (
                    f"Panel: {panel_ss['nombre']} ({_panel_area:.2f} m²) — "
                    f"área necesaria {area_nec:.1f} m² ÷ área panel {_panel_area:.2f} m²"
                )
            else:
                _kWp_nec = area_nec * dens_Wm2 / 1000.0
                _n_est = None
                _n_label = f"{_kWp_nec:.1f} kWp"
                _n_help = (
                    "Selecciona un panel en ⚡ Motor IV para ver el número exacto de módulos. "
                    f"Potencia requerida estimada: {_kWp_nec:.2f} kWp "
                    f"({area_nec:.1f} m² × {dens_Wm2:.0f} W/m²)"
                )

            st.subheader("📊 Resultados del diseño")
            delta_m2 = area_util - area_nec
            m1, m2, m3 = st.columns(3)
            m1.metric("Área necesaria", f"{area_nec:.1f} m²",
                      delta=f"{delta_m2:+.1f} m² vs disponible",
                      delta_color="normal" if delta_m2 >= 0 else "inverse")
            m2.metric("Cobertura alcanzable", f"{cob_real:.0f}%",
                      delta=f"objetivo {cobertura_pct}%",
                      delta_color="normal" if cob_real >= cobertura_pct else "inverse")
            m3.metric(
                "N paneles estimados" if _n_est is not None else "Potencia estimada",
                _n_label,
                help=_n_help,
            )

            semaforo = "🟢" if area_util >= area_nec else "🔴"
            st.info(
                f"{semaforo} Energía objetivo: **{E_objetivo:,.0f} kWh/año**  |  "
                f"Producción con área disponible: **{E_con_area:,.0f} kWh/año**"
            )
            st.session_state["energia_anual_estimada"] = E_con_area
            st.session_state["consumo_kwh_mes"]        = consumo_mes

            # ── Auto-persistir consumo a disco (sin requerir click en Guardar) ──
            try:
                _consumo_cache = {
                    "consumo_kwh_mes": consumo_mes,
                    "factura_cop":     factura_cop,
                    "cobertura_pct":   cobertura_pct,
                    "modo_calculo":    "consumo",
                    "tarifa_cop_kwh":  tarifa_kwh,
                    # #94 — recordar si el usuario entra por factura o por kWh
                    "entrada_consumo": entrada,
                }
                _consumo_path = _ruta_consumo_usuario()
                _prev_c: dict = {}
                if os.path.exists(_consumo_path):
                    with open(_consumo_path, "r", encoding="utf-8") as _fcc:
                        _prev_c = json.load(_fcc)
                if _consumo_cache != _prev_c:
                    os.makedirs(os.path.dirname(_consumo_path), exist_ok=True)
                    import uuid as _uuid_c
                    _tmp_c = f"{_consumo_path}.{os.getpid()}.{_uuid_c.uuid4().hex[:8]}.tmp"
                    with open(_tmp_c, "w", encoding="utf-8") as _fcc:
                        json.dump(_consumo_cache, _fcc, ensure_ascii=False)
                    os.replace(_tmp_c, _consumo_path)
            except Exception:
                pass

# ── Guardar ──────────────────────────────────────────────────────────────────
if st.button("💾 Guardar configuración", type="primary"):
    _dens_val = dens_Wm2 if "dens_Wm2" in dir() else cfg["dens_def"]

    # ── #172 — Última configuración CONFIRMADA (guardas dedicadas) ───────────
    # No sirve leer area_util_m2/tipo_instalacion del session_state: el render
    # ya los sobreescribe con los valores nuevos ANTES del click en Guardar.
    _area_util_prev = st.session_state.get("_area_util_guardada")
    _tipo_prev_save = st.session_state.get("_tipo_inst_guardado")

    st.session_state["nombre_proyecto"]    = nombre
    st.session_state["ciudad"]             = ciudad
    st.session_state["tipo_instalacion"]   = tipo_instalacion
    st.session_state["area_fachada_m2"]    = area   # clave histórica — no renombrar
    st.session_state["factor_ocupacion_pct"] = factor_ocupacion
    st.session_state["area_util_m2"]       = area_util
    st.session_state["modo_calculo"]       = modo_key
    st.session_state["PR"]                 = PR
    st.session_state["densidad_Wm2"]       = _dens_val
    st.session_state["tilt_default"]       = cfg["tilt_def"]
    st.session_state["tarifa_cop_kwh"]     = tarifa_kwh
    if modo_key == "consumo":
        st.session_state["factura_cop"]    = factura_cop
        st.session_state["consumo_kwh_mes"]= consumo_mes
        st.session_state["cobertura_pct"]  = cobertura_pct
    if ciudad in CIUDADES:
        c = CIUDADES[ciudad]
        # No pisar las temperaturas ya calculadas desde el TMY con ceros o
        # nulos del catálogo de ciudades (dejaba los widgets "en ceros").
        _temps_ciudad = (
            c.get("T_min_diseno"),
            c.get("T_cel_realista"),
            c.get("T_cel_extremo"),
        )
        if any(_t not in (None, 0, 0.0) for _t in _temps_ciudad):
            st.session_state["T_min_diseno"]   = c["T_min_diseno"]
            st.session_state["T_cel_realista"] = c["T_cel_realista"]
            st.session_state["T_cel_extremo"]  = c["T_cel_extremo"]
        st.session_state["GHI_kWh_m2_dia"] = c["GHI_kWh_m2_dia"]
        st.session_state["lat_proyecto"] = st.session_state.get("_lat_custom_temp", c["lat"])
        st.session_state["lon_proyecto"] = st.session_state.get("_lon_custom_temp", c["lon"])
        st.session_state["alt_proyecto"] = st.session_state.get("_alt_custom_temp", c["alt_m"])
        st.session_state["utc_offset_local"] = utc_offset_latam(
            st.session_state["lat_proyecto"], st.session_state["lon_proyecto"]
        )
    st.session_state["recurso_solar_ok"] = False

    # ── #64 — Si las coordenadas cambiaron, invalidar TODA la cadena solar ───
    # No basta con recurso_solar_ok=False: Financiero, Baterías, CO₂ y el
    # Reporte leen E_ac_anual_kWh directamente, así que una producción vieja
    # calculada con el sol de otro lugar sobreviviría al cambio de predio.
    _s_lat64 = st.session_state.get("_solar_lat_guardada")
    _s_lon64 = st.session_state.get("_solar_lon_guardada")
    if _s_lat64 is not None and (
        abs(st.session_state["lat_proyecto"] - float(_s_lat64)) > 0.0001 or
        abs(st.session_state["lon_proyecto"] - float(_s_lon64)) > 0.0001
    ):
        _CADENA_SOLAR_KEYS = (
            KEYS_RECURSO_SOLAR
            + KEYS_DERIVADOS_POA
            + ("_solar_lat_guardada", "_solar_lon_guardada", "_solar_alt_guardada",
               "_solar_tilt_guardado", "_solar_az_guardado", "_solar_albedo_guardado")
        )
        for _k64 in _CADENA_SOLAR_KEYS:
            st.session_state.pop(_k64, None)
        # #89 — invalidar también los resultados persistidos a disco
        from calculos.persistencia_resultados import limpiar_resultados_produccion
        limpiar_resultados_produccion(st.session_state.get("auth_email", ""))
        st.warning(
            "⚠️ **Las coordenadas del proyecto cambiaron** — se invalidaron el recurso "
            "solar y todos los resultados derivados (producción, bypass, multi-superficie). "
            "Vuelve a ejecutar **☀️ Recurso Solar** y las páginas siguientes para que toda "
            "la cadena use el sol de la ubicación nueva.",
            icon="🌍",
        )
    # ── #172 — Si cambió el área útil o el tipo de instalación, invalidar los
    # derivados: el recurso solar del sitio sigue válido, pero el nº de paneles,
    # la producción, el bypass, el financiero y el CO₂ ya no corresponden.
    elif (
        (_area_util_prev is not None and abs(area_util - float(_area_util_prev)) > 0.01)
        or (_tipo_prev_save is not None and tipo_instalacion != _tipo_prev_save)
    ):
        for _k172 in KEYS_DERIVADOS_POA:
            st.session_state.pop(_k172, None)
        _que_cambio = []
        if _tipo_prev_save is not None and tipo_instalacion != _tipo_prev_save:
            _que_cambio.append(f"tipo de instalación (**{_tipo_prev_save}** → **{tipo_instalacion}**)")
        if _area_util_prev is not None and abs(area_util - float(_area_util_prev)) > 0.01:
            _que_cambio.append(f"área útil (**{float(_area_util_prev):,.1f} m²** → **{area_util:,.1f} m²**)")
        st.warning(
            f"⚠️ Cambió el {' y el '.join(_que_cambio)} — se invalidaron los resultados "
            "derivados (producción, bypass, financiero, CO₂). El recurso solar del sitio "
            "sigue válido; vuelve a ejecutar **📐 Dimensionamiento → 📊 Producción** y las "
            "páginas siguientes.",
            icon="📐",
        )
    # ── #172 — Actualizar las guardas con la configuración recién guardada ───
    st.session_state["_area_util_guardada"] = area_util
    st.session_state["_tipo_inst_guardado"] = tipo_instalacion

    # ── Persistir a disco — sobrevive recargas y reinicios de PM2 ────────────
    _datos_json = {
        "nombre_proyecto":  nombre,
        "ciudad":           ciudad,
        "tipo_instalacion": tipo_instalacion,
        "area_fachada_m2":  area,
        "factor_ocupacion_pct": factor_ocupacion,
        "area_util_m2":     area_util,
        "modo_calculo":     modo_key,
        "PR":               PR,
        "densidad_Wm2":     _dens_val,
        "tilt_default":     cfg["tilt_def"],
        "tarifa_cop_kwh":   tarifa_kwh,
        "lat_proyecto":     st.session_state["lat_proyecto"],
        "lon_proyecto":     st.session_state["lon_proyecto"],
        "alt_proyecto":     st.session_state["alt_proyecto"],
    }
    if modo_key == "consumo":
        _datos_json.update({
            "factura_cop":     factura_cop,
            "consumo_kwh_mes": consumo_mes,
            "cobertura_pct":   cobertura_pct,
        })
    try:
        _guardar_proyecto(_datos_json)
    except Exception as _e:
        st.warning(f"⚠️ No se pudo guardar en disco: {_e}")

    _lat = st.session_state["lat_proyecto"]
    _lon = st.session_state["lon_proyecto"]
    _alt = st.session_state["alt_proyecto"]
    _coord_msg = (
        f"Predio: **{_lat:.5f}°**, **{_lon:.5f}°**, **{_alt} m.s.n.m.**"
        if (abs(_lat - CIUDADES[ciudad]["lat"]) > 0.0001 or
            abs(_lon - CIUDADES[ciudad]["lon"]) > 0.0001)
        else f"Coordenadas de referencia de {ciudad}"
    )
    st.success(
        f"✅ Configuración guardada — {cfg['icono']} **{tipo_instalacion}** · "
        f"{_coord_msg}. Continúa en ☀️ Recurso Solar."
    )
