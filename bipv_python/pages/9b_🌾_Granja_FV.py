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
    "Producción y ☀️ Recurso Solar. En esta fase el campo **no cambia la energía**: muestra si "
    "tu geometría coincide con la que usan los cálculos. Las fachadas y techos BIPV siguen en "
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

# ── 6. Vista 3D del campo ────────────────────────────────────────────────────
st.markdown("### 6. Vista 3D del campo")
_fig = go.Figure(data=trazas_campo(campo))
_fig.update_layout(
    scene=dict(xaxis_title="A lo largo de la fila (m)", yaxis_title="Adelante → atrás (m)",
               zaxis_title="Altura (m)", aspectmode="data"),
    height=520, margin=dict(l=0, r=0, t=30, b=0),
    title=f"{campo['modulos_colocados']} módulos · {campo['kwp']:,.2f} kWp · GCR {campo['gcr'] * 100:.1f} %",
)
st.plotly_chart(_fig, use_container_width=True)
st.caption("Ejes del campo: con azimut 180° la fila corre de Este a Oeste y el frente mira al Sur.")
