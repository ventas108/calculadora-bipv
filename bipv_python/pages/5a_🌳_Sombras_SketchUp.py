# -*- coding: utf-8 -*-
"""
🌳 Sombras desde SketchUp — Opción A
====================================
Sube el modelo 3D del sitio exportado de SketchUp (OBJ/STL/DAE/PLY/GLB),
define los puntos de análisis (una fila de módulos = un punto) y la app
calcula el Factor de Sombreado hora a hora con ray-casting contra el sol,
usando el MISMO TMY del proyecto (alineación 1:1 con 📊 Producción).

El resultado es el mismo CSV de la Calculadora de Sombreado 3D web:
entra directo a 🔀 Mismatch/Bypass → E_ac corregida → 💰 Financiero.
Las dos rutas (web y SketchUp) conviven — nada de lo existente cambia.
"""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sombras desde SketchUp", page_icon="🌳", layout="wide")

from calculos.auth import requerir_login
from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página

requerir_login()


from calculos.sombras_3d import (
    MAX_RAYOS,
    TRIMESH_OK,
    calcular_fs_horario,
    cargar_malla,
    estimar_rayos,
    exportar_csv_fs,
    resumen_fs,
    resumen_malla,
    validar_puntos,
)

st.title("🌳 Sombras desde tu modelo de SketchUp")
st.caption(
    "Modela el sitio en SketchUp (edificios vecinos, árboles, tu estructura), expórtalo "
    "y aquí se calcula el sombreado de las 8.760 horas automáticamente — la brecha que "
    "nos separaba de PVsyst, con un modelador mejor."
)

if not TRIMESH_OK:
    st.error(
        "Falta la librería **trimesh** en el servidor. Instálala una vez con:\n\n"
        "`cd /var/www/bipv/calculadora-bipv/bipv_python && venv/bin/pip install trimesh`"
    )
    st.stop()

with st.expander("📖 Cómo exportar desde SketchUp (léelo la primera vez)", expanded=False):
    st.markdown("""
1. Modela en **metros** y con el **norte real en el eje verde (Y)**. Si tu modelo está
   girado, aquí puedes indicar el ángulo de corrección.
2. **NO incluyas los paneles** en el modelo (se sombrearían a sí mismos). Solo obstáculos:
   edificios vecinos, árboles, tanques, la propia edificación si sombrea la fachada.
3. Árboles: modélalos como volúmenes simples (cilindro + esfera) — abajo puedes darles
   una transparencia típica (30–60% de la luz pasa el follaje).
4. Exporta: *Archivo → Exportar → Modelo 3D* → formato **OBJ** o **STL** (también DAE/GLB).
5. Cada **punto de análisis** = una fila de módulos: usa las coordenadas (x, y, z en m)
   del centro de esa fila, tomadas del propio SketchUp (herramienta de medición).
    """)

# ══════════════════════════════════════════════════════════════════════════════
# 1. Modelo 3D
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("1️⃣ Modelo 3D del sitio")

archivo = st.file_uploader(
    "Modelo exportado de SketchUp",
    type=["obj", "stl", "dae", "ply", "glb"],
    help="Solo los obstáculos que producen sombra — sin los paneles.",
)
c1, c2 = st.columns(2)
with c1:
    escala = st.selectbox(
        "Unidades del modelo",
        options=[("Metros (recomendado)", 1.0), ("Centímetros", 0.01),
                 ("Milímetros", 0.001), ("Pulgadas", 0.0254), ("Pies", 0.3048)],
        format_func=lambda o: o[0],
    )[1]
with c2:
    rot_norte = st.number_input(
        "Corrección de norte (° horario)",
        min_value=-180.0, max_value=180.0, value=0.0, step=1.0,
        help="Si el norte real NO es el eje verde del modelo: ángulo que hay que "
             "girar el modelo (visto desde arriba, sentido horario) para alinearlo.",
    )

malla = None
if archivo is not None:
    _tipo = archivo.name.rsplit(".", 1)[-1].lower()
    try:
        malla = cargar_malla(archivo.getvalue(), _tipo, escala=escala,
                             rotacion_norte_deg=rot_norte)
        r = resumen_malla(malla)
        st.success(
            f"Modelo cargado: **{r['n_triangulos']:,} triángulos** · dimensiones "
            f"{r['dim_x_m']} × {r['dim_y_m']} × {r['dim_z_m']} m (alto {r['z_min']}–{r['z_max']} m)."
        )
        if max(r["dim_x_m"], r["dim_y_m"], r["dim_z_m"]) > 2000:
            st.warning(
                "⚠️ El modelo mide más de 2 km — probablemente las unidades no son metros. "
                "Cambia el selector de unidades.", icon="⚠️",
            )
    except Exception as e:
        st.error(f"❌ No se pudo leer el modelo: {e}")
        malla = None

# ══════════════════════════════════════════════════════════════════════════════
# 2. Puntos de análisis
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("2️⃣ Puntos de análisis (una fila de módulos = un punto)")

_default_pts = pd.DataFrame([
    {
        "Punto": "Fila 1", "Fila": "Fila 1", "Fachada": "Principal",
        "N módulos": 1, "Área activa (m²)": 0.0,
        "Potencia instalada (kW)": 0.0,
        "x (m)": 0.0, "y (m)": 0.0, "z (m)": 1.0,
    },
    {
        "Punto": "Fila 2", "Fila": "Fila 2", "Fachada": "Principal",
        "N módulos": 1, "Área activa (m²)": 0.0,
        "Potencia instalada (kW)": 0.0,
        "x (m)": 0.0, "y (m)": 3.0, "z (m)": 1.0,
    },
])
df_pts = st.data_editor(
    st.session_state.get("sk_puntos_df", _default_pts),
    num_rows="dynamic", use_container_width=True, key="sk_puntos_editor",
)
st.session_state["sk_puntos_df"] = df_pts
st.caption(
    "Coordenadas en el sistema del modelo (X=Este/rojo, Y=Norte/verde, Z=altura), en metros. "
    "La **Fachada** permite filtrar en la Página 5 (igual que en la Calculadora web). "
    "Los pesos opcionales **N módulos**, **Área activa** y **Potencia instalada** "
    "permiten que la Página 5 pondere filas de distinto tamaño. Si se dejan vacíos o "
    "en cero, el contrato informa y usa promedio simple."
)

transparencia = st.slider(
    "Transparencia del obstáculo (árboles)",
    min_value=0.0, max_value=0.8, value=0.0, step=0.05,
    help="0 = sólido (edificios). Árboles: 0,3–0,6 (fracción de luz que atraviesa el follaje). "
         "Se aplica a TODO el modelo — si mezclas edificios y árboles, calcula en dos pasadas.",
)

# ══════════════════════════════════════════════════════════════════════════════
# 3. Calcular
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("3️⃣ Calcular el Factor de Sombreado horario")

_coords = st.session_state.get("zona_geo_coords")
_tmy = st.session_state.get("tmy_df")
cc1, cc2 = st.columns(2)
with cc1:
    lat = st.number_input("Latitud", min_value=-60.0, max_value=60.0,
                          value=float(_coords[0]) if _coords else 7.884, format="%.4f")
with cc2:
    lon = st.number_input("Longitud", min_value=-180.0, max_value=180.0,
                          value=float(_coords[1]) if _coords else -76.635, format="%.4f")

if _tmy is not None:
    st.info(
        "✅ Se usará el **índice horario del TMY del proyecto** (☀️ Recurso Solar): las horas "
        "del CSV coinciden 1:1 con las que usa 📊 Producción."
    )
else:
    st.error(
        "⛔ No hay TMY cargado en la sesión. Sin el TMY del proyecto las horas del CSV "
        "NO coinciden con las de Producción (el TMY de PVGIS viene en UTC) y la sombra "
        "quedaría corrida ~5 horas. **Corre primero ☀️ Recurso Solar** y vuelve."
    )
    st.stop()

# ── Firma de entradas: si algo cambia, el resultado anterior se invalida ─────
_firma = None
if archivo is not None:
    import hashlib
    _firma = hashlib.sha256(
        archivo.getvalue()
        + repr((escala, rot_norte, transparencia, round(lat, 4), round(lon, 4),
                len(_tmy) if _tmy is not None else 0,
                df_pts.to_json())).encode()
    ).hexdigest()
if st.session_state.get("sk_firma") not in (None, _firma):
    # cambió el modelo o algún parámetro → el cálculo viejo ya no es válido
    st.session_state.pop("sk_df_fs", None)
    st.session_state.pop("csv_fs_sketchup_bytes", None)
    st.session_state.pop("csv_fs_sketchup_nombre", None)

if st.button("▶️ Calcular sombras (ray-casting)", type="primary",
             disabled=(malla is None)):
    puntos = []
    for _, fila in df_pts.iterrows():
        try:
            puntos.append({
                "nombre": str(fila["Punto"]), "fachada": str(fila["Fachada"]),
                "fila": str(fila.get("Fila", fila["Punto"])),
                "n_modulos": float(fila.get("N módulos", 0) or 0),
                "area_activa_m2": float(fila.get("Área activa (m²)", 0) or 0),
                "potencia_instalada_kw": float(
                    fila.get("Potencia instalada (kW)", 0) or 0
                ),
                "x": float(fila["x (m)"]), "y": float(fila["y (m)"]), "z": float(fila["z (m)"]),
            })
        except (ValueError, TypeError):
            continue
    if not puntos:
        st.error("Define al menos un punto de análisis válido.")
    elif estimar_rayos(len(puntos)) > MAX_RAYOS:
        st.error(
            f"Demasiados puntos ({len(puntos)}): serían más de {MAX_RAYOS:,} rayos. "
            "Reduce a un punto por FILA de módulos (no por módulo)."
        )
    else:
        for _aviso in validar_puntos(malla, puntos):
            st.warning(_aviso, icon="⚠️")
        with st.spinner(f"Lanzando rayos para {len(puntos)} punto(s) × horas con sol…"):
            try:
                df_fs = calcular_fs_horario(
                    malla, puntos, lat, lon,
                    indice_tmy=_tmy.index,
                    transparencia=transparencia,
                )
                st.session_state["sk_df_fs"] = df_fs
                st.session_state["sk_firma"] = _firma
            except Exception as e:
                st.error(f"❌ Error en el cálculo: {e}")

df_fs = st.session_state.get("sk_df_fs")
if df_fs is not None:
    stats = resumen_fs(df_fs)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Puntos", stats["puntos"])
    m2.metric("Horas con sol evaluadas", f"{stats['horas_evaluadas']:,}")
    m3.metric("Horas con sombra", f"{stats['pct_horas_con_sombra']:.1f}%")
    m4.metric("FS medio (con sombra)", f"{stats['fs_medio_con_sombra']:.2f}")

    if stats["registros_con_sombra"] == 0:
        st.warning(
            "El modelo no produce NINGUNA sombra sobre los puntos. Verifica: unidades, "
            "corrección de norte, y que los puntos estén donde crees (z correcta).", icon="⚠️",
        )

    # Perfil mensual medio a mediodía para sanidad visual
    _md = df_fs[df_fs["Hora"].between(11, 13)].groupby("Mes")["FS_geometrico"].mean()
    if not _md.empty:
        st.caption("FS medio 11:00–13:00 por mes (verificación rápida):")
        st.bar_chart(_md)

    csv_bytes = exportar_csv_fs(df_fs)
    nombre_csv = "sombras_sketchup_FS_horario.csv"
    st.download_button("⬇️ Descargar CSV de FS horario", csv_bytes, nombre_csv, "text/csv")

    if st.button("📤 Enviar a la Página 5 (Mismatch/Bypass)", type="primary"):
        st.session_state["csv_fs_sketchup_bytes"] = csv_bytes
        st.session_state["csv_fs_sketchup_nombre"] = nombre_csv
        st.success(
            "Listo — abre 🔀 **Mismatch** y oprime el botón «🌳 Usar el CSV generado en "
            "Sombras SketchUp». De ahí en adelante la cadena es la de siempre: "
            "bypass → E_ac corregida → Producción/Financiero."
        )
