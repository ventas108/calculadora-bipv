"""Página 8 — Presupuesto Detallado — Costos Reales del Proyecto BIPV."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Presupuesto BIPV", page_icon="💼", layout="wide")
st.title("💼 Presupuesto Detallado — Costos Reales del Proyecto")
st.caption("Plantilla editable por sección. Ajusta cantidades y precios USD según el proyecto.")

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

_EXCEL = "/var/www/bipv/calculadora-bipv/bipv_python/datos/insumos_template.xlsx"
_COLS  = ["Descripcion", "Ref", "Cantidad", "Unidad", "USD_un"]

@st.cache_data(ttl=3600)
def _cargar_secciones():
    df = pd.read_excel(_EXCEL, sheet_name="Hoja1", header=None, dtype=str)
    sec_map = [
        ("1. MATERIALES",           "perfileria"),
        ("2. MANO DE OBRA",         "mano_obra"),
        ("3. SISTEMA FOTOVOLTAICO", "sistema_fv"),
        ("4. INVERSOR",             "inversor"),
    ]
    secciones = {}
    current = None; hdr = False; rows = []
    for _, row in df.iterrows():
        first = str(row.iloc[0] or "").strip()
        hit = False
        for prefix, key in sec_map:
            if first.upper().startswith(prefix.upper()):
                if current and rows:
                    secciones[current] = pd.DataFrame(rows, columns=_COLS)
                current = key; hdr = False; rows = []; hit = True; break
        if hit: continue
        if not current: continue
        if not hdr:
            if first == "Descripcion": hdr = True
            continue
        if "SUBTOTAL" in first.upper():
            secciones[current] = pd.DataFrame(rows, columns=_COLS)
            current = None; rows = []; hdr = False; continue
        if first and first not in ("None", "nan", ""):
            try:    usd  = float(str(row.iloc[4]).replace(",",".")) if len(row) > 4 else 0.0
            except: usd  = 0.0
            try:    cant = float(str(row.iloc[2]).replace(",","."))
            except: cant = 1.0
            rows.append([first, str(row.iloc[1] or ""), cant, str(row.iloc[3] or "un"), usd])
    if current and rows:
        secciones[current] = pd.DataFrame(rows, columns=_COLS)
    for df2 in secciones.values():
        df2["Cantidad"] = pd.to_numeric(df2["Cantidad"], errors="coerce").fillna(1.0)
        df2["USD_un"]   = pd.to_numeric(df2["USD_un"],   errors="coerce").fillna(0.0)
    return secciones

try:
    _plantilla = _cargar_secciones()
except Exception as e:
    st.error(f"No se pudo leer insumos_template.xlsx: {e}"); _plantilla = {}

def _editar_seccion(key, label, inyectar=None):
    base = _plantilla.get(key, pd.DataFrame(columns=_COLS)).copy()
    if inyectar is not None and not inyectar.empty:
        base = pd.concat([base, inyectar], ignore_index=True)
    extras = st.session_state.get(f"extra_{key}", [])
    if extras:
        base = pd.concat([base, pd.DataFrame(extras, columns=_COLS)], ignore_index=True)
    base["Cantidad"] = pd.to_numeric(base["Cantidad"], errors="coerce").fillna(0)
    base["USD_un"]   = pd.to_numeric(base["USD_un"],   errors="coerce").fillna(0)
    base["Total USD"]= (base["Cantidad"] * base["USD_un"]).round(2)

    edited = st.data_editor(
        base,
        column_config={
            "Descripcion": st.column_config.TextColumn("Descripción", width="large"),
            "Ref":         st.column_config.TextColumn("Ref.", width="small"),
            "Cantidad":    st.column_config.NumberColumn("Cantidad", format="%.2f"),
            "Unidad":      st.column_config.TextColumn("Unidad", width="small"),
            "USD_un":      st.column_config.NumberColumn("USD/un", format="%.2f"),
            "Total USD":   st.column_config.NumberColumn("Total USD", disabled=True, format="%.2f"),
        },
        use_container_width=True, num_rows="dynamic", key=f"ed_{key}",
    )
    cant   = pd.to_numeric(edited["Cantidad"], errors="coerce").fillna(0)
    precio = pd.to_numeric(edited["USD_un"],   errors="coerce").fillna(0)
    total  = float((cant * precio).sum())
    c1, _ = st.columns(2)
    c1.metric(f"Subtotal {label}", f"USD {total:,.0f}", f"$ {total*tc/1e6:.2f} M COP", delta_color="off")

    with st.expander("➕ Agregar ítem nuevo"):
        a1,a2,a3,a4,a5 = st.columns([3,1,1,1,1])
        nd  = a1.text_input("Descripción", key=f"nd_{key}")
        nr  = a2.text_input("Ref.",        key=f"nr_{key}")
        nq  = a3.number_input("Cantidad",  min_value=0.0, value=1.0, key=f"nq_{key}")
        nu  = a4.text_input("Unidad",      value="un",   key=f"nu_{key}")
        np_ = a5.number_input("USD/un",    min_value=0.0, value=0.0, key=f"np_{key}")
        if st.button("Agregar", key=f"btn_{key}"):
            if nd:
                lst = st.session_state.get(f"extra_{key}", [])
                lst.append([nd, nr, nq, nu, np_])
                st.session_state[f"extra_{key}"] = lst
                st.rerun()
    return total

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
    st.markdown("**Equipos del catálogo — sincronizados con 📐 Dimensionamiento**")
    cat_rows = []
    if n_pan > 0:
        cp = c_pan if c_pan > 0 else st.number_input("Costo módulo (USD/un)", 0.0, 500.0, 65.0, 5.0, key="cp_man")
        cat_rows.append(["Módulos BIPV — catálogo", "MOD-CAT", float(n_pan), "un", cp])
    ci = c_inv if c_inv > 0 else st.number_input("Costo inversor (USD/un)", 0.0, 20000.0, 1850.0, 50.0, key="ci_man")
    cat_rows.append(["Inversor — catálogo", "INV-CAT", 1.0, "un", ci])
    df_cat = pd.DataFrame(cat_rows, columns=_COLS)
    sub5 = _editar_seccion("catalogo", "Catálogo", inyectar=df_cat)

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

st.session_state["presupuesto_capex_usd"]   = capex_total
st.session_state["presupuesto_sub_directo"] = sub_dir
st.success(f"✅ CAPEX **USD {capex_total:,.0f}** ($ {capex_total*tc/1e6:.2f} M COP) "
           f"→ 💰 Financiero lo usa automáticamente.")
