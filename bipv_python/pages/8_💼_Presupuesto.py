"""Página 8 — Presupuesto Detallado — Costos Reales del Proyecto BIPV."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Presupuesto BIPV", page_icon="💼", layout="wide")
st.title("💼 Presupuesto Detallado — Costos Reales del Proyecto")
st.caption(
    "Marca o desmarca ítems con la columna **Activo** para incluirlos o excluirlos del total. "
    "Agrega filas con ➕ en la esquina inferior del editor. Elimina filas seleccionando la fila y "
    "presionando **Suprimir**. Los cambios se mantienen mientras la sesión esté abierta."
)

tc = st.number_input("💱 TRM (COP/USD)", min_value=1000.0, max_value=10000.0,
    value=float(st.session_state.get("tipo_cambio", 3600.0)), step=50.0)
st.session_state["tipo_cambio"] = tc

n_pan = int(st.session_state.get("N_paneles_final", 0))
p_stc = float(st.session_state.get("P_stc_kW_sistema", 0.0))
c_pan = float(st.session_state.get("costo_modulo_usd", 0.0))
c_inv = float(st.session_state.get("costo_inversor_usd", 0.0))

if n_pan > 0:
    st.info(f"📐 Dimensionamiento: **{n_pan} módulos** · **{p_stc:.2f} kWp** · "
            f"Panel **${c_pan:.0f}/un** · Inversor **${c_inv:.0f}/un**")
else:
    st.warning("⚠️ Ejecuta 📐 Dimensionamiento primero para vincular equipos automáticamente.")

# ── Constantes ──────────────────────────────────────────────────────────────
_EXCEL = "/var/www/bipv/calculadora-bipv/bipv_python/datos/insumos_template.xlsx"
_COLS  = ["Activo", "Descripcion", "Ref", "Cantidad", "Unidad", "USD_un"]

# ── Carga plantilla desde Excel ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _cargar_secciones_raw():
    """Lee el Excel y devuelve dict {key: DataFrame sin columna Activo}."""
    _BASE_COLS = ["Descripcion", "Ref", "Cantidad", "Unidad", "USD_un"]
    sec_map = [
        ("1. MATERIALES",           "perfileria"),
        ("2. MANO DE OBRA",         "mano_obra"),
        ("3. SISTEMA FOTOVOLTAICO", "sistema_fv"),
        ("4. INVERSOR",             "inversor"),
    ]
    df = pd.read_excel(_EXCEL, sheet_name="Hoja1", header=None, dtype=str)
    secciones = {}
    current = None; hdr = False; rows = []
    for _, row in df.iterrows():
        first = str(row.iloc[0] or "").strip()
        hit = False
        for prefix, key in sec_map:
            if first.upper().startswith(prefix.upper()):
                if current and rows:
                    secciones[current] = pd.DataFrame(rows, columns=_BASE_COLS)
                current = key; hdr = False; rows = []; hit = True; break
        if hit: continue
        if not current: continue
        if not hdr:
            if first == "Descripcion": hdr = True
            continue
        if "SUBTOTAL" in first.upper():
            secciones[current] = pd.DataFrame(rows, columns=_BASE_COLS)
            current = None; rows = []; hdr = False; continue
        if first and first not in ("None", "nan", ""):
            try:    usd  = float(str(row.iloc[4]).replace(",",".")) if len(row) > 4 else 0.0
            except: usd  = 0.0
            try:    cant = float(str(row.iloc[2]).replace(",","."))
            except: cant = 1.0
            rows.append([first, str(row.iloc[1] or ""), cant, str(row.iloc[3] or "un"), usd])
    if current and rows:
        secciones[current] = pd.DataFrame(rows, columns=_BASE_COLS)
    for df2 in secciones.values():
        df2["Cantidad"] = pd.to_numeric(df2["Cantidad"], errors="coerce").fillna(1.0)
        df2["USD_un"]   = pd.to_numeric(df2["USD_un"],   errors="coerce").fillna(0.0)
    return secciones


def _plantilla_con_activo(key, inyectar=None):
    """Devuelve DataFrame base con columna Activo=True, más inyección opcional."""
    raw = _secciones_raw.get(key, pd.DataFrame(columns=["Descripcion","Ref","Cantidad","Unidad","USD_un"])).copy()
    if inyectar is not None and not inyectar.empty:
        raw = pd.concat([raw, inyectar], ignore_index=True)
    raw.insert(0, "Activo", True)
    raw["Cantidad"] = pd.to_numeric(raw["Cantidad"], errors="coerce").fillna(0.0)
    raw["USD_un"]   = pd.to_numeric(raw["USD_un"],   errors="coerce").fillna(0.0)
    return raw


try:
    _secciones_raw = _cargar_secciones_raw()
except Exception as e:
    st.error(f"No se pudo leer insumos_template.xlsx: {e}")
    _secciones_raw = {}

# ── Editor de sección con persistencia en session_state ─────────────────────
def _editar_seccion(key, label, inyectar=None):
    ss_key = f"df_sec_{key}"

    col_reset, _ = st.columns([1, 5])
    if col_reset.button(f"↺ Resetear '{label}' a plantilla", key=f"reset_{key}"):
        if ss_key in st.session_state:
            del st.session_state[ss_key]
        st.rerun()

    # Inicializar desde plantilla si es la primera vez o fue reseteado
    if ss_key not in st.session_state:
        st.session_state[ss_key] = _plantilla_con_activo(key, inyectar)

    df_actual = st.session_state[ss_key].copy()

    # Asegurar columnas correctas (por si el df persistido no tiene Activo)
    if "Activo" not in df_actual.columns:
        df_actual.insert(0, "Activo", True)
    df_actual["Cantidad"] = pd.to_numeric(df_actual["Cantidad"], errors="coerce").fillna(0.0)
    df_actual["USD_un"]   = pd.to_numeric(df_actual["USD_un"],   errors="coerce").fillna(0.0)
    df_actual["Total USD"] = (df_actual["Cantidad"] * df_actual["USD_un"]).round(2)

    edited = st.data_editor(
        df_actual,
        column_config={
            "Activo":    st.column_config.CheckboxColumn("✔ Activo", width="small",
                            help="Desmarca para excluir este ítem del total sin borrarlo"),
            "Descripcion": st.column_config.TextColumn("Descripción", width="large"),
            "Ref":         st.column_config.TextColumn("Ref.", width="small"),
            "Cantidad":    st.column_config.NumberColumn("Cantidad", format="%.2f"),
            "Unidad":      st.column_config.TextColumn("Unidad", width="small"),
            "USD_un":      st.column_config.NumberColumn("USD/un", format="%.2f"),
            "Total USD":   st.column_config.NumberColumn("Total USD", disabled=True, format="%.2f"),
        },
        use_container_width=True,
        num_rows="dynamic",   # ← el usuario puede agregar filas con ➕ y eliminar con Supr
        key=f"ed_{key}",
    )

    # Recalcular totales y persistir
    edited["Cantidad"] = pd.to_numeric(edited["Cantidad"], errors="coerce").fillna(0.0)
    edited["USD_un"]   = pd.to_numeric(edited["USD_un"],   errors="coerce").fillna(0.0)
    edited["Total USD"] = (edited["Cantidad"] * edited["USD_un"]).round(2)
    # Solo guardar si hubo cambio real (evitar ciclos de rerun)
    if not edited.equals(st.session_state[ss_key]):
        st.session_state[ss_key] = edited

    # Total solo de filas activas
    activos = edited["Activo"].fillna(False).astype(bool)
    cant    = edited.loc[activos, "Cantidad"]
    precio  = edited.loc[activos, "USD_un"]
    total   = float((cant * precio).sum())
    total_inactivo = float((edited.loc[~activos, "Cantidad"] * edited.loc[~activos, "USD_un"]).sum())

    c1, c2, _ = st.columns([2, 2, 3])
    c1.metric(f"Subtotal {label} (activos)",
              f"USD {total:,.0f}", f"$ {total*tc/1e6:.2f} M COP", delta_color="off")
    if total_inactivo > 0:
        c2.metric("Ítems desactivados (excluidos)",
                  f"USD {total_inactivo:,.0f}", "no suma al total", delta_color="off")

    n_activos   = int(activos.sum())
    n_inactivos = int((~activos).sum())
    st.caption(
        f"📋 **{len(edited)} ítems** — {n_activos} activos, {n_inactivos} desactivados. "
        "Agrega filas nuevas con el botón ➕ al pie de la tabla. "
        "Elimina una fila seleccionándola y pulsando la tecla **Supr / Delete**."
    )

    return total

# ── Tabs ────────────────────────────────────────────────────────────────────
t1,t2,t3,t4,t5 = st.tabs([
    "🔩 Perfilería y Estructura",
    "👷 Mano de Obra",
    "⚡ Sistema FV",
    "🔌 Inversor y Equipos Eléctricos",
    "📦 Equipos del Catálogo",
])
with t1: sub1 = _editar_seccion("perfileria", "Perfilería")
with t2: sub2 = _editar_seccion("mano_obra",  "Mano de Obra")
with t3: sub3 = _editar_seccion("sistema_fv", "Sistema FV")
with t4: sub4 = _editar_seccion("inversor",   "Inversor/Eléctrico")
with t5:
    if n_pan > 0:
        st.markdown(
            f"**Equipos del catálogo** — sincronizados con 📐 Dimensionamiento "
            f"({n_pan} módulos · {p_stc:.2f} kWp)"
        )
    else:
        st.info(
            "📐 Dimensionamiento no ejecutado en esta sesión. "
            "Puedes ingresar los valores manualmente — la tabla se editará directamente."
        )
    cat_rows = []

    # ── Módulos: siempre presentes ──────────────────────────────────────────
    if n_pan > 0:
        # Cantidad auto desde Dimensionamiento; precio manual si no viene del catálogo
        cp = c_pan if c_pan > 0 else st.number_input(
            "Costo módulo (USD/un)", 0.0, 2000.0, 65.0, 5.0, key="cp_man")
        cat_rows.append(["Módulos BIPV — catálogo", "MOD-CAT", float(n_pan), "un", cp])
    else:
        # Sin Dimensionamiento: el usuario ingresa cantidad y precio manualmente
        col_m1, col_m2 = st.columns(2)
        n_man = col_m1.number_input("Cantidad de módulos", min_value=0, value=0, step=1, key="n_pan_man")
        cp_man = col_m2.number_input("Costo módulo (USD/un)", min_value=0.0, value=0.0, step=5.0, key="cp_man")
        cat_rows.append(["Módulos BIPV", "MOD-MAN", float(n_man), "un", cp_man])

    # ── Inversor: siempre presente ──────────────────────────────────────────
    ci = c_inv if c_inv > 0 else st.number_input(
        "Costo inversor (USD/un)", 0.0, 20000.0, 1850.0, 50.0, key="ci_man")
    cat_rows.append(["Inversor — catálogo", "INV-CAT", 1.0, "un", ci])

    _bat_dim_pres = st.session_state.get("bateria_dim")
    _bat_nom_pres = st.session_state.get("bateria_nombre", "Batería")
    if (_bat_dim_pres and _bat_dim_pres.get("N_baterias")
            and _bat_dim_pres.get("costo_unitario_usd")):
        cat_rows.append([
            f"Baterías — {_bat_nom_pres}", "BAT-CAT",
            float(_bat_dim_pres["N_baterias"]), "un",
            float(_bat_dim_pres.get("costo_unitario_usd") or 0),
        ])
    elif _bat_dim_pres and _bat_dim_pres.get("N_baterias"):
        st.caption(
            f"🔋 {int(_bat_dim_pres['N_baterias'])} und. de **{_bat_nom_pres}** "
            "dimensionadas en Pág. 11 — sin costo en catálogo, agregue manualmente si desea."
        )

    df_iny = pd.DataFrame(cat_rows, columns=["Descripcion","Ref","Cantidad","Unidad","USD_un"])

    # El catálogo re-inyecta equipos del Dimensionamiento al resetear
    ss_cat = "df_sec_catalogo"
    if ss_cat not in st.session_state or st.button("↺ Resetear 'Catálogo' a plantilla", key="reset_catalogo"):
        if ss_cat in st.session_state:
            del st.session_state[ss_cat]
    sub5 = _editar_seccion("catalogo", "Catálogo", inyectar=df_iny)

# ── Resumen CAPEX ────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Resumen CAPEX Total del Proyecto")
df_res = pd.DataFrame([
    {"Sección": "Perfilería y Estructura",           "USD": sub1, "COP (M)": round(sub1*tc/1e6,2)},
    {"Sección": "Mano de Obra y Servicios",          "USD": sub2, "COP (M)": round(sub2*tc/1e6,2)},
    {"Sección": "Sistema FV (cables, protecciones)", "USD": sub3, "COP (M)": round(sub3*tc/1e6,2)},
    {"Sección": "Inversor y Equipos Eléctricos",     "USD": sub4, "COP (M)": round(sub4*tc/1e6,2)},
    {"Sección": "Módulos + Inversor (catálogo)",     "USD": sub5, "COP (M)": round(sub5*tc/1e6,2)},
])
sub_dir = df_res["USD"].sum()
st.dataframe(df_res.style.format({"USD":"{:,.0f}","COP (M)":"{:.2f}"}), use_container_width=True)

col1, col2 = st.columns(2)
ind_pct  = col1.slider("Costos indirectos (%)",          5, 30, 15, 1) / 100
impr_pct = col2.slider("Imprevistos y contingencia (%)", 0, 20,  5, 1) / 100
indirectos  = sub_dir * ind_pct
imprevistos = (sub_dir + indirectos) * impr_pct
capex_total = sub_dir + indirectos + imprevistos

m1,m2,m3 = st.columns(3)
m1.metric("Subtotal directo",   f"USD {sub_dir:,.0f}",    f"$ {sub_dir*tc/1e6:.2f} M COP",    delta_color="off")
m2.metric("Indirectos + Impr.", f"USD {indirectos+imprevistos:,.0f}",
          f"$ {(indirectos+imprevistos)*tc/1e6:.2f} M COP", delta_color="off")
m3.metric("✅ CAPEX TOTAL",     f"USD {capex_total:,.0f}", f"$ {capex_total*tc/1e6:.2f} M COP", delta_color="off")

if p_stc > 0:
    st.metric("Costo por Wp", f"USD {capex_total/p_stc/1000:.2f}/Wp",
              delta=f"$ {capex_total*tc/p_stc/1000:,.0f} COP/Wp", delta_color="off")

_frac_eq = (sub3 + sub4 + sub5) / capex_total if capex_total > 0 else 0.65

st.session_state["presupuesto_capex_usd"]       = capex_total
st.session_state["presupuesto_sub_directo"]      = sub_dir
st.session_state["presupuesto_fraccion_equipos"] = _frac_eq

if p_stc > 0:
    costo_wp = capex_total / p_stc / 1000
    if costo_wp > 5.0:
        st.warning(
            f"⚠️ **Costo/Wp elevado: USD {costo_wp:.2f}/Wp** — "
            f"la referencia para BIPV instalado en Colombia es **USD 1.5–4.0/Wp**. "
            f"Verifica que los precios en todas las pestañas estén en **USD**, no en COP. "
            f"Si el Excel tiene precios en pesos, divídelos por la TRM ({tc:,.0f} COP/USD) "
            f"antes de ingresarlos."
        )
    elif costo_wp > 3.0:
        st.info(
            f"ℹ️ Costo/Wp: USD {costo_wp:.2f}/Wp — rango alto para BIPV "
            f"(referencia: USD 1.5–4.0/Wp). Revisa si Mano de Obra o Perfilería "
            f"incluyen IVA o tienen precios en COP."
        )

st.success(
    f"✅ CAPEX **USD {capex_total:,.0f}** ($ {capex_total*tc/1e6:.2f} M COP) "
    f"→ 💰 Financiero lo usa automáticamente. "
    f"Fracción equipos Ley 1715: **{_frac_eq*100:.0f}%**"
)
