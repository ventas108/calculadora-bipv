"""Página 8 — Presupuesto Bancable BIPV — CAPEX + Costos Blandos + OPEX Anual."""
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Presupuesto BIPV", page_icon="💼", layout="wide")
st.title("💼 Presupuesto Bancable — CAPEX · Costos Blandos · OPEX")
st.caption(
    "Presupuesto completo para bancabilidad (P90). "
    "Columna **✔ Activo**: desmarca para excluir sin borrar. "
    "Agrega filas con **➕** al pie. Elimina con **Supr**. "
    "Cambios persisten durante la sesión."
)

# ── Encabezado del presupuesto ────────────────────────────────────────────────
with st.expander("📋 Encabezado del presupuesto", expanded=False):
    hc1, hc2, hc3 = st.columns(3)
    ppto_nombre   = hc1.text_input("Nombre del proyecto", value=st.session_state.get("nombre_proyecto","BIPV Proyecto"))
    ppto_vigencia = hc2.date_input("Vigencia del presupuesto", value=date.today())
    ppto_elaboro  = hc3.text_input("Elaboró", value="Innovación Química / SolTech Energy")
    st.caption(
        f"Presupuesto válido hasta **{ppto_vigencia}** · "
        "Los precios deben actualizarse si la TRM varía >5% o los insumos tienen nueva cotización."
    )

# ── TRM y datos del Dimensionamiento ─────────────────────────────────────────
tc = st.number_input("💱 TRM (COP/USD)", min_value=1000.0, max_value=10000.0,
    value=float(st.session_state.get("tipo_cambio", 4200.0)), step=50.0)
st.session_state["tipo_cambio"] = tc

n_pan   = int(st.session_state.get("N_paneles_final", 0))
p_stc   = float(st.session_state.get("P_stc_kW_sistema", 0.0))
c_pan   = float(st.session_state.get("costo_modulo_usd", 0.0))
c_inv   = float(st.session_state.get("costo_inversor_usd", 0.0))
area_m2 = float(st.session_state.get("area_fachada_m2", 0.0))

if n_pan > 0:
    st.info(
        f"📐 Dimensionamiento: **{n_pan} módulos** · **{p_stc:.2f} kWp** · "
        f"Panel **${c_pan:.0f}/un** · Inversor **${c_inv:.0f}/un**"
        + (f" · Área fachada **{area_m2:.1f} m²**" if area_m2 > 0 else "")
    )
else:
    st.warning("⚠️ Ejecuta 📐 Dimensionamiento primero para vincular equipos automáticamente.")

# ── Constantes ────────────────────────────────────────────────────────────────
_EXCEL    = "/var/www/bipv/calculadora-bipv/bipv_python/datos/insumos_template.xlsx"
_BASE_COLS = ["Descripcion", "Ref", "Cantidad", "Unidad", "USD_un"]
_COLS      = ["Activo"] + _BASE_COLS

# ── Plantillas por defecto para secciones nuevas ──────────────────────────────
_SOFT_DEFAULT = [
    # Descripcion                                        Ref        Cant  Uni    USD_un
    ["Ingeniería, diseño y memorias de cálculo",       "ENG-001",  1.0, "glb",   0.0],
    ["Estudio de sombreado y simulación BIPV",         "ENG-002",  1.0, "glb",   0.0],
    ["Registro UPME y trámites Ley 1715",              "TRM-001",  1.0, "glb",   0.0],
    ["Concepto de conexión — operador de red",         "TRM-002",  1.0, "glb",   0.0],
    ["Certificación RETIE / RITEL",                    "TRM-003",  1.0, "glb",   0.0],
    ["Gestión del proyecto — Project Manager",         "PM-001",   1.0, "glb",   0.0],
    ["Asesoría legal y estructuración financiera",     "LEG-001",  1.0, "glb",   0.0],
    ["Auditoría técnica independiente (ITA)",          "ITA-001",  1.0, "glb",   0.0],
    ["Póliza CAR — construcción todo riesgo",          "SEG-001",  1.0, "glb",   0.0],
    ["Gastos notariales, registros y licencias",       "LEG-002",  1.0, "glb",   0.0],
]
_OPEX_DEFAULT = [
    # Descripcion                                        Ref        Cant  Uni     USD_un (por año)
    ["O&M preventivo — visitas técnicas anuales",      "OM-001",   1.0, "año",   0.0],
    ["Limpieza de módulos (aprox. 4 veces/año)",       "OM-002",   4.0, "serv",  0.0],
    ["Seguro operativo — todo riesgo instalación",     "SEG-002",  1.0, "año",   0.0],
    ["Monitoreo remoto (plataforma Growatt/SCADA)",    "MON-001",  1.0, "año",   0.0],
    ["Revisión anual inversor y comunicaciones",       "OM-003",   1.0, "año",   0.0],
    ["Fondo de reposición inversor (año 12–15)",       "RES-001",  1.0, "año",   0.0],
    ["Fondo de reposición módulos / garantías",        "RES-002",  1.0, "año",   0.0],
    ["Administración y costos fijos anuales",          "ADM-001",  1.0, "año",   0.0],
]

# ── Carga plantilla desde Excel ───────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _cargar_secciones_raw():
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
            try:    usd  = float(str(row.iloc[4]).replace(",",".")) if len(row)>4 else 0.0
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

try:
    _secciones_raw = _cargar_secciones_raw()
except Exception as e:
    st.error(f"No se pudo leer insumos_template.xlsx: {e}")
    _secciones_raw = {}

# ── Función: inicializar DataFrame con Activo=True ────────────────────────────
def _df_con_activo(rows_or_df):
    if isinstance(rows_or_df, pd.DataFrame):
        raw = rows_or_df.copy()
    else:
        raw = pd.DataFrame(rows_or_df, columns=_BASE_COLS)
    raw.insert(0, "Activo", True)
    raw["Cantidad"] = pd.to_numeric(raw["Cantidad"], errors="coerce").fillna(0.0)
    raw["USD_un"]   = pd.to_numeric(raw["USD_un"],   errors="coerce").fillna(0.0)
    return raw

def _plantilla_con_activo(key, inyectar=None):
    raw = _secciones_raw.get(key, pd.DataFrame(columns=_BASE_COLS)).copy()
    if inyectar is not None and not inyectar.empty:
        raw = pd.concat([raw, inyectar], ignore_index=True)
    return _df_con_activo(raw)

# ── Editor genérico con persistencia + fuente de precios ─────────────────────
def _editar_seccion(key, label, inyectar=None, referencia_mercado=""):
    ss_key = f"df_sec_{key}"

    col_r, col_f = st.columns([2, 4])
    if col_r.button(f"↺ Resetear '{label}'", key=f"reset_{key}"):
        st.session_state.pop(ss_key, None)
        st.rerun()
    fuente = col_f.text_input(
        "Fuente de precios / cotización",
        value=st.session_state.get(f"fuente_{key}", ""),
        placeholder=referencia_mercado or "Ej.: Cotización proveedor XYZ, vigente a julio 2026",
        key=f"fuente_inp_{key}",
        label_visibility="collapsed",
    )
    st.session_state[f"fuente_{key}"] = fuente
    if fuente:
        st.caption(f"📎 Fuente: {fuente}")

    if ss_key not in st.session_state:
        st.session_state[ss_key] = _plantilla_con_activo(key, inyectar)

    df_actual = st.session_state[ss_key].copy()
    if "Activo" not in df_actual.columns:
        df_actual.insert(0, "Activo", True)
    df_actual["Cantidad"] = pd.to_numeric(df_actual["Cantidad"], errors="coerce").fillna(0.0)
    df_actual["USD_un"]   = pd.to_numeric(df_actual["USD_un"],   errors="coerce").fillna(0.0)
    df_actual["Total USD"] = (df_actual["Cantidad"] * df_actual["USD_un"]).round(2)

    edited = st.data_editor(
        df_actual,
        column_config={
            "Activo":      st.column_config.CheckboxColumn("✔", width="small",
                               help="Desmarca para excluir del total sin borrar"),
            "Descripcion": st.column_config.TextColumn("Descripción", width="large"),
            "Ref":         st.column_config.TextColumn("Ref.", width="small"),
            "Cantidad":    st.column_config.NumberColumn("Cantidad", format="%.2f"),
            "Unidad":      st.column_config.TextColumn("Unidad", width="small"),
            "USD_un":      st.column_config.NumberColumn("USD/un", format="%.2f"),
            "Total USD":   st.column_config.NumberColumn("Total USD", disabled=True, format="%.2f"),
        },
        use_container_width=True, num_rows="dynamic", key=f"ed_{key}",
    )
    edited["Cantidad"] = pd.to_numeric(edited["Cantidad"], errors="coerce").fillna(0.0)
    edited["USD_un"]   = pd.to_numeric(edited["USD_un"],   errors="coerce").fillna(0.0)
    edited["Total USD"] = (edited["Cantidad"] * edited["USD_un"]).round(2)
    if not edited.equals(st.session_state[ss_key]):
        st.session_state[ss_key] = edited

    activos  = edited["Activo"].fillna(False).astype(bool)
    total    = float((edited.loc[activos,  "Cantidad"] * edited.loc[activos,  "USD_un"]).sum())
    t_excl   = float((edited.loc[~activos, "Cantidad"] * edited.loc[~activos, "USD_un"]).sum())

    c1, c2, _ = st.columns([2, 2, 3])
    c1.metric(f"Subtotal {label}", f"USD {total:,.0f}", f"$ {total*tc/1e6:.2f} M COP", delta_color="off")
    if t_excl > 0:
        c2.metric("Excluidos", f"USD {t_excl:,.0f}", "no suma al total", delta_color="off")
    n_a = int(activos.sum()); n_i = int((~activos).sum())
    st.caption(f"📋 {len(edited)} ítems — {n_a} activos, {n_i} desactivados. ➕ agregar · Supr eliminar")
    return total

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "🔩 Perfilería y Estructura",
    "👷 Mano de Obra",
    "⚡ Sistema FV",
    "🔌 Inversor y Equipos Eléctricos",
    "📦 Equipos del Catálogo",
    "🧾 Costos Blandos",
    "📅 OPEX Anual",
])
t1,t2,t3,t4,t5,t6,t7 = tabs

with t1:
    st.markdown("##### Perfilería, estructura BIPV, soportes, fijaciones")
    sub1 = _editar_seccion("perfileria", "Perfilería",
        referencia_mercado="Ej.: Cotización Ternium/Acesco, julio 2026")

with t2:
    st.markdown("##### Mano de obra instalación, certificaciones, transporte")
    sub2 = _editar_seccion("mano_obra", "Mano de Obra",
        referencia_mercado="Ej.: Presupuesto contratista eléctrico, julio 2026")

with t3:
    st.markdown("##### Cables, protecciones, cajas de paso, puesta a tierra, monitoreo")
    sub3 = _editar_seccion("sistema_fv", "Sistema FV",
        referencia_mercado="Ej.: Lista de precios Leroy Merlin / EPM, julio 2026")

with t4:
    st.markdown("##### Tableros, breakers, protecciones AC, comunicaciones")
    sub4 = _editar_seccion("inversor", "Inversor/Eléctrico",
        referencia_mercado="Ej.: Cotización Schneider / ABB distribuidora, julio 2026")

with t5:
    if n_pan > 0:
        st.markdown(
            f"**Equipos principales** — {n_pan} módulos · {p_stc:.2f} kWp"
            + (f" · {area_m2:.1f} m²" if area_m2>0 else "")
        )
    else:
        st.info("Dimensionamiento no ejecutado — ingresa cantidad y precio manualmente.")

    cat_rows = []
    if n_pan > 0:
        cp = c_pan if c_pan > 0 else st.number_input(
            "Costo módulo (USD/un)", 0.0, 2000.0, 65.0, 5.0, key="cp_man")
        cat_rows.append(["Módulos BIPV — catálogo", "MOD-CAT", float(n_pan), "un", cp])
    else:
        col_m1, col_m2 = st.columns(2)
        n_man  = col_m1.number_input("Cantidad de módulos", min_value=0, value=0, step=1, key="n_pan_man")
        cp_man = col_m2.number_input("Costo módulo (USD/un)", 0.0, 2000.0, 0.0, 5.0, key="cp_man")
        cat_rows.append(["Módulos BIPV", "MOD-MAN", float(n_man), "un", cp_man])

    ci = c_inv if c_inv > 0 else st.number_input(
        "Costo inversor (USD/un)", 0.0, 20000.0, 1850.0, 50.0, key="ci_man")
    cat_rows.append(["Inversor — catálogo", "INV-CAT", 1.0, "un", ci])

    _bat = st.session_state.get("bateria_dim")
    _bat_nom = st.session_state.get("bateria_nombre", "Batería")
    if _bat and _bat.get("N_baterias") and _bat.get("costo_unitario_usd"):
        cat_rows.append([f"Baterías — {_bat_nom}", "BAT-CAT",
            float(_bat["N_baterias"]), "un", float(_bat.get("costo_unitario_usd") or 0)])
    elif _bat and _bat.get("N_baterias"):
        st.caption(f"🔋 {int(_bat['N_baterias'])} und. {_bat_nom} — agrega precio manualmente")

    df_iny = pd.DataFrame(cat_rows, columns=_BASE_COLS)
    # Inicializar sección si aún no existe (el reset lo maneja _editar_seccion internamente)
    if "df_sec_catalogo" not in st.session_state:
        st.session_state.pop("df_sec_catalogo", None)
    sub5 = _editar_seccion("catalogo", "Catálogo", inyectar=df_iny,
        referencia_mercado="Ej.: Cotización JA Solar / Growatt distribuidor, julio 2026")

with t6:
    st.markdown("""
    ##### Costos blandos — ingeniería, trámites, legal, PM, seguros construcción
    > 💡 Referencia Colombia: costos blandos = **8–18% del CAPEX directo**.
    > ITA obligatorio para financiamiento bancario > USD 200k.
    > PM típico: 3–5% CAPEX. Póliza CAR: 0.4–0.6% CAPEX.
    """)

    ss_soft = "df_sec_soft"
    col_rs, col_fs = st.columns([2, 4])
    if col_rs.button("↺ Resetear 'Costos Blandos'", key="reset_soft"):
        st.session_state.pop(ss_soft, None)
        st.rerun()
    fuente_s = col_fs.text_input("Fuente / cotización soft costs",
        value=st.session_state.get("fuente_soft",""),
        placeholder="Ej.: Propuesta consultoría XYZ, cotización póliza ABC, julio 2026",
        key="fuente_inp_soft", label_visibility="collapsed")
    st.session_state["fuente_soft"] = fuente_s

    if ss_soft not in st.session_state:
        st.session_state[ss_soft] = _df_con_activo(_SOFT_DEFAULT)

    df_soft = st.session_state[ss_soft].copy()
    if "Activo" not in df_soft.columns:
        df_soft.insert(0, "Activo", True)
    df_soft["Cantidad"] = pd.to_numeric(df_soft["Cantidad"], errors="coerce").fillna(0.0)
    df_soft["USD_un"]   = pd.to_numeric(df_soft["USD_un"],   errors="coerce").fillna(0.0)
    df_soft["Total USD"] = (df_soft["Cantidad"] * df_soft["USD_un"]).round(2)

    ed_soft = st.data_editor(df_soft,
        column_config={
            "Activo":      st.column_config.CheckboxColumn("✔", width="small"),
            "Descripcion": st.column_config.TextColumn("Descripción", width="large"),
            "Ref":         st.column_config.TextColumn("Ref.", width="small"),
            "Cantidad":    st.column_config.NumberColumn("Cantidad", format="%.2f"),
            "Unidad":      st.column_config.TextColumn("Unidad", width="small"),
            "USD_un":      st.column_config.NumberColumn("USD/un o USD/glb", format="%.2f"),
            "Total USD":   st.column_config.NumberColumn("Total USD", disabled=True, format="%.2f"),
        },
        use_container_width=True, num_rows="dynamic", key="ed_soft",
    )
    ed_soft["Cantidad"] = pd.to_numeric(ed_soft["Cantidad"], errors="coerce").fillna(0.0)
    ed_soft["USD_un"]   = pd.to_numeric(ed_soft["USD_un"],   errors="coerce").fillna(0.0)
    ed_soft["Total USD"] = (ed_soft["Cantidad"] * ed_soft["USD_un"]).round(2)
    if not ed_soft.equals(st.session_state[ss_soft]):
        st.session_state[ss_soft] = ed_soft

    act_s  = ed_soft["Activo"].fillna(False).astype(bool)
    sub6   = float((ed_soft.loc[act_s, "Cantidad"] * ed_soft.loc[act_s, "USD_un"]).sum())
    excl_s = float((ed_soft.loc[~act_s,"Cantidad"] * ed_soft.loc[~act_s,"USD_un"]).sum())

    cs1, cs2, _ = st.columns([2, 2, 3])
    cs1.metric("Subtotal Costos Blandos", f"USD {sub6:,.0f}", f"$ {sub6*tc/1e6:.2f} M COP", delta_color="off")
    if excl_s > 0:
        cs2.metric("Excluidos", f"USD {excl_s:,.0f}", "no suma al total", delta_color="off")
    st.caption(f"📋 {len(ed_soft)} ítems — {int(act_s.sum())} activos, {int((~act_s).sum())} desactivados.")

with t7:
    st.markdown("""
    ##### OPEX anual — costos de operación y mantenimiento durante la vida útil del sistema
    > 💡 Referencia Colombia BIPV: **USD 8–15/kWp/año** (O&M + limpieza + seguro).
    > El OPEX total anual se envía automáticamente a 💰 Financiero para el flujo de caja a 25 años.
    > **USD/un en esta pestaña = costo anual del ítem** (no unitario).
    """)

    ss_opex = "df_sec_opex"
    col_ro, col_fo = st.columns([2, 4])
    if col_ro.button("↺ Resetear 'OPEX'", key="reset_opex"):
        st.session_state.pop(ss_opex, None)
        st.rerun()
    fuente_o = col_fo.text_input("Fuente / cotización OPEX",
        value=st.session_state.get("fuente_opex",""),
        placeholder="Ej.: Contrato O&M empresa Z, póliza seguro W, julio 2026",
        key="fuente_inp_opex", label_visibility="collapsed")
    st.session_state["fuente_opex"] = fuente_o

    if ss_opex not in st.session_state:
        st.session_state[ss_opex] = _df_con_activo(_OPEX_DEFAULT)

    df_opex = st.session_state[ss_opex].copy()
    if "Activo" not in df_opex.columns:
        df_opex.insert(0, "Activo", True)
    df_opex["Cantidad"] = pd.to_numeric(df_opex["Cantidad"], errors="coerce").fillna(0.0)
    df_opex["USD_un"]   = pd.to_numeric(df_opex["USD_un"],   errors="coerce").fillna(0.0)
    df_opex["Total USD"] = (df_opex["Cantidad"] * df_opex["USD_un"]).round(2)

    ed_opex = st.data_editor(df_opex,
        column_config={
            "Activo":      st.column_config.CheckboxColumn("✔", width="small"),
            "Descripcion": st.column_config.TextColumn("Descripción", width="large"),
            "Ref":         st.column_config.TextColumn("Ref.", width="small"),
            "Cantidad":    st.column_config.NumberColumn("Cant.", format="%.2f"),
            "Unidad":      st.column_config.TextColumn("Unidad", width="small",
                               help="'año' para costo fijo anual, 'serv' para por visita, etc."),
            "USD_un":      st.column_config.NumberColumn("USD/año (unitario)", format="%.2f",
                               help="Costo unitario anual del ítem. Total = Cant × USD/año"),
            "Total USD":   st.column_config.NumberColumn("Total USD/año", disabled=True, format="%.2f"),
        },
        use_container_width=True, num_rows="dynamic", key="ed_opex",
    )
    ed_opex["Cantidad"] = pd.to_numeric(ed_opex["Cantidad"], errors="coerce").fillna(0.0)
    ed_opex["USD_un"]   = pd.to_numeric(ed_opex["USD_un"],   errors="coerce").fillna(0.0)
    ed_opex["Total USD"] = (ed_opex["Cantidad"] * ed_opex["USD_un"]).round(2)
    if not ed_opex.equals(st.session_state[ss_opex]):
        st.session_state[ss_opex] = ed_opex

    act_o  = ed_opex["Activo"].fillna(False).astype(bool)
    sub7   = float((ed_opex.loc[act_o,"Cantidad"] * ed_opex.loc[act_o,"USD_un"]).sum())
    excl_o = float((ed_opex.loc[~act_o,"Cantidad"] * ed_opex.loc[~act_o,"USD_un"]).sum())

    co1, co2, co3, _ = st.columns([2, 2, 2, 2])
    co1.metric("OPEX Total Anual", f"USD {sub7:,.0f}/año",
               f"$ {sub7*tc/1e6:.3f} M COP/año", delta_color="off")
    if p_stc > 0:
        co2.metric("OPEX / kWp", f"USD {sub7/p_stc:.0f}/kWp·año",
                   "Ref: USD 8–15/kWp·año", delta_color="off")
    if excl_o > 0:
        co3.metric("Excluidos", f"USD {excl_o:,.0f}/año", "no suma al total", delta_color="off")
    st.caption(f"📋 {len(ed_opex)} ítems — {int(act_o.sum())} activos. → Este valor reemplaza el slider O&M en 💰 Financiero.")

# ══════════════════════════════════════════════════════════════════════════════
# RESUMEN CAPEX + CONTINGENCIAS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📊 Resumen CAPEX Total del Proyecto")

capex_directo = sub1 + sub2 + sub3 + sub4 + sub5
capex_base    = capex_directo + sub6  # directo + costos blandos

df_res = pd.DataFrame([
    {"Categoría": "🔩 Perfilería y Estructura",              "USD": sub1, "COP (M)": round(sub1*tc/1e6,2), "% CAPEX base": 0.0},
    {"Categoría": "👷 Mano de Obra y Servicios",             "USD": sub2, "COP (M)": round(sub2*tc/1e6,2), "% CAPEX base": 0.0},
    {"Categoría": "⚡ Sistema FV (cables, protecciones)",    "USD": sub3, "COP (M)": round(sub3*tc/1e6,2), "% CAPEX base": 0.0},
    {"Categoría": "🔌 Inversor y Equipos Eléctricos",        "USD": sub4, "COP (M)": round(sub4*tc/1e6,2), "% CAPEX base": 0.0},
    {"Categoría": "📦 Módulos + Inversor + Baterías",        "USD": sub5, "COP (M)": round(sub5*tc/1e6,2), "% CAPEX base": 0.0},
    {"Categoría": "🧾 Costos Blandos (soft costs)",          "USD": sub6, "COP (M)": round(sub6*tc/1e6,2), "% CAPEX base": 0.0},
])
if capex_base > 0:
    df_res["% CAPEX base"] = (df_res["USD"] / capex_base * 100).round(1)

# Fila subtotal
df_res.loc[len(df_res)] = {"Categoría": "🔵 CAPEX Base (directo + blandos)",
    "USD": capex_base, "COP (M)": round(capex_base*tc/1e6,2),
    "% CAPEX base": 100.0}

st.dataframe(
    df_res.style
        .format({"USD":"{:,.0f}","COP (M)":"{:.2f}","% CAPEX base":"{:.1f}%"})
        .apply(lambda r: ["font-weight:bold; background:#EAF4FB"]*len(r) if "CAPEX Base" in str(r["Categoría"]) else [""]*len(r), axis=1),
    use_container_width=True, hide_index=True,
)

st.markdown("##### ⚙️ Contingencias")
cc1, cc2, cc3 = st.columns(3)
ind_pct   = cc1.slider("Costos indirectos — AUI, administración, utilidad (%)",
                        2, 25, 12, 1, help="Típico Colombia: 10–18%") / 100
c_tec_pct = cc2.slider("Contingencia técnica — riesgo instalación BIPV fachada (%)",
                        0, 20, 10, 1, help="BIPV de fachada: 8–15%. Suelo convencional: 5–8%") / 100
c_pre_pct = cc3.slider("Contingencia de precios — volatilidad materiales (%)",
                        0, 10,  5, 1, help="Recomendado: 3–7% para proyectos con TRM expuesta") / 100

indirectos   = capex_base * ind_pct
c_tec        = capex_base * c_tec_pct
c_pre        = capex_base * c_pre_pct
capex_total  = capex_base + indirectos + c_tec + c_pre

m1,m2,m3,m4 = st.columns(4)
m1.metric("CAPEX Base",        f"USD {capex_base:,.0f}",    f"$ {capex_base*tc/1e6:.2f} M COP",    delta_color="off")
m2.metric("Indirectos",        f"USD {indirectos:,.0f}",    f"{ind_pct*100:.0f}% CAPEX base",      delta_color="off")
m3.metric("Contingencias",     f"USD {c_tec+c_pre:,.0f}",   f"Téc {c_tec_pct*100:.0f}% + Pre {c_pre_pct*100:.0f}%", delta_color="off")
m4.metric("✅ CAPEX TOTAL",    f"USD {capex_total:,.0f}",    f"$ {capex_total*tc/1e6:.2f} M COP",   delta_color="off")

# ── KPIs de bancabilidad ──────────────────────────────────────────────────────
st.markdown("##### 📐 KPIs de bancabilidad")
k1, k2, k3, k4 = st.columns(4)

if p_stc > 0:
    costo_wp = capex_total / p_stc / 1000
    k1.metric("Costo / Wp", f"USD {costo_wp:.2f}/Wp",
              f"$ {costo_wp*tc*1000:,.0f} COP/Wp", delta_color="off")
    if costo_wp > 5.0:
        st.warning(f"⚠️ USD {costo_wp:.2f}/Wp — muy alto. Ref. BIPV fachada Colombia: USD 1.8–4.0/Wp. "
                   f"Verifica que todos los precios estén en USD (no COP).")
    elif costo_wp > 3.5:
        st.info(f"ℹ️ USD {costo_wp:.2f}/Wp — rango alto. Ref.: USD 1.8–3.5/Wp para BIPV fachada.")

if area_m2 > 0:
    costo_m2 = capex_total / area_m2
    k2.metric("Costo / m²", f"USD {costo_m2:.0f}/m²",
              f"$ {costo_m2*tc/1e3:.1f} k COP/m²", delta_color="off")
    if costo_m2 > 400:
        st.info(f"ℹ️ USD {costo_m2:.0f}/m² — revisa si la subestructura o los módulos tienen precios altos. "
                f"Ref. BIPV: USD 180–350/m².")

if sub7 > 0 and capex_total > 0:
    opex_ratio = sub7 / capex_total * 100
    k3.metric("OPEX / CAPEX anual", f"{opex_ratio:.2f}%",
              "Ref.: 1.0–2.5%/año", delta_color="off")
    if opex_ratio > 3.0:
        st.warning(f"⚠️ OPEX/CAPEX = {opex_ratio:.1f}% — alto. Revisa los fondos de reposición o seguros.")

if p_stc > 0 and sub7 > 0:
    k4.metric("OPEX / kWp·año", f"USD {sub7/p_stc:.0f}",
              "Ref.: USD 8–15/kWp·año", delta_color="off")

# ── Costos blandos como % del directo ────────────────────────────────────────
if sub6 > 0 and capex_directo > 0:
    soft_pct = sub6 / capex_directo * 100
    st.caption(
        f"🧾 Costos blandos = **{soft_pct:.1f}% del CAPEX directo** "
        f"(referencia Colombia: 8–18%)"
    )

# ── Fracción de equipos para Ley 1715 ────────────────────────────────────────
_frac_eq = (sub3 + sub4 + sub5) / capex_total if capex_total > 0 else 0.65

# ── Publicar en session_state ─────────────────────────────────────────────────
st.session_state["presupuesto_capex_usd"]         = capex_total
st.session_state["presupuesto_capex_directo"]      = capex_directo
st.session_state["presupuesto_capex_blando"]       = sub6
st.session_state["presupuesto_sub_directo"]        = capex_directo   # compat.
st.session_state["presupuesto_fraccion_equipos"]   = _frac_eq
st.session_state["presupuesto_opex_anual_usd"]     = sub7            # ← nuevo → Financiero

st.success(
    f"✅ **CAPEX TOTAL USD {capex_total:,.0f}** ($ {capex_total*tc/1e6:.2f} M COP) "
    f"→ 💰 Financiero lo usa automáticamente. "
    f"Ley 1715 frac. equipos: **{_frac_eq*100:.0f}%**"
    + (f" · **OPEX USD {sub7:,.0f}/año** enviado al flujo de caja." if sub7 > 0 else
       " · ⚠️ OPEX = USD 0 — completa la pestaña 📅 OPEX Anual.")
)
