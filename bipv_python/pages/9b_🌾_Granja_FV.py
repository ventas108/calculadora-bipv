"""
Página 9b — 🌾 Granja FV (fase 1)
Campo de filas (mesas) para granjas solares y agrivoltaicas, separado de
🗺️ Vista 3D (BIPV). Spec 03-dimensionamiento/granja-fv-campo.
"""
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Granja FV — BIPV", page_icon="🌾", layout="wide")

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()

from calculos.campos_editor import sincronizar_campo
from calculos.campos_persistentes import campo_persistente
from datos.ciudades_colombia import CIUDADES
from calculos.agrivoltaica import luz_en_el_suelo, paso_maquinaria
from calculos.seguidor import SEGUIDOR_DEFECTO, comparar_seguidor_fijo, energia_estimada
from calculos.granja_fv import (
    CAMPOS_EDITABLES,
    aplicar_geometria_a_energia,
    geometria_filas,
    sombra_filas_estimada,
    calcular_campo,
    coherencia_campo,
    dimensiones_modulo,
    geometria_desde_estado,
    modulos_del_proyecto,
    sugerir_distribucion,
    trazas_campo,
)

st.title("🌾 Granja FV — campo de filas")
st.caption(
    "Diseño del campo de una granja solar o agrivoltaica: terreno, mesas, filas, separación "
    "(pitch), GCR y altura. Usa los mismos datos del proyecto que 📐 Dimensionamiento, 📊 "
    "Producción y ☀️ Recurso Solar. Comprueba que tu geometría coincide con la que usan los "
    "cálculos, lleva la sombra entre filas a la energía (sección 5) y calcula la luz que recibe el "
    "cultivo y el paso de la maquinaria (sección 6) y compara un seguidor de un eje con la estructura "
    "fija (sección 7). Las fachadas y techos BIPV siguen en "
    "🗺️ Vista 3D."
)

ss = st.session_state
panel = ss.get("panel_dict") or {}
if not panel:
    st.warning("⚠️ Primero elige el panel en 🏠 Proyecto o 📐 Dimensionamiento.")
    st.stop()

dims = dimensiones_modulo(panel)
pmax = float(panel.get("Pmax_stc") or 0.0)
proy = modulos_del_proyecto(ss)
geo = geometria_desde_estado(ss, dims)

# Datos de la geometría: se guardan con el proyecto en «granja_fv».
_datos = dict(ss.get("granja_fv") or {})
for _k in CAMPOS_EDITABLES:
    _datos.setdefault(_k, geo[_k])
    ss[f"granja_{_k}"] = _datos[_k]


def _aplicar_sugerencia(sugerencia):
    datos = dict(ss.get("granja_fv") or {})
    datos.update(sugerencia)
    ss["granja_fv"] = datos


# ── 1. Datos del proyecto ────────────────────────────────────────────────────
st.markdown("### 1. Datos del proyecto")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Módulos del proyecto", f"{proy['n']:,}",
          help="Los que simuló 📊 Producción; si todavía no simulaste, los de 📐 Dimensionamiento.")
c2.metric("Panel", panel.get("nombre", "—"))
c3.metric("Dimensiones del módulo", f"{dims['largo_m']:.3f} × {dims['ancho_m']:.3f} m",
          help="De la ficha del panel." if dims["origen"] == "ficha"
          else "Estimadas desde el área: la ficha no trae dimensiones.")
c4.metric("Inclinación · azimut", f"{geo['tilt_deg']:.0f}° · {geo['azimut_deg']:.0f}°",
          help="Vienen de 🏠 Proyecto (la misma POA que usa la energía). Cámbialos allá.")
if dims["origen"] != "ficha":
    st.info("ℹ️ La ficha del panel no trae dimensiones: se estiman desde el área del módulo.")

# ── 2. Terreno y mesas ───────────────────────────────────────────────────────
st.markdown("### 2. Terreno, mesas y filas")
t1, t2, t3 = st.columns(3)
with t1:
    campo_persistente(ss, st.number_input, "Ancho del terreno a lo largo de las filas (m)",
                      "granja_ancho_terreno_m", float(_datos["ancho_terreno_m"]),
                      min_value=1.0, max_value=5000.0, step=1.0,
                      help="Con azimut 180° las filas corren de Este a Oeste.")
    campo_persistente(ss, st.number_input, "Largo del terreno de adelante hacia atrás (m)",
                      "granja_largo_terreno_m", float(_datos["largo_terreno_m"]),
                      min_value=1.0, max_value=5000.0, step=1.0)
with t2:
    campo_persistente(ss, st.number_input, "Módulos en la pendiente de la mesa",
                      "granja_modulos_pendiente", int(_datos["modulos_pendiente"]),
                      min_value=1, max_value=6, step=1,
                      help="Cuántos módulos hay de abajo hacia arriba en cada mesa (por ejemplo 2).")
    sincronizar_campo(ss, "_w_granja_orientacion", str(_datos["orientacion"]))
    _ori = st.radio("Orientación del módulo", ["horizontal", "vertical"], horizontal=True,
                    key="_w_granja_orientacion",
                    help="Horizontal: el lado corto va en la pendiente. Vertical: el lado largo.")
    ss["granja_orientacion"] = _ori
    campo_persistente(ss, st.number_input, "Módulos por mesa a lo largo de la fila",
                      "granja_modulos_por_mesa", int(_datos["modulos_por_mesa"]),
                      min_value=1, max_value=500, step=1)
with t3:
    campo_persistente(ss, st.number_input, "Mesas por fila", "granja_mesas_por_fila",
                      int(_datos["mesas_por_fila"]), min_value=1, max_value=100, step=1)
    campo_persistente(ss, st.number_input, "Pasillo entre mesas de una fila (m)", "granja_pasillo_m",
                      float(_datos["pasillo_m"]), min_value=0.0, max_value=50.0, step=0.5)
    campo_persistente(ss, st.number_input, "Separación entre filas, eje a eje — pitch (m)",
                      "granja_pitch_m", float(_datos["pitch_m"]), min_value=0.5, max_value=50.0,
                      step=0.05, help="Distancia de una fila a la siguiente, medida en el suelo.")
    campo_persistente(ss, st.number_input, "Altura libre del borde inferior (m)",
                      "granja_altura_libre_m", float(_datos["altura_libre_m"]),
                      min_value=0.1, max_value=10.0, step=0.1,
                      help="Espacio bajo la mesa para el cultivo y la maquinaria.")

geo = dict(geo)
for _k in CAMPOS_EDITABLES:
    geo[_k] = ss[f"granja_{_k}"]
ss["granja_fv"] = {k: geo[k] for k in CAMPOS_EDITABLES}

_sug = sugerir_distribucion(proy["n"], dims, geo)
if _sug:
    st.button("🪄 Sugerir distribución", on_click=_aplicar_sugerencia, args=(_sug,),
              help=f"Menos filas posibles con una mesa por fila: {_sug['modulos_por_mesa']} módulos "
                   "por mesa a lo largo de la fila, con este terreno y esta separación.")
elif proy["n"]:
    st.caption("🪄 No hay una distribución de una mesa por fila que quepa en este terreno con esta "
               "separación: amplía el terreno o baja la separación entre filas.")

campo = calcular_campo(geo, dims, proy["n"], pmax)
ss["granja_fv_resultado"] = {k: v for k, v in campo.items() if k != "mesas"}

# ── 3. Resultados ────────────────────────────────────────────────────────────
st.markdown("### 3. Resultados del campo")
r1, r2, r3, r4, r5, r6 = st.columns(6)
r1.metric("Módulos ubicados", f"{campo['modulos_colocados']:,} / {proy['n']:,}")
r2.metric("Potencia", f"{campo['kwp']:,.2f} kWp")
r3.metric("GCR", f"{campo['gcr'] * 100:.1f} %", help="Ancho de la mesa ÷ separación entre filas.")
r4.metric("Ángulo límite de sombra", f"{campo['angulo_limite_deg']:.1f}°",
          help="Con el sol más bajo que este ángulo (visto de perfil) una fila sombrea a la siguiente.")
r5.metric("Corredor libre entre filas", f"{campo['corredor_m']:.2f} m")
r6.metric("Suelo libre", f"{campo['suelo_libre_pct']:.0f} %")
st.caption(
    f"🧮 Mesa: {int(geo['modulos_pendiente'])} × {int(geo['modulos_por_mesa'])} módulos · ancho en la "
    f"pendiente {campo['ancho_mesa_m']:.3f} m · huella {campo['huella_ns_m']:.2f} m · borde superior a "
    f"{campo['altura_superior_m']:.2f} m (centro a {campo['altura_centro_m']:.2f} m) · fila de "
    f"{campo['largo_fila_m']:.1f} m · caben {campo['filas_caben']} filas · usadas {campo['filas_usadas']}."
)
for _e in campo["errores"]:
    st.error(f"🔴 {_e}")

# ── 4. Coherencia con el resto del proyecto ─────────────────────────────────
st.markdown("### 4. Coherencia con el resto del proyecto")
for _c in coherencia_campo(campo, ss):
    {"🔴": st.error, "🟠": st.warning}.get(_c["nivel"], st.success if _c["nivel"] == "🟢" else st.info)(
        f"{_c['nivel']} {_c['texto']}")

# ── 5. Sombra entre filas y cara trasera en la energía (fase 2) ─────────────
st.markdown("### 5. Sombra entre filas y cara trasera en la energía")
st.caption(
    "Con la geometría del campo, ☀️ Recurso Solar calcula hora a hora la sombra que cada fila le "
    "hace a la siguiente (luz directa, difusa del cielo y reflejada del suelo) y, con paneles "
    "bifaciales, la luz que llega a la cara trasera según la altura y la separación reales."
)
_geo_e = geometria_filas(campo)
if not campo["errores"] and proy["n"]:
    st.button("⚡ Usar la geometría del campo en la energía", type="primary",
              on_click=aplicar_geometria_a_energia, args=(ss, campo),
              help=f"GCR {_geo_e['gcr']:.3f} · altura del centro {_geo_e['altura_m']:.2f} m · mesa "
                   f"{_geo_e['ancho_colector_m']:.3f} m. Luego vuelve a calcular en ☀️ Recurso Solar.")
    if ss.get("filas_energia") and ss.get("poa_geometria_filas") != ss.get("filas_energia"):
        st.info("ℹ️ Geometría enviada a la energía. Ahora ve a **☀️ Recurso Solar** y presiona el botón de "
                "cálculo para recalcular la POA; después vuelve a simular 📊 Producción.")
_tmy_g = ss.get("tmy_df")
# Mismas coordenadas que ☀️ Recurso Solar: predio exacto, si no el centro de la ciudad
_ciudad_g = CIUDADES.get(ss.get("ciudad", ""), {})
_lat_g = ss.get("lat_proyecto", _ciudad_g.get("lat"))
_lon_g = ss.get("lon_proyecto", _ciudad_g.get("lon"))
_alt_g = ss.get("alt_proyecto", _ciudad_g.get("alt_m", 0))
if _tmy_g is not None and _lat_g is not None and _lon_g is not None and not campo["errores"]:
    if st.button("📏 Estimar la sombra entre filas de este campo"):
        with st.spinner("Calculando 8.760 horas con pvlib infinite_sheds…"):
            ss["granja_sombra_estimada"] = {
                "geo": _geo_e,
                **sombra_filas_estimada(_tmy_g, float(_lat_g), float(_lon_g), float(_alt_g or 0.0),
                                        geo["tilt_deg"], geo["azimut_deg"],
                                        float(ss.get("albedo_suelo", 0.20)), campo),
            }
    _est = ss.get("granja_sombra_estimada")
    if _est and _est.get("geo") == _geo_e:
        e1, e2, e3 = st.columns(3)
        e1.metric("POA frontal sin filas vecinas", f"{_est['poa_sin_kwh_m2']:,.0f} kWh/m²")
        e2.metric("POA frontal con el campo", f"{_est['poa_con_kwh_m2']:,.0f} kWh/m²")
        e3.metric("Pérdida por sombra entre filas", f"{_est['perdida_frontal_pct']:.2f} %")
else:
    st.caption("📏 Para estimar la sombra entre filas, calcula primero el recurso solar en ☀️ Recurso Solar.")

# ── 6. Agrivoltaica: luz para el cultivo y maquinaria (fase 3) ─────────────
st.markdown("### 6. 🌱 Agrivoltaica: luz para el cultivo y paso de la maquinaria")
st.caption(
    "Cuánta luz del sol llega al suelo bajo las mesas y entre las filas, comparada con el mismo "
    "terreno sin paneles, y si la maquinaria agrícola cabe. Corte de perfil entre dos filas largas; "
    "no se suma la luz que reflejan el suelo y la cara de abajo de los paneles (resultado del lado seguro)."
)
m1, m2 = st.columns(2)
with m1:
    campo_persistente(ss, st.number_input, "Altura de la maquinaria (m)",
                      "granja_altura_maquinaria_m", float(ss.get("granja_altura_maquinaria_m", 2.5)),
                      min_value=0.5, max_value=6.0, step=0.1,
                      help="La máquina más alta que debe pasar (tractor con cabina ≈ 2,5–3,0 m).")
with m2:
    campo_persistente(ss, st.number_input, "Ancho de la maquinaria (m)",
                      "granja_ancho_maquinaria_m", float(ss.get("granja_ancho_maquinaria_m", 2.2)),
                      min_value=0.5, max_value=10.0, step=0.1,
                      help="Ancho de la máquina o del implemento más ancho.")
if not campo["errores"] and campo["gcr"] > 0:
    for _c in paso_maquinaria(campo, float(ss["granja_altura_maquinaria_m"]),
                              float(ss["granja_ancho_maquinaria_m"])):
        {"🟠": st.warning, "🟢": st.success}.get(_c["nivel"], st.info)(f"{_c['nivel']} {_c['texto']}")
_firma_luz = {k: round(float(campo[k]), 4) for k in ("gcr", "huella_ns_m", "altura_superior_m",
                                                      "tilt_deg", "azimut_deg")}
if _tmy_g is not None and _lat_g is not None and _lon_g is not None and not campo["errores"]:
    if st.button("🌱 Calcular la luz en el suelo"):
        with st.spinner("Calculando la luz en el suelo hora a hora…"):
            ss["granja_luz_suelo"] = {"firma": _firma_luz, **luz_en_el_suelo(
                _tmy_g, float(_lat_g), float(_lon_g), float(_alt_g or 0.0), campo)}
    _luz = ss.get("granja_luz_suelo")
    if _luz and _luz.get("firma") == _firma_luz:
        l1, l2, l3, l4, l5 = st.columns(5)
        l1.metric("Luz media en el suelo", f"{_luz['media_pct']:.0f} %",
                  help="Promedio entre dos filas, frente al terreno sin paneles.")
        l2.metric("Luz media anual", f"{_luz['media_kwh_m2']:,.0f} kWh/m²",
                  help=f"Sin paneles: {_luz['referencia_kwh_m2']:,.0f} kWh/m² al año.")
        l3.metric("Bajo las mesas", f"{_luz['bajo_mesa_pct']:.0f} %")
        l4.metric("Entre las filas", f"{_luz['entre_filas_pct']:.0f} %")
        l5.metric("Homogeneidad", f"{_luz['homogeneidad']:.2f}",
                  help="Punto más oscuro ÷ punto más iluminado: 1 = luz pareja en todo el suelo.")
        _gy = _luz["geometria"]
        _fp = go.Figure(go.Scatter(x=_luz["y_m"], y=_luz["pct"], mode="lines", name="Luz anual",
                                   line=dict(color="rgb(46,125,50)", width=3),
                                   hovertemplate="%{x:.2f} m · %{y:.0f} %<extra></extra>"))
        _fp.add_vrect(x0=0, x1=_gy["huella"], fillcolor="rgb(52,101,164)", opacity=0.15, line_width=0,
                      annotation_text="bajo la mesa", annotation_position="top left")
        _fp.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0), yaxis_title="Luz (% del campo abierto)",
                          xaxis_title="Posición desde el borde inferior de una mesa hasta la siguiente (m)",
                          yaxis_range=[0, 100], title="Luz anual en el suelo entre dos filas")
        st.plotly_chart(_fp, use_container_width=True)
        _meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        _fm = go.Figure(go.Heatmap(z=_luz["mensual_pct"], x=_luz["y_m"], y=_meses, zmin=0, zmax=100,
                                   colorscale="YlGn", colorbar=dict(title="%"),
                                   hovertemplate="%{y} · %{x:.2f} m · %{z:.0f} %<extra></extra>"))
        _fm.add_vline(x=_gy["huella"], line_dash="dash", line_color="rgb(52,101,164)")
        _fm.update_layout(height=380, margin=dict(l=0, r=0, t=30, b=0),
                          xaxis_title="Posición entre dos filas (m) — la línea marca el fin de la mesa",
                          title="Mapa de sombra en el suelo: luz de cada mes (% del campo abierto)")
        st.plotly_chart(_fm, use_container_width=True)
        st.caption(f"🌱 Bajo la mesa: 0 a {_gy['huella']:.2f} m · entre las filas: {_gy['huella']:.2f} a "
                   f"{_gy['pitch']:.2f} m · luz mínima {_luz['min_pct']:.0f} %, máxima {_luz['max_pct']:.0f} %.")
else:
    st.caption("🌱 Para calcular la luz en el suelo, calcula primero el recurso solar en ☀️ Recurso Solar.")

# ── 7. Seguidor de un eje frente a la estructura fija (fase 4) ─────────────
st.markdown("### 7. ☀️ Seguidor de un eje frente a la estructura fija")
st.caption(
    "Compara la luz en la cara frontal del campo fijo con un seguidor de eje Norte–Sur que gira de Este a "
    "Oeste, con y sin backtracking, usando el mismo modelo de filas. Sin backtracking la fila vecina "
    "tapa una franja del seguidor al amanecer y al atardecer y los diodos de bypass apagan bloques de "
    "celdas. La energía de 📊 Producción sigue calculada con la estructura fija."
)
s1, s2, s3, s4, s5 = st.columns(5)
with s1:
    campo_persistente(ss, st.number_input, "Módulos a lo ancho (vertical)", "granja_seg_modulos_ancho",
                      int(ss.get("granja_seg_modulos_ancho", SEGUIDOR_DEFECTO["modulos_ancho"])),
                      min_value=1, max_value=2, step=1, help="1P = un módulo en vertical; 2P = dos.")
with s2:
    campo_persistente(ss, st.number_input, "GCR del seguidor", "granja_seg_gcr",
                      float(ss.get("granja_seg_gcr", SEGUIDOR_DEFECTO["gcr"])),
                      min_value=0.15, max_value=0.70, step=0.01,
                      help="Ancho del seguidor ÷ separación entre ejes. Típico 0,30–0,40.")
with s3:
    campo_persistente(ss, st.number_input, "Altura del eje (m)", "granja_seg_altura_eje_m",
                      float(ss.get("granja_seg_altura_eje_m", SEGUIDOR_DEFECTO["altura_eje_m"])),
                      min_value=0.8, max_value=6.0, step=0.1)
with s4:
    campo_persistente(ss, st.number_input, "Ángulo máximo de giro (°)", "granja_seg_angulo_max_deg",
                      float(ss.get("granja_seg_angulo_max_deg", SEGUIDOR_DEFECTO["angulo_max_deg"])),
                      min_value=30.0, max_value=75.0, step=5.0)
with s5:
    sincronizar_campo(ss, "_w_granja_seg_celdas_partidas",
                      bool(ss.get("granja_seg_celdas_partidas", SEGUIDOR_DEFECTO["celdas_partidas"])))
    ss["granja_seg_celdas_partidas"] = st.checkbox(
        "Celdas partidas (half-cut)", key="_w_granja_seg_celdas_partidas",
        help="Módulos de medias celdas: las dos mitades trabajan en paralelo y una sombra en el borde "
             "apaga solo una mitad.")
_cfg_seg = {"modulos_ancho": int(ss["granja_seg_modulos_ancho"]), "gcr": float(ss["granja_seg_gcr"]),
            "altura_eje_m": float(ss["granja_seg_altura_eje_m"]),
            "angulo_max_deg": float(ss["granja_seg_angulo_max_deg"]),
            "celdas_partidas": bool(ss["granja_seg_celdas_partidas"])}
_fijo_seg = {"tilt_deg": float(campo["tilt_deg"]), "azimut_deg": float(campo["azimut_deg"]),
             "gcr": round(float(campo["gcr"]), 4), "altura_m": round(float(campo["altura_centro_m"]), 3),
             "ancho_m": round(float(campo["ancho_mesa_m"]), 3)}
_firma_seg = {"seg": _cfg_seg, "fijo": _fijo_seg, "largo": round(float(dims["largo_m"]), 4)}
if _tmy_g is not None and _lat_g is not None and _lon_g is not None and not campo["errores"] and campo["gcr"] > 0:
    if st.button("🔄 Comparar seguidor y estructura fija"):
        with st.spinner("Calculando 8.760 horas con pvlib (seguidor con y sin backtracking)…"):
            _r = comparar_seguidor_fijo(_tmy_g, float(_lat_g), float(_lon_g), float(_alt_g or 0.0),
                                        float(ss.get("albedo_suelo", 0.20)), _fijo_seg, _cfg_seg,
                                        float(dims["largo_m"]))
            ss["granja_seguidor"] = {"firma": _firma_seg, **_r}
    _seg = ss.get("granja_seguidor")
    if _seg and _seg.get("firma") == _firma_seg:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Estructura fija", f"{_seg['fijo']['poa_kwh_m2']:,.0f} kWh/m²",
                  help="Luz anual en la cara frontal del campo actual (con la sombra entre filas).")
        k2.metric("Seguidor con backtracking", f"{_seg['backtracking']['poa_kwh_m2']:,.0f} kWh/m²",
                  f"{_seg['ganancia_backtracking_pct']:+.1f} % frente a la fija")
        k3.metric("Seguidor sin backtracking", f"{_seg['sin_backtracking']['poa_kwh_m2']:,.0f} kWh/m²",
                  f"{_seg['ganancia_sin_backtracking_pct']:+.1f} % frente a la fija")
        k4.metric("Sombra eléctrica sin backtracking", f"{_seg['perdida_sombra_electrica_pct']:.1f} %",
                  help=f"{_seg['sin_backtracking']['horas_sombra']:,} horas al año con una franja de sombra de "
                       "la fila vecina; los diodos de bypass apagan los bloques de celdas tocados.")
        _gs = _seg["geometria"]
        st.caption(f"🔧 Seguidor de {_gs['ancho_m']:.2f} m de ancho · separación entre ejes {_gs['pitch_m']:.2f} m · "
                   f"{_gs['bloques']} bloque(s) de celdas a lo ancho · borde más bajo a {_gs['borde_bajo_m']:.2f} m "
                   f"con el giro máximo de {_gs['angulo_max_deg']:.0f}°.")
        if _gs["borde_bajo_m"] < 0.5:
            st.warning(f"🟠 Con el giro máximo el borde del seguidor queda a {_gs['borde_bajo_m']:.2f} m del "
                       "suelo: sube la altura del eje o baja el ángulo máximo.")
        _e_fijo = float(ss.get("E_ac_anual_kWh") or 0.0)
        if _e_fijo > 0:
            st.info(f"⚡ Estimación de primer orden: si 📊 Producción da {_e_fijo:,.0f} kWh/año con la estructura "
                    f"fija, el seguidor con backtracking daría ≈ {energia_estimada(_e_fijo, _seg):,.0f} kWh/año "
                    "(misma proporción que la luz frontal; no incluye el recorte extra del inversor, cambios de "
                    "temperatura, bifacialidad ni costos).")
        _meses_s = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        _fb = go.Figure()
        for _nom, _k, _col in (("Fija", "fijo", "rgb(120,120,120)"), ("Seguidor con backtracking", "backtracking",
                                                                      "rgb(46,125,50)"),
                               ("Seguidor sin backtracking", "sin_backtracking", "rgb(230,145,56)")):
            _fb.add_bar(x=_meses_s, y=_seg[_k]["mensual_kwh_m2"], name=_nom, marker_color=_col)
        _fb.update_layout(barmode="group", height=340, margin=dict(l=0, r=0, t=30, b=0),
                          yaxis_title="kWh/m²", title="Luz en la cara frontal por mes")
        st.plotly_chart(_fb, use_container_width=True)
        _de = _seg["dia_ejemplo"]
        _fa = go.Figure()
        _fa.add_scatter(x=_de["hora"], y=_de["backtracking"], name="Con backtracking", mode="lines+markers",
                        line=dict(color="rgb(46,125,50)"))
        _fa.add_scatter(x=_de["hora"], y=_de["sin_backtracking"], name="Sin backtracking", mode="lines+markers",
                        line=dict(color="rgb(230,145,56)", dash="dash"))
        _fa.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), xaxis_title="Hora local",
                          yaxis_title="Giro (°): − Este, + Oeste", title="Giro del seguidor el 21 de marzo")
        st.plotly_chart(_fa, use_container_width=True)
else:
    st.caption("☀️ Para comparar el seguidor, calcula primero el recurso solar en ☀️ Recurso Solar.")

# ── 8. Vista 3D del campo ────────────────────────────────────────────────────
st.markdown("### 8. Vista 3D del campo")
_fig = go.Figure(data=trazas_campo(campo))
_fig.update_layout(
    scene=dict(xaxis_title="A lo largo de la fila (m)", yaxis_title="Adelante → atrás (m)",
               zaxis_title="Altura (m)", aspectmode="data"),
    height=520, margin=dict(l=0, r=0, t=30, b=0),
    title=f"{campo['modulos_colocados']} módulos · {campo['kwp']:,.2f} kWp · GCR {campo['gcr'] * 100:.1f} %",
)
st.plotly_chart(_fig, use_container_width=True)
st.caption("Ejes del campo: con azimut 180° la fila corre de Este a Oeste y el frente mira al Sur.")
