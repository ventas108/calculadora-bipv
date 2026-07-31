"""Página 1 — Configuración del proyecto."""
import streamlit as st
from datos.ciudades_colombia import CIUDADES, LISTA_CIUDADES
from calculos.tz_utils import utc_offset_latam, tz_label

st.set_page_config(page_title="Proyecto — BIPV", page_icon="🏠", layout="wide")
st.title("🏠 Datos del Proyecto")

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
    ciudad = st.selectbox("Ciudad", LISTA_CIUDADES,
                          index=LISTA_CIUDADES.index(ciudad_anterior))

    # Si la ciudad cambió → pre-cargar coords de la nueva ciudad y rerenderizar limpio
    if ciudad != ciudad_anterior:
        c_nueva = CIUDADES.get(ciudad, {})
        st.session_state["ciudad"] = ciudad
        # Establecer coords nuevas ANTES de renderizar el expander (evita DOM error)
        st.session_state["_lat_custom_temp"] = c_nueva.get("lat", 4.711)
        st.session_state["_lon_custom_temp"] = c_nueva.get("lon", -74.072)
        st.session_state["_alt_custom_temp"] = c_nueva.get("alt_m", 0)
        for _k in ("lat_proyecto", "lon_proyecto", "alt_proyecto",
                   "densidad_Wm2", "PR", "tilt_default"):
            st.session_state.pop(_k, None)
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
        help=f"{cfg['icono']} {tipo_instalacion} — ingresa la superficie neta de paneles."
    )

    # ── Inputs adicionales Modo Consumo ──────────────────────────────────────
    consumo_mes   = 0.0
    factura_cop   = 0.0
    cobertura_pct = int(st.session_state.get("cobertura_pct", 80))

    tarifa_kwh = st.number_input(
        "Tarifa local (COP/kWh)",
        min_value=100.0, max_value=2000.0,
        value=float(st.session_state.get("tarifa_cop_kwh", 850.0)),
        step=10.0,
        help="Varía por ciudad y empresa prestadora. Consulta tu factura de energía.")

    if modo_key == "consumo":
        st.subheader("Consumo / Factura")
        entrada = st.radio("Ingresar por:", ["Factura COP", "Consumo kWh/mes"], horizontal=True)
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
                st.success(
                    f"✅ Coordenadas del predio: **{lat_custom:.5f}°**, "
                    f"**{lon_custom:.5f}°**, **{alt_custom} m.s.n.m.**  "
                    f"— Se usarán estas coordenadas en Recurso Solar."
                )
            else:
                st.info(
                    f"Usando coordenadas de referencia de {ciudad}: "
                    f"{c['lat']}°, {c['lon']}°. "
                    "Modifica los valores para usar las del predio específico."
                )

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
            E_anual = area * eta * GHI_anual * PR
            ahorro_mes = E_anual / 12.0 * tarifa_kwh
            st.subheader("📊 Estimación de producción")
            m1, m2 = st.columns(2)
            m1.metric("Energía anual proyectada", f"{E_anual:,.0f} kWh/año")
            m2.metric("Ahorro estimado", f"${ahorro_mes:,.0f} COP/mes")
            st.session_state["energia_anual_estimada"] = E_anual

        else:
            E_objetivo  = consumo_mes * (cobertura_pct / 100.0) * 12.0
            denominador = eta * GHI_anual * PR
            area_nec    = E_objetivo / denominador if denominador > 0 else 0.0
            E_con_area  = area * eta * GHI_anual * PR
            cob_real    = min(E_con_area / (consumo_mes * 12) * 100, 100) if consumo_mes > 0 else 0.0

            st.subheader("📊 Resultados del diseño")
            delta_m2 = area - area_nec
            m1, m2 = st.columns(2)
            m1.metric("Área necesaria", f"{area_nec:.1f} m²",
                      delta=f"{delta_m2:+.1f} m² vs disponible",
                      delta_color="normal" if delta_m2 >= 0 else "inverse")
            m2.metric("Cobertura alcanzable", f"{cob_real:.0f}%",
                      delta=f"objetivo {cobertura_pct}%",
                      delta_color="normal" if cob_real >= cobertura_pct else "inverse")

            semaforo = "🟢" if area >= area_nec else "🔴"
            st.info(
                f"{semaforo} Energía objetivo: **{E_objetivo:,.0f} kWh/año**  |  "
                f"Producción con área disponible: **{E_con_area:,.0f} kWh/año**"
            )
            st.session_state["energia_anual_estimada"] = E_con_area
            st.session_state["consumo_kwh_mes"]        = consumo_mes

# ── Guardar ──────────────────────────────────────────────────────────────────
if st.button("💾 Guardar configuración", type="primary"):
    st.session_state["nombre_proyecto"]    = nombre
    st.session_state["ciudad"]             = ciudad
    st.session_state["tipo_instalacion"]   = tipo_instalacion
    st.session_state["area_fachada_m2"]    = area   # clave histórica — no renombrar
    st.session_state["modo_calculo"]       = modo_key
    st.session_state["PR"]                 = PR
    st.session_state["densidad_Wm2"]       = dens_Wm2 if "dens_Wm2" in dir() else cfg["dens_def"]
    st.session_state["tilt_default"]       = cfg["tilt_def"]   # #47 — usado como default en Recurso Solar
    st.session_state["tarifa_cop_kwh"]     = tarifa_kwh
    if modo_key == "consumo":
        st.session_state["factura_cop"]    = factura_cop
        st.session_state["consumo_kwh_mes"]= consumo_mes
        st.session_state["cobertura_pct"]  = cobertura_pct
    if ciudad in CIUDADES:
        c = CIUDADES[ciudad]
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
