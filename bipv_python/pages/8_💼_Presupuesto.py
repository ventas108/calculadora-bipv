"""Página 8 — Presupuesto Bancable BIPV — CAPEX + Costos Blandos + OPEX Anual."""
import streamlit as st
import pandas as pd
from datetime import date, datetime
from calculos.trm_utils import init_trm, trm_widget


from calculos import presupuesto_store as pstore


def _marcar_fuente_capex(fuente: str) -> None:
    """Registra la FUENTE activa del CAPEX y la marca de tiempo de la última
    escritura de ``presupuesto_capex_usd`` en session_state.

    Esto permite que 💰 Financiero muestre explícitamente el origen del CAPEX
    ("Estimación Rápida", "Presupuesto detallado" o "Manual") y la hora de la
    última actualización. La marca de tiempo se escribe en el MISMO rerun en
    que cambia el CAPEX, para que ambas páginas queden siempre coherentes.
    """
    st.session_state["presupuesto_fuente"] = fuente
    st.session_state["presupuesto_capex_ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Presupuesto BIPV", page_icon="💼", layout="wide")

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion
bloquear_traduccion()
init_trm()   # fetch TRM del API en primera carga; garantiza session_state["tipo_cambio"]
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
    ppto_elaboro  = hc3.text_input("Elaboró", value="Innovación Química")
    st.caption(
        f"Presupuesto válido hasta **{ppto_vigencia}** · "
        "Los precios deben actualizarse si la TRM varía >5% o los insumos tienen nueva cotización."
    )

# ── TRM sincronizada — widget compartido con Financiero ──────────────────────
tc = trm_widget("ppto")

# ── #89 — Pestaña nueva / recarga: restaurar kWp y N_paneles desde disco ─────
# para que la Estimación Rápida no arranque con defaults falsos.
if not st.session_state.get("produccion_ok"):
    from calculos.persistencia_resultados import restaurar_resultados_produccion
    if restaurar_resultados_produccion(st.session_state):
        st.info("📂 **Datos restaurados del proyecto guardado** (kWp y n.º de paneles "
                "de la última simulación de Producción).", icon="📂")

n_pan   = int(st.session_state.get("N_paneles_final", 0))
p_stc   = float(st.session_state.get("P_stc_kW_sistema", 0.0))
c_pan   = float(st.session_state.get("costo_modulo_usd", 0.0))
c_inv   = float(st.session_state.get("costo_inversor_usd", 0.0))
# Área útil de paneles (agrivoltaica: factor de ocupación < 100%);
# si no existe, cae al área bruta histórica.
area_m2 = float(st.session_state.get("area_util_m2")
                or st.session_state.get("area_fachada_m2", 0.0))

if n_pan > 0:
    st.info(
        f"📐 Dimensionamiento: **{n_pan} módulos** · **{p_stc:.2f} kWp** · "
        f"Panel **${c_pan:.0f}/un** · Inversor **${c_inv:.0f}/un**"
        + (f" · Área de paneles **{area_m2:.1f} m²**" if area_m2 > 0 else "")
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

# ── Advertencia visible cuando alguna sección quedó vacía ────────────────────
_SEC_LABELS = {
    "perfileria":  "1. Materiales de Perfilería",
    "mano_obra":   "2. Mano de Obra y Servicios",
    "sistema_fv":  "3. Sistema Fotovoltaico",
    "inversor":    "4. Inversor y Equipos Eléctricos",
}
_secciones_vacias = [
    label for key, label in _SEC_LABELS.items()
    if key not in _secciones_raw or _secciones_raw[key].empty
]
if _secciones_vacias:
    st.warning(
        "⚠️ **Las siguientes secciones del Excel no cargaron filas** — "
        "se usará tabla vacía como punto de partida. "
        "Verifica que `insumos_template.xlsx` → Hoja1 contenga los encabezados "
        "`1. MATERIALES`, `2. MANO DE OBRA`, `3. SISTEMA FOTOVOLTAICO`, `4. INVERSOR` "
        "y una fila con `Descripcion` debajo de cada uno:  \n"
        + "  \n".join(f"• {s}" for s in _secciones_vacias)
    )

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
        _iny = inyectar.dropna(how="all")
        if not _iny.empty:
            raw = pd.concat([raw, _iny], ignore_index=True)
    return _df_con_activo(raw)

# ── Editor genérico con persistencia + fuente de precios ─────────────────────
def _editar_seccion(key, label, inyectar=None, referencia_mercado=""):
    ss_key = f"df_sec_{key}"
    _persistible = key in pstore.SECCIONES_PERSISTIBLES

    col_r, col_f = st.columns([2, 4])
    if col_r.button(f"↺ Resetear '{label}'", key=f"reset_{key}",
                    help="Vuelve a la plantilla original y descarta lo guardado en disco."):
        st.session_state.pop(ss_key, None)
        if _persistible:
            pstore.borrar_seccion(key)   # #114 — descartar también lo guardado
        st.rerun()

    # ── #114 — Restaurar fuente guardada en disco (antes del widget) ─────────
    if _persistible and f"fuente_{key}" not in st.session_state:
        _filas_g, _fuente_g = pstore.cargar_seccion(key)
        if _fuente_g:
            st.session_state[f"fuente_inp_{key}"] = _fuente_g

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
        # ── #114 — Preferir la versión guardada en disco sobre la plantilla ──
        _restaurado = False
        if _persistible:
            _filas_g, _fuente_g = pstore.cargar_seccion(key)
            if _filas_g:
                try:
                    _df_g = pd.DataFrame(_filas_g)
                    if "Descripcion" in _df_g.columns:
                        st.session_state[ss_key] = _df_g
                        _restaurado = True
                        st.caption("📂 Tabla restaurada de la última edición guardada "
                                   "— usa ↺ Resetear para volver a la plantilla.")
                except Exception:
                    pass   # archivo raro → caer a la plantilla
        if not _restaurado:
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
        # ── #114 — Persistir a disco en el mismo rerun del cambio ────────────
        if _persistible and not pstore.guardar_seccion(
                key, edited.to_dict("records"), fuente):
            st.caption("⚠️ No se pudo guardar la tabla en disco (permisos/espacio).")
    elif _persistible and fuente != st.session_state.get(f"_fuente_persistida_{key}"):
        # La fuente cambió sin cambiar filas → persistirla también
        pstore.guardar_seccion(key, edited.to_dict("records"), fuente)
        st.session_state[f"_fuente_persistida_{key}"] = fuente

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
# BENCHMARKS PARAMÉTRICOS — Colombia 2025-2026
# Fuente: Guía de Costos BIPV / IRENA / datos de mercado colombiano
# ══════════════════════════════════════════════════════════════════════════════
_BENCH = {
    # ── tipo_instalacion → escenario → { ítem: USD/Wp o USD fijo }
    # ── Formato: (opt, base, cons)
    "Granja FV campo": {
        "modulos_wp":       (0.180, 0.200, 0.220),
        "inversores_wp":    (0.060, 0.075, 0.090),
        "estructura_wp":    (0.080, 0.100, 0.120),
        "cableado_wp":      (0.040, 0.050, 0.060),
        "protecciones_wp":  (0.015, 0.020, 0.025),
        "trafo_fijo":       (15000, 22000, 35000),   # USD fijo (>100 kWp)
        "scada_fijo":       ( 8000, 11000, 15000),   # USD fijo
        "obra_civil_wp":    (0.050, 0.070, 0.090),
        "montaje_wp":       (0.040, 0.055, 0.070),
        "elect_wp":         (0.030, 0.040, 0.050),
        "puesta_marcha_wp": (0.010, 0.015, 0.020),
        "logistica_pct":    (0.030, 0.050, 0.070),  # % de equipos (módulos+inv)
        "ingenieria_pct":   (0.015, 0.022, 0.030),  # % CAPEX directo
        "pm_pct":           (0.030, 0.040, 0.050),  # % CAPEX directo
        "permisos_fijo":    ( 5000,  8000, 14000),  # USD fijo
        "conexion_fijo":    ( 8000, 16000, 32000),  # USD fijo
        "contingencia_pct": (0.080, 0.100, 0.120),  # % CAPEX total
        "opex_om_kw":       (  8.0,  10.0,  12.0),  # USD/kWp/año
        "opex_limpieza_kw": (  2.0,   3.0,   4.0),
        "opex_reposicion_kw":(  2.0,   2.5,   3.0),
        "opex_monitoreo_kw":(  3.0,   4.0,   5.0),
        "opex_seguro_pct":  (0.003, 0.004, 0.005),  # % CAPEX/año
    },
    "Techo industrial": {
        "modulos_wp":       (0.180, 0.205, 0.230),
        "inversores_wp":    (0.065, 0.080, 0.095),
        "estructura_wp":    (0.060, 0.080, 0.100),
        "cableado_wp":      (0.035, 0.045, 0.055),
        "protecciones_wp":  (0.012, 0.018, 0.022),
        "trafo_fijo":       (    0,     0,     0),   # no aplica típicamente
        "scada_fijo":       ( 5000,  8000, 12000),
        "obra_civil_wp":    (0.020, 0.030, 0.040),
        "montaje_wp":       (0.035, 0.050, 0.065),
        "elect_wp":         (0.025, 0.035, 0.045),
        "puesta_marcha_wp": (0.008, 0.012, 0.018),
        "logistica_pct":    (0.020, 0.035, 0.050),
        "ingenieria_pct":   (0.015, 0.022, 0.030),
        "pm_pct":           (0.025, 0.035, 0.045),
        "permisos_fijo":    ( 3000,  6000, 10000),
        "conexion_fijo":    ( 5000, 10000, 20000),
        "contingencia_pct": (0.070, 0.090, 0.110),
        "opex_om_kw":       (  6.0,   9.0,  12.0),
        "opex_limpieza_kw": (  1.5,   2.5,   3.5),
        "opex_reposicion_kw":(  2.0,   2.5,   3.0),
        "opex_monitoreo_kw":(  2.0,   3.0,   4.0),
        "opex_seguro_pct":  (0.003, 0.004, 0.005),
    },
    "BIPV fachada/pérgola": {
        "modulos_wp":       (0.250, 0.320, 0.400),
        "inversores_wp":    (0.070, 0.090, 0.110),
        "estructura_wp":    (0.200, 0.280, 0.380),
        "cableado_wp":      (0.050, 0.065, 0.080),
        "protecciones_wp":  (0.015, 0.022, 0.030),
        "trafo_fijo":       (    0,     0,     0),
        "scada_fijo":       ( 6000,  9000, 14000),
        "obra_civil_wp":    (0.040, 0.060, 0.090),
        "montaje_wp":       (0.080, 0.120, 0.180),
        "elect_wp":         (0.040, 0.055, 0.070),
        "puesta_marcha_wp": (0.015, 0.022, 0.030),
        "logistica_pct":    (0.025, 0.040, 0.060),
        "ingenieria_pct":   (0.020, 0.030, 0.040),
        "pm_pct":           (0.035, 0.045, 0.060),
        "permisos_fijo":    ( 4000,  8000, 15000),
        "conexion_fijo":    ( 5000, 10000, 20000),
        "contingencia_pct": (0.100, 0.130, 0.160),
        "opex_om_kw":       ( 10.0,  13.0,  16.0),
        "opex_limpieza_kw": (  2.0,   3.0,   4.5),
        "opex_reposicion_kw":(  2.5,   3.0,   4.0),
        "opex_monitoreo_kw":(  1.0,   2.0,   3.0),   # Growatt cloud + soporte; SCADA ya en CAPEX
        "opex_seguro_pct":  (0.002, 0.003, 0.004),   # 0.2–0.4 %/año; sector solar Colombia
    },
}

# Factor de zona geográfica (afecta obra civil + logística)
_ZONA_FACTOR = {
    "Bogotá / Sabana":          1.00,
    "Medellín / Antioquia":     1.05,
    "Cali / Valle":             1.07,
    "Barranquilla / Costa":     1.08,
    "Urabá / Chocó (tropical)": 1.17,
    "Llanos Orientales":        1.12,
    "Otra zona remota":         1.15,
}

def _calc_parametrico(kwp, tipo, escenario, zona):
    """Devuelve dict con desglose y totales en USD."""
    idx = {"Optimista": 0, "Base": 1, "Conservador": 2}[escenario]
    b = _BENCH[tipo]
    zf = _ZONA_FACTOR[zona]
    wp = kwp * 1000

    def g(key): return b[key][idx]

    # ── Equipos / duros ────────────────────────────────────────────────
    mod     = g("modulos_wp")    * wp
    inv     = g("inversores_wp") * wp
    est     = g("estructura_wp") * wp * zf
    cable   = g("cableado_wp")   * wp
    prot    = g("protecciones_wp") * wp
    trafo   = g("trafo_fijo")   if kwp >= 100 else 0
    scada   = g("scada_fijo")
    log_eq  = (mod + inv) * g("logistica_pct") * zf
    equip_total = mod + inv + est + cable + prot + trafo + scada + log_eq

    # ── Construcción / EPC ─────────────────────────────────────────────
    civil   = g("obra_civil_wp")    * wp * zf
    montaje = g("montaje_wp")       * wp
    elect   = g("elect_wp")         * wp
    pm_obra = g("puesta_marcha_wp") * wp
    epc_total = civil + montaje + elect + pm_obra

    # ── Costos directos ────────────────────────────────────────────────
    directo = equip_total + epc_total

    # ── Costos blandos ─────────────────────────────────────────────────
    ing     = directo * g("ingenieria_pct")
    pm      = directo * g("pm_pct")
    perm    = g("permisos_fijo")
    conex   = g("conexion_fijo")
    soft_total = ing + pm + perm + conex

    capex_base = directo + soft_total

    # ── Contingencias ──────────────────────────────────────────────────
    cont    = capex_base * g("contingencia_pct")
    capex_total = capex_base + cont

    # ── OPEX anual ─────────────────────────────────────────────────────
    # O&M y limpieza escalan con zona: requieren visitas presenciales → más
    # costosas en zonas remotas (Urabá zf=1.17, Llanos zf=1.12, etc.)
    opex_om     = g("opex_om_kw")         * kwp * zf
    opex_limp   = g("opex_limpieza_kw")   * kwp * zf
    opex_repos  = g("opex_reposicion_kw") * kwp        # repuestos: costo similar
    opex_mon    = g("opex_monitoreo_kw")  * kwp        # monitoreo remoto: no escala
    opex_seg    = capex_total * g("opex_seguro_pct")
    # ── Mínimo absoluto O&M para instalaciones ≥ 50 kWp ───────────────
    # Representa el costo mínimo de un contrato de mantenimiento preventivo
    # (visitas periódicas + mano de obra). Por debajo de este piso el modelo
    # subestima costos reales en proyectos medianos/grandes en Colombia.
    # Referencia: contrato básico BIPV/FV Colombia = USD 6,000–10,000/año.
    _opex_om_limp_calc = opex_om + opex_limp
    _opex_om_limp_min  = 8000.0 if kwp >= 300 else (5000.0 if kwp >= 50 else 0.0)
    if _opex_om_limp_calc < _opex_om_limp_min:
        _factor_min = _opex_om_limp_min / _opex_om_limp_calc if _opex_om_limp_calc > 0 else 1.0
        opex_om   *= _factor_min
        opex_limp *= _factor_min
    opex_total  = opex_om + opex_limp + opex_repos + opex_mon + opex_seg

    return {
        "kwp": kwp, "wp": wp,
        # Equipos
        "mod": mod, "inv": inv, "est": est, "cable": cable,
        "prot": prot, "trafo": trafo, "scada": scada, "log_eq": log_eq,
        "equip_total": equip_total,
        # EPC
        "civil": civil, "montaje": montaje, "elect": elect, "pm_obra": pm_obra,
        "epc_total": epc_total,
        # Soft
        "ing": ing, "pm": pm, "perm": perm, "conex": conex,
        "soft_total": soft_total,
        # Totales
        "directo": directo,
        "capex_base": capex_base,
        "cont": cont,
        "capex_total": capex_total,
        # OPEX
        "opex_om": opex_om, "opex_limp": opex_limp,
        "opex_repos": opex_repos, "opex_mon": opex_mon, "opex_seg": opex_seg,
        "opex_total": opex_total,
    }

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "🧮 Estimación Rápida",
    "🔩 Perfilería y Estructura",
    "👷 Mano de Obra",
    "⚡ Sistema FV",
    "🔌 Inversor y Equipos Eléctricos",
    "📦 Equipos del Catálogo",
    "🧾 Costos Blandos",
    "📅 OPEX Anual",
])
t0,t1,t2,t3,t4,t5,t6,t7 = tabs

# ══════════════════════════════════════════════════════════════════════════════
# TAB 0 — ESTIMACIÓN RÁPIDA PARAMÉTRICA
# ══════════════════════════════════════════════════════════════════════════════
with t0:
    st.markdown(
        "> 🧮 **Estimación paramétrica** — Benchmarks de mercado colombiano 2025-2026 "
        "(IRENA, UPME, CCSE, datos propios).  \n"
        "> No reemplaza cotización real. Cuando completes los tabs de cotización, "
        "desactívala con el botón '🔄 Limpiar' para que el Resumen use los valores reales."
    )

    # ── kWp del sistema: auto desde Dimensionamiento o entrada manual ─────────
    if p_stc > 0:
        kwp_est = p_stc
        st.success(
            f"⚡ Sistema detectado desde Dimensionamiento: **{kwp_est:.2f} kWp** · "
            f"{n_pan} módulos · TRM **{tc:,.0f} COP/USD**"
        )
    else:
        kwp_est = st.number_input(
            "Potencia instalada (kWp) — completa 📐 Dimensionamiento para auto-completar",
            min_value=1.0, max_value=100000.0, value=100.0, step=10.0, key="kwp_est_manual"
        )
        st.caption("💡 Ejecuta 📐 Dimensionamiento para que este valor se vincule automáticamente.")

    # ── #79 — Detectar zona fresca ANTES del auto-update ────────────────────────
    # La detección (predio → coords → TMY) debe correr antes del bloque de
    # auto-actualización para que éste use siempre la zona vigente del proyecto.
    _zona_opts  = list(_ZONA_FACTOR.keys())
    _municipio_predio = str(st.session_state.get("municipio_predio", "")).lower()
    _ciudad_tmy       = str(st.session_state.get("tmy_ciudad", "")).lower()
    _zona_geo_coords  = st.session_state.get("zona_geo_coords", "")
    if not _zona_geo_coords:
        _lat_p = float(st.session_state.get("lat_proyecto", 0.0))
        _lon_p = float(st.session_state.get("lon_proyecto", 0.0))
        if _lat_p and _lon_p:
            if   4.5 <= _lat_p <= 8.5 and _lon_p <= -76.0:              _zona_geo_coords = "Urabá / Chocó (tropical)"
            elif _lat_p > 8.5 or (_lat_p > 7.5 and _lon_p > -76.0):     _zona_geo_coords = "Barranquilla / Costa"
            elif _lon_p > -74.0:                                         _zona_geo_coords = "Llanos Orientales"
            elif _lat_p < 4.5 and _lon_p < -74.0:                       _zona_geo_coords = "Cali / Valle"
            elif _lat_p < 5.5 and _lon_p > -74.5:                       _zona_geo_coords = "Bogotá / Sabana"
            else:                                                         _zona_geo_coords = "Medellín / Antioquia"
            st.session_state["zona_geo_coords"] = _zona_geo_coords
    # IMPORTANTE: keywords más específicos primero (Urabá antes que "antioq").
    _zona_map = {
        "villavicencio": 5, "vichada": 5, "orinoquia": 5,
        "leticia": 5, "amazona": 5, "llano": 5,
        "urab": 4, "apartad": 4, "turbo": 4,
        "necoclí": 4, "necocli": 4, "chigorodo": 4, "chigorodó": 4,
        "mutata": 4, "mutatá": 4, "carepa": 4, "arboletes": 4,
        "choc": 4, "quibd": 4,
        "barranq": 3, "santa marta": 3, "cartagena": 3,
        "monteria": 3, "sincelejo": 3, "valledup": 3,
        "cordoba": 3, "sucre": 3, "cesar": 3, "magdalena": 3, "costa": 3,
        "cali": 2, "palmira": 2, "buenaven": 2, "popayan": 2,
        "valle": 2, "cauca": 2,
        "medell": 1, "rionegro": 1, "manizal": 1,
        "pereira": 1, "armenia": 1, "risaral": 1, "quindio": 1, "caldas": 1,
        "antioq": 1,
        "bogot": 0, "saban": 0, "tunja": 0, "cundinam": 0,
    }
    _zona_idx = 0; _zona_fuente = None
    for kw, idx in _zona_map.items():
        if kw in _municipio_predio:
            _zona_idx = idx; _zona_fuente = "predio"; break
    if not _zona_fuente and _zona_geo_coords in _zona_opts:
        _zona_idx = _zona_opts.index(_zona_geo_coords); _zona_fuente = "coords"
    if not _zona_fuente:
        for kw, idx in _zona_map.items():
            if kw in _ciudad_tmy:
                _zona_idx = idx; _zona_fuente = "TMY"; break

    # ── #79: re-sincronizar la zona ANTES del auto-update ────────────────────
    # La zona auto-detectada solo re-escribe el dropdown (est_zona) cuando
    # CAMBIA respecto a la última detección; el override manual del usuario
    # persiste mientras la detección no varíe. Hacerlo aquí (y no junto al
    # widget) garantiza que el bloque de auto-actualización de abajo calcule
    # con la MISMA zona que el dropdown terminará mostrando en este rerun.
    if _zona_fuente:
        _zona_auto_val = _zona_opts[_zona_idx]
        if st.session_state.get("_est_zona_auto_prev") != _zona_auto_val:
            st.session_state["est_zona"] = _zona_auto_val
            st.session_state["_est_zona_auto_prev"] = _zona_auto_val

    # Zona efectiva del rerun: la vigente del dropdown (ya re-sincronizada),
    # con la detectada o la config previa como respaldo.
    def _zona_vigente(cfg_prev: dict) -> str:
        _z = st.session_state.get("est_zona")
        if _z in _zona_opts:
            return _z
        if _zona_fuente:
            return _zona_opts[_zona_idx]
        return cfg_prev.get("zona", _zona_opts[0])

    # ── Auto-actualización silenciosa cuando el kWp del sistema cambió ────────
    # Si la estimación ya fue aplicada y el sistema cambió >5% de potencia,
    # recalcula y re-aplica automáticamente con el mismo tipo/escenario/zona.
    _er_cfg_prev = st.session_state.get("est_rapida_config", {})
    if st.session_state.get("est_rapida_aplicada") and _er_cfg_prev and p_stc > 0:
        _kwp_prev_er = float(_er_cfg_prev.get("kwp", 0))
        if _kwp_prev_er > 0 and abs(p_stc - _kwp_prev_er) / _kwp_prev_er > 0.05:
            _tipo_auto = _er_cfg_prev.get("tipo", list(_BENCH.keys())[0])
            _esc_auto  = _er_cfg_prev.get("escenario", "Base")
            # #79 — zona efectiva ya re-sincronizada arriba (respeta override manual)
            _zona_auto = _zona_vigente(_er_cfg_prev)
            _r_auto    = _calc_parametrico(p_stc, _tipo_auto, _esc_auto, _zona_auto)
            st.session_state["presupuesto_capex_usd"]        = _r_auto["capex_total"]
            _marcar_fuente_capex("Estimación Rápida")
            st.session_state["presupuesto_opex_anual_usd"]   = _r_auto["opex_total"]
            st.session_state["presupuesto_fraccion_equipos"] = (
                _r_auto["equip_total"] / _r_auto["capex_total"]
                if _r_auto["capex_total"] > 0 else 0.65
            )
            st.session_state["presupuesto_capex_directo"] = _r_auto["directo"]
            st.session_state["presupuesto_sub_directo"]   = _r_auto["directo"]
            st.session_state["presupuesto_capex_blando"]  = _r_auto["soft_total"]
            _zona_prev_er = _er_cfg_prev.get("zona", _zona_opts[0])
            st.session_state["est_rapida_config"] = {**_er_cfg_prev, "kwp": p_stc, "zona": _zona_auto}
            _zona_cambio_txt = (
                f" · zona actualizada de **{_zona_prev_er}** → **{_zona_auto}**"
                if _zona_auto != _zona_prev_er else ""
            )
            st.info(
                f"🔄 **Estimación Rápida auto-actualizada** — el sistema cambió de "
                f"**{_kwp_prev_er:.1f} → {p_stc:.1f} kWp**{_zona_cambio_txt}. "
                f"CAPEX actualizado a **USD {_r_auto['capex_total']:,.0f}** "
                f"({_tipo_auto} · {_esc_auto} · {_zona_auto}). "
                f"💰 Financiero refleja el nuevo valor automáticamente."
            )

    # ── Selectores: tipo, escenario, zona ────────────────────────────────────
    col_s1, col_s2, col_s3 = st.columns(3)

    # Auto-detectar tipo de instalación
    _tipo_opts = list(_BENCH.keys())
    _tipo_idx  = 0   # Granja FV por defecto
    if area_m2 > 0 and kwp_est > 0:
        _densidad = area_m2 / (kwp_est * 1000) * 1000  # m²/kWp
        if _densidad > 6.0:            # módulos de fachada ocupan más m²/kWp
            _tipo_idx = 2              # BIPV fachada/pérgola
        elif kwp_est < 200:
            _tipo_idx = 1              # Techo industrial
    elif kwp_est < 100:
        _tipo_idx = 1

    tipo_est = col_s1.selectbox(
        "Tipo de instalación", _tipo_opts, index=_tipo_idx, key="est_tipo",
        help="Se auto-detecta según la densidad de paneles del Dimensionamiento."
    )
    # Advertencia para proyectos BIPV micro: los costos fijos (scada, permisos,
    # conexión) elevan el USD/Wp significativamente por debajo de ~20 kWp.
    if "BIPV" in tipo_est and kwp_est < 20:
        st.warning(
            f"⚠️ **Proyecto BIPV muy pequeño ({kwp_est:.1f} kWp)** — "
            f"los costos fijos del modelo (SCADA, permisos RETIE/UPME, conexión a red) "
            f"representan más del 50 % del CAPEX a esta escala, elevando el indicador "
            f"USD/Wp por encima de los rangos de mercado típicos. "
            f"Esta estimación es válida como referencia de prefactibilidad, pero para "
            f"proyectos < 20 kWp se recomienda solicitar cotización EPC directamente. "
            f"Los rangos referenciales asumen proyectos ≥ 30 kWp."
        )
    escenario_est = col_s2.selectbox(
        "Escenario de costo", ["Optimista", "Base", "Conservador"], index=1, key="est_esc",
        help="Base = mediana de mercado. Optimista = compra directa + negociación. Conservador = + contingencias."
    )

    # Auto-detectar zona — ya computado antes del auto-update (#79).
    # FIX: pre-poblar session_state para TODAS las fuentes automáticas.
    # Sin esto, Streamlit ignora `index=` en renders sucesivos porque el key
    # ya existe en session_state con el valor anterior.
    # #79: la re-sincronización de est_zona ocurre ANTES del auto-update
    # (ver bloque "_zona_vigente" arriba) — aquí solo se renderiza el widget.
    zona_est = col_s3.selectbox(
        "Zona geográfica", _zona_opts, index=_zona_idx, key="est_zona",
        help="Se auto-detecta desde las coordenadas del predio (prioridad) o la ciudad de referencia climática. "
             "Puedes elegir otra manualmente; si la detección cambia (nuevas coordenadas), se vuelve a sincronizar."
    )

    # Aviso de divergencia: el usuario eligió una zona distinta a la detectada.
    # El cálculo usa SIEMPRE la del dropdown (zona_est) — nunca hay inconsistencia
    # silenciosa entre lo mostrado y lo calculado.
    if _zona_fuente and zona_est != _zona_opts[_zona_idx]:
        st.warning(
            f"⚠️ Zona seleccionada manualmente (**{zona_est}**, factor "
            f"×{_ZONA_FACTOR[zona_est]:.2f}) difiere de la auto-detectada "
            f"(**{_zona_opts[_zona_idx]}**, ×{_ZONA_FACTOR[_zona_opts[_zona_idx]]:.2f}). "
            f"El cálculo usa la seleccionada."
        )

    # Caption explicativo según la fuente de detección (solo si el dropdown
    # coincide con la detección — si difiere, ya se mostró el aviso de arriba)
    if _zona_fuente and zona_est != _zona_opts[_zona_idx]:
        pass
    elif _zona_fuente == "predio":
        st.caption(
            f"📍 Zona detectada desde las **coordenadas del predio** "
            f"({st.session_state.get('municipio_predio', '—')}) → "
            f"**{zona_est}** (factor ×{_ZONA_FACTOR[zona_est]:.2f})"
        )
    elif _zona_fuente == "coords":
        st.caption(
            f"🛰️ Zona detectada desde las **coordenadas del proyecto** "
            f"(lat/lon registradas en Recurso Solar) → "
            f"**{zona_est}** (factor ×{_ZONA_FACTOR[zona_est]:.2f})  \n"
            f"ℹ️ Ingresa el nombre del municipio en **Proyecto** para mayor precisión."
        )
    elif _zona_fuente == "TMY":
        st.caption(
            f"🌡️ Zona estimada desde ciudad de referencia TMY: "
            f"**{st.session_state.get('tmy_ciudad', '—')}** → "
            f"**{zona_est}** (factor ×{_ZONA_FACTOR[zona_est]:.2f})  \n"
            f"⚠️ La ciudad TMY puede diferir del predio real. Ejecuta **Recurso Solar** "
            f"con las coordenadas exactas del predio para mejorar la detección."
        )

    st.markdown("---")

    # ── Calcular los tres escenarios en paralelo ──────────────────────────────
    r_opt  = _calc_parametrico(kwp_est, tipo_est, "Optimista",   zona_est)
    r_base = _calc_parametrico(kwp_est, tipo_est, "Base",        zona_est)
    r_cons = _calc_parametrico(kwp_est, tipo_est, "Conservador", zona_est)
    r      = {"Optimista": r_opt, "Base": r_base, "Conservador": r_cons}[escenario_est]

    # ── Métricas principales del escenario activo ─────────────────────────────
    st.markdown(f"#### 📊 Desglose — Escenario **{escenario_est}** · {tipo_est} · {zona_est}")
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("CAPEX Total",    f"USD {r['capex_total']:,.0f}",
               f"$ {r['capex_total']*tc/1e6:.2f} M COP", delta_color="off")
    mc2.metric("USD / Wp",       f"USD {r['capex_total']/r['wp']:.3f}/Wp",
               f"Ref: {tipo_est[:5]}", delta_color="off")
    mc3.metric("OPEX Anual",     f"USD {r['opex_total']:,.0f}/año",
               f"USD {r['opex_total']/kwp_est:.1f}/kWp·año", delta_color="off")
    mc4.metric("Frac. equipos (Ley 1715)",
               f"{r['equip_total']/r['capex_total']*100:.1f}%",
               "Base Art. 12 IVA + Art. 11 renta", delta_color="off")

    # ── Tabla de desglose por categoría ──────────────────────────────────────
    # Todas las celdas se pre-formatean como strings para evitar que pandas
    # convierta None → NaN (NaN es truthy → ".format()" mostraría "nan").
    _ct = r["capex_total"]
    def _fmt(v):
        """USD formateado + % del CAPEX + COP en millones. Devuelve (usd_str, pct_str, cop_str)."""
        usd = f"{v:>12,.0f}"
        pct = f"{v/_ct*100:.1f}%"
        cop = f"{v*tc/1e6:.2f}"
        return usd, pct, cop

    # Tipo de fila: "H"=encabezado, "S"=subtotal, "T"=total, "I"=ítem
    _RAW: list[tuple] = []
    def add_h(label):                    _RAW.append(("H", label, "", "", ""))
    def add_i(label, v):
        u, p, c = _fmt(v);               _RAW.append(("I", label, u, p, c))
    def add_s(label, v):
        u, p, c = _fmt(v);               _RAW.append(("S", label, u, p, c))

    add_h("🔩 EQUIPOS / DUROS")
    add_i("  · Módulos FV",               r["mod"])
    add_i("  · Inversores",               r["inv"])
    add_i("  · Estructura de montaje",    r["est"])
    add_i("  · Cableado DC + AC",         r["cable"])
    add_i("  · Protecciones DC/AC",       r["prot"])
    if r["trafo"] > 0:
        add_i("  · Transformador MT",     r["trafo"])
    add_i("  · SCADA / Medición",         r["scada"])
    add_i("  · Logística / Transporte",   r["log_eq"])
    add_s("  Subtotal Equipos",           r["equip_total"])

    add_h("🏗️ CONSTRUCCIÓN / EPC")
    add_i("  · Obra civil + cimentación", r["civil"])
    add_i("  · Montaje estructural",      r["montaje"])
    add_i("  · Instalación eléctrica",    r["elect"])
    add_i("  · Puesta en marcha / Tests", r["pm_obra"])
    add_s("  Subtotal EPC",               r["epc_total"])

    add_h("🧾 COSTOS BLANDOS")
    add_i("  · Ingeniería + diseño",      r["ing"])
    add_i("  · Gestión de proyecto (PM)", r["pm"])
    add_i("  · Permisos / RETIE / UPME",  r["perm"])
    add_i("  · Conexión a la red",        r["conex"])
    add_s("  Subtotal Costos Blandos",    r["soft_total"])

    _RAW.append(("S", "⚙️ CONTINGENCIAS", *_fmt(r["cont"])))
    _RAW.append(("T", "✅ CAPEX TOTAL", f"{_ct:>12,.0f}", "100.0%", f"{_ct*tc/1e6:.2f}"))

    df_des = pd.DataFrame(
        [(d[1], d[2], d[3], d[4]) for d in _RAW],
        columns=["Categoría", "USD", "% CAPEX", "COP (M)"]
    )
    _tipos = [d[0] for d in _RAW]   # lista paralela: H/S/T/I por índice

    def _style_tabla(row):
        t = _tipos[row.name]
        if t == "T":   return ["font-weight:bold; background:#d0e8ff; color:#003060"] * len(row)
        if t == "S":   return ["font-weight:bold; background:#EAF4FB"] * len(row)
        if t == "H":   return ["font-weight:bold; background:#f0f4f8; color:#1a3c5e"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_des.style.apply(_style_tabla, axis=1),
        use_container_width=True, hide_index=True, height=560
    )

    # ── Comparativo 3 escenarios ──────────────────────────────────────────────
    with st.expander("📊 Comparativo Optimista / Base / Conservador", expanded=False):
        comp_data = []
        for esc, rv in [("Optimista", r_opt), ("Base", r_base), ("Conservador", r_cons)]:
            comp_data.append({
                "Escenario":      esc,
                "CAPEX (USD)":    rv["capex_total"],
                "USD/Wp":         rv["capex_total"] / rv["wp"],
                "CAPEX (M COP)":  rv["capex_total"] * tc / 1e6,
                "OPEX (USD/año)": rv["opex_total"],
                "OPEX (USD/kWp)": rv["opex_total"] / kwp_est,
                "Equipos (%)":    rv["equip_total"] / rv["capex_total"] * 100,
            })
        df_comp = pd.DataFrame(comp_data)
        st.dataframe(
            df_comp.style.format({
                "CAPEX (USD)": "{:,.0f}",
                "USD/Wp":      "{:.3f}",
                "CAPEX (M COP)": "{:.2f}",
                "OPEX (USD/año)": "{:,.0f}",
                "OPEX (USD/kWp)": "{:.1f}",
                "Equipos (%)":    "{:.1f}%",
            }).apply(lambda row: ["background:#e8f5e9"]*len(row) if row["Escenario"] == escenario_est
                     else [""]*len(row), axis=1),
            use_container_width=True, hide_index=True
        )

    # ── OPEX anual desglose ───────────────────────────────────────────────────
    with st.expander("📅 Desglose OPEX anual estimado", expanded=False):
        opex_rows = [
            ("O&M preventivo + correctivo",     r["opex_om"]),
            ("Limpieza de módulos",              r["opex_limp"]),
            ("Seguro operativo",                 r["opex_seg"]),
            ("Fondo reposición inversores",      r["opex_repos"]),
            ("Monitoreo remoto + administración",r["opex_mon"]),
            ("TOTAL OPEX anual",                 r["opex_total"]),
        ]
        df_opex_e = pd.DataFrame(opex_rows, columns=["Ítem", "USD/año"])
        df_opex_e["COP (M)/año"] = (df_opex_e["USD/año"] * tc / 1e6).round(3)
        df_opex_e["USD/kWp·año"] = (df_opex_e["USD/año"] / kwp_est).round(2)
        st.dataframe(
            df_opex_e.style
                .format({"USD/año": "{:,.0f}", "COP (M)/año": "{:.3f}", "USD/kWp·año": "{:.2f}"})
                .apply(lambda r: ["font-weight:bold; background:#EAF4FB"]*len(r)
                       if "TOTAL" in str(r["Ítem"]) else [""]*len(r), axis=1),
            use_container_width=True, hide_index=True
        )
        _ref_opex = {"Granja FV campo": "8–14", "Techo industrial": "9–16",
                     "BIPV fachada/pérgola": "18–32"}.get(tipo_est, "10–25")
        st.caption(f"Ref. Colombia {tipo_est}: **USD {_ref_opex}/kWp·año** "
                   f"(incluye O&M, limpieza, reposición inversores, monitoreo, seguro todo riesgo).  "
                   f"Este proyecto: **USD {r['opex_total']/kwp_est:.1f}/kWp·año**")

    # ── Nota de coherencia con valores ya corridos ────────────────────────────
    st.markdown("---")
    _ppto_real = float(st.session_state.get("presupuesto_capex_usd", 0.0))
    _opex_real = float(st.session_state.get("presupuesto_opex_anual_usd", 0.0))
    _est_activa = st.session_state.get("est_rapida_aplicada", False)

    if _ppto_real > 0 and not _est_activa:
        st.info(
            f"ℹ️ El Resumen ya tiene un CAPEX real desde los tabs de cotización: "
            f"**USD {_ppto_real:,.0f}**. "
            f"Para usar la estimación paramétrica, presiona '✅ Aplicar' abajo. "
            f"Para volver al cotizado, presiona '🔄 Limpiar'."
        )

    col_ap1, col_ap2, col_ap3 = st.columns([2, 2, 4])
    if col_ap1.button("✅ Aplicar a 💰 Financiero", type="primary", key="btn_aplicar_est"):
        st.session_state["presupuesto_capex_usd"]       = r["capex_total"]
        _marcar_fuente_capex("Estimación Rápida")
        st.session_state["presupuesto_opex_anual_usd"]  = r["opex_total"]
        st.session_state["presupuesto_fraccion_equipos"] = (
            r["equip_total"] / r["capex_total"] if r["capex_total"] > 0 else 0.65
        )
        st.session_state["presupuesto_capex_directo"]   = r["directo"]
        st.session_state["presupuesto_sub_directo"]     = r["directo"]
        st.session_state["presupuesto_capex_blando"]    = r["soft_total"]
        st.session_state["est_rapida_aplicada"]         = True
        st.session_state["est_rapida_config"]           = {
            "tipo": tipo_est, "escenario": escenario_est,
            "zona": zona_est, "kwp": kwp_est,
        }
        st.rerun()

    if col_ap2.button("🔄 Limpiar (usar cotización real)", key="btn_limpiar_est"):
        for _k in ["est_rapida_aplicada", "est_rapida_config",
                   "presupuesto_capex_usd", "presupuesto_opex_anual_usd",
                   "presupuesto_fraccion_equipos", "presupuesto_capex_directo",
                   "presupuesto_sub_directo", "presupuesto_capex_blando",
                   "presupuesto_fuente", "presupuesto_capex_ts"]:
            st.session_state.pop(_k, None)
        st.rerun()

    if _est_activa:
        cfg = st.session_state.get("est_rapida_config", {})
        st.success(
            f"✅ **Estimación paramétrica ACTIVA** → 💰 Financiero usa:  \n"
            f"CAPEX **USD {_ppto_real:,.0f}** (${_ppto_real*tc/1e6:.2f} M COP) · "
            f"OPEX **USD {_opex_real:,.0f}/año**  \n"
            f"Configuración: {cfg.get('tipo','—')} · {cfg.get('escenario','—')} · "
            f"{cfg.get('zona','—')} · {cfg.get('kwp',0):.1f} kWp  \n"
            f"🔄 Presiona 'Limpiar' cuando tengas cotizaciones reales."
        )
        # ── Alerta si el cálculo live difiere >10% del valor guardado ────────
        _live_capex = r.get("capex_total", 0)
        if _ppto_real > 0 and _live_capex > 0:
            _diff_pct = abs(_live_capex - _ppto_real) / _ppto_real * 100
            if _diff_pct > 10:
                st.warning(
                    f"⚠️ **Los parámetros cambiaron desde la última aplicación.** "
                    f"El cálculo actual arroja **USD {_live_capex:,.0f}** "
                    f"({_diff_pct:.0f}% {'más' if _live_capex>_ppto_real else 'menos'} "
                    f"que el valor guardado USD {_ppto_real:,.0f}).  \n"
                    f"💡 Presiona **✅ Aplicar** para actualizar Financiero con los nuevos parámetros, "
                    f"o los resultados de TIR/VPN reflejarán la configuración anterior."
                )
    else:
        st.caption(
            "⬆️ Presiona **✅ Aplicar** para enviar esta estimación a 💰 Financiero. "
            "El Resumen al final de la página seguirá mostrando los tabs de cotización real."
        )

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
    > 💡 Referencia Colombia: costos blandos = **10–20% del CAPEX directo** para BIPV.
    > ITA obligatorio para financiamiento bancario > USD 200k.
    > PM típico: 3–5% CAPEX. Póliza CAR: 0.4–0.6% CAPEX.
    """)

    ss_soft = "df_sec_soft"

    # ── CAPEX directo disponible en este tab (sub1–sub5 ya calculados arriba) ──
    _capex_dir_proxy = sub1 + sub2 + sub3 + sub4 + sub5

    # ── Función: valores conservadores por ítem según CAPEX directo ───────────
    def _soft_conservador(capex_dir: float) -> list:
        """Retorna lista compatible con _BASE_COLS con porcentajes conservadores."""
        cd = max(capex_dir, 0.0)
        def _v(pct, minv, maxv=None):
            v = cd * pct
            v = max(v, minv)
            if maxv is not None:
                v = min(v, maxv)
            return round(v, 2)
        return [
            # Descripcion                                       Ref        Cant  Uni    USD_un
            ["Ingeniería, diseño y memorias de cálculo",       "ENG-001",  1.0, "glb", _v(0.050, 1_500, 25_000)],
            ["Estudio de sombreado y simulación BIPV",         "ENG-002",  1.0, "glb", _v(0.015,   800,  5_000)],
            ["Registro UPME y trámites Ley 1715",              "TRM-001",  1.0, "glb", _v(0.060, 3_000, 15_000)],
            ["Concepto de conexión — operador de red",         "TRM-002",  1.0, "glb", _v(0.030, 1_500,  7_000)],
            ["Certificación RETIE / RITEL",                    "TRM-003",  1.0, "glb", _v(0.025, 1_200,  4_500)],
            ["Gestión del proyecto — Project Manager",         "PM-001",   1.0, "glb", _v(0.040, 1_000, 20_000)],
            ["Asesoría legal y estructuración financiera",     "LEG-001",  1.0, "glb", _v(0.015,   600,  8_000)],
            ["Auditoría técnica independiente (ITA)",          "ITA-001",  1.0, "glb",  0.0],   # desact. por defecto
            ["Póliza CAR — construcción todo riesgo",          "SEG-001",  1.0, "glb", _v(0.005,   300,  5_000)],
            ["Gastos notariales, registros y licencias",       "LEG-002",  1.0, "glb", _v(0.005,   500,  2_000)],
        ]

    # ── Botón: sugerir valores conservadores ─────────────────────────────────
    col_rs, col_sug, col_fs = st.columns([2, 2, 4])
    if col_rs.button("↺ Resetear 'Costos Blandos'", key="reset_soft"):
        st.session_state.pop(ss_soft, None)
        st.rerun()

    _btn_sug = col_sug.button("🪄 Sugerir valores conservadores", key="sug_soft",
        help="Calcula cada ítem como % del CAPEX directo con mínimos Colombia 2026. "
             "Puedes ajustar ítem a ítem después.")
    if _btn_sug:
        if _capex_dir_proxy > 0:
            st.session_state[ss_soft] = _df_con_activo(_soft_conservador(_capex_dir_proxy))
            # Desmarcar ITA (fila índice 7) — opcional solo para proyectos > 200k
            _df_tmp = st.session_state[ss_soft].copy()
            _df_tmp.at[7, "Activo"] = False
            st.session_state[ss_soft] = _df_tmp
            st.toast(f"✅ Costos blandos sugeridos sobre CAPEX directo USD {_capex_dir_proxy:,.0f}", icon="🪄")
        else:
            st.warning("⚠️ Completa primero al menos una pestaña de cotización (Perfilería, Mano de Obra, etc.) "
                       "para que la sugerencia se calcule sobre el CAPEX real de tu proyecto.")

    fuente_s = col_fs.text_input("Fuente / cotización soft costs",
        value=st.session_state.get("fuente_soft",""),
        placeholder="Ej.: Propuesta consultoría XYZ, cotización póliza ABC, julio 2026",
        key="fuente_inp_soft", label_visibility="collapsed")
    st.session_state["fuente_soft"] = fuente_s

    if ss_soft not in st.session_state:
        st.session_state[ss_soft] = _df_con_activo(_SOFT_DEFAULT)

    # ── Indicador % actual sobre CAPEX directo ────────────────────────────────
    if _capex_dir_proxy > 0:
        _soft_actual = float(
            pd.to_numeric(st.session_state[ss_soft].get("Cantidad", 0), errors="coerce").fillna(0)
            .mul(pd.to_numeric(st.session_state[ss_soft].get("USD_un", 0), errors="coerce").fillna(0))
            .sum()
        )
        _pct_actual = _soft_actual / _capex_dir_proxy * 100 if _capex_dir_proxy > 0 else 0
        _color = "🟢" if 8 <= _pct_actual <= 22 else ("🟡" if _pct_actual < 8 else "🔴")
        st.caption(
            f"{_color} Costos blandos actuales: **USD {_soft_actual:,.0f}** = "
            f"**{_pct_actual:.1f}% del CAPEX directo** (USD {_capex_dir_proxy:,.0f})  "
            f"· Referencia Colombia BIPV: 10–20%"
        )

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
    > 💡 Referencia Colombia: Granja FV **8–14 USD/kWp·año** · Techo industrial **9–16** · BIPV fachada **18–32**.
    > El OPEX BIPV es mayor porque incluye O&M especializado + seguro sobre CAPEX alto + reposición inversores.
    > El OPEX total anual se envía automáticamente a 💰 Financiero para el flujo de caja a 25 años.
    > **USD/un en esta pestaña = costo anual del ítem** (no unitario).
    """)

    ss_opex = "df_sec_opex"
    col_ro, col_sug_o, col_fo = st.columns([2, 2, 4])
    if col_ro.button("↺ Resetear 'OPEX'", key="reset_opex"):
        st.session_state.pop(ss_opex, None)
        st.rerun()

    # ── #72 — Botón sugerir valores O&M desde benchmarks paramétricos ─────────
    _btn_sug_o = col_sug_o.button("🪄 Sugerir valores O&M", key="sug_opex",
        help="Rellena los ítems con valores de referencia Colombia 2026 calculados "
             "desde el tipo de instalación, zona geográfica y potencia del sistema.")
    if _btn_sug_o:
        if p_stc > 0:
            _tipo_sug = st.session_state.get("est_tipo", list(_BENCH.keys())[1])
            _esc_sug  = st.session_state.get("est_esc",  "Base")
            _zona_sug = st.session_state.get("est_zona", list(_ZONA_FACTOR.keys())[0])
            _r_sug = _calc_parametrico(p_stc, _tipo_sug, _esc_sug, _zona_sug)
            _sug_rows = [
                ["O&M preventivo — visitas técnicas anuales",   "OM-001", 1.0, "año",  round(_r_sug["opex_om"],   2)],
                ["Limpieza de módulos (aprox. 4 veces/año)",    "OM-002", 4.0, "serv", round(_r_sug["opex_limp"] / 4, 2)],
                ["Seguro operativo — todo riesgo instalación",  "SEG-002",1.0, "año",  round(_r_sug["opex_seg"],  2)],
                ["Monitoreo remoto (plataforma Growatt/SCADA)", "MON-001",1.0, "año",  round(_r_sug["opex_mon"],  2)],
                ["Revisión anual inversor y comunicaciones",    "OM-003", 1.0, "año",  0.0],
                ["Fondo de reposición inversor (año 12–15)",    "RES-001",1.0, "año",  round(_r_sug["opex_repos"] * 0.70, 2)],
                ["Fondo de reposición módulos / garantías",     "RES-002",1.0, "año",  round(_r_sug["opex_repos"] * 0.30, 2)],
                ["Administración y costos fijos anuales",       "ADM-001",1.0, "año",  0.0],
            ]
            st.session_state[ss_opex] = _df_con_activo(_sug_rows)
            st.toast(
                f"✅ OPEX sugerido: USD {_r_sug['opex_total']:,.0f}/año "
                f"≈ {_r_sug['opex_total']/p_stc:.0f} USD/kWp·año "
                f"({_tipo_sug} · {_esc_sug} · {_zona_sug})", icon="🪄"
            )
        else:
            st.warning("⚠️ Completa 📐 Dimensionamiento primero para conocer la potencia del sistema.")

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
        _ref_opex_t7 = "18–32" if "BIPV" in str(st.session_state.get("tipo_instalacion","")) else "8–16"
        co2.metric("OPEX / kWp", f"USD {sub7/p_stc:.0f}/kWp·año",
                   f"Ref BIPV: 18–32 · Techo: 9–16 USD/kWp·año", delta_color="off")
    if excl_o > 0:
        co3.metric("Excluidos", f"USD {excl_o:,.0f}/año", "no suma al total", delta_color="off")
    st.caption(f"📋 {len(ed_opex)} ítems — {int(act_o.sum())} activos. → Este valor reemplaza el slider O&M en 💰 Financiero.")

    # ── #72 — Avisar cuando OPEX por kWp está por debajo del mínimo referencia ──
    if p_stc > 0 and sub7 > 0:
        _opex_kw_real = sub7 / p_stc
        _tipo_inst_t7 = str(st.session_state.get("tipo_instalacion", "")).lower()
        if any(x in _tipo_inst_t7 for x in ["bipv", "fachada", "pergola", "pérgola", "marquesina"]):
            _opex_ref_lo, _opex_ref_hi, _tipo_lbl = 18.0, 32.0, "BIPV fachada/pérgola"
        elif any(x in _tipo_inst_t7 for x in ["techo", "roof", "cubierta"]):
            _opex_ref_lo, _opex_ref_hi, _tipo_lbl = 9.0,  16.0, "techo industrial"
        else:
            _opex_ref_lo, _opex_ref_hi, _tipo_lbl = 8.0,  14.0, "granja FV campo"
        if _opex_kw_real < _opex_ref_lo * 0.6:
            st.error(
                f"🚨 **OPEX muy bajo: USD {_opex_kw_real:.0f}/kWp·año** — "
                f"la referencia para {_tipo_lbl} es **{_opex_ref_lo:.0f}–{_opex_ref_hi:.0f} USD/kWp·año**. "
                f"Un OPEX subestimado sobreestima la TIR y el VPN en el análisis financiero. "
                f"Usa **🪄 Sugerir valores O&M** para obtener valores de referencia."
            )
        elif _opex_kw_real < _opex_ref_lo:
            st.warning(
                f"⚠️ **OPEX bajo: USD {_opex_kw_real:.0f}/kWp·año** — "
                f"la referencia para {_tipo_lbl} es {_opex_ref_lo:.0f}–{_opex_ref_hi:.0f} USD/kWp·año. "
                f"Verifica que estén incluidos seguro, monitoreo y fondos de reposición."
            )
        elif _opex_kw_real > _opex_ref_hi * 1.3:
            st.info(
                f"ℹ️ OPEX alto: USD {_opex_kw_real:.0f}/kWp·año (ref. {_tipo_lbl}: "
                f"{_opex_ref_lo:.0f}–{_opex_ref_hi:.0f}). Revisa si hay ítems duplicados."
            )
    elif p_stc > 0 and sub7 == 0:
        st.info(
            "ℹ️ **OPEX = USD 0** — usa **🪄 Sugerir valores O&M** para pre-llenar con benchmarks "
            "de mercado colombiano, o ingresa los costos reales de O&M, seguro y reposición."
        )

# ══════════════════════════════════════════════════════════════════════════════
# RESUMEN CAPEX + CONTINGENCIAS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📊 Resumen CAPEX Total del Proyecto")

# ── Detectar modo activo: paramétrico vs cotización real ─────────────────────
_est_activa  = st.session_state.get("est_rapida_aplicada", False)
_tabs_sum    = sub1 + sub2 + sub3 + sub4 + sub5 + sub6
# "Cotización real" solo si los tabs tienen valores coherentes con el tamaño del sistema.
# IMPORTANTE: usar el kWp de la Estimación Rápida (est_rapida_config) como referencia,
# NO p_stc de session_state — p_stc puede ser ~4 kWp si la sesión se reinició,
# lo que haría pasar 0.34 USD/Wp como "coherente" al dividir 33k / 4kWp = 8.5.
_kwp_ref = (st.session_state.get("est_rapida_config") or {}).get("kwp") or p_stc
# Usar el mejor kWp disponible: est_rapida_config > Dimensionamiento > 0
_kwp_para_check = _kwp_ref or (p_stc if p_stc > 0 else 0)

if _tabs_sum > 0 and _kwp_para_check > 20:
    _usdwp_tabs  = _tabs_sum / (_kwp_para_check * 1000)
    _cotizacion_real = _usdwp_tabs >= 0.50   # mínimo absoluto para cualquier inst. solar
elif _tabs_sum > 0 and _kwp_para_check == 0:
    # kWp desconocido: solo aceptar si los tabs suman >500 USD (no son basura de sesión)
    _cotizacion_real = _tabs_sum > 500
elif _tabs_sum > 0:
    # Proyectos pequeños conocidos (<20 kWp): cualquier valor positivo vale
    _cotizacion_real = True
else:
    _cotizacion_real = False

if _est_activa and not _cotizacion_real:
    # ── MODO PARAMÉTRICO: usar los valores ya guardados en session_state ──────
    cfg = st.session_state.get("est_rapida_config", {})
    st.info(
        f"🧮 **Modo estimación paramétrica activa** — "
        f"{cfg.get('tipo','—')} · {cfg.get('escenario','—')} · "
        f"{cfg.get('zona','—')} · {cfg.get('kwp',0):.1f} kWp  \n"
        f"Los tabs de cotización están vacíos. Completa al menos uno para activar el modo cotización real, "
        f"o ve al tab **🧮 Estimación Rápida** para cambiar parámetros."
    )
    capex_total  = float(st.session_state.get("presupuesto_capex_usd", 0.0))
    opex_pub     = float(st.session_state.get("presupuesto_opex_anual_usd", 0.0))
    _frac_eq     = float(st.session_state.get("presupuesto_fraccion_equipos", 0.65))
    capex_directo= float(st.session_state.get("presupuesto_capex_directo", capex_total * 0.75))
    capex_base   = capex_directo + float(st.session_state.get("presupuesto_capex_blando", 0.0))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("CAPEX Paramétrico", f"USD {capex_total:,.0f}",
              f"$ {capex_total*tc/1e6:.2f} M COP", delta_color="off")
    m2.metric("USD / Wp", f"USD {capex_total/p_stc/1000:.3f}" if p_stc > 0 else "—",
              "Estimado paramétrico", delta_color="off")
    m3.metric("OPEX Anual", f"USD {opex_pub:,.0f}/año",
              f"USD {opex_pub/p_stc:.1f}/kWp·año" if p_stc > 0 else "—", delta_color="off")
    m4.metric("Frac. equipos (Ley 1715)", f"{_frac_eq*100:.1f}%",
              "Para Art. 12 + Art. 11", delta_color="off")

    st.success(
        f"✅ **CAPEX TOTAL USD {capex_total:,.0f}** ($ {capex_total*tc/1e6:.2f} M COP) "
        f"→ 💰 Financiero lo usa automáticamente. "
        f"Ley 1715 frac. equipos: **{_frac_eq*100:.0f}%** "
        f"· **OPEX USD {opex_pub:,.0f}/año** enviado al flujo de caja."
    )

else:
    # ── MODO COTIZACIÓN REAL: calcular desde tabs ─────────────────────────────
    if _est_activa and _cotizacion_real:
        st.success("✅ Cotización real detectada en tabs — usando esos valores (estimación paramétrica ignorada).")
        # ⚠️  NO borrar est_rapida_aplicada aquí: el session_state de la estimación
        # debe persistir para que Financiero siga usando el CAPEX correcto hasta que
        # el usuario presione explícitamente "Limpiar". El Resumen solo muestra los tabs
        # pero no fuerza a Financiero a cambiar de fuente automáticamente.
    elif not _est_activa and _tabs_sum > 0 and not _cotizacion_real:
        # Tabs con valores insuficientes (USD/Wp < 0.50 para este kWp) → avisar
        _usdwp_tabs_disp = _tabs_sum / (p_stc * 1000) if p_stc > 0 else 0
        st.warning(
            f"⚠️ **Tabs con valores incompletos** — los datos ingresados suman "
            f"**USD {_tabs_sum:,.0f}** ({_usdwp_tabs_disp:.2f} USD/Wp) para {p_stc:.0f} kWp. "
            f"El mínimo de referencia para cualquier instalación solar es **0.50 USD/Wp** "
            f"(= USD {p_stc*500:,.0f} para este proyecto).  \n"
            f"💡 Completa los tabs con cotizaciones reales, o usa la pestaña "
            f"**🧮 Estimación Rápida** para valores paramétricos."
        )

    capex_directo = sub1 + sub2 + sub3 + sub4 + sub5
    capex_base    = capex_directo + sub6

    df_res = pd.DataFrame([
        {"Categoría": "🔩 Perfilería y Estructura",           "USD": sub1, "COP (M)": round(sub1*tc/1e6,2), "% CAPEX base": 0.0},
        {"Categoría": "👷 Mano de Obra y Servicios",          "USD": sub2, "COP (M)": round(sub2*tc/1e6,2), "% CAPEX base": 0.0},
        {"Categoría": "⚡ Sistema FV (cables, protecciones)", "USD": sub3, "COP (M)": round(sub3*tc/1e6,2), "% CAPEX base": 0.0},
        {"Categoría": "🔌 Inversor y Equipos Eléctricos",     "USD": sub4, "COP (M)": round(sub4*tc/1e6,2), "% CAPEX base": 0.0},
        {"Categoría": "📦 Módulos + Inversor + Baterías",     "USD": sub5, "COP (M)": round(sub5*tc/1e6,2), "% CAPEX base": 0.0},
        {"Categoría": "🧾 Costos Blandos (soft costs)",       "USD": sub6, "COP (M)": round(sub6*tc/1e6,2), "% CAPEX base": 0.0},
    ])
    if capex_base > 0:
        df_res["% CAPEX base"] = (df_res["USD"] / capex_base * 100).round(1)
    df_res.loc[len(df_res)] = {"Categoría": "🔵 CAPEX Base (directo + blandos)",
        "USD": capex_base, "COP (M)": round(capex_base*tc/1e6,2), "% CAPEX base": 100.0}
    st.dataframe(
        df_res.style
            .format({"USD":"{:,.0f}","COP (M)":"{:.2f}","% CAPEX base":"{:.1f}%"})
            .apply(lambda r: ["font-weight:bold; background:#EAF4FB"]*len(r)
                   if "CAPEX Base" in str(r["Categoría"]) else [""]*len(r), axis=1),
        use_container_width=True, hide_index=True,
    )

    st.markdown("##### ⚙️ Contingencias")
    cc1, cc2, cc3 = st.columns(3)
    ind_pct   = cc1.slider("Costos indirectos — AUI, administración, utilidad (%)",
                            2, 25, 12, 1, help="Típico Colombia: 10–18%") / 100
    c_tec_pct = cc2.slider("Contingencia técnica (%)", 0, 20, 10, 1,
                            help="BIPV fachada: 10–15%. Techo industrial: 7–12%. Suelo convencional: 5–8%") / 100
    c_pre_pct = cc3.slider("Contingencia de precios (%)", 0, 10, 5, 1,
                            help="Recomendado: 3–7% para proyectos con TRM expuesta") / 100

    indirectos  = capex_base * ind_pct
    c_tec       = capex_base * c_tec_pct
    c_pre       = capex_base * c_pre_pct
    capex_total = capex_base + indirectos + c_tec + c_pre

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("CAPEX Base",    f"USD {capex_base:,.0f}",   f"$ {capex_base*tc/1e6:.2f} M COP", delta_color="off")
    m2.metric("Indirectos",    f"USD {indirectos:,.0f}",   f"{ind_pct*100:.0f}% CAPEX base",   delta_color="off")
    m3.metric("Contingencias", f"USD {c_tec+c_pre:,.0f}",  f"Téc {c_tec_pct*100:.0f}% + Pre {c_pre_pct*100:.0f}%", delta_color="off")
    m4.metric("✅ CAPEX TOTAL",f"USD {capex_total:,.0f}",   f"$ {capex_total*tc/1e6:.2f} M COP",delta_color="off")

    # ── KPIs de bancabilidad ──────────────────────────────────────────────────
    st.markdown("##### 📐 KPIs de bancabilidad")
    k1, k2, k3, k4 = st.columns(4)
    if p_stc > 0 and capex_total > 0:
        costo_wp = capex_total / p_stc / 1000
        k1.metric("Costo / Wp", f"USD {costo_wp:.2f}/Wp", f"$ {costo_wp*tc*1000:,.0f} COP/Wp", delta_color="off")
        if costo_wp > 5.0:
            st.warning(f"⚠️ USD {costo_wp:.2f}/Wp — muy alto. Ref. BIPV fachada: USD 1.8–4.0/Wp. "
                       f"Verifica que todos los precios estén en USD (no COP).")
        elif costo_wp > 3.5:
            st.info(f"ℹ️ USD {costo_wp:.2f}/Wp — rango alto. Ref.: USD 1.8–3.5/Wp para BIPV fachada.")
    if area_m2 > 0 and capex_total > 0:
        costo_m2 = capex_total / area_m2
        k2.metric("Costo / m²", f"USD {costo_m2:.0f}/m²", f"$ {costo_m2*tc/1e3:.1f} k COP/m²", delta_color="off")
        if costo_m2 > 400:
            st.info(f"ℹ️ USD {costo_m2:.0f}/m² — Ref. BIPV: USD 180–350/m².")
    if sub7 > 0 and capex_total > 0:
        opex_ratio = sub7 / capex_total * 100
        k3.metric("OPEX / CAPEX anual", f"{opex_ratio:.2f}%", "Ref.: 1.0–2.5%/año", delta_color="off")
        if opex_ratio > 3.0:
            st.warning(f"⚠️ OPEX/CAPEX = {opex_ratio:.1f}% — revisa fondos de reposición o seguros.")
    if p_stc > 0 and sub7 > 0:
        k4.metric("OPEX / kWp·año", f"USD {sub7/p_stc:.0f}", "BIPV: 18–32 · Techo: 9–16 · Granja: 8–14 USD/kWp·año", delta_color="off")
    if sub6 > 0 and capex_directo > 0:
        st.caption(f"🧾 Costos blandos = **{sub6/capex_directo*100:.1f}% del CAPEX directo** (ref. Colombia: 8–18%)")

    opex_pub  = sub7
    _frac_eq  = (sub3 + sub4 + sub5) / capex_total if capex_total > 0 else 0.65

    # ── Publicar en session_state ─────────────────────────────────────────────
    # GUARDIA: si la Estimación Rápida fue aplicada (est_rapida_aplicada=True),
    # NO sobreescribir presupuesto_capex_usd con el valor de los tabs.
    # La Estimación Rápida tiene autoridad hasta que el usuario presione "Limpiar".
    # Los tabs incompletos no deben silenciosamente reemplazar el CAPEX paramétrico.
    if not _est_activa:
        # #115 — La cotización real (subtotal de los tabs) fluye al CAPEX en el
        # MISMO rerun en que cambia el subtotal (no requiere pulsar botón), de
        # modo que 💰 Financiero refleja los precios actualizados de inmediato.
        _capex_prev = st.session_state.get("presupuesto_capex_usd", None)
        st.session_state["presupuesto_capex_usd"]       = capex_total
        st.session_state["presupuesto_opex_anual_usd"]  = sub7
        # Actualizar la marca de tiempo solo cuando el valor CAMBIA (comparación
        # EXACTA para que "última actualización" sea veraz incluso ante cambios
        # pequeños de precio) o cuando cambia la fuente activa.
        if _capex_prev != capex_total or st.session_state.get("presupuesto_fuente") != "Presupuesto detallado":
            _marcar_fuente_capex("Presupuesto detallado")
    st.session_state["presupuesto_capex_directo"]   = capex_directo
    st.session_state["presupuesto_capex_blando"]    = sub6
    st.session_state["presupuesto_sub_directo"]     = capex_directo
    st.session_state["presupuesto_fraccion_equipos"]= _frac_eq
    # ── Subtotales por sección (para el reporte PDF) ──────────────────────────
    st.session_state["presupuesto_sub_perfileria"]     = sub1
    st.session_state["presupuesto_sub_mano_obra"]      = sub2
    st.session_state["presupuesto_sub_sistema_fv"]     = sub3
    st.session_state["presupuesto_sub_inversor"]       = sub4
    st.session_state["presupuesto_sub_catalogo"]       = sub5
    st.session_state["presupuesto_capex_indirectos"]   = indirectos
    st.session_state["presupuesto_capex_cont"]         = c_tec + c_pre
    st.session_state["presupuesto_ind_pct"]            = ind_pct
    st.session_state["presupuesto_cont_pct"]           = c_tec_pct + c_pre_pct

    st.success(
        f"✅ **CAPEX TOTAL USD {capex_total:,.0f}** ($ {capex_total*tc/1e6:.2f} M COP) "
        f"→ 💰 Financiero lo usa automáticamente. "
        f"Ley 1715 frac. equipos: **{_frac_eq*100:.0f}%**"
        + (f" · **OPEX USD {sub7:,.0f}/año** enviado al flujo de caja." if sub7 > 0 else
           " · ⚠️ OPEX = USD 0 — completa la pestaña 📅 OPEX Anual.")
    )

    # ── #81 — Avisar si Costos Blandos están vacíos en modo cotización real ────
    if sub6 == 0 and capex_directo > 0:
        _ref_blando_lo = capex_directo * 0.10
        _ref_blando_hi = capex_directo * 0.20
        st.warning(
            f"⚠️ **Costos Blandos = USD 0** — la pestaña 🧾 Costos Blandos está vacía. "
            f"Para un presupuesto bancable, ingeniería, permisos RETIE/UPME, PM y seguros "
            f"representan el **10–20% del CAPEX directo** "
            f"(≈ USD {_ref_blando_lo:,.0f} – USD {_ref_blando_hi:,.0f} para este proyecto).  \n"
            f"Ve a la pestaña **🧾 Costos Blandos** → **🪄 Sugerir valores conservadores** para completarlos "
            f"antes de enviar el presupuesto a Financiero."
        )

# ══════════════════════════════════════════════════════════════════════════════
# 📤 EXPORTAR COTIZACIÓN — documento presentable para el cliente final
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📤 Exportar cotización")
st.caption(
    "Genera una cotización limpia para el cliente (Excel o PDF) con los ítems activos "
    "agrupados por categoría, subtotales y total en COP. No incluye KPIs bancarios ni "
    "columnas internas de fuente de precios."
)

# ── Reunir ítems ACTIVOS de todas las secciones → filas en COP ────────────────
_SEC_LABELS = {
    "perfileria": "🔩 Perfilería y Estructura",
    "mano_obra":  "👷 Mano de Obra y Servicios",
    "sistema_fv": "⚡ Sistema FV (cables, protecciones)",
    "inversor":   "🔌 Inversor y Equipos Eléctricos",
    "catalogo":   "📦 Equipos Principales",
    "soft":       "🧾 Costos Blandos (ingeniería, trámites, gestión)",
}

def _recolectar_items_cotizacion(trm_cop):
    """Extrae ítems activos de los DataFrames de sesión → filas de cotización.
    NO incluye la columna 'Costos Blandos' aquí: se muestra como línea de total aparte
    para mantener el subtotal = CAPEX directo (materiales + equipos + mano de obra)."""
    filas = []
    for _key in ("perfileria", "mano_obra", "sistema_fv", "inversor", "catalogo"):
        _df = st.session_state.get(f"df_sec_{_key}")
        if _df is None or not hasattr(_df, "iterrows"):
            continue
        for _, _r in _df.iterrows():
            if not bool(_r.get("Activo", True)):
                continue
            try:
                _cant = float(_r.get("Cantidad", 0) or 0)
                _uni_usd = float(_r.get("USD_un", 0) or 0)
            except (TypeError, ValueError):
                continue
            _desc = str(_r.get("Descripcion", "") or "").strip()
            _tot_usd = _cant * _uni_usd
            if not _desc or _tot_usd <= 0:
                continue
            filas.append({
                "categoria":    _SEC_LABELS.get(_key, _key),
                "descripcion":  _desc,
                "ref":          str(_r.get("Ref", "") or ""),
                "cantidad":     _cant,
                "unidad":       str(_r.get("Unidad", "") or ""),
                "unitario_usd": _uni_usd,
                "total_usd":    _tot_usd,
                "unitario_cop": _uni_usd * trm_cop,
                "total_cop":    _tot_usd * trm_cop,
            })
    return filas

_items_cot = _recolectar_items_cotizacion(tc)

# ── Totales en COP compuestos SIEMPRE desde los mismos ítems exportados ──────
# (revisión: no usar presupuesto_capex_usd — puede quedar rezagado del Resumen
# cuando la Estimación Rápida fue aplicada y luego se ingresaron cotizaciones
# reales; el total exportado DEBE cuadrar con la tabla exportada.)
_blando_usd      = float(st.session_state.get("presupuesto_capex_blando", 0.0))
_indirect_usd    = float(st.session_state.get("presupuesto_capex_indirectos", 0.0))
_cont_usd        = float(st.session_state.get("presupuesto_capex_cont", 0.0))

_subtotal_cop    = sum(i["total_cop"] for i in _items_cot)
_blando_cop      = _blando_usd * tc
_indirect_cop    = _indirect_usd * tc
_cont_cop        = _cont_usd * tc
_total_cop       = _subtotal_cop + _blando_cop + _indirect_cop + _cont_cop

# Guardia de consistencia: el total debe ser exactamente la suma de sus partes.
_descuadre = abs(_total_cop - (_subtotal_cop + _blando_cop + _indirect_cop + _cont_cop))
_hay_items = len(_items_cot) > 0 and _total_cop > 0 and _descuadre < 1.0

# Aviso si el CAPEX publicado por el Resumen difiere de lo que se exporta
_capex_usd_pub = float(st.session_state.get("presupuesto_capex_usd", 0.0))
if _items_cot and _capex_usd_pub > 0:
    _total_pub_cop = _capex_usd_pub * tc
    if abs(_total_pub_cop - _total_cop) / _total_pub_cop > 0.01:
        st.info(
            "ℹ️ El total de la cotización se calcula desde los ítems activos de las "
            "pestañas y difiere del CAPEX del Resumen "
            f"({'%.1f' % (abs(_total_pub_cop - _total_cop) / _total_pub_cop * 100)} %). "
            "Esto suele pasar cuando la Estimación Rápida sigue aplicada o hay ítems "
            "desactivados — recalcula el Resumen si quieres que coincidan."
        )

if not _hay_items:
    st.warning(
        "⚠️ No hay ítems activos con valor en la cotización. Completa al menos una "
        "pestaña de cotización (o aplica la 🧮 Estimación Rápida y luego ingresa "
        "cotizaciones reales) para habilitar la descarga."
    )

# ── #171 — Guardia TRM: nunca exportar una cotización con tasa de cambio en
# cero o sin confirmar. Si la API falló, la app queda con el "valor por
# defecto" (4.200) — una cotización al cliente con TRM inventada es tan grave
# como una en cero. La TRM manual (editada por el usuario) SÍ habilita.
# #174: política unificada en calculos/trm_utils.trm_confirmada()
from calculos.trm_utils import trm_confirmada as _trm_confirmada, trm_error_msg as _trm_error_msg
_trm_ok, _tc_g, _ = _trm_confirmada()
if _hay_items and not _trm_ok:
    st.error(_trm_error_msg(_tc_g))
_export_ok = _hay_items and _trm_ok

# ── Campos editables de la cotización ─────────────────────────────────────────
ce1, ce2 = st.columns([3, 1])
_cot_cliente = ce1.text_input(
    "Nombre del cliente / destinatario",
    value=st.session_state.get("cot_cliente", ""),
    placeholder="Ej.: Inmobiliaria Andina S.A.S.",
    key="cot_cliente",
)
_cot_validez = ce2.number_input(
    "Validez de la oferta (días)", min_value=1, max_value=365,
    value=int(st.session_state.get("cot_validez", 15)), step=1, key="cot_validez",
)

from calculos.export_cotizacion import NOTAS_DEFAULT as _NOTAS_DEFAULT_COT
_cot_notas = st.text_area(
    "Notas y condiciones (pie de la cotización)",
    value=st.session_state.get("cot_notas", _NOTAS_DEFAULT_COT),
    height=140, key="cot_notas",
)

# ── Armar dict de datos para el módulo (funciones puras) ──────────────────────
_fecha_hoy_str = date.today().strftime("%d/%m/%Y")
_fecha_iso     = date.today().strftime("%Y%m%d")
_datos_cot = {
    "empresa":            ppto_elaboro,
    "proyecto":           ppto_nombre,
    "cliente":            _cot_cliente,
    "fecha":              _fecha_hoy_str,
    "validez_dias":       int(_cot_validez),
    "trm":                float(tc),
    "items":              _items_cot,
    "subtotal_cop":       _subtotal_cop,
    "costos_blandos_cop": _blando_cop,
    "indirectos_cop":     _indirect_cop,
    "contingencia_cop":   _cont_cop,
    "total_cop":          _total_cop,
    "total_usd":          _capex_usd_pub if _capex_usd_pub > 0 else (_total_cop / tc if tc > 0 else 0.0),
    "notas":              _cot_notas,
}

# ── Botones de descarga (deshabilitados si no hay ítems) ──────────────────────
from calculos.export_cotizacion import (
    generar_cotizacion_excel as _gen_cot_xlsx,
    generar_cotizacion_pdf as _gen_cot_pdf,
    nombre_archivo_cotizacion as _nombre_cot,
)

_xlsx_bytes, _pdf_bytes, _err_cot = None, None, None
if _export_ok:
    try:
        _xlsx_bytes = _gen_cot_xlsx(_datos_cot)
        _pdf_bytes  = _gen_cot_pdf(_datos_cot)
    except ValueError as _e:
        _err_cot = str(_e)
        _export_ok = False
    except Exception as _e:  # noqa: BLE001
        _err_cot = f"Error al generar la cotización: {_e}"
        _export_ok = False

if _err_cot:
    st.error(f"❌ {_err_cot}")

cb1, cb2 = st.columns(2)
cb1.download_button(
    "⬇️ Descargar cotización (Excel)",
    data=_xlsx_bytes if _xlsx_bytes else b"",
    file_name=_nombre_cot(ppto_nombre, _fecha_iso, "xlsx"),
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True, disabled=not _export_ok, key="dl_cot_xlsx",
)
cb2.download_button(
    "⬇️ Descargar cotización (PDF)",
    data=_pdf_bytes if _pdf_bytes else b"",
    file_name=_nombre_cot(ppto_nombre, _fecha_iso, "pdf"),
    mime="application/pdf",
    use_container_width=True, disabled=not _export_ok, key="dl_cot_pdf",
)

if _export_ok:
    st.caption(
        f"📄 Cotización lista — {len(_items_cot)} ítems activos · "
        f"TOTAL $ {round(_total_cop):,.0f}".replace(",", ".") + " COP"
        + (f" (~USD {_datos_cot['total_usd']:,.0f})" if tc > 0 else "")
    )
