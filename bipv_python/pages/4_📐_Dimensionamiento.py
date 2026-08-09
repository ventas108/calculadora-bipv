"""Página 4 — Dimensionamiento de strings."""
import math
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from calculos.dimensionamiento import (
    mapear_inversores_catalogo,
    optimizar_n_serie,
    dimensionar_sistema,
)
from calculos.modelo_iv import preparar_panel_iv, resolver_curva_iv, resolver_panel_calibrado
from datos.tecnologias_bipv import MODULOS_BIPV
from datos.catalogo_paneles_excel import cargar_catalogo_excel, obtener_panel_excel
from datos.catalogo_inversores_excel import (
    cargar_catalogo_inversores,
    obtener_inversor_excel,
    diagnostico_catalogo_inversores as _diag_inv_fn,
    excel_mtime_inv as _mtime_inv,
    cargar_catalogo_inversores as _cargar_cat_inv,
)
from datos.catalogo_inversores import INVERSORES, seleccionar_inversor
from calculos.panel_iv_check import analizar_panel_motiv as _check_iv_dim

st.set_page_config(page_title="Dimensionamiento — BIPV", page_icon="📐", layout="wide")

from calculos.auth import requerir_login
requerir_login()

# ── #225: restaurar panel/inversor predeterminados del usuario ────────────────
# Debe correr ANTES de instanciar los selectores (patrón widgets keyed).
from calculos.persistencia_resultados import (
    cargar_seleccion_equipos,
    guardar_seleccion_equipos,
)
_auth_email_dim = st.session_state.get("auth_email", "")
if not st.session_state.get("_sel_equipos_restaurada"):
    st.session_state["_sel_equipos_restaurada"] = True
    _sel_pers = cargar_seleccion_equipos(_auth_email_dim)
    if _sel_pers.get("panel") and "panel_pref_persistido" not in st.session_state:
        st.session_state["panel_pref_persistido"] = _sel_pers["panel"]
    if _sel_pers.get("inversor") and not st.session_state.get("inversor_nombre_dim"):
        st.session_state["inversor_nombre_dim"] = _sel_pers["inversor"]

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página
st.title("📐 Dimensionamiento de Strings")
st.caption("Equivalente de Mod_OptimizarStringSizing + Mod_CalculoStringSizing (VBA)")

col1, col2 = st.columns(2)

with col1:
    _cat_excel = cargar_catalogo_excel()
    _lista_paneles = list(_cat_excel.keys()) if _cat_excel else list(MODULOS_BIPV.keys())
    _panel_pref = st.session_state.get("panel_pref_persistido", "")
    if _panel_pref in _lista_paneles:
        _idx_default = _lista_paneles.index(_panel_pref)
    else:
        _idx_default = _lista_paneles.index("ASP-ST1-T40") if "ASP-ST1-T40" in _lista_paneles else 0
    # #118 — badge ✅/⚠️ en la lista (mismo criterio que Motor IV: faltan Voc/Isc/Vmp/Imp)
    def _fmt_panel_dim(name: str) -> str:
        _p = (_cat_excel.get(name) if _cat_excel else None) or MODULOS_BIPV.get(name) or {}
        _err, _ = _check_iv_dim(_p)
        return f"{'⚠️' if _err else '✅'} {name}"
    panel_nombre   = st.selectbox("Panel", _lista_paneles, index=_idx_default,
                                  format_func=_fmt_panel_dim)
    _cat_inv = cargar_catalogo_inversores()
    _lista_inv = list(_cat_inv.keys()) if _cat_inv else list(INVERSORES.keys())
    _inv_default = st.session_state.get("inversor_nombre_dim", "")
    _idx_inv = (
        _lista_inv.index(_inv_default)
        if _inv_default in _lista_inv
        else next(
            (i for i, k in enumerate(_lista_inv)
             if "MID15KTL3" in k or "MID 15KTL3" in k),
            0,
        )
    )
    # El botón del mapeo puede solicitar un cambio de modelo antes del rerun.
    # Se usa una clave explícita para que el selector visible se sincronice
    # realmente, sin pisar una selección manual del usuario.
    _inv_pendiente = st.session_state.pop("_inversor_nombre_dim_pendiente", None)
    if _inv_pendiente in _lista_inv:
        st.session_state["inversor_selector_dim"] = _inv_pendiente
    elif (
        "inversor_selector_dim" not in st.session_state
        or st.session_state["inversor_selector_dim"] not in _lista_inv
    ):
        st.session_state["inversor_selector_dim"] = _lista_inv[_idx_inv]
    inversor_nombre = st.selectbox(
        "Inversor",
        _lista_inv,
        key="inversor_selector_dim",
    )
    # #225 — fijar la selección actual como predeterminada del usuario
    if st.button(
        "📌 Fijar panel + inversor como predeterminados",
        key="btn_fijar_seleccion_equipos",
        help=(
            "Guarda esta selección en tu cuenta: al abrir la app en una nueva "
            "sesión (F5 o reinicio del servidor), estos serán los valores "
            "preseleccionados en vez de los defaults de fábrica."
        ),
    ):
        if guardar_seleccion_equipos(_auth_email_dim, panel_nombre, inversor_nombre):
            st.session_state["panel_pref_persistido"] = panel_nombre
            st.success(
                f"📌 Guardado: **{panel_nombre}** + **{inversor_nombre}** "
                "quedarán preseleccionados en tus próximas sesiones."
            )
        else:
            st.warning("No se pudo guardar la selección (revisa permisos del servidor).")

# Cargar dicts antes de col2 para que estén disponibles al calcular N_min_scan
_panel_catalogo = obtener_panel_excel(panel_nombre) if _cat_excel else MODULOS_BIPV[panel_nombre]
panel    = resolver_panel_calibrado(_panel_catalogo)
inversor = obtener_inversor_excel(inversor_nombre) if _cat_inv else seleccionar_inversor(inversor_nombre)

# ── Aviso Motor IV: panel sin datos IV suficientes (#118) ─────────────────────
_iv_err, _iv_adv = _check_iv_dim(panel)
if _iv_err:
    _falt = ", ".join(f"`{c}`" for c, _ in _iv_err)
    st.warning(
        f"⚠️ **{panel_nombre}** no tiene datos IV suficientes para Motor IV.  \n"
        f"Campos requeridos ausentes: {_falt}.  \n"
        f"El dimensionamiento eléctrico funcionará, pero la curva I-V no podrá "
        f"simularse en Motor IV. Completa el catálogo Excel con estos valores."
    )
elif _iv_adv:
    _adv_campos = [c for c, _ in _iv_adv if not c.startswith("⚠️")]
    if _adv_campos:
        st.info(
            f"ℹ️ **{panel_nombre}** puede simularse en Motor IV con estimaciones.  \n"
            f"Campos opcionales ausentes: {', '.join(f'`{c}`' for c in _adv_campos)} "
            f"— se usarán defaults por tecnología."
        )

# ── #58 — Aviso cuando las especificaciones del panel son estimadas ──────────
# El catálogo Excel trae Confianza="Media" cuando las dimensiones físicas del
# panel son aproximadas (no confirmadas con ficha del fabricante). El área y el
# número de paneles calculados heredan ese margen de error.
# Auditoría: el catálogo mezcla 'Alta'/'high'/'Alta — ficha oficial…' con
# 'Media'/'medium'. Solo se avisa cuando la confianza declarada es media/baja;
# valores vacíos, 'nan' (celda vacía de pandas) o desconocidos NO disparan.
_confianza_panel = str(panel.get("confianza", "") or "").strip().lower()
_es_estimado = _confianza_panel.startswith(("media", "medium", "baja", "low"))
if _es_estimado:
    st.warning(
        f"ℹ️ **Datos estimados** — la confianza del catálogo para "
        f"**{panel_nombre}** es *{panel.get('confianza')}*: sus dimensiones "
        f"físicas son aproximadas.  \n"
        f"Los cálculos de **área y número de paneles** pueden tener margen de "
        f"error. Confirma las dimensiones exactas con el fabricante antes de "
        f"cotizar."
    )

# ── Auto-población de temperaturas desde TMY ──────────────────────────────────
# Se recalcula SOLO cuando cambia el origen de datos climáticos (nueva ciudad/TMY).
# Una vez aplicado para una ciudad, el usuario puede editar libremente los campos.
_tmy_df    = st.session_state.get("tmy_df")
_ciudad_ss = st.session_state.get("tmy_ciudad", "")
_ciudad_applied = st.session_state.get("_dim_tmy_ciudad_ref", None)
_temp_auto_info = None

# Guardián: si las tres temperaturas quedaron en 0 (p. ej. un proyecto
# guardado con ceros las pisó al restaurarse), re-sembrar desde el TMY.
# Físicamente T_mín, T_realista y T_extremo nunca son 0.0 a la vez.
_temps_en_cero = all(
    abs(float(st.session_state.get(_k) or 0.0)) < 1e-9
    for _k in ("T_min_diseno", "T_cel_realista", "T_cel_extremo")
) and any(
    st.session_state.get(_k) is not None
    for _k in ("T_min_diseno", "T_cel_realista", "T_cel_extremo")
)

if _tmy_df is not None and _ciudad_ss and (
    _ciudad_ss != _ciudad_applied or _temps_en_cero
):
    try:
        _noct    = float(panel.get("NOCT", 45.0))
        _t2m     = _tmy_df["T2m"] if "T2m" in _tmy_df.columns else _tmy_df.iloc[:, 0]
        _t_min   = round(float(_t2m.min()), 1)
        _t_p95   = round(float(_t2m.quantile(0.95)), 1)
        _t_max   = round(float(_t2m.max()), 1)
        # T_celda = T_amb + (NOCT-20)/800 * G  (fórmula Mod_TemperaturasDiseno VBA)
        _t_real  = round(_t_p95 + (_noct - 20.0) / 800.0 * 800.0, 1)   # G=800 W/m²
        _t_extr  = round(_t_max + (_noct - 20.0) / 800.0 * 1000.0, 1)  # G=1000 W/m²
        # Pre-poblar session_state ANTES de renderizar los widgets
        st.session_state["T_min_diseno"]       = _t_min
        st.session_state["T_cel_realista"]     = _t_real
        st.session_state["T_cel_extremo"]      = _t_extr
        st.session_state["_dim_tmy_ciudad_ref"] = _ciudad_ss
        _temp_auto_info = (
            f"🌡️ Temperaturas actualizadas desde TMY **{_ciudad_ss}** — "
            f"T_mín: {_t_min}°C · T_celda realista: {_t_real}°C · T_celda extremo: {_t_extr}°C "
            f"(NOCT {_noct}°C del panel)"
        )
    except Exception:
        pass  # Si falla, usa defaults anteriores sin interrumpir

with col2:
    # No pasar value= junto con key= cuando session_state ya trae el valor:
    # Streamlit advierte "created with a default value but also had its value
    # set via the Session State API". Se siembra el default solo si falta.
    st.session_state.setdefault("T_min_diseno", -5.0)
    st.session_state.setdefault("T_cel_realista", 36.35)
    st.session_state.setdefault("T_cel_extremo", 41.94)
    T_frio   = st.number_input("T_mín diseño (°C)", key="T_min_diseno",
                help="Auto-calculado como mínimo histórico del TMY. Determina Voc_max y riesgo sobre Vdc_max del inversor.")
    T_real   = st.number_input("T_celda caliente realista (°C)", key="T_cel_realista",
                help="T_amb P95 + (NOCT-20)/800×800 W/m². Determina Vmp de operación habitual.")
    T_extr   = st.number_input("T_celda caliente extremo (°C)", key="T_cel_extremo",
                help="T_amb máxima histórica + (NOCT-20)/800×1000 W/m². Determina Vmp mínimo (peor caso MPPT).")
    N_str_tr = st.number_input("N_strings por tracker (via combinadoras)", value=int(st.session_state.get("N_str_tr", 1)), min_value=1, key="N_str_tr")
    col_nm1, col_nm2 = st.columns(2)
    with col_nm1:
        # Auto-calcular N_min eléctrico desde MPPT del inversor para evitar que
        # un restart resetee a 5 y el optimizador proponga N inviables para el MPPT
        _vmppt_min  = inversor.get("Vmppt_min") or inversor.get("Vmppt_activo_min") or 0
        _vmp_panel  = panel.get("Vmp_stc") or panel.get("Vmp") or 1
        _n_min_elec = max(1, math.ceil(_vmppt_min / _vmp_panel)) if _vmppt_min else 5
        _n_min_guardado = int(
            st.session_state.get("N_min_scan", _n_min_elec)
        )
        _n_min_def = max(_n_min_elec, _n_min_guardado)
        _n_min_ajuste_manual = _n_min_def > _n_min_elec
        N_min_scan = st.number_input(
            (
                f"N mínimo a explorar "
                f"({'ajuste manual; eléctrico: ' + str(_n_min_elec) if _n_min_ajuste_manual else 'eléctrico: ' + str(_n_min_elec)})"
            ),
            value=_n_min_def, min_value=1, max_value=40, key="N_min_scan",
            help=f"Calculado como ⌈Vmppt_min({_vmppt_min}V) / Vmp_panel({_vmp_panel:.1f}V)⌉ = {_n_min_elec}"
        )
        if _n_min_ajuste_manual:
            st.caption(
                f"ℹ️ El mínimo eléctrico es **{_n_min_elec}**; se está explorando "
                f"desde **{_n_min_def}** por un valor manual guardado. "
                "Puedes reducirlo para incluir también configuraciones menores."
            )
    with col_nm2:
        N_max_scan = st.number_input("N máximo a explorar", value=int(st.session_state.get("N_max_scan", 20)), min_value=2, max_value=40, key="N_max_scan")

# ── Banner Motor Óptico ───────────────────────────────────────────────────────
_motor_ok_dim   = st.session_state.get("motor_optico_ok", False)
_mo_summary_dim = st.session_state.get("motor_optico_summary", {})
if _motor_ok_dim:
    _poa_ef_anual = st.session_state.get("poa_efectiva_anual_kWh_m2", 0.0)
    _factor_mo    = _mo_summary_dim.get("factor_global", 1.0)
    st.info(
        f"🔆 **Motor Óptico activo** — POA efectiva: **{_poa_ef_anual:,.0f} kWh/m²/año** "
        f"(factor global **{_factor_mo*100:.1f}%** = IAM + Soiling + Térmico).  \n"
        "El dimensionamiento eléctrico no depende de la POA; la corrección óptica se aplica "
        "automáticamente en 📊 **Producción** al simular."
    )

# Caption estable de temperaturas (siempre presente → evita removeChild de React)
_tmy_applied = st.session_state.get("_dim_tmy_ciudad_ref", "")
if _tmy_applied:
    st.caption(
        f"🌡️ Temperaturas desde TMY **{_tmy_applied}** — "
        f"T_mín: {T_frio:.1f}°C · T_cel realista: {T_real:.1f}°C · "
        f"T_cel extremo: {T_extr:.1f}°C  "
        f"*(NOCT {panel.get('NOCT', 45.0):.0f}°C · editable manualmente)*"
    )

# (panel e inversor ya cargados arriba)
if panel.get("costo_usd"):
    st.session_state["costo_modulo_usd"] = panel["costo_usd"]

# ── Indicador de datos para Motor IV ──────────────────────────────────────────
# Este estado debe usar el mismo validador que el aviso superior y Motor IV:
# Voc/Isc/Vmp/Imp son obligatorios; N_s, tecnología y coeficientes tienen
# defaults. Evita mostrar simultáneamente "puede simularse" y "solo energético".
if not _iv_err:
    st.success(
        "🟢 Datos IV obligatorios completos — Motor IV se activará automáticamente"
    )
else:
    _faltantes_obligatorios = ", ".join(c for c, _ in _iv_err)
    st.error(
        f"🔴 Ficha incompleta para Motor IV — faltan: "
        f"{_faltantes_obligatorios} | solo cálculo energético"
    )
if _iv_adv and not _iv_err:
    _adv_motor = ", ".join(c for c, _ in _iv_adv)
    st.info(
        f"ℹ️ Motor IV usará estimaciones/defaults en: {_adv_motor}. "
        "La simulación estará disponible, pero con menor precisión."
    )
if panel.get("notas"):
    st.caption(f"📋 {panel['notas'][:120]}")

# ── Motor IV automático — curva IV real para paneles 🟢 ───────────────────────
if not _iv_err:  # Voc/Isc/Vmp/Imp presentes; opcionales usan defaults
    _panel_iv = preparar_panel_iv(panel)
    if _panel_iv is not None:
        with st.expander("📈 Curva I-V real (Motor IV activado automáticamente)", expanded=False):
            _col_iv1, _col_iv2 = st.columns(2)
            with _col_iv1:
                _G_iv = st.slider("Irradiancia (W/m²)", 100, 1200, 1000, 100, key="iv_G")
                _T_iv = st.slider("T celda (°C)", 15, 75, 25, 5, key="iv_T")
            try:
                _res = resolver_curva_iv(float(_G_iv), float(_T_iv), _panel_iv, n_puntos=200)
                if _res["V"] is not None:
                    _V = _res["V"]
                    _I = _res["I"]
                    _P = _V * _I

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=list(_V), y=list(_I),
                        name="I-V", line=dict(color="#1f77b4", width=2),
                        yaxis="y1",
                    ))
                    fig.add_trace(go.Scatter(
                        x=list(_V), y=list(_P),
                        name="P-V", line=dict(color="#ff7f0e", width=2, dash="dash"),
                        yaxis="y2",
                    ))
                    # Punto MPP
                    fig.add_trace(go.Scatter(
                        x=[_res["Vmp"]], y=[_res["Pmax"]],
                        name=f"MPP ({_res['Pmax']:.1f} W)",
                        mode="markers",
                        marker=dict(size=10, color="red", symbol="star"),
                        yaxis="y2",
                    ))
                    fig.update_layout(
                        xaxis_title="Voltaje (V)",
                        yaxis=dict(title="Corriente (A)", side="left"),
                        yaxis2=dict(title="Potencia (W)", side="right", overlaying="y"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=340,
                        margin=dict(l=10, r=10, t=30, b=10),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Métricas STC
                    _mc1, _mc2, _mc3, _mc4, _mc5 = st.columns(5)
                    _mc1.metric("Voc", f"{_res['Voc']:.2f} V")
                    _mc2.metric("Isc", f"{_res['Isc']:.3f} A")
                    _mc3.metric("Vmp", f"{_res['Vmp']:.2f} V")
                    _mc4.metric("Imp", f"{_res['Imp']:.3f} A")
                    _mc5.metric("FF", f"{_res['FF']*100:.1f} %")

                    if _panel_iv.get("_estimado"):
                        _metodo = _panel_iv.get("_metodo", "fit_desoto")
                        st.caption(
                            f"⚠️ Parámetros SDM estimados vía **{_metodo}** desde ficha técnica "
                            f"(NsA={panel.get('NsA', '?')}, n={panel.get('n_idealidad', '?')}). "
                            "Resultado orientativo — para calibración exacta se requieren mediciones de laboratorio."
                        )
                    else:
                        st.caption("✅ Parámetros SDM calibrados directamente del catálogo.")
                else:
                    st.info("G=0 — introduce irradiancia > 0 para ver la curva.")
            except Exception as _e_iv:
                st.warning(f"Motor IV: no se pudo calcular la curva ({_e_iv})")

# ── Guardar panel en session_state para Motor IV automático (#7) ─────────────
st.session_state["panel_dict"]        = panel
st.session_state["panel_nombre_dim"]  = panel_nombre
# inversor ya cargado antes de col2
if inversor.get("costo_usd"):
    st.session_state["costo_inversor_usd"] = inversor["costo_usd"]
# Propagar inversor a session_state para compatibilidad baterías (#25)
st.session_state["inversor_nombre_dim"] = inversor_nombre
st.session_state["inversor_dict_dim"]   = inversor
if inversor.get("datos_completos"):
    st.success("🟢 Inversor: ficha completa")
else:
    _inv_falt = [k for k in ["Vdc_max","Vmppt_min","Vmppt_max","n_trackers","n_strings_tracker","I_max_tracker","P_dc_max_W"] if not inversor.get(k)]
    st.warning(f"🟡 Inversor incompleto — faltan: {', '.join(_inv_falt)}" if _inv_falt else "🟡 Inversor marcado como incompleto en catálogo")

st.markdown("---")
st.subheader("🧭 Mapeo de inversores opcionales para este panel")
st.caption(
    "Esta es una regla eléctrica informativa: se evalúa todo el catálogo contra "
    "el rango de N/string indicado. Puedes cargar un modelo compatible para "
    "actualizar la selección y obtener un prorrateo preliminar."
)
with st.container(border=True):
    st.caption(
        "✅ **Regla aplicada:** un inversor es opcional si al menos un "
        "**N/string** del rango explorado cumple simultáneamente Voc en frío, "
        "MPPT mínimo y máximo, y corriente máxima por tracker. "
        "El rango de este mapeo es independiente del inversor seleccionado. "
        "La selección del proyecto solo cambia cuando confirmas el botón de carga."
    )
    _map_c1, _map_c2 = st.columns(2)
    with _map_c1:
        _n_min_mapeo = st.number_input(
            "N mínimo para el mapeo",
            min_value=1,
            max_value=40,
            value=1,
            step=1,
            key="N_min_mapeo_inversores",
        )
    with _map_c2:
        _n_max_mapeo = st.number_input(
            "N máximo para el mapeo",
            min_value=1,
            max_value=40,
            value=max(20, int(N_max_scan)),
            step=1,
            key="N_max_mapeo_inversores",
        )
    if _n_max_mapeo < _n_min_mapeo:
        st.warning("El N máximo debe ser igual o mayor que el N mínimo.")
        _n_max_mapeo = _n_min_mapeo
    _cat_inv_mapeo = _cat_inv or INVERSORES
    _mapeo_inv = mapear_inversores_catalogo(
        panel=panel,
        inversores=_cat_inv_mapeo,
        N_min=int(_n_min_mapeo),
        N_max=int(_n_max_mapeo),
        T_frio=float(T_frio),
        T_real=float(T_real),
        T_extremo=float(T_extr),
        N_strings_tracker=int(N_str_tr),
    )
    _df_mapeo = pd.DataFrame(_mapeo_inv)
    _n_mapeo_ok = sum(fila["compatible"] for fila in _mapeo_inv)
    _n_mapeo_no_eval = sum(fila["estado"] == "🟡 No evaluable" for fila in _mapeo_inv)
    _n_mapeo_rech = len(_mapeo_inv) - _n_mapeo_ok - _n_mapeo_no_eval
    _mc1, _mc2, _mc3 = st.columns(3)
    _mc1.metric("✅ Compatibles", _n_mapeo_ok)
    _mc2.metric("🔴 No compatibles", _n_mapeo_rech)
    _mc3.metric("🟡 No evaluables", _n_mapeo_no_eval)
    st.caption(
        f"Panel evaluado: **{panel_nombre}** · rango mapeado: "
        f"**N={int(_n_min_mapeo)}–{int(_n_max_mapeo)} módulos/string** · "
        f"{len(_mapeo_inv)} inversores del catálogo."
    )
    if not _df_mapeo.empty:
        _cols_mapeo = [
            "modelo", "estado", "N_string_recomendado", "N_viables",
            "Voc_frio_V", "Vmp_real_V", "Isc_tracker_A", "Vdc_max_V",
            "MPPT_V", "trackers", "strings_tracker", "P_ac_nom_kW",
            "costo_usd", "motivo",
        ]
        _sel_mapeo = st.dataframe(
            _df_mapeo[_cols_mapeo],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="tabla_mapeo_inversores",
        )
        st.caption(
            "💡 Haz clic en una fila de la tabla para llevar ese modelo "
            "directamente a la casilla «Inversor compatible» de abajo."
        )
        _modelo_click_tabla = ""
        try:
            _filas_sel = _sel_mapeo.selection.rows
            if _filas_sel:
                _modelo_click_tabla = str(
                    _df_mapeo[_cols_mapeo].iloc[_filas_sel[0]]["modelo"]
                )
        except Exception:
            _modelo_click_tabla = ""
        _compatibles_mapeo = [
            fila for fila in _mapeo_inv
            if fila.get("compatible") and fila.get("N_string_recomendado")
        ]
        if _compatibles_mapeo:
            st.markdown("#### ⚡ Cargar un inversor compatible")
            st.caption(
                "Selecciona un modelo compatible para cargar su ficha en el selector "
                "principal y recalcular automáticamente un prorrateo preliminar."
            )
            _compatibles_por_nombre = {
                fila["modelo"]: fila for fila in _compatibles_mapeo
            }
            _opciones_compatibles = list(_compatibles_por_nombre)
            # Clic en la tabla → llevar el modelo a la casilla de abajo.
            # Solo cuando la selección de la tabla CAMBIA (no en cada rerun),
            # y ANTES de instanciar el selectbox (patrón widgets keyed).
            if (
                _modelo_click_tabla
                and _modelo_click_tabla
                != st.session_state.get("_ultimo_modelo_click_tabla", "")
            ):
                st.session_state["_ultimo_modelo_click_tabla"] = _modelo_click_tabla
                if _modelo_click_tabla in _opciones_compatibles:
                    st.session_state["selector_inversor_compatible_mapeo"] = (
                        _modelo_click_tabla
                    )
                else:
                    st.warning(
                        f"**{_modelo_click_tabla}** no es compatible con este "
                        "panel en el rango de N/string mapeado, así que no se "
                        "puede cargar en la casilla."
                    )
            _modelo_prelim_default = st.session_state.get(
                "prorrateo_preliminar_modelo", ""
            )
            _idx_compatible = (
                _opciones_compatibles.index(_modelo_prelim_default)
                if _modelo_prelim_default in _opciones_compatibles
                else 0
            )
            _modelo_compatible = st.selectbox(
                "Inversor compatible",
                _opciones_compatibles,
                index=_idx_compatible,
                format_func=lambda modelo: (
                    f"{modelo} · N/string recomendado: "
                    f"{_compatibles_por_nombre[modelo]['N_string_recomendado']}"
                ),
                key="selector_inversor_compatible_mapeo",
            )
            _fila_compatible = _compatibles_por_nombre[_modelo_compatible]
            if st.button(
                "⚡ Cargar y recalcular prorrateo preliminar",
                type="primary",
                key="cargar_inversor_compatible_mapeo",
            ):
                st.session_state["_inversor_nombre_dim_pendiente"] = _modelo_compatible
                st.session_state["inversor_nombre_dim"] = _modelo_compatible
                st.session_state["N_serie"] = int(
                    _fila_compatible["N_string_recomendado"]
                )
                # Resultado (sobrevive F5, a diferencia de la key del widget)
                st.session_state["N_str_tr_usado"] = int(N_str_tr)
                st.session_state["prorrateo_preliminar_modelo"] = _modelo_compatible
                st.session_state["prorrateo_preliminar_N"] = int(
                    _fila_compatible["N_string_recomendado"]
                )
                st.session_state["prorrateo_preliminar_panel"] = panel_nombre
                # #225 — persistir también al cargar un compatible
                guardar_seleccion_equipos(_auth_email_dim, panel_nombre, _modelo_compatible)
                st.session_state["panel_pref_persistido"] = panel_nombre
                st.rerun()
        else:
            st.info(
                "No hay inversores compatibles con el rango N/string seleccionado. "
                "Amplía el rango o revisa los datos eléctricos del catálogo."
            )
        st.download_button(
            "⬇️ Descargar mapeo de inversores (CSV)",
            _df_mapeo.to_csv(index=False).encode("utf-8-sig"),
            "mapeo_inversores_panel.csv",
            "text/csv",
            key="descargar_mapeo_inversores_panel",
        )

# ── Prorrateo preliminar desde un inversor compatible del mapeo ───────────────
_prelim_modelo = st.session_state.get("prorrateo_preliminar_modelo")
_prelim_n = st.session_state.get("prorrateo_preliminar_N")
if (
    _prelim_modelo
    and _prelim_modelo != inversor_nombre
) or (
    _prelim_modelo
    and st.session_state.get("prorrateo_preliminar_panel") != panel_nombre
):
    # Evita presentar un cálculo anterior después de una selección manual o
    # al cambiar de panel, donde el N recomendado podría ya no aplicar.
    st.session_state.pop("prorrateo_preliminar_modelo", None)
    st.session_state.pop("prorrateo_preliminar_N", None)
    st.session_state.pop("prorrateo_preliminar_panel", None)
    _prelim_modelo = None
    _prelim_n = None
if _prelim_modelo and _prelim_n:
    _prelim_inversor = obtener_inversor_excel(_prelim_modelo) if _cat_inv else (
        seleccionar_inversor(_prelim_modelo)
    )
    try:
        _prelim_n = int(_prelim_n)
        _prelim_n_mppt = int(
            float(
                _prelim_inversor.get("N_mppt")
                or _prelim_inversor.get("n_trackers")
                or 0
            )
        )
    except (TypeError, ValueError):
        _prelim_n_mppt = 0
    if _prelim_n_mppt > 0:
        _prelim_area_bruta = float(
            st.session_state.get("area_fachada_m2", 97.34)
        )
        _prelim_f_ocup = float(
            st.session_state.get("factor_ocupacion_pct", 100.0)
        )
        _prelim_area = _prelim_area_bruta * _prelim_f_ocup / 100.0
        _prelim_dim = dimensionar_sistema(
            panel,
            _prelim_area,
            _prelim_n,
            int(N_str_tr),
            _prelim_n_mppt,
        )
        st.markdown("### ⚡ Prorrateo preliminar del inversor cargado")
        st.success(
            f"✅ **{_prelim_modelo}** cargado desde el mapeo · "
            f"**{_prelim_n} módulos/string** · "
            f"{_prelim_n_mppt} tracker(s)"
        )
        _pc1, _pc2, _pc3, _pc4 = st.columns(4)
        _pc1.metric("Paneles / inversor", _prelim_dim["N_paneles"])
        _pc2.metric("P_DC / inversor", f"{_prelim_dim['P_dc_stc_kW']:.2f} kW")
        _pc3.metric("Área / inversor", f"{_prelim_dim['area_ocupada_m2']} m²")
        _pc4.metric("Cobertura unitaria", f"{_prelim_dim['cobertura_pct']}%")

        if _prelim_dim["area_ocupada_m2"] > 0:
            _prelim_n_inv = math.ceil(_prelim_area / _prelim_dim["area_ocupada_m2"])
            _prelim_total_panels = _prelim_n_inv * _prelim_dim["N_paneles"]
            _prelim_total_kwp = _prelim_n_inv * _prelim_dim["P_dc_stc_kW"]
            _prelim_total_area = _prelim_n_inv * _prelim_dim["area_ocupada_m2"]
            _prelim_cobertura = (
                min(round(_prelim_total_area / _prelim_area * 100, 1), 100.0)
                if _prelim_area > 0 else 0
            )
            _prelim_titulo_area = (
                "área útil para paneles"
                if _prelim_f_ocup < 100.0 else "toda el área"
            )
            st.markdown(
                f"#### 🏭 Proyecto completo ({_prelim_titulo_area})"
            )
            _pg1, _pg2, _pg3, _pg4, _pg5 = st.columns(5)
            _pg1.metric("Inversores", _prelim_n_inv)
            _pg2.metric("Paneles totales", f"{_prelim_total_panels:,}")
            _pg3.metric("kWp instalados", f"{_prelim_total_kwp:,.1f} kWp")
            _pg4.metric("Área cubierta", f"{_prelim_total_area:,.0f} m²")
            _pg5.metric(
                "Cobertura del área útil"
                if _prelim_f_ocup < 100.0 else "Cobertura total",
                f"{_prelim_cobertura} %",
            )
            st.session_state["N_inv_total"] = _prelim_n_inv
            st.session_state["P_dc_total_kWp"] = round(_prelim_total_kwp, 2)
            st.session_state["N_paneles_granja"] = _prelim_total_panels
    else:
        st.warning(
            f"El inversor **{_prelim_modelo}** no tiene un número válido de "
            "trackers para calcular el prorrateo preliminar."
        )

# ── #122 — Diagnóstico del catálogo de inversores (patrón #24 de baterías) ───
_diag_inv = _diag_inv_fn(mtime=_mtime_inv())
if _diag_inv["estado"] == "error":
    st.error(
        f"🔴 **Catálogo de inversores con problemas** — "
        f"{_diag_inv.get('detalle', 'faltan columnas críticas')}.  \n"
        f"Columnas críticas ausentes: "
        f"{', '.join(_diag_inv['columnas_criticas_faltantes']) or '—'}. "
        f"El dimensionamiento de strings puede salir incorrecto."
    )
elif _diag_inv["estado"] == "parcial":
    _resumen_p = []
    if _diag_inv["columnas_importantes_faltantes"]:
        _resumen_p.append(f"{len(_diag_inv['columnas_importantes_faltantes'])} columnas importantes ausentes")
    if _diag_inv["modelos_duplicados"]:
        _resumen_p.append(f"{len(_diag_inv['modelos_duplicados'])} modelos duplicados")
    if _diag_inv["modelos_incompletos"]:
        _resumen_p.append(f"{len(_diag_inv['modelos_incompletos'])} modelos incompletos")
    st.warning(f"🟡 Catálogo de inversores parcial: {' · '.join(_resumen_p)} — detalles abajo.")

with st.expander("🔍 Diagnóstico del catálogo de inversores", expanded=False):
    st.caption(f"Hoja usada: `{_diag_inv.get('hoja_usada', '—')}` · "
               f"Modelos cargados: **{_diag_inv.get('modelos_cargados', 0)}** · "
               f"Hojas en el Excel: {', '.join(_diag_inv.get('hojas_disponibles', []))}")
    if _diag_inv["columnas_criticas_faltantes"]:
        st.error("🔴 Columnas críticas ausentes: "
                 + ", ".join(f"`{c}`" for c in _diag_inv["columnas_criticas_faltantes"]))
    if _diag_inv["columnas_importantes_faltantes"]:
        st.warning("🟡 Columnas importantes ausentes: "
                   + ", ".join(f"`{c}`" for c in _diag_inv["columnas_importantes_faltantes"]))
    for _d in _diag_inv["modelos_duplicados"]:
        st.warning(f"🟡 **{_d['modelo']}** aparece {len(_d['filas_excel'])} veces "
                   f"(filas Excel {_d['filas_excel']}) — solo la última fila se usa.")
    for _m in _diag_inv["modelos_incompletos"]:
        st.info(f"ℹ️ **{_m['modelo']}**: faltan {', '.join(_m['campos_faltantes'])}")
    if _diag_inv["estado"] == "ok":
        st.success("🟢 Catálogo OK — columnas completas, sin duplicados ni modelos incompletos.")
    if st.button("🔄 Recargar catálogo de inversores", key="_reload_cat_inv",
                 help="Vuelve a leer el Excel del servidor (limpia la caché)."):
        _cargar_cat_inv.clear()
        _diag_inv_fn.clear()
        st.rerun()

if st.button("▶️ Optimizar N paneles/string", type="primary"):
    resultados = optimizar_n_serie(
        panel, inversor,
        T_frio=T_frio, T_real=T_real, T_extremo=T_extr,
        N_strings_tracker=int(N_str_tr),
        N_min=int(N_min_scan), N_max=int(N_max_scan),
    )

    filas = []
    for r in resultados:
        filas.append({
            "N/string": r.N_serie,
            "Voc frío (V)": r.Voc_frio,
            "Vmp realista (V)": r.Vmp_real,
            "Vmp extremo (V)": r.Vmp_extremo,
            "I equiv (A)": r.I_equiv_tracker,
            "1-Voc≤Vdc": r.v1_voc_max,
            "2-Vmp≥Vmppt_min": r.v2_vmp_real,
            "3-Vmp_ext≥Vmppt_min": r.v3_vmp_extr,
            "4-I≤Imax": r.v4_i_max,
            "5-Vmp≤Vmppt_max": r.v5_vmp_max,
            "MPPT util %": r.mppt_util_pct,
            "Riesgos": r.riesgos,
            "": r.semaforo_color(),
        })

    df = pd.DataFrame(filas)

    def colorear(val):
        if val == "FALLA":
            return "background-color: #FFCCCC; color: #CC0000; font-weight: bold"
        elif val == "ALERTA":
            return "background-color: #FFF3CD; color: #856404; font-weight: bold"
        elif val == "OK":
            return "background-color: #D4EDDA; color: #155724; font-weight: bold"
        return ""

    styled = df.style.map(colorear,
                          subset=["1-Voc≤Vdc", "2-Vmp≥Vmppt_min",
                                  "3-Vmp_ext≥Vmppt_min", "4-I≤Imax",
                                  "5-Vmp≤Vmppt_max"])
    st.dataframe(styled, use_container_width=True)

    # Mejor opción: N con 0 riesgos y MÁXIMA utilización del rango MPPT
    # (Vmp_real / Vmppt_max). Con el check v5 activo, candidatos con Vmp > Vmppt_max
    # ya quedan excluidos por riesgos > 0, así que max(mppt_util_pct) es seguro.
    sin_riesgos = [r for r in resultados if r.riesgos == 0]
    if sin_riesgos:
        mejor = max(sin_riesgos, key=lambda r: r.mppt_util_pct if r.mppt_util_pct > 0 else r.Vmp_real)
        _util_msg = f" · {mejor.mppt_util_pct:.1f}% MPPT" if mejor.mppt_util_pct > 0 else ""
        st.success(
            f"✅ N óptimo = **{mejor.N_serie} paneles/string** — "
            f"0 riesgos · Vmp = {mejor.Vmp_real:.1f} V{_util_msg}"
        )
        st.session_state["N_serie"] = mejor.N_serie
        st.session_state["N_str_tr_usado"] = int(N_str_tr)

        # Dimensionamiento del sistema — respeta el factor de ocupación
        # (agrivoltaica: los paneles solo cubren un % del terreno; el resto
        # queda libre para el cultivo)
        _area_bruta = float(st.session_state.get("area_fachada_m2", 97.34))
        _f_ocup     = float(st.session_state.get("factor_ocupacion_pct", 100.0))
        area        = _area_bruta * _f_ocup / 100.0
        if _f_ocup < 100.0:
            st.info(
                f"🌱 **Factor de ocupación {_f_ocup:.0f}%** — de los "
                f"{_area_bruta:,.0f} m² del terreno solo se dimensionan paneles "
                f"sobre **{area:,.0f} m²**; el resto queda libre para el cultivo. "
                f"(Se ajusta en 🏠 Proyecto.)"
            )
        dim  = dimensionar_sistema(panel, area, mejor.N_serie,
                                    int(N_str_tr), inversor["N_mppt"])

        st.markdown("### 📊 Por inversor (1 unidad)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Paneles / inversor", dim["N_paneles"])
        c2.metric("P_DC / inversor",    f"{dim['P_dc_stc_kW']:.2f} kW")
        c3.metric("Área / inversor",    f"{dim['area_ocupada_m2']} m²")
        c4.metric("Cobertura unitaria", f"{dim['cobertura_pct']}%")

        # ── Escalado a la granja completa ─────────────────────────────────────
        if dim["area_ocupada_m2"] > 0:
            N_inv        = math.ceil(area / dim["area_ocupada_m2"])
            total_panels = N_inv * dim["N_paneles"]
            total_kWp    = N_inv * dim["P_dc_stc_kW"]
            total_area   = N_inv * dim["area_ocupada_m2"]
            cobert_total = min(round(total_area / area * 100, 1), 100.0) if area > 0 else 0
            P_ac_inv_kW  = (inversor.get("P_ac_nom_W") or inversor.get("P_dc_max_W") or 0) / 1000
            _tit_area = ("área útil para paneles" if _f_ocup < 100.0 else "toda el área")
            st.markdown(f"### 🏭 Proyecto completo ({_tit_area})")
            g1, g2, g3, g4, g5 = st.columns(5)
            g1.metric("Inversores",       N_inv)
            g2.metric("Paneles totales",  f"{total_panels:,}")
            g3.metric("kWp instalados",   f"{total_kWp:,.1f} kWp")
            g4.metric("Área cubierta",    f"{total_area:,.0f} m²")
            g5.metric("Cobertura del área útil" if _f_ocup < 100.0 else "Cobertura total",
                      f"{cobert_total} %",
                      help=(f"Sobre los {area:,.0f} m² útiles para paneles "
                            f"({_f_ocup:.0f}% del terreno)") if _f_ocup < 100.0 else None)
            st.session_state["N_inv_total"]      = N_inv
            st.session_state["P_dc_total_kWp"]  = round(total_kWp, 2)
            st.session_state["N_paneles_granja"] = total_panels
    else:
        st.error("❌ Ningún N válido en el rango. Revisar parámetros del inversor o temperaturas.")
